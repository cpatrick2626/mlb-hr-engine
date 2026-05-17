#!/usr/bin/env python3
"""
settle_pick_tracker.py  —  Session 25: Batch-settle pick_tracker.csv outcomes
==============================================================================

Reads every unsettled row in pick_tracker.csv, looks up each player's HR result
for that date via the MLB Stats API game log, then writes hr_result and profit_loss
in-place.  Safe to run repeatedly (skips already-settled rows).

Only rows with REAL market odds (american_odds populated) are P&L-settled.
Rows without odds still get hr_result filled so future analysis can use them
as calibration data.

Usage:
  py -3.12 settle_pick_tracker.py              # settle all past dates
  py -3.12 settle_pick_tracker.py 2026-05-13   # settle a specific date
"""

import csv
import os
import sys
import time
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import requests

ROOT     = Path(__file__).parent
CSV_PATH = ROOT / "mlb_hr_engine_v4" / "tracking" / "pick_tracker.csv"

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Codex-HR-Engine/settle"})

# MLB Stats API endpoint for hitting game logs
_MLB_URL = "https://statsapi.mlb.com/api/v1/people/{pid}/stats"


# ── MLB Stats API ─────────────────────────────────────────────────────────────

def _fetch_hr_result(player_id: str, date_str: str) -> bool | None:
    """Return True (hit HR), False (played, no HR), or None (DNP/API error)."""
    try:
        r = _SESSION.get(
            _MLB_URL.format(pid=player_id),
            params={"stats": "gameLog", "group": "hitting", "season": date_str[:4]},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        stats_list = r.json().get("stats", [])
        splits = stats_list[0].get("splits", []) if stats_list else []
        for split in splits:
            if split.get("date") == date_str:
                return int(split.get("stat", {}).get("homeRuns", 0)) > 0
        return None   # date not in game log → DNP / postponement
    except Exception:
        return None


# ── P&L calculation ───────────────────────────────────────────────────────────

def _compute_pl(bet: float, odds: int, hit_hr: bool) -> float:
    if hit_hr:
        return round(bet * odds / 100, 2) if odds > 0 else round(bet * 100 / abs(odds), 2)
    return round(-bet, 2)


# ── Normalise name for fuzzy matching ─────────────────────────────────────────

def _norm(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower().strip()


# ── CSV helpers ───────────────────────────────────────────────────────────────

def _load() -> tuple[list[str], list[dict]]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows   = list(reader)
    return fields, rows


def _save(fields: list[str], rows: list[dict]) -> None:
    tmp = CSV_PATH.with_suffix(".tmp")
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, CSV_PATH)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


# ── Main settlement logic ─────────────────────────────────────────────────────

def settle_date(date_str: str, rows: list[dict], fields: list[str],
                verbose: bool = True) -> dict:
    """Settle all unsettled rows for date_str. Returns stats dict."""
    today = date.today().isoformat()
    if date_str >= today:
        if verbose:
            print(f"  [skip] {date_str} is today or future — games may not be final")
        return {"date": date_str, "settled": 0, "dnp": 0, "skipped": 0, "errors": 0}

    target = [r for r in rows
              if r.get("date") == date_str
              and r.get("hr_result", "").strip() not in ("0", "1", "void")]

    if not target:
        if verbose:
            print(f"  {date_str}: already settled or no rows")
        return {"date": date_str, "settled": 0, "dnp": 0, "skipped": 0, "errors": 0}

    # Batch fetch: one API call per unique player_id
    unique_pids = list({r["player_id"] for r in target if r.get("player_id", "").strip()})
    if verbose:
        print(f"  {date_str}: {len(target)} unsettled rows, {len(unique_pids)} unique player IDs")

    outcomes: dict[str, bool | None] = {}   # player_id → True/False/None
    for i, pid in enumerate(unique_pids):
        result = _fetch_hr_result(pid, date_str)
        outcomes[pid] = result
        if verbose and i > 0 and i % 20 == 0:
            print(f"    fetched {i}/{len(unique_pids)} ...", flush=True)
        time.sleep(0.05)   # polite rate limit (20 req/s)

    settled = dnp = errors = skipped = 0
    for row in rows:
        if row.get("date") != date_str:
            continue
        if row.get("hr_result", "").strip() in ("0", "1", "void"):
            continue   # already settled

        pid = row.get("player_id", "").strip()
        if not pid or pid not in outcomes:
            skipped += 1
            continue

        result = outcomes[pid]
        if result is None:
            # Not in game log: player DNP or postponement — mark void
            row["hr_result"]   = "void"
            row["profit_loss"] = "0.00"
            dnp += 1
            continue

        row["hr_result"] = "1" if result else "0"

        # Only compute P&L for rows that have real market odds
        try:
            bet  = float(row.get("bet_dollars", "0") or "0")
            odds = int(float(row.get("american_odds", "0") or "0"))
        except (ValueError, TypeError):
            bet, odds = 0.0, 0

        if bet > 0 and odds != 0:
            row["profit_loss"] = f"{_compute_pl(bet, odds, result):.2f}"
        else:
            row["profit_loss"] = ""   # no real bet logged

        settled += 1

    return {"date": date_str, "settled": settled, "dnp": dnp,
            "skipped": skipped, "errors": errors}


def settle_all(target_date: str | None = None, verbose: bool = True) -> None:
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found")
        sys.exit(1)

    fields, rows = _load()

    if target_date:
        dates = [target_date]
    else:
        today = date.today().isoformat()
        dates = sorted({r["date"] for r in rows if r.get("date", "") < today})

    if not dates:
        print("No past dates found in pick_tracker.csv")
        return

    print(f"Settling {len(dates)} date(s): {dates[0]} to {dates[-1]}")
    total_settled = total_dnp = 0
    for d in dates:
        stats = settle_date(d, rows, fields, verbose=verbose)
        total_settled += stats["settled"]
        total_dnp     += stats["dnp"]

    # Save in one write
    _save(fields, rows)

    # ── Summary report ────────────────────────────────────────────────────────
    settled_rows = [r for r in rows if r.get("hr_result") in ("0", "1")]
    with_pl      = [r for r in settled_rows if r.get("profit_loss", "").strip()
                    and r.get("profit_loss") != "0.00"]
    wins         = [r for r in with_pl if r.get("hr_result") == "1"]
    losses       = [r for r in with_pl if r.get("hr_result") == "0"]
    total_bet    = sum(float(r.get("bet_dollars", "0") or "0") for r in with_pl)
    total_pl     = sum(float(r.get("profit_loss", "0") or "0") for r in with_pl)

    print()
    print("=" * 65)
    print("  SETTLEMENT REPORT")
    print("=" * 65)
    print(f"  Newly settled this run:  {total_settled}")
    print(f"  Marked void (DNP):       {total_dnp}")
    print()
    print(f"  pick_tracker.csv cumulative (rows with real bet P&L):")
    print(f"  Total picks (bet):       {len(with_pl)}")
    print(f"  Wins (HR hit):           {len(wins)}")
    print(f"  Losses (no HR):          {len(losses)}")
    if with_pl:
        win_rate = len(wins) / len(with_pl) * 100
        roi      = total_pl / total_bet * 100 if total_bet > 0 else 0
        print(f"  Win rate:                {win_rate:.1f}%")
        print(f"  Total wagered:           ${total_bet:.2f}")
        print(f"  Net P&L:                 ${total_pl:+.2f}")
        print(f"  ROI:                     {roi:+.1f}%")

    # Barrel tier breakdown for settled rows with barrel_pct
    brl_groups: dict[str, list] = {}
    for r in with_pl:
        try:
            brl = float(r.get("barrel_pct", "0") or "0")
        except ValueError:
            brl = 0.0
        if brl < 6:     tier = "<6%"
        elif brl < 8:   tier = "6-8%"
        elif brl < 10:  tier = "8-10%"
        elif brl < 12:  tier = "10-12%"
        else:           tier = "12%+"
        brl_groups.setdefault(tier, []).append(float(r.get("profit_loss", "0") or "0"))

    if any(brl_groups.values()):
        print()
        print(f"  Barrel tier breakdown (settled picks with P&L):")
        for tier in ["<6%","6-8%","8-10%","10-12%","12%+"]:
            pls = brl_groups.get(tier, [])
            if not pls:
                continue
            nb  = len(pls)
            pl  = sum(pls)
            roi = pl / nb * 100   # assumes flat $1 bet is captured in profit_loss
            print(f"    {tier:8s}  n={nb:3d}  pl=${pl:+.2f}")

    print()
    print(f"Saved: {CSV_PATH}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    settle_all(target_date=target)
