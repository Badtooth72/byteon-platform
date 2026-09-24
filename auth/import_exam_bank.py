"""Idempotent, private MongoDB import for a prepared OCR paper seed.

Run inside the auth container with the seed and both source PDFs mounted or
copied temporarily. Re-running preserves teacher edits to existing questions.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from gridfs import GridFS
from pymongo import MongoClient, ASCENDING


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def store_pdf(fs, path, expected_hash, paper_id, role):
    if sha256(path) != expected_hash:
        raise ValueError(f"{role} PDF does not match the prepared seed")
    filename = f"{paper_id}-{role}.pdf"
    existing = fs.find_one({"filename": filename, "sha256": expected_hash})
    if existing:
        return existing._id
    with path.open("rb") as stream:
        return fs.put(
            stream,
            filename=filename,
            content_type="application/pdf",
            paper_id=paper_id,
            role=role,
            sha256=expected_hash,
        )


def import_seed(db, seed, paper_path, scheme_path):
    paper = seed["paper"]
    questions = seed["questions"]
    if seed.get("schema_version") != 1:
        raise ValueError("Unsupported seed schema")
    if sum(question["marks"] for question in questions) != paper["total_marks"]:
        raise ValueError("Question marks do not match the paper total")
    if len(questions) != paper["question_count"]:
        raise ValueError("Question count does not match the paper")
    if len({question["question_id"] for question in questions}) != len(questions):
        raise ValueError("Duplicate question IDs")
    codes = {topic["code"] for topic in seed["topics"]}
    if any(set(question["topic_codes"]) - codes for question in questions):
        raise ValueError("Unknown topic code")

    fs = GridFS(db, collection="exam_source_files")
    paper_file = store_pdf(fs, paper_path, paper["question_pdf_sha256"], paper["paper_id"], "question")
    scheme_file = store_pdf(fs, scheme_path, paper["mark_scheme_pdf_sha256"], paper["paper_id"], "mark-scheme")

    db.exam_papers.create_index("paper_id", unique=True)
    db.exam_topics.create_index("code", unique=True)
    db.exam_questions.create_index("question_id", unique=True)
    db.exam_questions.create_index([("paper_id", ASCENDING), ("number", ASCENDING)])
    db.exam_questions.create_index([("topic_codes", ASCENDING), ("marks", ASCENDING)])
    db.exam_questions.create_index([("subtopic", ASCENDING), ("paper_id", ASCENDING)])
    db.exam_questions.create_index([("year", ASCENDING), ("review_status", ASCENDING)])

    db.exam_papers.update_one(
        {"paper_id": paper["paper_id"]},
        {"$set": {**paper, "question_file_id": paper_file, "mark_scheme_file_id": scheme_file}},
        upsert=True,
    )
    for topic in seed["topics"]:
        db.exam_topics.update_one({"code": topic["code"]}, {"$set": topic}, upsert=True)
    for question in questions:
        document = {
            **question,
            "year": paper["year"],
            "series": paper["series"],
            "component": paper["component"],
        }
        db.exam_questions.update_one(
            {"question_id": question["question_id"]},
            {"$setOnInsert": document},
            upsert=True,
        )
        # Existing teacher edits win; add newly supported fields on re-import.
        existing = db.exam_questions.find_one(
            {"question_id": question["question_id"]},
            {"subtopic": 1, "question_text": 1, "prompt_review_status": 1},
        )
        additions = {}
        for field in ("subtopic", "question_text", "prompt_review_status"):
            if field not in existing and question.get(field):
                additions[field] = question[field]
        if additions:
            db.exam_questions.update_one({"_id": existing["_id"]}, {"$set": additions})
    # Add new search/AO fields to older imports without overwriting teacher edits.
    for existing in db.exam_questions.find(
        {"$or": [{"source_search_text": {"$exists": False}}, {"ao_marks": {"$exists": False}}]},
        {"question_id": 1, "paper_page_text": 1, "source_search_text": 1, "ao_marks": 1},
    ):
        additions = {}
        if "source_search_text" not in existing:
            additions["source_search_text"] = " ".join(
                (existing.get("paper_page_text") or {}).values()
            )
        if "ao_marks" not in existing:
            additions["ao_marks"] = {"AO1": None, "AO2": None, "AO3": None}
            additions["ao_review_status"] = "unassigned"
        if additions:
            db.exam_questions.update_one({"_id": existing["_id"]}, {"$set": additions})
    return len(questions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", type=Path)
    parser.add_argument("question_pdf", type=Path)
    parser.add_argument("mark_scheme_pdf", type=Path)
    args = parser.parse_args()
    seed_data = json.loads(args.seed.read_text(encoding="utf-8"))
    client = MongoClient(os.environ["MONGO_URI"])
    database = client.get_default_database()
    count = import_seed(database, seed_data, args.question_pdf, args.mark_scheme_pdf)
    print(f'Imported {count} question records for {seed_data["paper"]["paper_id"]}')
