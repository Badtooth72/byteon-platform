from datetime import datetime


LOGIC_CORE_IDS = {
    "identify-and", "identify-or", "identify-not",
    "truth-and", "truth-or", "truth-not",
    "build-alarm", "master-expression",
}
CODING_CHALLENGE_COUNT = 75
CODING_MAX_POINTS = CODING_CHALLENGE_COUNT * 10


def _number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _date(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")


def _result(points=0, maximum=0, attempts=0, detail="", updated_at=""):
    percent = round(min(100, max(0, points / maximum * 100)), 1) if maximum else 0
    return {
        "points": round(points, 1),
        "max_points": round(maximum, 1),
        "percent": percent,
        "attempts": int(attempts or 0),
        "detail": detail,
        "updated_at": _date(updated_at),
        "has_score": maximum > 0,
    }


def coding_score(data):
    levels = data.get("levels", data) if isinstance(data, dict) else {}
    points = maximum = attempts = 0
    latest = ""
    for level in levels.values() if isinstance(levels, dict) else []:
        if not isinstance(level, dict):
            continue
        challenges = level.get("challenges", {})
        if isinstance(challenges, dict) and challenges:
            for challenge in challenges.values():
                if not isinstance(challenge, dict):
                    continue
                points += _number(challenge.get("score"))
                maximum += 10
                attempts += int(_number(challenge.get("attempts")))
                latest = max(latest, _date(challenge.get("date")))
        else:
            level_points = _number(level.get("total_score"))
            if level_points:
                points += level_points
                maximum += max(100, level_points)
        latest = max(latest, _date(level.get("date")))
    completed = int(maximum / 10)
    return _result(points, CODING_MAX_POINTS, attempts, f"{completed} of {CODING_CHALLENGE_COUNT} challenges attempted", latest)


def conversion_score(data):
    best = None
    for mode, record in data.items() if isinstance(data, dict) else []:
        if not isinstance(record, dict):
            continue
        points = _number(record.get("score"))
        maximum = _number(record.get("question_count"), max(10, points))
        candidate = _result(points, maximum, maximum, f"Best mode: {str(mode).title()}", record.get("date"))
        if best is None or candidate["percent"] > best["percent"] or (
            candidate["percent"] == best["percent"] and candidate["points"] > best["points"]
        ):
            best = candidate
    return best or _result()


def logic_score(data):
    records = data if isinstance(data, dict) else {}
    completed = [records[key] for key in LOGIC_CORE_IDS if isinstance(records.get(key), dict)]
    points = sum(1 for record in completed if record.get("correct") or _number(record.get("score")) > 0)
    attempts = len(records.get("attempt_history", [])) if isinstance(records.get("attempt_history"), list) else len(completed)
    latest = max((_date(record.get("date")) for record in completed), default="")
    return _result(points, len(LOGIC_CORE_IDS), attempts, f"{len(completed)} of {len(LOGIC_CORE_IDS)} core challenges completed", latest)


def flashcard_score(data):
    summary = data.get("summary", data) if isinstance(data, dict) else {}
    if not isinstance(summary, dict):
        return _result()
    games = int(_number(summary.get("games_played")))
    accuracy = _number(summary.get("best_accuracy"))
    return _result(accuracy, 100, games, f"{games} game{'s' if games != 1 else ''} played", summary.get("last_played_at") or summary.get("updated_at")) if games or accuracy else _result()


def wordsearch_score(data):
    if not isinstance(data, dict):
        return _result()
    scored = [record for record in data.values() if isinstance(record, dict) and isinstance(record.get("score"), (int, float))]
    if not scored:
        return _result()
    best = max(scored, key=lambda record: record.get("score", 0))
    return _result(_number(best.get("score")), 100, len(scored), "Best recorded wordsearch", best.get("date"))


SCORERS = {
    "coding_challenges": coding_score,
    "conversion_game": conversion_score,
    "logic_gate_quiz": logic_score,
    "flashcard_generator": flashcard_score,
    "wordsearch": wordsearch_score,
}


def score_activity(activity_key, data):
    scorer = SCORERS.get(activity_key)
    return scorer(data or {}) if scorer else _result()
