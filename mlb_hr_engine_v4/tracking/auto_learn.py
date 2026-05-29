"""
Auto-Learn Engine — analyzes settled picks to surface what's actually working
and generate specific, numbered formula adjustment suggestions.

Called by the Performance tab to display insights and by apply_suggestion()
to write approved changes to learned_adjustments.json.

Performance notes:
- analyze() calls _pt_load_all() ONCE, then passes rows through the whole pipeline.
- summary_by() receives the pre-loaded rows list; no extra CSV reads.
- _generate_suggestions() receives the settled rows list; no module-level cache.
- apply_suggestion() also does a single read pass.

Learning targets:
  - Feature correlations   → which model inputs actually predict HRs
  - Model calibration      → is model_prob accurate vs actual hit rate
  - Per-source performance → which tab/strategy/formula generates the best picks
  - Threshold suggestions  → ev_pct, edge_pct, model_prob floor

NOTE: JIG weight suggestions are intentionally excluded. The JIG model uses
fixed weights and must remain isolated from main-engine adaptive logic.
"""

import json
import math
import os
import statistics
from pathlib import Path

import config
from tracking.pick_tracker import load_all as _pt_load_all, settled_rows, summary_by, total_summary

ADJUSTMENTS_PATH = Path(__file__).parent / "learned_adjustments.json"

# Feature definitions: (csv_field, display_label, direction_note)
FEATURES = [
    ("barrel_pct",      "Barrel %",         "Higher = more HRs"),
    ("exit_velo",       "Exit Velocity",     "Higher = more HRs"),
    ("hard_hit_pct",    "Hard Hit %",        "Higher = more HRs"),
    ("xslg",            "xSLG",             "Higher = more HRs"),
    ("slg",             "SLG",              "Higher = more HRs"),
    ("iso",             "ISO",              "Higher = more HRs"),
    ("pull_pct",        "Pull %",           "Higher = more HRs"),
    ("park_factor",     "Park Factor",      "Higher = more HRs"),
    ("pitcher_factor",  "Pitcher Factor",   "Higher = more HRs"),
    ("platoon_factor",  "Platoon Factor",   "Higher = more HRs"),
    ("weather_factor",  "Weather Factor",   "Higher = more HRs"),
    ("streak_factor",   "Streak Factor",    "Higher = more HRs"),
    ("model_prob_pct",  "Model Prob %",     "Primary model output"),
    ("ev_pct",          "EV %",             "Positive = good value"),
    ("edge_pct",        "Edge %",           "Higher = sharper edge"),
    ("confidence",      "Confidence Score", "Internal ranking signal"),
    ("pitcher_hr9",     "Pitcher HR/9",     "Higher = worse pitcher"),
    ("pitcher_k_pct",   "Pitcher K%",       "Higher = better pitcher (negative)"),
    ("launch_angle",    "Launch Angle",     "Optimal 20-35°"),
]

MIN_PICKS_FOR_ANALYSIS = 15
MIN_PICKS_PER_FEATURE  = 10


# ── Public API ────────────────────────────────────────────────────────────────

def analyze() -> dict:
    """
    Full analysis pass. ONE CSV read; rows passed through the entire pipeline.
    Returns a dict with keys:
      correlations, calibration, tab_performance, source_section_performance,
      jig_comparison, suggestions, total_picks, sufficient_data
    """
    all_rows = _pt_load_all()
    rows     = settled_rows(all_rows)
    n = len(rows)
    if n < MIN_PICKS_FOR_ANALYSIS:
        return {
            "sufficient_data": False,
            "total_picks":     n,
            "needed":          MIN_PICKS_FOR_ANALYSIS,
        }

    outcomes = [int(r.get("hr_result", 0)) for r in rows]

    correlations   = _feature_correlations(rows, outcomes)
    calibration    = _calibration(rows, outcomes)
    # Pass pre-loaded rows so summary_by() skips its own CSV read
    tab_perf       = summary_by("source_tab",     all_rows)
    section_perf   = summary_by("source_section", all_rows)
    jig_comparison = _jig_comparison(tab_perf, section_perf)
    suggestions    = _generate_suggestions(correlations, calibration, tab_perf, jig_comparison, rows)

    return {
        "sufficient_data":       True,
        "total_picks":           n,
        "correlations":          correlations,
        "calibration":           calibration,
        "tab_performance":       tab_perf,
        "section_performance":   section_perf,
        "jig_comparison":        jig_comparison,
        "suggestions":           suggestions,
        "applied_adjustments":   load_adjustments(),
    }


