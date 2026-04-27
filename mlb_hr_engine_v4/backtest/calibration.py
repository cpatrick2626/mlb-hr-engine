"""
Calibration analysis and P&L simulation for backtest results.

Calibration asks: when the model says 20%, do batters actually HR ~20% of the time?
A well-calibrated model's predictions match reality across all probability buckets.

P&L simulation shows what betting returns would look like if you had placed
flat $10 bets on every pick above a threshold. Uses average market odds per
probability bucket as a conservative estimate (since we don't have historical odds).
"""

import math
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console(legacy_windows=False, highlight=False, width=180)

# Probability buckets
BUCKETS = [
    (0.00, 0.05,  "0-5%"),
    (0.05, 0.10,  "5-10%"),
    (0.10, 0.15,  "10-15%"),
    (0.15, 0.20,  "15-20%"),
    (0.20, 0.25,  "20-25%"),
    (0.25, 0.30,  "25-30%"),
    (0.30, 1.00,  "30%+"),
]

# Conservative average market odds estimate per bucket (American)
# Based on typical HR prop pricing: low prob = higher odds, high prob = lower odds
BUCKET_AVG_ODDS = {
    "0-5%":   1400,
    "5-10%":   800,
    "10-15%":  500,
    "15-20%":  375,
    "20-25%":  300,
    "25-30%":  240,
    "30%+":    200,
}

FLAT_BET = 10.0  # dollars per pick in P&L simulation


def calibration_report(rows: list[dict], date_range: str) -> None:
    """Print full calibration report to console."""
    if not rows:
        console.print("[yellow]No data to calibrate.[/yellow]")
        return

    total = len(rows)
    hr_count = sum(1 for r in rows if r.get("hit_hr"))
    actual_rate = hr_count / total if total else 0
    biased_count = sum(1 for r in rows if r.get("is_biased"))
    bias_note = (f"  ⚠ {biased_count} records with season_pa>100 (look-ahead risk)"
                 if biased_count else "")

    console.print(Panel(
        f"[bold white]BACKTEST CALIBRATION REPORT[/bold white]\n"
        f"[dim]Date range: {date_range}  |  "
        f"Total batter-games: {total}  |  "
        f"Actual HR rate: {actual_rate*100:.2f}%{bias_note}[/dim]",
        style="bold blue",
        box=box.DOUBLE_EDGE,
        expand=False,
    ))
    console.print()

    # ── Calibration table ─────────────────────────────────────────────────────
    console.print(Panel("[bold white]MODEL CALIBRATION — Predicted vs Actual[/bold white]",
                        style="blue", expand=False))

    cal_table = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", expand=False, padding=(0, 1))
    cal_table.add_column("Prob Bucket",   width=12, no_wrap=True)
    cal_table.add_column("# Batters",     width=10, justify="right", no_wrap=True)
    cal_table.add_column("# HRs",         width=8,  justify="right", no_wrap=True)
    cal_table.add_column("Avg Model%",    width=12, justify="right", no_wrap=True)
    cal_table.add_column("Actual HR%",    width=12, justify="right", no_wrap=True)
    cal_table.add_column("Diff",          width=10, justify="right", no_wrap=True)
    cal_table.add_column("Brier contrib", width=14, justify="right", no_wrap=True)

    brier_sum = 0.0
    for lo, hi, label in BUCKETS:
        bucket = [r for r in rows if lo <= r.get("model_prob", 0) < hi]
        if not bucket:
            cal_table.add_row(label, "0", "--", "--", "--", "--", "--")
            continue
        n        = len(bucket)
        hits     = sum(1 for r in bucket if r.get("hit_hr"))
        avg_pred = sum(r.get("model_prob", 0) for r in bucket) / n
        act_rate = hits / n
        diff     = act_rate - avg_pred
        brier    = sum((r.get("model_prob", 0) - int(r.get("hit_hr", False)))**2
                       for r in bucket)
        brier_sum += brier

        diff_color = "green" if abs(diff) < 0.03 else ("yellow" if abs(diff) < 0.07 else "red")
        cal_table.add_row(
            label,
            str(n),
            str(hits),
            f"{avg_pred*100:.1f}%",
            f"{act_rate*100:.1f}%",
            f"[{diff_color}]{diff*100:+.1f}pp[/{diff_color}]",
            f"{brier:.2f}",
        )

    console.print(cal_table)
    brier_score = brier_sum / total if total else 0
    console.print(f"[dim]Brier Score: {brier_score:.4f}  "
                  f"(lower = better calibration; 0.0 = perfect, ~0.030 = typical for HR props)[/dim]\n")

    # ── P&L simulation table ──────────────────────────────────────────────────
    console.print(Panel("[bold white]SIMULATED P&L — Flat $10 per pick at estimated odds[/bold white]",
                        style="blue", expand=False))
    console.print("[dim]Uses conservative market-odds estimate per bucket. "
                  "Actual results may differ based on real line shopping.[/dim]\n")

    pnl_table = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", expand=False, padding=(0, 1))
    pnl_table.add_column("Min Model%",   width=12, no_wrap=True)
    pnl_table.add_column("# Bets",       width=8,  justify="right", no_wrap=True)
    pnl_table.add_column("# Won",        width=7,  justify="right", no_wrap=True)
    pnl_table.add_column("Win Rate",     width=10, justify="right", no_wrap=True)
    pnl_table.add_column("Avg Odds",     width=10, justify="right", no_wrap=True)
    pnl_table.add_column("Total Bet",    width=10, justify="right", no_wrap=True)
    pnl_table.add_column("Net P&L",      width=10, justify="right", no_wrap=True)
    pnl_table.add_column("ROI",          width=8,  justify="right", no_wrap=True)

    thresholds = [0.05, 0.10, 0.15, 0.20, 0.25]
    for thresh in thresholds:
        picks = [r for r in rows if r.get("model_prob", 0) >= thresh]
        if not picks:
            continue
        wins      = sum(1 for r in picks if r.get("hit_hr"))
        total_bet = len(picks) * FLAT_BET
        # Use bucket-based odds estimate for each pick
        pnl = 0.0
        for r in picks:
            mp = r.get("model_prob", 0)
            odds = _est_odds(mp)
            if r.get("hit_hr"):
                pnl += (odds / 100) * FLAT_BET if odds > 0 else (100 / abs(odds)) * FLAT_BET
            else:
                pnl -= FLAT_BET
        roi = pnl / total_bet * 100 if total_bet > 0 else 0
        avg_odds = int(sum(_est_odds(r.get("model_prob", 0)) for r in picks) / len(picks))

        roi_color = "bold green" if roi > 5 else ("green" if roi > 0 else ("yellow" if roi > -10 else "red"))
        pnl_color = "green" if pnl > 0 else "red"
        pnl_table.add_row(
            f">= {thresh*100:.0f}%",
            str(len(picks)),
            str(wins),
            f"{wins/len(picks)*100:.1f}%",
            f"+{avg_odds}" if avg_odds > 0 else str(avg_odds),
            f"${total_bet:.0f}",
            f"[{pnl_color}]${pnl:+.2f}[/{pnl_color}]",
            f"[{roi_color}]{roi:+.1f}%[/{roi_color}]",
        )

    console.print(pnl_table)
    console.print()

    # ── Top performers vs misses ──────────────────────────────────────────────
    _print_top_performers(rows)


