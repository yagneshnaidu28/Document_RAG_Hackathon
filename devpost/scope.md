---
doc: scope
status: approved
---

# Document Q&A Agent

A web app where you upload a PDF and ask questions that are answered only from that document, never from the model's general knowledge.

## The Unique Kernel
Grounded answers only. The agent answers from its own knowledge base (the chunks of the uploaded PDF), so there are no assumptions or hallucinations like a general chatbot might produce. If the answer isn't in the document, it says "not found in this document."

## Who It's For
A student (mostly) or an ordinary person holding a document of hundreds of pages, such as a syllabus, subject notes, a bill or a constitution. They need two or three things from it. Today they read page by page to find topics, questions and answers.

## The Core Loop
Upload a PDF, then ask a question. The agent retrieves the most similar chunks (top-k similarity search) and writes a connected answer from them. They come back to ask the next doubt. There is no automatic overview; if they want one, they ask for it as a query.

## Inspiration & Identity
Not established. Volunteered direction: simple, local-hosted React UI.

## Why This Matters to the Learner
Learning how to work with an agent and steer it until it meets the real need by the end. They've built basic RAG and four agents before, and now want to build this one with deliberate choices at every step.

## What "Working" Looks Like
The demo: open the frontend on localhost (port 4000). Upload a PDF (PDF only, max 40 MB). It is saved to a folder and its path is sent to the backend. The backend chunks it and saves the chunks to a vector DB, then returns `true`. The frontend moves to the agent screen, which shows past conversations and the uploaded PDF (deletable by a button). The user asks a question and gets an answer built from retrieved chunks, as plain text with no citations. If the document doesn't contain the answer, the reply is "not found in this document." Conversations are saved in a `sessions` folder as `session_<time>_<date>` files holding the full conversation, each with a `visibility` flag. It starts "true"; pressing delete in the UI sets it to hidden and the UI no longer shows that conversation.
The "oh, that's cool" beat: asking something the document doesn't cover and getting "not found in this document" instead of a guess.

## The POC Boundary
In (learner's decision: everything described is in the proof of concept):
- PDF upload UI (PDF only, 40 MB max), saved to a folder, path sent to the backend
- Backend upload endpoint, then chunking, then vector DB storage, then a success flag
- Agent screen: chat, past conversations list, uploaded PDF with delete button
- Retrieval (top-k similarity) and a grounded, connected answer; "not found in this document" fallback
- Sessions saved to files with a visibility flag; delete hides a conversation

## Later
- Pasting text instead of uploading a PDF (mentioned in the original idea; not in the demo flow)
- Citations / page numbers in answers
- Automatic document overview

## Explicitly Cut
Nothing cut yet. Note: this is a lot for 2–4 hours, so the build may need to simplify within these items.

## Open Items
- Session file format: `.json` vs `.md` (learner mentioned both).
- Delete value: described as "false" and "off" (to settle in PRD).
