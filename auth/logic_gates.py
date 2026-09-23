from datetime import datetime, timezone

CHALLENGES = (
    {"id":"identify-and","stage":1,"type":"choice","title":"AND gate","prompt":"Which gate outputs 1 only when both inputs are 1?","options":["AND","OR","NOT"],"answer":"AND","explanation":"AND needs every input to be 1."},
    {"id":"identify-or","stage":1,"type":"choice","title":"OR gate","prompt":"Which gate outputs 1 when either input is 1?","options":["AND","OR","NOT"],"answer":"OR","explanation":"OR outputs 1 when one or both inputs are 1."},
    {"id":"identify-not","stage":1,"type":"choice","title":"NOT gate","prompt":"Which gate reverses a single input?","options":["AND","OR","NOT"],"answer":"NOT","explanation":"NOT inverts its input."},
    {"id":"simulate-nand","stage":2,"type":"truth","title":"NAND simulator","prompt":"Complete the output column for A NAND B.","inputs":[[0,0],[0,1],[1,0],[1,1]],"answer":[1,1,1,0],"explanation":"NAND is the inverse of AND."},
    {"id":"simulate-xor","stage":2,"type":"truth","title":"XOR simulator","prompt":"Complete the output column for A XOR B.","inputs":[[0,0],[0,1],[1,0],[1,1]],"answer":[0,1,1,0],"explanation":"XOR outputs 1 when the inputs differ."},
    {"id":"build-alarm","stage":3,"type":"circuit","title":"Build an alarm","prompt":"Build P = (A OR B) AND (NOT C).","slots":3,"options":["AND","OR","NOT","XOR"],"answer":["OR","NOT","AND"],"labels":["Combine A and B","Transform C","Combine both branches"],"explanation":"OR combines A and B, NOT reverses C, then AND joins the branches."},
    {"id":"build-equality","stage":3,"type":"circuit","title":"Build an equality detector","prompt":"Build P = NOT (A XOR B).","slots":2,"options":["AND","OR","NOT","XOR"],"answer":["XOR","NOT"],"labels":["Compare A and B","Transform the result"],"explanation":"XOR finds different inputs; NOT makes the output 1 when they match."},
    {"id":"master-expression","stage":4,"type":"truth","title":"GCSE challenge","prompt":"Complete P for (A AND B) OR C.","inputs":[[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1]],"answer":[0,1,0,1,0,1,1,1],"explanation":"Evaluate A AND B first, then OR that result with C."},
)

def public_challenges():
    return [{k:v for k,v in item.items() if k not in {"answer","explanation"}} for item in CHALLENGES]

def mark_attempt(challenge_id, response):
    challenge = next((item for item in CHALLENGES if item["id"] == challenge_id), None)
    if not challenge: raise ValueError("Unknown challenge")
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
