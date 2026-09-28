"""Regression tests: pitcher game log includes postseason appearances.

The MLB Stats API gameLog endpoint defaults to gameType=R, so October
appearances were invisible to days-rest and recent pitcher form. The fake API
below honors the gameType request parameter the same way the live API does
(default R), so each test exercises the real request semantics without
touching the network.
"""

import re
import unittest
from unittest import mock

import config
from clients import mlb_stats
from engine import probability as prob

PID = 4242
ALLOWED = ("R", "F", "D", "L", "W")


def _row(date, game_type, gs, ip="6.0", hr=0, pk=None, bf=24, k=6):
    return {
        "date": date,
        "gameType": game_type,
        "game": {"gamePk": pk or int(date.replace("-", ""))},
        "stat": {
            "gamesStarted": gs, "inningsPitched": ip, "homeRuns": hr,
            "battersFaced": bf, "strikeOuts": k, "groundOuts": 5,
            "airOuts": 5, "baseOnBalls": 2,
        },
    }


class _FakeApi:
    """Mimics /people/{id}/stats and /people?hydrate= gameType filtering."""

    def __init__(self, rows_by_pid, season_by_pid=None):
        self.rows_by_pid = rows_by_pid
        self.season_by_pid = season_by_pid or {}
        self.calls = []

    def _filter(self, rows, game_types):
        return [r for r in rows if r["gameType"] in game_types]

    def __call__(self, path, params=None):
        params = params or {}
        self.calls.append((path, dict(params)))
        m = re.fullmatch(r"/people/(\d+)/stats", path)
        if m:
            types = params.get("gameType", "R").split(",")
            rows = self._filter(self.rows_by_pid.get(int(m.group(1)), []), types)
            return {"stats": [{"type": {"displayName": "gameLog"}, "splits": rows}]}
        if path == "/people":
            hydrate = params["hydrate"]
            gt = re.search(r"gameType=\[([^\]]*)\]", hydrate)
            types = gt.group(1).split(",") if gt else ["R"]
            people = []
            for pid_s in params["personIds"].split(","):
                pid = int(pid_s)
                stats = []
                if "season" in re.search(r"type=\[([^\]]*)\]", hydrate).group(1).split(","):
                    stats.append({"type": {"displayName": "season"},
                                  "splits": [{"stat": self.season_by_pid.get(pid, {})}]})
                if "gameLog" in hydrate:
                    stats.append({"type": {"displayName": "gameLog"},
                                  "splits": self._filter(self.rows_by_pid.get(pid, []), types)})
                people.append({"id": pid, "stats": stats})
            return {"people": people}
        raise AssertionError(f"unexpected path {path}")


