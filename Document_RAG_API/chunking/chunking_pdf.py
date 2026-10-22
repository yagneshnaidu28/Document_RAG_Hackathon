"""Read a PDF and split it into chunks.

Documents made of numbered parts ("32. Remedies for ...", "Article 32", "Section 4")
are split at those numbered headings and every piece is labelled with the
document's own word for them ("Article 32."), so that a question like
"what does article 32 say" can find it by similarity. Documents without
numbered headings use a plain recursive splitter.
"""
import os
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chunking.pdf_pages import extract_range

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
PARALLEL_FROM_PAGES = 40  # below this, one process is faster than starting workers
MIN_HEADINGS = 10  # fewer numbered headings than this: not a numbered document
MIN_BODY_CHARS = 60  # drops heading-only entries such as table-of-contents lines

# a line that starts like "32. Remedies ..." or "51A. Fundamental duties"
# (also "1[21A. Right to ..." where a footnote marker sits in front of the number)
HEADING = re.compile(r"""(?m)^\s*(?:\d{1,2}\[+)?(\d{1,3}[A-Z]{0,2})\.\s+(?=[A-Z\[“"'])""")
# "Short title.-Body": a short title, a full stop, then a dash. Some PDFs lose the
# dash character, so the Unicode replacement character counts too.
DASH_STYLE = re.compile(r"[^.]{1,200}\.\s*[—–\-�]")
# numbered amendment notes and similar, not real headings
NOTE_START = re.compile(
    r"\s*(Ins|Subs|Added|Omitted|Rep|Renumbered|Re-numbered|Cl|Clause|Sub-clause|The words|See|Cf|Ibid)\b"
)
STYLED_MIN = 40  # this many "Title.-Body" headings (or STYLED_SHARE of all) means the document uses that style
STYLED_SHARE = 0.3
MAX_JUMP = 60  # largest step up in heading number between neighbouring headings
# how documents refer to their numbered parts: "article 21", "section 4", ...
REFERENCE_WORDS = re.compile(
    r"\b(article|section|clause|chapter|rule|regulation|unit|lesson|topic|part|item)s?\s+\d",
    re.IGNORECASE,
)


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


def _label_word(text: str) -> str:
    """The word this document uses for its numbered parts (most common wins)."""
    counts = Counter(m.group(1).lower() for m in REFERENCE_WORDS.finditer(text))
    return (counts.most_common(1)[0][0] if counts else "section").capitalize()


def _only_rising(marks):
    """Real headings count upward through the text (1, 2, ... 21, 21A, 22 ...).
    A number that falls back or jumps far ahead is a list item or a note."""
    kept, last = [], 0
    for m in marks:
        value = int(re.match(r"\d+", m.group(1)).group())
        if last <= value <= last + MAX_JUMP:
            kept.append(m)
            last = value
    return kept


def _find_headings(text: str):
    marks = [
        m
        for m in HEADING.finditer(text)
        if not NOTE_START.match(text[m.end() : m.end() + 14])
    ]
    # If the document writes its headings as "Title.-Body", keep only those: numbered
    # lists, schedules and footnotes would otherwise be mistaken for headings.
    styled = [m for m in marks if DASH_STYLE.match(text[m.end() : m.end() + 260])]
    if len(styled) >= STYLED_MIN or (marks and len(styled) >= STYLED_SHARE * len(marks)):
        return _only_rising(styled)
    return marks


def _split_by_headings(pages, source):
    """Returns labelled chunks, or None when the document has no numbered headings."""
    text = "\n".join(p.page_content for p in pages)
    marks = _find_headings(text)
    if len(marks) < MIN_HEADINGS:
        return None

    word = _label_word(text)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    sections = []
    if marks[0].start() > 0:
        sections.append((None, text[: marks[0].start()]))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        sections.append((m.group(1), text[m.start() : end]))

    chunks = []
    for number, body in sections:
        body = body.strip()
        if not body:
            continue
        pieces = splitter.split_text(body) if len(body) > CHUNK_SIZE else [body]
        for j, piece in enumerate(pieces):
            if number is None:
                label = ""
            elif j == 0:
                label = f"{word} {number}. "
            else:
                label = f"{word} {number} (continued). "
            # a heading with nothing under it (table-of-contents line) is noise
            if number is not None and j == 0 and len(piece) < MIN_BODY_CHARS + len(number) + 4:
                continue
            chunks.append(Document(page_content=label + piece, metadata={"source": source}))
    return chunks


def chunk_pdf(pdf_path: str):
    """Take a PDF path, scrape it page by page, and return chunks.

    Raises NoReadableText if no page has any text.
    """
    pages = [p for p in _load_pages(pdf_path) if p.page_content.strip()]
    if not pages:
        raise NoReadableText("PDF has no readable text")

    chunks = _split_by_headings(pages, pdf_path)
    if not chunks:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(pages)
    chunks = [c for c in chunks if c.page_content.strip()]
    if not chunks:
        raise NoReadableText("PDF has no readable text")
    return chunks
