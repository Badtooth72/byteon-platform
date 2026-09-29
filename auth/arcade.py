"""Achievement-gated, short practice games. Course progress remains separate."""

from datetime import datetime
from random import SystemRandom
from secrets import token_urlsafe

from flask import jsonify, redirect, render_template, request, session, url_for


RANDOM = SystemRandom()
GAMES = (
    {"slug": "hex-snake", "title": "Hex Snake", "icon": "▣", "unlock": 200,
     "description": "Race around the neon maze, growing your snake by catching the right hex tiles."},
    {"slug": "bit-flip", "title": "Bit Flip", "icon": "◧", "unlock": 350,
     "description": "Flip eight bits and fire at descending hex invaders before they land."},
    {"slug": "packet-patrol", "title": "Packet Patrol", "icon": "⇌", "unlock": 500,
     "description": "Steer a moving packet into the right lane to defend protocols, searches, sorts and security."},
    {"slug": "logic-defender", "title": "Logic Gate Defender", "icon": "∧", "unlock": 650,
     "description": "Choose the right gate to stop hazards before they reach the core."},
    {"slug": "ctrl-alt-defeat", "title": "CTRL ALT DEFEAT", "icon": "✹", "unlock": 800,
     "description": "Shoot digital threats by powering your ship with GCSE knowledge."},
    {"slug": "cpu-tower", "title": "CPU Platform Tower", "icon": "▥", "unlock": 950,
     "description": "Climb a neon processor tower by landing on the right hardware platform."},
)
GAME_BY_SLUG = {game["slug"]: game for game in GAMES}
ROUNDS_PER_RUN = 10

PACKET_QUESTIONS = (
    ("Protocol", "A browser must send a password securely to a website. Which protocol?", ("HTTPS", "HTTP", "SMTP", "FTP"), "HTTPS", "HTTPS encrypts web traffic in transit."),
    ("Protocol", "A mail server needs to send a message to another mail server. Which protocol?", ("SMTP", "IMAP", "DNS", "HTTP"), "SMTP", "SMTP is used to send email."),
    ("Protocol", "A device knows a website name but needs its IP address. Which service?", ("DNS", "FTP", "SMTP", "IMAP"), "DNS", "DNS resolves a domain name to an IP address."),
    ("Protocol", "A pupil wants to synchronise received email across devices. Which protocol?", ("IMAP", "SMTP", "FTP", "HTTP"), "IMAP", "IMAP commonly keeps mailbox state in sync."),
    ("Security", "A fake school login page asks for a password. What is the attack?", ("Phishing", "Defragmentation", "Encryption", "Compression"), "Phishing", "Phishing tricks people into revealing credentials."),
    ("Security", "An ordinary student account must not open staff files. What control helps?", ("Access permissions", "More RAM", "A faster switch", "Compression"), "Access permissions", "Permissions restrict what an authenticated account may access."),
    ("Security", "A stolen laptop contains personal data. What protects the stored files?", ("Encryption", "DNS", "A larger cache", "A star topology"), "Encryption", "Encryption protects stored data from being read without its key."),
    ("Security", "Thousands of password guesses are tried against one account. What attack?", ("Brute force", "Phishing", "Packet switching", "Binary search"), "Brute force", "A brute-force attack tries many possible passwords."),
    ("Search", "Find 7 in an unsorted list. Which search always works?", ("Linear search", "Binary search", "Merge sort", "Insertion sort"), "Linear search", "Linear search checks items in order and does not require sorting."),
    ("Search", "Binary search checks the middle of 1, 3, 5, 7, 9, 11, 13. Looking for 11, which side next?", ("Right half", "Left half", "Start over", "Neither side"), "Right half", "11 is greater than 7, so discard the left half."),
    ("Search", "Before binary search begins, what must be true of the list?", ("It is sorted", "It has no duplicates", "It contains strings", "It has an even length"), "It is sorted", "Binary search relies on the order of the data."),
    ("Sort", "One bubble-sort pass over 4, 1, 3, 2 gives which list?", ("1, 3, 2, 4", "1, 2, 3, 4", "4, 3, 2, 1", "4, 1, 2, 3"), "1, 3, 2, 4", "Adjacent swaps move 4 to the end in the first pass."),
    ("Sort", "Which sort repeatedly splits a list, then combines sorted parts?", ("Merge sort", "Bubble sort", "Linear search", "Binary search"), "Merge sort", "Merge sort divides and merges ordered sublists."),
    ("Sort", "In insertion sort, where does the next item go?", ("Into its correct place in the sorted part", "Always at the end", "Into the middle regardless of value", "Into a random position"), "Into its correct place in the sorted part", "Insertion sort grows a sorted portion one item at a time."),
)

