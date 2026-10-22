"""Create a small sample syllabus PDF for testing (known facts)."""
import sys
from pathlib import Path

from pypdf import PdfWriter  # noqa: F401  (ensures pypdf is installed)

TEXT = [
    "Introduction to Marine Biology - Course Syllabus",
    "The course is taught by Dr. Alma Reyes and runs for twelve weeks.",
    "Week 1 covers ocean zones: the sunlit epipelagic zone reaches 200 metres deep. "
    "Below it the mesopelagic zone, also called the twilight zone, reaches 1000 metres.",
    "Week 2 covers coral reefs. Reefs are built by tiny animals called polyps, "
    "which live in partnership with algae named zooxanthellae.",
    "Week 3 covers tides. Spring tides happen at new and full moon, "
    "when the sun and moon line up with the earth.",
    "Grading: lab reports are worth 40 percent, the midterm exam 25 percent, "
    "and the final exam 35 percent.",
    "Late work loses 10 percent per day. Attendance is not graded.",
]


def make(path: str) -> None:
    # Minimal hand-written PDF with real text (no extra libraries needed).
    lines = []
    y = 760
    for t in TEXT:
        words, row = t.split(), ""
        for w in words:
            if len(row) + len(w) > 85:
                lines.append((y, row)); y -= 16; row = ""
            row += (w + " ")
        lines.append((y, row)); y -= 24
    stream = "BT /F1 11 Tf\n"
    for ypos, text in lines:
        safe = text.replace("(", "[").replace(")", "]")
        stream += f"1 0 0 1 40 {ypos} Tm ({safe}) Tj\n"
    stream += "ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = "%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n"
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    Path(path).write_bytes(out.encode("latin-1"))


if __name__ == "__main__":
    make(sys.argv[1] if len(sys.argv) > 1 else "sample_syllabus.pdf")
    print("created")
