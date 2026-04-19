"""
MLB HR Engine v4 — Streamlit Dashboard
Run:  streamlit run mlb_hr_engine_v4/app.py
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="MLB HR Engine v4",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

sys.path.insert(0, str(Path(__file__).parent))

import config
from engine.market import american_to_decimal, decimal_to_american
from engine.ev import expected_value_pct
from output.parlay import _evaluate_parlay, parlay_bet_size
from tracking import pnl as pnl_tracker, clv as clv_tracker

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #0d1117; color: #e6edf3; }
[data-testid="stHeader"] { background-color: #0d1117; }
.combo-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 12px 14px; margin-bottom: 10px;
}
.combo-card h5 { margin: 0 0 8px 0; color: #58a6ff; font-size: 13px; }
.leg-pill {
    display: inline-block; background: #21262d; border: 1px solid #30363d;
    border-radius: 6px; padding: 4px 10px; margin: 3px 2px;
    font-size: 12px; color: #e6edf3;
}
.odds-badge {
    display: inline-block; background: #1f6feb22; border: 1px solid #1f6feb;
    border-radius: 4px; padding: 2px 8px; font-size: 11px;
    color: #79c0ff; margin-left: 4px;
}
.ev-badge { display: inline-block; border-radius: 4px; padding: 2px 8px; font-size: 11px; margin-left: 4px; }
.ev-pos { background: #1a4731; border: 1px solid #2ea043; color: #3fb950; }
.ev-neg { background: #4a1919; border: 1px solid #da3633; color: #f85149; }
.section-header {
    font-size: 18px; font-weight: 700; color: #58a6ff;
    border-bottom: 1px solid #30363d; padding-bottom: 6px; margin: 20px 0 14px 0;
}
div[data-testid="stSelectbox"] label { font-size: 12px; color: #8b949e; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _load_data(target_date: str):
    from pipeline import load_game_data
    return load_game_data(target_date=target_date, progress_cb=[].append)


def get_data():
    from datetime import date as _date
    target_date = config.TARGET_DATE or _date.today().strftime("%Y-%m-%d")

    if "data" not in st.session_state or st.session_state.get("cache_key") != target_date:
        with st.spinner("Loading today's games, odds, and player profiles… (2-4 min first time)"):
            try:
                data = _load_data(target_date)
                st.session_state["data"] = data
                st.session_state["cache_key"] = target_date

                # Auto-log picks and opening CLV lines once per day
                ranked = data.get("ranked", [])
                if ranked:
                    try:
                        logged = pnl_tracker.log_picks(ranked, model_version="v4")
                        if logged:
                            clv_tracker.log_opening_lines(ranked)
                    except Exception:
                        pass  # Never crash the UI over logging failure
            except Exception as e:
                st.error(f"Failed to load game data: {e}")
                st.session_state["data"] = {
                    "ranked": [], "date": target_date, "stats": {},
                    "odds_source": "error", "batter_data": {},
                    "all_by_model": [], "team_players": {}, "auto_parlays": {},
                }
                st.session_state["cache_key"] = target_date

    return st.session_state["data"]


# ── Helpers ────────────────────────────────────────────────────────────────────
def _fmt_american(odds) -> str:
    if odds is None:
        return "--"
    return f"+{odds}" if int(odds) > 0 else str(odds)


def _combo_html(parlay: dict, label: str) -> str:
    legs_html = ""
    for leg in parlay["legs"]:
        odds_str = _fmt_american(leg.get("best_american"))
        legs_html += (
            f'<div class="leg-pill">'
            f'<b>{leg["player_name"]}</b> '
            f'<span style="color:#8b949e">({leg.get("team","")})</span> '
            f'<span class="odds-badge">{odds_str}</span>'
            f'</div>'
        )
    ev = parlay.get("ev_pct", 0)
    ev_cls  = "ev-pos" if ev >= 0 else "ev-neg"
    ev_sign = "+" if ev >= 0 else ""
    comb_odds = _fmt_american(parlay.get("combined_american"))
    prob_pct  = parlay.get("combined_prob_pct", 0)
    return f"""
