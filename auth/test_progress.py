import unittest

from progress import build_progress_record, validate_progress_payload


class ProgressTests(unittest.TestCase):
    def test_builds_versioned_record(self):
        activity, challenge, record = build_progress_record({
            "activity_key": "wordsearch", "challenge_id": "daily", "score": 8
        })
        self.assertEqual((activity, challenge), ("wordsearch", "daily"))
        self.assertEqual(record["schema_version"], 1)

    def test_rejects_unowned_activity_and_invalid_score(self):
        with self.assertRaisesRegex(ValueError, "own service"):
            validate_progress_payload({"activity_key": "coding_challenges", "score": 10})
        with self.assertRaisesRegex(ValueError, "Invalid score"):
            validate_progress_payload({"activity_key": "wordsearch", "score": 1000})


if __name__ == "__main__":
    unittest.main()
