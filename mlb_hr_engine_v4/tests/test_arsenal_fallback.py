"""
Regression tests for the Arsenal Edge / JIG arsenal-data source hardening
(retry -> legacy-validation -> pitch-level reconstruction -> DATA GAP).

Background incident: primary pitch-arsenal-stats endpoint returned HTTP 502;
the legacy wide-format CSV fallback then returned HTTP 200 with blank usage
columns, which _parse_arsenal_csv turned into {} — and {} was accepted as a
successful fallback, wiping AEE/JIG arsenal enrichment for the whole slate.
"""

import csv
import io
import unittest
from unittest import mock


class _Response:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self._text = text

    @property
    def content(self) -> bytes:
        return self._text.encode("utf-8-sig")

    @property
    def text(self) -> str:
        return self._text

    def raise_for_status(self) -> None:
        return None


def _primary_stats_csv(rows: list[dict]) -> str:
    fieldnames = [
        "player_id", "pitch_type", "pitch_usage", "run_value_per_100",
        "pa", "whiff_percent", "hard_hit_percent", "mph",
    ]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return out.getvalue()


def _valid_primary_csv_for(pid: int) -> str:
    return _primary_stats_csv([
        {
            "player_id": pid, "pitch_type": "FF", "pitch_usage": "55.0",
            "run_value_per_100": "-1.2", "pa": "120",
            "whiff_percent": "24.0", "hard_hit_percent": "38.0", "mph": "95.4",
        },
        {
            "player_id": pid, "pitch_type": "SL", "pitch_usage": "45.0",
            "run_value_per_100": "0.5", "pa": "90",
            "whiff_percent": "30.0", "hard_hit_percent": "32.0", "mph": "85.1",
        },
    ])


def _blank_legacy_csv() -> str:
    # HTTP 200, header present, all usage columns blank — the exact incident shape.
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["pitcher", "ff_pitcher", "sl_pitcher"])
    writer.writeheader()
    writer.writerow({"pitcher": "592779", "ff_pitcher": "", "sl_pitcher": ""})
    return out.getvalue()


class ArsenalPrimaryRetryTests(unittest.TestCase):
    """CASE 1 and CASE 2."""

    def setUp(self) -> None:
        from clients import arsenal
        self.arsenal = arsenal
        arsenal.clear_caches()

    def test_primary_success_no_fallback(self) -> None:
        arsenal = self.arsenal
        calls = []

        def fake_get(url, timeout=None, **kw):
            calls.append(url)
            return _Response(200, _valid_primary_csv_for(592779))

        with mock.patch.object(arsenal._SESSION, "get", side_effect=fake_get):
            result = arsenal.get_pitcher_arsenal(2026)

        self.assertEqual(len(calls), 1)
        self.assertIn(592779, result)
        self.assertEqual({p["pitch_type"] for p in result[592779]}, {"FF", "SL"})
        self.assertEqual(arsenal.get_arsenal_source(2026).get(592779), "primary")

    def test_primary_502_then_retry_success(self) -> None:
        arsenal = self.arsenal
        calls = []

        def fake_get(url, timeout=None, **kw):
            calls.append(url)
            if len(calls) == 1:
                return _Response(502, "")
            return _Response(200, _valid_primary_csv_for(592779))

        with mock.patch.object(arsenal._SESSION, "get", side_effect=fake_get):
            result = arsenal.get_pitcher_arsenal(2026)

        self.assertEqual(len(calls), 2, "expected exactly one retry")
        self.assertIn(592779, result)
        self.assertEqual(arsenal.get_arsenal_source(2026).get(592779), "primary")


class ArsenalLegacyFallbackValidationTests(unittest.TestCase):
    """CASE 3."""

    def setUp(self) -> None:
        from clients import arsenal
        self.arsenal = arsenal
        arsenal.clear_caches()

    def test_blank_legacy_fallback_is_rejected_not_accepted_as_success(self) -> None:
        arsenal = self.arsenal

        def fake_get(url, timeout=None, **kw):
            if "pitch-arsenal-stats" in url:
                return _Response(500, "")
            return _Response(200, _blank_legacy_csv())

        with mock.patch.object(arsenal._SESSION, "get", side_effect=fake_get):
            result = arsenal.get_pitcher_arsenal(2026)

        self.assertEqual(result, {})
        self.assertNotIn(2026, arsenal._ARSENAL_CACHE,
                          "a rejected fallback must not be cached as a successful year")


