from datetime import datetime, timezone
from secrets import choice

CHALLENGES = (
    {"id":"identify-and","stage":1,"type":"choice","title":"Gate detective","prompt":"Which gate outputs 1 only when both inputs are 1?","options":["AND","OR","NOT"],"answer":"AND","explanation":"AND needs every input to be 1."},
    {"id":"identify-or","stage":1,"type":"choice","title":"Gate detective","prompt":"Which gate outputs 1 when either input is 1?","options":["AND","OR","NOT"],"answer":"OR","explanation":"OR outputs 1 when one or both inputs are 1."},
    {"id":"identify-not","stage":1,"type":"choice","title":"Gate detective","prompt":"Which gate reverses a single input?","options":["AND","OR","NOT"],"answer":"NOT","explanation":"NOT inverts its input."},
    {"id":"truth-and","stage":2,"type":"truth","gate":"AND","title":"AND truth table","prompt":"Complete the output column for A ∧ B.","inputs":[[0,0],[0,1],[1,0],[1,1]],"answer":[0,0,0,1],"explanation":"AND (∧) outputs 1 only when both inputs are 1."},
    {"id":"truth-or","stage":2,"type":"truth","gate":"OR","title":"OR truth table","prompt":"Complete the output column for A ∨ B.","inputs":[[0,0],[0,1],[1,0],[1,1]],"answer":[0,1,1,1],"explanation":"OR (∨) outputs 1 when either or both inputs are 1."},
    {"id":"truth-not","stage":2,"type":"truth","gate":"NOT","title":"NOT truth table","prompt":"Complete the output column for ¬A.","inputs":[[0],[1]],"answer":[1,0],"explanation":"NOT (¬) reverses the input."},
    {"id":"build-alarm","stage":3,"type":"circuit","topology":"three-input","title":"Build an alarm","prompt":"Build P = (A ∨ B) ∧ (¬C).","slots":3,"options":["AND","OR","NOT"],"answer":["OR","NOT","AND"],"explanation":"OR combines A and B, NOT reverses C, then AND joins the branches."},
    {"id":"master-expression","stage":4,"type":"truth","title":"GCSE challenge","prompt":"Complete P for (A ∧ B) ∨ C.","inputs":[[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1]],"answer":[0,1,0,1,0,1,1,1],"explanation":"Evaluate A AND B first, then OR that result with C."},
    {"id":"extension-nand","stage":5,"type":"truth","gate":"NAND","title":"Above the spec: NAND","prompt":"Optional extension: complete A NAND B.","inputs":[[0,0],[0,1],[1,0],[1,1]],"answer":[1,1,1,0],"explanation":"NAND is the inverse of AND."},
    {"id":"extension-xor","stage":5,"type":"truth","gate":"XOR","title":"Above the spec: XOR","prompt":"Optional extension: complete A ⊕ B.","inputs":[[0,0],[0,1],[1,0],[1,1]],"answer":[0,1,1,0],"explanation":"XOR outputs 1 when the inputs differ."},
)

def public_challenges():
    return [{k:v for k,v in item.items() if k not in {"answer","explanation"}} for item in CHALLENGES]

def build_random_challenge(random_choice=choice):
    first = random_choice(["AND", "OR"])
    selected = {
        "prompt": f"Build P = ¬(A {gate_symbol(first)} B).",
        "answer": [first, "NOT"],
    }
    return {
        "id": "random",
        "stage": "random",
        "type": "circuit",
        "title": "Random circuit challenge",
        "options": ["AND", "OR", "NOT"],
        "topology": "two-stage",
        "slots": len(selected["answer"]),
        "explanation": "Read the expression from the innermost brackets outwards.",
        **selected,
    }

def gate_symbol(gate):
    return {"AND": "∧", "OR": "∨", "NOT": "¬"}[gate]

def public_challenge(challenge):
    return {k: v for k, v in challenge.items() if k not in {"answer", "explanation"}}

def mark_attempt(challenge_id, response):
    challenge = next((item for item in CHALLENGES if item["id"] == challenge_id), None)
    if not challenge: raise ValueError("Unknown challenge")
    return mark_challenge(challenge, response)

def mark_challenge(challenge, response):
    if challenge["type"] == "choice": normalised = str(response).strip().upper()
    elif challenge["type"] == "circuit":
        if not isinstance(response,list) or len(response) != challenge["slots"]: raise ValueError("Invalid circuit response")
        normalised = [str(value).strip().upper() for value in response]
    else:
        if not isinstance(response,list) or len(response) != len(challenge["inputs"]): raise ValueError("Invalid truth table response")
        if any(value not in (0,1) for value in response): raise ValueError("Truth table values must be 0 or 1")
        normalised = response
    return challenge, normalised == challenge["answer"]

def progress_record(challenge, correct, response, now=None):
    return {"schema_version":1,"score":1 if correct else 0,"correct":correct,"response":response,"stage":challenge["stage"],"date":now or datetime.now(timezone.utc)}
