#!/usr/bin/env python3
"""
analyze_live_roi.py  --  Session 25: Real-World Pick Tracking & Live ROI Validation
====================================================================================

Combines all settled pick data from:
  pick_tracker.csv  (primary -- settled by settle_pick_tracker.py)
  results.csv       (secondary -- settled by pnl.py / main.py)
  clv_log.csv       (CLV data)

Phases:
  2  Live ROI tracking     (total, rolling, segmented, drawdown, streaks)
  3  Closing line analysis  (CLV, line movement, market efficiency)
  4  Real vs synthetic ROI  (Session 24 synthetic vs actual settled outcomes)
  5  Production monitoring  (calibration drift, EV realization, threshold audit)

IMPORTANT RULES (Session 25):
  Do NOT optimize based on tiny live samples.
  Statistical flags shown on every table where n < 50.
  All conclusions explicitly caveatted where sample is insufficient.

Usage:
  py -3.12 analyze_live_roi.py
"""

import csv
import math
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT          = Path(__file__).parent
TRACKER_PATH  = ROOT / "mlb_hr_engine_v4" / "tracking" / "pick_tracker.csv"
RESULTS_PATH  = ROOT / "mlb_hr_engine_v4" / "tracking" / "results.csv"
CLV_PATH      = ROOT / "mlb_hr_engine_v4" / "tracking" / "clv_log.csv"
OUT_PATH      = ROOT / "live_roi_output.txt"

# Session 24 synthetic ROI benchmarks by barrel tier (for Phase 4 comparison)
SYNTHETIC_ROI = {
    "<4%":    -100.0,
    "4-6%":    -2.7,
    "6-8%":    -1.3,
    "8-10%":  +28.0,
    "10-12%": +65.3,
    "12%+":  +119.3,
}

# Synthetic edge breakeven (Session 24 finding: barrel >= 8% required)
SYNTHETIC_EDGE_BREAKEVEN = "8%"

# Production thresholds
MIN_EV_PCT   = 3.0
MIN_EDGE_PCT = 2.0
TIGHTER_EV   = 4.0
TIGHTER_EDGE = 2.5

# Minimum sample for statistical reliability
MIN_RELIABLE_N = 50


# ── Formatting ────────────────────────────────────────────────────────────────

def _hdr(title: str, width: int = 105) -> str:
    sep = "=" * width
    return f"\n{sep}\n{title.center(width)}\n{sep}"


def _sub(title: str, width: int = 105) -> str:
    return f"\n{'--' * 52}\n  {title}\n{'--' * 52}"


def _pct(v: float) -> str:
    return f"{v:+.2f}pp"


def _trow(cells: list, widths: list) -> str:
    return "  ".join(str(c)[:w].ljust(w) for c, w in zip(cells, widths))


def _warn(n: int) -> str:
    return f"  [!] n={n} < {MIN_RELIABLE_N} -- treat as directional only, not statistically significant" if n < MIN_RELIABLE_N else ""


# ── Data loading ──────────────────────────────────────────────────────────────

def _safe_float(v, default=0.0) -> float:
    try:
        return float(str(v).strip()) if v and str(v).strip() not in ("None", "") else default
    except (ValueError, TypeError):
        return default


def _safe_int(v, default=0) -> int:
    try:
        return int(float(str(v).strip())) if v and str(v).strip() not in ("None", "") else default
    except (ValueError, TypeError):
        return default


