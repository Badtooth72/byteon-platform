import json
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Callable

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/auth_db")
URL_PREFIX = os.getenv("URL_PREFIX", "").rstrip("/")
SESSION_SECRET = os.getenv("SESSION_SECRET", "super-secret")
FLASHCARD_DB = os.getenv("FLASHCARD_DB")
FLASHCARD_COLLECTION = os.getenv("FLASHCARD_COLLECTION", "flashcard_sets")
SUPER_ADMIN_USERNAMES = {
    item.strip().lower()
    for item in os.getenv("SUPER_ADMIN_USERNAMES", "").split(",")
    if item.strip()
}
PORT = int(os.getenv("PORT", "5005"))

app = Flask(__name__)
app.config["SECRET_KEY"] = SESSION_SECRET
app.config["JSON_SORT_KEYS"] = False

mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)

if FLASHCARD_DB:
    db_name = FLASHCARD_DB
else:
    db_name = MONGO_URI.rsplit("/", 1)[-1].split("?", 1)[0] or "auth_db"

db = mongo_client[db_name]
sets_collection = db[FLASHCARD_COLLECTION]

KEYWORD_GROUPS = {
    "Systems architecture": [
        "CPU",
        "ALU",
        "Control Unit",
        "Cache",
        "Registers",
        "Clock speed",
        "Cores",
        "Fetch-decode-execute cycle",
        "Embedded system",
    ],
    "Memory and storage": [
        "RAM",
        "ROM",
        "Virtual memory",
        "Optical storage",
        "Magnetic storage",
        "Solid-state storage",
        "Capacity",
        "Compression",
        "Cloud storage",
    ],
    "Computer networks": [
        "LAN",
        "WAN",
        "NIC",
        "MAC address",
        "IP address",
        "Protocol",
        "Packet",
        "Router",
        "Switch",
        "Star topology",
        "Bus topology",
        "Mesh topology",
    ],
    "Network security": [
        "Malware",
        "Phishing",
        "Brute force attack",
        "Denial of service",
        "Penetration testing",
        "Firewall",
        "Encryption",
        "Authentication",
        "Biometric security",
    ],
    "Systems software": [
        "Operating system",
        "Utility software",
        "User interface",
        "Multitasking",
        "Memory management",
        "Peripheral management",
        "File management",
    ],
    "Ethical, legal, cultural": [
        "Copyright",
        "Computer Misuse Act",
        "Data Protection Act",
        "Privacy",
        "Environmental impact",
        "Open source",
        "Digital divide",
    ],
}

