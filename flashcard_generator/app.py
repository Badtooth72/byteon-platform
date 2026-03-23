from __future__ import annotations

import math
import os
import secrets
from datetime import datetime
from typing import Any

import requests
from bson import ObjectId
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)
app.secret_key = os.getenv("FLASHCARD_SECRET_KEY", "change-me-in-production")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
FLASHCARD_DB = os.getenv("FLASHCARD_DB", "auth_db")
FLASHCARD_COLLECTION = os.getenv("FLASHCARD_COLLECTION", "flashcard_sets")
AUTH_API_BASE = os.getenv("AUTH_API_BASE", "")

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
        "Bitmap Image", "Metadata", "Resolution", "Colour Depth", "Sound Sampling", "Sample Rate",
        "Bit Depth", "Compression", "Lossy", "Lossless"
    ],
    "Networks": [
        "LAN", "WAN", "NIC", "MAC Address", "IP Address", "Router", "Switch", "WAP",
        "Topologies", "Star Topology", "Mesh Topology", "Bus Topology", "Client-Server", "Peer-to-Peer",
        "DNS", "Hosting", "The Cloud"
    ],
    "Protocols and Layers": [
        "TCP/IP", "Application Layer", "Transport Layer", "Internet Layer", "Link Layer",
        "HTTP", "HTTPS", "FTP", "SMTP", "IMAP", "POP", "URL", "Packets"
    ],
    "Network Security": [
        "Malware", "Virus", "Worm", "Trojan", "Spyware", "Phishing", "Brute Force",
        "Denial of Service", "Data Interception", "SQL Injection", "Passwords", "Encryption", "Firewall",
        "Penetration Testing", "Social Engineering"
    ],
    "Systems Software": [
        "Operating System", "User Interface", "Memory Management", "Multitasking", "Peripheral Management",
        "User Management", "File Management", "Utility Software", "Defragmentation", "Backup", "Compression Utility",
        "Encryption Utility"
    ],
    "Ethical Legal Cultural": [
        "Open Source", "Proprietary Software", "Legislation", "Copyright", "Computer Misuse Act",
        "Data Protection Act", "Environmental Impact", "Privacy", "Cultural Issues"
    ]
}

CARD_TYPE_META = {
    "standard": {
        "label": "Standard",
        "front_label": "Prompt / keyword",
        "back_label": "Meaning / answer"
    },
    "cloze": {
        "label": "Fill in the blanks",
        "front_label": "Incomplete text",
        "back_label": "Completed answer"
    },
    "diagram": {
        "label": "Diagram / image prompt",
        "front_label": "Prompt / task",
        "back_label": "Model answer"
    },
    "table": {
        "label": "Table / comparison",
        "front_label": "Table starter / headings",
        "back_label": "Completed table / answer"
    },
    "quiz": {
        "label": "Quick quiz",
        "front_label": "Question",
        "back_label": "Answer"
    }
}


def utcnow() -> datetime:
    return datetime.utcnow()


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
    for key in ("created_at", "updated_at"):
        if isinstance(out.get(key), datetime):
            out[key] = out[key].isoformat()
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
            "notes": ""
        })
    return cards


def get_set_or_404(set_id: str) -> dict[str, Any]:
    try:
        doc = safe_query_one(lambda: sets_collection.find_one({"_id": ObjectId(set_id)}))
        return doc or abort(404)
    except Exception:
        abort(404)


def can_view(doc: dict[str, Any], username: str) -> bool:
    if doc.get("is_public"):
        return True
    return username != "guest" and username == doc.get("owner")


def can_edit(doc: dict[str, Any], username: str) -> bool:
    return username != "guest" and username == doc.get("owner")


def card_type_meta(card_type: str) -> dict[str, str]:
    return CARD_TYPE_META.get(card_type, CARD_TYPE_META["standard"])


@app.context_processor
def inject_globals() -> dict[str, Any]:
    return {
        "card_type_meta": CARD_TYPE_META,
        "current_user": get_current_user(),
        "year": datetime.utcnow().year,
    }


