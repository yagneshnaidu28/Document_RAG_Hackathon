---
doc: checklist
status: approved
---

# Build Checklist

Build mode: learn

## Slices

- [x] **1. You can upload a PDF and it gets chunked and stored**
  Becomes usable: A running site (port 4000) and API (port 8000). Picking a PDF shows the three-dots loader, then a "ready" message. A bad file shows "this document is invalid." Chunks are saved in Chroma.
  Why now: This is the riskiest unfamiliar part (PyPDFLoader, chunking, local embeddings, Chroma, FastAPI-to-React wiring). Finding problems here is cheap, and it includes all project bootstrapping.
  PRD ref: `prd.md > Features and Behavior > Upload`, `prd.md > The Core Journey` (steps 1-3)
  Spec ref: `spec.md > Components > Upload endpoint and chunking`, `spec.md > File Structure`, `spec.md > Stack`, `spec.md > Data Model`
  Build: Create `Document_RAG_API` (FastAPI, `chunking/chunking_pdf.py`, `rag/vectorstore.py`, `requirements.txt`, `.env.example`) and `Document_RAG_APP` (Vite React on port 4000, UploadScreen). `POST /upload-pdf` validates PDF/40 MB/has text, saves to `storage/uploads/`, chunks, stores in Chroma, writes `document.json`. Measure chunking time on a real PDF.
  Verify (mechanical): Install dependencies; start both servers with no errors; upload a sample PDF through the API and confirm the chunk count in Chroma is above zero and `document.json` exists; upload a non-PDF, an oversized file and a text-less PDF and confirm each is rejected with nothing stored.
  Learner check: Open `http://localhost:4000`, pick a PDF, watch the loader, and see the ready message; then try a non-PDF file and see "this document is invalid."
  Commit: `Add PDF upload, chunking and Chroma storage`

- [x] **2. You can ask a question and get a grounded answer, or "not found in this document"**
  Becomes usable: A basic chat box under the upload that answers from the document using top-5 retrieval and Gemini.
  Why now: This is the unique kernel (answers only from the document). It comes right after upload so the whole idea is provable before any extra screens.
  PRD ref: `prd.md > Features and Behavior > Chat`
  Spec ref: `spec.md > Components > Retrieval and chat`, `spec.md > External Services and Dependencies`, `spec.md > Important Failure Modes`
  Build: Add `rag/chat.py` (k=5 retrieval, strict grounding prompt, last-6-messages memory, Gemini call, exact "not found in this document."), `POST /chat`, and a minimal chat in the site. Add `tests/` with questions the sample PDF does and does not cover, plus a follow-up question. Verify the Gemini model name first.
  Verify (mechanical): Run the test questions: covered ones return answers containing known facts; uncovered ones return exactly "not found in this document."; record how the follow-up question behaves; with the key missing the API returns a clean error.
  Learner check: Ask a question you know the PDF answers, then one it does not cover, and say whether the answers are right and whether the "not found" holds.
  Commit: `Add grounded chat with Gemini and retrieval tests`

- [x] **3. You get the full agent screen: header, PDF card, replace and delete**
  Becomes usable: The agent screen layout with the logo header, the PDF icon card (hover delete with "are you sure?", upload a new PDF), the no-document state, and the chat in place.
  Why now: Puts the kernel inside the product's real layout and covers the document lifecycle before conversations depend on it.
  PRD ref: `prd.md > Screens and Layout`, `prd.md > Features and Behavior > Replacing and deleting the PDF`
  Spec ref: `spec.md > Components > Document replace and delete`, `spec.md > Components > Frontend: Agent screen`
  Build: Add `GET /document` and `DELETE /document`; replace-on-upload clears old Chroma data and file; add Header, DocumentCard, ConfirmDialog; route between upload and agent screens automatically.
  Verify (mechanical): Upload A then B and confirm only B's chunks remain and answers come from B; delete the document and confirm Chroma, the file and `document.json` are gone and `/chat` refuses with "no document to search"; the site builds without errors.
  Learner check: Upload a PDF, land on the agent screen, hover the PDF icon and delete it (confirming), see the no-document message, then upload another and ask a question.
  Commit: `Add agent screen with document replace and delete`

