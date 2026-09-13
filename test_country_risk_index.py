import unittest

from country_risk_index import _normalise_debt, _normalise_growth, _normalise_wgi, score


class CountryRiskIndexTests(unittest.TestCase):
    def test_transformations_have_expected_direction_and_bounds(self):
        self.assertEqual(_normalise_wgi(2.5), 0)
        self.assertEqual(_normalise_wgi(-2.5), 100)
        self.assertEqual(_normalise_growth(10), 0)
        self.assertEqual(_normalise_growth(-10), 100)
        self.assertEqual(_normalise_debt(150), 100)
        self.assertEqual(_normalise_debt(300), 100)

    def test_missing_component_weights_are_renormalised(self):
        governance = {
            "government_effectiveness": {"year": 2023, "value": 0},
            "political_stability": {"year": 2023, "value": 0},
            "rule_of_law": {"year": 2023, "value": 0},
            "control_of_corruption": {"year": 2023, "value": 0},
        }
        row = score({code: governance for code in ("RUS", "IRN", "VEN", "SYR")}, 2024)[0]
        self.assertEqual(row["government_score"], 50)
        self.assertEqual(row["composite_score"], 50)
        self.assertIn("freedom_total", row["missing_indicators"])


if __name__ == "__main__":
    unittest.main()
