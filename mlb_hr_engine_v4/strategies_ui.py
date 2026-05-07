# ═══════════════════════════════════════════════════════════════════════════
# ADVANCED STRATEGIES (formerly Tab 4)
# ═══════════════════════════════════════════════════════════════════════════
def tab_advanced_strategies(data: dict, parlays_callback=None):
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
        logged_players = []
        for name in player_names:
            p = player_map.get(name)
            if not p:
                continue
            odds = p.get("fanduel_american") or p.get("best_american")
            label = f"{p['player_name']} ({p.get('team', '')}) {_fmt_american(odds)}"
            if label not in current:
                current.append(label)
                added += 1
                logged_players.append(p)
        if added:
            st.session_state["fd_slip"] = current
            st.session_state.pop("fd_slip_select", None)
            # Log to strategy tracker and unified pick tracker
            try:
                from tracking import strategy_log as _sl
                from tracking import pick_tracker as _pt
                for p in logged_players:
                    _sl.log_pick(p, strategy_type)
                    _pt.log_pick(p, "Strategies", strategy_type)
            except Exception:
                pass
            st.toast(f"✅ {added} player{'s' if added != 1 else ''} added to FD Slip!")
            st.rerun()
        return added

    st.markdown('<div class="section-header">🎯 ADVANCED BETTING STRATEGIES</div>', unsafe_allow_html=True)

    # ── Strategy Performance Dashboard ────────────────────────────────────────
    try:
        from tracking import strategy_log as _sl
        _perf_data = _sl.summary()
        _all_picks = _sl.all_picks()
    except Exception:
        _perf_data = []
        _all_picks = []

    _total_tracked = sum(r["Picks"] for r in _perf_data)
    _total_decided = sum(r["_decided"] for r in _perf_data)
    _total_wins    = sum(r["Wins"] for r in _perf_data)
    _total_profit  = sum(r["_profit"] for r in _perf_data)
    _perf_label = (
        f"📊 Strategy Performance  —  {_total_tracked} picks tracked"
        + (f"  ·  {_total_wins}/{_total_decided} wins" if _total_decided else "")
        + (f"  ·  Net ${_total_profit:+.2f}" if _total_decided else "")
    )

    with st.expander(_perf_label, expanded=False):
        if not _perf_data:
            st.info("No strategy picks logged yet. Add players to your FD Slip from any strategy below to start tracking.")
        else:
            # Summary table
            import pandas as pd
            _display_cols = ["Strategy", "Picks", "Wins", "Losses", "Pending", "Win%", "Net P&L", "ROI%", "Last Pick"]
            _df = pd.DataFrame(_perf_data)[_display_cols]

            def _color_roi(val):
                if val == "—":
                    return "color: #666666"
                return "color: #4ade80" if val.startswith("+") else "color: #f87171"

            def _color_pl(val):
                if val == "—":
                    return "color: #666666"
                return "color: #4ade80" if val.startswith("$+") else "color: #f87171"

            styled = (
                _df.style
                .applymap(_color_roi, subset=["ROI%"])
                .applymap(_color_pl, subset=["Net P&L"])
                .set_properties(**{"font-size": "12px"})
            )
            st.dataframe(styled, hide_index=True, use_container_width=True)

            # Per-strategy breakdown (bar chart style using metrics)
            if _total_decided > 0:
                st.markdown("**Win Rate by Strategy** (decided picks only)")
                _decided_strats = [r for r in _perf_data if r["_decided"] > 0]
                if _decided_strats:
                    _cols = st.columns(min(len(_decided_strats), 4))
                    for _ci, _r in enumerate(_decided_strats[:4]):
                        with _cols[_ci % 4]:
                            _wr = _r["_win_rate"] * 100
                            _roi_val = _r["_roi"]
                            _roi_str = f"{_roi_val:+.1f}%"
                            st.metric(
                                _r["Strategy"][:22],
                                f"{_wr:.0f}% ({_r['Wins']}/{_r['_decided']})",
                                delta=_roi_str,
                                delta_color="normal",
                            )

            st.divider()

            # Recent picks log
            st.markdown("**Recent Strategy Picks**")
            if _all_picks:
                _recent = _all_picks[:25]
                _pick_rows = []
                for _pk in _recent:
                    _hr = _pk.get("hr_result", "")
                    _pl_val = _pk.get("profit_loss", "")
                    _result_str = "✅ HR" if _hr == "1" else ("❌ No HR" if _hr == "0" else "⏳ Pending")
                    _pl_str = f"${float(_pl_val):+.2f}" if _pl_val else "—"
                    _pick_rows.append({
                        "Date":       _pk.get("date", ""),
                        "Strategy":   _pk.get("strategy", ""),
                        "Player":     _pk.get("player_name", ""),
                        "Team":       _pk.get("team", ""),
                        "Odds":       _pk.get("american_odds", ""),
                        "Model%":     _pk.get("model_prob_pct", ""),
                        "EV%":        _pk.get("ev_pct", ""),
                        "Result":     _result_str,
                        "P&L":        _pl_str,
                    })
                _log_df = pd.DataFrame(_pick_rows)

                def _color_result(val):
                    if "HR" in val and "No" not in val:
                        return "color: #4ade80"
                    if "No HR" in val:
                        return "color: #f87171"
                    return "color: #888888"

                def _color_pnl(val):
                    if val == "—":
                        return "color: #666666"
                    try:
                        return "color: #4ade80" if float(val.replace("$","").replace("+","")) > 0 else "color: #f87171"
                    except ValueError:
                        return "color: #666666"

                _log_styled = (
                    _log_df.style
                    .applymap(_color_result, subset=["Result"])
                    .applymap(_color_pnl,   subset=["P&L"])
                    .set_properties(**{"font-size": "11px"})
                )
                st.dataframe(_log_styled, hide_index=True, use_container_width=True)
            else:
                st.caption("No picks logged yet.")

    # Strategy selector
    strategy_type = st.selectbox(
        "Select Strategy Type",
        [
            "🎰 Parlays",
            "Correlation Parlays",
            "Team Stacks",
            "Value Bomb Parlays",
            "Power Profile Parlays",
            "Lineup Heart Parlays",
            "Park Monster Parlays",
            "Pitcher Target Parlays",
            "Platoon Advantage Parlays",
            "Weather Boost Parlays",
            "Hot Streak Parlays",
            "Stars Aligned",
            "xStats Regression",
            "Short Rest Pitcher Target",
            "Long Shot Value",
            "Multi-Edge Confirmation",
            "Same-Game Builder",
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

        # Build lookup for modal triggers — set session_state["show_modal"]; fired by main()
        _player_map = {p["player_name"]: p for p in all_players if p.get("player_name")}

        def _player_row(player_name: str, team: str, meta: str, modal_key: str):
            """Render a player as a clickable button (opens modal) + stats caption + FD link."""
            _rc1, _rc2 = st.columns([5, 1])
            with _rc1:
                if st.button(
                    f"• {player_name}",
                    key=modal_key,
                    help=f"View full stats for {player_name}",
                    use_container_width=True,
                ):
                    st.session_state["show_modal"] = _player_map.get(
                        player_name, {"player_name": player_name}
                    )
                    st.rerun()
                _parts = ([f"({team})"] if team else []) + ([meta] if meta else [])
                if _parts:
                    st.markdown(
                        f"<div style='font-size:11px; color:#888888; margin:-6px 0 4px 8px;'>"
                        f"{'  ·  '.join(_parts)}</div>",
                        unsafe_allow_html=True,
                    )
            with _rc2:
                st.link_button("FD →", _fd_url(player_name), use_container_width=True)

        def _diverse_top(parlays: list, limit: int = 10) -> list:
            """Each player appears in at most one slip; slips ranked by best combined odds."""
            used: set = set()
            result = []
            for p in sorted(parlays, key=lambda x: x.get("american_odds", 0), reverse=True):
                legs = p.get("legs", [])
                if not any(name in used for name in legs):
                    result.append(p)
                    used.update(legs)
                    if len(result) >= limit:
                        break
            return result

        if strategy_type == "🎰 Parlays":
            if parlays_callback is not None:
                parlays_callback(data)
            else:
                st.warning("Parlays view not available.")

        elif strategy_type == "Correlation Parlays":
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
            corr_parlays = _diverse_top(_cached_corr_parlays(_cache_key))

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
                        for j, (player, team) in enumerate(zip(parlay['legs'], parlay['teams'])):
                            _player_row(player, team, "", f"modal_corr_{i}_{j}")

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
            _raw_stacks = _cached_stacks(_stack_key)
            # Deduplicate: each player in at most one displayed stack
            _used_in_stack: set = set()
            stacks = []
            for _s in (_raw_stacks or []):
                _snames = _s.get("players", [])
                if not any(n in _used_in_stack for n in _snames):
                    stacks.append(_s)
                    _used_in_stack.update(_snames)

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
                        for j, (player, spot) in enumerate(zip(stack['players'], stack['lineup_spots'])):
                            spot_str = f"#{spot}" if spot else "?"
                            _player_row(player, stack['team'], f"Spot {spot_str}", f"modal_stack_{i}_{j}")

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
                return _diverse_top(sorted(bombs, key=lambda x: x["ev_pct"], reverse=True))

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
                        for j, (player, team, ev_e, odds_e) in enumerate(zip(b['legs'], b['teams'], b['ev_each'], b['odds_each'])):
                            _player_row(player, team, f"EV {ev_e:+.1f}%  {_fmt_american(odds_e)}", f"modal_vb_{i}_{j}")
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
                def _to_float(val, default=0.0):
                    try:
                        return float(str(val).replace("%", "").strip())
                    except (TypeError, ValueError):
                        return default

                def _power_score(p):
                    brl = _to_float(p.get("barrel_pct") or p.get("brl_pct"))
                    ev  = _to_float(p.get("exit_velo"))
                    gb  = _to_float(p.get("gb_pct"), default=50.0)
                    pf  = _to_float(p.get("pitcher_factor"), default=1.0)
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
                                "barrel_pcts": [_to_float(p.get("barrel_pct") or p.get("brl_pct")) for p in combo],
                                "exit_velos": [_to_float(p.get("exit_velo")) for p in combo],
                                "base_prob": base_prob,
                                "parlay_odds": parlay_odds,
                                "american_odds": _dta(parlay_odds),
                                "ev_pct": ev * 100,
                                "n_legs": n_legs,
                            })
                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

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
                        for j, (player, team, pwr, brl, evo) in enumerate(zip(pp['legs'], pp['teams'], pp['power_scores'], pp['barrel_pcts'], pp['exit_velos'])):
                            brl_str = f"Brl {brl:.1f}%" if brl else ""
                            evo_str = f"EV {evo:.1f}" if evo else ""
                            meta = "  ·  ".join(filter(None, [brl_str, evo_str]))
                            _player_row(player, team, meta, f"modal_pp_{i}_{j}")
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

                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

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
                        for j, (player, team, spot) in enumerate(zip(hp['legs'], hp['teams'], hp['spots'])):
                            _player_row(player, team, f"Spot #{spot}", f"modal_lh_{i}_{j}")
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
                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

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
                        for j, (player, team, pf) in enumerate(zip(par['legs'], par['teams'], par['park_factors'])):
                            _player_row(player, team, f"Park {pf:.2f}x", f"modal_park_{i}_{j}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_park_{i}"):
                                n = _add_to_fd_slip(par['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No park monster parlays found — no games in hitter-friendly parks today")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Pitcher Target Parlays":
            st.markdown("### 🎯 Pitcher Target Parlays")
            st.info(
                "Stack multiple hitters against the same HR-prone starting pitcher. "
                "When a leaky arm is on the mound, the whole opposing lineup benefits — "
                "and their HRs are correlated through the shared matchup."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_pitcher_targets(player_ids: tuple):
                from collections import defaultdict
                # Group qualified players (model_prob >= 0.07, has odds) by opponent pitcher
                by_pitcher = defaultdict(list)
                for p in all_players:
                    if p.get("model_prob", 0) < 0.07 or not p.get("best_american"):
                        continue
                    pid_name = p.get("pitcher_name", "TBD")
                    if pid_name and pid_name != "TBD":
                        by_pitcher[pid_name].append(p)

                parlays = []
                for pitcher_name, hitters in by_pitcher.items():
                    if len(hitters) < 2:
                        continue
                    # Use the pitcher factor from any hitter facing this pitcher
                    avg_pit_fac = sum(h.get("pitcher_factor", 1.0) for h in hitters) / len(hitters)
                    avg_pit_hr9 = sum(h.get("pitcher_hr9", 0.0) for h in hitters) / len(hitters)
                    if avg_pit_fac < 1.05 and avg_pit_hr9 < 1.2:
                        continue  # pitcher isn't particularly HR-prone

                    hitters_sorted = sorted(hitters, key=lambda h: h.get("model_prob", 0), reverse=True)
                    for n_legs in (2, 3):
                        pool = hitters_sorted[:min(n_legs + 3, len(hitters_sorted))]
                        for combo in itertools.combinations(pool, n_legs):
                            base_prob = 1.0
                            parlay_odds = 1.0
                            for h in combo:
                                base_prob *= h.get("model_prob", 0)
                                parlay_odds *= _ato_d(h["best_american"])
                            # Same-pitcher correlation boost: 8% per leg above 1
                            corr_boost = 1.0 + 0.08 * (n_legs - 1)
                            adj_prob = min(base_prob * corr_boost, 0.30)
                            ev = (parlay_odds * adj_prob) - 1
                            if ev > 0:
                                parlays.append({
                                    "pitcher_name": pitcher_name,
                                    "pitcher_factor": round(avg_pit_fac, 3),
                                    "pitcher_hr9":   round(avg_pit_hr9, 2),
                                    "legs":          [h["player_name"] for h in combo],
                                    "teams":         [h.get("team", "") for h in combo],
                                    "model_probs":   [round(h.get("model_prob", 0) * 100, 1) for h in combo],
                                    "odds_each":     [h["best_american"] for h in combo],
                                    "corr_boost":    corr_boost,
                                    "base_prob":     base_prob,
                                    "adj_prob":      adj_prob,
                                    "parlay_odds":   parlay_odds,
                                    "american_odds": _dta(parlay_odds),
                                    "ev_pct":        ev * 100,
                                    "n_legs":        n_legs,
                                })
                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

            _pt_key = tuple(p.get("player_name", "") for p in all_players)
            pt_parlays = _cached_pitcher_targets(_pt_key)

            if pt_parlays:
                for i, pt in enumerate(pt_parlays, 1):
                    pf_color = "#ff5722" if pt["pitcher_factor"] >= 1.20 else "#ff9800"
                    label = (
                        f"vs {pt['pitcher_name']}  |  "
                        f"{pt['n_legs']}-leg  |  "
                        f"EV {pt['ev_pct']:+.1f}%  |  "
                        f"Pitcher fac {pt['pitcher_factor']:.2f}x"
                    )
                    with st.expander(label):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Parlay EV", f"{pt['ev_pct']:+.1f}%")
                            st.metric("Adj. Probability", f"{pt['adj_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(pt['american_odds']))
                            st.metric("Corr Boost", f"+{(pt['corr_boost']-1)*100:.0f}%")
                        with col3:
                            st.metric("Pitcher HR Factor", f"{pt['pitcher_factor']:.2f}x")
                            st.metric("Pitcher HR/9", f"{pt['pitcher_hr9']:.2f}")
                        st.write(f"**Hitters vs {pt['pitcher_name']}:**")
                        for j, (player, team, mp, odds_e) in enumerate(zip(
                            pt['legs'], pt['teams'], pt['model_probs'], pt['odds_each']
                        )):
                            _player_row(player, team, f"Model {mp:.1f}%  {_fmt_american(odds_e)}", f"modal_pt_{i}_{j}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_pt_{i}"):
                                n = _add_to_fd_slip(pt['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No profitable pitcher-target parlays found — try refreshing after lineups post.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Platoon Advantage Parlays":
            st.markdown("### ⚡ Platoon Advantage Parlays")
            st.info(
                "Players with the strongest handedness edge against today's starter. "
                "A platoon factor above 1.10 means the batter hits for meaningfully more "
                "power from this side of the plate — a repeatable, book-beating edge."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_platoon_parlays(player_ids: tuple):
                candidates = sorted(
                    [p for p in all_players
                     if p.get("platoon_factor", 1.0) >= 1.08
                     and p.get("model_prob", 0) >= 0.07
                     and p.get("best_american")],
                    key=lambda p: p.get("platoon_factor", 1.0) * p.get("model_prob", 0),
                    reverse=True,
                )[:20]

                parlays = []
                for n_legs in (2, 3):
                    pool = candidates if n_legs == 2 else candidates[:12]
                    for combo in itertools.combinations(pool, n_legs):
                        base_prob = 1.0
                        parlay_odds = 1.0
                        avg_plat = sum(p.get("platoon_factor", 1.0) for p in combo) / len(combo)
                        for p in combo:
                            base_prob *= p.get("model_prob", 0)
                            parlay_odds *= _ato_d(p["best_american"])
                        ev = (parlay_odds * base_prob) - 1
                        if ev > 0:
                            parlays.append({
                                "legs":           [p["player_name"] for p in combo],
                                "teams":          [p.get("team", "") for p in combo],
                                "platoon_factors":[round(p.get("platoon_factor", 1.0), 3) for p in combo],
                                "pitchers":       [p.get("pitcher_name", "TBD") for p in combo],
                                "model_probs":    [round(p.get("model_prob", 0) * 100, 1) for p in combo],
                                "avg_platoon":    round(avg_plat, 3),
                                "base_prob":      base_prob,
                                "parlay_odds":    parlay_odds,
                                "american_odds":  _dta(parlay_odds),
                                "ev_pct":         ev * 100,
                                "n_legs":         n_legs,
                            })
                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

            _plat_key = tuple(p.get("player_name", "") for p in all_players)
            plat_parlays = _cached_platoon_parlays(_plat_key)

            if plat_parlays:
                for i, pp in enumerate(plat_parlays, 1):
                    label = (
                        f"{pp['n_legs']}-Leg Platoon #{i}  |  "
                        f"EV {pp['ev_pct']:+.1f}%  |  "
                        f"Avg Platoon Edge {pp['avg_platoon']:.2f}x"
                    )
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Parlay EV", f"{pp['ev_pct']:+.1f}%")
                            st.metric("Hit Probability", f"{pp['base_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(pp['american_odds']))
                            st.metric("Avg Platoon Factor", f"{pp['avg_platoon']:.2f}x")
                        st.write("**Players:**")
                        for j, (player, team, plat, pitcher, mp) in enumerate(zip(
                            pp['legs'], pp['teams'], pp['platoon_factors'],
                            pp['pitchers'], pp['model_probs']
                        )):
                            _player_row(player, team, f"Platoon {plat:.2f}x  vs {pitcher}  Model {mp:.1f}%", f"modal_plat_{i}_{j}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_plat_{i}"):
                                n = _add_to_fd_slip(pp['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No platoon-advantage parlays found — may need lineups and pitcher hands posted.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Weather Boost Parlays":
            st.markdown("### ☀️ Weather Boost Parlays")
            st.info(
                "Games with favorable conditions — warm temps and wind blowing out to center. "
                "Hot, thin air lets the ball carry farther. Wind-out adds 3–10% per mph. "
                "Dome teams always receive a neutral factor."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_weather_parlays(player_ids: tuple):
                MIN_WEATHER = 1.04
                candidates = sorted(
                    [p for p in all_players
                     if p.get("weather_factor", 1.0) >= MIN_WEATHER
                     and p.get("model_prob", 0) >= 0.07
                     and p.get("best_american")],
                    key=lambda p: p.get("weather_factor", 1.0) * p.get("model_prob", 0),
                    reverse=True,
                )[:20]

                parlays = []
                for n_legs in (2, 3):
                    pool = candidates if n_legs == 2 else candidates[:12]
                    for combo in itertools.combinations(pool, n_legs):
                        base_prob = 1.0
                        parlay_odds = 1.0
                        avg_wx = sum(p.get("weather_factor", 1.0) for p in combo) / len(combo)
                        for p in combo:
                            base_prob *= p.get("model_prob", 0)
                            parlay_odds *= _ato_d(p["best_american"])
                        ev = (parlay_odds * base_prob) - 1
                        if ev > 0:
                            parlays.append({
                                "legs":            [p["player_name"] for p in combo],
                                "teams":           [p.get("team", "") for p in combo],
                                "weather_factors": [round(p.get("weather_factor", 1.0), 3) for p in combo],
                                "home_teams":      [p.get("home_team", "") for p in combo],
                                "avg_weather":     round(avg_wx, 3),
                                "base_prob":       base_prob,
                                "parlay_odds":     parlay_odds,
                                "american_odds":   _dta(parlay_odds),
                                "ev_pct":          ev * 100,
                                "n_legs":          n_legs,
                            })
                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

            _wx_key = tuple(p.get("player_name", "") for p in all_players)
            wx_parlays = _cached_weather_parlays(_wx_key)

            if wx_parlays:
                for i, wx in enumerate(wx_parlays, 1):
                    label = (
                        f"{wx['n_legs']}-Leg Weather #{i}  |  "
                        f"EV {wx['ev_pct']:+.1f}%  |  "
                        f"Avg Weather {wx['avg_weather']:.2f}x"
                    )
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Parlay EV", f"{wx['ev_pct']:+.1f}%")
                            st.metric("Hit Probability", f"{wx['base_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(wx['american_odds']))
                            st.metric("Avg Weather Factor", f"{wx['avg_weather']:.3f}x")
                        st.write("**Players:**")
                        for j, (player, team, wf, ht) in enumerate(zip(
                            wx['legs'], wx['teams'], wx['weather_factors'], wx['home_teams']
                        )):
                            _player_row(player, f"{team} @ {ht}", f"Weather {wf:.3f}x", f"modal_wx_{i}_{j}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_wx_{i}"):
                                n = _add_to_fd_slip(wx['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No weather-boost parlays found — no games with strongly favorable conditions today.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Hot Streak Parlays":
            st.markdown("### 🔥 Hot Streak Parlays")
            st.info(
                "Players whose last-10-game HR rate is running above their season average. "
                "The streak factor is capped at ±8% to avoid noise — these are genuine "
                "sustained hot spells, not one-game flukes."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_streak_parlays(player_ids: tuple):
                MIN_STREAK = 1.03
                candidates = sorted(
                    [p for p in all_players
                     if p.get("streak_factor", 1.0) >= MIN_STREAK
                     and p.get("model_prob", 0) >= 0.07
                     and p.get("best_american")],
                    key=lambda p: p.get("streak_factor", 1.0) * p.get("model_prob", 0),
                    reverse=True,
                )[:20]

                parlays = []
                for n_legs in (2, 3):
                    pool = candidates if n_legs == 2 else candidates[:12]
                    for combo in itertools.combinations(pool, n_legs):
                        base_prob = 1.0
                        parlay_odds = 1.0
                        avg_streak = sum(p.get("streak_factor", 1.0) for p in combo) / len(combo)
                        for p in combo:
                            base_prob *= p.get("model_prob", 0)
                            parlay_odds *= _ato_d(p["best_american"])
                        ev = (parlay_odds * base_prob) - 1
                        if ev > 0:
                            parlays.append({
                                "legs":           [p["player_name"] for p in combo],
                                "teams":          [p.get("team", "") for p in combo],
                                "streak_factors": [round(p.get("streak_factor", 1.0), 3) for p in combo],
                                "short_hrs":      [p.get("short_form_hr", 0) for p in combo],
                                "short_pas":      [p.get("short_form_pa", 0) for p in combo],
                                "model_probs":    [round(p.get("model_prob", 0) * 100, 1) for p in combo],
                                "avg_streak":     round(avg_streak, 3),
                                "base_prob":      base_prob,
                                "parlay_odds":    parlay_odds,
                                "american_odds":  _dta(parlay_odds),
                                "ev_pct":         ev * 100,
                                "n_legs":         n_legs,
                            })
                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

            _str_key = tuple(p.get("player_name", "") for p in all_players)
            streak_parlays = _cached_streak_parlays(_str_key)

            if streak_parlays:
                for i, sp in enumerate(streak_parlays, 1):
                    label = (
                        f"{sp['n_legs']}-Leg Hot Streak #{i}  |  "
                        f"EV {sp['ev_pct']:+.1f}%  |  "
                        f"Avg Streak Factor {sp['avg_streak']:.3f}x"
                    )
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Parlay EV", f"{sp['ev_pct']:+.1f}%")
                            st.metric("Hit Probability", f"{sp['base_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(sp['american_odds']))
                            st.metric("Avg Streak Factor", f"{sp['avg_streak']:.3f}x")
                        st.write("**Players (last 10 games):**")
                        for j, (player, team, sf, shr, spa, mp) in enumerate(zip(
                            sp['legs'], sp['teams'], sp['streak_factors'],
                            sp['short_hrs'], sp['short_pas'], sp['model_probs']
                        )):
                            recent_str = f"{shr} HR / {spa} PA" if spa > 0 else "recent data N/A"
                            _player_row(player, team, f"Streak {sf:.3f}x  |  Last 10: {recent_str}  |  Model {mp:.1f}%", f"modal_str_{i}_{j}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_str_{i}"):
                                n = _add_to_fd_slip(sp['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No hot-streak parlays found — players may not have 8+ recent PA yet.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Stars Aligned":
            st.markdown("### ⭐ Stars Aligned")
            st.info(
                "Players where every game-day factor is working in their favor: "
                "hitter-friendly park, HR-prone pitcher, favorable weather, and a platoon edge. "
                "These are the 'everything is right today' plays — rare but highest-conviction."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_stars_aligned(player_ids: tuple):
                def _alignment_score(p) -> float:
                    park    = p.get("park_factor",    1.0)
                    pit     = p.get("pitcher_factor", 1.0)
                    wx      = p.get("weather_factor", 1.0)
                    plat    = p.get("platoon_factor", 1.0)
                    streak  = p.get("streak_factor",  1.0)
                    # Score = product of all factors > 1.0; penalize any factor < 1.0
                    raw = (park * pit * wx * plat * streak)
                    penalty = sum(
                        max(0.0, 1.0 - f)
                        for f in [park, pit, wx, plat, streak]
                    )
                    return raw - penalty * 0.5

                candidates = sorted(
                    [p for p in all_players
                     if p.get("park_factor",    1.0) >= 0.98
                     and p.get("pitcher_factor", 1.0) >= 1.00
                     and p.get("weather_factor", 1.0) >= 1.00
                     and p.get("platoon_factor", 1.0) >= 1.00
                     and p.get("model_prob",     0.0) >= 0.08
                     and p.get("best_american")],
                    key=_alignment_score,
                    reverse=True,
                )[:20]

                parlays = []
                for n_legs in (2, 3):
                    pool = candidates if n_legs == 2 else candidates[:12]
                    for combo in itertools.combinations(pool, n_legs):
                        base_prob = 1.0
                        parlay_odds = 1.0
                        for p in combo:
                            base_prob *= p.get("model_prob", 0)
                            parlay_odds *= _ato_d(p["best_american"])
                        ev = (parlay_odds * base_prob) - 1
                        if ev > 0:
                            parlays.append({
                                "legs":     [p["player_name"] for p in combo],
                                "teams":    [p.get("team", "") for p in combo],
                                "factors":  [{
                                    "park":    round(p.get("park_factor",    1.0), 3),
                                    "pitcher": round(p.get("pitcher_factor", 1.0), 3),
                                    "weather": round(p.get("weather_factor", 1.0), 3),
                                    "platoon": round(p.get("platoon_factor", 1.0), 3),
                                    "streak":  round(p.get("streak_factor",  1.0), 3),
                                } for p in combo],
                                "scores":        [round(_alignment_score(p), 3) for p in combo],
                                "base_prob":     base_prob,
                                "parlay_odds":   parlay_odds,
                                "american_odds": _dta(parlay_odds),
                                "ev_pct":        ev * 100,
                                "n_legs":        n_legs,
                            })
                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

            _sa_key = tuple(p.get("player_name", "") for p in all_players)
            sa_parlays = _cached_stars_aligned(_sa_key)

            if sa_parlays:
                for i, sa in enumerate(sa_parlays, 1):
                    avg_score = sum(sa["scores"]) / len(sa["scores"])
                    label = (
                        f"{sa['n_legs']}-Leg Stars Aligned #{i}  |  "
                        f"EV {sa['ev_pct']:+.1f}%  |  "
                        f"Avg Alignment {avg_score:.3f}"
                    )
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Parlay EV", f"{sa['ev_pct']:+.1f}%")
                            st.metric("Hit Probability", f"{sa['base_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(sa['american_odds']))
                            st.metric("Avg Alignment Score", f"{avg_score:.3f}")
                        for j, (player, team, fac, score) in enumerate(zip(
                            sa['legs'], sa['teams'], sa['factors'], sa['scores']
                        )):
                            factor_parts = [
                                f"Park {fac['park']:.2f}x",
                                f"Pit {fac['pitcher']:.2f}x",
                                f"Wx {fac['weather']:.2f}x",
                                f"Plat {fac['platoon']:.2f}x",
                                f"Streak {fac['streak']:.3f}x",
                            ]
                            _player_row(player, team, "  ·  ".join(factor_parts), f"modal_sa_{i}_{j}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_sa_{i}"):
                                n = _add_to_fd_slip(sa['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning(
                    "No stars-aligned plays found — today's games may have mixed conditions "
                    "(suppressive park, tough pitcher, or bad weather for some players)."
                )
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "xStats Regression":
            st.markdown("### 📈 xStats Regression Candidates")
            st.info(
                "Players where expected SLG (xSLG) is ≥15% higher than actual SLG — "
                "their underlying contact quality exceeds their results. "
                "Positive regression is likely: the market underprices them."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_xstats_regression(player_ids: tuple):
                def _to_float(val, default=0.0):
                    try:
                        return float(str(val).replace("%", "").strip())
                    except (TypeError, ValueError):
                        return default

                candidates = []
                for p in all_players:
                    xslg = _to_float(p.get("xslg") or p.get("x_slg"))
                    slg  = _to_float(p.get("slg"))
                    if xslg <= 0 or slg <= 0:
                        continue
                    regression_gap = (xslg - slg) / slg if slg > 0 else 0
                    if regression_gap < 0.15:
                        continue
                    if p.get("model_prob", 0) < 0.06:
                        continue
                    candidates.append({
                        **p,
                        "_xslg": xslg,
                        "_slg":  slg,
                        "_gap":  regression_gap,
                    })
                return sorted(candidates, key=lambda x: x["_gap"], reverse=True)[:15]

            _xsr_key = tuple(p.get("player_name", "") for p in all_players)
            xsr_players = _cached_xstats_regression(_xsr_key)

            if xsr_players:
                # Deduplicate: each player once
                _used_xsr: set = set()
                for i, p in enumerate(xsr_players, 1):
                    name = p.get("player_name", "")
                    if name in _used_xsr:
                        continue
                    _used_xsr.add(name)
                    gap_pct = p["_gap"] * 100
                    label = (
                        f"#{i} {name}  |  "
                        f"xSLG {p['_xslg']:.3f} vs SLG {p['_slg']:.3f}  |  "
                        f"Gap +{gap_pct:.1f}%  |  Model {p.get('model_prob',0)*100:.1f}%"
                    )
                    with st.expander(label):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("xSLG", f"{p['_xslg']:.3f}")
                            st.metric("Actual SLG", f"{p['_slg']:.3f}")
                        with col2:
                            st.metric("Regression Gap", f"+{gap_pct:.1f}%")
                            st.metric("Model Prob", f"{p.get('model_prob',0)*100:.1f}%")
                        with col3:
                            st.metric("Market Odds", _fmt_american(p.get("best_american")))
                            st.metric("EV%", f"{p.get('ev_pct',0):+.1f}%")
                        _player_row(name, p.get("team",""), f"xSLG {p['_xslg']:.3f}  ·  SLG {p['_slg']:.3f}  ·  Gap +{gap_pct:.1f}%", f"modal_xsr_{i}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add to FD Slip", key=f"fd_xsr_{i}"):
                                n = _add_to_fd_slip([name], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No xStats regression candidates found — xSLG data may not be loaded yet.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Short Rest Pitcher Target":
            st.markdown("### ⏱️ Short Rest Pitcher Target")
            st.info(
                "Batters facing a starting pitcher on ≤3 days rest. "
                "Short-rest arms show measurably lower velocity and command — "
                "more mistakes in the zone means more HR opportunity for hitters."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_short_rest(player_ids: tuple):
                from collections import defaultdict
                sr_players = [
                    p for p in all_players
                    if p.get("pitcher_days_rest") is not None
                    and int(p.get("pitcher_days_rest", 99)) <= 3
                    and p.get("model_prob", 0) >= 0.06
                    and p.get("best_american")
                ]
                by_pitcher = defaultdict(list)
                for p in sr_players:
                    by_pitcher[p.get("pitcher_name", "TBD")].append(p)

                parlays = []
                for pit_name, hitters in by_pitcher.items():
                    days = int(hitters[0].get("pitcher_days_rest", 99))
                    pit_fac = hitters[0].get("pitcher_factor", 1.0)
                    # Short rest boost: 1 day = +12%, 2 days = +8%, 3 days = +5%
                    rest_boost = {1: 1.12, 2: 1.08, 3: 1.05}.get(days, 1.0)
                    hitters_sorted = sorted(hitters, key=lambda h: h.get("model_prob", 0), reverse=True)
                    for n_legs in (2, 3) if len(hitters_sorted) >= 2 else (1,):
                        if n_legs == 1:
                            h = hitters_sorted[0]
                            parlays.append({
                                "pitcher_name": pit_name,
                                "days_rest": days,
                                "rest_boost": rest_boost,
                                "pitcher_factor": round(pit_fac, 3),
                                "legs": [h["player_name"]],
                                "teams": [h.get("team", "")],
                                "model_probs": [round(h.get("model_prob", 0) * 100, 1)],
                                "odds_each": [h.get("best_american")],
                                "base_prob": h.get("model_prob", 0),
                                "adj_prob": min(h.get("model_prob", 0) * rest_boost, 0.35),
                                "parlay_odds": _ato_d(h["best_american"]),
                                "american_odds": h["best_american"],
                                "ev_pct": ((_ato_d(h["best_american"]) * min(h.get("model_prob",0)*rest_boost, 0.35)) - 1) * 100,
                                "n_legs": 1,
                            })
                            continue
                        pool = hitters_sorted[:min(n_legs + 2, len(hitters_sorted))]
                        for combo in itertools.combinations(pool, n_legs):
                            base_prob = 1.0
                            parlay_odds = 1.0
                            for h in combo:
                                base_prob *= h.get("model_prob", 0)
                                parlay_odds *= _ato_d(h["best_american"])
                            adj_prob = min(base_prob * rest_boost * (1.0 + 0.06 * (n_legs - 1)), 0.35)
                            ev = (parlay_odds * adj_prob) - 1
                            if ev > 0:
                                parlays.append({
                                    "pitcher_name": pit_name,
                                    "days_rest": days,
                                    "rest_boost": rest_boost,
                                    "pitcher_factor": round(pit_fac, 3),
                                    "legs": [h["player_name"] for h in combo],
                                    "teams": [h.get("team", "") for h in combo],
                                    "model_probs": [round(h.get("model_prob",0)*100,1) for h in combo],
                                    "odds_each": [h["best_american"] for h in combo],
                                    "base_prob": base_prob,
                                    "adj_prob": adj_prob,
                                    "parlay_odds": parlay_odds,
                                    "american_odds": _dta(parlay_odds),
                                    "ev_pct": ev * 100,
                                    "n_legs": n_legs,
                                })
                return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))

            _sr_key = tuple(p.get("player_name", "") for p in all_players)
            sr_parlays = _cached_short_rest(_sr_key)

            if sr_parlays:
                for i, sr in enumerate(sr_parlays, 1):
                    rest_tag = f"{sr['days_rest']}d rest" if sr['days_rest'] else "short rest"
                    label = (
                        f"vs {sr['pitcher_name']} ({rest_tag})  |  "
                        f"{sr['n_legs']}-leg  |  EV {sr['ev_pct']:+.1f}%  |  "
                        f"Rest Boost +{(sr['rest_boost']-1)*100:.0f}%"
                    )
                    with st.expander(label):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Parlay EV", f"{sr['ev_pct']:+.1f}%")
                            st.metric("Adj. Probability", f"{sr['adj_prob']*100:.2f}%")
                        with col2:
                            st.metric("American Odds", _fmt_american(sr['american_odds']))
                            st.metric("Rest Boost", f"+{(sr['rest_boost']-1)*100:.0f}%")
                        with col3:
                            st.metric("Days Rest", sr['days_rest'])
                            st.metric("Pitcher Factor", f"{sr['pitcher_factor']:.2f}x")
                        st.write(f"**Hitters vs {sr['pitcher_name']} ({rest_tag}):**")
                        for j, (player, team, mp, odds_e) in enumerate(zip(
                            sr['legs'], sr['teams'], sr['model_probs'], sr['odds_each']
                        )):
                            _player_row(player, team, f"Model {mp:.1f}%  {_fmt_american(odds_e)}", f"modal_sr_{i}_{j}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add All to FD Slip", key=f"fd_sr_{i}"):
                                n = _add_to_fd_slip(sr['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No short-rest pitcher matchups found — all starters appear to be on normal rest.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Long Shot Value":
            st.markdown("### 🎲 Long Shot Value")
            st.info(
                "Players priced at +350 or longer where the model finds positive EV and ≥6% probability. "
                "These are mispriced long shots — the market overestimates the difficulty. "
                "Small stakes, big upside."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_long_shots(player_ids: tuple):
                candidates = sorted(
                    [p for p in all_players
                     if p.get("best_american", 0) >= 350
                     and p.get("ev_pct", 0) > 0
                     and p.get("model_prob", 0) >= 0.06],
                    key=lambda p: p.get("ev_pct", 0),
                    reverse=True,
                )[:20]
                # Build single-player slips and 2-leg combos
                result = []
                _used: set = set()
                for p in candidates:
                    name = p.get("player_name", "")
                    if name not in _used:
                        result.append({
                            "legs": [name],
                            "teams": [p.get("team", "")],
                            "model_probs": [round(p.get("model_prob", 0) * 100, 1)],
                            "odds_each": [p.get("best_american")],
                            "ev_pcts": [round(p.get("ev_pct", 0), 1)],
                            "barrel_pcts": [p.get("barrel_pct") or p.get("brl_pct")],
                            "american_odds": p.get("best_american"),
                            "base_prob": p.get("model_prob", 0),
                            "ev_pct": p.get("ev_pct", 0),
                            "n_legs": 1,
                        })
                        _used.add(name)
                # Add 2-leg long shot parlays
                for combo in itertools.combinations(candidates[:10], 2):
                    p1, p2 = combo
                    if p1.get("player_name") in _used or p2.get("player_name") in _used:
                        continue
                    base_prob = p1.get("model_prob", 0) * p2.get("model_prob", 0)
                    parlay_odds = _ato_d(p1["best_american"]) * _ato_d(p2["best_american"])
                    ev = (parlay_odds * base_prob) - 1
                    if ev > 0:
                        result.append({
                            "legs": [p1["player_name"], p2["player_name"]],
                            "teams": [p1.get("team",""), p2.get("team","")],
                            "model_probs": [round(p1.get("model_prob",0)*100,1), round(p2.get("model_prob",0)*100,1)],
                            "odds_each": [p1["best_american"], p2["best_american"]],
                            "ev_pcts": [round(p1.get("ev_pct",0),1), round(p2.get("ev_pct",0),1)],
                            "barrel_pcts": [p1.get("barrel_pct") or p1.get("brl_pct"), p2.get("barrel_pct") or p2.get("brl_pct")],
                            "american_odds": _dta(parlay_odds),
                            "base_prob": base_prob,
                            "ev_pct": ev * 100,
                            "n_legs": 2,
                        })
                return sorted(result, key=lambda x: x["ev_pct"], reverse=True)[:15]

            _ls_key = tuple(p.get("player_name", "") for p in all_players)
            long_shots = _cached_long_shots(_ls_key)

            if long_shots:
                for i, ls in enumerate(long_shots, 1):
                    legs_tag = "Single" if ls['n_legs'] == 1 else f"{ls['n_legs']}-Leg Parlay"
                    label = (
                        f"{legs_tag} #{i}  |  "
                        f"Odds {_fmt_american(ls['american_odds'])}  |  "
                        f"EV {ls['ev_pct']:+.1f}%"
                    )
                    with st.expander(label):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Market Odds", _fmt_american(ls['american_odds']))
                            st.metric("Model Prob", f"{ls['base_prob']*100:.1f}%")
                        with col2:
                            st.metric("EV%", f"{ls['ev_pct']:+.1f}%")
                            st.metric("Legs", ls['n_legs'])
                        st.write("**Players:**")
                        for j, (player, team, mp, odds_e, ev_e) in enumerate(zip(
                            ls['legs'], ls['teams'], ls['model_probs'], ls['odds_each'], ls['ev_pcts']
                        )):
                            _player_row(player, team, f"Model {mp:.1f}%  {_fmt_american(odds_e)}  EV {ev_e:+.1f}%", f"modal_ls_{i}_{j}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add to FD Slip", key=f"fd_ls_{i}"):
                                n = _add_to_fd_slip(ls['legs'], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No mispriced long shots found — market pricing looks accurate at +350+ today.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Multi-Edge Confirmation":
            st.markdown("### 🔬 Multi-Edge Confirmation")
            st.info(
                "Players simultaneously clearing 3 or more independent edge criteria: "
                "park factor ≥1.05, pitcher factor ≥1.05, platoon factor ≥1.05, "
                "weather factor ≥1.04, streak factor ≥1.03. "
                "Each confirmed edge is independent — stacking them materially increases conviction."
            )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_multi_edge(player_ids: tuple):
                _THRESHOLDS = {
                    "park":    ("park_factor",    1.05),
                    "pitcher": ("pitcher_factor", 1.05),
                    "platoon": ("platoon_factor", 1.05),
                    "weather": ("weather_factor", 1.04),
                    "streak":  ("streak_factor",  1.03),
                }

                candidates = []
                for p in all_players:
                    if p.get("model_prob", 0) < 0.06 or not p.get("best_american"):
                        continue
                    confirmed = [
                        edge for edge, (field, threshold) in _THRESHOLDS.items()
                        if p.get(field, 1.0) >= threshold
                    ]
                    if len(confirmed) < 3:
                        continue
                    edge_product = 1.0
                    for edge, (field, _) in _THRESHOLDS.items():
                        if edge in confirmed:
                            edge_product *= p.get(field, 1.0)
                    candidates.append({
                        **p,
                        "_confirmed": confirmed,
                        "_edge_count": len(confirmed),
                        "_edge_product": round(edge_product, 4),
                    })
                return sorted(candidates, key=lambda x: (x["_edge_count"], x["_edge_product"]), reverse=True)[:15]

            _me_key = tuple(p.get("player_name", "") for p in all_players)
            me_players = _cached_multi_edge(_me_key)

            if me_players:
                _used_me: set = set()
                for i, p in enumerate(me_players, 1):
                    name = p.get("player_name", "")
                    if name in _used_me:
                        continue
                    _used_me.add(name)
                    edge_labels = {
                        "park":    f"Park {p.get('park_factor',1.0):.2f}x",
                        "pitcher": f"Pit {p.get('pitcher_factor',1.0):.2f}x",
                        "platoon": f"Plat {p.get('platoon_factor',1.0):.2f}x",
                        "weather": f"Wx {p.get('weather_factor',1.0):.2f}x",
                        "streak":  f"Streak {p.get('streak_factor',1.0):.3f}x",
                    }
                    confirmed_str = "  ·  ".join(edge_labels[e] for e in p["_confirmed"])
                    label = (
                        f"#{i} {name}  |  "
                        f"{p['_edge_count']} edges confirmed  |  "
                        f"Model {p.get('model_prob',0)*100:.1f}%  |  "
                        f"EV {p.get('ev_pct',0):+.1f}%"
                    )
                    with st.expander(label):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Edges Confirmed", p["_edge_count"])
                            st.metric("Edge Product", f"{p['_edge_product']:.4f}x")
                        with col2:
                            st.metric("Model Prob", f"{p.get('model_prob',0)*100:.1f}%")
                            st.metric("Market Odds", _fmt_american(p.get("best_american")))
                        with col3:
                            st.metric("EV%", f"{p.get('ev_pct',0):+.1f}%")
                            not_confirmed = [e for e in ("park","pitcher","platoon","weather","streak") if e not in p["_confirmed"]]
                            st.metric("Misses", len(not_confirmed))
                        _player_row(name, p.get("team",""), confirmed_str, f"modal_me_{i}")
                        if not_confirmed:
                            miss_labels = {
                                "park":    f"Park {p.get('park_factor',1.0):.2f}x",
                                "pitcher": f"Pit {p.get('pitcher_factor',1.0):.2f}x",
                                "platoon": f"Plat {p.get('platoon_factor',1.0):.2f}x",
                                "weather": f"Wx {p.get('weather_factor',1.0):.2f}x",
                                "streak":  f"Streak {p.get('streak_factor',1.0):.3f}x",
                            }
                            st.caption(f"Not cleared: {', '.join(miss_labels[e] for e in not_confirmed)}")
                        fd_col, _ = st.columns([1, 2])
                        with fd_col:
                            if st.button("📲 Add to FD Slip", key=f"fd_me_{i}"):
                                n = _add_to_fd_slip([name], all_players)
                                if not n:
                                    st.info("Already in slip.")
            else:
                st.warning("No players clearing 3+ simultaneous edges today.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Same-Game Builder":
            st.markdown("### 🎮 Same-Game Parlay Builder")
            st.info(
                "Pick a specific game and build a parlay from its players. "
                "Same-game parlays carry natural correlation — when the game environment "
                "is good (warm, wind-out, hittable pitcher), multiple HRs become more likely together."
            )

            # Group players by game (home_team is the unique game key)
            from collections import defaultdict
            by_game: dict = defaultdict(list)
            for p in all_players:
                if p.get("best_american"):
                    home = p.get("home_team", "")
                    away_team = p.get("opponent", "") if p.get("team") == home else p.get("team", "")
                    game_label = f"{away_team} @ {home}"
                    by_game[game_label].append(p)

            if not by_game:
                st.warning("No players with odds available. Refresh after lineups post.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())
            else:
                game_options = sorted(by_game.keys())
                selected_game = st.selectbox(
                    "Select a game:",
                    game_options,
                    key="sgb_game_select",
                )
                game_players = sorted(
                    by_game.get(selected_game, []),
                    key=lambda p: p.get("model_prob", 0), reverse=True,
                )

                if game_players:
                    # Show game context from first player
                    gp0 = game_players[0]
                    home = gp0.get("home_team", "")
                    wx_fac  = gp0.get("weather_factor", 1.0)
                    pk_fac  = gp0.get("park_factor",    1.0)

                    meta_parts = [
                        f"Park: **{pk_fac:.2f}x**",
                        f"Weather: **{wx_fac:.2f}x**",
                    ]
                    weather_dict = gp0.get("weather", {})
                    if weather_dict:
                        temp  = weather_dict.get("temp_f", "--")
                        wind  = weather_dict.get("wind_mph", "--")
                        st.caption(
                            f"📍 {selected_game}  |  "
                            + "  |  ".join(meta_parts)
                            + f"  |  🌡️ {temp}°F  💨 {wind} mph"
                        )
                    else:
                        st.caption(f"📍 {selected_game}  |  " + "  |  ".join(meta_parts))

                    # Player selector
                    player_opts  = [p["player_name"] for p in game_players]
                    player_map   = {p["player_name"]: p for p in game_players}
                    selected_legs = st.multiselect(
                        "Select 2–4 players for your parlay:",
                        options=player_opts,
                        max_selections=4,
                        key="sgb_legs",
                        format_func=lambda n: (
                            f"{n}  ({player_map[n].get('team','')})"
                            f"  {_fmt_american(player_map[n].get('best_american'))}"
                            f"  Model {player_map[n].get('model_prob',0)*100:.1f}%"
                        ),
                    )

                    # Quick-reference table
                    rows = []
                    for p in game_players:
                        rows.append({
                            "Player":   p["player_name"],
                            "Team":     p.get("team", ""),
                            "Spot":     f"#{p['lineup_spot']}" if p.get("lineup_spot") else "?",
                            "Odds":     _fmt_american(p.get("best_american")),
                            "Model%":   f"{p.get('model_prob',0)*100:.1f}%",
                            "Pitcher":  p.get("pitcher_name", "TBD"),
                            "Pit Fac":  f"{p.get('pitcher_factor',1.0):.2f}x",
                            "Platoon":  f"{p.get('platoon_factor',1.0):.2f}x",
                            "EV%":      f"{p.get('ev_pct',0):+.1f}%",
                        })

                    import pandas as pd
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

                    if len(selected_legs) >= 2:
                        legs = [player_map[n] for n in selected_legs]
                        base_prob = 1.0
                        parlay_odds = 1.0
                        for p in legs:
                            base_prob *= p.get("model_prob", 0)
                            parlay_odds *= _ato_d(p["best_american"])

                        # SGP correlation boost: players in same game share environment
                        n = len(legs)
                        same_team_pairs = sum(
                            1 for a, b in itertools.combinations(legs, 2)
                            if a.get("team") == b.get("team")
                        )
                        corr_boost = 1.0 + 0.06 * same_team_pairs + 0.03 * (n - 1)
                        adj_prob = min(base_prob * corr_boost, 0.35)
                        ev = (parlay_odds * adj_prob) - 1

                        ev_color = "#4ade80" if ev >= 0 else "#f87171"
                        sign = "+" if ev >= 0 else ""
                        st.markdown(
                            f"<div style='background:#0a0a1a; border:1px solid #1a1a3a; "
                            f"border-radius:8px; padding:12px 16px; margin-top:12px;'>"
                            f"<div style='font-size:13px; font-weight:700; color:#f0f0f0; margin-bottom:8px;'>"
                            f"{'  +  '.join(selected_legs)}</div>"
                            f"<div style='font-size:12px; color:#888;'>"
                            f"Combined odds: <b style='color:#FF6666'>{_fmt_american(_dta(parlay_odds))}</b>"
                            f" &nbsp;|&nbsp; Raw prob: <b style='color:#f0f0f0'>{base_prob*100:.2f}%</b>"
                            f" &nbsp;|&nbsp; Adj prob: <b style='color:#f0f0f0'>{adj_prob*100:.2f}%</b>"
                            f" &nbsp;|&nbsp; EV: <b style='color:{ev_color}'>{sign}{ev*100:.1f}%</b>"
                            f" &nbsp;|&nbsp; Corr boost: +{(corr_boost-1)*100:.0f}%"
                            f"</div></div>",
                            unsafe_allow_html=True,
                        )

                        if st.button("📲 Add All to FD Slip", key="sgb_add_slip"):
                            n_added = _add_to_fd_slip(selected_legs, all_players)
                            if not n_added:
                                st.info("Already in slip.")
                    elif selected_legs:
                        st.caption("Select at least 2 players to calculate parlay odds.")

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
