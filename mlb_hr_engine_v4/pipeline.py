"""
Shared data pipeline — used by both main.py (CLI) and app.py (Streamlit).

Call load_game_data() once per session. It fetches everything and returns
a single dict that both the CLI display and the Streamlit UI can consume.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from rapidfuzz import fuzz, process as fuzz_process
import unicodedata

import config
from clients import mlb_stats, odds_api
from clients import weather as weather_client
from clients import statcast as statcast_client
from clients import arsenal as arsenal_client
from data.park_factors import get_park
from engine import market as mkt, probability as prob, ev as ev_engine, sizing, filters
from output import ranker, parlay as parlay_engine
from output.parlay import build_profile_parlays
from tracking import adaptive_weights as _aw


# ── Core helpers (same logic as v3 main.py, extracted here) ──────────────────

def _utc_to_local_hour(game_time_utc: str, tz_offset: int) -> int:
    """Parse game_time_utc ('2026-04-26T22:05:00Z') and return local game hour (0-23)."""
    try:
        utc_hour = int(game_time_utc[11:13])
        return (utc_hour + tz_offset) % 24
    except (IndexError, ValueError):
        return 19  # fallback to 7pm local


def _safe_float(val) -> "float | None":
    """Convert a Statcast value that may be '--', None, or a numeric string to float."""
    try:
        return float(val) if val and str(val) != '--' else None
    except (ValueError, TypeError):
        return None


def _build_player_profile(
    player_id, player_name, lineup_spot, team, opponent,
    home_team, pitcher, batter_data, pitcher_data,
    game_time_utc: str = "",
    arsenal_data: dict = None, arsenal_prior: dict = None,
):
    season_stats    = mlb_stats.get_player_season_stats(player_id)
    recent_stats    = mlb_stats.get_player_recent_stats(player_id)
    short_form      = mlb_stats.get_player_short_form(player_id, days=14)
    season_pa = int(season_stats.get("plateAppearances", 0))
    recent_pa = int(recent_stats.get("plateAppearances", 0))
    if season_pa == 0 and recent_pa == 0:
        return None

    power_mult = statcast_client.batter_power_multiplier(player_id, batter_data)
    sc_stats   = dict(batter_data.get(player_id) or {})
    sc_pa      = sc_stats.get("pa", 0)
    # Default to "current" only when the player IS in batter_data (tier-1 rows have no key set);
    # players absent entirely get "none" so confidence_score awards no Statcast bonus.
    sc_source  = sc_stats.get("statcast_source", "current" if sc_stats else "none")
    raw_rate   = prob.base_hr_rate(season_stats, recent_stats, statcast_mult=power_mult,
                                    recent_weight=_aw.get("recent_weight"))
    hr_rate    = prob.statcast_blended_rate(
        raw_rate, power_mult, season_pa,
        statcast_pa=sc_pa, statcast_source=sc_source,
    )
    sc_summary = statcast_client.statcast_summary(player_id, batter_data)

    # Derived contact-quality fields used by profile-based parlay scoring
    actual_slg = float(season_stats.get("sluggingPercentage", 0) or 0)
    xba_float  = _safe_float(sc_stats.get("xba"))
    xslg_float = _safe_float(sc_stats.get("xslg"))

    xiso       = (round(xslg_float - xba_float, 3)
                  if (xslg_float is not None and xba_float is not None) else None)
    xslg_diff  = (round(xslg_float - actual_slg, 3)
                  if xslg_float is not None else None)

    streak_fac = prob.hot_streak_factor(short_form, season_stats)
    k_fac      = prob.batter_k_suppressor(season_stats)

    # Batter handedness needed for park factor — fetch before pk_factor computation
    batter_info = mlb_stats.get_player_info(player_id)
    batter_side = batter_info.get("batSide", {}).get("code", "")
    splits      = mlb_stats.get_player_platoon_splits(player_id)

    exp_pa    = prob.expected_pa(lineup_spot)
    pk_factor = prob.park_factor(home_team, batter_side)
    pk_factor = prob.fly_ball_adjusted_park_factor(pk_factor, sc_stats.get("fb_pct"))

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
    sc_pit_fac     = statcast_client.pitcher_contact_suppressor(pitcher_id or 0, pitcher_data)
    k_gb_fac       = prob.pitcher_k_gb_suppressor(pitcher_stats)
    pit_factor     = prob.pitcher_combined_factor(hr_fb_fac, sc_pit_fac, k_gb_fac)
    recent_pit_fac = prob.pitcher_recent_factor(recent_pitcher_stats)
    pit_factor     = max(0.55, min(1.60, pit_factor * recent_pit_fac))
    fatigue_fac    = prob.pitcher_fatigue_factor(pitcher_days_rest)
    pit_factor     = max(0.55, min(1.60, pit_factor * fatigue_fac))

    # Pitcher HR/9 for confidence threshold flag
    pit_ip = mlb_stats.parse_ip(pitcher_stats.get("inningsPitched", "0.0"))
    pit_hrs  = int(pitcher_stats.get("homeRuns", 0))
    pitcher_hr9 = round((pit_hrs / pit_ip) * 9.0, 2) if pit_ip >= 5 else 0.0

    # Pitch arsenal matchup + velocity decline factors
    _arsenal = arsenal_data or {}
    _arsenal_prior = arsenal_prior or {}
    arsenal_matchup_mult = arsenal_client.arsenal_matchup_factor(pitcher_id or 0, _arsenal)
    velo_fac             = arsenal_client.pitcher_velo_decline_factor(pitcher_id or 0, _arsenal, _arsenal_prior)
    arsenal_fac          = prob.arsenal_factor(arsenal_matchup_mult)

    # Pulled air-ball factor
    pab_mult  = statcast_client.pulled_air_ball_metric(player_id, batter_data)
    pab_factor = prob.pulled_air_ball_factor(pab_mult)

    park_data  = get_park(home_team)
    is_dome    = home_team in weather_client.DOME_TEAMS
    cf_bearing = park_data.get("cf_bearing", 0.0)
    game_hour  = _utc_to_local_hour(game_time_utc, park_data.get("tz_offset", -5))
    weather    = weather_client.get_game_weather(park_data["lat"], park_data["lon"], game_hour)
    w_factor   = max(0.80, min(1.20,
        weather_client.temp_factor(weather["temp_f"])
        * weather_client.wind_factor(weather["wind_mph"], weather["wind_deg"], is_dome, cf_bearing)
        * weather_client.humidity_factor(weather.get("humidity_pct", 55), is_dome)
    ))

    plat_factor = prob.platoon_factor(splits, pitcher_hand, batter_side, season_pa)

    # Stage 6: batter × pitcher interaction term (non-additive matchup synergy).
    # Uses pit_factor (full combined signal) instead of sc_pit_fac alone — sc_pit_fac
    # is already embedded in pit_factor at 40% weight, so using it directly double-counted
    # the Statcast signal. Coefficient adaptive (default 0.20, tuned by auto-learn).
    batter_excess  = max(0.0, power_mult - 1.0)
    pitcher_excess = max(0.0, pit_factor - 1.0)
    _ic = _aw.get("interaction_coeff", 0.20)
    interaction    = batter_excess * pitcher_excess * _ic

    early_supp    = prob.early_season_suppressor(season_pa, sc_source)
    adjusted_rate = min(0.15, hr_rate * streak_fac * k_fac * early_supp * (1.0 + interaction))
    model_prob = prob.game_hr_probability(
        adjusted_rate, exp_pa,
        pk_factor=pk_factor, pitcher_fac=pit_factor,
        w_factor=w_factor, plat_factor=plat_factor,
        pab_fac=pab_factor, arsenal_fac=arsenal_fac, velo_fac=velo_fac,
    )
    # When lineup hasn't been posted (spot is None), the player may not start.
    # 0.82 discount ≈ 82% probability of actually being in the lineup.
    if not lineup_spot:
        model_prob = round(model_prob * 0.82, 4)

    # Apply adaptive calibration scale (moves model_prob toward observed hit rate)
    model_prob = round(_aw.apply_prob_scale(model_prob), 4)

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
        "pulled_air_ball_factor": round(pab_factor, 3),
        "arsenal_factor": round(arsenal_fac, 3),
        "velo_decline_factor": round(velo_fac, 3),
        "batter_side": batter_side,
        "model_prob": round(model_prob, 4), "weather": weather,
        "pitcher_hr9": pitcher_hr9,
        "short_form_pa": int(short_form.get("plateAppearances", 0)),
        "short_form_hr": int(short_form.get("homeRuns", 0)),
        "streak_factor": round(streak_fac, 3),
        "k_factor": round(k_fac, 3),
        "early_season_suppressor": round(early_supp, 3),
        "avg_launch_angle": sc_summary.get("avg_launch_angle"),
        "xslg": sc_summary.get("xslg"),
        "xba": xba_float,
        "xiso": xiso,
        "xslg_diff": xslg_diff,
        "actual_slg": round(actual_slg, 3),
    }


def _ascii_fold(name: str) -> str:
    """Strip accents for robust fuzzy matching (e.g. 'José' → 'Jose')."""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")

_NAME_MATCH_CACHE: dict[str, str | None] = {}


def _build_odds_lookup(all_props):
    """Pre-build a lookup structure for O(1) odds matching."""
    if not all_props:
        return {}, []

    # Group props by player name; store both original and ascii-folded key
    odds_by_player = {}
    for prop in all_props:
        name = prop["player_name"]
        key  = _ascii_fold(name)
        if key not in odds_by_player:
            odds_by_player[key] = []
        odds_by_player[key].append(prop)

    unique_names = list(odds_by_player.keys())
    return odds_by_player, unique_names


def _match_odds(player, odds_lookup, unique_names):
    """Match odds using pre-built lookup structure (O(1) after fuzzy match)."""
    if not odds_lookup:
        return player

    # Fold accents before matching so 'José' == 'Jose' at the fuzzy layer
    folded_name = _ascii_fold(player["player_name"])
    if folded_name not in _NAME_MATCH_CACHE:
        m = fuzz_process.extractOne(
            folded_name, unique_names,
            scorer=fuzz.token_sort_ratio, score_cutoff=90,
        )
        _NAME_MATCH_CACHE[folded_name] = m[0] if m else None
    matched_name = _NAME_MATCH_CACHE[folded_name]
    if not matched_name:
        return player

    matches = odds_lookup.get(matched_name, [])
    if not matches:
        return player

    prices  = [p["price"] for p in matches]
    summary = mkt.market_summary(prices)
    best    = max(matches, key=lambda x: x["price"])
    fd_matches = [p for p in matches if p.get("bookmaker") == "fanduel"]
    fd_odds = max(fd_matches, key=lambda x: x["price"])["price"] if fd_matches else None
    # Deduplicate per book: keep best price per bookmaker for the comparison table
    book_best: dict[str, int] = {}
    for prop in matches:
        bk = prop.get("bookmaker", "")
        if bk and (bk not in book_best or prop["price"] > book_best[bk]):
            book_best[bk] = prop["price"]
    player.update({
        "best_american":      best["price"], "best_bookmaker": best.get("bookmaker", ""),
        "all_prices":         prices, "n_books": summary.get("n_books", 1),
        "prices_by_book":     book_best,   # {bookmaker: american_odds} for comparison table
        # consensus no-vig for edge (conservative market baseline); best no-vig for EV display
        "market_no_vig_prob": round(summary.get("no_vig_prob_consensus", 0), 4),
        "market_implied_avg": round(summary.get("implied_prob_avg", 0), 4),
        "fanduel_american":   fd_odds,
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
    # Handle non-numeric values like '--' gracefully
    barrel_pct_str = str(player.get("barrel_pct", "0")).replace("%", "")
    try:
        barrel_raw = float(barrel_pct_str) / 100.0 if barrel_pct_str and barrel_pct_str != '--' else 0.0
    except (ValueError, TypeError):
        barrel_raw = 0.0

    try:
        pitcher_hr9 = float(player.get("pitcher_hr9", 0) or 0)
    except (ValueError, TypeError):
        pitcher_hr9 = 0.0

    player["confidence"] = prob.confidence_score(
        player.get("season_pa", 0), player.get("recent_pa", 0),
        model_p, market_p,
        statcast_source=player.get("statcast_source", "none"),
        barrel_rate=barrel_raw,
        pitcher_hr9=pitcher_hr9,
        xslg=_safe_float(player.get("xslg")),
        lineup_confirmed=bool(player.get("lineup_spot")),
        n_books=player.get("n_books", 1),
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

    # Run adaptive learning if new settled picks are available since last run
    try:
        from tracking import auto_learn as _al
        result = _al.auto_apply_safe()
        if result.get("applied"):
            _aw.invalidate_cache()
            _cb(f"Adaptive weights updated: {', '.join(result['applied'])}")
    except Exception as _e:
        print(f"[pipeline] auto_apply_safe skipped: {_e}")

    # Fetch schedule and odds in parallel for improved performance
    _cb("Fetching schedule and odds concurrently...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both fetch tasks concurrently
        future_schedule = executor.submit(mlb_stats.get_today_schedule, game_date)
        future_odds = executor.submit(odds_api.get_hr_odds_all_games)

        # Collect schedule result
        try:
            games = future_schedule.result()
        except Exception as e:
            print(f"[pipeline] schedule fetch failed: {e}")
            games = []

    # Validate game dates — reject stale cached games from wrong date
    valid_games = []
    for g in games:
        g_date = g.get("game_date") or (g.get("game_time_utc", "")[:10] if g.get("game_time_utc") else "")
        if g_date and g_date != game_date:
            print(f"[pipeline] WARNING: skipping game {g.get('game_pk')} dated {g_date} (expected {game_date})")
            continue
        valid_games.append(g)
    games = valid_games

    # Collect odds result with error handling
    try:
        all_props, odds_source, odds_quota = future_odds.result()
    except Exception:
        all_props, odds_source, odds_quota = [], "none", {"used": None, "remaining": None}

    # Collect all player and pitcher IDs from lineups first (for Statcast filtering)
    _cb("Collecting lineup players...")
    batter_ids = set()
    pitcher_ids = set()

    # Pre-scan games to collect all player IDs; cache rosters to avoid double API calls
    _roster_cache: dict[int, list] = {}
    for game in games:
        # Add starting pitchers
        if game.get("home_pitcher", {}).get("id"):
            pitcher_ids.add(game["home_pitcher"]["id"])
        if game.get("away_pitcher", {}).get("id"):
            pitcher_ids.add(game["away_pitcher"]["id"])

        # Add batters from lineups
        for lineup, tid in [
            (game.get("home_lineup", []), game.get("home_team_id")),
            (game.get("away_lineup", []), game.get("away_team_id")),
        ]:
            if lineup:
                for batter in lineup:
                    if batter.get("id"):
                        batter_ids.add(batter["id"])
            elif tid:
                if tid not in _roster_cache:
                    _roster_cache[tid] = mlb_stats.get_team_active_roster(tid)
                for player in _roster_cache[tid]:
                    if player.get("id"):
                        batter_ids.add(player["id"])

    # Fetch Statcast, MLB stats, and arsenal data in parallel for maximum efficiency
    _cb(f"Loading data for {len(batter_ids)} batters, {len(pitcher_ids)} pitchers...")
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(statcast_client.get_batter_statcast, player_ids=batter_ids): "batter_statcast",
            executor.submit(statcast_client.get_pitcher_statcast, player_ids=pitcher_ids): "pitcher_statcast",
            executor.submit(mlb_stats.bulk_fetch_player_stats, batter_ids): "mlb_player_stats",
            executor.submit(mlb_stats.bulk_fetch_pitcher_stats, pitcher_ids): "mlb_pitcher_stats",
            executor.submit(arsenal_client.get_pitcher_arsenal, config.CURRENT_SEASON): "arsenal_curr",
            executor.submit(arsenal_client.get_pitcher_arsenal, config.CURRENT_SEASON - 1): "arsenal_prior",
        }

        results = {}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                print(f"Error fetching {key}: {e}")
                results[key] = {} if key in ("batter_statcast", "pitcher_statcast", "arsenal_curr", "arsenal_prior") else None

    # Batted-ball data is already merged into batter_data/pitcher_data by get_*_statcast()
    batter_data   = results.get("batter_statcast", {})
    pitcher_data  = results.get("pitcher_statcast", {})
    arsenal_data  = results.get("arsenal_curr", {})
    arsenal_prior = results.get("arsenal_prior", {})

    # Collect tasks first so roster fallbacks run before the parallel phase.
    tasks: list[tuple] = []
    for game in games:
        home, away = game["home_team"], game["away_team"]
        game_time_utc = game.get("game_time_utc", "")
        for lineup, team, opp, team_id, opp_pitcher in [
            (game["home_lineup"], home, away, game.get("home_team_id"), game.get("away_pitcher", {})),
            (game["away_lineup"], away, home, game.get("away_team_id"), game.get("home_pitcher", {})),
        ]:
            if not lineup:
                if team_id:
                    if team_id not in _roster_cache:
                        _roster_cache[team_id] = mlb_stats.get_team_active_roster(team_id)
                    lineup = _roster_cache[team_id]
                if not lineup:
                    continue
            for batter in lineup:
                pid  = batter.get("id")
                name = batter.get("name", "Unknown")
                if not pid:
                    continue
                tasks.append((pid, name, batter.get("lineup_spot"), team, opp, home, opp_pitcher,
                              game_time_utc, game.get("game_pk"), game.get("status", "Scheduled")))

    # Pre-warm weather cache: fetch each unique (lat, lon, hour) combo in parallel
    # before the 16-thread profile pool starts, so threads never race on the same park.
    _unique_wx = {
        (get_park(home_team)["lat"], get_park(home_team)["lon"],
         _utc_to_local_hour(game_time_utc, get_park(home_team).get("tz_offset", -5)))
        for _, _, _, _, _, home_team, _, game_time_utc, _, _ in tasks
    }
    if _unique_wx:
        with ThreadPoolExecutor(max_workers=min(len(_unique_wx), 8)) as _wx_exec:
            list(_wx_exec.map(lambda t: weather_client.get_game_weather(*t), _unique_wx))

    _cb(f"Building profiles for {len(tasks)} players...")

    def _profile(args: tuple):
        pid, name, spot, team, opp, home_team, opp_pitcher, game_time_utc, game_pk, game_status = args
        try:
            profile = _build_player_profile(
                pid, name, spot, team, opp, home_team, opp_pitcher,
                batter_data, pitcher_data,
                game_time_utc=game_time_utc,
                arsenal_data=arsenal_data, arsenal_prior=arsenal_prior,
            )
            if profile:
                profile["game_time_utc"] = game_time_utc
                profile["game_pk"]       = game_pk
                profile["game_status"]   = game_status
            return profile
        except Exception as e:
            print(f"[pipeline] profile error for {name} ({pid}): {e}")
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

    qualified    = []
    team_players: dict[str, list[dict]] = {}
    sc_counts    = {"current": 0, "blended": 0, "prior": 0, "none": 0}
    pit_ids: set = set()
    for p in all_players:
        passed, reasons = filters.apply_filters(p)
        p["filter_reasons"] = reasons
        p["soft_flags"]     = filters.soft_flags(p)
        if passed:
            qualified.append(p)
        if p.get("best_american"):
            team_players.setdefault(p["team"], []).append(p)
        src = p.get("statcast_source") or ""
        sc_counts[src if src in sc_counts else "none"] += 1
        if p.get("pitcher_id"):
            pit_ids.add(p["pitcher_id"])

    for team in team_players:
        team_players[team].sort(key=lambda x: x.get("model_prob", 0), reverse=True)

    ranked      = ranker.rank_picks(qualified)
    all_by_model = ranker.rank_all_by_model(all_players)

    # Stamp tier + score on every player so strategies_ui can sort by confidence
    _ranked_map = {p.get("player_name"): p for p in ranked}
    for p in all_players:
        if p.get("player_name") in _ranked_map:
            # Qualified picks already have tier/score from rank_picks
            _rp = _ranked_map[p["player_name"]]
            p["confidence_tier"] = _rp.get("confidence_tier", "C")
            p["score"]           = _rp.get("score", 0)
        else:
            ev   = p.get("ev_pct", 0)
            edge = p.get("edge_pct", 0)
            conf = p.get("confidence", 0)
            p["confidence_tier"] = ranker.confidence_tier(conf, edge)
            p["score"]           = ranker.composite_score(ev, edge, conf)

    # Auto parlay combos (legacy leg-count view + new profile-based view)
    auto_parlays    = parlay_engine.build_auto_parlays(ranked)
    profile_parlays = build_profile_parlays(all_players)

    return {
        "date":         game_date,
        "games":        games,
        "all_players":  all_players,
        "all_by_model": all_by_model,
        "qualified":    qualified,  # Add for main.py compatibility
        "ranked":       ranked,
        "odds_source":   odds_source,
        "odds_quota":    odds_quota,
        "batter_data":  batter_data,  # Add for main.py compatibility
        "batter_count":  len(batter_data),
        "team_players":  team_players,
        "auto_parlays":    auto_parlays,
        "profile_parlays": profile_parlays,
        "stats": {
            "games":     len(games),
            "players":   len(all_players),
            "qualified": len(qualified),
            "filtered":  len(all_players) - len(qualified),
            "sc_current":  sc_counts["current"],
            "sc_blended":  sc_counts["blended"],
            "sc_prior":    sc_counts["prior"],
            "sc_none":     sc_counts["none"],
            "pit_sc_count": len(pitcher_data),
            "pit_total":   len(pit_ids),
        },
    }
