from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Any

import requests
from bson import ObjectId
from bson.errors import InvalidId
from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    request,
    session,
    url_for as flask_url_for,
)
from pymongo import DESCENDING, MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)
app.secret_key = os.getenv("FLASHCARD_SECRET_KEY", "change-me-in-production")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
FLASHCARD_DB = os.getenv("FLASHCARD_DB", "auth_db")
FLASHCARD_COLLECTION = os.getenv("FLASHCARD_COLLECTION", "flashcard_sets")
AUTH_API_BASE = os.getenv("AUTH_API_BASE", "")
URL_PREFIX = os.getenv("URL_PREFIX", "/flashcards").rstrip("/")
PORT = int(os.getenv("PORT", "5005"))

mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
db = mongo_client[FLASHCARD_DB]
sets_collection = db[FLASHCARD_COLLECTION]

KEYWORD_GROUPS = {
    "Systems Architecture": [
        "CPU", "ALU", "Control Unit", "Registers", "Program Counter", "MAR", "MDR",
        "Accumulator", "Cache", "Clock Speed", "Cores", "Fetch-Decode-Execute", "Embedded Systems"
    ],
    "Memory and Storage": [
        "RAM", "ROM", "Virtual Memory", "Cache Size", "Magnetic Storage", "Optical Storage",
        "Solid State Storage", "SSD", "Hard Disk", "Capacity", "Durability", "Reliability", "Portability"
    ],
    "Data Representation": [
        "Binary", "Hexadecimal", "Denary", "Nibble", "Byte", "Bit", "ASCII", "Unicode",
        "Bitmap Image", "Metadata", "Resolution", "Colour Depth", "Sound Sampling",
        "Sample Rate", "Bit Depth", "Compression", "Lossy", "Lossless"
    ],
    "Networks": [
        "LAN", "WAN", "NIC", "MAC Address", "IP Address", "Router", "Switch", "WAP",
        "Topologies", "Star Topology", "Mesh Topology", "Bus Topology", "Client-Server",
        "Peer-to-Peer", "DNS", "Hosting", "The Cloud"
    ],
    "Protocols and Layers": [
        "TCP/IP", "Application Layer", "Transport Layer", "Internet Layer", "Link Layer",
        "HTTP", "HTTPS", "FTP", "SMTP", "IMAP", "POP", "URL", "Packets"
    ],
    "Network Security": [
        "Malware", "Virus", "Worm", "Trojan", "Spyware", "Phishing", "Brute Force",
        "Denial of Service", "Data Interception", "SQL Injection", "Passwords",
        "Encryption", "Firewall", "Penetration Testing", "Social Engineering"
    ],
    "Systems Software": [
        "Operating System", "User Interface", "Memory Management", "Multitasking",
        "Peripheral Management", "User Management", "File Management", "Utility Software",
        "Defragmentation", "Backup", "Compression Utility", "Encryption Utility"
    ],
    "Ethical Legal Cultural": [
        "Open Source", "Proprietary Software", "Legislation", "Copyright",
        "Computer Misuse Act", "Data Protection Act", "Environmental Impact",
        "Privacy", "Cultural Issues"
    ],
}