- [x] **4. Conversations are saved, listed, continued, and deleted**
  Becomes usable: A collapsible sidebar with New chat, past conversations (first question as title, timestamp), click to continue, per-conversation delete with confirmation, and read-only history for old documents.
  Why now: It depends on the chat and the document lifecycle, and it is the last big behavior in the PRD.
  PRD ref: `prd.md > Features and Behavior > Conversations (sidebar)`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Components > Sessions`, `spec.md > Components > Frontend: Agent screen`, `spec.md > Data Model`
  Build: Add `sessions.py` and the session routes (create, list, get, delete via `visibility`); save messages on each chat; add Sidebar; mark sessions read-only when `document_id` differs; disable input for read-only sessions.
  Verify (mechanical): Via API: create a session, chat, list it with the correct title and timestamp, restart the server and confirm it persists, delete it and confirm it no longer lists but its file shows `visibility: false`; replace the document and confirm the old session reports `read_only`.
  Learner check: Ask two questions, start a new chat, reopen the first from the sidebar and continue it, delete one (confirming), replace the PDF and see the old chat can no longer be continued.
  Commit: `Add saved conversations with sidebar and read-only history`

- [x] **5. It looks like your design and handles the awkward cases**
  Becomes usable: Blue-and-white minimal styling with your logo, the three-dots waiting indicators, clear error messages, and a README with start steps for the demo.
  Why now: Styling and edge cases come last so they polish working behavior; the README makes the repo and recording easy.
  PRD ref: `prd.md > Look and Feel`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Look and Feel`, `spec.md > Important Failure Modes`, `spec.md > Where It Runs and How Someone Tries It`
  Build: Apply the palette and plain font, add the logo, the waiting indicator in chat, a short error message when Gemini fails, the empty states, and a README with setup and run steps.
  Verify (mechanical): Production build of the site succeeds; run the full journey end to end (upload, covered question, uncovered question, delete conversation, delete PDF); with a bad API key the chat shows an error message and nothing crashes.
  Learner check: Run the full demo flow as you'd record it and say what feels off in the look, wording or flow.
  Commit: `Apply design, error states and README`

## Hands-on Checkpoints

- [x] Early usable behavior explored — after slice 2 (grounded chat working)
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: 
Route and stops: 
Edit outcome: 
Reflection: 
Activity mode: 

