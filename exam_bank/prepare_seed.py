"""Extract teacher review material from local PDFs; output is private import data.

Usage: python prepare_seed.py PAPER.pdf MARK_SCHEME.pdf output.json
Requires pdfplumber. The resulting JSON contains source page text and must not
be committed to the public repository.
"""

import hashlib
import json
import sys
from pathlib import Path

import pdfplumber

from manifest import ITEMS, PAPER, TOPICS


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_pages(path):
    with pdfplumber.open(path) as pdf:
        return [(page.extract_text() or "").strip() for page in pdf.pages]


def build_seed(paper_path, scheme_path):
    question_pages = extract_pages(paper_path)
    scheme_pages = extract_pages(scheme_path)
    if len(question_pages) != 16 or len(scheme_pages) != 19:
        raise ValueError("Unexpected PDF page count; check the selected June 2025 files")
    if sum(item[1] for item in ITEMS) != PAPER["total_marks"]:
        raise ValueError("Question marks do not add up to the paper total")
    if len({item[0] for item in ITEMS}) != len(ITEMS):
        raise ValueError("Duplicate question label")

    questions = []
    for label, marks, paper_pages, mark_pages, topics, summary in ITEMS:
        questions.append({
            "question_id": f'{PAPER["paper_id"]}-q{label.replace("(", "-").replace(")", "")}',
            "paper_id": PAPER["paper_id"],
            "label": label,
            "number": int(label.split("(")[0]),
            "marks": marks,
            "topic_codes": topics,
            "summary": summary,
            "paper_pages": paper_pages,
            "mark_scheme_pages": mark_pages,
            "paper_page_text": {str(p): question_pages[p - 1] for p in paper_pages},
            "mark_scheme_page_text": {str(p): scheme_pages[p - 1] for p in mark_pages},
            "review_status": "needs_transcription_review",
            "source_kind": "official_past_paper",
            "question_kind": "official",
            "derived_from_question_id": None,
        })

    return {
        "schema_version": 1,
        "paper": {
            **PAPER,
            "question_count": len(questions),
            "question_pdf_sha256": digest(paper_path),
            "mark_scheme_pdf_sha256": digest(scheme_path),
            "question_pdf_pages": len(question_pages),
            "mark_scheme_pdf_pages": len(scheme_pages),
        },
        "topics": TOPICS,
        "questions": questions,
    }


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: prepare_seed.py PAPER.pdf MARK_SCHEME.pdf output.json")
    output = Path(sys.argv[3])
    seed = build_seed(Path(sys.argv[1]), Path(sys.argv[2]))
    output.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'Prepared {len(seed["questions"])} questions, {sum(q["marks"] for q in seed["questions"])} marks')
