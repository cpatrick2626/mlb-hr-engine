import unittest

from api.main import _build_slate_payload


def _row(**overrides):
    row = {
        "player_id": 1,
        "player_name": "Test Batter",
        "team": "PIT",
        "opponent": "CHC",
        "home_team": "CHC",
        "model_prob": 0.188,
        "season_pa": 100,
        "season_hr": 10,
    }
    row.update(overrides)
    return row


def _payload_for(row, odds_pending=False, odds_pending_stale=False):
    return _build_slate_payload(
        {"all_players": [row], "games": [], "odds_quota": {"used": 2, "remaining": 498}},
        odds_pending=odds_pending,
        odds_pending_stale=odds_pending_stale,
    )["leaderboard_rows"][0]


class TestExistingFieldsUnchanged(unittest.TestCase):
    """Additive-only guard: pre-existing odds fields must not move."""

    def test_existing_market_fields_unchanged_with_real_odds(self):
        out = _payload_for(_row(fanduel_american=500, best_american=500, best_bookmaker="fanduel"))
        self.assertEqual(out["odds"], "+500")
        self.assertEqual(out["odds_bookmaker"], "fanduel")
        self.assertAlmostEqual(out["implied_prob"], round(100.0 / 600.0, 4))
        self.assertAlmostEqual(out["edge"], round(0.188 - 100.0 / 600.0, 4))
        self.assertIsNotNone(out["ev_pct"])

    def test_old_payload_shape_still_present(self):
        out = _payload_for(_row())
        for key in ("model_prob", "model_prob_projected", "tier", "hrprob"):
            self.assertIn(key, out)


class TestFairBuyFields(unittest.TestCase):
    def test_fair_and_buy_from_model_prob(self):
        out = _payload_for(_row(model_prob=0.188))
        self.assertEqual(out["fair_odds"], 432)
        self.assertEqual(out["buy_odds_5"], 459)
        self.assertEqual(out["buy_odds_10"], 486)

    def test_projected_fields_from_projected_prob(self):
        out = _payload_for(_row(model_prob=0.10, model_prob_projected=0.188))
        self.assertEqual(out["fair_odds_projected"], 432)
        self.assertEqual(out["buy_odds_10_projected"], 486)
        # unsuffixed fields must derive only from model_prob, never projected
        self.assertNotEqual(out["fair_odds"], out["fair_odds_projected"])

    def test_null_projected_prob_yields_null_projected_fields(self):
        out = _payload_for(_row(model_prob_projected=None))
        self.assertIsNone(out["fair_odds_projected"])
        self.assertIsNone(out["buy_odds_5_projected"])
        self.assertIsNone(out["buy_odds_10_projected"])


class TestProjectedVsActual(unittest.TestCase):
    def test_both_present_computes_additive_fields(self):
        out = _payload_for(_row(
            model_prob=0.10, model_prob_projected=0.25,
            fanduel_american=200, best_american=200, best_bookmaker="fanduel",
        ))
        self.assertIsNotNone(out["edge_projected_vs_actual"])
        self.assertIsNotNone(out["ev_pct_projected_vs_actual"])
        # never overwrites the real edge/ev_pct (those come from model_prob=0.10)
        self.assertNotEqual(out["edge_projected_vs_actual"], out["edge"])

    def test_null_projected_prob_no_fallback_to_current(self):
        out = _payload_for(_row(
            model_prob=0.10, model_prob_projected=None,
            fanduel_american=200, best_american=200,
        ))
        self.assertIsNone(out["edge_projected_vs_actual"])
        self.assertIsNone(out["ev_pct_projected_vs_actual"])

    def test_null_actual_odds_no_fallback(self):
        out = _payload_for(_row(
            model_prob=0.10, model_prob_projected=0.25,
            fanduel_american=None, best_american=None,
        ))
        self.assertIsNone(out["edge_projected_vs_actual"])
        self.assertIsNone(out["ev_pct_projected_vs_actual"])


class TestDecisionAction(unittest.TestCase):
    def test_unconfirmed_uses_projected_prob(self):
        out = _payload_for(_row(
            model_prob=0.05, model_prob_projected=0.188,
            lineup_confirmed=False,
        ))
        self.assertIn("WATCH FOR +486 OR BETTER", out["decision_action"])

    def test_confirmed_uses_current_prob_even_with_projected_present(self):
        out = _payload_for(_row(
            model_prob=0.188, model_prob_projected=0.05,
            lineup_confirmed=True,
        ))
        self.assertIn("WATCH FOR +486 OR BETTER", out["decision_action"])

    def test_actual_market_above_threshold(self):
        # decision prob .188, quote +500 well above +10% buy (+486)
        out = _payload_for(_row(
            model_prob=0.188, lineup_confirmed=True,
            fanduel_american=500, best_american=500,
        ))
        self.assertIn("ABOVE +10% BUY", out["decision_action"])
        self.assertIn("+500", out["decision_action"])

    def test_actual_market_below_threshold(self):
        # quote +430 is below the +486 threshold for p=.188
        out = _payload_for(_row(
            model_prob=0.188, lineup_confirmed=True,
            fanduel_american=430, best_american=430,
        ))
        self.assertIn("BELOW +10% BUY", out["decision_action"])

    def test_never_uses_forbidden_superlatives(self):
        out = _payload_for(_row(
            model_prob=0.188, lineup_confirmed=True,
            fanduel_american=5000, best_american=5000,
        ))
        for banned in ("LOCK", "BEST BET", "MAX BET", "STRONG BET"):
            self.assertNotIn(banned, out["decision_action"])


