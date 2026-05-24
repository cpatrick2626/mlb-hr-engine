#!/usr/bin/env python3
"""
analyze_market_inefficiency.py  —  Session 24: Market Inefficiency Segmentation & Edge Quality
================================================================================================

Goal: identify where sportsbooks systematically misprice HR probability, which archetypes
create sustainable betting edge, where false edges occur, which book tiers are most exploitable,
and where ROI actually concentrates.

Data strategy (no settled pick_tracker rows available):
  PRIMARY   fb_pct_raw_data.csv — 10,777 batter-games with model_prob + actual HR outcomes
  SYNTHETIC engine/vig.py book pricing model — simulate per-book prices vs a naive market baseline
  CALIBRATION model_prob is PRE-calibration; we apply Platt inline to get calibrated prob

Synthetic market model:
  The "market's" true-probability anchor uses only publicly observable contextual signals:
    market_true_prob = 1 - exp(-LEAGUE_AVG_HR_PA × pk_factor × pit_factor × plat_factor × exp_pa)
  This represents a book pricing without Statcast barrel/exit-velo data.
  OUR model (cal_prob) adds the Statcast power_mult layer on top.
  The information gap (cal_prob - market_true_prob) drives synthetic edge.
  Where cal_prob > market + vig-adjusted threshold: positive EV bet.
  Where cal_prob < market OR context stacking inflates market_prob: false or negative edge.

Phases:
  1  Edge segmentation audit  (by barrel-tier/odds-range/park/pitcher/platoon/power/FB%/pull%)
  2  Sportsbook tier analysis  (retail vs sharp vs offshore — how vig destroys edge)
  3  Archetype ROI analysis    (barrel × power × park cross-tabs)
  4  Edge quality filtering    (threshold sweep: EV, edge, 2D grid, false-edge breakdown)
  5  ROI stability analysis    (variance, Sharpe proxy, monthly, sample sufficiency)

Usage:
  py -3.12 analyze_market_inefficiency.py
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
OUT_PATH = ROOT / "market_inefficiency_output.txt"

# ── Engine constants (mirrors config.py + calibration.py) ────────────────────
LEAGUE_AVG_HR_PA = 0.030
MAX_PROB         = 0.29

# Standard Platt calibration params (as fitted per CLAUDE.md)
PLATT_A = 0.7805
PLATT_B = -0.4611

# Elite Platt tier (barrel >= 0.10) — from Session 23
ELITE_PLATT_A             = 0.92
ELITE_PLATT_B             = -0.10
ELITE_PLATT_BARREL_THRESH = 0.10

# Production filter thresholds
MIN_EV_PCT   = 3.0
MIN_EDGE_PCT = 2.0

# Books to simulate  (key: tier)
BOOK_TIERS = {
    "fanduel":    "retail",
    "draftkings": "retail",
    "fanatics":   "retail",
    "caesars":    "mid",
    "betmgm":     "mid",
    "betrivers":  "sharp",
    "circa":      "sharp",
    "betonlineag":"offshore",
    "pinnacle":   "offshore",
}

# Per-book base vig (from vig.py)
BOOK_VIG: dict[str, float] = {
    "fanduel":    0.095,
    "draftkings": 0.088,
    "fanatics":   0.110,
    "caesars":    0.078,
    "betmgm":     0.082,
    "betrivers":  0.070,
    "circa":      0.040,
    "betonlineag":0.055,
    "pinnacle":   0.030,
}

# Odds-range vig multipliers (from vig.py: implied-prob lower bound → multiplier)
ODDS_RANGE_MULT: list[tuple[float, float]] = [
    (0.33, 0.88),
    (0.20, 1.00),
    (0.12, 1.12),
    (0.07, 1.25),
    (0.00, 1.40),
]

LINEUP_PA = {1: 4.5, 2: 4.3, 3: 4.2, 4: 4.1, 5: 3.9,
             6: 3.7, 7: 3.6, 8: 3.4, 9: 3.2}
DEFAULT_PA = 3.8

# Reference book for primary EV/edge/ROI calcs (mid-retail, widely available)
REF_BOOK = "draftkings"


# ── Math helpers ──────────────────────────────────────────────────────────────

def _logit(p: float) -> float:
    p = max(1e-9, min(1 - 1e-9, p))
    return math.log(p / (1 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def platt_scale(p: float, a: float, b: float) -> float:
    return _sigmoid(a * _logit(p) + b)


def apply_calibration(p: float, barrel_rate: float = 0.0) -> float:
    """Apply Platt calibration; elite barrel tier uses separate params (Session 23)."""
    p = max(0.001, min(MAX_PROB, p))
    if barrel_rate >= ELITE_PLATT_BARREL_THRESH:
        return platt_scale(p, ELITE_PLATT_A, ELITE_PLATT_B)
    return platt_scale(p, PLATT_A, PLATT_B)


def american_from_prob(p: float) -> int:
    """Convert implied probability to American odds (rounded to nearest 5)."""
    p = max(0.01, min(0.98, p))
    if p >= 0.5:
        raw = -(p / (1 - p)) * 100
    else:
        raw = ((1 - p) / p) * 100
    return int(round(raw / 5.0) * 5)


def implied_prob(american: int) -> float:
    if american > 0:
        return 100.0 / (american + 100.0)
    return abs(american) / (abs(american) + 100.0)


def _odds_range_mult(american: int) -> float:
    ip = implied_prob(american)
    for threshold, mult in ODDS_RANGE_MULT:
        if ip >= threshold:
            return mult
    return 1.40


def decimal_odds_from_american(american: int) -> float:
    if american > 0:
        return american / 100.0 + 1.0
    return 100.0 / abs(american) + 1.0


def market_true_prob(pk: float, pit: float, plat: float, exp_pa: float) -> float:
    """Naive market's true-probability anchor: basic context signals only, no Statcast.

    Represents a book pricing from park factor, pitcher type, platoon advantage —
    all publicly observable — but without barrel rate or exit-velocity data.
    League-average HR/PA × contextual multipliers × expected PA → Poisson game prob.
    """
    lam = LEAGUE_AVG_HR_PA * pk * pit * plat * exp_pa
    return 1.0 - math.exp(-lam)


def book_market_american(mtp: float, book: str) -> int:
    """American odds the book would post for a given market true probability (after vig)."""
    base_vig = BOOK_VIG.get(book, 0.08)
    am_fair  = american_from_prob(mtp)
    vig_mult = _odds_range_mult(am_fair)
    vig      = min(base_vig * vig_mult, 0.25)
    implied  = min(0.98, mtp * (1.0 + vig))
    return american_from_prob(implied)


def ev_pct(model_p: float, american: int) -> float:
    """EV% of a $1 bet: model sees model_p true prob, book posts at american."""
    d = decimal_odds_from_american(american)
    return (model_p * (d - 1.0) - (1.0 - model_p)) * 100.0


def edge_pct_val(cal_p: float, mtp: float) -> float:
    """Edge in pp: calibrated model prob minus market's true-prob anchor."""
    return (cal_p - mtp) * 100.0