## Revisions
- Chunking changed from SemanticChunker to RecursiveCharacterTextSplitter — semantic chunking took over 4 minutes on a 402-page PDF (it embeds every sentence on the CPU); the learner chose to switch, and the same file now uploads in about 62 seconds.
- The upload screen now shows "cannot reach the server" for a network failure instead of "this document is invalid" — a stopped API was mistaken for an invalid document during testing.
- Gemini model: `gemini-2.5-flash` returns 404 for this key, and the free tier allows 20 requests per day per model — the chat now falls back across several Gemini models in order (still Gemini, learner's choice unchanged).
- Until slice 4 adds saved sessions, `POST /chat` takes the last messages from the request (`history`) instead of a session id — the site keeps the conversation in memory for now.
- Build-time retrieval test: 5/5 covered questions answered correctly and 5/5 uncovered returned exactly "not found in this document". Follow-up check: "Which one is biggest?" works, but "Explain that more simply" returns "not found in this document" because the question is searched as typed (the tradeoff the learner accepted); revisit adding a rewrite step if it matters.
- Layout restyled to match the learner's reference screenshot: logo and name move into the sidebar (no top header band), upload becomes a dashed drop box with drag and drop, the PDF row shows chunk count and upload time with an always-visible delete button, and the chat gets a centered prompt and rounded input bar. Multiple-document selector, select-all, voice input and suggestion chips from the reference were left out as new features. `prd.md` and `spec.md` updated to match.
- Upload speed tuned at the learner's request: a 402-page PDF went from 62 s to about 35-42 s and no longer waits for the model to load on the first upload. Model preloaded at server start; pypdf page reading parallelised for PDFs of 40+ pages; torch uses all cores; upload work moved off the server's main loop. ONNX and bfloat16 gave no gain, so embedding speed is the remaining floor.
- Chat fixed after the learner reported "not found" for "give me summary of document" and slow answers: summary/overview questions now use chunks sampled evenly across the whole document (top-5 similarity returned unrelated chunks for them); the fast `gemini-3.5-flash-lite` is tried first with a 30 s timeout and no retries (answers about 2 s instead of 15-25 s; the slower thinking models are fallbacks). Normal questions still use plain top-5 similarity as the learner chose.
- Retrieval changed from plain top-5 similarity to a hybrid (embedding + BM25 keyword, merged, best 8, plus the following chunk when a match is cut mid-sentence) — on the learner's 402-page Constitution PDF, embeddings alone could not find article numbers ("what was article 373 about" returned chunks about articles 306, 342, 370, 371D). Verified: Articles 14, 17, 21, 24, 373 answered correctly, off-topic questions still return "not found in this document", and the keyword index resets when the document changes. Learner informed.
- Slice 4: `POST /chat` now takes `session_id` and loads the last 6 messages from the saved session (replacing the temporary `history` sent by the page in slice 2); a failed answer still keeps the saved question and returns the session id so the page stays attached to its conversation.
- Slice 5: the upload box and PDF row now sit side by side and are slimmer (the chat was cramped in the learner's screenshot); dependency versions pinned in `requirements.txt` (`langchain-experimental` dropped, `langchain-text-splitters` added after the chunking switch); an invalid Gemini key now fails in about 1 s instead of trying every fallback model; README added with setup, demo flow and notes.
- Retriever size set to the top 7 matches at the learner's request (was 5, then 8 with the hybrid search); the code, spec and README now say 7.
- Retriever switched to plain similarity search, top 7, at the learner's decision after a side-by-side test on their Constitution PDF (similarity found the answer chunk for 8 of 10 questions, the hybrid for 10 of 10; similarity misses lookups by article number). The keyword search code was removed. "explain me article 457" returning "not found in this document" was correct: the Constitution ends at Article 395 and 457 appears nowhere in the PDF.
- Search quality rebuilt after the learner reported "not found" for article questions ("what article 32 says") and asked to re-chunk: tested four chunkings and three embedding models on a 402-page Constitution PDF with 14-20 questions. Re-chunking alone did not help (4-5 of 14 with MiniLM). Heading-aware chunks labelled "Article N." plus the bge-small-en-v1.5 embedding model gave 18 of 20 with plain top-7 similarity (retriever unchanged, still similarity only). Schedule lists and amendment footnotes had been mislabelled as articles (e.g. "Article 44" from a schedule item); fixed by keeping only "Title.-Body" headings in rising order. Cost: uploads about 90 s for 400 pages. Two short number-only questions still miss ("what does article 23 says", "article 17"). "explain me article 457" returning "not found" was correct (the Constitution ends at Article 395).
- Chunking generalised at the learner's request ("should work for all documents, not just the current one"): the first version was tuned to the Constitution (a legal-footnote word list, a "Title.-Body" check) and could not see decimal headings (1.1, 2.3.1) or keyword headings (Chapter 3, UNIT 2, Section 4, Week 5). Rewritten to recognise numbered and keyword headings in any document, with safeguards and a plain-splitter fallback. Tested with generated PDFs in five styles (contract, syllabus, textbook, lecture notes, report; small and large versions): heading-aware chunking scored 57/60 versus 48/60 for plain chunking, and on the Constitution 19/22. Two bugs found by the tests and fixed: label-only headings ("Unit 10.") became chunks that outranked their content (now merged into the next section), and short numbered items were being dropped (now kept). Remaining weakness: near-identical numbered sections told apart only by a decimal number (topic 2.3 vs 2.4).
