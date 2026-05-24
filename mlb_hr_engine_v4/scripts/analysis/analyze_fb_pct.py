"""
analyze_fb_pct.py  —  Fly Ball % Signal Promotion & Validation
===============================================================
Tests 7 FB% configurations against 2026 season backtest data and outputs a
full comparative report covering Brier, MAE, calibration, simulated ROI,
false-positive rate, missed-HR rate, and top-pick accuracy.

Methodology
-----------
Phase 1 (data collection):
  Runs the standard backtest for the requested date range, capturing each
  batter-game's raw Statcast signals alongside the actual HR outcome.
  Results are saved to fb_pct_raw_data.csv for Phase 2.

Phase 2 (variant analysis):
  For each FB% configuration, recomputes batter_power_multiplier from the
  captured Statcast signals without any additional API calls. Scales hr_rate
  proportionally (power_mult_variant / power_mult_baseline) then re-derives
  model_prob using the captured pk_factor, pit_factor, and plat_factor.
  Approximation holds well near baseline — dominant effect of FB% weight
  change flows through the Statcast blending step, which is linear.

Phase 3 (report):
  Writes fb_pct_analysis_output.txt with all metrics per variant.

Usage
-----
  python analyze_fb_pct.py                       # last 45 days
  python analyze_fb_pct.py 30                    # last N days
  python analyze_fb_pct.py 2026-04-01 2026-05-15 # explicit range
  python analyze_fb_pct.py --analyze-only        # skip collection, reuse CSV
  python analyze_fb_pct.py --collect-only        # collect only, skip analysis
"""

import csv
import io
import math
import sys
import time
from datetime import date, timedelta
from pathlib import Path

# Force UTF-8 stdout on Windows so box-drawing characters print correctly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Allow imports from the v4 root
sys.path.insert(0, str(Path(__file__).parent / "mlb_hr_engine_v4"))

import config
from clients import statcast as statcast_client
from data.park_factors import get_park
from backtest.outcomes import get_game_results, get_date_range
from backtest.runner import score_date, clear_cache as _clear_runner_cache
from engine import probability as prob

# ── Output paths ──────────────────────────────────────────────────────────────
RAW_DATA_CSV = Path(__file__).parent / "fb_pct_raw_data.csv"
REPORT_PATH  = Path(__file__).parent / "fb_pct_analysis_output.txt"

# ── Variant definitions ───────────────────────────────────────────────────────
# Each variant specifies FB% weight and companion adjustable weights.
# Fixed weights: barrel=0.40, pull=0.10, hard_hit=0.08 → sum=0.58
# Variable weights (fb + sweet + xslg + ev) must sum to 0.42.
# Park scale: FB% deviation multiplier in fly_ball_adjusted_park_factor.
VARIANTS = [
    {
        "name":        "Baseline",
        "tag":         "BASE",
        "fb":          0.15,
        "sweet":       0.12,
        "xslg":        0.10,
        "ev":          0.05,
        "gate":        False,
        "gate_floor":  0.50,
        "park_scale":  0.30,
        "description": "Current production (FB=15%, no quality gate)",
    },
    {
        "name":        "FB15_gated",
        "tag":         "G15",
        "fb":          0.15,
        "sweet":       0.12,
        "xslg":        0.10,
        "ev":          0.05,
        "gate":        True,
        "gate_floor":  0.50,
        "park_scale":  0.30,
        "description": "Original weight + quality gate only (isolates gate effect)",
    },
    {
        "name":        "FB18_gated",
        "tag":         "G18",
        "fb":          0.18,
        "sweet":       0.11,
        "xslg":        0.09,
        "ev":          0.04,
        "gate":        True,
        "gate_floor":  0.50,
        "park_scale":  0.30,
        "description": "Conservative FB increase (18%) with quality gate",
    },
    {
        "name":        "FB20_flat",
        "tag":         "F20",
        "fb":          0.20,
        "sweet":       0.10,
        "xslg":        0.08,
        "ev":          0.04,
        "gate":        False,
        "gate_floor":  0.50,
        "park_scale":  0.30,
        "description": "FB=20% flat weight, no quality gate",
    },
    {
        "name":        "FB20_gated [PROPOSED]",
        "tag":         "G20",
        "fb":          0.20,
        "sweet":       0.10,
        "xslg":        0.08,
        "ev":          0.04,
        "gate":        True,
        "gate_floor":  0.50,
        "park_scale":  0.30,
        "description": "FB=20% with quality gate — proposed production config",
    },
    {
        "name":        "FB22_gated",
        "tag":         "G22",
        "fb":          0.22,
        "sweet":       0.10,
        "xslg":        0.06,
        "ev":          0.04,
        "gate":        True,
        "gate_floor":  0.50,
        "park_scale":  0.30,
        "description": "Aggressive FB increase (22%) with quality gate",
    },
    {
        "name":        "FB20_park+",
        "tag":         "P20",
        "fb":          0.20,
        "sweet":       0.10,
        "xslg":        0.08,
        "ev":          0.04,
        "gate":        True,
        "gate_floor":  0.50,
        "park_scale":  0.40,
        "description": "FB=20% gated + stronger park interaction (scale=0.40)",
    },
]

