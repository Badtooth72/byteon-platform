"""Public-safe indexes for the June 2022 and 2023 OCR J277 papers.

Summaries and tags are navigation aids; the private source PDFs remain authoritative.
"""

from manifest import TOPICS as SYSTEM_TOPICS
from manifest_j27702 import TOPICS as PROGRAMMING_TOPICS


# label | marks | question page | mark-scheme page | topic | short summary
ROWS = {
    (2022, 1): """
1(a)|4|2|7|1.2|Binary units table
1(b)|2|2|7|1.2|Denary to binary
1(c)|2|2|7|1.2|Hexadecimal to denary
1(d)|1|2|7|1.2|Binary to hexadecimal
1(e)|1|2|7|1.2|Four-bit range
1(f)|1|2|7|1.2|Binary right shift
2|4|3|8|1.1|CPU components and registers table
3(a)(i)|3|4|9|1.3|Network performance and device count
3(a)(ii)|1|4|9|1.3|Network performance factor
3(b)|7|4|10|1.3|Web access and IPv4 terminology
3(c)|2|5|10|1.3|Ethernet standard
3(d)|3|5|10|1.3|Router tasks
3(e)|2|5|11|1.4|Reasons for encryption
3(f)|2|5|11|1.3|Email and secure web protocols
4|8|6|12|1.6|AI in social networking
5(a)|2|8|13|1.4|Physical security methods
5(b)|6|8|13|1.4|Software security methods
5(c)|5|9|15|1.6|Legislation classification table
6(a)(i)|3|10|15|1.2|Analogue sound sampling
6(a)(ii)|3|10|16|1.2|Sound file effects table
6(b)(i)|1|10|16|1.2|ASCII character code
6(b)(ii)|1|11|16|1.2|Character sets
6(c)|3|11|16|1.2|Image metadata
6(d)(i)|2|11|17|1.2|Compression benefits
6(d)(ii)|2|11|17|1.2|Lossy compression suitability
7(a)(i)|1|12|18|1.2|RAM and ROM
7(a)(ii)|2|12|18|1.2|RAM contents
7(b)(i)|2|12|18|1.2|Secondary storage need
7(b)(ii)|4|12|19|1.2|Secondary storage choice
""",
    (2022, 2): """
1(a)|4|2|7|2.2|Selection and iteration table
1(b)|1|2|7|2.2|Score increment statement
1(c)|2|2|7|2.1|Decomposition
2(a)(i)|3|3|8|2.4|Logic circuit diagram
2(a)(ii)|2|3|8|2.4|Truth table purpose
2(a)(iii)|1|3|8|2.4|Truth table row count
2(b)|5|4|9|2.1|Discount flowchart
2(c)|2|5|10|2.1|Service charge inputs
2(d)(i)|2|6|10|2.2|Casting
2(d)(ii)|4|6|10|2.2|Staff ID trace table
3(a)|3|7|11|2.1|Merge sort stages
3(b)|4|8|11|2.1|Binary search
3(c)|2|8|11|2.1|Linear search
4(a)|2|9|12|2.3|Code maintainability
4(b)(i)|2|9|12|2.2|Arithmetic operators table
4(b)(ii)|5|10|12|2.5|Translators and languages
4(c)|6|11|13|2.2|Total and average algorithm
5(a)(i)|2|12|14|2.2|Booking data types
5(a)(ii)|1|12|14|2.2|Boolean booking field
5(a)(iii)|4|13|14|2.2|Correct SQL query
5(b)(i)|5|14|15|2.2|Booking validation code
5(b)(ii)|3|15|16|2.3|Nights test plan table
5(c)(i)|4|16|16|2.2|Room price function
5(c)(ii)|3|16|17|2.2|Call room price function
5(d)|2|17|17|2.2|Room array loop errors
5(e)|6|18|18|2.2|Parking charge algorithm
""",
    (2023, 1): """
1(a)|1|2|8|1.2|Binary representation statement
1(b)|4|2|8|1.2|Denary binary hexadecimal table
1(c)|1|3|8|1.2|Largest file size
1(d)|1|3|8|1.2|Equivalent file sizes
1(e)|2|3|8|1.2|Binary addition
1(f)|2|3|9|1.2|Binary shift
2(a)(i)|4|4|10|1.3|Protocols table
2(a)(ii)|2|4|10|1.3|Protocol layers
2(b)(i)|1|4|10|1.3|LAN feature
2(b)(ii)|4|5|11|1.3|Wireless LAN benefits
2(b)(iii)|2|5|11|1.3|Wireless LAN drawbacks
3(a)|5|6|12|1.2|Character set terminology
3(b)(i)|1|6|12|1.2|Image metadata definition
3(b)(ii)|2|7|12|1.2|Pixel colour grid
3(b)(iii)|1|7|12|1.2|Colour depth range
3(b)(iv)|2|7|13|1.2|Colour depth effects
3(c)(i)|3|8|13|1.2|Text compression choice
3(c)(ii)|3|8|14|1.2|Image compression choice
4(a)|4|9|15|1.4|Security threats and protection table
4(b)|3|9|15|1.4|Other security threat
5(a)(i)|2|10|16|1.2|Primary and secondary storage
5(a)(ii)|2|10|17|1.2|Secondary storage example
5(a)(iii)|4|10|18|1.2|Virtual memory statements
5(b)|1|11|18|1.5|Utility software
5(c)(i)|3|11|19|1.3|Client computer
5(c)(ii)|3|11|19|1.3|Server computer
5(d)(i)|4|12|20|1.6|Proprietary software benefits
5(d)(ii)|2|12|20|1.6|Open source user benefit
6|8|13|21|1.6|Facial recognition impacts
7|3|14|23|1.1|Embedded system in a car
""",
    (2023, 2): """
1(a)|4|2|8|2.5|Programming language table
1(b)|1|2|8|2.2|Integer addition pseudocode
1(c)(i)|1|2|9|2.2|Exponent operator
1(c)(ii)|1|2|9|2.2|Modulus operator
1(c)(iii)|1|3|9|2.2|Subtraction operator
1(d)|3|3|10|2.2|Loop trace table
2(a)|2|4|11|2.3|Syntax and logic errors
2(b)|4|4|12|2.3|Correct logic errors
3(a)|2|5|13|2.1|Insertion sort temporary value
3(b)|2|5|13|2.1|Nested loop types
3(c)(i)|2|6|14|2.1|Insertion and bubble sort difference
3(c)(ii)|2|6|15|2.1|Insertion and bubble sort similarities
4(a)|3|7|16|2.4|Floodlight logic diagram
4(b)|2|8|17|2.4|Identify gates from truth tables
5(a)(i)|2|9|18|2.3|Reasons to test programs
5(a)(ii)|2|9|19|2.3|Test type table
5(a)(iii)|4|9|20|2.3|Test features
5(b)|6|10|22|2.3|Game input validation
5(c)|6|11|24|2.2|Adding game algorithm
6(a)|4|13|25|2.2|Alarm data types table
6(b)|4|13|25|2.4|Alarm Boolean expression
6(c)(i)|1|14|27|2.2|Sensor code check
6(c)(ii)|1|14|27|2.2|Sensor reset call
6(c)(iii)|1|14|27|2.2|Sensor code output
6(c)(iv)|1|14|28|2.2|Sensor code condition
6(c)(v)|2|14|28|2.2|Sensor reset algorithm
6(d)|3|15|28|2.2|Event log SQL query
6(e)|6|16|29|2.2|Save logs procedure
6(f)(i)|1|17|29|2.2|Data type conversion
6(f)(ii)|6|18|30|2.2|Total sensor time program
""",
}


def manifest(year, component):
    topic_defs = SYSTEM_TOPICS if component == 1 else PROGRAMMING_TOPICS
    items = []
    subtopics = {}
    for raw in ROWS[(year, component)].strip().splitlines():
        label, marks, question_page, scheme_page, topic, summary = raw.split("|", 5)
        items.append((label, int(marks), [int(question_page)], [int(scheme_page)], [topic], summary))
        subtopics[label] = summary
    paper = {
        "paper_id": f"ocr-j277-0{component}-{year}-06", "awarding_body": "OCR",
        "qualification": "GCSE Computer Science", "specification": "J277",
        "component": f"J277/0{component}",
        "title": "Computer Systems" if component == 1 else "Computational Thinking, Algorithms and Programming",
        "series": "June", "year": year, "duration_minutes": 90,
        "total_marks": 80, "source_kind": "official_past_paper",
    }
    return paper, items, topic_defs, subtopics
