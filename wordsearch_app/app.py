from __future__ import annotations

import random
import re
import os
import string
from typing import Any

from flask import Flask, jsonify, render_template, request

from puzzle_data import TERM_BANK, all_terms

app = Flask(__name__)

URL_PREFIX = os.getenv("URL_PREFIX", "/wordsearch_app").rstrip("/")

DIFFICULTY_PRESETS = {
    "easy": {
        "label": "Easy",
        "size": 12,
        "words": 8,
        "directions": [(0, 1), (1, 0)],
    },
    "medium": {
        "label": "Medium",
        "size": 14,
        "words": 10,
        "directions": [(0, 1), (1, 0), (0, -1), (-1, 0)],
    },
    "hard": {
        "label": "Hard",
        "size": 16,
        "words": 12,
        "directions": [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (-1, -1), (1, -1), (-1, 1),
        ],
    },
    "expert": {
        "label": "Expert",
        "size": 18,
        "words": 14,
        "directions": [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (-1, -1), (1, -1), (-1, 1),
        ],
    },
}


def normalize_term(term: str) -> str:
    return re.sub(r"[^A-Za-z]", "", term).upper()


def build_term_pool(category: str, max_length: int) -> list[dict[str, Any]]:
    if category == "mixed":
        pool = all_terms()
    else:
        category_bundle = TERM_BANK.get(category)
        if not category_bundle:
            pool = all_terms()
        else:
            pool = [
                {
                    "category_key": category,
                    "category_label": category_bundle["label"],
                    **item,
                }
                for item in category_bundle["terms"]
            ]

    filtered = []
    seen = set()
    for item in pool:
        answer = normalize_term(item["term"])
        if 3 <= len(answer) <= max_length and answer not in seen:
            seen.add(answer)
            filtered.append({
                **item,
                "answer": answer,
                "length": len(answer),
            })
    return filtered


def pick_terms(category: str, difficulty: str) -> list[dict[str, Any]]:
    preset = DIFFICULTY_PRESETS[difficulty]
    size = preset["size"]
    requested = preset["words"]
    pool = build_term_pool(category, size)

    if not pool:
        raise ValueError("No terms available for this configuration.")

    if category == "mixed":
        by_category: dict[str, list[dict[str, Any]]] = {}
        for item in pool:
            by_category.setdefault(item["category_key"], []).append(item)

        chosen: list[dict[str, Any]] = []
        category_keys = list(by_category.keys())
        random.shuffle(category_keys)
        while len(chosen) < requested and category_keys:
            progressed = False
            for key in category_keys:
                available = [item for item in by_category[key] if item not in chosen]
                if available and len(chosen) < requested:
                    chosen.append(random.choice(available))
                    progressed = True
            if not progressed:
                break

        if len(chosen) < requested:
            remaining = [item for item in pool if item not in chosen]
            random.shuffle(remaining)
            chosen.extend(remaining[: requested - len(chosen)])
    else:
        chosen = random.sample(pool, k=min(requested, len(pool)))

    chosen.sort(key=lambda item: item["length"], reverse=True)
    return chosen


def can_place(board: list[list[str]], word: str, row: int, col: int, dr: int, dc: int) -> bool:
    size = len(board)
    end_row = row + dr * (len(word) - 1)
    end_col = col + dc * (len(word) - 1)
    if not (0 <= end_row < size and 0 <= end_col < size):
        return False

    for index, char in enumerate(word):
        r = row + dr * index
        c = col + dc * index
        current = board[r][c]
        if current not in ("", char):
            return False
    return True


def place_word(board: list[list[str]], word: str, row: int, col: int, dr: int, dc: int) -> list[list[int]]:
    path: list[list[int]] = []
    for index, char in enumerate(word):
        r = row + dr * index
        c = col + dc * index
        board[r][c] = char
        path.append([r, c])
    return path


def generate_board(selected_terms: list[dict[str, Any]], difficulty: str) -> tuple[list[list[str]], list[dict[str, Any]]]:
    preset = DIFFICULTY_PRESETS[difficulty]
    size = preset["size"]
    directions = preset["directions"][:]

    for _ in range(200):
        board = [["" for _ in range(size)] for _ in range(size)]
        placements: list[dict[str, Any]] = []
        success = True

        for item in selected_terms:
            word = item["answer"]
            attempts: list[tuple[int, int, int, int]] = []
            shuffled_directions = directions[:]
            random.shuffle(shuffled_directions)
            for dr, dc in shuffled_directions:
                rows = list(range(size))
                cols = list(range(size))
                random.shuffle(rows)
                random.shuffle(cols)
                for row in rows:
                    for col in cols:
                        attempts.append((row, col, dr, dc))
            random.shuffle(attempts)

            placed = False
            for row, col, dr, dc in attempts:
                if can_place(board, word, row, col, dr, dc):
                    path = place_word(board, word, row, col, dr, dc)
                    placements.append({
                        "key": item["answer"],
                        "label": item["term"],
                        "answer": item["answer"],
                        "clue": item["clue"],
                        "length": item["length"],
                        "category": item["category_label"],
                        "path": path,
                    })
                    placed = True
                    break

            if not placed:
                success = False
                break

        if success:
            filler_letters = "EEEEAAAARRIIOOTTNNSSLLCCDMPUGFYWBVKXJQZ"
            for row in range(size):
                for col in range(size):
                    if not board[row][col]:
                        board[row][col] = random.choice(filler_letters)
            return board, placements

    raise RuntimeError("Unable to generate a puzzle with the chosen settings.")


@app.route("/")
def index():
    categories = {
        "mixed": "Mixed J277 Terms",
        **{key: bundle["label"] for key, bundle in TERM_BANK.items()},
    }
    return render_template(
        "index.html",
        categories=categories,
        difficulties={key: preset["label"] for key, preset in DIFFICULTY_PRESETS.items()},
    )


@app.route("/api/new-game", methods=["POST"])
def api_new_game():
    payload = request.get_json(silent=True) or {}
    difficulty = payload.get("difficulty", "medium")
    category = payload.get("category", "mixed")

    if difficulty not in DIFFICULTY_PRESETS:
        return jsonify({"error": "Invalid difficulty."}), 400

    try:
        selected_terms = pick_terms(category, difficulty)
        board, placements = generate_board(selected_terms, difficulty)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    preset = DIFFICULTY_PRESETS[difficulty]

    return jsonify(
        {
            "difficulty": difficulty,
            "difficulty_label": preset["label"],
            "category": category,
            "category_label": "Mixed J277 Terms" if category == "mixed" else TERM_BANK.get(category, {}).get("label", "Mixed J277 Terms"),
            "size": preset["size"],
            "grid": board,
            "words": placements,
        }
    )


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
