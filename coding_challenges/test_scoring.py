import unittest

from scoring import challenge_score


class ChallengeScoreTests(unittest.TestCase):
    def test_correct_score_reduces_by_two_per_attempt(self):
        self.assertEqual(challenge_score(True, 1), 10)
        self.assertEqual(challenge_score(True, 3), 6)
        self.assertEqual(challenge_score(True, 8), 0)

    def test_incorrect_attempt_scores_zero(self):
        self.assertEqual(challenge_score(False, 1), 0)


if __name__ == "__main__":
    unittest.main()
