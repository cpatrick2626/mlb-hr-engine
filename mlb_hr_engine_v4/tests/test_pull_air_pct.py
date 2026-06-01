"""Canonical pull_air_pct on pipeline players (Statcast-derived, no HVY wiring yet)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from clients import pull_air, statcast


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


class TestPullAirResolver(unittest.TestCase):
    """Parity: resolver fallback matches _pf-style legacy; canonical wins when finite."""

    def test_fallback_pf_style_strings(self) -> None:
        p = {"pull_pct": "40.0%", "fb_pct": "35.0%", "ld_pct": "20.0%"}
        self.assertAlmostEqual(pull_air.resolve_pull_air_pct(p), 22.0, places=4)

    def test_canonical_preferred_over_mismatched_components(self) -> None:
        p = {
            "pull_air_pct": 21.5,
            "pull_pct": "99.0%",
            "fb_pct": "1.0%",
            "ld_pct": "0.0%",
        }
        self.assertAlmostEqual(pull_air.resolve_pull_air_pct(p), 21.5, places=4)

    def test_statcast_summary_pull_air_matches_resolver(self) -> None:
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
        player = {
            "pull_air_pct": s["pull_air_pct"],
            "pull_pct": s["pull_pct"],
            "fb_pct": s["fb_pct"],
            "ld_pct": s["ld_pct"],
        }
        self.assertAlmostEqual(pull_air.resolve_pull_air_pct(player), s["pull_air_pct"], places=4)

    def test_non_finite_canonical_falls_back(self) -> None:
        p = {
            "pull_air_pct": float("nan"),
            "pull_pct": "40.0%",
            "fb_pct": "35.0%",
            "ld_pct": "20.0%",
        }
        self.assertAlmostEqual(pull_air.resolve_pull_air_pct(p), 22.0, places=4)

    def test_none_canonical_uses_fallback(self) -> None:
        p = {"pull_air_pct": None, "pull_pct": "40.0%", "fb_pct": "35.0%", "ld_pct": "20.0%"}
        self.assertAlmostEqual(pull_air.resolve_pull_air_pct(p), 22.0, places=4)

    def test_bool_canonical_ignored(self) -> None:
        p = {"pull_air_pct": True, "pull_pct": "40.0%", "fb_pct": "35.0%", "ld_pct": "20.0%"}
        self.assertAlmostEqual(pull_air.resolve_pull_air_pct(p), 22.0, places=4)

    def test_parse_pct_display_matches_pf_semantics(self) -> None:
        self.assertEqual(pull_air.parse_pct_display(None, 0.0), 0.0)
        self.assertEqual(pull_air.parse_pct_display("--", 0.0), 0.0)
        self.assertAlmostEqual(pull_air.parse_pct_display("38.2%", 0.0), 38.2, places=4)

    def test_pitch_mix_imports(self) -> None:
        from clients import pitch_mix  # noqa: F401

    def test_compute_modifier_signal3_accepts_pipeline_display_strings(self) -> None:
        """Regression: Statcast summary strings must not raise str-float in contact_score."""
        from clients import pitch_mix

        player = {
            "park_factor": 1.0,
            "weather_factor": 1.0,
            "batter_side": "R",
            "pull_air_pct": 22.0,
            "pull_pct": "40.0%",
            "fb_pct": "35.0%",
            "ld_pct": "20.0%",
            "barrel_pct": "10.0%",
            "sweet_spot_pct": "35.0%",
            "exit_velo": "91.0",
        }
        m = pitch_mix._compute_modifier(player, [], {"R": {}, "L": {}}, {}, {})
        self.assertTrue(0.70 <= m <= 1.40)

    def test_canonical_pitcher_arsenal_falls_back_to_overall_split_metrics(self) -> None:
        from clients import pitch_mix

        arsenal_data = {
            99: [
                {"pitch_type": "FF", "pitch_pct": 0.55, "rv_per100": 1.2, "pa": 40, "whiff_pct": 0.24, "hard_hit_pct": 0.40},
                {"pitch_type": "SL", "pitch_pct": 0.45, "rv_per100": -0.4, "pa": 30, "whiff_pct": 0.31, "hard_hit_pct": 0.28},
            ]
        }
        split_stats = {
            "FF": {"pitch_pct": 0.60, "pa": 18, "avg_speed": 96.2, "k_pct": 0.22, "hr_rate": 0.0, "pitch_ba": 0.250, "pitch_slg": 0.410, "pitch_iso": 0.160, "display_hh": 0.33}
        }
        overall_stats = {
            "FF": {"pitch_pct": 0.56, "pa": 48, "avg_speed": 96.1, "k_pct": 0.24, "hr_rate": 0.021, "pitch_ba": 0.244, "pitch_slg": 0.401, "pitch_iso": 0.157, "display_hh": 0.35},
            "SL": {"pitch_pct": 0.44, "pa": 36, "avg_speed": 86.5, "k_pct": 0.38, "hr_rate": 0.0, "pitch_ba": 0.188, "pitch_slg": 0.250, "pitch_iso": 0.062, "display_hh": 0.22},
        }

        with mock.patch.object(pitch_mix, "get_pitcher_pitch_stats", side_effect=[split_stats, overall_stats]):
            rows = pitch_mix._build_pitcher_arsenal_canonical(99, arsenal_data, {}, "L")

        by_pitch = {row["pitch_type"]: row for row in rows}
        self.assertEqual(set(by_pitch), {"FF", "SL"})
        self.assertAlmostEqual(by_pitch["SL"]["pitch_ba"], 0.188, places=3)
        self.assertAlmostEqual(by_pitch["SL"]["pitch_slg"], 0.250, places=3)
        self.assertAlmostEqual(by_pitch["SL"]["hr_rate"], 0.0, places=3)

    def test_canonical_pitcher_arsenal_keeps_live_only_pitch_rows(self) -> None:
        from clients import pitch_mix

        arsenal_data = {
            99: [
                {"pitch_type": "FF", "pitch_pct": 0.70, "rv_per100": 0.8, "pa": 50, "whiff_pct": 0.22, "hard_hit_pct": 0.41},
            ]
        }
        split_stats = {
            "FF": {"pitch_pct": 0.62, "pa": 24, "avg_speed": 95.8, "k_pct": 0.21, "hr_rate": 0.042, "pitch_ba": 0.280, "pitch_slg": 0.520, "pitch_iso": 0.240, "display_hh": 0.41},
            "ST": {"pitch_pct": 0.38, "pa": 16, "avg_speed": 83.1, "k_pct": 0.34, "hr_rate": 0.0, "pitch_ba": 0.190, "pitch_slg": 0.240, "pitch_iso": 0.050, "display_hh": 0.25},
        }
        overall_stats = split_stats

        with mock.patch.object(pitch_mix, "get_pitcher_pitch_stats", side_effect=[split_stats, overall_stats]):
            rows = pitch_mix._build_pitcher_arsenal_canonical(99, arsenal_data, {}, "L")

        by_pitch = {row["pitch_type"]: row for row in rows}
        self.assertEqual(set(by_pitch), {"FF", "ST"})
        self.assertAlmostEqual(sum(row["pitch_pct"] for row in rows), 1.0, places=2)

    def test_canonical_batter_rows_resolve_aliases_once(self) -> None:
        from clients import pitch_mix

        pitcher_arsenal = [{"pitch_type": "ST", "pitch_pct": 0.35}, {"pitch_type": "FF", "pitch_pct": 0.65}]
        batter_vs = {
            "SV": {"pa": 7, "hr": 1, "hr_rate": 1 / 7, "ba": 0.286, "slg": 0.714, "k_pct": 0.143},
            "FF": {"pa": 10, "hr": 0, "hr_rate": 0.0, "ba": 0.300, "slg": 0.500, "k_pct": 0.200},
        }

        rows = pitch_mix._build_batter_rows(pitcher_arsenal, batter_vs)
        by_pitch = {row["pitch_type"]: row for row in rows}
        self.assertIn("ST", by_pitch)
        self.assertEqual(by_pitch["ST"]["hr"], 1)
        self.assertAlmostEqual(by_pitch["FF"]["hr_rate"], 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
