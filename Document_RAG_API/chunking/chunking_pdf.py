"""Read a PDF and split it into chunks.

Structured documents (laws, contracts, syllabi, textbooks) are split at their
headings, and every piece starts with its heading label ("Article 32.",
"Unit 2.", "Section 4.2."), so a question such as "what does article 32 say"
or "what is covered in unit 2" can be matched by similarity. Documents with
no clear headings use a plain recursive splitter.

Recognised headings (nothing here is specific to one document):
  - numbered:  "32. Title", "5) Title", "51A. Title", "2.3 Title", "2.3.1 Title"
  - keyword:   "Chapter 3: Title", "UNIT 2 - Title", "Section 4. Title", "Week 5"
"""
import os
import re
import statistics
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chunking.pdf_pages import extract_range

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
PARALLEL_FROM_PAGES = 40  # below this, one process is faster than starting workers

MIN_HEADINGS = 5  # fewer headings than this: use the plain splitter
MIN_KEYWORD_HEADINGS = 3  # keyword headings ("Unit 2") are rarer, so a lower bar
SHORT_BODY = 60  # a section with less text than this is "short"
TOC_RUN = 5  # this many short sections in a row look like a table of contents
MIN_MEDIAN_CHARS = 100  # median chunk shorter than this: the headings were not real

# "32. Title", "5) Title", "51A. Title" (also "1[21A. Title" with a footnote mark)
# and decimal "2.3 Title", "2.3.1 Title".
NUMBERED = re.compile(
    r"""(?mx)^[ \t]*(?:\d{1,2}\[+)?
        (?:(\d{1,3}[A-Z]{0,2})[.)]|(\d{1,3}(?:\.\d{1,3})+)\.?)
        [ \t]+(?=[A-Z\[“"'])"""
)
# "Chapter 3: Title", "UNIT 2 - Title", "Section 4. Title", "Week 5" (nothing else on the line)
KEYWORD = re.compile(
    r"(?mi)^[ \t]*(article|section|clause|chapter|unit|lesson|module|part|topic|week|rule|"
    r"regulation|lecture|session|appendix|schedule)[ \t]+(\d{1,3}[A-Za-z]?|[IVXLC]{1,6})\b"
    r"(?=[ \t]*(?:[:.\-–—)]|$))"
)
# "Short title.-Body": some documents (statutes) write every heading this way
DASH_STYLE = re.compile(r"[^.]{1,200}\.\s*[—–\-�]")
# numbered amendment notes, not headings
NOTE_START = re.compile(
    r"\s*(?:Ins\.|Subs\.|Rep\.|Added by|Omitted|Renumbered|Re-numbered|Inserted by|Substituted by)"
)
STYLED_MIN = 40  # this many "Title.-Body" headings (or STYLED_SHARE of all) means the document uses that style
STYLED_SHARE = 0.3
MAX_JUMP = 60  # in that style, the largest step up in number between neighbouring headings
# how documents refer to their own numbered parts: "article 21", "section 4", ...
REFERENCE_WORDS = re.compile(
    r"\b(article|section|clause|chapter|rule|regulation|unit|lesson|topic|item)s?\s+\d",
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
    """In 'Title.-Body' documents real headings count upward through the text
    (1, 2, ... 21, 21A, 22 ...). A number that falls back or jumps far ahead is a
    list item or note."""
    kept, last = [], 0
    for m in marks:
        value = int(re.match(r"\d+", m[1]).group())
        if last <= value <= last + MAX_JUMP:
            kept.append(m)
            last = value
    return kept


def _find_headings(text: str):
    """Returns [(start_position, label, kind)] in reading order, e.g.
    (120, "Article 32", "numbered") or (40, "Unit 2", "keyword")."""
    numbered = []
    for m in NUMBERED.finditer(text):
        if NOTE_START.match(text[m.end() : m.end() + 16]):
            continue
        token = m.group(1) or m.group(2)
        numbered.append((m.start(), token, m.end()))
    styled = [h for h in numbered if DASH_STYLE.match(text[h[2] : h[2] + 260])]
    if len(styled) >= STYLED_MIN or (numbered and len(styled) >= STYLED_SHARE * len(numbered)):
        numbered = _only_rising([(s, t, e) for s, t, e in styled])

    # a real heading is capitalised ("Chapter 3", "UNIT 2"); a lower-case "article 368."
    # at the start of a wrapped line is just a reference inside a sentence
    keyword = [
        (m.start(), f"{m.group(1).capitalize()} {m.group(2).upper()}", "keyword")
        for m in KEYWORD.finditer(text)
        if m.group(1)[0].isupper()
    ]
    if len(keyword) < MIN_KEYWORD_HEADINGS:
        keyword = []

    word = _label_word(text)
    taken = {pos for pos, _, _ in keyword}
    merged = [
        (pos, f"{word} {tok}", "numbered") for pos, tok, _ in numbered if pos not in taken
    ]
    return sorted(merged + keyword)


def _split_by_headings(pages, source):
    """Returns labelled chunks, or None when the document has no reliable headings."""
    text = "\n".join(p.page_content for p in pages)
    headings = _find_headings(text)
    if len(headings) < MIN_HEADINGS:
        return None

    sections = []  # (label or "", body, kind)
    if headings[0][0] > 0:
        sections.append(("", text[: headings[0][0]].strip(), ""))
    for i, (pos, label, kind) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else len(text)
        sections.append((label, text[pos:end].strip(), kind))

    # A long run of short sections is a table of contents: keep its text (nothing
    # is lost) but without heading labels, so it does not pose as the real sections.
    short = [len(b) < SHORT_BODY + len(l) for l, b, _ in sections]
    i = 0
    while i < len(sections):
        if short[i] and sections[i][0]:
            j = i
            while j < len(sections) and short[j] and sections[j][0]:
                j += 1
            if j - i >= TOC_RUN:
                joined = "\n".join(b for _, b in sections[i:j])
                sections[i:j] = [("", joined)] + [("", "")] * (j - i - 1)
            i = j
        else:
            i += 1

    # A heading with hardly any text under it ("UNIT 2: Genetics" right before "2.1 ...")
    # is merged into the section that follows, so it travels with real content instead
    # of becoming a label-only chunk that outranks the content. Its words stay in the
    # text; a parent such as "Unit 2" is not repeated in the label of every child.
    merged, carry = [], None  # carry = (label, body, kind)
    for k, (label, body, kind) in enumerate(sections):
        if not body:
            continue
        own_short = bool(label) and len(body) < SHORT_BODY + len(label)
        if carry:
            c_label, c_body, c_kind = carry
            if label and c_kind == "numbered":
                label = f"{c_label}, {label}"  # "Article 52, Article 53": both stay findable
            elif not label:
                label = c_label
            body, carry = c_body + "\n" + body, None
        if own_short and k < len(sections) - 1:
            carry = (label, body, kind)
            continue
        merged.append((label, body))
    if carry:
        merged.append((carry[0], carry[1]))
    sections = merged

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = []
    for label, body in sections:
        if not body:
            continue
        pieces = splitter.split_text(body) if len(body) > CHUNK_SIZE else [body]
        for j, piece in enumerate(pieces):
            if not label:
                prefix = ""
            elif j == 0:
                prefix = f"{label}. "
            else:
                prefix = f"{label} (continued). "
            chunks.append(Document(page_content=prefix + piece, metadata={"source": source}))

    if not chunks or statistics.median(len(c.page_content) for c in chunks) < MIN_MEDIAN_CHARS:
        return None  # the "headings" were really list items or notes
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
