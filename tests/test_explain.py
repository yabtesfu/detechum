import unittest

from detechum.explain import MAX_SENTENCES, sentence_contributions, split_sentences


def sentences(text):
    return [text[a:b] for a, b in split_sentences(text)]


class SplitSentencesTest(unittest.TestCase):
    def test_splits_on_terminal_punctuation(self):
        self.assertEqual(sentences("It rained. We stayed in! Did you? Yes."),
                         ["It rained.", "We stayed in!", "Did you?", "Yes."])

    def test_spans_index_the_original_text(self):
        text = "  First one.   Second one.  "
        self.assertEqual([text[a:b] for a, b in split_sentences(text)], ["First one.", "Second one."])

    def test_abbreviations_and_initials_do_not_split(self):
        self.assertEqual(sentences("Dr. Abebe met J. Smith at 3 p.m. on Monday. They talked."),
                         ["Dr. Abebe met J. Smith at 3 p.m. on Monday.", "They talked."])

    def test_decimal_numbers_do_not_split(self):
        self.assertEqual(sentences("The rate was 6.6 percent. It fell later."),
                         ["The rate was 6.6 percent.", "It fell later."])

    def test_lowercase_continuation_does_not_split(self):
        self.assertEqual(sentences("He said e.g. apples and pears. Then he left."),
                         ["He said e.g. apples and pears.", "Then he left."])

    def test_closing_quote_stays_with_its_sentence(self):
        self.assertEqual(sentences('She said "Stop." Then she left.'), ['She said "Stop."', "Then she left."])

    def test_blank_line_separates_unpunctuated_lines(self):
        self.assertEqual(sentences("A heading\n\nThe body starts here. It continues."),
                         ["A heading", "The body starts here.", "It continues."])

    def test_text_without_terminal_punctuation_is_one_sentence(self):
        self.assertEqual(sentences("no punctuation at all"), ["no punctuation at all"])

    def test_empty_text_has_no_sentences(self):
        self.assertEqual(split_sentences("  \n "), [])


class MarkerScorer:
    """Scores a text by how many times it contains the word FLAG."""

    def __init__(self):
        self.calls = []

    def score(self, texts):
        self.calls.append(list(texts))
        return [float(t.count("FLAG")) * 2.0 for t in texts]


class SentenceContributionsTest(unittest.TestCase):
    TEXT = "Plain opening. This one has a FLAG in it. Plain ending."

    def test_contribution_is_the_drop_when_the_sentence_is_removed(self):
        scorer = MarkerScorer()
        result = sentence_contributions(self.TEXT, scorer, full_score=2.0)
        self.assertEqual([c.contribution for c in result], [0.0, 2.0, 0.0])
        self.assertEqual(result[1].index, 2)
        self.assertEqual(result[1].text, "This one has a FLAG in it.")
        self.assertEqual(result[1].score_without, 0.0)

    def test_scorer_is_called_once_with_one_variant_per_sentence(self):
        scorer = MarkerScorer()
        sentence_contributions(self.TEXT, scorer, full_score=2.0)
        self.assertEqual(scorer.calls, [["This one has a FLAG in it. Plain ending.",
                                         "Plain opening. Plain ending.",
                                         "Plain opening. This one has a FLAG in it."]])

    def test_single_sentence_text_is_not_analysed(self):
        scorer = MarkerScorer()
        self.assertEqual(sentence_contributions("Only one FLAG sentence.", scorer, full_score=2.0), [])
        self.assertEqual(scorer.calls, [])

    def test_only_the_first_sentences_are_analysed(self):
        text = " ".join(f"Sentence number {i}." for i in range(MAX_SENTENCES + 5))
        self.assertEqual(len(sentence_contributions(text, MarkerScorer(), full_score=0.0)), MAX_SENTENCES)


if __name__ == "__main__":
    unittest.main()
