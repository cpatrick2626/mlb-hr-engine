"""
Shared data pipeline — used by both main.py (CLI) and app.py (Streamlit).

Call load_game_data() once per session. It fetches everything and returns
a single dict that both the CLI display and the Streamlit UI can consume.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from rapidfuzz import fuzz, process as fuzz_process

import config
from clients import mlb_stats, odds_api
from clients import weather as weather_client
from clients import statcast as statcast_client
from data.park_factors import get_park
from engine import market as mkt, probability as prob, ev as ev_engine, sizing, filters
from output import ranker, parlay as parlay_engine
from output.parlay import build_profile_parlays


# ── Core helpers (same logic as v3 main.py, extracted here) ──────────────────

def _build_player_profile(
    player_id, player_name, lineup_spot, team, opponent,
    home_team, pitcher, batter_data, pitcher_data,
    batter_bb_data=None, pitcher_bb_data=None,
):
    season_stats    = mlb_stats.get_player_season_stats(player_id)
    recent_stats    = mlb_stats.get_player_recent_stats(player_id)
    short_form      = mlb_stats.get_player_short_form(player_id, days=14)
    season_pa = int(season_stats.get("plateAppearances", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))
    if season_pa == 0 and recent_pa == 0:
        return None

    raw_rate   = prob.base_hr_rate(season_stats, recent_stats)
    power_mult = statcast_client.batter_power_multiplier(player_id, batter_data, batter_bb_data)
    sc_stats   = dict(batter_data.get(player_id) or {})
    sc_pa      = sc_stats.get("pa", 0)
    sc_source  = sc_stats.get("statcast_source", "current")
    hr_rate    = prob.statcast_blended_rate(
        raw_rate, power_mult, season_pa,
        statcast_pa=sc_pa, statcast_source=sc_source,
    )
    sc_summary = statcast_client.statcast_summary(player_id, batter_data, batter_bb_data)

    # Derived contact-quality fields used by profile-based parlay scoring
    xba_raw    = sc_stats.get("xba")
    xslg_raw   = sc_stats.get("xslg")
    actual_slg = float(season_stats.get("sluggingPercentage", 0) or 0)
    xiso       = (round(float(xslg_raw) - float(xba_raw), 3)
                  if (xslg_raw is not None and xba_raw is not None) else None)
    xslg_diff  = (round(float(xslg_raw) - actual_slg, 3)
                  if xslg_raw is not None else None)

    streak_fac = prob.hot_streak_factor(short_form, season_stats)
    k_fac      = prob.batter_k_suppressor(season_stats)

    exp_pa    = prob.expected_pa(lineup_spot)
    pk_factor = prob.park_factor(home_team, team == home_team)
    pk_factor = prob.fly_ball_adjusted_park_factor(pk_factor, season_stats)

    pitcher_id   = pitcher.get("id")
    pitcher_name = pitcher.get("name", "TBD")
    pitcher_hand = ""
    pitcher_stats = {}
    recent_pitcher_stats = {}
    pitcher_days_rest = 5
    if pitcher_id:
        pitcher_stats        = mlb_stats.get_pitcher_season_stats(pitcher_id)
        recent_pitcher_stats = mlb_stats.get_pitcher_recent_stats(pitcher_id)
        pitcher_days_rest    = mlb_stats.get_pitcher_days_rest(pitcher_id)
        info = mlb_stats.get_player_info(pitcher_id)
        pitcher_hand = info.get("pitchHand", {}).get("code", "")

    hr_fb_fac      = prob.pitcher_hr_factor(pitcher_stats)
    sc_pit_fac     = statcast_client.pitcher_contact_suppressor(pitcher_id or 0, pitcher_data, pitcher_bb_data)
    k_gb_fac       = prob.pitcher_k_gb_suppressor(pitcher_stats)
    pit_factor     = prob.pitcher_combined_factor(hr_fb_fac, sc_pit_fac, k_gb_fac)
    recent_pit_fac = prob.pitcher_recent_factor(recent_pitcher_stats)
    pit_factor     = max(0.55, min(1.60, pit_factor * recent_pit_fac))
    fatigue_fac    = prob.pitcher_fatigue_factor(pitcher_days_rest)
    pit_factor     = max(0.55, min(1.60, pit_factor * fatigue_fac))

    # Pitcher HR/9 for confidence threshold flag
    pit_ip_str = pitcher_stats.get("inningsPitched", "0.0")
    try:
        parts  = str(pit_ip_str).split(".")
        pit_ip = int(parts[0]) + int(parts[1]) / 3.0 if len(parts) > 1 else float(pit_ip_str)
    except Exception:
        pit_ip = 0.0
    pit_hrs  = int(pitcher_stats.get("homeRuns", 0))
    pitcher_hr9 = round((pit_hrs / pit_ip) * 9.0, 2) if pit_ip >= 5 else 0.0

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

    # Stage 6: batter × pitcher interaction term (non-additive matchup synergy).
    # When an elite power hitter (high Statcast) faces a hittable pitcher (high
    # contact quality allowed), the combined effect exceeds simple multiplication.
    batter_excess  = max(0.0, power_mult - 1.0)
    pitcher_excess = max(0.0, sc_pit_fac - 1.0)
    interaction    = batter_excess * pitcher_excess * 0.35

    adjusted_rate = hr_rate * streak_fac * k_fac * (1.0 + interaction)
    model_prob = prob.game_hr_probability(
        adjusted_rate, exp_pa,
        pk_factor=pk_factor, pitcher_fac=pit_factor,
        w_factor=w_factor, plat_factor=plat_factor,
    )
    # When lineup hasn't been posted (spot is None), the player may not start.
    # 0.82 discount ≈ 82% probability of actually being in the lineup.
    if not lineup_spot:
        model_prob = round(model_prob * 0.82, 4)

    return {
        "player_id": player_id, "player_name": player_name,
        "team": team, "opponent": opponent, "home_team": home_team,
        "pitcher_name": pitcher_name, "pitcher_id": pitcher_id,
        "lineup_spot": lineup_spot, "expected_pa": round(exp_pa, 1),
        "season_pa": season_pa, "season_hr": int(season_stats.get("homeRuns", 0)),
        "recent_pa": recent_pa, "hr_rate": round(hr_rate, 5),
        "raw_hr_rate": round(raw_rate, 5), "statcast_power_mult": power_mult,
        "has_statcast": (player_id in batter_data
                         and batter_data[player_id].get("statcast_source", "current") == "current"),
        "statcast_source": sc_source,
        "barrel_pct": sc_summary["barrel_pct"],
        "exit_velo": sc_summary["exit_velo"], "hard_hit": sc_summary["hard_hit"],
        "sweet_spot_pct": sc_summary["sweet_spot_pct"],
        "fb_pct": sc_summary["fb_pct"], "gb_pct": sc_summary["gb_pct"],
        "ld_pct": sc_summary["ld_pct"], "pull_pct": sc_summary["pull_pct"],
        "oppo_pct": sc_summary["oppo_pct"],
        "park_factor": round(pk_factor, 3), "pitcher_factor": round(pit_factor, 3),
        "pitcher_days_rest": pitcher_days_rest, "fatigue_factor": round(fatigue_fac, 3),
        "weather_factor": round(w_factor, 3), "platoon_factor": round(plat_factor, 3),
        "model_prob": round(model_prob, 4), "weather": weather,
        "pitcher_hr9": pitcher_hr9,
        "short_form_pa": int(short_form.get("plateAppearances", 0)),
        "short_form_hr": int(short_form.get("homeRuns", 0)),
        "streak_factor": round(streak_fac, 3),
        "k_factor": round(k_fac, 3),
        "avg_launch_angle": sc_summary.get("avg_launch_angle"),
        "xslg": sc_summary.get("xslg"),
        "xba": xba_raw,
        "xiso": xiso,
        "xslg_diff": xslg_diff,
        "actual_slg": round(actual_slg, 3),
    }


def _build_odds_lookup(all_props):
    """Pre-build a lookup structure for O(1) odds matching."""
    if not all_props:
        return {}, []

    # Group props by player name
    odds_by_player = {}
    for prop in all_props:
        name = prop["player_name"]
        if name not in odds_by_player:
            odds_by_player[name] = []
        odds_by_player[name].append(prop)

    # Create list of unique player names for fuzzy matching
    unique_names = list(odds_by_player.keys())

    return odds_by_player, unique_names


def _match_odds(player, odds_lookup, unique_names):
    """Match odds using pre-built lookup structure (O(1) after fuzzy match)."""
    if not odds_lookup:
        return player

    # Fuzzy match against unique names only (much smaller list)
    match = fuzz_process.extractOne(
        player["player_name"], unique_names,
        scorer=fuzz.token_sort_ratio, score_cutoff=82,
    )
    if not match:
        return player

    matched_name = match[0]
    matches = odds_lookup.get(matched_name, [])
    if not matches:
        return player

    prices  = [p["price"] for p in matches]
    summary = mkt.market_summary(prices)
    best    = max(matches, key=lambda x: x["price"])
    fd_matches = [p for p in matches if p.get("bookmaker") == "fanduel"]
    fd_odds = max(fd_matches, key=lambda x: x["price"])["price"] if fd_matches else None
    player.update({
        "best_american": best["price"], "best_bookmaker": best.get("bookmaker", ""),
        "all_prices": prices, "n_books": summary.get("n_books", 1),
        "market_no_vig_prob": round(summary.get("no_vig_prob_best", 0), 4),
        "market_implied_avg": round(summary.get("implied_prob_avg", 0), 4),
        "fanduel_american": fd_odds,
    })
    return player


def _enrich_with_ev(player):
    if not player.get("best_american"):
        return player
    dec_odds = mkt.american_to_decimal(player["best_american"])
    model_p  = player["model_prob"]
    market_p = player.get("market_no_vig_prob", 0)

    # edge_pct uses the full model signal (odds-independent)
    player["edge_pct"] = ev_engine.edge_pct(model_p, market_p)

    # EV% is capped so long-shot odds (+2000, +3000) can't amplify a small
    # probability gap into absurd triple-digit EV values.
    # Cap: model cannot claim more than 1.4x the market's true probability.
    # At 1.4x the math produces max ~45% EV regardless of odds length.
    ev_model_p = min(model_p, market_p * 1.4) if market_p > 0 else model_p
    player["ev_pct"] = ev_engine.expected_value_pct(ev_model_p, dec_odds)

    # Extract raw barrel rate for threshold bonus
    barrel_raw  = float(str(player.get("barrel_pct", "0")).replace("%", "") or 0) / 100.0
    pitcher_hr9 = float(player.get("pitcher_hr9", 0) or 0)

    player["confidence"] = prob.confidence_score(
        player.get("season_pa", 0), player.get("recent_pa", 0),
        model_p, market_p,
        has_statcast=player.get("has_statcast", False),
        barrel_rate=barrel_raw,
        pitcher_hr9=pitcher_hr9,
    )
    player["bet_dollars"] = sizing.bet_dollars(model_p, player["best_american"])
    return player


def serializable(players: list) -> list:
    """Strip non-JSON-serializable fields (weather dict, sets, bytes) for JSON dumps."""
    return [
        {k: v for k, v in p.items() if k != "weather" and not isinstance(v, (set, bytes))}
        for p in players
    ]


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
    batter_data   = statcast_client.get_batter_statcast()
    pitcher_data  = statcast_client.get_pitcher_statcast()
    batter_bb     = statcast_client.get_batter_batted_ball()
    pitcher_bb    = statcast_client.get_pitcher_batted_ball()

    # Collect tasks first so roster fallbacks run before the parallel phase.
    tasks: list[tuple] = []
    for game in games:
        home, away = game["home_team"], game["away_team"]
        for lineup, team, opp, team_id, opp_pitcher in [
            (game["home_lineup"], home, away, game.get("home_team_id"), game.get("away_pitcher", {})),
            (game["away_lineup"], away, home, game.get("away_team_id"), game.get("home_pitcher", {})),
        ]:
            if not lineup:
                if team_id:
                    lineup = mlb_stats.get_team_active_roster(team_id)
                if not lineup:
                    continue
            for batter in lineup:
                pid  = batter.get("id")
                name = batter.get("name", "Unknown")
                if not pid:
                    continue
                tasks.append((pid, name, batter.get("lineup_spot"), team, opp, home, opp_pitcher))

    _cb(f"Building profiles for {len(tasks)} players...")

    def _profile(args: tuple):
        pid, name, spot, team, opp, home_team, opp_pitcher = args
        try:
            return _build_player_profile(
                pid, name, spot, team, opp, home_team, opp_pitcher,
                batter_data, pitcher_data,
                batter_bb_data=batter_bb,
                pitcher_bb_data=pitcher_bb,
            )
        except Exception:
            return None

    all_players = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        for p in executor.map(_profile, tasks):
            if p:
                all_players.append(p)

    _cb("Computing EV...")
    # Pre-build odds lookup structure once (O(n))
    odds_lookup, unique_names = _build_odds_lookup(all_props)

    # Now match each player using the pre-built structure (O(1) per player)
    for p in all_players:
        _match_odds(p, odds_lookup, unique_names)
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

    # Auto parlay combos (legacy leg-count view + new profile-based view)
    auto_parlays    = parlay_engine.build_auto_parlays(ranked)
    profile_parlays = build_profile_parlays(all_players)

    return {
        "date":         game_date,
        "games":        games,
        "all_players":  all_players,
        "all_by_model": all_by_model,
        "ranked":       ranked,
        "odds_source":   odds_source,
        "batter_count":  len(batter_data),
        "team_players":  team_players,
        "auto_parlays":    auto_parlays,
        "profile_parlays": profile_parlays,
        "stats": {
            "games":     len(games),
            "players":   len(all_players),
            "qualified": len(qualified),
            "filtered":  len(all_players) - len(qualified),
        },
    }
