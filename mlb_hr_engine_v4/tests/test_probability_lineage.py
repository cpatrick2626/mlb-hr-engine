"""Descriptive MAIN probability-lineage regression tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engine import calibration
import config
if isinstance(sys.modules.get("tracking"), mock.Mock):
    for module_name in tuple(sys.modules):
        if module_name == "tracking" or module_name.startswith("tracking."):
            del sys.modules[module_name]
if isinstance(sys.modules.get("pipeline"), mock.Mock):
    del sys.modules["pipeline"]
import pipeline


def _legacy_apply_calibration(p: float, barrel_rate: float = 0.0) -> float:
    """Frozen pre-instrumentation reference copied from origin/main."""
    if not getattr(config, "CALIBRATION_ENABLED", False):
        return p

    method = getattr(config, "CALIBRATION_METHOD", "none")
    if method == "platt":
        if (
            getattr(config, "ELITE_PLATT_ENABLED", False)
            and barrel_rate
            >= getattr(config, "ELITE_PLATT_BARREL_THRESHOLD", 0.10)
        ):
            a = getattr(config, "ELITE_PLATT_A", 0.92)
            b = getattr(config, "ELITE_PLATT_B", -0.10)
        else:
            a = getattr(config, "CALIBRATION_PLATT_A", 1.0)
            b = getattr(config, "CALIBRATION_PLATT_B", 0.0)
        result = calibration.platt_scale(p, a, b)
    elif method == "isotonic":
        breakpoints = getattr(config, "CALIBRATION_ISOTONIC_BREAKPOINTS", [])
        values = getattr(config, "CALIBRATION_ISOTONIC_VALUES", [])
        result = calibration.isotonic_scale(p, breakpoints, values)
    else:
        return p

    maximum = getattr(config, "MAX_GAME_HR_PROB", 0.29)
    return round(min(maximum, max(0.001, result)), 4)


def _legacy_apply_warehouse_isotonic(p: float) -> float:
    """Frozen pre-instrumentation warehouse branch from origin/main."""
    if not getattr(config, "WAREHOUSE_ISOTONIC_ENABLED", False):
        return p
    curve = calibration._load_warehouse_curve()
    if not curve:
        return p
    result = calibration.isotonic_scale(
        p,
        curve["breakpoints"],
        curve["values"],
    )
    return round(max(0.001, min(1.0 - calibration._EPS, result)), 4)


class TestCalibrationLineage(unittest.TestCase):
    def test_standard_and_elite_traces_preserve_golden_outputs(self) -> None:
        cases = [
            (0.0300, 0.0500, 0.0401, "PLATT_STANDARD", 0.7805, -0.4611),
            (0.1000, 0.0999, 0.1019, "PLATT_STANDARD", 0.7805, -0.4611),
            (0.1000, 0.1000, 0.1070, "PLATT_ELITE", 0.92, -0.10),
            (0.1750, 0.1200, 0.1785, "PLATT_ELITE", 0.92, -0.10),
            (0.2900, 0.2000, 0.2842, "PLATT_ELITE", 0.92, -0.10),
        ]

        for probability, barrel_rate, expected, branch, expected_a, expected_b in cases:
            with self.subTest(probability=probability, barrel_rate=barrel_rate):
                trace: dict = {}
                actual = calibration.apply_calibration(
                    probability,
                    barrel_rate=barrel_rate,
                    lineage=trace,
                )

                self.assertEqual(actual, expected)
                self.assertEqual(trace["calibration_branch"], branch)
                self.assertEqual(trace["calibration_barrel_rate"], barrel_rate)
                self.assertEqual(trace["elite_barrel_threshold"], 0.10)
                self.assertEqual(trace["elite_threshold_met"], branch == "PLATT_ELITE")
                self.assertEqual(trace["platt_a"], expected_a)
                self.assertEqual(trace["platt_b"], expected_b)


class TestMainProbabilityChainLineage(unittest.TestCase):
    def test_scale_variants_preserve_golden_final_probabilities(self) -> None:
        cases = [
            (1.00, 0.0300, 0.0500, 0.0300, 0.0401, "PLATT_STANDARD"),
            (1.00, 0.1000, 0.1000, 0.1000, 0.1070, "PLATT_ELITE"),
            (1.12, 0.0300, 0.0500, 0.0336, 0.0438, "PLATT_STANDARD"),
            (1.12, 0.1000, 0.1000, 0.1120, 0.1187, "PLATT_ELITE"),
            (1.12, 0.2900, 0.2000, 0.2900, 0.2842, "PLATT_ELITE"),
        ]

        for scale, pre_scale, barrel_rate, post_scale, expected, branch in cases:
            with self.subTest(scale=scale, pre_scale=pre_scale, barrel_rate=barrel_rate):
                runtime = {
                    "schema_version": 1,
                    "effective_prob_scale": scale,
                    "warehouse_isotonic_enabled": False,
                    "source_lane": "test",
                }
                with mock.patch.object(
                    pipeline._aw,
                    "get",
                    side_effect=lambda key, default=None: (
                        scale if key == "prob_scale" else default
                    ),
                ):
                    actual, lineage = pipeline._apply_main_probability_adjustments(
                        pre_scale,
                        barrel_rate=barrel_rate,
                        runtime_provenance=runtime,
                    )

                self.assertEqual(actual, expected)
                self.assertEqual(lineage["pre_scale_model_prob"], pre_scale)
                self.assertEqual(
                    lineage["post_scale_pre_calibration_prob"], post_scale
                )
                self.assertEqual(lineage["calibration_branch"], branch)
                self.assertEqual(lineage["post_platt_prob"], expected)
                self.assertEqual(lineage["final_model_prob"], expected)
                self.assertEqual(
                    lineage["adaptive_apply_status"],
                    "IDENTITY" if scale == 1.0 else "APPLIED",
                )
                self.assertEqual(
                    lineage["warehouse_isotonic_status"],
                    "DISABLED",
                )

    def test_instrumented_chain_is_bit_for_bit_equal_to_legacy_chain(self) -> None:
        probabilities = [index / 1000 for index in range(1, 291)]
        barrel_rates = [0.0, 0.0999, 0.10, 0.20]

        for scale in (1.0, 1.12):
            runtime = {
                "schema_version": 1,
                "effective_prob_scale": scale,
                "warehouse_isotonic_enabled": False,
            }
            with mock.patch.object(
                pipeline._aw,
                "get",
                side_effect=lambda key, default=None: (
                    scale if key == "prob_scale" else default
                ),
            ):
                for probability in probabilities:
                    for barrel_rate in barrel_rates:
                        legacy = round(
                            pipeline._aw.apply_prob_scale(probability), 4
                        )
                        legacy = round(
                            _legacy_apply_calibration(
                                legacy,
                                barrel_rate=barrel_rate,
                            ),
                            4,
                        )
                        legacy = _legacy_apply_warehouse_isotonic(legacy)

                        instrumented, lineage = (
                            pipeline._apply_main_probability_adjustments(
                                probability,
                                barrel_rate=barrel_rate,
                                runtime_provenance=runtime,
                            )
                        )

                        self.assertEqual(instrumented.hex(), legacy.hex())
                        self.assertEqual(
                            lineage["final_model_prob"].hex(), legacy.hex()
                        )


class TestLineageCollectionContainment(unittest.TestCase):
    def _load_one_profile(self, *, game_pk, provenance_error=False):
        captured = []
        game = {
            "home_team": "HOME", "away_team": "AWAY",
            "home_lineup": [{"id": 7, "name": "Player"}],
            "away_lineup": [], "home_pitcher": {}, "away_pitcher": {},
            "game_pk": game_pk,
        }

        def build_profile(*_args, **kwargs):
            probability, _ = pipeline._apply_main_probability_adjustments(
                0.1,
                barrel_rate=0.1,
                runtime_provenance=kwargs["probability_runtime_provenance"],
            )
            return {
                "player_id": 7, "player_name": "Player", "team": "HOME",
                "model_prob": probability, "confidence": 1,
                "statcast_source": "none",
            }

        patches = [
            mock.patch.object(pipeline.mlb_stats, "clear_game_log_caches"),
            mock.patch.object(pipeline.mlb_stats, "get_today_schedule", return_value=[game]),
            mock.patch.object(pipeline.odds_api, "get_hr_odds_all_games", return_value=([], "none", {})),
            mock.patch.object(pipeline.statcast_client, "get_batter_statcast", return_value={}),
            mock.patch.object(pipeline.statcast_client, "get_pitcher_statcast", return_value={}),
            mock.patch.object(pipeline.mlb_stats, "bulk_fetch_player_stats", return_value={}),
            mock.patch.object(pipeline.mlb_stats, "bulk_fetch_pitcher_stats", return_value={}),
            mock.patch.object(pipeline.statcast_client, "get_bat_tracking", return_value={}),
            mock.patch.object(pipeline, "_fetch_typical_slots", return_value={}),
            mock.patch.object(pipeline, "get_park", return_value={"lat": 0, "lon": 0, "tz_offset": 0}),
            mock.patch.object(pipeline.weather_client, "get_game_weather", return_value={}),
            mock.patch.object(pipeline.weather_client, "display_weather_fields", return_value={}),
            mock.patch.object(pipeline, "_build_player_profile", side_effect=build_profile),
            mock.patch.object(pipeline, "_build_odds_lookup", return_value=({}, set())),
            mock.patch.object(pipeline, "_build_fd_link_map", return_value={}),
            mock.patch.object(pipeline, "_match_odds"),
            mock.patch.object(pipeline, "_enrich_with_ev", side_effect=lambda player: player),
            mock.patch.object(pipeline, "_attach_fd_links"),
            mock.patch.object(pipeline.filters, "apply_filters", return_value=(False, [])),
            mock.patch.object(pipeline.filters, "soft_flags", return_value=[]),
            mock.patch.object(pipeline.ranker, "rank_picks", return_value=[]),
            mock.patch.object(pipeline.ranker, "rank_all_by_model", return_value=[]),
            mock.patch.object(pipeline.ranker, "confidence_tier", return_value="C"),
            mock.patch.object(pipeline.ranker, "composite_score", return_value=0),
            mock.patch.object(pipeline.ranker, "rank_within_tiers"),
            mock.patch.object(pipeline.parlay_engine, "build_auto_parlays", return_value=[]),
            mock.patch.object(pipeline, "build_profile_parlays", return_value=[]),
            mock.patch.object(pipeline, "_schedule_batter_stat_history_capture", side_effect=lambda _date, _players, lineage: captured.append(lineage)),
        ]
        if provenance_error:
            patches.append(mock.patch.object(
                pipeline, "_build_runtime_provenance", side_effect=RuntimeError("test provenance failure")
            ))

        with __import__("contextlib").ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            result = pipeline.load_game_data(target_date="2026-09-21")
        return result, captured

    def test_missing_game_pk_keeps_profile_and_skips_lineage_key(self) -> None:
        with self.assertLogs("pipeline", level="WARNING") as logs:
            result, captured = self._load_one_profile(game_pk=None)

        self.assertEqual(len(result["all_players"]), 1)
        self.assertIsNone(result["all_players"][0]["game_pk"])
        self.assertEqual(captured, [{}])
        self.assertIn("skipped unkeyable player", "\n".join(logs.output))

    def test_provenance_failure_keeps_probability_and_skips_lineage_capture(self) -> None:
        expected, _ = pipeline._apply_main_probability_adjustments(
            0.1, barrel_rate=0.1, runtime_provenance={}
        )
        with self.assertLogs("pipeline", level="WARNING") as logs:
            result, captured = self._load_one_profile(
                game_pk=100, provenance_error=True
            )

        self.assertEqual(result["all_players"][0]["model_prob"].hex(), expected.hex())
        self.assertEqual(captured, [{}])
        self.assertIn("runtime provenance unavailable", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