def _est_odds(model_prob: float) -> int:
    """Estimate market odds (American) for a given model probability."""
    for lo, hi, label in BUCKETS:
        if lo <= model_prob < hi:
            return BUCKET_AVG_ODDS[label]
    return BUCKET_AVG_ODDS["30%+"]


def _print_top_performers(rows: list[dict]) -> None:
    """Show high-model-prob picks that hit and high-prob misses."""
    high_prob = [r for r in rows if r.get("model_prob", 0) >= 0.15]
    if not high_prob:
        return

    hits   = sorted([r for r in high_prob if r.get("hit_hr")],
                    key=lambda x: x.get("model_prob", 0), reverse=True)
    misses = sorted([r for r in high_prob if not r.get("hit_hr")],
                    key=lambda x: x.get("model_prob", 0), reverse=True)

    console.print(Panel("[bold white]HIGH-PROBABILITY PICKS (>= 15% model)[/bold white]",
                        style="dim blue", expand=False))

    perf_table = Table(box=box.SIMPLE, header_style="bold dim cyan", expand=False, padding=(0, 1))
    perf_table.add_column("Date",       width=12, no_wrap=True)
    perf_table.add_column("Player",     width=22, no_wrap=True)
    perf_table.add_column("Team",       width=5,  no_wrap=True)
    perf_table.add_column("Vs Pitcher", width=20, no_wrap=True)
    perf_table.add_column("Model%",     width=9,  justify="right", no_wrap=True)
    perf_table.add_column("Result",     width=8,  justify="center", no_wrap=True)

    shown = 0
    for r in (hits[:10] + misses[:10]):
        result_str = "[green]HR[/green]" if r.get("hit_hr") else "[red]No HR[/red]"
        perf_table.add_row(
            r.get("game_date", "--"),
            r.get("player_name", ""),
            r.get("team", ""),
            r.get("pitcher_name", "TBD"),
            f"{r.get('model_prob', 0)*100:.1f}%",
            result_str,
        )
        shown += 1
    console.print(perf_table)
    console.print()
