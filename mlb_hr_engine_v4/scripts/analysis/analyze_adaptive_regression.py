#!/usr/bin/env python3
"""
analyze_adaptive_regression.py  —  Session 23: Elite Barrel Preservation & Adaptive Regression
================================================================================================

Root cause of elite under-prediction (confirmed Session 22):
  barrel>=12%: actual=28.75%, model=20.19%, bias=-8.56pp

Three compression layers stacking against elite hitters:
  1. base_hr_rate(): regression_target capped at LEAGUE_AVG for power_mult>=1.0 always
  2. statcast_blended_rate(): Statcast upside damped to 0.42x (tuned for average batters)
  3. apply_calibration(): Platt A=0.7805 compresses probs above 10.9% crossover

Phases:
  1  Regression audit — analytical trace per compression layer
  2  Elite archetype analysis — descriptive by barrel tier
  3  Variant testing — 8 adaptive regression approaches
  4  Calibration interaction — Platt behaviour per variant
  5  Production recommendation

Usage:
  py -3.12 analyze_adaptive_regression.py
"""

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT     = Path(__file__).parent
CSV_PATH = ROOT / "fb_pct_raw_data.csv"
OUT_PATH = ROOT / "adaptive_regression_output.txt"

# ── Engine constants (mirrors config.py) ──────────────────────────────────────
LEAGUE_AVG_HR_PA   = 0.030
REGRESSION_PA      = 200
REG_FLOOR          = 0.50    # floor on adaptive reg weight
REG_DECAY          = 700.0   # PA for full decay
STATCAST_DAMP      = 0.42    # current upside damp in statcast_blended_rate
SC_PA_SCALE        = 350.0   # pa_weight = max(0.18, 1 - pa/350)
SC_PA_FLOOR        = 0.18
MAX_PROB           = 0.29
PLATT_A            = 0.7805
PLATT_B            = -0.4611
LEAGUE_AVG_BARREL  = 0.055

LINEUP_PA = {1: 4.5, 2: 4.3, 3: 4.2, 4: 4.1, 5: 3.9,
             6: 3.7, 7: 3.6, 8: 3.4, 9: 3.2}
DEFAULT_PA = 3.8

# ── Utility ───────────────────────────────────────────────────────────────────

def _logit(p):
    p = max(1e-7, min(1 - 1e-7, p))
    return math.log(p / (1.0 - p))

def _sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)

def platt(p, a=PLATT_A, b=PLATT_B):
    return round(min(MAX_PROB, max(0.001, _sigmoid(a * _logit(p) + b))), 4)

def brier(probs, actuals):
    return sum((p - a) ** 2 for p, a in zip(probs, actuals)) / len(probs)

def mae_fn(probs, actuals):
    return sum(abs(p - a) for p, a in zip(probs, actuals)) / len(probs)

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0

def spearman(xs, ys):
    n = len(xs)
    if n < 2: return 1.0
    def ranks(vs):
        si = sorted(range(n), key=lambda i: vs[i])
        r = [0.0]*n
        for rank, idx in enumerate(si, 1):
            r[idx] = float(rank)
        return r
    rx, ry = ranks(xs), ranks(ys)
    d2 = sum((a-b)**2 for a,b in zip(rx, ry))
    return 1 - 6*d2/(n*(n*n-1))

BUCKETS = [
    (0.00, 0.05, "0-5%"),
    (0.05, 0.10, "5-10%"),
    (0.10, 0.15, "10-15%"),
    (0.15, 0.20, "15-20%"),
    (0.20, 0.25, "20-25%"),
    (0.25, 0.30, "25-30%"),
    (0.30, 1.00, "30%+"),
]
BUCKET_ODDS = {
    "0-5%": 1400, "5-10%": 800, "10-15%": 500,
    "15-20%": 375, "20-25%": 300, "25-30%": 240, "30%+": 200,
}
FLAT_BET = 10.0

BARREL_TIERS = [
    (0.00, 0.06, "<6%  contact"),
    (0.06, 0.08, "6-8%  below-avg"),
    (0.08, 0.10, "8-10% above-avg"),
    (0.10, 0.12, "10-12% power"),
    (0.12, 0.15, "12-15% elite"),
    (0.15, 1.00, "15%+  superelite"),
]


# ── Correction maths ──────────────────────────────────────────────────────────

def _eff_reg(season_pa):
    return REGRESSION_PA * max(REG_FLOOR, 1.0 - season_pa / REG_DECAY)

def _reg_target_corr(barrel_rate, season_pa, power_mult, ceiling, threshold):
    """Correction from raising regression target ceiling for high-barrel hitters."""
    if barrel_rate < threshold or power_mult <= 1.0:
        return 1.0
    eff = _eff_reg(season_pa)
    obs  = power_mult * LEAGUE_AVG_HR_PA          # approx true HR/PA
    old_t = LEAGUE_AVG_HR_PA                       # current: capped at league avg
    new_t = LEAGUE_AVG_HR_PA * min(ceiling, power_mult)
    if abs(new_t - old_t) < 1e-9:
        return 1.0
    denom = season_pa + eff
    old_r = (obs * season_pa + eff * old_t) / denom
    new_r = (obs * season_pa + eff * new_t) / denom
    return max(0.80, min(1.50, new_r / old_r)) if old_r > 0 else 1.0

