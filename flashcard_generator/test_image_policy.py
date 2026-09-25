import unittest

from image_policy import approved_image_url, has_unapproved_images, stock_image_choices


class ImagePolicyTests(unittest.TestCase):
    def test_only_gallery_images_can_be_saved(self):
        approved = stock_image_choices("/flashcards")[0]["url"]
        self.assertEqual(approved_image_url(approved), approved)
        self.assertFalse(has_unapproved_images([{"image_front": approved, "image_back": ""}]))
        for value in ("data:image/png;base64,abc", "https://example.com/picture.png", "/flashcards/static/stock/unknown.svg"):
            with self.subTest(value=value):
                self.assertEqual(approved_image_url(value), "")
                self.assertTrue(has_unapproved_images([{"image_front": value}]))

    def test_malformed_card_data_is_rejected(self):
        self.assertTrue(has_unapproved_images(None))
        self.assertTrue(has_unapproved_images(["not a card"]))


if __name__ == "__main__":
    unittest.main()
