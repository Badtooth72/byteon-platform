import unittest
from datetime import datetime, timedelta, timezone

from homework import TRACE_TASKS, mark_trace, parse_due_date, activity_is_new


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


if __name__ == "__main__":
    unittest.main()
