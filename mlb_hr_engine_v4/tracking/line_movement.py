"""
Line movement tracker — logs odds snapshots for qualified picks throughout the day.

Each time the pipeline runs (or the app refreshes), current odds are appended with a
timestamp. Querying snapshots for a player shows how the line moved from morning open
to pre-game close, which signals whether sharp money is agreeing or disagreeing.

Positive movement (odds shortening, e.g. +350 → +290): market agrees — confidence up.
Negative movement (odds lengthening, e.g. +290 → +340): market fading — proceed carefully.
"""

import csv
from datetime import date, datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent / "line_movement_log.csv"
FIELDS = ["date", "time_utc", "player_name", "team", "american_odds", "ev_pct", "model_prob_pct"]

_BOOK_ORDER = ["fanduel", "draftkings", "betmgm", "caesars", "pointsbet", "betrivers"]


def log_current_odds(picks: list[dict]) -> int:
    """Snapshot current odds for all qualified picks. Returns count logged."""
    if not picks:
        return 0
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    time_utc = now.strftime("%H:%M")
    rows = []
    for p in picks:
        if not p.get("best_american"):
            continue
        rows.append({
            "date":           today,
            "time_utc":       time_utc,
            "player_name":    p.get("player_name", ""),
            "team":           p.get("team", ""),
            "american_odds":  p.get("best_american", ""),
            "ev_pct":         f"{p.get('ev_pct', 0):.2f}",
            "model_prob_pct": f"{p.get('model_prob', 0)*100:.2f}",
        })
    _append(rows)
    return len(rows)


def get_movement_today(target_date: str = None) -> dict[str, list[dict]]:
    """Return {player_name: [snapshots_oldest_first]} for target_date (default today)."""
    d = target_date or date.today().isoformat()
    if not LOG_PATH.exists():
        return {}
    by_player: dict[str, list[dict]] = {}
    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("date") == d:
                by_player.setdefault(row["player_name"], []).append(row)
    return by_player


def movement_summary(snapshots: list[dict]) -> dict:
    """Summarise a player's intraday line movement from their snapshot list."""
    if not snapshots:
        return {}
    def _odds(row):
        try:
            return int(row["american_odds"])
        except (ValueError, TypeError):
            return None

    valid = [(s["time_utc"], _odds(s)) for s in snapshots if _odds(s) is not None]
    if not valid:
        return {}
    opening_time, opening_odds = valid[0]
    current_time, current_odds = valid[-1]
    # Convert to implied prob to measure movement direction
    def _impl(o):
        return 100 / (o + 100) if o > 0 else abs(o) / (abs(o) + 100)

    open_impl = _impl(opening_odds)
    curr_impl = _impl(current_odds)
    # Positive move_pct = market shortened (market gained confidence = good signal)
    move_pct = round((curr_impl - open_impl) * 100, 2)
    return {
        "opening_odds":  opening_odds,
        "opening_time":  opening_time,
        "current_odds":  current_odds,
        "current_time":  current_time,
        "n_snapshots":   len(valid),
        "move_pct":      move_pct,   # positive = line shortened (market agrees)
        "direction":     "▲ shortened" if move_pct > 0.5 else ("▼ lengthened" if move_pct < -0.5 else "→ stable"),
    }


def _append(rows: list[dict]) -> None:
    write_header = not LOG_PATH.exists()
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
