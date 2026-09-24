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

from manifest import ITEMS as PAPER_1_ITEMS, PAPER as PAPER_1, TOPICS as PAPER_1_TOPICS
from manifest_j27702 import ITEMS as PAPER_2_ITEMS, PAPER as PAPER_2, TOPICS as PAPER_2_TOPICS


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_pages(path):
    with pdfplumber.open(path) as pdf:
        return [(page.extract_text() or "").strip() for page in pdf.pages]


def build_seed(paper_path, scheme_path):
    if "J27702" in paper_path.name.upper():
        paper, items, topics = PAPER_2, PAPER_2_ITEMS, PAPER_2_TOPICS
        expected_pages = (20, 31)
    elif "J27701" in paper_path.name.upper():
        paper, items, topics = PAPER_1, PAPER_1_ITEMS, PAPER_1_TOPICS
        expected_pages = (16, 19)
    else:
        raise ValueError("Unsupported paper code")
    question_pages = extract_pages(paper_path)
    scheme_pages = extract_pages(scheme_path)
    if (len(question_pages), len(scheme_pages)) != expected_pages:
        raise ValueError("Unexpected PDF page count; check the selected June 2025 files")
    if sum(item[1] for item in items) != paper["total_marks"]:
        raise ValueError("Question marks do not add up to the paper total")
    if len({item[0] for item in items}) != len(items):
        raise ValueError("Duplicate question label")

    questions = []
    for label, marks, paper_pages, mark_pages, question_topics, summary in items:
        questions.append({
            "question_id": f'{paper["paper_id"]}-q{label.replace("(", "-").replace(")", "")}',
            "paper_id": paper["paper_id"],
            "label": label,
            "number": int(label.split("(")[0]),
            "marks": marks,
            "topic_codes": question_topics,
            "summary": summary,
            "paper_pages": paper_pages,
            "mark_scheme_pages": mark_pages,
            "paper_page_text": {str(p): question_pages[p - 1] for p in paper_pages},
            "mark_scheme_page_text": {str(p): scheme_pages[p - 1] for p in mark_pages},
            "review_status": "needs_transcription_review",
            "source_kind": "official_past_paper",
            "question_kind": "official",
            "derived_from_question_id": None,
            "source_search_text": " ".join(question_pages[p - 1] for p in paper_pages),
            "ao_marks": {"AO1": None, "AO2": None, "AO3": None},
            "ao_review_status": "unassigned",
        })

    return {
        "schema_version": 1,
        "paper": {
            **paper,
            "question_count": len(questions),
            "question_pdf_sha256": digest(paper_path),
            "mark_scheme_pdf_sha256": digest(scheme_path),
            "question_pdf_pages": len(question_pages),
            "mark_scheme_pdf_pages": len(scheme_pages),
        },
        "topics": topics,
        "questions": questions,
    }


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: prepare_seed.py PAPER.pdf MARK_SCHEME.pdf output.json")
    output = Path(sys.argv[3])
    seed = build_seed(Path(sys.argv[1]), Path(sys.argv[2]))
    output.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'Prepared {len(seed["questions"])} questions, {sum(q["marks"] for q in seed["questions"])} marks')
