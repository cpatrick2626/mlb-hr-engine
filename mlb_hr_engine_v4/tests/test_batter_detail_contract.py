import asyncio
import copy
import unittest
from unittest import mock

from fastapi.testclient import TestClient


def _profile(*, live: bool) -> dict:
    from clients.batter_pitch_profile import empty_batter_pitch_profile_display

    if not live:
        return empty_batter_pitch_profile_display("R", reason="fixture_gap")
    return {
        "rows": [{
            "pitch_type": "FF", "xwoba": 0.4, "barrel_pct": 20.0,
            "whiff_pct": 25.0, "pill": "EXPLOIT", "pill_thin_sample": False,
            "damage": 66.7,
            "sample": {
                "pa_ending_events": 12, "xwoba_observations": 12,
                "contacts": 10, "barrels": 2, "swings": 20, "whiffs": 5,
            },
            "availability": {
                "xwoba": "Live", "barrel_pct": "Live", "whiff_pct": "Live",
                "pill": "Live", "damage": "Live",
            },
        }],
        "_meta": {
            "source": "fixture", "freshness": "Live",
            "availability": {
                "xwoba": "Live", "barrel_pct": "Live", "whiff_pct": "Live",
            },
            "pitcher_hand": "R", "season": 2026,
            "fetched_at": "2026-07-14T12:00:00Z", "cache": "miss",
            "columns_present": {
                "estimated_woba_using_speedangle": True,
                "launch_speed_angle": True, "description": True,
                "pitch_type": True, "p_throws": True,
            },
            "sample_policy": {
                "xwoba_min_observations": 10,
                "barrel_pct_min_contacts": 5,
                "whiff_pct_min_swings": 15,
            },
            "tactical_contract": {
                "exploit_xwoba_min": 0.38, "hunt_xwoba_min": 0.34,
                "top_usage_min_pct": 20.0,
                "damage_metric": "xwOBA-based damage",
                "damage_xwoba_range": [0.2, 0.5],
            },
            "units": {
                "xwoba": "rate", "barrel_pct": "percent",
                "whiff_pct": "percent", "damage": "0-100 xwOBA-based",
            },
            "reason": None,
            "display_only": True,
        },
    }


def _context(*, full: bool) -> tuple[dict, dict, dict, dict, str]:
    payload = {
        "date": "2026-07-14",
        "slate_cache": {"date": "2026-07-14", "generated_at": "2026-07-14T12:00:00Z"},
    }
    if not full:
        return payload, {"player_id": 77, "pitcher_id": 88, "pitcher_hand": "R"}, {}, {}, "Live"
    player = {
        "player_id": 77, "pitcher_id": 88, "game_pk": 1001,
        "pitcher_hand": "R", "batter_side": "S", "model_prob": 0.18,
        "hrprob_projected": 51.0, "model_prob_projected": 0.15,
        "season_hr": 20, "team_games_played": 90, "batting_avg": 0.275,
        "actual_slg": 0.5, "max_ev": 113.0, "exit_velo": 91.2,
        "hard_hit": 0.48, "barrel_pct": 0.16, "sweet_spot_pct": 0.37,
        "avg_launch_angle": 14.0, "pull_air_pct": 0.28, "xslg": 0.52,
        "xiso": 0.245, "vs_rhp_slg": 0.51, "vs_lhp_slg": 0.42,
        "pull_pct": 0.47, "center_pct": 0.33, "oppo_pct": 0.2,
        "squp": 0.31, "park_factor": 1.05, "weather_factor": 1.03,
        "weather": {"temp_f": 82, "wind_mph": 8, "humidity_pct": 60},
        "pitcher_hr9": 1.4, "pitcher_barrel_allowed": 0.09,
        "pitcher_vuln": "HIGH", "pitcher_days_rest": 4, "fatigue_factor": 1.02,
        "recent_form_games": [{"date": "2026-07-13", "hr": 1, "avg": 0.5, "slg": 1.25, "pa": 4}],
    }
    row = {
        "id": 77, "pitcher_id": 88, "game_pk": 1001, "hrprob": 62.0,
        "model_prob": 0.18, "tier": "APEX", "model_tier_rank": "APEX #1",
        "bbpct": 0.1, "arsenal_edge_score": 75,
        "arsenal_edge_label": "EDGE", "arsenal_edge_key_pitch": "FF",
        "arsenal_edge_confidence": "HIGH",
    }
    game = {"game_pk": 1001, "hrFactor": 1.05}
    return payload, player, row, game, "Live"


