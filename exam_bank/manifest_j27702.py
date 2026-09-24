"""Question boundaries and topic tags for OCR J277/02 June 2025."""

PAPER = {
    "paper_id": "ocr-j277-02-2025-06",
    "awarding_body": "OCR",
    "qualification": "GCSE Computer Science",
    "specification": "J277",
    "component": "J277/02",
    "title": "Computational Thinking, Algorithms and Programming",
    "series": "June",
    "year": 2025,
    "duration_minutes": 90,
    "total_marks": 80,
    "source_kind": "official_past_paper",
}

TOPICS = [
    {"code": "2.1", "name": "Algorithms"},
    {"code": "2.2", "name": "Programming fundamentals"},
    {"code": "2.3", "name": "Producing robust programs"},
    {"code": "2.4", "name": "Boolean logic"},
    {"code": "2.5", "name": "Programming languages and Integrated Development Environments"},
]

# label, marks, question pages, mark scheme pages, topics, brief index summary
ITEMS = [
    ("1(a)", 4, [2], [14], ["2.3"], "Normal, boundary and invalid test data"),
    ("1(b)(i)", 3, [2], [14], ["2.2"], "Complete input validation algorithm"),
    ("1(b)(ii)", 1, [2], [14], ["2.2"], "Identify a variable"),
    ("1(b)(iii)", 1, [2], [14], ["2.2"], "Identify a Boolean operator"),
    ("2(a)", 2, [3], [15], ["2.1"], "Trace a flowchart with iteration"),
    ("2(b)(i)", 4, [3], [15], ["2.2"], "Types of iteration"),
    ("2(b)(ii)", 2, [4], [15], ["2.2"], "Programming constructs"),
    ("2(c)", 4, [4], [16, 17], ["2.5"], "IDE tools used to implement a flowchart"),
    ("3(a)", 4, [5], [18], ["2.1"], "Merge sort steps"),
    ("3(b)", 3, [6], [18], ["2.1", "2.2"], "Insertion sort, bubble sort and arrays"),
    ("3(c)(i)", 1, [6], [18], ["2.1"], "Identify a search algorithm"),
    ("3(c)(ii)", 1, [6], [19], ["2.1"], "Search stopping condition"),
    ("4(a)", 5, [7], [20], ["2.2"], "Read, cast and output values from a text file"),
    ("4(b)", 1, [7], [20], ["2.2"], "Identify casting"),
    ("5(a)", 3, [8], [21], ["2.4"], "Draw the security logic circuit"),
    ("5(b)", 2, [8], [21], ["2.4"], "AND truth table"),
    ("5(c)", 3, [9], [22], ["2.1"], "Match computational thinking techniques"),
    ("5(d)", 6, [10], [23], ["2.3", "2.2"], "Validate a four-character PIN"),
    ("6(a)(i)", 1, [11], [24], ["2.2"], "Password input statements"),
    ("6(a)(ii)", 3, [11], [24], ["2.2"], "Compare two passwords"),
    ("6(b)(i)", 4, [12], [25], ["2.2"], "Correct an SQL query"),
    ("6(b)(ii)", 1, [12], [25], ["2.2"], "Identify a database record"),
    ("6(b)(iii)", 2, [12], [25], ["2.2"], "Choose database field data types"),
    ("6(c)(i)", 4, [13], [26], ["2.2"], "Write a ticket price function"),
    ("6(c)(ii)", 2, [13], [27], ["2.2"], "Call the ticket price function"),
    ("6(d)(i)", 4, [14], [27, 28], ["2.1", "2.2"], "Trace array total algorithm"),
    ("6(d)(ii)", 2, [15], [29], ["2.2"], "Refine array loop for more stages"),
    ("6(d)(iii)", 1, [15], [29], ["2.2"], "Output a labelled count"),
    ("6(e)", 6, [16], [30], ["2.2", "2.3"], "Ticket booking algorithm with repetition"),
]

SUBTOPICS = {
    "1(a)": "Testing", "1(b)(i)": "Validation",
    "1(b)(ii)": "Variables", "1(b)(iii)": "Boolean expressions",
    "2(a)": "Flowcharts", "2(b)(i)": "Iteration",
    "2(b)(ii)": "Programming constructs", "2(c)": "IDE tools",
    "3(a)": "Sorting algorithms", "3(b)": "Sorting algorithms",
    "3(c)(i)": "Searching algorithms", "3(c)(ii)": "Searching algorithms",
    "4(a)": "File handling", "4(b)": "Data types",
    "5(a)": "Logic circuits", "5(b)": "Boolean expressions",
    "5(c)": "Computational thinking", "5(d)": "Validation",
    "6(a)(i)": "Inputs and outputs", "6(a)(ii)": "Selection",
    "6(b)(i)": "SQL", "6(b)(ii)": "Databases",
    "6(b)(iii)": "Data types", "6(c)(i)": "Functions",
    "6(c)(ii)": "Functions", "6(d)(i)": "Trace tables",
    "6(d)(ii)": "Iteration", "6(d)(iii)": "Inputs and outputs",
    "6(e)": "Iteration",
}
