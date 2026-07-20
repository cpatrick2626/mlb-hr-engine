"""Authenticated My Tickets read-contract tests."""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi.testclient import TestClient


class _Result:
    def __init__(self, data):
        self.data = data


class _TicketQuery:
    def __init__(self, rows_by_user: dict[str, list[dict]]):
        self._rows_by_user = rows_by_user
        self._user_id = None

    def select(self, _columns: str):
        return self

    def eq(self, column: str, value):
        if column == "user_id":
            self._user_id = value
        return self

    def order(self, _column: str, desc: bool = False):
        return self

    def execute(self):
        return _Result(self._rows_by_user.get(self._user_id, []))


class _Supabase:
    def __init__(self, rows_by_user: dict[str, list[dict]]):
        self._rows_by_user = rows_by_user

    def table(self, name: str):
        if name != "tickets":
            raise AssertionError(f"unexpected table read: {name}")
        return _TicketQuery(self._rows_by_user)


def _rows() -> dict[str, list[dict]]:
    return {
        "user-a": [
            {
                "ticket_id": "open-1",
                "created_at": "2026-07-20T12:00:00Z",
                "date": "2026-07-20",
                "board": "main",
                "status": "pending",
                "fd_deployed": True,
                "completed_at": "2026-07-20T12:05:00Z",
                "settled_at": None,
                "legs": [
                    {
                        "leg_id": "leg-1",
                        "player_name": "Aaron Judge",
                        "team": "NYY",
                        "opponent": "BOS",
                        "pitcher": "Starter One",
                        "hr_result": None,
                        "settlement_status": "pending",
                        "leg_date": "2026-07-20",
                        "removed": False,
                    },
                    {
                        "leg_id": "leg-2",
                        "player_name": "Player Two",
                        "team": "NYY",
                        "opponent": "BOS",
                        "pitcher": "Starter One",
                        "hr_result": None,
                        "settlement_status": "pending",
                        "leg_date": "2026-07-20",
                        "removed": False,
                    },
                ],
            },
            {
                "ticket_id": "old-1",
                "created_at": "2026-07-01T12:00:00Z",
                "date": "2026-07-01",
                "board": "jig",
                "status": "pending",
                "fd_deployed": True,
                "completed_at": "2026-07-01T12:05:00Z",
                "settled_at": None,
                "legs": [{
                    "leg_id": "leg-old",
                    "player_name": "Old Result",
                    "team": "LAD",
                    "opponent": "SF",
                    "pitcher": "Starter Old",
                    "hr_result": 1,
                    "settlement_status": "settled",
                    "leg_date": "2026-07-01",
                    "removed": False,
                }],
            },
        ],
        "user-b": [{"ticket_id": "other-user", "legs": []}],
    }


