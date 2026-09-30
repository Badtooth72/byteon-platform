import unittest
from unittest.mock import patch

try:
    from flask import Flask
    from arcade import GAMES, make_round, public_round, register_arcade, centipede_unlocked
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
                elif operation == "$unset":
                    target.pop(key, None)
                else:
                    target[key] = value


class FakeAttempts:
    def __init__(self):
        self.rows = []

    def insert_one(self, row):
        self.rows.append(row)


@unittest.skipIf(Flask is None, "Flask is available in the auth container")
class ArcadeTests(unittest.TestCase):
    def make_client(self, points, role="student"):
        app = Flask(__name__)
        app.secret_key = "test-only"
        users, attempts = FakeUsers(points), FakeAttempts()
        users.user["role"] = role
        mongo = type("Mongo", (), {"db": type("DB", (), {"users": users, "arcade_attempts": attempts})()})()
        register_arcade(app, mongo, lambda user: {"points": user["points_for_test"]})
        client = app.test_client()
        with client.session_transaction() as state:
            state["username"] = "student"
        return client, users, attempts

    def test_unlocks_in_hundred_point_steps(self):
        self.assertEqual([game["unlock"] for game in GAMES if game["slug"] != "centipede"], [200, 350, 500, 650, 800, 950, 1100])
        client, _, _ = self.make_client(200)
        self.assertEqual(client.get("/games/hex-snake").status_code, 200)
        self.assertEqual(client.get("/games/bit-flip").status_code, 302)
        self.assertEqual(client.post("/api/games/bit-flip/start").status_code, 403)
        self.assertEqual(client.post("/api/games/packet-patrol/start").status_code, 403)

    def test_admin_can_preview_every_game(self):
        client, _, _ = self.make_client(0, role="admin")
        for game in GAMES:
            self.assertEqual(client.get("/games/" + game["slug"]).status_code, 200)
            if game["slug"] != "centipede":
                self.assertEqual(client.post("/api/games/" + game["slug"] + "/start").status_code, 200)
        self.assertIn(b'dispatch-stage', client.get('/games/cpu-dispatch').data)
        self.assertEqual(client.get('/games/cpu-tower').location, '/games/cpu-dispatch')

    def test_centipede_requires_progress_or_teacher_award(self):
        client, users, _ = self.make_client(1000)
        self.assertEqual(client.get("/games/centipede").status_code, 302)
        self.assertFalse(centipede_unlocked(users.user))
        users.user["rewards"] = {"ready_player_one": {"granted_by": "teacher"}}
        self.assertEqual(client.get("/games/centipede").status_code, 200)
        self.assertEqual(client.post("/api/games/centipede/start").status_code, 404)
        users.user["rewards"] = {}
        with patch("arcade.course_progress", return_value={"percent": 90}):
            self.assertEqual(client.get("/games/centipede").status_code, 200)

    def test_ten_rounds_save_one_score_and_hide_answers(self):
        client, users, attempts = self.make_client(200)
        started = client.post("/api/games/hex-snake/start")
        self.assertEqual(started.status_code, 200)
        self.assertNotIn("correct", started.json["challenge"])
        run_id = started.json["run_id"]
        for round_number in range(1, 11):
            answer = users.user["arcade_runs"]["hex-snake"]["challenge"]["correct"]
            response = client.post("/api/games/hex-snake/answer", json={"answer": answer, "run_id": run_id})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["round"], round_number)
        self.assertTrue(response.json["finished"])
        self.assertEqual(response.json["score"], 100)
        self.assertEqual(users.user["activities"]["arcade"]["hex-snake"]["best"], 100)
        self.assertEqual(len(attempts.rows), 1)
        self.assertEqual(client.post("/api/games/hex-snake/answer", json={"answer": "00"}).status_code, 409)

    def test_snake_crash_counts_as_miss(self):
        client, _, _ = self.make_client(200)
        run_id = client.post("/api/games/hex-snake/start").json["run_id"]
        response = client.post("/api/games/hex-snake/answer", json={"answer": "CRASH", "run_id": run_id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["correct"])
        self.assertEqual(response.json["score"], 0)

    def test_timeout_counts_as_miss_for_action_games(self):
        client, _, _ = self.make_client(950)
        for slug in ("bit-flip", "logic-defender", "ctrl-alt-defeat", "cpu-dispatch"):
            run_id = client.post(f"/api/games/{slug}/start").json["run_id"]
            response = client.post(f"/api/games/{slug}/answer", json={"answer": "TIMEOUT", "run_id": run_id})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json["correct"])

    def test_bit_flip_marks_the_selected_invader(self):
        client, _, _ = self.make_client(350)
        started = client.post("/api/games/bit-flip/start")
        targets = started.json["challenge"]["targets"]
        self.assertEqual(len(set(targets)), 3)
        answer = f"2:{int(targets[2], 16):08b}"
        response = client.post("/api/games/bit-flip/answer", json={"answer": answer, "run_id": started.json["run_id"]})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["correct"])
        self.assertEqual(response.json["score"], 10)

    def test_game_runs_survive_other_game_starts_and_reject_stale_answers(self):
        client, _, _ = self.make_client(950)
        snake = client.post("/api/games/hex-snake/start").json
        shooter = client.post("/api/games/ctrl-alt-defeat/start").json
        self.assertEqual(client.post("/api/games/hex-snake/answer", json={
            "answer": "CRASH", "run_id": snake["run_id"]}).status_code, 200)
        self.assertEqual(client.post("/api/games/ctrl-alt-defeat/answer", json={
            "answer": "TIMEOUT", "run_id": shooter["run_id"]}).status_code, 200)
        replacement = client.post("/api/games/hex-snake/start").json
        self.assertNotEqual(snake["run_id"], replacement["run_id"])
        self.assertEqual(client.post("/api/games/hex-snake/answer", json={
            "answer": "CRASH", "run_id": snake["run_id"]}).status_code, 409)

    def test_shooter_early_game_over_saves_only_server_marked_points(self):
        client, users, attempts = self.make_client(800)
        started = client.post("/api/games/ctrl-alt-defeat/start").json
        answer = users.user["arcade_runs"]["ctrl-alt-defeat"]["challenge"]["correct"]
        client.post("/api/games/ctrl-alt-defeat/answer", json={"run_id": started["run_id"], "answer": answer})
        ended = client.post("/api/games/ctrl-alt-defeat/abort", json={"run_id": started["run_id"], "score": 9999})
        self.assertEqual(ended.status_code, 200)
        self.assertEqual(ended.json["score"], 10)
        self.assertEqual(users.user["activities"]["arcade"]["ctrl-alt-defeat"]["best"], 10)
        self.assertEqual(attempts.rows[0]["rounds"], 1)
        self.assertEqual(client.post("/api/games/ctrl-alt-defeat/abort", json={"run_id": started["run_id"]}).status_code, 409)

    def test_round_generation_and_answer_privacy(self):
        for slug in (game["slug"] for game in GAMES if game["slug"] not in {"centipede", "system-tetris"}):
            challenge = make_round(slug)
            self.assertNotIn("correct", public_round(challenge))
            self.assertNotIn("explanation", public_round(challenge))
            if slug == "hex-snake":
                self.assertEqual(len(challenge["choices"]), 4)
                self.assertIn(challenge["correct"], challenge["choices"])
            elif slug == "bit-flip":
                self.assertEqual(len(challenge["correct"]), 8)
            elif slug == "cpu-dispatch":
                self.assertEqual(challenge["route_length"], len(challenge["correct"].split(">")))
            else:
                self.assertEqual(len(set(challenge["choices"])), 4)

    def test_cpu_dispatch_marks_route_and_rejects_invalid_stations(self):
        client, users, _ = self.make_client(950)
        started = client.post('/api/games/cpu-dispatch/start').json
        self.assertNotIn('correct', started['challenge'])
        self.assertNotIn('explanation', started['challenge'])
        self.assertEqual(client.post('/api/games/cpu-dispatch/answer', json={
            'run_id': started['run_id'], 'answer': 'PC>GPU'}).status_code, 400)
        answer = users.user['arcade_runs']['cpu-dispatch']['challenge']['correct']
        result = client.post('/api/games/cpu-dispatch/answer', json={
            'run_id': started['run_id'], 'answer': answer})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json['correct'])
        self.assertEqual(result.json['score'], 10)

    def test_tetris_saves_separate_line_record(self):
        client, users, attempts = self.make_client(1100)
        started = client.post("/api/games/system-tetris/start").json
        self.assertNotIn("challenge", started)
        result = client.post("/api/games/system-tetris/finish", json={"run_id": started["run_id"], "lines": 0})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(users.user["activities"]["arcade"]["system-tetris"]["best_lines"], 0)
        self.assertEqual(attempts.rows[-1]["lines"], 0)
        self.assertEqual(client.post("/api/games/system-tetris/finish", json={"run_id": started["run_id"], "lines": 0}).status_code, 409)
        started = client.post("/api/games/system-tetris/start").json
        self.assertEqual(client.post("/api/games/system-tetris/finish", json={"run_id": started["run_id"], "lines": 100}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
