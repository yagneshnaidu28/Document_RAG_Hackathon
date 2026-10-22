"""Saved conversations: one JSON file per conversation in storage/sessions/.

File name: session_<time>_<date>.json, for example session_15-02-11_22-10-2026.json
Fields: id, document_id, created_at, visibility, messages[{role, text, time}]
`visibility` starts true; deleting a conversation sets it to false (the file stays,
the conversation is just no longer listed).
"""
import json
import re
from datetime import datetime, timezone

from rag.vectorstore import STORAGE

SESSIONS_DIR = STORAGE / "sessions"
_ID = re.compile(r"^session_[0-9A-Za-z_-]+$")


def _path(session_id: str):
    if not _ID.match(session_id):
        raise KeyError(session_id)
    return SESSIONS_DIR / f"{session_id}.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create(document_id: str) -> dict:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    base = f"session_{now:%H-%M-%S}_{now:%d-%m-%Y}"
    session_id, n = base, 2
    while (SESSIONS_DIR / f"{session_id}.json").exists():
        session_id, n = f"{base}_{n}", n + 1
    session = {
        "id": session_id,
        "document_id": document_id,
        "created_at": now_iso(),
        "visibility": True,
        "messages": [],
    }
    save(session)
    return session


def load(session_id: str) -> dict:
    """Raises KeyError if it does not exist or is not a valid id."""
    path = _path(session_id)
    if not path.exists():
        raise KeyError(session_id)
    return json.loads(path.read_text(encoding="utf-8"))


def save(session: dict) -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    _path(session["id"]).write_text(
        json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def add_message(session: dict, role: str, text: str) -> None:
    session["messages"].append({"role": role, "text": text, "time": now_iso()})
    save(session)


def title_of(session: dict) -> str:
    for m in session["messages"]:
        if m["role"] == "user":
            return m["text"]
    return "New chat"


def summary(session: dict, current_document_id) -> dict:
    return {
        "id": session["id"],
        "title": title_of(session),
        "created_at": session["created_at"],
        "read_only": session["document_id"] != current_document_id,
    }


def list_visible(current_document_id) -> list[dict]:
    if not SESSIONS_DIR.exists():
        return []
    found = []
    for path in SESSIONS_DIR.glob("session_*.json"):
        try:
            s = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        # a conversation with no messages yet is not worth listing
        if s.get("visibility") is True and s.get("messages"):
            found.append(s)
    found.sort(key=lambda s: s["created_at"], reverse=True)
    return [summary(s, current_document_id) for s in found]


def hide(session_id: str) -> None:
    session = load(session_id)
    session["visibility"] = False
    save(session)