class ArsenalPitchLevelFallbackTests(unittest.TestCase):
    """CASE 4, CASE 5, CASE 6."""

    def setUp(self) -> None:
        from clients import arsenal
        self.arsenal = arsenal
        arsenal.clear_caches()

    def _always_failing_primary_and_legacy(self, url, timeout=None, **kw):
        if "pitch-arsenal-stats" in url:
            return _Response(500, "")
        return _Response(200, _blank_legacy_csv())

    def test_pitch_level_fallback_reconstructs_real_arsenal(self) -> None:
        arsenal = self.arsenal
        pitch_stats = {
            "FF": {"pa": 80, "pitch_pct": 0.6, "avg_speed": 96.0, "display_hh": 0.35,
                   "k_pct": 0.25, "hr_rate": 0.03},
            "SL": {"pa": 40, "pitch_pct": 0.4, "avg_speed": 85.0, "display_hh": 0.30,
                   "k_pct": 0.30, "hr_rate": 0.02},
        }
        with mock.patch.object(arsenal._SESSION, "get", side_effect=self._always_failing_primary_and_legacy), \
             mock.patch("clients.pitch_mix.get_pitcher_pitch_stats", return_value=pitch_stats), \
             mock.patch("clients.pitch_mix.get_pitcher_data_year", return_value=2026):
            result = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[592779])

        self.assertIn(592779, result)
        pitches = {p["pitch_type"]: p for p in result[592779]}
        self.assertEqual(set(pitches), {"FF", "SL"})
        self.assertEqual(pitches["FF"]["pitch_pct"], 0.6)
        self.assertEqual(pitches["FF"]["avg_speed"], 96.0)
        self.assertEqual(pitches["FF"]["hard_hit_pct"], 0.35)
        # Never fabricated — fields not derivable from pitch-level data stay None
        self.assertIsNone(pitches["FF"]["rv_per100"])
        self.assertIsNone(pitches["FF"]["whiff_pct"])
        self.assertEqual(arsenal.get_arsenal_source(2026).get(592779), "pitch_level_fallback")

    def test_single_pitcher_failure_does_not_wipe_slate(self) -> None:
        arsenal = self.arsenal

        def fake_pitch_stats(pid, side=""):
            if pid == 111:
                return {"FF": {"pa": 50, "pitch_pct": 1.0, "avg_speed": 94.0, "display_hh": 0.3}}
            return {}  # pid 222 has no usable pitch-level data

        with mock.patch.object(arsenal._SESSION, "get", side_effect=self._always_failing_primary_and_legacy), \
             mock.patch("clients.pitch_mix.get_pitcher_pitch_stats", side_effect=fake_pitch_stats), \
             mock.patch("clients.pitch_mix.get_pitcher_data_year", return_value=2026):
            result = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[111, 222])

        self.assertIn(111, result)
        self.assertNotIn(222, result)
        sources = arsenal.get_arsenal_source(2026)
        self.assertEqual(sources.get(111), "pitch_level_fallback")
        self.assertEqual(sources.get(222), "unavailable")

    def test_total_failure_stays_data_gap_no_fabrication(self) -> None:
        arsenal = self.arsenal
        with mock.patch.object(arsenal._SESSION, "get", side_effect=self._always_failing_primary_and_legacy), \
             mock.patch("clients.pitch_mix.get_pitcher_pitch_stats", return_value={}):
            result = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[999])

        self.assertNotIn(999, result)
        self.assertEqual(arsenal.get_arsenal_source(2026).get(999), "unavailable")


