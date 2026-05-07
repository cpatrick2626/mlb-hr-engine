"""
Auto-Learn Engine — analyzes settled picks to surface what's actually working
and generate specific, numbered formula adjustment suggestions.

Called by the Performance tab to display insights and by apply_suggestion()
to write approved changes to learned_adjustments.json.

Learning targets:
  - Feature correlations   → which model inputs actually predict HRs
  - Model calibration      → is model_prob accurate vs actual hit rate
  - Per-source performance → which tab/strategy/formula generates the best picks
  - JIG weight suggestions → barrel vs xSLG vs pitch vs pull etc.
  - Threshold suggestions  → ev_pct, edge_pct, model_prob floor
"""

import json
import math
import statistics
from pathlib import Path
from typing import Optional

from tracking.pick_tracker import settled_rows, summary_by, total_summary

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

# JIG weight fields — must match the sliders in app.py
JIG_FIELDS = [
    ("barrel_pct",   "Barrel%"),
    ("xslg",         "xSLG"),
    ("pitcher_factor","Pitcher"),
    ("hard_hit_pct", "Hard Hit"),
    ("iso",          "ISO"),
    ("pull_pct",     "Pull%"),
    ("launch_angle", "Launch"),
]

MIN_PICKS_FOR_ANALYSIS = 15
MIN_PICKS_PER_FEATURE  = 10


# ── Public API ────────────────────────────────────────────────────────────────

def analyze() -> dict:
    """
    Full analysis pass. Returns a dict with keys:
      correlations, calibration, tab_performance, source_section_performance,
      jig_comparison, suggestions, total_picks, sufficient_data
    """
    rows = settled_rows()
    n = len(rows)
    if n < MIN_PICKS_FOR_ANALYSIS:
        return {
            "sufficient_data": False,
            "total_picks":     n,
            "needed":          MIN_PICKS_FOR_ANALYSIS,
        }

    outcomes = [int(r.get("hr_result", 0)) for r in rows]

    correlations       = _feature_correlations(rows, outcomes)
    calibration        = _calibration(rows, outcomes)
    tab_perf           = summary_by("source_tab")
    section_perf       = summary_by("source_section")
    jig_comparison     = _jig_comparison(tab_perf, section_perf)
    suggestions        = _generate_suggestions(correlations, calibration, tab_perf, jig_comparison)

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
    adj = load_adjustments()
    rows  = settled_rows()
    if not rows:
        return False

    outcomes = [int(r.get("hr_result", 0)) for r in rows]
    corrs    = _feature_correlations(rows, outcomes)
    calib    = _calibration(rows, outcomes)

    if suggestion_id == "jig_weights":
        adj["jig_weights"] = _compute_jig_weight_suggestion(corrs)
    elif suggestion_id == "min_ev":
        adj["min_ev_pct"] = _compute_ev_threshold(rows)
    elif suggestion_id == "min_model_prob":
        adj["min_model_prob"] = _compute_prob_threshold(rows)
    elif suggestion_id == "prob_scale":
        adj["prob_scale"] = _compute_prob_scale(calib)
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
            "field":   field,
            "label":   label,
            "note":    note,
            "corr":    round(corr, 4),
            "n":       len(vals),
            "n_hits":  n_hits,
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
            "bucket":       f"{avg_pred*100:.0f}%",
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
) -> list[dict]:
    suggestions = []
    sid = 0

    # ── 1. JIG weight rebalancing ──────────────────────────────────────────
    jig_corrs = {c["field"]: c for c in correlations if c["field"] in dict(JIG_FIELDS)}
    if len(jig_corrs) >= 3:
        sid += 1
        new_weights = _compute_jig_weight_suggestion(correlations)
        weight_lines = [f"{lbl}: {new_weights.get(field, '—'):.0%}" for field, lbl in JIG_FIELDS if field in new_weights]
        suggestions.append({
            "id":        "jig_weights",
            "sid":       sid,
            "title":     "Rebalance JIG Formula Weights",
            "detail":    (
                "Based on feature-outcome correlations from your settled picks, "
                "the highest-predicting metrics should carry more weight. "
                "Suggested new weights: " + ", ".join(weight_lines) + "."
            ),
            "value":     new_weights,
            "impact":    "medium",
        })

    # ── 2. Model probability calibration ──────────────────────────────────
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

    # ── 3. EV threshold adjustment ─────────────────────────────────────────
    settled = [r for r in _load_settled_cached()]
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

    # ── 4. JIG AI vs JIG Way recommendation ───────────────────────────────
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

    # ── 5. Underperforming factors ─────────────────────────────────────────
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
                    f"across {lc['n']} picks. Consider reducing its weight in the JIG formula or "
                    "its threshold in strategy filters."
                ),
                "value":  {f"reduce_{lc['field']}": True},
                "impact": "low",
            })

    return suggestions


# ── Computation helpers ───────────────────────────────────────────────────────

def _compute_jig_weight_suggestion(correlations: list[dict]) -> dict:
    """
    Convert feature correlations to JIG weights using softmax-like normalization.
    Only includes fields that appear in JIG_FIELDS.
    """
    jig_field_set = {f for f, _ in JIG_FIELDS}
    relevant = {c["field"]: max(0.0, c["corr"]) for c in correlations if c["field"] in jig_field_set}

    if not relevant:
        return {}

    total = sum(relevant.values())
    if total <= 0:
        n = len(relevant)
        return {f: round(1 / n, 2) for f in relevant}

    raw = {f: v / total for f, v in relevant.items()}

    # Clamp: no single weight < 3% or > 40%
    clamped = {f: max(0.03, min(0.40, v)) for f, v in raw.items()}
    ctotal  = sum(clamped.values())
    return {f: round(v / ctotal, 2) for f, v in clamped.items()}


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


_settled_cache: list[dict] = []


def _load_settled_cached() -> list[dict]:
    global _settled_cache
    if not _settled_cache:
        _settled_cache = settled_rows()
    return _settled_cache


def _save_adjustments(adj: dict) -> None:
    ADJUSTMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ADJUSTMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(adj, f, indent=2)
