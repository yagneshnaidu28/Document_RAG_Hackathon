# Document Agents

Upload a PDF and ask questions that are answered **only from that document**. If the answer isn't in the document, it says **"not found in this document"** instead of guessing.

Built for the Devpost "Build With AI: Basics" hackathon as a proof of concept.

## What it does

- Upload one PDF (PDF only, up to 40 MB). It is read, split into chunks, and stored in a local vector database (Chroma).
- Ask questions in a chat. The app finds the 7 most similar chunks (plain similarity search) and Gemini writes a connected answer from them only.
- Summary-style questions ("give me a summary", "what is this about") use chunks sampled across the whole document.
- Conversations are saved as JSON files, listed in a sidebar (first question + time), and can be continued or deleted.
- Replacing or deleting the PDF makes older conversations read-only, because they belong to a different document.

## How it works

```
React site (port 4000)  -->  FastAPI (port 8000)
                                |-- chunking/chunking_pdf.py   pypdf + heading-aware RecursiveCharacterTextSplitter
                                |-- rag/vectorstore.py         local bge-small embeddings + Chroma
                                |-- rag/chat.py                top-7 similarity retrieval + strict grounding prompt + Gemini
                                |-- sessions.py                saved conversations (storage/sessions/*.json)
```

## Run it

You need **Python 3.12**, **Node 20+**, and a free **Gemini API key** from https://aistudio.google.com/apikey.

### 1. Backend (port 8000)

```powershell
cd Document_RAG_API
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then open .env and paste your key after GOOGLE_API_KEY=
uvicorn main:app --port 8000
```

The first start downloads the embedding model (about 130 MB) and loads it, which takes a few seconds. The API is ready when it prints "Application startup complete".

### 2. Frontend (port 4000)

```powershell
cd Document_RAG_APP
npm install
npm run dev
```

Open http://localhost:4000.

## Try it (demo flow)

1. Upload a PDF (a syllabus or notes file works well). A 20-50 page PDF takes about 10 seconds; a 400-page book takes about 90 seconds.
2. Ask a question the PDF answers. You get an answer drawn from the document.
3. Ask something it doesn't cover ("who won the 2018 World Cup?"). You get **not found in this document**.
4. Click **New chat**, ask another question, then reopen the first conversation from the sidebar and continue it.
5. Delete a conversation (confirm the dialog). Replace the PDF and notice old conversations become read-only.

## Notes

- **Gemini free tier** allows roughly 20 requests per day per model. The chat tries several Gemini models in order (set your own list with `GEMINI_MODELS` in `.env`). If every model is rate-limited you will see a short error message instead of an answer.
- **How documents are split:** structured documents (laws, contracts, syllabi, textbooks) are cut at their headings ("Article 32", "Clause 7", "Unit 2", "Section 4.2") and each piece is labelled, so "what does clause 7 say" works. Documents with no clear headings are split into plain overlapping chunks. The search matches meaning, so telling apart many near-identical numbered sections by number alone (topic 2.3 vs 2.4) can still miss; adding a few words about the topic helps.
- **Scanned PDFs** (images of pages with no text) are not supported; they are reported as "this document is invalid".
- Your key lives only in `Document_RAG_API/.env`, which is git-ignored. Uploaded PDFs, the vector store and conversations live in `Document_RAG_API/storage/` (also git-ignored).
- Retrieval check used during the build: `Document_RAG_API/tests/test_grounding.py` (run `python tests/make_sample_pdf.py sample.pdf`, upload it, then `python tests/test_grounding.py`).
- Planning documents (scope, PRD, spec, build checklist) are in `devpost/`.
