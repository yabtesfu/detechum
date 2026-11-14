import unittest

from detechum.facts import check_facts, extract_facts


class ExtractFactsTest(unittest.TestCase):
    def test_numbers_ignore_thousands_separators(self):
        self.assertEqual(extract_facts("We scored 1,250 essays.")["numbers"], {"1250"})

    def test_number_words_map_to_digits(self):
        self.assertEqual(extract_facts("It took five weeks.")["numbers"], {"5"})

    def test_pronoun_one_is_not_a_number(self):
        self.assertEqual(extract_facts("One of the reasons is cost.")["numbers"], set())

    def test_dates_in_different_formats_are_equal(self):
        a = extract_facts("Released on 14 Nov 2026.")["dates"]
        b = extract_facts("Released on November 14, 2026.")["dates"]
        c = extract_facts("Released on 2026-11-14.")["dates"]
        self.assertEqual(a, {(2026, 11, 14)})
        self.assertEqual(a, b)
        self.assertEqual(a, c)

    def test_date_parts_are_not_double_counted_as_numbers(self):
        self.assertEqual(extract_facts("Released on 14 Nov 2026.")["numbers"], set())

    def test_sentence_initial_word_is_not_a_name(self):
        self.assertEqual(extract_facts("Second, the team at Acme shipped it.")["names"], {"Acme"})


class CheckFactsTest(unittest.TestCase):
    def test_identical_text_is_preserved(self):
        text = 'At Acme we cut latency by 40% in March 2025, said "the numbers speak".'
        result = check_facts(text, text)
        self.assertTrue(result.preserved)
        self.assertFalse(any(result.added.values()))

    def test_changed_number_is_missing_and_added(self):
        result = check_facts("Latency fell by 40%.", "Latency fell by 45%.")
        self.assertFalse(result.preserved)
        self.assertEqual(result.missing["numbers"], ["40%"])
        self.assertEqual(result.added["numbers"], ["45%"])

    def test_dropped_name_is_missing(self):
        result = check_facts("I deployed it with Docker and Kubernetes.", "I deployed it with Kubernetes.")
        self.assertEqual(result.missing["names"], ["Docker"])

    def test_name_moved_to_sentence_start_is_not_missing(self):
        result = check_facts("At Eskalate, I built services.", "Eskalate: I built services there.")
        self.assertTrue(result.preserved)

    def test_lowercased_proper_noun_is_reported(self):
        result = check_facts("I used Docker for builds.", "I used docker for builds.")
        self.assertEqual(result.missing["names"], ["Docker"])

    def test_altered_quote_is_missing(self):
        result = check_facts('She said "ship it on Friday".', 'She said "ship it Friday".')
        self.assertEqual(result.missing["quotes"], ["ship it on Friday"])

    def test_curly_and_straight_quotes_are_equivalent(self):
        result = check_facts("He wrote “done by noon”.", 'He wrote "done by noon".')
        self.assertTrue(result.preserved)

    def test_added_claim_with_new_name_is_flagged_but_does_not_fail(self):
        result = check_facts("I review Go code.", "I review Go code and run the Race Detector on CI.")
        self.assertTrue(result.preserved)
        self.assertIn("Race Detector", result.added["names"])

    def test_changed_date_is_reported(self):
        result = check_facts("Due 3 March 2026.", "Due 13 March 2026.")
        self.assertEqual(result.missing["dates"], ["(2026, 3, 3)"])


if __name__ == "__main__":
    unittest.main()
