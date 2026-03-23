from flask import Flask, request, render_template, redirect, session, url_for, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_session import Session
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from redis import Redis
from datetime import datetime, timedelta
import os
import ssl


app = Flask(__name__)

# -----------------------------------------------------------------------------
# App / session config
# -----------------------------------------------------------------------------
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-env")

app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", "6379")))
app.config["SESSION_COOKIE_NAME"] = os.getenv("SESSION_COOKIE_NAME", "byteon_session")
app.config["SESSION_COOKIE_PATH"] = "/"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "5")))
Session(app)

app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://mongo:27017/auth_db")
mongo = PyMongo(app)

# -----------------------------------------------------------------------------
# LDAP config
# -----------------------------------------------------------------------------
LDAP_SERVER = os.getenv("LDAP_SERVER", "10.13.0.4")
LDAP_PORT = int(os.getenv("LDAP_PORT", "636"))
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "DC=richardlander,DC=internal")
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
LDAP_BIND_PASSWORD = os.getenv("LDAP_BIND_PASSWORD")
LDAP_CA_CERT_FILE = os.getenv("LDAP_CA_CERT_FILE", "")
LDAP_VALIDATE_CERTS = os.getenv("LDAP_VALIDATE_CERTS", "false").lower() == "true"

# -----------------------------------------------------------------------------
# Activity config
# -----------------------------------------------------------------------------
AVAILABLE_ACTIVITIES = {
    "coding_challenges": {
        "name": "Coding Challenges",
        "link": "/coding-challenges",
        "leaderboard_enabled": True,
        "leaderboard_page": "/coding-challenges/leaderboard",
        "show_in_global_leaderboard": True,
    },
    "conversion_game": {
        "name": "Conversion Quiz",
        "link": "/conversion-game",
        "leaderboard_enabled": True,
        "leaderboard_page": "/conversion-games/leaderboard",
        "show_in_global_leaderboard": True,
    },
    "logic_gate_quiz": {
        "name": "Logic Gate Quiz",
        "link": "/logic-gate-quiz",
        "leaderboard_enabled": True,
        "leaderboard_page": "/logic-gate-quiz/leaderboard",
        "show_in_global_leaderboard": True,
    },
    "year_11_revision": {
        "name": "Year 11 Revision",
        "link": "/year-11-revision",
        "leaderboard_enabled": False,
        "show_in_global_leaderboard": False,
        "resources": [
            {"name": "J277/01 Computer Systems", "link": "/year-11-revision/j277-01"},
            {"name": "J277/02 Computational Thinking, Algorithms and Programming", "link": "/year-11-revision/j277-02"},
        ],
    },
    "flashcard_generator": {
        "name": "Flashcard Generator",
        "link": "/flashcards/",
        "leaderboard_enabled": True,
        "leaderboard_page": "/leaderboards/flashcard_generator",
        "show_in_global_leaderboard": True,
    },
}

LEADERBOARD_ENABLED_KEYS = {
    key for key, info in AVAILABLE_ACTIVITIES.items()
    if info.get("leaderboard_enabled")
}

