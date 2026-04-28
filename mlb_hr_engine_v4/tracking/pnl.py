"""
P&L Tracker â€” logs picks and tracks outcomes + profit/loss.

Storage:
  When Google Sheets is configured (GOOGLE_CREDENTIALS + GOOGLE_SHEET_ID secrets),
  data is written to and read from the cloud sheet â€” survives Streamlit restarts.
  Otherwise falls back to local CSV files (codex_hr_engine_v4/tracking/).

Workflow:
  1. app.py / main.py calls log_picks() each run â†’ appends to picks_log
  2. Sidebar "Update Yesterday" button calls update_yesterday() â†’ settles outcomes
  3. tab_performance() calls pnl_summary() + get_picks_log() to display results
"""

import csv
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import requests

from tracking import sheets as _sheets

LOG_PATH     = Path(__file__).parent / "picks_log.csv"
RESULTS_PATH = Path(__file__).parent / "results.csv"

LOG_FIELDS = [
    "date", "model_version", "player_id", "player_name", "team", "opponent",
    "pitcher", "lineup_spot", "model_prob_pct", "market_prob_pct",
    "ev_pct", "edge_pct", "american_odds", "bet_dollars",
    "park_factor", "pitcher_factor", "weather_factor",
    "season_pa", "recent_pa", "confidence", "score",
]

RESULTS_FIELDS = LOG_FIELDS + ["hr_result", "profit_loss", "notes"]


# â”€â”€ Public API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def storage_backend() -> str:
    return "sheets" if _sheets.available() else "csv"


def log_picks(picks: list[dict], model_version: str = "v4") -> int:
    """Append today's qualified picks. Returns number logged (0 if already done)."""
    today = date.today().isoformat()

    if _sheets.available():
        if today in _sheets.existing_dates("picks_log"):
            return 0
        rows = [_pick_row(p, today, model_version) for p in picks]
        _sheets.append_rows("picks_log", LOG_FIELDS, rows)
    else:
        if today in _read_existing_dates(LOG_PATH):
            return 0
        rows = [_pick_row(p, today, model_version) for p in picks]
        _append_csv(LOG_PATH, LOG_FIELDS, rows)

    return len(rows)


def log_slip_picks(picks: list[dict], model_version: str = "v4") -> int:
    """
    Log manually-selected slip picks, skipping any already logged today.
    Unlike log_picks(), this does not gate on the whole day — only on
    individual player duplicates (same player_name + date).
    Returns count of newly added rows.
    """
    today = date.today().isoformat()
    if _sheets.available():
        existing = {r.get("player_name", "") for r in _sheets.read_rows("picks_log")
                    if r.get("date") == today}
        new_rows = [_pick_row(p, today, model_version) for p in picks
                    if p.get("player_name", "") not in existing]
        if new_rows:
            _sheets.append_rows("picks_log", LOG_FIELDS, new_rows)
    else:
        existing: set[str] = set()
        if LOG_PATH.exists():
            with open(LOG_PATH, newline="", encoding="utf-8") as f:
                existing = {r.get("player_name", "") for r in csv.DictReader(f)
                            if r.get("date") == today}
        new_rows = [_pick_row(p, today, model_version) for p in picks
                    if p.get("player_name", "") not in existing]
        if new_rows:
            _append_csv(LOG_PATH, LOG_FIELDS, new_rows)
    return len(new_rows)


def update_yesterday() -> dict:
    """
    Fetch yesterday's HR outcomes from MLB Stats API and settle picks.
    Returns dict with keys: settled (int), not_found (int), date (str).
    """
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return _settle_date(yesterday)


def fetch_yesterday_outcomes(model_version: str = "v4") -> dict[str, bool]:
    """
    Fetch HR outcomes for yesterday's picks. Returns {player_name: hit_hr}.
    Called by main.py at startup to auto-settle without requiring Streamlit.
    """
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    pending = _load_pending(yesterday)
    outcomes: dict[str, bool] = {}
    for pick in pending:
        pid = pick.get("player_id") or ""
        if not pid:
            continue
        result = _mlb_hr_result(int(pid), yesterday)
        if result is not None:
            outcomes[pick["player_name"]] = result
    return outcomes


