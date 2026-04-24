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
        ["Correlation Parlays", "Team Stacks", "Hedge Calculator", "Progressive Staking"],
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
