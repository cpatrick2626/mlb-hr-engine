"""
analyze_elite_separation.py  —  Elite Hitter Separation & Context Stack Moderation
====================================================================================
Analyzes whether archetype-conditioned context moderation improves calibration
for elite HR hitters vs average contact batters.

Key questions:
  1. Which batter archetypes are most over/under-predicted?
  2. How does the context multiplier distribute by power tier?
  3. Does moderating context by power_mult reduce bias for all archetypes?
  4. What moderation parameters produce the best overall calibration?

Methodology
-----------
  Reads fb_pct_raw_data.csv (10,777 batter-games, Apr 1–May 15 2026).
  Back-calculates combined_implied = -ln(1-p) / (adjusted_rate * exp_pa).
  Tests 6 moderation variants by applying power_mult as an attenuation factor
  to the context deviation (combined - 1.0), then recomputes model_prob.
  Metrics: Brier, MAE, bucket bias, elite-tier bias, Spearman rank stability.

Usage
-----
  py -3.12 analyze_elite_separation.py          # full analysis
  py -3.12 analyze_elite_separation.py --debug  # extra row-level diagnostics
"""

import csv
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent
CSV_PATH  = ROOT / "fb_pct_raw_data.csv"
OUT_PATH  = ROOT / "elite_separation_output.txt"

DEBUG = "--debug" in sys.argv

# ── PA by lineup spot (mirrors config.py LINEUP_PA) ──────────────────────────
LINEUP_PA = {1: 4.5, 2: 4.3, 3: 4.2, 4: 4.1, 5: 3.9,
             6: 3.7, 7: 3.6, 8: 3.4, 9: 3.2}
DEFAULT_PA = 3.8

# ── Calibration constants (from config.py / Session 21 fit) ──────────────────
CAL_A = 0.7805
CAL_B = -0.4611
MAX_PROB = 0.29


