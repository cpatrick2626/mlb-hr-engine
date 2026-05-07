"""
Unified Pick Tracker — logs every pick from every tab/section with full model context.

Fields captured at pick time (snapshot of what the model saw) plus outcome fields
filled in later by settle_date(). This gives auto_learn.py the feature vectors it
needs to compute correlations and calibration.

Storage: tracking/pick_tracker.csv  (local CSV; no Sheets dependency)
Settlement: driven by pnl._settle_date() via settle_date() below.
"""

import csv
from datetime import date
from pathlib import Path

LOG_PATH = Path(__file__).parent / "pick_tracker.csv"

FIELDS = [
    # Context
    "date", "source_tab", "source_section",
    # Identity
    "player_name", "team", "player_id",
    # Market
    "american_odds", "bet_dollars",
    # Model outputs
    "model_prob_pct", "ev_pct", "edge_pct", "confidence",
    # Game-day factors (multiplicative adjustments applied to base rate)
    "park_factor", "pitcher_factor", "platoon_factor", "weather_factor", "streak_factor",
    # Power / Statcast metrics (raw values)
    "barrel_pct", "exit_velo", "hard_hit_pct", "launch_angle",
    # Slash stats
    "xslg", "slg", "iso", "pull_pct",
    # Pitcher context
    "pitcher_hr9", "pitcher_k_pct",
    # Lineup
    "lineup_spot",
    # Outcome (filled by settle_date)
    "hr_result", "profit_loss",
]


# ── Public API ────────────────────────────────────────────────────────────────

def log_pick(player: dict, source_tab: str, source_section: str = "") -> bool:
    """
    Record one pick with its source and full model context.
    Returns True if newly added; False if this player is already logged
    today from the same source_tab + source_section.
    """
    today = date.today().isoformat()
    name  = player.get("player_name", "")
    rows  = _load_all()
    for r in rows:
        if (r.get("date") == today
                and r.get("source_tab") == source_tab
                and r.get("source_section") == source_section
                and r.get("player_name") == name):
            return False

    def _f(key, default=0.0):
        try:
            v = player.get(key)
            return float(str(v).replace("%", "").strip()) if v is not None else default
        except (TypeError, ValueError):
            return default

    odds = player.get("fanduel_american") or player.get("best_american") or ""
    bet  = _f("bet_dollars") or 10.0

    _append([{
        "date":            today,
        "source_tab":      source_tab,
        "source_section":  source_section,
        "player_name":     name,
        "team":            player.get("team", ""),
        "player_id":       player.get("player_id", ""),
        "american_odds":   str(odds),
        "bet_dollars":     f"{bet:.2f}",
        "model_prob_pct":  f"{_f('model_prob') * 100:.2f}",
        "ev_pct":          f"{_f('ev_pct'):.2f}",
        "edge_pct":        f"{_f('edge_pct'):.2f}",
        "confidence":      f"{_f('confidence'):.1f}",
        "park_factor":     f"{_f('park_factor', 1.0):.4f}",
        "pitcher_factor":  f"{_f('pitcher_factor', 1.0):.4f}",
        "platoon_factor":  f"{_f('platoon_factor', 1.0):.4f}",
        "weather_factor":  f"{_f('weather_factor', 1.0):.4f}",
        "streak_factor":   f"{_f('streak_factor', 1.0):.4f}",
        "barrel_pct":      f"{_f('barrel_pct') or _f('brl_pct'):.2f}",
        "exit_velo":       f"{_f('exit_velo'):.1f}",
        "hard_hit_pct":    f"{_f('hard_hit_pct') or _f('hh_pct'):.2f}",
        "launch_angle":    f"{_f('launch_angle') or _f('la'):.1f}",
        "xslg":            f"{_f('xslg') or _f('x_slg'):.4f}",
        "slg":             f"{_f('slg'):.4f}",
        "iso":             f"{_f('iso'):.4f}",
        "pull_pct":        f"{_f('pull_pct'):.2f}",
        "pitcher_hr9":     f"{_f('pitcher_hr9'):.3f}",
        "pitcher_k_pct":   f"{_f('pitcher_k_pct'):.4f}",
        "lineup_spot":     str(player.get("lineup_spot", "")),
        "hr_result":       "",
        "profit_loss":     "",
    }])
    return True


