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
from api.cache import store_picks


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

    store_picks(target_date, payload)

    stats = data.get("stats", {})
    print(
        f"[cron] Done — {stats.get('qualified', 0)} qualified picks, "
        f"{stats.get('players', 0)} total players stored for {target_date}"
    )
    return payload


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
