"""Achievement-gated, short practice games. Course progress remains separate."""

from datetime import datetime
from random import SystemRandom
from secrets import token_urlsafe

from flask import jsonify, redirect, render_template, request, session, url_for


RANDOM = SystemRandom()
GAMES = (
    {"slug": "hex-snake", "title": "Hex Snake", "icon": "▣", "unlock": 100,
     "description": "Steer the snake towards the hexadecimal value of a denary target."},
    {"slug": "bit-flip", "title": "Bit Flip", "icon": "◧", "unlock": 200,
     "description": "Flip eight bits to match an incoming hexadecimal value."},
    {"slug": "packet-patrol", "title": "Packet Patrol", "icon": "⇌", "unlock": 300,
     "description": "Choose protocols, trace searches and sorts, and defend a network."},
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


def make_round(slug, used=None):
    if slug == "hex-snake":
        target = RANDOM.randrange(0, 256)
        distractors = RANDOM.sample([value for value in range(256) if value != target], 3)
        choices = [f"{value:02X}" for value in [target, *distractors]]
        RANDOM.shuffle(choices)
        return {"kind": "snake", "prompt": f"Steer to the hex value of {target}₁₀", "choices": choices,
                "correct": f"{target:02X}", "explanation": f"{target} in hexadecimal is {target:02X}."}
    if slug == "bit-flip":
        target = RANDOM.randrange(0, 256)
        return {"kind": "bits", "prompt": f"Build {target:02X}₁₆ in eight bits", "target": f"{target:02X}",
                "correct": f"{target:08b}", "explanation": f"{target:02X}₁₆ is {target:08b}₂ ({target}₁₀)."}
    available = [i for i in range(len(PACKET_QUESTIONS)) if i not in (used or [])]
    if not available:
        available = list(range(len(PACKET_QUESTIONS)))
    question_id = RANDOM.choice(available)
    category, prompt, options, correct, explanation = PACKET_QUESTIONS[question_id]
    choices = list(options)
    RANDOM.shuffle(choices)
    return {"kind": "packet", "category": category, "prompt": prompt, "choices": choices,
            "correct": correct, "explanation": explanation, "question_id": question_id}


def public_round(round_data):
    return {key: value for key, value in round_data.items() if key not in {"correct", "explanation", "question_id"}}


def register_arcade(app, mongo, achievements_for_user):
    def current_user():
        username = session.get("username")
        return mongo.db.users.find_one({"username": username}) if username else None

    def points_for(user):
        return achievements_for_user(user)["points"]

    def catalogue(user):
        points = points_for(user)
        records = (user.get("activities") or {}).get("arcade") or {}
        return [{**game, "unlocked": points >= game["unlock"],
                 "best": (records.get(game["slug"]) or {}).get("best", 0),
                 "plays": (records.get(game["slug"]) or {}).get("plays", 0)} for game in GAMES]

    @app.route("/games")
    def arcade_home():
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        return render_template("arcade_home.html", games=catalogue(user), points=points_for(user))

    @app.route("/games/<slug>")
    def arcade_game(slug):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        game = GAME_BY_SLUG.get(slug)
        if not game:
            return "Game not found", 404
        if points_for(user) < game["unlock"]:
            return redirect(url_for("arcade_home"))
        record = ((user.get("activities") or {}).get("arcade") or {}).get(slug) or {}
        return render_template("arcade_game.html", game=game, best=record.get("best", 0))

    def game_access(slug):
        user = current_user()
        game = GAME_BY_SLUG.get(slug)
        if not user:
            return None, (jsonify({"error": "Sign in to play"}), 401)
        if not game:
            return None, (jsonify({"error": "Unknown game"}), 404)
        if points_for(user) < game["unlock"]:
            return None, (jsonify({"error": f"Earn {game['unlock']} achievement points to unlock this game"}), 403)
        return user, None

    @app.post("/api/games/<slug>/start")
    def arcade_start(slug):
        user, error = game_access(slug)
        if error:
            return error
        first = make_round(slug)
        state = {"slug": slug, "nonce": token_urlsafe(16), "round": 1, "score": 0,
                 "started": datetime.utcnow().isoformat(), "used": [first["question_id"]] if slug == "packet-patrol" else [],
                 "challenge": first}
        session["arcade_run"] = state
        return jsonify({"round": 1, "total": ROUNDS_PER_RUN, "score": 0, "challenge": public_round(first)})

    @app.post("/api/games/<slug>/answer")
    def arcade_answer(slug):
        user, error = game_access(slug)
        if error:
            return error
        state = session.get("arcade_run") or {}
        if state.get("slug") != slug or not state.get("challenge"):
            return jsonify({"error": "Start a new game first"}), 409
        data = request.get_json(silent=True) or {}
        answer = data.get("answer")
        if not isinstance(answer, str) or len(answer) > 80:
            return jsonify({"error": "Choose a valid answer"}), 400
        challenge = state["challenge"]
        if slug in {"hex-snake", "packet-patrol"} and answer not in challenge["choices"]:
            return jsonify({"error": "Choose a displayed answer"}), 400
        if slug == "bit-flip" and (len(answer) != 8 or any(bit not in "01" for bit in answer)):
            return jsonify({"error": "Set all eight bits"}), 400
        correct = answer == challenge["correct"]
        if correct:
            state["score"] += 10
        result = {"correct": correct, "explanation": challenge["explanation"], "score": state["score"],
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
            session.pop("arcade_run", None)
        else:
            state["round"] += 1
            next_round = make_round(slug, state["used"])
            if slug == "packet-patrol":
                state["used"].append(next_round["question_id"])
            state["challenge"] = next_round
            session["arcade_run"] = state
            result["next"] = public_round(next_round)
        return jsonify(result)

    return catalogue
