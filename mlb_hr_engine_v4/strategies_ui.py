# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 - ADVANCED STRATEGIES
# ═══════════════════════════════════════════════════════════════════════════
def tab_advanced_strategies(data: dict):
    """Advanced betting strategies tab with correlation parlays, hedging, stacks, etc."""
    import urllib.parse
    import streamlit as st
    import traceback as _tb
    import math
    import sys
    import itertools
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    import config

    def _fd_url(player_name: str = "") -> str:
        if player_name:
            q = urllib.parse.quote(player_name)
            return f"https://sportsbook.fanduel.com/search?q={q}"
        return "https://sportsbook.fanduel.com/baseball/mlb?tab=player-home-runs"

    def _fd_link(player_name: str) -> str:
        url = _fd_url(player_name)
        return (
            f"<a href='{url}' target='_blank' "
            f"style='color:#4488ff; font-size:11px; background:#0d0d2a; "
            f"padding:2px 8px; border-radius:4px; border:1px solid #1a2a66; "
            f"text-decoration:none; white-space:nowrap;'>Open FD →</a>"
        )

    def _fmt_american(odds) -> str:
        if odds is None:
            return "--"
        return f"+{odds}" if int(odds) > 0 else str(odds)

    def _ato_d(american) -> float:
        american = int(american)
        if american >= 100:
            return (american / 100.0) + 1
        return (100.0 / abs(american)) + 1

    def _dta(decimal: float) -> int:
        if decimal >= 2.0:
            return int((decimal - 1) * 100)
        return int(-100 / (decimal - 1))

    def _add_to_fd_slip(player_names: list, all_players: list) -> int:
        player_map = {p["player_name"]: p for p in all_players if p.get("player_name")}
        current = list(st.session_state.get("fd_slip", []))
        added = 0
        for name in player_names:
            p = player_map.get(name)
            if not p:
                continue
            odds = p.get("fanduel_american") or p.get("best_american")
            label = f"{p['player_name']} ({p.get('team', '')}) {_fmt_american(odds)}"
            if label not in current:
                current.append(label)
                added += 1
        if added:
            st.session_state["fd_slip"] = current
            st.session_state.pop("fd_slip_select", None)
            st.toast(f"✅ {added} player{'s' if added != 1 else ''} added to FD Slip!")
            st.rerun()
        return added

    st.markdown('<div class="section-header">🎯 ADVANCED BETTING STRATEGIES</div>', unsafe_allow_html=True)

    # Strategy selector
    strategy_type = st.selectbox(
        "Select Strategy Type",
        [
            "Correlation Parlays",
            "Team Stacks",
            "Value Bomb Parlays",
            "Power Profile Parlays",
            "Lineup Heart Parlays",
            "Park Monster Parlays",
            "Hedge Calculator",
            "Progressive Staking",
        ],
        help="Choose an advanced betting strategy to analyze"
    )

    try:
        from strategies import (
            find_correlated_parlays,
            build_team_stacks,
            calculate_hedge_bet,
            fibonacci_stake,
            dalembert_stake,
            oscar_grind_stake
        )

        all_players = data.get("all_players", [])
        ranked = data.get("ranked", [])

        if strategy_type == "Correlation Parlays":
            st.markdown("### 🔗 Correlation-Based Parlays")
            st.info("Same-team players facing the same pitcher — correlation bonus applied to EV")

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_corr_parlays(player_ids: tuple):
                return find_correlated_parlays(
                    players=all_players,
                    max_legs=3,
                    min_correlation=0.15,
                    min_individual_prob=0.08,
                )

            _cache_key = tuple(p.get("player_name", "") for p in all_players)
            corr_parlays = _cached_corr_parlays(_cache_key)

            if corr_parlays:
                for i, parlay in enumerate(corr_parlays[:5], 1):
                    with st.expander(f"Parlay #{i}: {len(parlay['legs'])} legs - EV: {parlay['ev_pct']:+.1f}%"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Correlation Score", f"{parlay['correlation_score']:.2f}")
                            st.metric("Adjusted Probability", f"{parlay['adjusted_prob']*100:.2f}%")
                            st.metric("American Odds", f"{parlay['american_odds']:+d}")
                        with col2:
                            st.metric("EV %", f"{parlay['ev_pct']:+.1f}%")
                            st.metric("Confidence", f"{parlay['confidence']:.0f}%")
                            st.metric("Correlation Bonus", f"{parlay['correlation_bonus']*100:.1f}%")

                        st.write("**Players:**")
                        for player, team in zip(parlay['legs'], parlay['teams']):
                            st.markdown(
                                f"<div style='display:flex; justify-content:space-between; "
                                f"align-items:center; padding:3px 0;'>"
                                f"<span>• <b>{player}</b> <span style='color:#888'>({team})</span></span>"
                                f"{_fd_link(player)}</div>",
                                unsafe_allow_html=True,
                            )

                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button(f"📲 Add All to FD Slip", key=f"fd_corr_{i}"):
                                n = _add_to_fd_slip(parlay['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No correlation parlays found with current criteria")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Team Stacks":
            st.markdown("### 🏟️ Team Stack Parlays")
            st.info("Multiple players from same team - capitalize on offensive explosions")

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_stacks(player_ids: tuple):
                return build_team_stacks(
                    players=all_players,
                    min_team_size=2,
                    max_stack_size=3,
                    min_individual_prob=0.08,
                    min_stack_ev=10.0,
                )

            _stack_key = tuple(p.get("player_name", "") for p in all_players)
            stacks = _cached_stacks(_stack_key)

            if stacks:
                all_stack_teams = sorted({s["team"] for s in stacks})
                team_filter = st.selectbox(
                    "Filter by team",
                    ["All Teams"] + all_stack_teams,
                    key="stack_team_filter",
                )
                filtered_stacks = (
                    stacks if team_filter == "All Teams"
                    else [s for s in stacks if s["team"] == team_filter]
                )
            else:
                filtered_stacks = []

            if filtered_stacks:
                for i, stack in enumerate(filtered_stacks[:8], 1):
                    with st.expander(f"{stack['team']} Stack: {stack['size']} players - EV: {stack['ev_pct']:+.1f}%"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Stack Size", stack['size'])
                            st.metric("Adjusted Probability", f"{stack['adjusted_prob']*100:.2f}%")
                            st.metric("American Odds", f"{stack['american_odds']:+d}")
                        with col2:
                            st.metric("EV %", f"{stack['ev_pct']:+.1f}%")
                            st.metric("Team Factor", f"{stack['team_explosion_factor']:.2f}x")
                            st.metric("Confidence", f"{stack['confidence']:.0f}%")

                        st.write("**Players (Lineup Spot):**")
                        for player, spot in zip(stack['players'], stack['lineup_spots']):
                            spot_str = f"#{spot}" if spot else "?"
                            st.markdown(
                                f"<div style='display:flex; justify-content:space-between; "
                                f"align-items:center; padding:3px 0;'>"
                                f"<span>• <b>{player}</b> <span style='color:#888'>({spot_str})</span></span>"
                                f"{_fd_link(player)}</div>",
                                unsafe_allow_html=True,
                            )

                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button(f"📲 Add All to FD Slip", key=f"fd_stack_{i}"):
                                n = _add_to_fd_slip(stack['players'], all_players)
                                if n:
                                    st.success(f"+{n} player{'s' if n != 1 else ''} added to FD Slip!")
                                else:
                                    st.info("Already in slip.")
            else:
                st.warning("No profitable team stacks found")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Value Bomb Parlays":
            st.markdown("### 💣 Value Bomb Parlays")
            st.info("Pure positive-EV picks combined into parlays — no correlation required, just raw edge")

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_value_bombs(player_ids: tuple):
                candidates = sorted(
                    [p for p in all_players if p.get("ev_pct", 0) > 0 and p.get("best_american") and p.get("model_prob", 0) >= 0.08],
                    key=lambda p: p.get("ev_pct", 0), reverse=True,
                )[:25]
                bombs = []
                for n_legs in (2, 3):
                    for combo in itertools.combinations(candidates, n_legs):
                        base_prob = 1.0
                        parlay_odds = 1.0
                        for p in combo:
                            base_prob *= p.get("model_prob", 0)
                            parlay_odds *= _ato_d(p["best_american"])
                        ev = (parlay_odds * base_prob) - 1
                        if ev > 0:
                            bombs.append({
                                "legs": [p["player_name"] for p in combo],
                                "teams": [p.get("team", "") for p in combo],
                                "ev_each": [round(p.get("ev_pct", 0), 1) for p in combo],
                                "odds_each": [p["best_american"] for p in combo],
                                "base_prob": base_prob,
                                "parlay_odds": parlay_odds,
                                "american_odds": _dta(parlay_odds),
                                "ev_pct": ev * 100,
                                "n_legs": n_legs,
                            })
                return sorted(bombs, key=lambda x: x["ev_pct"], reverse=True)[:10]

            _vb_key = tuple(p.get("player_name", "") for p in all_players)
            bombs = _cached_value_bombs(_vb_key)

            if bombs:
                for i, b in enumerate(bombs, 1):
                    label = f"{'2' if b['n_legs']==2 else '3'}-Leg Bomb #{i}: EV {b['ev_pct']:+.1f}%  |  {_fmt_american(b['american_odds'])}"
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Parlay EV", f"{b['ev_pct']:+.1f}%")
                            st.metric("Hit Probability", f"{b['base_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(b['american_odds']))
                            st.metric("Legs", b['n_legs'])
                        st.write("**Players:**")
                        for player, team, ev_e, odds_e in zip(b['legs'], b['teams'], b['ev_each'], b['odds_each']):
                            st.markdown(
                                f"<div style='display:flex; justify-content:space-between; align-items:center; padding:3px 0;'>"
                                f"<span>• <b>{player}</b> <span style='color:#888'>({team})</span> "
                                f"<span style='color:#4caf50; font-size:11px;'>EV {ev_e:+.1f}%  {_fmt_american(odds_e)}</span></span>"
                                f"{_fd_link(player)}</div>",
                                unsafe_allow_html=True,
                            )
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_vb_{i}"):
                                n = _add_to_fd_slip(b['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No positive-EV parlays found today")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Power Profile Parlays":
            st.markdown("### ⚡ Power Profile Parlays")
            st.info("Players with elite barrel%, high exit velocity, and low GB% — pure power metrics vs weak pitchers")

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_power_parlays(player_ids: tuple):
                def _power_score(p):
                    brl = float(p.get("barrel_pct") or p.get("brl_pct") or 0)
                    ev  = float(p.get("exit_velo") or 0)
                    gb  = float(p.get("gb_pct") or 50)
                    pf  = float(p.get("pitcher_factor") or 1.0)
                    brl_n = min(brl / 18.0, 1.0)
                    ev_n  = max(0.0, (ev - 85.0) / 15.0)
                    gb_n  = max(0.0, (50.0 - gb) / 30.0)
                    pf_n  = max(0.0, (pf - 1.0) / 0.5)
                    return brl_n * 0.40 + ev_n * 0.30 + gb_n * 0.20 + pf_n * 0.10

                candidates = [
                    p for p in all_players
                    if p.get("model_prob", 0) >= 0.08 and p.get("best_american")
                ]
                if not candidates:
                    return []
                scored = sorted(candidates, key=_power_score, reverse=True)[:20]

                parlays = []
                for n_legs in (2, 3):
                    pool = scored if n_legs == 2 else scored[:12]
                    for combo in itertools.combinations(pool, n_legs):
                        base_prob = 1.0
                        parlay_odds = 1.0
                        for p in combo:
                            base_prob *= p.get("model_prob", 0)
                            parlay_odds *= _ato_d(p["best_american"])
                        ev = (parlay_odds * base_prob) - 1
                        if ev > 0:
                            parlays.append({
                                "legs": [p["player_name"] for p in combo],
                                "teams": [p.get("team", "") for p in combo],
                                "power_scores": [round(_power_score(p), 3) for p in combo],
                                "barrel_pcts": [p.get("barrel_pct") or p.get("brl_pct") or 0 for p in combo],
                                "exit_velos": [p.get("exit_velo") or 0 for p in combo],
                                "base_prob": base_prob,
                                "parlay_odds": parlay_odds,
                                "american_odds": _dta(parlay_odds),
                                "ev_pct": ev * 100,
                                "n_legs": n_legs,
                            })
                return sorted(parlays, key=lambda x: x["ev_pct"], reverse=True)[:10]

            _pp_key = tuple(p.get("player_name", "") for p in all_players)
            power_parlays = _cached_power_parlays(_pp_key)

            if power_parlays:
                for i, pp in enumerate(power_parlays, 1):
                    avg_pwr = sum(pp['power_scores']) / len(pp['power_scores'])
                    label = f"{'2' if pp['n_legs']==2 else '3'}-Leg Power #{i}: EV {pp['ev_pct']:+.1f}%  |  Avg Power Score {avg_pwr:.2f}"
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Parlay EV", f"{pp['ev_pct']:+.1f}%")
                            st.metric("Hit Probability", f"{pp['base_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(pp['american_odds']))
                            st.metric("Avg Power Score", f"{avg_pwr:.3f}")
                        st.write("**Players:**")
                        for player, team, pwr, brl, evo in zip(pp['legs'], pp['teams'], pp['power_scores'], pp['barrel_pcts'], pp['exit_velos']):
                            brl_str = f"Brl {brl:.1f}%" if brl else ""
                            evo_str = f"EV {evo:.1f}" if evo else ""
                            meta = "  ".join(filter(None, [brl_str, evo_str]))
                            st.markdown(
                                f"<div style='display:flex; justify-content:space-between; align-items:center; padding:3px 0;'>"
                                f"<span>• <b>{player}</b> <span style='color:#888'>({team})</span> "
                                f"<span style='color:#ff9800; font-size:11px;'>{meta}</span></span>"
                                f"{_fd_link(player)}</div>",
                                unsafe_allow_html=True,
                            )
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_pp_{i}"):
                                n = _add_to_fd_slip(pp['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No power profile parlays found — may need Statcast data loaded")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Lineup Heart Parlays":
            st.markdown("### ❤️ Lineup Heart Parlays")
            st.info("Players batting 2-5 in the order — the heart of the lineup sees the most RBI chances and protection")

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_heart_parlays(player_ids: tuple):
                from collections import defaultdict
                heart_spots = {2, 3, 4, 5}
                heart_players = [
                    p for p in all_players
                    if p.get("lineup_spot") in heart_spots
                    and p.get("model_prob", 0) >= 0.08
                    and p.get("best_american")
                ]
                # Group by team to apply correlation boost for teammates
                by_team = defaultdict(list)
                for p in heart_players:
                    by_team[p.get("team", "UNK")].append(p)

                parlays = []
                # Same-team heart combos (correlated)
                for team, roster in by_team.items():
                    for combo in itertools.combinations(roster, 2):
                        base_prob = combo[0]["model_prob"] * combo[1]["model_prob"]
                        spots = [p.get("lineup_spot", 9) for p in combo]
                        consecutive = abs(spots[0] - spots[1]) <= 1
                        corr_boost = 1.15 if consecutive else 1.10
                        adj_prob = min(base_prob * corr_boost, 0.25)
                        parlay_odds = _ato_d(combo[0]["best_american"]) * _ato_d(combo[1]["best_american"])
                        ev = (parlay_odds * adj_prob) - 1
                        if ev > 0:
                            parlays.append({
                                "legs": [p["player_name"] for p in combo],
                                "teams": [p.get("team", "") for p in combo],
                                "spots": spots,
                                "type": "same-team",
                                "corr_boost": corr_boost,
                                "base_prob": base_prob,
                                "adj_prob": adj_prob,
                                "parlay_odds": parlay_odds,
                                "american_odds": _dta(parlay_odds),
                                "ev_pct": ev * 100,
                            })

                # Cross-team heart combos (top players only, no corr boost)
                top_hearts = sorted(heart_players, key=lambda p: p.get("model_prob", 0), reverse=True)[:15]
                for combo in itertools.combinations(top_hearts, 2):
                    if combo[0].get("team") == combo[1].get("team"):
                        continue  # already handled above
                    base_prob = combo[0]["model_prob"] * combo[1]["model_prob"]
                    parlay_odds = _ato_d(combo[0]["best_american"]) * _ato_d(combo[1]["best_american"])
                    ev = (parlay_odds * base_prob) - 1
                    if ev > 0:
                        parlays.append({
                            "legs": [p["player_name"] for p in combo],
                            "teams": [p.get("team", "") for p in combo],
                            "spots": [p.get("lineup_spot") for p in combo],
                            "type": "cross-team",
                            "corr_boost": 1.0,
                            "base_prob": base_prob,
                            "adj_prob": base_prob,
                            "parlay_odds": parlay_odds,
                            "american_odds": _dta(parlay_odds),
                            "ev_pct": ev * 100,
                        })

                return sorted(parlays, key=lambda x: x["ev_pct"], reverse=True)[:10]

            _lh_key = tuple(p.get("player_name", "") for p in all_players)
            heart_parlays = _cached_heart_parlays(_lh_key)

            if heart_parlays:
                for i, hp in enumerate(heart_parlays, 1):
                    tag = "🔗 Same-Team" if hp["type"] == "same-team" else "🔀 Cross-Team"
                    spots_str = " & ".join(f"#{s}" for s in hp["spots"])
                    label = f"{tag} Heart #{i}: EV {hp['ev_pct']:+.1f}%  |  Spots {spots_str}"
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Parlay EV", f"{hp['ev_pct']:+.1f}%")
                            st.metric("Adj. Probability", f"{hp['adj_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(hp['american_odds']))
                            if hp["type"] == "same-team":
                                st.metric("Correlation Boost", f"{(hp['corr_boost']-1)*100:.0f}%")
                        st.write("**Players:**")
                        for player, team, spot in zip(hp['legs'], hp['teams'], hp['spots']):
                            st.markdown(
                                f"<div style='display:flex; justify-content:space-between; align-items:center; padding:3px 0;'>"
                                f"<span>• <b>{player}</b> <span style='color:#888'>({team})</span> "
                                f"<span style='color:#e91e63; font-size:11px;'>Spot #{spot}</span></span>"
                                f"{_fd_link(player)}</div>",
                                unsafe_allow_html=True,
                            )
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_lh_{i}"):
                                n = _add_to_fd_slip(hp['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No lineup heart parlays found — lineups may not be posted yet")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Park Monster Parlays":
            st.markdown("### 🏟️ Park Monster Parlays")
            st.info("Players in the most hitter-friendly parks — Coors, Great American, Fenway, etc. — where the ball flies")

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_park_parlays(player_ids: tuple):
                from collections import defaultdict
                min_park = 1.08
                park_players = sorted(
                    [p for p in all_players
                     if p.get("park_factor", 1.0) >= min_park
                     and p.get("model_prob", 0) >= 0.07
                     and p.get("best_american")],
                    key=lambda p: p.get("park_factor", 1.0) * p.get("model_prob", 0),
                    reverse=True,
                )[:25]

                by_park = defaultdict(list)
                for p in park_players:
                    by_park[round(p.get("park_factor", 1.0), 2)].append(p)

                parlays = []
                for n_legs in (2, 3):
                    pool = park_players if n_legs == 2 else park_players[:15]
                    for combo in itertools.combinations(pool, n_legs):
                        base_prob = 1.0
                        parlay_odds = 1.0
                        avg_park = sum(p.get("park_factor", 1.0) for p in combo) / len(combo)
                        for p in combo:
                            base_prob *= p.get("model_prob", 0)
                            parlay_odds *= _ato_d(p["best_american"])
                        park_boost = 1.0 + (avg_park - 1.0) * 0.5
                        adj_prob = min(base_prob * park_boost, 0.25)
                        ev = (parlay_odds * adj_prob) - 1
                        if ev > 0:
                            parlays.append({
                                "legs": [p["player_name"] for p in combo],
                                "teams": [p.get("team", "") for p in combo],
                                "park_factors": [round(p.get("park_factor", 1.0), 3) for p in combo],
                                "avg_park": round(avg_park, 3),
                                "park_boost": round(park_boost, 3),
                                "base_prob": base_prob,
                                "adj_prob": adj_prob,
                                "parlay_odds": parlay_odds,
                                "american_odds": _dta(parlay_odds),
                                "ev_pct": ev * 100,
                                "n_legs": n_legs,
                            })
                return sorted(parlays, key=lambda x: x["ev_pct"], reverse=True)[:10]

            _park_key = tuple(p.get("player_name", "") for p in all_players)
            park_parlays = _cached_park_parlays(_park_key)

            if park_parlays:
                for i, par in enumerate(park_parlays, 1):
                    label = f"{'2' if par['n_legs']==2 else '3'}-Leg Park Monster #{i}: EV {par['ev_pct']:+.1f}%  |  Avg Park {par['avg_park']:.2f}x"
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Parlay EV", f"{par['ev_pct']:+.1f}%")
                            st.metric("Adj. Probability", f"{par['adj_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(par['american_odds']))
                            st.metric("Park Boost", f"{(par['park_boost']-1)*100:.1f}%")
                        st.write("**Players:**")
                        for player, team, pf in zip(par['legs'], par['teams'], par['park_factors']):
                            st.markdown(
                                f"<div style='display:flex; justify-content:space-between; align-items:center; padding:3px 0;'>"
                                f"<span>• <b>{player}</b> <span style='color:#888'>({team})</span> "
                                f"<span style='color:#00bcd4; font-size:11px;'>Park {pf:.2f}x</span></span>"
                                f"{_fd_link(player)}</div>",
                                unsafe_allow_html=True,
                            )
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_park_{i}"):
                                n = _add_to_fd_slip(par['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No park monster parlays found — no games in hitter-friendly parks today")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Hedge Calculator":
            st.markdown("### 🛡️ Hedge Betting Calculator")
            st.info("Pick a player to pre-fill their odds, or enter manually")

            # Player quick-fill
            odds_players = sorted(
                [p for p in all_players if p.get("best_american")],
                key=lambda p: p.get("model_prob", 0), reverse=True,
            )
            player_opts = ["-- Enter manually --"] + [
                f"{p['player_name']} ({p.get('team','')})  {_fmt_american(p.get('best_american'))}"
                for p in odds_players
            ]
            player_map = {
                f"{p['player_name']} ({p.get('team','')})  {_fmt_american(p.get('best_american'))}": p
                for p in odds_players
            }
            selected_player_label = st.selectbox(
                "Quick-fill from today's players",
                player_opts,
                key="hedge_player_select",
            )
            selected_player = player_map.get(selected_player_label)
            prefill_odds = int(selected_player["best_american"]) if selected_player else 400

            col1, col2 = st.columns(2)
            with col1:
                original_stake = st.number_input(
                    "Original Stake ($)", min_value=1.0,
                    value=float(st.session_state.get("hedge_stake", 100.0)), step=10.0,
                    key="hedge_stake",
                )
                original_odds = st.number_input(
                    "Original Odds", min_value=-10000, max_value=10000,
                    value=prefill_odds, key="hedge_orig_odds",
                )
                if selected_player:
                    st.caption(
                        f"Model prob: **{selected_player.get('model_prob',0)*100:.1f}%** "
                        f"&nbsp;|&nbsp; EV: **{selected_player.get('ev_pct',0):+.1f}%**"
                    )
            with col2:
                hedge_odds = st.number_input(
                    "Current Hedge Odds", min_value=-10000, max_value=10000,
                    value=int(st.session_state.get("hedge_hedge_odds", -150)),
                    help="Odds to bet the opposite outcome (no HR)",
                    key="hedge_hedge_odds",
                )
                target_profit = st.number_input(
                    "Target Profit ($)", min_value=0.0,
                    value=float(st.session_state.get("hedge_target", 0.0)),
                    help="0 = break even",
                    key="hedge_target",
                )

            if st.button("Calculate Hedge", type="primary"):
                hedge = calculate_hedge_bet(
                    original_stake, original_odds, hedge_odds,
                    target_profit if target_profit > 0 else None,
                )
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Hedge Stake", f"${hedge['hedge_stake']:.2f}")
                    st.metric("Total Risk", f"${hedge['total_risk']:.2f}")
                with col2:
                    st.metric("If Original Wins", f"${hedge['if_original_wins']:+.2f}")
                    st.metric("If Hedge Wins", f"${hedge['if_hedge_wins']:+.2f}")
                with col3:
                    st.metric("Guaranteed Profit", f"${hedge['guaranteed_profit']:+.2f}")
                    st.metric("Hedge ROI", f"{hedge['hedge_roi']:.1f}%")

            st.divider()
            if selected_player:
                st.link_button(
                    f"📲 Open {selected_player['player_name']} on FanDuel",
                    _fd_url(selected_player["player_name"]),
                    use_container_width=True,
                )
            else:
                st.link_button("📲 Browse FanDuel HR Props", _fd_url(), use_container_width=True)

        elif strategy_type == "Progressive Staking":
            st.markdown("### 📈 Progressive Staking Systems")
            st.info("Alternative staking strategies beyond Kelly Criterion — session state persists across reruns")

            col1, col2 = st.columns(2)
            with col1:
                system = st.selectbox(
                    "Staking System",
                    ["Fibonacci", "D'Alembert", "Oscar's Grind"],
                    key="staking_system",
                    help="Select a progressive staking system",
                )
                base_unit = st.number_input(
                    "Base Unit ($)", min_value=1.0, step=5.0,
                    value=float(st.session_state.get("staking_base_unit", 10.0)),
                    key="staking_base_unit",
                )
                bankroll = st.session_state.get("bankroll_override", config.BANKROLL)

            with col2:
                if system == "Fibonacci":
                    loss_streak = st.number_input(
                        "Current Loss Streak", min_value=0, max_value=10,
                        value=int(st.session_state.get("staking_fib_streak", 0)),
                        key="staking_fib_streak",
                    )
                    stake = fibonacci_stake(base_unit, loss_streak, bankroll)
                    st.metric("Next Stake", f"${stake:.2f}")
                    bcol1, bcol2 = st.columns(2)
                    with bcol1:
                        if st.button("✅ Win", key="fib_win"):
                            new_streak = max(0, loss_streak - 2)
                            st.session_state["staking_fib_streak"] = new_streak
                            st.rerun()
                    with bcol2:
                        if st.button("❌ Loss", key="fib_loss"):
                            st.session_state["staking_fib_streak"] = loss_streak + 1
                            st.rerun()
                    st.caption("After loss: move to next Fibonacci number. After win: move back two.")

                elif system == "D'Alembert":
                    wins = st.number_input(
                        "Session Wins", min_value=0,
                        value=int(st.session_state.get("staking_dal_wins", 0)),
                        key="staking_dal_wins",
                    )
                    losses = st.number_input(
                        "Session Losses", min_value=0,
                        value=int(st.session_state.get("staking_dal_losses", 0)),
                        key="staking_dal_losses",
                    )
                    stake = dalembert_stake(base_unit, wins, losses, bankroll)
                    st.metric("Next Stake", f"${stake:.2f}")
                    bcol1, bcol2, bcol3 = st.columns(3)
                    with bcol1:
                        if st.button("✅ Win", key="dal_win"):
                            st.session_state["staking_dal_wins"] = wins + 1
                            st.rerun()
                    with bcol2:
                        if st.button("❌ Loss", key="dal_loss"):
                            st.session_state["staking_dal_losses"] = losses + 1
                            st.rerun()
                    with bcol3:
                        if st.button("🔄 Reset", key="dal_reset"):
                            st.session_state["staking_dal_wins"] = 0
                            st.session_state["staking_dal_losses"] = 0
                            st.rerun()
                    st.caption("Increase by 1 unit after loss, decrease after win.")

                elif system == "Oscar's Grind":
                    session_profit = st.number_input(
                        "Session P&L ($)",
                        value=float(st.session_state.get("staking_og_profit", 0.0)),
                        key="staking_og_profit",
                    )
                    streak_type = st.selectbox(
                        "Current Streak", ["win", "loss"],
                        index=["win", "loss"].index(
                            st.session_state.get("staking_og_streak_type", "win")
                        ),
                        key="staking_og_streak_type",
                    )
                    streak_length = st.number_input(
                        "Streak Length", min_value=0,
                        value=int(st.session_state.get("staking_og_streak_len", 0)),
                        key="staking_og_streak_len",
                    )
                    stake = oscar_grind_stake(
                        base_unit, session_profit, streak_type, streak_length, bankroll,
                    )
                    st.metric("Next Stake", f"${stake:.2f}")
                    bcol1, bcol2, bcol3 = st.columns(3)
                    with bcol1:
                        if st.button("✅ Win", key="og_win"):
                            st.session_state["staking_og_profit"] = session_profit + stake
                            st.session_state["staking_og_streak_type"] = "win"
                            st.session_state["staking_og_streak_len"] = (
                                streak_length + 1 if streak_type == "win" else 1
                            )
                            st.rerun()
                    with bcol2:
                        if st.button("❌ Loss", key="og_loss"):
                            st.session_state["staking_og_profit"] = session_profit - stake
                            st.session_state["staking_og_streak_type"] = "loss"
                            st.session_state["staking_og_streak_len"] = (
                                streak_length + 1 if streak_type == "loss" else 1
                            )
                            st.rerun()
                    with bcol3:
                        if st.button("🔄 Reset", key="og_reset"):
                            st.session_state["staking_og_profit"] = 0.0
                            st.session_state["staking_og_streak_type"] = "win"
                            st.session_state["staking_og_streak_len"] = 0
                            st.rerun()
                    st.caption("Goal: Win 1 unit per session. Keep stakes same in losses, increase in wins.")

            st.divider()
            st.link_button("📲 Browse FanDuel HR Props", _fd_url(), use_container_width=True)

    except ImportError as e:
        st.error("Advanced strategies module not found. Strategies are being developed.")
        st.code(str(e))
    except Exception as e:
        st.error(f"Error in advanced strategies: {e}")
        st.code(_tb.format_exc())
