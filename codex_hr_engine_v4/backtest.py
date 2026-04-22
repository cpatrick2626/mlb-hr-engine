"""
Codex HR Engine v3 â€” Backtest Runner
====================================
Scores the v3 model against actual historical game results and prints
a calibration report showing how well predicted probabilities match reality.

Usage:
  python backtest.py            # last 14 days
  python backtest.py 30         # last N days
  python backtest.py 2026-04-01 2026-04-17   # explicit date range

Output:
  - Calibration table: predicted HR% vs actual HR% per probability bucket
  - Brier score (model sharpness metric)
  - Simulated P&L at various probability thresholds

Note:
  Uses current season stats (not stats-as-of-date), so early-season results
  have minimal look-ahead bias â€” most 2026 PA are < 30, so prior-year stats
  are used anyway. Later in the season, treat calibration as approximate.
"""

import sys
from datetime import date, timedelta

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from clients import statcast as statcast_client
from backtest.outcomes import get_game_results, get_date_range
from backtest.runner import score_date
from backtest.calibration import calibration_report

console = Console(legacy_windows=False, highlight=False, width=180)


def parse_args() -> tuple[str, str]:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    today = date.today()

    if len(args) == 0:
        # Default: last 14 days
        start = (today - timedelta(days=14)).isoformat()
        end   = (today - timedelta(days=1)).isoformat()
    elif len(args) == 1 and args[0].isdigit():
        # N days back
        n     = int(args[0])
        start = (today - timedelta(days=n)).isoformat()
        end   = (today - timedelta(days=1)).isoformat()
    elif len(args) == 2:
        start, end = args[0], args[1]
    else:
        console.print("[red]Usage: python backtest.py [days] or [start_date end_date][/red]")
        sys.exit(1)

    return start, end


def run():
    start_date, end_date = parse_args()
    dates = get_date_range(start_date, end_date)

    console.print(f"\n[bold blue]CODEX HR ENGINE v4 â€” BACKTEST[/bold blue]")
    console.print(f"[dim]Date range: {start_date} to {end_date}  ({len(dates)} days)[/dim]\n")

    # Pre-fetch Statcast once (cached for the whole session)
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  transient=True) as progress:
        task = progress.add_task("Loading Statcast leaderboard...", total=None)
        batter_data  = statcast_client.get_batter_statcast()
        pitcher_data = statcast_client.get_pitcher_statcast()
        progress.update(task, description=f"Statcast: {len(batter_data)} batters, {len(pitcher_data)} pitchers")

    console.print(f"[dim]Statcast loaded: {len(batter_data)} batters, {len(pitcher_data)} pitchers[/dim]\n")

    all_rows = []
    skipped_dates = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  transient=True) as progress:
        task = progress.add_task("", total=len(dates))

        for i, d in enumerate(dates):
            progress.update(task, description=f"Processing {d} ({i+1}/{len(dates)})...",
                            completed=i)
            try:
                results = get_game_results(d)
                if not results:
                    skipped_dates.append(d)
                    continue

                # Add game_date to each row for the report
                for r in results:
                    r["game_date"] = d

                scored = score_date(d, results, batter_data, pitcher_data)
                all_rows.extend(scored)
                progress.update(task, description=f"{d}: {len(scored)} batters scored")
            except Exception as e:
                skipped_dates.append(d)
                console.print(f"[yellow]Skipped {d}: {e}[/yellow]")

        progress.update(task, completed=len(dates))

    if skipped_dates:
        console.print(f"[dim]Skipped {len(skipped_dates)} date(s) with no games or errors.[/dim]\n")

    if not all_rows:
        console.print("[red]No data collected â€” cannot generate report.[/red]")
        sys.exit(1)

    console.print(f"[dim]Collected {len(all_rows)} batter-game records across "
                  f"{len(dates) - len(skipped_dates)} dates.[/dim]\n")

    calibration_report(all_rows, f"{start_date} to {end_date}")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red bold]Fatal error:[/red bold] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

