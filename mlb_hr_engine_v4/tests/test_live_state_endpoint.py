"""Contract tests for GET /api/live-state/{game_pk} (Phase 1, Layer 1).

Mocks clients.mlb_stats.get_live_game_state — never hits the live MLB feed.
Confirms: live/non-live/missing-field cases all return well-formed JSON
(never a 500), and the in-process TTL cache dedupes repeated polls for the
same game_pk within the TTL window.
"""

import unittest
from unittest import mock

from fastapi.testclient import TestClient

import api.main as main
from api.main import app


class LiveStateEndpointContractTests(unittest.TestCase):
    def setUp(self):
        main._LIVE_STATE_CACHE.clear()

    def tearDown(self):
        main._LIVE_STATE_CACHE.clear()

    def test_live_game_returns_full_contract_shape(self):
        state = {
            "game_pk": 745123, "status": "Live", "inning": 6, "inning_half": "Top",
            "outs": 2, "score": {"home": 3, "away": 2},
            "bases": {"first": True, "second": False, "third": True},
            "current_pitcher": {"id": 123, "name": "P One"},
            "current_batter": {"id": 456, "name": "B One"},
            "on_deck": {"id": 789, "name": "B Two"},
        }
        with mock.patch("api.main.get_live_game_state", return_value=state) as fetch:
            response = TestClient(app).get("/api/live-state/745123")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        fetch.assert_called_once_with(745123)
        for key in (
            "game_pk", "status", "inning", "inning_half", "outs", "score", "bases",
            "current_pitcher", "current_batter", "on_deck", "fetched_at",
        ):
            self.assertIn(key, body)
        self.assertEqual(body["score"], {"home": 3, "away": 2})
        self.assertEqual(body["current_batter"], {"id": 456, "name": "B One"})

    def test_non_live_game_returns_well_formed_nulls_not_error(self):
        state = {
            "game_pk": 745124, "status": "Preview", "inning": None, "inning_half": None,
            "outs": None, "score": {"home": None, "away": None},
            "bases": {"first": False, "second": False, "third": False},
            "current_pitcher": None, "current_batter": None, "on_deck": None,
        }
        with mock.patch("api.main.get_live_game_state", return_value=state):
            response = TestClient(app).get("/api/live-state/745124")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "Preview")
        self.assertIsNone(body["current_batter"])
        self.assertIsNone(body["inning"])

    def test_client_raising_never_produces_a_500(self):
        with mock.patch("api.main.get_live_game_state", side_effect=Exception("mlb api down")):
            response = TestClient(app).get("/api/live-state/745125")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["status"])
        self.assertIsNone(body["current_batter"])
        self.assertEqual(body["score"], {"home": None, "away": None})

    def test_missing_game_pk_field_defaults_null_not_500(self):
        """Simulates a partial upstream payload — missing keys, not just null values."""
        with mock.patch("api.main.get_live_game_state", return_value={"game_pk": 745126}):
            response = TestClient(app).get("/api/live-state/745126")
        self.assertEqual(response.status_code, 200)
        # FastAPI serializes whatever dict comes back; route itself adds no
        # extra assumptions about keys being present beyond fetched_at.
        self.assertIn("fetched_at", response.json())

    def test_repeated_polls_within_ttl_hit_cache_not_client(self):
        """Real elapsed time between two immediate calls is far below the 20s TTL."""
        state = {"game_pk": 1, "status": "Live", "inning": 1, "inning_half": "Top",
                 "outs": 0, "score": {"home": 0, "away": 0},
                 "bases": {"first": False, "second": False, "third": False},
                 "current_pitcher": None, "current_batter": None, "on_deck": None}
        with mock.patch("api.main.get_live_game_state", return_value=state) as fetch:
            client = TestClient(app)
            client.get("/api/live-state/1")
            client.get("/api/live-state/1")
            client.get("/api/live-state/1")

        fetch.assert_called_once_with(1)

    def test_poll_after_ttl_expiry_refetches(self):
        """Backdate the cache entry past the TTL directly, rather than mocking the
        process-wide time.monotonic clock (which anyio/starlette also rely on)."""
        state = {"game_pk": 1, "status": "Live", "inning": 1, "inning_half": "Top",
                 "outs": 0, "score": {"home": 0, "away": 0},
                 "bases": {"first": False, "second": False, "third": False},
                 "current_pitcher": None, "current_batter": None, "on_deck": None}
        with mock.patch("api.main.get_live_game_state", return_value=state) as fetch:
            client = TestClient(app)
            client.get("/api/live-state/1")
            fetched_at, cached_state = main._LIVE_STATE_CACHE[1]
            main._LIVE_STATE_CACHE[1] = (
                fetched_at - (main.LIVE_STATE_CACHE_TTL_SECONDS + 5), cached_state,
            )
            client.get("/api/live-state/1")

        self.assertEqual(fetch.call_count, 2)

    def test_different_game_pks_are_cached_independently(self):
        with mock.patch("api.main.get_live_game_state", return_value={"game_pk": 0}) as fetch:
            client = TestClient(app)
            client.get("/api/live-state/1")
            client.get("/api/live-state/2")

        self.assertEqual(fetch.call_count, 2)
        fetch.assert_any_call(1)
        fetch.assert_any_call(2)


if __name__ == "__main__":
    unittest.main()
