#!/usr/bin/env python3
"""
Standalone pipeline runner — called by GitHub Actions cron (and optionally local dev).

Usage:
  python -m api.cron              # run for today
  python -m api.cron 2026-05-12  # run for a specific date

GitHub Actions sets ODDS_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY as secrets.
Locally, these are read from .env via python-dotenv.
"""

import sys
import os
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Support running as a module from mlb_hr_engine_v4/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pipeline import load_game_data, serializable, schedule_jig_stat_capture
from api.cache import store_picks, insert_picks, today_et

MODEL_VERSION = "v4"


# ── Odds skip-guard ────────────────────────────────────────────────────────────
# Gate the Odds API pull at zero odds-API cost. Game times come from the free
# MLB Stats API. All comparisons are in UTC so DST is self-calibrating.

# Must match clients/odds_api._CACHE_PATH and CACHE_TTL_MINUTES exactly.
_ODDS_CACHE_PATH         = Path(__file__).parent.parent / "data" / "odds_cache.json"
_ODDS_CACHE_TTL_MINUTES  = 45   # mirrors odds_api.CACHE_TTL_MINUTES
_PULL_WINDOW_H_BEFORE    = 4    # open the window this many hours before first pitch
_PULL_WINDOW_H_AFTER     = 3    # close the window this many hours after last first pitch


