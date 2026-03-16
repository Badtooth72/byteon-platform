from flask import Flask, request, render_template, redirect, session, url_for, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_session import Session
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from redis import Redis
from datetime import datetime, timedelta
import os
import ssl

app = Flask(__name__)
app.secret_key = "super-secret"  # Replace in production

# Session configuration
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(host="redis", port=6379)
app.config["SESSION_COOKIE_NAME"] = "byteon_session"
app.config["SESSION_COOKIE_PATH"] = "/"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)
Session(app)

# MongoDB connection
app.config["MONGO_URI"] = "mongodb://mongo:27017/auth_db"
mongo = PyMongo(app)

# LDAP config
LDAP_SERVER = os.getenv("LDAP_SERVER", "10.13.0.4")
LDAP_PORT = int(os.getenv("LDAP_PORT", "636"))
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "DC=richardlander,DC=internal")
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
LDAP_BIND_PASSWORD = os.getenv("LDAP_BIND_PASSWORD")
LDAP_CA_CERT_FILE = os.getenv("LDAP_CA_CERT_FILE", "")


def build_ldap_server():
    if LDAP_CA_CERT_FILE:
        tls_config = Tls(
            ca_certs_file=LDAP_CA_CERT_FILE,
            validate=ssl.CERT_REQUIRED,
            version=ssl.PROTOCOL_TLSv1_2,
        )
    else:
        # Temporary fallback if no CA cert is mounted yet
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


AVAILABLE_ACTIVITIES = {
    "coding_challenges": {
        "name": "Coding Challenges",
        "link": "/coding_challenges",
    },
    "conversion_quiz": {
        "name": "Conversion Quiz",
        "link": "/conversion-game",
        "leaderboard": "/conversion-game/conversion_game_leaderboard.html",
    },
    "logic_gate_quiz": {
        "name": "Logic Gate Quiz",
        "link": "/logic-gate-quiz",
    },
    "year_11_revision": {
        "name": "Year 11 Revision",
        "link": "/year-11-revision",
        "resources": [
            {"name": "J277/01 Computer Systems", "link": "/year-11-revision/j277-01"},
            {"name": "J277/02 Computational Thinking, Algorithms and Programming", "link": "/year-11-revision/j277-02"},
        ],
    },
}


def summarise_coding_challenges(activity_data):
    if not isinstance(activity_data, dict) or not activity_data:
        return {}

    # Some versions store coding data under "levels"
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


def summarise_conversion_quiz(activity_data):
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
        "best_time_seconds": round(best_time or 0, 2),
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


def summarise_activity(activity_key, activity_data):
    if activity_key == "coding_challenges":
        return summarise_coding_challenges(activity_data)
    if activity_key == "conversion_quiz":
        return summarise_conversion_quiz(activity_data)
    if activity_key == "logic_gate_quiz":
        return summarise_logic_gate_quiz(activity_data)
    if activity_key == "year_11_revision":
        return {}
    return {}


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"].lower()
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
        activity_data = user_activities.get(key, {})
        summary = summarise_activity(key, activity_data)

        dashboard_data.append(
            {
                "key": key,
                "name": info["name"],
                "link": info["link"],
                "summary": summary,
                "leaderboard": info.get("leaderboard"),
                "resources": info.get("resources", []),
            }
        )

    return render_template(
        "dashboard.html",
        display_name=user.get("display_name", session["username"]),
        last_login=user.get("last_login"),
        login_count=user.get("login_count", 1),
        activities=dashboard_data,
        role=user.get("role", "student"),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/conversion_game/leaderboard")
def conversion_game_leaderboard():
    users = mongo.db.users.find({"activities.conversion_game": {"$exists": True}})
    results = []

    for user in users:
        conversions = user.get("activities", {}).get("conversion_game", {})
        for mode, data in conversions.items():
            result = {
                "username": user.get("username", "unknown"),
                "forename": user.get("forename", "unknown"),
                "surname": user.get("surname", "unknown"),
                "class_name": user.get("class_name", "unknown"),
                "yeargroup": user.get("current_yeargroup", "unknown"),
                "mode": mode,
                "score": data.get("score", 0),
                "fastest_time": round(data.get("fastest_time", 0), 2),
                "total_time": round(data.get("total_time", 0), 2),
                "date": data.get("date", datetime.utcnow()).isoformat(),
            }
            results.append(result)

    results.sort(key=lambda x: (-x["score"], x["mode"]))
    return jsonify(results[:20])


@app.route("/api/user")
def api_user():
    username = request.args.get("username", "").lower()
    if not username:
        return jsonify({"error": "Missing username"}), 400

    user = mongo.db.users.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(
        {
            "forename": user.get("forename", ""),
            "surname": user.get("surname", ""),
            "class_name": user.get("class_name", ""),
            "current_yeargroup": user.get("current_yeargroup", ""),
        }
    )


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

    return jsonify(
        {
            "mode": best[0],
            "score": best[1]["score"],
            "time": best[1]["total_time"],
        }
    )


@app.route("/api/progress", methods=["POST"])
def api_progress():
    data = request.get_json()
    username = data.get("username")
    activity_key = data.get("activity_key")
    score = data.get("score")
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