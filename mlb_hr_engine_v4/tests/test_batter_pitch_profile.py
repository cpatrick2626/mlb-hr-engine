import asyncio
import copy
import csv
import io
import unittest
from unittest import mock


class _BufferedCsvResponse:
    def __init__(self, body: bytes) -> None:
        self.content = body
        self.closed = False

    def raise_for_status(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


def _profile_csv(season: int) -> bytes:
    output = io.StringIO()
    fieldnames = [
        "pitch_type", "events", "p_throws", "game_year", "game_pk",
        "at_bat_number", "estimated_woba_using_speedangle", "launch_speed_angle",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for index in range(12):
        writer.writerow({
            "pitch_type": "FA" if index < 6 else "FF",
            "events": "field_out",
            "p_throws": "R",
            "game_year": season,
            "game_pk": 1,
            "at_bat_number": index + 1,
            "estimated_woba_using_speedangle": "0.400",
            "launch_speed_angle": "6" if index == 0 else "4" if index < 6 else "",
        })
    for index in range(4):
        writer.writerow({
            "pitch_type": "SV",
            "events": "field_out",
            "p_throws": "R",
            "game_year": season,
            "game_pk": 1,
            "at_bat_number": 100 + index,
            "estimated_woba_using_speedangle": "0.900",
            "launch_speed_angle": "6",
        })
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def _all_pitches_csv(season: int) -> bytes:
    output = io.StringIO()
    fieldnames = [
        "pitch_type", "description", "type", "p_throws", "game_year",
        "game_pk", "at_bat_number", "pitch_number",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for index in range(20):
        writer.writerow({
            "pitch_type": "FA" if index < 10 else "FF",
            "description": "swinging_strike" if index < 5 else "foul",
            "type": "S",
            "p_throws": "R",
            "game_year": season,
            "game_pk": 1,
            "at_bat_number": 200 + index,
            "pitch_number": 1,
        })
    for index in range(10):
        writer.writerow({
            "pitch_type": "SV",
            "description": "swinging_strike_blocked" if index < 5 else "hit_into_play",
            "type": "S" if index < 5 else "X",
            "p_throws": "R",
            "game_year": season,
            "game_pk": 1,
            "at_bat_number": 300 + index,
            "pitch_number": 1,
        })
    writer.writerow({
        "pitch_type": "FF", "description": "called_strike", "type": "S",
        "p_throws": "R", "game_year": season, "game_pk": 1,
        "at_bat_number": 999, "pitch_number": 1,
    })
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def _missing_metric_columns_csv(season: int) -> bytes:
    output = io.StringIO()
    fieldnames = [
        "pitch_type", "events", "p_throws", "game_year", "game_pk", "at_bat_number",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for index in range(12):
        writer.writerow({
            "pitch_type": "FF", "events": "field_out", "p_throws": "R",
            "game_year": season, "game_pk": 1, "at_bat_number": index + 1,
        })
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def _missing_whiff_columns_csv(season: int) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["pitch_type", "game_year"])
    writer.writeheader()
    writer.writerow({"pitch_type": "FF", "game_year": season})
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def _verdict_row(pitch_type: str, xwoba: float | None, pill: str) -> dict:
    return {"pitch_type": pitch_type, "xwoba": xwoba, "pill": pill}


class BatterPitchProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        from clients import batter_pitch_profile

        batter_pitch_profile._BATTER_PITCH_PROFILE_DISPLAY_CACHE.clear()
        batter_pitch_profile._BATTER_PITCH_PROFILE_DISPLAY_CACHE_TIME.clear()

    def test_display_cache_is_isolated_canonical_and_sample_gated(self) -> None:
        from clients import batter_pitch_profile

        pa_response = _BufferedCsvResponse(
            _profile_csv(batter_pitch_profile.config.CURRENT_SEASON),
        )
        all_pitches_response = _BufferedCsvResponse(
            _all_pitches_csv(batter_pitch_profile.config.CURRENT_SEASON),
        )

        with mock.patch.object(
            batter_pitch_profile._SESSION,
            "get",
            side_effect=[pa_response, all_pitches_response],
        ) as fetch:
            profile = batter_pitch_profile.get_batter_pitch_profile_display(77, "R")
            cached = batter_pitch_profile.get_batter_pitch_profile_display(77, "R")

        rows = {row["pitch_type"]: row for row in profile["rows"]}
        self.assertEqual(set(rows), {"FF", "ST"})
        self.assertEqual(rows["FF"]["xwoba"], 0.4)
        self.assertEqual(rows["FF"]["barrel_pct"], 16.7)
        self.assertEqual(rows["FF"]["whiff_pct"], 25.0)
        self.assertEqual(rows["FF"]["pill"], "EXPLOIT")
        self.assertFalse(rows["FF"]["pill_thin_sample"])
        self.assertEqual(rows["FF"]["damage"], 66.7)
        self.assertEqual(rows["FF"]["sample"]["swings"], 20)
        self.assertEqual(rows["FF"]["sample"]["whiffs"], 5)
        self.assertIsNone(rows["ST"]["xwoba"])
        self.assertIsNone(rows["ST"]["barrel_pct"])
        self.assertIsNone(rows["ST"]["whiff_pct"])
        self.assertEqual(rows["ST"]["pill"], "NEUTRAL")
        self.assertTrue(rows["ST"]["pill_thin_sample"])
        self.assertIsNone(rows["ST"]["damage"])
        self.assertEqual(rows["ST"]["availability"]["whiff_pct"], "Gap")
        self.assertEqual(profile["_meta"]["sample_policy"]["whiff_pct_min_swings"], 15)
        self.assertTrue(profile["_meta"]["columns_present"]["description"])
        self.assertEqual(cached["_meta"]["cache"], "hit")
        self.assertEqual(fetch.call_count, 2)
        self.assertIn("hfAB", fetch.call_args_list[0].kwargs["params"])
        self.assertNotIn("hfAB", fetch.call_args_list[1].kwargs["params"])
        self.assertTrue(pa_response.closed)
        self.assertTrue(all_pitches_response.closed)

    def test_missing_savant_columns_return_gaps_without_fabrication(self) -> None:
        from clients import batter_pitch_profile

        responses = [
            _BufferedCsvResponse(
                _missing_metric_columns_csv(batter_pitch_profile.config.CURRENT_SEASON),
            ),
            _BufferedCsvResponse(
                _missing_whiff_columns_csv(batter_pitch_profile.config.CURRENT_SEASON),
            ),
        ]
        with mock.patch.object(
            batter_pitch_profile._SESSION, "get", side_effect=responses,
        ):
            profile = batter_pitch_profile.get_batter_pitch_profile_display(78, "R")

        row = profile["rows"][0]
        self.assertIsNone(row["xwoba"])
        self.assertIsNone(row["barrel_pct"])
        self.assertIsNone(row["whiff_pct"])
        self.assertEqual(row["pill"], "NEUTRAL")
        self.assertTrue(row["pill_thin_sample"])
        self.assertIsNone(row["damage"])
        self.assertEqual(profile["_meta"]["availability"], {
            "xwoba": "Gap", "barrel_pct": "Gap", "whiff_pct": "Gap",
        })
        self.assertFalse(profile["_meta"]["columns_present"]["description"])

    def test_failed_fetch_does_not_poison_display_cache(self) -> None:
        from clients import batter_pitch_profile

        with mock.patch.object(
            batter_pitch_profile._SESSION, "get", side_effect=RuntimeError("fixture failure"),
        ):
            profile = batter_pitch_profile.get_batter_pitch_profile_display(79, "R")

        self.assertEqual(profile["rows"], [])
        self.assertEqual(profile["_meta"]["freshness"], "Gap")
        self.assertFalse(any(
            key[1] == 79
            for key in batter_pitch_profile._BATTER_PITCH_PROFILE_DISPLAY_CACHE
        ))

    def test_each_pitch_metric_has_an_independent_thin_sample_gate(self) -> None:
        from clients import batter_pitch_profile

        rows = {
            row["pitch_type"]: row
            for row in batter_pitch_profile._finalize(
                {
                    "FF": {
                        "pa_ending_events": 9, "xwoba_sum": 3.6, "xwoba_n": 9,
                        "contacts": 5, "barrels": 1,
                    },
                    "SL": {
                        "pa_ending_events": 10, "xwoba_sum": 4.0, "xwoba_n": 10,
                        "contacts": 4, "barrels": 1,
                    },
                    "CH": {
                        "pa_ending_events": 10, "xwoba_sum": 4.0, "xwoba_n": 10,
                        "contacts": 5, "barrels": 1,
                    },
                },
                {
                    "FF": {"swings": 15, "whiffs": 3},
                    "SL": {"swings": 15, "whiffs": 3},
                    "CH": {"swings": 14, "whiffs": 3},
                },
                pa_freshness="Live",
                whiff_freshness="Live",
            )
        }

        self.assertIsNone(rows["FF"]["xwoba"])
        self.assertIsNotNone(rows["FF"]["barrel_pct"])
        self.assertIsNotNone(rows["FF"]["whiff_pct"])
        self.assertIsNotNone(rows["SL"]["xwoba"])
        self.assertIsNone(rows["SL"]["barrel_pct"])
        self.assertIsNotNone(rows["SL"]["whiff_pct"])
        self.assertIsNotNone(rows["CH"]["xwoba"])
        self.assertIsNotNone(rows["CH"]["barrel_pct"])
        self.assertIsNone(rows["CH"]["whiff_pct"])

    def test_context_cache_is_dh_distinct_and_ttl_safe(self) -> None:
        from clients import batter_pitch_profile

        responses = [
            _BufferedCsvResponse(_profile_csv(batter_pitch_profile.config.CURRENT_SEASON)),
            _BufferedCsvResponse(_all_pitches_csv(batter_pitch_profile.config.CURRENT_SEASON)),
        ]
        with mock.patch.object(
            batter_pitch_profile._SESSION, "get", side_effect=responses,
        ) as fetch:
            first = batter_pitch_profile.get_batter_pitch_profile_display(
                80, "R", slate_date="2026-07-14", pitcher_id=91,
                game_pk=1001, batter_side="S",
            )
            second = batter_pitch_profile.get_batter_pitch_profile_display(
                80, "R", slate_date="2026-07-14", pitcher_id=92,
                game_pk=1002, batter_side="S",
            )

        matching_keys = [
            key for key in batter_pitch_profile._BATTER_PITCH_PROFILE_DISPLAY_CACHE
            if key[1] == 80 and key[5] == "R"
        ]
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual({key[3] for key in matching_keys}, {1001, 1002})
        self.assertEqual({key[2] for key in matching_keys}, {91, 92})
        self.assertEqual({key[4] for key in matching_keys}, {"L"})
        self.assertEqual(first["rows"], second["rows"])
        self.assertEqual(second["_meta"]["cache"], "hit")

        expired_key = next(key for key in matching_keys if key[3] == 1002)
        batter_pitch_profile._BATTER_PITCH_PROFILE_DISPLAY_CACHE_TIME[expired_key] = (
            batter_pitch_profile.time.monotonic()
            - batter_pitch_profile.DISPLAY_CACHE_TTL_SECONDS
            - 1
        )
        self.assertIsNone(batter_pitch_profile._display_cache_get(expired_key))

    def test_ratified_pills_and_xwoba_damage_scale(self) -> None:
        from clients import batter_pitch_profile

        def row(xwoba: float | None) -> tuple[str, bool, float | None]:
            pill, thin = batter_pitch_profile._pill_from_xwoba(xwoba)
            return pill, thin, batter_pitch_profile._damage_from_xwoba(xwoba)

        self.assertEqual(row(0.500), ("EXPLOIT", False, 100.0))
        self.assertEqual(row(0.380), ("EXPLOIT", False, 60.0))
        self.assertEqual(row(0.340), ("HUNT", False, 46.7))
        self.assertEqual(row(0.200), ("NEUTRAL", False, 0.0))
        self.assertEqual(row(None), ("NEUTRAL", True, None))

    def test_all_four_ratified_pitch_mix_verdicts_and_gap(self) -> None:
        from clients.batter_pitch_profile import pitch_mix_verdict_display

        deploy = pitch_mix_verdict_display(
            [_verdict_row("FF", 0.400, "EXPLOIT"), _verdict_row("SL", 0.300, "NEUTRAL")],
            [{"pitch_type": "FF", "pitch_pct": 0.35}, {"pitch_type": "SL", "pitch_pct": 0.25}],
        )
        watch = pitch_mix_verdict_display(
            [_verdict_row("FF", 0.400, "EXPLOIT"), _verdict_row("SI", 0.300, "NEUTRAL")],
            [{"pitch_type": "FF", "pitch_pct": 0.15}, {"pitch_type": "SI", "pitch_pct": 0.55}],
        )
        hold = pitch_mix_verdict_display(
            [_verdict_row("FF", 0.300, "NEUTRAL"), _verdict_row("SL", 0.320, "NEUTRAL")],
            [{"pitch_type": "FF", "usage": 18.0}, {"pitch_type": "SL", "usage": 17.0}],
        )
        scratch = pitch_mix_verdict_display(
            [_verdict_row("FF", 0.300, "NEUTRAL"), _verdict_row("SL", 0.330, "NEUTRAL")],
            [{"pitch_type": "FF", "pitch_pct": 0.60}, {"pitch_type": "SL", "pitch_pct": 0.40}],
        )
        gap = pitch_mix_verdict_display(
            [_verdict_row("FF", None, "NEUTRAL")],
            [{"pitch_type": "FF", "pitch_pct": 0.60}],
        )

        self.assertEqual(deploy["label"], "DEPLOY")
        self.assertEqual(deploy["exploit_pitches"][0]["pitch_type"], "FF")
        self.assertEqual(watch["label"], "WATCHLIST")
        self.assertEqual(hold["label"], "HOLD")
        self.assertEqual(scratch["label"], "SCRATCH")
        self.assertIsNone(gap["label"])
        self.assertEqual(gap["availability"], "Gap")

    def test_batter_detail_is_only_consumer_and_does_not_warm_scoring_caches(self) -> None:
        from api import main as api_main
        from clients import pitch_mix

        payload = {"date": "2026-07-14", "slate_cache": {"generated_at": "2026-07-14T12:00:00Z"}}
        player = {"player_id": 77, "pitcher_id": 88, "pitcher_hand": "R"}
        profile = {
            "rows": [{
                "pitch_type": "FF", "xwoba": 0.4, "barrel_pct": 16.7,
                "whiff_pct": 25.0, "pill": "EXPLOIT", "pill_thin_sample": False,
                "damage": 66.7,
                "sample": {
                    "pa_ending_events": 12, "xwoba_observations": 12,
                    "contacts": 6, "barrels": 1, "swings": 20, "whiffs": 5,
                },
                "availability": {
                    "xwoba": "Live", "barrel_pct": "Live", "whiff_pct": "Live",
                    "pill": "Live", "damage": "Live",
                },
            }],
            "_meta": {"source": "fixture", "freshness": "Live", "display_only": True},
        }
        cache_before = copy.deepcopy(pitch_mix._BATTER_PT_CACHE)
        arsenal_fixture = {
            88: [{"code": "FF", "usage": 45.0}],
        }

        with (
            mock.patch.object(
                api_main, "_cached_batter_context",
                return_value=(payload, player, {}, {}, "Live"),
            ),
            mock.patch.object(
                api_main, "get_batter_pitch_profile_display", return_value=profile,
            ) as get_profile,
            mock.patch.dict(
                api_main._PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE,
                arsenal_fixture,
                clear=True,
            ),
            mock.patch.object(
                api_main, "get_pitcher_arsenal",
                side_effect=AssertionError("detail endpoint must not warm arsenal cache"),
            ),
        ):
            arsenal_before = copy.deepcopy(
                api_main._PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE,
            )
            detail = asyncio.run(api_main.get_batter_detail(77, pitcher_id=88))
            self.assertEqual(
                api_main._PITCHER_DETAIL_ARSENAL_DISPLAY_CACHE,
                arsenal_before,
            )

        self.assertEqual(detail["pitch_profile"], profile)
        self.assertEqual(detail["pitch_mix_verdict"], "DEPLOY")
        self.assertEqual(detail["pitch_mix_exploit_pitches"][0]["pitch_type"], "FF")
        self.assertEqual(detail["pitch_mix_verdict_meta"]["availability"], "Live")
        self.assertEqual(pitch_mix._BATTER_PT_CACHE, cache_before)
        get_profile.assert_called_once_with(
            77,
            "R",
            slate_date="2026-07-14",
            pitcher_id=88,
            game_pk=0,
            batter_side="",
        )


if __name__ == "__main__":
    unittest.main()