def sim_profit_loss(hit_hr: int, american: int) -> float:
    """Simulated P&L for a $1 flat bet at given odds."""
    d = decimal_odds_from_american(american)
    return (d - 1.0) if hit_hr else -1.0


def brier(p: float, hit_hr: int) -> float:
    return (p - hit_hr) ** 2


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data() -> list[dict]:
    rows = []
    skipped = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            try:
                _hr_raw = raw.get("hit_hr", "0") or "0"
                hit_hr  = 1 if str(_hr_raw).strip().lower() in ("1", "true", "yes") else 0

                r: dict = {
                    "game_date":    raw["game_date"],
                    "player_name":  raw["player_name"],
                    "team":         raw["team"],
                    "opponent":     raw["opponent"],
                    "pitcher_name": raw.get("pitcher_name", ""),
                    "lineup_spot":  int(float(raw["lineup_spot"] or 0)) if raw.get("lineup_spot") else 0,
                    "hit_hr":       hit_hr,
                    "model_prob":   float(raw["model_prob"] or 0),   # PRE-calibration
                    "hr_rate":      float(raw["hr_rate"] or 0),
                    "season_pa":    float(raw["season_pa"] or 0),
                    "sc_source":    raw.get("sc_source", ""),
                    "power_mult":   float(raw["power_mult"] or 1.0),
                    "pk_factor":    float(raw["pk_factor"] or 1.0),
                    "pit_factor":   float(raw["pit_factor"] or 1.0),
                    "plat_factor":  float(raw["plat_factor"] or 1.0),
                    "k_fac":        float(raw["k_fac"] or 1.0),
                    "streak_fac":   float(raw["streak_fac"] or 1.0),
                    "barrel_rate":  float(raw["barrel_rate"] or 0),
                    "fb_pct":       float(raw["fb_pct"] or 0),
                    "pull_pct":     float(raw["pull_pct"] or 0),
                    "exit_velo":    float(raw["exit_velocity_avg"] or 0),
                    "hard_hit_pct": float(raw["hard_hit_pct"] or 0),
                    "xslg":         float(raw["xslg"] or 0),
                }

                r["cal_prob"] = apply_calibration(r["model_prob"], r["barrel_rate"])
                r["exp_pa"]   = LINEUP_PA.get(r["lineup_spot"], DEFAULT_PA)

                # Synthetic market true probability (naive: no Statcast)
                r["mtp"] = market_true_prob(
                    r["pk_factor"], r["pit_factor"], r["plat_factor"], r["exp_pa"]
                )

                # Reference book (DraftKings) metrics
                r["ref_am"]   = book_market_american(r["mtp"], REF_BOOK)
                r["ref_ev"]   = ev_pct(r["cal_prob"], r["ref_am"])
                r["ref_edge"] = edge_pct_val(r["cal_prob"], r["mtp"])
                r["ref_pl"]   = sim_profit_loss(r["hit_hr"], r["ref_am"])
                r["is_bet"]   = r["ref_ev"] >= MIN_EV_PCT and r["ref_edge"] >= MIN_EDGE_PCT

                rows.append(r)
            except (ValueError, KeyError) as exc:
                skipped += 1
                if skipped <= 2:
                    print(f"  [warn] skipped row: {exc}", flush=True)
    return rows


# ── Segmentation helpers ──────────────────────────────────────────────────────

def barrel_tier(br: float) -> str:
    if br < 0.04:   return "<4%"
    if br < 0.06:   return "4-6%"
    if br < 0.08:   return "6-8%"
    if br < 0.10:   return "8-10%"
    if br < 0.12:   return "10-12%"
    return "12%+"


def odds_range_label(american: int) -> str:
    if american <= 200:   return "<+200"
    if american <= 350:   return "+200-350"
    if american <= 500:   return "+350-500"
    if american <= 700:   return "+500-700"
    if american <= 1000:  return "+700-1000"
    return "+1000+"


def park_tier(pk: float) -> str:
    if pk >= 1.08:  return "Hitter (1.08+)"
    if pk >= 1.02:  return "Slight+ (1.02-1.07)"
    if pk >= 0.95:  return "Neutral (0.95-1.01)"
    if pk >= 0.88:  return "Slight- (0.88-0.94)"
    return "Pitcher (<0.88)"


def pitcher_tier(pit: float) -> str:
    if pit >= 1.10:  return "Poor HR suppressor (1.10+)"
    if pit >= 1.00:  return "Below avg (1.00-1.09)"
    if pit >= 0.90:  return "Average (0.90-0.99)"
    if pit >= 0.80:  return "Good (0.80-0.89)"
    return "Elite suppressor (<0.80)"


def platoon_tier(plat: float) -> str:
    if plat >= 1.08:  return "Strong adv (1.08+)"
    if plat >= 1.02:  return "Mild adv (1.02-1.07)"
    if plat >= 0.96:  return "Neutral (0.96-1.01)"
    return "Disadv (<0.96)"


def power_tier(pm: float) -> str:
    if pm >= 1.40:  return "Elite (1.40+)"
    if pm >= 1.15:  return "Above avg (1.15-1.39)"
    if pm >= 0.85:  return "Average (0.85-1.14)"
    return "Below avg (<0.85)"


def fb_tier(fb: float) -> str:
    if fb >= 0.34:  return "High FB (34%+)"
    if fb >= 0.27:  return "Above avg (27-33%)"
    if fb >= 0.20:  return "Average (20-26%)"
    return "Low FB (<20%)"


def pull_tier(pull: float) -> str:
    if pull >= 0.50:  return "Pull-heavy (50%+)"
    if pull >= 0.40:  return "Pull-leaning (40-49%)"
    return "Neutral/oppo (<40%)"


# ── Segment accumulator ───────────────────────────────────────────────────────

