"""Reviewed question boundaries and topic tags for OCR J277/01 June 2025.

Summaries are navigation aids. The original paper and mark scheme remain the
authoritative source until each item has been transcribed and checked.
"""

PAPER = {
    "paper_id": "ocr-j277-01-2025-06",
    "awarding_body": "OCR",
    "qualification": "GCSE Computer Science",
    "specification": "J277",
    "component": "J277/01",
    "title": "Computer Systems",
    "series": "June",
    "year": 2025,
    "duration_minutes": 90,
    "total_marks": 80,
    "source_kind": "official_past_paper",
}

TOPICS = [
    {"code": "1.1", "name": "Systems architecture"},
    {"code": "1.2", "name": "Memory and storage"},
    {"code": "1.3", "name": "Computer networks, connections and protocols"},
    {"code": "1.4", "name": "Network security"},
    {"code": "1.5", "name": "Systems software"},
    {"code": "1.6", "name": "Ethical, legal, cultural and environmental impacts"},
]

# label, marks, question pages, mark scheme pages, topics, brief index summary
ITEMS = [
    ("1(a)", 6, [2], [8], ["1.2"], "How sound is sampled and represented"),
    ("1(b)(i)", 1, [3], [8], ["1.2"], "Definition of a pixel"),
    ("1(b)(ii)", 2, [3], [8], ["1.2"], "Bitmap file size calculation"),
    ("1(b)(iii)", 1, [3], [8], ["1.2"], "Bits needed for 240 colours"),
    ("1(c)", 4, [3], [9], ["1.2"], "Choice of portable secondary storage"),
    ("2(a)", 5, [4], [10], ["1.5"], "Operating system functions and tasks"),
    ("2(b)(i)", 1, [4], [10], ["1.5"], "Purpose of utility software"),
    ("2(b)(ii)", 3, [4], [10], ["1.5", "1.4"], "Purpose and function of encryption software"),
    ("3", 8, [6, 7], [11, 12], ["1.6"], "Ethical and environmental impact of shorter tablet life"),
    ("4(a)", 2, [8], [12], ["1.3"], "Why a building network is a LAN"),
    ("4(b)(i)", 2, [8], [12], ["1.3"], "Meaning of mesh topology"),
    ("4(b)(ii)", 4, [8], [13], ["1.3"], "Mesh topology benefits and drawbacks"),
    ("4(c)(i)", 3, [9], [14], ["1.3"], "Benefits of Wi-Fi at a youth centre"),
    ("4(c)(ii)", 4, [9], [14], ["1.3"], "Bandwidth and concurrent users"),
    ("4(d)", 5, [10], [15], ["1.3"], "Drawbacks of cloud storage"),
    ("4(e)(i)", 1, [10], [15], ["1.3"], "Device needed for internet access"),
    ("4(e)(ii)", 4, [11], [15], ["1.3"], "Valid and invalid IPv4 addresses"),
    ("4(e)(iii)", 4, [11], [16], ["1.3"], "Resolving a URL to an IP address"),
    ("4(f)", 4, [12], [16], ["1.6"], "Data protection legislation and compliance"),
    ("5(a)", 1, [13], [17], ["1.2"], "Terabytes to megabytes"),
    ("5(b)", 4, [13], [17], ["1.2"], "Denary, binary and hexadecimal conversion"),
    ("5(c)", 2, [14], [17], ["1.2"], "Eight-bit binary addition"),
    ("5(d)", 1, [14], [17], ["1.2"], "Two-place right binary shift"),
    ("5(e)", 2, [14], [17], ["1.2"], "Binary shift to multiply by eight"),
    ("6(a)", 2, [15], [18], ["1.2"], "ASCII representation of a word"),
    ("6(b)", 2, [15], [18], ["1.2"], "Unicode benefit and drawback"),
    ("6(c)", 2, [15], [18], ["1.1"], "CPU registers and their purposes"),
]

SUBTOPICS = {
    "1(a)": "Sound representation", "1(b)(i)": "Image representation",
    "1(b)(ii)": "Image representation", "1(b)(iii)": "Image representation",
    "1(c)": "Secondary storage", "2(a)": "Operating systems",
    "2(b)(i)": "Utility software", "2(b)(ii)": "Utility software",
    "3": "Environmental impacts", "4(a)": "Network types",
    "4(b)(i)": "Network topology", "4(b)(ii)": "Network topology",
    "4(c)(i)": "Network connections", "4(c)(ii)": "Network performance",
    "4(d)": "Cloud storage", "4(e)(i)": "Network hardware",
    "4(e)(ii)": "Network addressing", "4(e)(iii)": "DNS",
    "4(f)": "Data protection", "5(a)": "Storage capacity",
    "5(b)": "Number representation", "5(c)": "Binary arithmetic",
    "5(d)": "Binary arithmetic", "5(e)": "Binary arithmetic",
    "6(a)": "Character sets", "6(b)": "Character sets",
    "6(c)": "CPU registers",
}
