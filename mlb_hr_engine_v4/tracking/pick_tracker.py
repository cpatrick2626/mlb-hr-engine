"""
Unified Pick Tracker

Logs every pick from every tab/section with full model context.
Settlement fills in hr_result / profit_loss via pnl._settle_date().

Performance notes:
- _load_all() reads the CSV once; callers receive the rows list.
- log_picks_bulk() does ONE read + ONE write regardless of batch size.
- Dedup uses a frozenset for O(1) key lookup, not a per-pick linear scan.
- summary_by() accepts an optional pre-loaded rows list to skip re-reads.
"""

import csv
import os
import unicodedata
from datetime import date, timedelta
from pathlib import Path

LOG_PATH = Path(__file__).parent / "pick_tracker.csv"

FIELDS = [
    "date", "source_tab", "source_section",
    "player_name", "team", "player_id",
    "american_odds", "bet_dollars",
    "model_prob_pct", "ev_pct", "edge_pct", "confidence",
    "park_factor", "pitcher_factor", "platoon_factor", "weather_factor", "streak_factor",
    "sweet_spot_pct", "arsenal_factor", "pulled_air_ball_factor",
    "barrel_pct", "exit_velo", "hard_hit_pct", "launch_angle",
    "xslg", "slg", "iso", "pull_pct",
    "pitcher_hr9", "pitcher_k_pct",
    "lineup_spot",
    "hr_result", "profit_loss",
]


# ── Public API ────────────────────────────────────────────────────────────────

def log_pick(player: dict, source_tab: str, source_section: str = "") -> bool:
    """Log one pick. Returns True if newly added."""
    return log_picks_bulk([player], source_tab, source_section) == 1


def log_picks_bulk(players: list[dict], source_tab: str, source_section: str = "") -> int:
    """
    Log multiple players in one read + one write.
    Returns count of newly added rows (skips duplicates).
    """
    if not players:
        return 0

    today     = date.today().isoformat()
    all_rows  = _load_all()
    # Build O(1) dedup key set
    existing  = frozenset(
        (r.get("date"), r.get("source_tab"), r.get("source_section"), r.get("player_name"))
        for r in all_rows
    )

    new_rows = []
    for player in players:
        name = player.get("player_name", "")
        key  = (today, source_tab, source_section, name)
        if key in existing:
            continue
        existing = existing | {key}   # update so duplicates within the batch are also caught
        new_rows.append(_build_row(player, today, source_tab, source_section))

    if new_rows:
        _append(new_rows)
    return len(new_rows)


def settle_date(date_str: str, outcomes: dict[str, bool]) -> int:
    """
    Fill hr_result / profit_loss for unsettled picks on date_str.
    Returns count of newly settled rows.
    """
    if not LOG_PATH.exists():
        return 0
    rows    = _load_all()
    changed = 0
    for row in rows:
        if row.get("date") != date_str or row.get("hr_result") not in ("", None):
            continue
        name = row.get("player_name", "")
        norm_name = _norm(name)
        hit_hr = next((v for k, v in outcomes.items() if _norm(k) == norm_name), None)
        if hit_hr is None:
            continue
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
    """All picks newest-first. limit=0 means no limit."""
    rows = list(reversed(_load_all()))
    return rows[:limit] if limit else rows


def settled_rows(rows: list[dict] | None = None) -> list[dict]:
    """Rows with a definitive outcome. Pass pre-loaded rows to skip re-read."""
    src = rows if rows is not None else _load_all()
    return [r for r in src if r.get("hr_result") in ("0", "1")]


def summary_by(group_field: str, rows: list[dict] | None = None) -> list[dict]:
    """
    Aggregate performance by any field (source_tab, source_section, etc.).
    Pass pre-loaded rows to avoid re-reading the CSV.
    Returns list sorted by decided picks desc then ROI desc.
    """
    src = rows if rows is not None else _load_all()
    agg: dict[str, dict] = {}
    for row in src:
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
        if hr == "void":
            pass   # excluded from all P&L totals
        elif hr == "":
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
        decided  = a["wins"] + a["losses"]
        win_rate = a["wins"] / decided if decided else None
        roi      = (a["profit"] / a["wagered"] * 100) if a["wagered"] > 0 else None
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


