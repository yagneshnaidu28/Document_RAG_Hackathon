"""Retrieval (top-5) and the strict grounded answer."""
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from rag.vectorstore import get_store

K = 5
HISTORY_MESSAGES = 6
NOT_FOUND = "not found in this document"

SYSTEM_PROMPT = f"""You answer questions about ONE document, using ONLY the context excerpts provided.

Rules:
- Use only facts stated in the context excerpts. Never use outside knowledge, never guess, never assume.
- If the context does not clearly contain the answer, reply with exactly: {NOT_FOUND}
- If the question is about something other than the document, reply with exactly: {NOT_FOUND}
- Write the answer as plain text in clear, connected sentences. No citations, no page numbers.
- Earlier chat messages are only for understanding what the question refers to; the facts must still come from the context."""


# Tried in order. The free tier allows only ~20 requests per day per model, so a
# rate-limited or retired model falls through to the next one. Override with
# GEMINI_MODELS="model-a,model-b" in .env.
DEFAULT_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
]


def _models() -> list[str]:
    raw = os.getenv("GEMINI_MODELS", "")
    return [m.strip() for m in raw.split(",") if m.strip()] or DEFAULT_MODELS


def _invoke(messages):
    last_error = None
    for name in _models():
        try:
            return ChatGoogleGenerativeAI(model=name, temperature=0).invoke(messages)
        except Exception as e:  # rate limit, retired model, temporary outage
            last_error = e
    raise last_error


def retrieve(question: str):
    """Plain top-k similarity search over the stored chunks."""
    return get_store().similarity_search(question, k=K)


def answer(question: str, history: list[dict] | None = None) -> str:
    chunks = retrieve(question)
    context = "\n\n---\n\n".join(c.page_content for c in chunks)

    recent = (history or [])[-HISTORY_MESSAGES:]
    chat_so_far = "\n".join(
        f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('text', '')}"
        for m in recent
    )

    user_prompt = (
        f"Context excerpts:\n{context}\n\n"
        f"Earlier messages:\n{chat_so_far or '(none)'}\n\n"
        f"Question: {question}"
    )
    reply = _invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
    )
    text = reply.content if isinstance(reply.content, str) else "".join(
        p.get("text", "") if isinstance(p, dict) else str(p) for p in reply.content
    )
    text = text.strip()
    if NOT_FOUND in text.lower() and len(text) < len(NOT_FOUND) + 40:
        return NOT_FOUND
    return text
