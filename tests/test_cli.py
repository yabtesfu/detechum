import tempfile
import unittest
from pathlib import Path

import numpy as np

from detechum.calibration import fit_calibrator
from detechum.cli import AI_EDITED_NOTE, CAVEAT, SENTENCE_CAVEAT, _load_scorer, analyse, render_text
from detechum.models import GPTTRACE
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


class ModelVerificationTest(unittest.TestCase):
    def test_verified_model_is_recorded_in_the_result_and_named_in_the_report(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration(), model=GPTTRACE.record())
        self.assertEqual(result["model"]["weights_sha256"], GPTTRACE.weights.sha256)
        self.assertIn(f"{GPTTRACE.repo} at revision {GPTTRACE.revision[:12]}, files verified by SHA 256",
                      render_text(result))

    def test_report_makes_no_verification_claim_without_a_model_record(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration())
        self.assertIsNone(result["model"])
        self.assertNotIn("verified", render_text(result))

    def test_no_scorer_is_loaded_from_a_folder_that_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / GPTTRACE.folder
            folder.mkdir()
            # Would raise NameError if the loader executed it.
            (folder / "normalize.py").write_text("executed_before_verification\n")
            with self.assertRaises(SystemExit) as raised:
                _load_scorer(Path(tmp), None)
        self.assertIn("No score was produced", str(raised.exception))


class MarkerScorer(FakeScorer):
    """Adds 3.0 to the base score for every occurrence of the word FLAG."""

    def score(self, texts):
        return [self._score + 3.0 * t.count("FLAG") for t in texts]


MARKED_TEXT = "Plain opening sentence. This one carries a FLAG inside. " + "Plain filler sentence. " * 60


class SentenceEffectsTest(unittest.TestCase):
    def test_sentence_that_raises_the_score_is_listed_with_the_score_without_it(self):
        result = analyse(MARKED_TEXT, MarkerScorer(-2.0), calibration())
        sentences = result["sentences"]
        self.assertEqual(sentences["count"], 62)
        self.assertEqual(sentences["analysed"], 60)
        self.assertEqual([s["index"] for s in sentences["strongest"]], [2])
        self.assertEqual(sentences["strongest"][0]["contribution"], 3.0)
        self.assertEqual(sentences["strongest"][0]["score_without"], -2.0)
        self.assertLess(sentences["strongest"][0]["p_ai_without"], result["p_ai"])

    def test_no_sentence_qualifies_when_none_moves_the_score_enough(self):
        result = analyse(MARKED_TEXT, FakeScorer(8.0), calibration())
        self.assertEqual(result["sentences"]["strongest"], [])
        self.assertIn("rests on the text as a whole", render_text(result))

    def test_single_sentence_text_reports_that_effects_cannot_be_measured(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration())
        self.assertEqual(result["sentences"]["analysed"], 0)
        self.assertIn("fewer than two sentences", render_text(result))

    def test_explain_can_be_switched_off(self):
        result = analyse(MARKED_TEXT, MarkerScorer(-2.0), calibration(), explain=False)
        self.assertIsNone(result["sentences"])
        self.assertNotIn("Sentences that raise the score", render_text(result))

    def test_report_lists_the_sentence_and_the_analysis_limit(self):
        text = render_text(analyse(MARKED_TEXT, MarkerScorer(-2.0), calibration()))
        self.assertIn('S2   +3.00  "This one carries a FLAG inside."', text)
        self.assertIn("Only the first 60 of 62 sentences were analysed.", text)
        self.assertIn(SENTENCE_CAVEAT, text)

    def test_without_calibration_the_probability_without_the_sentence_is_omitted(self):
        result = analyse(MARKED_TEXT, MarkerScorer(-2.0), None)
        self.assertIsNone(result["sentences"]["strongest"][0]["p_ai_without"])
        self.assertIn("Without it: raw score -2.00\n", render_text(result))


if __name__ == "__main__":
    unittest.main()