def _logit(p: float) -> float:
    p = max(1e-6, min(1 - 1e-6, p))
    return math.log(p / (1 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def calibrate(p: float) -> float:
    return round(min(MAX_PROB, max(0.001, _sigmoid(CAL_A * _logit(p) + CAL_B))), 4)


# ── Moderation variants ───────────────────────────────────────────────────────
VARIANTS = [
    {"name": "V0_Baseline",       "tag": "BASE",  "method": "baseline",    "floor": 1.00},
    {"name": "V1_Linear_f60",     "tag": "L60",   "method": "linear",      "floor": 0.60},
    {"name": "V2_Linear_f70",     "tag": "L70",   "method": "linear",      "floor": 0.70},
    {"name": "V3_Linear_f75",     "tag": "L75",   "method": "linear",      "floor": 0.75},
    {"name": "V4_Sqrt",           "tag": "SQRT",  "method": "sqrt",        "floor": 0.00},
    {"name": "V5_Cap_by_tier",    "tag": "CAP",   "method": "cap",         "floor": 0.00},
]


def moderate_combined(combined: float, power_mult: float, method: str, floor: float) -> float:
    """Apply archetype-conditioned moderation to the combined context multiplier."""
    dev = combined - 1.0  # deviation from neutral

    if method == "baseline":
        return combined

    elif method == "linear":
        # Scale context deviation by power_mult, floored at `floor`
        attn = max(floor, min(1.0, power_mult))
        return 1.0 + dev * attn

    elif method == "sqrt":
        # Softer nonlinear attenuation
        attn = min(1.0, math.sqrt(max(0.0, power_mult)))
        return 1.0 + dev * attn

    elif method == "cap":
        # Hard cap on combined by power_mult tier; suppression only, no boost
        if dev <= 0:
            return combined  # never inflate negative context
        if power_mult < 0.75:
            cap = 1.20
        elif power_mult < 1.00:
            cap = 1.30
        elif power_mult < 1.25:
            cap = 1.42
        else:
            cap = 1.50
        return min(combined, cap)

    return combined


def poisson_prob(rate: float, exp_pa: float, combined: float) -> float:
    combined = max(0.42, min(1.50, combined))
    lam = rate * combined * exp_pa
    return min(MAX_PROB, max(0.001, 1.0 - math.exp(-lam)))


# ── Brier / MAE helpers ───────────────────────────────────────────────────────
def brier(probs, actuals):
    return sum((p - a) ** 2 for p, a in zip(probs, actuals)) / len(probs)


def mae(probs, actuals):
    return sum(abs(p - a) for p, a in zip(probs, actuals)) / len(probs)


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def spearman(xs, ys):
    """Spearman rank correlation between two equal-length lists."""
    n = len(xs)
    if n < 2:
        return 1.0
    rank_x = _ranks(xs)
    rank_y = _ranks(ys)
    d2 = sum((rx - ry) ** 2 for rx, ry in zip(rank_x, rank_y))
    return 1 - (6 * d2) / (n * (n * n - 1))


def _ranks(xs):
    sorted_idx = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    for rank, idx in enumerate(sorted_idx, 1):
        ranks[idx] = float(rank)
    return ranks


# ── Load and parse CSV ────────────────────────────────────────────────────────
def load_rows():
    rows = []
    bad = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            try:
                lineup_spot_raw = raw.get("lineup_spot", "").strip()
                lineup_spot = int(lineup_spot_raw) if lineup_spot_raw and lineup_spot_raw.lower() not in ("none", "") else None
                exp_pa = LINEUP_PA.get(lineup_spot, DEFAULT_PA) if lineup_spot else DEFAULT_PA

                hit_hr_raw = raw.get("hit_hr", "False").strip().lower()
                actual = 1 if hit_hr_raw in ("true", "1", "yes") else 0

                model_prob = float(raw["model_prob"])
                hr_rate    = float(raw["hr_rate"])
                k_fac      = float(raw.get("k_fac", 1.0))
                streak_fac = float(raw.get("streak_fac", 1.0))
                power_mult = float(raw.get("power_mult", 1.0))
                pk_factor  = float(raw.get("pk_factor", 1.0))
                pit_factor = float(raw.get("pit_factor", 1.0))
                plat_factor = float(raw.get("plat_factor", 1.0))

                barrel_rate = float(raw.get("barrel_rate", 0.055))
                fb_pct      = float(raw.get("fb_pct", 0.264))
                sweet_spot  = float(raw.get("sweet_spot_pct", 0.334))
                pull_pct    = float(raw.get("pull_pct", 0.392))
                exit_velo   = float(raw.get("exit_velocity_avg", 89.1))
                hard_hit    = float(raw.get("hard_hit_pct", 0.399))
                xslg        = float(raw.get("xslg", 0.418))
                season_pa   = int(float(raw.get("season_pa", 0)))
                sc_source   = raw.get("sc_source", "none")

                # adjusted_rate: applies streak + K suppressor (early_supp and interaction
                # are excluded — not in CSV; mid-season these are near 1.0)
                adjusted_rate = min(0.15, hr_rate * k_fac * streak_fac)
                if adjusted_rate <= 0:
                    bad += 1
                    continue

                # Back-calculate the implied combined multiplier
                # model_prob = 1 - exp(-adjusted_rate * combined * exp_pa)
                # Clamp model_prob to avoid log(0) edge cases
                mp_safe = min(model_prob, MAX_PROB - 0.001)
                if mp_safe <= 0.001:
                    bad += 1
                    continue
                lam_implied = -math.log(1.0 - mp_safe)
                combined_implied = lam_implied / (adjusted_rate * exp_pa)
                # Clamp to physically reasonable range
                combined_implied = max(0.42, min(2.20, combined_implied))

                # Explicit context from CSV (no weather — w_factor not stored)
                combined_explicit = max(0.42, min(1.50, pk_factor * pit_factor * plat_factor))

                rows.append({
                    "actual":            actual,
                    "model_prob":        model_prob,
                    "hr_rate":           hr_rate,
                    "adjusted_rate":     adjusted_rate,
                    "exp_pa":            exp_pa,
                    "lineup_spot":       lineup_spot,
                    "power_mult":        power_mult,
                    "combined_implied":  combined_implied,
                    "combined_explicit": combined_explicit,
                    "pk_factor":         pk_factor,
                    "pit_factor":        pit_factor,
                    "plat_factor":       plat_factor,
                    "barrel_rate":       barrel_rate,
                    "fb_pct":            fb_pct,
                    "sweet_spot":        sweet_spot,
                    "pull_pct":          pull_pct,
                    "exit_velo":         exit_velo,
                    "hard_hit":          hard_hit,
                    "xslg":              xslg,
                    "season_pa":         season_pa,
                    "sc_source":         sc_source,
                    "player_name":       raw.get("player_name", ""),
                })
            except (ValueError, KeyError, ZeroDivisionError):
                bad += 1
    return rows, bad


# ── Archetype binning ─────────────────────────────────────────────────────────
def barrel_tier(barrel_rate: float) -> str:
    if barrel_rate >= 0.12:
        return "Elite (≥12%)"
    elif barrel_rate >= 0.09:
        return "Power (9–12%)"
    elif barrel_rate >= 0.055:
        return "Average (5.5–9%)"
    else:
        return "Contact (<5.5%)"


def power_mult_tier(pm: float) -> str:
    if pm >= 1.20:
        return "Elite (≥1.20)"
    elif pm >= 1.00:
        return "Above avg (1.0–1.20)"
    elif pm >= 0.80:
        return "Below avg (0.80–1.0)"
    else:
        return "Suppressed (<0.80)"


def context_tier(combined: float) -> str:
    if combined >= 1.35:
        return "High (≥1.35)"
    elif combined >= 1.20:
        return "Moderate (1.20–1.35)"
    elif combined >= 1.05:
        return "Mild (1.05–1.20)"
    else:
        return "Neutral (<1.05)"


def prob_bucket(p: float) -> str:
    if p < 0.08:
        return "<8%"
    elif p < 0.12:
        return "8–12%"
    elif p < 0.15:
        return "12–15%"
    elif p < 0.18:
        return "15–18%"
    elif p < 0.22:
        return "18–22%"
    else:
        return "22%+"


BARREL_TIER_ORDER   = ["Elite (≥12%)", "Power (9–12%)", "Average (5.5–9%)", "Contact (<5.5%)"]
POWER_TIER_ORDER    = ["Elite (≥1.20)", "Above avg (1.0–1.20)", "Below avg (0.80–1.0)", "Suppressed (<0.80)"]
CONTEXT_TIER_ORDER  = ["High (≥1.35)", "Moderate (1.20–1.35)", "Mild (1.05–1.20)", "Neutral (<1.05)"]
PROB_BUCKET_ORDER   = ["<8%", "8–12%", "12–15%", "15–18%", "18–22%", "22%+"]


# ── Report builder ────────────────────────────────────────────────────────────
def run_analysis():
    print("Loading CSV...")
    rows, bad = load_rows()
    print(f"  Loaded {len(rows):,} rows  |  Skipped {bad} bad rows")

    lines = []

    def sep(char="═", width=88):
        lines.append(char * width)

    def hdr(title):
        sep()
        lines.append(f"  {title}")
        sep()

    def row_str(*cols, widths=None):
        if widths is None:
            widths = [30] + [10] * (len(cols) - 1)
        return "".join(str(c).ljust(w) for c, w in zip(cols, widths))

    # ── SECTION 1: DATASET OVERVIEW ──────────────────────────────────────────
    hdr("SECTION 1 — DATASET OVERVIEW")
    lines.append(f"  Total batter-games : {len(rows):,}")
    lines.append(f"  Total HR outcomes  : {sum(r['actual'] for r in rows):,}")
    lines.append(f"  Actual HR rate     : {mean([r['actual'] for r in rows]):.4f} ({mean([r['actual'] for r in rows])*100:.2f}%)")
    lines.append(f"  Mean model_prob    : {mean([r['model_prob'] for r in rows]):.4f} ({mean([r['model_prob'] for r in rows])*100:.2f}%)")
    lines.append(f"  Overall model bias : {(mean([r['model_prob'] for r in rows]) - mean([r['actual'] for r in rows]))*100:+.2f}pp")
    lines.append(f"  Brier score        : {brier([r['model_prob'] for r in rows], [r['actual'] for r in rows]):.5f}")
    lines.append(f"  MAE                : {mae([r['model_prob'] for r in rows], [r['actual'] for r in rows]):.5f}")
    lines.append("")

    # Statcast source breakdown
    sc_groups: dict[str, list] = {}
    for r in rows:
        sc_groups.setdefault(r["sc_source"], []).append(r)
    lines.append("  Statcast source distribution:")
    lines.append(f"  {'Source':<12} {'N':>7}  {'Actual%':>8}  {'Model%':>8}  {'Bias':>8}")
    lines.append("  " + "-" * 52)
    for src in ["current", "blended", "prior", "none"]:
        grp = sc_groups.get(src, [])
        if not grp:
            continue
        a = mean([r["actual"] for r in grp])
        m = mean([r["model_prob"] for r in grp])
        lines.append(f"  {src:<12} {len(grp):>7,}  {a*100:>7.2f}%  {m*100:>7.2f}%  {(m-a)*100:>+7.2f}pp")
    lines.append("")

    # ── SECTION 2: ELITE HITTER ARCHETYPE ANALYSIS ───────────────────────────
    hdr("SECTION 2 — ELITE HITTER ARCHETYPE ANALYSIS (by barrel_rate tier)")
    lines.append(f"  {'Tier':<22} {'N':>6}  {'HR%Act':>7}  {'HR%Mod':>7}  {'Bias':>8}  {'Brier':>8}  {'MAE':>8}")
    lines.append("  " + "-" * 72)

    for tier in BARREL_TIER_ORDER:
        grp = [r for r in rows if barrel_tier(r["barrel_rate"]) == tier]
        if not grp:
            continue
        a = mean([r["actual"] for r in grp])
        m = mean([r["model_prob"] for r in grp])
        b = brier([r["model_prob"] for r in grp], [r["actual"] for r in grp])
        m_ae = mae([r["model_prob"] for r in grp], [r["actual"] for r in grp])
        lines.append(f"  {tier:<22} {len(grp):>6,}  {a*100:>6.2f}%  {m*100:>6.2f}%  {(m-a)*100:>+7.2f}pp  {b:>8.5f}  {m_ae:>8.5f}")

    lines.append("")
    lines.append("  By power_mult tier:")
    lines.append(f"  {'Tier':<26} {'N':>6}  {'HR%Act':>7}  {'HR%Mod':>7}  {'Bias':>8}  {'Brier':>8}")
    lines.append("  " + "-" * 72)
    for tier in POWER_TIER_ORDER:
        grp = [r for r in rows if power_mult_tier(r["power_mult"]) == tier]
        if not grp:
            continue
        a = mean([r["actual"] for r in grp])
        m = mean([r["model_prob"] for r in grp])
        b = brier([r["model_prob"] for r in grp], [r["actual"] for r in grp])
        lines.append(f"  {tier:<26} {len(grp):>6,}  {a*100:>6.2f}%  {m*100:>6.2f}%  {(m-a)*100:>+7.2f}pp  {b:>8.5f}")
    lines.append("")

    # ── SECTION 3: CONTEXT STACK AUDIT ───────────────────────────────────────
    hdr("SECTION 3 — CONTEXT STACK AUDIT")

    comb_all = [r["combined_implied"] for r in rows]
    lines.append(f"  combined_implied stats (back-calculated from model_prob):")
    lines.append(f"    Mean     : {mean(comb_all):.4f}")
    sorted_c = sorted(comb_all)
    n = len(sorted_c)
    lines.append(f"    p25/p50/p75/p90 : {sorted_c[n//4]:.4f} / {sorted_c[n//2]:.4f} / {sorted_c[3*n//4]:.4f} / {sorted_c[int(n*0.90)]:.4f}")
    lines.append(f"    p95/p99         : {sorted_c[int(n*0.95)]:.4f} / {sorted_c[int(n*0.99)]:.4f}")
    lines.append("")

    # High-prob players specifically
    hi_rows = [r for r in rows if r["model_prob"] >= 0.15]
    lo_rows = [r for r in rows if r["model_prob"] < 0.15]
    lines.append(f"  model_prob ≥ 15%:  N={len(hi_rows):,}  mean_combined={mean([r['combined_implied'] for r in hi_rows]):.4f}  "
                 f"actual_HR%={mean([r['actual'] for r in hi_rows])*100:.2f}%  model_HR%={mean([r['model_prob'] for r in hi_rows])*100:.2f}%  "
                 f"bias={(mean([r['model_prob'] for r in hi_rows])-mean([r['actual'] for r in hi_rows]))*100:+.2f}pp")
    lines.append(f"  model_prob <  15%: N={len(lo_rows):,}  mean_combined={mean([r['combined_implied'] for r in lo_rows]):.4f}  "
                 f"actual_HR%={mean([r['actual'] for r in lo_rows])*100:.2f}%  model_HR%={mean([r['model_prob'] for r in lo_rows])*100:.2f}%  "
                 f"bias={(mean([r['model_prob'] for r in lo_rows])-mean([r['actual'] for r in lo_rows]))*100:+.2f}pp")
    lines.append("")

    # Cross-tab: power_mult tier × context tier
    lines.append("  Cross-tab: power_mult tier × context_tier (combined_implied)")
    lines.append("  Format: Bias (Actual% → Model%)")
    lines.append("")
    # Header
    col_w = 18
    lines.append("  " + "Power\\Context".ljust(28) + "".join(ct.ljust(col_w) for ct in CONTEXT_TIER_ORDER))
    lines.append("  " + "-" * (28 + col_w * len(CONTEXT_TIER_ORDER)))

    for ptier in POWER_TIER_ORDER:
        row_parts = [ptier.ljust(28)]
        for ctier in CONTEXT_TIER_ORDER:
            grp = [r for r in rows
                   if power_mult_tier(r["power_mult"]) == ptier
                   and context_tier(r["combined_implied"]) == ctier]
            if len(grp) < 5:
                row_parts.append("n/a".ljust(col_w))
            else:
                a = mean([r["actual"] for r in grp])
                m = mean([r["model_prob"] for r in grp])
                cell = f"{(m-a)*100:+.1f}pp (n={len(grp)})"
                row_parts.append(cell.ljust(col_w))
        lines.append("  " + "".join(row_parts))
    lines.append("")

    # Distribution of ≥15% picks by power_mult tier
    lines.append("  Where are the ≥15% picks concentrated?")
    lines.append(f"  {'Power tier':<28} {'All':>6}  {'≥15%':>6}  {'%share':>7}  {'Mean_comb':>10}  {'Actual%':>7}  {'Bias':>8}")
    lines.append("  " + "-" * 75)
    for ptier in POWER_TIER_ORDER:
        all_t  = [r for r in rows if power_mult_tier(r["power_mult"]) == ptier]
        hi_t   = [r for r in all_t if r["model_prob"] >= 0.15]
        if not all_t:
            continue
        pct = len(hi_t) / len(all_t) * 100
        mc  = mean([r["combined_implied"] for r in hi_t]) if hi_t else 0
        ac  = mean([r["actual"] for r in hi_t]) if hi_t else 0
        mp  = mean([r["model_prob"] for r in hi_t]) if hi_t else 0
        bias = (mp - ac) * 100 if hi_t else 0
        lines.append(f"  {ptier:<28} {len(all_t):>6,}  {len(hi_t):>6,}  {pct:>6.1f}%  {mc:>10.4f}  {ac*100:>6.2f}%  {bias:>+7.2f}pp")
    lines.append("")

    # ── SECTION 4: MODERATION VARIANT ANALYSIS ───────────────────────────────
    hdr("SECTION 4 — MODERATION VARIANT ANALYSIS")
    lines.append("  For each variant, combined_implied is moderated by power_mult then")
    lines.append("  re-clamped to [0.42, 1.50] before recomputing model_prob via Poisson.")
    lines.append("  Cal = post-Platt-calibration (A=0.7805, B=-0.4611).")
    lines.append("  Note: cal params were fitted on baseline — treat cal columns as approximate.")
    lines.append("")

    variant_results = []
    for v in VARIANTS:
        probs_raw, probs_cal = [], []
        actuals = []
        for r in rows:
            mod = moderate_combined(r["combined_implied"], r["power_mult"],
                                    v["method"], v["floor"])
            p_raw = poisson_prob(r["adjusted_rate"], r["exp_pa"], mod)
            p_cal = calibrate(p_raw)
            probs_raw.append(p_raw)
            probs_cal.append(p_cal)
            actuals.append(r["actual"])

        base_probs = [r["model_prob"] for r in rows]
        spear = spearman(base_probs, probs_raw)

        variant_results.append({
            "v":         v,
            "probs_raw": probs_raw,
            "probs_cal": probs_cal,
            "actuals":   actuals,
            "spearman":  spear,
        })

    # Overall metrics table
    lines.append(f"  {'Variant':<18} {'Tag':>4}  {'Brier':>8}  {'Brier+Cal':>10}  {'MAE':>8}  {'Bias':>8}  {'Bias+Cal':>9}  {'Spearman':>9}")
    lines.append("  " + "-" * 90)
    for vr in variant_results:
        v  = vr["v"]
        pr = vr["probs_raw"]
        pc = vr["probs_cal"]
        ac = vr["actuals"]
        br  = brier(pr, ac)
        brc = brier(pc, ac)
        m_ae = mae(pr, ac)
        bi  = (mean(pr) - mean(ac)) * 100
        bic = (mean(pc) - mean(ac)) * 100
        sp  = vr["spearman"]
        lines.append(f"  {v['name']:<18} {v['tag']:>4}  {br:>8.5f}  {brc:>10.5f}  {m_ae:>8.5f}  {bi:>+7.2f}pp  {bic:>+8.2f}pp  {sp:>9.6f}")
    lines.append("")

    # ── SECTION 5: BUCKET-LEVEL BIAS BY VARIANT ──────────────────────────────
    hdr("SECTION 5 — BUCKET-LEVEL BIAS BY VARIANT (pre-calibration)")
    lines.append(f"  {'Bucket':<10} {'Actual%':>7}  " + "  ".join(f"{v['v']['tag']:>7}" for v in variant_results))
    lines.append("  " + "-" * (20 + 11 * len(variant_results)))

    for bucket in PROB_BUCKET_ORDER:
        # Pick one variant's probs to define bucket membership (baseline = V0)
        base_probs = variant_results[0]["probs_raw"]
        bucket_idx = [i for i, p in enumerate(base_probs) if prob_bucket(p) == bucket]
        if len(bucket_idx) < 5:
            continue
        actual_rate = mean([variant_results[0]["actuals"][i] for i in bucket_idx])
        parts = [f"  {bucket:<10} {actual_rate*100:>6.2f}%  "]
        for vr in variant_results:
            m = mean([vr["probs_raw"][i] for i in bucket_idx])
            bias = (m - actual_rate) * 100
            parts.append(f"{bias:>+6.1f}pp  ")
        lines.append("".join(parts))
    lines.append("")

    # ── SECTION 6: ELITE HITTER BIAS BY VARIANT ──────────────────────────────
    hdr("SECTION 6 — BIAS BY ARCHETYPE TIER PER VARIANT (pre-calibration)")

    def archetype_bias_table(tier_fn, tier_order, label):
        lines.append(f"  Segmented by {label}:")
        lines.append(f"  {'Tier':<26} {'Actual%':>7}  {'N':>5}  " + "  ".join(f"{v['v']['tag']:>7}" for v in variant_results))
        lines.append("  " + "-" * (40 + 11 * len(variant_results)))
        for tier in tier_order:
            idx = [i for i, r in enumerate(rows) if tier_fn(r) == tier]
            if len(idx) < 5:
                continue
            actual_rate = mean([rows[i]["actual"] for i in idx])
            parts = [f"  {tier:<26} {actual_rate*100:>6.2f}%  {len(idx):>5}  "]
            for vr in variant_results:
                m = mean([vr["probs_raw"][i] for i in idx])
                bias = (m - actual_rate) * 100
                parts.append(f"{bias:>+6.1f}pp  ")
            lines.append("".join(parts))
        lines.append("")

    archetype_bias_table(lambda r: barrel_tier(r["barrel_rate"]),   BARREL_TIER_ORDER,   "barrel_rate tier")
    archetype_bias_table(lambda r: power_mult_tier(r["power_mult"]), POWER_TIER_ORDER, "power_mult tier")

    # ── SECTION 7: HIGH-CONTEXT CONTACT BATTER ANALYSIS ─────────────────────
    hdr("SECTION 7 — HIGH-CONTEXT CONTACT BATTER INFLATION AUDIT")
    lines.append("  These are the rows driving over-prediction: low power_mult + high context.")
    lines.append("")

    # Low power_mult + high context
    inflation_cases = [r for r in rows if r["power_mult"] < 0.90 and r["combined_implied"] >= 1.30]
    non_inflation   = [r for r in rows if not (r["power_mult"] < 0.90 and r["combined_implied"] >= 1.30)]

    def describe_group(grp, label):
        if not grp:
            lines.append(f"  {label}: empty")
            return
        a = mean([r["actual"] for r in grp])
        m = mean([r["model_prob"] for r in grp])
        c = mean([r["combined_implied"] for r in grp])
        pm = mean([r["power_mult"] for r in grp])
        b = brier([r["model_prob"] for r in grp], [r["actual"] for r in grp])
        lines.append(f"  {label}:")
        lines.append(f"    N={len(grp):,}  actual={a*100:.2f}%  model={m*100:.2f}%  bias={(m-a)*100:+.2f}pp  "
                     f"mean_comb={c:.4f}  mean_pm={pm:.4f}  Brier={b:.5f}")

    describe_group(inflation_cases, "Low power_mult (<0.90) + High context (≥1.30)")
    describe_group(non_inflation, "All other rows")
    lines.append("")

    # How much does moderation reduce their model_prob?
    lines.append("  Effect of each moderation method on inflation cases (Δ model_prob):")
    lines.append(f"  {'Variant':<18} {'Mean Δ prob':>12}  {'Mean new prob':>14}  {'New bias':>10}")
    lines.append("  " + "-" * 60)
    inflation_idx = [i for i, r in enumerate(rows) if r["power_mult"] < 0.90 and r["combined_implied"] >= 1.30]
    for vr in variant_results:
        if not inflation_idx:
            break
        orig = mean([rows[i]["model_prob"] for i in inflation_idx])
        new  = mean([vr["probs_raw"][i] for i in inflation_idx])
        act  = mean([rows[i]["actual"]    for i in inflation_idx])
        delta = new - orig
        bias  = (new - act) * 100
        lines.append(f"  {vr['v']['name']:<18} {delta*100:>+11.2f}pp  {new*100:>13.2f}%  {bias:>+9.2f}pp")
    lines.append("")

    # ── SECTION 8: TOP-PICK ANALYSIS (≥ 15% threshold) ───────────────────────
    hdr("SECTION 8 — TOP-PICK ANALYSIS (model_prob ≥ 15%)")

    # For each variant, which rows get ≥15%?
    lines.append(f"  {'Variant':<18} {'N picks':>8}  {'Actual%':>8}  {'Model%':>8}  {'Bias':>8}  {'Brier':>8}")
    lines.append("  " + "-" * 70)
    for vr in variant_results:
        hi_idx = [i for i, p in enumerate(vr["probs_raw"]) if p >= 0.15]
        if not hi_idx:
            lines.append(f"  {vr['v']['name']:<18} {'0':>8}")
            continue
        ac  = mean([vr["actuals"][i]    for i in hi_idx])
        mp  = mean([vr["probs_raw"][i]  for i in hi_idx])
        b   = brier([vr["probs_raw"][i] for i in hi_idx], [vr["actuals"][i] for i in hi_idx])
        bias = (mp - ac) * 100
        lines.append(f"  {vr['v']['name']:<18} {len(hi_idx):>8,}  {ac*100:>7.2f}%  {mp*100:>7.2f}%  {bias:>+7.2f}pp  {b:>8.5f}")
    lines.append("")

    # ── SECTION 9: ELITE HITTER ISOLATION (barrel > 9%) ─────────────────────
    hdr("SECTION 9 — ELITE HITTER ISOLATION (barrel_rate > 9%)")
    lines.append("  Focus: are elite hitters' probabilities increasing or decreasing?")
    lines.append("")

    elite_idx = [i for i, r in enumerate(rows) if r["barrel_rate"] > 0.09]
    non_elite_idx = [i for i, r in enumerate(rows) if r["barrel_rate"] <= 0.09]

    lines.append(f"  Elite hitters (barrel>9%): N={len(elite_idx):,}")
    lines.append(f"  {'Variant':<18} {'Mean prob':>10}  {'Actual%':>8}  {'Bias':>8}  {'vs Baseline Δ':>14}")
    lines.append("  " + "-" * 65)
    base_elite_prob = mean([variant_results[0]["probs_raw"][i] for i in elite_idx]) if elite_idx else 0
    for vr in variant_results:
        if not elite_idx:
            break
        mp  = mean([vr["probs_raw"][i] for i in elite_idx])
        ac  = mean([vr["actuals"][i]   for i in elite_idx])
        bias = (mp - ac) * 100
        delta = (mp - base_elite_prob) * 100
        lines.append(f"  {vr['v']['name']:<18} {mp*100:>9.2f}%  {ac*100:>7.2f}%  {bias:>+7.2f}pp  {delta:>+13.2f}pp")
    lines.append("")

    lines.append(f"  Non-elite hitters (barrel≤9%): N={len(non_elite_idx):,}")
    lines.append(f"  {'Variant':<18} {'Mean prob':>10}  {'Actual%':>8}  {'Bias':>8}  {'vs Baseline Δ':>14}")
    lines.append("  " + "-" * 65)
    base_ne_prob = mean([variant_results[0]["probs_raw"][i] for i in non_elite_idx]) if non_elite_idx else 0
    for vr in variant_results:
        if not non_elite_idx:
            break
        mp  = mean([vr["probs_raw"][i]  for i in non_elite_idx])
        ac  = mean([vr["actuals"][i]    for i in non_elite_idx])
        bias = (mp - ac) * 100
        delta = (mp - base_ne_prob) * 100
        lines.append(f"  {vr['v']['name']:<18} {mp*100:>9.2f}%  {ac*100:>7.2f}%  {bias:>+7.2f}pp  {delta:>+13.2f}pp")
    lines.append("")

    # ── SECTION 10: CONTEXT CAP THRESHOLD SCAN ───────────────────────────────
    hdr("SECTION 10 — CONTEXT CAP THRESHOLD SCAN (Variant V5_Cap by power_mult)")
    lines.append("  Tests different cap ceilings for sub-avg batters (power_mult < 1.0).")
    lines.append("  Ceiling applied only when combined_implied > cap (no inflation).")
    lines.append("")

    sub_avg_idx = [i for i, r in enumerate(rows) if r["power_mult"] < 1.0]
    lines.append(f"  Sub-avg batter rows: N={len(sub_avg_idx):,}")
    lines.append(f"  {'Cap':<10} {'Brier(all)':>12}  {'Bias(all)':>10}  {'Bias(sub-avg)':>14}  {'Bias(elite)':>12}  {'N≥15%':>7}")
    lines.append("  " + "-" * 75)

    for cap_val in [1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.50]:
        test_probs = []
        for r in rows:
            if r["power_mult"] < 1.0:
                c = min(r["combined_implied"], cap_val) if r["combined_implied"] > cap_val else r["combined_implied"]
            else:
                c = r["combined_implied"]
            test_probs.append(poisson_prob(r["adjusted_rate"], r["exp_pa"], c))
        actuals_all = [r["actual"] for r in rows]
        br   = brier(test_probs, actuals_all)
        bi   = (mean(test_probs) - mean(actuals_all)) * 100
        bi_s = (mean([test_probs[i] for i in sub_avg_idx]) - mean([rows[i]["actual"] for i in sub_avg_idx])) * 100
        bi_e = (mean([test_probs[i] for i in elite_idx]) - mean([rows[i]["actual"] for i in elite_idx])) * 100
        n15  = sum(1 for p in test_probs if p >= 0.15)
        lines.append(f"  {cap_val:<10.2f} {br:>12.5f}  {bi:>+9.2f}pp  {bi_s:>+13.2f}pp  {bi_e:>+11.2f}pp  {n15:>7,}")
    lines.append("")

    # ── SECTION 11: COMBINED RECOMMENDED CONFIG ───────────────────────────────
    hdr("SECTION 11 — RECOMMENDATION & IMPLEMENTATION NOTES")

    # Determine best variant by Brier
    best_vr = min(variant_results, key=lambda vr: brier(vr["probs_raw"], vr["actuals"]))

    lines.append("  Best variant by Brier score:")
    lines.append(f"    {best_vr['v']['name']}  (tag={best_vr['v']['tag']}, method={best_vr['v']['method']}, floor={best_vr['v']['floor']})")
    best_b  = brier(best_vr["probs_raw"], best_vr["actuals"])
    base_b  = brier(variant_results[0]["probs_raw"], variant_results[0]["actuals"])
    lines.append(f"    Brier: {best_b:.5f}  vs Baseline: {base_b:.5f}  Δ={best_b - base_b:+.5f}")
    lines.append("")

    # Elite hitter bias before/after best variant
    if elite_idx:
        be_old = (mean([variant_results[0]["probs_raw"][i] for i in elite_idx]) -
                  mean([rows[i]["actual"] for i in elite_idx])) * 100
        be_new = (mean([best_vr["probs_raw"][i] for i in elite_idx]) -
                  mean([rows[i]["actual"] for i in elite_idx])) * 100
        lines.append(f"  Elite hitter bias: {be_old:+.2f}pp → {be_new:+.2f}pp (Δ={be_new-be_old:+.2f}pp)")

    # Inflation case bias before/after
    if inflation_idx:
        bi_old = (mean([variant_results[0]["probs_raw"][i] for i in inflation_idx]) -
                  mean([rows[i]["actual"] for i in inflation_idx])) * 100
        bi_new = (mean([best_vr["probs_raw"][i] for i in inflation_idx]) -
                  mean([rows[i]["actual"] for i in inflation_idx])) * 100
        lines.append(f"  Inflation case bias: {bi_old:+.2f}pp → {bi_new:+.2f}pp (Δ={bi_new-bi_old:+.2f}pp)")
    lines.append("")

    lines.append("  Implementation notes:")
    lines.append("    1. Add `power_mult: float = 1.0` kwarg to game_hr_probability() in probability.py")
    lines.append("       Apply moderation to combined BEFORE the [0.42,1.50] clamp.")
    lines.append("    2. Add config flags: CONTEXT_MODERATION_ENABLED (bool), CONTEXT_MODERATION_FLOOR (float)")
    lines.append("    3. Pass power_mult from pipeline.py and backtest/runner.py")
    lines.append("    4. Re-run analyze_calibration.py after implementation to re-fit Platt params")
    lines.append("    5. Rollback: set CONTEXT_MODERATION_ENABLED=False")
    lines.append("")

    lines.append("  Critical constraint check:")
    lines.append("    Moderation should reduce over-prediction of contact batters in high context")
    lines.append("    WITHOUT suppressing elite hitters. Check Section 9 to confirm elite bias")
    lines.append("    does not move further negative (i.e., variant must not make elite bias worse).")
    lines.append("")

    sep()

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        print("Run:  py -3.12 analyze_fb_pct.py  (first run to collect data)")
        sys.exit(1)

    report = run_analysis()
    print(report)
    OUT_PATH.write_text(report, encoding="utf-8")
    print(f"\n[Output saved to {OUT_PATH}]")