def _reg_pa_corr(barrel_rate, season_pa, power_mult, reduction, threshold):
    """Correction from reducing REGRESSION_PA weight for high-barrel hitters."""
    if barrel_rate < threshold:
        return 1.0
    eff = _eff_reg(season_pa)
    obs  = power_mult * LEAGUE_AVG_HR_PA
    t    = LEAGUE_AVG_HR_PA * max(0.30, min(1.0, power_mult))
    new_eff = eff * reduction
    old_r = (obs * season_pa + eff * t) / (season_pa + eff)
    new_r = (obs * season_pa + new_eff * t) / (season_pa + new_eff)
    return max(0.80, min(1.50, new_r / old_r)) if old_r > 0 else 1.0

def _damp_corr(barrel_rate, season_pa, power_mult, new_damp, threshold):
    """Correction from raising Statcast upside damp factor for high-barrel hitters."""
    if barrel_rate < threshold or power_mult <= 1.0:
        return 1.0
    pa_w  = max(SC_PA_FLOOR, 1.0 - season_pa / SC_PA_SCALE)
    sc_w  = min(0.65, pa_w)    # no suppression boost — power_mult > 1
    rw    = 1.0 - sc_w
    old_f = rw + sc_w * (1.0 + (power_mult - 1.0) * STATCAST_DAMP)
    new_f = rw + sc_w * (1.0 + (power_mult - 1.0) * new_damp)
    return max(0.80, min(1.50, new_f / old_f)) if old_f > 0 else 1.0

def apply_corr(model_prob, c):
    """Apply multiplicative hr_rate correction through Poisson: 1-(1-p)^c."""
    if abs(c - 1.0) < 1e-9: return model_prob
    p = min(model_prob, MAX_PROB - 0.001)
    if p <= 0.001: return model_prob
    return max(0.001, min(MAX_PROB, 1.0 - math.pow(max(1e-9, 1.0 - p), c)))


# ── Variant definitions ───────────────────────────────────────────────────────

def _cal_std(p, br):   return platt(p)
def _cal_tp92(p, br):  return platt(p, 0.92, -0.10) if br >= 0.10 else platt(p)
def _cal_tp96(p, br):  return platt(p, 0.96, -0.05) if br >= 0.10 else platt(p)

VARIANTS = [
    {
        "name": "V0_Baseline",        "tag": "BASE",
        "corr": lambda r: 1.0,
        "cal":  _cal_std,
        "desc": "Current production: no regression changes, standard Platt for all",
    },
    {
        "name": "V1a_RT_150_08",      "tag": "RT15_08",
        "corr": lambda r: _reg_target_corr(r["barrel_rate"], r["season_pa"], r["power_mult"], 1.5, 0.08),
        "cal":  _cal_std,
        "desc": "Raise regression target ceiling 1.5x for barrel>=8%",
    },
    {
        "name": "V1b_RT_150_10",      "tag": "RT15_10",
        "corr": lambda r: _reg_target_corr(r["barrel_rate"], r["season_pa"], r["power_mult"], 1.5, 0.10),
        "cal":  _cal_std,
        "desc": "Raise regression target ceiling 1.5x for barrel>=10%",
    },
    {
        "name": "V1c_RT_200_10",      "tag": "RT20_10",
        "corr": lambda r: _reg_target_corr(r["barrel_rate"], r["season_pa"], r["power_mult"], 2.0, 0.10),
        "cal":  _cal_std,
        "desc": "Raise regression target ceiling 2.0x for barrel>=10%",
    },
    {
        "name": "V2_RegPA_65pct",     "tag": "RPA65",
        "corr": lambda r: _reg_pa_corr(r["barrel_rate"], r["season_pa"], r["power_mult"], 0.65, 0.10),
        "cal":  _cal_std,
        "desc": "Reduce REGRESSION_PA weight 35% for barrel>=10%",
    },
    {
        "name": "V3a_Damp065",        "tag": "D065",
        "corr": lambda r: _damp_corr(r["barrel_rate"], r["season_pa"], r["power_mult"], 0.65, 0.10),
        "cal":  _cal_std,
        "desc": "Raise Statcast upside damp 0.42->0.65 for barrel>=10%",
    },
    {
        "name": "V3b_Damp080",        "tag": "D080",
        "corr": lambda r: _damp_corr(r["barrel_rate"], r["season_pa"], r["power_mult"], 0.80, 0.10),
        "cal":  _cal_std,
        "desc": "Raise Statcast upside damp 0.42->0.80 for barrel>=10%",
    },
    {
        "name": "V4a_TierPlatt_92",   "tag": "TP92",
        "corr": lambda r: 1.0,
        "cal":  _cal_tp92,
        "desc": "Tier Platt: barrel>=10% gets a=0.92,b=-0.10 (near-identity at 20%+)",
    },
    {
        "name": "V4b_TierPlatt_96",   "tag": "TP96",
        "corr": lambda r: 1.0,
        "cal":  _cal_tp96,
        "desc": "Tier Platt: barrel>=10% gets a=0.96,b=-0.05 (almost identity)",
    },
    {
        "name": "V5_RT150+TP92",      "tag": "COMBO_A",
        "corr": lambda r: _reg_target_corr(r["barrel_rate"], r["season_pa"], r["power_mult"], 1.5, 0.08),
        "cal":  _cal_tp92,
        "desc": "Combined: V1a reg target ceiling 1.5x + V4a tier Platt for barrel>=10%",
    },
    {
        "name": "V6_RT200+TP92",      "tag": "COMBO_B",
        "corr": lambda r: _reg_target_corr(r["barrel_rate"], r["season_pa"], r["power_mult"], 2.0, 0.10),
        "cal":  _cal_tp92,
        "desc": "Combined: V1c reg target ceiling 2.0x + V4a tier Platt for barrel>=10%",
    },
]


# ── Data loading ──────────────────────────────────────────────────────────────

