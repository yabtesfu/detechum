import unittest

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
        # The example from the design discussion: best guess 0.70, range 0.62 to 0.81.
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


if __name__ == "__main__":
    unittest.main()
