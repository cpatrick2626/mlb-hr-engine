"""Contract tests for the authenticated My Tickets endpoint."""

import copy
import unittest
from datetime import date
from types import SimpleNamespace
from unittest import mock

from fastapi.testclient import TestClient

from api.main import app, require_auth


def _game(state="Final", *, away="NYY", home="BOS", with_linescore=True):
    game = {
        "status": {"abstractGameState": state},
        "teams": {
            "away": {"team": {"abbreviation": away}},
            "home": {"team": {"abbreviation": home}},
        },
    }
    if with_linescore:
        game["linescore"] = {
            "innings": [
                {"num": 1, "away": {"runs": 1}, "home": {"runs": 0}},
                {"num": 2, "away": {"runs": 0}, "home": {"runs": 2}},
            ],
            "teams": {
                "away": {"runs": 1, "hits": 5, "errors": 0},
                "home": {"runs": 2, "hits": 6, "errors": 1},
            },
            "currentInning": 2,
            "balls": 3,
            "strikes": 2,
            "outs": 1,
        }
    return game


class _Query:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []

    def select(self, _columns):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        user_id = next(value for field, value in self.filters if field == "user_id")
        rows = [copy.deepcopy(row) for row in self.rows if row["_user_id"] == user_id]
        for row in rows:
            row.pop("_user_id")
            row["legs"] = [leg for leg in row.get("legs", []) if not leg.get("removed")]
        return SimpleNamespace(data=rows)


class _Client:
    def __init__(self, rows):
        self.rows = rows
        self.query = None

    def table(self, name):
        if name != "tickets":
            raise AssertionError(f"unexpected table: {name}")
        self.query = _Query(self.rows)
        return self.query


class TicketHistoryContractTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {
                "_user_id": "user-a",
                "ticket_id": "ticket-a",
                "date": "2026-07-19",
                "board": "MAIN",
                "ticket_type": None,
                "num_legs": 3,
                "status": "pending",
                "fd_deployed": True,
                "created_at": "2026-07-19T12:00:00Z",
                "completed_at": "2026-07-19T12:01:00Z",
                "odds_american": 999,
                "legs": [
                    {
                        "leg_date": "2026-07-19",
                        "player_name": "Settled Player",
                        "team": "NYY",
                        "opponent": "BOS",
                        "pitcher": "Pitcher One",
                        "hr_result": 1,
                        "settlement_status": "settled",
                        "removed": False,
                        "market_odds_american": 500,
                    },
                    {
                        "leg_date": "2026-07-19",
                        "player_name": "Pending Player",
                        "team": "BOS",
                        "opponent": "NYY",
                        "pitcher": "Pitcher Two",
                        "hr_result": None,
                        "settlement_status": "pending",
                        "removed": False,
                    },
                    {"leg_date": "2026-07-19", "removed": True},
                ],
            },
            {
                "_user_id": "user-b",
                "ticket_id": "ticket-b",
                "date": "2026-07-20",
                "board": "JIG",
                "ticket_type": None,
                "num_legs": 1,
                "status": "building",
                "fd_deployed": False,
                "created_at": "2026-07-20T12:00:00Z",
                "completed_at": None,
                "legs": [{
                    "leg_date": "2026-07-20",
                    "player_name": "Other User Player",
                    "team": "LAD",
                    "opponent": "SF",
                    "pitcher": "Pitcher Three",
                    "hr_result": None,
                    "settlement_status": "pending",
                    "removed": False,
                }],
            },
            {
                "_user_id": "user-a",
                "ticket_id": "ticket-a-settled",
                "date": "2026-07-19",
                "board": "MAIN",
                "ticket_type": None,
                "num_legs": 1,
                "status": "settled",
                "fd_deployed": True,
                "created_at": "2026-07-19T11:00:00Z",
                "completed_at": "2026-07-19T11:01:00Z",
                "legs": [{
                    "leg_date": "2026-07-19",
                    "player_name": "Earlier Settled Player",
                    "team": "NYY",
                    "opponent": "BOS",
                    "pitcher": "Pitcher One",
                    "hr_result": 0,
                    "settlement_status": "settled",
                    "removed": False,
                }],
            },
        ]
        self.db = _Client(self.rows)

    def tearDown(self):
        app.dependency_overrides.clear()

    def _request(self, user_id, schedule):
        app.dependency_overrides[require_auth] = lambda: {"sub": user_id}
        with (
            mock.patch("api.main.supabase_client", return_value=self.db),
            mock.patch("api.main.today_et", return_value=date(2026, 7, 20)),
            mock.patch("api.ticket_history.schedule_for_date", side_effect=schedule),
        ):
            return TestClient(app).get("/api/my-tickets")

    def test_owned_pending_and_settled_legs_share_one_date_call(self):
        schedule_calls = []

        def schedule(date_str):
            schedule_calls.append(date_str)
            return [_game()]

        response = self._request("user-a", schedule)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(schedule_calls, ["2026-07-19"])
        self.assertEqual(
            [ticket["ticket_id"] for ticket in response.json()["tickets"]],
            ["ticket-a", "ticket-a-settled"],
        )
        self.assertEqual(
            {ticket["status"] for ticket in response.json()["tickets"]},
            {"pending", "settled"},
        )
        legs = response.json()["tickets"][0]["legs"]
        self.assertEqual(len(legs), 2)
        self.assertEqual({leg["settlement_status"] for leg in legs}, {"pending", "settled"})
        self.assertEqual(legs[0]["game_status"], "Final")
        self.assertEqual(legs[0]["linescore"]["innings"][0], {"inning": 1, "away": 1, "home": 0})
        self.assertEqual(legs[0]["linescore"]["totals"]["home"], {
            "team": "BOS", "runs": 2, "hits": 6, "errors": 1,
        })
        serialized = response.text.lower()
        self.assertNotIn("odds", serialized)
        self.assertTrue(all(key not in serialized for key in ("currentinning", '"balls"', '"strikes"', '"outs"')))
        self.assertIn(("user_id", "user-a"), self.db.query.filters)
        self.assertIn(("legs.removed", False), self.db.query.filters)

    def test_cross_user_isolation_and_scheduled_empty_linescore(self):
        response = self._request(
            "user-b",
            lambda _date: [_game("Preview", away="LAD", home="SF", with_linescore=False)],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([ticket["ticket_id"] for ticket in response.json()["tickets"]], ["ticket-b"])
        leg = response.json()["tickets"][0]["legs"][0]
        self.assertEqual(leg["game_status"], "Scheduled")
        self.assertEqual(leg["linescore"]["innings"], [])
        self.assertIsNone(leg["linescore"]["totals"]["away"]["runs"])

    def test_empty_history_skips_schedule(self):
        schedule = mock.Mock()
        response = self._request("no-tickets", schedule)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"tickets": []})
        schedule.assert_not_called()

    def test_unauthenticated_is_401(self):
        self.assertEqual(TestClient(app).get("/api/my-tickets").status_code, 401)

    @mock.patch("api.ticket_history.resolver_get")
    def test_schedule_uses_resolver_client_and_required_hydrate(self, resolver_get):
        from api.ticket_history import schedule_for_date

        resolver_get.return_value = {
            "dates": [
                {"date": "2026-07-19", "games": [{"gamePk": 123}]},
                {"date": "2026-07-20", "games": [{"gamePk": 999}]},
            ]
        }
        self.assertEqual(schedule_for_date("2026-07-19"), [{"gamePk": 123}])
        resolver_get.assert_called_once_with(
            "/schedule",
            {"sportId": 1, "date": "2026-07-19", "hydrate": "team,linescore"},
        )


if __name__ == "__main__":
    unittest.main()
