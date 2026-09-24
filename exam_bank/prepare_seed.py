"""Extract teacher review material from local PDFs; output is private import data.

Usage: python prepare_seed.py PAPER.pdf MARK_SCHEME.pdf output.json [private_prompts.json]
Requires pdfplumber. The resulting JSON contains source page text and must not
be committed to the public repository.
"""

import hashlib
import json
import sys
from pathlib import Path

import pdfplumber

from manifest import ITEMS as PAPER_1_ITEMS, PAPER as PAPER_1, TOPICS as PAPER_1_TOPICS, SUBTOPICS as PAPER_1_SUBTOPICS
from manifest_j27702 import ITEMS as PAPER_2_ITEMS, PAPER as PAPER_2, TOPICS as PAPER_2_TOPICS, SUBTOPICS as PAPER_2_SUBTOPICS
from manifest_2024_j27701 import ITEMS as P1_2024_ITEMS, PAPER as P1_2024, TOPICS as P1_2024_TOPICS, SUBTOPICS as P1_2024_SUBTOPICS
from manifest_2024_j27702 import ITEMS as P2_2024_ITEMS, PAPER as P2_2024, TOPICS as P2_2024_TOPICS, SUBTOPICS as P2_2024_SUBTOPICS


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_pages(path):
    with pdfplumber.open(path) as pdf:
        return [(page.extract_text() or "").strip() for page in pdf.pages]


def build_seed(paper_path, scheme_path, prompts=None):
    prompts = prompts or {}
    name = paper_path.name.upper()
    visual_required = set()
    if "J27702" in name and "2024" in name:
        paper, items, topics = P2_2024, P2_2024_ITEMS, P2_2024_TOPICS
        subtopics, expected_pages = P2_2024_SUBTOPICS, (20, 27)
        visual_required = {"2"}
    elif "J27701" in name and "2024" in name:
        paper, items, topics = P1_2024, P1_2024_ITEMS, P1_2024_TOPICS
        subtopics, expected_pages = P1_2024_SUBTOPICS, (16, 22)
    elif "J27702" in name and "2025" in name:
        paper, items, topics = PAPER_2, PAPER_2_ITEMS, PAPER_2_TOPICS
        subtopics = PAPER_2_SUBTOPICS
        expected_pages = (20, 31)
    elif "J27701" in name and "2025" in name:
        paper, items, topics = PAPER_1, PAPER_1_ITEMS, PAPER_1_TOPICS
        subtopics = PAPER_1_SUBTOPICS
        expected_pages = (16, 19)
    else:
        raise ValueError("Unsupported paper code")
    question_pages = extract_pages(paper_path)
    scheme_pages = extract_pages(scheme_path)
    if (len(question_pages), len(scheme_pages)) != expected_pages:
        raise ValueError("Unexpected PDF page count; check the selected paper and mark scheme")
    if sum(item[1] for item in items) != paper["total_marks"]:
        raise ValueError("Question marks do not add up to the paper total")
    if len({item[0] for item in items}) != len(items):
        raise ValueError("Duplicate question label")
    labels = {item[0] for item in items}
    if set(subtopics) != labels or (prompts and set(prompts) != labels):
        raise ValueError("Every question needs one clean prompt and subtopic")

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
            "question_text": prompts.get(label, ""),
            "prompt_review_status": "draft_needs_source_check" if label in prompts else "not_transcribed",
            "requires_source_visual": label in visual_required,
            "subtopic": subtopics.get(label, ""),
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
    if len(sys.argv) not in {4, 5}:
        raise SystemExit("Usage: prepare_seed.py PAPER.pdf MARK_SCHEME.pdf output.json [private_prompts.json]")
    output = Path(sys.argv[3])
    prompts = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8")) if len(sys.argv) == 5 else None
    seed = build_seed(Path(sys.argv[1]), Path(sys.argv[2]), prompts)
    output.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'Prepared {len(seed["questions"])} questions, {sum(q["marks"] for q in seed["questions"])} marks')
