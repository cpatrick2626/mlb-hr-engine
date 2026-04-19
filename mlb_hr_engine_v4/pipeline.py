"""
Shared data pipeline — used by both main.py (CLI) and app.py (Streamlit).

Call load_game_data() once per session. It fetches everything and returns
a single dict that both the CLI display and the Streamlit UI can consume.
"""

from datetime import date, timedelta
from rapidfuzz import fuzz, process as fuzz_process

import config
from clients import mlb_stats, odds_api
from clients import weather as weather_client
from clients import statcast as statcast_client
from data.park_factors import get_park
from engine import market as mkt, probability as prob, ev as ev_engine, sizing, filters
from output import ranker, parlay as parlay_engine


# ── Core helpers (same logic as v3 main.py, extracted here) ──────────────────

def _build_player_profile(
    player_id, player_name, lineup_spot, team, opponent,
    home_team, pitcher, batter_data, pitcher_data,
):
    season_stats = mlb_stats.get_player_season_stats(player_id)
    recent_stats = mlb_stats.get_player_recent_stats(player_id)
    season_pa = int(season_stats.get("plateAppearances", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))
    if season_pa == 0 and recent_pa == 0:
        return None

    raw_rate   = prob.base_hr_rate(season_stats, recent_stats)
    power_mult = statcast_client.batter_power_multiplier(player_id, batter_data)
    hr_rate    = prob.statcast_blended_rate(raw_rate, power_mult, season_pa)
    sc_summary = statcast_client.statcast_summary(player_id, batter_data)

    exp_pa    = prob.expected_pa(lineup_spot)
    pk_factor = prob.park_factor(home_team, team == home_team)

    pitcher_id   = pitcher.get("id")
    pitcher_name = pitcher.get("name", "TBD")
    pitcher_hand = ""
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
        "has_statcast": player_id in batter_data,
        "barrel_pct": sc_summary["barrel_pct"],
        "exit_velo": sc_summary["exit_velo"], "hard_hit": sc_summary["hard_hit"],
        "park_factor": round(pk_factor, 3), "pitcher_factor": round(pit_factor, 3),
        "weather_factor": round(w_factor, 3), "platoon_factor": round(plat_factor, 3),
        "model_prob": round(model_prob, 4), "weather": weather,
    }


def _match_odds(player, all_props):
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


def _enrich_with_ev(player):
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


# ── Public API ────────────────────────────────────────────────────────────────

def load_game_data(
    target_date: str = None,
    progress_cb=None,       # optional callable(str) for status messages
) -> dict:
    """
    Full pipeline: schedule → Statcast → per-player profiles → odds → EV → filters → rank.
    Returns a dict consumed by both main.py and app.py.
    """
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    game_date = target_date or (config.TARGET_DATE or date.today().strftime("%Y-%m-%d"))

    _cb("Fetching schedule...")
    games = mlb_stats.get_today_schedule(game_date)

    _cb("Fetching odds...")
    try:
        all_props, odds_source = odds_api.get_hr_odds_all_games()
    except Exception:
        all_props, odds_source = [], "none"

    _cb("Loading Statcast...")
    batter_data  = statcast_client.get_batter_statcast()
    pitcher_data = statcast_client.get_pitcher_statcast()

    all_players = []
    for game in games:
        home, away = game["home_team"], game["away_team"]
        for lineup, team, opp, opp_pitcher in [
            (game["home_lineup"], home, away, game.get("away_pitcher", {})),
            (game["away_lineup"], away, home, game.get("home_pitcher", {})),
        ]:
            if not lineup:
                continue
            for batter in lineup:
                pid  = batter.get("id")
                name = batter.get("name", "Unknown")
                if not pid:
                    continue
                _cb(f"Profiling {name}...")
                try:
                    p = _build_player_profile(
                        pid, name, batter.get("lineup_spot"),
                        team, opp, home, opp_pitcher,
                        batter_data, pitcher_data,
                    )
                    if p:
                        all_players.append(p)
                except Exception:
                    pass

    _cb("Computing EV...")
    for p in all_players:
        _match_odds(p, all_props)
        _enrich_with_ev(p)

    qualified = []
    for p in all_players:
        passed, reasons = filters.apply_filters(p)
        p["filter_reasons"] = reasons
        p["soft_flags"]     = filters.soft_flags(p)
        if passed:
            qualified.append(p)

    ranked      = ranker.rank_picks(qualified)
    all_by_model = ranker.rank_all_by_model(all_players)

    # Build team → players map for manual parlay builder
    team_players: dict[str, list[dict]] = {}
    for p in all_players:
        if p.get("best_american"):
            team_players.setdefault(p["team"], []).append(p)
    for team in team_players:
        team_players[team].sort(key=lambda x: x.get("model_prob", 0), reverse=True)

    # Auto parlay combos
    auto_parlays = parlay_engine.build_auto_parlays(ranked)

    return {
        "date":         game_date,
        "games":        games,
        "all_players":  all_players,
        "all_by_model": all_by_model,
        "qualified":    qualified,
        "ranked":       ranked,
        "odds_source":  odds_source,
        "all_props":    all_props,
        "batter_data":  batter_data,
        "team_players": team_players,
        "auto_parlays": auto_parlays,
        "stats": {
            "games":     len(games),
            "players":   len(all_players),
            "qualified": len(qualified),
            "filtered":  len(all_players) - len(qualified),
        },
    }