LOGIC_QUESTIONS = (
    ("Logic", "Which gate outputs 1 only when both inputs are 1?", ("AND", "OR", "NOT", "None"), "AND", "AND needs both inputs to be 1."),
    ("Logic", "Which gate outputs 1 when either input is 1?", ("OR", "AND", "NOT", "None"), "OR", "OR needs at least one input to be 1."),
    ("Logic", "Which gate reverses one input?", ("NOT", "AND", "OR", "None"), "NOT", "NOT inverts a single Boolean value."),
    ("Logic", "A=1 and B=0. What is A ∧ B?", ("0", "1", "2", "Undefined"), "0", "AND requires both inputs to be 1."),
    ("Logic", "A=1 and B=0. What is A ∨ B?", ("1", "0", "2", "Undefined"), "1", "OR is 1 when at least one input is 1."),
    ("Logic", "A=0. What is ¬A?", ("1", "0", "2", "Undefined"), "1", "NOT reverses 0 to 1."),
    ("Logic", "A=1, B=1. What is ¬(A ∧ B)?", ("0", "1", "2", "Undefined"), "0", "AND gives 1; NOT changes it to 0."),
    ("Logic", "A=0, B=1. What is ¬A ∧ B?", ("1", "0", "2", "Undefined"), "1", "NOT A is 1; 1 AND 1 is 1."),
    ("Logic", "A=0, B=0. What is A ∨ B?", ("0", "1", "2", "Undefined"), "0", "Neither input is 1, so OR gives 0."),
    ("Logic", "A=1, B=0. What is ¬(A ∨ B)?", ("0", "1", "2", "Undefined"), "0", "OR gives 1; NOT changes it to 0."),
)

SHOOTER_QUESTIONS = (
    ("Malware", "Which malicious program spreads by copying itself between computers?", ("Worm", "Compiler", "Firewall", "Cache"), "Worm", "A worm self-replicates across systems."),
    ("Security", "What filters network traffic against rules?", ("Firewall", "RAM", "ALU", "DNS"), "Firewall", "A firewall permits or blocks traffic according to rules."),
    ("Security", "What protects data on a stolen laptop from being read?", ("Encryption", "Compression", "Defragmentation", "Caching"), "Encryption", "Encryption makes stored data unreadable without the key."),
    ("Malware", "What is software that secretly records keystrokes?", ("Keylogger", "Hypervisor", "Compiler", "Protocol"), "Keylogger", "A keylogger records key presses without permission."),
    ("Networks", "Which service translates domain names into IP addresses?", ("DNS", "SMTP", "FTP", "IMAP"), "DNS", "DNS resolves names to IP addresses."),
    ("Hardware", "Which component performs arithmetic and logic?", ("ALU", "CU", "ROM", "NIC"), "ALU", "The arithmetic logic unit performs calculations and logic."),
    ("Data", "How many bits are in a byte?", ("8", "4", "16", "32"), "8", "A byte has eight bits."),
    ("Programming", "Which construct repeats instructions?", ("Iteration", "Selection", "Sequence", "Abstraction"), "Iteration", "Iteration means repeating instructions."),
    ("Security", "A fake login page steals passwords. What is this?", ("Phishing", "Sorting", "Encryption", "Caching"), "Phishing", "Phishing tricks people into revealing credentials."),
    ("Data", "Which compression reconstructs the original exactly?", ("Lossless", "Lossy", "Analogue", "Sampling"), "Lossless", "Lossless compression preserves all original information."),
)

