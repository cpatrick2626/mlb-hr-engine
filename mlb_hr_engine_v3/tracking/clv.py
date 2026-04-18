"""
Closing Line Value (CLV) tracker.

CLV measures whether the odds at the time you pick were better or worse
than the closing line. If your picks consistently beat the closing line,
the model is sharp — the market agrees with you after seeing more info.

Workflow:
  1. log_opening_lines(picks) saves odds at time of pick (morning)
  2. fetch_closing_lines() pulls final odds before first pitch
  3. compute_clv() calculates edge gained/lost vs close
  4. Results written to tracking/clv_log.csv

CLV > 0 consistently means: you're getting better prices than sharp money.
CLV < 0 consistently means: the market moved against you (bad sign for model).
"""

import csv
from datetime import date
from pathlib import Path
from typing import Optional

import requests

import config

CLV_LOG = Path(__file__).parent / "clv_log.csv"

CLV_FIELDS = [
    "date", "player_name", "team", "model_prob_pct",
    "opening_american", "opening_implied_pct",
    "closing_american", "closing_implied_pct",
    "clv_pct", "notes",
]


def log_opening_lines(picks: list[dict]) -> None:
    """Save pick odds at time of model run (the 'opening' line for CLV purposes)."""
    today = date.today().isoformat()
    existing = _existing_dates()
    if today in existing:
        return

    rows = []
    for p in picks:
        odds = p.get("best_american")
        if not odds:
            continue
        implied = _implied(odds)
        rows.append({
            "date":                today,
            "player_name":         p["player_name"],
            "team":                p.get("team", ""),
            "model_prob_pct":      f"{p.get('model_prob', 0)*100:.2f}",
            "opening_american":    odds,
            "opening_implied_pct": f"{implied*100:.2f}",
            "closing_american":    "",
            "closing_implied_pct": "",
            "clv_pct":             "",
            "notes":               "",
        })

    _append(rows)


def fetch_and_compute_clv(target_date: Optional[str] = None) -> list[dict]:
    """
    For picks logged on target_date, fetch closing odds from the Odds API
    and compute CLV. Updates clv_log.csv with results.
    """
    date_str = target_date or date.today().isoformat()
    picks = _load_picks_for_date(date_str)
    if not picks:
        return []

    # Try to fetch current odds for these players
    closing = _fetch_current_hr_odds()

    updated = []
    for pick in picks:
        name = pick["player_name"]
        close_odds = closing.get(_normalize(name))
        if close_odds is None:
            updated.append({**pick, "notes": "closing line unavailable"})
            continue

        open_implied = float(pick.get("opening_implied_pct", 0)) / 100.0
        close_implied = _implied(close_odds)
        clv = (open_implied - close_implied) * 100  # positive = we got better price

        updated.append({
            **pick,
            "closing_american":    close_odds,
            "closing_implied_pct": f"{close_implied*100:.2f}",
            "clv_pct":             f"{clv:.2f}",
        })

    _rewrite(date_str, updated)
    return updated


def clv_summary() -> dict:
    """Aggregate CLV stats across all logged picks."""
    if not CLV_LOG.exists():
        return {}

    clv_vals = []
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get("clv_pct", "")
            if val:
                try:
                    clv_vals.append(float(val))
                except ValueError:
                    pass

    if not clv_vals:
        return {}

    avg = sum(clv_vals) / len(clv_vals)
    positive = sum(1 for v in clv_vals if v > 0)
    return {
        "picks_with_clv": len(clv_vals),
        "avg_clv_pct":    round(avg, 2),
        "pct_beating_close": round(positive / len(clv_vals) * 100, 1),
        "verdict": "SHARP" if avg > 0.5 else ("NEUTRAL" if avg > -0.5 else "SOFT"),
    }


# ── Internal ──────────────────────────────────────────────────────────────────

def _implied(american: int) -> float:
    if american > 0:
        return 100 / (american + 100)
    return abs(american) / (abs(american) + 100)


def _normalize(name: str) -> str:
    return name.lower().strip()


def _append(rows: list[dict]) -> None:
    write_header = not CLV_LOG.exists()
    with open(CLV_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLV_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def _load_picks_for_date(date_str: str) -> list[dict]:
    if not CLV_LOG.exists():
        return []
    rows = []
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("date") == date_str:
                rows.append(dict(row))
    return rows


def _rewrite(date_str: str, updated: list[dict]) -> None:
    all_rows = []
    if CLV_LOG.exists():
        with open(CLV_LOG, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            all_rows = [r for r in reader if r.get("date") != date_str]
    all_rows.extend(updated)
    with open(CLV_LOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)


def _existing_dates() -> set[str]:
    if not CLV_LOG.exists():
        return set()
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {r.get("date", "") for r in reader}


def _fetch_current_hr_odds() -> dict[str, int]:
    """Best available HR odds keyed by normalized player name."""
    if not config.ODDS_API_KEY:
        return {}
    try:
        resp = requests.get(
            "https://api.the-odds-api.com/v4/sports/baseball_mlb/events",
            params={"apiKey": config.ODDS_API_KEY, "dateFormat": "iso"},
            timeout=12,
        )
        events = resp.json() if resp.status_code == 200 else []
        best: dict[str, int] = {}
        for event in events:
            r2 = requests.get(
                f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{event['id']}/odds",
                params={"apiKey": config.ODDS_API_KEY, "regions": "us",
                        "markets": "batter_home_runs", "oddsFormat": "american"},
                timeout=12,
            )
            if r2.status_code != 200:
                continue
            for book in r2.json().get("bookmakers", []):
                for mkt in book.get("markets", []):
                    for o in mkt.get("outcomes", []):
                        if o.get("point") == 0.5:
                            name = _normalize(o.get("description", ""))
                            price = int(o.get("price", 0))
                            if name and (name not in best or price > best[name]):
                                best[name] = price
        return best
    except Exception:
        return {}