def _dict_shape(value):
    if isinstance(value, dict):
        return {key: _dict_shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return "value"
    return "value"


class BatterDetailContractTests(unittest.TestCase):
    def setUp(self) -> None:
        from api import main as api_main
        from clients import batter_pitch_profile

        api_main._PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE.clear()
        batter_pitch_profile._BATTER_PITCH_PROFILE_DISPLAY_CACHE.clear()
        batter_pitch_profile._BATTER_PITCH_PROFILE_DISPLAY_CACHE_TIME.clear()

    def test_full_degraded_partial_and_full_share_stable_contract(self) -> None:
        from api import main as api_main
        from clients import mlb_stats

        with (
            mock.patch.object(api_main, "get_picks", return_value=None),
            mock.patch.object(api_main, "get_latest_picks", side_effect=TimeoutError("down")),
            mock.patch.object(
                api_main, "get_batter_pitch_profile_display",
                return_value=_profile(live=False),
            ),
            mock.patch.dict(mlb_stats._GAME_LOG_CACHE, {}, clear=True),
            mock.patch.dict(mlb_stats._PITCHER_GAME_LOG_CACHE, {}, clear=True),
        ):
            degraded_response = TestClient(api_main.app).get(
                "/api/batter-detail",
                params={"batter_id": 77, "pitcher_id": 88, "game_pk": 1001},
            )
            self.assertEqual(degraded_response.status_code, 200)
            degraded = degraded_response.json()

        partial_context = _context(full=False)
        with (
            mock.patch.object(api_main, "_cached_batter_context", return_value=partial_context),
            mock.patch.object(
                api_main, "get_batter_pitch_profile_display",
                return_value=_profile(live=True),
            ),
            mock.patch.object(
                api_main, "pitch_mix_verdict_display",
                side_effect=TimeoutError("usage module failed"),
            ),
            mock.patch.dict(mlb_stats._GAME_LOG_CACHE, {}, clear=True),
            mock.patch.dict(mlb_stats._PITCHER_GAME_LOG_CACHE, {}, clear=True),
        ):
            partial = asyncio.run(api_main.get_batter_detail(77, pitcher_id=88))

        full_context = _context(full=True)
        batter_games = [{
            "date": "2026-07-13",
            "stat": {
                "atBats": 4, "homeRuns": 1, "hits": 2,
                "totalBases": 5, "plateAppearances": 4,
            },
        }]
        pitcher_games = [{
            "date": "2026-07-13",
            "stat": {
                "homeRuns": 1, "strikeOuts": 7,
                "inningsPitched": "6.0", "baseOnBalls": 2,
            },
        }]
        with (
            mock.patch.object(api_main, "_cached_batter_context", return_value=full_context),
            mock.patch.object(
                api_main, "get_batter_pitch_profile_display",
                return_value=_profile(live=True),
            ),
            mock.patch.dict(
                api_main._PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE,
                {88: [{"pitch_type": "FF", "usage": 45.0}]}, clear=True,
            ),
            mock.patch.dict(mlb_stats._GAME_LOG_CACHE, {77: batter_games}, clear=True),
            mock.patch.dict(mlb_stats._PITCHER_GAME_LOG_CACHE, {88: pitcher_games}, clear=True),
        ):
            full = asyncio.run(
                api_main.get_batter_detail(77, pitcher_id=88, game_pk=1001),
            )

        self.assertEqual(_dict_shape(degraded), _dict_shape(partial))
        self.assertEqual(_dict_shape(partial), _dict_shape(full))
        self.assertEqual(degraded["meta"]["freshness"], "Gap")
        for module in (
            "threat", "statcast", "splits", "discipline", "environment",
            "pitcher", "arsenal", "fatigue", "recent",
        ):
            self.assertTrue(all(
                value == "Gap"
                for value in degraded[module]["_meta"]["availability"].values()
            ))
        self.assertEqual(degraded["pitch_profile"]["_meta"]["freshness"], "Gap")
        self.assertEqual(degraded["pitch_mix_verdict_meta"]["availability"], "Gap")
        self.assertEqual(partial["pitch_profile"]["_meta"]["freshness"], "Live")
        self.assertEqual(partial["pitch_mix_verdict_meta"]["availability"], "Gap")
        self.assertEqual(full["pitch_mix_verdict"], "DEPLOY")
        self.assertEqual(full["recent"]["_meta"]["freshness"], "Live")

    def test_doubleheader_rows_resolve_by_game_without_collision(self) -> None:
        from api import main as api_main

        payload = {
            "date": "2026-07-14",
            "all_by_model": [
                {"player_id": 77, "pitcher_id": 91, "game_pk": 1001, "model_prob": 0.11},
                {"player_id": 77, "pitcher_id": 92, "game_pk": 1002, "model_prob": 0.22},
            ],
            "slate_cache": {
                "date": "2026-07-14", "generated_at": "2026-07-14T12:00:00Z",
                "leaderboard_rows": [
                    {"id": 77, "pitcher_id": 91, "game_pk": 1001, "hrprob": 41},
                    {"id": 77, "pitcher_id": 92, "game_pk": 1002, "hrprob": 58},
                ],
                "slate_games": [
                    {"game_pk": 1001, "hrFactor": 0.95},
                    {"game_pk": 1002, "hrFactor": 1.08},
                ],
            },
        }
        with mock.patch.object(api_main, "get_picks", return_value=payload):
            first = api_main._cached_batter_context(77, pitcher_id=91, game_pk=1001)
            second = api_main._cached_batter_context(77, pitcher_id=92, game_pk=1002)

        self.assertEqual(first[1]["model_prob"], 0.11)
        self.assertEqual(first[2]["hrprob"], 41)
        self.assertEqual(first[3]["game_pk"], 1001)
        self.assertEqual(second[1]["model_prob"], 0.22)
        self.assertEqual(second[2]["hrprob"], 58)
        self.assertEqual(second[3]["game_pk"], 1002)

    def test_module_failure_does_not_mutate_scoring_cache(self) -> None:
        from api import main as api_main
        from clients import mlb_stats, pitch_mix

        scoring_cache_before = copy.deepcopy(pitch_mix._BATTER_PT_CACHE)
        with (
            mock.patch.object(api_main, "_cached_batter_context", return_value=_context(full=True)),
            mock.patch.object(
                api_main, "get_batter_pitch_profile_display",
                side_effect=TimeoutError("Savant timeout"),
            ),
            mock.patch.dict(mlb_stats._GAME_LOG_CACHE, {77: "corrupt"}, clear=True),
            mock.patch.dict(mlb_stats._PITCHER_GAME_LOG_CACHE, {88: "corrupt"}, clear=True),
        ):
            detail = asyncio.run(api_main.get_batter_detail(77, pitcher_id=88, game_pk=1001))

        self.assertEqual(detail["threat"]["model_prob"], 0.18)
        self.assertEqual(detail["pitch_profile"]["_meta"]["freshness"], "Gap")
        # recent form now comes from slate (recent_form_games), not the game-log cache,
        # so a corrupt cache no longer produces a Gap — batter_recent is still valid.
        self.assertEqual(detail["recent"]["batter_games"], [
            {"date": "2026-07-13", "hr": 1, "avg": 0.5, "slg": 1.25, "pa": 4},
        ])
        self.assertEqual(pitch_mix._BATTER_PT_CACHE, scoring_cache_before)


if __name__ == "__main__":
    unittest.main()