CPU_QUESTIONS = (
    ("CPU", "Which register stores the address of the next instruction?", ("Program counter", "MDR", "Accumulator", "Cache"), "Program counter", "The program counter stores the next instruction address."),
    ("CPU", "Which register holds a memory address being accessed?", ("MAR", "MDR", "ALU", "ROM"), "MAR", "The memory address register holds an address."),
    ("CPU", "Which register holds data transferred to or from memory?", ("MDR", "MAR", "CU", "Cache"), "MDR", "The memory data register holds transferred data."),
    ("CPU", "Which CPU part performs arithmetic and logical operations?", ("ALU", "CU", "ROM", "NIC"), "ALU", "The arithmetic logic unit performs arithmetic and logic."),
    ("CPU", "Which CPU part coordinates and decodes instructions?", ("Control unit", "ALU", "Hard disk", "GPU"), "Control unit", "The control unit coordinates CPU activity."),
    ("Cycle", "What is the first stage of the fetch–decode–execute cycle?", ("Fetch", "Decode", "Execute", "Store"), "Fetch", "The next instruction is fetched from memory first."),
    ("Cycle", "What stage follows fetch?", ("Decode", "Execute", "Upload", "Compress"), "Decode", "The fetched instruction is decoded before execution."),
    ("Cycle", "After decode, what does the CPU do?", ("Execute", "Fetch", "Archive", "Boot"), "Execute", "The decoded instruction is executed."),
    ("Memory", "Which fast store keeps frequently used data close to the CPU?", ("Cache", "Optical disc", "ROM", "Cloud"), "Cache", "Cache reduces slower main-memory accesses."),
    ("CPU", "Which register can hold the result of an ALU operation?", ("Accumulator", "MAR", "PC", "NIC"), "Accumulator", "The accumulator can hold intermediate results."),
)

QUESTION_BANKS = {"packet-patrol": PACKET_QUESTIONS, "logic-defender": LOGIC_QUESTIONS,
                  "ctrl-alt-defeat": SHOOTER_QUESTIONS, "cpu-tower": CPU_QUESTIONS}


def make_round(slug, used=None):
    if slug == "hex-snake":
        target = RANDOM.randrange(0, 256)
        distractors = RANDOM.sample([value for value in range(256) if value != target], 3)
        choices = [f"{value:02X}" for value in [target, *distractors]]
        RANDOM.shuffle(choices)
        return {"kind": "snake", "prompt": f"Steer to the hex value of {target}₁₀", "choices": choices,
                "correct": f"{target:02X}", "explanation": f"{target} in hexadecimal is {target:02X}."}
    if slug == "bit-flip":
        targets = RANDOM.sample(range(0, 256), 3)
        return {"kind": "bits", "prompt": "Match an invader's hexadecimal value, then fire",
                "targets": [f"{target:02X}" for target in targets], "target": f"{targets[0]:02X}",
                "correct": f"{targets[0]:08b}", "explanation": "Select an invader, set its 8-bit binary value and fire."}
    bank = QUESTION_BANKS[slug]
    available = [i for i in range(len(bank)) if i not in (used or [])]
    if not available:
        available = list(range(len(bank)))
    question_id = RANDOM.choice(available)
    category, prompt, options, correct, explanation = bank[question_id]
    choices = list(options)
    RANDOM.shuffle(choices)
    return {"kind": slug, "category": category, "prompt": prompt, "choices": choices,
            "correct": correct, "explanation": explanation, "question_id": question_id}


def public_round(round_data):
    return {key: value for key, value in round_data.items() if key not in {"correct", "explanation", "question_id"}}


