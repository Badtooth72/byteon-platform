import unittest
from achievements import eligible_achievements, achievement_summary


class AchievementTests(unittest.TestCase):
    def test_first_trace_does_not_unlock_full_lab(self):
        earned = eligible_achievements({"trace_table": {"running-total": {"score": 100}}})
        self.assertIn("trace-first", earned)
        self.assertIn("trace-perfect", earned)
        self.assertNotIn("trace-all", earned)
        self.assertEqual(achievement_summary(earned)["points"], 30)

    def test_badges_cover_all_activities_and_do_not_award_empty_records(self):
        self.assertEqual(eligible_achievements({}), set())
        activities = {"coding_challenges": {"levels": {"1": {"challenges": {"1": {"score": 0, "best_score": 10}}}}},
                      "logic_gate_quiz": {"truth-and": {"correct": True}},
                      "conversion_game": {"hard": {"score": 20, "question_count": 20}},
                      "wordsearch": {"summary": {"wins": 1, "no_hints": 1, "speed": 1, "expert": 1}}}
        earned = eligible_achievements(activities, {"count": 3, "shared": 1})
        for badge in ["coding-first", "logic-first", "conversion-hard", "flashcard-three", "flashcard-share", "wordsearch-expert"]:
            self.assertIn(badge, earned)


if __name__ == '__main__':
    unittest.main()
