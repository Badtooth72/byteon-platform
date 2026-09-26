from datetime import datetime


class ChallengeRepository:
    def __init__(self, mongo):
        self.mongo = mongo

    def find(self, level, challenge_id):
        return self.mongo.db.challenges.find_one(
            {"level": int(level), "challenge_id": int(challenge_id)}, {"_id": 0}
        )


class ProgressRepository:
    def __init__(self, mongo):
        self.mongo = mongo

    def challenge_progress(self, username, level, challenge_id):
        user = self.mongo.db.users.find_one({"username": username}) or {}
        return user.get("activities", {}).get("coding_challenges", {}).get(
            "levels", {}
        ).get(level, {}).get("challenges", {}).get(challenge_id, {})

    def save(self, username, level, challenge_id, score, attempts, submission):
        path = f"activities.coding_challenges.levels.{level}.challenges.{challenge_id}"
        self.mongo.db.users.update_one(
            {"username": username},
            {"$set": {f"{path}.schema_version": 1, f"{path}.score": score,
                      f"{path}.attempts": attempts, f"{path}.submission": submission,
                      f"{path}.date": datetime.utcnow()}, "$max": {f"{path}.best_score": score}},
            upsert=False,
        )
        user = self.mongo.db.users.find_one({"username": username}) or {}
        challenges = user.get("activities", {}).get("coding_challenges", {}).get(
            "levels", {}
        ).get(level, {}).get("challenges", {})
        total = sum(item.get("score", 0) for item in challenges.values())
        self.mongo.db.users.update_one(
            {"username": username},
            {"$set": {f"activities.coding_challenges.levels.{level}.total_score": total}},
        )
        return total
