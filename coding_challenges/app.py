from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import openai
from flask_pymongo import PyMongo
import sys
import re
import time
from urllib.parse import urlsplit
from flask_session import Session
from redis import Redis
from datetime import timedelta
from scoring import challenge_score


app = Flask(__name__)
app.secret_key = os.environ["BYTEON_SESSION_SECRET"]

# Shared session config
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(host="redis", port=6379)
app.config["SESSION_COOKIE_NAME"] = "byteon_session"
app.config["SESSION_COOKIE_PATH"] = "/"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)

Session(app)
@app.before_request
def make_session_permanent():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("Origin")
        if origin and urlsplit(origin).netloc != request.host:
            return jsonify({"error": "Cross-origin request rejected"}), 403
    session.permanent = True
    session.modified = True


# MongoDB connections
mongo_auth = PyMongo(app, uri="mongodb://mongo:27017/auth_db")
mongo_challenges = PyMongo(app, uri="mongodb://mongo:27017/coding_challenges")

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
MAX_CODE_LENGTH = int(os.getenv("MAX_CODE_LENGTH", "12000"))
AI_REQUESTS_PER_MINUTE = int(os.getenv("AI_REQUESTS_PER_MINUTE", "10"))


def require_username():
    return session.get("username")


def validate_challenge(data):
    level = str(data.get("level", "1"))
    challenge_id = str(data.get("challenge_id", ""))
    if level not in {"1", "2", "3"} or not re.fullmatch(r"[0-9]+", challenge_id):
        return None, None
    challenge = mongo_challenges.db.challenges.find_one(
        {"level": int(level), "challenge_id": int(challenge_id)}, {"_id": 0}
    )
    return level, challenge


def ai_rate_limited(username):
    bucket = int(time.time() // 60)
    key = f"byteon:ai:{username}:{bucket}"
    redis_client = app.config["SESSION_REDIS"]
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, 90)
    return count > AI_REQUESTS_PER_MINUTE


def save_challenge_progress(username, level, challenge_id, score, attempts, submission):
    challenge_path = f"activities.coding_challenges.levels.{level}.challenges.{challenge_id}"
    mongo_auth.db.users.update_one(
        {"username": username},
        {"$set": {challenge_path: {
            "score": score, "attempts": attempts, "submission": submission
        }}},
        upsert=False,
    )
    user = mongo_auth.db.users.find_one({"username": username}) or {}
    challenges = user.get("activities", {}).get("coding_challenges", {}).get("levels", {}).get(level, {}).get("challenges", {})
    total_score = sum(c.get("score", 0) for c in challenges.values())
    mongo_auth.db.users.update_one(
        {"username": username},
        {"$set": {f"activities.coding_challenges.levels.{level}.total_score": total_score}},
    )
    return total_score

@app.route("/")
def root():
    return redirect("/coding-challenges/")


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True})


@app.route("/coding-challenges/")
def home():
    if "username" not in session:
        return redirect("/auth")

    username = session["username"]
    user = mongo_auth.db.users.find_one({"username": username})
    level_scores = {"1": 0, "2": 0, "3": 0}
    total_score = 0

    if user:
        levels = user.get("activities", {}).get("coding_challenges", {}).get("levels", {})
        for level, data in levels.items():
            level_total = data.get("total_score", 0)
            if level in level_scores:
                level_scores[level] = level_total
            total_score += level_total

    return render_template("home.html", level_scores=level_scores, total_score=total_score)


@app.route("/coding-challenges/leaderboard")
def leaderboard_page():
    return render_template("leaderboard.html")



@app.route("/coding-challenges/challenges")
def challenges_page():
    if "username" not in session:
        return redirect("/auth")

    username = session["username"]
    level = request.args.get("level", "1")

    try:
        level_int = int(level)
    except ValueError:
        level_int = 1

    challenges = list(
        mongo_challenges.db.challenges
        .find({"level": level_int}, {"_id": 0})
        .sort("challenge_id", 1)
    )

    return render_template("challenges.html",
                           challenges=challenges,
                           level=level_int,
                           username=username)