class _Base(unittest.TestCase):
    target_date = "2025-10-10"

    def setUp(self):
        patches = [
            mock.patch.dict(mlb_stats._PITCHER_GAME_LOG_CACHE, {}, clear=True),
            mock.patch.dict(mlb_stats._PITCHER_GAME_LOG_CACHE_TS, {}, clear=True),
            mock.patch.dict(mlb_stats._BULK_PITCHER_STATS_CACHE, {}, clear=True),
            mock.patch.object(config, "TARGET_DATE", self.target_date),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def use_api(self, rows, season=None):
        api = _FakeApi({PID: rows}, {PID: season or {}})
        p = mock.patch.object(mlb_stats, "_get", side_effect=api)
        p.start()
        self.addCleanup(p.stop)
        return api

    @staticmethod
    def legacy_rest(rows, today):
        """Pre-fix behaviour: R-only log, newest row drives rest."""
        from datetime import date
        r_rows = sorted((r for r in rows if r["gameType"] == "R"),
                        key=lambda s: s["date"], reverse=True)
        if not r_rows:
            return 5
        return (date.fromisoformat(today) - date.fromisoformat(r_rows[0]["date"])).days


class RegularSeasonUnchangedTests(_Base):
    target_date = "2025-09-20"

    def test_regular_season_history_rest_and_recent_inputs_unchanged(self):
        rows = [_row(f"2025-08-{d:02d}", "R", 1, hr=d % 3) for d in (1, 7, 13, 19, 25, 31)]
        rows.append(_row("2025-09-06", "R", 0, ip="1.0"))  # relief outing, regular season
        rows.append(_row("2025-09-15", "R", 1, hr=2))
        self.use_api(rows)

        history = mlb_stats._pitcher_game_log_splits(PID)
        legacy = sorted(rows, key=lambda s: s["date"], reverse=True)
        self.assertEqual(history, legacy)
        self.assertEqual(mlb_stats.get_pitcher_days_rest(PID), 5)
        self.assertEqual(mlb_stats.get_pitcher_days_rest(PID),
                         self.legacy_rest(rows, self.target_date))
        self.assertEqual(mlb_stats.get_pitcher_recent_stats(PID),
                         mlb_stats._acc_pitching(legacy[:config.PITCHER_RECENT_GAMES]))


class PostseasonAppearanceTests(_Base):
    def test_wild_card_appearance_is_newer_and_drives_rest(self):
        rows = [_row("2025-09-27", "R", 1), _row("2025-10-01", "F", 1)]
        self.use_api(rows)
        with mock.patch.object(config, "TARGET_DATE", "2025-10-06"):
            self.assertEqual(mlb_stats._pitcher_game_log_splits(PID)[0]["gameType"], "F")
            self.assertEqual(mlb_stats.get_pitcher_days_rest(PID), 5)
        self.assertEqual(self.legacy_rest(rows, "2025-10-06"), 9)

    def test_relief_outing_before_postseason_start_counts_for_rest(self):
        rows = [
            _row("2025-09-28", "R", 1),
            _row("2025-10-04", "D", 1),
            _row("2025-10-07", "D", 0, ip="1.1", bf=5),   # relief
        ]
        self.use_api(rows)
        # Next start 2025-10-09: the relief outing two days earlier is the latest appearance.
        self.assertEqual(mlb_stats.get_pitcher_days_rest_as_of(PID, "2025-10-09"), 2)
        with mock.patch.object(config, "TARGET_DATE", "2025-10-09"):
            self.assertEqual(mlb_stats.get_pitcher_days_rest(PID), 2)
        self.assertEqual(self.legacy_rest(rows, "2025-10-09"), 11)
        self.assertEqual(prob.pitcher_fatigue_factor(2), 1.08)


class MultipleRoundsTests(_Base):
    def test_all_postseason_rounds_kept_in_order_without_duplicates(self):
        rows = [
            _row("2025-10-26", "W", 1),
            _row("2025-09-27", "R", 1),
            _row("2025-10-13", "L", 1),
            _row("2025-09-30", "F", 1),
            _row("2025-10-06", "D", 1),
        ]
        self.use_api(rows)
        history = mlb_stats._pitcher_game_log_splits(PID)
        self.assertEqual([r["gameType"] for r in history], ["W", "L", "D", "F", "R"])
        self.assertEqual([r["date"] for r in history], sorted((r["date"] for r in rows), reverse=True))
        pks = [r["game"]["gamePk"] for r in history]
        self.assertEqual(len(pks), len(set(pks)))
        self.assertEqual(len(history), 5)


class OtherGameTypesExcludedTests(_Base):
    def test_request_asks_only_for_allowed_game_types(self):
        api = self.use_api([_row("2025-09-27", "R", 1)])
        mlb_stats._pitcher_game_log_splits(PID)
        (_, params), = api.calls
        self.assertEqual(params["gameType"], "R,F,D,L,W")

    def test_spring_exhibition_allstar_rows_never_enter_history(self):
        rows = [
            _row("2025-03-10", "S", 1), _row("2025-03-25", "E", 1),
            _row("2025-07-15", "A", 0), _row("2025-10-02", "P", 1),
            _row("2025-09-27", "R", 1), _row("2025-10-01", "F", 1),
        ]
        # Simulate an API that ignores the gameType filter entirely.
        leaky = {"stats": [{"splits": rows}]}
        with mock.patch.object(mlb_stats, "_get", return_value=leaky):
            history = mlb_stats._pitcher_game_log_splits(PID)
        self.assertEqual({r["gameType"] for r in history}, {"R", "F"})


class RecentFormTests(_Base):
    def test_recent_window_includes_postseason_with_same_size_and_formula(self):
        rows = [
            _row("2025-09-10", "R", 1, ip="7.0", hr=0),
            _row("2025-09-16", "R", 1, ip="6.0", hr=0),
            _row("2025-09-22", "R", 1, ip="6.0", hr=0),
            _row("2025-09-28", "R", 1, ip="6.0", hr=0),
            _row("2025-10-01", "F", 1, ip="5.0", hr=2),
            _row("2025-10-06", "D", 0, ip="1.0", hr=1, bf=5),
            _row("2025-10-09", "D", 1, ip="6.0", hr=1),
        ]
        self.use_api(rows)
        recent = mlb_stats.get_pitcher_recent_stats(PID)
        newest = sorted(rows, key=lambda s: s["date"], reverse=True)[:config.PITCHER_RECENT_GAMES]
        self.assertEqual(recent, mlb_stats._acc_pitching(newest))
        self.assertEqual(recent["homeRuns"], 4)
        self.assertAlmostEqual(recent["inningsPitched"], 24.0)

        legacy_newest = [r for r in sorted(rows, key=lambda s: s["date"], reverse=True)
                         if r["gameType"] == "R"][:config.PITCHER_RECENT_GAMES]
        legacy = mlb_stats._acc_pitching(legacy_newest)
        # Same formula, different (corrected) input.
        self.assertEqual(prob.pitcher_recent_factor(legacy), 0.864)
        self.assertEqual(prob.pitcher_recent_factor(recent), 1.055)

        as_of = mlb_stats.get_pitcher_recent_stats_as_of(PID, "2025-10-09")
        self.assertEqual(as_of, mlb_stats._acc_pitching(
            [r for r in sorted(rows, key=lambda s: s["date"], reverse=True)
             if r["date"] < "2025-10-09"][:config.PITCHER_RECENT_GAMES]))

    def test_backtest_season_proxy_stays_regular_season_only(self):
        rows = [_row("2025-09-28", "R", 1, hr=1), _row("2025-10-01", "F", 1, hr=3)]
        self.use_api(rows)
        season = mlb_stats.get_pitcher_stats_as_of(PID, "2025-10-09")
        self.assertEqual(season, mlb_stats._acc_pitching([rows[0]]))


class CacheSafetyTests(_Base):
    def test_run_reset_and_bulk_fetch_replace_r_only_cache(self):
        rows = [_row("2025-09-27", "R", 1), _row("2025-10-07", "D", 0, ip="1.0")]
        season = {"homeRuns": 20, "inningsPitched": "180.0"}
        api = self.use_api(rows, season)
        # Stale, fresh-looking R-only entry left by pre-fix code.
        mlb_stats._PITCHER_GAME_LOG_CACHE[PID] = [rows[0]]
        mlb_stats._PITCHER_GAME_LOG_CACHE_TS[PID] = 9e18

        mlb_stats.clear_game_log_caches()        # pipeline does this first
        mlb_stats.bulk_fetch_pitcher_stats({PID})

        self.assertEqual([r["gameType"] for r in mlb_stats._PITCHER_GAME_LOG_CACHE[PID]], ["D", "R"])
        self.assertEqual(mlb_stats.get_pitcher_days_rest(PID), 3)
        self.assertEqual(mlb_stats._BULK_PITCHER_STATS_CACHE[PID], season)
        hydrates = [p["hydrate"] for path, p in api.calls if path == "/people"]
        self.assertEqual(len(hydrates), 2)
        self.assertNotIn("gameType", hydrates[0])            # season totals unchanged
        self.assertIn("gameType=[R,F,D,L,W]", hydrates[1])  # log is postseason-aware
        # The bulk path wrote the log, so the per-pitcher fetch was never needed.
        self.assertFalse(any(path.endswith("/stats") for path, _ in api.calls))

    def test_individual_fetch_after_reset_sees_postseason(self):
        rows = [_row("2025-09-27", "R", 1), _row("2025-10-07", "D", 1)]
        self.use_api(rows)
        mlb_stats._PITCHER_GAME_LOG_CACHE[PID] = [rows[0]]
        mlb_stats._PITCHER_GAME_LOG_CACHE_TS[PID] = 9e18
        mlb_stats.clear_game_log_caches()
        self.assertEqual(mlb_stats.get_pitcher_days_rest(PID), 3)


if __name__ == "__main__":
    unittest.main()
