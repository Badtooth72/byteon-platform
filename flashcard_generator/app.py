from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json
import os

from bson import ObjectId
from flask import Flask, abort, jsonify, redirect, render_template, request, session
from flask_pymongo import PyMongo
from flask_session import Session
from redis import Redis

BASE_DIR = Path(__file__).resolve().parent
URL_PREFIX = os.getenv("URL_PREFIX", "/flashcards").rstrip("/")
if not URL_PREFIX.startswith("/"):
    URL_PREFIX = "/" + URL_PREFIX

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path=f"{URL_PREFIX}/static",
)

app.secret_key = os.getenv("SESSION_SECRET", "super-secret")
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://mongo:27017/auth_db")
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
)
app.config["SESSION_COOKIE_NAME"] = "byteon_session"
app.config["SESSION_COOKIE_PATH"] = "/"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)
app.config["SESSION_USE_SIGNER"] = False
app.config["SESSION_PERMANENT"] = True

Session(app)
mongo = PyMongo(app)

KEYWORDS_PATH = BASE_DIR / "data" / "j277_keywords.json"
with open(KEYWORDS_PATH, "r", encoding="utf-8") as handle:
    J277_KEYWORDS = json.load(handle)

MIN_CARDS = 10
COLLECTION = "flashcard_sets"


@app.template_filter("nice_dt")
def nice_dt(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return value.strftime("%d %b %Y, %H:%M")


def prefixed(path: str = "") -> str:
    path = path or ""
    if not path.startswith("/"):
        path = "/" + path
    return f"{URL_PREFIX}{path}"


def now_utc():
    return datetime.utcnow()


def current_username() -> str | None:
    username = session.get("username")
    if username:
        return str(username).lower().strip()
    return None


def require_user_page() -> str:
    username = current_username()
    if username:
        return username
    raise PermissionError("No active session")


def user_profile(username: str) -> dict:
    user = mongo.db.users.find_one({"username": username}) or {}
    display_name = user.get("display_name")
    if not display_name:
        display_name = " ".join(
            bit for bit in [user.get("forename", ""), user.get("surname", "")] if bit
        ).strip() or username
    return {
        "username": username,
        "display_name": display_name,
        "forename": user.get("forename", ""),
        "surname": user.get("surname", ""),
        "class_name": user.get("class_name", ""),
        "yeargroup": user.get("current_yeargroup", ""),
    }


def serialise_set(doc: dict, viewer: str | None = None) -> dict:
    owner = doc.get("owner_username", "")
    shared_to = doc.get("shared_to", [])
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title", "Untitled set"),
        "description": doc.get("description", ""),
        "owner_username": owner,
        "owner_display_name": doc.get("owner_display_name", owner),
        "card_count": len(doc.get("cards", [])),
        "is_public": doc.get("is_public", False),
        "shared_to": shared_to,
        "cards": doc.get("cards", []),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "can_edit": viewer == owner,
        "can_view": bool(viewer == owner or doc.get("is_public", False) or (viewer and viewer in shared_to)),
    }


def find_accessible_set(set_id: str, viewer: str) -> dict | None:
    try:
        oid = ObjectId(set_id)
    except Exception:
        return None

    return mongo.db[COLLECTION].find_one(
        {
            "_id": oid,
            "$or": [
                {"owner_username": viewer},
                {"is_public": True},
                {"shared_to": viewer},
            ],
        }
    )


def parse_shared_to(value) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or "").replace("\n", ",").split(",")
    return sorted({item.strip().lower() for item in raw if str(item).strip()})


def normalise_cards(cards: list[dict]) -> list[dict]:
    cleaned = []
    for idx, card in enumerate(cards, start=1):
        keyword = str(card.get("keyword", "")).strip() or f"Card {idx}"
        meaning = str(card.get("meaning", "")).strip()
        notes = str(card.get("notes", "")).strip()
        image = str(card.get("image", "")).strip()
        cleaned.append({"keyword": keyword, "meaning": meaning, "notes": notes, "image": image})
    return cleaned


