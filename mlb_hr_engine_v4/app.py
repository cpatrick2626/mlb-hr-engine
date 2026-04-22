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

# PWA + mobile home-screen support
# iOS: "Add to Home Screen" in Safari makes this launch full-screen, no browser chrome
# Android: Chrome will prompt "Install App" automatically with these tags
st.markdown("""
<head>
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="26JIG23">
<meta name="theme-color" content="#0d0d0d">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<link rel="apple-touch-icon" href="https://em-content.zobj.net/source/apple/354/baseball_26be.png">
<link rel="manifest" href="data:application/json,{
  &quot;name&quot;: &quot;26JIG23 Prop Engine&quot;,
  &quot;short_name&quot;: &quot;26JIG23&quot;,
  &quot;start_url&quot;: &quot;/&quot;,
  &quot;display&quot;: &quot;standalone&quot;,
  &quot;background_color&quot;: &quot;#0d0d0d&quot;,
  &quot;theme_color&quot;: &quot;#0d0d0d&quot;,
  &quot;icons&quot;: [{
    &quot;src&quot;: &quot;https://em-content.zobj.net/source/apple/354/baseball_26be.png&quot;,
    &quot;sizes&quot;: &quot;192x192&quot;,
    &quot;type&quot;: &quot;image/png&quot;
  }]
}">
</head>
""", unsafe_allow_html=True)

sys.path.insert(0, str(Path(__file__).parent))

import config
from engine.market import american_to_decimal, decimal_to_american
from engine.ev import expected_value_pct
from output.parlay import _evaluate_parlay, parlay_bet_size
from output.ranker import rank_picks as _rank_picks
from tracking import pnl as pnl_tracker, clv as clv_tracker

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;700;900&display=swap');

