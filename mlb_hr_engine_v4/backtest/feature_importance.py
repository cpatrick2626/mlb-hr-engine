"""
Feature importance analysis for the HR prediction model.

Computes point-biserial correlations between each model factor and actual HR
outcomes, then ranks factors by predictive power.  Run after the backtest
collects rows to understand which signals genuinely separate HR games from
non-HR games — not just which factors move model_prob, but which predict reality.

Usage:
  from backtest.feature_importance import report, rank_factors
  rank_factors(all_rows)   # returns sorted list of dicts
  report(all_rows)         # prints rich table to console
"""

import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console(legacy_windows=False, highlight=False, width=180)

# (field_name, display_label, direction)
# direction: "positive" = higher value predicts more HRs
#            "negative" = higher value predicts fewer HRs
FACTORS = [
    # Primary model output
    ("model_prob",        "Model Probability",         "positive"),
    ("hr_rate",           "Raw HR Rate",               "positive"),
    # Batter composite + individual signals
    ("power_mult",        "Statcast Power Multiplier", "positive"),
    ("barrel_rate",       "Barrel Rate",               "positive"),
    ("fb_pct",            "Fly Ball %",                "positive"),
    ("sweet_spot_pct",    "Sweet Spot %",              "positive"),
    ("pull_pct",          "Pull %",                    "positive"),
    ("exit_velocity_avg", "Exit Velocity",             "positive"),
    ("hard_hit_pct",      "Hard Hit %",                "positive"),
    ("xslg",              "xSLG",                      "positive"),
    # Pitcher signals
    ("pit_factor",        "Pitcher Factor",            "positive"),
    ("hr9",               "Pitcher HR/9",              "positive"),
    ("hr_fb_fac",         "Pitcher HR/FB Factor",      "positive"),
    ("k_gb_fac",          "Pitcher K+GB Suppressor",   "negative"),
    # Matchup & environment
    ("pk_factor",         "Park Factor",               "positive"),
    ("plat_factor",       "Platoon Factor",            "positive"),
    ("streak_fac",        "Streak Factor",             "positive"),
    ("k_fac",             "Batter K-Rate Factor",      "negative"),
    # Data quantity
    ("season_pa",         "Season PA",                 "positive"),
]

# Factors from the same "hard contact" cluster — warn when 3+ appear in top 10
_HARD_CONTACT_CLUSTER = {"barrel_rate", "hard_hit_pct", "exit_velocity_avg", "xslg"}


def rank_factors(rows: list[dict], min_n: int = 30) -> list[dict]:
    """
    Compute point-biserial correlations between each factor field and hit_hr.
    Returns list sorted by |correlation| descending.

    min_n: minimum non-None observations required to include a factor.
    """
    results = []
    for field, label, direction in FACTORS:
        vals, outcomes = [], []
        for r in rows:
            v = r.get(field)
            o = r.get("hit_hr")
            if v is None or o is None:
                continue
            try:
                vals.append(float(v))
                outcomes.append(int(bool(o)))
            except (TypeError, ValueError):
                continue
        if len(vals) < min_n:
            continue
        corr  = _point_biserial(vals, outcomes)
        n_hr  = sum(outcomes)
        results.append({
            "field":     field,
            "label":     label,
            "direction": direction,
            "corr":      round(corr, 4),
            "n":         len(vals),
            "n_hr":      n_hr,
            "hr_rate":   round(n_hr / len(vals), 3),
            "strength":  _strength(corr),
            "rank":      0,
        })

    results.sort(key=lambda x: abs(x["corr"]), reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i
    return results


def report(rows: list[dict], min_n: int = 30) -> None:
    """Print feature importance ranking table to console."""
    ranked  = rank_factors(rows, min_n=min_n)
    n_total = len(rows)
    n_hr    = sum(1 for r in rows if r.get("hit_hr"))
    hr_pct  = n_hr / n_total * 100 if n_total else 0.0

    console.print(Panel(
        f"[bold white]FEATURE IMPORTANCE — Point-Biserial Correlations with HR Outcome[/bold white]\n"
        f"[dim]Batter-games: {n_total}  |  Overall HR rate: {hr_pct:.2f}%  |  "
        f"Min observations per factor: {min_n}[/dim]",
        style="bold blue", box=box.DOUBLE_EDGE, expand=False,
    ))

    if not ranked:
        console.print("[yellow]Insufficient data for feature importance analysis "
                      f"(need {min_n}+ non-null obs per factor).[/yellow]\n")
        return

    t = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", expand=False, padding=(0, 1))
    t.add_column("Rank",      width=6,  justify="right", no_wrap=True)
    t.add_column("Factor",    width=28, no_wrap=True)
    t.add_column("Corr",      width=9,  justify="right", no_wrap=True)
    t.add_column("Strength",  width=12, no_wrap=True)
    t.add_column("Direction", width=13, no_wrap=True)
    t.add_column("HR%",       width=8,  justify="right", no_wrap=True)
    t.add_column("N",         width=8,  justify="right", no_wrap=True)

    for r in ranked:
        s_color = (
            "bold green" if r["strength"] == "Strong"
            else "green" if r["strength"] == "Moderate"
            else "yellow" if r["strength"] == "Weak"
            else "dim"
        )
        c_color = "green" if r["corr"] >= 0 else "red"
        dir_str = "↑ more HRs" if r["direction"] == "positive" else "↓ fewer HRs"
        t.add_row(
            str(r["rank"]),
            r["label"],
            f"[{c_color}]{r['corr']:+.4f}[/{c_color}]",
            f"[{s_color}]{r['strength']}[/{s_color}]",
            dir_str,
            f"{r['hr_rate']*100:.1f}%",
            str(r["n"]),
        )

    console.print(t)

    # Redundancy warning: flag hard-contact cluster over-representation
    top_cluster = [r for r in ranked[:10] if r["field"] in _HARD_CONTACT_CLUSTER]
    if len(top_cluster) >= 3:
        names = ", ".join(r["label"] for r in top_cluster)
        console.print(
            f"\n[yellow dim]Redundancy note: {names} belong to the same 'hard contact' cluster "
            f"(pairwise r~0.65–0.80). Their combined weight represents one independent dimension. "
            f"Barrel% is the canonical representative; the others add marginal signal.[/yellow dim]"
        )

    console.print()


# ── Internal helpers ───────────────────────────────────────────────────────────

def _point_biserial(vals: list[float], outcomes: list[int]) -> float:
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
        return 0.0 if sd == 0 else (m1 - m0) / sd * math.sqrt(n1 * n0 / n ** 2)
    except statistics.StatisticsError:
        return 0.0


def _strength(corr: float) -> str:
    a = abs(corr)
    if a >= 0.25:
        return "Strong"
    if a >= 0.12:
        return "Moderate"
    if a >= 0.04:
        return "Weak"
    return "Negligible"
