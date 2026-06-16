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
from datetime import date, datetime

# Support running as a module from mlb_hr_engine_v4/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pipeline import load_game_data, serializable
from api.cache import store_picks, insert_picks

MODEL_VERSION = "v4"


def run(target_date: str = None) -> dict:
    target_date = target_date or date.today().strftime("%Y-%m-%d")
    print(f"[cron] Running pipeline for {target_date}...")

    data = load_game_data(target_date)

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

    try:
        n = insert_picks(target_date, data.get("ranked", []), source_tab="cron", engine_version=MODEL_VERSION)
        print(f"[cron] picks table — {n} rows upserted for {target_date}")
    except Exception as e:
        print(f"[cron] picks table write failed (non-fatal): {e}")

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
    print(
        f"[cron] Done — {stats.get('qualified', 0)} qualified picks, "
        f"{stats.get('players', 0)} total players stored for {target_date}"
    )
    return payload


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
