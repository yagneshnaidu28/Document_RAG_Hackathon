"""Embeddings and the Chroma vector store (one document at a time)."""
import os
import shutil
from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

STORAGE = Path(__file__).resolve().parent.parent / "storage"
CHROMA_DIR = STORAGE / "chroma"
COLLECTION = "document"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embeddings():
    import torch

    torch.set_num_threads(os.cpu_count() or 4)  # torch defaults to half the cores
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL, encode_kwargs={"batch_size": 32}
    )


def get_store() -> Chroma:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def clear_store() -> None:
    """Delete every stored chunk."""
    store = get_store()
    try:
        store.delete_collection()
    except Exception:
        pass
    # release handles, then remove leftovers on disk
    del store
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)


def add_chunks(chunks) -> int:
    clear_store()
    store = get_store()
    store.add_documents(chunks)
    return len(chunks)


def count_chunks() -> int:
    try:
        return get_store()._collection.count()
    except Exception:
        return 0