class ArsenalPrimaryRecoveryTests(unittest.TestCase):
    """
    Regression coverage for the cache-pinning gap found in the Stage 2B audit:
    a transient primary outage must not stay authoritative forever in a
    long-lived process (Fly API / Streamlit), and recovery must not require a
    process restart or season/year rollover.
    """

    def setUp(self) -> None:
        from clients import arsenal
        self.arsenal = arsenal
        arsenal.clear_caches()

    def test_pitch_level_fallback_self_heals_when_primary_recovers(self) -> None:
        """
        CALL 1: primary fails, legacy invalid, pitch-level fallback succeeds.
        CALL 2: primary is healthy again.
        Already correct pre-fix: total primary+legacy failure is never cached at
        the _ARSENAL_CACHE[year] level, so the next call re-attempts primary from
        scratch and its result always wins the merge over stale pitch-level data.
        This test proves that behavior rather than changing it.
        """
        arsenal = self.arsenal
        pid = 592779
        pitch_stats = {
            "FF": {"pa": 80, "pitch_pct": 0.6, "avg_speed": 96.0, "display_hh": 0.35},
        }
        always_failing = lambda url, timeout=None, **kw: (
            _Response(500, "") if "pitch-arsenal-stats" in url else _Response(200, _blank_legacy_csv())
        )

        with mock.patch.object(arsenal._SESSION, "get", side_effect=always_failing), \
             mock.patch("clients.pitch_mix.get_pitcher_pitch_stats", return_value=pitch_stats), \
             mock.patch("clients.pitch_mix.get_pitcher_data_year", return_value=2026):
            call1 = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[pid])

        self.assertIn(pid, call1)
        self.assertEqual(arsenal.get_arsenal_source(2026).get(pid), "pitch_level_fallback")
        self.assertNotIn(2026, arsenal._ARSENAL_CACHE)

        primary_now_healthy = lambda url, timeout=None, **kw: (
            _Response(200, _valid_primary_csv_for(pid)) if "pitch-arsenal-stats" in url else _Response(500, "")
        )
        with mock.patch.object(arsenal._SESSION, "get", side_effect=primary_now_healthy):
            call2 = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[pid])

        self.assertEqual(arsenal.get_arsenal_source(2026).get(pid), "primary")
        self.assertEqual({p["pitch_type"] for p in call2[pid]}, {"FF", "SL"})
        self.assertIsNotNone(call2[pid][0]["rv_per100"], "primary data must supersede fallback, not merge with it")

    def test_legacy_fallback_does_not_pin_cache_after_primary_recovers(self) -> None:
        """
        CALL 1: primary fails, legacy fallback SUCCEEDS with usable usage data.
        This is the case that previously pinned _ARSENAL_CACHE[year] forever,
        since a successful legacy fetch is cached at the year level with no
        retry path. CALL 2 (after the cooldown) must be able to promote back
        to primary without a process restart.
        """
        arsenal = self.arsenal
        pid = 592779
        usable_legacy_csv = (
            "pitcher,ff_pitcher,sl_pitcher\n"
            f"{pid},60,40\n"
        )
        primary_down_legacy_up = lambda url, timeout=None, **kw: (
            _Response(500, "") if "pitch-arsenal-stats" in url else _Response(200, usable_legacy_csv)
        )

        with mock.patch.object(arsenal._SESSION, "get", side_effect=primary_down_legacy_up):
            call1 = arsenal.get_pitcher_arsenal(2026)

        self.assertIn(pid, call1)
        self.assertEqual(arsenal.get_arsenal_source(2026).get(pid), "legacy_fallback")
        self.assertEqual(arsenal._ARSENAL_CACHE_SOURCE.get(2026), "legacy_fallback")
        self.assertIsNone(call1[pid][0]["rv_per100"], "legacy CSV has no rv_per100 — must not be fabricated")

        # Force the retry cooldown to have already elapsed (simulates the next
        # eligible call after primary recovery, without waiting on a real clock
        # or restarting the process).
        arsenal._ARSENAL_FALLBACK_RETRY_AFTER[2026] = 0.0

        primary_now_healthy = lambda url, timeout=None, **kw: (
            _Response(200, _valid_primary_csv_for(pid)) if "pitch-arsenal-stats" in url else _Response(500, "")
        )
        with mock.patch.object(arsenal._SESSION, "get", side_effect=primary_now_healthy):
            call2 = arsenal.get_pitcher_arsenal(2026)

        self.assertEqual(arsenal.get_arsenal_source(2026).get(pid), "primary")
        self.assertEqual(arsenal._ARSENAL_CACHE_SOURCE.get(2026), "primary")
        self.assertIsNotNone(call2[pid][0]["rv_per100"], "must be authoritative primary data, not stale legacy")

    def test_legacy_fallback_retry_is_cooldown_bounded_not_hammered(self) -> None:
        """A retry attempt must not fire on every single call while primary is
        still down — only after the cooldown window elapses."""
        arsenal = self.arsenal
        pid = 592779
        usable_legacy_csv = (
            "pitcher,ff_pitcher,sl_pitcher\n"
            f"{pid},60,40\n"
        )
        calls = []

        def primary_down_legacy_up(url, timeout=None, **kw):
            calls.append(url)
            return _Response(500, "") if "pitch-arsenal-stats" in url else _Response(200, usable_legacy_csv)

        with mock.patch.object(arsenal._SESSION, "get", side_effect=primary_down_legacy_up):
            arsenal.get_pitcher_arsenal(2026)
            calls_after_call1 = len(calls)
            arsenal.get_pitcher_arsenal(2026)  # cooldown not elapsed — must not retry primary again

        self.assertEqual(len(calls), calls_after_call1, "second call must not re-hit primary before cooldown elapses")


