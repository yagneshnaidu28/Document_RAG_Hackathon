import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

load_dotenv(Path(__file__).resolve().parent / ".env")

import sessions  # noqa: E402
from chunking.chunking_pdf import NoReadableText, chunk_pdf  # noqa: E402
from rag.chat import answer  # noqa: E402
from rag.vectorstore import STORAGE, add_chunks, clear_store, get_embeddings  # noqa: E402

MAX_BYTES = 40 * 1024 * 1024
UPLOADS = STORAGE / "uploads"
DOCUMENT_FILE = STORAGE / "document.json"

@asynccontextmanager
async def lifespan(_app):
    get_embeddings()  # load the embedding model now, not during the first upload
    yield


app = FastAPI(title="Document Agents API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://127.0.0.1:4000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def invalid() -> HTTPException:
    return HTTPException(status_code=400, detail="this document is invalid")


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile):
    name = file.filename or ""
    if not name.lower().endswith(".pdf"):
        raise invalid()

    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or not data.startswith(b"%PDF"):
        raise invalid()

    UPLOADS.mkdir(parents=True, exist_ok=True)
    pdf_path = UPLOADS / f"{uuid.uuid4().hex}.pdf"
    pdf_path.write_bytes(data)

    try:
        chunks = await run_in_threadpool(chunk_pdf, str(pdf_path))
    except (NoReadableText, Exception):
        pdf_path.unlink(missing_ok=True)
        raise invalid()

    # new document replaces the old one
    for old in UPLOADS.glob("*.pdf"):
        if old != pdf_path:
            old.unlink(missing_ok=True)
    count = await run_in_threadpool(add_chunks, chunks)
    DOCUMENT_FILE.write_text(
        json.dumps(
            {
                "document_id": pdf_path.stem,
                "filename": name,
                "chunks": count,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    return {"ok": True, "chunks": count}


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


@app.post("/chat")
def chat(req: ChatRequest):
    doc = current_document()
    if not doc:
        raise HTTPException(status_code=409, detail="no document to search")
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="empty question")

    if req.session_id:
        try:
            session = sessions.load(req.session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="conversation not found")
        if session["document_id"] != doc["document_id"]:
            raise HTTPException(
                status_code=409,
                detail="this conversation is read-only because its document was replaced or deleted",
            )
    else:
        session = sessions.create(doc["document_id"])

    history = session["messages"][-6:]
    sessions.add_message(session, "user", question)  # saved even if the answer fails
    try:
        text = answer(question, history)
    except Exception:
        return JSONResponse(
            status_code=502,
            content={
                "detail": "the answer could not be generated, please try again",
                "session_id": session["id"],
            },
        )
    sessions.add_message(session, "assistant", text)
    return {"answer": text, "session_id": session["id"]}


@app.get("/sessions")
def list_sessions():
    doc = current_document()
    return sessions.list_visible(doc["document_id"] if doc else None)


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    try:
        session = sessions.load(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="conversation not found")
    if session.get("visibility") is not True:
        raise HTTPException(status_code=404, detail="conversation not found")
    doc = current_document()
    out = sessions.summary(session, doc["document_id"] if doc else None)
    out["messages"] = session["messages"]
    return out


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    try:
        sessions.hide(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="conversation not found")
    return {"ok": True}


def current_document():
    if not DOCUMENT_FILE.exists():
        return None
    try:
        return json.loads(DOCUMENT_FILE.read_text(encoding="utf-8"))
    except ValueError:
        return None


@app.get("/document")
def get_document():
    doc = current_document()
    if not doc:
        return {"exists": False}
    return {
        "exists": True,
        "document_id": doc["document_id"],
        "filename": doc["filename"],
        "chunks": doc.get("chunks"),
        "uploaded_at": doc.get("uploaded_at"),
    }


@app.delete("/document")
def delete_document():
    clear_store()
    for pdf in UPLOADS.glob("*.pdf"):
        pdf.unlink(missing_ok=True)
    DOCUMENT_FILE.unlink(missing_ok=True)
    return {"ok": True}