CARD_TYPE_META = {
    "standard": {
        "label": "Standard",
        "front_label": "Front",
        "back_label": "Back",
    },
    "cloze": {
        "label": "Fill in the blanks",
        "front_label": "Sentence with gap",
        "back_label": "Completed answer",
    },
    "diagram": {
        "label": "Diagram prompt",
        "front_label": "Prompt / image task",
        "back_label": "Model answer",
    },
    "table": {
        "label": "Table / compare",
        "front_label": "Prompt / comparison",
        "back_label": "Completed answer",
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
    if not URL_PREFIX:
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    if path.startswith(URL_PREFIX + "/") or path == URL_PREFIX:
        return path
    return f"{URL_PREFIX}{path}"


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
        "url_prefix": URL_PREFIX,
    }


if URL_PREFIX:
    @app.route(f"{URL_PREFIX}/static/<path:filename>")
    def static_prefixed(filename: str):
        return send_from_directory(app.static_folder, filename)


def route_with_prefix(rule: str, **options: Any) -> Callable:
    """
    Register both /path and /flashcards/path so the app survives
    even if the proxy rewriting is imperfect.
    """
    def decorator(func: Callable) -> Callable:
        endpoint = options.pop("endpoint", func.__name__)
        app.add_url_rule(rule, endpoint=endpoint, view_func=func, **options)

        if URL_PREFIX:
            if rule == "/":
                prefixed_rules = [URL_PREFIX, f"{URL_PREFIX}/"]
            else:
                prefixed_rules = [f"{URL_PREFIX}{rule}"]

            for idx, prefixed_rule in enumerate(prefixed_rules, start=1):
                app.add_url_rule(
                    prefixed_rule,
                    endpoint=f"{endpoint}__prefixed_{idx}",
                    view_func=func,
                    **options,
                )
        return func

    return decorator


def mongo_available() -> bool:
    try:
        mongo_client.admin.command("ping")
        return True
    except Exception as exc:
        logger.warning("Mongo ping failed: %s", exc)
        return False


def safe_query_one(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except PyMongoError as exc:
        logger.exception("Mongo query failed: %s", exc)
        return None


def safe_query_many(fn: Callable[[], list[dict]]) -> list[dict]:
    try:
        return fn()
    except PyMongoError as exc:
        logger.exception("Mongo query failed: %s", exc)
        return []


def safe_write(fn: Callable[[], Any]) -> tuple[Any, str | None]:
    try:
        return fn(), None
    except PyMongoError as exc:
        logger.exception("Mongo write failed: %s", exc)
        return None, str(exc)


def parse_object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def get_current_user() -> str:
    for key in ("username", "user", "display_name", "upn", "email"):
        value = session.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for header in ("X-Forwarded-User", "X-Remote-User", "Remote-User"):
        value = request.headers.get(header)
        if value and value.strip():
            return value.strip()

    return "guest"


def is_super_admin(username: str) -> bool:
    return username.lower() in SUPER_ADMIN_USERNAMES


def normalise_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []

    for index, card in enumerate(cards or [], start=1):
        card_type = str(card.get("card_type", "standard")).strip().lower()
        if card_type not in CARD_TYPE_META:
            card_type = "standard"

        cleaned.append(
            {
                "position": index,
                "keyword": str(card.get("keyword", "")).strip(),
                "card_type": card_type,
                "front_text": str(card.get("front_text", "")).strip(),
                "back_text": str(card.get("back_text", "")).strip(),
                "prompt_text": str(card.get("prompt_text", "")).strip(),
                "answer_text": str(card.get("answer_text", "")).strip(),
                "hint": str(card.get("hint", "")).strip(),
                "word_bank": str(card.get("word_bank", "")).strip(),
                "image_front": str(card.get("image_front", "")).strip(),
                "image_back": str(card.get("image_back", "")).strip(),
                "notes": str(card.get("notes", "")).strip(),
            }
        )

    while len(cleaned) < 10:
        cleaned.append(blank_card(len(cleaned) + 1))

    for index, card in enumerate(cleaned, start=1):
        card["position"] = index

    return cleaned


def blank_card(position: int, card_type: str = "standard") -> dict[str, Any]:
    if card_type not in CARD_TYPE_META:
        card_type = "standard"

    if card_type == "cloze":
        front = "The CPU contains the ______ and the Control Unit."
        back = "The CPU contains the ALU and the Control Unit."
    else:
        front = ""
        back = ""

    return {
        "position": position,
        "keyword": "",
        "card_type": card_type,
        "front_text": front,
        "back_text": back,
        "prompt_text": "",
        "answer_text": "",
        "hint": "",
        "word_bank": "",
        "image_front": "",
        "image_back": "",
        "notes": "",
    }


def serialise_set(doc: dict[str, Any]) -> dict[str, Any]:
    cards = normalise_cards(doc.get("cards", []))
    return {
        "id": str(doc.get("_id", "")),
        "title": doc.get("title", "Untitled set"),
        "description": doc.get("description", ""),
        "owner": doc.get("owner", "guest"),
        "selected_keywords": doc.get("selected_keywords", []),
        "cards": cards,
        "card_count": len(cards),
        "is_public": bool(doc.get("is_public", False)),
        "share_code": doc.get("share_code", ""),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def can_edit(doc: dict[str, Any], username: str) -> bool:
    owner = str(doc.get("owner", "")).strip().lower()
    return username.strip().lower() == owner or is_super_admin(username)


def can_view(doc: dict[str, Any], username: str) -> bool:
    return bool(doc.get("is_public")) or can_edit(doc, username)


def generate_share_code() -> str:
    return secrets.token_urlsafe(8)


def get_set_or_404(set_id: str) -> dict[str, Any]:
    oid = parse_object_id(set_id)
    if not oid:
        abort(404)

    doc = safe_query_one(lambda: sets_collection.find_one({"_id": oid}))
    if not doc:
        abort(404)
    return doc


def build_share_url(share_code: str) -> str:
    path = apply_prefix(flask_url_for("shared_set", share_code=share_code))
    return f"{request.url_root.rstrip('/')}{path}"


@route_with_prefix("/healthz", methods=["GET"])
def healthz():
    return jsonify(
        {
            "ok": True,
            "mongo": mongo_available(),
            "user": get_current_user(),
            "prefix": URL_PREFIX or "/",
        }
    )


@route_with_prefix("/", methods=["GET"])
def index():
    username = get_current_user()
    mongo_ok = mongo_available()

    my_sets: list[dict[str, Any]] = []
    public_sets: list[dict[str, Any]] = []

    if mongo_ok:
        my_sets = [
            serialise_set(doc)
            for doc in safe_query_many(
                lambda: list(
                    sets_collection.find({"owner": username}).sort("updated_at", DESCENDING)
                )
            )
        ]
        public_sets = [
            serialise_set(doc)
            for doc in safe_query_many(
                lambda: list(
                    sets_collection.find({"is_public": True}).sort("updated_at", DESCENDING).limit(24)
                )
            )
            if doc.get("owner") != username
        ]

    return render_template(
        "index.html",
        keyword_groups=KEYWORD_GROUPS,
        card_type_meta=CARD_TYPE_META,
        my_sets=my_sets,
        public_sets=public_sets,
        mongo_ok=mongo_ok,
    )


@route_with_prefix("/editor/new", methods=["POST"])
def editor_new():
    title = request.form.get("title", "").strip() or "Untitled set"

    try:
        card_count = int(request.form.get("card_count", "10"))
    except ValueError:
        card_count = 10

    card_count = max(10, min(card_count, 100))

    selected_keywords = request.form.getlist("keywords") or request.form.getlist("selected_keywords")

    initial_set = {
        "id": "",
        "title": title,
        "description": "",
        "owner": get_current_user(),
        "selected_keywords": selected_keywords,
        "cards": [blank_card(idx + 1) for idx in range(card_count)],
        "card_count": card_count,
        "is_public": False,
        "share_code": "",
        "created_at": "",
        "updated_at": "",
    }

    return render_template(
        "editor.html",
        initial_set=initial_set,
        initial_set_json=json.dumps(initial_set),
        card_type_meta=CARD_TYPE_META,
        card_type_meta_json=json.dumps(CARD_TYPE_META),
    )


@route_with_prefix("/editor/<set_id>", methods=["GET"])
def editor_existing(set_id: str):
    username = get_current_user()
    doc = get_set_or_404(set_id)

    if not can_edit(doc, username):
        abort(403)

    set_data = serialise_set(doc)
    return render_template(
        "editor.html",
        initial_set=set_data,
        initial_set_json=json.dumps(set_data),
        card_type_meta=CARD_TYPE_META,
        card_type_meta_json=json.dumps(CARD_TYPE_META),
    )


@route_with_prefix("/api/sets", methods=["POST"])
def save_set():
    if not mongo_available():
        return (
            jsonify(
                {
                    "error": "MongoDB is not reachable from the flashcard app. Check MONGO_URI/networking."
                }
            ),
            503,
        )

    username = get_current_user()
    payload = request.get_json(force=True, silent=True) or {}

    title = str(payload.get("title", "")).strip() or "Untitled set"
    description = str(payload.get("description", "")).strip()
    selected_keywords = [
        str(item).strip()
        for item in payload.get("selected_keywords", [])
        if str(item).strip()
    ]
    cards = normalise_cards(payload.get("cards", []))

    existing_id = str(payload.get("id", "")).strip()
    existing_doc = None

    if existing_id:
        existing_doc = get_set_or_404(existing_id)
        if not can_edit(existing_doc, username):
            return jsonify({"error": "You do not have permission to edit this set."}), 403

    now = utcnow_iso()

    if existing_doc:
        update_doc = {
            "title": title,
            "description": description,
            "selected_keywords": selected_keywords,
            "cards": cards,
            "updated_at": now,
        }

        _, err = safe_write(
            lambda: sets_collection.update_one(
                {"_id": existing_doc["_id"]},
                {"$set": update_doc},
            )
        )
        if err:
            return jsonify({"error": f"Unable to update flashcard set: {err}"}), 503

        saved = safe_query_one(lambda: sets_collection.find_one({"_id": existing_doc["_id"]}))
    else:
        new_doc = {
            "title": title,
            "description": description,
            "owner": username,
            "selected_keywords": selected_keywords,
            "cards": cards,
            "is_public": False,
            "share_code": "",
            "created_at": now,
            "updated_at": now,
        }

        result, err = safe_write(lambda: sets_collection.insert_one(new_doc))
        if err:
            return jsonify({"error": f"Unable to save flashcard set: {err}"}), 503

        saved = safe_query_one(lambda: sets_collection.find_one({"_id": result.inserted_id}))

    if not saved:
        return jsonify({"error": "Flashcard set was not found after saving."}), 500

    set_data = serialise_set(saved)
    return jsonify(
        {
            "ok": True,
            "id": set_data["id"],
            "title": set_data["title"],
            "updated_at": set_data["updated_at"],
            "view_url": apply_prefix(flask_url_for("view_set", set_id=set_data["id"])),
            "play_url": apply_prefix(flask_url_for("play_set", set_id=set_data["id"])),
            "print_url": apply_prefix(flask_url_for("print_set", set_id=set_data["id"])),
            "edit_url": apply_prefix(flask_url_for("editor_existing", set_id=set_data["id"])),
            "share_code": set_data["share_code"],
            "is_public": set_data["is_public"],
        }
    )


@route_with_prefix("/api/sets/<set_id>/share", methods=["POST"])
def share_set(set_id: str):
    if not mongo_available():
        return (
            jsonify(
                {
                    "error": "MongoDB is not reachable from the flashcard app. Check MONGO_URI/networking."
                }
            ),
            503,
        )

    username = get_current_user()
    doc = get_set_or_404(set_id)

    if not can_edit(doc, username):
        return jsonify({"error": "You do not have permission to share this set."}), 403

    payload = request.get_json(force=True, silent=True) or {}
    public = bool(payload.get("public", True))
    share_code = doc.get("share_code") or generate_share_code()

    _, err = safe_write(
        lambda: sets_collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "is_public": public,
                    "share_code": share_code,
                    "updated_at": utcnow_iso(),
                }
            },
        )
    )
    if err:
        return jsonify({"error": f"Unable to update share settings: {err}"}), 503

    updated = safe_query_one(lambda: sets_collection.find_one({"_id": doc["_id"]}))
    if not updated:
        return jsonify({"error": "Unable to reload flashcard set after sharing."}), 500

    return jsonify(
        {
            "ok": True,
            "share_code": updated.get("share_code"),
            "share_url": build_share_url(updated.get("share_code")),
            "is_public": updated.get("is_public", False),
        }
    )


