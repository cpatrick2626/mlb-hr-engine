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
import traceback
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

from pipeline import load_game_data, serializable
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
            "[capture] CAPTURE FAILED: games present but zero odds fetched — "
            "check ODDS_API_KEY / odds source"
        )
        raise RuntimeError("capture failed: games present but zero odds fetched")

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

    payload = {
        "date":            target_date,
        "ran_at":          datetime.utcnow().isoformat() + "Z",
        "ranked":          serializable(data.get("ranked", [])),
        "all_by_model":    serializable(data.get("all_by_model", []))[:50],
        "auto_parlays":    data.get("auto_parlays", {}),
        "profile_parlays": data.get("profile_parlays", {}),
        "stats":           data.get("stats", {}),
    }

    try:
        # api.main imports api.auth, which requires SUPABASE_JWT_SECRET at
        # module level. The GH Actions cron env doesn't set it (cron never
        # verifies JWTs), so provide a placeholder before importing.
        os.environ.setdefault("SUPABASE_JWT_SECRET", "")
        from api.main import _build_slate_payload
        payload["slate_cache"] = _build_slate_payload(data)
        print(f"[cron] slate_cache built — {len(payload['slate_cache'].get('leaderboard_rows', []))} rows")
    except Exception as e:
        print(f"[cron] slate_cache build failed (payload stored without it): {e}")

    store_picks(target_date, payload)

    picks_upserted = 0
    try:
        n = insert_picks(target_date, data.get("ranked", []), source_tab="cron", engine_version=MODEL_VERSION)
        picks_upserted = int(n or 0)
        print(f"[cron] picks table — {n} rows upserted for {target_date}")
    except Exception as e:
        logger.error(
            "[cron] picks table insert FAILED for %s — picks NOT written: %s",
            target_date, e, exc_info=True,
        )
        print(f"[cron] ERROR: picks table insert FAILED for {target_date}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

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
