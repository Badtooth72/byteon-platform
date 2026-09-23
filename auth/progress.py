import re
from datetime import datetime, timezone


LEGACY_WRITABLE_ACTIVITIES = {"logic_gate_quiz", "wordsearch"}


def validate_progress_payload(data):
    activity_key = data.get("activity_key")
    challenge_id = data.get("challenge_id", "default")
    score = data.get("score", 0)
    submission = data.get("submission")

    if not isinstance(activity_key, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", activity_key):
        raise ValueError("Invalid activity_key")
    if activity_key not in LEGACY_WRITABLE_ACTIVITIES:
        raise ValueError("This activity records progress through its own service")
    if not isinstance(challenge_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", challenge_id):
        raise ValueError("Invalid challenge_id")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100:
        raise ValueError("Invalid score")
    if submission is not None and (not isinstance(submission, str) or len(submission) > 4000):
        raise ValueError("Invalid submission")
    return activity_key, challenge_id, score, submission


def build_progress_record(data, now=None):
    activity_key, challenge_id, score, submission = validate_progress_payload(data)
    record = {
        "schema_version": 1,
        "score": score,
        "submission": submission,
        "date": now or datetime.now(timezone.utc),
    }
    if data.get("level") is not None:
        record["level"] = data["level"]
    return activity_key, challenge_id, record
