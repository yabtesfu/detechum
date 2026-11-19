import unittest

import numpy as np

from detechum.conformal import ConformalLayer, fit_conformal, min_calibration_texts


def layer(human, ai, alpha_human=0.01, alpha_ai=0.05, edges=(150,)):
    return ConformalLayer(edges=edges, human_scores=(np.sort(np.asarray(human, dtype=float)),),
                          ai_scores=(np.sort(np.asarray(ai, dtype=float)),),
                          alpha_human=alpha_human, alpha_ai=alpha_ai)


class MinCalibrationTextsTest(unittest.TestCase):
    def test_one_percent_needs_99_texts_and_five_percent_needs_19(self):
        self.assertEqual(min_calibration_texts(0.01), 99)
        self.assertEqual(min_calibration_texts(0.05), 19)

    def test_result_is_the_smallest_count_that_can_reach_alpha(self):
        for alpha in (0.001, 0.01, 0.03, 0.05, 0.07, 0.1, 0.5):
            n = min_calibration_texts(alpha)
            self.assertLessEqual(1 / (n + 1), alpha)
            self.assertGreater(1 / n, alpha)


class AssessTest(unittest.TestCase):
    def test_counts_and_p_values_on_a_small_example(self):
        result = layer(human=[1, 2, 3, 4], ai=[3, 5, 6]).assess(3.5, 200)
        self.assertEqual((result.human_at_or_above, result.n_human), (1, 4))
        self.assertEqual((result.ai_at_or_below, result.n_ai), (1, 3))
        self.assertEqual(result.p_human, 2 / 5)
        self.assertEqual(result.p_ai, 2 / 4)

    def test_tied_calibration_scores_count_as_at_least_as_extreme(self):
        result = layer(human=[1, 3, 3], ai=[3, 3, 9]).assess(3.0, 200)
        self.assertEqual(result.human_at_or_above, 2)
        self.assertEqual(result.ai_at_or_below, 2)

    def test_human_cannot_be_ruled_out_with_98_human_texts(self):
        result = layer(human=np.zeros(98), ai=np.full(50, 10.0)).assess(1000.0, 200)
        self.assertFalse(result.can_exclude_human)
        self.assertTrue(result.human_in_set)

    def test_human_is_ruled_out_above_all_of_99_human_texts(self):
        result = layer(human=np.zeros(99), ai=np.full(50, 10.0)).assess(10.0, 200)
        self.assertTrue(result.can_exclude_human)
        self.assertFalse(result.human_in_set)
        self.assertTrue(result.ai_in_set)

    def test_one_human_text_at_the_score_keeps_human_in_the_set_at_n_99(self):
        human = np.concatenate([np.zeros(98), [10.0]])
        self.assertTrue(layer(human=human, ai=np.full(50, 10.0)).assess(10.0, 200).human_in_set)

    def test_score_between_the_classes_empties_the_set(self):
        result = layer(human=np.zeros(99), ai=np.full(19, 10.0)).assess(5.0, 200)
        self.assertFalse(result.human_in_set)
        self.assertFalse(result.ai_in_set)

    def test_band_without_ai_texts_always_keeps_ai_in_the_set(self):
        result = layer(human=np.zeros(99), ai=[]).assess(-50.0, 200)
        self.assertFalse(result.can_exclude_ai)
        self.assertTrue(result.ai_in_set)

    def test_non_finite_score_is_rejected(self):
        with self.assertRaises(ValueError):
            layer(human=[0.0], ai=[1.0]).assess(float("nan"), 200)


class BandsTest(unittest.TestCase):
    def setUp(self):
        scores = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        labels = [0, 1, 0, 1, 0, 1]
        n_words = [100, 150, 249, 250, 499, 5000]
        self.layer = fit_conformal(scores, labels, n_words, edges=(150, 250), alpha_human=0.01, alpha_ai=0.05)

    def test_texts_are_sorted_into_bands_by_length_and_class(self):
        self.assertEqual([s.tolist() for s in self.layer.human_scores], [[2.0], [4.0]])
        self.assertEqual([s.tolist() for s in self.layer.ai_scores], [[1.0], [3.0, 5.0]])

    def test_band_limits_are_lower_inclusive_and_upper_exclusive(self):
        self.assertEqual(self.layer.assess(0.0, 249).max_words, 250)
        self.assertEqual(self.layer.assess(0.0, 250).min_words, 250)
        self.assertIsNone(self.layer.assess(0.0, 250).max_words)

    def test_text_shorter_than_the_first_band_has_no_result(self):
        self.assertIsNone(self.layer.assess(0.0, 149))

    def test_layer_survives_a_round_trip_through_a_dict(self):
        restored = ConformalLayer.from_dict(self.layer.to_dict())
        self.assertEqual(restored.assess(3.5, 300).to_dict(), self.layer.assess(3.5, 300).to_dict())

    def test_malformed_input_is_rejected(self):
        ok = dict(edges=(150,), alpha_human=0.01, alpha_ai=0.05)
        with self.assertRaises(ValueError):
            fit_conformal([1.0, 2.0], [0, 2], [200, 200], **ok)
        with self.assertRaises(ValueError):
            fit_conformal([1.0, 2.0], [0, 1], [200], **ok)
        with self.assertRaises(ValueError):
            fit_conformal([1.0], [0], [200], **ok | {"edges": (250, 150)})
        with self.assertRaises(ValueError):
            fit_conformal([1.0], [0], [200], **ok | {"alpha_human": 0.0})
        with self.assertRaises(ValueError):
            fit_conformal([float("inf")], [0], [200], **ok)


class CoverageTest(unittest.TestCase):
    def test_share_of_human_texts_ruled_out_stays_near_alpha_on_fresh_draws(self):
        # With 199 calibration texts and alpha 0.05 the exact rate is 10/200. 4000 trials put the
        # standard error near 0.0035, so 0.065 is more than four standard errors above it.
        rng = np.random.default_rng(7)
        ruled_out = 0
        for _ in range(4000):
            draws = rng.normal(size=200)
            ruled_out += not layer(human=draws[:199], ai=[], alpha_human=0.05).assess(draws[199], 200).human_in_set
        self.assertLess(ruled_out / 4000, 0.065)
        self.assertGreater(ruled_out / 4000, 0.035)


if __name__ == "__main__":
    unittest.main()
