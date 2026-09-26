from activity_scores import LOGIC_CORE_IDS, TRACE_CORE_IDS

CATALOGUE = [
    ("coding-first", "Coding", "First program", "Attempt a coding challenge.", 10),
    ("coding-ten", "Coding", "Ten solutions", "Earn points on ten coding challenges.", 20),
    ("coding-level", "Coding", "Level complete", "Earn points on every challenge in a coding level.", 30),
    ("coding-all", "Coding", "Code champion", "Earn points on all 75 coding challenges.", 50),
    ("logic-first", "Logic", "Gate detective", "Answer a core logic question correctly.", 10),
    ("logic-tables", "Logic", "Truth teller", "Complete all three core truth tables correctly.", 20),
    ("logic-all", "Logic", "Circuit master", "Answer all eight core logic questions correctly.", 30),
    ("trace-first", "Trace tables", "On the trail", "Attempt a set trace table.", 10),
    ("trace-perfect", "Trace tables", "Perfect trace", "Score 100% on a set trace table.", 20),
    ("trace-all", "Trace tables", "Trace master", "Score 100% on all five set trace tables.", 30),
    ("trace-random", "Trace tables", "Beyond the basics", "Score 100% on a random trace table.", 20),
    ("conversion-first", "Conversions", "Number explorer", "Complete a conversion quiz.", 10),
    ("conversion-perfect", "Conversions", "Perfect conversion", "Get every answer right in a conversion quiz.", 20),
    ("conversion-hard", "Conversions", "Number master", "Get every answer right in hard mode.", 30),
    ("flashcard-first", "Flashcards", "Deck designer", "Save your first flashcard deck.", 10),
    ("flashcard-three", "Flashcards", "Revision library", "Save three flashcard decks.", 20),
    ("flashcard-share", "Flashcards", "Knowledge sharer", "Share one of your flashcard decks.", 20),
    ("wordsearch-first", "Wordsearch", "First win", "Complete a wordsearch.", 10),
    ("wordsearch-hints", "Wordsearch", "No training wheels", "Complete a wordsearch without hints.", 20),
    ("wordsearch-speed", "Wordsearch", "Speed runner", "Complete a wordsearch in under three minutes.", 20),
    ("wordsearch-expert", "Wordsearch", "Expert survivor", "Complete an expert wordsearch.", 30),
]


def eligible_achievements(activities, decks=None):
    earned = set()
    levels = (activities.get("coding_challenges") or {}).get("levels", {})
    records = [record for level in levels.values() if isinstance(level, dict) for record in (level.get("challenges") or {}).values() if isinstance(record, dict)]
    solved = [record for record in records if max(record.get("score", 0), record.get("best_score", 0)) > 0]
    if records: earned.add("coding-first")
    if len(solved) >= 10: earned.add("coding-ten")
    if any(len(level.get("challenges", {})) >= 25 and all(max(record.get("score", 0), record.get("best_score", 0)) > 0 for record in level["challenges"].values()) for level in levels.values() if isinstance(level, dict)): earned.add("coding-level")
    if len(solved) >= 75: earned.add("coding-all")
    logic = activities.get("logic_gate_quiz") or {}
    correct = {key for key in LOGIC_CORE_IDS if (logic.get(key) or {}).get("correct") or (logic.get(key) or {}).get("score", 0) > 0}
    if correct: earned.add("logic-first")
    if {"truth-and", "truth-or", "truth-not"} <= correct: earned.add("logic-tables")
    if LOGIC_CORE_IDS <= correct: earned.add("logic-all")
    trace = activities.get("trace_table") or {}
    traced = {key for key in TRACE_CORE_IDS if isinstance(trace.get(key), dict)}
    perfect = {key for key in traced if trace[key].get("score", 0) >= 100}
    if traced: earned.add("trace-first")
    if perfect: earned.add("trace-perfect")
    if TRACE_CORE_IDS <= perfect: earned.add("trace-all")
    if (trace.get("random") or {}).get("score", 0) >= 100: earned.add("trace-random")
    conversions = activities.get("conversion_game") or {}
    flags = activities.get("conversion_game_flags") or {}
    if flags.get("perfect"): earned.add("conversion-perfect")
    if flags.get("hard"): earned.add("conversion-hard")
    if conversions: earned.add("conversion-first")
    for mode, record in conversions.items():
        if isinstance(record, dict) and record.get("score", 0) >= record.get("question_count", 10):
            earned.add("conversion-perfect")
            if mode == "hard": earned.add("conversion-hard")
    decks = decks or {}
    if decks.get("count", 0) >= 1: earned.add("flashcard-first")
    if decks.get("count", 0) >= 3: earned.add("flashcard-three")
    if decks.get("shared", 0) >= 1: earned.add("flashcard-share")
    wordsearch = (activities.get("wordsearch") or {}).get("summary", {})
    for flag, badge in [("wins", "wordsearch-first"), ("no_hints", "wordsearch-hints"), ("speed", "wordsearch-speed"), ("expert", "wordsearch-expert")]:
        if wordsearch.get(flag, 0): earned.add(badge)
    return earned


def achievement_summary(earned):
    badges = [{"id": key, "activity": activity, "title": title, "description": description, "points": points, "earned": key in earned}
              for key, activity, title, description, points in CATALOGUE]
    return {"badges": badges, "count": sum(item["earned"] for item in badges), "total": len(badges),
            "points": sum(item["points"] for item in badges if item["earned"])}
