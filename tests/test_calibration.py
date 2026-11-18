import json
import unittest

import numpy as np

from detechum.calibration import (Calibrator, brier_score, choose_tau, expected_calibration_error,
                                  fit_calibrator, reliability_bins)
from detechum.verdict import Verdict, decide_verdict


def overlapping_sample(n_per_class=300, seed=0):
    rng = np.random.default_rng(seed)
    scores = np.concatenate([rng.normal(-1.0, 1.0, n_per_class), rng.normal(1.0, 1.0, n_per_class)])
    labels = np.concatenate([np.zeros(n_per_class, int), np.ones(n_per_class, int)])
    return scores, labels


class FitCalibratorTest(unittest.TestCase):
    def setUp(self):
        self.scores, self.labels = overlapping_sample()
        self.cal = fit_calibrator(self.scores, self.labels, seed=1, n_bootstrap=200)

    def test_map_and_bounds_are_monotone_and_ordered(self):
        for curve in (self.cal.p_ai, self.cal.p_low, self.cal.p_high):
            self.assertTrue(np.all(np.diff(curve) >= 0))
            self.assertTrue(np.all((curve >= 0) & (curve <= 1)))
        self.assertTrue(np.all(self.cal.p_low <= self.cal.p_ai))
        self.assertTrue(np.all(self.cal.p_ai <= self.cal.p_high))

    def test_midpoint_of_symmetric_classes_is_near_even_odds(self):
        p, lo, hi = self.cal.predict(0.0)
        self.assertAlmostEqual(p, 0.5, delta=0.15)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_scores_outside_the_calibration_range_take_the_end_values(self):
        self.assertEqual(self.cal.predict(99.0), self.cal.predict(float(self.scores.max())))
        self.assertEqual(self.cal.predict(-99.0), self.cal.predict(float(self.scores.min())))

    def test_same_seed_gives_identical_calibrator(self):
        again = fit_calibrator(self.scores, self.labels, seed=1, n_bootstrap=200)
        np.testing.assert_array_equal(self.cal.p_low, again.p_low)
        np.testing.assert_array_equal(self.cal.p_high, again.p_high)

    def test_json_round_trip_preserves_predictions(self):
        restored = Calibrator.from_dict(json.loads(json.dumps(self.cal.to_dict())))
        self.assertEqual(restored.predict(0.3), self.cal.predict(0.3))
        self.assertEqual((restored.n_human, restored.n_ai), (300, 300))

    def test_scored_document_is_accepted_by_decide_verdict(self):
        doc = self.cal.scored_document(score=5.0, n_words=400)
        self.assertEqual(decide_verdict(doc, tau=0.5), Verdict.LIKELY_AI)


class SeparatedClassesTest(unittest.TestCase):
    """Perfectly separated classes must not produce a certainty the sample size cannot support."""

    def test_pure_block_keeps_a_binomial_lower_bound(self):
        scores = np.concatenate([np.linspace(-2, -1, 20), np.linspace(1, 2, 20)])
        labels = np.concatenate([np.zeros(20, int), np.ones(20, int)])
        cal = fit_calibrator(scores, labels, seed=3, n_bootstrap=100)
        p, lo, hi = cal.predict(2.0)
        self.assertEqual(p, 1.0)
        self.assertAlmostEqual(lo, 0.05 ** (1 / 20), places=6)  # exact one sided 95% bound for 20 of 20
        p, lo, hi = cal.predict(-2.0)
        self.assertEqual(p, 0.0)
        self.assertAlmostEqual(hi, 1 - 0.05 ** (1 / 20), places=6)


class FitCalibratorInputTest(unittest.TestCase):
    def test_single_class_raises(self):
        with self.assertRaises(ValueError):
            fit_calibrator([0.1, 0.2, 0.3], [1, 1, 1], seed=0)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            fit_calibrator([0.1, 0.2], [0, 1, 1], seed=0)

    def test_non_binary_labels_raise(self):
        with self.assertRaises(ValueError):
            fit_calibrator([0.1, 0.2, 0.3], [0, 1, 2], seed=0)

    def test_non_finite_scores_raise(self):
        with self.assertRaises(ValueError):
            fit_calibrator([0.1, float("nan"), 0.3], [0, 1, 1], seed=0)


class ChooseTauTest(unittest.TestCase):
    def setUp(self):
        self.scores, self.labels = overlapping_sample()
        self.cal = fit_calibrator(self.scores, self.labels, seed=1, n_bootstrap=200)
        self.humans = self.scores[self.labels == 0]

    def flagged(self, tau):
        return sum(self.cal.predict(float(s))[1] >= tau for s in self.humans)

    def test_flags_at_most_the_target_share_of_humans(self):
        tau = choose_tau(self.cal, self.humans, target_fpr=0.01)
        self.assertLessEqual(self.flagged(tau), 3)  # 1% of 300

    def test_never_below_even_odds(self):
        tau = choose_tau(self.cal, self.humans, target_fpr=0.5)
        self.assertGreaterEqual(tau, 0.5)

    def test_returns_none_when_no_threshold_meets_the_target(self):
        certain = Calibrator(knots=np.array([0.0, 1.0]), p_ai=np.ones(2), p_low=np.ones(2), p_high=np.ones(2),
                             n_human=1, n_ai=1)
        self.assertIsNone(choose_tau(certain, [0.2, 0.4, 0.6], target_fpr=0.01))

    def test_invalid_target_raises(self):
        with self.assertRaises(ValueError):
            choose_tau(self.cal, self.humans, target_fpr=0.0)


class ReliabilityTest(unittest.TestCase):
    def test_perfectly_calibrated_predictions_have_zero_error(self):
        p = np.array([0.0] * 10 + [1.0] * 10)
        labels = np.array([0] * 10 + [1] * 10)
        self.assertEqual(expected_calibration_error(p, labels, n_bins=2), 0.0)
        self.assertEqual(brier_score(p, labels), 0.0)

    def test_constant_half_on_balanced_labels(self):
        p, labels = np.full(20, 0.5), np.array([0, 1] * 10)
        self.assertAlmostEqual(expected_calibration_error(p, labels, n_bins=1), 0.0)
        self.assertAlmostEqual(brier_score(p, labels), 0.25)

    def test_overconfident_predictions_are_penalised(self):
        p, labels = np.ones(10), np.array([1] * 6 + [0] * 4)
        self.assertAlmostEqual(expected_calibration_error(p, labels, n_bins=1), 0.4)

    def test_bins_cover_every_text_once(self):
        scores, labels = overlapping_sample(50)
        bins = reliability_bins(1 / (1 + np.exp(-scores)), labels, n_bins=15)
        self.assertEqual(len(bins), 15)
        self.assertEqual(sum(b["n"] for b in bins), 100)

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            reliability_bins([], [])


if __name__ == "__main__":
    unittest.main()
