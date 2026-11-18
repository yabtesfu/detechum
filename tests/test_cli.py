import unittest

import numpy as np

from detechum.calibration import fit_calibrator
from detechum.cli import AI_EDITED_NOTE, CAVEAT, analyse, render_text
from detechum.verdict import Verdict


class FakeScorer:
    name = "fake_scorer"

    def __init__(self, score: float, truncated: bool = False):
        self._score, self._truncated, self.seen = score, truncated, []

    def score(self, texts):
        self.seen += texts
        return [self._score] * len(texts)

    def is_truncated(self, text):
        return self._truncated


def calibration(tau=0.5, scorer="fake_scorer"):
    rng = np.random.default_rng(0)
    scores = np.concatenate([rng.normal(-1, 1, 200), rng.normal(1, 1, 200)])
    labels = np.concatenate([np.zeros(200, int), np.ones(200, int)])
    cal = fit_calibrator(scores, labels, seed=0, n_bootstrap=100)
    return {"name": "test_calibration", "scorer": scorer, "tau": tau, "description": "synthetic",
            "calibrator": cal.to_dict()}


LONG_TEXT = "word " * 200
SHORT_TEXT = "word " * 20


class AnalyseTest(unittest.TestCase):
    def test_high_score_on_long_text_is_likely_ai_with_the_editing_note(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration())
        self.assertEqual(result["verdict"], Verdict.LIKELY_AI.value)
        self.assertIn(AI_EDITED_NOTE, result["reasons"])
        self.assertGreater(result["p_ai"], 0.9)
        self.assertLessEqual(result["interval"][0], result["p_ai"])

    def test_low_score_on_long_text_is_likely_human(self):
        result = analyse(LONG_TEXT, FakeScorer(-8.0), calibration())
        self.assertEqual(result["verdict"], Verdict.LIKELY_HUMAN.value)
        self.assertNotIn(AI_EDITED_NOTE, result["reasons"])

    def test_borderline_score_cannot_be_told(self):
        result = analyse(LONG_TEXT, FakeScorer(0.0), calibration())
        self.assertEqual(result["verdict"], Verdict.CANT_TELL.value)

    def test_short_text_gets_probability_but_no_verdict(self):
        result = analyse(SHORT_TEXT, FakeScorer(8.0), calibration())
        self.assertEqual(result["verdict"], Verdict.NO_VERDICT.value)
        self.assertIsNotNone(result["p_ai"])
        self.assertIn("20 words", result["reasons"][0])

    def test_without_calibration_only_the_raw_score_is_reported(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), None)
        self.assertEqual(result["verdict"], Verdict.NO_VERDICT.value)
        self.assertIsNone(result["p_ai"])
        self.assertEqual(result["raw_score"], 8.0)

    def test_calibration_without_threshold_gives_no_verdict(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration(tau=None))
        self.assertEqual(result["verdict"], Verdict.NO_VERDICT.value)

    def test_calibration_for_another_scorer_is_rejected(self):
        with self.assertRaises(ValueError):
            analyse(LONG_TEXT, FakeScorer(8.0), calibration(scorer="other_scorer"))

    def test_empty_text_is_rejected(self):
        with self.assertRaises(ValueError):
            analyse("  \n ", FakeScorer(8.0), None)

    def test_scorer_receives_normalized_text_and_removals_are_reported(self):
        scorer = FakeScorer(-8.0)
        result = analyse("hel\u200blo " + LONG_TEXT, scorer, calibration())
        self.assertNotIn("\u200b", scorer.seen[0])
        self.assertTrue(result["evasion_suspected"])
        self.assertEqual(len(result["normalization"]), 1)

    def test_truncation_is_reported(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0, truncated=True), calibration())
        self.assertIn("only its beginning was scored", result["reasons"][0])


class RenderTextTest(unittest.TestCase):
    def test_report_shows_interval_verdict_and_caveat(self):
        text = render_text(analyse(LONG_TEXT, FakeScorer(8.0), calibration()))
        self.assertIn("90% interval", text)
        self.assertIn(Verdict.LIKELY_AI.value, text)
        self.assertIn("fitted on 200 human and 200 AI texts", text)
        self.assertTrue(text.endswith(CAVEAT))

    def test_report_without_calibration_says_probability_is_not_available(self):
        text = render_text(analyse(LONG_TEXT, FakeScorer(8.0), None))
        self.assertIn("not available", text)


if __name__ == "__main__":
    unittest.main()
