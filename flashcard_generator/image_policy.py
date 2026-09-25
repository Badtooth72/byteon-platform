"""Approved flashcard illustrations and the image values accepted from decks."""

STOCK_IMAGES = (
    ("cpu", "CPU chip"),
    ("binary", "Binary digits"),
    ("memory", "Memory modules"),
    ("network", "Computer network"),
    ("security", "Cyber security"),
    ("logic", "Logic gates"),
    ("database", "Database"),
    ("code", "Programming code"),
)

IMAGE_FIELDS = ("image_front", "image_back")


def stock_image_choices(prefix="/flashcards"):
    prefix = prefix.rstrip("/")
    return [
        {"id": image_id, "label": label, "url": f"{prefix}/static/stock/{image_id}.svg"}
        for image_id, label in STOCK_IMAGES
    ]


def approved_image_url(value, prefix="/flashcards"):
    allowed = {image["url"] for image in stock_image_choices(prefix)}
    value = str(value or "").strip()
    return value if value in allowed else ""


def has_unapproved_images(cards, prefix="/flashcards"):
    if not isinstance(cards, list) or any(not isinstance(card, dict) for card in cards):
        return True
    return any(
        card.get(field) and not approved_image_url(card[field], prefix)
        for card in cards
        for field in IMAGE_FIELDS
    )
