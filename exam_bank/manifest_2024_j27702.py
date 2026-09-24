"""Question boundaries and topic tags for OCR J277/02 June 2024."""

from manifest_j27702 import TOPICS

PAPER = {
    "paper_id": "ocr-j277-02-2024-06", "awarding_body": "OCR",
    "qualification": "GCSE Computer Science", "specification": "J277",
    "component": "J277/02", "title": "Computational Thinking, Algorithms and Programming",
    "series": "June", "year": 2024, "duration_minutes": 90,
    "total_marks": 80, "source_kind": "official_past_paper",
}

# label, marks, question pages, mark-scheme pages, topic codes, index summary
ITEMS = [
    ("1", 3, [2], [8], ["2.2"], "Selection and iteration keywords"),
    ("2", 4, [2], [9], ["2.1"], "Complete an odd-even flowchart"),
    ("3(a)", 2, [3], [10], ["2.3"], "Syntax error definition and example"),
    ("3(b)", 4, [3], [11], ["2.2"], "Find and correct two logic errors"),
    ("3(c)(i)", 3, [4], [11, 12], ["2.1"], "Trace a binary search"),
    ("3(c)(ii)", 1, [4], [12], ["2.1"], "Binary search prerequisite"),
    ("3(c)(iii)", 1, [4], [12], ["2.1"], "Identify merge sort"),
    ("4(a)", 2, [4], [12], ["2.2"], "Input and output in a video program"),
    ("4(b)", 2, [4], [13], ["2.3"], "Defensive design method"),
    ("5(a)", 4, [5], [14], ["2.4"], "Truth table for AND then OR"),
    ("5(b)", 3, [5], [15], ["2.4"], "Draw NOT, OR and AND circuit"),
    ("6(a)", 3, [6], [16], ["2.2"], "String functions and output"),
    ("6(b)", 3, [6], [16], ["2.2"], "Assign and concatenate strings"),
    ("7(a)", 2, [7], [17], ["2.5"], "Reasons to use a low-level language"),
    ("7(b)", 3, [7], [17], ["2.5"], "Benefits of a compiler"),
    ("8(a)", 4, [8], [18], ["2.3"], "Improve algorithm maintainability"),
    ("8(b)", 6, [9], [19], ["2.2"], "Complete bounded movement function"),
    ("9(a)(i)", 3, [11], [20], ["2.2"], "Data types for sports-day variables"),
    ("9(a)(ii)", 4, [12], [20], ["2.1", "2.2"], "Complete linear search function"),
    ("9(b)", 4, [13], [21], ["2.1"], "Trace a javelin scoring algorithm"),
    ("9(c)(i)", 4, [14], [22], ["2.3", "2.2"], "Validate a high-jump height"),
    ("9(c)(ii)", 3, [14], [23], ["2.3"], "Normal, boundary and erroneous test data"),
    ("9(d)", 4, [15], [23], ["2.2"], "Complete sports-day SQL query"),
    ("9(e)(i)", 1, [15], [24], ["2.1"], "Abstraction in sports-day design"),
    ("9(e)(ii)", 1, [15], [24], ["2.1"], "Decomposition in sports-day design"),
    ("9(f)", 6, [16], [25, 26], ["2.2"], "Algorithm to find winning team"),
]

SUBTOPICS = {
    "1": "Programming constructs", "2": "Flowcharts",
    "3(a)": "Program errors", "3(b)": "Program errors",
    "3(c)(i)": "Searching algorithms", "3(c)(ii)": "Searching algorithms",
    "3(c)(iii)": "Sorting algorithms", "4(a)": "Inputs and outputs",
    "4(b)": "Defensive design", "5(a)": "Boolean expressions",
    "5(b)": "Logic circuits", "6(a)": "String operations",
    "6(b)": "String operations", "7(a)": "Programming languages",
    "7(b)": "Translators", "8(a)": "Maintainability",
    "8(b)": "Functions", "9(a)(i)": "Data types",
    "9(a)(ii)": "Searching algorithms", "9(b)": "Trace tables",
    "9(c)(i)": "Validation", "9(c)(ii)": "Testing",
    "9(d)": "SQL", "9(e)(i)": "Abstraction",
    "9(e)(ii)": "Decomposition", "9(f)": "Iteration",
}
