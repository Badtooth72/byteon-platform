import unittest

from manifest import ITEMS, PAPER, TOPICS
from manifest_j27702 import ITEMS as PAPER_2_ITEMS, PAPER as PAPER_2, TOPICS as PAPER_2_TOPICS


class PaperManifestTests(unittest.TestCase):
    def test_every_mark_is_accounted_for_once(self):
        self.assertEqual(len(ITEMS), 27)
        self.assertEqual(sum(item[1] for item in ITEMS), PAPER["total_marks"])
        self.assertEqual(len({item[0] for item in ITEMS}), len(ITEMS))

    def test_references_and_topic_codes_are_valid(self):
        codes = {topic["code"] for topic in TOPICS}
        for label, marks, pages, scheme_pages, topics, _ in ITEMS:
            with self.subTest(label=label):
                self.assertGreater(marks, 0)
                self.assertTrue(all(1 <= page <= 16 for page in pages))
                self.assertTrue(all(1 <= page <= 19 for page in scheme_pages))
                self.assertTrue(topics)
                self.assertFalse(set(topics) - codes)

    def test_paper_two_question_map(self):
        self.assertEqual(len(PAPER_2_ITEMS), 29)
        self.assertEqual(sum(item[1] for item in PAPER_2_ITEMS), PAPER_2["total_marks"])
        self.assertEqual(len({item[0] for item in PAPER_2_ITEMS}), len(PAPER_2_ITEMS))
        codes = {topic["code"] for topic in PAPER_2_TOPICS}
        for label, marks, pages, scheme_pages, topics, _ in PAPER_2_ITEMS:
            with self.subTest(label=label):
                self.assertGreater(marks, 0)
                self.assertTrue(all(1 <= page <= 20 for page in pages))
                self.assertTrue(all(1 <= page <= 31 for page in scheme_pages))
                self.assertFalse(set(topics) - codes)
                self.assertTrue(all(code.startswith("2.") for code in topics))


if __name__ == "__main__":
    unittest.main()
