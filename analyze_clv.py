"""
analyze_clv.py — Session 26: Dedicated Closing Line Value Analysis
===================================================================

CLV is the primary long-run edge validation metric for sharp sports betting.
Positive CLV consistently = model finds value before the market does.
Negative CLV consistently = model is mispriced or edge has shrunk.

This script pulls CLV data from two sources:
  clv_log.csv       (richer metadata: model_prob, barrel, ev, edge, archetype)
  pick_tracker.csv  (clv_pp + clv_pct_rel fields added in Session 26)

Phases:
  1  Overall CLV summary + verdict
  2  CLV by barrel tier (primary edge predictor)
  3  CLV by sportsbook
  4  CLV by EV% range
  5  CLV by opening odds range
  6  CLV by model probability bucket
  7  CLV trend over time (rolling 20-pick window)
  8  CLV persistence: are early CLV gains sustained?
  9  Statistical validity and minimum n warnings

IMPORTANT RULES (Session 26):
  Do NOT adjust model thresholds based on early CLV data.
  CLV data < 100 picks is directional only.
  All tables include n with small-sample flags.

Usage:
  py -3.12 analyze_clv.py              # full report
  py -3.12 analyze_clv.py --summary    # overall summary only
  py -3.12 analyze_clv.py --phase 2    # specific phase
  py -3.12 analyze_clv.py --tracker    # only use pick_tracker.csv (no clv_log)
"""

import csv
import math
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT         = Path(__file__).parent
CLV_LOG      = ROOT / "mlb_hr_engine_v4" / "tracking" / "clv_log.csv"
TRACKER_PATH = ROOT / "mlb_hr_engine_v4" / "tracking" / "pick_tracker.csv"
OUT_PATH     = ROOT / "analyze_clv_output.txt"

MIN_N_RELIABLE   = 100   # minimum picks for reliable CLV conclusions
MIN_N_SEGMENT    = 20    # minimum per-segment for directional conclusions
MIN_N_REPORTABLE = 5     # minimum to display at all

