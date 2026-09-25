import keyword
import html
import tokenize
from datetime import datetime, timezone
from io import StringIO
from random import SystemRandom

TRACE_TASKS = {
    "running-total": {
        "title": "Running total", "topic": "2.1 Algorithms",
        "intro": "Record the value after each pass through the loop.",
        "code": "numbers = [3, 5, 2]\ntotal = 0\nfor number in numbers:\n    total += number\n    print(total)",
        "columns": ["number", "total", "output"],
        "rows": [["3", "3", "3"], ["5", "8", "8"], ["2", "10", "10"]],
    },
    "count-even": {
        "title": "Count the even numbers", "topic": "2.1 Algorithms",
        "intro": "Record whether each number is even and the running count.",
        "code": "numbers = [4, 7, 6, 9]\ncount = 0\nfor number in numbers:\n    if number % 2 == 0:\n        count += 1",
        "columns": ["number", "even? (yes/no)", "count"],
        "rows": [["4", "yes", "1"], ["7", "no", "1"], ["6", "yes", "2"], ["9", "no", "2"]],
    },
    "while-loop": {
        "title": "While loop", "topic": "2.1 Algorithms",
        "intro": "Follow x through every pass through the loop.",
        "code": "x = 1\nwhile x < 10:\n    print(x)\n    x = x * 2",
        "columns": ["pass", "output", "x after doubling"],
        "rows": [["1", "1", "2"], ["2", "2", "4"], ["3", "4", "8"], ["4", "8", "16"]],
    },
    "find-largest": {
        "title": "Find the largest", "topic": "2.1 Algorithms",
        "intro": "Record the largest value and printed output after each comparison.",
        "code": "numbers = [6, 2, 9, 4]\nlargest = numbers[0]\nfor number in numbers[1:]:\n    if number > largest:\n        largest = number\n    print(largest)",
        "columns": ["number", "largest", "output"],
        "rows": [["2", "6", "6"], ["9", "9", "9"], ["4", "9", "9"]],
    },
    "linear-search": {
        "title": "Linear search", "topic": "2.1 Algorithms",
        "intro": "Record each position, value and whether the target has been found.",
        "code": "values = [8, 3, 7, 1]\ntarget = 7\nfound = False\nfor position in range(len(values)):\n    if values[position] == target:\n        found = True",
        "columns": ["position", "value", "found? (true/false)"],
        "rows": [["0", "8", "false"], ["1", "3", "false"], ["2", "7", "true"], ["3", "1", "true"]],
    },
}

ASSIGNABLE = {
    "trace_table": ("Trace table lab", "/trace-tables"),
    "coding_challenges": ("Coding challenges", "/coding-challenges/"),
    "conversion_game": ("Conversion quiz", "/conversion-game/"),
    "logic_gate_quiz": ("Logic gate quiz", "/logic-gate-quiz/"),
    # Older assignments still need their labels and links.
    "flashcard_generator": ("Flashcard play", "/flashcards/play"),
    "wordsearch": ("Wordsearch", "/wordsearch_app/"),
}
NEW_ASSIGNABLE = {key: ASSIGNABLE[key] for key in ("trace_table", "coding_challenges", "conversion_game", "logic_gate_quiz")}
CONVERSION_MODES = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
LOGIC_TASKS = {
    "identify-and": "Identify AND", "identify-or": "Identify OR", "identify-not": "Identify NOT",
    "truth-and": "AND truth table", "truth-or": "OR truth table", "truth-not": "NOT truth table",
    "build-alarm": "Build an alarm", "master-expression": "GCSE circuit challenge",
}


def highlight_code(code):
    """Escape code and apply local Python syntax classes."""
    lines = code.splitlines(keepends=True)
    starts = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line)
    output = []
    last = 0
    try:
        for token in tokenize.generate_tokens(StringIO(code).readline):
            if token.type == tokenize.ENDMARKER:
                break
            if token.type in {tokenize.INDENT, tokenize.DEDENT}:
                continue
            start = starts[token.start[0] - 1] + token.start[1]
            end = starts[token.end[0] - 1] + token.end[1]
            output.append(html.escape(code[last:start]))
            style = "code-keyword" if token.type == tokenize.NAME and token.string in keyword.kwlist else (
                "code-number" if token.type == tokenize.NUMBER else "code-string" if token.type == tokenize.STRING else "")
            value = html.escape(code[start:end])
            output.append(f'<span class="{style}">{value}</span>' if style else value)
            last = end
    except (tokenize.TokenError, IndexError):
        return html.escape(code)
    output.append(html.escape(code[last:]))
    return "".join(output)