def register_arcade(app, mongo, achievements_for_user):
    def current_user():
        username = session.get("username")
        return mongo.db.users.find_one({"username": username}) if username else None

    def points_for(user):
        return achievements_for_user(user)["points"]

    def can_play(user, game):
        return user.get("role") == "admin" or points_for(user) >= game["unlock"]

    def catalogue(user):
        points = points_for(user)
        records = (user.get("activities") or {}).get("arcade") or {}
        return [{**game, "unlocked": user.get("role") == "admin" or points >= game["unlock"],
                 "preview": user.get("role") == "admin" and points < game["unlock"],
                 "best": (records.get(game["slug"]) or {}).get("best", 0),
                 "plays": (records.get(game["slug"]) or {}).get("plays", 0)} for game in GAMES]

    @app.route("/games")
    def arcade_home():
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        return render_template("arcade_home.html", games=catalogue(user), points=points_for(user), preview=user.get("role") == "admin")

    @app.route("/games/<slug>")
    def arcade_game(slug):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        game = GAME_BY_SLUG.get(slug)
        if not game:
            return "Game not found", 404
        if not can_play(user, game):
            return redirect(url_for("arcade_home"))
        record = ((user.get("activities") or {}).get("arcade") or {}).get(slug) or {}
        return render_template("arcade_game.html", game=game, best=record.get("best", 0), preview=user.get("role") == "admin" and points_for(user) < game["unlock"])

    def game_access(slug):
        user = current_user()
        game = GAME_BY_SLUG.get(slug)
        if not user:
            return None, (jsonify({"error": "Sign in to play"}), 401)
        if not game:
            return None, (jsonify({"error": "Unknown game"}), 404)
        if not can_play(user, game):
            return None, (jsonify({"error": f"Earn {game['unlock']} achievement points to unlock this game"}), 403)
        return user, None

    @app.post("/api/games/<slug>/start")
    def arcade_start(slug):
        user, error = game_access(slug)
        if error:
            return error
        first = make_round(slug)
        state = {"slug": slug, "nonce": token_urlsafe(16), "round": 1, "score": 0,
                 "started": datetime.utcnow().isoformat(), "used": [first["question_id"]] if slug in QUESTION_BANKS else [],
                 "challenge": first}
        session.pop("arcade_run", None)
        mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {f"arcade_runs.{slug}": state}})
        return jsonify({"round": 1, "total": ROUNDS_PER_RUN, "score": 0,
                        "run_id": state["nonce"], "challenge": public_round(first)})

    @app.post("/api/games/<slug>/answer")
    def arcade_answer(slug):
        user, error = game_access(slug)
        if error:
            return error
        state = ((user.get("arcade_runs") or {}).get(slug) or {})
        data = request.get_json(silent=True) or {}
        if state.get("slug") != slug or not state.get("challenge") or data.get("run_id") != state.get("nonce"):
            return jsonify({"error": "Start a new game first"}), 409
        answer = data.get("answer")
        if not isinstance(answer, str) or len(answer) > 80:
            return jsonify({"error": "Choose a valid answer"}), 400
        challenge = state["challenge"]
        if slug != "bit-flip" and answer not in challenge["choices"] and answer != "TIMEOUT" and not (slug == "hex-snake" and answer == "CRASH"):
            return jsonify({"error": "Choose a displayed answer"}), 400
        if slug == "bit-flip" and answer != "TIMEOUT":
            parts = answer.split(":", 1)
            if len(parts) != 2 or parts[0] not in {"0", "1", "2"} or len(parts[1]) != 8 or any(bit not in "01" for bit in parts[1]):
                return jsonify({"error": "Choose an invader and set all eight bits"}), 400
            selected = int(parts[0])
            target = int(challenge["targets"][selected], 16)
            correct = parts[1] == f"{target:08b}"
            explanation = f"{target:02X}₁₆ is {target:08b}₂ ({target}₁₀)."
        else:
            correct = answer == challenge["correct"]
            explanation = challenge["explanation"]
        if correct:
            state["score"] += 10
        result = {"correct": correct, "explanation": explanation, "score": state["score"],
                  "round": state["round"], "total": ROUNDS_PER_RUN}
        if state["round"] >= ROUNDS_PER_RUN:
            result["finished"] = True
            result["best"] = max(state["score"], ((user.get("activities") or {}).get("arcade") or {}).get(slug, {}).get("best", 0))
            mongo.db.users.update_one({"_id": user["_id"]}, {
                "$inc": {f"activities.arcade.{slug}.plays": 1},
                "$max": {f"activities.arcade.{slug}.best": state["score"]},
                "$set": {f"activities.arcade.{slug}.latest": state["score"],
                         f"activities.arcade.{slug}.last_played": datetime.utcnow()},
            })
            mongo.db.arcade_attempts.insert_one({"username": user["username"], "game": slug,
                                                  "score": state["score"], "rounds": ROUNDS_PER_RUN,
                                                  "played_at": datetime.utcnow()})
            mongo.db.users.update_one({"_id": user["_id"]}, {"$unset": {f"arcade_runs.{slug}": ""}})
        else:
            state["round"] += 1
            next_round = make_round(slug, state["used"])
            if slug in QUESTION_BANKS:
                state["used"].append(next_round["question_id"])
            state["challenge"] = next_round
            mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {f"arcade_runs.{slug}": state}})
            result["next"] = public_round(next_round)
        return jsonify(result)

    return catalogue
