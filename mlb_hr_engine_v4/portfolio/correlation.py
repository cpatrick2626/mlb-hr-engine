"""
portfolio/correlation.py — Factor-based pick correlation model (Session 27).

HR prop picks are NOT independent events. Shared environmental factors create
positive correlations that inflate portfolio variance beyond what naive pick counts suggest.

Factor model:
  ρ(i,j) = Σ w_k * I(pick i and pick j share factor k)

  Shared factors and estimated weights:
    - Same lineup (date + team):        ρ = LINEUP_CORR  (0.40)
      Both batters face same pitcher, same park, same weather, same lineup density
    - Same park, different team, same day: ρ = PARK_CORR (0.12)
      Shared park factor + weather conditions, independent pitchers/lineups
    - Same day, different game:          ρ = DAY_CORR   (0.04)
      Macro same-day effects only (league-wide HR environment)
    - Different date:                    ρ = 0.0
      Statistically independent

Literature reference:
  Fantasy sports research shows within-lineup correlations of 0.25-0.50 for HR outcomes
  depending on lineup position proximity. We use 0.40 as a central estimate.

Usage:
  from portfolio.correlation import pick_correlation, portfolio_corr_stats
  stats = portfolio_corr_stats(rows)
  print(f"Avg pairwise ρ: {stats['avg_pairwise_corr']:.3f}")
  print(f"Effective N: {stats['effective_n']:.1f} of {len(rows)}")
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional


# ── Factor weights ────────────────────────────────────────────────────────────
# These represent the correlation contribution from each shared factor.
# Calibrated from fantasy sports / sports betting literature.
# Rollback: set all to 0 for independence assumption.

LINEUP_CORR  = 0.40   # same date + same team (shared pitcher+park+weather+lineup)
PARK_CORR    = 0.12   # same park + same date, different teams (cross-game park/weather)
DAY_CORR     = 0.04   # same date, different park (macro league HR environment)

# Keys used to identify factors in each row
_DATE_KEY    = "date"
_TEAM_KEY    = "team"
_OPPONENT_KEY = "opponent"   # may be blank in pre-Session 25 rows


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(str(v).strip()) if v is not None and str(v).strip() != "" else default
    except (ValueError, TypeError):
        return default


# ── Pairwise correlation ──────────────────────────────────────────────────────

def pick_correlation(a: dict, b: dict) -> float:
    """
    Estimate pairwise correlation between two HR picks.

    Args:
        a, b: pick dicts (from pick_tracker.csv rows)

    Returns:
        Estimated ρ ∈ [0, 1].
    """
    date_a = a.get(_DATE_KEY, "")
    date_b = b.get(_DATE_KEY, "")

    # Different dates = independent
    if date_a != date_b or not date_a:
        return 0.0

    team_a = (a.get(_TEAM_KEY) or "").upper().strip()
    team_b = (b.get(_TEAM_KEY) or "").upper().strip()

    # Same team, same date = shared lineup environment
    if team_a == team_b and team_a:
        return LINEUP_CORR

    # Different team, same date — check if they share a park (one team plays at the other's park)
    opp_a = (a.get(_OPPONENT_KEY) or "").upper().strip()
    opp_b = (b.get(_OPPONENT_KEY) or "").upper().strip()

    # Cross-game park correlation: team_a's opponent is team_b (they play each other)
    if opp_a and opp_b:
        # a plays b's team or b plays a's team = same game = use lineup-level correlation
        if opp_a == team_b or opp_b == team_a:
            return LINEUP_CORR * 0.85   # slightly lower: different pitcher perspective
        # Otherwise: different games, same day
        return DAY_CORR
    else:
        # No opponent data — assume different games, same day
        return DAY_CORR


# ── Portfolio-level statistics ────────────────────────────────────────────────

def portfolio_corr_stats(rows: list[dict]) -> dict:
    """
    Compute portfolio-level correlation statistics.

    Returns:
        {
          avg_pairwise_corr: float,
          effective_n: float,
          n_picks: int,
          within_lineup_pairs: int,    # pairs with high correlation
          cross_game_pairs: int,
          independent_pairs: int,
          lineup_clusters: list[dict], # per (date, team) cluster info
          high_corr_pct: float,        # % of pairs with ρ >= 0.30
        }
    """
    from .metrics import effective_n as _effective_n

    n = len(rows)
    if n == 0:
        return {"n_picks": 0, "avg_pairwise_corr": 0.0, "effective_n": 0.0}

    # Group by (date, team) to count same-lineup pairs efficiently
    by_date_team: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        key = (r.get(_DATE_KEY, ""), (r.get(_TEAM_KEY) or "").upper().strip())
        by_date_team[key].append(r)

    # Group by date to count cross-game pairs
    by_date: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_date[r.get(_DATE_KEY, "")].append(r)

    total_pairs     = n * (n - 1) / 2
    lineup_pairs    = 0
    cross_game_pairs = 0
    independent_pairs = 0
    corr_sum        = 0.0

    for (date, team), members in by_date_team.items():
        k = len(members)
        if k >= 2:
            pairs_here = k * (k - 1) / 2
            lineup_pairs += pairs_here
            corr_sum += pairs_here * LINEUP_CORR

    # Cross-game pairs (same date, different team)
    for date, day_rows in by_date.items():
        day_n = len(day_rows)
        day_lineup_pairs = 0
        for (d, t), members in by_date_team.items():
            if d == date and len(members) >= 2:
                k = len(members)
                day_lineup_pairs += k * (k - 1) / 2
        same_day_pairs = day_n * (day_n - 1) / 2
        cross_here = same_day_pairs - day_lineup_pairs
        cross_game_pairs += cross_here
        corr_sum += cross_here * DAY_CORR

    independent_pairs = total_pairs - lineup_pairs - cross_game_pairs

    avg_corr = corr_sum / total_pairs if total_pairs > 0 else 0.0
    n_eff    = _effective_n(n, avg_corr)

    # Per-cluster summary
    clusters = []
    for (date, team), members in sorted(by_date_team.items()):
        k = len(members)
        wins = sum(1 for m in members if m.get("hr_result") == "1")
        clusters.append({
            "date":      date,
            "team":      team,
            "n_picks":   k,
            "wins":      wins,
            "corr":      LINEUP_CORR,
            "pairs":     k * (k - 1) // 2,
        })
    clusters.sort(key=lambda x: (-x["n_picks"], x["date"], x["team"]))

    return {
        "n_picks":            n,
        "total_pairs":        int(total_pairs),
        "lineup_pairs":       int(lineup_pairs),
        "cross_game_pairs":   int(cross_game_pairs),
        "independent_pairs":  int(independent_pairs),
        "avg_pairwise_corr":  round(avg_corr, 4),
        "effective_n":        n_eff,
        "clusters":           clusters,
        "high_corr_pct":      round(lineup_pairs / total_pairs * 100, 1) if total_pairs > 0 else 0.0,
    }


def same_lineup_win_corr(rows: list[dict]) -> Optional[float]:
    """
    Realized same-lineup correlation: when one player in a lineup HRs,
    how much more likely are other picks in that lineup to HR?

    Returns:
        Realized ρ estimate or None if insufficient settled data.
    """
    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    if len(settled) < 20:
        return None

    by_cluster: dict[tuple, list[int]] = defaultdict(list)
    for r in settled:
        key = (r.get("date", ""), (r.get("team") or "").upper().strip())
        by_cluster[key].append(int(r.get("hr_result", 0)))

    # Only clusters with ≥2 picks
    multi_clusters = {k: v for k, v in by_cluster.items() if len(v) >= 2}
    if not multi_clusters:
        return None

    # Compute Pearson correlation across all pairs in each cluster
    pair_corrs = []
    for outcomes in multi_clusters.values():
        n = len(outcomes)
        for i in range(n):
            for j in range(i + 1, n):
                pair_corrs.append((outcomes[i], outcomes[j]))

    if len(pair_corrs) < 10:
        return None

    # Pearson r for binary pairs
    x = [p[0] for p in pair_corrs]
    y = [p[1] for p in pair_corrs]
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    cov  = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / n
    sx   = (sum((v - mx) ** 2 for v in x) / n) ** 0.5
    sy   = (sum((v - my) ** 2 for v in y) / n) ** 0.5
    if sx <= 0 or sy <= 0:
        return None
    return round(cov / (sx * sy), 4)


def corr_by_cluster_size(rows: list[dict]) -> list[dict]:
    """
    Show how win rate varies by same-lineup cluster size.
    Useful for detecting whether larger clusters have different win rates (HR environment effect).
    """
    settled = [r for r in rows if r.get("hr_result") in ("0", "1")]
    if not settled:
        return []

    by_cluster: dict[tuple, list] = defaultdict(list)
    for r in settled:
        key = (r.get("date", ""), (r.get("team") or "").upper().strip())
        by_cluster[key].append(r)

    # Group rows by their cluster size
    size_groups: dict[int, list] = defaultdict(list)
    for cluster_rows in by_cluster.values():
        k = len(cluster_rows)
        size_groups[k].extend(cluster_rows)

    result = []
    for size in sorted(size_groups.keys()):
        members = size_groups[size]
        n_total = len(members)
        n_wins  = sum(1 for m in members if m.get("hr_result") == "1")
        win_pct = n_wins / n_total * 100 if n_total > 0 else 0.0
        result.append({
            "cluster_size": size,
            "n_picks":      n_total,
            "n_clusters":   n_total // size,
            "wins":         n_wins,
            "win_pct":      round(win_pct, 1),
        })
    return result
