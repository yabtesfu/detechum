import unittest

from detechum.stats import clopper_pearson, flag_stats, threshold_for_fpr


class ClopperPearsonTest(unittest.TestCase):
    def test_zero_successes_upper_bound(self):
        lo, hi = clopper_pearson(0, 300)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.0122, places=3)  # exact bound; the rule of three gives 0.01

    def test_all_successes(self):
        lo, hi = clopper_pearson(10, 10)
        self.assertEqual(hi, 1.0)
        self.assertAlmostEqual(lo, 0.6915, places=3)

    def test_interval_contains_point_estimate(self):
        lo, hi = clopper_pearson(7, 91)
        self.assertLess(lo, 7 / 91)
        self.assertGreater(hi, 7 / 91)

    def test_invalid_counts_raise(self):
        with self.assertRaises(ValueError):
            clopper_pearson(5, 3)


class ThresholdTest(unittest.TestCase):
    def test_flags_at_most_target_fraction(self):
        scores = [float(i) for i in range(200)]
        t = threshold_for_fpr(scores, 0.01)
        self.assertLessEqual(sum(s > t for s in scores) / len(scores), 0.01)

    def test_flag_stats_counts_strictly_above(self):
        stats = flag_stats([0.0, 1.0, 2.0, 3.0], threshold=2.0)
        self.assertEqual((stats["flagged"], stats["n"]), (1, 4))


if __name__ == "__main__":
    unittest.main()
