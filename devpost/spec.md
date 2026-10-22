---
doc: spec
status: approved
---

# Document Agents — Technical Spec

## How This Works, In Plain Language
There are two programs. A **React website** (what the user sees, on port 4000) and a **Python API** built with FastAPI (the brain, on port 8000). The website sends requests to the API and shows what comes back.

When a user uploads a PDF, the API saves it in a folder, reads each page's text (PyPDFLoader), and splits the text into chunks of about 1000 characters that end at paragraph or sentence boundaries (recursive splitting, with a small overlap). Each chunk is turned into a list of numbers (an embedding, made by a local sentence-transformers model) and stored in Chroma, a small database kept in a folder on the laptop.

When the user asks a question, the question is turned into numbers the same way. Chroma returns the 5 chunks whose numbers are closest (top-k similarity). Those 5 chunks, the last 6 chat messages, and the question go to Gemini with a strict prompt: answer only from these chunks; if the answer isn't there, reply exactly "not found in this document." The reply is shown in the chat and saved in a session file.

Why this shape: it is the smallest pipeline that keeps your kernel (answers only from the document), with no accounts, no cloud database, and only one external service (Gemini).

## The Core Journey Through the System
PRD ref: `prd.md > The Core Journey`.
1. The user opens `http://localhost:4000`. The site asks the API `GET /document`. No document → upload screen.
2. The user picks a PDF. The site checks it is a `.pdf` of at most 40 MB, shows the three-dots loader, and sends it to `POST /upload-pdf`.
3. The API checks again, saves the file in `storage/uploads/`, and calls `chunking_pdf(pdf_path)` in the `chunking` folder. That function loads pages, drops empty ones, splits them into chunks, and returns the chunks. If there is no readable text, the API replies "invalid."
4. The API clears the old Chroma data, stores the new chunks, writes `storage/document.json` (new document id and filename), and answers `{"ok": true}`.
5. The site opens the agent screen: header, sidebar (`GET /sessions`), the PDF icon, and the chat.
6. The user types a question. The site sends `POST /chat` with the session id and question.
7. The API retrieves the top 5 chunks, builds the grounded prompt with the last 6 messages, calls Gemini, appends both messages to the session file, and returns the answer text.
8. The user deletes a conversation (confirmed): `DELETE /sessions/{id}` sets `visibility` to false. Deleting the PDF: `DELETE /document` clears Chroma, the file, and `document.json`.

