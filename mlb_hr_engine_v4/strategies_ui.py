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
            st.info("Players who historically hit HRs on the same days - smarter parlay construction")

            corr_parlays = find_correlated_parlays(
                players=all_players,
                max_legs=4,
                min_correlation=0.15,
                min_individual_prob=0.08
            )

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
                                if n:
                                    st.success(f"+{n} player{'s' if n != 1 else ''} added to FD Slip!")
                                else:
                                    st.info("Already in slip.")
            else:
                st.warning("No correlation parlays found with current criteria")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())

        elif strategy_type == "Team Stacks":
            st.markdown("### 🏟️ Team Stack Parlays")
            st.info("Multiple players from same team - capitalize on offensive explosions")

            stacks = build_team_stacks(
                players=all_players,
                min_team_size=2,
                max_stack_size=4,
                min_individual_prob=0.08,
                min_stack_ev=10.0
            )

            if stacks:
                for i, stack in enumerate(stacks[:8], 1):
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
            st.info("Calculate optimal hedge bets to guarantee profit or minimize loss")

            col1, col2 = st.columns(2)
            with col1:
                original_stake = st.number_input("Original Stake ($)", min_value=1.0, value=100.0, step=10.0)
                original_odds = st.number_input("Original Odds", min_value=-10000, max_value=10000, value=400)
            with col2:
                hedge_odds = st.number_input("Current Hedge Odds", min_value=-10000, max_value=10000, value=-150,
                                           help="Odds to bet opposite outcome")
                target_profit = st.number_input("Target Profit ($)", min_value=0.0, value=0.0,
                                               help="0 = break even")

            if st.button("Calculate Hedge"):
                hedge = calculate_hedge_bet(original_stake, original_odds, hedge_odds,
                                           target_profit if target_profit > 0 else None)

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
            st.link_button("📲 Browse FanDuel HR Props", _fd_url(), use_container_width=True)

        elif strategy_type == "Progressive Staking":
            st.markdown("### 📈 Progressive Staking Systems")
            st.info("Alternative staking strategies beyond Kelly Criterion")

            col1, col2 = st.columns(2)
            with col1:
                system = st.selectbox(
                    "Staking System",
                    ["Fibonacci", "D'Alembert", "Oscar's Grind"],
                    help="Select a progressive staking system"
                )
                base_unit = st.number_input("Base Unit ($)", min_value=1.0, value=10.0, step=5.0)
                bankroll = st.session_state.get("bankroll_override", config.BANKROLL)

            with col2:
                if system == "Fibonacci":
                    loss_streak = st.number_input("Current Loss Streak", min_value=0, max_value=10, value=0)
                    stake = fibonacci_stake(base_unit, loss_streak, bankroll)
                    st.metric("Next Stake", f"${stake:.2f}")
                    st.caption("After loss: move to next Fibonacci number. After win: move back two.")

                elif system == "D'Alembert":
                    wins = st.number_input("Session Wins", min_value=0, value=0)
                    losses = st.number_input("Session Losses", min_value=0, value=0)
                    stake = dalembert_stake(base_unit, wins, losses, bankroll)
                    st.metric("Next Stake", f"${stake:.2f}")
                    st.caption("Increase by 1 unit after loss, decrease after win.")

                elif system == "Oscar's Grind":
                    session_profit = st.number_input("Session P&L ($)", value=0.0)
                    streak_type = st.selectbox("Current Streak", ["win", "loss"])
                    streak_length = st.number_input("Streak Length", min_value=0, value=0)
                    stake = oscar_grind_stake(base_unit, session_profit, streak_type,
                                             streak_length, bankroll)
                    st.metric("Next Stake", f"${stake:.2f}")
                    st.caption("Goal: Win 1 unit per session. Keep stakes same in losses, increase in wins.")

            st.divider()
            st.link_button("📲 Browse FanDuel HR Props", _fd_url(), use_container_width=True)

    except ImportError as e:
        st.error("Advanced strategies module not found. Strategies are being developed.")
        st.code(str(e))
    except Exception as e:
        st.error(f"Error in advanced strategies: {e}")
        st.code(_tb.format_exc())
