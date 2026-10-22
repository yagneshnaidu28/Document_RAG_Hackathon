"""Retrieval and the strict grounded answer.

Normal questions: plain top-k similarity search (k=5).
Whole-document questions (summary, overview, main topics): a handful of chunks
sampled evenly across the document, because no 5 chunks are "closest" to
"summary of the document".
"""
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from rag.vectorstore import get_store

K = 5
OVERVIEW_CHUNKS = 14
HISTORY_MESSAGES = 6
NOT_FOUND = "not found in this document"
MODEL_TIMEOUT_SECONDS = 30

SYSTEM_PROMPT = f"""You answer questions about ONE document, using ONLY the context excerpts provided.

Rules:
- Use only facts stated in the context excerpts. Never use outside knowledge, never guess, never assume.
- If the context does not clearly contain the answer, reply with exactly: {NOT_FOUND}
- If the question is about something other than the document, reply with exactly: {NOT_FOUND}
- Write the answer as plain text in clear, connected sentences. No citations, no page numbers.
- Earlier chat messages are only for understanding what the question refers to; the facts must still come from the context."""

OVERVIEW_PROMPT = f"""You describe ONE document using ONLY the excerpts provided. The excerpts are sampled evenly from the beginning, middle and end of the whole document.

Rules:
- Summarize what the document is and what it covers, based only on the excerpts. Never add outside knowledge or guess details the excerpts do not show.
- Write clear, connected plain text (short paragraphs or a short list of main topics). No citations, no page numbers.
- If the excerpts are empty or meaningless, reply with exactly: {NOT_FOUND}"""

# Fast model first. Others are slower "thinking" models, kept as fallbacks for
# rate limits (free tier: ~20 requests/day/model) or outages.
# Override with GEMINI_MODELS="model-a,model-b" in .env.
DEFAULT_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
]

OVERVIEW_PATTERN = re.compile(
    r"\b(summar(y|ise|ize|ies)|overview|outline|gist|tl;?dr|"
    r"main (topics?|points?|ideas?|contents?)|key (points?|topics?|takeaways?)|"
    r"table of contents|"
    r"what('?s| is| does) (this|the|that) (document|pdf|file|text|book|syllabus|paper|doc)\b.*"
    r"(about|contain|cover|include|say)|"
    r"about (this|the) (document|pdf|file|book|syllabus|doc)|"
    r"what (information|topics?) (does|is in|are in)|"
    r"tell me about (this|the) (document|pdf|file|book|syllabus|doc))",
    re.IGNORECASE,
)


def _models() -> list[str]:
    raw = os.getenv("GEMINI_MODELS", "")
    return [m.strip() for m in raw.split(",") if m.strip()] or DEFAULT_MODELS


def _invoke(messages):
    """Try each model in turn; a slow, rate-limited or retired one is skipped
    after at most MODEL_TIMEOUT_SECONDS (no long library retries)."""
    last_error = None
    for name in _models():
        try:
            return ChatGoogleGenerativeAI(
                model=name,
                temperature=0,
                max_retries=0,
                timeout=MODEL_TIMEOUT_SECONDS,
            ).invoke(messages)
        except Exception as e:
            last_error = e
    raise last_error


def is_overview_question(question: str) -> bool:
    return bool(OVERVIEW_PATTERN.search(question))


def retrieve(question: str):
    """Plain top-k similarity search over the stored chunks."""
    return get_store().similarity_search(question, k=K)


def sample_whole_document(n: int = OVERVIEW_CHUNKS):
    """n chunks spread evenly over the document, in reading order."""
    data = get_store().get(include=["documents", "metadatas"])
    items = [
        (m.get("page", 0) if m else 0, i, d)
        for i, (d, m) in enumerate(zip(data["documents"], data["metadatas"]))
    ]
    items.sort(key=lambda x: (x[0], x[1]))
    if len(items) <= n:
        return [d for _, _, d in items]
    step = len(items) / n
    return [items[int(i * step)][2] for i in range(n)]


def _text(reply) -> str:
    content = reply.content
    if isinstance(content, str):
        return content.strip()
    return "".join(
        p.get("text", "") if isinstance(p, dict) else str(p) for p in content
    ).strip()


def answer(question: str, history: list[dict] | None = None) -> str:
    if is_overview_question(question):
        excerpts = sample_whole_document()
        system = OVERVIEW_PROMPT
    else:
        excerpts = [c.page_content for c in retrieve(question)]
        system = SYSTEM_PROMPT
    context = "\n\n---\n\n".join(excerpts)

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
    reply = _invoke([SystemMessage(content=system), HumanMessage(content=user_prompt)])
    text = _text(reply)
    if NOT_FOUND in text.lower() and len(text) < len(NOT_FOUND) + 40:
        return NOT_FOUND
    return text