## Stack
- **Backend:** Python 3.12, **FastAPI** + Uvicorn. Chosen by the learner: lightweight and reliable. https://fastapi.tiangolo.com/
- **PDF reading:** **PyPDFLoader** (LangChain `langchain_community`, uses `pypdf`). Learner choice: used it before and finds it reliable. https://python.langchain.com/docs/integrations/document_loaders/pypdfloader/
- **Chunking:** **RecursiveCharacterTextSplitter** (`langchain_text_splitters`, chunk size 1000, overlap 150). Changed from semantic chunking during the build at the learner's request: semantic chunking took over 4 minutes on a 402-page PDF; this takes about 1 minute for the same file. Tradeoff: chunks follow size and paragraph boundaries, not shifts in meaning.
- **Embeddings:** **sentence-transformers** local model (`all-MiniLM-L6-v2`), via `langchain_huggingface`. Accepted recommendation: free, offline, no key. https://www.sbert.net/
- **Vector store:** **Chroma** via `langchain_chroma`, saved to a local folder. Learner choice. https://docs.trychroma.com/
- **Retriever:** plain top-k similarity, **k = 5**. Learner choice. Tradeoff: always returns 5 chunks, even for off-topic questions, so "not found" relies on the prompt.
- **LLM:** **Gemini** via `langchain_google_genai`, API key in a local `.env` (learner creates it). Model name to verify early (planned `gemini-2.5-flash`; unverified, check Google's current model list). https://ai.google.dev/gemini-api/docs
- **Frontend:** **React** with Vite, dev server on port 4000. https://react.dev/ and https://vite.dev/
- Exact library versions are unverified; pin them during build step 1 and check they install together.

## Where It Runs and How Someone Tries It
Runs locally on Windows; requires Python 3.12, Node 24, and a Gemini API key.
- Backend: from `Document_RAG_API`, create a venv, `pip install -r requirements.txt`, put `GOOGLE_API_KEY` in `.env`, run `uvicorn main:app --port 8000`.
- Frontend: from `Document_RAG_APP`, `npm install`, `npm run dev` (port 4000).
- Open `http://localhost:4000`.
- Demo recording: upload a PDF, ask a covered question, ask an uncovered question ("not found in this document"), delete a conversation, delete the PDF. The first run downloads the embedding model (about 90 MB), so do it before recording.
- Deployment: not planned. Submission still needs the demo video and a public GitHub repository (`.env`, `storage/`, and the venv stay out of git).

## Look and Feel
PRD ref: `prd.md > Look and Feel`. Blue and white theme with black text. Clean, minimal, plenty of white space. Plain system sans-serif font (the learner named none). Primary blue for header, buttons, and the chat send arrow; light blue tint for the sidebar. Calm copy. The learner provides the logo (blue bot holding a book), placed in `Document_RAG_APP/src/assets/`. Plain CSS handles all of this.

## Components

### Upload endpoint and chunking
`POST /upload-pdf` receives the file, validates (PDF only, max 40 MB, has text), saves it, calls `chunking/chunking_pdf.py: chunk_pdf(pdf_path)` which returns chunks, stores them, and writes the document record.
PRD ref: `prd.md > Features and Behavior > Upload`.

### Document replace and delete
`GET /document`, `DELETE /document`. A new upload first clears old Chroma data and the old file.
PRD ref: `prd.md > Features and Behavior > Replacing and deleting the PDF`.

### Retrieval and chat
`POST /chat`: retrieve top 5, build the strict grounding prompt (context chunks, last 6 messages, question; rule: use only the context; otherwise reply exactly "not found in this document."), call Gemini, save to the session. Refuses with "no document to search" if none exists.
PRD ref: `prd.md > Features and Behavior > Chat`.

### Sessions
`POST /sessions` (new), `GET /sessions` (visible ones, newest first, with title and timestamp, and a `read_only` flag), `GET /sessions/{id}`, `DELETE /sessions/{id}` (sets `visibility` false). A session is read-only when its `document_id` differs from the current document's.
PRD ref: `prd.md > Features and Behavior > Conversations (sidebar)`.

### Frontend: Upload screen
Drop/pick area, client-side checks, three-dots loader, "this document is invalid."
PRD ref: `prd.md > Screens and Layout`.

### Frontend: Agent screen
`Header` (logo + "Document Agents"), `Sidebar` (collapsible, New chat, conversation rows with delete), `DocumentCard` (PDF icon, hover delete, upload-new), `Chat` (messages, three-dots while waiting, input + arrow), `ConfirmDialog` ("are you sure?"). Read-only sessions disable the input.
PRD ref: `prd.md > Screens and Layout`, `prd.md > States and Boundaries`.

## Data Model
- **`storage/uploads/<file>.pdf`** — the current PDF. Replaced or removed with the document.
- **`storage/chroma/`** — Chroma data for the current document only. Cleared on replace or delete.
- **`storage/document.json`** — `{ "document_id", "filename", "uploaded_at" }`. Absent when no document exists.
- **`storage/sessions/session_<time>_<date>.json`** — `{ "id", "document_id", "created_at", "visibility": true, "messages": [{ "role", "text", "time" }] }`. The title is the first user message. Persists across restarts.
- Browser keeps nothing important; everything is read from the API on reload.

## File Structure
```
Document_rag/
├── Document_RAG_API/
│   ├── main.py                # FastAPI app, routes, CORS
│   ├── chunking/
│   │   └── chunking_pdf.py    # chunk_pdf(pdf_path): PyPDFLoader + RecursiveCharacterTextSplitter
│   ├── rag/
│   │   ├── vectorstore.py     # Chroma + embeddings, add/clear
│   │   └── chat.py            # retrieval (k=5), grounding prompt, Gemini call
│   ├── sessions.py            # read/write session JSON files
│   ├── storage/               # uploads/, chroma/, sessions/, document.json (git-ignored)
│   ├── tests/                 # build-time retrieval/grounding checks
│   ├── requirements.txt
│   └── .env.example           # GOOGLE_API_KEY=
├── Document_RAG_APP/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js             # calls to the API
│   │   ├── components/        # UploadScreen, Header, Sidebar, DocumentCard, Chat, ConfirmDialog
│   │   └── assets/            # logo
│   ├── package.json
│   └── vite.config.js         # dev port 4000
├── devpost/
└── README.md
```

## External Services and Dependencies
- **Gemini API** — called by `langchain_google_genai` `ChatGoogleGenerativeAI`; auth is the `GOOGLE_API_KEY` from `.env`; free-tier rate limits apply (unverified, check). Docs: https://ai.google.dev/gemini-api/docs
- **Hugging Face model download** (one time, for the embedding model). Docs: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- Everything else is local.

## Important Failure Modes
- **Unusable PDF** (not a PDF, over 40 MB, no text, or chunking fails) → "this document is invalid"; nothing stored.
- **Gemini fails** (no key, rate limit, offline) → a short error message in the chat; the user's question stays saved.
- **Off-topic question retrieves 5 weak chunks and the model answers anyway** → mitigated by the strict prompt and tested during the build with questions the document does and does not cover. If it leaks, add a score threshold.
- **Follow-up questions without a rewrite step** → may retrieve poor chunks. Tested during the build.
- **Slow upload on a very large PDF** → the loader covers the wait; measured: 402 pages in about 62 seconds (page loading and embedding dominate).
- **Site cannot reach the API** → "cannot reach the server, please try again" (separate from "this document is invalid").

## What Was Simplified and Why
- **One PDF at a time, local files, no accounts** instead of multi-document, multi-user storage — the PRD requires one document.
- **Plain top-k without a threshold** (learner's choice) — simplest; verified by tests.
- **No question rewrite step** (learner's choice) — fewer model calls.
- **The site sends the PDF to the API as an upload** because a browser page cannot write into a folder on its own; the API saves it and passes the saved path to `chunk_pdf`. This is the same flow you described, with the API doing the saving.
- **No deployment** — local run plus recording.

## Decisions and Open Issues
**Learner decisions:** FastAPI; PyPDFLoader; recursive character chunking (changed from semantic chunking in the build because of upload time); local sentence-transformers; Chroma; plain top-k with k=5; Gemini (API key supplied by the learner); no follow-up rewrite; last 6 messages; `.json` sessions with a `visibility` flag; strict grounding prompt plus build-time test questions.

**Learner uncertainty / agreed investigation:** none named. The follow-up question tradeoff (no rewrite) is the item to check: during the build, ask a follow-up such as "explain that more simply" and record whether retrieval holds up. If it fails, we decide then whether to add the rewrite.

**Implementation details derived by me:** API route names, folder names, `storage/` layout, React with Vite, plain CSS, the embedding model name (`all-MiniLM-L6-v2`).

**Open / to verify early in the build:** current Gemini model name and free-tier limits; that the pinned LangChain packages install together on Python 3.12; the logo file; the exact grounding prompt wording (finalized and tested at build time).
