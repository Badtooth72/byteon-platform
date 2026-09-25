from flask import Flask, request, render_template, redirect, session, url_for, jsonify, send_from_directory, send_file
from flask_pymongo import PyMongo
from flask_session import Session
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.utils.conv import escape_filter_chars
from redis import Redis
from datetime import datetime, timedelta
from io import BytesIO
from gridfs import GridFS
from secrets import compare_digest
import os
import re
import ssl
from secrets import token_urlsafe
from urllib.parse import urlsplit
from progress import build_progress_record
from logic_gates import (
    build_random_challenge,
    mark_attempt,
    mark_challenge,
    progress_record,
    public_challenge,
    public_challenges,
)
from activity_scores import score_activity
from exam_bank_logic import parse_ao_marks, summarise_test, coverage_percentages


app = Flask(__name__)

# -----------------------------------------------------------------------------
# App / session config
# -----------------------------------------------------------------------------
app.secret_key = os.environ["BYTEON_SESSION_SECRET"]

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
ADMIN_USERNAMES = {
    value.strip().lower()
    for value in os.getenv("ADMIN_USERNAMES", "").split(",")
    if value.strip()
}


def student_profile_from_sql(username):
    """Refresh the computing-class details for a student at sign-in."""
    settings = [os.getenv(name) for name in ("SQL_SERVER", "SQL_DATABASE", "SQL_USERNAME", "SQL_PASSWORD")]
    if not all(settings):
        return {}
    import pyodbc

    connection = pyodbc.connect(
        "DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={};DATABASE={};UID={};PWD={};"
        "TrustServerCertificate=yes;Connection Timeout=5;".format(*settings)
    )
    try:
        row = connection.cursor().execute(
            "SELECT TOP 1 forename, surname, current_yeargroup, class_name "
            "FROM View_Students_Computing WHERE net_userid = ?", username
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return {}
    return {
        "forename": (row.forename or "").strip(),
        "surname": (row.surname or "").strip(),
        "current_yeargroup": str(row.current_yeargroup or "").strip(),
        "class_name": (row.class_name or "").strip(),
    }

# -----------------------------------------------------------------------------
# Activity config
# -----------------------------------------------------------------------------
AVAILABLE_ACTIVITIES = {
    "coding_challenges": {
        "name": "Coding Challenges",
        "link": "/coding-challenges",
        "leaderboard_enabled": True,
        "leaderboard_page": "/leaderboards/coding_challenges",
        "show_in_global_leaderboard": True,
    },
    "conversion_game": {
        "name": "Conversion Quiz",
        "link": "/conversion-game",
        "leaderboard_enabled": True,
        "leaderboard_page": "/leaderboards/conversion_game",
        "show_in_global_leaderboard": True,
    },
    "logic_gate_quiz": {
        "name": "Logic Gate Quiz",
        "link": "/logic-gate-quiz",
        "leaderboard_enabled": True,
        "leaderboard_page": "/leaderboards/logic-gate-quiz",
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
    "wordsearch": {
    "name": "CS Word Search",
    "link": "/wordsearch_app/",
    "leaderboard_enabled": False,
    "show_in_global_leaderboard": False,
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
        keys = [activity_key] if activity_key else GLOBAL_LEADERBOARD_KEYS
        for key in keys:
            score = score_activity(key, user.get("activities", {}).get(key, {}))
            if not score["has_score"]:
                continue
            rows.append({
                "activity_key": key,
                "activity_name": AVAILABLE_ACTIVITIES[key]["name"],
                "username": user.get("username", ""),
                "full_name": get_user_full_name(user),
                "class_name": user.get("class_name", ""),
                "yeargroup": user.get("current_yeargroup", ""),
                "role": user.get("role", "student"),
                "sub_activity": score["detail"],
                "score": score["percent"],
                "points": score["points"],
                "max_points": score["max_points"],
                "attempts": score["attempts"],
                "date": score["updated_at"],
                "fastest_time": 0,
                "total_time": 0,
            })
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
@app.before_request
def reject_cross_origin_writes():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    origin = request.headers.get("Origin")
    if origin and urlsplit(origin).netloc != request.host:
        return jsonify({"error": "Cross-origin request rejected"}), 403
    return None


@app.route("/healthz")
def healthz():
    try:
        mongo.cx.admin.command("ping")
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False}), 503


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
                search_filter=f"(sAMAccountName={escape_filter_chars(username)})",
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

                profile_updates = {"last_login": datetime.utcnow()}
                if username in ADMIN_USERNAMES:
                    profile_updates["role"] = "admin"
                else:
                    try:
                        profile_updates.update(student_profile_from_sql(username))
                    except Exception:
                        app.logger.exception("Could not refresh computing class for %s", username)

                mongo.db.users.update_one(
                    {"username": username},
                    {
                        "$setOnInsert": {
                            "display_name": username,
                            "activities": {},
                        },
                        "$set": profile_updates,
                        "$inc": {
                            "login_count": 1,
                        },
                    },
                    upsert=True,
                )

                return redirect(url_for("dashboard"))

            return render_template("login.html", error="Invalid username or password.")

        except Exception:
            app.logger.exception("LDAP login failed")
            return render_template("login.html", error="Login is temporarily unavailable.")

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
        summary = score_activity(key, activity_data)

        dashboard_data.append({
            "key": key,
            "name": info["name"],
            "link": info["link"],
            "summary": summary,
            "leaderboard": info.get("leaderboard_page") if info.get("leaderboard_enabled") else None,
            "resources": info.get("resources", []),
            "icon": {
                "coding_challenges": "</>", "conversion_game": "01",
                "logic_gate_quiz": "∧", "flashcard_generator": "Aa",
                "wordsearch": "#", "year_11_revision": "✓",
            }.get(key, "•"),
        })

    scored_percentages = [item["summary"]["percent"] for item in dashboard_data if item["summary"]["has_score"]]
    overall = round(sum(scored_percentages) / len(scored_percentages), 1) if scored_percentages else 0

    return render_template(
        "dashboard.html",
        display_name=get_user_full_name(user),
        last_login=user.get("last_login"),
        login_count=user.get("login_count", 1),
        activities=dashboard_data,
        role=user.get("role", "student"),
        username=user.get("username", session["username"]),
        class_name=user.get("class_name", ""),
        yeargroup=user.get("current_yeargroup", ""),
        overall=overall,
    )


@app.route("/user/<username>")
def user_detail(username):
    if "username" not in session:
        return redirect(url_for("login"))

    viewer = mongo.db.users.find_one({"username": session["username"]}) or {}
    if username != session["username"] and viewer.get("role") not in {"teacher", "admin"}:
        return "Access denied", 403

    user = mongo.db.users.find_one({"username": username})
    if not user:
        return "User not found", 404

    activities = []
    for key, info in AVAILABLE_ACTIVITIES.items():
        score = score_activity(key, user.get("activities", {}).get(key, {}))
        activities.append({"key": key, "name": info["name"], "link": info["link"], **score})

    scored = [activity["percent"] for activity in activities if activity["has_score"]]
    overall = round(sum(scored) / len(scored), 1) if scored else 0
    return render_template(
        "user_detail.html",
        user=user,
        display_name=get_user_full_name(user),
        activities=activities,
        overall=overall,
        can_manage=viewer.get("role") in {"teacher", "admin"},
    )


@app.route("/users")
def users_page():
    if "username" not in session:
        return redirect(url_for("login"))
    viewer = mongo.db.users.find_one({"username": session["username"]}) or {}
    if viewer.get("role") not in {"teacher", "admin"}:
        return "Access denied", 403

    users = []
    for user in mongo.db.users.find({}, {"_id": 0}).sort("username", 1):
        scores = [
            score_activity(key, user.get("activities", {}).get(key, {}))
            for key in GLOBAL_LEADERBOARD_KEYS
        ]
        recorded = [score["percent"] for score in scores if score["has_score"]]
        users.append({
            "username": user.get("username", ""),
            "display_name": get_user_full_name(user),
            "role": user.get("role", "student"),
            "class_name": user.get("class_name", ""),
            "yeargroup": user.get("current_yeargroup", ""),
            "overall": round(sum(recorded) / len(recorded), 1) if recorded else 0,
            "activities": len(recorded),
            "last_login": user.get("last_login"),
        })
    classes = sorted({user["class_name"] for user in users if user["class_name"]})
    return render_template("users.html", users=users, classes=classes)


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
    return render_template("leaderboards.html", title="All Leaderboards", activity_key="all")


@app.route("/leaderboards/<activity_key>")
def activity_leaderboard_page(activity_key):
    if "username" not in session:
        return redirect(url_for("login"))

    if activity_key not in LEADERBOARD_ENABLED_KEYS:
        return redirect(url_for("dashboard"))

    title = AVAILABLE_ACTIVITIES[activity_key]["name"]
    return render_template("leaderboards.html", title=title, activity_key=activity_key)


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
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401
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
    current = mongo.db.users.find_one({"username": session.get("username")})
    if not current or current.get("role") not in {"teacher", "admin"}:
        return jsonify({"error": "Access denied"}), 403
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
    username = session.get("username")
    if not username:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json() or {}

    try:
        activity_key, challenge_id, record = build_progress_record(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    update = {f"activities.{activity_key}.{challenge_id}": record}

    result = mongo.db.users.update_one(
        {"username": username},
        {"$set": update},
        upsert=True,
    )

    return jsonify({"success": True, "modified_count": result.modified_count})

@app.route("/api/logic-gates/challenges")
def logic_gate_challenges():
    return jsonify({"challenges": public_challenges()})

@app.route("/api/logic-gates/attempt", methods=["POST"])
def logic_gate_attempt():
    username = session.get("username")
    if not username:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    try:
        challenge, correct = mark_attempt(data.get("challenge_id"), data.get("response"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    record = progress_record(challenge, correct, data.get("response"))
    history_record = {**record, "challenge_id": challenge["id"]}
    mongo.db.users.update_one(
        {"username": username},
        {
            "$set": {f"activities.logic_gate_quiz.{challenge['id']}": record},
            "$push": {"activities.logic_gate_quiz.attempt_history": {"$each": [history_record], "$slice": -100}},
        },
        upsert=True,
    )
    return jsonify({
        "correct": correct,
        "explanation": challenge["explanation"],
        "score": record["score"],
    })


@app.route("/api/logic-gates/random-circuit")
def logic_gate_random_circuit():
    if not session.get("username"):
        return jsonify({"error": "Not logged in"}), 401

    challenge = build_random_challenge()
    token = token_urlsafe(16)
    session["logic_gate_random"] = {"token": token, "challenge": challenge}
    return jsonify({"token": token, "challenge": public_challenge(challenge)})


@app.route("/api/logic-gates/random-attempt", methods=["POST"])
def logic_gate_random_attempt():
    username = session.get("username")
    if not username:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    saved = session.get("logic_gate_random") or {}
    if not saved or data.get("token") != saved.get("token"):
        return jsonify({"error": "This random challenge has expired"}), 400

    challenge = saved["challenge"]
    try:
        _, correct = mark_challenge(challenge, data.get("response"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    record = progress_record(challenge, correct, data.get("response"))
    history_record = {**record, "challenge_id": "random"}
    mongo.db.users.update_one(
        {"username": username},
        {
            "$set": {"activities.logic_gate_quiz.random_latest": record},
            "$push": {"activities.logic_gate_quiz.attempt_history": {"$each": [history_record], "$slice": -100}},
        },
        upsert=True,
    )
    if correct:
        session.pop("logic_gate_random", None)

    return jsonify({
        "correct": correct,
        "explanation": challenge["explanation"],
        "score": record["score"],
    })


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


def exam_bank_teacher():
    username = session.get("username")
    if not username:
        return None
    return mongo.db.users.find_one(
        {"username": username, "role": {"$in": ["teacher", "admin"]}},
        {"_id": 0, "username": 1, "role": 1},
    )


def exam_bank_form_token():
    if not session.get("exam_bank_form_token"):
        session["exam_bank_form_token"] = token_urlsafe(24)
    return session["exam_bank_form_token"]


def valid_exam_bank_form():
    expected = session.get("exam_bank_form_token", "")
    supplied = request.form.get("form_token", "")
    return bool(expected and supplied and compare_digest(expected, supplied))


@app.route("/exam-bank")
def exam_bank_page():
    if not session.get("username"):
        return redirect(url_for("login"))
    if not exam_bank_teacher():
        return "Access denied", 403
    topic = request.args.get("topic", "")
    subtopic = request.args.get("subtopic", "")
    year = request.args.get("year", "")
    paper_id = request.args.get("paper", "")
    component = request.args.get("component", "")
    search = request.args.get("q", "").strip()[:100]
    ao = request.args.get("ao", "")
    query = {}
    if topic:
        query["topic_codes"] = topic
    if subtopic:
        query["subtopic"] = subtopic
    if component:
        if component not in {"J277/01", "J277/02"}:
            return "Invalid component", 400
        query["component"] = component
    if year:
        if not year.isdigit():
            return "Invalid year", 400
        query["year"] = int(year)
    if paper_id:
        query["paper_id"] = paper_id
    if search:
        query["$or"] = [
            {"summary": {"$regex": re.escape(search), "$options": "i"}},
            {"source_search_text": {"$regex": re.escape(search), "$options": "i"}},
            {"question_text": {"$regex": re.escape(search), "$options": "i"}},
            {"label": {"$regex": re.escape(search), "$options": "i"}},
        ]
    if ao:
        if ao not in {"AO1", "AO2", "AO3"}:
            return "Invalid assessment objective", 400
        query["ao_review_status"] = "teacher_verified"
        query[f"ao_marks.{ao}"] = {"$gt": 0}
    questions = list(mongo.db.exam_questions.find(
        query,
        {"_id": 0, "question_id": 1, "paper_id": 1, "label": 1, "summary": 1,
         "marks": 1, "topic_codes": 1, "year": 1, "review_status": 1,
         "component": 1, "ao_marks": 1, "ao_review_status": 1,
         "subtopic": 1, "prompt_review_status": 1, "question_tables": 1},
    ).sort([("year", -1), ("paper_id", 1), ("number", 1), ("label", 1)]).limit(500))
    papers = list(mongo.db.exam_papers.find(
        {}, {"_id": 0, "paper_id": 1, "year": 1, "title": 1, "component": 1}
    ).sort([("year", -1), ("component", 1)]))
    topics = list(mongo.db.exam_topics.find({}, {"_id": 0}).sort("code", 1))
    subtopics = sorted(value for value in mongo.db.exam_questions.distinct("subtopic") if value)
    drafts = list(mongo.db.exam_test_drafts.find(
        {"created_by": session["username"]}, {"_id": 0, "test_id": 1, "title": 1, "total_marks": 1}
    ).sort("created_at", -1).limit(10))
    return render_template("exam_bank.html", questions=questions, papers=papers, topics=topics,
                           subtopics=subtopics, selected_subtopic=subtopic,
                           drafts=drafts, form_token=exam_bank_form_token(),
                           selected_topic=topic, selected_year=year, selected_paper=paper_id,
                           selected_component=component, selected_search=search, selected_ao=ao)


@app.route("/exam-bank/random")
def exam_bank_random():
    if not session.get("username"):
        return redirect(url_for("login"))
    if not exam_bank_teacher():
        return "Access denied", 403

    papers = list(mongo.db.exam_papers.find(
        {}, {"_id": 0, "paper_id": 1, "year": 1, "component": 1, "title": 1}
    ).sort([("year", -1), ("component", 1)]))
    topics = list(mongo.db.exam_topics.find(
        {}, {"_id": 0, "code": 1, "name": 1}
    ).sort("code", 1))
    paper_id = request.args.get("paper", "")
    topic = request.args.get("topic", "")
    if paper_id and paper_id not in {paper["paper_id"] for paper in papers}:
        return "Invalid paper", 400
    if topic and topic not in {item["code"] for item in topics}:
        return "Invalid topic", 400

    query = {}
    if paper_id:
        query["paper_id"] = paper_id
    if topic:
        query["topic_codes"] = topic
    available_count = mongo.db.exam_questions.count_documents(query)
    question = None
    paper = None
    if request.args.get("draw") == "1" and available_count:
        previous_id = request.args.get("exclude", "")[:120]
        sample_query = dict(query)
        if previous_id and available_count > 1:
            sample_query["question_id"] = {"$ne": previous_id}
        question = next(mongo.db.exam_questions.aggregate([
            {"$match": sample_query}, {"$sample": {"size": 1}},
            {"$project": {"_id": 0}},
        ]), None)
        if question:
            paper = next((item for item in papers if item["paper_id"] == question["paper_id"]), None)
    return render_template("exam_random.html", papers=papers, topics=topics,
                           selected_paper=paper_id, selected_topic=topic,
                           available_count=available_count, question=question, paper=paper)


@app.route("/exam-bank/question/<question_id>")
def exam_bank_question(question_id):
    if not session.get("username"):
        return redirect(url_for("login"))
    if not exam_bank_teacher():
        return "Access denied", 403
    question = mongo.db.exam_questions.find_one({"question_id": question_id}, {"_id": 0})
    if not question:
        return "Question not found", 404
    paper = mongo.db.exam_papers.find_one({"paper_id": question["paper_id"]},
                                          {"_id": 0, "question_file_id": 0, "mark_scheme_file_id": 0})
    return render_template("exam_question.html", question=question, paper=paper,
                           form_token=exam_bank_form_token(), error=request.args.get("error"))


@app.route("/exam-bank/question/<question_id>/prompt", methods=["POST"])
def exam_bank_question_prompt(question_id):
    if not exam_bank_teacher():
        return "Access denied", 403
    if not valid_exam_bank_form():
        return "Invalid form token", 400
    question = mongo.db.exam_questions.find_one({"question_id": question_id}, {"_id": 1, "question_tables": 1})
    if not question:
        return "Question not found", 404
    prompt = request.form.get("question_text", "").strip()
    subtopic = request.form.get("subtopic", "").strip()
    if len(prompt) > 8000 or len(subtopic) > 80:
        return "Prompt or subtopic is too long", 400
    status = "not_transcribed"
    if prompt:
        status = "teacher_verified" if request.form.get("verified") == "yes" else "draft_needs_source_check"
    mongo.db.exam_questions.update_one({"_id": question["_id"]}, {"$set": {
        "question_text": prompt, "subtopic": subtopic,
        "prompt_review_status": status,
        "table_review_status": status if question.get("question_tables") else "not_applicable",
        "prompt_reviewed_by": session["username"], "prompt_reviewed_at": datetime.utcnow(),
    }})
    return redirect(url_for("exam_bank_question", question_id=question_id))


@app.route("/exam-bank/analysis")
def exam_bank_analysis():
    if not session.get("username"):
        return redirect(url_for("login"))
    if not exam_bank_teacher():
        return "Access denied", 403
    papers = list(mongo.db.exam_papers.find(
        {}, {"_id": 0, "paper_id": 1, "year": 1, "component": 1, "title": 1}
    ).sort([("year", 1), ("component", 1)]))
    selected = request.args.getlist("paper")
    if selected:
        papers = [paper for paper in papers if paper["paper_id"] in selected]
    report = []
    for paper in papers:
        questions = list(mongo.db.exam_questions.find(
            {"paper_id": paper["paper_id"]},
            {"_id": 0, "marks": 1, "topic_codes": 1, "subtopic": 1},
        ))
        report.append({
            **paper, "question_count": len(questions),
            "total_marks": sum(item["marks"] for item in questions),
            "topics": coverage_percentages(questions, "topic"),
            "subtopics": coverage_percentages(questions, "subtopic"),
        })
    topic_labels = sorted({label for paper in report for label in paper["topics"]})
    subtopic_labels = sorted({label for paper in report for label in paper["subtopics"]})
    return render_template("exam_analysis.html", report=report,
                           topic_labels=topic_labels, subtopic_labels=subtopic_labels)


@app.route("/exam-bank/question/<question_id>/ao", methods=["POST"])
def exam_bank_question_ao(question_id):
    if not exam_bank_teacher():
        return "Access denied", 403
    if not valid_exam_bank_form():
        return "Invalid form token", 400
    question = mongo.db.exam_questions.find_one({"question_id": question_id}, {"_id": 0, "marks": 1})
    if not question:
        return "Question not found", 404
    try:
        marks, status = parse_ao_marks(request.form, question["marks"])
    except ValueError as exc:
        return redirect(url_for("exam_bank_question", question_id=question_id, error=str(exc)))
    mongo.db.exam_questions.update_one(
        {"question_id": question_id},
        {"$set": {"ao_marks": marks, "ao_review_status": status,
                  "ao_reviewed_by": session["username"], "ao_reviewed_at": datetime.utcnow()}},
    )
    return redirect(url_for("exam_bank_question", question_id=question_id))


@app.route("/exam-bank/tests", methods=["POST"])
def exam_bank_create_test():
    if not exam_bank_teacher():
        return "Access denied", 403
    if not valid_exam_bank_form():
        return "Invalid form token", 400
    title = request.form.get("title", "").strip()[:120] or "Untitled topic test"
    ids = request.form.getlist("question_id")
    if not ids or len(ids) > 100 or len(set(ids)) != len(ids):
        return "Select between 1 and 100 distinct questions", 400
    documents = {
        item["question_id"]: item
        for item in mongo.db.exam_questions.find({"question_id": {"$in": ids}}, {"_id": 0})
    }
    if len(documents) != len(ids):
        return "One or more questions were not found", 400
    questions = [documents[question_id] for question_id in ids]
    summary = summarise_test(questions)
    test_id = token_urlsafe(12)
    mongo.db.exam_test_drafts.create_index("test_id", unique=True)
    mongo.db.exam_test_drafts.create_index([("created_by", 1), ("created_at", -1)])
    mongo.db.exam_test_drafts.insert_one({
        "test_id": test_id, "title": title, "created_by": session["username"],
        "created_at": datetime.utcnow(), "question_ids": ids,
        "total_marks": summary["total_marks"], "status": "draft",
    })
    return redirect(url_for("exam_bank_test", test_id=test_id))


@app.route("/exam-bank/tests/<test_id>")
def exam_bank_test(test_id):
    if not exam_bank_teacher():
        return "Access denied", 403
    draft = mongo.db.exam_test_drafts.find_one(
        {"test_id": test_id, "created_by": session["username"]}, {"_id": 0}
    )
    if not draft:
        return "Draft not found", 404
    documents = {
        item["question_id"]: item
        for item in mongo.db.exam_questions.find(
            {"question_id": {"$in": draft["question_ids"]}},
            {"_id": 0, "question_id": 1, "paper_id": 1, "label": 1, "summary": 1,
             "marks": 1, "topic_codes": 1, "ao_marks": 1, "ao_review_status": 1,
             "component": 1, "review_status": 1, "subtopic": 1,
             "question_text": 1, "prompt_review_status": 1,
             "requires_source_visual": 1, "question_tables": 1,
             "table_review_status": 1},
        )
    }
    questions = [documents[question_id] for question_id in draft["question_ids"] if question_id in documents]
    return render_template("exam_test.html", draft=draft, questions=questions,
                           summary=summarise_test(questions),
                           topic_coverage=coverage_percentages(questions, "topic"),
                           subtopic_coverage=coverage_percentages(questions, "subtopic"))


@app.route("/exam-bank/source/<paper_id>/<role>")
def exam_bank_source(paper_id, role):
    if not session.get("username"):
        return redirect(url_for("login"))
    if not exam_bank_teacher():
        return "Access denied", 403
    if role not in {"question", "mark-scheme"}:
        return "Source not found", 404
    paper = mongo.db.exam_papers.find_one({"paper_id": paper_id})
    if not paper:
        return "Source not found", 404
    file_id = paper.get("question_file_id" if role == "question" else "mark_scheme_file_id")
    if not file_id:
        return "Source not found", 404
    source = GridFS(mongo.db, collection="exam_source_files").get(file_id)
    return send_file(BytesIO(source.read()), mimetype="application/pdf",
                     download_name=f"{paper_id}-{role}.pdf", as_attachment=False)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
