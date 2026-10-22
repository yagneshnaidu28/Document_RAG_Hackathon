"""Build-time check of retrieval + grounding.

Run with the sample syllabus (made by make_sample_pdf.py) as the current document:
    python tests/test_grounding.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from rag.chat import NOT_FOUND, answer  # noqa: E402

COVERED = [
    ("Who teaches the course?", ["reyes"]),
    ("How deep is the twilight zone?", ["1000"]),
    ("What percent is the midterm worth?", ["25"]),
    ("What are coral reefs built by?", ["polyp"]),
    ("What is the penalty for late work?", ["10"]),
]
UNCOVERED = [
    "Who won the football world cup in 2018?",
    "What is the capital of France?",
    "How do I bake a chocolate cake?",
    "What is the syllabus for organic chemistry?",
    "Explain how photosynthesis works.",
]

failures = 0
print("== covered questions ==")
for q, keys in COVERED:
    a = answer(q)
    ok = all(k in a.lower() for k in keys)
    failures += not ok
    print("PASS" if ok else "FAIL", "|", q, "->", a[:100].replace("\n", " "))

print("== uncovered questions (must be exactly: %s) ==" % NOT_FOUND)
for q in UNCOVERED:
    a = answer(q)
    ok = a == NOT_FOUND
    failures += not ok
    print("PASS" if ok else "FAIL", "|", q, "->", a[:100].replace("\n", " "))

print("== follow-up (informational, not pass/fail) ==")
hist = [
    {"role": "user", "text": "How are grades split?"},
    {"role": "assistant", "text": "Lab reports 40 percent, midterm 25 percent, final 35 percent."},
]
for q in ["Explain that more simply", "Which one is biggest?"]:
    print("-", q, "->", answer(q, hist)[:120].replace("\n", " "))

print("\nfailures:", failures)
sys.exit(1 if failures else 0)
