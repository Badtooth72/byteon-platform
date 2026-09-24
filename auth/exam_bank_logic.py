"""Validation and totals for teacher-curated assessment drafts."""

AO_KEYS = ("AO1", "AO2", "AO3")


def parse_ao_marks(values, total_marks):
    raw = [str(values.get(key, "")).strip() for key in AO_KEYS]
    if not any(raw):
        return {key: None for key in AO_KEYS}, "unassigned"
    if not all(value.isdecimal() for value in raw):
        raise ValueError("Enter a whole number for every AO, including zeros")
    marks = {key: int(value) for key, value in zip(AO_KEYS, raw)}
    if sum(marks.values()) != total_marks:
        raise ValueError(f"AO marks must add up to {total_marks}")
    return marks, "teacher_verified"


def summarise_test(questions):
    topic_marks = {}
    ao_marks = {key: 0 for key in AO_KEYS}
    unknown_ao_marks = 0
    for question in questions:
        for code in question.get("topic_codes", []):
            topic_marks[code] = topic_marks.get(code, 0) + question["marks"]
        marks = question.get("ao_marks") or {}
        if question.get("ao_review_status") == "teacher_verified" and all(
            isinstance(marks.get(key), int) for key in AO_KEYS
        ):
            for key in AO_KEYS:
                ao_marks[key] += marks[key]
        else:
            unknown_ao_marks += question["marks"]
    return {
        "total_marks": sum(question["marks"] for question in questions),
        "question_count": len(questions),
        "topic_marks": topic_marks,
        "ao_marks": ao_marks,
        "unknown_ao_marks": unknown_ao_marks,
    }
