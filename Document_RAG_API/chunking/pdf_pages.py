"""Tiny worker module: extract text for a range of pages (kept light so worker
processes start fast)."""


def extract_range(args):
    pdf_path, start, end = args
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    out = []
    for i in range(start, end):
        try:
            text = reader.pages[i].extract_text() or ""
        except Exception:
            text = ""
        out.append((i, text))
    return out