<div class="combo-card">
  <h5>{label}</h5>
  {legs_html}
  <div style="margin-top:8px; font-size:11px; color:#8b949e;">
    Combined odds: <b style="color:#e6edf3">{comb_odds}</b>
    &nbsp;|&nbsp; Model prob: <b style="color:#e6edf3">{prob_pct:.2f}%</b>
    &nbsp;|&nbsp; EV: <span class="ev-badge {ev_cls}">{ev_sign}{ev:.1f}%</span>
  </div>
</div>"""


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — TODAY'S PICKS
# ══════════════════════════════════════════════════════════════════════════════
def tab_picks(data: dict):
    ranked    = data.get("ranked", [])
    stats     = data.get("stats", {})
    source    = data.get("odds_source", "none")
    n_batters = len(data.get("batter_data", {}))

    st.markdown(
        f"<div style='color:#8b949e; font-size:13px; margin-bottom:16px;'>"
        f"📅 {data.get('date','')} &nbsp;|&nbsp; "
        f"Games: {stats.get('games',0)} &nbsp;|&nbsp; "
        f"Players: {stats.get('players',0)} &nbsp;|&nbsp; "
        f"Qualified: {stats.get('qualified',0)} &nbsp;|&nbsp; "
        f"Odds source: {source} &nbsp;|&nbsp; "
        f"Statcast: {n_batters} batters"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not ranked:
        st.warning("No qualified picks today — all filtered out or no odds available.")
    else:
        rows = []
        for p in ranked:
            ev   = p.get("ev_pct", 0)
            edge = p.get("edge_pct", 0)
            rows.append({
                "#":       p.get("rank", ""),
                "Player":  p.get("player_name", ""),
                "Team":    p.get("team", ""),
                "Opp":     p.get("opponent", ""),
                "Pitcher": p.get("pitcher_name", "TBD"),
                "Odds":    _fmt_american(p.get("best_american")),
                "Model%":  f"{p.get('model_prob',0)*100:.1f}%",
                "Mkt%":    f"{p.get('market_no_vig_prob',0)*100:.1f}%",
                "Edge":    f"{edge:+.1f}%",
                "EV%":     f"{ev:+.1f}%",
                "Bet $":   f"${p.get('bet_dollars',0):.0f}",
                "Conf":    f"{p.get('confidence',0):.0f}",
                "Brl%":    p.get("barrel_pct", "--"),
                "EV mph":  p.get("exit_velo", "--"),
                "Score":   f"{p.get('score',0):.1f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">All Players — Model Probabilities</div>',
                unsafe_allow_html=True)
    all_by_model = data.get("all_by_model", [])
    if all_by_model:
        model_rows = []
        for p in all_by_model[:30]:
            model_rows.append({
                "Player":    p.get("player_name", ""),
                "Team":      p.get("team", ""),
                "Vs":        p.get("pitcher_name", "TBD"),
                "Spot":      p.get("lineup_spot", "?"),
                "Model%":    f"{p.get('model_prob',0)*100:.1f}%",
                "Brl%":      p.get("barrel_pct", "--"),
                "Exit Velo": p.get("exit_velo", "--"),
                "PwrMult":   f"{p.get('statcast_power_mult',1):.2f}",
                "Park":      f"{p.get('park_factor',1):.2f}",
                "Pitcher":   f"{p.get('pitcher_factor',1):.2f}",
            })
        st.dataframe(pd.DataFrame(model_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PARLAYS
# ══════════════════════════════════════════════════════════════════════════════
def tab_parlays(data: dict):
    ranked       = data.get("ranked", [])
    team_players = data.get("team_players", {})
    auto_parlays = data.get("auto_parlays", {})

    st.markdown('<div class="section-header">⚡ AUTO PARLAYS</div>', unsafe_allow_html=True)
    st.caption("Top 3 diverse combinations per leg size, ranked by combined EV%.")

    if not ranked or not any(auto_parlays.values()):
        st.warning("Not enough qualified picks with odds to build auto parlays.")
    else:
        col2, col3, col4 = st.columns(3)
        for col, n_legs, label in [
            (col2, 2, "2 LEG"), (col3, 3, "3 LEG"), (col4, 4, "4 LEG")
        ]:
            with col:
                st.markdown(f"### {label}")
                combos = auto_parlays.get(n_legs, [])
                if not combos:
                    st.caption("Not enough picks for this leg count.")
                else:
                    for i, combo in enumerate(combos, 1):
                        st.markdown(_combo_html(combo, f"Combo {i}"), unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="section-header">🛠️ MANUAL PARLAY BUILDER</div>',
                unsafe_allow_html=True)
    st.caption("Select a team for each leg — best pick auto-fills, or choose from the dropdown.")

    teams_list = sorted(team_players.keys())
    if not teams_list:
        st.warning("No team data available — refresh data first.")
        return

    def manual_column(col, n_legs: int, key_prefix: str):
        with col:
            st.markdown(f"### {n_legs} LEG")
            legs_built = []
            for i in range(n_legs):
                st.markdown(f"**Leg {i+1}**")
                team = st.selectbox(
                    "Team",
                    options=["-- select --"] + teams_list,
                    key=f"{key_prefix}_team_{i}",
                    label_visibility="collapsed",
                )
                if team == "-- select --":
                    st.text_input("Player", value="", placeholder="(select team first)",
                                  disabled=True, key=f"{key_prefix}_player_disp_{i}")
                    continue
                players = team_players.get(team, [])
                if not players:
                    st.warning(f"No players with odds for {team}")
                    continue
                player_names = [p["player_name"] for p in players]
                player_map   = {p["player_name"]: p for p in players}
                selected_name = st.selectbox(
                    "Player",
                    options=player_names,
                    key=f"{key_prefix}_player_{i}",
                    label_visibility="collapsed",
                )
                sel = player_map.get(selected_name)
                if sel:
                    odds_str  = _fmt_american(sel.get("best_american"))
                    model_pct = f"{sel.get('model_prob',0)*100:.1f}%"
                    st.markdown(
                        f"<div style='font-size:11px; color:#8b949e; margin:-8px 0 8px 0;'>"
                        f"Odds: <b style='color:#79c0ff'>{odds_str}</b> &nbsp;|&nbsp; "
                        f"Model: <b style='color:#e6edf3'>{model_pct}</b></div>",
                        unsafe_allow_html=True,
                    )
                    legs_built.append(sel)

            if st.button(f"Build {n_legs}-Leg Parlay", key=f"{key_prefix}_build",
                         type="primary", use_container_width=True):
                if len(legs_built) == n_legs:
                    parlay = _evaluate_parlay(legs_built)
                    bet    = parlay_bet_size(parlay)
                    comb   = _fmt_american(parlay["combined_american"])
                    prob   = parlay["combined_prob_pct"]
                    ev     = parlay["ev_pct"]
                    ev_color = "#3fb950" if ev >= 0 else "#f85149"
                    sign   = "+" if ev >= 0 else ""
                    st.markdown(f"""
                        <div class="combo-card" style="border-color:#1f6feb">
                          <div style="font-size:13px; margin-bottom:6px;">
                            <b>Combined odds:</b> <span style="color:#79c0ff; font-size:15px">{comb}</span>
                          </div>
                          <div style="font-size:12px; color:#8b949e;">
                            Model prob: <b style="color:#e6edf3">{prob:.2f}%</b>
                            &nbsp;|&nbsp; EV: <b style="color:{ev_color}">{sign}{ev:.1f}%</b>
                            &nbsp;|&nbsp; Suggested bet: <b style="color:#3fb950">${bet:.0f}</b>
                          </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.error(f"Select all {n_legs} legs before building.")

    m2, m3, m4 = st.columns(3)
    manual_column(m2, 2, "m2")
    manual_column(m3, 3, "m3")
    manual_column(m4, 4, "m4")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