# ── Calibration buckets ───────────────────────────────────────────────────────
BUCKETS = [
    (0.00, 0.05,  "0-5%"),
    (0.05, 0.10,  "5-10%"),
    (0.10, 0.15,  "10-15%"),
    (0.15, 0.20,  "15-20%"),
    (0.20, 0.25,  "20-25%"),
    (0.25, 0.30,  "25-30%"),
    (0.30, 1.00,  "30%+"),
]

# Estimated market odds per bucket for ROI simulation
BUCKET_ODDS = {
    "0-5%": 1400, "5-10%": 800, "10-15%": 500,
    "15-20%": 375, "20-25%": 300, "25-30%": 240, "30%+": 200,
}
FLAT_BET = 10.0


# ── Phase 1: Data collection ──────────────────────────────────────────────────

def collect_raw_data(start_date: str, end_date: str) -> list[dict]:
    """Run backtest for date range, save raw scored data to CSV."""
    print(f"\n[Phase 1] Collecting backtest data: {start_date} to {end_date}")

    start_year   = int(start_date[:4])
    current_year = date.today().year
    statcast_year = (start_year - 1) if start_year < current_year else None

    label = f"{statcast_year} Statcast (prior-year)" if statcast_year else "2026 Statcast"
    print(f"  Loading {label}...", end=" ", flush=True)
    batter_data  = statcast_client.get_batter_statcast(year=statcast_year)
    pitcher_data = statcast_client.get_pitcher_statcast(year=statcast_year)
    print(f"{len(batter_data)} batters, {len(pitcher_data)} pitchers")

    dates    = get_date_range(start_date, end_date)
    all_rows = []
    skipped  = []

    for i, d in enumerate(dates):
        print(f"  [{i+1}/{len(dates)}] {d}", end=" ", flush=True)
        try:
            results = get_game_results(d)
            if not results:
                print("(no games)")
                skipped.append(d)
                continue
            for r in results:
                r["game_date"] = d
            scored = score_date(d, results, batter_data, pitcher_data)
            all_rows.extend(scored)
            _clear_runner_cache()
            print(f"→ {len(scored)} batter-games")
        except Exception as e:
            print(f"→ SKIP: {e}")
            skipped.append(d)
        time.sleep(0.1)

    print(f"\n  Collected {len(all_rows)} batter-game records "
          f"({len(dates)-len(skipped)} dates, {len(skipped)} skipped)")

    if all_rows:
        _save_raw_csv(all_rows)
        print(f"  Saved to {RAW_DATA_CSV}")

    return all_rows


