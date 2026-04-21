"""
Rich console output — tables, panels, and summary.
"""

from datetime import date

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

import config
from engine.market import american_to_decimal
from output.parlay import parlay_bet_size

# legacy_windows=False forces modern Unicode rendering on Windows
console = Console(legacy_windows=False, highlight=False, width=180)


def _fmt_american(odds: int) -> str:
    return f"+{odds}" if odds > 0 else str(odds)


def _color_ev(ev: float) -> str:
    if ev >= 15:
        return f"[bold green]+{ev:.1f}%[/bold green]"
    if ev >= 8:
        return f"[green]+{ev:.1f}%[/green]"
    if ev >= 0:
        return f"[yellow]+{ev:.1f}%[/yellow]"
    return f"[red]{ev:.1f}%[/red]"


def _color_edge(edge: float) -> str:
    if edge >= 8:
        return f"[bold green]+{edge:.1f}%[/bold green]"
    if edge >= 5:
        return f"[green]+{edge:.1f}%[/green]"
    if edge >= 3:
        return f"[yellow]+{edge:.1f}%[/yellow]"
    return f"[red]{edge:.1f}%[/red]"


def _color_conf(conf: float) -> str:
    if conf >= 70:
        return f"[bold green]{conf:.0f}[/bold green]"
    if conf >= 50:
        return f"[green]{conf:.0f}[/green]"
    if conf >= 35:
        return f"[yellow]{conf:.0f}[/yellow]"
    return f"[red]{conf:.0f}[/red]"


def print_header(target_date: str = None) -> None:
    day = target_date or date.today().strftime("%Y-%m-%d")
    console.print(Panel(
        f"[bold white]MLB HOME RUN PROP BETTING ENGINE[/bold white]\n"
        f"[dim]Date: {day}  |  Bankroll: ${config.BANKROLL:,.0f}  |  Kelly Fraction: {config.KELLY_FRACTION:.0%}[/dim]",
        style="bold blue",
        box=box.DOUBLE_EDGE,
        expand=False,
    ))
    console.print()


def print_top_picks(ranked_picks: list[dict]) -> None:
    if not ranked_picks:
        console.print("[yellow]No qualified picks today (all filtered out).[/yellow]")
        return

    console.print(Panel(
        "[bold white]TOP HR BETS — RANKED BY EV%[/bold white]",
        style="blue",
        expand=False,
    ))

    table = Table(
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold cyan",
        expand=False,
        padding=(0, 1),
    )

    table.add_column("#",       style="bold", width=3,  justify="right", no_wrap=True)
    table.add_column("Player",  width=22, no_wrap=True)
    table.add_column("Team",    width=5,  no_wrap=True)
    table.add_column("Opp",     width=5,  no_wrap=True)
    table.add_column("Odds",    width=7,  justify="right", no_wrap=True)
    table.add_column("Model%",  width=8,  justify="right", no_wrap=True)
    table.add_column("Mkt%",    width=7,  justify="right", no_wrap=True)
    table.add_column("Edge",    width=9,  justify="right", no_wrap=True)
    table.add_column("EV%",     width=9,  justify="right", no_wrap=True)
    table.add_column("Bet $",   width=7,  justify="right", no_wrap=True)
    table.add_column("Conf",    width=5,  justify="right", no_wrap=True)
    table.add_column("Score",   width=6,  justify="right", no_wrap=True)

    for p in ranked_picks:
        flags = p.get("soft_flags", [])
        name = p["player_name"]
        if flags:
            name = f"{name} [dim]{'  '.join(flags)}[/dim]"

        table.add_row(
            str(p.get("rank", "?")),
            name,
            p.get("team", ""),
            p.get("opponent", ""),
            _fmt_american(p.get("best_american", 0)),
            f"{p.get('model_prob', 0)*100:.1f}%",
            f"{p.get('market_no_vig_prob', 0)*100:.1f}%",
            _color_edge(p.get("edge_pct", 0)),
            _color_ev(p.get("ev_pct", 0)),
            f"${p.get('bet_dollars', 0):.0f}",
            _color_conf(p.get("confidence", 0)),
            f"{p.get('score', 0):.1f}",
        )

    console.print(table)
    console.print()