def update_results(date_str: str, outcomes: dict[str, bool], model_version: str = "v4") -> int:
    """
    Write settled outcomes to results.csv. Returns count of rows written.
    Called by main.py after fetch_yesterday_outcomes().
    """
    pending = _load_pending(date_str)
    result_rows = []
    settled = 0
    for pick in pending:
        name     = pick["player_name"]
        hit_hr   = outcomes.get(name)
        odds_raw = pick.get("american_odds", "") or ""
        bet      = float(pick.get("bet_dollars") or 0)
        try:
            odds = int(float(odds_raw))
        except (ValueError, TypeError):
            odds = 0

        # Only write definitive outcomes — skip unknowns (DNP/API failure/postponement)
        # so the pick stays in picks_log as pending and can be retried next run.
        if hit_hr is None:
            continue

        result_rows.append({
            **pick,
            "hr_result":   1 if hit_hr else 0,
            "profit_loss": _compute_pl(bet, odds, hit_hr),
            "notes":       "",
        })
        settled += 1

    if result_rows:
        if _sheets.available():
            _sheets.append_rows("results", RESULTS_FIELDS, result_rows)
        else:
            _append_csv(RESULTS_PATH, RESULTS_FIELDS, result_rows)
    return settled


def settle_all_unsettled() -> dict:
    """
    Backfill outcomes for all past dates that have unsettled picks.
    Returns {date: settled_count}. Safe to call repeatedly (skips already-settled dates).
    """
    if not LOG_PATH.exists():
        return {}

    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        all_picks = list(csv.DictReader(f))

    today = date.today().isoformat()
    past_dates = sorted({r.get("date", "") for r in all_picks if r.get("date", "") < today})

    summary = {}
    for d in past_dates:
        result = _settle_date(d)
        if result["settled"] + result["not_found"] > 0:
            summary[d] = result["settled"]
    return summary


def _settle_date(date_str: str) -> dict:
    """Settle all pending picks for a given date. Returns settlement stats."""
    pending = _load_pending(date_str)
    if not pending:
        return {"settled": 0, "not_found": 0, "date": date_str}

    outcomes: dict[str, bool] = {}
    for pick in pending:
        pid = pick.get("player_id") or ""
        if not pid:
            continue
        result = _mlb_hr_result(int(pid), date_str)
        if result is not None:
            outcomes[pick["player_name"]] = result

    settled = 0
    result_rows = []
    for pick in pending:
        name     = pick["player_name"]
        hit_hr   = outcomes.get(name)
        odds_raw = pick.get("american_odds", "") or ""
        bet      = float(pick.get("bet_dollars") or 0)
        try:
            odds = int(float(odds_raw))
        except (ValueError, TypeError):
            odds = 0

        # Only write definitive outcomes — skip unknowns so they stay retryable.
        if hit_hr is None:
            continue

        result_rows.append({
            **pick,
            "hr_result":   1 if hit_hr else 0,
            "profit_loss": _compute_pl(bet, odds, hit_hr),
            "notes":       "",
        })
        settled += 1

    if result_rows:
        if _sheets.available():
            _sheets.append_rows("results", RESULTS_FIELDS, result_rows)
        else:
            _append_csv(RESULTS_PATH, RESULTS_FIELDS, result_rows)

    return {"settled": settled, "not_found": len(pending) - settled, "date": date_str}


def pnl_summary() -> dict:
    """Return running P&L stats from settled results."""
    rows = _load_results()
    if not rows:
        return {}

    total_bet, total_profit, wins, losses, pending = 0.0, 0.0, 0, 0, 0
    for row in rows:
        bet = float(row.get("bet_dollars") or 0)
        pl  = row.get("profit_loss", "")
        total_bet += bet
        if pl == "" or pl is None:
            pending += 1
        else:
            profit = float(pl)
            total_profit += profit
            if profit > 0:
                wins += 1
            else:
                losses += 1

    decided = wins + losses
    return {
        "total_picks":   decided + pending,
        "wins":          wins,
        "losses":        losses,
        "pending":       pending,
        "win_rate":      wins / decided if decided else 0,
        "total_wagered": total_bet,
        "total_profit":  total_profit,
        "roi_pct":       total_profit / total_bet * 100 if total_bet > 0 else 0,
        "backend":       storage_backend(),
    }


