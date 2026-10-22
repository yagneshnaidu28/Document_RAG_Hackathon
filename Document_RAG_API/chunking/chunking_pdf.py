"""Read a PDF and split it into chunks."""
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


class NoReadableText(Exception):
    """The PDF has no extractable text (for example a scanned PDF)."""


def chunk_pdf(pdf_path: str):
    """Take a PDF path, scrape it page by page, and return chunks.

    Raises NoReadableText if no page has any text.
    """
    pages = PyPDFLoader(pdf_path).load()
    pages = [p for p in pages if p.page_content.strip()]
    if not pages:
        raise NoReadableText("PDF has no readable text")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(pages)
    return [c for c in chunks if c.page_content.strip()]
