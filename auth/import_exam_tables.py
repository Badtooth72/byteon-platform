"""Import private table layouts into existing exam questions without replacing reviews.

Usage: python import_exam_tables.py private_tables.json
The JSON maps question_id to {question_text, question_tables}.
"""

import argparse
import json
import os
from pathlib import Path

from pymongo import MongoClient

from exam_bank_logic import validate_question_tables


def import_tables(db, mapping):
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError("Expected a non-empty question mapping")
    documents = {}
    for question_id, content in mapping.items():
        if not isinstance(question_id, str) or not isinstance(content, dict):
            raise ValueError("Invalid question mapping")
        prompt = content.get("question_text")
        if not isinstance(prompt, str) or not 0 < len(prompt.strip()) <= 8000:
            raise ValueError(f"Invalid prompt for {question_id}")
        validate_question_tables(content.get("question_tables"))
        question = db.exam_questions.find_one(
            {"question_id": question_id},
            {"_id": 1, "prompt_review_status": 1, "table_review_status": 1, "question_tables": 1},
        )
        if not question:
            raise ValueError(f"Unknown question: {question_id}")
        documents[question_id] = question
    changed = 0
    skipped = 0
    for question_id, content in mapping.items():
        question = documents[question_id]
        if question.get("question_tables") or question.get("prompt_review_status") == "teacher_verified" or question.get("table_review_status") == "teacher_verified":
            skipped += 1
            continue
        result = db.exam_questions.update_one(
            {"_id": question["_id"], "question_tables": {"$exists": False}},
            {"$set": {
                "question_text": content["question_text"].strip(),
                "question_tables": content["question_tables"],
                "prompt_review_status": "draft_needs_source_check",
                "table_review_status": "draft_needs_source_check",
            }},
        )
        changed += result.modified_count
    return changed, skipped


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mapping", type=Path)
    args = parser.parse_args()
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    db = MongoClient(os.environ["MONGO_URI"]).get_default_database()
    changed, skipped = import_tables(db, mapping)
    print(f"Added table layouts to {changed} questions; preserved {skipped} existing layouts or reviews")