def load_tracker() -> list[dict]:
    """Load settled pick_tracker.csv rows (hr_result in 0/1)."""
    if not TRACKER_PATH.exists():
        return []
    rows = []
    with open(TRACKER_PATH, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            if raw.get("hr_result", "").strip() not in ("0", "1"):
                continue
            try:
                r = {
                    "source":        "tracker",
                    "date":          raw["date"],
                    "player_name":   raw["player_name"],
                    "team":          raw.get("team", ""),
                    "player_id":     raw.get("player_id", ""),
                    "opponent":      raw.get("opponent", ""),
                    "pitcher":       raw.get("pitcher", ""),
                    "sportsbook":    raw.get("sportsbook", ""),
                    "american_odds": _safe_int(raw.get("american_odds") or raw.get("best_odds")),
                    "bet_dollars":   _safe_float(raw.get("bet_dollars"), 0.0),
                    "model_prob":    _safe_float(raw.get("model_prob_pct")) / 100.0,
                    "market_prob":   _safe_float(raw.get("market_prob_pct")) / 100.0,
                    "ev_pct":        _safe_float(raw.get("ev_pct")),
                    "edge_pct":      _safe_float(raw.get("edge_pct")),
                    "confidence":    _safe_float(raw.get("confidence")),
                    "barrel_pct":    _safe_float(raw.get("barrel_pct")),
                    "park_factor":   _safe_float(raw.get("park_factor"), 1.0),
                    "pitcher_factor":_safe_float(raw.get("pitcher_factor"), 1.0),
                    "platoon_factor":_safe_float(raw.get("platoon_factor"), 1.0),
                    "lineup_spot":   _safe_int(raw.get("lineup_spot")),
                    "hit_hr":        1 if raw["hr_result"] == "1" else 0,
                    "profit_loss":   _safe_float(raw.get("profit_loss")),
                    "source_tab":    raw.get("source_tab", ""),
                    "source_section":raw.get("source_section", ""),
                    "engine_version":raw.get("engine_version", ""),
                }
                rows.append(r)
            except (ValueError, KeyError):
                continue
    return rows


def load_results() -> list[dict]:
    """Load settled rows from results.csv (legacy pnl tracking)."""
    if not RESULTS_PATH.exists():
        return []
    rows = []
    with open(RESULTS_PATH, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            if raw.get("hr_result", "").strip() not in ("0", "1"):
                continue
            try:
                r = {
                    "source":        "results",
                    "date":          raw.get("date", ""),
                    "player_name":   raw.get("player_name", ""),
                    "team":          raw.get("team", ""),
                    "player_id":     raw.get("player_id", ""),
                    "opponent":      raw.get("opponent", ""),
                    "pitcher":       raw.get("pitcher", ""),
                    "sportsbook":    "",
                    "american_odds": _safe_int(raw.get("american_odds")),
                    "bet_dollars":   _safe_float(raw.get("bet_dollars"), 0.0),
                    "model_prob":    _safe_float(raw.get("model_prob_pct")) / 100.0,
                    "market_prob":   _safe_float(raw.get("market_prob_pct")) / 100.0,
                    "ev_pct":        _safe_float(raw.get("ev_pct")),
                    "edge_pct":      _safe_float(raw.get("edge_pct")),
                    "confidence":    _safe_float(raw.get("confidence")),
                    "barrel_pct":    _safe_float(raw.get("barrel_pct")),
                    "park_factor":   _safe_float(raw.get("park_factor"), 1.0),
                    "pitcher_factor":_safe_float(raw.get("pitcher_factor"), 1.0),
                    "platoon_factor":_safe_float(raw.get("platoon_factor"), 1.0),
                    "lineup_spot":   _safe_int(raw.get("lineup_spot")),
                    "hit_hr":        1 if raw["hr_result"] == "1" else 0,
                    "profit_loss":   _safe_float(raw.get("profit_loss")),
                    "source_tab":    "results",
                    "source_section":"",
                    "engine_version":raw.get("model_version", ""),
                }
                rows.append(r)
            except (ValueError, KeyError):
                continue
    return rows


def load_clv() -> list[dict]:
    """Load CLV log rows that have closing odds populated."""
    if not CLV_PATH.exists():
        return []
    rows = []
    with open(CLV_PATH, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            clv_str = raw.get("clv_pct", "").strip()
            if not clv_str:
                continue
            try:
                rows.append({
                    "date":             raw.get("date", ""),
                    "player_name":      raw.get("player_name", ""),
                    "team":             raw.get("team", ""),
                    "model_prob_pct":   _safe_float(raw.get("model_prob_pct")),
                    "opening_american": _safe_int(raw.get("opening_american")),
                    "opening_implied":  _safe_float(raw.get("opening_implied_pct")) / 100,
                    "closing_american": _safe_int(raw.get("closing_american")),
                    "closing_implied":  _safe_float(raw.get("closing_implied_pct")) / 100,
                    "clv_pct":          _safe_float(clv_str),
                })
            except (ValueError, KeyError):
                continue
    return rows


# ── Segment helpers ───────────────────────────────────────────────────────────

def barrel_tier(brl: float) -> str:
    if brl < 4:    return "<4%"
    if brl < 6:    return "4-6%"
    if brl < 8:    return "6-8%"
    if brl < 10:   return "8-10%"
    if brl < 12:   return "10-12%"
    return "12%+"


def ev_bucket(ev: float) -> str:
    if ev < 3:    return "<3%"
    if ev < 6:    return "3-6%"
    if ev < 10:   return "6-10%"
    if ev < 20:   return "10-20%"
    return "20%+"


def edge_bucket(edg: float) -> str:
    if edg < 1:    return "<1%"
    if edg < 2:    return "1-2%"
    if edg < 3:    return "2-3%"
    if edg < 5:    return "3-5%"
    return "5%+"


def odds_bucket(am: int) -> str:
    if am <= 0:     return "n/a"
    if am <= 300:   return "+100-300"
    if am <= 500:   return "+300-500"
    if am <= 700:   return "+500-700"
    if am <= 1000:  return "+700-1000"
    return "+1000+"


def prob_bucket(p: float) -> str:
    if p < 0.06:   return "<6%"
    if p < 0.08:   return "6-8%"
    if p < 0.10:   return "8-10%"
    if p < 0.12:   return "10-12%"
    if p < 0.15:   return "12-15%"
    if p < 0.20:   return "15-20%"
    return "20%+"


# ── ROI helpers ───────────────────────────────────────────────────────────────

def roi_stats(rows: list[dict]) -> dict:
    """Compute basic ROI stats from a list of settled pick dicts."""
    if not rows:
        return {"n": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_bet": 0,
                "total_pl": 0, "roi": 0, "avg_pl": 0, "std_pl": 0}
    n     = len(rows)
    wins  = sum(r["hit_hr"] for r in rows)
    pl    = [r["profit_loss"] for r in rows]
    bet   = sum(r["bet_dollars"] for r in rows if r["bet_dollars"] > 0)
    tot_pl = sum(pl)
    avg_pl = tot_pl / n
    std_pl = math.sqrt(sum((p - avg_pl) ** 2 for p in pl) / n) if n > 1 else 0
    return {
        "n":        n,
        "wins":     wins,
        "losses":   n - wins,
        "win_rate": wins / n,
        "total_bet":bet,
        "total_pl": tot_pl,
        "roi":      tot_pl / bet * 100 if bet > 0 else 0.0,
        "avg_pl":   avg_pl,
        "std_pl":   std_pl,
        "sharpe":   avg_pl / std_pl if std_pl > 0 else 0,
    }


def brier_score(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    return sum((r["model_prob"] - r["hit_hr"]) ** 2 for r in rows) / len(rows)


def ev_realization(rows: list[dict]) -> float:
    """Ratio of actual ROI to expected EV. 1.0 = perfect; <0 = bleeding."""
    with_ev = [r for r in rows if r["ev_pct"] > 0 and r["bet_dollars"] > 0]
    if not with_ev:
        return float("nan")
    expected_roi = sum(r["ev_pct"] for r in with_ev) / len(with_ev)
    s = roi_stats(with_ev)
    actual_roi   = s["roi"]
    if expected_roi == 0:
        return float("nan")
    return actual_roi / expected_roi


# ── Main analysis ─────────────────────────────────────────────────────────────

def run_analysis(tracker: list[dict], results: list[dict], clv: list[dict]) -> list[str]:
    out = []

    # Combine and deduplicate (date+player_name)
    seen: set = set()
    all_settled: list[dict] = []
    for r in tracker + results:
        key = (r["date"], r["player_name"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        all_settled.append(r)
    all_settled.sort(key=lambda r: r["date"])

    # Picks with real bet dollars
    bet_rows = [r for r in all_settled if r["bet_dollars"] > 0 and r["american_odds"] != 0]

    stats_all = roi_stats(all_settled)
    stats_bet = roi_stats(bet_rows)

    out.append(_hdr("Session 25 -- Real-World Pick Tracking & Live ROI Validation"))
    out.append(f"\n  Run date:    {date.today().isoformat()}")
    out.append(f"  Data sources: pick_tracker.csv (settled) + results.csv")
    out.append(f"  Settled picks (all):   {len(all_settled)}")
    out.append(f"  Picks with real bets:  {len(bet_rows)}")
    out.append(f"  CLV log entries:       {len(clv)}")
    out.append(f"\n  STATISTICAL CAVEAT: Reliable analysis requires n>={MIN_RELIABLE_N}.")
    out.append(f"  All results below are directional indicators only until sample grows.")

    if len(all_settled) == 0:
        out.append("\n  No settled picks found. Run settle_pick_tracker.py first.")
        return out

    # =========================================================================
    # PHASE 2: Live ROI Tracking
    # =========================================================================
    out.append(_hdr("PHASE 2 -- Live ROI Tracking & Segmentation"))

    # 2a -- Overall summary
    out.append(_sub("2a. Overall Performance Summary"))
    s = stats_bet if bet_rows else stats_all
    use_rows = bet_rows if bet_rows else all_settled
    label = "real bets" if bet_rows else "all settled (no real bet dollars)"

    out.append(f"\n  {label.upper()}  (n={s['n']}){_warn(s['n'])}")
    out.append(f"  Wins (HR hit):        {s['wins']}")
    out.append(f"  Losses (no HR):       {s['losses']}")
    out.append(f"  Win rate:             {s['win_rate']*100:.2f}%")
    out.append(f"  Total wagered:        ${s['total_bet']:.2f}")
    out.append(f"  Net P&L:              ${s['total_pl']:+.2f}")
    out.append(f"  ROI:                  {s['roi']:+.2f}%")
    out.append(f"  Brier score:          {brier_score(use_rows):.5f}")
    if s['std_pl'] > 0:
        ci = 1.96 * s['std_pl'] / math.sqrt(s['n'])
        out.append(f"  Std dev P&L:          {s['std_pl']:.4f}")
        out.append(f"  Sharpe proxy:         {s['sharpe']:.4f}")
        out.append(f"  95% CI on ROI (+/-):  {ci*100:.1f}pp")

    ev_real = ev_realization(use_rows)
    if not math.isnan(ev_real):
        out.append(f"  EV realization:       {ev_real:.2f}x  "
                   f"({'above expectation' if ev_real > 1 else 'below expectation'})")

    # 2b -- Monthly/weekly breakdown
    out.append(_sub("2b. Performance by Date"))
    date_groups: dict[str, list] = defaultdict(list)
    for r in use_rows:
        date_groups[r["date"]].append(r)
    widths2b = [12, 6, 6, 8, 8, 10]
    hdr2b    = ["Date", "Bets", "Wins", "WinRate", "AvgEV%", "ROI%"]
    out.append(_trow(hdr2b, widths2b))
    out.append("  " + "-" * sum(widths2b))
    running_pl = 0.0
    running_bet = 0.0
    for d in sorted(date_groups.keys()):
        dr   = date_groups[d]
        s_d  = roi_stats(dr)
        running_pl  += s_d["total_pl"]
        running_bet += s_d["total_bet"]
        avg_ev = sum(r["ev_pct"] for r in dr) / len(dr) if dr else 0
        out.append(_trow([d, s_d["n"], s_d["wins"],
                          f"{s_d['win_rate']*100:.1f}%",
                          f"{avg_ev:.1f}%",
                          f"{s_d['roi']:+.1f}%"], widths2b))
    if running_bet > 0:
        out.append(f"\n  Cumulative ROI: {running_pl/running_bet*100:+.2f}%")

    # 2c -- Barrel tier segmentation
    out.append(_sub("2c. Performance by Barrel Tier"))
    widths2c = [12, 6, 6, 8, 8, 8, 10, 14]
    hdr2c    = ["Barrel", "n", "Wins", "HR%", "Model%", "Market%", "ROI%", "Syn.ROI(S24)"]
    out.append(_trow(hdr2c, widths2c))
    out.append("  " + "-" * sum(widths2c))
    for tier in ["<4%","4-6%","6-8%","8-10%","10-12%","12%+"]:
        sub = [r for r in use_rows if barrel_tier(r["barrel_pct"]) == tier]
        if not sub:
            continue
        s_t   = roi_stats(sub)
        avg_m = sum(r["model_prob"] for r in sub) / len(sub) * 100
        avg_mkt = sum(r["market_prob"] for r in sub) / len(sub) * 100
        syn   = SYNTHETIC_ROI.get(tier, float("nan"))
        out.append(_trow([tier, s_t["n"], s_t["wins"],
                          f"{s_t['win_rate']*100:.1f}%",
                          f"{avg_m:.1f}%",
                          f"{avg_mkt:.1f}%" if avg_mkt > 0 else "n/a",
                          f"{s_t['roi']:+.1f}%",
                          f"{syn:+.1f}%" if not math.isnan(syn) else "—"], widths2c)
                   + _warn(s_t["n"]))

    # 2d -- EV range segmentation
    out.append(_sub("2d. Performance by EV% Range"))
    widths2d = [12, 6, 6, 8, 10]
    hdr2d    = ["EV Range", "n", "Wins", "HR%", "ROI%"]
    out.append(_trow(hdr2d, widths2d))
    out.append("  " + "-" * sum(widths2d))
    for bucket in ["<3%","3-6%","6-10%","10-20%","20%+"]:
        sub = [r for r in use_rows if ev_bucket(r["ev_pct"]) == bucket]
        if not sub:
            continue
        s_b = roi_stats(sub)
        out.append(_trow([bucket, s_b["n"], s_b["wins"],
                          f"{s_b['win_rate']*100:.1f}%",
                          f"{s_b['roi']:+.1f}%"], widths2d) + _warn(s_b["n"]))

    # 2e -- Edge range
    out.append(_sub("2e. Performance by Edge% Range"))
    out.append(_trow(["Edge Range","n","Wins","HR%","ROI%"], widths2d))
    out.append("  " + "-" * sum(widths2d))
    for bucket in ["<1%","1-2%","2-3%","3-5%","5%+"]:
        sub = [r for r in use_rows if edge_bucket(r["edge_pct"]) == bucket]
        if not sub:
            continue
        s_b = roi_stats(sub)
        out.append(_trow([bucket, s_b["n"], s_b["wins"],
                          f"{s_b['win_rate']*100:.1f}%",
                          f"{s_b['roi']:+.1f}%"], widths2d) + _warn(s_b["n"]))

    # 2f -- Odds range
    out.append(_sub("2f. Performance by Odds Range"))
    out.append(_trow(["Odds Range","n","Wins","HR%","ROI%"], widths2d))
    out.append("  " + "-" * sum(widths2d))
    for bucket in ["+100-300","+300-500","+500-700","+700-1000","+1000+"]:
        sub = [r for r in use_rows if odds_bucket(r["american_odds"]) == bucket]
        if not sub:
            continue
        s_b = roi_stats(sub)
        out.append(_trow([bucket, s_b["n"], s_b["wins"],
                          f"{s_b['win_rate']*100:.1f}%",
                          f"{s_b['roi']:+.1f}%"], widths2d) + _warn(s_b["n"]))

    # 2g -- Drawdown and streaks
    out.append(_sub("2g. Drawdown & Streak Analysis"))
    if use_rows:
        chronological = sorted(use_rows, key=lambda r: r["date"])
        cumulative    = 0.0
        peak          = 0.0
        trough        = 0.0
        max_drawdown  = 0.0
        cur_win_streak= 0
        cur_los_streak= 0
        max_win_streak= 0
        max_los_streak= 0
        bet_per_pick  = 1.0   # normalise to $1 flat bet
        for r in chronological:
            bet = r["bet_dollars"] if r["bet_dollars"] > 0 else 1.0
            pl_norm = r["profit_loss"] / bet   # normalised to bet size
            cumulative += pl_norm
            peak = max(peak, cumulative)
            dd   = peak - cumulative
            max_drawdown = max(max_drawdown, dd)
            if r["hit_hr"]:
                cur_win_streak += 1
                cur_los_streak  = 0
                max_win_streak  = max(max_win_streak, cur_win_streak)
            else:
                cur_los_streak += 1
                cur_win_streak  = 0
                max_los_streak  = max(max_los_streak, cur_los_streak)

        out.append(f"\n  Max drawdown (per-unit):  {max_drawdown:.4f}x bet")
        out.append(f"  Max win streak:           {max_win_streak}")
        out.append(f"  Max loss streak:          {max_los_streak}")
        out.append(f"  Current win streak:       {cur_win_streak}")
        out.append(f"  Current loss streak:      {cur_los_streak}")
        out.append(f"  Bankroll change (flat):   {cumulative:+.4f}x per unit bet")

    # 2h -- Threshold comparison (current vs tighter)
    out.append(_sub("2h. Threshold Comparison (EV >= 3% edge >= 2% vs EV >= 4% edge >= 2.5%)"))
    curr_q  = [r for r in use_rows if r["ev_pct"] >= MIN_EV_PCT and r["edge_pct"] >= MIN_EDGE_PCT]
    tight_q = [r for r in use_rows if r["ev_pct"] >= TIGHTER_EV  and r["edge_pct"] >= TIGHTER_EDGE]
    s_curr  = roi_stats(curr_q)
    s_tight = roi_stats(tight_q)
    widths2h = [24, 6, 6, 8, 10]
    out.append(_trow(["Threshold","n","Wins","HR%","ROI%"], widths2h))
    out.append("  " + "-" * sum(widths2h))
    out.append(_trow([f"Current EV>={MIN_EV_PCT}% E>={MIN_EDGE_PCT}%",
                      s_curr["n"], s_curr["wins"],
                      f"{s_curr['win_rate']*100:.1f}%",
                      f"{s_curr['roi']:+.1f}%"], widths2h) + _warn(s_curr["n"]))
    out.append(_trow([f"Tighter EV>={TIGHTER_EV}% E>={TIGHTER_EDGE}%",
                      s_tight["n"], s_tight["wins"],
                      f"{s_tight['win_rate']*100:.1f}%",
                      f"{s_tight['roi']:+.1f}%"], widths2h) + _warn(s_tight["n"]))

    # 2i -- Source tab breakdown
    out.append(_sub("2i. Performance by Source Section"))
    tab_groups: dict[str, list] = defaultdict(list)
    for r in use_rows:
        tab_groups[r["source_section"] or r["source_tab"]].append(r)
    for tab, tab_rows in sorted(tab_groups.items(), key=lambda x: -len(x[1])):
        s_t = roi_stats(tab_rows)
        out.append(f"  {tab[:30]:<30}  n={s_t['n']:4d}  wins={s_t['wins']:3d}  "
                   f"HR%={s_t['win_rate']*100:.1f}%  ROI={s_t['roi']:+.1f}%")

    # =========================================================================
    # PHASE 3: Closing Line Analysis
    # =========================================================================
    out.append(_hdr("PHASE 3 -- Closing Line Analysis (CLV)"))

    if not clv:
        out.append("\n  No CLV data available (clv_log.csv has no closing odds populated).")
        out.append("  CLV will populate automatically once closing lines are fetched via:")
        out.append("    from tracking import clv; clv.fetch_and_compute_clv()")
        out.append("  This runs in app.py sidebar 'Update Yesterday' button.")
        out.append("\n  WHAT WOULD CLV TELL US:")
        out.append("  - CLV > 0: model beats the close (sharp money agrees after seeing more info)")
        out.append("  - CLV < 0: market moved against us (model pricing lagged market consensus)")
        out.append("  - Consistent CLV > 0.5pp = genuine market edge (not just variance)")
        out.append("  - CLV persists even in losing streaks if model is truly sharp")
    else:
        clv_vals = [r["clv_pct"] for r in clv]
        n_clv   = len(clv_vals)
        avg_clv = sum(clv_vals) / n_clv
        pos_clv = sum(1 for v in clv_vals if v > 0)
        verdict = "SHARP" if avg_clv > 0.5 else ("NEUTRAL" if avg_clv > -0.5 else "SOFT")

        out.append(f"\n  CLV entries with closing odds: {n_clv}{_warn(n_clv)}")
        out.append(f"  Average CLV:                   {avg_clv:+.2f}pp")
        out.append(f"  % beating closing line:        {pos_clv/n_clv*100:.1f}%")
        out.append(f"  Verdict:                       {verdict}")
        out.append(f"\n  Interpretation: CLV={avg_clv:+.2f}pp means our opening price was "
                   f"{'better' if avg_clv > 0 else 'worse'} than the close by "
                   f"{abs(avg_clv):.2f}pp on average.")

        # CLV by model prob bucket
        if n_clv >= 10:
            out.append(_sub("3a. CLV by Model Probability Bucket"))
            prob_clv: dict[str, list] = defaultdict(list)
            for r in clv:
                bucket = prob_bucket(r["model_prob_pct"] / 100)
                prob_clv[bucket].append(r["clv_pct"])
            for bucket in ["<6%","6-8%","8-10%","10-12%","12-15%","15-20%","20%+"]:
                vals = prob_clv.get(bucket, [])
                if not vals:
                    continue
                out.append(f"  {bucket:8s}  n={len(vals):3d}  avg_clv={sum(vals)/len(vals):+.2f}pp  "
                           f"pct_positive={sum(1 for v in vals if v>0)/len(vals)*100:.0f}%")

    out.append(_sub("3b. Line Movement Interpretation"))
    out.append("  Line shortening (odds decrease) = market agrees with model (confidence boost).")
    out.append("  Line lengthening (odds increase) = market fading model (proceed carefully).")
    out.append("  Consistent shortening on qualified picks = sustainable real-world edge.")
    out.append("  Check line_movement_log.csv for intraday snapshots once populated.")

    out.append(_sub("3c. Stale Line Detection Criteria"))
    out.append("  A 'stale' line is one where the book hasn't moved despite public info.")
    out.append("  Signs of stale lines (favorable for bettor):")
    out.append("    - Opening odds >3 hours before first pitch with no movement")
    out.append("    - Odds longer than all other books by >50 American odds")
    out.append("    - Book with historical lag: check BOOK_VIG table in vig.py")
    out.append("  Prioritize: Pinnacle/Circa as sharp anchors; fade FanDuel/Fanatics for staleness.")

    # =========================================================================
    # PHASE 4: Real vs Synthetic ROI Comparison
    # =========================================================================
    out.append(_hdr("PHASE 4 -- Real-World vs Synthetic ROI Comparison"))

    out.append(_sub("4a. Barrel Tier: Real ROI vs Session 24 Synthetic ROI"))
    out.append("\n  Session 24 synthetic used naive market (no Statcast baseline).")
    out.append("  Real ROI uses actual market prices and settled outcomes.")
    out.append("  Gap = real - synthetic: negative = model underperforms synthetic expectation.\n")

    widths4 = [12, 6, 6, 8, 10, 12, 10]
    hdr4    = ["Barrel", "n", "Wins", "HR%", "RealROI%", "SynROI(S24)", "Gap"]
    out.append(_trow(hdr4, widths4))
    out.append("  " + "-" * sum(widths4))
    for tier in ["<4%","4-6%","6-8%","8-10%","10-12%","12%+"]:
        sub  = [r for r in use_rows if barrel_tier(r["barrel_pct"]) == tier]
        syn  = SYNTHETIC_ROI.get(tier, float("nan"))
        if not sub:
            out.append(_trow([tier, 0, 0, "—", "—",
                              f"{syn:+.1f}%" if not math.isnan(syn) else "—", "—"], widths4))
            continue
        s_t  = roi_stats(sub)
        gap  = s_t["roi"] - syn if not math.isnan(syn) else float("nan")
        out.append(_trow([tier, s_t["n"], s_t["wins"],
                          f"{s_t['win_rate']*100:.1f}%",
                          f"{s_t['roi']:+.1f}%",
                          f"{syn:+.1f}%" if not math.isnan(syn) else "—",
                          f"{gap:+.1f}pp" if not math.isnan(gap) else "—"], widths4)
                   + _warn(s_t["n"]))

    out.append(_sub("4b. Variance Analysis: Is the Gap Explained by Sample Size?"))
    if use_rows:
        s_all = roi_stats(use_rows)
        n     = s_all["n"]
        wins  = s_all["wins"]
        hr    = s_all["win_rate"]
        se    = math.sqrt(hr * (1 - hr) / n) if n > 0 else 0
        out.append(f"\n  Overall n={n}  HR%={hr*100:.1f}%  ROI={s_all['roi']:+.1f}%")
        out.append(f"  SE of win rate = {se*100:.2f}pp")
        out.append(f"  95% CI on win rate: [{(hr-1.96*se)*100:.1f}%, {(hr+1.96*se)*100:.1f}%]")

        # Binomial probability of observing this many wins under various true-prob assumptions
        out.append(f"\n  Binomial probability of {wins} wins in {n} picks:")
        for true_p in [0.10, 0.12, 0.15, 0.18, 0.20, 0.25]:
            # P(X <= wins) under Binomial(n, true_p)
            log_prob = 0.0
            binom_p  = 0.0
            lc = 0.0
            for k in range(wins + 1):
                # log C(n,k) + k*log(p) + (n-k)*log(1-p)
                try:
                    lc_new = (math.lgamma(n+1) - math.lgamma(k+1) - math.lgamma(n-k+1)
                              + k * math.log(true_p) + (n-k) * math.log(1-true_p))
                    binom_p += math.exp(lc_new)
                except Exception:
                    pass
            binom_p = min(1.0, binom_p)
            out.append(f"    true_p={true_p*100:.0f}%  P(wins<={wins}) = {binom_p*100:.1f}%  "
                       f"{'[plausible variance]' if binom_p > 0.05 else '[statistically unlikely]'}")

    out.append(_sub("4c. Elite Hitters (barrel >= 10%) — Specific Validation"))
    elite = [r for r in use_rows if r["barrel_pct"] >= 10]
    if elite:
        s_e  = roi_stats(elite)
        avg_m = sum(r["model_prob"] for r in elite) / len(elite) * 100
        out.append(f"\n  n={s_e['n']}  HR%={s_e['win_rate']*100:.1f}%  "
                   f"model_avg={avg_m:.1f}%  ROI={s_e['roi']:+.1f}%")
        out.append(f"  Synthetic (Session 24): barrel 10-12% => +65%, barrel 12%+ => +119%")
        out.append(f"  Session 23 fix target:  barrel>=12% actual should be ~28-30%")
        if s_e["n"] < MIN_RELIABLE_N:
            out.append(f"  {_warn(s_e['n'])}")
        bias = avg_m - s_e["win_rate"] * 100
        out.append(f"  Model calibration bias: {bias:+.2f}pp "
                   f"({'over-predicting' if bias > 2 else 'under-predicting' if bias < -2 else 'well-calibrated'})")
    else:
        out.append("\n  No elite barrel (>=10%) picks settled yet.")

    out.append(_sub("4d. Long-shot Analysis (odds > +700)"))
    longshots = [r for r in use_rows if r["american_odds"] > 700]
    if longshots:
        s_l   = roi_stats(longshots)
        avg_m = sum(r["model_prob"] for r in longshots) / len(longshots) * 100
        out.append(f"\n  n={s_l['n']}  HR%={s_l['win_rate']*100:.1f}%  "
                   f"model_avg={avg_m:.1f}%  ROI={s_l['roi']:+.1f}%")
        out.append(f"  Session 24 synthetic: +700-1000 odds => +46% ROI")
        out.append(_warn(s_l["n"]))
    else:
        out.append("\n  No long-shot (>+700) settled picks with real bets.")

    # =========================================================================
    # PHASE 5: Production Monitoring
    # =========================================================================
    out.append(_hdr("PHASE 5 -- Production Monitoring & Diagnostics"))

    # 5a -- Calibration drift
    out.append(_sub("5a. Calibration Drift: Model Probability vs Actual HR Rate"))
    out.append("\n  If model consistently over/under-predicts within a bucket,")
    out.append("  the Platt calibration may need re-fitting (run analyze_calibration.py).\n")
    prob_groups: dict[str, list] = defaultdict(list)
    for r in all_settled:
        prob_groups[prob_bucket(r["model_prob"])].append(r)
    widths5a = [10, 6, 8, 8, 8]
    hdr5a    = ["Prob Bkt", "n", "HR%", "Model%", "Bias"]
    out.append(_trow(hdr5a, widths5a))
    out.append("  " + "-" * sum(widths5a))
    for bkt in ["<6%","6-8%","8-10%","10-12%","12-15%","15-20%","20%+"]:
        sub = prob_groups.get(bkt, [])
        if not sub:
            continue
        hr_rate  = sum(r["hit_hr"] for r in sub) / len(sub) * 100
        avg_m    = sum(r["model_prob"] for r in sub) / len(sub) * 100
        bias     = avg_m - hr_rate
        out.append(_trow([bkt, len(sub), f"{hr_rate:.2f}%",
                          f"{avg_m:.2f}%", _pct(bias)], widths5a) + _warn(len(sub)))

    out.append("\n  CALIBRATION ALERT THRESHOLDS:")
    out.append("    |bias| > 3pp in any bucket with n>=50 -> re-run analyze_calibration.py")
    out.append("    |bias| > 5pp in any bucket with n>=30 -> immediate re-calibration needed")

    # 5b -- EV realization by segment
    out.append(_sub("5b. EV Realization Rate (actual ROI / expected EV)"))
    out.append("\n  EV realization = actual_roi / expected_ev_pct.")
    out.append("  1.0 = perfect; > 1 = outperforming; < 0 = bleeding.")
    out.append("  Target: > 0.0 over 100+ picks (positive ROI vs expected EV).\n")
    for barrel_seg in ["<4%","4-6%","6-8%","8-10%","10-12%","12%+"]:
        sub = [r for r in use_rows if barrel_tier(r["barrel_pct"]) == barrel_seg
               and r["ev_pct"] > 0]
        if not sub:
            continue
        real = ev_realization(sub)
        s_t  = roi_stats(sub)
        avg_ev = sum(r["ev_pct"] for r in sub) / len(sub)
        out.append(f"  {barrel_seg:8s}  n={len(sub):3d}  expected_ev={avg_ev:.1f}%  "
                   f"actual_roi={s_t['roi']:+.1f}%  "
                   f"realization={'N/A' if math.isnan(real) else f'{real:.2f}x'}")

    # 5c -- Sportsbook performance
    out.append(_sub("5c. Sportsbook Performance (books with sportsbook field populated)"))
    book_rows = [r for r in use_rows if r.get("sportsbook", "").strip()]
    if not book_rows:
        out.append("\n  No sportsbook field populated in pick_tracker.csv yet.")
        out.append("  'sportsbook' column added by Session 25 schema upgrade.")
        out.append("  Will populate automatically for future picks once best_book is logged.")
        out.append("\n  Session 24 synthetic sportsbook ranking (for reference):")
        book_rank = [
            ("Pinnacle",   3.0,  "+46.3%"),
            ("Circa",      4.0,  "+44.6%"),
            ("BetOnlineAG",5.5,  "+42.2%"),
            ("BetRivers",  7.0,  "+39.9%"),
            ("Caesars",    7.8,  "+38.7%"),
            ("DraftKings", 8.8,  "+37.1%"),
            ("FanDuel",    9.5,  "+35.8%"),
            ("Fanatics",  11.0,  "+35.1%"),
        ]
        for book, vig, roi in book_rank:
            out.append(f"    {book:14s}  vig={vig:.1f}%  syn_roi={roi}")
    else:
        book_groups: dict[str, list] = defaultdict(list)
        for r in book_rows:
            book_groups[r["sportsbook"]].append(r)
        widths5c = [16, 6, 6, 8, 10]
        hdr5c    = ["Book", "n", "Wins", "HR%", "ROI%"]
        out.append(_trow(hdr5c, widths5c))
        out.append("  " + "-" * sum(widths5c))
        for book, br in sorted(book_groups.items(), key=lambda x: -len(x[1])):
            s_b = roi_stats(br)
            out.append(_trow([book[:16], s_b["n"], s_b["wins"],
                              f"{s_b['win_rate']*100:.1f}%",
                              f"{s_b['roi']:+.1f}%"], widths5c) + _warn(s_b["n"]))

    # 5d -- Calibration drift alert
    out.append(_sub("5d. Drift Detection Summary"))
    total_model_prob = sum(r["model_prob"] for r in all_settled) / len(all_settled) if all_settled else 0
    total_actual     = sum(r["hit_hr"] for r in all_settled) / len(all_settled) if all_settled else 0
    overall_bias     = total_model_prob - total_actual

    out.append(f"\n  Overall model probability:   {total_model_prob*100:.2f}%")
    out.append(f"  Overall actual HR rate:      {total_actual*100:.2f}%")
    out.append(f"  Overall calibration bias:    {overall_bias*100:+.2f}pp")

    if abs(overall_bias) < 0.02:
        drift_status = "STABLE -- no calibration drift detected"
    elif abs(overall_bias) < 0.05:
        drift_status = "WATCH -- mild bias, monitor over next 50 picks"
    else:
        drift_status = "ALERT -- significant bias, re-run analyze_calibration.py"
    out.append(f"  Drift status:                {drift_status}")
    out.append(f"  [!] n={len(all_settled)} is {'sufficient' if len(all_settled)>=MIN_RELIABLE_N else 'too small'} for reliable drift detection")

    # 5e -- Daily ROI dashboard template
    out.append(_sub("5e. Daily ROI Dashboard -- Current State"))
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today_rows = [r for r in use_rows if r["date"] == today]
    yest_rows  = [r for r in use_rows if r["date"] == yesterday]
    s_today = roi_stats(today_rows)
    s_yest  = roi_stats(yest_rows)

    out.append(f"\n  Today ({today}):     {s_today['n']} settled  HR%={s_today['win_rate']*100:.1f}%  ROI={s_today['roi']:+.1f}%")
    out.append(f"  Yesterday ({yesterday}): {s_yest['n']} settled  HR%={s_yest['win_rate']*100:.1f}%  ROI={s_yest['roi']:+.1f}%")
    out.append(f"  All-time (settled):      {len(use_rows)} picks   ROI={stats_bet['roi']:+.1f}%")
    out.append(f"\n  SETTLEMENT STATUS:")
    out.append(f"    pick_tracker.csv settled rows: {len([r for r in all_settled if r['source']=='tracker'])}")
    out.append(f"    results.csv settled rows:      {len([r for r in all_settled if r['source']=='results'])}")
    out.append(f"    CLV entries with close:        {len(clv)}")

    # =========================================================================
    # SUMMARY & ROADMAP
    # =========================================================================
    out.append(_hdr("SUMMARY & LONG-TERM VALIDATION ROADMAP"))

    out.append("\n  [Current State]")
    out.append(f"  Total settled picks: {len(all_settled)}")
    out.append(f"  Picks with real bets: {len(bet_rows)}")
    out.append(f"  Overall ROI: {stats_bet['roi']:+.1f}%  (n={stats_bet['n']})")
    out.append(f"  CLV tracking: {'active' if clv else 'not yet collecting closing lines'}")
    out.append(f"\n  STATISTICAL DISCLAIMER:")
    out.append(f"  With n={len(use_rows)} settled picks, the 95% ROI confidence interval spans")
    s_use = roi_stats(use_rows)
    if s_use["std_pl"] > 0 and s_use["n"] > 0:
        ci = 1.96 * s_use["std_pl"] / math.sqrt(s_use["n"]) * 100
        out.append(f"  +/- {ci:.0f}pp around any ROI estimate. No conclusions are statistically")
    out.append(f"  reliable until n >= {MIN_RELIABLE_N} (target: 200+ for meaningful segmentation).")

    out.append("\n  [Validation Milestones]")
    milestones = [
        (50,   "Preliminary ROI direction visible; calibration drift detectable"),
        (100,  "barrel>=10% segment has sufficient samples (n~15-20 expected)"),
        (200,  "Overall ROI statistically meaningful; CLV vs ROI correlation visible"),
        (500,  "Segment-level ROI reliable; threshold optimization feasible"),
        (1000, "Full production validation; re-calibration confidence high"),
    ]
    for n_target, description in milestones:
        status = "COMPLETE" if len(all_settled) >= n_target else f"need {n_target-len(all_settled)} more"
        out.append(f"  n={n_target:5d}: {description}")
        out.append(f"          Status: [{status}]")

    out.append("\n  [Immediate Next Actions]")
    out.append("  1. Run settle_pick_tracker.py daily (or auto-trigger from app.py startup)")
    out.append("  2. Activate CLV fetch: clv.fetch_and_compute_clv() in app.py sidebar")
    out.append("  3. Ensure 'sportsbook' field is populated in pick logging pipeline")
    out.append("  4. Settle May 15 picks once today's games complete")
    out.append("  5. Re-run analyze_calibration.py after n>=100 settled (Step 3 re-calibration)")
    out.append("  6. Do NOT adjust thresholds based on current n -- wait for n>=200")

    out.append("\n  [What Session 23+24 Predicted -- Real Validation Targets]")
    out.append("  Session 23: barrel>=12% actual HR rate should approach 28-30% (vs model 19-20%)")
    out.append("  Session 24: barrel>=8% edge breakeven -- barrel<6% expected negative ROI")
    out.append("  Session 24: tighter thresholds (EV>=4%, edge>=2.5%) should outperform current")
    out.append("  CRITICAL: Do NOT confirm or reject these without n>=50 per barrel tier")

    return out


def main():
    print("Loading data ...", flush=True)
    tracker = load_tracker()
    results = load_results()
    clv     = load_clv()
    print(f"  pick_tracker settled: {len(tracker)}")
    print(f"  results.csv settled:  {len(results)}")
    print(f"  CLV entries:          {len(clv)}")

    lines  = run_analysis(tracker, results, clv)
    report = "\n".join(str(x) for x in lines)
    print(report)
    OUT_PATH.write_text(report, encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