class TestMarketState(unittest.TestCase):
    def test_live_market_when_odds_present(self):
        out = _payload_for(_row(fanduel_american=500, best_american=500))
        self.assertEqual(out["market_state"], "LIVE_MARKET")

    def test_pre_market_when_globally_pending_and_not_stale(self):
        out = _payload_for(_row(fanduel_american=None, best_american=None),
                            odds_pending=True, odds_pending_stale=False)
        self.assertEqual(out["market_state"], "PRE_MARKET")

    def test_market_unknown_when_pending_stale(self):
        out = _payload_for(_row(fanduel_american=None, best_american=None),
                            odds_pending=True, odds_pending_stale=True)
        self.assertEqual(out["market_state"], "MARKET_UNKNOWN")

    def test_market_unknown_when_not_pending_but_no_row_odds(self):
        out = _payload_for(_row(fanduel_american=None, best_american=None),
                            odds_pending=False, odds_pending_stale=False)
        self.assertEqual(out["market_state"], "MARKET_UNKNOWN")

    def test_never_emits_no_market(self):
        for pending, stale in ((True, True), (True, False), (False, False)):
            out = _payload_for(_row(fanduel_american=None, best_american=None),
                                odds_pending=pending, odds_pending_stale=stale)
            self.assertNotEqual(out["market_state"], "NO_MARKET")


class TestQuoteTimestamp(unittest.TestCase):
    def test_fanduel_last_update_passed_through(self):
        out = _payload_for(_row(
            fanduel_american=500, fanduel_last_update="2026-09-16T11:00:00Z",
            best_american=500, best_last_update="2026-09-16T10:00:00Z",
        ))
        self.assertEqual(out["market_observed_at"], "2026-09-16T11:00:00Z")

    def test_best_book_last_update_used_when_no_fanduel(self):
        out = _payload_for(_row(
            fanduel_american=None,
            best_american=500, best_bookmaker="betrivers",
            best_last_update="2026-09-16T10:00:00Z",
        ))
        self.assertEqual(out["market_observed_at"], "2026-09-16T10:00:00Z")

    def test_null_when_no_odds(self):
        out = _payload_for(_row(fanduel_american=None, best_american=None))
        self.assertIsNone(out["market_observed_at"])

    def test_null_when_odds_present_but_no_timestamp(self):
        out = _payload_for(_row(fanduel_american=500, best_american=500))
        self.assertIsNone(out["market_observed_at"])


class TestOldPayloadCompatibility(unittest.TestCase):
    def test_row_with_no_new_source_fields_is_null_safe(self):
        # Simulates a row shape from before this change: no lineup_confirmed,
        # no model_prob_projected, no *_last_update fields. lineup_confirmed
        # defaults to False (unconfirmed) with no projection, so decision_action
        # must be null rather than falling back to current model_prob.
        out = _payload_for({
            "player_id": 2, "player_name": "Legacy Batter", "team": "PIT",
            "opponent": "CHC", "home_team": "CHC", "model_prob": 0.10,
        })
        self.assertIsNone(out["fair_odds_projected"])
        self.assertIsNone(out["market_observed_at"])
        self.assertIsNone(out["decision_action"])
        self.assertEqual(out["market_state"], "MARKET_UNKNOWN")


class TestUnconfirmedNoProjection(unittest.TestCase):
    """Unconfirmed player with no model_prob_projected must not derive an
    Early-Day decision from current model_prob. CURRENT FAIR/BUY may still
    populate from model_prob for contextual display."""

    def test_decision_action_null_when_unconfirmed_and_no_projection(self):
        out = _payload_for(_row(
            model_prob=0.188, model_prob_projected=None,
            lineup_confirmed=False,
        ))
        self.assertIsNone(out["decision_action"])
        self.assertEqual(out["fair_odds"], 432)
        self.assertEqual(out["buy_odds_10"], 486)
        self.assertIsNone(out["fair_odds_projected"])
        self.assertIsNone(out["buy_odds_10_projected"])


if __name__ == "__main__":
    unittest.main()