def update_activity_summary(username: str) -> None:
    sets = list(
        mongo.db[COLLECTION]
        .find({"owner_username": username}, {"title": 1, "updated_at": 1, "cards": 1, "is_public": 1})
        .sort("updated_at", -1)
    )
    total_cards = sum(len(item.get("cards", [])) for item in sets)
    public_sets = sum(1 for item in sets if item.get("is_public"))
    summary = {
        "sets_created": len(sets),
        "public_sets": public_sets,
        "total_cards": total_cards,
        "updated_at": now_utc(),
    }
    if sets:
        summary["latest_set_title"] = sets[0].get("title", "Untitled set")

    mongo.db.users.update_one(
        {"username": username},
        {"$set": {"activities.flashcard_generator.summary": summary}},
        upsert=True,
    )


@app.route(prefixed(""))
@app.route(prefixed("/"))
def index():
    try:
        username = require_user_page()
    except PermissionError:
        return redirect("/login")
    return render_template("index.html", user=user_profile(username), min_cards=MIN_CARDS, keyword_groups=J277_KEYWORDS, prefix=URL_PREFIX)


@app.route(prefixed("/editor"))
def editor_new():
    try:
        username = require_user_page()
    except PermissionError:
        return redirect("/login")

    starter_keywords = [item["keyword"] for group in J277_KEYWORDS for item in group["items"]][:MIN_CARDS]
    starter_cards = [{"keyword": keyword, "meaning": "", "notes": "", "image": ""} for keyword in starter_keywords]
    return render_template(
        "editor.html",
        user=user_profile(username),
        min_cards=MIN_CARDS,
        keyword_groups=J277_KEYWORDS,
        edit_mode=False,
        flashcard_set={"title": "", "description": "", "is_public": False, "shared_to": [], "cards": starter_cards},
        prefix=URL_PREFIX,
    )


@app.route(prefixed("/editor/<set_id>"))
def editor_existing(set_id):
    try:
        username = require_user_page()
    except PermissionError:
        return redirect("/login")

    doc = find_accessible_set(set_id, username)
    if not doc:
        abort(404)
    if doc.get("owner_username") != username:
        abort(403)

    return render_template(
        "editor.html",
        user=user_profile(username),
        min_cards=MIN_CARDS,
        keyword_groups=J277_KEYWORDS,
        edit_mode=True,
        flashcard_set=serialise_set(doc, username),
        prefix=URL_PREFIX,
    )


@app.route(prefixed("/my-sets"))
def my_sets():
    try:
        username = require_user_page()
    except PermissionError:
        return redirect("/login")

    docs = list(mongo.db[COLLECTION].find({"owner_username": username}).sort("updated_at", -1))
    return render_template("my_sets.html", user=user_profile(username), sets=[serialise_set(doc, username) for doc in docs], prefix=URL_PREFIX)


@app.route(prefixed("/shared-library"))
def shared_library():
    try:
        username = require_user_page()
    except PermissionError:
        return redirect("/login")

    query = request.args.get("q", "").strip()
    mongo_query = {"$or": [{"is_public": True}, {"shared_to": username}, {"owner_username": username}]}
    if query:
        mongo_query["$and"] = [{"$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"cards.keyword": {"$regex": query, "$options": "i"}},
        ]}]

    docs = list(mongo.db[COLLECTION].find(mongo_query).sort("updated_at", -1).limit(100))
    return render_template("shared_library.html", user=user_profile(username), query=query, sets=[serialise_set(doc, username) for doc in docs], prefix=URL_PREFIX)


@app.route(prefixed("/view/<set_id>"))
def view_set(set_id):
    try:
        username = require_user_page()
    except PermissionError:
        return redirect("/login")

    doc = find_accessible_set(set_id, username)
    if not doc:
        abort(404)
    return render_template("view_set.html", user=user_profile(username), flashcard_set=serialise_set(doc, username), prefix=URL_PREFIX)


