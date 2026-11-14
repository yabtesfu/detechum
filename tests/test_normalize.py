import unittest

from detechum.normalize import normalize


class NormalizeTest(unittest.TestCase):
    def test_clean_text_is_unchanged_and_report_is_empty(self):
        text = "Regular exercise improves sleep quality."
        cleaned, report = normalize(text)
        self.assertEqual(cleaned, text)
        self.assertFalse(report.evasion_suspected)
        self.assertEqual(report.summary(), [])

    def test_zero_width_space_is_removed_and_reported(self):
        cleaned, report = normalize("exer\u200bcise")
        self.assertEqual(cleaned, "exercise")
        self.assertEqual(report.invisible["ZERO WIDTH SPACE"], 1)
        self.assertTrue(report.evasion_suspected)

    def test_cyrillic_lookalike_inside_latin_word_is_mapped(self):
        cleaned, report = normalize("the \u0441at sat")  # Cyrillic es in "cat"
        self.assertEqual(cleaned, "the cat sat")
        self.assertEqual(sum(report.lookalikes.values()), 1)

    def test_pure_russian_word_is_untouched(self):
        text = "Привет, мир. Hello world."
        cleaned, report = normalize(text)
        self.assertEqual(cleaned, text)
        self.assertFalse(report.evasion_suspected)

    def test_greek_word_is_untouched(self):
        text = "The word καλός means good."
        self.assertEqual(normalize(text)[0], text)

    def test_emoji_zwj_sequence_is_preserved(self):
        family = "\U0001F468\u200d\U0001F469\u200d\U0001F467"
        cleaned, report = normalize(f"Our family {family} at home.")
        self.assertIn(family, cleaned)
        self.assertFalse(report.evasion_suspected)

    def test_persian_zwnj_is_preserved(self):
        text = "می\u200cخواهم"  # Persian "I want"
        cleaned, report = normalize(text)
        self.assertEqual(cleaned, text)
        self.assertFalse(report.evasion_suspected)

    def test_zwnj_between_latin_letters_is_removed(self):
        cleaned, report = normalize("hu\u200cman")
        self.assertEqual(cleaned, "human")
        self.assertTrue(report.evasion_suspected)

    def test_emoji_variation_selector_is_preserved(self):
        text = "Done ❤\ufe0f"
        self.assertEqual(normalize(text)[0], text)

    def test_nbsp_is_typography_not_evasion(self):
        cleaned, report = normalize("10\u00a0km")
        self.assertEqual(cleaned, "10 km")
        self.assertFalse(report.evasion_suspected)
        self.assertEqual(report.summary(), ["1 typographic spaces replaced with normal spaces"])


if __name__ == "__main__":
    unittest.main()
