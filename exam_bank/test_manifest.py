import unittest

from manifest import ITEMS, PAPER, TOPICS, SUBTOPICS
from manifest_j27702 import ITEMS as PAPER_2_ITEMS, PAPER as PAPER_2, TOPICS as PAPER_2_TOPICS, SUBTOPICS as PAPER_2_SUBTOPICS
from manifest_2024_j27701 import ITEMS as P1_2024_ITEMS, PAPER as P1_2024, SUBTOPICS as P1_2024_SUBTOPICS
from manifest_2024_j27702 import ITEMS as P2_2024_ITEMS, PAPER as P2_2024, SUBTOPICS as P2_2024_SUBTOPICS


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

    def test_2024_papers_have_complete_question_maps(self):
        for paper, items, subtopics, max_paper_page, max_scheme_page in (
            (P1_2024, P1_2024_ITEMS, P1_2024_SUBTOPICS, 16, 22),
            (P2_2024, P2_2024_ITEMS, P2_2024_SUBTOPICS, 20, 27),
        ):
            with self.subTest(paper=paper["paper_id"]):
                labels = {item[0] for item in items}
                self.assertEqual(sum(item[1] for item in items), 80)
                self.assertEqual(set(subtopics), labels)
                for label, marks, pages, scheme_pages, topic_codes, _ in items:
                    self.assertGreater(marks, 0)
                    self.assertTrue(all(1 <= page <= max_paper_page for page in pages))
                    self.assertTrue(all(1 <= page <= max_scheme_page for page in scheme_pages))
                    self.assertTrue(topic_codes)

    def test_2025_subtopic_maps_cover_every_question(self):
        self.assertEqual(set(SUBTOPICS), {item[0] for item in ITEMS})
        self.assertEqual(set(PAPER_2_SUBTOPICS), {item[0] for item in PAPER_2_ITEMS})


if __name__ == "__main__":
    unittest.main()
