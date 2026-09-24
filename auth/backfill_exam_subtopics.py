"""Fill missing subtopic tags without changing teacher-edited questions.

Usage inside the auth container: python backfill_exam_subtopics.py mapping.json
The mapping is a JSON object of question_id to subtopic label.
"""

import json
import os
import sys
from pathlib import Path

from pymongo import MongoClient


def backfill(db, mapping):
    changed = 0
    for question_id, subtopic in mapping.items():
        if not isinstance(question_id, str) or not isinstance(subtopic, str) or not subtopic.strip():
            raise ValueError("Invalid subtopic mapping")
        result = db.exam_questions.update_one(
            {"question_id": question_id, "$or": [{"subtopic": {"$exists": False}}, {"subtopic": ""}]},
            {"$set": {"subtopic": subtopic.strip()}},
        )
        changed += result.modified_count
    return changed


if __name__ == "__main__":
    mapping = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    db = MongoClient(os.environ["MONGO_URI"]).get_default_database()
    print(f"Added subtopics to {backfill(db, mapping)} existing questions")
