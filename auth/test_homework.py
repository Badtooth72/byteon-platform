import unittest
from datetime import datetime, timedelta, timezone

from homework import (
    TRACE_TASKS, mark_trace, parse_due_date, activity_is_new, generate_trace,
    highlight_code, validate_target, specific_progress,
)


class HomeworkTests(unittest.TestCase):
    def test_every_trace_table_marks_exact_answers(self):
        for task_id, task in TRACE_TASKS.items():
            with self.subTest(task_id=task_id):
                result = mark_trace(task_id, task["rows"])
                self.assertEqual(result["points"], result["max_points"])
                self.assertEqual(result["percent"], 100)

    def test_trace_table_gives_partial_credit_and_rejects_malformed_rows(self):
        answers = [row.copy() for row in TRACE_TASKS["running-total"]["rows"]]
        answers[0][1] = "99"
        result = mark_trace("running-total", answers)
        self.assertEqual(result["points"], result["max_points"] - 1)
        with self.assertRaises(ValueError):
            mark_trace("running-total", [["3"]])

    def test_existing_activity_must_be_newer_than_assignment(self):
        now = datetime.now(timezone.utc)
        self.assertFalse(activity_is_new({"has_score": True, "updated_at": (now - timedelta(days=1)).isoformat()}, now))
        self.assertTrue(activity_is_new({"has_score": True, "updated_at": (now + timedelta(minutes=1)).isoformat()}, now))
        self.assertFalse(activity_is_new({"has_score": False, "updated_at": now.isoformat()}, now))
        self.assertEqual(parse_due_date("2026-10-01").year, 2026)

    def test_five_fixed_tasks_show_code(self):
        self.assertGreaterEqual(len(TRACE_TASKS), 5)
        for task in TRACE_TASKS.values():
            self.assertIn("\n", task["code"])
            self.assertIn("<span", highlight_code(task["code"]))
        self.assertIn("&lt;", highlight_code("if x < 3:\n    print(x)"))

    def test_random_generators_are_markable_with_double_points(self):
        class FakeRandom:
            def __init__(self, kind):
                self.kind = kind
            def choice(self, options):
                return self.kind
            def randint(self, low, high):
                return low
        for kind in ("total", "threshold", "multiply"):
            with self.subTest(kind=kind):
                task = generate_trace(FakeRandom(kind))
                result = mark_trace("random", task["rows"], task)
                self.assertEqual(result["percent"], 100)
                self.assertEqual(result["points"], result["max_points"])
                self.assertEqual(result["max_points"], 2 * len(task["rows"]) * len(task["columns"]))

    def test_specific_homework_targets(self):
        now = datetime.now(timezone.utc)
        self.assertEqual(validate_target("trace_table", "random", "75"), 75)
        with self.assertRaises(ValueError):
            validate_target("trace_table", "random", "101")
        with self.assertRaises(ValueError):
            validate_target("coding_challenges", "1:99", "70", {"1:1"})
        assignment = {"activity_key": "coding_challenges", "task_id": "1:1", "created_at": now}
        user = {"activities": {"coding_challenges": {"levels": {"1": {"challenges": {"1": {"score": 7, "attempts": 2}}}}}}}
        self.assertEqual(specific_progress(assignment, user), 70)
        assignment = {"activity_key": "logic_gate_quiz", "task_id": "truth-and", "created_at": now}
        user = {"activities": {"logic_gate_quiz": {"truth-and": {"correct": True, "date": now}}}}
        self.assertEqual(specific_progress(assignment, user), 100)
        assignment = {"activity_key": "conversion_game", "task_id": "easy", "created_at": now}
        user = {"activities": {"conversion_game": {"easy": {"score": 8, "question_count": 10, "date": now}}}}
        self.assertEqual(specific_progress(assignment, user), 80)


if __name__ == "__main__":
    unittest.main()
