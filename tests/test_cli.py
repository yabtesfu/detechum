import tempfile
import unittest
from pathlib import Path

import numpy as np

from detechum.calibration import fit_calibrator
from detechum.conformal import fit_conformal
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


def calibration(tau=0.5, scorer="fake_scorer", conformal=None):
    """`conformal` is (human texts, AI texts, first band edge) for the conformal layer, or None for no layer."""
    rng = np.random.default_rng(0)
    scores = np.concatenate([rng.normal(-1, 1, 200), rng.normal(1, 1, 200)])
    labels = np.concatenate([np.zeros(200, int), np.ones(200, int)])
    cal = fit_calibrator(scores, labels, seed=0, n_bootstrap=100)
    out = {"name": "test_calibration", "scorer": scorer, "tau": tau, "description": "synthetic",
           "calibrator": cal.to_dict()}
    if conformal:
        n_human, n_ai, edge = conformal
        keep = np.concatenate([np.arange(n_human), 200 + np.arange(n_ai)])
        out["conformal"] = fit_conformal(scores[keep], labels[keep], np.full(len(keep), 200), edges=(edge,),
                                         alpha_human=0.01, alpha_ai=0.05).to_dict()
    return out


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


class ConformalLayerTest(unittest.TestCase):
    def test_label_is_kept_when_the_band_rules_out_the_other_class(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration(conformal=(200, 200, 150)))
        self.assertEqual(result["verdict"], Verdict.LIKELY_AI.value)
        self.assertIn("Among calibration texts of 150 or more words, 0 of 200 human texts score this high or "
                      "higher and 200 of 200 AI texts score this low or lower.", result["reasons"])
        self.assertEqual(result["reasons"][-1], AI_EDITED_NOTE)
        self.assertFalse(result["conformal"]["human_in_set"])

        result = analyse(LONG_TEXT, FakeScorer(-8.0), calibration(conformal=(200, 200, 150)))
        self.assertEqual(result["verdict"], Verdict.LIKELY_HUMAN.value)

    def test_too_few_human_texts_in_the_band_withhold_the_ai_label(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration(conformal=(98, 200, 150)))
        self.assertEqual(result["verdict"], Verdict.CANT_TELL.value)
        self.assertIn("At least 99 human calibration texts of this length are needed", result["reasons"][-1])
        self.assertNotIn(AI_EDITED_NOTE, result["reasons"])

    def test_human_texts_scoring_as_high_withhold_the_ai_label(self):
        cal = calibration()
        cal["conformal"] = {"edges": [150], "alpha_human": 0.01, "alpha_ai": 0.05,
                            "human_scores": [[0.0] * 99 + [20.0] * 5], "ai_scores": [[1.0] * 50]}
        result = analyse(LONG_TEXT, FakeScorer(8.0), cal)
        self.assertEqual(result["verdict"], Verdict.CANT_TELL.value)
        self.assertIn("5 of 104 human texts score this high or higher", result["reasons"][-2])
        self.assertIn("does not rule out a human writer at the 1% error target", result["reasons"][-1])

    def test_too_few_ai_texts_in_the_band_withhold_the_human_label(self):
        result = analyse(LONG_TEXT, FakeScorer(-8.0), calibration(conformal=(200, 18, 150)))
        self.assertEqual(result["verdict"], Verdict.CANT_TELL.value)
        self.assertIn("At least 19 AI calibration texts of this length are needed", result["reasons"][-1])

    def test_band_too_thin_for_any_label_gives_no_verdict(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration(conformal=(98, 18, 150)))
        self.assertEqual(result["verdict"], Verdict.NO_VERDICT.value)
        self.assertIn("needs at least 99 human or 19 AI calibration texts", result["reasons"][-1])

    def test_score_between_the_classes_is_reported_as_resembling_neither(self):
        cal = calibration()
        cal["conformal"] = {"edges": [150], "alpha_human": 0.01, "alpha_ai": 0.05,
                            "human_scores": [[0.0] * 99], "ai_scores": [[10.0] * 19]}
        result = analyse(LONG_TEXT, FakeScorer(5.0), cal)
        self.assertEqual(result["verdict"], Verdict.CANT_TELL.value)
        self.assertIn("It resembles neither group", result["reasons"][-1])

    def test_length_outside_every_band_gives_no_verdict(self):
        result = analyse(LONG_TEXT, FakeScorer(8.0), calibration(conformal=(200, 200, 300)))
        self.assertEqual(result["verdict"], Verdict.NO_VERDICT.value)
        self.assertIn("no length band for a text of 200 words", result["reasons"][-1])

    def test_calibration_without_the_layer_reports_no_conformal_result(self):
        self.assertIsNone(analyse(LONG_TEXT, FakeScorer(8.0), calibration())["conformal"])


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
