"""
Codex HR Engine -- v2
=================================
Enhancements over v1:
  - Statcast barrel%/exit velocity blended into power estimate
  - HR/FB pitcher factor (better than raw HR/9)
  - Real platoon splits from MLB Stats API
  - Statcast pitcher contact quality (barrel% against, EV against)
  - P&L tracker (auto-logs picks, auto-fetches yesterday outcomes)
  - Closing Line Value (CLV) tracking

Run:  python main.py
"""

import sys
import json
import traceback
from datetime import date, timedelta

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rapidfuzz import fuzz, process as fuzz_process

import config
from clients import mlb_stats, odds_api
from clients import weather as weather_client
from clients import statcast as statcast_client
from data.park_factors import get_park
from engine import market as mkt, probability as prob, ev as ev_engine, sizing, filters
from output import ranker, parlay as parlay_engine, display
from tracking import pnl as pnl_tracker, clv as clv_tracker

MODEL_VERSION = "v2"
console = Console(legacy_windows=False, highlight=False, width=180)


def build_player_profile(
    player_id, player_name, lineup_spot, team, opponent,
    home_team, pitcher, batter_data, pitcher_data,
):
    season_stats = mlb_stats.get_player_season_stats(player_id)
    recent_stats = mlb_stats.get_player_recent_stats(player_id)
    season_pa = int(season_stats.get("plateAppearances", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))
    if season_pa == 0 and recent_pa == 0:
        return None

    raw_rate     = prob.base_hr_rate(season_stats, recent_stats)
    power_mult   = statcast_client.batter_power_multiplier(player_id, batter_data)
    has_statcast = player_id in batter_data
    hr_rate      = prob.statcast_blended_rate(raw_rate, power_mult, season_pa)
    sc_summary   = statcast_client.statcast_summary(player_id, batter_data)

    exp_pa    = prob.expected_pa(lineup_spot)
    pk_factor = prob.park_factor(home_team, team == home_team)

    pitcher_id    = pitcher.get("id")
    pitcher_name  = pitcher.get("name", "TBD")
    pitcher_hand  = ""
    pitcher_stats = {}
    if pitcher_id:
        pitcher_stats = mlb_stats.get_pitcher_season_stats(pitcher_id)
        info = mlb_stats.get_player_info(pitcher_id)
        pitcher_hand = info.get("pitchHand", {}).get("code", "")

    hr_fb_fac  = prob.pitcher_hr_factor(pitcher_stats)
    sc_pit_fac = statcast_client.pitcher_contact_suppressor(pitcher_id or 0, pitcher_data)
    pit_factor = prob.pitcher_combined_factor(hr_fb_fac, sc_pit_fac)

    park_data = get_park(home_team)
    is_dome   = home_team in weather_client.DOME_TEAMS
    weather   = weather_client.get_game_weather(park_data["lat"], park_data["lon"])
    w_factor  = max(0.80, min(1.20,
        weather_client.temp_factor(weather["temp_f"])
        * weather_client.wind_factor(weather["wind_mph"], weather["wind_deg"], is_dome)
    ))

    batter_info = mlb_stats.get_player_info(player_id)
    batter_side = batter_info.get("batSide", {}).get("code", "")
    splits      = mlb_stats.get_player_platoon_splits(player_id)
    plat_factor = prob.platoon_factor(splits, pitcher_hand, batter_side, season_pa)

    model_prob = prob.game_hr_probability(
        hr_rate, exp_pa,
        pk_factor=pk_factor, pitcher_fac=pit_factor,
        w_factor=w_factor, plat_factor=plat_factor,
    )

    return {
        "player_id": player_id, "player_name": player_name,
        "team": team, "opponent": opponent, "home_team": home_team,
        "pitcher_name": pitcher_name, "pitcher_id": pitcher_id,
        "lineup_spot": lineup_spot, "expected_pa": round(exp_pa, 1),
        "season_pa": season_pa, "season_hr": int(season_stats.get("homeRuns", 0)),
        "recent_pa": recent_pa, "hr_rate": round(hr_rate, 5),
        "raw_hr_rate": round(raw_rate, 5), "statcast_power_mult": power_mult,
        "has_statcast": has_statcast, "barrel_pct": sc_summary["barrel_pct"],
        "exit_velo": sc_summary["exit_velo"], "hard_hit": sc_summary["hard_hit"],
        "park_factor": round(pk_factor, 3), "pitcher_factor": round(pit_factor, 3),
        "weather_factor": round(w_factor, 3), "platoon_factor": round(plat_factor, 3),
        "model_prob": round(model_prob, 4), "weather": weather,
    }


def match_odds(player, all_props):
    if not all_props:
        return player
    prop_names = [p["player_name"] for p in all_props]
    match = fuzz_process.extractOne(
        player["player_name"], prop_names,
        scorer=fuzz.token_sort_ratio, score_cutoff=82,
    )
    if not match:
        return player
    matched_name = match[0]
    matches = [p for p in all_props if p["player_name"] == matched_name]
    if not matches:
        return player
    prices  = [p["price"] for p in matches]
    summary = mkt.market_summary(prices)
    best    = max(matches, key=lambda x: x["price"])
    player.update({
        "best_american": best["price"], "best_bookmaker": best.get("bookmaker", ""),
        "all_prices": prices, "n_books": summary.get("n_books", 1),
        "market_no_vig_prob": round(summary.get("no_vig_prob_best", 0), 4),
        "market_implied_avg": round(summary.get("implied_prob_avg", 0), 4),
    })
    return player


