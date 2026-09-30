import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    Environment = FileSystemLoader = None

from homework import (
    TRACE_TASKS, mark_trace, parse_due_date, activity_is_new, generate_trace,
    highlight_code, validate_target, specific_progress,
    summarise_task_status, assignment_tasks, homework_reminder, can_view_homework,
)


class HomeworkTests(unittest.TestCase):
    @unittest.skipIf(Environment is None, "Jinja2 is available in the auth container")
    def test_homework_templates_compile(self):
        environment = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
        environment.get_template("homework.html")
        environment.get_template("homework_detail.html")

    def test_drafts_only_visible_to_author_until_published(self):
        assignment = {"status": "draft", "class_name": "11A", "created_by": "teacher1"}
        self.assertTrue(can_view_homework(assignment, {"role": "teacher", "username": "teacher1"}))
        self.assertFalse(can_view_homework(assignment, {"role": "teacher", "username": "teacher2"}))
        self.assertFalse(can_view_homework(assignment, {"role": "student", "username": "pupil", "class_name": "11A"}))
        assignment["status"] = "published"
        self.assertTrue(can_view_homework(assignment, {"role": "student", "class_name": "11A"}))
        self.assertFalse(can_view_homework(assignment, {"role": "student", "class_name": "11B"}))

    def test_homework_reminders_follow_due_date_and_completion(self):
        now = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)
        due = datetime(2026, 10, 1, 23, 59, tzinfo=timezone.utc)
        self.assertEqual(homework_reminder(due, "Not started", now)["kind"], "soon")
        self.assertEqual(homework_reminder(due, "Submitted", now)["kind"], "complete")
        self.assertEqual(homework_reminder(due, "In progress", now + timedelta(days=3))["kind"], "overdue")

    def test_multiple_tasks_require_the_selected_number_of_targets(self):
        tasks = [{"score": 80, "target_score": 70}, {"score": 60, "target_score": 70}, {"score": None, "target_score": 70}]
        self.assertEqual(summarise_task_status(tasks)["label"], "In progress")
        self.assertEqual(summarise_task_status(tasks, 1)["label"], "Target met")
        self.assertEqual(summarise_task_status(tasks)["reached"], 1)
        self.assertEqual(len(assignment_tasks({"task_id": "running-total"})), 1)

    def test_whole_coding_level_uses_all_challenges_as_denominator(self):
        assignment = {"activity_key": "coding_challenges", "task_id": "level:1", "challenge_count": 25}
        user = {"activities": {"coding_challenges": {"levels": {"1": {"challenges": {"1": {"score": 10}}}}}}}
        self.assertEqual(specific_progress(assignment, user), 4)

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