def generate_trace(rng=None):
    rng = rng or SystemRandom()
    kind = rng.choice(("total", "threshold", "multiply"))
    if kind == "total":
        numbers = [rng.randint(1, 9) for _ in range(4)]
        total = 0
        rows = []
        for number in numbers:
            total += number
            rows.append([str(number), str(total), str(total)])
        return {"title": "Random running total", "topic": "2.1 Algorithms", "intro": "A new set of values each time. Correct cells earn double points.",
                "code": f"numbers = {numbers}\ntotal = 0\nfor number in numbers:\n    total += number\n    print(total)",
                "columns": ["number", "total", "output"], "rows": rows, "bonus_multiplier": 2}
    if kind == "threshold":
        numbers = [rng.randint(1, 12) for _ in range(4)]
        limit = rng.randint(4, 9)
        count = 0
        rows = []
        for number in numbers:
            if number > limit:
                count += 1
            rows.append([str(number), "yes" if number > limit else "no", str(count)])
        return {"title": "Random threshold counter", "topic": "2.1 Algorithms", "intro": "A new set of values each time. Correct cells earn double points.",
                "code": f"numbers = {numbers}\nlimit = {limit}\ncount = 0\nfor number in numbers:\n    if number > limit:\n        count += 1",
                "columns": ["number", "above limit? (yes/no)", "count"], "rows": rows, "bonus_multiplier": 2}
    start = rng.randint(1, 3)
    factor = rng.randint(2, 3)
    x = start
    rows = []
    for pass_number in range(1, 5):
        output = x
        x *= factor
        rows.append([str(pass_number), str(output), str(x)])
    return {"title": "Random loop", "topic": "2.1 Algorithms", "intro": "A new loop each time. Correct cells earn double points.",
            "code": f"x = {start}\nfor pass_number in range(1, 5):\n    print(x)\n    x = x * {factor}",
            "columns": ["pass", "output", "x after multiplication"], "rows": rows, "bonus_multiplier": 2}


def mark_trace(task_id, answers, task=None):
    task = task or TRACE_TASKS.get(task_id)
    if not task or not isinstance(answers, list) or len(answers) != len(task["rows"]):
        raise ValueError("Invalid trace table")
    expected = task["rows"]
    if any(not isinstance(row, list) or len(row) != len(task["columns"]) for row in answers):
        raise ValueError("Invalid trace table")
    if any(not isinstance(cell, str) or len(cell) > 40 for row in answers for cell in row):
        raise ValueError("Invalid cell")
    marked = [[given.strip().lower() == correct.lower() for given, correct in zip(row, answer)]
              for row, answer in zip(answers, expected)]
    correct_cells = sum(sum(row) for row in marked)
    maximum_cells = sum(len(row) for row in expected)
    multiplier = task.get("bonus_multiplier", 1)
    return {"points": correct_cells * multiplier, "max_points": maximum_cells * multiplier,
            "percent": round(correct_cells / maximum_cells * 100), "marked": marked, "expected": expected}


def parse_due_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    except (TypeError, ValueError):
        raise ValueError("Choose a valid due date")


def as_utc(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def activity_is_new(summary, assigned_at):
    when = as_utc(summary.get("updated_at"))
    assigned = as_utc(assigned_at)
    return bool(when and assigned and summary.get("has_score") and when >= assigned)


def validate_target(activity_key, task_id, target_score, coding_ids=None):
    if activity_key not in NEW_ASSIGNABLE:
        raise ValueError("Choose an activity with recorded scores")
    try:
        target = int(target_score)
    except (TypeError, ValueError):
        raise ValueError("Target score must be a whole percentage")
    if not 1 <= target <= 100:
        raise ValueError("Target score must be between 1% and 100%")
    if activity_key == "trace_table" and task_id not in {*TRACE_TASKS, "random"}:
        raise ValueError("Choose a trace table")
    if activity_key == "logic_gate_quiz" and task_id not in LOGIC_TASKS:
        raise ValueError("Choose a logic gate challenge")
    if activity_key == "conversion_game" and task_id not in CONVERSION_MODES:
        raise ValueError("Choose a conversion mode")
    if activity_key == "coding_challenges" and task_id not in (coding_ids or set()):
        raise ValueError("Choose a coding challenge")
    return target


def task_title(activity_key, task_id, coding_titles=None):
    if activity_key == "trace_table":
        return "Random bonus challenge" if task_id == "random" else TRACE_TASKS.get(task_id, {}).get("title", "Trace table")
    if activity_key == "logic_gate_quiz":
        return LOGIC_TASKS.get(task_id, "Logic gate challenge")
    if activity_key == "conversion_game":
        return f"{CONVERSION_MODES.get(task_id, task_id.title())} mode"
    if activity_key == "coding_challenges":
        return (coding_titles or {}).get(task_id, f"Challenge {task_id}")
    return ASSIGNABLE.get(activity_key, (activity_key, ""))[0]


def specific_progress(assignment, user):
    """Return the score for exactly the assigned task, or None before a new attempt."""
    activity = assignment["activity_key"]
    task_id = assignment.get("task_id")
    data = (user.get("activities") or {}).get(activity, {}) or {}
    assigned_at = as_utc(assignment.get("created_at"))
    if activity == "coding_challenges" and task_id and ":" in task_id:
        level, challenge_id = task_id.split(":", 1)
        record = data.get("levels", {}).get(level, {}).get("challenges", {}).get(challenge_id, {})
        attempts = int(record.get("attempts", 0) or 0)
        if not attempts:
            return None
        return round(min(100, max(0, float(record.get("score", 0)) * 10)), 1)
    if activity == "logic_gate_quiz" and task_id:
        record = data.get(task_id, {})
        when = as_utc(record.get("date"))
        if not when or not assigned_at or when < assigned_at:
            return None
        return 100 if record.get("correct") else 0
    if activity == "conversion_game" and task_id:
        record = data.get(task_id, {})
        when = as_utc(record.get("date"))
        if not when or not assigned_at or when < assigned_at:
            return None
        maximum = float(record.get("question_count") or 10)
        return round(min(100, max(0, float(record.get("score", 0)) / maximum * 100)), 1) if maximum > 0 else None
    return None
