"""Read a PDF and split it into chunks."""
import os
from concurrent.futures import ProcessPoolExecutor

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chunking.pdf_pages import extract_range

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
PARALLEL_FROM_PAGES = 40  # below this, one process is faster than starting workers


class NoReadableText(Exception):
    """The PDF has no extractable text (for example a scanned PDF)."""


def _load_pages(pdf_path: str):
    """Read page text with pypdf. Big PDFs are read in parallel, one slice of
    pages per CPU core; small ones use LangChain's PyPDFLoader directly."""
    from pypdf import PdfReader

    n_pages = len(PdfReader(pdf_path).pages)
    if n_pages < PARALLEL_FROM_PAGES:
        return PyPDFLoader(pdf_path).load()

    workers = max(2, min(os.cpu_count() or 2, 8))
    step = -(-n_pages // workers)
    ranges = [(pdf_path, s, min(s + step, n_pages)) for s in range(0, n_pages, step)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        parts = list(pool.map(extract_range, ranges))
    return [
        Document(page_content=text, metadata={"source": pdf_path, "page": i})
        for part in parts
        for i, text in part
    ]


def chunk_pdf(pdf_path: str):
    """Take a PDF path, scrape it page by page, and return chunks.

    Raises NoReadableText if no page has any text.
    """
    pages = [p for p in _load_pages(pdf_path) if p.page_content.strip()]
    if not pages:
        raise NoReadableText("PDF has no readable text")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(pages)
    return [c for c in chunks if c.page_content.strip()]