CARD_TYPE_META = {
    "standard": {
        "label": "Standard",
        "front_label": "Prompt / keyword",
        "back_label": "Meaning / answer",
    },
    "cloze": {
        "label": "Fill in the blanks",
        "front_label": "Incomplete text",
        "back_label": "Completed answer",
    },
    "diagram": {
        "label": "Diagram / image prompt",
        "front_label": "Prompt / task",
        "back_label": "Model answer",
    },
    "table": {
        "label": "Table / comparison",
        "front_label": "Table starter / headings",
        "back_label": "Completed table / answer",
    },
    "quiz": {
        "label": "Quick quiz",
        "front_label": "Question",
        "back_label": "Answer",
    },
}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def apply_prefix(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    if URL_PREFIX and not path.startswith(URL_PREFIX + "/") and path != URL_PREFIX:
        return f"{URL_PREFIX}{path}"
    return path


def prefixed_url_for(endpoint: str, **values: Any) -> str:
    external = values.pop("_external", False)
    url = flask_url_for(endpoint, _external=external, **values)
    if external:
        return url
    return apply_prefix(url)


app.jinja_env.globals["url_for"] = prefixed_url_for


def add_dual_route(rule: str, endpoint: str | None = None, **options: Any):
    def decorator(func):
        app.add_url_rule(rule, endpoint=endpoint, view_func=func, **options)

        if URL_PREFIX:
            if rule == "/":
                app.add_url_rule(URL_PREFIX, endpoint=f"{func.__name__}_prefixed_root", view_func=func, **options)
                app.add_url_rule(f"{URL_PREFIX}/", endpoint=f"{func.__name__}_prefixed_root_slash", view_func=func, **options)
            else:
                app.add_url_rule(f"{URL_PREFIX}{rule}", endpoint=f"{func.__name__}_prefixed", view_func=func, **options)
        return func
    return decorator


def generate_share_code(length: int = 10) -> str:
    return secrets.token_urlsafe(length)[:length]


def get_current_user() -> str:
    for key in ("username", "user"):
        if session.get(key):
            return str(session[key]).lower()

    forwarded = request.headers.get("X-Forwarded-User") or request.headers.get("X-Remote-User")
    if forwarded:
        return forwarded.lower()

    if AUTH_API_BASE:
        try:
            url = AUTH_API_BASE.rstrip("/") + "/api/session-user"
            headers = {}
            cookie_header = request.headers.get("Cookie")
            if cookie_header:
                headers["Cookie"] = cookie_header
            response = requests.get(url, headers=headers, timeout=3)
            if response.ok:
                payload = response.json()
                username = payload.get("username", "guest")
                if username and username != "guest":
                    return str(username).lower()
        except Exception:
            pass

    return "guest"


def mongo_available() -> bool:
    try:
        mongo_client.admin.command("ping")
        return True
    except Exception:
        return False


def safe_query_many(cursor_factory, default=None):
    if default is None:
        default = []
    try:
        return list(cursor_factory())
    except Exception:
        return default


def safe_query_one(query_factory, default=None):
    try:
        return query_factory()
    except Exception:
        return default


def safe_write(write_factory):
    try:
        return write_factory(), None
    except Exception as exc:
        return None, str(exc)


def serialise_set(doc: dict[str, Any]) -> dict[str, Any]:
    out = {
        "id": str(doc["_id"]),
        "title": doc.get("title", "Untitled set"),
        "owner": doc.get("owner", "guest"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "selected_keywords": doc.get("selected_keywords", []),
        "card_count": doc.get("card_count", len(doc.get("cards", []))),
        "cards": doc.get("cards", []),
        "share_code": doc.get("share_code"),
        "is_public": doc.get("is_public", False),
        "description": doc.get("description", ""),
    }
    return out


def build_default_cards(card_count: int, keywords: list[str]) -> list[dict[str, Any]]:
    card_count = max(10, int(card_count or 10))
    cards = []
    padded_keywords = list(keywords[:card_count])
    while len(padded_keywords) < card_count:
        padded_keywords.append("")

    for idx in range(card_count):
        keyword = padded_keywords[idx]
        cards.append({
            "position": idx + 1,
            "keyword": keyword,
            "card_type": "standard",
            "front_text": keyword or f"Card {idx + 1}",
            "back_text": "",
            "prompt_text": keyword or "",
            "answer_text": "",
            "hint": "",
            "word_bank": "",
            "image_front": "",
            "image_back": "",
            "notes": "",
        })
    return cards


def get_set_or_404(set_id: str) -> dict[str, Any]:
    try:
        oid = ObjectId(set_id)
    except (InvalidId, TypeError):
        abort(404)

    doc = safe_query_one(lambda: sets_collection.find_one({"_id": oid}))
    if not doc:
        abort(404)
    return doc


def can_view(doc: dict[str, Any], username: str) -> bool:
    if doc.get("is_public"):
        return True
    return username != "guest" and username == doc.get("owner")


def can_edit(doc: dict[str, Any], username: str) -> bool:
    return username != "guest" and username == doc.get("owner")


def build_share_url(share_code: str) -> str:
    return f"{request.url_root.rstrip('/')}{apply_prefix(flask_url_for('shared_set', share_code=share_code))}"


@app.context_processor
def inject_globals() -> dict[str, Any]:
    return {
        "card_type_meta": CARD_TYPE_META,
        "current_user": get_current_user(),
        "year": datetime.utcnow().year,
        "url_prefix": URL_PREFIX,
    }


@add_dual_route("/", methods=["GET"])
def index() -> str:
    username = get_current_user()
    db_ok = mongo_available()

    my_sets = []
    if username != "guest" and db_ok:
        my_sets = [
            serialise_set(doc)
            for doc in safe_query_many(
                lambda: sets_collection.find({"owner": username}).sort("updated_at", DESCENDING).limit(24)
            )
        ]

    public_sets = []
    if db_ok:
        public_sets = [
            serialise_set(doc)
            for doc in safe_query_many(
                lambda: sets_collection.find({"is_public": True}).sort("updated_at", DESCENDING).limit(12)
            )
        ]

    return render_template(
        "index.html",
        keyword_groups=KEYWORD_GROUPS,
        my_sets=my_sets,
        public_sets=public_sets,
        card_type_meta=CARD_TYPE_META,
        username=username,
        db_ok=db_ok,
    )


@add_dual_route("/api/me", methods=["GET"])
def api_me():
    return jsonify({"username": get_current_user()})


@add_dual_route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True, "mongo": mongo_available(), "user": get_current_user(), "prefix": URL_PREFIX})