def get_picks_log() -> list[dict]:
    """Return all picks ever logged, newest first."""
    if _sheets.available():
        rows = _sheets.read_rows("picks_log")
    else:
        if not LOG_PATH.exists():
            return []
        with open(LOG_PATH, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    return list(reversed(rows))


# â”€â”€ Internal helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _pick_row(p: dict, today: str, model_version: str) -> dict:
    return {
        "date":            today,
        "model_version":   model_version,
        "player_id":       p.get("player_id", ""),
        "player_name":     p.get("player_name", ""),
        "team":            p.get("team", ""),
        "opponent":        p.get("opponent", ""),
        "pitcher":         p.get("pitcher_name", ""),
        "lineup_spot":     p.get("lineup_spot", ""),
        "model_prob_pct":  f"{p.get('model_prob', 0)*100:.2f}",
        "market_prob_pct": f"{p.get('market_no_vig_prob', 0)*100:.2f}",
        "ev_pct":          f"{p.get('ev_pct', 0):.2f}",
        "edge_pct":        f"{p.get('edge_pct', 0):.2f}",
        "american_odds":   p.get("best_american", ""),
        "bet_dollars":     f"{p.get('bet_dollars', 0):.2f}",
        "park_factor":     f"{p.get('park_factor', 1):.3f}",
        "pitcher_factor":  f"{p.get('pitcher_factor', 1):.3f}",
        "weather_factor":  f"{p.get('weather_factor', 1):.3f}",
        "season_pa":       p.get("season_pa", ""),
        "recent_pa":       p.get("recent_pa", ""),
        "confidence":      f"{p.get('confidence', 0):.1f}",
        "score":           f"{p.get('score', 0):.2f}",
    }


def _load_pending(date_str: str) -> list[dict]:
    """Load picks for a date that haven't been settled yet."""
    if _sheets.available():
        all_picks = _sheets.read_rows("picks_log")
        settled_names = {r.get("player_name") for r in _load_results()
                         if str(r.get("date", "")) == date_str}
        return [r for r in all_picks
                if str(r.get("date", "")) == date_str
                and r.get("player_name") not in settled_names]
    else:
        if not LOG_PATH.exists():
            return []
        with open(LOG_PATH, newline="", encoding="utf-8") as f:
            all_picks = list(csv.DictReader(f))
        # Check which are already settled
        settled_names: set[str] = set()
        if RESULTS_PATH.exists():
            with open(RESULTS_PATH, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("date") == date_str:
                        settled_names.add(row.get("player_name", ""))
        return [r for r in all_picks
                if r.get("date") == date_str
                and r.get("player_name") not in settled_names]


def _load_results() -> list[dict]:
    if _sheets.available():
        return _sheets.read_rows("results")
    if not RESULTS_PATH.exists():
        return []
    with open(RESULTS_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _append_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
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
        return {row.get("date", "") for row in csv.DictReader(f)}


def _mlb_hr_result(player_id: int, date_str: str) -> Optional[bool]:
    try:
        resp = requests.get(
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats",
            params={"stats": "gameLog", "group": "hitting", "season": date_str[:4]},
            timeout=10,
        )
        splits = resp.json().get("stats", [{}])[0].get("splits", [])
        for split in splits:
            if split.get("date") == date_str:
                return int(split.get("stat", {}).get("homeRuns", 0)) > 0
        # Date not in game log — player may not have played (DNP/scratch/postponement).
        # Return None so the pick stays pending and is retried rather than settled as a loss.
        return None
    except Exception:
        return None


def _compute_pl(bet: float, odds: int, hit_hr: bool) -> float:
    """Calculate profit/loss for a settled pick."""
    if hit_hr:
        return round(bet * odds / 100, 2) if odds > 0 else round(bet * 100 / abs(odds), 2)
    return round(-bet, 2)

