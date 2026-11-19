import itertools
import unittest

from detechum.conformal import ConformalResult
from detechum.verdict import MIN_WORDS_FOR_VERDICT, ScoredDocument, Verdict, decide_verdict

TAU = 0.70
OK_LEN = MIN_WORDS_FOR_VERDICT + 50


def doc(p_low, p_ai, p_high, n_words=OK_LEN, calibrated=True):
    return ScoredDocument(p_ai=p_ai, p_low=p_low, p_high=p_high,
                          n_words=n_words, stratum_calibrated=calibrated)


class DecideVerdictTest(unittest.TestCase):
    def test_whole_interval_above_tau_is_ai(self):
        self.assertIs(decide_verdict(doc(0.75, 0.85, 0.92), TAU), Verdict.LIKELY_AI)

    def test_whole_interval_below_tau_is_human(self):
        self.assertIs(decide_verdict(doc(0.05, 0.20, 0.40), TAU), Verdict.LIKELY_HUMAN)

    def test_straddling_interval_is_cant_tell_even_if_point_estimate_is_over(self):
        # Point estimate equals tau, but the interval extends below it.
        self.assertIs(decide_verdict(doc(0.62, 0.70, 0.81), TAU), Verdict.CANT_TELL)

    def test_lower_bound_exactly_at_tau_counts_as_ai(self):
        self.assertIs(decide_verdict(doc(0.70, 0.80, 0.90), TAU), Verdict.LIKELY_AI)

    def test_upper_bound_exactly_at_tau_is_not_human(self):
        self.assertIs(decide_verdict(doc(0.40, 0.55, 0.70), TAU), Verdict.CANT_TELL)

    def test_short_text_gets_no_verdict_even_when_confident(self):
        self.assertIs(decide_verdict(doc(0.95, 0.98, 0.99, n_words=40), TAU), Verdict.NO_VERDICT)

    def test_uncalibrated_stratum_gets_no_verdict(self):
        self.assertIs(decide_verdict(doc(0.95, 0.98, 0.99, calibrated=False), TAU), Verdict.NO_VERDICT)

    def test_inconsistent_interval_raises(self):
        with self.assertRaises(ValueError):
            decide_verdict(doc(0.80, 0.70, 0.90), TAU)

    def test_bad_tau_raises(self):
        with self.assertRaises(ValueError):
            decide_verdict(doc(0.1, 0.2, 0.3), 1.0)


def conformal(human_in_set: bool, ai_in_set: bool, n_human: int = 199, n_ai: int = 199) -> ConformalResult:
    return ConformalResult(min_words=150, max_words=None, n_human=n_human, n_ai=n_ai,
                           human_at_or_above=min(n_human, 50) if human_in_set else 0,
                           ai_at_or_below=min(n_ai, 50) if ai_in_set else 0, alpha_human=0.01, alpha_ai=0.05)


AI_INTERVAL, HUMAN_INTERVAL, STRADDLING = doc(0.75, 0.85, 0.92), doc(0.05, 0.20, 0.40), doc(0.62, 0.70, 0.81)


class ConformalVerdictTest(unittest.TestCase):
    def test_ai_label_needs_ai_alone_in_the_set(self):
        self.assertIs(decide_verdict(AI_INTERVAL, TAU, conformal(False, True)), Verdict.LIKELY_AI)
        self.assertIs(decide_verdict(AI_INTERVAL, TAU, conformal(True, True)), Verdict.CANT_TELL)
        self.assertIs(decide_verdict(AI_INTERVAL, TAU, conformal(False, False)), Verdict.CANT_TELL)

    def test_human_label_needs_human_alone_in_the_set(self):
        self.assertIs(decide_verdict(HUMAN_INTERVAL, TAU, conformal(True, False)), Verdict.LIKELY_HUMAN)
        self.assertIs(decide_verdict(HUMAN_INTERVAL, TAU, conformal(True, True)), Verdict.CANT_TELL)
        self.assertIs(decide_verdict(HUMAN_INTERVAL, TAU, conformal(False, False)), Verdict.CANT_TELL)

    def test_band_too_thin_to_rule_out_either_class_gets_no_verdict(self):
        thin = conformal(True, True, n_human=98, n_ai=18)
        self.assertIs(decide_verdict(AI_INTERVAL, TAU, thin), Verdict.NO_VERDICT)

    def test_band_with_enough_texts_of_one_class_can_still_give_that_label(self):
        no_ai_texts = conformal(False, True, n_human=99, n_ai=0)
        self.assertIs(decide_verdict(AI_INTERVAL, TAU, no_ai_texts), Verdict.LIKELY_AI)

    def test_conformal_layer_never_creates_or_changes_a_label(self):
        for document, human_in, ai_in in itertools.product(
                (AI_INTERVAL, HUMAN_INTERVAL, STRADDLING), (True, False), (True, False)):
            without = decide_verdict(document, TAU)
            self.assertIn(decide_verdict(document, TAU, conformal(human_in, ai_in)), {without, Verdict.CANT_TELL})


if __name__ == "__main__":
    unittest.main()
