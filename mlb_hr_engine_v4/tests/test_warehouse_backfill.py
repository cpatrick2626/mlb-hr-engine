"""Warehouse Phase 2 exact-game outcome backfill tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api import warehouse_backfill


def _game(game_pk: int, state: str) -> dict:
    return {
        "gamePk": game_pk,
        "abstractGameState": state,
        "detailedState": state,
    }


class _Result:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, rows: list[dict], payload: dict):
        self.rows = rows
        self.payload = payload
        self.filters = []

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def is_(self, field, value):
        self.filters.append((field, None if value == "null" else value))
        return self

    def execute(self):
        matched = [
            row for row in self.rows
            if all(row.get(field) == value for field, value in self.filters)
        ]
        for row in matched:
            row.update(self.payload)
        return _Result([dict(row) for row in matched])


class _FakeTable:
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def update(self, payload):
        return _FakeQuery(self.rows, payload)


class _FakeClient:
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def table(self, name):
        if name != "batter_stat_history":
            raise AssertionError(name)
        return _FakeTable(self.rows)


class TestWarehouseBackfill(unittest.TestCase):
    def test_exact_game_matching_is_doubleheader_safe(self) -> None:
        rows = [
            {"batter_id": 7, "game_pk": 100},
            {"batter_id": 7, "game_pk": 101},
        ]
        boxscores = {
            100: {7: {"hr": 1}},
            101: {7: {"hr": 0}},
        }

        result = warehouse_backfill.resolve_outcomes(
            rows,
            "2026-07-21",
            schedule_fn=lambda _: [_game(100, "Final"), _game(101, "Final")],
            boxscore_fn=lambda game_pk: boxscores[game_pk],
            sleep_fn=lambda _: None,
        )

        outcomes = {(r["batter_id"], r["game_pk"]): r["hr_outcome"] for r in result}
        self.assertEqual(outcomes[(7, 100)], 1)
        self.assertEqual(outcomes[(7, 101)], 0)

    def test_non_final_and_empty_boxscore_stay_unresolved(self) -> None:
        rows = [
            {"batter_id": 7, "game_pk": 100},
            {"batter_id": 8, "game_pk": 101},
        ]
        result = warehouse_backfill.resolve_outcomes(
            rows,
            "2026-07-21",
            schedule_fn=lambda _: [_game(100, "Live"), _game(101, "Final")],
            boxscore_fn=lambda _: {},
            sleep_fn=lambda _: None,
        )

        by_game = {r["game_pk"]: r for r in result}
        self.assertIsNone(by_game[100]["hr_outcome"])
        self.assertEqual(by_game[100]["reason"], "game_not_final")
        self.assertIsNone(by_game[101]["hr_outcome"])
        self.assertEqual(by_game[101]["reason"], "empty_boxscore")

    def test_commit_updates_only_null_exact_match_and_rerun_is_idempotent(self) -> None:
        untouched_payload = {"model_prob": 0.42}
        rows = [
            {
                "slate_date": "2026-07-21", "run_ts": "a", "batter_id": 7,
                "game_pk": 100, "hr_outcome": None, "raw_payload": untouched_payload,
            },
            {
                "slate_date": "2026-07-21", "run_ts": "b", "batter_id": 7,
                "game_pk": 100, "hr_outcome": 1, "raw_payload": {"keep": True},
            },
            {
                "slate_date": "2026-07-21", "run_ts": "c", "batter_id": 7,
                "game_pk": 101, "hr_outcome": None, "raw_payload": {"keep": True},
            },
        ]
        resolutions = [{
            "slate_date": "2026-07-21", "batter_id": 7, "game_pk": 100,
            "hr_outcome": 0,
        }]
        client = _FakeClient(rows)

        first = warehouse_backfill.commit_outcomes(resolutions, client=client)
        second = warehouse_backfill.commit_outcomes(resolutions, client=client)

        self.assertEqual(first, 1)
        self.assertEqual(second, 0)
        self.assertEqual(rows[0]["hr_outcome"], 0)
        self.assertEqual(rows[1]["hr_outcome"], 1)
        self.assertIsNone(rows[2]["hr_outcome"])
        self.assertIs(rows[0]["raw_payload"], untouched_payload)


if __name__ == "__main__":
    unittest.main()