def print_model_probabilities(all_players: list[dict], top_n: int = 20) -> None:
    """v2: includes Statcast barrel% and power multiplier columns."""
    console.print(Panel(
        f"[bold white]MODEL HR PROBABILITIES — TOP {top_n} [dim](v2: Statcast enhanced)[/dim][/bold white]",
        style="dim blue",
        expand=False,
    ))

    table = Table(box=box.SIMPLE, header_style="bold dim cyan", expand=True)
    table.add_column("Player",      min_width=20, no_wrap=True)
    table.add_column("Team",        min_width=4,  no_wrap=True)
    table.add_column("Opp Pitcher", min_width=18, no_wrap=True)
    table.add_column("Spot",        min_width=4,  justify="right", no_wrap=True)
    table.add_column("HR/PA",       min_width=7,  justify="right", no_wrap=True)
    table.add_column("Brl%",        min_width=6,  justify="right", no_wrap=True)
    table.add_column("EV",          min_width=5,  justify="right", no_wrap=True)
    table.add_column("Pwr",         min_width=5,  justify="right", no_wrap=True)
    table.add_column("Park",        min_width=6,  justify="right", no_wrap=True)
    table.add_column("Ptch",        min_width=6,  justify="right", no_wrap=True)
    table.add_column("Model%",      min_width=7,  justify="right", no_wrap=True)

    sorted_players = sorted(all_players, key=lambda x: x.get("model_prob", 0), reverse=True)

    for p in sorted_players[:top_n]:
        pf = p.get("park_factor", 1.0)
        pf_str = (f"[green]{pf:.2f}[/green]" if pf >= 1.05 else
                  f"[red]{pf:.2f}[/red]" if pf <= 0.93 else f"{pf:.2f}")
        pitf = p.get("pitcher_factor", 1.0)
        pitf_str = (f"[green]{pitf:.2f}[/green]" if pitf >= 1.05 else
                    f"[red]{pitf:.2f}[/red]" if pitf <= 0.85 else f"{pitf:.2f}")

        pwr = p.get("statcast_power_mult", 1.0)
        pwr_str = (f"[green]{pwr:.2f}[/green]" if pwr >= 1.15 else
                   f"[red]{pwr:.2f}[/red]" if pwr <= 0.85 else f"{pwr:.2f}")

        brl = p.get("barrel_pct", "")
        brl_str = f"[bold]{brl}[/bold]" if brl else "[dim]--[/dim]"

        ev_str = p.get("exit_velo", "") or "[dim]--[/dim]"
        spot_str = str(p.get("lineup_spot")) if p.get("lineup_spot") else "?"

        table.add_row(
            p.get("player_name", ""),
            p.get("team", ""),
            p.get("pitcher_name", "TBD"),
            spot_str,
            f"{p.get('hr_rate', 0)*100:.2f}%",
            brl_str,
            ev_str,
            pwr_str,
            pf_str,
            pitf_str,
            f"[bold]{p.get('model_prob', 0)*100:.1f}%[/bold]",
        )

    console.print(table)
    console.print()