class Seg:
    __slots__ = ("n", "hr", "sum_mp", "sum_cp", "sum_mtp",
                 "sum_brier_m", "sum_brier_c",
                 "sum_ev", "sum_edge", "sum_pl", "bets")

    def __init__(self):
        self.n           = 0
        self.hr          = 0
        self.sum_mp      = 0.0   # pre-calibration model_prob
        self.sum_cp      = 0.0   # calibrated prob
        self.sum_mtp     = 0.0   # market true prob (naive)
        self.sum_brier_m = 0.0
        self.sum_brier_c = 0.0
        self.sum_ev      = 0.0   # EV% on qualifying picks
        self.sum_edge    = 0.0   # edge pp on qualifying picks
        self.sum_pl      = 0.0   # P&L on qualifying picks ($1 flat)
        self.bets        = 0     # qualifying pick count

    def add(self, r: dict):
        self.n           += 1
        self.hr          += r["hit_hr"]
        self.sum_mp      += r["model_prob"]
        self.sum_cp      += r["cal_prob"]
        self.sum_mtp     += r["mtp"]
        self.sum_brier_m += brier(r["model_prob"], r["hit_hr"])
        self.sum_brier_c += brier(r["cal_prob"],   r["hit_hr"])
        if r["is_bet"]:
            self.sum_ev   += r["ref_ev"]
            self.sum_edge += r["ref_edge"]
            self.sum_pl   += r["ref_pl"]
            self.bets     += 1

    def actual_pct(self)  -> float: return (self.hr / self.n * 100) if self.n else 0.0
    def model_pct(self)   -> float: return (self.sum_mp / self.n * 100) if self.n else 0.0
    def cal_pct(self)     -> float: return (self.sum_cp / self.n * 100) if self.n else 0.0
    def mkt_pct(self)     -> float: return (self.sum_mtp / self.n * 100) if self.n else 0.0
    def bias_c(self)      -> float: return self.cal_pct() - self.actual_pct()
    def mkt_bias(self)    -> float: return self.mkt_pct() - self.actual_pct()
    def model_edge(self)  -> float: return self.cal_pct() - self.mkt_pct()
    def brier_m(self)     -> float: return (self.sum_brier_m / self.n) if self.n else 0.0
    def brier_c(self)     -> float: return (self.sum_brier_c / self.n) if self.n else 0.0
    def avg_ev(self)      -> float: return (self.sum_ev / self.bets) if self.bets else 0.0
    def avg_edge(self)    -> float: return (self.sum_edge / self.bets) if self.bets else 0.0
    def roi(self)         -> float: return (self.sum_pl / self.bets * 100) if self.bets else 0.0


# ── Report formatting ─────────────────────────────────────────────────────────

def _hdr(title: str, width: int = 110) -> str:
    sep = "=" * width
    return f"\n{sep}\n{title.center(width)}\n{sep}"


def _sub(title: str, width: int = 110) -> str:
    return f"\n{'─' * width}\n  {title}\n{'─' * width}"


def _pct(v: float) -> str:
    return f"{v:+.2f}pp" if v != 0 else " 0.00pp"


def _table_row(cells: list, widths: list) -> str:
    parts = []
    for c, w in zip(cells, widths):
        s = str(c)
        parts.append(s[:w].ljust(w))
    return "  ".join(parts)


def seg_table(segs: dict[str, Seg], title: str,
              ordered_keys: list | None = None, min_n: int = 20) -> list[str]:
    lines = [_sub(title)]
    widths = [26, 6, 6, 7, 7, 8, 8, 8, 7, 7, 7]
    hdr = ["Segment", "N", "HR%", "Cal%", "Mkt%", "MdlEdge", "CalBias", "Bets",
           "AvgEV%", "AvgEdge", "ROI%"]
    lines.append(_table_row(hdr, widths))
    lines.append("  " + "-" * (sum(widths) + 2 * len(widths)))

    if ordered_keys:
        items = [(k, segs[k]) for k in ordered_keys if k in segs]
    else:
        items = sorted(segs.items(), key=lambda x: -x[1].n)

    for label, s in items:
        if s.n < min_n:
            continue
        row = [
            label[:26],
            s.n,
            f"{s.actual_pct():.1f}%",
            f"{s.cal_pct():.1f}%",
            f"{s.mkt_pct():.1f}%",
            _pct(s.model_edge()),
            _pct(s.bias_c()),
            s.bets,
            f"{s.avg_ev():.1f}%" if s.bets else "—",
            f"{s.avg_edge():.1f}%" if s.bets else "—",
            f"{s.roi():+.1f}%" if s.bets else "—",
        ]
        lines.append(_table_row(row, widths))
    return lines


# ── Main analysis ─────────────────────────────────────────────────────────────

