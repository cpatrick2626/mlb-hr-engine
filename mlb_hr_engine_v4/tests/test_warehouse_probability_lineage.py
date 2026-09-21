"""Warehouse-only persistence tests for MAIN probability lineage."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if isinstance(sys.modules.get("tracking"), mock.Mock):
    for module_name in tuple(sys.modules):
        if module_name == "tracking" or module_name.startswith("tracking."):
            del sys.modules[module_name]
if isinstance(sys.modules.get("pipeline"), mock.Mock):
    del sys.modules["pipeline"]
import pipeline


class _Result:
    data = []


class _CaptureTable:
    def __init__(self) -> None:
        self.rows = None
        self.on_conflict = None

    def upsert(self, rows, on_conflict):
        self.rows = rows
        self.on_conflict = on_conflict
        return self

    def execute(self):
        return _Result()


class _CaptureClient:
    def __init__(self) -> None:
        self.target = None
        self.table_api = _CaptureTable()

    def table(self, name):
        self.target = name
        return self.table_api


class TestWarehouseProbabilityLineage(unittest.TestCase):
    def test_main_snapshot_adds_lineage_without_mutating_live_payload(self) -> None:
        client = _CaptureClient()
        fake_supabase = types.SimpleNamespace(create_client=lambda *_: client)
        player = {"player_id": 7, "game_pk": 100, "model_prob": 0.1785}
        lineage = {
            "schema_version": 1,
            "snapshot_kind": "main_probability",
            "pre_scale_model_prob": 0.175,
            "effective_prob_scale": 1.0,
            "post_scale_pre_calibration_prob": 0.175,
            "calibration_branch": "PLATT_ELITE",
            "final_model_prob": 0.1785,
        }

        with (
            mock.patch.dict(sys.modules, {"supabase": fake_supabase}),
            mock.patch.dict(
                "os.environ",
                {"SUPABASE_URL": "local", "SUPABASE_SERVICE_KEY": "local"},
                clear=False,
            ),
        ):
            pipeline._write_batter_stat_history(
                "2026-09-20",
                "2026-09-20T12:00:00+00:00",
                (player,),
                {(7, 100): lineage},
            )

        stored = client.table_api.rows[0]["raw_payload"]
        self.assertEqual(client.target, "batter_stat_history")
        self.assertEqual(stored["probability_lineage"], lineage)
        self.assertEqual(stored["model_prob"], lineage["final_model_prob"])
        self.assertNotIn("probability_lineage", player)

    def test_missing_lineage_preserves_normal_snapshot_and_batch(self) -> None:
        client = _CaptureClient()
        fake_supabase = types.SimpleNamespace(create_client=lambda *_: client)
        missing_lineage = {"player_id": 7, "game_pk": 100, "model_prob": 0.1785}
        valid_lineage = {"player_id": 8, "game_pk": 100, "model_prob": 0.1632}
        untrusted_lineage = {"player_id": 9, "game_pk": 100, "model_prob": 0.1510}
        lineage = {"schema_version": 1, "final_model_prob": 0.1632}

        with (
            mock.patch.dict(sys.modules, {"supabase": fake_supabase}),
            mock.patch.dict(
                "os.environ",
                {"SUPABASE_URL": "local", "SUPABASE_SERVICE_KEY": "local"},
                clear=False,
            ),
            self.assertLogs("pipeline", level="WARNING") as logs,
        ):
            pipeline._write_batter_stat_history(
                "2026-09-20",
                "2026-09-20T12:00:00+00:00",
                (missing_lineage, valid_lineage, untrusted_lineage),
                {(8, 100): lineage, (9, 100): {}},
            )

        self.assertEqual(len(client.table_api.rows), 3)
        missing_stored, valid_stored, untrusted_stored = [
            row["raw_payload"] for row in client.table_api.rows
        ]
        self.assertEqual(missing_stored, missing_lineage)
        self.assertNotIn("probability_lineage", missing_stored)
        self.assertEqual(valid_stored["probability_lineage"], lineage)
        self.assertEqual(untrusted_stored, untrusted_lineage)
        self.assertNotIn("probability_lineage", untrusted_stored)
        self.assertIn("normal snapshots preserved", "\n".join(logs.output))

    def test_jig_snapshot_does_not_claim_a_new_probability_lineage(self) -> None:
        client = _CaptureClient()
        fake_supabase = types.SimpleNamespace(create_client=lambda *_: client)

        with (
            mock.patch.dict(sys.modules, {"supabase": fake_supabase}),
            mock.patch.dict(
                "os.environ",
                {"SUPABASE_URL": "local", "SUPABASE_SERVICE_KEY": "local"},
                clear=False,
            ),
        ):
            pipeline._write_jig_stat_history(
                "2026-09-20",
                "2026-09-20T12:00:01+00:00",
                ({"id": 7, "game_pk": 100, "jigScore": 88},),
                {(7, 100): {"model_prob": 0.1785, "game_status": "Preview"}},
            )

        stored = client.table_api.rows[0]["raw_payload"]
        self.assertNotIn("probability_lineage", stored)


if __name__ == "__main__":
    unittest.main()