def tab_performance():
    backend = pnl_tracker.storage_backend()
    st.markdown(
        f"<div style='font-size:11px; color:#8b949e; margin-bottom:12px;'>"
        f"Storage: <b style='color:#{'3fb950' if backend=='sheets' else 'e3b341'}'>"
        f"{'☁️ Google Sheets (persistent)' if backend=='sheets' else '💾 Local CSV (ephemeral on Streamlit Cloud)'}"
        f"</b></div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-header">📊 Running P&L</div>', unsafe_allow_html=True)
    try:
        summary = pnl_tracker.pnl_summary()
        clv     = clv_tracker.clv_summary()
    except Exception as e:
        st.error(f"Error loading performance data: {e}")
        return

    if summary:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Picks",   summary.get("total_picks", 0))
        c2.metric("Win Rate",      f"{summary.get('win_rate',0)*100:.1f}%")
        c3.metric("Total Wagered", f"${summary.get('total_wagered',0):,.2f}")
        c4.metric("Net P&L",       f"${summary.get('total_profit',0):+,.2f}")
        c5.metric("ROI",           f"{summary.get('roi_pct',0):+.1f}%")

        col_w, col_l, col_p = st.columns(3)
        col_w.metric("Wins",    summary.get("wins", 0))
        col_l.metric("Losses",  summary.get("losses", 0))
        col_p.metric("Pending", summary.get("pending", 0))
    else:
        st.info("No results logged yet. Picks are auto-logged when you open Today's Picks tab.")

    if clv:
        st.markdown('<div class="section-header">🎯 Closing Line Value</div>',
                    unsafe_allow_html=True)
        verdict = clv.get("verdict", "N/A")
        v_color = {"SHARP": "🟢", "NEUTRAL": "🟡", "SOFT": "🔴"}.get(verdict, "⚪")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CLV Picks",   clv.get("picks_with_clv", 0))
        c2.metric("Avg CLV",     f"{clv.get('avg_clv_pct',0):+.2f}%")
        c3.metric("Beat Close",  f"{clv.get('pct_beating_close',0):.1f}%")
        c4.metric("Verdict",     f"{v_color} {verdict}")

    st.markdown('<div class="section-header">📋 Picks Log</div>', unsafe_allow_html=True)
    try:
        rows = pnl_tracker.get_picks_log()
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No picks logged yet — open Today's Picks tab to auto-log today's picks.")
    except Exception as e:
        st.error(f"Could not load picks log: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown(
        "<h1 style='color:#58a6ff; margin-bottom:4px;'>⚾ MLB HR Prop Betting Engine</h1>"
        "<p style='color:#8b949e; margin-top:0;'>v4 — Streamlit Dashboard</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["📋 Today's Picks", "🎰 Parlays", "📊 Performance"])

    with tab1:
        data = get_data()
        tab_picks(data)

    with tab2:
        data = get_data()
        tab_parlays(data)

    with tab3:
        tab_performance()

    with st.sidebar:
        st.markdown("### ⚾ Controls")

        if st.button("🔄 Refresh Today's Data", use_container_width=True):
            st.cache_data.clear()
            for key in ["data", "cache_key"]:
                st.session_state.pop(key, None)
            st.rerun()

        st.divider()

        if st.button("✅ Update Yesterday's Results", use_container_width=True):
            with st.spinner("Fetching yesterday's outcomes from MLB…"):
                try:
                    result = pnl_tracker.update_yesterday()
                    st.success(
                        f"Settled {result['settled']} pick(s) for {result['date']}. "
                        f"{result['not_found']} not found."
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

        st.divider()
        st.caption(f"Bankroll: ${config.BANKROLL:,.0f}")
        st.caption(f"Kelly: {config.KELLY_FRACTION:.0%}")
        st.caption(f"Min EV: {config.MIN_EV_PCT}%")
        backend = pnl_tracker.storage_backend()
        st.caption(f"Storage: {'☁️ Sheets' if backend == 'sheets' else '💾 Local CSV'}")


if __name__ == "__main__":
    main()
