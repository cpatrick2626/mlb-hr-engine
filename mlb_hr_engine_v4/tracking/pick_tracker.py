"""
Unified Pick Tracker  (Session 26 schema: v3)

Logs every pick from every tab/section with full model context.
Settlement fills in hr_result / profit_loss via pnl._settle_date().

Session 25 additions (backward-compatible):
  pick_id        — deterministic ID: sha1(date+player+source_tab)[:12]
  opponent       — opposing team
  pitcher        — opposing pitcher name
  sportsbook     — book the odds were sourced from
  best_odds      — best available American odds at pick time
  market_prob_pct— no-vig implied probability from market
  engine_version — e.g. "v4"
  logged_at      — ISO-8601 UTC timestamp of log write

Session 26 CLV additions (backward-compatible):
  open_implied_pct  — vigged implied prob from best_odds at log time (× 100)
  open_no_vig_pct   — no-vig opening probability (× 100, book-specific)
  close_odds        — closing American odds (populated by capture_closing_lines.py)
  close_no_vig_pct  — no-vig closing probability (× 100)
  clv_pp            — CLV in pp: (close_no_vig - open_no_vig) × 100 (+ = sharp)
  clv_pct_rel       — CLV relative to opening: clv_pp / open_no_vig × 100

Performance notes:
- _load_all() reads the CSV once; callers receive the rows list.
- log_picks_bulk() does ONE read + ONE write regardless of batch size.
- Dedup uses a frozenset for O(1) key lookup, not a per-pick linear scan.
- summary_by() accepts an optional pre-loaded rows list to skip re-reads.
"""

import csv
import hashlib
import os
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent / "pick_tracker.csv"

# Session 25 current version tag (bump whenever calibration params change)
ENGINE_VERSION = "v4"

FIELDS = [
    # ── Core identity ──────────────────────────────────────────────────────────
    "date", "source_tab", "source_section",
    "player_name", "team", "player_id",
    "american_odds", "bet_dollars",
    # ── Model output ──────────────────────────────────────────────────────────
    "model_prob_pct", "ev_pct", "edge_pct", "confidence",
    # ── Context multipliers ────────────────────────────────────────────────────
    "park_factor", "pitcher_factor", "platoon_factor", "weather_factor", "streak_factor",
    # ── Statcast signals ───────────────────────────────────────────────────────
    "barrel_pct", "exit_velo", "hard_hit_pct", "launch_angle",
    "xslg", "slg", "iso", "pull_pct",
    # ── Pitcher stats ──────────────────────────────────────────────────────────
    "pitcher_hr9", "pitcher_k_pct",
    # ── Lineup ────────────────────────────────────────────────────────────────
    "lineup_spot",
    # ── Session 25 additions ──────────────────────────────────────────────────
    "pick_id", "opponent", "pitcher",
    "sportsbook", "best_odds", "market_prob_pct",
    "engine_version", "logged_at",
    # ── Session 26 CLV additions ──────────────────────────────────────────────
    "open_implied_pct",    # vigged implied prob at open × 100
    "open_no_vig_pct",     # no-vig opening prob × 100
    "close_odds",          # closing American odds (from capture_closing_lines.py)
    "close_no_vig_pct",    # no-vig closing prob × 100
    "clv_pp",              # (close_no_vig - open_no_vig) × 100; + = sharp
    "clv_pct_rel",         # clv_pp / open_no_vig × 100 (relative CLV)
    # ── Settlement (filled by settle_date / pnl._settle_date) ─────────────────
    "hr_result", "profit_loss",
]

# Fields added in Session 25
_SESSION25_FIELDS = [
    "pick_id", "opponent", "pitcher",
    "sportsbook", "best_odds", "market_prob_pct",
    "engine_version", "logged_at",
]