def log_picks_bulk(players: list[dict], source_tab: str, source_section: str = "") -> int:
    """Log multiple players at once; returns count of newly logged."""
    return sum(1 for p in players if log_pick(p, source_tab, source_section))


def settle_date(date_str: str, outcomes: dict[str, bool]) -> int:
    """
    Fill hr_result / profit_loss for unsettled picks on date_str.
    outcomes maps player_name → True (HR) / False (no HR).
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


def all_picks(limit: int = 0) -> list[dict]:
    """All picks, newest first. limit=0 means no limit."""
    rows = list(reversed(_load_all()))
    return rows[:limit] if limit else rows


def summary_by(group_field: str) -> list[dict]:
    """
    Aggregate performance by any field (source_tab, source_section, etc.).
    Returns list of dicts sorted by decided picks desc then ROI desc.
    """
    rows = _load_all()
    agg: dict[str, dict] = {}
    for row in rows:
        key = row.get(group_field, "Unknown") or "Unknown"
        if key not in agg:
            agg[key] = {"picks": 0, "wins": 0, "losses": 0, "pending": 0,
                        "profit": 0.0, "wagered": 0.0, "last_date": ""}
        a = agg[key]
        a["picks"]    += 1
        a["last_date"] = max(a["last_date"], row.get("date", ""))
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
                a["wins"] += 1
            else:
                a["losses"] += 1

    result = []
    for key, a in agg.items():
        decided   = a["wins"] + a["losses"]
        win_rate  = a["wins"] / decided if decided else None
        roi       = (a["profit"] / a["wagered"] * 100) if a["wagered"] > 0 else None
        result.append({
            group_field:  key,
            "Picks":      a["picks"],
            "Wins":       a["wins"],
            "Losses":     a["losses"],
            "Pending":    a["pending"],
            "Win%":       f"{win_rate*100:.1f}%" if win_rate is not None else "—",
            "Net P&L":    f"${a['profit']:+.2f}" if decided else "—",
            "ROI%":       f"{roi:+.1f}%" if roi is not None else "—",
            "Last Pick":  a["last_date"],
            "_decided":   decided,
            "_roi":       roi or 0.0,
            "_profit":    a["profit"],
            "_win_rate":  win_rate or 0.0,
        })
    return sorted(result, key=lambda x: (x["_decided"], x["_roi"]), reverse=True)


def settled_rows() -> list[dict]:
    """All rows with a definitive outcome (hr_result = '0' or '1')."""
    return [r for r in _load_all() if r.get("hr_result") in ("0", "1")]


def total_summary() -> dict:
    """Overall totals across all picks."""
    rows = _load_all()
    picks, wins, losses, pending, wagered, profit = 0, 0, 0, 0, 0.0, 0.0
    for r in rows:
        picks += 1
        hr = r.get("hr_result", "")
        try:
            bet = float(r.get("bet_dollars", "10") or "10")
        except (ValueError, TypeError):
            bet = 10.0
        if hr == "":
            pending += 1
        else:
            wagered += bet
            profit  += float(r.get("profit_loss", 0) or 0)
            if hr == "1":
                wins += 1
            else:
                losses += 1
    decided = wins + losses
    return {
        "picks":    picks,
        "wins":     wins,
        "losses":   losses,
        "pending":  pending,
        "decided":  decided,
        "win_rate": wins / decided if decided else 0.0,
        "wagered":  wagered,
        "profit":   profit,
        "roi":      profit / wagered * 100 if wagered > 0 else 0.0,
    }


# ── Internal ──────────────────────────────────────────────────────────────────

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