GLOBAL_LEADERBOARD_KEYS = {
    key for key, info in AVAILABLE_ACTIVITIES.items()
    if info.get("show_in_global_leaderboard")
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def build_ldap_server():
    if LDAP_CA_CERT_FILE and LDAP_VALIDATE_CERTS:
        tls_config = Tls(
            ca_certs_file=LDAP_CA_CERT_FILE,
            validate=ssl.CERT_REQUIRED,
            version=ssl.PROTOCOL_TLSv1_2,
        )
    else:
        tls_config = Tls(
            validate=ssl.CERT_NONE,
            version=ssl.PROTOCOL_TLSv1_2,
        )

    return Server(
        LDAP_SERVER,
        port=LDAP_PORT,
        use_ssl=True,
        tls=tls_config,
        get_info=ALL,
    )


def get_user_full_name(user):
    forename = (user.get("forename") or "").strip()
    surname = (user.get("surname") or "").strip()
    full_name = f"{forename} {surname}".strip()
    return full_name if full_name else user.get("display_name") or user.get("username", "Unknown")


def is_student_record_complete(user):
    return all([
        (user.get("forename") or "").strip(),
        (user.get("surname") or "").strip(),
        (user.get("class_name") or "").strip(),
        str(user.get("current_yeargroup") or "").strip(),
    ])


def iso_date(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if value:
        return str(value)
    return ""


def safe_round(value, default=0.0):
    try:
        return round(float(value), 2)
    except Exception:
        return round(float(default), 2)


def summarise_coding_challenges(activity_data):
    if not isinstance(activity_data, dict) or not activity_data:
        return {}

    levels_data = activity_data.get("levels", activity_data)
    if not isinstance(levels_data, dict) or not levels_data:
        return {}

    section_count = 0
    total_score = 0
    total_challenges = 0
    total_attempts = 0

    for _, section_data in levels_data.items():
        if not isinstance(section_data, dict):
            continue

        section_count += 1
        total_score += section_data.get("total_score", 0)

        challenges = section_data.get("challenges", {})
        if isinstance(challenges, dict):
            total_challenges += len(challenges)
            for _, challenge_data in challenges.items():
                if isinstance(challenge_data, dict):
                    total_attempts += challenge_data.get("attempts", 0)

    if section_count == 0:
        return {}

    return {
        "sections_completed": section_count,
        "total_score": total_score,
        "challenges_attempted": total_challenges,
        "total_attempts": total_attempts,
    }


def summarise_conversion_game(activity_data):
    if not isinstance(activity_data, dict) or not activity_data:
        return {}

    best_mode = None
    best_score = -1
    best_time = None

    for mode, data in activity_data.items():
        if not isinstance(data, dict):
            continue

        score = data.get("score", 0)
        total_time = data.get("total_time", 0)

        if score > best_score:
            best_score = score
            best_mode = mode
            best_time = total_time
        elif score == best_score and best_time is not None and total_time < best_time:
            best_mode = mode
            best_time = total_time

    if best_mode is None:
        return {}

    return {
        "best_mode": best_mode,
        "best_score": best_score,
        "best_time_seconds": safe_round(best_time or 0),
    }


def summarise_logic_gate_quiz(activity_data):
    if not isinstance(activity_data, dict) or not activity_data:
        return {}

    completed_tasks = 0
    total_score = 0

    for _, data in activity_data.items():
        if isinstance(data, dict) and "score" in data:
            completed_tasks += 1
            total_score += data.get("score", 0)

    if completed_tasks == 0:
        return {}

    return {
        "completed_tasks": completed_tasks,
        "total_score": total_score,
    }


def summarise_flashcard_generator(activity_data):
    if not isinstance(activity_data, dict) or not activity_data:
        return {}

    summary = activity_data.get("summary", activity_data)
    if not isinstance(summary, dict) or not summary:
        return {}

    cleaned = {}
    for key in [
        "sets_created",
        "public_sets",
        "total_cards",
        "correct_identified",
        "games_played",
        "best_accuracy",
        "total_score",
        "latest_set_title",
        "updated_at",
        "last_played_at",
    ]:
        value = summary.get(key)
        if value not in (None, "", []):
            cleaned[key] = value

    return cleaned


def summarise_activity(activity_key, activity_data):
    if activity_key == "coding_challenges":
        return summarise_coding_challenges(activity_data)
    if activity_key == "conversion_game":
        return summarise_conversion_game(activity_data)
    if activity_key == "logic_gate_quiz":
        return summarise_logic_gate_quiz(activity_data)
    if activity_key == "flashcard_generator":
        return summarise_flashcard_generator(activity_data)
    return {}


def normalise_conversion_rows(user):
    rows = []
    conversions = user.get("activities", {}).get("conversion_game", {}) or {}

    for mode, data in conversions.items():
        if not isinstance(data, dict):
            continue

        rows.append({
            "activity_key": "conversion_game",
            "activity_name": AVAILABLE_ACTIVITIES["conversion_game"]["name"],
            "username": user.get("username", ""),
            "full_name": get_user_full_name(user),
            "forename": user.get("forename", ""),
            "surname": user.get("surname", ""),
            "class_name": user.get("class_name", ""),
            "yeargroup": user.get("current_yeargroup", ""),
            "sub_activity": mode,
            "score": data.get("score", 0),
            "fastest_time": safe_round(data.get("fastest_time", 0)),
            "total_time": safe_round(data.get("total_time", 0)),
            "date": iso_date(data.get("date")),
        })

    return rows


def normalise_logic_gate_rows(user):
    rows = []
    quiz_data = user.get("activities", {}).get("logic_gate_quiz", {}) or {}

    for level, data in quiz_data.items():
        if not isinstance(data, dict):
            continue

        rows.append({
            "activity_key": "logic_gate_quiz",
            "activity_name": AVAILABLE_ACTIVITIES["logic_gate_quiz"]["name"],
            "username": user.get("username", ""),
            "full_name": get_user_full_name(user),
            "forename": user.get("forename", ""),
            "surname": user.get("surname", ""),
            "class_name": user.get("class_name", ""),
            "yeargroup": user.get("current_yeargroup", ""),
            "sub_activity": level,
            "score": data.get("score", 0),
            "fastest_time": safe_round(data.get("fastest_time", 0)),
            "total_time": safe_round(data.get("total_time", 0)),
            "date": iso_date(data.get("date")),
        })

    return rows


def normalise_coding_rows(user):
    rows = []
    coding_data = user.get("activities", {}).get("coding_challenges", {}) or {}
    levels_data = coding_data.get("levels", coding_data)

    if not isinstance(levels_data, dict):
        return rows

    for section_name, section_data in levels_data.items():
        if not isinstance(section_data, dict):
            continue

        rows.append({
            "activity_key": "coding_challenges",
            "activity_name": AVAILABLE_ACTIVITIES["coding_challenges"]["name"],
            "username": user.get("username", ""),
            "full_name": get_user_full_name(user),
            "forename": user.get("forename", ""),
            "surname": user.get("surname", ""),
            "class_name": user.get("class_name", ""),
            "yeargroup": user.get("current_yeargroup", ""),
            "sub_activity": section_name,
            "score": section_data.get("total_score", 0),
            "fastest_time": 0.0,
            "total_time": 0.0,
            "date": iso_date(section_data.get("date")),
        })

    return rows


def normalise_flashcard_rows(user):
    summary = (user.get("activities", {}).get("flashcard_generator", {}) or {}).get("summary", {}) or {}
    if not isinstance(summary, dict):
        return []

    score = int(summary.get("total_score", 0) or 0)
    if score <= 0:
        return []

    cards_made = int(summary.get("total_cards", 0) or 0)
    correct_identified = int(summary.get("correct_identified", 0) or 0)
    games_played = int(summary.get("games_played", 0) or 0)
    subtitle = f"Cards: {cards_made} | Correct: {correct_identified} | Games: {games_played}"

    return [{
        "activity_key": "flashcard_generator",
        "activity_name": AVAILABLE_ACTIVITIES["flashcard_generator"]["name"],
        "username": user.get("username", ""),
        "full_name": get_user_full_name(user),
        "forename": user.get("forename", ""),
        "surname": user.get("surname", ""),
        "class_name": user.get("class_name", ""),
        "yeargroup": user.get("current_yeargroup", ""),
        "sub_activity": subtitle,
        "score": score,
        "fastest_time": 0.0,
        "total_time": 0.0,
        "date": iso_date(summary.get("updated_at") or summary.get("last_played_at")),
    }]


def build_activity_rows(activity_key, user):
    if activity_key == "conversion_game":
        return normalise_conversion_rows(user)
    if activity_key == "logic_gate_quiz":
        return normalise_logic_gate_rows(user)
    if activity_key == "coding_challenges":
        return normalise_coding_rows(user)
    if activity_key == "flashcard_generator":
        return normalise_flashcard_rows(user)
    return []


def sort_leaderboard_rows(rows):
    return sorted(
        rows,
        key=lambda x: (
            -int(x.get("score", 0)),
            float(x.get("total_time", 0) or 0),
            float(x.get("fastest_time", 0) or 0),
            x.get("full_name", "").lower(),
        )
    )


def get_leaderboard_rows(activity_key=None, limit=20):
    users = mongo.db.users.find({"activities": {"$exists": True}})
    rows = []

    for user in users:
        if not is_student_record_complete(user):
            continue

        if activity_key:
            rows.extend(build_activity_rows(activity_key, user))
        else:
            for key in GLOBAL_LEADERBOARD_KEYS:
                rows.extend(build_activity_rows(key, user))

    rows = [
    row for row in rows
    if isinstance(row.get("score", None), (int, float)) and row.get("score", 0) > 0
    ]
    rows = sort_leaderboard_rows(rows)

    return rows[:limit]

def normalise_yeargroup(value):
    raw = str(value or "").strip().lower()
    raw = raw.replace("year ", "").strip()
    return raw

def should_show_activity_to_user(activity_key, user):
    yeargroup = normalise_yeargroup(user.get("current_yeargroup"))

    if activity_key == "year_11_revision":
        return yeargroup == "11"

    if activity_key == "flashcard_generator":
        return yeargroup in {"10", "11"}

    return True


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]

        try:
            server = build_ldap_server()

            search_conn = Connection(server, user=LDAP_BIND_DN, password=LDAP_BIND_PASSWORD)
            if not search_conn.bind():
                return render_template("login.html", error="Unable to bind with service account.")

            search_conn.search(
                search_base=LDAP_BASE_DN,
                search_filter=f"(sAMAccountName={username})",
                search_scope=SUBTREE,
                attributes=["distinguishedName"],
            )

            if not search_conn.entries:
                return render_template("login.html", error="User not found in Active Directory.")

            user_dn = search_conn.entries[0].distinguishedName.value

            user_conn = Connection(server, user=user_dn, password=password)
            if user_conn.bind():
                session["username"] = username
                session.permanent = True

                mongo.db.users.update_one(
                    {"username": username},
                    {
                        "$setOnInsert": {
                            "display_name": username,
                            "activities": {},
                        },
                        "$set": {
                            "last_login": datetime.utcnow(),
                        },
                        "$inc": {
                            "login_count": 1,
                        },
                    },
                    upsert=True,
                )

                return redirect(url_for("dashboard"))

            return render_template("login.html", error="Invalid username or password.")

        except Exception as e:
            return render_template("login.html", error=f"LDAP error: {str(e)}")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"username": session["username"]}) or {}
    user_activities = user.get("activities", {}) or {}

    dashboard_data = []

    for key, info in AVAILABLE_ACTIVITIES.items():
        if not should_show_activity_to_user(key, user):
            continue

        activity_data = user_activities.get(key, {}) or {}
        summary = summarise_activity(key, activity_data)

        dashboard_data.append({
            "key": key,
            "name": info["name"],
            "link": info["link"],
            "summary": summary,
            "leaderboard": info.get("leaderboard_page") if info.get("leaderboard_enabled") else None,
            "resources": info.get("resources", []),
        })

    return render_template(
        "dashboard.html",
        display_name=get_user_full_name(user),
        last_login=user.get("last_login"),
        login_count=user.get("login_count", 1),
        activities=dashboard_data,
        role=user.get("role", "student"),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------------------------------------------------------------
# Leaderboards
# -----------------------------------------------------------------------------
@app.route("/leaderboards")
def combined_leaderboard_page():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("leaderboard.html", title="All Leaderboards", activity_key="all")


@app.route("/leaderboards/<activity_key>")
def activity_leaderboard_page(activity_key):
    if "username" not in session:
        return redirect(url_for("login"))

    if activity_key not in LEADERBOARD_ENABLED_KEYS:
        return redirect(url_for("dashboard"))

    title = AVAILABLE_ACTIVITIES[activity_key]["name"]
    return render_template("leaderboard.html", title=title, activity_key=activity_key)


@app.route("/api/leaderboards")
def api_all_leaderboards():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    limit = int(request.args.get("limit", 50))
    rows = get_leaderboard_rows(activity_key=None, limit=limit)
    return jsonify(rows)


@app.route("/api/leaderboards/<activity_key>")
def api_activity_leaderboard(activity_key):
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if activity_key not in LEADERBOARD_ENABLED_KEYS:
        return jsonify({"error": "Unsupported activity"}), 404

    limit = int(request.args.get("limit", 20))
    rows = get_leaderboard_rows(activity_key=activity_key, limit=limit)
    return jsonify(rows)


@app.route("/api/conversion_game/leaderboard")
def conversion_game_leaderboard():
    users = mongo.db.users.find({"activities.conversion_game": {"$exists": True}})
    results = []

    for user in users:
        forename = (user.get("forename") or "").strip()
        surname = (user.get("surname") or "").strip()
        class_name = (user.get("class_name") or "").strip()
        yeargroup = str(user.get("current_yeargroup") or "").strip()

        if not all([forename, surname, class_name, yeargroup]):
            continue

        conversions = user.get("activities", {}).get("conversion_game", {}) or {}

        for mode, data in conversions.items():
            if not isinstance(data, dict):
                continue

            score = data.get("score", 0)
            if not isinstance(score, (int, float)) or score <= 0:
                continue

            results.append({
                "username": user.get("username", "unknown"),
                "forename": forename,
                "surname": surname,
                "class_name": class_name,
                "yeargroup": yeargroup,
                "mode": mode,
                "score": score,
                "fastest_time": round(data.get("fastest_time", 0), 2),
                "total_time": round(data.get("total_time", 0), 2),
                "date": data.get("date", datetime.utcnow()).isoformat(),
            })

    results.sort(key=lambda x: (-x["score"], x["total_time"], x["fastest_time"], x["surname"], x["forename"]))
    return jsonify(results[:20])


# -----------------------------------------------------------------------------
# User / progress APIs
# -----------------------------------------------------------------------------
@app.route("/api/user")
def api_user():
    username = request.args.get("username", "").strip().lower()
    if not username:
        return jsonify({"error": "Missing username"}), 400

    user = mongo.db.users.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "forename": user.get("forename", ""),
        "surname": user.get("surname", ""),
        "class_name": user.get("class_name", ""),
        "current_yeargroup": user.get("current_yeargroup", ""),
    })


