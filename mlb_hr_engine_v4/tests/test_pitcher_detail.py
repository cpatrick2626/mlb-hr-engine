import asyncio
import csv
import io
import unittest
from pathlib import Path
from unittest import mock


class _BufferedCsvResponse:
    """Savant response whose body is valid even when the raw stream is unavailable."""

    def __init__(self, body: bytes) -> None:
        self.content = body
        self.closed = False

    @property
    def raw(self):
        raise ValueError("I/O operation on closed file.")

    def raise_for_status(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


def _savant_csv(season: int) -> bytes:
    output = io.StringIO()
    fieldnames = [
        "pitch_type", "events", "stand", "release_speed", "launch_speed",
        "game_year", "game_pk", "at_bat_number",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for index in range(20):
        is_fastball = index < 12
        writer.writerow({
            "pitch_type": "FA" if is_fastball else "SV",
            "events": "home_run" if index == 0 else "strikeout" if index in {1, 2, 3, 4, 12, 13} else "field_out",
            "stand": "R",
            "release_speed": "96.4" if is_fastball else "83.2",
            "launch_speed": "101.0" if index in {0, 5, 6, 7, 8, 9, 14, 15, 16, 17, 18} else "89.0",
            "game_year": str(season),
            "game_pk": "1",
            "at_bat_number": str(index + 1),
        })
    return ("\ufeff" + output.getvalue()).encode("utf-8")


class PitcherSavantRegressionTests(unittest.TestCase):
    def test_buffered_csv_populates_canonical_pitch_stats_when_raw_stream_is_closed(self) -> None:
        from clients import pitch_mix

        response = _BufferedCsvResponse(_savant_csv(pitch_mix.config.CURRENT_SEASON))
        pitch_mix.clear_caches()
        with mock.patch.object(pitch_mix._SESSION, "get", return_value=response):
            stats = pitch_mix.get_pitcher_pitch_stats(99, "R", display_only=True)
            scoring_stats = pitch_mix.get_pitcher_pitch_stats(99, "R")

        self.assertEqual(set(stats), {"FF", "ST"})
        self.assertEqual(stats["FF"]["pa"], 12)
        self.assertEqual(stats["FF"]["avg_speed"], 96.4)
        self.assertEqual(stats["FF"]["k_pct"], 0.333)
        self.assertEqual(stats["FF"]["hr_rate"], 0.083)
        self.assertIsNone(stats["ST"]["hr_rate"])
        self.assertEqual(scoring_stats, {})
        self.assertNotIn(99, pitch_mix._PITCHER_SAVANT_CACHE)
        self.assertIn(99, pitch_mix._PITCHER_DISPLAY_SAVANT_CACHE)
        self.assertTrue(response.closed)

    def test_small_sample_thresholds_remain_null(self) -> None:
        from clients import pitch_mix

        totals = {
            "CH": {
                "pa": 4, "hr": 1, "k": 2, "h": 1, "tb": 4.0, "ab": 4,
                "speed_sum": 340.0, "speed_n": 4, "hard_hit": 3, "contact": 4,
            }
        }
        stats = pitch_mix._finalize_pitch_stats(totals, 4)["CH"]

        self.assertIsNone(stats["hr_rate"])
        self.assertIsNone(stats["k_pct"])
        self.assertIsNone(stats["display_hh"])
        self.assertEqual(stats["pa"], 4)
        self.assertEqual(stats["hr"], 1)
        self.assertEqual(stats["k"], 2)


class PitcherDetailEndpointTests(unittest.TestCase):
    def test_raw_arsenal_aliases_join_canonical_stats_for_the_same_pitch(self) -> None:
        from api import main as api_main

        arsenal = {
            99: [
                {"pitch_type": "FA", "pitch_pct": 0.60, "avg_speed": None, "whiff_pct": 0.25},
                {"pitch_type": "SV", "pitch_pct": 0.40, "avg_speed": None, "whiff_pct": 0.31},
            ]
        }
        pitch_stats = {
            "FF": {"pa": 30, "hr": 2, "k": 8, "avg_speed": 96.4, "hr_rate": 0.067, "k_pct": 0.267, "display_hh": 0.42},
            "ST": {"pa": 8, "hr": 0, "k": 3, "avg_speed": 83.2, "hr_rate": None, "k_pct": 0.375, "display_hh": None},
        }

        with (
            mock.patch.object(api_main, "get_pitcher_arsenal", return_value=arsenal),
            mock.patch.object(api_main, "get_pitcher_pitch_stats", return_value=pitch_stats) as get_stats,
            mock.patch.object(api_main, "get_batter_vs_pitches", return_value={}),
        ):
            detail = asyncio.run(api_main.get_pitcher_detail(99, batter_id=0, batter_side="R", pitcher_hand="R"))

        by_code = {row["code"]: row for row in detail["arsenal"]}
        self.assertEqual(set(by_code), {"FF", "ST"})
        self.assertEqual(detail["pitch_stats"]["FF"]["avg_speed"], 96.4)
        self.assertEqual(detail["pitch_stats"]["ST"]["avg_speed"], 83.2)
        self.assertNotEqual(detail["pitch_stats"]["FF"]["avg_speed"], detail["pitch_stats"]["ST"]["avg_speed"])
        self.assertIsNone(detail["pitch_stats"]["ST"]["hr_rate"])
        get_stats.assert_called_once_with(99, "R", display_only=True)


class AeiFrontendContractTests(unittest.TestCase):
    def test_arsenal_renderer_preserves_hr_sample_gate_and_scales_hh_fraction(self) -> None:
        source = (Path(__file__).parents[2] / "frontend" / "assets" / "js" / "full-slate-matrix.js").read_text(encoding="utf-8")

        self.assertIn("ps.pa >= 10", source)
        self.assertIn("(Number(ps.display_hh)*100).toFixed(0)", source)


if __name__ == "__main__":
    unittest.main()
