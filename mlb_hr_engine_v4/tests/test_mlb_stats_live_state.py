"""Unit tests for the Phase-1 live-state client bundle (clients/mlb_stats.py).

Mocks the MLB Stats API transport (_get) — never hits the live feed. Confirms
the live / non-live / missing-field / request-failure cases all return a
well-formed dict and never raise.
"""

import unittest
from unittest import mock

from clients import mlb_stats


def _schedule_response(game_pk, abstract_state):
    return {
        "dates": [
            {"games": [{"gamePk": game_pk, "status": {"abstractGameState": abstract_state}}]},
        ]
    }


class GetGameAbstractStatusTests(unittest.TestCase):
    def test_zero_game_pk_short_circuits(self):
        self.assertEqual(mlb_stats.get_game_abstract_status(0), "")

    def test_matches_by_game_pk(self):
        with mock.patch.object(mlb_stats, "_get", return_value=_schedule_response(745123, "Live")):
            self.assertEqual(mlb_stats.get_game_abstract_status(745123), "Live")

    def test_no_matching_game_pk_returns_empty(self):
        with mock.patch.object(mlb_stats, "_get", return_value=_schedule_response(999, "Live")):
            self.assertEqual(mlb_stats.get_game_abstract_status(745123), "")

    def test_request_failure_returns_empty_not_raise(self):
        with mock.patch.object(mlb_stats, "_get", side_effect=Exception("network down")):
            self.assertEqual(mlb_stats.get_game_abstract_status(745123), "")


class GetLiveGameStateTests(unittest.TestCase):
    def test_zero_game_pk_returns_well_formed_nulls(self):
        state = mlb_stats.get_live_game_state(0)
        self.assertEqual(state["game_pk"], 0)
        self.assertIsNone(state["status"])
        self.assertIsNone(state["inning"])
        self.assertIsNone(state["current_batter"])
        self.assertEqual(state["score"], {"home": None, "away": None})
        self.assertEqual(state["bases"], {"first": False, "second": False, "third": False})

    def test_live_game_full_bundle(self):
        linescore = {
            "currentInning": 6,
            "inningState": "Top",
            "outs": 2,
            "teams": {"home": {"runs": 3}, "away": {"runs": 2}},
            "offense": {
                "batter": {"id": 456, "fullName": "Current Batter"},
                "onDeck": {"id": 789, "fullName": "On Deck Guy"},
                "first": {"id": 111, "fullName": "Runner One"},
                "third": {"id": 333, "fullName": "Runner Three"},
            },
            "defense": {"pitcher": {"id": 123, "fullName": "Current Pitcher"}},
        }

        def fake_get(path, params=None):
            if path == "/schedule":
                return _schedule_response(745123, "Live")
            if path == "/game/745123/linescore":
                return linescore
            raise AssertionError(f"unexpected path: {path}")

        with mock.patch.object(mlb_stats, "_get", side_effect=fake_get):
            state = mlb_stats.get_live_game_state(745123)

        self.assertEqual(state["game_pk"], 745123)
        self.assertEqual(state["status"], "Live")
        self.assertEqual(state["inning"], 6)
        self.assertEqual(state["inning_half"], "Top")
        self.assertEqual(state["outs"], 2)
        self.assertEqual(state["score"], {"home": 3, "away": 2})
        self.assertEqual(state["bases"], {"first": True, "second": False, "third": True})
        self.assertEqual(state["current_pitcher"], {"id": 123, "name": "Current Pitcher"})
        self.assertEqual(state["current_batter"], {"id": 456, "name": "Current Batter"})
        self.assertEqual(state["on_deck"], {"id": 789, "name": "On Deck Guy"})

    def test_non_live_game_returns_nulls_not_500_shape(self):
        def fake_get(path, params=None):
            if path == "/schedule":
                return _schedule_response(745124, "Preview")
            if path == "/game/745124/linescore":
                return {}  # scheduled game — linescore is empty before first pitch
            raise AssertionError(f"unexpected path: {path}")

        with mock.patch.object(mlb_stats, "_get", side_effect=fake_get):
            state = mlb_stats.get_live_game_state(745124)

        self.assertEqual(state["status"], "Preview")
        self.assertIsNone(state["inning"])
        self.assertIsNone(state["outs"])
        self.assertIsNone(state["current_batter"])
        self.assertIsNone(state["on_deck"])
        self.assertIsNone(state["current_pitcher"])
        self.assertEqual(state["score"], {"home": None, "away": None})
        self.assertEqual(state["bases"], {"first": False, "second": False, "third": False})

    def test_missing_person_id_is_treated_as_absent(self):
        """A batter/pitcher dict without an id (TBD-style placeholder) -> None, never a partial object."""
        linescore = {
            "currentInning": 1,
            "offense": {"batter": {"fullName": "TBD"}},
            "defense": {},
        }

        def fake_get(path, params=None):
            if path == "/schedule":
                return _schedule_response(1, "Live")
            return linescore

        with mock.patch.object(mlb_stats, "_get", side_effect=fake_get):
            state = mlb_stats.get_live_game_state(1)

        self.assertIsNone(state["current_batter"])
        self.assertIsNone(state["current_pitcher"])

    def test_linescore_request_failure_still_returns_well_formed_dict(self):
        def fake_get(path, params=None):
            if path == "/schedule":
                return _schedule_response(745125, "Live")
            raise Exception("timeout")

        with mock.patch.object(mlb_stats, "_get", side_effect=fake_get):
            state = mlb_stats.get_live_game_state(745125)

        self.assertEqual(state["status"], "Live")
        self.assertIsNone(state["inning"])
        self.assertIsNone(state["current_batter"])
        self.assertEqual(state["score"], {"home": None, "away": None})

    def test_both_requests_failing_never_raises(self):
        with mock.patch.object(mlb_stats, "_get", side_effect=Exception("down")):
            state = mlb_stats.get_live_game_state(745126)
        self.assertEqual(state["game_pk"], 745126)
        self.assertIsNone(state["status"])
        self.assertIsNone(state["current_batter"])


if __name__ == "__main__":
    unittest.main()
