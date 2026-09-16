import unittest

from engine import market as mkt


class TestDecimalAmericanConversion(unittest.TestCase):
    def test_positive_round_trip(self):
        dec = mkt.american_to_decimal(250)
        self.assertAlmostEqual(dec, 3.5)
        self.assertEqual(mkt.decimal_to_american(dec), 250)

    def test_negative_round_trip(self):
        dec = mkt.american_to_decimal(-150)
        self.assertAlmostEqual(dec, 1.6666666666666667)
        self.assertEqual(mkt.decimal_to_american(dec), -150)


class TestFairAndBuyOdds(unittest.TestCase):
    """p=.188 is the CRITICAL TEST fixture from the Early-Day Decision Intelligence spec."""

    def test_fair_odds_p188(self):
        self.assertEqual(mkt.fair_odds_from_prob(0.188), 432)

    def test_buy_5_p188(self):
        self.assertEqual(mkt.buy_odds_from_prob(0.188, 0.05), 459)

    def test_buy_10_p188_strict_threshold(self):
        # Naive rounding of 485.106... would give +485, which is UNDER 10% EV.
        # +486 is the smallest whole-number price that clears 10% EV.
        self.assertEqual(mkt.buy_odds_from_prob(0.188, 0.10), 486)

    def test_buy_10_p188_485_is_below_target(self):
        self.assertLess(mkt.ev_pct_for_prob(0.188, 485), 10.0)

    def test_buy_10_p188_486_clears_target(self):
        self.assertGreaterEqual(mkt.ev_pct_for_prob(0.188, 486), 10.0)

    def test_negative_odds_fair(self):
        self.assertEqual(mkt.fair_odds_from_prob(0.60), -150)

    def test_negative_odds_buy_10(self):
        self.assertEqual(mkt.buy_odds_from_prob(0.60, 0.10), -120)

    def test_null_probability_is_null(self):
        self.assertIsNone(mkt.fair_odds_from_prob(None))
        self.assertIsNone(mkt.buy_odds_from_prob(None, 0.10))

    def test_invalid_probability_is_null(self):
        self.assertIsNone(mkt.fair_odds_from_prob(0.0))
        self.assertIsNone(mkt.fair_odds_from_prob(1.0))
        self.assertIsNone(mkt.buy_odds_from_prob(1.5, 0.10))


class TestEvPctForProb(unittest.TestCase):
    def test_null_inputs(self):
        self.assertIsNone(mkt.ev_pct_for_prob(None, 500))
        self.assertIsNone(mkt.ev_pct_for_prob(0.2, None))

    def test_matches_break_even_at_fair_price(self):
        fair = mkt.fair_odds_from_prob(0.25)
        self.assertAlmostEqual(mkt.ev_pct_for_prob(0.25, fair), 0.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
