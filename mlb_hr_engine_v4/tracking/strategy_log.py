"""
Strategy Performance Tracker

Records every pick added to the FD Slip from the Advanced Strategies tab,
tagged by strategy name. Settlement is driven by the same MLB API outcomes
fetched by pnl.py (via settle_date()).

Storage: tracking/strategy_log.csv  (local CSV, no Sheets dependency)
P&L uses the player's bet_dollars; falls back to a $10 flat unit.
"""

import csv
from datetime import date
from pathlib import Path

LOG_PATH = Path(__file__).parent / "strategy_log.csv"

FIELDS = [
    "date", "strategy", "player_name", "team",
    "american_odds", "model_prob_pct", "ev_pct",
    "bet_dollars", "hr_result", "profit_loss",
]


# ── Public API ────────────────────────────────────────────────────────────────

def log_pick(player: dict, strategy: str) -> bool:
    """
    Record a strategy-sourced pick.
    Returns True if newly added, False if already logged today for this strategy.
    """
    today = date.today().isoformat()
    name  = player.get("player_name", "")
    existing = _load_all()
    for row in existing:
        if row.get("date") == today and row.get("strategy") == strategy and row.get("player_name") == name:
            return False

    odds = player.get("fanduel_american") or player.get("best_american") or ""
    bet  = player.get("bet_dollars", 0) or 10.0
    try:
        bet = float(bet)
    except (TypeError, ValueError):
        bet = 10.0

    _append([{
        "date":            today,
        "strategy":        strategy,
        "player_name":     name,
        "team":            player.get("team", ""),
        "american_odds":   str(odds),
        "model_prob_pct":  f"{player.get('model_prob', 0) * 100:.2f}",
        "ev_pct":          f"{player.get('ev_pct', 0):.2f}",
        "bet_dollars":     f"{bet:.2f}",
        "hr_result":       "",
        "profit_loss":     "",
    }])
    return True


def settle_date(date_str: str, outcomes: dict[str, bool]) -> int:
    """
    Fill in hr_result / profit_loss for all unsettled picks on date_str.
    outcomes maps player_name → True/False (hit HR or not).
    Returns count of rows newly settled.
    """
    if not LOG_PATH.exists():
        return 0
    rows = _load_all()
    changed = 0
    for row in rows:
        if row.get("date") != date_str:
            continue
        if row.get("hr_result") not in ("", None):
            continue
        name = row.get("player_name", "")
        if name not in outcomes:
            continue
        hit_hr = outcomes[name]
        try:
            odds = int(float(row.get("american_odds", "0") or "0"))
        except (ValueError, TypeError):
            odds = 0
        try:
            bet = float(row.get("bet_dollars", "10") or "10")
        except (ValueError, TypeError):
            bet = 10.0
        row["hr_result"]   = "1" if hit_hr else "0"
        row["profit_loss"] = f"{_pl(bet, odds, hit_hr):.2f}"
        changed += 1
    if changed:
        _rewrite(rows)
    return changed


def all_picks() -> list[dict]:
    """All logged picks, newest first."""
    return list(reversed(_load_all()))


def summary() -> list[dict]:
    """
    Per-strategy aggregated performance.
    Returns list of dicts sorted by decided picks desc, then net ROI desc.
    """
    rows = _load_all()
    agg: dict[str, dict] = {}
    for row in rows:
        strat = row.get("strategy", "Unknown") or "Unknown"
        if strat not in agg:
            agg[strat] = {
                "picks": 0, "wins": 0, "losses": 0, "pending": 0,
                "profit": 0.0, "wagered": 0.0, "last_date": "",
            }
        a = agg[strat]
        a["picks"]     += 1
        a["last_date"]  = max(a["last_date"], row.get("date", ""))
        hr = row.get("hr_result", "")
        pl = row.get("profit_loss", "")
        try:
            bet = float(row.get("bet_dollars", "10") or "10")
        except (ValueError, TypeError):
            bet = 10.0
        if hr == "":
            a["pending"] += 1
        else:
            a["wagered"] += bet
            a["profit"]  += float(pl) if pl else 0.0
            if hr == "1":
                a["wins"]   += 1
            else:
                a["losses"] += 1

    result = []
    for strat, a in agg.items():
        decided = a["wins"] + a["losses"]
        win_rate = a["wins"] / decided if decided else None
        roi      = (a["profit"] / a["wagered"] * 100) if a["wagered"] > 0 else None
        result.append({
            "Strategy":  strat,
            "Picks":     a["picks"],
            "Wins":      a["wins"],
            "Losses":    a["losses"],
            "Pending":   a["pending"],
            "Win%":      f"{win_rate*100:.1f}%" if win_rate is not None else "—",
            "Net P&L":   f"${a['profit']:+.2f}" if decided else "—",
            "ROI%":      f"{roi:+.1f}%" if roi is not None else "—",
            "Last Pick": a["last_date"],
            # raw values for sorting / conditional formatting
            "_decided":  decided,
            "_roi":      roi if roi is not None else 0.0,
            "_profit":   a["profit"],
            "_win_rate": win_rate if win_rate is not None else 0.0,
        })
    return sorted(result, key=lambda x: (x["_decided"], x["_roi"]), reverse=True)


def delete_pick(date_str: str, strategy: str, player_name: str) -> bool:
    """Remove a specific unsettled pick. Returns True if removed."""
    rows = _load_all()
    before = len(rows)
    rows = [
        r for r in rows
        if not (r.get("date") == date_str and r.get("strategy") == strategy
                and r.get("player_name") == player_name and not r.get("hr_result"))
    ]
    if len(rows) < before:
        _rewrite(rows)
        return True
    return False


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_all() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _append(rows: list[dict]) -> None:
    write_header = not LOG_PATH.exists()
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerows(rows)


def _rewrite(rows: list[dict]) -> None:
    with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _pl(bet: float, odds: int, hit_hr: bool) -> float:
    if hit_hr:
        return bet * odds / 100 if odds > 0 else (bet * 100 / abs(odds) if odds != 0 else 0.0)
    return -bet
