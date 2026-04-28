"""
Codex HR Engine -- v4
=================================
Enhancements over v3:
  - Streamlit web dashboard:  streamlit run app.py
      Tab 1: Today's Picks table
      Tab 2: Parlays â€” Auto (2/3/4-leg top-EV combos) + Manual builder
      Tab 3: Performance â€” P&L history, CLV tracking
  - All v3 features: backtest framework, Statcast, platoon splits, P&L + CLV

Run:  python main.py          (CLI)
      streamlit run app.py    (web UI)
      python backtest.py 14   (backtest)
"""

import sys
import json
import traceback
from datetime import date, timedelta

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

import config
import pipeline
from clients import odds_api
from output import parlay as parlay_engine, display
from tracking import pnl as pnl_tracker, clv as clv_tracker

MODEL_VERSION = "v4"
console = Console(legacy_windows=False, highlight=False, width=180)


def run(dump_json_path: str = None):
    target_date = config.TARGET_DATE or date.today().strftime("%Y-%m-%d")
    quiet = dump_json_path is not None
    if not quiet:
        display.print_header(target_date)

    progress_console = Console(file=open(sys.stderr.fileno(), "w", closefd=False)) if quiet else None
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  transient=True, console=progress_console) as progress:
        task = progress.add_task("Loading...", total=None)

        def _cb(msg: str):
            progress.update(task, description=msg)

        try:
            data = pipeline.load_game_data(target_date, progress_cb=_cb)
        except Exception as e:
            console.print(f"[red]Pipeline error: {e}[/red]")
            traceback.print_exc()
            return

    if not data["games"]:
        if not quiet:
            console.print(f"[yellow]No games for {target_date}.[/yellow]")
        return

    all_players  = data["all_players"]
    all_by_model = data["all_by_model"]
    qualified    = data["qualified"]
    ranked       = data["ranked"]
    stats        = data["stats"]
    odds_source  = data["odds_source"]
    batter_data  = data["batter_data"]

    # â”€â”€ Tracking (CLI-only) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if ranked:
        logged = pnl_tracker.log_picks(ranked, model_version=MODEL_VERSION)
        clv_tracker.log_opening_lines(ranked)
        if logged:
            console.print(f"[dim]Logged {logged} picks -> tracking/picks_log.csv[/dim]\n")
        # Attempt CLV update with current odds — fills in closing lines if run near first pitch.
        # Safe to call multiple times: overwrites only today's rows.
        try:
            clv_results = clv_tracker.fetch_and_compute_clv(target_date)
            filled = sum(1 for r in clv_results if r.get("clv_pct"))
            if filled:
                console.print(f"[dim]CLV updated: {filled}/{len(clv_results)} picks have closing lines[/dim]\n")
        except Exception:
            pass
    try:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        yest_outcomes = pnl_tracker.fetch_yesterday_outcomes(MODEL_VERSION)
        if yest_outcomes:
            pnl_tracker.update_results(yesterday, yest_outcomes, MODEL_VERSION)
            console.print(f"[dim]Updated {len(yest_outcomes)} yesterday outcomes[/dim]\n")
    except Exception:
        pass

    # â”€â”€ Display â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not quiet:
        if odds_source == "none":
            display.print_no_odds_warning(api_key_set=bool(config.ODDS_API_KEY))
            odds_api.write_shopping_list(all_by_model[:30])
        else:
            console.print(f"[dim]Odds source: {odds_source} | Statcast: {len(batter_data)} batters[/dim]\n")

        display.print_top_picks(ranked)
        display.print_model_probabilities(all_by_model, top_n=20)

        if ranked:
            best_parlay = parlay_engine.build_best_parlay(ranked)
            display.print_parlay(best_parlay)

        display.print_pnl(pnl_tracker.pnl_summary(), clv_tracker.clv_summary())
        display.print_summary(stats)

    # â”€â”€ JSON dump (compare mode) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if dump_json_path:
        dump = {
            "version": "v2",
            "date": target_date,
            "stats": stats,
            "odds_source": odds_source,
            "all_players": pipeline.serializable(all_players),
            "qualified":   pipeline.serializable(qualified),
            "ranked":      pipeline.serializable(ranked),
        }
        with open(dump_json_path, "w", encoding="utf-8") as f:
            json.dump(dump, f)


if __name__ == "__main__":
    dump_path = None
    if "--dump-json" in sys.argv:
        idx = sys.argv.index("--dump-json")
        if idx + 1 < len(sys.argv):
            dump_path = sys.argv[idx + 1]
    try:
        run(dump_json_path=dump_path)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]"); sys.exit(0)
    except Exception as e:
        console.print(f"\n[red bold]Fatal error:[/red bold] {e}")
        traceback.print_exc(); sys.exit(1)

