import unittest
from activity_scores import score_activity


class ActivityScoreTests(unittest.TestCase):
    def test_coding_uses_ten_points_per_saved_challenge(self):
        data = {"levels":{"1":{"challenges":{"1":{"score":10,"attempts":1},"2":{"score":6,"attempts":3}}}}}
        self.assertEqual(score_activity("coding_challenges", data)["percent"], 80)

    def test_conversion_uses_question_count(self):
        data = {"hard":{"score":7,"question_count":10}}
        self.assertEqual(score_activity("conversion_game", data)["percent"], 70)

    def test_logic_ignores_extension_when_calculating_core_percentage(self):
        data = {"identify-and":{"score":1,"correct":True},"extension-xor":{"score":1,"correct":True}}
        result = score_activity("logic_gate_quiz", data)
        self.assertEqual(result["points"], 1)
        self.assertEqual(result["max_points"], 8)

    def test_flashcards_use_best_accuracy(self):
        data = {"summary":{"games_played":3,"best_accuracy":82.5}}
        self.assertEqual(score_activity("flashcard_generator", data)["percent"], 82.5)


if __name__ == "__main__":
    unittest.main()