def enrich_with_ev(player):
    if not player.get("best_american"):
        return player
    dec_odds = mkt.american_to_decimal(player["best_american"])
    model_p  = player["model_prob"]
    market_p = player.get("market_no_vig_prob", 0)
    player["ev_pct"]     = ev_engine.expected_value_pct(model_p, dec_odds)
    player["edge_pct"]   = ev_engine.edge_pct(model_p, market_p)
    player["confidence"] = prob.confidence_score(
        player.get("season_pa", 0), player.get("recent_pa", 0),
        model_p, market_p, has_statcast=player.get("has_statcast", False),
    )
    player["bet_dollars"] = sizing.bet_dollars(model_p, player["best_american"])
    return player


def _serializable(players: list) -> list:
    """Strip non-JSON-serializable fields."""
    safe = []
    for p in players:
        row = {k: v for k, v in p.items() if k != "weather" and not isinstance(v, (set, bytes))}
        safe.append(row)
    return safe


def run(dump_json_path: str = None):
    target_date = config.TARGET_DATE or date.today().strftime("%Y-%m-%d")
    quiet = dump_json_path is not None
    if not quiet:
        display.print_header(target_date)
    all_players = []
    stats = {"games": 0, "players": 0, "qualified": 0, "filtered": 0}
    odds_source = "none"

    progress_console = Console(file=open(sys.stderr.fileno(), "w", closefd=False)) if quiet else None
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  transient=True, console=progress_console) as progress:
        task = progress.add_task("Fetching schedule...", total=None)

        try:
            games = mlb_stats.get_today_schedule(target_date)
        except Exception as e:
            console.print(f"[red]Schedule error: {e}[/red]"); return
        stats["games"] = len(games)
        if not games:
            if not quiet:
                console.print(f"[yellow]No games for {target_date}.[/yellow]")
            return

        progress.update(task, description="Fetching odds...")
        try:
            all_props, odds_source = odds_api.get_hr_odds_all_games()
        except Exception:
            all_props, odds_source = [], "none"

        progress.update(task, description="Loading Statcast data...")
        batter_data  = statcast_client.get_batter_statcast()
        pitcher_data = statcast_client.get_pitcher_statcast()
        progress.update(task, description=f"Statcast: {len(batter_data)} batters, {len(pitcher_data)} pitchers")

        for game in games:
            home, away = game["home_team"], game["away_team"]
            home_pitcher = game.get("home_pitcher", {})
            away_pitcher = game.get("away_pitcher", {})
            for lineup, team, opp, opp_pitcher in [
                (game["home_lineup"], home, away, away_pitcher),
                (game["away_lineup"], away, home, home_pitcher),
            ]:
                if not lineup:
                    continue
                for batter in lineup:
                    pid  = batter.get("id")
                    name = batter.get("name", "Unknown")
                    if not pid:
                        continue
                    progress.update(task, description=f"Profiling: {name}")
                    try:
                        p = build_player_profile(
                            pid, name, batter.get("lineup_spot"),
                            team, opp, home, opp_pitcher,
                            batter_data, pitcher_data,
                        )
                        if p:
                            all_players.append(p)
                    except Exception:
                        pass

        stats["players"] = len(all_players)
        progress.update(task, description="Computing EV...")
        for p in all_players:
            match_odds(p, all_props)
            enrich_with_ev(p)

        qualified = []
        for p in all_players:
            passed, reasons = filters.apply_filters(p)
            p["filter_reasons"] = reasons
            p["soft_flags"]     = filters.soft_flags(p)
            if passed:
                qualified.append(p)
            else:
                stats["filtered"] += 1
        stats["qualified"] = len(qualified)
        progress.update(task, description="Ranking...")

    ranked       = ranker.rank_picks(qualified)
    all_by_model = ranker.rank_all_by_model(all_players)

    if ranked:
        logged = pnl_tracker.log_picks(ranked, model_version=MODEL_VERSION)
        clv_tracker.log_opening_lines(ranked)
        if logged:
            console.print(f"[dim]Logged {logged} picks -> tracking/picks_log.csv[/dim]\n")
    try:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        yest_outcomes = pnl_tracker.fetch_yesterday_outcomes(MODEL_VERSION)
        if yest_outcomes:
            pnl_tracker.update_results(yesterday, yest_outcomes, MODEL_VERSION)
            console.print(f"[dim]Updated {len(yest_outcomes)} yesterday outcomes[/dim]\n")
    except Exception:
        pass

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
        data = {
            "version": "v2",
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
        console.print("\n[yellow]Interrupted.[/yellow]"); sys.exit(0)
    except Exception as e:
        console.print(f"\n[red bold]Fatal error:[/red bold] {e}")
        traceback.print_exc(); sys.exit(1)

