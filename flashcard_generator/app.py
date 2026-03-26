from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Any, Callable

import requests
from bson import ObjectId
from bson.errors import InvalidId
from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    request,
    send_from_directory,
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
AUTH_API_BASE = os.getenv("AUTH_API_BASE", "http://auth:5002")
URL_PREFIX = os.getenv("URL_PREFIX", "/flashcards").rstrip("/")
PORT = int(os.getenv("PORT", "5005"))
MIN_CARDS = int(os.getenv("MIN_FLASHCARDS", "5"))

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
    ],
}

CARD_TYPE_META = {
    "standard": {
        "label": "Standard",
        "front_label": "Prompt / keyword",
        "back_label": "Meaning / answer",
    },
    "quiz": {
        "label": "Quiz",
        "front_label": "Question",
        "back_label": "Accepted answer(s) or keywords",
    },
    "cloze": {
        "label": "Fill in the blanks",
        "front_label": "Sentence with blanks",
        "back_label": "Accepted answer(s)",
    },
    "diagram": {
        "label": "Diagram / image prompt",
        "front_label": "Task / question",
        "back_label": "Model answer",
    },
}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def apply_prefix(path: str) -> str:
    if not URL_PREFIX:
        return path
    if not path.startswith("/"):
        path = "/" + path
    if path == URL_PREFIX or path.startswith(URL_PREFIX + "/"):
        return path
    return URL_PREFIX + path


def prefixed_url_for(endpoint: str, **values: Any) -> str:
    external = values.pop("_external", False)
    url = flask_url_for(endpoint, _external=external, **values)
    if external:
        return url
    return apply_prefix(url)


app.jinja_env.globals["url_for"] = prefixed_url_for


@app.context_processor
def inject_globals() -> dict[str, Any]:
    return {
        "current_user": get_current_user(),
        "card_type_meta": CARD_TYPE_META,
        "min_cards": MIN_CARDS,
        "url_prefix": URL_PREFIX,
        "year": datetime.now(timezone.utc).year,
    }


if URL_PREFIX:
    @app.route(f"{URL_PREFIX}/static/<path:filename>")
    def static_prefixed(filename: str):
        return send_from_directory(app.static_folder, filename)


def route_with_prefix(rule: str, **options: Any) -> Callable:
    def decorator(func: Callable) -> Callable:
        endpoint = options.pop("endpoint", func.__name__)
        app.add_url_rule(rule, endpoint=endpoint, view_func=func, **options)
        if URL_PREFIX:
            if rule == "/":
                rules = [URL_PREFIX, f"{URL_PREFIX}/"]
            else:
                rules = [f"{URL_PREFIX}{rule}"]
            for idx, prefixed_rule in enumerate(rules, start=1):
                app.add_url_rule(prefixed_rule, endpoint=f"{endpoint}__prefixed_{idx}", view_func=func, **options)
        return func
    return decorator


def mongo_available() -> bool:
    try:
        mongo_client.admin.command("ping")
        return True
    except Exception:
        return False


def safe_query_one(factory: Callable[[], Any], default: Any = None) -> Any:
    try:
        return factory()
    except PyMongoError:
        return default