class MyTicketsContractTests(unittest.TestCase):
    def tearDown(self) -> None:
        from api import main as api_main

        api_main.app.dependency_overrides.clear()

    def test_caller_gets_pending_and_settled_history_with_context_for_all_dates(self) -> None:
        from api import main as api_main
        from api.auth import require_auth

        def schedule(date_str: str):
            if date_str == "2026-07-01":
                away, home, state = "SF", "LAD", "Final"
            else:
                away, home, state = "BOS", "NYY", "Live"
            return [{
                "gamePk": 1001,
                "status": {"abstractGameState": state},
                "teams": {
                    "home": {"team": {"abbreviation": home}},
                    "away": {"team": {"abbreviation": away}},
                },
                "linescore": {
                    "innings": [{
                        "num": 1,
                        "away": {"runs": 0},
                        "home": {"runs": 1},
                    }],
                    "teams": {
                        "away": {"runs": 0, "hits": 1, "errors": 0},
                        "home": {"runs": 1, "hits": 2, "errors": 0},
                    },
                },
            }]
        api_main.app.dependency_overrides[require_auth] = lambda: {"sub": "user-a"}

        with (
            mock.patch.object(api_main, "supabase_client", return_value=_Supabase(_rows())),
            mock.patch("api.ticket_history.schedule_for_date", side_effect=schedule) as schedule_mock,
        ):
            response = TestClient(api_main.app).get("/api/my-tickets")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([t["ticket_id"] for t in payload["tickets"]], ["open-1", "old-1"])
        self.assertNotIn("groups", payload)
        self.assertEqual(
            schedule_mock.call_args_list,
            [mock.call("2026-07-01"), mock.call("2026-07-20")],
        )

        open_legs = payload["tickets"][0]["legs"]
        self.assertEqual(open_legs[0]["game_status"], "In Progress")
        self.assertEqual(open_legs[0]["linescore"]["innings"][0]["home"], 1)
        settled_leg = payload["tickets"][1]["legs"][0]
        self.assertEqual(settled_leg["game_status"], "Final")
        self.assertEqual(settled_leg["linescore"]["innings"][0]["home"], 1)
        self.assertNotIn("odds", str(payload).lower())
        self.assertNotIn('"player":', str(payload).lower())

    def test_unauthenticated_request_is_rejected_with_401(self) -> None:
        from api import main as api_main

        response = TestClient(api_main.app).get("/api/my-tickets")

        self.assertEqual(response.status_code, 401)

    def test_authenticated_payload_without_sub_is_rejected_with_401(self) -> None:
        from api import main as api_main
        from api.auth import require_auth

        api_main.app.dependency_overrides[require_auth] = lambda: {}
        response = TestClient(api_main.app).get("/api/my-tickets")

        self.assertEqual(response.status_code, 401)

    def test_jwt_subject_scopes_results_and_empty_history_is_safe(self) -> None:
        from api import main as api_main
        from api.auth import require_auth

        client = _Supabase(_rows())
        api_main.app.dependency_overrides[require_auth] = lambda: {"sub": "user-b"}
        with (
            mock.patch.object(api_main, "supabase_client", return_value=client),
        ):
            other = TestClient(api_main.app).get("/api/my-tickets")

        self.assertEqual(other.status_code, 200)
        self.assertEqual([ticket["ticket_id"] for ticket in other.json()["tickets"]], ["other-user"])
        self.assertNotIn("open-1", str(other.json()))

        api_main.app.dependency_overrides[require_auth] = lambda: {"sub": "user-empty"}
        with (
            mock.patch.object(api_main, "supabase_client", return_value=client),
        ):
            empty = TestClient(api_main.app).get("/api/my-tickets")

        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json(), {"tickets": []})

    def test_schedule_calls_are_once_per_relevant_date_and_scheduled_innings_are_empty(self) -> None:
        from api import main as api_main
        from api.auth import require_auth

        rows = _rows()["user-a"]
        rows.insert(1, {
            "ticket_id": "recent-settled",
            "date": "2026-07-18",
            "status": "pending",
            "legs": [{
                "leg_id": "recent-leg",
                "player_name": "Recent Result",
                "team": "LAD",
                "opponent": "SF",
                "pitcher": "Recent Starter",
                "hr_result": 0,
                "settlement_status": "settled",
                "leg_date": "2026-07-18",
                "removed": False,
            }],
        })

        def schedule(date_str: str):
            matchup = ("BOS", "NYY") if date_str == "2026-07-20" else ("SF", "LAD")
            return [{
                "gamePk": 1001,
                "status": {"abstractGameState": "Preview"},
                "teams": {
                    "away": {"team": {"abbreviation": matchup[0]}},
                    "home": {"team": {"abbreviation": matchup[1]}},
                },
            }]

        api_main.app.dependency_overrides[require_auth] = lambda: {"sub": "user-a"}
        with (
            mock.patch.object(api_main, "supabase_client", return_value=_Supabase({"user-a": rows})),
            mock.patch("api.ticket_history.schedule_for_date", side_effect=schedule) as schedule_mock,
        ):
            response = TestClient(api_main.app).get("/api/my-tickets")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            schedule_mock.call_args_list,
            [mock.call("2026-07-01"), mock.call("2026-07-18"), mock.call("2026-07-20")],
        )
        tickets = {ticket["ticket_id"]: ticket for ticket in response.json()["tickets"]}
        self.assertEqual(tickets["recent-settled"]["legs"][0]["game_status"], "Scheduled")
        self.assertEqual(tickets["recent-settled"]["legs"][0]["linescore"]["innings"], [])
        self.assertEqual(tickets["old-1"]["legs"][0]["game_status"], "Scheduled")
        self.assertEqual(tickets["old-1"]["legs"][0]["linescore"]["innings"], [])

    def test_schedule_fetch_uses_resolver_client_with_team_and_linescore_hydration(self) -> None:
        from api import ticket_history

        with mock.patch.object(
            ticket_history,
            "resolver_get",
            return_value={"dates": [{"date": "2026-07-20", "games": []}]},
        ) as resolver_get:
            games = ticket_history.schedule_for_date("2026-07-20")

        self.assertEqual(games, [])
        resolver_get.assert_called_once_with(
            "/schedule",
            {"sportId": 1, "date": "2026-07-20", "hydrate": "team,linescore"},
        )


if __name__ == "__main__":
    unittest.main()
