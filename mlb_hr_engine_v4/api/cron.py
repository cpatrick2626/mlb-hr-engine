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
import logging
from datetime import datetime

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
        f"{stats.get('players', 0)} total players stored for {target_date}"
    )
    return payload


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