W = 74  # output width


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_clv_log() -> list[dict]:
    if not CLV_LOG.exists():
        return []
    with open(CLV_LOG, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_tracker() -> list[dict]:
    if not TRACKER_PATH.exists():
        return []
    with open(TRACKER_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _safe_float(v, default=None):
    if v is None or str(v).strip() == "":
        return default
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return default


def _extract_clv_from_tracker(rows: list[dict]) -> list[dict]:
    """Pull CLV-relevant fields from pick_tracker.csv rows (Session 26 schema)."""
    out = []
    for r in rows:
        clv_raw = r.get("clv_pp", "")
        if not clv_raw:
            continue
        try:
            clv = float(clv_raw)
        except (ValueError, TypeError):
            continue

        out.append({
            "date":              r.get("date", ""),
            "player_name":       r.get("player_name", ""),
            "team":              r.get("team", ""),
            "sportsbook":        r.get("sportsbook", ""),
            "model_prob_pct":    r.get("model_prob_pct", ""),
            "barrel_pct":        r.get("barrel_pct", ""),
            "ev_pct":            r.get("ev_pct", ""),
            "edge_pct":          r.get("edge_pct", ""),
            "opening_american":  r.get("best_odds") or r.get("american_odds") or "",
            "opening_no_vig_pct":r.get("open_no_vig_pct", ""),
            "closing_american":  r.get("close_odds", ""),
            "closing_no_vig_pct":r.get("close_no_vig_pct", ""),
            "clv_pp":            clv_raw,
            "clv_pct_rel":       r.get("clv_pct_rel", ""),
            "beats_close":       "1" if clv > 0 else "0",
            "source":            "tracker",
        })
    return out


def _load_combined(use_tracker_only: bool = False) -> list[dict]:
    """
    Load CLV rows from clv_log.csv and/or pick_tracker.csv.
    Dedup by (date, player_name).
    """
    seen: set[tuple] = set()
    result = []

    if not use_tracker_only:
        for r in _load_clv_log():
            if not r.get("clv_pp"):
                continue
            key = (r.get("date", ""), r.get("player_name", "").lower().strip())
            if key not in seen:
                seen.add(key)
                r["source"] = "clv_log"
                result.append(r)

    tracker_clv = _extract_clv_from_tracker(_load_tracker())
    for r in tracker_clv:
        key = (r.get("date", ""), r.get("player_name", "").lower().strip())
        if key not in seen:
            seen.add(key)
            result.append(r)

    return result


# ── Statistical helpers ───────────────────────────────────────────────────────

def _ci_half(vals: list[float], z: float = 1.96) -> float:
    """Half-width of z-score confidence interval for the mean."""
    n = len(vals)
    if n < 2:
        return float("inf")
    mean = sum(vals) / n
    var  = sum((v - mean) ** 2 for v in vals) / (n - 1)
    se   = math.sqrt(var / n)
    return z * se


def _sig_flag(n: int) -> str:
    if n >= MIN_N_RELIABLE:
        return ""
    if n >= MIN_N_SEGMENT:
        return " [dir]"
    if n >= MIN_N_REPORTABLE:
        return " [n<20]"
    return " [tiny]"


def _verdict(avg_pp: float) -> str:
    if avg_pp > 1.0:   return "SHARP"
    if avg_pp > 0.0:   return "SLIGHTLY SHARP"
    if avg_pp > -1.0:  return "NEUTRAL"
    return "SOFT"


def _beats_pct(vals: list[float]) -> float:
    if not vals:
        return 0.0
    return sum(1 for v in vals if v > 0) / len(vals) * 100


# ── Segment builder ───────────────────────────────────────────────────────────

def _by_segment(rows: list[dict], key_fn) -> list[dict]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        v = _safe_float(r.get("clv_pp"))
        if v is None:
            continue
        k = key_fn(r)
        if k is None:
            continue
        buckets[k].append(v)

    result = []
    for seg, vals in buckets.items():
        n    = len(vals)
        if n < MIN_N_REPORTABLE:
            continue
        avg  = sum(vals) / n
        ci   = _ci_half(vals)
        result.append({
            "segment":   seg,
            "n":         n,
            "avg_pp":    round(avg, 3),
            "ci":        round(ci, 3),
            "beats_pct": round(_beats_pct(vals), 1),
            "flag":      _sig_flag(n),
        })
    return sorted(result, key=lambda x: -x["n"])


# ── Segment key functions ──────────────────────────────────────────────────────

def _key_barrel(r):
    b = _safe_float(r.get("barrel_pct"))
    if b is None:
        return None
    if b < 4:   return "barrel <4%"
    if b < 6:   return "barrel 4-6%"
    if b < 8:   return "barrel 6-8%"
    if b < 10:  return "barrel 8-10%"
    if b < 12:  return "barrel 10-12%"
    return "barrel 12%+"


def _key_book(r):
    b = (r.get("sportsbook") or "").strip()
    return b if b else "unknown"


def _key_ev(r):
    ev = _safe_float(r.get("ev_pct"))
    if ev is None:
        return None
    if ev < 2:   return "EV <2%"
    if ev < 4:   return "EV 2-4%"
    if ev < 6:   return "EV 4-6%"
    if ev < 10:  return "EV 6-10%"
    return "EV 10%+"


def _key_odds(r):
    v = r.get("opening_american") or ""
    try:
        odds = int(float(v))
    except (ValueError, TypeError):
        return None
    if odds <= 0:     return None
    if odds < 200:    return "+100-199"
    if odds < 300:    return "+200-299"
    if odds < 400:    return "+300-399"
    if odds < 500:    return "+400-499"
    if odds < 700:    return "+500-699"
    if odds < 1000:   return "+700-999"
    return "+1000+"


def _key_prob(r):
    p = _safe_float(r.get("model_prob_pct"))
    if p is None:
        return None
    if p < 8:    return "prob <8%"
    if p < 10:   return "prob 8-10%"
    if p < 12:   return "prob 10-12%"
    if p < 15:   return "prob 12-15%"
    if p < 20:   return "prob 15-20%"
    return "prob 20%+"


def _key_edge(r):
    e = _safe_float(r.get("edge_pct"))
    if e is None:
        return None
    if e < 2:    return "edge <2%"
    if e < 4:    return "edge 2-4%"
    if e < 6:    return "edge 4-6%"
    if e < 10:   return "edge 6-10%"
    return "edge 10%+"


# ── Output helpers ────────────────────────────────────────────────────────────

def _header(title: str, out):
    out(f"\n{'─'*W}")
    out(f"  {title}")
    out(f"{'─'*W}")


def _seg_table(rows: list[dict], label: str, out, sort_key=None):
    if not rows:
        out(f"  No data.")
        return

    def _sort(x):
        if sort_key == "barrel":
            order = ["barrel <4%","barrel 4-6%","barrel 6-8%","barrel 8-10%",
                     "barrel 10-12%","barrel 12%+"]
            try:
                return order.index(x["segment"])
            except ValueError:
                return 99
        if sort_key == "odds":
            order = ["+100-199","+200-299","+300-399","+400-499",
                     "+500-699","+700-999","+1000+"]
            try:
                return order.index(x["segment"])
            except ValueError:
                return 99
        return -x["n"]

    rows_sorted = sorted(rows, key=_sort)

    out(f"\n  {label}:")
    out(f"  {'Segment':<22} {'n':>5} {'Avg CLV':>10} {'95% CI':>10} {'Beats%':>8}  Flag")
    out(f"  {'─'*64}")
    for s in rows_sorted:
        ci_str = f"±{s['ci']:.2f}" if s["ci"] < 99 else "  —"
        bar    = "  ← target" if ("10%+" in s["segment"] or "12%+" in s["segment"] or
                                    "12%" in s["segment"]) and "barrel" in s["segment"] else ""
        out(f"  {s['segment']:<22} {s['n']:>5} {s['avg_pp']:>+10.3f}pp {ci_str:>9} "
            f"{s['beats_pct']:>7.1f}%{s['flag']}{bar}")


def _rolling_clv(rows: list[dict], window: int = 20) -> list[dict]:
    """Compute rolling average CLV over time-ordered picks."""
    ordered = sorted(
        [(r.get("date",""), i, _safe_float(r.get("clv_pp")))
         for i, r in enumerate(rows)
         if _safe_float(r.get("clv_pp")) is not None],
        key=lambda x: (x[0], x[1])
    )
    vals = [v for _, _, v in ordered]
    dates = [d for d, _, _ in ordered]

    result = []
    for i in range(window - 1, len(vals)):
        chunk  = vals[i - window + 1 : i + 1]
        avg    = sum(chunk) / len(chunk)
        result.append({
            "pick_num": i + 1,
            "date":     dates[i],
            "avg_clv":  round(avg, 3),
            "beats_pct":round(_beats_pct(chunk), 1),
        })
    return result


# ── Phases ────────────────────────────────────────────────────────────────────

def phase1_summary(rows: list[dict], out):
    _header("PHASE 1 — OVERALL CLV SUMMARY", out)

    vals = [_safe_float(r.get("clv_pp")) for r in rows]
    vals = [v for v in vals if v is not None]

    n_total    = len(rows)
    n_with_clv = len(vals)

    out(f"\n  Total rows loaded  : {n_total}")
    out(f"  Picks with CLV     : {n_with_clv}")

    if n_with_clv == 0:
        out(f"\n  NO CLV DATA.")
        out(f"  Run capture_closing_lines.py before first pitch to begin accumulating CLV.")
        out(f"\n  CLV formula:")
        out(f"    clv_pp = (close_no_vig − open_no_vig) × 100")
        out(f"    positive = we got a better price than where the market closed = sharp signal")
        return

    avg  = sum(vals) / n_with_clv
    ci   = _ci_half(vals)
    bp   = _beats_pct(vals)

    rel_vals = [_safe_float(r.get("clv_pct_rel"))
                for r in rows if _safe_float(r.get("clv_pct_rel")) is not None]
    avg_rel  = sum(rel_vals) / len(rel_vals) if rel_vals else None

    flag = _sig_flag(n_with_clv)
    out(f"\n  Avg CLV (pp)       : {avg:+.3f}pp  ±{ci:.2f} (95% CI){flag}")
    if avg_rel is not None:
        out(f"  Avg CLV (relative) : {avg_rel:+.2f}%")
    out(f"  Beats close        : {bp:.1f}%  (>50% = sharp, target ≥55%)")
    out(f"  Verdict            : {_verdict(avg)}")

    if avg > 1.0:
        out(f"\n  ✓ Model is beating the closing line. Positive CLV means we are identifying")
        out(f"    value before the market moves. Long-run EV is validated by CLV > wins/losses.")
    elif avg > 0.0:
        out(f"\n  → Model is marginally beating close. Continue accumulating — directional signal")
        out(f"    is positive but needs n≥{MIN_N_RELIABLE} for statistical confidence.")
    elif avg > -1.0:
        out(f"\n  ~ Model and market are roughly in agreement. Neither sharp nor soft.")
        out(f"    Consider reviewing EV filter thresholds once n≥{MIN_N_RELIABLE}.")
    else:
        out(f"\n  ✗ Model is behind the closing line. Market disagrees with model pricing.")
        out(f"    Run monitoring_dashboard.py Phase 4 to check calibration drift.")

    if n_with_clv < MIN_N_RELIABLE:
        out(f"\n  NOTE: {n_with_clv} picks is below the {MIN_N_RELIABLE}-pick threshold for reliable CLV.")
        out(f"  CLV estimates are directional; do NOT modify model based on this data.")
        out(f"  Need {MIN_N_RELIABLE - n_with_clv} more picks with CLV for actionable conclusions.")

    # Source breakdown
    from_log     = sum(1 for r in rows if r.get("source") == "clv_log")
    from_tracker = sum(1 for r in rows if r.get("source") == "tracker")
    if from_log > 0 or from_tracker > 0:
        out(f"\n  Data sources:")
        if from_log > 0:
            out(f"    clv_log.csv       : {from_log} rows")
        if from_tracker > 0:
            out(f"    pick_tracker.csv  : {from_tracker} rows")


def phase2_barrel(rows: list[dict], out):
    _header("PHASE 2 — CLV BY BARREL TIER", out)
    out(f"\n  Barrel% is the #1 predictor of HR probability (r=+0.30 in 2026 signal rank).")
    out(f"  Target: barrel≥8% picks should show positive CLV if model has real edge.")

    segs = _by_segment(rows, _key_barrel)
    _seg_table(segs, "CLV by barrel tier", out, sort_key="barrel")

    barrel_clv = {s["segment"]: s["avg_pp"] for s in segs}
    high_barrel = {k: v for k, v in barrel_clv.items() if "10%" in k or "12%" in k}

    if high_barrel:
        all_pos = all(v > 0 for v in high_barrel.values())
        out(f"\n  Key finding:")
        if all_pos:
            out(f"    ✓ Elite barrel tiers show positive CLV — model has edge in high-quality picks")
        else:
            neg = [k for k, v in high_barrel.items() if v <= 0]
            out(f"    ~ Elite barrel tiers showing negative CLV in: {', '.join(neg)}")
            out(f"      Review calibration for elite batters (Session 23 Step 3 pending?)")
    elif segs:
        out(f"\n  Insufficient data for barrel tier conclusions.")


def phase3_book(rows: list[dict], out):
    _header("PHASE 3 — CLV BY SPORTSBOOK", out)
    out(f"\n  Sharp books (Pinnacle, Circa) close lines efficiently → CLV there is hardest to achieve.")
    out(f"  Retail books (FanDuel, DraftKings) leave more CLV room but smaller edges.")

    # Filter out unknown
    log_rows = [r for r in rows if (r.get("sportsbook") or "").strip()]
    segs = _by_segment(log_rows, _key_book)
    if not segs:
        out(f"\n  No sportsbook data. Field populated once picks are logged with 'sportsbook'.")
        out(f"  Ensure picks are logged via the Session 25+ schema (app.py or log_picks_bulk).")
        return

    _seg_table(segs, "CLV by book", out)
    out(f"\n  Interpretation:")
    out(f"    + CLV vs sharp books = strong signal (hard market to beat)")
    out(f"    + CLV vs retail only = weaker signal (easier market)")
    out(f"    - CLV vs any book consistently = model is mispriced for that context")


def phase4_ev(rows: list[dict], out):
    _header("PHASE 4 — CLV BY EV% RANGE", out)
    out(f"\n  Model EV% = (model_prob − market_prob) / market_prob. Should correlate with CLV.")
    out(f"  High-EV picks should beat closing line more than low-EV picks if model is right.")

    segs = _by_segment(rows, _key_ev)
    _seg_table(segs, "CLV by EV range", out)

    # Check if EV gradient is positive
    ordered_ev = sorted(
        [(s["segment"], s["avg_pp"], s["n"]) for s in segs if s["n"] >= MIN_N_REPORTABLE],
        key=lambda x: ["EV <2%","EV 2-4%","EV 4-6%","EV 6-10%","EV 10%+"].index(x[0])
        if x[0] in ["EV <2%","EV 2-4%","EV 4-6%","EV 6-10%","EV 10%+"] else 99
    )
    if len(ordered_ev) >= 3:
        vals_pp = [v for _, v, _ in ordered_ev]
        is_ascending = all(vals_pp[i] <= vals_pp[i+1] for i in range(len(vals_pp)-1))
        is_generally_ascending = (vals_pp[-1] > vals_pp[0]) if len(vals_pp) >= 2 else False
        out(f"\n  EV gradient check:")
        if is_ascending or is_generally_ascending:
            out(f"    ✓ Higher model EV correlates with higher CLV — EV filter is meaningful")
        else:
            out(f"    ~ No clear EV-CLV gradient. Model EV may not predict market movement accurately.")
            out(f"      This is normal at small sample sizes.")


def phase5_odds(rows: list[dict], out):
    _header("PHASE 5 — CLV BY ODDS RANGE", out)
    out(f"\n  Long shots (+500+) move more in absolute pp terms but from a smaller base.")
    out(f"  Relative CLV (%) is more meaningful across odds ranges than raw pp.")

    segs = _by_segment(rows, _key_odds)
    _seg_table(segs, "CLV by opening odds", out, sort_key="odds")

    # Also compute relative CLV by odds
    buckets_rel: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        rel = _safe_float(r.get("clv_pct_rel"))
        if rel is None:
            continue
        k = _key_odds(r)
        if k is None:
            continue
        buckets_rel[k].append(rel)

    rel_table = [
        (k, sum(v)/len(v), len(v))
        for k, v in buckets_rel.items()
        if len(v) >= MIN_N_REPORTABLE
    ]
    if rel_table:
        out(f"\n  Relative CLV (%) by odds — more comparable across ranges:")
        out(f"  {'Odds Range':<18} {'n':>5} {'Avg rel CLV':>13}")
        out(f"  {'─'*38}")
        for seg, avg_r, n in sorted(rel_table, key=lambda x: -x[2]):
            flag = _sig_flag(n)
            out(f"  {seg:<18} {n:>5} {avg_r:>+13.2f}%{flag}")


def phase6_prob(rows: list[dict], out):
    _header("PHASE 6 — CLV BY MODEL PROBABILITY BUCKET", out)
    out(f"\n  Model probability buckets mirror the calibration audit (monitoring_dashboard.py Phase 4).")
    out(f"  If CLV is negative in specific prob buckets, calibration may be off for that range.")

    segs = _by_segment(rows, _key_prob)
    _seg_table(segs, "CLV by model probability", out)

    segs_edge = _by_segment(rows, _key_edge)
    _seg_table(segs_edge, "CLV by edge%", out)


def phase7_trend(rows: list[dict], out):
    _header("PHASE 7 — CLV TREND OVER TIME", out)

    vals_all = [_safe_float(r.get("clv_pp")) for r in rows]
    n_with   = sum(1 for v in vals_all if v is not None)

    if n_with < 20:
        out(f"\n  Insufficient data for trend analysis (need 20+ picks with CLV, have {n_with}).")
        return

    rolling = _rolling_clv(rows, window=20)
    if len(rolling) < 3:
        out(f"\n  Not enough rolling windows to display trend.")
        return

    out(f"\n  Rolling 20-pick CLV average (most recent last):")
    out(f"  {'Pick#':>6}  {'Date':<12} {'Roll.AvgCLV':>12} {'Beats%':>8}")
    out(f"  {'─'*42}")

    # Show every 5th window + last
    step = max(1, len(rolling) // 10)
    display_idxs = set(range(0, len(rolling), step)) | {len(rolling) - 1}
    for i, r in enumerate(rolling):
        if i in display_idxs:
            trend = ""
            if i > 0:
                prev = rolling[i-1]["avg_clv"]
                curr = r["avg_clv"]
                trend = " ↑" if curr > prev + 0.1 else (" ↓" if curr < prev - 0.1 else " →")
            out(f"  {r['pick_num']:>6}  {r['date']:<12} {r['avg_clv']:>+12.3f}pp "
                f"{r['beats_pct']:>7.1f}%{trend}")

    first_avg = rolling[0]["avg_clv"]
    last_avg  = rolling[-1]["avg_clv"]
    change    = last_avg - first_avg
    out(f"\n  Trend: {'improving' if change > 0.1 else ('declining' if change < -0.1 else 'flat')} "
        f"({change:+.3f}pp over {len(rolling)} windows)")
    if last_avg > 1.0:
        out(f"  ✓ CLV is tracking positive — model has been finding value")
    elif last_avg > 0.0:
        out(f"  → CLV is marginally positive — directional signal good, needs more data")
    else:
        out(f"  ~ CLV has dipped negative recently — watch calibration drift")


def phase8_persistence(rows: list[dict], out):
    _header("PHASE 8 — CLV PERSISTENCE & EDGE STABILITY", out)

    vals_all = [_safe_float(r.get("clv_pp")) for r in rows]
    vals_all = [v for v in vals_all if v is not None]
    n        = len(vals_all)

    if n < 40:
        out(f"\n  Insufficient data for persistence analysis (need 40+ picks, have {n}).")
        out(f"  Re-run once more closing lines are captured.")
        return

    # Split into halves
    half = n // 2
    first_half  = vals_all[:half]
    second_half = vals_all[half:]

    avg_first  = sum(first_half) / half
    avg_second = sum(second_half) / len(second_half)

    out(f"\n  CLV stability across time (first {half} vs last {len(second_half)} picks):")
    out(f"    First {half:<4} picks: avg CLV = {avg_first:+.3f}pp  "
        f"beats = {_beats_pct(first_half):.1f}%")
    out(f"    Last  {len(second_half):<4} picks: avg CLV = {avg_second:+.3f}pp  "
        f"beats = {_beats_pct(second_half):.1f}%")

    change = avg_second - avg_first
    if abs(change) < 0.5:
        out(f"\n  → CLV is stable ({change:+.3f}pp change) — no meaningful drift")
    elif change > 0:
        out(f"\n  ✓ CLV is improving over time ({change:+.3f}pp) — model learning or market lagging")
    else:
        out(f"\n  ~ CLV is declining over time ({change:+.3f}pp) — possible market efficiency increase")

    # Date coverage
    dates = sorted({r.get("date","") for r in rows if r.get("date") and _safe_float(r.get("clv_pp")) is not None})
    if dates:
        out(f"\n  Date range: {dates[0]} → {dates[-1]}  ({len(dates)} distinct dates)")

    # By quarter if enough data
    if n >= 80:
        quarters = [vals_all[i*n//4:(i+1)*n//4] for i in range(4)]
        out(f"\n  Quartile breakdown (Q1=earliest, Q4=latest):")
        for i, q in enumerate(quarters, 1):
            if q:
                out(f"    Q{i} (n={len(q):>4}): avg CLV = {sum(q)/len(q):+.3f}pp  "
                    f"beats = {_beats_pct(q):.1f}%")


def phase9_validity(rows: list[dict], out):
    _header("PHASE 9 — STATISTICAL VALIDITY & MILESTONES", out)

    vals_all = [_safe_float(r.get("clv_pp")) for r in rows]
    vals_all = [v for v in vals_all if v is not None]
    n        = len(vals_all)

    milestones = [20, 50, 100, 200, 500]

    out(f"\n  Sample milestones (CLV data):")
    for m in milestones:
        if n >= m:
            out(f"    ✓  n≥{m:<5} — reached ({n} total)")
        else:
            out(f"    ○  n≥{m:<5} — need {m - n} more picks with CLV")

    if n < 20:
        out(f"\n  STATUS: Too early for any CLV conclusions ({n} picks with CLV).")
        out(f"          Run capture_closing_lines.py daily to accumulate data.")
        return

    avg = sum(vals_all) / n
    ci  = _ci_half(vals_all)
    ci_lo = avg - ci
    ci_hi = avg + ci

    out(f"\n  Current estimate: {avg:+.3f}pp  (95% CI: {ci_lo:+.3f} to {ci_hi:+.3f})")

    # Test if significantly different from 0
    if ci_lo > 0.0:
        out(f"  ✓ 95% CI is entirely positive — CLV is statistically significant (sharp signal)")
    elif ci_hi < 0.0:
        out(f"  ✗ 95% CI is entirely negative — CLV is statistically significantly soft")
    else:
        out(f"  ~ 95% CI crosses zero — CLV is not yet statistically distinguishable from 0")
        out(f"    Continue accumulating picks.")

    # Variance and distribution
    if n >= 5:
        var = sum((v - avg)**2 for v in vals_all) / (n - 1)
        sd  = math.sqrt(var)
        out(f"\n  CLV distribution:")
        out(f"    Std dev  : ±{sd:.3f}pp")
        out(f"    Min      : {min(vals_all):+.3f}pp")
        out(f"    Max      : {max(vals_all):+.3f}pp")
        out(f"    Pct >0   : {_beats_pct(vals_all):.1f}%")
        out(f"    Pct >1pp : {sum(1 for v in vals_all if v > 1.0)/n*100:.1f}%")
        out(f"    Pct <-3pp: {sum(1 for v in vals_all if v < -3.0)/n*100:.1f}%")

    out(f"\n  Recommended next action:")
    if n < 50:
        out(f"    Focus on capturing closing lines daily. Avoid any model changes based on CLV.")
    elif n < 100:
        out(f"    CLV is directional only. Flag any segments with n≥20 and avg<-1pp for monitoring.")
        out(f"    Do NOT modify model until n≥100.")
    elif n < 200:
        out(f"    CLV is actionable at segment level for n≥50 segments.")
        out(f"    Consider adjusting EV thresholds if overall CLV is negative for n≥100.")
    else:
        out(f"    n≥200 — statistical conclusions are robust for overall and major segments.")
        out(f"    Minor segments (n<50) remain directional only.")

    # Cross-validation with ROI
    tracker_rows = _load_tracker()
    settled = [r for r in tracker_rows if r.get("hr_result") in ("0","1")]
    n_settled = len(settled)
    if n_settled > 0:
        wins = sum(1 for r in settled if r.get("hr_result") == "1")
        out(f"\n  Cross-reference with settled picks:")
        out(f"    Settled picks  : {n_settled}")
        out(f"    Win rate       : {wins/n_settled*100:.1f}%")
        out(f"    CLV data       : {n} picks ({n/n_settled*100:.0f}% coverage)")
        if n > 0 and n_settled > 0:
            out(f"\n  NOTE: CLV validates long-run edge independently of wins/losses.")
            out(f"    Positive CLV at n≥100 is strong evidence of real edge even if ROI is volatile.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    summary_only   = "--summary" in args
    tracker_only   = "--tracker" in args
    phase_filter   = None
    if "--phase" in args:
        idx = args.index("--phase")
        if idx + 1 < len(args):
            try:
                phase_filter = int(args[idx + 1])
            except ValueError:
                pass

    buf_lines = []

    def out(msg=""):
        print(msg)
        buf_lines.append(msg)

    rows = _load_combined(use_tracker_only=tracker_only)

    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out(f"\n{'='*W}")
    out(f"  CLV ANALYSIS REPORT — {ts}")
    if tracker_only:
        out(f"  Source: pick_tracker.csv only")
    out(f"{'='*W}")

    if summary_only:
        phase1_summary(rows, out)
        out(f"\n{'='*W}\n")
        return

    run = lambda n, fn: fn(rows, out) if (phase_filter is None or phase_filter == n) else None

    run(1, phase1_summary)
    run(2, phase2_barrel)
    run(3, phase3_book)
    run(4, phase4_ev)
    run(5, phase5_odds)
    run(6, phase6_prob)
    run(7, phase7_trend)
    run(8, phase8_persistence)
    run(9, phase9_validity)

    out(f"\n{'='*W}")
    out(f"  END OF CLV REPORT")
    out(f"  Capture more CLV data: py -3.12 capture_closing_lines.py (run ~30min before first pitch)")
    out(f"  Daily automation: py -3.12 ops_daily.py")
    out(f"{'='*W}\n")

    # Save report
    try:
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(buf_lines))
        print(f"  Report saved: {OUT_PATH}")
    except Exception as e:
        print(f"  [WARN] Could not save report: {e}")


if __name__ == "__main__":
    main()
