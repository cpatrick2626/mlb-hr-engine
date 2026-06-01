"""
Codex HR Engine
==========================
Entry point â€” orchestrates the full pipeline:

  1. Pull today's MLB schedule + lineups + probable pitchers
  2. Build HR probability for each starting batter
  3. Fetch market odds (requires ODDS_API_KEY in .env)
  4. Compute EV%, Edge%, Kelly bet size
  5. Apply filters
  6. Rank picks by composite score
  7. Print results + best parlay

Usage:
  python main.py               # runs for today
  TARGET_DATE=2025-04-20 python main.py  # specific date override

Requirements:
  pip install -r requirements.txt
  Copy .env.example â†’ .env and add your ODDS_API_KEY
"""

import sys
import json
import traceback
from datetime import date

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rapidfuzz import fuzz, process as fuzz_process

import config
from clients import mlb_stats, odds_api
from clients import weather as weather_client
from data.park_factors import get_park
from engine import market as mkt, probability as prob, ev as ev_engine, sizing, filters
from output import ranker, parlay as parlay_engine, display

console = Console(legacy_windows=False, highlight=False)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Player Profile Builder
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_player_profile(
    player_id: int,
    player_name: str,
    lineup_spot: int,
    team: str,
    opponent: str,
    home_team: str,
    pitcher: dict,
) -> dict | None:
    """
    Fetch stats and compute model HR probability for one batter.
    Returns None if insufficient data.
    """
    # Fetch hitting stats
    season_stats = mlb_stats.get_player_season_stats(player_id)
    recent_stats = mlb_stats.get_player_recent_stats(player_id)

    season_pa = int(season_stats.get("plateAppearances", 0))
    season_hr = int(season_stats.get("homeRuns", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))

    # Skip pitchers and players with zero PAs (e.g., catchers warming up)
    if season_pa == 0 and recent_pa == 0:
        return None

    # Compute base HR rate (weighted, regressed)
    hr_rate = prob.base_hr_rate(season_stats, recent_stats)
    exp_pa = prob.expected_pa(lineup_spot)

    # Park factor
    pk_factor = prob.park_factor(home_team, batter_is_home=(team == home_team))

    # Pitcher factor
    pitcher_stats: dict = {}
    pitcher_name = pitcher.get("name", "TBD")
    pitcher_id = pitcher.get("id")
    pitcher_hand = ""
    if pitcher_id:
        pitcher_stats = mlb_stats.get_pitcher_season_stats(pitcher_id)
        info = mlb_stats.get_player_info(pitcher_id)
        pitcher_hand = info.get("pitchHand", {}).get("code", "")
    pit_factor = prob.pitcher_hr_factor(pitcher_stats)

    # Weather factor (cached per park)
    park_data = get_park(home_team)
    is_dome = home_team in weather_client.DOME_TEAMS
    weather_data = weather_client.get_game_weather(park_data["lat"], park_data["lon"])
    w_factor = (
        weather_client.temp_factor(weather_data["temp_f"])
        * weather_client.wind_factor(weather_data["wind_mph"], weather_data["wind_deg"], is_dome)
    )
    w_factor = max(0.80, min(1.20, w_factor))

    # Handedness (batter info)
    batter_info = mlb_stats.get_player_info(player_id)
    batter_side = batter_info.get("batSide", {}).get("code", "")
    h_factor = prob.handedness_factor(batter_side, pitcher_hand)

    # Final model probability
    model_probability = prob.game_hr_probability(
        hr_rate, exp_pa,
        p_factor=pit_factor,
        pk_factor=pk_factor,
        w_factor=w_factor,
        h_factor=h_factor,
    )

    return {
        "player_id": player_id,
        "player_name": player_name,
        "team": team,
        "opponent": opponent,
        "home_team": home_team,
        "pitcher_name": pitcher_name,
        "pitcher_id": pitcher_id,
        "lineup_spot": lineup_spot,
        "expected_pa": round(exp_pa, 1),
        "season_pa": season_pa,
        "season_hr": season_hr,
        "recent_pa": recent_pa,
        "hr_rate": round(hr_rate, 5),
        "park_factor": round(pk_factor, 3),
        "pitcher_factor": round(pit_factor, 3),
        "weather_factor": round(w_factor, 3),
        "handedness_factor": round(h_factor, 3),
        "model_prob": round(model_probability, 4),
        "weather": weather_data,
    }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Market Matching
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def match_odds(player: dict, all_props: list[dict]) -> dict:
    """
    Fuzzy-match player name to market prop lines.
    Returns enriched player dict with odds data.
    """
    if not all_props:
        return player

    prop_names = [p["player_name"] for p in all_props]
    match = fuzz_process.extractOne(
        player["player_name"],
        prop_names,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=82,
    )
    if not match:
        return player

    matched_name = match[0]
    matching_props = [p for p in all_props if p["player_name"] == matched_name]
    if not matching_props:
        return player

    prices = [p["price"] for p in matching_props]
    summary = mkt.market_summary(prices)

    best = max(matching_props, key=lambda x: x["price"])
    player["best_american"] = best["price"]
    player["best_bookmaker"] = best.get("bookmaker", "")
    player["all_prices"] = prices
    player["n_books"] = summary.get("n_books", 1)
    player["market_no_vig_prob"] = round(summary.get("no_vig_prob_best", 0), 4)
    player["market_implied_avg"] = round(summary.get("implied_prob_avg", 0), 4)

    return player


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# EV + Sizing
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def enrich_with_ev(player: dict) -> dict:
    """Add EV%, Edge%, confidence, bet size to a player profile."""
    if not player.get("best_american"):
        return player

    dec_odds = mkt.american_to_decimal(player["best_american"])
    model_p = player["model_prob"]
    market_p = player.get("market_no_vig_prob", 0)

    player["ev_pct"] = ev_engine.expected_value_pct(model_p, dec_odds)
    player["edge_pct"] = ev_engine.edge_pct(model_p, market_p)
    player["confidence"] = prob.confidence_score(
        player.get("season_pa", 0),
        player.get("recent_pa", 0),
        model_p,
        market_p,
    )
    player["bet_dollars"] = sizing.bet_dollars(model_p, player["best_american"])

    return player


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Main Pipeline
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _serializable(players: list) -> list:
    """Strip non-JSON-serializable fields (e.g. raw weather dict)."""
    safe = []
    for p in players:
        row = {k: v for k, v in p.items() if k != "weather" and not isinstance(v, (set, bytes))}
        safe.append(row)
    return safe