def print_pnl(summary: dict, clv: dict) -> None:
    """Show running P&L and CLV summary panel."""
    if not summary and not clv:
        return

    lines = ["[bold white]RUNNING PERFORMANCE[/bold white]\n"]

    if summary:
        roi_color = "green" if summary.get("roi_pct", 0) >= 0 else "red"
        lines += [
            f"  Picks logged  : {summary.get('total_picks', 0)}  "
            f"({summary.get('wins', 0)}W / {summary.get('losses', 0)}L / "
            f"{summary.get('pending', 0)} pending)",
            f"  Win rate      : {summary.get('win_rate', 0)*100:.1f}%",
            f"  Total wagered : ${summary.get('total_wagered', 0):,.2f}",
            f"  Net P&L       : [{roi_color}]${summary.get('total_profit', 0):+,.2f}[/{roi_color}]",
            f"  ROI           : [{roi_color}]{summary.get('roi_pct', 0):+.1f}%[/{roi_color}]",
        ]

    if clv:
        clv_color = "green" if clv.get("avg_clv_pct", 0) > 0 else "red"
        verdict = clv.get("verdict", "N/A")
        verdict_color = {"SHARP": "green", "NEUTRAL": "yellow", "SOFT": "red"}.get(verdict, "white")
        lines += [
            "",
            f"  CLV picks     : {clv.get('picks_with_clv', 0)}",
            f"  Avg CLV       : [{clv_color}]{clv.get('avg_clv_pct', 0):+.2f}%[/{clv_color}]",
            f"  Beat close    : {clv.get('pct_beating_close', 0):.1f}%",
            f"  Verdict       : [{verdict_color}]{verdict}[/{verdict_color}]",
        ]

    console.print(Panel("\n".join(lines), style="dim", expand=False,
                        title="[dim]TRACKER[/dim]"))
    console.print()


def print_parlay(parlay: dict, bankroll: float = None) -> None:
    if not parlay:
        return

    bankroll = bankroll or config.BANKROLL
    bet = parlay_bet_size(parlay, bankroll)

    lines: list[str] = [
        f"[bold white]{parlay['n_legs']}-LEG HR PARLAY[/bold white]\n"
    ]
    for i, leg in enumerate(parlay["legs"], 1):
        lines.append(
            f"  {i}. [cyan]{leg['player_name']}[/cyan] ({leg.get('team','')}) "
            f"HR  {_fmt_american(leg['best_american'])}  "
            f"[dim]model: {leg['model_prob']*100:.1f}%[/dim]"
        )

    lines.append("")
    lines.append(
        f"  Combined odds : [bold yellow]{_fmt_american(parlay['combined_american'])}[/bold yellow]"
        f"  ({parlay['combined_decimal']:.1f}x)"
    )
    lines.append(
        f"  Model prob    : [bold]{parlay['combined_prob_pct']:.2f}%[/bold]"
    )
    lines.append(
        f"  Parlay EV%    : {_color_ev(parlay['ev_pct'])}"
    )
    if bet >= config.MIN_BET_DOLLARS:
        lines.append(f"  Suggested bet : [bold green]${bet:.0f}[/bold green]  [dim](1/8 Kelly)[/dim]")
    else:
        lines.append(f"  [dim]Bet size below minimum — skip or flat-bet small.[/dim]")

    console.print(Panel(
        "\n".join(lines),
        style="yellow",
        box=box.ROUNDED,
        title="[bold yellow]BEST PARLAY[/bold yellow]",
        expand=False,
    ))
    console.print()


def print_no_odds_warning(api_key_set: bool = False) -> None:
    if api_key_set:
        msg = (
            "[yellow]Odds API is unreachable (corporate network/firewall).\n"
            "Use [bold]manual_odds.csv[/bold] to enter odds from your phone or home network.\n"
            "Model probabilities are shown below -- fill in odds to get EV/edge rankings.[/yellow]"
        )
    else:
        msg = (
            "[yellow]No ODDS_API_KEY set -- market comparison disabled.\n"
            "Add your key to [bold].env[/bold] "
            "(free key at https://the-odds-api.com).\n"
            "Showing model probabilities only.[/yellow]"
        )
    console.print(Panel(msg, style="yellow", expand=False))
    console.print()


def print_summary(stats: dict) -> None:
    console.print(
        f"[dim]Games processed: {stats.get('games',0)}  |  "
        f"Players evaluated: {stats.get('players',0)}  |  "
        f"Qualified bets: {stats.get('qualified',0)}  |  "
        f"Filtered out: {stats.get('filtered',0)}[/dim]"
    )
    console.print()
