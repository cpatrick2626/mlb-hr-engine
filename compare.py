"""
compare.py — Side-by-side comparison of v1 vs v2 MLB HR Engine outputs.

Usage:
    python compare.py                    # runs both engines for today
    python compare.py 2026-04-18         # specific date (overrides TARGET_DATE)
    python compare.py --skip-run         # use existing v1_data.json / v2_data.json

Requires both engines to be working (requirements installed in both dirs).
"""

import sys
import json
import os
import subprocess
import tempfile
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

PYTHON = sys.executable
BASE_DIR = Path(__file__).parent
V1_DIR = BASE_DIR / "mlb_hr_engine_v1"
V2_DIR = BASE_DIR / "mlb_hr_engine_v2"

console = Console(legacy_windows=False, highlight=False, width=200)


# ── Run engines ───────────────────────────────────────────────────────────────

def run_engine(version_dir: Path, json_path: str, target_date: str = None) -> bool:
    """Run one engine with --dump-json. Returns True on success."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if target_date:
        env["TARGET_DATE"] = target_date

    cmd = [PYTHON, str(version_dir / "main.py"), "--dump-json", json_path]
    label = version_dir.name

    console.print(f"[dim]Running {label}...[/dim]")
    result = subprocess.run(
        cmd,
        cwd=str(version_dir),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        console.print(f"[red]{label} exited with error:[/red]\n{result.stderr[-2000:]}")
        return False
    if not Path(json_path).exists():
        console.print(f"[red]{label} ran but did not produce {json_path}[/red]")
        console.print(f"[dim]stdout:[/dim] {result.stdout[-1000:]}")
        console.print(f"[dim]stderr:[/dim] {result.stderr[-1000:]}")
        return False
    return True


# ── Comparison logic ──────────────────────────────────────────────────────────

def _fmt_pct(val, decimals=1) -> str:
    if val is None:
        return "--"
    return f"{val*100:.{decimals}f}%"


def _delta_color(delta_pct: float) -> str:
    if delta_pct >= 3:
        return f"[bold green]+{delta_pct:.1f}pp[/bold green]"
    if delta_pct >= 1:
        return f"[green]+{delta_pct:.1f}pp[/green]"
    if delta_pct >= -1:
        return f"[dim]{delta_pct:+.1f}pp[/dim]"
    if delta_pct >= -3:
        return f"[red]{delta_pct:.1f}pp[/red]"
    return f"[bold red]{delta_pct:.1f}pp[/bold red]"


def _status(in_v1: bool, in_v2: bool) -> str:
    if in_v1 and in_v2:
        return "[green]BOTH[/green]"
    if in_v1:
        return "[yellow]V1 ONLY[/yellow]"
    if in_v2:
        return "[cyan]V2 ONLY[/cyan]"
    return "[dim]neither[/dim]"


def compare(v1_path: str, v2_path: str) -> None:
    with open(v1_path, encoding="utf-8") as f:
        v1 = json.load(f)
    with open(v2_path, encoding="utf-8") as f:
        v2 = json.load(f)

    date_str = v1.get("date", "?")
    v1_stats = v1.get("stats", {})
    v2_stats = v2.get("stats", {})

    # Build lookup dicts keyed by player_id
    def by_id(players):
        return {p["player_id"]: p for p in players if "player_id" in p}

    v1_all = by_id(v1.get("all_players", []))
    v2_all = by_id(v2.get("all_players", []))
    v1_ranked_ids = {p["player_id"]: p.get("rank", 99) for p in v1.get("ranked", [])}
    v2_ranked_ids = {p["player_id"]: p.get("rank", 99) for p in v2.get("ranked", [])}

    all_ids = sorted(v1_all.keys() | v2_all.keys())

    # ── Header panel ──────────────────────────────────────────────────────────
    console.print(Panel(
        f"[bold white]MLB HR ENGINE — v1 vs v2 COMPARISON[/bold white]\n"
        f"[dim]Date: {date_str}  |  "
        f"V1: {v1_stats.get('players',0)} players, {v1_stats.get('qualified',0)} picks  |  "
        f"V2: {v2_stats.get('players',0)} players, {v2_stats.get('qualified',0)} picks  |  "
        f"Odds: {v1.get('odds_source','?')}[/dim]",
        style="bold blue",
        box=box.DOUBLE_EDGE,
        expand=False,
    ))
    console.print()

    # ── Main comparison table — all players both versions modeled ─────────────
    console.print(Panel("[bold white]MODEL PROBABILITY COMPARISON — ALL SHARED PLAYERS[/bold white]",
                        style="blue", expand=False))

    shared_ids = [pid for pid in all_ids if pid in v1_all and pid in v2_all]
    # Sort by V2 model prob descending
    shared_ids.sort(key=lambda pid: v2_all[pid].get("model_prob", 0), reverse=True)

    table = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", expand=False, padding=(0, 1))
    table.add_column("Player",      width=22, no_wrap=True)
    table.add_column("Team",        width=5,  no_wrap=True)
    table.add_column("Opp",         width=5,  no_wrap=True)
    table.add_column("V1 Model%",   width=10, justify="right", no_wrap=True)
    table.add_column("V2 Model%",   width=10, justify="right", no_wrap=True)
    table.add_column("Delta",       width=12, justify="right", no_wrap=True)
    table.add_column("V1 EV%",      width=9,  justify="right", no_wrap=True)
    table.add_column("V2 EV%",      width=9,  justify="right", no_wrap=True)
    table.add_column("V1 Rank",     width=7,  justify="right", no_wrap=True)
    table.add_column("V2 Rank",     width=7,  justify="right", no_wrap=True)
    table.add_column("Pick status", width=10, no_wrap=True)

    rows_added = 0
    for pid in shared_ids[:50]:
        p1 = v1_all[pid]
        p2 = v2_all[pid]
        v1_prob = p1.get("model_prob", 0)
        v2_prob = p2.get("model_prob", 0)
        delta = (v2_prob - v1_prob) * 100
        in_v1 = pid in v1_ranked_ids
        in_v2 = pid in v2_ranked_ids
        v1_rank = str(v1_ranked_ids[pid]) if in_v1 else "--"
        v2_rank = str(v2_ranked_ids[pid]) if in_v2 else "--"
        v1_ev = p1.get("ev_pct")
        v2_ev = p2.get("ev_pct")

        def fmt_ev(ev):
            if ev is None:
                return "[dim]--[/dim]"
            color = "bold green" if ev >= 15 else ("green" if ev >= 8 else ("yellow" if ev >= 0 else "red"))
            sign = "+" if ev >= 0 else ""
            return f"[{color}]{sign}{ev:.1f}%[/{color}]"

        table.add_row(
            p2.get("player_name", ""),
            p2.get("team", ""),
            p2.get("opponent", ""),
            _fmt_pct(v1_prob),
            _fmt_pct(v2_prob),
            _delta_color(delta),
            fmt_ev(v1_ev),
            fmt_ev(v2_ev),
            v1_rank,
            v2_rank,
            _status(in_v1, in_v2),
        )
        rows_added += 1

    console.print(table)
    console.print(f"[dim]Showing top 50 by V2 model% ({len(shared_ids)} players in both)[/dim]\n")

    # ── Picks-only summary table ──────────────────────────────────────────────
    v1_qual_ids = {p["player_id"] for p in v1.get("qualified", [])}
    v2_qual_ids = {p["player_id"] for p in v2.get("qualified", [])}
    all_pick_ids = v1_qual_ids | v2_qual_ids

    if all_pick_ids:
        console.print(Panel("[bold white]QUALIFIED PICKS COMPARISON[/bold white]",
                            style="blue", expand=False))
        pick_table = Table(box=box.SIMPLE_HEAD, header_style="bold cyan", expand=False, padding=(0, 1))
        pick_table.add_column("Player",      width=22, no_wrap=True)
        pick_table.add_column("Team",        width=5,  no_wrap=True)
        pick_table.add_column("Odds",        width=7,  justify="right", no_wrap=True)
        pick_table.add_column("V1 Prob",     width=9,  justify="right", no_wrap=True)
        pick_table.add_column("V2 Prob",     width=9,  justify="right", no_wrap=True)
        pick_table.add_column("Delta",       width=12, justify="right", no_wrap=True)
        pick_table.add_column("V1 EV%",      width=9,  justify="right", no_wrap=True)
        pick_table.add_column("V2 EV%",      width=9,  justify="right", no_wrap=True)
        pick_table.add_column("Status",      width=10, no_wrap=True)

        def pick_sort_key(pid):
            p = v2_all.get(pid) or v1_all.get(pid, {})
            return p.get("model_prob", 0)

        for pid in sorted(all_pick_ids, key=pick_sort_key, reverse=True):
            p1 = v1_all.get(pid, {})
            p2 = v2_all.get(pid, {})
            ref = p2 or p1
            v1_prob = p1.get("model_prob", 0)
            v2_prob = p2.get("model_prob", 0)
            delta = (v2_prob - v1_prob) * 100
            in_v1 = pid in v1_qual_ids
            in_v2 = pid in v2_qual_ids
            odds = ref.get("best_american", "")
            odds_str = (f"+{odds}" if isinstance(odds, int) and odds > 0 else str(odds)) if odds else "--"
            v1_ev = p1.get("ev_pct")
            v2_ev = p2.get("ev_pct")

            def fmt_ev2(ev):
                if ev is None:
                    return "[dim]--[/dim]"
                color = "bold green" if ev >= 15 else ("green" if ev >= 8 else ("yellow" if ev >= 0 else "red"))
                sign = "+" if ev >= 0 else ""
                return f"[{color}]{sign}{ev:.1f}%[/{color}]"

            pick_table.add_row(
                ref.get("player_name", ""),
                ref.get("team", ""),
                odds_str,
                _fmt_pct(v1_prob) if v1_prob else "[dim]--[/dim]",
                _fmt_pct(v2_prob) if v2_prob else "[dim]--[/dim]",
                _delta_color(delta),
                fmt_ev2(v1_ev),
                fmt_ev2(v2_ev),
                _status(in_v1, in_v2),
            )

        console.print(pick_table)
        console.print()

    # ── Key differences summary ───────────────────────────────────────────────
    v1_only = v1_qual_ids - v2_qual_ids
    v2_only = v2_qual_ids - v1_qual_ids
    both = v1_qual_ids & v2_qual_ids

    def name(pid):
        p = v2_all.get(pid) or v1_all.get(pid, {})
        return p.get("player_name", str(pid))

    lines = ["[bold white]SUMMARY[/bold white]\n"]
    lines.append(f"  Picks in both  : [green]{len(both)}[/green]  — "
                 + (", ".join(name(p) for p in both) if both else "none"))
    lines.append(f"  V1 only picks  : [yellow]{len(v1_only)}[/yellow]  — "
                 + (", ".join(name(p) for p in v1_only) if v1_only else "none"))
    lines.append(f"  V2 only picks  : [cyan]{len(v2_only)}[/cyan]  — "
                 + (", ".join(name(p) for p in v2_only) if v2_only else "none"))

    if shared_ids:
        deltas = [(v2_all[p].get("model_prob", 0) - v1_all[p].get("model_prob", 0)) * 100
                  for p in shared_ids]
        avg_delta = sum(deltas) / len(deltas)
        up_ct = sum(1 for d in deltas if d > 0.5)
        dn_ct = sum(1 for d in deltas if d < -0.5)
        lines.append(f"\n  Model probability shift (v2 - v1):")
        lines.append(f"    Avg delta    : {avg_delta:+.2f} pp")
        lines.append(f"    V2 higher    : {up_ct} players")
        lines.append(f"    V2 lower     : {dn_ct} players")

    console.print(Panel("\n".join(lines), style="dim", expand=False))
    console.print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    skip_run = "--skip-run" in args
    args = [a for a in args if a != "--skip-run"]
    target_date = args[0] if args else None

    v1_json = str(BASE_DIR / "compare_v1.json")
    v2_json = str(BASE_DIR / "compare_v2.json")

    if not skip_run:
        ok1 = run_engine(V1_DIR, v1_json, target_date)
        ok2 = run_engine(V2_DIR, v2_json, target_date)
        if not ok1 or not ok2:
            console.print("[red]One or both engines failed — cannot compare.[/red]")
            sys.exit(1)
    else:
        if not Path(v1_json).exists() or not Path(v2_json).exists():
            console.print("[red]Missing compare_v1.json or compare_v2.json — run without --skip-run first.[/red]")
            sys.exit(1)
        console.print("[dim]Using existing JSON dumps.[/dim]\n")

    compare(v1_json, v2_json)


if __name__ == "__main__":
    main()