/* ── Animations ── */
@keyframes glow-pulse {
    0%,100% { box-shadow: 0 0 12px rgba(198,1,31,0.5), 0 0 30px rgba(198,1,31,0.2); }
    50%      { box-shadow: 0 0 25px rgba(255,50,50,0.8), 0 0 60px rgba(198,1,31,0.4); }
}
@keyframes shimmer {
    0%   { background-position: -400% center; }
    100% { background-position: 400% center; }
}
@keyframes border-flash {
    0%,100% { border-color: #C6011F; }
    50%      { border-color: #FF6666; }
}

/* ── Base ── */
.stApp {
    background-color: #040404;
    background-image:
        radial-gradient(ellipse at 15% 0%,   rgba(198,1,31,0.12) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 100%,  rgba(198,1,31,0.07) 0%, transparent 55%);
    color: #f0f0f0;
}
[data-testid="stHeader"] { background-color: #040404; border-bottom: 1px solid #1a0000; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0000 0%, #070000 100%);
    border-right: 2px solid #C6011F;
    box-shadow: 4px 0 30px rgba(198,1,31,0.25);
}
[data-testid="stSidebar"] * { color: #f0f0f0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 5px;
    background-color: #040404;
    padding: 12px 0 0 0;
    border-bottom: 3px solid #C6011F;
}
.stTabs [data-baseweb="tab"] {
    height: 66px;
    background: linear-gradient(180deg, #180000 0%, #0c0000 100%);
    border: 1px solid #4a0000;
    border-bottom: none;
    border-radius: 10px 10px 0 0;
    padding: 0 52px;
    font-size: 15px !important;
    font-weight: 900 !important;
    color: #666666 !important;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    transition: all 0.15s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(180deg, #D4001F 0%, #8B0000 100%) !important;
    color: #ffffff !important;
    border-color: #FF3333 !important;
    box-shadow: 0 -6px 24px rgba(198,1,31,0.65), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    text-shadow: 0 1px 8px rgba(0,0,0,0.6);
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    background: linear-gradient(180deg, #280000 0%, #180000 100%) !important;
    color: #dddddd !important;
    border-color: #880000 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 24px; }

/* ── Cards ── */
.combo-card {
    background: linear-gradient(135deg, #130000 0%, #090000 100%);
    border: 1px solid #C6011F;
    border-radius: 10px; padding: 18px 20px; margin-bottom: 14px;
    box-shadow: 0 6px 24px rgba(198,1,31,0.18), inset 0 1px 0 rgba(255,80,80,0.08);
}
.combo-card h5 {
    margin: 0 0 10px 0; color: #FF5555; font-size: 13px;
    font-weight: 900; letter-spacing: 2px; text-transform: uppercase;
}
.leg-pill {
    display: inline-block;
    background: linear-gradient(135deg, #1e0000 0%, #140000 100%);
    border: 1px solid #770000;
    border-radius: 6px; padding: 6px 14px; margin: 4px 3px;
    font-size: 12px; color: #eeeeee; font-weight: 600;
}
.odds-badge {
    display: inline-block; background: #1c0000; border: 1px solid #C6011F;
    border-radius: 4px; padding: 3px 10px; font-size: 12px;
    color: #FF6666; margin-left: 6px; font-weight: 800;
}
.ev-badge {
    display: inline-block; border-radius: 4px; padding: 3px 10px;
    font-size: 12px; margin-left: 6px; font-weight: 800;
}
.ev-pos { background: #062014; border: 1px solid #2ea043; color: #4ade80; }
.ev-neg { background: #200808; border: 1px solid #cc2222; color: #f87171; }

/* ── Section headers ── */
.section-header {
    font-size: 17px; font-weight: 900; color: #FF4444;
    border-left: 5px solid #FFD700;
    border-bottom: 1px solid #220000;
    padding: 10px 0 10px 16px;
    margin: 32px 0 20px 0;
    letter-spacing: 3px; text-transform: uppercase;
    text-shadow: 0 0 25px rgba(255,60,60,0.45);
    background: linear-gradient(90deg, rgba(198,1,31,0.10) 0%, transparent 65%);
}

/* ── Range bar ── */
.range-bar {
    font-size: 12px;
    background: linear-gradient(90deg, #110000 0%, #090000 100%);
    border: 1px solid #2a0000;
    border-left: 4px solid #C6011F;
    border-radius: 6px; padding: 10px 16px; margin-bottom: 14px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

/* ── Rating badges ── */
.r-goat { color:#FFD700; font-weight:900; font-size:14px; text-shadow: 0 0 8px rgba(255,215,0,0.6); }
.r-fire { color:#FF5500; font-weight:900; font-size:14px; text-shadow: 0 0 8px rgba(255,85,0,0.5); }
.r-good { color:#4ade80; font-weight:800; font-size:13px; }
.r-marg { color:#666666; font-weight:400; font-size:12px; }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #120000 0%, #080000 100%);
    border: 1px solid #380000;
    border-top: 3px solid #C6011F;
    border-radius: 10px; padding: 14px 16px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.5);
}
[data-testid="stMetricLabel"] {
    color: #777777 !important; font-size: 10px !important;
    letter-spacing: 1.5px; text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important; font-weight: 900 !important;
    font-size: 1.8rem !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #2a0000; border-radius: 8px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.6);
}

/* ── Buttons ── */
.stButton button {
    background: linear-gradient(135deg, #C6011F 0%, #8B0000 100%) !important;
    color: #ffffff !important;
    border: 1px solid #FF3333 !important;
    font-weight: 900 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 18px rgba(198,1,31,0.45) !important;
    transition: all 0.15s ease !important;
}
.stButton button:hover {
    background: linear-gradient(135deg, #FF2020 0%, #C6011F 100%) !important;
    box-shadow: 0 6px 30px rgba(255,30,30,0.70) !important;
    transform: translateY(-2px) !important;
}

/* ── Inputs ── */
[data-testid="stNumberInput"] input {
    background: #0f0000 !important; border: 1px solid #440000 !important;
    color: #FFD700 !important; font-weight: 800 !important; font-size: 16px !important;
    border-radius: 6px !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] { color: #555; }

/* ── Divider ── */
hr { border-color: #1e0000 !important; margin: 12px 0 !important; }

/* ── Selectbox ── */
div[data-testid="stSelectbox"] label { font-size: 12px; color: #666; }

/* ── Alert boxes ── */
[data-testid="stAlert"] { border-radius: 8px !important; border-left-width: 4px !important; }
</style>
""", unsafe_allow_html=True)


# ── Rating helpers ─────────────────────────────────────────────────────────────

def _pick_rating(ev_pct: float, edge_pct: float, model_prob: float, confidence: float) -> str:
    # ONCE IN A LIFETIME: genuinely rare — needs high EV + meaningful edge + confident model.
    # High odds (e.g. +2000) can produce huge EV% mathematically even on slim edge;
    # requiring edge >= 12 and confidence >= 65 filters those out.
    if ev_pct >= 50 and edge_pct >= 12 and confidence >= 65:
        return "🌟 ONCE IN A LIFETIME"
    # STRONG EDGE: clear mispricing with a confident model signal.
    if (ev_pct >= 30 and edge_pct >= 8 and confidence >= 50) or \
       (ev_pct >= 15 and edge_pct >= 5 and confidence >= 50):
        return "🔥 STRONG EDGE"
    # BREAD AND BUTTER: any positive EV with minimum edge — bread-and-butter plays.
    if ev_pct >= 5 and edge_pct >= 2:
        return "✅ BREAD AND BUTTER"
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


def _apply_ui_filters(players: list, min_ev: float, min_edge: float) -> list:
    """Re-filter all_players using sidebar thresholds (post-cache, no reload needed)."""
    result = []
    for p in players:
        if not p.get("best_american"):
            continue
        if p.get("ev_pct", -999) < min_ev:
            continue
        if p.get("edge_pct", -999) < min_edge:
            continue
        if p.get("expected_pa", 0) < config.MIN_PA_THRESHOLD:
            continue
        if p.get("park_factor", 1.0) < config.MAX_PARK_PENALTY:
            continue
        if p.get("weather_factor", 1.0) < config.MAX_WEATHER_PENALTY:
            continue
        if p.get("pitcher_factor", 1.0) < config.MAX_PITCHER_SUPPRESSOR:
            continue
        result.append(p)
    return _rank_picks(result)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — TODAY'S PICKS
# ══════════════════════════════════════════════════════════════════════════════
def tab_picks(data: dict, min_ev: float, min_edge: float):
    all_players = data.get("all_players", [])
    ranked    = _apply_ui_filters(all_players, min_ev, min_edge)
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
        f"Qualified: <b style='color:#FF3333'>{len(ranked)}</b> "
        f"<span style='color:#555'>(EV≥{min_ev:.0f}% Edge≥{min_edge:.1f}%)</span> &nbsp;|&nbsp; "
        f"Odds: <b style='color:#f0f0f0'>{source}</b> &nbsp;|&nbsp; "
        f"Statcast: <b style='color:#f0f0f0'>{n_batters}</b> batters"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not ranked:
        with_odds = [p for p in all_players if p.get("best_american")]
        if not with_odds:
            st.warning("No market odds available today — check API key or try Force Refresh.")
            st.info(f"Pipeline found {len(all_players)} players total. 0 matched to odds lines.")
        else:
            evs   = sorted((p.get("ev_pct", -999) for p in with_odds), reverse=True)
            edges = sorted((p.get("edge_pct", -999) for p in with_odds), reverse=True)
            best_ev   = evs[0]   if evs   else -999
            best_edge = edges[0] if edges else -999
            st.warning(
                f"No picks pass current filters (EV ≥ {min_ev:.1f}%, Edge ≥ {min_edge:.1f}%). "
                f"Slide **both sliders left** in the sidebar to see picks."
            )
            st.info(
                f"Pool: **{len(all_players)}** players total | "
                f"**{len(with_odds)}** have odds | "
                f"Best EV: **{best_ev:+.1f}%** | Best Edge: **{best_edge:+.1f}%**\n\n"
                f"Set Min EV ≤ {best_ev:.1f}% and Min Edge ≤ {best_edge:.1f}% to see the top pick."
            )
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
                "SwSp%":    p.get("sweet_spot_pct", "--"),
                "EV mph":   p.get("exit_velo", "--"),
                "FB%":      p.get("fb_pct", "--"),
                "GB%":      p.get("gb_pct", "--"),
                "Pull%":    p.get("pull_pct", "--"),
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
                    help="🌟 Once in a lifetime (EV≥15%) | 🔥 Strong edge (EV≥10%) | ✅ Bread & butter (EV≥5%) | 📊 Marginal"),
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
                    help=f"Model% − Market%. Active threshold +{min_edge:.1f}%.\nRange: {edge_rng}"),
                "EV%":     st.column_config.TextColumn("EV%",
                    help=f"Expected value per $100 wagered. Active threshold +{min_ev:.0f}%.\nRange: {ev_rng}"),
                "Bet $":   st.column_config.TextColumn("Bet $",
                    help=f"Quarter-Kelly sizing on ${session_br:,.0f} bankroll (5% cap = ${session_br*config.MAX_BET_PCT:.0f} max).\nRange: {bet_rng}"),
                "Conf":    st.column_config.TextColumn("Conf",
                    help=f"Confidence 0–100: sample size + Statcast availability + model/market agreement.\nRange: {conf_rng}"),
                "Brl%":    st.column_config.TextColumn("Brl%",
                    help="Statcast barrel rate. League avg ~5.2%. Higher = more true HR power."),
                "SwSp%":   st.column_config.TextColumn("SwSp%",
                    help="Sweet spot rate (LA 8-32°). League avg ~34%. The exact HR angle band."),
                "EV mph":  st.column_config.TextColumn("EV mph",
                    help="Average exit velocity. League avg ~88.9 mph."),
                "FB%":     st.column_config.TextColumn("FB%",
                    help="Fly ball rate. League avg ~36%. Higher = more HR opportunities."),
                "GB%":     st.column_config.TextColumn("GB%",
                    help="Ground ball rate. League avg ~43%. Higher = fewer HR chances."),
                "Pull%":   st.column_config.TextColumn("Pull%",
                    help="Pull rate. League avg ~40%. Pull hitters access the short porch."),
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
                "SwSp%":    p.get("sweet_spot_pct", "--"),
                "FB%":      p.get("fb_pct", "--"),
                "GB%":      p.get("gb_pct", "--"),
                "Pull%":    p.get("pull_pct", "--"),
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

    # Read filter thresholds from session state first (sidebar sets them on each rerun)
    _min_ev   = float(st.session_state.get("min_ev",   config.MIN_EV_PCT))
    _min_edge = float(st.session_state.get("min_edge", config.MIN_EDGE_PCT))

    # ── Title ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='
        text-align:center; padding:40px 0 28px 0;
        background: radial-gradient(ellipse at 50% 0%, rgba(198,1,31,0.18) 0%, transparent 65%);
        border-bottom: 1px solid #1a0000;
        margin-bottom: 4px;
    '>
      <div style='
        font-size:10px; font-weight:800; color:#C6011F; letter-spacing:8px;
        text-transform:uppercase; margin-bottom:14px;
        text-shadow: 0 0 15px rgba(198,1,31,0.9);
      '>⚾ &nbsp;&nbsp; MLB HOME RUN INTELLIGENCE &nbsp;&nbsp; ⚾</div>

      <div style='
        font-size:4.2rem; font-weight:900; letter-spacing:6px;
        background: linear-gradient(110deg, #FF0000 0%, #FF5555 25%, #FFD700 50%, #FF5555 75%, #FF0000 100%);
        background-size: 300% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 4px 0; text-transform: uppercase; line-height: 1.05;
        filter: drop-shadow(0 0 40px rgba(200,0,30,0.55));
      '>26JIG23</div>

      <div style='
        font-size:1.55rem; font-weight:900; letter-spacing:10px;
        color:#CC0018; text-transform:uppercase;
        text-shadow: 0 0 20px rgba(198,1,31,0.5);
        margin-bottom:16px;
      '>PROP BETTING ENGINE</div>

      <div style='
        display:inline-flex; gap:24px; align-items:center;
        font-size:9px; font-weight:700; color:#444444;
        letter-spacing:4px; text-transform:uppercase;
      '>
        <span style="color:#C6011F;">▸</span> STATCAST POWERED
        <span style="color:#333;">|</span>
        <span style="color:#C6011F;">▸</span> REAL-TIME ODDS
        <span style="color:#333;">|</span>
        <span style="color:#C6011F;">▸</span> POISSON MODEL
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs([
        "📋  TODAY'S PICKS",
        "🎰  PARLAYS",
        "📊  PERFORMANCE",
    ])

    with tab1:
        data = get_data()
        tab_picks(data, _min_ev, _min_edge)

    with tab2:
        data = get_data()
        tab_parlays(data)

    with tab3:
        tab_performance()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding:18px 0 14px 0;
          background: linear-gradient(180deg, rgba(198,1,31,0.18) 0%, transparent 100%);
          border-bottom: 2px solid #C6011F; margin-bottom:4px;'>
          <div style='font-size:26px; font-weight:900; color:#C6011F;
            letter-spacing:3px; text-shadow:0 0 20px rgba(198,1,31,0.7);'>⚾ 26JIG23</div>
          <div style='font-size:8px; font-weight:800; color:#555; letter-spacing:5px;
            text-transform:uppercase; margin-top:5px;'>PROP BETTING ENGINE</div>
        </div>
        """, unsafe_allow_html=True)

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

        st.markdown("#### 🎯 Filter Thresholds")
        _min_ev = st.slider(
            "Min EV%",
            min_value=-10.0, max_value=15.0,
            value=float(st.session_state.get("min_ev", config.MIN_EV_PCT)),
            step=0.5,
            help="Slide to -10 to show all players with odds, regardless of EV.",
        )
        _min_edge = st.slider(
            "Min Edge%",
            min_value=-5.0, max_value=8.0,
            value=float(st.session_state.get("min_edge", config.MIN_EDGE_PCT)),
            step=0.5,
            help="Slide to -5 to show all players with odds, regardless of edge.",
        )
        st.session_state["min_ev"]    = _min_ev
        st.session_state["min_edge"]  = _min_edge

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

        with st.expander("📱 Add to Home Screen"):
            st.markdown("""
**iPhone (Safari)**
1. Open the app URL in Safari
2. Tap the **Share** button (box with arrow)
3. Scroll down → tap **Add to Home Screen**
4. Tap **Add** — done

**Android (Chrome)**
1. Open the app URL in Chrome
2. Tap the **⋮** menu (top-right)
3. Tap **Add to Home screen**
4. Tap **Add** — done

The app will open full-screen like a native app.
""")

        st.divider()
        # API key status indicator
        key_set = bool(config.ODDS_API_KEY)
        st.markdown(
            f"<div style='font-size:12px; padding:6px 10px; border-radius:6px; "
            f"background:{'#0a2a14' if key_set else '#2a0a0a'}; "
            f"border:1px solid {'#2ea043' if key_set else '#da3633'};'>"
            f"{'✅ Odds API key detected' if key_set else '❌ Odds API key MISSING — set in Streamlit secrets'}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Active EV filter: {_min_ev:.1f}%")
        st.caption(f"Active Edge filter: {_min_edge:.1f}%")
        backend = pnl_tracker.storage_backend()
        st.caption(f"Storage: {'☁️ Sheets' if backend == 'sheets' else '💾 Local CSV'}")
        st.caption(f"Auto-refresh: every 60 min")


if __name__ == "__main__":
    main()
