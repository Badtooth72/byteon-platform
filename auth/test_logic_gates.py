import unittest
from logic_gates import mark_attempt, progress_record, public_challenges

class LogicGateTests(unittest.TestCase):
    def test_answers_are_not_public(self):
        self.assertTrue(all("answer" not in item for item in public_challenges()))
    def test_deterministic_marking(self):
        challenge, correct = mark_attempt("build-alarm", ["OR","NOT","AND"])
        self.assertTrue(correct)
        self.assertEqual(progress_record(challenge, correct, ["OR","NOT","AND"])["score"], 1)
    def test_rejects_malformed_truth_table(self):
        with self.assertRaises(ValueError): mark_attempt("simulate-xor", [0,1])

if __name__ == "__main__": unittest.main()