@add_dual_route("/api/generate-template", methods=["POST"])
def api_generate_template():
    payload = request.get_json(force=True)
    card_count = max(10, int(payload.get("card_count", 10)))
    keywords = payload.get("keywords") or []
    title = (payload.get("title") or "New Flashcard Set").strip()

    data = {
        "title": title,
        "description": payload.get("description", ""),
        "selected_keywords": keywords,
        "card_count": card_count,
        "cards": build_default_cards(card_count, keywords),
    }
    return jsonify(data)


@add_dual_route("/editor/new", methods=["GET", "POST"])
def editor_new() -> str:
    username = get_current_user()

    if request.method == "POST":
        title = request.form.get("title", "New Flashcard Set")
        card_count = request.form.get("card_count", request.form.get("count", 10))
        raw_keywords = request.form.getlist("keywords") or request.form.getlist("keyword")
    else:
        title = request.args.get("title", "New Flashcard Set")
        card_count = request.args.get("card_count", request.args.get("count", 10))
        raw_keywords = request.args.getlist("keywords") or request.args.getlist("keyword")

    try:
        card_count = max(10, int(card_count))
    except ValueError:
        card_count = 10

    initial = {
        "id": None,
        "title": title,
        "description": "",
        "selected_keywords": raw_keywords,
        "card_count": card_count,
        "cards": build_default_cards(card_count, raw_keywords),
        "owner": username,
        "share_code": None,
        "is_public": False,
    }

    return render_template("editor.html", initial_set=initial, editable=True)


@add_dual_route("/editor/<set_id>", methods=["GET"])
def editor_existing(set_id: str) -> str:
    username = get_current_user()
    doc = get_set_or_404(set_id)

    if not can_edit(doc, username):
        abort(403)

    return render_template("editor.html", initial_set=serialise_set(doc), editable=True)


