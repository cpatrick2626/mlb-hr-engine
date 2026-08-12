"""Unit tests for api.cron.should_pull_odds().

Verifies the guard returns the correct (bool, reason) for each scenario
without making any Odds API or MLB Stats API calls.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Stub heavyweight imports that cron.py pulls in at module level so the guard
# functions can be tested without the full project dependency stack.
_STUB_MODULES = [
    "pipeline", "rapidfuzz", "rapidfuzz.fuzz", "rapidfuzz.process",
    "tracking", "tracking.pnl", "tracking.adaptive_weights",
    "api.cache", "api.main", "api.auth",
]
for _m in _STUB_MODULES:
    if _m not in sys.modules:
        sys.modules[_m] = mock.MagicMock()

# Also stub dotenv so load_dotenv() is a no-op if not installed.
if "dotenv" not in sys.modules:
    sys.modules["dotenv"] = mock.MagicMock()

from api import cron


class TestShouldPullOdds(unittest.TestCase):
    """Guard logic: correct skip/pull decision per scenario."""

    DATE = "2026-08-11"

    # Night slate — first pitch 7 PM ET = 23:00 UTC, last pitch 10 PM ET = 02:00 UTC +1d
    NIGHT_FIRST = datetime(2026, 8, 11, 23, 0, tzinfo=timezone.utc)
    NIGHT_LAST  = datetime(2026, 8, 12,  2, 0, tzinfo=timezone.utc)

    # Day slate — first pitch noon ET = 16:00 UTC, last pitch 4 PM ET = 20:00 UTC
    DAY_FIRST = datetime(2026, 8, 11, 16, 0, tzinfo=timezone.utc)
    DAY_LAST  = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)

    def _run(
        self,
        now_utc: datetime,
        cache_age_min: float,
        times: list[datetime],
    ) -> tuple[bool, str]:
        """Exercise should_pull_odds() with mocked time, cache age, and game times."""
        with (
            mock.patch.object(cron, "_odds_cache_age_minutes", return_value=cache_age_min),
            mock.patch.object(cron, "_game_start_times_utc", return_value=times),
            mock.patch("api.cron.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = now_utc
            mock_dt.fromisoformat = datetime.fromisoformat  # not used here but safe
            return cron.should_pull_odds(self.DATE)

    # ── Scenario 1: 6 AM, night-game slate ────────────────────────────────────

    def test_6am_night_slate_skip(self):
        """6 AM ET (10:00 UTC), first pitch 23:00 UTC — 13 h away → skip (too early)."""
        now = datetime(2026, 8, 11, 10, 0, tzinfo=timezone.utc)
        pull, reason = self._run(now, float("inf"), [self.NIGHT_FIRST, self.NIGHT_LAST])
        self.assertFalse(pull)
        self.assertIn("too early", reason)

    # ── Scenario 2: 3 PM ET, night-game slate ─────────────────────────────────

    def test_3pm_night_slate_pull(self):
        """3 PM ET (19:00 UTC), first pitch 23:00 UTC — exactly 4 h window → pull."""
        now = datetime(2026, 8, 11, 19, 0, tzinfo=timezone.utc)
        pull, reason = self._run(now, float("inf"), [self.NIGHT_FIRST, self.NIGHT_LAST])
        self.assertTrue(pull)
        self.assertIn("within window", reason)

    # ── Scenario 3: 8 AM ET, day-game slate ───────────────────────────────────

    def test_8am_day_slate_pull(self):
        """8 AM ET (12:00 UTC), first pitch 16:00 UTC — exactly 4 h boundary → pull."""
        now = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
        pull, reason = self._run(now, float("inf"), [self.DAY_FIRST, self.DAY_LAST])
        self.assertTrue(pull)
        self.assertIn("within window", reason)

    # ── Scenario 4: post-last-game ────────────────────────────────────────────

    def test_post_last_game_skip(self):
        """06:00 UTC next day, last pitch 02:00 UTC — 4 h past window → skip."""
        now = datetime(2026, 8, 12, 6, 0, tzinfo=timezone.utc)
        pull, reason = self._run(now, float("inf"), [self.NIGHT_FIRST, self.NIGHT_LAST])
        self.assertFalse(pull)
        self.assertIn("all games done", reason)

    # ── Scenario 5: no games today ────────────────────────────────────────────

    def test_no_games_skip(self):
        """No game times returned from MLB Stats → skip."""
        now = datetime(2026, 8, 11, 19, 0, tzinfo=timezone.utc)
        pull, reason = self._run(now, float("inf"), [])
        self.assertFalse(pull)
        self.assertIn("no games", reason)

    # ── Scenario 6: cache still fresh ────────────────────────────────────────

    def test_fresh_cache_skip(self):
        """Cache age 20 min < 45 min TTL → skip regardless of game timing."""
        now = datetime(2026, 8, 11, 19, 0, tzinfo=timezone.utc)
        pull, reason = self._run(now, 20.0, [self.NIGHT_FIRST, self.NIGHT_LAST])
        self.assertFalse(pull)
        self.assertIn("cache fresh", reason)

    # ── Guard cost assertion ──────────────────────────────────────────────────

    def test_guard_reads_no_odds_api(self):
        """The guard never calls odds_api — get_hr_odds_all_games must not be invoked."""
        from clients import odds_api
        now = datetime(2026, 8, 11, 19, 0, tzinfo=timezone.utc)
        with (
            mock.patch.object(cron, "_odds_cache_age_minutes", return_value=float("inf")),
            mock.patch.object(cron, "_game_start_times_utc", return_value=[self.NIGHT_FIRST, self.NIGHT_LAST]),
            mock.patch("api.cron.datetime") as mock_dt,
            mock.patch.object(odds_api, "get_hr_odds_all_games") as mock_odds,
        ):
            mock_dt.now.return_value = now
            cron.should_pull_odds(self.DATE)
        mock_odds.assert_not_called()


if __name__ == "__main__":
    unittest.main()
