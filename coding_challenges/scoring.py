def challenge_score(correct: bool, attempts: int, maximum: int = 10) -> int:
    """Return the authoritative score for a marked coding attempt."""
    if not correct:
        return 0
    safe_attempts = max(1, int(attempts))
    return max(maximum - (safe_attempts - 1) * 2, 0)