@app.route(prefixed("/print/<set_id>"))
def print_set(set_id):
    try:
        username = require_user_page()
    except PermissionError:
        return redirect("/login")

    doc = find_accessible_set(set_id, username)
    if not doc:
        abort(404)

    cards = serialise_set(doc, username)["cards"]
    chunks = [cards[i:i + 4] for i in range(0, len(cards), 4)]
    return render_template("print_set.html", user=user_profile(username), flashcard_set=serialise_set(doc, username), chunks=chunks, prefix=URL_PREFIX)


@app.route(prefixed("/api/keywords"))
def api_keywords():
    if not current_username():
        return jsonify({"error": "Not logged in"}), 401
    return jsonify(J277_KEYWORDS)


@app.route(prefixed("/api/set"), methods=["POST"])
def create_set():
    username = current_username()
    if not username:
        return jsonify({"error": "Not logged in"}), 401

    payload = request.get_json(force=True)
    cards = payload.get("cards", [])
    if len(cards) < MIN_CARDS:
        return jsonify({"error": f"At least {MIN_CARDS} cards are required."}), 400

    profile = user_profile(username)
    doc = {
        "title": (payload.get("title", "Untitled set") or "Untitled set").strip(),
        "description": str(payload.get("description", "")).strip(),
        "owner_username": username,
        "owner_display_name": profile["display_name"],
        "is_public": bool(payload.get("is_public", False)),
        "shared_to": parse_shared_to(payload.get("shared_to", [])),
        "cards": normalise_cards(cards),
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    result = mongo.db[COLLECTION].insert_one(doc)
    update_activity_summary(username)
    return jsonify({"success": True, "id": str(result.inserted_id)})


@app.route(prefixed("/api/set/<set_id>"), methods=["PUT"])
def update_set(set_id):
    username = current_username()
    if not username:
        return jsonify({"error": "Not logged in"}), 401

    payload = request.get_json(force=True)
    cards = payload.get("cards", [])
    if len(cards) < MIN_CARDS:
        return jsonify({"error": f"At least {MIN_CARDS} cards are required."}), 400

    try:
        oid = ObjectId(set_id)
    except Exception:
        return jsonify({"error": "Invalid set id"}), 400

    existing = mongo.db[COLLECTION].find_one({"_id": oid, "owner_username": username})
    if not existing:
        return jsonify({"error": "Set not found or not editable"}), 404

    mongo.db[COLLECTION].update_one(
        {"_id": oid},
        {"$set": {
            "title": (payload.get("title", "Untitled set") or "Untitled set").strip(),
            "description": str(payload.get("description", "")).strip(),
            "is_public": bool(payload.get("is_public", False)),
            "shared_to": parse_shared_to(payload.get("shared_to", [])),
            "cards": normalise_cards(cards),
            "updated_at": now_utc(),
        }},
    )
    update_activity_summary(username)
    return jsonify({"success": True, "id": set_id})


@app.route(prefixed("/api/set/<set_id>"), methods=["DELETE"])
def delete_set(set_id):
    username = current_username()
    if not username:
        return jsonify({"error": "Not logged in"}), 401

    try:
        oid = ObjectId(set_id)
    except Exception:
        return jsonify({"error": "Invalid set id"}), 400

    result = mongo.db[COLLECTION].delete_one({"_id": oid, "owner_username": username})
    if not result.deleted_count:
        return jsonify({"error": "Set not found or not editable"}), 404

    update_activity_summary(username)
    return jsonify({"success": True})


@app.route(prefixed("/health"))
def health():
    return {"status": "ok"}


@app.errorhandler(401)
def unauthorized(_):
    return render_template("error.html", message="You need to be logged in to use the flashcard generator.", prefix=URL_PREFIX), 401


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", message="You can view this set, but only the owner can edit it. Permissions. The hobby that never dies.", prefix=URL_PREFIX), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", message="That flashcard set was not found.", prefix=URL_PREFIX), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
