from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import openai
from flask_pymongo import PyMongo
import sys
from flask_session import Session
from redis import Redis
from datetime import timedelta


app = Flask(__name__)
app.secret_key = "super-secret"  # Replace in production

# Shared session config
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(host="redis", port=6379)
app.config["SESSION_COOKIE_NAME"] = "byteon_session"
app.config["SESSION_COOKIE_PATH"] = "/"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)

Session(app)
@app.before_request
def make_session_permanent():
    session.permanent = True
    session.modified = True


# MongoDB connections
mongo_auth = PyMongo(app, uri="mongodb://mongo:27017/auth_db")
mongo_challenges = PyMongo(app, uri="mongodb://mongo:27017/coding_challenges")

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def root():
    return redirect("/coding-challenges/")


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

    data = request.get_json()
    print("[DEBUG] Received /api/progress POST:", data, file=sys.stderr)

    username = session["username"]
    level = str(data.get("level", "1"))
    challenge_id = str(data.get("challenge_id"))
    score = data.get("score", 0)
    attempts = data.get("attempts", 1)
    submission = data.get("submission", "")

    if not challenge_id:
        return jsonify({"error": "challenge_id is required"}), 400

    challenge_path = f"activities.coding_challenges.levels.{level}.challenges.{challenge_id}"
    mongo_auth.db.users.update_one(
        {"username": username},
        {"$set": {
            challenge_path: {
                "score": score,
                "attempts": attempts,
                "submission": submission
            }
        }},
        upsert=True
    )

    user = mongo_auth.db.users.find_one({"username": username})
    challenges = user.get("activities", {}).get("coding_challenges", {}).get("levels", {}).get(level, {}).get("challenges", {})
    total_score = sum(c.get("score", 0) for c in challenges.values())

    mongo_auth.db.users.update_one(
        {"username": username},
        {"$set": {
            f"activities.coding_challenges.levels.{level}.total_score": total_score
        }}
    )

    return jsonify({
        "message": "Progress updated successfully.",
        "username": username,
        "level": level,
        "total_score": total_score,
        "challenge_progress": challenges
    })

@app.route("/coding-challenges/api/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    code = data.get("code", "").strip()
    challenge_id = data.get("challenge_id", "")
    description = data.get("description", "").strip()
    example_output = data.get("example", "").strip()

    if not code:
        return jsonify({"feedback": "No code has been submitted."})

    prompt = (
        f"Challenge ID: {challenge_id}\n"
        f"Challenge Description: {description}\n"
        f"Expected Output: {example_output}\n\n"
        f"Submitted Code:\n{code}\n\n"
        "Review this for a GCSE-level student. Say 'Well done!' if correct. "
        "Otherwise, provide short constructive feedback (under 50 words).Do not give full solution.docvker "
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a helpful assistant reviewing student code."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.5,
        )
        feedback_text = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"feedback": feedback_text})

@app.route("/coding-challenges/api/help", methods=["POST"])
def help_suggestions():
    data = request.get_json()
    code = data.get("code", "").strip()
    challenge_id = data.get("challenge_id", "")
    description = data.get("description", "").strip()
    example_output = data.get("example", "").strip()

    if not code:
        return jsonify({"feedback": "No code has been submitted. Please write something and try again."})

    prompt = (
        f"Challenge ID: {challenge_id}\n"
        f"Challenge Description: {description}\n"
        f"Expected Output: {example_output}\n\n"
        f"Submitted Code:\n{code}\n\n"
        "Give only a short hint to help the student improve. Avoid full solutions. Keep it under 50 words."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a helpful assistant giving hints for code improvement."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.5,
        )
        feedback_text = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
