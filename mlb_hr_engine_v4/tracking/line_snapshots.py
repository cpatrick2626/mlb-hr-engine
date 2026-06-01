"""
Line snapshot storage — captures odds at specific timestamps for CLV computation.

Workflow:
  morning  : 'opening' snapshot captured when picks are logged
  pre-game : 'closing' snapshot captured ~30-60 min before first pitch
  analysis : CLV computed from (opening - closing) delta

Storage: line_snapshots.csv (append-only raw log)
         One row per player × date × snapshot_type × sportsbook.

The 'closing' snapshot represents the final market consensus before sharp
money is locked out — the canonical CLV reference point.
"""

from __future__ import annotations

import csv
import os
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

SNAPSHOT_PATH = Path(__file__).parent / "line_snapshots.csv"

SNAPSHOT_FIELDS = [
    "date",
    "player_name",
    "team",
    "snapshot_type",      # "opening" | "pre_game" | "closing" | "manual"
    "snapshot_ts",        # ISO-8601 UTC timestamp of capture
    "sportsbook",
    "american_odds",
    "implied_pct",        # raw vigged implied probability × 100
    "no_vig_pct",         # no-vig probability × 100 (uses engine.vig)
    "game_id",            # Odds API event ID for dedup
]

# Snapshot type priority: higher = more preferred as "closing" reference
_SNAP_PRIORITY = {"closing": 3, "pre_game": 2, "manual": 1, "opening": 0}


# ── Public API ────────────────────────────────────────────────────────────────

def save_snapshots(
    props: list[dict],
    snapshot_type: str,
    date_str: Optional[str] = None,
) -> int:
    """
    Save a batch of odds snapshots.

    Args:
        props: list of prop dicts from odds_api._get_event_props() or clv._fetch_current_hr_odds()
               Expected keys: player_name, price (American), bookmaker, [team], [game_id]
        snapshot_type: "opening" | "pre_game" | "closing"
        date_str: ISO date (default: today)

    Returns:
        Count of rows written.
    """
    date_str = date_str or date.today().isoformat()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        from engine.vig import no_vig_prob_for_book, _implied
    except ImportError:
        def _implied(american: int) -> float:
            if american > 0:
                return 100.0 / (american + 100.0)
            return abs(american) / (abs(american) + 100.0)
        def no_vig_prob_for_book(american: int, book: str) -> float:
            return _implied(american) / 1.075  # fallback global vig

    rows = []
    for p in props:
        american = p.get("price")
        if not american:
            continue
        try:
            american = int(american)
        except (ValueError, TypeError):
            continue
        if -100 < american < 100:
            continue

        book = p.get("bookmaker", "")
        implied = _implied(american)
        try:
            nv = no_vig_prob_for_book(american, book)
        except Exception:
            nv = implied / 1.075

        rows.append({
            "date":          date_str,
            "player_name":   p.get("player_name", ""),
            "team":          p.get("team", "") or p.get("home_team", ""),
            "snapshot_type": snapshot_type,
            "snapshot_ts":   ts,
            "sportsbook":    book,
            "american_odds": american,
            "implied_pct":   f"{implied * 100:.3f}",
            "no_vig_pct":    f"{nv * 100:.3f}",
            "game_id":       p.get("game_id", ""),
        })

    if rows:
        _append_snapshots(rows)
    return len(rows)


