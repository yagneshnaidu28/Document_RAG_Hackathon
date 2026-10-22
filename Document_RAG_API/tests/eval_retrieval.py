"""Measure retrieval on the document that is currently loaded in the app.

For each question you know the answer to, check whether the text that holds the
answer is among the top-7 chunks the search returns. No Gemini calls, no quota.

    python tests/eval_retrieval.py tests/questions_constitution.json

The questions file is a list of {"q": "...", "expect": "..."}: `expect` is a short
phrase that appears in the document right where the answer is (lower case is fine).
Upload the PDF in the app first. Run this before and after a change (chunking,
embedding model, retriever) to see whether it actually helped.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.chat import K, retrieve  # noqa: E402


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def main(path: str) -> int:
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    found = 0
    for case in cases:
        chunks = retrieve(case["q"])
        hit = any(norm(case["expect"]) in norm(c) for c in chunks)
        found += hit
        print(("FOUND  " if hit else "missed ") + "| " + case["q"])
    print(f"\n{found}/{len(cases)} questions have their answer in the top {K} chunks")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
