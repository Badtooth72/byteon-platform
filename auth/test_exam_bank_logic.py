import unittest

from exam_bank_logic import parse_ao_marks, summarise_test, coverage_percentages, validate_question_tables


class ExamBankLogicTests(unittest.TestCase):
    def test_ao_breakdown_requires_all_marks(self):
        self.assertEqual(parse_ao_marks({"AO1": "1", "AO2": "0", "AO3": "2"}, 3),
                         ({"AO1": 1, "AO2": 0, "AO3": 2}, "teacher_verified"))
        with self.assertRaises(ValueError):
            parse_ao_marks({"AO1": "1", "AO2": "", "AO3": "2"}, 3)
        with self.assertRaises(ValueError):
            parse_ao_marks({"AO1": "1", "AO2": "0", "AO3": "2"}, 4)

    def test_test_totals_separate_known_and_unknown_ao_marks(self):
        questions = [
            {"marks": 3, "topic_codes": ["2.1"], "ao_marks": {"AO1": 1, "AO2": 2, "AO3": 0},
             "ao_review_status": "teacher_verified"},
            {"marks": 4, "topic_codes": ["2.1", "2.2"], "ao_review_status": "unassigned"},
        ]
        summary = summarise_test(questions)
        self.assertEqual(summary["total_marks"], 7)
        self.assertEqual(summary["topic_marks"], {"2.1": 7, "2.2": 4})
        self.assertEqual(summary["ao_marks"], {"AO1": 1, "AO2": 2, "AO3": 0})
        self.assertEqual(summary["unknown_ao_marks"], 4)

    def test_coverage_splits_shared_topics_and_uses_full_subtopic_marks(self):
        questions = [
            {"marks": 4, "topic_codes": ["2.1", "2.2"], "subtopic": "Searching"},
            {"marks": 6, "topic_codes": ["2.2"], "subtopic": "Iteration"},
        ]
        topics = coverage_percentages(questions, "topic")
        self.assertEqual(topics["2.1"]["percent"], 20)
        self.assertEqual(topics["2.2"]["percent"], 80)
        subtopics = coverage_percentages(questions, "subtopic")
        self.assertEqual(subtopics["2.1 · Searching"]["percent"], 40)
        self.assertEqual(subtopics["2.2 · Iteration"]["percent"], 60)

    def test_table_layout_rejects_missing_cells_and_duplicate_answer_keys(self):
        table = [{"caption": "Conversion", "columns": ["Binary", "Denary"],
                  "rows": [["1010", {"answer_key": "a"}], [{"answer_key": "b"}, "12"]]}]
        self.assertEqual(validate_question_tables(table), table)
        with self.assertRaises(ValueError):
            validate_question_tables([{"caption": "Broken", "columns": ["A", "B"], "rows": [["1"]]}])
        with self.assertRaises(ValueError):
            validate_question_tables([{"caption": "Repeated", "columns": ["A", "B"],
                                       "rows": [[{"answer_key": "x"}, {"answer_key": "x"}]]}])
