---
doc: prd
status: approved
---

# Document Agents — Product Requirements

A clean, minimal web app where a student uploads one PDF and asks questions that are answered only from that document.
Source: `scope.md > The Unique Kernel`, `scope.md > The Core Loop`, `scope.md > What "Working" Looks Like`.

## The Core Journey
1. The user opens the app (local frontend, port 4000) and sees an upload screen that accepts PDFs only.
2. They choose a PDF (max 40 MB). The screen shows a loading indicator: three dots moving left to right.
3. If the file is valid, it is processed and the app moves to the agent screen. If not, the screen says "this document is invalid."
4. On the agent screen the uploaded PDF appears as an icon, and the chat is ready.
5. The user types a question and presses Enter (or the arrow). The agent answers using only the document, as plain text.
6. If the document doesn't contain the answer, the reply is "not found in this document."
7. The conversation appears in the sidebar and can be continued later. Success is a correct answer from the document and a "not found" for something it doesn't cover.

## Screens and Layout
Two screens.

**Upload screen** (first visit, or when no document exists): an upload area for a PDF. Shows the loading indicator while the PDF is processed, and "this document is invalid" for unusable files.

**Agent screen:**
- **Header:** the logo on the left (provided by the learner; a blue bot holding a book) and the heading "Document Agents" in the middle (h5 or h6, whichever looks right).
- **Left sidebar:** collapsible (open/close). At the top is a "New chat" button. Below it is the list of past conversations. Each row shows the conversation's first question as its title, plus a timestamp, and has its own delete button.
- **Document area:** to the right of the sidebar and below the header, one component showing the uploaded PDF as an icon (not the document's contents). Hovering the icon reveals a delete button. A way to upload a new PDF is also here.
- **Chat:** below the document component. The conversation fills the area, and the input bar with an Enter arrow sits at the bottom.

## Look and Feel
- Blue and white theme; black text.
- Clean, clear, minimal.
- Logo: a bot/agent holding a book, in blue (supplied by the learner).
- Font character: not specified; a clean, plain font is assumed.

## Features and Behavior

### Upload
- Accepts PDF only, max 40 MB.
- Shows a moving three-dots loader while uploading and chunking.
- On an unusable file (not a PDF, over 40 MB, no readable content), shows "this document is invalid."
- Only one PDF exists at a time.
  - [ ] A valid PDF leads to the agent screen automatically.
  - [ ] A non-PDF, an oversized PDF, or an unreadable one shows "this document is invalid" and nothing is stored.

### Replacing and deleting the PDF
- Uploading a new PDF from the agent screen removes the previous document's chunks, builds the new ones, and the agent switches to the new document automatically.
- Hovering the PDF icon reveals a delete button. It asks "are you sure?" before deleting.
- After deletion no document exists: the chat shows that there is no document to search, and the user can upload a new one.
  - [ ] After replacing, questions are answered from the new PDF only.
  - [ ] After deleting, asking a question is not possible; the screen says there is no document to search.

### Chat
- The user asks a question; the agent retrieves the most similar parts of the document and writes a connected, plain-text answer (no citations or page numbers).
- If the answer isn't in the document, the reply is "not found in this document."
  - [ ] A question covered by the document gets an answer drawn from it.
  - [ ] A question the document doesn't cover gets "not found in this document," not a guess.

### Conversations (sidebar)
- "New chat" starts a fresh conversation.
- Clicking a past conversation opens it on screen, and the user can continue it.
- Each conversation has its own delete button with an "are you sure?" confirmation; a deleted conversation disappears from the list.
- Conversations about a previous document stay in the list but are read-only: they can't be continued once that document is deleted or replaced.
  - [ ] The title is the first question; a timestamp is shown.
  - [ ] Deleting a conversation removes it from the list after confirmation.
  - [ ] An old conversation from a deleted/replaced document opens but cannot be continued.
  - [ ] The sidebar can be opened and closed.

## States and Boundaries
- **First use / no document** — upload screen; on the agent screen, "no document to search."
- **Processing** — three moving dots.
- **Invalid file** — "this document is invalid."
- **Persistence** — conversations are saved and still listed after reopening; a deleted conversation is hidden from the list (saved with a visibility flag, initially true; delete turns it off).
- **Waiting for an answer** — assumption: a similar three-dots indicator in the chat.
- **Answer failure (e.g. backend down)** — assumption: a short error message in the chat. Not decided by the learner.

## Product Decisions
- Grounded answers only, with "not found in this document" fallback — avoids hallucination, the kernel.
- No citations or page numbers — keep answers plain.
- One PDF at a time; a new upload replaces everything — simple, no multi-document handling.
- Old conversations stay read-only after their document goes — preserves history without answering from the wrong document.
- Confirmation before every delete — prevent accidents.
- Everything described is in the POC (learner's decision in scope).

## What We're Building
Upload (PDF, 40 MB), loading and invalid states, agent screen (header, collapsible sidebar, PDF component, chat), replace/delete PDF, grounded Q&A with "not found" fallback, saved conversations with delete and read-only history.

## Deferred From the POC
- Pasting text instead of uploading a PDF — not in the demo flow.
- Citations / page numbers — kept plain for now.
- Automatic document overview — only on request as a query.

## Possible Later Enhancements
Multiple documents at once; renaming conversations.

## Non-Goals
- No guessing from general knowledge.
- No user accounts or sharing.

## Open Questions
- Session file format (`.json` vs `.md`) and the exact visibility value — can be settled in `4-spec` (technical).
- Answer-waiting and answer-failure display are assumptions; confirm at review.
- Whether the three-dot loader style is final, and the logo file location — before build.
