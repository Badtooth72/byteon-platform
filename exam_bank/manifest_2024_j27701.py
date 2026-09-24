"""Question boundaries and topic tags for OCR J277/01 June 2024."""

from manifest import TOPICS

PAPER = {
    "paper_id": "ocr-j277-01-2024-06", "awarding_body": "OCR",
    "qualification": "GCSE Computer Science", "specification": "J277",
    "component": "J277/01", "title": "Computer Systems", "series": "June",
    "year": 2024, "duration_minutes": 90, "total_marks": 80,
    "source_kind": "official_past_paper",
}

# label, marks, question pages, scheme pages, topic codes, short index summary
ITEMS = [
    ("1(a)", 3, [2], [8], ["1.2"], "Binary and denary conversion"),
    ("1(b)", 4, [2], [8], ["1.2"], "Binary ranges, colour depth and character sets"),
    ("1(c)", 1, [2], [8], ["1.2"], "Four-place left binary shift"),
    ("1(d)", 3, [3], [9], ["1.2"], "Hexadecimal to denary conversion"),
    ("1(e)", 2, [3], [9], ["1.2"], "Eight-bit binary addition"),
    ("2(a)(i)", 2, [3], [10], ["1.3"], "IPv4 and IPv6 examples"),
    ("2(a)(ii)", 2, [4], [10], ["1.3"], "MAC address format"),
    ("2(b)(i)", 4, [4], [11], ["1.3"], "Benefits of a wired airport network"),
    ("2(b)(ii)", 3, [4], [12], ["1.3"], "Reasons for airport wireless access"),
    ("2(c)(i)", 3, [5], [12, 13], ["1.3"], "Draw a star topology"),
    ("2(c)(ii)", 2, [5], [13], ["1.3"], "Star versus mesh topology"),
    ("2(c)(iii)", 3, [5], [13], ["1.3"], "Role of a switch"),
    ("3(a)", 4, [6], [14], ["1.5"], "Operating system functions"),
    ("3(b)", 6, [6], [14], ["1.5"], "Encryption and defragmentation utilities"),
    ("4", 8, [8, 9], [15, 16], ["1.6"], "Open source versus proprietary licensing"),
    ("5(a)(i)", 1, [10], [17], ["1.2"], "Identify sound sampling"),
    ("5(a)(ii)", 2, [10], [17], ["1.2"], "Effect of bit depth on sound"),
    ("5(b)(i)", 4, [10], [18], ["1.2"], "Choose secondary storage"),
    ("5(b)(ii)", 1, [10], [18], ["1.2"], "Other secondary storage type"),
    ("5(b)(iii)", 1, [11], [18], ["1.2"], "Compare storage capacities"),
    ("5(b)(iv)", 2, [11], [19], ["1.2"], "Estimate recording storage in GB"),
    ("6(a)", 2, [12], [19], ["1.1"], "Fetch-execute cycle"),
    ("6(b)", 4, [12], [20], ["1.1"], "CPU register names and purposes"),
    ("6(c)", 3, [12], [20], ["1.1"], "CPU performance characteristics"),
    ("7(a)", 3, [13], [21], ["1.1"], "Embedded system characteristics"),
    ("7(b)(i)", 2, [13], [21], ["1.2"], "ROM contents in an embedded system"),
    ("7(b)(ii)", 3, [13], [21], ["1.2"], "RAM data in an embedded system"),
    ("7(b)(iii)", 2, [13], [21], ["1.2"], "Why virtual memory is unnecessary"),
]

SUBTOPICS = {
    "1(a)": "Number representation", "1(b)": "Number representation",
    "1(c)": "Binary arithmetic", "1(d)": "Number representation", "1(e)": "Binary arithmetic",
    "2(a)(i)": "Network addressing", "2(a)(ii)": "Network addressing",
    "2(b)(i)": "Network connections", "2(b)(ii)": "Network connections",
    "2(c)(i)": "Network topology", "2(c)(ii)": "Network topology", "2(c)(iii)": "Network hardware",
    "3(a)": "Operating systems", "3(b)": "Utility software", "4": "Software licensing",
    "5(a)(i)": "Sound representation", "5(a)(ii)": "Sound representation",
    "5(b)(i)": "Secondary storage", "5(b)(ii)": "Secondary storage",
    "5(b)(iii)": "Storage capacity", "5(b)(iv)": "Storage capacity",
    "6(a)": "CPU operation", "6(b)": "CPU registers", "6(c)": "CPU performance",
    "7(a)": "Embedded systems", "7(b)(i)": "Primary memory",
    "7(b)(ii)": "Primary memory", "7(b)(iii)": "Virtual memory",
}