def total_summary(rows: list[dict] | None = None) -> dict:
    """Overall totals. Pass pre-loaded rows to avoid re-read."""
    src = rows if rows is not None else _load_all()
    picks, wins, losses, pending, wagered, profit = 0, 0, 0, 0, 0.0, 0.0
    for r in src:
        picks += 1
        hr = r.get("hr_result", "")
        try:
            bet = float(r.get("bet_dollars", "10") or "10")
        except (ValueError, TypeError):
            bet = 10.0
        if hr == "void":
            pass   # excluded from all P&L totals
        elif hr == "":
            pending += 1
        else:
            wagered += bet
            try:
                profit += float(r.get("profit_loss", 0) or 0)
            except (ValueError, TypeError):
                pass
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


def load_all() -> list[dict]:
    """Public read — returns all rows. Use this when you need the raw rows."""
    return _load_all()


def expire_stale(days: int = 7) -> int:
    """
    Mark pending picks older than `days` with no settled result as void.
    Returns count newly expired.
    """
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    rows   = _load_all()
    changed = 0
    for row in rows:
        if row.get("date", "") >= cutoff:
            continue
        if row.get("hr_result", "") not in ("", None):
            continue
        row["hr_result"]   = "void"
        row["profit_loss"] = "0.00"
        changed += 1
    if changed:
        _rewrite(rows)
    return changed


# ── Internal ──────────────────────────────────────────────────────────────────

def _norm(name: str) -> str:
    """Fold accents and lowercase for robust name matching (e.g. 'José' → 'jose')."""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower().strip()


def _load_all() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _append(rows: list[dict]) -> None:
    _atomic_write(_load_all() + rows)


def _rewrite(rows: list[dict]) -> None:
    _atomic_write(rows)


def _atomic_write(rows: list[dict]) -> None:
    tmp = LOG_PATH.with_suffix(".tmp")
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, LOG_PATH)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def _build_row(player: dict, today: str, source_tab: str, source_section: str) -> dict:
    def _f(key, default=0.0):
        try:
            v = player.get(key)
            return float(str(v).replace("%", "").strip()) if v is not None else default
        except (TypeError, ValueError):
            return default

    odds = player.get("fanduel_american") or player.get("best_american") or ""
    bet  = _f("bet_dollars") or 10.0
    return {
        "date":           today,
        "source_tab":     source_tab,
        "source_section": source_section,
        "player_name":    player.get("player_name", ""),
        "team":           player.get("team", ""),
        "player_id":      player.get("player_id", ""),
        "american_odds":  str(odds),
        "bet_dollars":    f"{bet:.2f}",
        "model_prob_pct": f"{_f('model_prob') * 100:.2f}",
        "ev_pct":         f"{_f('ev_pct'):.2f}",
        "edge_pct":       f"{_f('edge_pct'):.2f}",
        "confidence":     f"{_f('confidence'):.1f}",
        "park_factor":    f"{_f('park_factor', 1.0):.4f}",
        "pitcher_factor": f"{_f('pitcher_factor', 1.0):.4f}",
        "platoon_factor": f"{_f('platoon_factor', 1.0):.4f}",
        "weather_factor": f"{_f('weather_factor', 1.0):.4f}",
        "streak_factor":          f"{_f('streak_factor', 1.0):.4f}",
        "sweet_spot_pct":         f"{_f('sweet_spot_pct'):.2f}",
        "arsenal_factor":         f"{_f('arsenal_factor', 1.0):.4f}",
        "pulled_air_ball_factor": f"{_f('pulled_air_ball_factor', 1.0):.4f}",
        "barrel_pct":             f"{_f('barrel_pct') or _f('brl_pct'):.2f}",
        "exit_velo":      f"{_f('exit_velo'):.1f}",
        "hard_hit_pct":   f"{_f('hard_hit_pct') or _f('hh_pct'):.2f}",
        "launch_angle":   f"{_f('launch_angle') or _f('la'):.1f}",
        "xslg":           f"{_f('xslg') or _f('x_slg'):.4f}",
        "slg":            f"{_f('slg'):.4f}",
        "iso":            f"{_f('iso'):.4f}",
        "pull_pct":       f"{_f('pull_pct'):.2f}",
        "pitcher_hr9":    f"{_f('pitcher_hr9'):.3f}",
        "pitcher_k_pct":  f"{_f('pitcher_k_pct'):.4f}",
        "lineup_spot":    str(player.get("lineup_spot", "")),
        "hr_result":      "",
        "profit_loss":    "",
    }


def _pl(bet: float, odds: int, hit_hr: bool) -> float:
    if hit_hr:
        return bet * odds / 100 if odds > 0 else (bet * 100 / abs(odds) if odds != 0 else 0.0)
    return -bet
