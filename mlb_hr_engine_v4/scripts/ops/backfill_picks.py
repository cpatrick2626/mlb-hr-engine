#!/usr/bin/env python3
"""
One-time backfill: reads tracking/pick_tracker.csv → inserts into Supabase picks table.

Run from mlb_hr_engine_v4/:
  python scripts/ops/backfill_picks.py

Expects SUPABASE_URL and SUPABASE_SERVICE_KEY in env / .env.
ON CONFLICT (date, player_id, source_tab) DO NOTHING — safe to re-run.
"""

import os
import sys
import csv
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "tracking", "pick_tracker.csv")
BATCH_SIZE = 500


def _float(val):
    try:
        v = float(val)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def _int(val):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def _bool_clv(clv_pp):
    """beats_close = True when clv_pp > 0 (closed with positive CLV)."""
    v = _float(clv_pp)
    if v is None:
        return None
    return v > 0


def _dedupe_key(record: dict) -> tuple:
    return (record["date"], record["player_id"], record["source_tab"])


def _choose_record(existing: dict, candidate: dict) -> dict:
    existing_settled = existing.get("hr_result") is not None
    candidate_settled = candidate.get("hr_result") is not None

    if candidate_settled and not existing_settled:
        return candidate
    if existing_settled and not candidate_settled:
        return existing
    return candidate


def build_row(r: dict) -> dict:
    qualified = r.get("source_section", "").strip() == "Qualified Picks"
    source_tab = r.get("source_tab", "").strip() or "csv"

    # lineup_spot may be "None" string in CSV
    ls_raw = r.get("lineup_spot", "")
    lineup_spot = _int(ls_raw) if ls_raw not in ("", "None", "none") else None

    # hr_result: empty string → NULL; "0"/"1" → int
    hr_raw = r.get("hr_result", "").strip()
    hr_result = _int(hr_raw) if hr_raw not in ("", "None") else None

    # close_odds → closing_american (integer american odds, e.g. 600)
    closing_am = _int(r.get("close_odds", ""))

    return {
        "date":             r["date"],
        "player_id":        _int(r["player_id"]),
        "player_name":      r["player_name"],
        "team":             r.get("team") or None,
        "opponent":         r.get("opponent") or None,
        "pitcher":          r.get("pitcher") or None,
        "lineup_spot":      lineup_spot,
        "model_prob_pct":   _float(r.get("model_prob_pct")),
        "market_prob_pct":  _float(r.get("market_prob_pct")),
        "ev_pct":           _float(r.get("ev_pct")),
        "edge_pct":         _float(r.get("edge_pct")),
        "american_odds":    _int(r.get("american_odds")),
        "bet_dollars":      _float(r.get("bet_dollars")),
        "barrel_pct":       _float(r.get("barrel_pct")),
        "xslg":             _float(r.get("xslg")),
        "park_factor":      _float(r.get("park_factor")),
        "pitcher_factor":   _float(r.get("pitcher_factor")),
        "confidence_tier":  None,  # CSV has numeric confidence score, not tier string
        "qualified":        qualified,
        "filter_reasons":   None,
        "source_tab":       source_tab,
        "hr_result":        hr_result,
        "profit_loss":      _float(r.get("profit_loss")),
        "opening_american": None,  # CSV has open_implied_pct (prob %), not american odds
        "opening_no_vig_pct": _float(r.get("open_no_vig_pct")),
        "closing_american": closing_am,
        "closing_no_vig_pct": _float(r.get("close_no_vig_pct")),
        "clv_pp":           _float(r.get("clv_pp")),
        "clv_pct_rel":      _float(r.get("clv_pct_rel")),
        "beats_close":      _bool_clv(r.get("clv_pp")),
        "engine_version":   r.get("engine_version") or None,
    }


def main():
    from supabase import create_client
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"[backfill] {len(rows)} rows read from pick_tracker.csv")

    deduped_records = {}
    skipped = 0
    for r in rows:
        pid = _int(r.get("player_id"))
        if pid is None:
            skipped += 1
            continue
        record = build_row(r)
        key = _dedupe_key(record)
        existing = deduped_records.get(key)
        deduped_records[key] = record if existing is None else _choose_record(existing, record)

    records = list(deduped_records.values())
    deduped_count = len(rows) - skipped - len(records)

    print(
        f"[backfill] {len(records)} deduped records to insert "
        f"({skipped} skipped — no player_id, {deduped_count} duplicates removed)"
    )

    inserted = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        client.table("picks").upsert(
            batch, on_conflict="date,player_id,source_tab"
        ).execute()
        inserted += len(batch)
        print(f"[backfill] {inserted}/{len(records)} upserted...")

    print(f"[backfill] Done — {inserted} rows upserted.")
    print()
    print("Verify with:")
    print("  SELECT count(*) FROM picks;")
    print("  SELECT count(*) FROM picks WHERE hr_result IS NOT NULL;")


if __name__ == "__main__":
    main()
