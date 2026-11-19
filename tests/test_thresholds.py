import json
import unittest
from pathlib import Path

from detechum import calibration, verdict

ROOT = Path(__file__).resolve().parents[1]


def load_thresholds() -> dict:
    values = {}
    for line in (ROOT / "eval" / "config" / "thresholds.yaml").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition(":")
            values[key.strip()] = json.loads(value)
    return values


class FrozenThresholdsTest(unittest.TestCase):
    def setUp(self):
        self.frozen = load_thresholds()

    def test_verdict_constants_in_the_code_match_the_frozen_file(self):
        self.assertEqual(verdict.MIN_WORDS_FOR_VERDICT, self.frozen["min_words_for_verdict"])
        self.assertEqual(calibration.INTERVAL_LEVEL, self.frozen["probability_interval_level"])
        self.assertEqual(calibration.N_BOOTSTRAP, self.frozen["bootstrap_resamples"])
        self.assertEqual(calibration.MIN_TAU, self.frozen["min_tau"])

    def test_pilot_calibration_file_was_built_with_the_frozen_values(self):
        pilot = json.loads((ROOT / "results" / "calibration_pilot_v2" / "calibration.json").read_text())
        self.assertEqual(pilot["target_fpr"], self.frozen["m1_target_fpr"])
        self.assertEqual(pilot["conformal"]["alpha_human"], self.frozen["conformal_alpha_human"])
        self.assertEqual(pilot["conformal"]["alpha_ai"], self.frozen["conformal_alpha_ai"])
        self.assertEqual(pilot["conformal"]["edges"], self.frozen["conformal_band_edges_words"])

    def test_conformal_bands_start_at_the_minimum_length_and_follow_the_reporting_strata(self):
        bands, strata = self.frozen["conformal_band_edges_words"], self.frozen["length_strata_edges_words"]
        self.assertEqual(bands[0], self.frozen["min_words_for_verdict"])
        self.assertEqual(bands, [edge for edge in strata if edge >= bands[0]])

    def test_a_human_stratum_that_supports_the_claim_can_also_rule_out_a_human_writer(self):
        self.assertEqual(self.frozen["conformal_alpha_human"], self.frozen["m1_target_fpr"])
        self.assertGreaterEqual(self.frozen["m1_min_human_texts_for_claim"] + 1,
                                1 / self.frozen["conformal_alpha_human"])


if __name__ == "__main__":
    unittest.main()