@add_dual_route("/api/sets", methods=["POST"])
def save_set():
    username = get_current_user()
    if username == "guest":
        return jsonify({"error": "You need to be logged in to save sets."}), 401

    payload = request.get_json(force=True)
    set_id = payload.get("id")
    cards = payload.get("cards", [])

    if not isinstance(cards, list) or len(cards) < 10:
        return jsonify({"error": "A set must contain at least 10 cards."}), 400

    clean_cards = []
    for idx, card in enumerate(cards, start=1):
        clean_cards.append({
            "position": idx,
            "keyword": str(card.get("keyword", "")).strip(),
            "card_type": str(card.get("card_type", "standard")).strip() or "standard",
            "front_text": str(card.get("front_text", "")).strip(),
            "back_text": str(card.get("back_text", "")).strip(),
            "prompt_text": str(card.get("prompt_text", "")).strip(),
            "answer_text": str(card.get("answer_text", "")).strip(),
            "hint": str(card.get("hint", "")).strip(),
            "word_bank": str(card.get("word_bank", "")).strip(),
            "image_front": str(card.get("image_front", "")),
            "image_back": str(card.get("image_back", "")),
            "notes": str(card.get("notes", "")).strip(),
        })

    document = {
        "title": str(payload.get("title", "Untitled set")).strip() or "Untitled set",
        "description": str(payload.get("description", "")).strip(),
        "owner": username,
        "selected_keywords": payload.get("selected_keywords", []),
        "card_count": len(clean_cards),
        "cards": clean_cards,
        "updated_at": utcnow_iso(),
    }

    if set_id:
        doc = get_set_or_404(set_id)
        if not can_edit(doc, username):
            return jsonify({"error": "You do not have permission to edit this set."}), 403
        sets_collection.update_one({"_id": doc["_id"]}, {"$set": document})
        saved = sets_collection.find_one({"_id": doc["_id"]})
    else:
        document["created_at"] = utcnow_iso()
        document["is_public"] = False
        document["share_code"] = None
        inserted = sets_collection.insert_one(document)
        saved = sets_collection.find_one({"_id": inserted.inserted_id})

    return jsonify({
        "ok": True,
        "set": serialise_set(saved),
        "view_url": apply_prefix(flask_url_for("view_set", set_id=str(saved["_id"]))),
        "play_url": apply_prefix(flask_url_for("play_set", set_id=str(saved["_id"]))),
        "print_url": apply_prefix(flask_url_for("print_set", set_id=str(saved["_id"]))),
        "edit_url": apply_prefix(flask_url_for("editor_existing", set_id=str(saved["_id"]))),
    })


@add_dual_route("/api/sets/<set_id>/share", methods=["POST"])
def share_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)

    if not can_edit(doc, username):
        return jsonify({"error": "You do not have permission to share this set."}), 403

    payload = request.get_json(force=True, silent=True) or {}
    public = bool(payload.get("public", True))
    share_code = doc.get("share_code") or generate_share_code()

    result, err = safe_write(lambda: sets_collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"is_public": public, "share_code": share_code, "updated_at": utcnow_iso()}}
    ))
    if err:
        return jsonify({"error": err}), 500

    updated = sets_collection.find_one({"_id": doc["_id"]})
    return jsonify({
        "ok": True,
        "share_code": updated.get("share_code"),
        "share_url": build_share_url(updated.get("share_code")),
        "is_public": updated.get("is_public", False),
    })


@add_dual_route("/api/sets/<set_id>/delete", methods=["POST"])
def delete_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)

    if not can_edit(doc, username):
        return jsonify({"error": "You do not have permission to delete this set."}), 403

    sets_collection.delete_one({"_id": doc["_id"]})
    return jsonify({"ok": True})


@add_dual_route("/set/<set_id>", methods=["GET"])
def view_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_view(doc, username):
        abort(403)
    return render_template("view_set.html", set_data=serialise_set(doc))


@add_dual_route("/play/<set_id>", methods=["GET"])
def play_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_view(doc, username):
        abort(403)
    return render_template("play_set.html", set_data=serialise_set(doc))


@add_dual_route("/print/<set_id>", methods=["GET"])
def print_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_view(doc, username):
        abort(403)

    set_data = serialise_set(doc)
    cards = set_data["cards"]
    per_page = 4
    front_pages = [cards[i:i + per_page] for i in range(0, len(cards), per_page)]
    back_pages = [list(reversed(page)) for page in front_pages]

    return render_template(
        "print_set.html",
        set_data=set_data,
        front_pages=front_pages,
        back_pages=back_pages,
    )


@add_dual_route("/shared/<share_code>", methods=["GET"])
def shared_set(share_code: str):
    doc = safe_query_one(lambda: sets_collection.find_one({"share_code": share_code}))
    if not doc or not doc.get("is_public"):
        abort(404)
    return render_template("view_set.html", set_data=serialise_set(doc))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You do not have access to that flashcard set."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="That page or flashcard set could not be found."), 404


@app.errorhandler(500)
def internal_error(_error):
    return render_template("error.html", code=500, message="The flashcard app hit an internal error."), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)