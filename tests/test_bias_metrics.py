import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
_spec = importlib.util.spec_from_file_location("bias_experiment", ROOT / "eval" / "bias_experiment.py")
bias = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bias)


class ClopperPearsonTest(unittest.TestCase):
    def test_zero_successes_upper_bound_matches_rule_of_three_order(self):
        lo, hi = bias.clopper_pearson(0, 300)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.0122, places=3)  # exact bound; the rule of three gives 0.01

    def test_all_successes(self):
        lo, hi = bias.clopper_pearson(10, 10)
        self.assertEqual(hi, 1.0)
        self.assertAlmostEqual(lo, 0.6915, places=3)

    def test_interval_contains_point_estimate(self):
        lo, hi = bias.clopper_pearson(7, 91)
        self.assertLess(lo, 7 / 91)
        self.assertGreater(hi, 7 / 91)


class NativeThresholdTest(unittest.TestCase):
    def test_flags_at_most_target_fraction(self):
        scores = [float(i) for i in range(200)]
        t = bias.native_threshold(scores)
        flagged = sum(s > t for s in scores)
        self.assertLessEqual(flagged / len(scores), bias.TARGET_FPR)

    def test_flag_stats_counts_strictly_above(self):
        stats = bias.flag_stats([0.0, 1.0, 2.0, 3.0], threshold=2.0)
        self.assertEqual(stats["flagged"], 1)
        self.assertEqual(stats["n"], 4)


if __name__ == "__main__":
    unittest.main()
