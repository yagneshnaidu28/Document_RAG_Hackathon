import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parent / ".env")

from chunking.chunking_pdf import NoReadableText, chunk_pdf  # noqa: E402
from rag.vectorstore import STORAGE, add_chunks  # noqa: E402

MAX_BYTES = 40 * 1024 * 1024
UPLOADS = STORAGE / "uploads"
DOCUMENT_FILE = STORAGE / "document.json"

app = FastAPI(title="Document Agents API")
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
        chunks = chunk_pdf(str(pdf_path))
    except (NoReadableText, Exception):
        pdf_path.unlink(missing_ok=True)
        raise invalid()

    # new document replaces the old one
    for old in UPLOADS.glob("*.pdf"):
        if old != pdf_path:
            old.unlink(missing_ok=True)
    count = add_chunks(chunks)
    DOCUMENT_FILE.write_text(
        json.dumps(
            {
                "document_id": pdf_path.stem,
                "filename": name,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    return {"ok": True, "chunks": count}
