"""Canonical pull_air_pct on pipeline players (Statcast-derived, no HVY wiring yet)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from clients import statcast


class TestPullAirPct(unittest.TestCase):
    def test_from_fractions_matches_legacy_display_scale(self) -> None:
        self.assertAlmostEqual(statcast.pull_air_pct_from_fractions(0.4, 0.35, 0.20), 22.0, places=4)
        self.assertAlmostEqual(
            statcast.pull_air_pct_from_fractions(0.43, 0.36, 0.20),
            100.0 * 0.43 * 0.56,
            places=4,
        )

    def test_from_fractions_none_if_any_missing(self) -> None:
        self.assertIsNone(statcast.pull_air_pct_from_fractions(None, 0.3, 0.2))
        self.assertIsNone(statcast.pull_air_pct_from_fractions(0.4, None, 0.2))
        self.assertIsNone(statcast.pull_air_pct_from_fractions(0.4, 0.3, None))

    def test_statcast_summary_includes_pull_air_pct(self) -> None:
        pid = 12345
        batter_data = {
            pid: {
                "barrel_rate": 0.10,
                "exit_velocity_avg": 90.0,
                "hard_hit_pct": 0.45,
                "sweet_spot_pct": 0.35,
                "avg_launch_angle": 15.0,
                "xslg": 0.500,
                "fb_pct": 0.35,
                "gb_pct": 0.40,
                "ld_pct": 0.20,
                "pull_pct": 0.40,
                "oppo_pct": 0.20,
                "pa": 200,
                "season": 2026,
                "statcast_source": "current",
            }
        }
        s = statcast.statcast_summary(pid, batter_data)
        self.assertIn("pull_air_pct", s)
        self.assertAlmostEqual(s["pull_air_pct"], 22.0, places=4)
        self.assertEqual(s["pull_pct"], "40.0%")
        self.assertEqual(s["fb_pct"], "35.0%")
        self.assertEqual(s["ld_pct"], "20.0%")

    def test_pipeline_imports_after_change(self) -> None:
        import pipeline  # noqa: F401

    def test_app_py_compiles(self) -> None:
        import py_compile

        app_path = _ROOT / "app.py"
        py_compile.compile(str(app_path), doraise=True)


if __name__ == "__main__":
    unittest.main()