def apply_suggestion(suggestion_id: str, value=None) -> bool:
    """
    Write an approved suggestion to learned_adjustments.json.
    Returns True on success.
    """
    adj      = load_adjustments()
    all_rows = _pt_load_all()
    rows     = settled_rows(all_rows)
    if not rows:
        return False

    outcomes = [int(r.get("hr_result", 0)) for r in rows]
    corrs    = _feature_correlations(rows, outcomes)
    calib    = _calibration(rows, outcomes)

    if suggestion_id == "min_ev":
        adj["min_ev_pct"] = _compute_ev_threshold(rows)
    elif suggestion_id == "min_model_prob":
        adj["min_model_prob"] = _compute_prob_threshold(rows)
    elif suggestion_id == "prob_scale":
        adj["prob_scale"] = _compute_prob_scale(calib)
    # ranker_ev_weight learning retired — Ranker Reform 2026-05-29
    elif suggestion_id == "recent_weight":
        new_rw = _compute_recent_weight(rows)
        if new_rw is not None:
            adj["recent_weight"] = round(new_rw, 2)
        else:
            return False
    elif suggestion_id == "custom" and value is not None:
        adj.update(value)
    else:
        return False

    _save_adjustments(adj)
    return True


def load_adjustments() -> dict:
    """Load currently applied adjustments from disk."""
    if not ADJUSTMENTS_PATH.exists():
        return {}
    try:
        with open(ADJUSTMENTS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def reset_adjustments() -> None:
    """Remove all learned adjustments."""
    if ADJUSTMENTS_PATH.exists():
        ADJUSTMENTS_PATH.unlink()


def auto_apply_safe() -> dict:
    """
    Automatically apply low-risk weight adjustments based on settled picks.

    Skips if results.csv hasn't changed since learned_adjustments.json was last
    written — so there's no overhead on runs with no new settled picks.

    Returns {"applied": list[str], "skipped": str | None}.
    """
    results_path = Path(__file__).parent / "results.csv"

    # Skip if no new results since last adjustment write
    if results_path.exists() and ADJUSTMENTS_PATH.exists():
        if os.path.getmtime(str(results_path)) <= os.path.getmtime(str(ADJUSTMENTS_PATH)):
            return {"applied": [], "skipped": "no new results"}

    all_rows = _pt_load_all()
    rows     = settled_rows(all_rows)
    n        = len(rows)
    if n < 15:
        return {"applied": [], "skipped": f"insufficient data ({n} settled picks, need 15)"}

    outcomes = [int(r.get("hr_result", 0)) for r in rows]
    calib    = _calibration(rows, outcomes)
    adj      = load_adjustments()
    applied  = []

    # 1. Probability calibration scale
    if n >= 20 and calib:
        total_bias = sum(b["bias_pct"] for b in calib) / len(calib)
        if abs(total_bias) >= 2.0:
            scale = _compute_prob_scale(calib)
            scale = round(max(0.88, min(1.12, scale)), 3)  # tighter auto-apply bounds
            if abs(scale - adj.get("prob_scale", 1.0)) >= 0.02:
                adj["prob_scale"] = scale
                applied.append(f"prob_scale→{scale:.3f} (avg bias {total_bias:+.1f}%)")

    # 2. EV threshold — only raise when low-EV picks clearly underperform
    if n >= 20:
        low_ev  = [r for r in rows if 0 < float(r.get("ev_pct", 0) or 0) < 3.0]
        high_ev = [r for r in rows if float(r.get("ev_pct", 0) or 0) >= 5.0]
        if len(low_ev) >= 8 and len(high_ev) >= 8:
            low_wr  = _win_rate(low_ev)
            high_wr = _win_rate(high_ev)
            if low_wr < high_wr - 0.10:
                new_min = _compute_ev_threshold(rows)
                new_min = round(max(2.0, min(6.0, new_min)), 1)
                if abs(new_min - adj.get("min_ev_pct", config.MIN_EV_PCT)) >= 0.5:
                    adj["min_ev_pct"] = new_min
                    applied.append(
                        f"min_ev_pct→{new_min:.1f}% "
                        f"(low-EV win rate {low_wr:.0%} vs {high_wr:.0%})"
                    )

    # 4. Recent/season blend (needs streak_factor in picks log)
    if n >= 25:
        new_rw = _compute_recent_weight(rows)
        if new_rw is not None:
            new_rw = round(max(0.20, min(0.45, new_rw)), 2)
            if abs(new_rw - adj.get("recent_weight", config.RECENT_WEIGHT)) >= 0.04:
                adj["recent_weight"] = new_rw
                applied.append(f"recent_weight→{new_rw:.2f}")

    if applied:
        _save_adjustments(adj)
        try:
            from tracking import adaptive_weights as _aw
            _aw.invalidate_cache()
        except Exception:
            pass

    return {"applied": applied, "skipped": None if applied else "no improvements found"}


# ── Analysis helpers ──────────────────────────────────────────────────────────

def _feature_correlations(rows: list[dict], outcomes: list[int]) -> list[dict]:
    """
    Point-biserial correlation between each numeric feature and HR outcome.
    Returns list sorted by |correlation| descending.
    """
    results = []
    for field, label, note in FEATURES:
        vals, paired = [], []
        for r, o in zip(rows, outcomes):
            try:
                v = float(r.get(field, "") or "0")
                if v != 0.0:
                    vals.append(v)
                    paired.append(o)
            except (ValueError, TypeError):
                pass
        if len(vals) < MIN_PICKS_PER_FEATURE:
            continue
        corr = _point_biserial(vals, paired)
        n_hits = sum(paired)
        results.append({
            "field":    field,
            "label":    label,
            "note":     note,
            "corr":     round(corr, 4),
            "n":        len(vals),
            "n_hits":   n_hits,
            "strength": _corr_strength(corr),
        })
    return sorted(results, key=lambda x: abs(x["corr"]), reverse=True)


def _calibration(rows: list[dict], outcomes: list[int]) -> list[dict]:
    """
    Bucket picks by model_prob decile; compare avg predicted vs avg actual.
    Returns list of bucket dicts.
    """
    paired = []
    for r, o in zip(rows, outcomes):
        try:
            prob = float(r.get("model_prob_pct", "0") or "0") / 100.0
            if 0 < prob <= 1:
                paired.append((prob, o))
        except (ValueError, TypeError):
            pass

    if len(paired) < 10:
        return []

    paired.sort(key=lambda x: x[0])
    n = len(paired)
    bucket_size = max(5, n // 5)

    buckets = []
    for i in range(0, n, bucket_size):
        chunk = paired[i: i + bucket_size]
        if not chunk:
            continue
        probs   = [x[0] for x in chunk]
        actuals = [x[1] for x in chunk]
        avg_pred   = statistics.mean(probs)
        avg_actual = statistics.mean(actuals)
        bias = avg_actual - avg_pred
        buckets.append({
            "bucket":        f"{avg_pred*100:.0f}%",
            "avg_predicted": round(avg_pred * 100, 1),
            "avg_actual":    round(avg_actual * 100, 1),
            "bias_pct":      round(bias * 100, 1),
            "n":             len(chunk),
        })
    return buckets


def _jig_comparison(tab_perf: list[dict], section_perf: list[dict]) -> dict:
    """Extract JIG AI vs JIG Way head-to-head from section performance."""
    ai_row  = next((r for r in section_perf if "JIG AI"  in r.get("source_section", "")), None)
    way_row = next((r for r in section_perf if "JIG Way" in r.get("source_section", "")), None)
    return {"ai": ai_row, "way": way_row}


def _generate_suggestions(
    correlations: list[dict],
    calibration:  list[dict],
    tab_perf:     list[dict],
    jig_comp:     dict,
    settled:      list[dict],
) -> list[dict]:
    """Build numbered suggestion list. `settled` is the pre-loaded settled rows list."""
    suggestions = []
    sid = 0

    # ── 1. Model probability calibration ──────────────────────────────────
    if calibration:
        total_bias = sum(b["bias_pct"] for b in calibration) / len(calibration)
        if abs(total_bias) >= 2.0:
            sid += 1
            direction = "overestimates" if total_bias < 0 else "underestimates"
            scale = _compute_prob_scale(calibration)
            suggestions.append({
                "id":     "prob_scale",
                "sid":    sid,
                "title":  f"Recalibrate Model Probabilities (avg {total_bias:+.1f}% bias)",
                "detail": (
                    f"The model {direction} hit probability by an average of {abs(total_bias):.1f}% "
                    f"across your {sum(b['n'] for b in calibration)} settled picks. "
                    f"Applying a scale factor of {scale:.3f} to model_prob would improve calibration."
                ),
                "value":  {"prob_scale": scale},
                "impact": "high" if abs(total_bias) >= 5 else "medium",
            })

    # ── 2. EV threshold adjustment ─────────────────────────────────────────
    low_ev  = [r for r in settled if 0 < float(r.get("ev_pct", 0) or 0) < 3.0]
    high_ev = [r for r in settled if float(r.get("ev_pct", 0) or 0) >= 5.0]
    if len(low_ev) >= 10 and len(high_ev) >= 10:
        low_wr  = _win_rate(low_ev)
        high_wr = _win_rate(high_ev)
        if low_wr < high_wr - 0.05:
            sid += 1
            suggestions.append({
                "id":     "min_ev",
                "sid":    sid,
                "title":  f"Raise Min EV Threshold (low-EV picks: {low_wr*100:.0f}% vs high-EV: {high_wr*100:.0f}%)",
                "detail": (
                    f"Picks with EV 0–3% are winning at {low_wr*100:.0f}% vs "
                    f"{high_wr*100:.0f}% for EV 5%+ picks. "
                    "Raising MIN_EV_PCT to 5.0 would filter out underperforming low-edge picks."
                ),
                "value":  {"min_ev_pct": 5.0},
                "impact": "medium",
            })

    # ── 3. JIG AI vs JIG Way recommendation ───────────────────────────────
    ai  = jig_comp.get("ai")
    way = jig_comp.get("way")
    if ai and way and ai["_decided"] >= 5 and way["_decided"] >= 5:
        winner = "JIG AI" if ai["_win_rate"] >= way["_win_rate"] else "The JIG Way"
        delta  = abs(ai["_win_rate"] - way["_win_rate"]) * 100
        if delta >= 5.0:
            sid += 1
            suggestions.append({
                "id":     "jig_formula",
                "sid":    sid,
                "title":  f"Prefer {winner} formula (+{delta:.0f}% win rate)",
                "detail": (
                    f"JIG AI: {ai['Win%']} win rate ({ai['_decided']} picks). "
                    f"The JIG Way: {way['Win%']} win rate ({way['_decided']} picks). "
                    f"{winner} is outperforming by {delta:.0f} percentage points. "
                    "Consider using it as your primary tab until results converge."
                ),
                "value":  {"preferred_jig": winner},
                "impact": "high" if delta >= 10 else "medium",
            })

    # ── 4. Underperforming factors ─────────────────────────────────────────
    low_corr = [c for c in correlations if 0 < c["corr"] < 0.05 and c["n"] >= 15]
    if low_corr:
        for lc in low_corr[:2]:
            sid += 1
            suggestions.append({
                "id":     f"reduce_{lc['field']}",
                "sid":    sid,
                "title":  f"Reduce influence of {lc['label']} (corr={lc['corr']:.3f})",
                "detail": (
                    f"{lc['label']} shows near-zero correlation ({lc['corr']:.3f}) with actual HR outcomes "
                    f"across {lc['n']} picks. Consider reducing its threshold in strategy filters."
                ),
                "value":  {f"reduce_{lc['field']}": True},
                "impact": "low",
            })

    # ── 6. Recent/season weight ────────────────────────────────────────────
    new_rw = _compute_recent_weight(settled)
    if new_rw is not None:
        current_rw = load_adjustments().get("recent_weight", config.RECENT_WEIGHT)
        if abs(new_rw - current_rw) >= 0.04:
            direction = "increase" if new_rw > current_rw else "decrease"
            sid += 1
            suggestions.append({
                "id":     "recent_weight",
                "sid":    sid,
                "title":  f"{'Increase' if new_rw > current_rw else 'Decrease'} recent-form weight → {new_rw:.0%}",
                "detail": (
                    f"Hot-streak picks (streak_factor > 1.05) are winning at a "
                    f"meaningfully different rate than neutral picks across your settled history. "
                    f"Adjusting RECENT_WEIGHT {current_rw:.0%}→{new_rw:.0%} will {direction} "
                    "how much the last-20-game HR rate influences each prediction."
                ),
                "value":  {"recent_weight": new_rw},
                "impact": "medium",
            })

    return suggestions


# ── Computation helpers ───────────────────────────────────────────────────────

def _compute_ev_threshold(rows: list[dict]) -> float:
    """Find EV threshold that maximizes win rate on settled picks."""
    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    if len(settled) < 20:
        return 3.0
    thresholds = [t / 10 for t in range(10, 80, 5)]
    best_t, best_wr = 3.0, 0.0
    for t in thresholds:
        subset = [r for r in settled if float(r.get("ev_pct", 0) or 0) >= t]
        if len(subset) < 5:
            break
        wr = _win_rate(subset)
        if wr > best_wr:
            best_wr, best_t = wr, t
    return round(best_t, 1)


def _compute_prob_threshold(rows: list[dict]) -> float:
    """Find model_prob threshold that maximizes win rate."""
    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    if len(settled) < 20:
        return 0.06
    thresholds = [t / 100 for t in range(5, 20)]
    best_t, best_wr = 0.06, 0.0
    for t in thresholds:
        subset = [r for r in settled if float(r.get("model_prob_pct", 0) or 0) / 100 >= t]
        if len(subset) < 5:
            break
        wr = _win_rate(subset)
        if wr > best_wr:
            best_wr, best_t = wr, t
    return round(best_t, 3)


def _compute_prob_scale(calibration: list[dict]) -> float:
    """Compute a multiplicative scale for model_prob to reduce bias."""
    if not calibration:
        return 1.0
    total_pred   = sum(b["avg_predicted"] for b in calibration)
    total_actual = sum(b["avg_actual"]    for b in calibration)
    if total_pred <= 0:
        return 1.0
    scale = total_actual / total_pred
    return round(max(0.70, min(1.30, scale)), 3)


def _point_biserial(vals: list[float], outcomes: list[int]) -> float:
    """Point-biserial correlation between continuous vals and binary outcomes."""
    n = len(vals)
    if n < 5:
        return 0.0
    n1 = sum(outcomes)
    n0 = n - n1
    if n1 == 0 or n0 == 0:
        return 0.0
    try:
        m1 = statistics.mean(v for v, o in zip(vals, outcomes) if o == 1)
        m0 = statistics.mean(v for v, o in zip(vals, outcomes) if o == 0)
        sd = statistics.stdev(vals)
        if sd == 0:
            return 0.0
        return (m1 - m0) / sd * math.sqrt(n1 * n0 / n**2)
    except statistics.StatisticsError:
        return 0.0


def _corr_strength(corr: float) -> str:
    a = abs(corr)
    if a >= 0.30:
        return "Strong"
    if a >= 0.15:
        return "Moderate"
    if a >= 0.05:
        return "Weak"
    return "Negligible"


def _win_rate(rows: list[dict]) -> float:
    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    if not settled:
        return 0.0
    return sum(1 for r in settled if r.get("hr_result") == "1") / len(settled)


def _compute_recent_weight(rows: list[dict]) -> "float | None":
    """
    Compare win rates of hot-streak vs neutral picks to infer whether the
    recent 20-game HR rate should carry more or less weight than the season rate.
    Requires streak_factor column (added to LOG_FIELDS in v4).
    """
    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    # Require at least some rows with streak_factor data
    with_streak = [r for r in settled
                   if r.get("streak_factor") and r.get("streak_factor") not in ("", "None")]
    if len(with_streak) < 20:
        return None

    hot     = [r for r in with_streak if float(r["streak_factor"]) > 1.05]
    cold    = [r for r in with_streak if float(r["streak_factor"]) < 0.95]
    neutral = [r for r in with_streak if 0.95 <= float(r["streak_factor"]) <= 1.05]
    if len(hot) < 5 or len(neutral) < 5:
        return None

    hot_wr     = _win_rate(hot)
    neutral_wr = _win_rate(neutral)
    delta      = hot_wr - neutral_wr
    if abs(delta) < 0.05:
        return None

    current = config.RECENT_WEIGHT  # 0.30
    if delta > 0:
        return round(current + min(0.10, delta), 2)
    else:
        return round(current - min(0.08, abs(delta)), 2)


def _save_adjustments(adj: dict) -> None:
    ADJUSTMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ADJUSTMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(adj, f, indent=2)