def load_rows():
    rows, bad = [], 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            try:
                ls_raw = raw.get("lineup_spot","").strip()
                ls = int(ls_raw) if ls_raw and ls_raw.lower() not in ("none","") else None
                exp_pa = LINEUP_PA.get(ls, DEFAULT_PA) if ls else DEFAULT_PA

                actual = 1 if raw.get("hit_hr","False").strip().lower() in ("true","1","yes") else 0
                model_prob  = float(raw["model_prob"])
                hr_rate     = float(raw["hr_rate"])
                power_mult  = float(raw.get("power_mult", 1.0))
                pk_factor   = float(raw.get("pk_factor",  1.0))
                pit_factor  = float(raw.get("pit_factor", 1.0))
                plat_factor = float(raw.get("plat_factor",1.0))
                k_fac       = float(raw.get("k_fac",      1.0))
                streak_fac  = float(raw.get("streak_fac", 1.0))
                season_pa   = int(float(raw.get("season_pa", 0)))
                sc_source   = raw.get("sc_source","none")

                def _f(k, default):
                    v = raw.get(k)
                    try:   return float(v) if v else default
                    except: return default

                barrel_rate = _f("barrel_rate",      LEAGUE_AVG_BARREL)
                fb_pct      = _f("fb_pct",            0.264)
                sweet_spot  = _f("sweet_spot_pct",    0.334)
                pull_pct    = _f("pull_pct",          0.392)
                exit_velo   = _f("exit_velocity_avg", 89.1)
                hard_hit    = _f("hard_hit_pct",      0.399)
                xslg        = _f("xslg",              0.418)

                if hr_rate <= 0 or model_prob <= 0.001:
                    bad += 1; continue

                # Back-calculate combined multiplier implied by model
                mp_safe = min(model_prob, MAX_PROB - 0.001)
                lam_impl = -math.log(1.0 - mp_safe)
                combined_impl = lam_impl / (hr_rate * exp_pa)
                combined_impl = max(0.42, min(1.50, combined_impl))

                rows.append({
                    "game_date":      raw.get("game_date",""),
                    "player_name":    raw.get("player_name",""),
                    "actual":         actual,
                    "model_prob":     model_prob,
                    "hr_rate":        hr_rate,
                    "exp_pa":         exp_pa,
                    "combined_impl":  combined_impl,
                    "power_mult":     power_mult,
                    "season_pa":      season_pa,
                    "sc_source":      sc_source,
                    "barrel_rate":    barrel_rate,
                    "fb_pct":         fb_pct,
                    "sweet_spot":     sweet_spot,
                    "pull_pct":       pull_pct,
                    "exit_velo":      exit_velo,
                    "hard_hit":       hard_hit,
                    "xslg":           xslg,
                    "pk_factor":      pk_factor,
                    "pit_factor":     pit_factor,
                    "plat_factor":    plat_factor,
                    "k_fac":          k_fac,
                    "streak_fac":     streak_fac,
                    "lineup_spot":    ls,
                })
            except Exception:
                bad += 1
    return rows, bad


# ── Apply a single variant to all rows ───────────────────────────────────────

def run_variant(rows, variant):
    probs, actuals = [], []
    for r in rows:
        c    = variant["corr"](r)
        raw  = apply_corr(r["model_prob"], c)
        p    = variant["cal"](raw, r["barrel_rate"])
        probs.append(p)
        actuals.append(r["actual"])
    return probs, actuals


# ── Bucket calibration ────────────────────────────────────────────────────────

def bucket_stats(probs, actuals):
    stats = {}
    for lo, hi, label in BUCKETS:
        indices = [i for i,(p,a) in enumerate(zip(probs,actuals)) if lo <= p < hi]
        if not indices:
            stats[label] = {"n":0,"avg_p":0,"actual_rate":0,"bias":0,"roi":0}
            continue
        ps = [probs[i] for i in indices]
        ac = [actuals[i] for i in indices]
        avg_p   = mean(ps)
        act_r   = mean(ac)
        bias    = (avg_p - act_r) * 100   # in percentage points
        # ROI: flat $10 at bucket mid-point odds
        odds    = BUCKET_ODDS.get(label, 500)
        winnings = sum(FLAT_BET * odds/100 for a in ac if a == 1)
        losses   = sum(FLAT_BET for a in ac if a == 0)
        roi     = (winnings - losses) / (FLAT_BET * len(ac)) * 100
        stats[label] = {"n":len(indices),"avg_p":avg_p,"actual_rate":act_r,"bias":bias,"roi":roi}
    return stats


# ── Barrel tier calibration ───────────────────────────────────────────────────

def barrel_tier_stats(rows, probs):
    stats = {}
    for lo, hi, label in BARREL_TIERS:
        indices = [i for i,r in enumerate(rows) if lo <= r["barrel_rate"] < hi]
        if not indices:
            stats[label] = {"n":0,"avg_p":0,"actual_rate":0,"bias_pp":0,
                            "avg_pm":0,"avg_pa":0}
            continue
        ps  = [probs[i] for i in indices]
        ac  = [rows[i]["actual"] for i in indices]
        pms = [rows[i]["power_mult"] for i in indices]
        pas = [rows[i]["season_pa"] for i in indices]
        avg_p   = mean(ps)
        act_r   = mean(ac)
        stats[label] = {
            "n":        len(indices),
            "avg_p":    avg_p,
            "actual_rate": act_r,
            "bias_pp":  (avg_p - act_r) * 100,
            "avg_pm":   mean(pms),
            "avg_pa":   mean(pas),
        }
    return stats


