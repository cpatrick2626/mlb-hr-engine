"""
26JIG23 Prop Betting Engine — Streamlit Dashboard
"""

import sys
import time
from pathlib import Path

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="26JIG23 Prop Betting Engine",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
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
/* ── Base ── */
.stApp { background-color: #080808; color: #f0f0f0; }
[data-testid="stHeader"] { background-color: #080808; }
[data-testid="stSidebar"] {
    background-color: #0d0000;
    border-right: 2px solid #C6011F;
}
[data-testid="stSidebar"] * { color: #f0f0f0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background-color: #080808;
    padding: 8px 0 0 0;
    border-bottom: 2px solid #C6011F;
}
.stTabs [data-baseweb="tab"] {
    height: 56px;
    background-color: #150000;
    border: 1px solid #440000;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 0 40px;
    font-size: 15px !important;
    font-weight: 800 !important;
    color: #aaaaaa !important;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
.stTabs [aria-selected="true"] {
    background-color: #C6011F !important;
    color: #ffffff !important;
    border-color: #C6011F !important;
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    background-color: #2a0000 !important;
    color: #ffffff !important;
    border-color: #C6011F !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 20px;
}

/* ── Cards ── */
.combo-card {
    background: #110000; border: 1px solid #C6011F;
    border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;
}
.combo-card h5 { margin: 0 0 8px 0; color: #FF4444; font-size: 13px; font-weight: 700; }
.leg-pill {
    display: inline-block; background: #1a0000; border: 1px solid #880000;
    border-radius: 6px; padding: 5px 12px; margin: 3px 2px;
    font-size: 12px; color: #f0f0f0;
}
.odds-badge {
    display: inline-block; background: #200000; border: 1px solid #C6011F;
    border-radius: 4px; padding: 2px 8px; font-size: 11px;
    color: #FF6666; margin-left: 4px;
}
.ev-badge { display: inline-block; border-radius: 4px; padding: 2px 8px; font-size: 11px; margin-left: 4px; }
.ev-pos { background: #0a2a14; border: 1px solid #2ea043; color: #4ade80; }
.ev-neg { background: #2a0a0a; border: 1px solid #da3633; color: #f87171; }

/* ── Section headers ── */
.section-header {
    font-size: 16px; font-weight: 800; color: #FF3333;
    border-bottom: 2px solid #C6011F; padding-bottom: 6px;
    margin: 24px 0 16px 0; letter-spacing: 2px; text-transform: uppercase;
}

/* ── Range bar ── */
.range-bar {
    font-size: 11px; background: #110000; border: 1px solid #330000;
    border-radius: 6px; padding: 8px 14px; margin-bottom: 10px;
}

/* ── Rating badges ── */
.r-goat  { color:#FFD700; font-weight:900; font-size:13px; }
.r-fire  { color:#FF4500; font-weight:800; font-size:13px; }
.r-good  { color:#4ade80; font-weight:700; font-size:12px; }
.r-marg  { color:#888888; font-weight:400; font-size:12px; }

/* ── Metrics ── */
[data-testid="stMetric"] { background:#110000; border:1px solid #330000; border-radius:8px; padding:10px; }
[data-testid="stMetricLabel"] { color:#aaaaaa !important; font-size:11px; }
[data-testid="stMetricValue"] { color:#f0f0f0 !important; font-weight:700; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #330000; border-radius: 6px; }

/* ── Buttons ── */
.stButton button {
    background: #C6011F !important; color: white !important;
    border: none !important; font-weight: 700 !important;
    letter-spacing: 1px;
}
.stButton button:hover { background: #FF2222 !important; }

div[data-testid="stSelectbox"] label { font-size: 12px; color: #888888; }
</style>
""", unsafe_allow_html=True)


# ── Rating helpers ─────────────────────────────────────────────────────────────

def _pick_rating(ev_pct: float, edge_pct: float, model_prob: float, confidence: float) -> str:
    if ev_pct >= 35 or (ev_pct >= 28 and edge_pct >= 15 and confidence >= 72):
        return "🌟 ONCE IN A LIFETIME"
    if ev_pct >= 20 and edge_pct >= 10:
        return "🔥 AMAZING"
    if ev_pct >= 10 and edge_pct >= 5:
        return "✅ GOOD"
    return "📊 MARGINAL"


def _pitcher_label(name: str, pitcher_factor: float, platoon_factor: float) -> str:
    """
    Color-code pitcher by matchup difficulty.
    Red = batter will struggle. Green = pitcher is a target.
    ⚡ = batter has platoon edge (faces pitcher from opposite hand).
    """
    platoon = " ⚡" if platoon_factor and platoon_factor > 1.06 else ""
    if pitcher_factor < 0.80:
        return f"🔴 {name}{platoon}"   # Elite suppressor — avoid
    if pitcher_factor < 0.92:
        return f"🟠 {name}{platoon}"   # Tough matchup
    if pitcher_factor <= 1.08:
        return f"⬜ {name}{platoon}"   # Neutral
    if pitcher_factor <= 1.20:
        return f"🟡 {name}{platoon}"   # Favorable — homer-prone
    return f"🟢 {name}{platoon}"       # Elite HR target


def _spot_label(spot, platoon_factor: float) -> str:
    """Color-code lineup spot by expected PA value."""
    edge = "⚡" if platoon_factor and platoon_factor > 1.06 else ""
    if spot is None:
        return f"?{edge}"
    spot = int(spot)
    if spot <= 4:
        icon = "🟢"
    elif spot <= 6:
        icon = "🟡"
    else:
        icon = "🔴"
    return f"{icon}{spot}{edge}"


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3300, show_spinner=False)
def _load_data(target_date: str):
    from pipeline import load_game_data
    return load_game_data(target_date=target_date, progress_cb=[].append)


_SESSION_TTL = 3300  # seconds — must match cache TTL so autorefresh always gets fresh data


def get_data():
    from datetime import date as _date
    target_date = config.TARGET_DATE or _date.today().strftime("%Y-%m-%d")
    now = time.time()
    age = now - st.session_state.get("data_loaded_at", 0)
    stale = age > _SESSION_TTL or st.session_state.get("cache_key") != target_date

    if "data" not in st.session_state or stale:
        with st.spinner("⚾ Loading today's games, odds, and player profiles… (2-4 min first load)"):
            try:
                data = _load_data(target_date)
                st.session_state["data"]           = data
                st.session_state["cache_key"]      = target_date
                st.session_state["data_loaded_at"] = now

                ranked = data.get("ranked", [])
                if ranked:
                    try:
                        logged = pnl_tracker.log_picks(ranked, model_version="v4")
                        if logged:
                            clv_tracker.log_opening_lines(ranked)
                    except Exception:
                        pass

                try:
                    pnl_tracker.update_yesterday()
                except Exception:
                    pass

            except Exception as e:
                st.error(f"Failed to load game data: {e}")
                st.session_state["data"] = {
                    "ranked": [], "date": target_date, "stats": {},
                    "odds_source": "error", "batter_data": {},
                    "all_by_model": [], "team_players": {}, "auto_parlays": {},
                }
                st.session_state["cache_key"]      = target_date
                st.session_state["data_loaded_at"] = now

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
            f'<span style="color:#888888">({leg.get("team","")})</span> '
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
  <div style="margin-top:8px; font-size:11px; color:#888888;">
    Combined odds: <b style="color:#f0f0f0">{comb_odds}</b>
    &nbsp;|&nbsp; Model prob: <b style="color:#f0f0f0">{prob_pct:.2f}%</b>
    &nbsp;|&nbsp; EV: <span class="ev-badge {ev_cls}">{ev_sign}{ev:.1f}%</span>
  </div>
</div>"""


def _bankroll_scale() -> float:
    """Scale factor for bet sizing based on user's session bankroll vs config default."""
    session_br = st.session_state.get("bankroll_override", config.BANKROLL)
    return float(session_br) / config.BANKROLL if config.BANKROLL else 1.0


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — TODAY'S PICKS
# ══════════════════════════════════════════════════════════════════════════════
def tab_picks(data: dict):
    ranked    = data.get("ranked", [])
    stats     = data.get("stats", {})
    source    = data.get("odds_source", "none")
    n_batters = len(data.get("batter_data", {}))
    scale     = _bankroll_scale()

    st.markdown(
        f"<div style='color:#888888; font-size:12px; margin-bottom:16px; "
        f"background:#110000; border:1px solid #330000; border-radius:6px; padding:8px 14px;'>"
        f"📅 {data.get('date','')} &nbsp;|&nbsp; "
        f"Games: <b style='color:#f0f0f0'>{stats.get('games',0)}</b> &nbsp;|&nbsp; "
        f"Players: <b style='color:#f0f0f0'>{stats.get('players',0)}</b> &nbsp;|&nbsp; "
        f"Qualified: <b style='color:#FF3333'>{stats.get('qualified',0)}</b> &nbsp;|&nbsp; "
        f"Odds: <b style='color:#f0f0f0'>{source}</b> &nbsp;|&nbsp; "
        f"Statcast: <b style='color:#f0f0f0'>{n_batters}</b> batters"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not ranked:
        st.warning("No qualified picks today — all filtered out or no odds available.")
    else:
        rows = []
        for p in ranked:
            ev        = p.get("ev_pct", 0)
            edge      = p.get("edge_pct", 0)
            model_p   = p.get("model_prob", 0)
            conf      = p.get("confidence", 0)
            pit_fac   = p.get("pitcher_factor", 1.0)
            plat_fac  = p.get("platoon_factor", 1.0)
            spot      = p.get("lineup_spot")
            bet       = p.get("bet_dollars", 0) * scale

            rows.append({
                "Rating":   _pick_rating(ev, edge, model_p, conf),
                "#":        p.get("rank", ""),
                "Player":   p.get("player_name", ""),
                "Team":     p.get("team", ""),
                "Opp":      p.get("opponent", ""),
                "Spot":     _spot_label(spot, plat_fac),
                "Pitcher":  _pitcher_label(p.get("pitcher_name", "TBD"), pit_fac, plat_fac),
                "Odds":     _fmt_american(p.get("best_american")),
                "Model%":   f"{model_p*100:.1f}%",
                "Mkt%":     f"{p.get('market_no_vig_prob',0)*100:.1f}%",
                "Edge":     f"{edge:+.1f}%",
                "EV%":      f"{ev:+.1f}%",
                "Bet $":    f"${bet:.0f}",
                "Conf":     f"{conf:.0f}",
                "Brl%":     p.get("barrel_pct", "--"),
                "EV mph":   p.get("exit_velo", "--"),
                "Score":    f"{p.get('score',0):.1f}",
            })

        # ── Range stats bar ─────────────────────────────────────────────────
        def _rng(vals, fmt=".1f", suffix="", sign=False):
            clean = [v for v in vals if v is not None]
            if not clean:
                return "N/A"
            lo, hi = min(clean), max(clean)
            pfx = "+" if sign else ""
            return f"{lo:{pfx+fmt}}{suffix} → {hi:{pfx+fmt}}{suffix}"

        evs    = [p.get("ev_pct", 0) for p in ranked]
        edges  = [p.get("edge_pct", 0) for p in ranked]
        models = [p.get("model_prob", 0) * 100 for p in ranked]
        mkts   = [p.get("market_no_vig_prob", 0) * 100 for p in ranked]
        bets   = [p.get("bet_dollars", 0) * scale for p in ranked]
        confs  = [p.get("confidence", 0) for p in ranked]
        scores = [p.get("score", 0) for p in ranked]

        range_items = [
            ("Model%", _rng(models, suffix="%")),
            ("Mkt%",   _rng(mkts, suffix="%")),
            ("Edge",   _rng(edges, sign=True, suffix="%")),
            ("EV%",    _rng(evs, sign=True, suffix="%")),
            ("Bet $",  f"${min(bets):.0f} → ${max(bets):.0f}" if bets else "N/A"),
            ("Conf",   _rng(confs, fmt=".0f")),
        ]
        range_html = " &nbsp;|&nbsp; ".join(
            f"<span style='color:#888888'>{k}:</span> "
            f"<span style='color:#f0f0f0; font-weight:600'>{v}</span>"
            for k, v in range_items
        )
        st.markdown(
            f"<div class='range-bar'>📊 Today's ranges — {range_html}</div>",
            unsafe_allow_html=True,
        )

        # ── Legend ──────────────────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:11px; color:#888888; margin-bottom:8px;'>"
            "<b style='color:#f0f0f0'>Pitcher:</b> "
            "🔴 Elite suppressor &nbsp; 🟠 Tough &nbsp; ⬜ Neutral &nbsp; 🟡 Favorable &nbsp; 🟢 HR target &nbsp; ⚡ Platoon edge"
            "&nbsp;&nbsp;&nbsp;<b style='color:#f0f0f0'>Spot:</b> "
            "🟢 Premium (1-4) &nbsp; 🟡 Mid (5-6) &nbsp; 🔴 Bottom (7-9)"
            "</div>",
            unsafe_allow_html=True,
        )

        ev_rng    = _rng(evs, sign=True, suffix="%")
        edge_rng  = _rng(edges, sign=True, suffix="%")
        model_rng = _rng(models, suffix="%")
        mkt_rng   = _rng(mkts, suffix="%")
        bet_rng   = f"${min(bets):.0f} → ${max(bets):.0f}" if bets else "N/A"
        conf_rng  = _rng(confs, fmt=".0f")
        score_rng = _rng(scores, fmt=".1f")

        session_br = st.session_state.get("bankroll_override", config.BANKROLL)
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rating":  st.column_config.TextColumn("Rating",
                    help="🌟 Once in a lifetime (EV≥35%) | 🔥 Amazing (EV≥20%) | ✅ Good (EV≥10%) | 📊 Marginal"),
                "#":       st.column_config.TextColumn("#",
                    help="Composite rank: 40% EV% + 35% Edge% + 25% Confidence"),
                "Player":  st.column_config.TextColumn("Player"),
                "Team":    st.column_config.TextColumn("Team"),
                "Opp":     st.column_config.TextColumn("Opp"),
                "Spot":    st.column_config.TextColumn("Spot",
                    help="Lineup spot. 🟢=premium PA (1-4), 🟡=mid (5-6), 🔴=bottom (7-9). ⚡=platoon edge vs this pitcher."),
                "Pitcher": st.column_config.TextColumn("Pitcher",
                    help="🔴=elite suppressor, 🟠=tough, ⬜=neutral, 🟡=favorable, 🟢=HR target. ⚡=batter has platoon edge."),
                "Odds":    st.column_config.TextColumn("Odds",
                    help="Best American odds across all books for HR (0.5+)"),
                "Model%":  st.column_config.TextColumn("Model%",
                    help=f"Poisson HR probability — Statcast + park + pitcher + weather + platoon.\nRange: {model_rng}"),
                "Mkt%":    st.column_config.TextColumn("Mkt%",
                    help=f"Market no-vig implied probability.\nRange: {mkt_rng}"),
                "Edge":    st.column_config.TextColumn("Edge",
                    help=f"Model% − Market%. Min threshold +{config.MIN_EDGE_PCT}%.\nRange: {edge_rng}"),
                "EV%":     st.column_config.TextColumn("EV%",
                    help=f"Expected value per $100 wagered. Min threshold +{config.MIN_EV_PCT}%.\nRange: {ev_rng}"),
                "Bet $":   st.column_config.TextColumn("Bet $",
                    help=f"Quarter-Kelly sizing on ${session_br:,.0f} bankroll (5% cap = ${session_br*config.MAX_BET_PCT:.0f} max).\nRange: {bet_rng}"),
                "Conf":    st.column_config.TextColumn("Conf",
                    help=f"Confidence 0–100: sample size + Statcast availability + model/market agreement.\nRange: {conf_rng}"),
                "Brl%":    st.column_config.TextColumn("Brl%",
                    help="Statcast barrel rate. League avg ~5.2%. Higher = more true HR power."),
                "EV mph":  st.column_config.TextColumn("EV mph",
                    help="Average exit velocity. League avg ~88.9 mph."),
                "Score":   st.column_config.TextColumn("Score",
                    help=f"Ranking score = 40% EV% + 35% Edge% + 25% Conf.\nRange: {score_rng}"),
            },
        )

    st.markdown('<div class="section-header">All Players — Model Probabilities</div>',
                unsafe_allow_html=True)
    all_by_model = data.get("all_by_model", [])
    if all_by_model:
        model_rows = []
        for p in all_by_model[:30]:
            pit_fac  = p.get("pitcher_factor", 1.0)
            plat_fac = p.get("platoon_factor", 1.0)
            model_rows.append({
                "Player":   p.get("player_name", ""),
                "Team":     p.get("team", ""),
                "Spot":     _spot_label(p.get("lineup_spot"), plat_fac),
                "Vs":       _pitcher_label(p.get("pitcher_name", "TBD"), pit_fac, plat_fac),
                "Model%":   f"{p.get('model_prob',0)*100:.1f}%",
                "Brl%":     p.get("barrel_pct", "--"),
                "Exit Velo":p.get("exit_velo", "--"),
                "PwrMult":  f"{p.get('statcast_power_mult',1):.2f}",
                "Park":     f"{p.get('park_factor',1):.2f}",
                "Pitcher":  f"{p.get('pitcher_factor',1):.2f}",
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
    st.caption("Top 3 diverse combinations per leg count, ranked by combined EV%.")

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
                    pit_fac  = sel.get("pitcher_factor", 1.0)
                    plat_fac = sel.get("platoon_factor", 1.0)
                    odds_str  = _fmt_american(sel.get("best_american"))
                    model_pct = f"{sel.get('model_prob',0)*100:.1f}%"
                    pitcher_lbl = _pitcher_label(sel.get("pitcher_name","TBD"), pit_fac, plat_fac)
                    st.markdown(
                        f"<div style='font-size:11px; color:#888888; margin:-8px 0 8px 0;'>"
                        f"Odds: <b style='color:#FF6666'>{odds_str}</b> &nbsp;|&nbsp; "
                        f"Model: <b style='color:#f0f0f0'>{model_pct}</b> &nbsp;|&nbsp; "
                        f"Pitcher: {pitcher_lbl}</div>",
                        unsafe_allow_html=True,
                    )
                    legs_built.append(sel)

            if st.button(f"Build {n_legs}-Leg Parlay", key=f"{key_prefix}_build",
                         type="primary", use_container_width=True):
                if len(legs_built) == n_legs:
                    scale  = _bankroll_scale()
                    parlay = _evaluate_parlay(legs_built)
                    bet    = parlay_bet_size(parlay) * scale
                    comb   = _fmt_american(parlay["combined_american"])
                    prob   = parlay["combined_prob_pct"]
                    ev     = parlay["ev_pct"]
                    ev_color = "#4ade80" if ev >= 0 else "#f87171"
                    sign   = "+" if ev >= 0 else ""
                    st.markdown(f"""
                        <div class="combo-card" style="border-color:#C6011F">
                          <div style="font-size:13px; margin-bottom:6px;">
                            <b>Combined odds:</b> <span style="color:#FF6666; font-size:15px">{comb}</span>
                          </div>
                          <div style="font-size:12px; color:#888888;">
                            Model prob: <b style="color:#f0f0f0">{prob:.2f}%</b>
                            &nbsp;|&nbsp; EV: <b style="color:{ev_color}">{sign}{ev:.1f}%</b>
                            &nbsp;|&nbsp; Suggested bet: <b style="color:#4ade80">${bet:.0f}</b>
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
        f"<div style='font-size:11px; color:#888888; margin-bottom:12px; "
        f"background:#110000; border:1px solid #330000; border-radius:6px; padding:8px 14px;'>"
        f"Storage: <b style='color:{'#4ade80' if backend=='sheets' else '#FFD700'}'>"
        f"{'☁️ Google Sheets — persistent across deploys' if backend=='sheets' else '💾 Local CSV — resets on redeploy'}"
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
        st.info("No results logged yet. Picks are auto-logged when Today's Picks tab loads.")

    if clv:
        st.markdown('<div class="section-header">🎯 Closing Line Value</div>',
                    unsafe_allow_html=True)
        verdict = clv.get("verdict", "N/A")
        v_icon  = {"SHARP": "🟢", "NEUTRAL": "🟡", "SOFT": "🔴"}.get(verdict, "⚪")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CLV Picks",  clv.get("picks_with_clv", 0))
        c2.metric("Avg CLV",    f"{clv.get('avg_clv_pct',0):+.2f}%")
        c3.metric("Beat Close", f"{clv.get('pct_beating_close',0):.1f}%")
        c4.metric("Verdict",    f"{v_icon} {verdict}")

    st.markdown('<div class="section-header">📋 Picks Log</div>', unsafe_allow_html=True)
    try:
        rows = pnl_tracker.get_picks_log()
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No picks logged yet — open Today's Picks tab to auto-log.")
    except Exception as e:
        st.error(f"Could not load picks log: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    # Auto-refresh every 60 minutes. Session TTL (3300s) guarantees cache
    # is expired when the rerun fires, so fresh data is always fetched.
    st_autorefresh(interval=3_600_000, key="hourly_refresh")

    # ── Title ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; padding:28px 0 20px 0;'>
      <div style='font-size:11px; color:#C6011F; letter-spacing:6px;
        text-transform:uppercase; margin-bottom:6px;'>
        ⚾ &nbsp; MLB HOME RUN INTELLIGENCE &nbsp; ⚾
      </div>
      <h1 style='
        font-size:3.2rem; font-weight:900; letter-spacing:5px;
        background: linear-gradient(135deg, #FF0000 0%, #FF4444 40%, #FFD700 70%, #FF4444 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0; text-transform: uppercase; line-height: 1.1;
      '>26JIG23 PROP BETTING ENGINE</h1>
      <div style='font-size:11px; color:#666666; letter-spacing:4px;
        text-transform:uppercase; margin-top:8px;'>
        POWERED BY STATCAST &nbsp;·&nbsp; REAL-TIME ODDS &nbsp;·&nbsp; POISSON MODEL
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "📋  TODAY'S PICKS",
        "🎰  PARLAYS",
        "📊  PERFORMANCE",
    ])

    with tab1:
        data = get_data()
        tab_picks(data)

    with tab2:
        data = get_data()
        tab_parlays(data)

    with tab3:
        tab_performance()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<h2 style='color:#C6011F; letter-spacing:2px; "
            "text-align:center; margin-bottom:4px;'>⚾ 26JIG23</h2>"
            "<p style='color:#888; text-align:center; font-size:11px; "
            "letter-spacing:2px; margin-top:0;'>PROP BETTING ENGINE</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        # Bankroll input
        st.markdown("#### 💰 Bankroll")
        default_br = int(st.session_state.get("bankroll_override", config.BANKROLL))
        new_br = st.number_input(
            "Set your bankroll ($)",
            min_value=100,
            max_value=500_000,
            value=default_br,
            step=100,
            label_visibility="collapsed",
        )
        if new_br != st.session_state.get("bankroll_override"):
            st.session_state["bankroll_override"] = new_br
        st.caption(f"Max bet: ${new_br * config.MAX_BET_PCT:,.0f} &nbsp;|&nbsp; Kelly: {config.KELLY_FRACTION:.0%}")

        st.divider()

        if st.button("🔄 Force Refresh Data", use_container_width=True):
            st.cache_data.clear()
            for k in ["data", "cache_key", "data_loaded_at"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.divider()

        if st.button("✅ Update Yesterday's Results", use_container_width=True):
            with st.spinner("Fetching outcomes from MLB…"):
                try:
                    result = pnl_tracker.update_yesterday()
                    st.success(
                        f"Settled {result['settled']} pick(s). "
                        f"{result['not_found']} not found."
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

        st.divider()
        st.caption(f"Min EV: {config.MIN_EV_PCT}%")
        st.caption(f"Min Edge: {config.MIN_EDGE_PCT}%")
        backend = pnl_tracker.storage_backend()
        st.caption(f"Storage: {'☁️ Sheets' if backend == 'sheets' else '💾 Local CSV'}")
        st.caption(f"Auto-refresh: every 60 min")


if __name__ == "__main__":
    main()
