"""Honest ticket probability/EV contract tests; no scoring code is imported."""

from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace
from unittest import mock

from fastapi.testclient import TestClient

from api import main as api_main
from api.auth import require_auth


def _leg(leg_id, probability, odds, *, pa=30):
    return {
        "leg_id": leg_id,
        "player_name": f"Player {leg_id}",
        "model_prob": probability,
        "market_odds_american": odds,
        "signal_snapshot": {"vs_hand_pa": pa} if pa is not None else {},
        "removed": False,
    }


class _Query:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []

    def select(self, _columns): return self
    def eq(self, field, value): self.filters.append((field, value)); return self
    def limit(self, _value): return self

    def execute(self):
        rows = [
            copy.deepcopy(row)
            for row in self.rows
            if all(row.get(field) == value for field, value in self.filters)
        ]
        return SimpleNamespace(data=rows)


class _Db:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        if name != "tickets":
            raise AssertionError(f"unexpected table: {name}")
        return _Query(self.rows)


class TicketAnalysisMathTests(unittest.TestCase):
    def test_negative_parlay_grades_poorly_and_singles_better_fires(self):
        analysis = api_main._ticket_analysis({
            "ticket_id": "ticket-negative",
            "odds_american": None,
            "legs": [
                _leg("one", 0.20, 350, pa=8),
                _leg("two", 0.16, 500, pa=25),
            ],
        })
        first, second = analysis["legs"]
        self.assertEqual(first["implied_prob"], 0.2222)
        self.assertEqual(first["edge"], -0.0222)
        self.assertEqual(first["ev_pct"], -10.0)
        self.assertEqual(second["implied_prob"], 0.1667)
        self.assertEqual(second["edge"], -0.0067)
        self.assertEqual(second["ev_pct"], -4.0)
        self.assertEqual(analysis["combined"]["probability"], 0.032)
        self.assertEqual(analysis["combined"]["decimal_odds"], 27.0)
        self.assertEqual(analysis["combined"]["ev_pct"], -13.6)
        self.assertEqual(analysis["grade"], {
            "status": "complete",
            "letter": "F",
            "label": "POOR",
            "color": "red",
            "driver": "combined_ev_pct",
        })
        self.assertEqual(analysis["confidence"]["label"], "LOW")
        self.assertIn("thin_sample_under_10_pa", analysis["confidence"]["reasons"])
        self.assertIs(analysis["honest_read"]["singles_would_be_better"], True)
        self.assertEqual(analysis["honest_read"]["best_single_ev_pct"], -4.0)

    def test_positive_single_grades_good_with_same_board_ev_math(self):
        analysis = api_main._ticket_analysis({
            "ticket_id": "ticket-positive",
            "odds_american": None,
            "legs": [_leg("one", 0.20, 450, pa=40)],
        })
        leg = analysis["legs"][0]
        self.assertEqual(leg["implied_prob"], 0.1818)
        self.assertEqual(leg["edge"], 0.0182)
        self.assertEqual(leg["ev_pct"], 10.0)
        self.assertEqual(analysis["combined"]["probability"], 0.20)
        self.assertEqual(analysis["combined"]["ev_pct"], 10.0)
        self.assertEqual(analysis["grade"]["letter"], "A")
        self.assertEqual(analysis["grade"]["label"], "GOOD")
        self.assertEqual(analysis["grade"]["color"], "green")
        self.assertIs(analysis["honest_read"]["singles_would_be_better"], False)

    def test_missing_leg_odds_makes_combined_ev_and_grade_pending(self):
        analysis = api_main._ticket_analysis({
            "ticket_id": "ticket-pending",
            "odds_american": 2000,
            "legs": [_leg("one", 0.20, 450), _leg("two", 0.16, None)],
        })
        self.assertEqual(analysis["combined"]["probability"], 0.032)
        self.assertIsNone(analysis["combined"]["ev_pct"])
        self.assertIs(analysis["combined"]["partial"], True)
        self.assertIn("one_or_more_legs_missing_odds", analysis["combined"]["pending_reasons"])
        self.assertEqual(analysis["grade"]["status"], "pending")
        self.assertIsNone(analysis["grade"]["letter"])
        self.assertIsNone(analysis["honest_read"]["singles_would_be_better"])
        self.assertEqual(analysis["confidence"]["label"], "LOW")

    def test_actual_ticket_odds_override_leg_product_for_combined_ev(self):
        analysis = api_main._ticket_analysis({
            "ticket_id": "ticket-actual-odds",
            "odds_american": 2400,
            "legs": [_leg("one", 0.20, 350), _leg("two", 0.16, 500)],
        })
        self.assertEqual(analysis["combined"]["odds_source"], "ticket_actual")
        self.assertEqual(analysis["combined"]["decimal_odds"], 25.0)
        self.assertEqual(analysis["combined"]["ev_pct"], -20.0)

    def test_negative_american_odds_use_board_implied_probability_math(self):
        analysis = api_main._ticket_analysis({
            "ticket_id": "ticket-negative-american",
            "odds_american": None,
            "legs": [_leg("one", 0.60, -150, pa=40)],
        })
        leg = analysis["legs"][0]
        self.assertEqual(leg["implied_prob"], 0.60)
        self.assertEqual(leg["decimal_odds"], 1.6667)
        self.assertEqual(leg["edge"], 0.0)
        self.assertEqual(leg["ev_pct"], 0.0)
        self.assertEqual(analysis["grade"]["label"], "NEUTRAL")


class TicketAnalysisEndpointTests(unittest.TestCase):
    def tearDown(self):
        api_main.app.dependency_overrides.clear()

    def _client_for(self, user_id):
        api_main.app.dependency_overrides[require_auth] = lambda: {"sub": user_id}
        return TestClient(api_main.app)

    def test_analysis_is_owner_only_and_exposes_no_private_identity(self):
        db = _Db([{
            "ticket_id": "ticket-a",
            "user_id": "user-a",
            "odds_american": None,
            "legs": [_leg("one", 0.20, 450)],
        }])
        with mock.patch.object(api_main, "supabase_client", return_value=db):
            forbidden = self._client_for("user-b").get("/api/tickets/ticket-a/analysis")
            response = self._client_for("user-a").get("/api/tickets/ticket-a/analysis")
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("user_id", response.text)
        self.assertNotIn("email", response.text.lower())
        api_main.app.dependency_overrides.clear()
        self.assertEqual(
            TestClient(api_main.app).get("/api/tickets/ticket-a/analysis").status_code,
            401,
        )

    def test_complete_contract_explicitly_resets_active_slip(self):
        with mock.patch.object(
            api_main,
            "complete_ticket",
            return_value={"ticket_id": "ticket-a", "num_legs": 2, "fd_deployed": True},
        ):
            response = self._client_for("user-a").post(
                "/api/tickets/complete",
                json={"ticket_id": "ticket-a", "stake": 5},
            )
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["reset_slip"], True)
        self.assertIsNone(response.json()["active_ticket_id"])


if __name__ == "__main__":
    unittest.main()
