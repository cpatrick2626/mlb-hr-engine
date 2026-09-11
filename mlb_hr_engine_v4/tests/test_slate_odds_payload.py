import unittest

from api.main import _build_slate_payload


def _row(**overrides):
    row = {
        "player_id": 1,
        "player_name": "Test Batter",
        "team": "PIT",
        "opponent": "CHC",
        "home_team": "CHC",
        "model_prob": 0.12,
        "season_pa": 100,
        "season_hr": 10,
    }
    row.update(overrides)
    return row


def _payload_for(row):
    return _build_slate_payload(
        {"all_players": [row], "games": [], "odds_quota": {"used": 2, "remaining": 498}}
    )["leaderboard_rows"][0]


class TestSlateOddsPayload(unittest.TestCase):
    def test_fanduel_is_preferred(self):
        out = _payload_for(
            _row(fanduel_american=450, best_american=500, best_bookmaker="betrivers")
        )
        self.assertEqual(out["odds"], "+450")
        self.assertEqual(out["odds_bookmaker"], "fanduel")
        self.assertIsNotNone(out["implied_prob"])
        self.assertIsNotNone(out["edge"])
        self.assertIsNotNone(out["ev_pct"])

    def test_best_bookmaker_fallback_is_published(self):
        out = _payload_for(
            _row(best_american=500, best_bookmaker="betrivers", fanduel_american=None)
        )
        self.assertEqual(out["odds"], "+500")
        self.assertEqual(out["odds_bookmaker"], "betrivers")
        self.assertIsNotNone(out["implied_prob"])
        self.assertIsNotNone(out["edge"])
        self.assertIsNotNone(out["ev_pct"])

    def test_no_book_line_remains_null(self):
        out = _payload_for(_row(fanduel_american=None, best_american=None))
        self.assertIsNone(out["odds"])
        self.assertIsNone(out["odds_bookmaker"])
        self.assertIsNone(out["implied_prob"])
        self.assertIsNone(out["edge"])
        self.assertIsNone(out["ev_pct"])


if __name__ == "__main__":
    unittest.main()