@app.route("/api/session-user")
def session_user():
    if "username" not in session:
        return jsonify({"username": "guest"})
    return jsonify({"username": session["username"]})


@app.route("/api/best-score")
def api_best_score():
    username = session.get("username")
    if not username:
        return jsonify({"error": "Not logged in"}), 401

    user = mongo.db.users.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404

    scores = user.get("activities", {}).get("conversion_game", {})
    best = max(scores.items(), key=lambda kv: kv[1]["score"], default=(None, None))

    if not best[1]:
        return jsonify({})

    return jsonify({
        "mode": best[0],
        "score": best[1]["score"],
        "time": best[1].get("total_time", 0),
    })


@app.route("/api/progress", methods=["POST"])
def api_progress():
    data = request.get_json() or {}

    username = (data.get("username") or "").strip().lower()
    activity_key = data.get("activity_key")
    score = data.get("score", 0)
    challenge_id = data.get("challenge_id", "default")
    submission = data.get("submission")
    level = data.get("level")

    if not username or not activity_key:
        return jsonify({"error": "Missing username or activity_key"}), 400

    update = {
        f"activities.{activity_key}.{challenge_id}": {
            "score": score,
            "submission": submission,
            "date": datetime.utcnow(),
        }
    }

    if level:
        update[f"activities.{activity_key}.{challenge_id}"]["level"] = level

    result = mongo.db.users.update_one(
        {"username": username},
        {"$set": update},
        upsert=True,
    )

    return jsonify({"success": True, "modified_count": result.modified_count})


# -----------------------------------------------------------------------------
# Revision resources
# -----------------------------------------------------------------------------
@app.route("/year-11-revision")
def year_11_revision():
    return redirect(url_for("dashboard"))


@app.route("/year-11-revision/j277-01")
def year_11_revision_j277_01():
    return send_from_directory("static", "j277-01-cram.html")


@app.route("/year-11-revision/j277-02")
def year_11_revision_j277_02():
    return send_from_directory("static", "j277-02-cram.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)