def run(dump_json_path: str = None) -> None:
    target_date = config.TARGET_DATE or date.today().strftime("%Y-%m-%d")
    quiet = dump_json_path is not None
    if not quiet:
        display.print_header(target_date)

    all_players: list[dict] = []
    stats = {"games": 0, "players": 0, "qualified": 0, "filtered": 0}
    odds_source = "none"

    progress_console = Console(file=open(sys.stderr.fileno(), "w", closefd=False)) if quiet else None
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=progress_console,
    ) as progress:

        # â”€â”€ Step 1: Schedule â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        task = progress.add_task("Fetching today's MLB schedule...", total=None)
        try:
            games = mlb_stats.get_today_schedule(target_date)
        except Exception as e:
            console.print(f"[red]Failed to fetch schedule: {e}[/red]")
            return
        progress.update(task, description=f"Found {len(games)} games")
        stats["games"] = len(games)

        if not games:
            if not quiet:
                console.print(f"[yellow]No MLB games found for {target_date}.[/yellow]")
            return

        # â”€â”€ Step 2: Market Odds â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        progress.update(task, description="Fetching market odds...")
        all_props: list[dict] = []
        try:
            all_props, odds_source = odds_api.get_hr_odds_all_games()
            if odds_source != "none":
                progress.update(task, description=f"Odds loaded from {odds_source} ({len(all_props)} lines)")
        except Exception as e:
            console.print(f"[yellow]Odds error: {e}[/yellow]")

        # â”€â”€ Step 3: Build Player Profiles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for game in games:
            home = game["home_team"]
            away = game["away_team"]
            home_pitcher = game.get("home_pitcher", {})
            away_pitcher = game.get("away_pitcher", {})

            # Home batters face away pitcher; away batters face home pitcher
            batter_groups = [
                (game["home_lineup"], home, away, away_pitcher),
                (game["away_lineup"], away, home, home_pitcher),
            ]

            for lineup, team, opp, opp_pitcher in batter_groups:
                if not lineup:
                    # If lineup not yet posted, skip this group (could enhance
                    # with projected lineups in a future version)
                    continue

                for batter in lineup:
                    pid = batter.get("id")
                    name = batter.get("name", "Unknown")
                    spot = batter.get("lineup_spot")

                    if not pid:
                        continue

                    progress.update(task, description=f"Building profile: {name}")
                    try:
                        profile = build_player_profile(
                            player_id=pid,
                            player_name=name,
                            lineup_spot=spot,
                            team=team,
                            opponent=opp,
                            home_team=home,
                            pitcher=opp_pitcher,
                        )
                        if profile:
                            all_players.append(profile)
                    except Exception:
                        # Log but continue â€” one failed profile shouldn't stop the run
                        pass

        stats["players"] = len(all_players)

        # â”€â”€ Step 4: Match Odds + Compute EV â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        progress.update(task, description="Matching odds and computing EV...")
        for p in all_players:
            match_odds(p, all_props)
            enrich_with_ev(p)

        # â”€â”€ Step 5: Filter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        qualified: list[dict] = []
        for p in all_players:
            passed, reasons = filters.apply_filters(p)
            p["filter_reasons"] = reasons
            p["soft_flags"] = filters.soft_flags(p)
            if passed:
                qualified.append(p)
            else:
                stats["filtered"] += 1

        stats["qualified"] = len(qualified)

        progress.update(task, description="Ranking picks...")

    # â”€â”€ Step 6: Rank â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ranked = ranker.rank_picks(qualified)
    all_by_model = ranker.rank_all_by_model(all_players)

    # â”€â”€ Step 7: Output â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not quiet:
        if odds_source == "none":
            display.print_no_odds_warning(api_key_set=bool(config.ODDS_API_KEY))
            shopping_list = all_by_model[:30]
            odds_api.write_shopping_list(shopping_list)
            console.print(
                "[bold yellow]Shopping list written ->[/bold yellow] "
                "[bold white]manual_odds.csv[/bold white]\n\n"
                "  1. Open [bold]manual_odds.csv[/bold] in Excel or Notepad\n"
                "  2. Fill in the [bold]american_odds[/bold] column (e.g. [cyan]+285[/cyan]) "
                "from DraftKings, FanDuel, etc.\n"
                "  3. Run [bold]python main.py[/bold] again -- the engine will load your odds\n"
            )
        else:
            console.print(f"[dim]Odds source: {odds_source}[/dim]\n")

        display.print_top_picks(ranked)
        display.print_model_probabilities(all_by_model, top_n=20)

        if ranked:
            best_parlay = parlay_engine.build_best_parlay(ranked)
            display.print_parlay(best_parlay)

        display.print_summary(stats)

    # â”€â”€ JSON dump (compare mode) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if dump_json_path:
        data = {
            "version": "v1",
            "date": target_date,
            "stats": stats,
            "odds_source": odds_source,
            "all_players": _serializable(all_players),
            "qualified": _serializable(qualified),
            "ranked": _serializable(ranked),
        }
        with open(dump_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)


if __name__ == "__main__":
    dump_path = None
    if "--dump-json" in sys.argv:
        idx = sys.argv.index("--dump-json")
        if idx + 1 < len(sys.argv):
            dump_path = sys.argv[idx + 1]
    try:
        run(dump_json_path=dump_path)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red bold]Fatal error:[/red bold] {e}")
        traceback.print_exc()
        sys.exit(1)