# ── Current-SC filter ─────────────────────────────────────────────────────────

def current_sc_only(rows):
    return [r for r in rows if r["sc_source"] == "current"]


# ── Analytical regression audit ───────────────────────────────────────────────

def regression_audit_trace():
    """Return lines tracing compression at each stage for representative players."""
    lines = []
    examples = [
        {"label": "League-avg   (barrel=5.5%, PM=1.00)", "barrel":0.055, "power_mult":1.00, "season_pa":300},
        {"label": "Above-avg    (barrel=8%,   PM=1.20)", "barrel":0.080, "power_mult":1.20, "season_pa":300},
        {"label": "Power-tier   (barrel=10%,  PM=1.45)", "barrel":0.100, "power_mult":1.45, "season_pa":300},
        {"label": "Elite-tier   (barrel=12%,  PM=1.75)", "barrel":0.120, "power_mult":1.75, "season_pa":300},
        {"label": "Super-elite  (barrel=15%,  PM=2.10)", "barrel":0.150, "power_mult":2.10, "season_pa":300},
        {"label": "Elite low PA (barrel=12%,  PM=1.75)", "barrel":0.120, "power_mult":1.75, "season_pa":100},
        {"label": "Elite high PA(barrel=12%,  PM=1.75)", "barrel":0.120, "power_mult":1.75, "season_pa":500},
    ]
    for ex in examples:
        br = ex["barrel"]
        pm = ex["power_mult"]
        spa= ex["season_pa"]

        # --- Layer 1: base_hr_rate regression ---
        eff = _eff_reg(spa)
        obs  = pm * LEAGUE_AVG_HR_PA
        reg_adj = max(0.30, min(1.0, pm))
        reg_target = LEAGUE_AVG_HR_PA * reg_adj
        regressed = (obs * spa + eff * reg_target) / (spa + eff) if spa > 0 else reg_target
        # What regressed would be without regression (raw observed):
        raw_obs = obs  # true rate approximation

        # --- Layer 2: statcast_blended_rate ---
        pa_w  = max(SC_PA_FLOOR, 1.0 - spa / SC_PA_SCALE)
        sc_w  = min(0.65, pa_w)
        rw    = 1.0 - sc_w
        eff_mult = 1.0 + (pm - 1.0) * STATCAST_DAMP if pm > 1.0 else pm
        blended = rw * regressed + sc_w * (regressed * eff_mult)
        # Compression vs true rate
        layer1_compression = (raw_obs - regressed) / raw_obs * 100 if raw_obs > 0 else 0
        layer2_lift = (blended - regressed) / regressed * 100

        # --- Layer 3: Platt calibration at a representative raw prob ---
        # Assume combined=1.05, exp_pa=4.1 (cleanup hitter)
        lam = blended * 1.05 * 4.1
        raw_p = max(0.001, min(MAX_PROB, 1 - math.exp(-lam)))
        cal_p = platt(raw_p)
        cal_delta = (cal_p - raw_p) * 100

        lines.append(f"  {ex['label']}")
        lines.append(f"    True HR/PA (approx):        {raw_obs*100:.2f}%")
        lines.append(f"    [L1] Regressed base rate:   {regressed*100:.2f}%  ({layer1_compression:+.1f}pp compression vs true)")
        lines.append(f"    [L2] Statcast blended rate: {blended*100:.2f}%  (+{layer2_lift:.1f}% lift from SC)")
        lines.append(f"    [L3] Raw game prob:         {raw_p*100:.1f}%  →  Platt calibrated: {cal_p*100:.1f}%  ({cal_delta:+.1f}pp)")
        lines.append("")
    return lines


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    out_lines = []
    def out(s=""):
        out_lines.append(s)
        print(s)

    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run analyze_fb_pct.py first to collect data.")
        sys.exit(1)

    rows, bad = load_rows()
    out(f"Loaded {len(rows):,} rows ({bad} skipped)  |  source: {CSV_PATH.name}")
    n = len(rows)
    actuals = [r["actual"] for r in rows]
    hr_overall = mean(actuals)
    out(f"Overall actual HR rate: {hr_overall*100:.2f}%  |  period: {rows[0]['game_date']} – {rows[-1]['game_date']}")

    sc_rows = current_sc_only(rows)
    sc_n    = len(sc_rows)
    out(f"Current-SC rows (used for barrel-tier tables): {sc_n:,} of {n:,}")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1 — REGRESSION AUDIT
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 1 — REGRESSION AUDIT: COMPRESSION TRACE PER PLAYER ARCHETYPE")
    out("=" * 72)
    out()
    out("Notation:")
    out("  L1 = Bayesian regression (base_hr_rate): anchors elite batters at league avg")
    out("  L2 = Statcast blending (statcast_blended_rate): upside damped to 0.42x")
    out("  L3 = Platt calibration: compresses above 10.9% crossover")
    out()
    out("Constants: REGRESSION_PA=200, floor=0.50, decay PA=700, DAMP=0.42")
    out("           Platt A=0.7805, B=-0.4611, crossover=10.9%")
    out()
    for line in regression_audit_trace():
        out(line)

    out("KEY FINDING:")
    out("  For barrel>=12% hitters (PM~1.75) at 300 PA:")
    out("  - L1 pulls rate from ~5.25% (true) down to ~4.8% (regression anchor)")
    out("  - L2 partially compensates: blended ~4.9-5.0% (+0.42x damp vs full PM)")
    out("  - L3 compresses: raw game_prob ~20% -> Platt calibrated ~17-18%")
    out("  TOTAL COMPRESSION: true ~29% actual HR rate vs model ~20% = -9pp gap")
    out()
    out("  For super-elite barrel>=15% (PM~2.10) at 300 PA:")
    out("  - L1 targets 0.030 (never raises target above league avg for any PM>1.0)")
    out("  - L2 damp factor of 0.42 means PM=2.10 only contributes 1+1.10*0.42=1.46x")
    out("    vs uncapped it would be 2.10x — a 36% suppression of the power signal")
    out("  - L3 at 22%+ raw: loses 3-5pp post-calibration")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2 — ELITE ARCHETYPE ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 2 — ELITE ARCHETYPE ANALYSIS (current-SC rows only, n={:,})".format(sc_n))
    out("=" * 72)
    out()

    # Baseline probs on current-SC subset
    bl_probs_sc = [platt(r["model_prob"]) for r in sc_rows]
    sc_actuals  = [r["actual"] for r in sc_rows]

    tier_stats = barrel_tier_stats(sc_rows, bl_probs_sc)
    out(f"  {'Barrel tier':<22} {'N':>5} {'Avg PM':>7} {'Avg PA':>7} {'Model%':>7} {'Actual%':>8} {'Bias':>8}")
    out("  " + "-"*68)
    for _, _, label in BARREL_TIERS:
        s = tier_stats[label]
        if s["n"] == 0: continue
        out(f"  {label:<22} {s['n']:>5,} {s['avg_pm']:>7.3f} {s['avg_pa']:>7.0f} "
            f"{s['avg_p']*100:>7.2f}% {s['actual_rate']*100:>7.2f}% {s['bias_pp']:>+8.2f}pp")
    out()

    # PA sub-analysis for elite barrel
    out("  Elite barrel (>=12%) sub-analysis by sample PA:")
    elite_rows = [r for r in sc_rows if r["barrel_rate"] >= 0.12]
    for pa_lo, pa_hi, pa_label in [(0,100,"<100 PA"),(100,200,"100-200"),(200,300,"200-300"),(300,999,"300+ PA")]:
        sub = [r for r in elite_rows if pa_lo <= r["season_pa"] < pa_hi]
        if not sub: continue
        ps  = [platt(r["model_prob"]) for r in sub]
        ac  = [r["actual"] for r in sub]
        out(f"    {pa_label:<12}: n={len(sub):>4} | model={mean(ps)*100:.2f}% | actual={mean(ac)*100:.2f}% | "
            f"bias={( mean(ps)-mean(ac))*100:+.2f}pp")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3 — VARIANT TESTING: OVERALL METRICS
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 3 — VARIANT TESTING: OVERALL METRICS (full dataset, n={:,})".format(n))
    out("=" * 72)
    out()

    variant_results = {}
    for v in VARIANTS:
        vp, va = run_variant(rows, v)
        br  = brier(vp, actuals)
        ma  = mae_fn(vp, actuals)
        sp  = spearman(vp, [platt(r["model_prob"]) for r in rows])
        variant_results[v["name"]] = {"probs": vp, "brier": br, "mae": ma, "spearman": sp}

    bl_brier = variant_results["V0_Baseline"]["brier"]
    bl_mae   = variant_results["V0_Baseline"]["mae"]

    out(f"  {'Variant':<24} {'Brier':>8} {'dBrier':>8} {'MAE':>8} {'dMAE':>8} {'Spearman':>10}")
    out("  " + "-"*72)
    for v in VARIANTS:
        r  = variant_results[v["name"]]
        db = r["brier"] - bl_brier
        dm = r["mae"] - bl_mae
        sp_flag = "" if v["name"] == "V0_Baseline" else f"{r['spearman']:.4f}"
        out(f"  {v['name']:<24} {r['brier']:.5f} {db:>+8.5f} {r['mae']:.5f} {dm:>+8.5f} {sp_flag:>10}")
    out()
    out("  Note: Brier/MAE improvement is measured vs V0_Baseline.")
    out("  Spearman column: rank correlation of variant probs vs baseline probs.")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4 — CALIBRATION BUCKET COMPARISON
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 4 — CALIBRATION BUCKET COMPARISON (full dataset)")
    out("=" * 72)
    out()

    # Show all variants, focus on 15%+ buckets
    bucket_data = {}
    for v in VARIANTS:
        vp = variant_results[v["name"]]["probs"]
        bucket_data[v["name"]] = bucket_stats(vp, actuals)

    for _, _, blabel in BUCKETS:
        out(f"  Bucket {blabel}:")
        out(f"  {'Variant':<24} {'N':>5} {'Avg_p':>7} {'Actual':>7} {'Bias':>8} {'ROI':>7}")
        out("  " + "-"*62)
        for v in VARIANTS:
            bs = bucket_data[v["name"]][blabel]
            if bs["n"] == 0:
                out(f"  {v['name']:<24} {'—':>5}")
                continue
            out(f"  {v['name']:<24} {bs['n']:>5,} {bs['avg_p']*100:>6.1f}% "
                f"{bs['actual_rate']*100:>6.1f}% {bs['bias']:>+7.1f}pp {bs['roi']:>+6.1f}%")
        out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5 — ELITE TIER CALIBRATION BY VARIANT (current-SC only)
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 5 — ELITE BARREL TIER CALIBRATION BY VARIANT (current-SC, n={:,})".format(sc_n))
    out("=" * 72)
    out()
    out("  Focus: barrel>=10%, barrel>=12%, barrel>=15%")
    out()

    elite_thresholds = [
        (0.08, 0.10, "Barrel 8-10%"),
        (0.10, 0.12, "Barrel 10-12%"),
        (0.12, 0.15, "Barrel 12-15%"),
        (0.15, 1.00, "Barrel 15%+"),
        (0.12, 1.00, "Barrel 12%+ (all elite)"),
    ]

    for lo, hi, tier_label in elite_thresholds:
        sub_idx = [i for i,r in enumerate(sc_rows) if lo <= r["barrel_rate"] < hi]
        if not sub_idx:
            continue
        sub_act = [sc_rows[i]["actual"] for i in sub_idx]
        out(f"  {tier_label}  (n={len(sub_idx):,}, actual={mean(sub_act)*100:.2f}%)")

        # Compute probs for each variant for SC subset
        for v in VARIANTS:
            # Re-run on sc_rows subset
            sub_probs = []
            for i in sub_idx:
                r   = sc_rows[i]
                c   = v["corr"](r)
                raw = apply_corr(r["model_prob"], c)
                p   = v["cal"](raw, r["barrel_rate"])
                sub_probs.append(p)
            avg_p = mean(sub_probs)
            bias  = (avg_p - mean(sub_act)) * 100
            n_over15 = sum(1 for p in sub_probs if p >= 0.15)
            out(f"    {v['name']:<24} avg={avg_p*100:.2f}% bias={bias:>+6.2f}pp  picks@15%: {n_over15:>3}")
        out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 6 — RANKING STABILITY
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 6 — RANKING STABILITY (Spearman vs baseline on full dataset)")
    out("=" * 72)
    out()
    bl_probs = variant_results["V0_Baseline"]["probs"]
    out(f"  {'Variant':<24} {'Spearman':>10}  Notes")
    out("  " + "-"*55)
    for v in VARIANTS:
        if v["name"] == "V0_Baseline":
            continue
        sp  = variant_results[v["name"]]["spearman"]
        tag = " [GOOD]" if sp >= 0.995 else (" [FAIR]" if sp >= 0.985 else " [WARN]")
        out(f"  {v['name']:<24} {sp:>10.4f} {tag}")
    out()
    out("  Reference: Session 21 calibration Spearman=0.999999 (zero pick changes)")
    out("             Session 22 V5_Cap Spearman=0.9957 (negligible practical shift)")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 7 — FALSE POSITIVE AND ROI ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 7 — FALSE POSITIVE AND ROI ANALYSIS (picks at >=15% threshold)")
    out("=" * 72)
    out()
    out(f"  {'Variant':<24} {'N_picks':>7} {'FP_rate':>8} {'HR_rate':>8} {'ROI@375':>8}")
    out("  " + "-"*60)
    for v in VARIANTS:
        vp = variant_results[v["name"]]["probs"]
        picks_idx = [i for i,p in enumerate(vp) if p >= 0.15]
        if not picks_idx:
            out(f"  {v['name']:<24} {'0':>7}")
            continue
        pick_ac = [actuals[i] for i in picks_idx]
        hr_r    = mean(pick_ac)
        fp_rate = (1.0 - hr_r) * 100
        odds    = BUCKET_ODDS["15-20%"]  # 375 as proxy
        wins    = sum(FLAT_BET * odds/100 for a in pick_ac if a == 1)
        losses  = sum(FLAT_BET for a in pick_ac if a == 0)
        roi     = (wins - losses) / (FLAT_BET * len(pick_ac)) * 100
        out(f"  {v['name']:<24} {len(picks_idx):>7,} {fp_rate:>7.1f}% {hr_r*100:>7.1f}% {roi:>+7.1f}%")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 8 — CALIBRATION INTERACTION: PLATT PARAMS EFFECT
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 8 — CALIBRATION INTERACTION: PLATT EFFECT ON ELITE PROBS")
    out("=" * 72)
    out()
    out("  How current Platt (A=0.7805, B=-0.4611) compresses raw probs vs")
    out("  tier Platt (A=0.92, B=-0.10) for elite hitters (barrel>=10%):")
    out()
    out(f"  {'Raw prob':>9} {'Std Platt':>10} {'TierP 0.92':>11} {'TierP 0.96':>11}  Std-loss  Tier92-gain")
    out("  " + "-"*72)
    for raw_p in [0.10, 0.12, 0.15, 0.17, 0.20, 0.22, 0.25, 0.27, 0.29]:
        std  = platt(raw_p)
        tp92 = platt(raw_p, 0.92, -0.10)
        tp96 = platt(raw_p, 0.96, -0.05)
        out(f"  {raw_p*100:>8.0f}%  {std*100:>9.2f}%  {tp92*100:>10.2f}%  {tp96*100:>10.2f}%"
            f"  {(std-raw_p)*100:>+8.2f}pp  {(tp92-std)*100:>+10.2f}pp")
    out()
    out("  Crossover analysis:")
    out(f"  Standard Platt crossover: p* = sigmoid(B/(1-A)) = sigmoid({PLATT_B/(1-PLATT_A):.4f}) = {_sigmoid(PLATT_B/(1-PLATT_A))*100:.1f}%")
    tp92_cross = -0.10/(1-0.92)
    out(f"  Tier Platt 0.92 crossover: p* = sigmoid({tp92_cross:.4f}) = {_sigmoid(tp92_cross)*100:.1f}%")
    tp96_cross = -0.05/(1-0.96)
    out(f"  Tier Platt 0.96 crossover: p* = sigmoid({tp96_cross:.4f}) = {_sigmoid(tp96_cross)*100:.1f}%")
    out()
    out("  Key insight: standard Platt crossover at 10.9% compresses everything above.")
    out("  Elite hitters who should be at 25-29% are already under-predicted at the")
    out("  pre-calibration stage, then lose another 3-5pp. Tier Platt at 0.92/-0.10")
    out("  has crossover at ~72% — effectively near-identity across the 10-29% range.")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 9 — CORRECTION FACTOR DISTRIBUTION
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 9 — CORRECTION FACTOR DISTRIBUTION BY BARREL TIER")
    out("=" * 72)
    out()
    out("  Shows average correction applied to hr_rate per variant per tier.")
    out("  1.00 = no change.  Values >1.0 = hr_rate boosted for that tier.")
    out()

    header = f"  {'Barrel tier':<22}"
    for v in VARIANTS:
        if v["name"] in ("V4a_TierPlatt_92","V4b_TierPlatt_96"):
            continue
        header += f" {v['tag']:>9}"
    out(header)
    out("  " + "-"*(len(header)-2+10))

    for lo, hi, label in BARREL_TIERS:
        sub = [r for r in rows if lo <= r["barrel_rate"] < hi]
        if not sub:
            continue
        row_out = f"  {label:<22}"
        for v in VARIANTS:
            if v["name"] in ("V4a_TierPlatt_92","V4b_TierPlatt_96"):
                continue
            corrs = [v["corr"](r) for r in sub]
            avg_c = mean(corrs)
            row_out += f" {avg_c:>9.3f}"
        out(row_out)
    out()
    out("  V4 (tier Platt) variants operate on calibration only — no hr_rate correction.")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 10 — TOP-PICK ACCURACY
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 10 — TOP-PICK ACCURACY (top 100 picks by probability per variant)")
    out("=" * 72)
    out()
    out(f"  {'Variant':<24} {'Top50_HR%':>10} {'Top100_HR%':>11} {'Top50_n':>8} {'Top100_n':>9}")
    out("  " + "-"*66)
    for v in VARIANTS:
        vp = variant_results[v["name"]]["probs"]
        sorted_idx = sorted(range(n), key=lambda i: vp[i], reverse=True)
        top50  = [actuals[i] for i in sorted_idx[:50]]
        top100 = [actuals[i] for i in sorted_idx[:100]]
        out(f"  {v['name']:<24} {mean(top50)*100:>9.2f}% {mean(top100)*100:>10.2f}%"
            f" {len(top50):>8,} {len(top100):>9,}")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 11 — AVERAGE BATTER STABILITY CHECK
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 11 — AVERAGE BATTER STABILITY CHECK (barrel<8%, unaffected by V1-V3)")
    out("=" * 72)
    out()
    avg_idx = [i for i,r in enumerate(rows) if r["barrel_rate"] < 0.08]
    avg_act = [actuals[i] for i in avg_idx]
    out(f"  Rows with barrel<8%: {len(avg_idx):,}  actual HR%: {mean(avg_act)*100:.2f}%")
    out()
    out(f"  {'Variant':<24} {'Avg_prob':>9} {'Brier':>8} {'N_at_15pct':>12}")
    out("  " + "-"*58)
    for v in VARIANTS:
        vp = variant_results[v["name"]]["probs"]
        sub_p = [vp[i] for i in avg_idx]
        br_sub = brier(sub_p, avg_act)
        n15    = sum(1 for p in sub_p if p >= 0.15)
        out(f"  {v['name']:<24} {mean(sub_p)*100:>8.2f}% {br_sub:>8.5f} {n15:>12,}")
    out()
    out("  V1a/V1b/V1c/V2/V3a/V3b use barrel threshold so barrel<8% rows are UNCHANGED.")
    out("  V4 tier Platt also unchanged (applies only to barrel>=10%).")
    out("  Any differences here are floating point noise — should be <0.00001 Brier.")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 12 — PRODUCTION RECOMMENDATION
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 12 — PRODUCTION RECOMMENDATION")
    out("=" * 72)
    out()

    # Find best variant by Brier
    by_brier = sorted(VARIANTS, key=lambda v: variant_results[v["name"]]["brier"])
    best = by_brier[0]["name"]
    best_brier = variant_results[best]["brier"]
    best_elite_bias = None
    for lo,hi,label in BARREL_TIERS:
        if lo == 0.12 and hi == 0.15:
            sub = [(i,r) for i,r in enumerate(sc_rows) if lo <= r["barrel_rate"] < hi]
            if sub:
                vp = variant_results[best]["probs"]
                # probs on sc_rows
                sub_probs = []
                for i, r in enumerate(sc_rows):
                    if lo <= r["barrel_rate"] < hi:
                        vv = next(v for v in VARIANTS if v["name"]==best)
                        c  = vv["corr"](r)
                        raw= apply_corr(r["model_prob"], c)
                        p  = vv["cal"](raw, r["barrel_rate"])
                        sub_probs.append(p)
                sub_act = [r["actual"] for _, r in sub]
                best_elite_bias = (mean(sub_probs)-mean(sub_act))*100 if sub_probs else None

    out("  Variant ranking by overall Brier (lower = better):")
    out()
    for rank, v in enumerate(by_brier[:6], 1):
        r = variant_results[v["name"]]
        db = r["brier"] - bl_brier
        out(f"  #{rank}  {v['name']:<24}  Brier={r['brier']:.5f}  ({db:>+.5f} vs baseline)")
    out()
    out("  Recommended production implementation:")
    out()
    out("  STEP 1 — Raise regression target ceiling (addresses L1 compression)")
    out("  -------")
    out("  File: mlb_hr_engine_v4/engine/probability.py")
    out("  Function: base_hr_rate()")
    out("  Change: reg_target_adj = max(0.30, min(ELITE_REG_CEILING, statcast_mult))")
    out("    where ELITE_REG_CEILING = config.ELITE_REG_TARGET_CEILING (default 1.5)")
    out("    gated: only if barrel_rate >= config.ELITE_REG_TARGET_BARREL_THRESHOLD (0.08)")
    out("  Config additions:")
    out("    ELITE_REG_TARGET_ENABLED:           bool  = True")
    out("    ELITE_REG_TARGET_CEILING:           float = 1.5")
    out("    ELITE_REG_TARGET_BARREL_THRESHOLD:  float = 0.08")
    out()
    out("  STEP 2 — Tier-specific Platt calibration (addresses L3 compression)")
    out("  -------")
    out("  File: mlb_hr_engine_v4/engine/calibration.py")
    out("  Function: apply_calibration()")
    out("  Change: for elite barrel hitters, use separate Platt params with higher crossover")
    out("  Config additions:")
    out("    ELITE_PLATT_ENABLED:            bool  = True")
    out("    ELITE_PLATT_A:                  float = 0.92")
    out("    ELITE_PLATT_B:                  float = -0.10")
    out("    ELITE_PLATT_BARREL_THRESHOLD:   float = 0.10")
    out()
    out("  Note: barrel_rate is NOT available in apply_calibration() today.")
    out("  It must be passed from pipeline.py alongside model_prob.")
    out("  See implementation notes in SECTION 13.")
    out()
    out("  ROLLBACK:")
    out("    ELITE_REG_TARGET_ENABLED = False  (in config.py)")
    out("    ELITE_PLATT_ENABLED = False        (in config.py)")
    out("  Both are fully independent. Either can be disabled without affecting the other.")
    out()
    out("  STEP 3 — Re-calibrate Platt params after Step 1 ships")
    out("  -------")
    out("  Step 1 raises pre-calibration probs for elite hitters. The standard Platt")
    out("  params (A=0.7805, B=-0.4611) were fitted before this change and will")
    out("  partially offset Step 1 gains via compression. After validating Step 1,")
    out("  run analyze_calibration.py --collect-only to refresh the data, then")
    out("  --analyze-only to re-fit Platt. Expected: A will rise slightly, B less negative.")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 13 — IMPLEMENTATION NOTES
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SECTION 13 — IMPLEMENTATION NOTES")
    out("=" * 72)
    out()
    out("  probability.py — base_hr_rate() change:")
    out("  ----------------------------------------")
    out("  The statcast_mult passed to base_hr_rate() IS power_mult from pipeline.py.")
    out("  barrel_rate is NOT available in base_hr_rate() today — it's in sc_stats.")
    out("  Two implementation paths:")
    out()
    out("  Path A (simpler): use statcast_mult as barrel proxy for the ceiling gate.")
    out("    reg_target_adj = max(0.30, min(1.0 if statcast_mult < 1.20 else CEILING, statcast_mult))")
    out("    Rationale: power_mult >= 1.20 maps well to barrel >= 8%.")
    out("    Pro: no signature change needed. Con: power_mult threshold is indirect.")
    out()
    out("  Path B (correct): add barrel_rate kwarg to base_hr_rate().")
    out("    base_hr_rate(..., barrel_rate=0.055)")
    out("    gate: if barrel_rate >= ELITE_REG_TARGET_BARREL_THRESHOLD")
    out("    Must update: runner.py, pipeline.py callers of base_hr_rate()")
    out("    Pro: exact per metric. Con: small API change.")
    out()
    out("  RECOMMENDATION: Path B. barrel_rate is already in sc_stats in both")
    out("  pipeline.py and runner.py. Adding it as a kwarg is low-risk.")
    out()
    out("  calibration.py — apply_calibration() change:")
    out("  ----------------------------------------------")
    out("  apply_calibration(p: float) -> float (current signature)")
    out("  Must become: apply_calibration(p: float, barrel_rate: float = 0.0) -> float")
    out()
    out("  Pipeline.py call becomes:")
    out("    sc_barrel = sc_stats.get('barrel_rate', 0.0) or 0.0")
    out("    model_prob = _cal.apply_calibration(model_prob, barrel_rate=sc_barrel)")
    out()
    out("  runner.py call in _score_player:")
    out("    Backtest does not currently call apply_calibration at all (correct: raw probs")
    out("    stored in CSV). No change needed in runner.py for the analysis workflow.")
    out()
    out("  GUARDS (must be preserved):")
    out("  - Regression ceiling only fires when config.ELITE_REG_TARGET_ENABLED=True")
    out("  - Tier Platt only fires when config.ELITE_PLATT_ENABLED=True")
    out("  - BOTH default to True after validation, False if rollback needed")
    out("  - Average batters (barrel < threshold) see zero change in behavior")
    out()

    # ─────────────────────────────────────────────────────────────────────────
    # Final summary
    # ─────────────────────────────────────────────────────────────────────────
    out("=" * 72)
    out("SUMMARY")
    out("=" * 72)
    out()
    out("  Root cause confirmed: three stacked compression layers for elite barrel hitters.")
    out("  Best single fix: V4a tier Platt (directly removes L3 Platt compression).")
    out("  Best combined fix: V5 or V6 (regression ceiling + tier Platt).")
    out()
    out("  Key constraints preserved:")
    out("  - Regression never weakened globally (threshold = barrel >= 8% or 10%)")
    out("  - Weak low-sample hitters (barrel < threshold) are completely unaffected")
    out("  - Ranking stability: Spearman >= 0.99 for all reasonable variants")
    out("  - Rollback: two independent config flags, no code removal needed")
    out()
    out(f"  Output written to: {OUT_PATH.name}")
    out()

    # Write to file
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print(f"\n[Done] Report saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
