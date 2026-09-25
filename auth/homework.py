from datetime import datetime, timezone


TRACE_TASKS = {
    "running-total": {
        "title": "Running total",
        "topic": "2.1 Algorithms",
        "intro": "Start with total = 0. For each number in [3, 5, 2], add the number to total and output total.",
        "columns": ["number", "total", "output"],
        "rows": [["3", "3", "3"], ["5", "8", "8"], ["2", "10", "10"]],
    },
    "count-even": {
        "title": "Count the even numbers",
        "topic": "2.1 Algorithms",
        "intro": "Start with count = 0. For each number in [4, 7, 6, 9], add 1 to count only when the number is even.",
        "columns": ["number", "even? (yes/no)", "count"],
        "rows": [["4", "yes", "1"], ["7", "no", "1"], ["6", "yes", "2"], ["9", "no", "2"]],
    },
    "while-loop": {
        "title": "While loop",
        "topic": "2.1 Algorithms",
        "intro": "Start with x = 1. While x < 10, output x, then double x. Record each pass through the loop.",
        "columns": ["pass", "output", "x after doubling"],
        "rows": [["1", "1", "2"], ["2", "2", "4"], ["3", "4", "8"], ["4", "8", "16"]],
    },
}

ASSIGNABLE = {
    "trace_table": ("Trace table lab", "/trace-tables"),
    "coding_challenges": ("Coding challenges", "/coding-challenges"),
    "conversion_game": ("Conversion quiz", "/conversion-game"),
    "logic_gate_quiz": ("Logic gate quiz", "/logic-gate-quiz"),
    "flashcard_generator": ("Flashcard play", "/flashcards/play"),
    "wordsearch": ("Wordsearch", "/wordsearch_app/"),
}


def mark_trace(task_id, answers):
    task = TRACE_TASKS.get(task_id)
    if not task or not isinstance(answers, list) or len(answers) != len(task["rows"]):
        raise ValueError("Invalid trace table")
    expected = task["rows"]
    if any(not isinstance(row, list) or len(row) != len(task["columns"]) for row in answers):
        raise ValueError("Invalid trace table")
    if any(not isinstance(cell, str) or len(cell) > 40 for row in answers for cell in row):
        raise ValueError("Invalid cell")
    marked = [[given.strip().lower() == correct.lower() for given, correct in zip(row, answer)]
              for row, answer in zip(answers, expected)]
    points = sum(sum(row) for row in marked)
    maximum = sum(len(row) for row in expected)
    return {"points": points, "max_points": maximum, "percent": round(points / maximum * 100), "marked": marked,
            "expected": expected}


def parse_due_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    except (TypeError, ValueError):
        raise ValueError("Choose a valid due date")


def activity_is_new(summary, assigned_at):
    value = summary.get("updated_at")
    if not value or not summary.get("has_score"):
        return False
    try:
        when = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if assigned_at.tzinfo is None:
            assigned_at = assigned_at.replace(tzinfo=timezone.utc)
        return when >= assigned_at
    except ValueError:
        return False