@app.route("/coding-challenges/api/progress", methods=["GET"])
def get_progress():
    username = session.get("username")
    level = request.args.get("level", "1")

    if not username:
        return jsonify({"error": "Not logged in"}), 401

    user = mongo_auth.db.users.find_one({"username": username}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    level_data = user.get("activities", {}).get("coding_challenges", {}).get("levels", {}).get(level, {})
    return jsonify({
        "username": username,
        "level": level,
        "progress": level_data
    })

@app.route("/coding-challenges/api/progress", methods=["POST"])
def update_progress():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    print("[DEBUG] Received /api/progress POST:", data, file=sys.stderr)

    username = session["username"]
    level, challenge = validate_challenge(data)
    challenge_id = str(data.get("challenge_id", ""))
    submission = data.get("submission", "")

    if not challenge:
        return jsonify({"error": "Unknown challenge"}), 400
    if data.get("action") != "quit":
        return jsonify({"error": "Scores are recorded by the assessment endpoint"}), 400
    existing = (mongo_auth.db.users.find_one({"username": username}) or {}).get("activities", {}).get("coding_challenges", {}).get("levels", {}).get(level, {}).get("challenges", {}).get(challenge_id, {})
    attempts = max(1, int(existing.get("attempts", 0)))
    total_score = save_challenge_progress(username, level, challenge_id, 0, attempts, submission[:MAX_CODE_LENGTH])

    return jsonify({
        "message": "Progress updated successfully.",
        "username": username,
        "level": level,
        "total_score": total_score,
        "score": 0
    })

@app.route("/coding-challenges/api/feedback", methods=["POST"])
def feedback():
    username = require_username()
    if not username:
        return jsonify({"error": "Not logged in"}), 401
    if ai_rate_limited(username):
        return jsonify({"error": "Too many AI requests. Please wait a minute."}), 429
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    level, challenge = validate_challenge(data)
    if not challenge:
        return jsonify({"error": "Unknown challenge"}), 400
    challenge_id = str(challenge["challenge_id"])
    description = challenge.get("description", "")
    example_output = challenge.get("example", "")

    if not code:
        return jsonify({"feedback": "No code has been submitted."})
    if len(code) > MAX_CODE_LENGTH:
        return jsonify({"error": "Submission is too long."}), 413

    prompt = (
        f"Challenge ID: {challenge_id}\n"
        f"Challenge Description: {description}\n"
        f"Expected Output: {example_output}\n\n"
        f"Submitted Code:\n{code}\n\n"
        "Review this for a GCSE-level student. Start the response with exactly "
        "'VERDICT: CORRECT' or 'VERDICT: INCORRECT', followed by short constructive "
        "feedback under 50 words. Do not give the full solution."
    )

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You're a helpful assistant reviewing student code."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.5,
        )
        feedback_text = response["choices"][0]["message"]["content"].strip()
    except Exception:
        app.logger.exception("Unable to generate submission feedback")
        return jsonify({"error": "Feedback is temporarily unavailable. Please try again."}), 503

    correct = feedback_text.upper().startswith("VERDICT: CORRECT")
    clean_feedback = re.sub(r"^VERDICT:\s*(CORRECT|INCORRECT)\s*", "", feedback_text, flags=re.I).strip()
    user = mongo_auth.db.users.find_one({"username": username}) or {}
    existing = user.get("activities", {}).get("coding_challenges", {}).get("levels", {}).get(level, {}).get("challenges", {}).get(challenge_id, {})
    attempts = int(existing.get("attempts", 0)) + 1
    score = challenge_score(correct, attempts)
    total_score = save_challenge_progress(username, level, challenge_id, score, attempts, code)
    return jsonify({"feedback": clean_feedback, "correct": correct, "score": score,
                    "attempts": attempts, "total_score": total_score})

@app.route("/coding-challenges/api/help", methods=["POST"])
def help_suggestions():
    username = require_username()
    if not username:
        return jsonify({"error": "Not logged in"}), 401
    if ai_rate_limited(username):
        return jsonify({"error": "Too many AI requests. Please wait a minute."}), 429
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    _, challenge = validate_challenge(data)
    if not challenge:
        return jsonify({"error": "Unknown challenge"}), 400
    challenge_id = challenge["challenge_id"]
    description = challenge.get("description", "")
    example_output = challenge.get("example", "")

    if not code:
        return jsonify({"feedback": "No code has been submitted. Please write something and try again."})
    if len(code) > MAX_CODE_LENGTH:
        return jsonify({"error": "Submission is too long."}), 413

    prompt = (
        f"Challenge ID: {challenge_id}\n"
        f"Challenge Description: {description}\n"
        f"Expected Output: {example_output}\n\n"
        f"Submitted Code:\n{code}\n\n"
        "Give only a short hint to help the student improve. Avoid full solutions. Keep it under 50 words."
    )

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You're a helpful assistant giving hints for code improvement."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.5,
        )
        feedback_text = response["choices"][0]["message"]["content"].strip()
    except Exception:
        app.logger.exception("Unable to generate help suggestions")
        return jsonify({"error": "Help is temporarily unavailable. Please try again."}), 503

    return jsonify({"feedback": feedback_text})

@app.route("/coding-challenges/api/leaderboard")
def leaderboard():
    users = mongo_auth.db.users.find({}, {"username": 1, "display_name": 1, "activities.coding_challenges.levels": 1})
    leaderboard_data = []
    current_user = session.get("username")

    for user in users:
        username = user.get("username", "")
        display_name = user.get("display_name", username)
        levels = user.get("activities", {}).get("coding_challenges", {}).get("levels", {})
        level_scores = {
            "1": levels.get("1", {}).get("total_score", 0),
            "2": levels.get("2", {}).get("total_score", 0),
            "3": levels.get("3", {}).get("total_score", 0)
        }
        total = sum(level_scores.values())
        leaderboard_data.append({
            "username": username,
            "display_name": display_name,
            "level_scores": level_scores,
            "total": total,
            "is_self": username == current_user
        })

    return jsonify(leaderboard_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