class ArsenalSameSeasonGuardTests(unittest.TestCase):
    """
    Stage 2C: same-season safety guard for the pitch-level Arsenal fallback.

    Background incident: pitch_mix.py's prior-season rollback (intentional for
    other pitch_mix consumers, e.g. IL stints / early-season returns) was being
    silently accepted by the Arsenal pitch-level fallback too, so a pitcher
    with no current-season Statcast rows (e.g. Emmanuel Clase, requested 2026)
    would reconstruct an arsenal from 2025 data and present it as a 2026
    Arsenal Edge fallback.
    """

    def setUp(self) -> None:
        from clients import arsenal
        self.arsenal = arsenal
        arsenal.clear_caches()

    def _always_failing_primary_and_legacy(self, url, timeout=None, **kw):
        if "pitch-arsenal-stats" in url:
            return _Response(500, "")
        return _Response(200, _blank_legacy_csv())

    def test_current_season_pitch_level_data_is_accepted(self) -> None:
        """CASE 1: requested 2026, pitch_mix resolves to 2026 -> accepted."""
        arsenal = self.arsenal
        pitch_stats = {
            "SL": {"pa": 40, "pitch_pct": 1.0, "avg_speed": 85.0, "display_hh": 0.30},
        }
        with mock.patch.object(arsenal._SESSION, "get", side_effect=self._always_failing_primary_and_legacy), \
             mock.patch("clients.pitch_mix.get_pitcher_pitch_stats", return_value=pitch_stats), \
             mock.patch("clients.pitch_mix.get_pitcher_data_year", return_value=2026):
            result = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[661403])

        self.assertIn(661403, result)
        self.assertEqual(arsenal.get_arsenal_source(2026).get(661403), "pitch_level_fallback")

    def test_prior_season_rollback_is_rejected_not_fabricated(self) -> None:
        """CASE 2: requested 2026, pitch_mix rolls back to 2025 -> rejected,
        stays unavailable, no fabricated arsenal (the Emmanuel Clase case)."""
        arsenal = self.arsenal
        pitch_stats = {
            "SL": {"pa": 40, "pitch_pct": 1.0, "avg_speed": 85.0, "display_hh": 0.30},
        }
        with mock.patch.object(arsenal._SESSION, "get", side_effect=self._always_failing_primary_and_legacy), \
             mock.patch("clients.pitch_mix.get_pitcher_pitch_stats", return_value=pitch_stats), \
             mock.patch("clients.pitch_mix.get_pitcher_data_year", return_value=2025):
            result = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[661403])

        self.assertNotIn(661403, result)
        self.assertEqual(arsenal.get_arsenal_source(2026).get(661403), "unavailable")

    def test_primary_recovers_with_requested_season_after_rejected_fallback(self) -> None:
        """CASE 3: after a rejected cross-season fallback, primary recovering
        with the requested season becomes authoritative — no restart required."""
        arsenal = self.arsenal
        pid = 661403
        pitch_stats = {
            "SL": {"pa": 40, "pitch_pct": 1.0, "avg_speed": 85.0, "display_hh": 0.30},
        }
        with mock.patch.object(arsenal._SESSION, "get", side_effect=self._always_failing_primary_and_legacy), \
             mock.patch("clients.pitch_mix.get_pitcher_pitch_stats", return_value=pitch_stats), \
             mock.patch("clients.pitch_mix.get_pitcher_data_year", return_value=2025):
            call1 = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[pid])

        self.assertNotIn(pid, call1)
        self.assertEqual(arsenal.get_arsenal_source(2026).get(pid), "unavailable")

        primary_now_healthy = lambda url, timeout=None, **kw: (
            _Response(200, _valid_primary_csv_for(pid)) if "pitch-arsenal-stats" in url else _Response(500, "")
        )
        with mock.patch.object(arsenal._SESSION, "get", side_effect=primary_now_healthy):
            call2 = arsenal.get_pitcher_arsenal(2026, pitcher_ids=[pid])

        self.assertIn(pid, call2)
        self.assertEqual(arsenal.get_arsenal_source(2026).get(pid), "primary")
        self.assertIsNotNone(call2[pid][0]["rv_per100"], "must be authoritative primary data")


if __name__ == "__main__":
    unittest.main()
