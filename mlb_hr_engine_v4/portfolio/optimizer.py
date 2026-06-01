"""
portfolio/optimizer.py — Constrained portfolio pick selection (Session 27).

Selects the optimal subset of picks from a daily pick slate using a greedy
algorithm with configurable hard constraints.

Algorithm:
  1. Score each pick using a composite quality metric
  2. Sort picks descending by score
  3. Greedily add picks while all constraints are satisfied
  4. Return the selected subset with optimization metadata

Composite score (default weights):
  score = ev_pct * 0.35 + edge_pct * 0.30 + (confidence/50) * 0.20 + barrel_bonus * 0.15

  barrel_bonus = max(0, (barrel_pct - 6.0) / 6.0)   # 0 at barrel=6%, 1.0 at barrel=12%
  Normalized so barrel contributes 0-0.15 points above the 6% threshold.

Key insight from Session 27 data analysis:
  Each team generates 9-13 picks per day. Capping at 4 picks/team while
  selecting the highest-scoring subset is the single biggest improvement over
  the current no-cap system. It reduces same-game exposure by 60-75% while
  preserving virtually all pick quality (higher-scoring picks survive the cap).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ── Constraint configuration ──────────────────────────────────────────────────

@dataclass
class PortfolioConstraints:
    """
    Hard constraints for portfolio optimization.

    All constraint violations cause a pick to be excluded.
    Soft preferences (scoring bonuses) are handled by the score function.
    """
    # Volume caps
    max_picks_total:    int   = 25      # max total picks per day
    max_picks_per_team: int   = 4       # max picks from same lineup per day
    max_picks_per_pitcher: int = 4      # max picks against same pitcher (if field available)

    # Quality floors
    # NOTE: Both ev_pct and edge_pct floor to 0.0 because historical rows have avg_edge=1.47%
    # (below the 2% floor) and ev_pct is inconsistently stored as decimal vs percentage across
    # row vintages. Quality filtering is handled by the composite score ranking, not hard floors.
    min_ev_pct:   float = 0.0           # 0 = no EV filter (data inconsistency in old rows)
    min_edge_pct: float = 0.0           # 0 = no edge floor (historical avg=1.47%, below 2% floor)
    min_barrel_pct: float = 0.0         # barrel floor (0 = no filter; set 6.0 for quality filter)

    # Odds range cap (prevent over-concentration in one odds tier)
    max_per_odds_tier: int = 10         # max picks in same odds range bucket

    # Scoring weights
    ev_weight:         float = 0.35
    edge_weight:       float = 0.30
    confidence_weight: float = 0.20
    barrel_weight:     float = 0.15

    # Barrel scoring reference
    barrel_score_floor: float = 6.0    # barrel below this contributes 0 bonus
    barrel_score_ref:   float = 6.0    # denominator for barrel bonus normalization

    def summary(self) -> str:
        parts = [
            f"max {self.max_picks_total} picks/day",
            f"max {self.max_picks_per_team}/team",
        ]
        if self.min_barrel_pct > 0:
            parts.append(f"barrel≥{self.min_barrel_pct:.0f}%")
        if self.min_ev_pct > 3.0:
            parts.append(f"EV≥{self.min_ev_pct:.0f}%")
        return " | ".join(parts)


# Preset constraint sets for comparison
CONSTRAINTS_CONSERVATIVE = PortfolioConstraints(
    max_picks_total=15, max_picks_per_team=3, min_barrel_pct=6.0, min_ev_pct=0.0)

CONSTRAINTS_MODERATE = PortfolioConstraints(
    max_picks_total=20, max_picks_per_team=4, min_barrel_pct=0.0, min_ev_pct=0.0)

CONSTRAINTS_RELAXED = PortfolioConstraints(
    max_picks_total=30, max_picks_per_team=6, min_barrel_pct=0.0, min_ev_pct=0.0)

CONSTRAINTS_BARREL_FOCUSED = PortfolioConstraints(
    max_picks_total=15, max_picks_per_team=4, min_barrel_pct=8.0, min_ev_pct=0.0)

CONSTRAINT_PRESETS = {
    "conservative":    CONSTRAINTS_CONSERVATIVE,
    "moderate":        CONSTRAINTS_MODERATE,
    "relaxed":         CONSTRAINTS_RELAXED,
    "barrel_focused":  CONSTRAINTS_BARREL_FOCUSED,
}


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(str(v).strip()) if v is not None and str(v).strip() != "" else default
    except (ValueError, TypeError):
        return default


def _odds_tier(row: dict) -> str:
    o = int(_safe_float(row.get("american_odds") or row.get("best_odds"), 100))
    if o < 300:  return "+100-299"
    if o < 500:  return "+300-499"
    if o < 700:  return "+500-699"
    if o < 1000: return "+700-999"
    return "+1000+"


# ── Scoring ───────────────────────────────────────────────────────────────────

def composite_score(row: dict, constraints: PortfolioConstraints) -> float:
    """
    Compute the composite quality score for a single pick.

    Returns:
        Score ≥ 0. Higher = better pick for portfolio inclusion.
    """
    ev_pct     = _safe_float(row.get("ev_pct"))
    edge_pct   = _safe_float(row.get("edge_pct"))
    confidence = _safe_float(row.get("confidence"), 50.0)
    barrel_pct = _safe_float(row.get("barrel_pct"))

    # Barrel bonus: normalized above the floor
    barrel_above = max(0.0, barrel_pct - constraints.barrel_score_floor)
    barrel_bonus = min(1.0, barrel_above / constraints.barrel_score_ref)

    score = (
        ev_pct   * constraints.ev_weight +
        edge_pct * constraints.edge_weight +
        (confidence / 50.0) * constraints.confidence_weight +
        barrel_bonus * constraints.barrel_weight
    )
    return round(max(0.0, score), 4)


# ── Optimizer ─────────────────────────────────────────────────────────────────

class PortfolioOptimizer:
    """
    Greedy constrained portfolio optimizer.

    Selects the highest-quality subset of picks from a daily slate while
    respecting all hard constraints.

    Usage:
        opt = PortfolioOptimizer(constraints=CONSTRAINTS_MODERATE)
        result = opt.optimize(picks)
        selected = result["selected"]
        print(result["summary"])
    """

    def __init__(self, constraints: Optional[PortfolioConstraints] = None):
        self.constraints = constraints or PortfolioConstraints()

    def optimize(self, rows: list[dict]) -> dict:
        """
        Optimize pick selection for a given set of rows (typically one day).

        Args:
            rows: pick rows with at least ev_pct, edge_pct, confidence, barrel_pct

        Returns:
            {
              selected: list of selected rows,
              rejected: list of rejected rows with rejection reason,
              n_input: int,
              n_selected: int,
              n_rejected_constraints: int,
              summary: str,
              stats: {before/after comparison of quality metrics},
            }
        """
        c = self.constraints

        # Step 1: Pre-filter quality floors
        passed: list[dict] = []
        failed: list[dict] = []
        for r in rows:
            ev    = _safe_float(r.get("ev_pct"))
            edge  = _safe_float(r.get("edge_pct"))
            barrel = _safe_float(r.get("barrel_pct"))

            if ev < c.min_ev_pct:
                failed.append({**r, "_reject_reason": f"EV {ev:.1f}% < floor {c.min_ev_pct:.0f}%"})
            elif edge < c.min_edge_pct:
                failed.append({**r, "_reject_reason": f"edge {edge:.1f}% < floor {c.min_edge_pct:.0f}%"})
            elif barrel < c.min_barrel_pct and c.min_barrel_pct > 0:
                failed.append({**r, "_reject_reason": f"barrel {barrel:.1f}% < floor {c.min_barrel_pct:.0f}%"})
            else:
                passed.append(r)

        # Step 2: Score and sort
        scored = sorted(
            [(composite_score(r, c), r) for r in passed],
            key=lambda x: -x[0]
        )

        # Step 3: Greedy selection with constraint tracking
        team_counts:    dict[str, int] = defaultdict(int)
        pitcher_counts: dict[str, int] = defaultdict(int)
        odds_tier_counts: dict[str, int] = defaultdict(int)
        total_count = 0

        selected: list[dict] = []
        cap_rejected: list[dict] = []

        for score, row in scored:
            if total_count >= c.max_picks_total:
                cap_rejected.append({**row, "_reject_reason": f"total cap ({c.max_picks_total})"})
                continue

            team = (row.get("team") or "UNK").upper().strip()
            pitcher = (row.get("pitcher") or "").strip()
            odds_t  = _odds_tier(row)

            if team_counts[team] >= c.max_picks_per_team:
                cap_rejected.append({**row, "_reject_reason": f"team cap ({c.max_picks_per_team}) for {team}"})
                continue

            if pitcher and pitcher_counts[pitcher] >= c.max_picks_per_pitcher:
                cap_rejected.append({**row, "_reject_reason": f"pitcher cap ({c.max_picks_per_pitcher}) for {pitcher}"})
                continue

            if odds_tier_counts[odds_t] >= c.max_per_odds_tier:
                cap_rejected.append({**row, "_reject_reason": f"odds tier cap ({c.max_per_odds_tier}) for {odds_t}"})
                continue

            # Accept
            team_counts[team]  += 1
            pitcher_counts[pitcher] += 1
            odds_tier_counts[odds_t] += 1
            total_count += 1
            selected.append({**row, "_score": score})

        all_rejected = failed + cap_rejected
        n_in  = len(rows)
        n_sel = len(selected)

        summary = (
            f"Optimized {n_in}→{n_sel} picks  "
            f"({len(failed)} quality-filtered, {len(cap_rejected)} cap-rejected)  "
            f"[{c.summary()}]"
        )

        stats = _compare_portfolios(rows, selected)

        return {
            "selected":               selected,
            "rejected":               all_rejected,
            "cap_rejected":           cap_rejected,
            "quality_filtered":       failed,
            "n_input":                n_in,
            "n_selected":             n_sel,
            "n_rejected_quality":     len(failed),
            "n_rejected_cap":         len(cap_rejected),
            "summary":                summary,
            "stats":                  stats,
            "constraints_applied":    c.summary(),
        }

    def optimize_multi_date(self, rows: list[dict]) -> dict:
        """
        Optimize picks independently for each date in rows.

        Returns combined result with per-date breakdown.
        """
        from collections import defaultdict as dd
        by_date: dict[str, list] = dd(list)
        for r in rows:
            by_date[r.get("date", "")].append(r)

        all_selected: list[dict] = []
        all_rejected:  list[dict] = []
        per_date: list[dict] = []

        for d, day_rows in sorted(by_date.items()):
            res = self.optimize(day_rows)
            all_selected.extend(res["selected"])
            all_rejected.extend(res["rejected"])
            per_date.append({
                "date":       d,
                "n_input":    res["n_input"],
                "n_selected": res["n_selected"],
                "summary":    res["summary"],
            })

        total_stats = _compare_portfolios(rows, all_selected)

        return {
            "selected":   all_selected,
            "rejected":   all_rejected,
            "per_date":   per_date,
            "n_input":    len(rows),
            "n_selected": len(all_selected),
            "stats":      total_stats,
        }


def _compare_portfolios(raw: list[dict], optimized: list[dict]) -> dict:
    """Compare quality metrics between raw and optimized portfolios."""
    def _avg(rows, key):
        vals = [_safe_float(r.get(key)) for r in rows if _safe_float(r.get(key)) > 0]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    def _win_rate(rows):
        settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
        if not settled:
            return None
        wins = sum(1 for r in settled if r.get("hr_result") == "1")
        return round(wins / len(settled) * 100, 2)

    def _roi(rows):
        settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
        total_w = sum(_safe_float(r.get("bet_dollars")) for r in settled)
        total_p = sum(_safe_float(r.get("profit_loss")) for r in settled)
        return round(total_p / total_w * 100, 2) if total_w > 0 else None

    def _barrel_above_8(rows):
        vals = [_safe_float(r.get("barrel_pct")) for r in rows]
        if not vals:
            return 0.0
        return round(sum(1 for v in vals if v >= 8) / len(vals) * 100, 1)

    return {
        "raw": {
            "n":              len(raw),
            "avg_ev_pct":     _avg(raw, "ev_pct"),
            "avg_edge_pct":   _avg(raw, "edge_pct"),
            "avg_barrel":     _avg(raw, "barrel_pct"),
            "pct_barrel_8+":  _barrel_above_8(raw),
            "avg_confidence": _avg(raw, "confidence"),
            "win_rate_pct":   _win_rate(raw),
            "roi_pct":        _roi(raw),
        },
        "optimized": {
            "n":              len(optimized),
            "avg_ev_pct":     _avg(optimized, "ev_pct"),
            "avg_edge_pct":   _avg(optimized, "edge_pct"),
            "avg_barrel":     _avg(optimized, "barrel_pct"),
            "pct_barrel_8+":  _barrel_above_8(optimized),
            "avg_confidence": _avg(optimized, "confidence"),
            "win_rate_pct":   _win_rate(optimized),
            "roi_pct":        _roi(optimized),
        },
    }


def evaluate_constraint_presets(rows: list[dict]) -> list[dict]:
    """
    Evaluate all preset constraint configurations on a set of rows.

    Returns:
        List of {preset_name, n_selected, quality_stats, roi, ...} for each preset.
    """
    results = []
    for name, constraints in CONSTRAINT_PRESETS.items():
        opt = PortfolioOptimizer(constraints=constraints)
        res = opt.optimize_multi_date(rows)
        stats = res["stats"]
        opt_stats = stats.get("optimized", {})
        results.append({
            "preset":          name,
            "constraints":     constraints.summary(),
            "n_selected":      res["n_selected"],
            "n_input":         res["n_input"],
            "pct_selected":    round(res["n_selected"] / res["n_input"] * 100, 1) if res["n_input"] > 0 else 0,
            "avg_ev_pct":      opt_stats.get("avg_ev_pct"),
            "avg_edge_pct":    opt_stats.get("avg_edge_pct"),
            "avg_barrel":      opt_stats.get("avg_barrel"),
            "pct_barrel_8+":   opt_stats.get("pct_barrel_8+"),
            "win_rate_pct":    opt_stats.get("win_rate_pct"),
            "roi_pct":         opt_stats.get("roi_pct"),
        })

    return results