@app.get("/")
def index() -> str:
    username = get_current_user()
    db_ok = mongo_available()
    my_sets = []
    if username != "guest" and db_ok:
        my_sets = [serialise_set(doc) for doc in safe_query_many(lambda: sets_collection.find({"owner": username}).sort("updated_at", -1).limit(24))]

    public_sets = []
    if db_ok:
        public_sets = [
            serialise_set(doc) for doc in safe_query_many(lambda: sets_collection.find({"is_public": True}).sort("updated_at", -1).limit(12))
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


@app.get("/api/me")
def api_me():
    return jsonify({"username": get_current_user()})


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "mongo": mongo_available(), "user": get_current_user()})


@app.post("/api/generate-template")
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


@app.get("/editor/new")
def editor_new() -> str:
    username = get_current_user()
    card_count = max(10, int(request.args.get("count", 10)))
    raw_keywords = request.args.getlist("keyword")
    title = request.args.get("title", "New Flashcard Set")
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


@app.get("/editor/<set_id>")
def editor_existing(set_id: str) -> str:
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_edit(doc, username):
        abort(403)
    return render_template("editor.html", initial_set=serialise_set(doc), editable=True)


@app.post("/api/sets")
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
        "updated_at": utcnow(),
    }

    if set_id:
        doc = get_set_or_404(set_id)
        if not can_edit(doc, username):
            return jsonify({"error": "You do not have permission to edit this set."}), 403
        sets_collection.update_one({"_id": doc["_id"]}, {"$set": document})
        saved = sets_collection.find_one({"_id": doc["_id"]})
    else:
        document["created_at"] = utcnow()
        document["is_public"] = False
        document["share_code"] = None
        inserted = sets_collection.insert_one(document)
        saved = sets_collection.find_one({"_id": inserted.inserted_id})

    return jsonify({"ok": True, "set": serialise_set(saved)})


@app.post("/api/sets/<set_id>/share")
def share_set(set_id: str):
    if not mongo_available():
        return jsonify({"error": "MongoDB is not reachable from the flashcard app. Check MONGO_URI/networking."}), 503
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_edit(doc, username):
        return jsonify({"error": "You do not have permission to share this set."}), 403

    payload = request.get_json(force=True, silent=True) or {}
    public = bool(payload.get("public", True))
    share_code = doc.get("share_code") or generate_share_code()
    sets_collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"is_public": public, "share_code": share_code, "updated_at": utcnow()}}
    )
    updated = sets_collection.find_one({"_id": doc["_id"]})
    return jsonify({
        "ok": True,
        "share_code": updated.get("share_code"),
        "share_url": url_for("shared_set", share_code=updated.get("share_code"), _external=True),
        "is_public": updated.get("is_public", False),
    })


@app.post("/api/sets/<set_id>/delete")
def delete_set(set_id: str):
    if not mongo_available():
        return jsonify({"error": "MongoDB is not reachable from the flashcard app. Check MONGO_URI/networking."}), 503
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_edit(doc, username):
        return jsonify({"error": "You do not have permission to delete this set."}), 403
    _, err = safe_write(lambda: sets_collection.delete_one({"_id": doc["_id"]}))
    if err:
        return jsonify({"error": f"Unable to delete flashcard set: {err}"}), 503
    return jsonify({"ok": True})


@app.get("/set/<set_id>")
def view_set(set_id: str) -> str:
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_view(doc, username):
        abort(403)
    return render_template("view_set.html", set_data=serialise_set(doc))


@app.get("/play/<set_id>")
def play_set(set_id: str) -> str:
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_view(doc, username):
        abort(403)
    return render_template("play_set.html", set_data=serialise_set(doc))


@app.get("/print/<set_id>")
def print_set(set_id: str) -> str:
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_view(doc, username):
        abort(403)

    set_data = serialise_set(doc)
    cards = set_data["cards"]
    per_page = 4
    front_pages = [cards[idx: idx + per_page] for idx in range(0, len(cards), per_page)]
    back_pages = [list(reversed(page)) for page in front_pages]
    return render_template("print_set.html", set_data=set_data, front_pages=front_pages, back_pages=back_pages)


@app.get("/shared/<share_code>")
def shared_set(share_code: str) -> str:
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)


@app.errorhandler(500)
def internal_error(_error):
    return render_template("error.html", code=500, message="The flashcard app hit an internal error. Check Mongo connectivity and container logs."), 500