def get_best_close(
    player_name: str,
    date_str: str,
    preferred_book: str = "",
) -> Optional[dict]:
    """
    Return the best closing-line snapshot for a player on a date.

    Preference order:
      1. 'closing' type snapshot at preferred_book
      2. 'closing' type at any book (best odds = highest American)
      3. 'pre_game' type (highest American)
      4. None if no post-opening snapshot exists

    Returns dict with keys: american_odds, no_vig_pct, sportsbook, snapshot_type, snapshot_ts
    or None if not found.
    """
    snaps = load_for_date(date_str, player_name)
    # Filter to non-opening snapshots
    candidates = [s for s in snaps if s.get("snapshot_type") != "opening"]
    if not candidates:
        return None

    # Sort: preferred_book first, then by priority, then by best American odds
    norm_pref = _norm(preferred_book)

    def sort_key(s):
        prio    = _SNAP_PRIORITY.get(s.get("snapshot_type", ""), 0)
        is_pref = 1 if (_norm(s.get("sportsbook", "")) == norm_pref and norm_pref) else 0
        try:
            odds = int(s.get("american_odds", 0))
        except (ValueError, TypeError):
            odds = 0
        return (is_pref, prio, odds)

    best = max(candidates, key=sort_key)
    return {
        "american_odds":  int(best.get("american_odds", 0)),
        "no_vig_pct":     float(best.get("no_vig_pct", 0)),
        "implied_pct":    float(best.get("implied_pct", 0)),
        "sportsbook":     best.get("sportsbook", ""),
        "snapshot_type":  best.get("snapshot_type", ""),
        "snapshot_ts":    best.get("snapshot_ts", ""),
    }


def get_opening_snap(
    player_name: str,
    date_str: str,
    preferred_book: str = "",
) -> Optional[dict]:
    """Return the opening-type snapshot for a player on a date."""
    snaps = load_for_date(date_str, player_name)
    candidates = [s for s in snaps if s.get("snapshot_type") == "opening"]
    if not candidates:
        return None
    norm_pref = _norm(preferred_book)

    def sort_key(s):
        is_pref = 1 if (_norm(s.get("sportsbook", "")) == norm_pref and norm_pref) else 0
        try:
            odds = int(s.get("american_odds", 0))
        except (ValueError, TypeError):
            odds = 0
        return (is_pref, odds)

    best = max(candidates, key=sort_key)
    return {
        "american_odds":  int(best.get("american_odds", 0)),
        "no_vig_pct":     float(best.get("no_vig_pct", 0)),
        "implied_pct":    float(best.get("implied_pct", 0)),
        "sportsbook":     best.get("sportsbook", ""),
        "snapshot_ts":    best.get("snapshot_ts", ""),
    }


def load_for_date(date_str: str, player_name: str = "") -> list[dict]:
    """All snapshots for a date, optionally filtered by player name."""
    if not SNAPSHOT_PATH.exists():
        return []
    norm = _norm(player_name) if player_name else ""
    rows = []
    with open(SNAPSHOT_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("date") != date_str:
                continue
            if norm and _norm(row.get("player_name", "")) != norm:
                continue
            rows.append(dict(row))
    return rows


def dates_with_snapshots() -> list[str]:
    """All dates that have at least one snapshot, sorted ascending."""
    if not SNAPSHOT_PATH.exists():
        return []
    dates: set[str] = set()
    with open(SNAPSHOT_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = row.get("date", "")
            if d:
                dates.add(d)
    return sorted(dates)


def snapshot_count() -> dict:
    """Summary counts: {total, by_type, by_date_count}."""
    if not SNAPSHOT_PATH.exists():
        return {"total": 0, "by_type": {}, "date_count": 0}
    total = 0
    by_type: dict[str, int] = {}
    dates: set[str] = set()
    with open(SNAPSHOT_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            t = row.get("snapshot_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
            dates.add(row.get("date", ""))
    return {"total": total, "by_type": by_type, "date_count": len(dates)}


# ── Internal ──────────────────────────────────────────────────────────────────

def _norm(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower().strip()


def _append_snapshots(rows: list[dict]) -> None:
    write_header = not SNAPSHOT_PATH.exists()
    tmp = SNAPSHOT_PATH.with_suffix(".tmp")
    try:
        # Read existing
        existing: list[dict] = []
        if SNAPSHOT_PATH.exists():
            with open(SNAPSHOT_PATH, newline="", encoding="utf-8") as f:
                existing = list(csv.DictReader(f))
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SNAPSHOT_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(existing)
            writer.writerows(rows)
        os.replace(tmp, SNAPSHOT_PATH)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
