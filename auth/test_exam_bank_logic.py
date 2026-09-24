import unittest

from exam_bank_logic import parse_ao_marks, summarise_test


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