# Fields added in Session 26
_SESSION26_FIELDS = [
    "open_implied_pct", "open_no_vig_pct",
    "close_odds", "close_no_vig_pct",
    "clv_pp", "clv_pct_rel",
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

    _migrate_schema()   # ensure CSV has all Session 25 columns before writing

    today     = date.today().isoformat()
    all_rows  = _load_all()
    # Dedup on pick_id (deterministic) — falls back to (date, tab, section, name)
    existing_ids   = frozenset(r.get("pick_id", "") for r in all_rows if r.get("pick_id"))
    existing_keys  = frozenset(
        (r.get("date"), r.get("source_tab"), r.get("source_section"), r.get("player_name"))
        for r in all_rows
    )

    new_rows = []
    for player in players:
        name   = player.get("player_name", "")
        pid    = _gen_pick_id(today, name, source_tab)
        if pid in existing_ids:
            continue
        key = (today, source_tab, source_section, name)
        if key in existing_keys:
            continue
        existing_ids  = existing_ids  | {pid}
        existing_keys = existing_keys | {key}
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

def _gen_pick_id(date_str: str, player_name: str, source_tab: str) -> str:
    """Deterministic 12-char pick ID: sha1(date+player+source)[:12].
    Same inputs → same ID, so re-logging the same pick generates the same ID (natural dedup)."""
    raw = f"{date_str}|{player_name.strip().lower()}|{source_tab.strip().lower()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _migrate_schema() -> None:
    """
    Migrate existing CSV to current schema (Sessions 25 + 26).
    Adds missing columns and backfills open_implied_pct / open_no_vig_pct from
    existing american_odds / best_odds data when present.
    Safe to call multiple times — no-op if schema already current.
    """
    if not LOG_PATH.exists():
        return
    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        existing_fields = list(reader.fieldnames or [])
        rows = list(reader)

    all_new = _SESSION25_FIELDS + _SESSION26_FIELDS
    missing = [f for f in all_new if f not in existing_fields]
    if not missing:
        return

    # Reorder so settlement fields remain last
    non_settlement = [f for f in existing_fields if f not in ("hr_result", "profit_loss")]
    settlement     = [f for f in existing_fields if f in ("hr_result", "profit_loss")]
    added          = [f for f in missing if f not in settlement]
    new_fields     = non_settlement + added + settlement

    # Backfill open_implied_pct and open_no_vig_pct from existing odds where possible
    needs_open_imp = "open_implied_pct" in missing
    needs_open_nv  = "open_no_vig_pct" in missing
    if needs_open_imp or needs_open_nv:
        for row in rows:
            odds_str = row.get("best_odds") or row.get("american_odds") or ""
            if not odds_str:
                continue
            try:
                american = int(float(odds_str))
            except (ValueError, TypeError):
                continue
            if -100 < american < 100:
                continue
            if needs_open_imp and not row.get("open_implied_pct"):
                imp = _american_to_implied(american)
                row["open_implied_pct"] = f"{imp * 100:.3f}"
            if needs_open_nv and not row.get("open_no_vig_pct"):
                book = row.get("sportsbook", "")
                nv   = _american_to_no_vig(american, book)
                row["open_no_vig_pct"] = f"{nv * 100:.3f}"

    tmp = LOG_PATH.with_suffix(".tmp")
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=new_fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        os.replace(tmp, LOG_PATH)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


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

    odds       = player.get("fanduel_american") or player.get("best_american") or ""
    bet        = _f("bet_dollars") or 10.0
    player_name = player.get("player_name", "")
    sportsbook  = player.get("best_book") or player.get("sportsbook") or ""

    # market_prob_pct: prefer explicit key, fall back to market_no_vig_prob
    mkt_raw = player.get("market_prob_pct") or player.get("market_no_vig_prob")
    if mkt_raw is not None:
        try:
            mkt_p = float(str(mkt_raw).replace("%","").strip())
            # If value looks like a fraction (0 < x < 1), convert to pct
            if mkt_p and mkt_p < 1.0:
                mkt_p = mkt_p * 100
            market_prob_str = f"{mkt_p:.2f}"
        except (ValueError, TypeError):
            market_prob_str = ""
    else:
        market_prob_str = ""

    return {
        "date":            today,
        "source_tab":      source_tab,
        "source_section":  source_section,
        "player_name":     player_name,
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
        # Session 25 fields
        "pick_id":         _gen_pick_id(today, player_name, source_tab),
        "opponent":        player.get("opponent", ""),
        "pitcher":         player.get("pitcher_name", "") or player.get("pitcher", ""),
        "sportsbook":      sportsbook,
        "best_odds":       str(odds),
        "market_prob_pct": market_prob_str,
        "engine_version":  ENGINE_VERSION,
        "logged_at":       datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # Session 26: CLV opening fields — computed at log time from best_odds
        **_build_clv_open_fields(odds, sportsbook),
        # Settlement
        "hr_result":       "",
        "profit_loss":     "",
    }


def _pl(bet: float, odds: int, hit_hr: bool) -> float:
    if hit_hr:
        return bet * odds / 100 if odds > 0 else (bet * 100 / abs(odds) if odds != 0 else 0.0)
    return -bet


def _build_clv_open_fields(odds_raw, sportsbook: str) -> dict:
    """Compute Session 26 opening CLV fields from odds at log time."""
    try:
        american = int(float(str(odds_raw).strip()))
        if -100 < american < 100:
            raise ValueError
    except (ValueError, TypeError):
        return {f: "" for f in _SESSION26_FIELDS}

    imp = _american_to_implied(american)
    nv  = _american_to_no_vig(american, sportsbook)
    return {
        "open_implied_pct": f"{imp * 100:.3f}",
        "open_no_vig_pct":  f"{nv * 100:.3f}",
        "close_odds":        "",
        "close_no_vig_pct":  "",
        "clv_pp":            "",
        "clv_pct_rel":       "",
    }


def _american_to_implied(american: int) -> float:
    if american > 0:
        return 100.0 / (american + 100.0)
    return abs(american) / (abs(american) + 100.0)


def _american_to_no_vig(american: int, book: str = "") -> float:
    try:
        import sys, os
        from pathlib import Path
        _v4 = Path(__file__).parent.parent
        if str(_v4) not in sys.path:
            sys.path.insert(0, str(_v4))
        from engine.vig import no_vig_prob_for_book
        return no_vig_prob_for_book(american, book)
    except Exception:
        imp = _american_to_implied(american)
        return imp / 1.075  # fallback global vig


# ── Session 26: CLV field update ─────────────────────────────────────────────

def update_clv_fields(
    date_str: str,
    player_name: str,
    close_odds: int,
    close_no_vig_pct: float,
    sportsbook: str = "",
) -> bool:
    """
    Write CLV fields for a settled (or unsettled) pick in pick_tracker.csv.
    Called by capture_closing_lines.py after fetching closing odds.

    Returns True if a matching row was found and updated.
    """
    _migrate_schema()
    rows   = _load_all()
    norm   = _norm(player_name)
    found  = False

    for row in rows:
        if row.get("date") != date_str:
            continue
        if _norm(row.get("player_name", "")) != norm:
            continue
        if row.get("close_odds"):   # already populated — don't overwrite
            continue

        # Recompute open_no_vig from best_odds if not already filled
        if not row.get("open_no_vig_pct"):
            odds_str = row.get("best_odds") or row.get("american_odds") or ""
            try:
                open_am = int(float(odds_str))
                bk = row.get("sportsbook", "") or sportsbook
                nv = _american_to_no_vig(open_am, bk)
                row["open_no_vig_pct"] = f"{nv * 100:.3f}"
                if not row.get("open_implied_pct"):
                    imp = _american_to_implied(open_am)
                    row["open_implied_pct"] = f"{imp * 100:.3f}"
            except (ValueError, TypeError):
                pass

        open_nv_str = row.get("open_no_vig_pct", "")
        try:
            open_nv = float(open_nv_str) / 100.0
        except (ValueError, TypeError):
            open_nv = 0.0

        row["close_odds"]       = close_odds
        row["close_no_vig_pct"] = f"{close_no_vig_pct:.3f}"

        if open_nv > 0:
            clv_pp  = (close_no_vig_pct / 100.0 - open_nv) * 100
            clv_pp  = max(-100.0, min(100.0, clv_pp))
            clv_rel = (clv_pp / (open_nv * 100)) * 100
            row["clv_pp"]       = f"{clv_pp:.3f}"
            row["clv_pct_rel"]  = f"{clv_rel:.2f}"

        found = True

    if found:
        _rewrite(rows)
    return found
