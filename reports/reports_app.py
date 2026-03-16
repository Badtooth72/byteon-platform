from flask import Flask, render_template, request, redirect, session, url_for
from flask_pymongo import PyMongo
from flask_session import Session
from redis import Redis
import os

app = Flask(__name__)

# Session Configuration
app.secret_key = "super-secret"
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(host="redis", port=6379)
app.config["SESSION_COOKIE_NAME"] = "byteon_session"
app.config["SESSION_COOKIE_PATH"] = "/"
Session(app)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://mongo:27017/auth_db"
mongo = PyMongo(app)

@app.before_request
def restrict_access():
    allowed_paths = ["/debug-session", "/logout", "/update_role", "/delete_user", "/edit_user"]
    if request.path in allowed_paths or request.path.startswith("/static") or request.path.startswith("/user"):
        return
    if "username" not in session:
        return redirect("/")

@app.route("/")
def index():
    username = session.get("username")
    user = mongo.db.users.find_one({"username": username})
    if not user or user.get("role") not in ["teacher", "admin"]:
        return "Access denied", 403

    users = mongo.db.users.find({}, {"_id": 0})
    user_list = []

    for u in users:
        activities = u.get("activities", {})
        coding = activities.get("coding_challenges", {}).get("levels", {})
        total_score = sum(lvl.get("total_score", 0) for lvl in coding.values())
        user_list.append({
            "username": u.get("username"),
            "display_name": u.get("display_name", u.get("username")),
            "last_login": u.get("last_login"),
            "login_count": u.get("login_count", 1),
            "role": u.get("role", "student"),
            "coding_score": total_score
        })

    return render_template("dashboard.html", users=user_list, current_user=user)


@app.route("/report/")
def report_home():
    current_user = mongo.db.users.find_one({"username": session.get("username")})
    return render_template("report_home.html", current_user=current_user)


@app.route("/report/users")
def list_users():
    username = session.get("username")
    user = mongo.db.users.find_one({"username": username})
    if not user or user.get("role") not in ["teacher", "admin"]:
        return "Access denied", 403

    users = mongo.db.users.find({}, {"_id": 0})
    user_list = []

    for u in users:
        activities = u.get("activities", {})
        coding = activities.get("coding_challenges", {}).get("levels", {})
        total_score = sum(lvl.get("total_score", 0) for lvl in coding.values())
        user_list.append({
            "username": u.get("username"),
            "display_name": u.get("display_name", u.get("username")),
            "last_login": u.get("last_login"),
            "login_count": u.get("login_count", 1),
            "role": u.get("role", "student"),
            "coding_score": total_score
        })

    return render_template("dashboard.html", users=user_list, current_user=user)



@app.route("/user/<username>")
def view_user(username):
    current_user = mongo.db.users.find_one({"username": session.get("username")})
    if current_user.get("role") not in ["admin", "teacher"]:
        return "Access denied", 403

    user = mongo.db.users.find_one({"username": username})
    return render_template("user_detail.html", user=user)

@app.route("/edit_user", methods=["POST"])
def edit_user():
    current_user = mongo.db.users.find_one({"username": session.get("username")})
    if current_user.get("role") != "admin":
        return "Access denied", 403

    username = request.form["username"]
    new_role = request.form.get("role")
    display_name = request.form.get("display_name")
    update = {}
    if new_role:
        update["role"] = new_role
    if display_name:
        update["display_name"] = display_name

    mongo.db.users.update_one({"username": username}, {"$set": update})
    return redirect(url_for("index"))

@app.route("/delete_user", methods=["POST"])
def delete_user():
    current_user = mongo.db.users.find_one({"username": session.get("username")})
    if current_user.get("role") != "admin":
        return "Access denied", 403

    username = request.form["username"]
    mongo.db.users.delete_one({"username": username})
    return redirect(url_for("report_home"))


@app.route("/login")
def login():
    username = session.get("username")
    if not username:
        return redirect("/")

    user = mongo.db.users.find_one({"username": username})

    if not user:
        auth_user = mongo.db.users.find_one({"username": username})
        display_name = auth_user.get("display_name", username) if auth_user else username

        mongo.db.users.insert_one({
            "username": username,
            "display_name": display_name,
            "role": "admin" if username == "agriffiths" else "teacher",
            "login_count": 1
        })
    else:
        mongo.db.users.update_one({"username": username}, {"$inc": {"login_count": 1}})

    return redirect("/")

@app.route("/update_role", methods=["POST"])
def update_role():
    username = session.get("username")
    admin = mongo.db.users.find_one({"username": username})
    if admin.get("role") != "admin":
        return "Only admins can update roles.", 403

    target_username = request.form["username"]
    new_role = request.form["role"]
    mongo.db.users.update_one({"username": target_username}, {"$set": {"role": new_role}})
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/debug-session")
def debug_session():
    return f"Session = {dict(session)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