def run_analysis(rows: list[dict]) -> list[str]:
    out = []
    n_total = len(rows)
    hr_total = sum(r["hit_hr"] for r in rows)
    n_bets   = sum(1 for r in rows if r["is_bet"])

    # Pre-assign segment labels
    b_tiers = ["<4%","4-6%","6-8%","8-10%","10-12%","12%+"]
    for r in rows:
        r["_bt"]    = barrel_tier(r["barrel_rate"])
        r["_ol"]    = odds_range_label(r["ref_am"])
        r["_park"]  = park_tier(r["pk_factor"])
        r["_pit"]   = pitcher_tier(r["pit_factor"])
        r["_plat"]  = platoon_tier(r["plat_factor"])
        r["_power"] = power_tier(r["power_mult"])
        r["_fb"]    = fb_tier(r["fb_pct"])
        r["_pull"]  = pull_tier(r["pull_pct"])

    out.append(_hdr("Session 24 — Market Inefficiency Segmentation & Edge Quality Analysis"))
    out.append(f"\n  Dataset:  {n_total:,} batter-games  |  Actual HRs: {hr_total:,} ({hr_total/n_total*100:.2f}%)")
    out.append(f"  Ref book: {REF_BOOK.upper()} (vig={BOOK_VIG[REF_BOOK]*100:.1f}%)  |  "
               f"Books simulated: {len(BOOK_TIERS)}")
    out.append(f"  Filters:  EV≥{MIN_EV_PCT}%  Edge≥{MIN_EDGE_PCT}%  →  {n_bets:,} qualifying picks")
    out.append( "")
    out.append( "  Market model assumption:")
    out.append( "    'market true prob' = 1 - exp(-LEAGUE_AVG × pk × pit × plat × exp_pa)")
    out.append( "    Books price from park/pitcher/platoon only — NO Statcast barrel/exit-velo.")
    out.append( "    Our model adds Statcast (power_mult) then calibrates → information advantage.")
    out.append( "    Edge = cal_prob - market_true_prob (our Statcast premium)")
    out.append( "    Positive edge exists for Statcast-elite batters; flat/negative for avg batters")
    out.append( "    in good context (false edge: context inflates market price without Statcast lift).")

    # ════════════════════════════════════════════════════════════════════════════
    # PHASE 1: Edge Segmentation Audit
    # ════════════════════════════════════════════════════════════════════════════
    out.append(_hdr("PHASE 1 — Edge Segmentation Audit"))
    out.append(f"\n  Column legend:")
    out.append(f"    Cal%     = avg calibrated model probability")
    out.append(f"    Mkt%     = avg synthetic market true probability (naive baseline)")
    out.append(f"    MdlEdge  = Cal% - Mkt%  (our Statcast information premium)")
    out.append(f"    CalBias  = Cal% - actual HR%  (calibration error; 0 = perfectly calibrated)")
    out.append(f"    Bets     = picks passing EV≥3% AND Edge≥2%")
    out.append(f"    ROI%     = sim P&L per $1 flat bet at DraftKings synthetic price")

    # 1a — Barrel tier
    segs_bt: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        segs_bt[r["_bt"]].add(r)
    out += seg_table(segs_bt, "1a. By Barrel Rate Tier", ordered_keys=b_tiers, min_n=20)

    # 1b — Odds range (market-implied American odds buckets)
    segs_ol: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        segs_ol[r["_ol"]].add(r)
    odds_order = ["<+200","+200-350","+350-500","+500-700","+700-1000","+1000+"]
    out += seg_table(segs_ol, "1b. By Synthetic Odds Range (market American odds)", ordered_keys=odds_order, min_n=20)

    # 1c — Park tier
    segs_park: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        segs_park[r["_park"]].add(r)
    out += seg_table(segs_park, "1c. By Park Tier", min_n=20)

    # 1d — Pitcher tier
    segs_pit: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        segs_pit[r["_pit"]].add(r)
    out += seg_table(segs_pit, "1d. By Pitcher Tier (pit_factor)", min_n=20)

    # 1e — Platoon tier
    segs_plat: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        segs_plat[r["_plat"]].add(r)
    out += seg_table(segs_plat, "1e. By Platoon Factor", min_n=20)

    # 1f — Power tier
    segs_power: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        segs_power[r["_power"]].add(r)
    out += seg_table(segs_power, "1f. By Power Multiplier Tier (Statcast)", min_n=20)

    # 1g — FB% tier
    segs_fb: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        segs_fb[r["_fb"]].add(r)
    out += seg_table(segs_fb, "1g. By Fly-Ball Rate Tier", min_n=20)

    # 1h — Pull% tier
    segs_pull: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        segs_pull[r["_pull"]].add(r)
    out += seg_table(segs_pull, "1h. By Pull% Tier", min_n=20)

    # 1i — Streak factor
    segs_streak: dict[str, Seg] = defaultdict(Seg)
    for r in rows:
        sf = r["streak_fac"]
        if sf >= 1.06:   lbl = "Hot (1.06+)"
        elif sf >= 1.01: lbl = "Warm (1.01-1.05)"
        elif sf >= 0.96: lbl = "Neutral (0.96-1.00)"
        else:            lbl = "Cold (<0.96)"
        segs_streak[lbl].add(r)
    streak_order = ["Hot (1.06+)","Warm (1.01-1.05)","Neutral (0.96-1.00)","Cold (<0.96)"]
    out += seg_table(segs_streak, "1i. By Streak Factor", ordered_keys=streak_order, min_n=20)

    # ════════════════════════════════════════════════════════════════════════════
    # PHASE 2: Sportsbook Tier Analysis
    # ════════════════════════════════════════════════════════════════════════════
    out.append(_hdr("PHASE 2 — Sportsbook Tier Analysis"))
    out.append("\n  How vig rate across book tiers determines bet volume and EV leakage.")
    out.append("  All books price vs same synthetic market_true_prob; vig is the only differentiator.")
    out.append("  'EV leakage' = the EV destroyed by vig: positive edge that doesn't survive vig.\n")

    book_stats: dict[str, dict] = {}
    for book, tier in BOOK_TIERS.items():
        bv     = BOOK_VIG[book]
        bets   = 0
        sum_ev = sum_pl = sum_hr = sum_edge = 0.0
        total_edge_all = 0.0  # edge on ALL rows (not just qualifying)
        n_positive_edge = 0

        for r in rows:
            mtp  = r["mtp"]
            am   = book_market_american(mtp, book)
            ev   = ev_pct(r["cal_prob"], am)
            edg  = edge_pct_val(r["cal_prob"], mtp)
            pl   = sim_profit_loss(r["hit_hr"], am)
            total_edge_all += edg
            if edg > 0:
                n_positive_edge += 1
            if ev >= MIN_EV_PCT and edg >= MIN_EDGE_PCT:
                bets    += 1
                sum_ev  += ev
                sum_pl  += pl
                sum_hr  += r["hit_hr"]
                sum_edge += edg

        book_stats[book] = {
            "tier":          tier,
            "vig":           bv,
            "bets":          bets,
            "avg_ev":        sum_ev  / bets if bets else 0,
            "roi":           sum_pl  / bets * 100 if bets else 0,
            "hit_rt":        sum_hr  / bets * 100 if bets else 0,
            "avg_edge":      sum_edge / bets if bets else 0,
            "n_pos_edge":    n_positive_edge,
            "avg_edge_all":  total_edge_all / n_total,
        }

    # EV break-even analysis per book
    out.append("  EV break-even: minimum true-prob premium (pp) needed to overcome each book's vig.")
    out.append("  At +600 odds (14.3% implied), each 1pp of vig costs ~0.6pp EV.\n")
    widths_be = [16, 8, 8, 8, 10, 8]
    hdr_be = ["Book", "Tier", "Vig%", "Bets", "AvgEdge%", "ROI%"]
    out.append(_table_row(hdr_be, widths_be))
    out.append("  " + "-" * (sum(widths_be) + 2 * len(widths_be)))
    for book, s in sorted(book_stats.items(), key=lambda x: -x[1]["bets"]):
        row = [book, s["tier"], f"{s['vig']*100:.1f}%", s["bets"],
               f"{s['avg_edge']:.1f}%" if s["bets"] else "—",
               f"{s['roi']:+.1f}%" if s["bets"] else "—"]
        out.append(_table_row(row, widths_be))

    out.append("\n  Positive-edge picks (before vig filter): count by book")
    out.append("  (All books see same edge distribution; vig determines what survives the EV filter)")
    for book, s in sorted(book_stats.items(), key=lambda x: x[1]["vig"]):
        pct = s["n_pos_edge"] / n_total * 100
        out.append(f"    {book:16s}  vig={s['vig']*100:.1f}%  "
                   f"pos-edge rows={s['n_pos_edge']:,} ({pct:.1f}%)")

    out.append("\n  Book Tier Summary:")
    tier_agg: dict[str, dict] = {}
    for book, s in book_stats.items():
        t = s["tier"]
        if t not in tier_agg:
            tier_agg[t] = {"books": 0, "bets": 0, "ev": 0.0, "roi": 0.0, "vig": 0.0}
        tier_agg[t]["books"] += 1
        tier_agg[t]["bets"]  += s["bets"]
        tier_agg[t]["ev"]    += s["avg_ev"]
        tier_agg[t]["roi"]   += s["roi"]
        tier_agg[t]["vig"]   += s["vig"]
    for tier in ["retail","mid","sharp","offshore"]:
        ts = tier_agg.get(tier)
        if not ts:
            continue
        nb = ts["books"]
        out.append(f"    {tier:10s}  avg_vig={ts['vig']/nb*100:.1f}%  "
                   f"total_bets={ts['bets']}  avg_ev={ts['ev']/nb:.1f}%  "
                   f"avg_roi={ts['roi']/nb:+.1f}%")

    # ════════════════════════════════════════════════════════════════════════════
    # PHASE 3: Archetype ROI Analysis
    # ════════════════════════════════════════════════════════════════════════════
    out.append(_hdr("PHASE 3 — Archetype ROI Analysis"))
    out.append("\n  Cross-segment: barrel × power, barrel × park, barrel × platoon.")
    out.append("  'MdlEdge' = Cal% - Mkt%  (systematic info advantage vs naive market).")
    out.append("  Cells with ≥15 qualifying bets shown; others noted as sparse.\n")

    def cross_tab(rows_: list, key_fn_a, key_fn_b, keys_a: list, keys_b: list,
                  title: str, label_a: str = "A", min_bets: int = 15) -> list[str]:
        lines = [_sub(title)]
        cross: dict[tuple, Seg] = defaultdict(Seg)
        for r_ in rows_:
            cross[(key_fn_a(r_), key_fn_b(r_))].add(r_)
        col_w = 26
        hdr_r = f"  {label_a[:14]:<14}"
        for kb in keys_b:
            hdr_r += kb[:col_w].ljust(col_w)
        lines.append(hdr_r)
        for ka in keys_a:
            row_str = f"  {ka[:14]:<14}"
            for kb in keys_b:
                s = cross.get((ka, kb))
                if s and s.bets >= min_bets:
                    row_str += (f"n={s.bets} HR={s.actual_pct():.0f}% "
                                f"ROI={s.roi():+.0f}%").ljust(col_w)
                elif s and s.n >= 20:
                    row_str += f"({s.n} rows, <{min_bets} bets)".ljust(col_w)
                else:
                    row_str += "—".ljust(col_w)
            lines.append(row_str)
        return lines

    power_tiers  = ["Below avg (<0.85)", "Average (0.85-1.14)", "Above avg (1.15-1.39)", "Elite (1.40+)"]
    park_tiers   = ["Pitcher (<0.88)", "Slight- (0.88-0.94)", "Neutral (0.95-1.01)",
                    "Slight+ (1.02-1.07)", "Hitter (1.08+)"]
    plat_tiers   = ["Disadv (<0.96)", "Neutral (0.96-1.01)", "Mild adv (1.02-1.07)", "Strong adv (1.08+)"]

    out += cross_tab(rows, lambda r: r["_bt"], lambda r: r["_power"],
                     b_tiers, power_tiers, "3a. Barrel × Power Tier", "Barrel")
    out += cross_tab(rows, lambda r: r["_bt"], lambda r: r["_park"],
                     b_tiers, park_tiers, "3b. Barrel × Park Tier", "Barrel")
    out += cross_tab(rows, lambda r: r["_bt"], lambda r: r["_plat"],
                     b_tiers, plat_tiers, "3c. Barrel × Platoon Tier", "Barrel")

    # 3d — Best composite archetypes (barrel + power + park, ≥20 bets)
    out.append(_sub("3d. Top 15 Archetype Clusters by ROI (barrel+power+park, ≥20 bets)"))
    cross_combo: dict[tuple, Seg] = defaultdict(Seg)
    for r in rows:
        cross_combo[(r["_bt"], r["_power"], r["_park"])].add(r)
    qualified = [(k, s) for k, s in cross_combo.items() if s.bets >= 20]
    qualified.sort(key=lambda x: -x[1].roi())
    widths3d = [10, 22, 20, 6, 8, 8, 8, 8]
    hdr3d    = ["Barrel", "Power", "Park", "Bets", "HR%", "MdlEdge", "AvgEV%", "ROI%"]
    out.append(_table_row(hdr3d, widths3d))
    out.append("  " + "-" * (sum(widths3d) + 2 * len(widths3d)))
    for (bt, pt, pk), s in qualified[:15]:
        row3d = [bt, pt[:22], pk[:20], s.bets, f"{s.actual_pct():.1f}%",
                 _pct(s.model_edge()), f"{s.avg_ev():.1f}%", f"{s.roi():+.1f}%"]
        out.append(_table_row(row3d, widths3d))

    out.append(_sub("3e. Bottom 10 Archetype Clusters by ROI (≥20 bets — false edge traps)"))
    out.append("  These are batter-types that LOOK attractive but deliver poor simulated ROI.")
    out.append(_table_row(hdr3d, widths3d))
    out.append("  " + "-" * (sum(widths3d) + 2 * len(widths3d)))
    for (bt, pt, pk), s in qualified[-10:]:
        row3d = [bt, pt[:22], pk[:20], s.bets, f"{s.actual_pct():.1f}%",
                 _pct(s.model_edge()), f"{s.avg_ev():.1f}%", f"{s.roi():+.1f}%"]
        out.append(_table_row(row3d, widths3d))

    # ════════════════════════════════════════════════════════════════════════════
    # PHASE 4: Edge Quality Filtering Audit
    # ════════════════════════════════════════════════════════════════════════════
    out.append(_hdr("PHASE 4 — Edge Quality Filtering Audit"))
    out.append("\n  Threshold sweep: MIN_EV_PCT (1.0–7.0) and MIN_EDGE_PCT (0.5–5.0).")
    out.append("  ROI is simulated P&L at DraftKings synthetic prices, $1 flat bet.\n")

    # 4a — EV sweep (fixed edge=2.0)
    out.append(_sub("4a. EV Threshold Sweep (MIN_EDGE_PCT fixed at 2.0pp)"))
    widths4 = [10, 8, 8, 8, 10, 8]
    hdr4 = ["MinEV%", "Bets", "HR%", "AvgEdge%", "AvgEV%", "ROI%"]
    out.append(_table_row(hdr4, widths4))
    out.append("  " + "-" * (sum(widths4) + 2 * len(widths4)))
    for ev_floor in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]:
        bets = sum_ev_v = sum_pl_v = sum_hr_v = sum_edg_v = 0
        for r in rows:
            if r["ref_ev"] >= ev_floor and r["ref_edge"] >= 2.0:
                bets     += 1
                sum_ev_v += r["ref_ev"]
                sum_pl_v += r["ref_pl"]
                sum_hr_v += r["hit_hr"]
                sum_edg_v += r["ref_edge"]
        marker = " ← current" if ev_floor == MIN_EV_PCT else ""
        row4 = [f"{ev_floor:.1f}%", bets,
                f"{sum_hr_v/bets*100:.1f}%" if bets else "—",
                f"{sum_edg_v/bets:.1f}%" if bets else "—",
                f"{sum_ev_v/bets:.1f}%" if bets else "—",
                f"{sum_pl_v/bets*100:+.1f}%" if bets else "—"]
        out.append(_table_row(row4, widths4) + marker)

    # 4b — Edge sweep (fixed EV=3.0)
    out.append(_sub("4b. Edge Threshold Sweep (MIN_EV_PCT fixed at 3.0%)"))
    hdr4b = ["MinEdge%", "Bets", "HR%", "AvgEdge%", "AvgEV%", "ROI%"]
    out.append(_table_row(hdr4b, widths4))
    out.append("  " + "-" * (sum(widths4) + 2 * len(widths4)))
    for edg_floor in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
        bets = sum_edg_v = sum_pl_v = sum_hr_v = sum_ev_v = 0
        for r in rows:
            if r["ref_ev"] >= 3.0 and r["ref_edge"] >= edg_floor:
                bets      += 1
                sum_edg_v += r["ref_edge"]
                sum_pl_v  += r["ref_pl"]
                sum_hr_v  += r["hit_hr"]
                sum_ev_v  += r["ref_ev"]
        marker = " ← current" if edg_floor == MIN_EDGE_PCT else ""
        row4b = [f"{edg_floor:.1f}%", bets,
                 f"{sum_hr_v/bets*100:.1f}%" if bets else "—",
                 f"{sum_edg_v/bets:.1f}%" if bets else "—",
                 f"{sum_ev_v/bets:.1f}%" if bets else "—",
                 f"{sum_pl_v/bets*100:+.1f}%" if bets else "—"]
        out.append(_table_row(row4b, widths4) + marker)

    # 4c — 2D grid EV × Edge
    out.append(_sub("4c. 2D Grid: EV% floor × Edge% floor — ROI% (bets)"))
    ev_g   = [2.0, 3.0, 4.0, 5.0, 6.0]
    edge_g = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    col_w4 = 20
    hdr_g  = "  " + "EV\\Edge".ljust(8)
    for ef in edge_g:
        hdr_g += f"{ef:.1f}%".ljust(col_w4)
    out.append(hdr_g)
    for ev_f in ev_g:
        row_str = "  " + f"{ev_f:.1f}%".ljust(8)
        for edg_f in edge_g:
            bets = sum_pl = sum_hr = 0
            for r in rows:
                if r["ref_ev"] >= ev_f and r["ref_edge"] >= edg_f:
                    bets   += 1
                    sum_pl += r["ref_pl"]
                    sum_hr += r["hit_hr"]
            if bets >= 10:
                roi  = sum_pl / bets * 100
                cell = f"{roi:+.1f}%(n={bets})"
            elif bets > 0:
                cell = f"n={bets}<10"
            else:
                cell = "—"
            marker = "*" if (ev_f == MIN_EV_PCT and edg_f == MIN_EDGE_PCT) else " "
            row_str += (marker + cell).ljust(col_w4)
        out.append(row_str)
    out.append("  (* = current production threshold)")

    # 4d — False edge breakdown by calibration tier
    out.append(_sub("4d. Calibration Bias by Probability Tier (all 10,777 rows)"))
    out.append("  Shows where the model over/under-predicts; 'MktBias' = market's misprice.")
    out.append("  Sustainable edge = low CalBias AND positive MdlEdge AND positive ROI.\n")
    prob_buckets = [
        ("cal<6%",   lambda r: r["cal_prob"] < 0.06),
        ("6-8%",     lambda r: 0.06 <= r["cal_prob"] < 0.08),
        ("8-10%",    lambda r: 0.08 <= r["cal_prob"] < 0.10),
        ("10-12%",   lambda r: 0.10 <= r["cal_prob"] < 0.12),
        ("12-15%",   lambda r: 0.12 <= r["cal_prob"] < 0.15),
        ("15-20%",   lambda r: 0.15 <= r["cal_prob"] < 0.20),
        ("20%+",     lambda r: r["cal_prob"] >= 0.20),
    ]
    widths4d = [10, 8, 8, 8, 10, 10, 8]
    hdr4d    = ["CalProb", "N", "HR%", "Cal%", "CalBias", "MdlEdge", "Bets"]
    out.append(_table_row(hdr4d, widths4d))
    out.append("  " + "-" * (sum(widths4d) + 2 * len(widths4d)))
    for lbl, fn in prob_buckets:
        sub = [r for r in rows if fn(r)]
        if len(sub) < 10:
            continue
        n     = len(sub)
        n_hr  = sum(r["hit_hr"] for r in sub)
        avg_c = sum(r["cal_prob"] for r in sub) / n
        avg_m = sum(r["mtp"] for r in sub) / n
        n_bet = sum(1 for r in sub if r["is_bet"])
        bias  = avg_c * 100 - n_hr / n * 100
        medge = (avg_c - avg_m) * 100
        row4d = [lbl, n, f"{n_hr/n*100:.2f}%", f"{avg_c*100:.2f}%",
                 _pct(bias), _pct(medge), n_bet]
        out.append(_table_row(row4d, widths4d))

    # 4e — Edge quality by barrel tier (qualifying picks only)
    qualifying = [r for r in rows if r["is_bet"]]
    if qualifying:
        out.append(_sub("4e. Edge Quality Metrics by Barrel Tier (qualifying picks only)"))
        widths4e = [12, 6, 8, 8, 8, 8, 8]
        hdr4e    = ["Barrel", "Bets", "HR%", "Cal%", "MdlEdge", "AvgEV%", "ROI%"]
        out.append(_table_row(hdr4e, widths4e))
        out.append("  " + "-" * (sum(widths4e) + 2 * len(widths4e)))
        for bt in b_tiers:
            sub = [r for r in qualifying if r["_bt"] == bt]
            if not sub:
                continue
            n     = len(sub)
            n_hr  = sum(r["hit_hr"] for r in sub)
            avg_c = sum(r["cal_prob"] for r in sub) / n
            avg_m = sum(r["mtp"] for r in sub) / n
            avg_ev = sum(r["ref_ev"] for r in sub) / n
            tot_pl = sum(r["ref_pl"] for r in sub)
            row4e = [bt, n, f"{n_hr/n*100:.1f}%", f"{avg_c*100:.1f}%",
                     _pct((avg_c-avg_m)*100), f"{avg_ev:.1f}%", f"{tot_pl/n*100:+.1f}%"]
            out.append(_table_row(row4e, widths4e))

    # ════════════════════════════════════════════════════════════════════════════
    # PHASE 5: ROI Stability Analysis
    # ════════════════════════════════════════════════════════════════════════════
    out.append(_hdr("PHASE 5 — ROI Stability Analysis"))
    out.append("\n  Variance, win rate, Sharpe proxy, calendar concentration, sample sufficiency.\n")

    if not qualifying:
        out.append("  No qualifying picks — cannot compute stability metrics.")
        return out

    n_q    = len(qualifying)
    n_hr_q = sum(r["hit_hr"] for r in qualifying)
    pl_list = [r["ref_pl"] for r in qualifying]
    avg_pl  = sum(pl_list) / n_q
    var_pl  = sum((x - avg_pl) ** 2 for x in pl_list) / n_q
    std_pl  = math.sqrt(var_pl) if var_pl > 0 else 0.001
    sharpe  = avg_pl / std_pl
    win_rt  = n_hr_q / n_q * 100

    out.append(f"  Qualifying picks (EV≥{MIN_EV_PCT}%, Edge≥{MIN_EDGE_PCT}%): {n_q:,}")
    out.append(f"  Hit rate (actual HR%): {win_rt:.2f}%")
    out.append(f"  Avg P&L per pick ($1 flat): {avg_pl:+.4f}  →  ROI: {avg_pl*100:+.2f}%")
    out.append(f"  Std dev of P&L: {std_pl:.4f}")
    out.append(f"  Sharpe proxy (avg/std): {sharpe:.4f}")
    out.append(f"  95% CI width on ROI (±): {1.96*std_pl/math.sqrt(n_q)*100:.2f}pp")

    # 5a — Monthly breakdown
    out.append(_sub("5a. ROI by Calendar Month"))
    monthly_pl: dict[str, list] = defaultdict(list)
    monthly_hr: dict[str, int]  = defaultdict(int)
    for r in qualifying:
        month = r["game_date"][:7] if len(r["game_date"]) >= 7 else "unknown"
        monthly_pl[month].append(r["ref_pl"])
        monthly_hr[month]  += r["hit_hr"]
    widths5a = [10, 6, 8, 10, 10]
    hdr5a    = ["Month", "Bets", "HR%", "ROI%", "StdDev"]
    out.append(_table_row(hdr5a, widths5a))
    out.append("  " + "-" * (sum(widths5a) + 2 * len(widths5a)))
    for month in sorted(monthly_pl.keys()):
        pls = monthly_pl[month]
        nb  = len(pls)
        avg = sum(pls) / nb
        std = math.sqrt(sum((x-avg)**2 for x in pls)/nb) if nb > 1 else 0
        out.append(_table_row([month, nb, f"{monthly_hr[month]/nb*100:.1f}%",
                                f"{avg*100:+.1f}%", f"{std:.3f}"], widths5a))

    # 5b — ROI by barrel tier (stability)
    out.append(_sub("5b. ROI Stability by Barrel Tier (qualifying picks only)"))
    widths5b = [12, 6, 8, 8, 8, 8, 10, 10]
    hdr5b    = ["Barrel", "Bets", "HR%", "Cal%", "Mkt%", "MdlEdge", "AvgEV%", "ROI%"]
    out.append(_table_row(hdr5b, widths5b))
    out.append("  " + "-" * (sum(widths5b) + 2 * len(widths5b)))
    for bt in b_tiers:
        sub = [r for r in qualifying if r["_bt"] == bt]
        if not sub:
            continue
        n     = len(sub)
        n_hr  = sum(r["hit_hr"] for r in sub)
        avg_c = sum(r["cal_prob"] for r in sub) / n
        avg_m = sum(r["mtp"] for r in sub) / n
        avg_e = sum(r["ref_ev"] for r in sub) / n
        tot_p = sum(r["ref_pl"] for r in sub)
        row5b = [bt, n, f"{n_hr/n*100:.1f}%", f"{avg_c*100:.1f}%",
                 f"{avg_m*100:.1f}%", _pct((avg_c-avg_m)*100),
                 f"{avg_e:.1f}%", f"{tot_p/n*100:+.1f}%"]
        out.append(_table_row(row5b, widths5b))

    # 5c — ROI by odds range
    out.append(_sub("5c. ROI & Variance by Odds Range (qualifying picks only)"))
    odds_q: dict[str, list] = defaultdict(list)
    odds_hr: dict[str, int]  = defaultdict(int)
    for r in qualifying:
        odds_q[r["_ol"]].append(r["ref_pl"])
        odds_hr[r["_ol"]] += r["hit_hr"]
    widths5c = [14, 6, 8, 10, 10]
    hdr5c    = ["Odds Range", "Bets", "HR%", "ROI%", "StdDev"]
    out.append(_table_row(hdr5c, widths5c))
    out.append("  " + "-" * (sum(widths5c) + 2 * len(widths5c)))
    for ol in ["<+200","+200-350","+350-500","+500-700","+700-1000","+1000+"]:
        pls = odds_q.get(ol, [])
        if len(pls) < 5:
            continue
        nb  = len(pls)
        avg = sum(pls) / nb
        std = math.sqrt(sum((x-avg)**2 for x in pls)/nb) if nb > 1 else 0
        out.append(_table_row([ol, nb, f"{odds_hr[ol]/nb*100:.1f}%",
                                f"{avg*100:+.1f}%", f"{std:.3f}"], widths5c))

    # 5d — Sample sufficiency
    out.append(_sub("5d. Sample Sufficiency — Statistical Power"))
    actual_hr_rate = n_hr_q / n_q
    se = math.sqrt(actual_hr_rate * (1 - actual_hr_rate) / n_q)
    out.append(f"\n  n={n_q:,}  actual HR%={actual_hr_rate*100:.2f}%")
    out.append(f"  SE = {se*100:.2f}pp  →  95% CI [{(actual_hr_rate-1.96*se)*100:.2f}%, "
               f"{(actual_hr_rate+1.96*se)*100:.2f}%]")
    for resolution_pp in [1.0, 0.5]:
        n_needed = int(math.ceil((1.96**2) * actual_hr_rate * (1-actual_hr_rate) / (resolution_pp/100)**2))
        out.append(f"  Picks needed for ±{resolution_pp:.1f}pp resolution: {n_needed:,}")

    # ════════════════════════════════════════════════════════════════════════════
    # SUMMARY & RECOMMENDATIONS
    # ════════════════════════════════════════════════════════════════════════════
    out.append(_hdr("SUMMARY & PRODUCTION RECOMMENDATIONS"))

    out.append("\n  [Market Model Interpretation]")
    out.append(f"  Synthetic edge source: Statcast power_mult not used by naive market baseline.")
    out.append(f"  Qualifying picks (EV≥3%, Edge≥2%): {n_q:,} of {n_total:,} ({n_q/n_total*100:.1f}%)")
    out.append(f"  Simulated ROI at DraftKings: {avg_pl*100:+.2f}%  |  Sharpe proxy: {sharpe:.4f}")

    out.append("\n  [Calibration Quality — Where Model Is Most Trustworthy]")
    # find best-calibrated barrel tier (among those with n>=100)
    best_bt = min(
        [(bt, segs_bt[bt]) for bt in b_tiers if bt in segs_bt and segs_bt[bt].n >= 100],
        key=lambda x: abs(x[1].bias_c()), default=("—", None)
    )
    worst_bt = max(
        [(bt, segs_bt[bt]) for bt in b_tiers if bt in segs_bt and segs_bt[bt].n >= 100],
        key=lambda x: abs(x[1].bias_c()), default=("—", None)
    )
    if best_bt[1]:
        out.append(f"  Best-calibrated barrel tier: {best_bt[0]} "
                   f"(CalBias={_pct(best_bt[1].bias_c())}, n={best_bt[1].n})")
    if worst_bt[1]:
        out.append(f"  Worst-calibrated barrel tier: {worst_bt[0]} "
                   f"(CalBias={_pct(worst_bt[1].bias_c())}, n={worst_bt[1].n})")

    out.append("\n  [Sportsbook Ranking — Most Exploitable (highest synthetic EV)]")
    for i, (book, s) in enumerate(
            sorted(book_stats.items(), key=lambda x: -x[1]["avg_ev"])[:5], 1):
        out.append(f"  {i}. {book:16s}  vig={s['vig']*100:.1f}%  bets={s['bets']}  "
                   f"avg_ev={s['avg_ev']:.1f}%  roi={s['roi']:+.1f}%")

    out.append("\n  [Edge Quality Assessment]")
    # Compare ROI at current vs alternative thresholds
    alt_bets = sum(1 for r in rows if r["ref_ev"] >= 4.0 and r["ref_edge"] >= 2.5)
    alt_pl   = sum(r["ref_pl"] for r in rows if r["ref_ev"] >= 4.0 and r["ref_edge"] >= 2.5)
    alt_roi  = alt_pl / alt_bets * 100 if alt_bets else 0
    out.append(f"  Current  EV≥3%  Edge≥2%:  n={n_q}  roi={avg_pl*100:+.1f}%")
    out.append(f"  Tighter  EV≥4%  Edge≥2.5%: n={alt_bets}  roi={alt_roi:+.1f}%")
    out.append(f"  {'Tighten thresholds' if alt_roi > avg_pl*100 + 2 else 'Keep current thresholds'}"
               f" (simulated; requires real settled data to confirm)")

    out.append("\n  [Barrel-ROI Concentration]")
    bt_roi_map = {}
    for bt in b_tiers:
        sub = [r for r in qualifying if r["_bt"] == bt]
        if sub:
            bt_roi_map[bt] = sum(r["ref_pl"] for r in sub) / len(sub) * 100
    if bt_roi_map:
        best  = max(bt_roi_map, key=bt_roi_map.get)
        worst = min(bt_roi_map, key=bt_roi_map.get)
        out.append(f"  Best  barrel ROI tier: {best}  →  {bt_roi_map[best]:+.1f}%")
        out.append(f"  Worst barrel ROI tier: {worst} →  {bt_roi_map[worst]:+.1f}%")

    out.append("\n  [Next Steps — Requiring Real Settled Data]")
    out.append("  1. pick_tracker.csv has 0 settled rows — all ROI here is SYNTHETIC.")
    out.append("  2. Once ≥200 picks settle, re-run with real market prices + outcomes.")
    out.append("  3. Expected improvement from Session 23 (elite barrel preservation):")
    out.append("     barrel≥12% bets should show better hit rates as cal_prob rises.")
    out.append("  4. Book-specific threshold: sharp books (circa, pinnacle) should use")
    out.append("     lower EV floor (e.g. 1.5%) since their vig already screens bad edges.")
    out.append("  5. Composite archetype clusters from Phase 3d can inform a scoring bonus")
    out.append("     in ranker.py for picks that match best-ROI profiles.")
    out.append("  6. Session 24 limitation: market model assumes books ignore Statcast.")
    out.append("     Reality: sharp books partially price barrel rate. True edge is lower.")

    return out


def main():
    print(f"Loading {CSV_PATH.name} ...", end=" ", flush=True)
    rows = load_data()
    print(f"{len(rows):,} rows loaded.")

    print("Running analysis ...", flush=True)
    output_lines = run_analysis(rows)
    report = "\n".join(str(x) for x in output_lines)

    print(report)
    OUT_PATH.write_text(report, encoding="utf-8")
    print(f"\nSaved → {OUT_PATH}")


if __name__ == "__main__":
    main()
