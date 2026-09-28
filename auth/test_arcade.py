import unittest

try:
    from flask import Flask
    from arcade import GAMES, make_round, public_round, register_arcade
except ModuleNotFoundError:
    Flask = None


class FakeUsers:
    def __init__(self, points):
        self.user = {"_id": 1, "username": "student", "points_for_test": points, "activities": {}}

    def find_one(self, query):
        return self.user if query.get("username") == "student" else None

    def update_one(self, query, changes):
        for operation, values in changes.items():
            for path, value in values.items():
                target = self.user
                parts = path.split(".")
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                key = parts[-1]
                if operation == "$inc":
                    target[key] = target.get(key, 0) + value
                elif operation == "$max":
                    target[key] = max(target.get(key, 0), value)
                else:
                    target[key] = value


class FakeAttempts:
    def __init__(self):
        self.rows = []

    def insert_one(self, row):
        self.rows.append(row)


@unittest.skipIf(Flask is None, "Flask is available in the auth container")
class ArcadeTests(unittest.TestCase):
    def make_client(self, points):
        app = Flask(__name__)
        app.secret_key = "test-only"
        users, attempts = FakeUsers(points), FakeAttempts()
        mongo = type("Mongo", (), {"db": type("DB", (), {"users": users, "arcade_attempts": attempts})()})()
        register_arcade(app, mongo, lambda user: {"points": user["points_for_test"]})
        client = app.test_client()
        with client.session_transaction() as state:
            state["username"] = "student"
        return client, users, attempts

    def test_unlocks_in_hundred_point_steps(self):
        self.assertEqual([game["unlock"] for game in GAMES], [100, 200, 300])
        client, _, _ = self.make_client(100)
        self.assertEqual(client.get("/games/hex-snake").status_code, 200)
        self.assertEqual(client.get("/games/bit-flip").status_code, 302)
        self.assertEqual(client.post("/api/games/bit-flip/start").status_code, 403)
        self.assertEqual(client.post("/api/games/packet-patrol/start").status_code, 403)

    def test_ten_rounds_save_one_score_and_hide_answers(self):
        client, users, attempts = self.make_client(100)
        started = client.post("/api/games/hex-snake/start")
        self.assertEqual(started.status_code, 200)
        self.assertNotIn("correct", started.json["challenge"])
        for round_number in range(1, 11):
            with client.session_transaction() as state:
                answer = state["arcade_run"]["challenge"]["correct"]
            response = client.post("/api/games/hex-snake/answer", json={"answer": answer})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["round"], round_number)
        self.assertTrue(response.json["finished"])
        self.assertEqual(response.json["score"], 100)
        self.assertEqual(users.user["activities"]["arcade"]["hex-snake"]["best"], 100)
        self.assertEqual(len(attempts.rows), 1)
        self.assertEqual(client.post("/api/games/hex-snake/answer", json={"answer": "00"}).status_code, 409)

    def test_round_generation_and_answer_privacy(self):
        for slug in ("hex-snake", "bit-flip", "packet-patrol"):
            challenge = make_round(slug)
            self.assertNotIn("correct", public_round(challenge))
            self.assertNotIn("explanation", public_round(challenge))
            if slug == "hex-snake":
                self.assertEqual(len(challenge["choices"]), 4)
                self.assertIn(challenge["correct"], challenge["choices"])
            elif slug == "bit-flip":
                self.assertEqual(len(challenge["correct"]), 8)
            else:
                self.assertEqual(len(set(challenge["choices"])), 4)


if __name__ == "__main__":
    unittest.main()