def safe_query_many(factory: Callable[[], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    try:
        return factory()
    except PyMongoError:
        return []


def safe_write(factory: Callable[[], Any]) -> tuple[Any, str | None]:
    try:
        return factory(), None
    except PyMongoError as exc:
        return None, str(exc)


def get_current_user() -> str:
    for key in ("username", "user", "display_name", "upn", "email"):
        value = session.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()

    for header in ("X-Forwarded-User", "X-Remote-User", "Remote-User"):
        value = request.headers.get(header)
        if value and value.strip():
            return value.strip().lower()

    cookie_header = request.headers.get("Cookie", "")
    if AUTH_API_BASE and cookie_header:
        try:
            response = requests.get(
                f"{AUTH_API_BASE.rstrip('/')}/api/session-user",
                headers={"Cookie": cookie_header},
                timeout=3,
            )
            if response.ok:
                payload = response.json()
                username = payload.get("username") or payload.get("user") or payload.get("display_name")
                if isinstance(username, str) and username.strip():
                    return username.strip().lower()
        except Exception:
            pass

    return "guest"


def parse_object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def build_default_cards(card_count: int, keywords: list[str]) -> list[dict[str, Any]]:
    card_count = max(MIN_CARDS, int(card_count or MIN_CARDS))
    cards: list[dict[str, Any]] = []
    padded_keywords = list(keywords[:card_count])
    while len(padded_keywords) < card_count:
        padded_keywords.append("")

    for idx in range(card_count):
        keyword = padded_keywords[idx]
        cards.append(
            {
                "position": idx + 1,
                "keyword": keyword,
                "card_type": "standard",
                "front_text": keyword or f"Card {idx + 1}",
                "back_text": "",
                "hint": "",
                "word_bank": "",
                "image_front": "",
                "image_back": "",
                "notes": "",
            }
        )
    return cards


def normalise_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean: list[dict[str, Any]] = []
    for index, card in enumerate(cards or [], start=1):
        card_type = str(card.get("card_type", "standard")).strip().lower()
        if card_type not in CARD_TYPE_META:
            card_type = "standard"
        clean.append(
            {
                "position": index,
                "keyword": str(card.get("keyword", "")).strip(),
                "card_type": card_type,
                "front_text": str(card.get("front_text", "")).strip(),
                "back_text": str(card.get("back_text", "")).strip(),
                "hint": str(card.get("hint", "")).strip(),
                "word_bank": str(card.get("word_bank", "")).strip(),
                "image_front": str(card.get("image_front", "")).strip(),
                "image_back": str(card.get("image_back", "")).strip(),
                "notes": str(card.get("notes", "")).strip(),
            }
        )
    while len(clean) < MIN_CARDS:
        clean.append(
            {
                "position": len(clean) + 1,
                "keyword": "",
                "card_type": "standard",
                "front_text": f"Card {len(clean) + 1}",
                "back_text": "",
                "hint": "",
                "word_bank": "",
                "image_front": "",
                "image_back": "",
                "notes": "",
            }
        )
    for idx, card in enumerate(clean, start=1):
        card["position"] = idx
    return clean


def serialise_set(doc: dict[str, Any]) -> dict[str, Any]:
    out = {
        "id": str(doc.get("_id", "")),
        "title": doc.get("title", "Untitled set"),
        "owner": doc.get("owner", "guest"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "selected_keywords": doc.get("selected_keywords", []),
        "card_count": doc.get("card_count", len(doc.get("cards", []))),
        "cards": normalise_cards(doc.get("cards", [])),
        "share_code": doc.get("share_code", ""),
        "is_public": bool(doc.get("is_public", False)),
        "description": doc.get("description", ""),
    }
    for key in ("created_at", "updated_at"):
        if isinstance(out.get(key), datetime):
            out[key] = out[key].isoformat()
    return out


def get_set_or_404(set_id: str) -> dict[str, Any]:
    oid = parse_object_id(set_id)
    if not oid:
        abort(404)
    doc = safe_query_one(lambda: sets_collection.find_one({"_id": oid}))
    if not doc:
        abort(404)
    return doc


def can_view(doc: dict[str, Any], username: str) -> bool:
    return bool(doc.get("is_public")) or (username != "guest" and username == doc.get("owner"))


def can_edit(doc: dict[str, Any], username: str) -> bool:
    return username != "guest" and username == doc.get("owner")


def build_share_url(share_code: str) -> str:
    return f"{request.url_root.rstrip('/')}{apply_prefix(flask_url_for('shared_set', share_code=share_code))}"


@route_with_prefix("/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True, "mongo": mongo_available(), "user": get_current_user(), "prefix": URL_PREFIX or "/"})


@route_with_prefix("/", methods=["GET"])
def index() -> str:
    username = get_current_user()
    my_sets: list[dict[str, Any]] = []
    public_sets: list[dict[str, Any]] = []
    if mongo_available():
        if username != "guest":
            my_sets = [serialise_set(doc) for doc in safe_query_many(lambda: list(sets_collection.find({"owner": username}).sort("updated_at", DESCENDING).limit(24)))]
        public_sets = [serialise_set(doc) for doc in safe_query_many(lambda: list(sets_collection.find({"is_public": True}).sort("updated_at", DESCENDING).limit(12)))]
    return render_template("index.html", keyword_groups=KEYWORD_GROUPS, my_sets=my_sets, public_sets=public_sets)


@route_with_prefix("/editor/new", methods=["GET", "POST"])
def editor_new() -> str:
    if request.method == "POST":
        title = request.form.get("title", "New Flashcard Set")
        count = request.form.get("card_count", request.form.get("count", MIN_CARDS))
        keywords = request.form.getlist("keyword") or request.form.getlist("keywords")
    else:
        title = request.args.get("title", "New Flashcard Set")
        count = request.args.get("card_count", request.args.get("count", MIN_CARDS))
        keywords = request.args.getlist("keyword") or request.args.getlist("keywords")
    try:
        count = max(MIN_CARDS, int(count))
    except ValueError:
        count = MIN_CARDS
    initial = {
        "id": None,
        "title": title,
        "description": "",
        "selected_keywords": keywords,
        "card_count": count,
        "cards": build_default_cards(count, keywords),
        "owner": get_current_user(),
        "share_code": None,
        "is_public": False,
    }
    return render_template("editor.html", initial_set=initial)


@route_with_prefix("/editor/<set_id>", methods=["GET"])
def editor_existing(set_id: str) -> str:
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_edit(doc, username):
        abort(403)
    return render_template("editor.html", initial_set=serialise_set(doc))


@route_with_prefix("/api/sets", methods=["POST"])
def save_set():
    username = get_current_user()
    if username == "guest":
        return jsonify({"error": "You need to be logged in to save sets."}), 401

    payload = request.get_json(force=True, silent=True) or {}
    cards = normalise_cards(payload.get("cards", []))
    if len(cards) < MIN_CARDS:
        return jsonify({"error": f"A set must contain at least {MIN_CARDS} cards."}), 400

    document = {
        "title": str(payload.get("title", "Untitled set")).strip() or "Untitled set",
        "description": str(payload.get("description", "")).strip(),
        "owner": username,
        "selected_keywords": [str(item).strip() for item in payload.get("selected_keywords", []) if str(item).strip()],
        "card_count": len(cards),
        "cards": cards,
        "updated_at": datetime.now(timezone.utc),
    }

    set_id = str(payload.get("id") or "").strip()
    if set_id:
        doc = get_set_or_404(set_id)
        if not can_edit(doc, username):
            return jsonify({"error": "You do not have permission to edit this set."}), 403
        _, err = safe_write(lambda: sets_collection.update_one({"_id": doc["_id"]}, {"$set": document}))
        if err:
            return jsonify({"error": err}), 500
        saved = sets_collection.find_one({"_id": doc["_id"]})
    else:
        document["created_at"] = datetime.now(timezone.utc)
        document["is_public"] = False
        document["share_code"] = ""
        result, err = safe_write(lambda: sets_collection.insert_one(document))
        if err:
            return jsonify({"error": err}), 500
        saved = sets_collection.find_one({"_id": result.inserted_id})

    if not saved:
        return jsonify({"error": "Saved set could not be reloaded."}), 500

    set_data = serialise_set(saved)
    return jsonify(
        {
            "ok": True,
            "set": set_data,
            "id": set_data["id"],
            "view_url": apply_prefix(flask_url_for("view_set", set_id=set_data["id"])),
            "play_url": apply_prefix(flask_url_for("play_set", set_id=set_data["id"])),
            "print_url": apply_prefix(flask_url_for("print_set", set_id=set_data["id"])),
            "edit_url": apply_prefix(flask_url_for("editor_existing", set_id=set_data["id"])),
        }
    )


@route_with_prefix("/api/sets/<set_id>/share", methods=["POST"])
def share_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_edit(doc, username):
        return jsonify({"error": "You do not have permission to share this set."}), 403

    payload = request.get_json(force=True, silent=True) or {}
    public = bool(payload.get("public", True))
    share_code = doc.get("share_code") or secrets.token_urlsafe(8)
    _, err = safe_write(lambda: sets_collection.update_one({"_id": doc["_id"]}, {"$set": {"is_public": public, "share_code": share_code, "updated_at": datetime.now(timezone.utc)}}))
    if err:
        return jsonify({"error": err}), 500
    updated = sets_collection.find_one({"_id": doc["_id"]})
    if not updated:
        return jsonify({"error": "Unable to reload flashcard set after sharing."}), 500
    return jsonify({"ok": True, "share_code": updated.get("share_code"), "share_url": build_share_url(updated.get("share_code")), "is_public": bool(updated.get("is_public", False))})


@route_with_prefix("/api/sets/<set_id>/delete", methods=["POST"])
def delete_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_edit(doc, username):
        return jsonify({"error": "You do not have permission to delete this set."}), 403
    _, err = safe_write(lambda: sets_collection.delete_one({"_id": doc["_id"]}))
    if err:
        return jsonify({"error": err}), 500
    return jsonify({"ok": True})


@route_with_prefix("/set/<set_id>", methods=["GET"])
def view_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_view(doc, username):
        abort(403)
    return render_template("view_set.html", set_data=serialise_set(doc))


@route_with_prefix("/play/<set_id>", methods=["GET"])
def play_set(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)
    if not can_view(doc, username):
        abort(403)
    return render_template("play_set.html", set_data=serialise_set(doc))


@route_with_prefix("/print/<set_id>", methods=["GET"])
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
    return render_template("print_set.html", set_data=set_data, front_pages=front_pages, back_pages=back_pages)


@route_with_prefix("/shared/<share_code>", methods=["GET"])
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