def _odds_cache_age_minutes() -> float:
    """Age of the odds disk cache in minutes; infinity when missing or unreadable."""
    try:
        with open(_ODDS_CACHE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return (time.time() - data["timestamp"]) / 60
    except Exception:
        return float("inf")


def _game_start_times_utc(target_date: str) -> list[datetime]:
    """
    Return UTC start datetimes for today's games from the MLB Stats API.
    FREE — no Odds API call. Returns [] on error or when times are unavailable.
    """
    try:
        from clients import mlb_stats
        games = mlb_stats.get_today_schedule(target_date)
        times: list[datetime] = []
        for g in games:
            ts = g.get("game_time_utc", "")
            if not ts:
                continue
            try:
                times.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except ValueError:
                pass
        return times
    except Exception as exc:
        logger.warning("[odds_guard] schedule fetch failed: %s", exc)
        return []


def should_pull_odds(target_date: str) -> tuple[bool, str]:
    """
    Return (should_pull, reason). Costs zero Odds API requests — game times
    come from the free MLB Stats API (no key required).

    Pulls only when ALL conditions hold:
      1. Odds cache is stale (age > 45 min)
      2. Current UTC >= first pitch UTC − 4 h
      3. Current UTC <  last  pitch UTC + 3 h

    DST-safe: every comparison is UTC throughout; no hard-coded ET offsets.
    """
    age_min = _odds_cache_age_minutes()
    if age_min <= _ODDS_CACHE_TTL_MINUTES:
        return False, f"cache fresh (age={age_min:.0f}m)"

    times = _game_start_times_utc(target_date)
    if not times:
        return False, "no games scheduled or start times unavailable"

    now_utc     = datetime.now(timezone.utc)
    first_pitch = min(times)
    last_pitch  = max(times)

    if now_utc < first_pitch - timedelta(hours=_PULL_WINDOW_H_BEFORE):
        hours_away = (first_pitch - now_utc).total_seconds() / 3600
        return False, f"first game in {hours_away:.1f}h (too early)"

    if now_utc >= last_pitch + timedelta(hours=_PULL_WINDOW_H_AFTER):
        hours_ago = (now_utc - last_pitch).total_seconds() / 3600
        return False, f"all games done — last pitch {hours_ago:.1f}h ago"

    return True, (
        f"within window — first={first_pitch.strftime('%H:%MZ')} "
        f"last={last_pitch.strftime('%H:%MZ')}"
    )


def _write_odds_skip_sentinel() -> None:
    """
    Write an empty fresh-cache sentinel so odds_api._load_cache() short-circuits
    the Odds API call. The pipeline then runs in odds_pending mode (projected slate,
    zero odds cost). Sentinel expires naturally after _ODDS_CACHE_TTL_MINUTES.
    """
    sentinel = {
        "timestamp": time.time(),
        "props":     [],
        "quota":     {"used": None, "remaining": None},
        "fd_links":  [],
    }
    try:
        _ODDS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _ODDS_CACHE_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(sentinel, f)
        os.replace(tmp, _ODDS_CACHE_PATH)
        logger.info(
            "[odds_guard] sentinel written — Odds API blocked for %dm",
            _ODDS_CACHE_TTL_MINUTES,
        )
    except Exception as exc:
        logger.warning("[odds_guard] sentinel write failed (non-fatal): %s", exc)


# ── Existing capture helpers (unchanged) ───────────────────────────────────────

def _require_odds_api_key() -> None:
    if not os.getenv("ODDS_API_KEY", "").strip():
        logger.error("[capture] FATAL: ODDS_API_KEY not set")
        raise RuntimeError("ODDS_API_KEY not set")


def _capture_readiness(data: dict) -> dict:
    capture = data.get("_capture_stats", {})
    return {
        "games_scheduled": int(capture.get("games_scheduled", 0) or 0),
        "players_attempted": int(capture.get("players_attempted", 0) or 0),
        "odds_lines_fetched": int(capture.get("odds_lines_fetched", 0) or 0),
        "players_matched_to_odds": int(capture.get("players_matched_to_odds", 0) or 0),
        "qualified_count": int(capture.get("qualified_count", 0) or 0),
    }


def _log_capture_summary(capture: dict, picks_upserted: int) -> None:
    logger.info(
        "[capture] CAPTURE_SUMMARY: games=%d odds_lines=%d matched=%d qualified=%d picks_upserted=%d",
        capture["games_scheduled"],
        capture["odds_lines_fetched"],
        capture["players_matched_to_odds"],
        capture["qualified_count"],
        picks_upserted,
    )


def _check_capture_readiness(capture: dict) -> None:
    if capture["games_scheduled"] == 0:
        logger.info("[capture] no games scheduled — empty slate expected")
        return

    if capture["odds_lines_fetched"] == 0:
        _log_capture_summary(capture, picks_upserted=0)
        logger.error(
            "[capture] ODDS PENDING: games present but zero odds fetched — "
            "building projected slate; will backfill when odds post. "
            "Check ODDS_API_KEY / odds source if this persists past expected post time."
        )
        return  # proceed — projected slate builds without odds

    if capture["qualified_count"] == 0:
        logger.warning(
            "[capture] games and odds present but zero qualified — verify filters/thresholds"
        )


def run(target_date: str = None) -> dict:
    _require_odds_api_key()
    target_date = target_date or today_et().strftime("%Y-%m-%d")
    print(f"[cron] Running pipeline for {target_date}...")

    # ── Odds skip-guard ───────────────────────────────────────────────────────
    # Gate the Odds API pull at zero cost. When the guard blocks, a sentinel
    # fresh-cache is written so load_game_data() sees zero odds and takes the
    # existing odds_pending path — the MLB Stats slate still builds normally.
    pull_odds, guard_reason = should_pull_odds(target_date)
    if pull_odds:
        logger.info("[odds_guard] PULL — %s", guard_reason)
    else:
        logger.info("[odds_guard] SKIP — %s", guard_reason)
        _write_odds_skip_sentinel()

    data = load_game_data(target_date)
    capture = _capture_readiness(data)
    _check_capture_readiness(capture)

    odds_pending = capture["games_scheduled"] > 0 and capture["odds_lines_fetched"] == 0

    # Observability: distinguish early-morning pending (normal) from stale pending
    # (odds should have posted by now — likely dead key or quota exhaustion).
    # Threshold: 1pm ET = 17:00 UTC (EDT, UTC-4 in season). Greppable alert label.
    odds_pending_stale = False
    if odds_pending:
        _ODDS_EXPECTED_POST_HOUR_UTC = 17
        if datetime.utcnow().hour >= _ODDS_EXPECTED_POST_HOUR_UTC:
            odds_pending_stale = True
            logger.error(
                "[capture] ALERT ODDS_PENDING_PAST_THRESHOLD: odds still zero past %d:00 UTC — "
                "check ODDS_API_KEY / quota; possible dead key.",
                _ODDS_EXPECTED_POST_HOUR_UTC,
            )

    payload = {
        "date":               target_date,
        "ran_at":             datetime.utcnow().isoformat() + "Z",
        "ranked":             serializable(data.get("ranked", [])),
        "all_by_model":       serializable(data.get("all_by_model", []))[:50],
        "auto_parlays":       data.get("auto_parlays", {}),
        "profile_parlays":    data.get("profile_parlays", {}),
        "stats":              data.get("stats", {}),
        "odds_pending":       odds_pending,
        "odds_pending_stale": odds_pending_stale,
        "odds_guard":         {"pull": pull_odds, "reason": guard_reason},
    }

    try:
        # api.main imports api.auth, which requires SUPABASE_JWT_SECRET at
        # module level. The GH Actions cron env doesn't set it (cron never
        # verifies JWTs), so provide a placeholder before importing.
        os.environ.setdefault("SUPABASE_JWT_SECRET", "")
        from api.main import _build_slate_payload
        payload["slate_cache"] = _build_slate_payload(
            data, odds_pending=odds_pending, odds_pending_stale=odds_pending_stale
        )
        print(f"[cron] slate_cache built — {len(payload['slate_cache'].get('leaderboard_rows', []))} rows")
    except Exception as e:
        print(f"[cron] slate_cache build failed (payload stored without it): {e}")

    # JIG warehouse secondary capture — fire-and-forget after jigScore is computed.
    # Inserts new batter_stat_history rows (distinct run_ts from MAIN capture) so
    # warehouse_backfill can label them with hr_outcome. Non-fatal if it fails.
    try:
        jig_rows = (payload.get("slate_cache") or {}).get("leaderboard_rows_jig") or []
        schedule_jig_stat_capture(target_date, jig_rows, data.get("all_players", []))
        print(f"[cron] JIG warehouse capture scheduled — {len(jig_rows)} rows")
    except Exception as e:
        print(f"[cron] JIG warehouse capture scheduling failed (non-fatal): {e}")

    store_picks(target_date, payload)

    qualified_rows = data.get("ranked") or []
    picks_upserted = 0
    try:
        n = insert_picks(target_date, qualified_rows, source_tab="cron", engine_version=MODEL_VERSION)
        picks_upserted = int(n or 0)
        if picks_upserted != len(qualified_rows):
            raise RuntimeError(
                f"picks upsert count mismatch: submitted {len(qualified_rows)}, "
                f"confirmed {picks_upserted}"
            )
        print(f"[cron] picks table — {n} rows upserted for {target_date}")
    except Exception as e:
        logger.error(
            "[capture] PERSIST FAILED: %d qualified rows submitted, "
            "write did not confirm — failing run: %s",
            len(qualified_rows), e, exc_info=True,
        )
        raise

    # Log full slate to full_slate_log.csv on the Fly volume (Part 3)
    try:
        from tracking import pnl as pnl_tracker
        all_players = data.get("all_players", [])
        ranked = data.get("ranked", [])
        q_names = {p.get("player_name", "") for p in ranked}
        full_logged = pnl_tracker.log_all_players(
            all_players, model_version=MODEL_VERSION, qualified_names=q_names
        )
        print(f"[cron] full_slate_log — {full_logged} rows written")
    except Exception as e:
        print(f"[cron] full_slate_log failed (non-fatal): {e}")

    stats = data.get("stats", {})
    _log_capture_summary(capture, picks_upserted)
    print(
        f"[cron] Done — {stats.get('qualified', 0)} qualified picks, "
        f"{stats.get('players', 0)} total players stored for {target_date}; "
        f"odds_guard={'PULL' if pull_odds else 'SKIP'} ({guard_reason})"
    )
    return payload


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
