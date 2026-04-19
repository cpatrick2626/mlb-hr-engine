"""
P&L Tracker — logs picks daily and tracks outcomes + profit/loss.

Files written to mlb_hr_engine_v2/tracking/:
  picks_log.csv    — every pick ever made (auto-appended each run)
  results.csv      — picks with outcome filled in (HR yes/no, profit)

Workflow:
  1. main.py calls log_picks() each run → appends to picks_log.csv
  2. After games end, run:  python tracking/update_results.py
     → auto-fetches MLB game results and calculates P&L
  3. display.py calls pnl_summary() to show running totals at the bottom
"""

import csv
import os
from datetime import date, timedelta
from pathlib import Path

import requests

LOG_PATH     = Path(__file__).parent / "picks_log.csv"
RESULTS_PATH = Path(__file__).parent / "results.csv"

LOG_FIELDS = [
    "date", "model_version", "player_name", "team", "opponent",
    "pitcher", "lineup_spot", "model_prob_pct", "market_prob_pct",
    "ev_pct", "edge_pct", "american_odds", "bet_dollars",
    "park_factor", "pitcher_factor", "weather_factor",
    "season_pa", "recent_pa", "confidence", "score",
]

RESULTS_FIELDS = LOG_FIELDS + ["hr_result", "profit_loss", "notes"]


def log_picks(picks: list[dict], model_version: str = "v2") -> int:
    """
    Append today's qualified picks to picks_log.csv.
    Returns number of picks logged.
    Skips re-logging if today's picks already exist.
    """
    today = date.today().isoformat()
    existing_dates = _read_existing_dates(LOG_PATH)

    if today in existing_dates:
        return 0  # Already logged today

    rows = []
    for p in picks:
        rows.append({
            "date":             today,
            "model_version":    model_version,
            "player_name":      p.get("player_name", ""),
            "team":             p.get("team", ""),
            "opponent":         p.get("opponent", ""),
            "pitcher":          p.get("pitcher_name", ""),
            "lineup_spot":      p.get("lineup_spot", ""),
            "model_prob_pct":   f"{p.get('model_prob', 0)*100:.2f}",
            "market_prob_pct":  f"{p.get('market_no_vig_prob', 0)*100:.2f}",
            "ev_pct":           f"{p.get('ev_pct', 0):.2f}",
            "edge_pct":         f"{p.get('edge_pct', 0):.2f}",
            "american_odds":    p.get("best_american", ""),
            "bet_dollars":      f"{p.get('bet_dollars', 0):.2f}",
            "park_factor":      f"{p.get('park_factor', 1):.3f}",
            "pitcher_factor":   f"{p.get('pitcher_factor', 1):.3f}",
            "weather_factor":   f"{p.get('weather_factor', 1):.3f}",
            "season_pa":        p.get("season_pa", ""),
            "recent_pa":        p.get("recent_pa", ""),
            "confidence":       f"{p.get('confidence', 0):.1f}",
            "score":            f"{p.get('score', 0):.2f}",
        })

    _append_rows(LOG_PATH, LOG_FIELDS, rows)
    return len(rows)


def fetch_yesterday_outcomes(model_version: str = "v2") -> dict[str, bool]:
    """
    Auto-fetch game results from MLB Stats API for yesterday's picks.
    Returns {player_name: hit_hr (bool)}.
    """
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    pending = _load_pending_picks(yesterday, model_version)
    if not pending:
        return {}

    outcomes: dict[str, bool] = {}
    for pick in pending:
        pid = pick.get("player_id")
        if not pid:
            continue
        hit_hr = _check_player_hr_yesterday(int(pid), yesterday)
        if hit_hr is not None:
            outcomes[pick["player_name"]] = hit_hr

    return outcomes


def update_results(date_str: str, outcomes: dict[str, bool], model_version: str = "v2") -> None:
    """
    Write outcomes to results.csv for a given date.
    outcomes: {player_name: hit_hr}
    """
    picks = _load_pending_picks(date_str, model_version)
    rows = []
    for p in picks:
        name = p["player_name"]
        hit_hr = outcomes.get(name)
        odds = int(p.get("american_odds", 0) or 0)
        bet = float(p.get("bet_dollars", 0) or 0)

        if hit_hr is None:
            profit = ""
        elif hit_hr:
            if odds > 0:
                profit = round(bet * odds / 100, 2)
            else:
                profit = round(bet * 100 / abs(odds), 2)
        else:
            profit = round(-bet, 2)

        rows.append({**p, "hr_result": 1 if hit_hr else 0 if hit_hr is not None else "",
                     "profit_loss": profit, "notes": ""})

    _append_rows(RESULTS_PATH, RESULTS_FIELDS, rows)


def pnl_summary() -> dict:
    """
    Return running P&L stats from results.csv.
    """
    if not RESULTS_PATH.exists():
        return {}

    total_bet = 0.0
    total_profit = 0.0
    wins = 0
    losses = 0
    pending = 0

    with open(RESULTS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bet = float(row.get("bet_dollars", 0) or 0)
            pl = row.get("profit_loss", "")
            total_bet += bet
            if pl == "":
                pending += 1
            else:
                profit = float(pl)
                total_profit += profit
                if profit > 0:
                    wins += 1
                else:
                    losses += 1

    total_decided = wins + losses
    return {
        "total_picks":   total_decided + pending,
        "wins":          wins,
        "losses":        losses,
        "pending":       pending,
        "win_rate":      wins / total_decided if total_decided else 0,
        "total_wagered": total_bet,
        "total_profit":  total_profit,
        "roi_pct":       (total_profit / total_bet * 100) if total_bet > 0 else 0,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _append_rows(path: Path, fields: list[str], rows: list[dict]) -> None:
    write_header = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def _read_existing_dates(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["date"] for row in reader if "date" in row}


def _load_pending_picks(date_str: str, model_version: str) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    rows = []
    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("date") == date_str and row.get("model_version") == model_version:
                rows.append(row)
    return rows


def _check_player_hr_yesterday(player_id: int, date_str: str) -> bool | None:
    """Query MLB Stats API game log for a specific date."""
    try:
        resp = requests.get(
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats",
            params={"stats": "gameLog", "group": "hitting",
                    "season": date_str[:4]},
            timeout=10,
        )
        splits = resp.json().get("stats", [{}])[0].get("splits", [])
        for split in splits:
            if split.get("date") == date_str:
                return int(split.get("stat", {}).get("homeRuns", 0)) > 0
        return False
    except Exception:
        return None