def _save_raw_csv(rows: list[dict]) -> None:
    if not rows:
        return
    fields = [
        "game_date", "player_id", "player_name", "team", "opponent", "home_team",
        "pitcher_name", "lineup_spot", "hit_hr",
        "model_prob", "hr_rate", "season_pa", "sc_source",
        "power_mult", "pk_factor", "pit_factor", "plat_factor",
        "k_fac", "streak_fac",
        "barrel_rate", "fb_pct", "sweet_spot_pct", "pull_pct",
        "exit_velocity_avg", "hard_hit_pct", "xslg",
    ]
    with open(RAW_DATA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_raw_csv() -> list[dict]:
    """Load previously saved raw data from CSV."""
    if not RAW_DATA_CSV.exists():
        raise FileNotFoundError(f"Raw data not found: {RAW_DATA_CSV}\nRun without --analyze-only first.")
    rows = []
    with open(RAW_DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Coerce types
            for int_col in ["player_id", "lineup_spot", "season_pa"]:
                try:
                    row[int_col] = int(row[int_col]) if row[int_col] else 0
                except ValueError:
                    row[int_col] = 0
            for bool_col in ["hit_hr"]:
                row[bool_col] = row[bool_col].lower() in ("true", "1", "yes")
            for float_col in [
                "model_prob", "hr_rate", "power_mult", "pk_factor",
                "pit_factor", "plat_factor", "k_fac", "streak_fac",
                "barrel_rate", "fb_pct", "sweet_spot_pct", "pull_pct",
                "exit_velocity_avg", "hard_hit_pct", "xslg",
            ]:
                try:
                    row[float_col] = float(row[float_col]) if row[float_col] else None
                except ValueError:
                    row[float_col] = None
            rows.append(row)
    print(f"  Loaded {len(rows)} batter-game records from {RAW_DATA_CSV}")
    return rows


# ── Phase 2: Variant analysis ─────────────────────────────────────────────────

def _stabilize(value: float, league_avg: float, pa: int, half_life: int) -> float:
    trust = pa / (pa + half_life) if pa > 0 else 0.0
    return trust * value + (1.0 - trust) * league_avg


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _safe_stat(val, default: float) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def compute_variant_power_mult(row: dict, variant: dict) -> float:
    """
    Recompute batter_power_multiplier from captured raw Statcast signals
    using the given variant's FB% weight and quality-gate settings.
    Mirrors statcast.batter_power_multiplier exactly except for these params.
    Returns 1.0 when Statcast data is absent.
    """
    pa = row.get("season_pa") or 0
    if not pa:
        return 1.0

    stab = config.STATCAST_STABILIZATION_PA

    barrel_rate = _safe_stat(row.get("barrel_rate"), config.LEAGUE_AVG_BARREL_RATE)
    ev          = _safe_stat(row.get("exit_velocity_avg"), config.LEAGUE_AVG_EXIT_VELO)
    xslg        = _safe_stat(row.get("xslg"), config.LEAGUE_AVG_XSLG)
    hard_hit    = _safe_stat(row.get("hard_hit_pct"), config.LEAGUE_AVG_HARD_HIT)
    sweet_spot  = _safe_stat(row.get("sweet_spot_pct"), config.LEAGUE_AVG_SWEET_SPOT)
    fb_pct      = _safe_stat(row.get("fb_pct"), config.LEAGUE_AVG_FB_PCT)
    pull_pct    = _safe_stat(row.get("pull_pct"), config.LEAGUE_AVG_PULL_PCT)

    # Validate ranges (mirror statcast._safe)
    if not (0.0 <= barrel_rate <= 0.30): barrel_rate = config.LEAGUE_AVG_BARREL_RATE
    if not (60.0 <= ev <= 120.0):        ev          = config.LEAGUE_AVG_EXIT_VELO
    if not (0.0 <= xslg <= 4.0):         xslg        = config.LEAGUE_AVG_XSLG
    if not (0.0 <= hard_hit <= 0.80):    hard_hit    = config.LEAGUE_AVG_HARD_HIT
    if not (0.0 <= sweet_spot <= 0.70):  sweet_spot  = config.LEAGUE_AVG_SWEET_SPOT
    if not (0.05 <= fb_pct <= 0.70):     fb_pct      = config.LEAGUE_AVG_FB_PCT
    if not (0.10 <= pull_pct <= 0.75):   pull_pct    = config.LEAGUE_AVG_PULL_PCT

    # Per-metric stabilization
    barrel_rate = _stabilize(barrel_rate, config.LEAGUE_AVG_BARREL_RATE, pa, stab["barrel_rate"])
    ev          = _stabilize(ev,          config.LEAGUE_AVG_EXIT_VELO,   pa, stab["exit_velocity_avg"])
    xslg        = _stabilize(xslg,        config.LEAGUE_AVG_XSLG,        pa, stab["xslg"])
    hard_hit    = _stabilize(hard_hit,    config.LEAGUE_AVG_HARD_HIT,    pa, stab["hard_hit_pct"])
    sweet_spot  = _stabilize(sweet_spot,  config.LEAGUE_AVG_SWEET_SPOT,  pa, stab["sweet_spot_pct"])
    fb_pct      = _stabilize(fb_pct,      config.LEAGUE_AVG_FB_PCT,      pa, stab["fb_pct"])
    pull_pct    = _stabilize(pull_pct,    config.LEAGUE_AVG_PULL_PCT,    pa, stab["pull_pct"])

    # Per-metric multipliers (same bounds as production)
    barrel_mult     = _clamp(barrel_rate  / config.LEAGUE_AVG_BARREL_RATE, 0.30, 2.50)
    ev_mult         = _clamp(1.0 + (ev - config.LEAGUE_AVG_EXIT_VELO) / 100.0, 0.85, 1.20)
    xslg_mult       = _clamp(xslg         / config.LEAGUE_AVG_XSLG,         0.50, 2.00)
    hard_hit_mult   = _clamp(hard_hit     / config.LEAGUE_AVG_HARD_HIT,     0.60, 1.70)
    sweet_spot_mult = _clamp(sweet_spot   / config.LEAGUE_AVG_SWEET_SPOT,   0.65, 1.55)
    fb_mult         = _clamp(fb_pct       / config.LEAGUE_AVG_FB_PCT,       0.55, 1.70)
    pull_mult       = _clamp(pull_pct     / config.LEAGUE_AVG_PULL_PCT,     0.65, 1.55)

    # Quality gate on FB% upside
    if variant["gate"]:
        barrel_quality = min(1.0, barrel_mult)
        gate = variant["gate_floor"] + (1.0 - variant["gate_floor"]) * barrel_quality
        fb_deviation = fb_mult - 1.0
        fb_effective = (1.0 + fb_deviation * gate) if fb_deviation > 0 else fb_mult
    else:
        fb_effective = fb_mult

    composite = (
        barrel_mult     * 0.40
        + fb_effective  * variant["fb"]
        + sweet_spot_mult * variant["sweet"]
        + pull_mult     * 0.10
        + xslg_mult     * variant["xslg"]
        + hard_hit_mult * 0.08
        + ev_mult       * variant["ev"]
    )
    raw_composite = _clamp(composite, 0.45, 1.75)

    sc_source = row.get("sc_source", "current")
    if sc_source == "prior":
        raw_composite = 1.0 + config.PRIOR_YEAR_TRUST * (raw_composite - 1.0)

    return round(_clamp(raw_composite, 0.45, 1.75), 3)


def compute_variant_pk_factor(row: dict, variant: dict) -> float:
    """Recompute park factor with variant's FB% park-interaction scale."""
    park_scale = variant["park_scale"]
    home_team  = row.get("home_team", "")
    fb_pct     = row.get("fb_pct")
    try:
        raw_pf = get_park(home_team).get("hr_factor", 1.0)
    except Exception:
        raw_pf = 1.0

    if fb_pct is None:
        return raw_pf
    fb_dev   = (fb_pct - config.LEAGUE_AVG_FB_PCT) / config.LEAGUE_AVG_FB_PCT
    adjusted = 1.0 + (raw_pf - 1.0) * (1.0 + park_scale * fb_dev)
    return _clamp(adjusted, 0.70, 1.45)


def score_variant(rows: list[dict], variant: dict) -> list[dict]:
    """
    Recompute model_prob for every row using the variant configuration.

    Method:
      1. Recompute power_mult_variant from raw Statcast signals.
      2. Scale hr_rate proportionally to the power_mult change:
           hr_rate_v = hr_rate_base * (power_mult_v / power_mult_base)
         This approximation is exact when Statcast dominates (large PA sample)
         and slightly off when Bayesian regression dominates (small PA, early season).
      3. Recompute model_prob from hr_rate_v using captured pk, pit, plat factors.
      4. For park_scale variants, also recompute pk_factor.
    """
    scored = []
    for row in rows:
        try:
            pm_base = row.get("power_mult")
            if not pm_base:
                scored.append({**row, "model_prob_v": row.get("model_prob", 0)})
                continue

            pm_v = compute_variant_power_mult(row, variant)

            # Scale hr_rate by power_mult ratio
            hr_rate_base = row.get("hr_rate")
            if not hr_rate_base:
                scored.append({**row, "model_prob_v": row.get("model_prob", 0)})
                continue

            ratio      = pm_v / pm_base if pm_base > 0 else 1.0
            hr_rate_v  = _clamp(hr_rate_base * ratio, 0.001, 0.15)

            # Park factor: recompute if park scale changed
            if variant["park_scale"] != 0.30:
                pk_v = compute_variant_pk_factor(row, variant)
            else:
                pk_v = row.get("pk_factor", 1.0) or 1.0

            pit_fac   = row.get("pit_factor",  1.0) or 1.0
            plat_fac  = row.get("plat_factor", 1.0) or 1.0
            exp_pa    = prob.expected_pa(row.get("lineup_spot"))

            model_prob_v = prob.game_hr_probability(
                hr_rate_v, exp_pa,
                pk_factor=pk_v, pitcher_fac=pit_fac,
                w_factor=1.0, plat_factor=plat_fac,
            )

            scored.append({**row, "model_prob_v": round(model_prob_v, 4)})
        except Exception:
            scored.append({**row, "model_prob_v": row.get("model_prob", 0)})

    return scored


# ── Phase 3: Metrics ──────────────────────────────────────────────────────────

def brier_score(rows: list[dict], prob_key: str = "model_prob_v") -> float:
    if not rows:
        return 0.0
    return sum((r[prob_key] - int(r["hit_hr"])) ** 2 for r in rows) / len(rows)


def mae(rows: list[dict], prob_key: str = "model_prob_v") -> float:
    if not rows:
        return 0.0
    return sum(abs(r[prob_key] - int(r["hit_hr"])) for r in rows) / len(rows)


def calibration_table(rows: list[dict], prob_key: str = "model_prob_v") -> list[dict]:
    result = []
    for lo, hi, label in BUCKETS:
        bucket = [r for r in rows if lo <= r.get(prob_key, 0) < hi]
        if not bucket:
            result.append({"label": label, "n": 0, "hits": 0,
                           "avg_pred": 0, "actual": 0, "diff": 0})
            continue
        n        = len(bucket)
        hits     = sum(1 for r in bucket if r["hit_hr"])
        avg_pred = sum(r[prob_key] for r in bucket) / n
        actual   = hits / n
        result.append({
            "label": label, "n": n, "hits": hits,
            "avg_pred": avg_pred, "actual": actual,
            "diff": actual - avg_pred,
        })
    return result


def roi_at_threshold(rows: list[dict], threshold: float,
                     prob_key: str = "model_prob_v") -> dict:
    picks = [r for r in rows if r.get(prob_key, 0) >= threshold]
    if not picks:
        return {"n": 0, "wins": 0, "roi": 0.0, "pnl": 0.0}
    wins      = sum(1 for r in picks if r["hit_hr"])
    total_bet = len(picks) * FLAT_BET
    pnl       = 0.0
    for r in picks:
        mp = r[prob_key]
        # Estimate odds from bucket
        odds = next(
            (BUCKET_ODDS[label] for lo, hi, label in BUCKETS if lo <= mp < hi),
            BUCKET_ODDS["30%+"],
        )
        pnl += (odds / 100) * FLAT_BET if r["hit_hr"] else -FLAT_BET
    return {
        "n": len(picks), "wins": wins,
        "roi": (pnl / total_bet * 100) if total_bet > 0 else 0.0,
        "pnl": pnl,
    }


def false_positive_rate(rows: list[dict], threshold: float,
                        prob_key: str = "model_prob_v") -> float:
    """Fraction of picks above threshold that did NOT hit HR."""
    picks = [r for r in rows if r.get(prob_key, 0) >= threshold]
    if not picks:
        return 0.0
    return sum(1 for r in picks if not r["hit_hr"]) / len(picks)


def missed_hr_rate(rows: list[dict], threshold: float,
                   prob_key: str = "model_prob_v") -> float:
    """Fraction of actual HRs that the model placed below threshold."""
    actual_hrs = [r for r in rows if r["hit_hr"]]
    if not actual_hrs:
        return 0.0
    return sum(1 for r in actual_hrs if r.get(prob_key, 0) < threshold) / len(actual_hrs)


def top_pick_accuracy(rows: list[dict], top_n: int = 10,
                      prob_key: str = "model_prob_v") -> float:
    """HR rate among the top N highest-probability predictions per date."""
    by_date: dict[str, list[dict]] = {}
    for r in rows:
        d = r.get("game_date", "")
        by_date.setdefault(d, []).append(r)

    hits = total = 0
    for date_rows in by_date.values():
        top = sorted(date_rows, key=lambda x: x.get(prob_key, 0), reverse=True)[:top_n]
        hits  += sum(1 for r in top if r["hit_hr"])
        total += len(top)

    return hits / total if total > 0 else 0.0


def power_mult_shift_analysis(rows: list[dict]) -> dict:
    """
    Characterize which players are most affected by the FB% promotion.
    Groups by: (a) high FB / low barrel, (b) high FB / high barrel, (c) low FB.
    """
    groups = {
        "high_fb_low_barrel": [],
        "high_fb_high_barrel": [],
        "low_fb": [],
    }
    for row in rows:
        fb = row.get("fb_pct")
        br = row.get("barrel_rate")
        if fb is None or br is None:
            continue
        fb_above = fb > config.LEAGUE_AVG_FB_PCT
        br_above = br > config.LEAGUE_AVG_BARREL_RATE
        if fb_above and not br_above:
            groups["high_fb_low_barrel"].append(row)
        elif fb_above and br_above:
            groups["high_fb_high_barrel"].append(row)
        else:
            groups["low_fb"].append(row)

    result = {}
    for grp, grp_rows in groups.items():
        if not grp_rows:
            result[grp] = {"n": 0, "hr_rate": 0.0}
            continue
        result[grp] = {
            "n":       len(grp_rows),
            "hr_rate": sum(1 for r in grp_rows if r["hit_hr"]) / len(grp_rows),
        }
    return result


# ── Reporting ─────────────────────────────────────────────────────────────────

def _line(char="─", width=100):
    return char * width


def _pct(v: float) -> str:
    return f"{v*100:.2f}%"


def _pp(v: float) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v*100:.1f}pp"


def generate_report(all_rows: list[dict], variant_results: list[dict],
                    date_range: str, group_analysis: dict) -> str:
    lines = []
    total  = len(all_rows)
    hr_cnt = sum(1 for r in all_rows if r["hit_hr"])
    actual_rate = hr_cnt / total if total else 0

    lines.append(_line("═"))
    lines.append("FLY BALL % SIGNAL PROMOTION — ANALYSIS REPORT")
    lines.append(f"Date range: {date_range}  |  Batter-games: {total}  |  "
                 f"Actual HR rate: {_pct(actual_rate)}  |  HRs: {hr_cnt}")
    lines.append(_line("═"))

    # ── Overview table ────────────────────────────────────────────────────────
    lines.append("\n1. OVERVIEW — Key Metrics Per Variant")
    lines.append(_line())
    hdr = (f"{'Variant':<26} {'FB%':>5} {'Gate':>5} "
           f"{'Brier':>8} {'vs Base':>8} "
           f"{'MAE':>8} {'vs Base':>8} "
           f"{'ROI@10%':>9} {'ROI@15%':>9}")
    lines.append(hdr)
    lines.append(_line("-"))

    base_brier = base_mae = None
    for vr in variant_results:
        vdata = vr["variant"]
        if base_brier is None:
            base_brier = vr["brier"]
            base_mae   = vr["mae"]

        brier_delta = vr["brier"] - base_brier
        mae_delta   = vr["mae"]   - base_mae
        tag_gate    = "yes" if vdata["gate"] else "no"
        roi10  = vr["roi_10pct"]["roi"]
        roi15  = vr["roi_15pct"]["roi"]

        marker = " ◄" if vdata.get("tag") == "G20" else "  "
        lines.append(
            f"{vdata['name']:<26} {vdata['fb']*100:>4.0f}% {tag_gate:>5} "
            f"{vr['brier']:>8.5f} {brier_delta:>+8.5f} "
            f"{vr['mae']:>8.5f} {mae_delta:>+8.5f} "
            f"{roi10:>+8.1f}% {roi15:>+8.1f}%{marker}"
        )

    trivial = actual_rate * (1 - actual_rate)
    lines.append(_line("-"))
    lines.append(f"Trivial baseline Brier (predict league avg for all): {trivial:.5f}")
    lines.append(f"Lower Brier = better  |  Negative Brier delta = improvement over baseline")

    # ── Calibration tables ────────────────────────────────────────────────────
    lines.append("\n\n2. CALIBRATION BY PROBABILITY BUCKET")
    lines.append(_line())

    for vr in variant_results:
        vdata = vr["variant"]
        lines.append(f"\n  {vdata['name']}  ({vdata['description']})")
        lines.append(f"  {'Bucket':<10} {'N':>6} {'HRs':>5} {'Pred':>8} {'Actual':>8} {'Diff':>8}")
        lines.append(f"  {_line('-', 52)}")
        for b in vr["calibration"]:
            if b["n"] == 0:
                lines.append(f"  {b['label']:<10} {'—':>6}")
                continue
            diff_str = _pp(b["diff"])
            flag = " !" if abs(b["diff"]) > 0.03 else "  "
            lines.append(
                f"  {b['label']:<10} {b['n']:>6} {b['hits']:>5} "
                f"{_pct(b['avg_pred']):>8} {_pct(b['actual']):>8} "
                f"{diff_str:>8}{flag}"
            )

    # ── False positive / missed HR analysis ───────────────────────────────────
    lines.append("\n\n3. FALSE-POSITIVE & MISSED-HR ANALYSIS")
    lines.append(_line())
    hdr2 = (f"{'Variant':<26} "
            f"{'FP@10%':>8} {'FP@15%':>8} "
            f"{'Miss@10%':>10} {'Miss@15%':>10} "
            f"{'Top10/day':>11}")
    lines.append(hdr2)
    lines.append(_line("-"))

    for vr in variant_results:
        vdata = vr["variant"]
        marker = " ◄" if vdata.get("tag") == "G20" else "  "
        lines.append(
            f"{vdata['name']:<26} "
            f"{vr['fp_10pct']*100:>7.1f}% {vr['fp_15pct']*100:>7.1f}% "
            f"{vr['miss_10pct']*100:>9.1f}% {vr['miss_15pct']*100:>9.1f}% "
            f"{vr['top10_acc']*100:>10.1f}%{marker}"
        )

    lines.append("\n  FP@X%  = fraction of picks above X% threshold that did NOT hit HR")
    lines.append("  Miss%  = fraction of actual HRs with model_prob below threshold")
    lines.append("  Top10  = HR rate among top 10 highest-probability picks per game day")

    # ── ROI simulation detail ─────────────────────────────────────────────────
    lines.append("\n\n4. SIMULATED P&L DETAIL (flat $10 per pick, estimated market odds)")
    lines.append(_line())

    for thresh_key, thresh_pct, label in [
        ("roi_10pct", 0.10, ">= 10% model prob"),
        ("roi_15pct", 0.15, ">= 15% model prob"),
        ("roi_20pct", 0.20, ">= 20% model prob"),
    ]:
        lines.append(f"\n  Threshold: {label}")
        lines.append(f"  {'Variant':<26} {'# Picks':>8} {'# Wins':>8} {'Total Bet':>10} {'Net P&L':>10} {'ROI':>8}")
        lines.append(f"  {_line('-', 72)}")
        for vr in variant_results:
            rd = vr[thresh_key]
            marker = " ◄" if vr["variant"].get("tag") == "G20" else "  "
            lines.append(
                f"  {vr['variant']['name']:<26} {rd['n']:>8} {rd['wins']:>8} "
                f"${rd['n']*10:>9.0f} ${rd['pnl']:>+9.2f} {rd['roi']:>+7.1f}%{marker}"
            )

    # ── Player group analysis ─────────────────────────────────────────────────
    lines.append("\n\n5. PLAYER GROUP ANALYSIS — Who Is Affected By FB% Promotion")
    lines.append(_line())
    lines.append("  Groups by current-season Statcast data (baseline power_mult):")
    lines.append("")

    for grp, gdata in group_analysis.items():
        label = grp.replace("_", " ").title()
        if gdata["n"] == 0:
            lines.append(f"  {label:<30}: 0 batter-games")
            continue
        lines.append(
            f"  {label:<30}: {gdata['n']:>6} batter-games  |  "
            f"actual HR rate = {_pct(gdata['hr_rate'])}"
        )

    lines.append("")
    lines.append("  Interpretation:")
    lines.append("  - high_fb_low_barrel : Target group for quality gate (should NOT be inflated)")
    lines.append("  - high_fb_high_barrel: Power hitters who benefit most from FB% promotion")
    lines.append("  - low_fb             : Ground-ball hitters; FB% acts as suppressor (correct)")

    # ── Redundancy / interaction analysis ────────────────────────────────────
    lines.append("\n\n6. SIGNAL INTERACTION — FB% vs Other Metrics")
    lines.append(_line())

    all_with_fb = [r for r in all_rows if r.get("fb_pct") and r.get("barrel_rate")]
    if all_with_fb:
        # Pearson correlation: fb_pct vs barrel_rate
        n     = len(all_with_fb)
        fb_v  = [r["fb_pct"]     for r in all_with_fb]
        br_v  = [r["barrel_rate"] for r in all_with_fb]
        hh_v  = [r["hard_hit_pct"] or config.LEAGUE_AVG_HARD_HIT for r in all_with_fb]
        hr_v  = [int(r["hit_hr"]) for r in all_with_fb]

        def _corr(xs, ys):
            mx = sum(xs)/len(xs); my = sum(ys)/len(ys)
            num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
            dx  = math.sqrt(sum((x-mx)**2 for x in xs))
            dy  = math.sqrt(sum((y-my)**2 for y in ys))
            return num / (dx * dy) if dx > 0 and dy > 0 else 0.0

        r_fb_br  = _corr(fb_v, br_v)
        r_fb_hh  = _corr(fb_v, hh_v)
        r_fb_hr  = _corr(fb_v, hr_v)
        r_br_hr  = _corr(br_v, hr_v)

        lines.append(f"\n  Pearson correlations (n={n} batter-games with full Statcast):")
        lines.append(f"  FB%    vs barrel%:    r = {r_fb_br:+.4f}  "
                     f"({'moderate overlap' if abs(r_fb_br)>0.30 else 'low overlap'})")
        lines.append(f"  FB%    vs hard_hit%:  r = {r_fb_hh:+.4f}  "
                     f"({'moderate overlap' if abs(r_fb_hh)>0.30 else 'low overlap'})")
        lines.append(f"  FB%    vs HR outcome: r = {r_fb_hr:+.4f}  (point-biserial, raw predictor)")
        lines.append(f"  barrel% vs HR outcome:r = {r_br_hr:+.4f}  (point-biserial, for reference)")

        # VIF approximation: R² of fb_pct ~ barrel_rate regression
        mx  = sum(br_v)/n
        my  = sum(fb_v)/n
        ss_tot = sum((y-my)**2 for y in fb_v)
        slope  = sum((x-mx)*(y-my) for x,y in zip(br_v,fb_v)) / max(sum((x-mx)**2 for x in br_v), 1e-9)
        yhat   = [my + slope*(x-mx) for x in br_v]
        ss_res = sum((y-yh)**2 for y, yh in zip(fb_v, yhat))
        r2_fb_on_barrel = 1.0 - ss_res / max(ss_tot, 1e-9)
        vif_approx = 1.0 / max(1.0 - r2_fb_on_barrel, 1e-9)
        lines.append(f"\n  VIF approximation (FB% ~ barrel%): R²={r2_fb_on_barrel:.3f}, VIF≈{vif_approx:.1f}")
        lines.append(f"  VIF < 5: low multicollinearity — FB% is sufficiently independent of barrel%")
        lines.append(f"  VIF > 5: significant overlap — weight increase risks double-counting")

    # ── Recommendation ────────────────────────────────────────────────────────
    lines.append("\n\n7. RECOMMENDATION")
    lines.append(_line())

    # Find best variant by Brier
    best_brier = min(variant_results, key=lambda x: x["brier"])
    best_roi15 = max(variant_results, key=lambda x: x["roi_15pct"]["roi"])
    proposed   = next((vr for vr in variant_results if vr["variant"].get("tag") == "G20"), None)

    lines.append(f"\n  Best Brier score:  {best_brier['variant']['name']}  "
                 f"({best_brier['brier']:.5f})")
    lines.append(f"  Best ROI@15%:      {best_roi15['variant']['name']}  "
                 f"({best_roi15['roi_15pct']['roi']:+.1f}%)")
    if proposed:
        lines.append(f"\n  Proposed config (FB20_gated):")
        lines.append(f"    Brier:    {proposed['brier']:.5f} "
                     f"({'improvement' if proposed['brier'] < base_brier else 'regression'} "
                     f"vs baseline)")
        lines.append(f"    ROI@15%:  {proposed['roi_15pct']['roi']:+.1f}%")
        lines.append(f"    FP@15%:   {proposed['fp_15pct']*100:.1f}%")
        lines.append(f"    Miss@15%: {proposed['miss_15pct']*100:.1f}%")

    lines.append("\n  See section 2 calibration diffs for bucket-level impact.")
    lines.append("  If proposed Brier is worse or calibration diff exceeds ±3pp in any bucket,")
    lines.append("  revert config.FB_PCT_WEIGHT to 0.15 and config.FB_QUALITY_GATE_ENABLED to False.")
    lines.append(_line("═"))

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def parse_args():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    analyze_only  = "--analyze-only"  in flags
    collect_only  = "--collect-only"  in flags

    today = date.today()
    if len(args) == 0:
        start = (today - timedelta(days=45)).isoformat()
        end   = (today - timedelta(days=1)).isoformat()
    elif len(args) == 1 and args[0].isdigit():
        n     = int(args[0])
        start = (today - timedelta(days=n)).isoformat()
        end   = (today - timedelta(days=1)).isoformat()
    elif len(args) == 2:
        start, end = args[0], args[1]
    else:
        print("Usage: python analyze_fb_pct.py [days|start end] [--analyze-only|--collect-only]")
        sys.exit(1)

    return start, end, analyze_only, collect_only


def main():
    start_date, end_date, analyze_only, collect_only = parse_args()
    date_range = f"{start_date} to {end_date}"

    print("\n" + "═" * 70)
    print("  FB% SIGNAL PROMOTION — ANALYSIS")
    print(f"  Date range: {date_range}")
    print("═" * 70)

    # ── Phase 1 ───────────────────────────────────────────────────────────────
    if analyze_only:
        print("\n[Phase 1] Skipped (--analyze-only)")
        all_rows = load_raw_csv()
    else:
        all_rows = collect_raw_data(start_date, end_date)
        if not all_rows:
            print("[ERROR] No data collected. Cannot run analysis.")
            sys.exit(1)

    if collect_only:
        print("\n[Phase 2/3] Skipped (--collect-only)")
        return

    if not all_rows and analyze_only:
        all_rows = load_raw_csv()

    # ── Phase 2 ───────────────────────────────────────────────────────────────
    print(f"\n[Phase 2] Running {len(VARIANTS)} variant analyses on {len(all_rows)} rows...")

    # Baseline uses model_prob from the runner directly (no recomputation needed)
    # For all other variants, recompute from raw signals.
    variant_results = []
    for i, variant in enumerate(VARIANTS):
        print(f"  [{i+1}/{len(VARIANTS)}] {variant['name']}...", end=" ", flush=True)

        if variant.get("tag") == "BASE":
            # Baseline: use captured model_prob as-is
            scored = [{**r, "model_prob_v": r.get("model_prob", 0)} for r in all_rows]
        else:
            scored = score_variant(all_rows, variant)

        b     = brier_score(scored)
        m     = mae(scored)
        cal   = calibration_table(scored)
        roi10 = roi_at_threshold(scored, 0.10)
        roi15 = roi_at_threshold(scored, 0.15)
        roi20 = roi_at_threshold(scored, 0.20)
        fp10  = false_positive_rate(scored, 0.10)
        fp15  = false_positive_rate(scored, 0.15)
        ms10  = missed_hr_rate(scored, 0.10)
        ms15  = missed_hr_rate(scored, 0.15)
        top10 = top_pick_accuracy(scored, top_n=10)

        variant_results.append({
            "variant":     variant,
            "brier":       b,
            "mae":         m,
            "calibration": cal,
            "roi_10pct":   roi10,
            "roi_15pct":   roi15,
            "roi_20pct":   roi20,
            "fp_10pct":    fp10,
            "fp_15pct":    fp15,
            "miss_10pct":  ms10,
            "miss_15pct":  ms15,
            "top10_acc":   top10,
        })
        print(f"Brier={b:.5f}  ROI@15%={roi15['roi']:+.1f}%")

    # ── Phase 3 ───────────────────────────────────────────────────────────────
    print("\n[Phase 3] Generating report...")

    group_analysis = power_mult_shift_analysis(all_rows)
    report_text    = generate_report(all_rows, variant_results, date_range, group_analysis)

    print("\n" + report_text)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n  Full report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted]")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"\n[FATAL] {e}")
        traceback.print_exc()
        sys.exit(1)