@route_with_prefix("/api/sets/<set_id>/delete", methods=["POST"])
def delete_set(set_id: str):
    if not mongo_available():
        return (
            jsonify(
                {
                    "error": "MongoDB is not reachable from the flashcard app. Check MONGO_URI/networking."
                }
            ),
            503,
        )

    username = get_current_user()
    doc = get_set_or_404(set_id)

    if not can_edit(doc, username):
        return jsonify({"error": "You do not have permission to delete this set."}), 403

    _, err = safe_write(lambda: sets_collection.delete_one({"_id": doc["_id"]}))
    if err:
        return jsonify({"error": f"Unable to delete flashcard set: {err}"}), 503

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
    front_pages = [cards[idx : idx + per_page] for idx in range(0, len(cards), per_page)]
    back_pages = [list(reversed(page)) for page in front_pages]

    return render_template(
        "print_set.html",
        set_data=set_data,
        front_pages=front_pages,
        back_pages=back_pages,
    )


@route_with_prefix("/shared/<share_code>", methods=["GET"])
def shared_set(share_code: str):
    doc = safe_query_one(lambda: sets_collection.find_one({"share_code": share_code}))
    if not doc or not doc.get("is_public"):
        abort(404)

    return render_template("view_set.html", set_data=serialise_set(doc))


@app.errorhandler(403)
def forbidden(_error):
    return (
        render_template(
            "error.html",
            code=403,
            message="You do not have access to that flashcard set.",
        ),
        403,
    )


@app.errorhandler(404)
def not_found(_error):
    return (
        render_template(
            "error.html",
            code=404,
            message="That page or flashcard set could not be found.",
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(_error):
    return (
        render_template(
            "error.html",
            code=500,
            message="The flashcard app hit an internal error.",
        ),
        500,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)