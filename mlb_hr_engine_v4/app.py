"""
Codex HR Engine — Streamlit Dashboard
"""

import sys
import html
import traceback as _tb
import urllib.parse
import datetime as _dt
from datetime import timezone as _tz, timedelta as _td
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import filter_controls as _fc


def _pf(val, default=0.0):
    """Parse a percent-or-float display value to float (strips '%', handles '--'/None)."""
    if val is None:
        return default
    try:
        v = str(val).replace("%", "").strip()
        return float(v) if v and v != "--" else default
    except ValueError:
        return default


def _badge(val, thr, fmt):
    """Green span if val >= thr, red otherwise."""
    c = "#4ade80" if val >= thr else "#f87171"
    return f"<span style='color:{c}; font-weight:700;'>{fmt}</span>"


# ── Card HTML render cache ─────────────────────────────────────────────────────
# Keyed by (card_type, slate_ts, player_id, volatile_flags...).
# Cleared when slate_ts (data_loaded_at) changes — safe for any rerender cadence.
# Covers _intelligence_card_html, _elite_card_html, and Matchup Edge inline HTML.
_CARD_CACHE: dict = {}
_CARD_CACHE_SLATE: str = ""


def _card_html(fp: tuple, builder) -> str:
    """Return cached card HTML or build+cache it. builder is a zero-arg callable."""
    global _CARD_CACHE, _CARD_CACHE_SLATE
    slate_ts = fp[1]  # fp[0]=card_type, fp[1]=slate_ts
    if _CARD_CACHE_SLATE != slate_ts:
        _CARD_CACHE.clear()
        _CARD_CACHE_SLATE = slate_ts
    cached = _CARD_CACHE.get(fp)
    if cached is None:
        cached = builder()
        _CARD_CACHE[fp] = cached
    return cached


st.set_page_config(
    page_title="Codex HR Engine",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="auto",
)

# PWA + mobile home-screen support
# iOS: "Add to Home Screen" in Safari makes this launch full-screen, no browser chrome
# Android: Chrome will prompt "Install App" automatically with these tags
st.markdown("""
<head>
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Codex HR Engine">
<meta name="theme-color" content="#0d0d0d">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<link rel="apple-touch-icon" href="https://em-content.zobj.net/source/apple/354/baseball_26be.png">
<link rel="manifest" href="data:application/json,{
  &quot;name&quot;: &quot;Codex HR Engine&quot;,
  &quot;short_name&quot;: &quot;Codex HR Engine&quot;,
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

# Fix path for both local and Streamlit Cloud
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Debug module loading for Streamlit Cloud
try:
    import config
    from engine.market import american_to_decimal, decimal_to_american
    from engine.ev import expected_value_pct
    from output.parlay import _evaluate_parlay, parlay_bet_size
    from output.ranker import rank_picks as _rank_picks
    from tracking import pnl as pnl_tracker, clv as clv_tracker
    from tracking import line_movement as lm_tracker
    from strategies_ui import tab_advanced_strategies
    from clients.pull_air import resolve_pull_air_pct
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Directory exists: {current_dir.exists()}")
    print(f"sys.path: {sys.path[:3]}")
    # Try alternative import method
    import importlib.util
    spec = importlib.util.spec_from_file_location("output.parlay", current_dir / "output" / "parlay.py")
    if spec and spec.loader:
        parlay_module = importlib.util.module_from_spec(spec)
        sys.modules["output.parlay"] = parlay_module
        spec.loader.exec_module(parlay_module)
        _evaluate_parlay = parlay_module._evaluate_parlay
        parlay_bet_size = parlay_module.parlay_bet_size
    # Import the rest normally after fixing parlay
    import config
    from engine.market import american_to_decimal, decimal_to_american
    from engine.ev import expected_value_pct
    from output.ranker import rank_picks as _rank_picks
    from tracking import pnl as pnl_tracker, clv as clv_tracker
    from tracking import line_movement as lm_tracker
    from clients.pull_air import resolve_pull_air_pct
    # Try to import strategies UI
    try:
        from strategies_ui import tab_advanced_strategies
    except ImportError:
        def tab_advanced_strategies(data, parlays_callback=None):
            st.info("Advanced strategies module is being loaded...")

# â"€â"€ Styling â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;700;900&display=swap');

/* â"€â"€ Animations â"€â"€ */
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

/* â"€â"€ Base â"€â"€ */
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

/* â"€â"€ Tabs â"€â"€ */
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

/* â"€â"€ Cards â"€â"€ */
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
.stat-box { background: #111128; border-radius: 5px; padding: 5px 8px; font-size: 11px; }
.stat-box-green { background: #111828; border-radius: 5px; padding: 5px 8px; font-size: 11px; }

/* â"€â"€ Section headers â"€â"€ */
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

/* â"€â"€ Range bar â"€â"€ */
.range-bar {
    font-size: 12px;
    background: linear-gradient(90deg, #110000 0%, #090000 100%);
    border: 1px solid #2a0000;
    border-left: 4px solid #C6011F;
    border-radius: 6px; padding: 10px 16px; margin-bottom: 14px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

/* â"€â"€ Rating badges â"€â"€ */
.r-goat { color:#FFD700; font-weight:900; font-size:14px; text-shadow: 0 0 8px rgba(255,215,0,0.6); }
.r-fire { color:#FF5500; font-weight:900; font-size:14px; text-shadow: 0 0 8px rgba(255,85,0,0.5); }
.r-good { color:#4ade80; font-weight:800; font-size:13px; }
.r-marg { color:#666666; font-weight:400; font-size:12px; }

/* â"€â"€ Metrics â"€â"€ */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #120000 0%, #080000 100%);
    border: 1px solid #380000;
    border-top: 3px solid #C6011F;
    border-radius: 10px; padding: 14px 16px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.5);
}
[data-testid="stMetricLabel"] {
    color: #666666 !important; font-size: 10px !important;
    letter-spacing: 1.5px; text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important; font-weight: 900 !important;
    font-size: 1.8rem !important;
}

/* â"€â"€ Dataframe â"€â"€ */
[data-testid="stDataFrame"] {
    border: 1px solid #2a0000; border-radius: 8px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.6);
}

/* â"€â"€ Buttons â"€â"€ */
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

/* â"€â"€ Inputs â"€â"€ */
[data-testid="stNumberInput"] input {
    background: #0f0000 !important; border: 1px solid #440000 !important;
    color: #FFD700 !important; font-weight: 800 !important; font-size: 16px !important;
    border-radius: 6px !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] { color: #555; }

/* â"€â"€ Divider â"€â"€ */
hr { border-color: #1e0000 !important; margin: 12px 0 !important; }

/* â"€â"€ Selectbox â"€â"€ */
div[data-testid="stSelectbox"] label { font-size: 12px; color: #666; }

/* â"€â"€ Alert boxes â"€â"€ */
[data-testid="stAlert"] { border-radius: 8px !important; border-left-width: 4px !important; }

/* ══════════════════════════ TACTICAL INTELLIGENCE CARD SYSTEM ══════════════════════════ */

/* Pitch attack vulnerability tags — always visible on Level 1 card */
.tac-pitch-tag {
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 3px;
    font-weight: 600;
    white-space: nowrap;
    display: inline-block;
    margin: 1px 2px 1px 0;
}
.tac-pitch-favorable { background: #0a2010; color: #4ade80; border: 1px solid #1a5530; }
.tac-pitch-vulnerable { background: #200808; color: #f87171; border: 1px solid #550a0a; }
.tac-pitch-neutral    { background: #0a0a14; color: #94a3b8; border: 1px solid #1e2a3a; }

/* Tactical feed card button — minimal chrome, acts as click trigger */
.tac-btn .stButton button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #555 !important;
    font-size: 10px !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
    text-transform: none !important;
    padding: 2px 6px !important;
    min-height: 22px !important;
    margin-bottom: 2px !important;
}
.tac-btn .stButton button:hover {
    background: rgba(198,1,31,0.08) !important;
    color: #f0f0f0 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ══════════════════════════ MOBILE ══════════════════════════ */
@media (max-width: 768px) {
    /* Main content — tighter padding */
    .main .block-container {
        padding-left: 8px !important;
        padding-right: 8px !important;
        padding-top: 8px !important;
        max-width: 100% !important;
    }

    /* Primary tabs — compact for 3 tabs on a 375px screen */
    .stTabs [data-baseweb="tab"] {
        height: 44px !important;
        padding: 0 10px !important;
        font-size: 9px !important;
        letter-spacing: 0.3px !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 10px !important; }

    /* Section headers — no overflow */
    .section-header {
        font-size: 13px !important;
        letter-spacing: 0.5px !important;
        padding: 7px 0 7px 10px !important;
        margin: 14px 0 10px 0 !important;
        word-break: break-word !important;
    }

    /* Range bar — let items wrap */
    .range-bar {
        font-size: 11px !important;
        padding: 8px 10px !important;
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 4px 10px !important;
    }

    /* Cards */
    .combo-card { padding: 10px 12px !important; }
    .leg-pill { font-size: 11px !important; padding: 4px 8px !important; margin: 3px 2px !important; }

    /* Metrics — smaller value, tighter box */
    [data-testid="stMetric"] { padding: 10px 10px !important; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    [data-testid="stMetricLabel"] { font-size: 9px !important; }

    /* Columns — wrap so 5-col layouts become 2-per-row instead of 5 squished */
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    [data-testid="column"] { min-width: 140px !important; flex: 1 1 140px !important; }

    /* Buttons — minimum 44px touch target */
    .stButton button {
        min-height: 44px !important;
        font-size: 10px !important;
        letter-spacing: 1px !important;
    }

    /* Rating badges */
    .r-goat, .r-fire { font-size: 12px !important; }
    .r-good, .r-marg { font-size: 11px !important; }

    /* Alerts */
    [data-testid="stAlert"] { font-size: 13px !important; }

    /* Sidebar toggle button — larger touch target (Streamlit default is small) */
    [data-testid="stSidebarCollapseButton"] button { min-width: 44px !important; min-height: 44px !important; }
}

/* ── Momentum scrolling for dataframe containers on iOS ── */
@media (max-width: 768px) {
    [data-testid="stDataFrame"] > div { -webkit-overflow-scrolling: touch; }
}
</style>
""", unsafe_allow_html=True)


# â"€â"€ Rating helpers â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€

def _pick_rating(ev_pct: float, edge_pct: float, model_prob: float, confidence: float) -> str:
    # EV% is capped at ~45% max (model prob capped at 1.4x market before calculation).
    # Thresholds calibrated to that compressed scale:
    #   5-15% EV  → solid play (model sees modest mispricing)
    #   15-30% EV → strong edge (clear disagreement with confident signal)
    #   30%+ EV   → once in a lifetime (rare: high EV + big edge + high confidence)
    if ev_pct >= 30 and edge_pct >= 12 and confidence >= 65:
        return "🌟 ONCE IN A LIFETIME"
    if (ev_pct >= 18 and edge_pct >= 7 and confidence >= 50) or \
       (ev_pct >= 12 and edge_pct >= 5 and confidence >= 50):
        return "🔥 STRONG EDGE"
    if ev_pct >= 5 and edge_pct >= 2:
        return "✅ SOLID PLAY"
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


# ── Auto-refresh fragment ─────────────────────────────────────────────────────
@st.fragment(run_every=60)
def _auto_refresh_ticker():
    """Ticks every 60 s. Clears data cache and triggers full rerun when interval is met."""
    if not st.session_state.get("auto_refresh_on"):
        return
    loaded_at = st.session_state.get("data_loaded_at")
    if not loaded_at:
        return
    interval_min = int(st.session_state.get("auto_refresh_interval", 15))
    elapsed_min  = (_dt.datetime.now() - loaded_at).total_seconds() / 60
    if elapsed_min >= interval_min:
        from clients import mlb_stats as _ms_ar, statcast as _sc_ar
        _ms_ar.clear_all_caches()
        _sc_ar.clear_all_caches()
        st.cache_data.clear()
        for k in ["data", "cache_key", "data_loaded_at"]:
            st.session_state.pop(k, None)
        st.toast("↻ Auto-refreshing data now — page will reload momentarily")
        st.rerun()


# ── Data loading ──────────────────────────────────────────────────────────────
def get_data():
    import gc
    from pipeline import load_game_data
    # Always derive "today" in Eastern Time — MLB schedules run on ET and the
    # system clock may be UTC, which rolls to the next day at 8 PM ET.
    target_date = config.TARGET_DATE or _dt.datetime.now(_EDT).strftime("%Y-%m-%d")

    if "data" not in st.session_state or st.session_state.get("cache_key") != target_date:
        with st.status("⚾ Loading MLB data — first load takes 2-4 min…", expanded=True) as _status:
            try:
                def _cb(msg: str):
                    _status.write(msg)
                    print(f"[pipeline] {msg}")

                data = load_game_data(target_date=target_date, progress_cb=_cb)
                gc.collect()  # free statcast/HTTP memory before rendering
                st.session_state["data"]           = data
                st.session_state["cache_key"]      = target_date
                st.session_state["data_loaded_at"] = _dt.datetime.now()
                _status.update(
                    label=(f"✅ Loaded — {data['stats'].get('players', 0)} players, "
                           f"{data['stats'].get('qualified', 0)} qualified"),
                    state="complete", expanded=False,
                )

                ranked      = data.get("ranked", [])
                all_players = data.get("all_players", [])
                if ranked:
                    try:
                        logged = pnl_tracker.log_picks(ranked, model_version="v4")
                        if logged:
                            clv_tracker.log_opening_lines(ranked)
                    except Exception as e:
                        st.warning(f"Pick tracking error: {e}")
                    try:
                        lm_tracker.log_current_odds(ranked)
                    except Exception as e:
                        st.warning(f"Line movement tracking error: {e}")

                # Auto-log all formula picks to unified pick tracker (no FD slip needed)
                try:
                    from tracking import pick_tracker as _pt
                    # Qualified picks — these passed all 7 filters
                    _pt.log_picks_bulk(ranked, source_tab="Engine", source_section="Qualified Picks")
                    # All players the engine scored (for calibration across the full prob range)
                    _ranked_names = {p.get("player_name") for p in ranked}
                    non_ranked = [p for p in all_players if p.get("player_name") not in _ranked_names]
                    _pt.log_picks_bulk(non_ranked, source_tab="Engine", source_section="All Players")
                except Exception as e:
                    pass  # never block the UI for tracking errors

                try:
                    pnl_tracker.settle_all_unsettled()
                except Exception as e:
                    st.warning(f"Outcome settlement error: {e}")

                # Store pitcher map for change detection
                try:
                    from clients.mlb_stats import get_today_pitcher_map
                    pm = get_today_pitcher_map()
                    # session_start map is set once per session — never overwritten
                    if "pitcher_map_session_start" not in st.session_state:
                        st.session_state["pitcher_map_session_start"] = pm
                    # at_load map updates on every refresh — diff vs session_start
                    old_map = st.session_state.get("pitcher_map_session_start", {})
                    changes = {}
                    for team, info in pm.items():
                        old_info = old_map.get(team, {})
                        if (old_info.get("id") and info.get("id")
                                and old_info["id"] != info["id"]):
                            changes[team] = {
                                "old": old_info.get("name", "?"),
                                "new": info.get("name", "?"),
                            }
                    st.session_state["pitcher_map_at_load"] = pm
                    st.session_state["pitcher_changes"] = changes
                except Exception:
                    pass

            except Exception as e:
                _status.update(label="❌ Load failed — see error below", state="error")
                _err_str = str(e).lower()
                if "odds" in _err_str or "api key" in _err_str or "401" in _err_str or "403" in _err_str:
                    st.error("Odds API failed. Check your API key in the sidebar Settings section.")
                elif "mlb" in _err_str or "statsapi" in _err_str or "connection" in _err_str or "timeout" in _err_str:
                    st.error("MLB Stats API unreachable. Check your internet connection and try Force Refresh.")
                else:
                    st.error(f"Failed to load game data: {e}")
                if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())
                st.session_state["data"] = {
                    "ranked": [], "date": target_date, "stats": {},
                    "odds_source": "error", "batter_count": 0,
                    "all_by_model": [], "all_players": [], "games": [],
                    "team_players": {}, "auto_parlays": {}, "profile_parlays": [],
                }
                st.session_state["cache_key"] = target_date

    return st.session_state["data"]


# â"€â"€ Helpers â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
def _fmt_american(odds) -> str:
    if odds is None:
        return "--"
    return f"+{odds}" if int(odds) > 0 else str(odds)


# ── Stat color coding ──────────────────────────────────────────────────────────
_DARK_GREEN = "background-color:#14532d; color:#f0f0f0"
_GREEN      = "background-color:#166534; color:#f0f0f0"
_RED        = "background-color:#7f1d1d; color:#f0f0f0"
_DARK_RED   = "background-color:#450a0a; color:#f0f0f0"

def _stat_css(col: str, val) -> str:
    """Return CSS style string for a stat cell based on column name and value."""
    try:
        raw = float(str(val).replace("%", "").replace("+", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return ""
    if col == "Brl%":
        if raw >= 10:  return _DARK_GREEN
        if raw >= 5.2: return _GREEN
        if raw >= 3:   return _RED
        return _DARK_RED
    if col == "SwSp%":
        if raw >= 40:  return _DARK_GREEN
        if raw >= 34:  return _GREEN
        if raw >= 28:  return _RED
        return _DARK_RED
    if col in ("EV mph", "Exit Velo"):
        if raw >= 95:   return _DARK_GREEN
        if raw >= 88.9: return _GREEN
        if raw >= 85:   return _RED
        return _DARK_RED
    if col == "FB%":
        if raw >= 40: return _DARK_GREEN
        if raw >= 36: return _GREEN
        if raw >= 30: return _RED
        return _DARK_RED
    if col == "GB%":
        if raw <= 20: return _DARK_GREEN
        if raw <= 24: return _GREEN
        if raw <= 29: return ""
        if raw <= 40: return _RED
        return _DARK_RED
    if col in ("EV%",):
        if raw >= 20: return _DARK_GREEN
        if raw >= 10: return _GREEN
        if raw >= 3:  return ""
        return _RED
    if col in ("Edge", "Edge%"):
        if raw >= 10: return _DARK_GREEN
        if raw >= 5:  return _GREEN
        if raw >= 2:  return ""
        return _RED
    if col == "Model%":
        if raw >= 25: return _DARK_GREEN
        if raw >= 15: return _GREEN
        if raw >= 8:  return ""
        return _RED
    if col == "Conf":
        if raw >= 70: return _DARK_GREEN
        if raw >= 50: return _GREEN
        if raw >= 30: return ""
        return _RED
    if col == "PwrMult":
        if raw >= 1.40: return _DARK_GREEN
        if raw >= 1.10: return _GREEN
        if raw >= 0.90: return ""
        if raw >= 0.70: return _RED
        return _DARK_RED
    if col == "Confidence":
        if raw >= 70: return _DARK_GREEN
        if raw >= 50: return _GREEN
        if raw >= 30: return ""
        return _RED
    if col in ("Hard Hit%", "Hard Hit"):
        if raw >= 47: return _DARK_GREEN
        if raw >= 40: return _GREEN
        if raw >= 35: return _RED
        return _DARK_RED
    if col == "HR Win%":
        if raw >= 40: return _DARK_GREEN
        if raw >= 34: return _GREEN
        if raw >= 28: return _RED
        return _DARK_RED
    if col == "xSLG":
        if raw >= 0.500: return _DARK_GREEN
        if raw >= 0.420: return _GREEN
        if raw >= 0.350: return _RED
        return _DARK_RED
    if col == "Barrel%":
        if raw >= 10:  return _DARK_GREEN
        if raw >= 5.2: return _GREEN
        if raw >= 3:   return _RED
        return _DARK_RED
    if col == "Pull AIR":
        if raw >= 25: return _DARK_GREEN
        if raw >= 18: return _GREEN
        if raw >= 12: return _RED
        return _DARK_RED
    if col == "ISO":
        if raw >= 0.230: return _DARK_GREEN
        if raw >= 0.170: return _GREEN
        if raw >= 0.130: return _RED
        return _DARK_RED
    if col in ("HVY", "HVY Base"):
        if raw >= 70: return _DARK_GREEN
        if raw >= 50: return _GREEN
        if raw >= 35: return _RED
        return _DARK_RED
    return ""

def _stat_badge(col: str, val) -> str:
    """Return emoji-prefixed value so quality shows without Styler (works with column_config)."""
    css = _stat_css(col, val)
    if css == _DARK_GREEN: return f"💚 {val}"
    if css == _GREEN:      return f"🟢 {val}"
    if css == _RED:        return f"🔴 {val}"
    if css == _DARK_RED:   return f"⛔ {val}"
    return str(val)


_HEAT_COLS = {
    "Brl%", "SwSp%", "EV mph", "Exit Velo", "FB%", "GB%", "EV%", "Edge", "Edge%",
    "Model%", "Conf", "PwrMult", "Confidence", "Hard Hit%", "Hard Hit",
    "HR Win%", "xSLG", "Barrel%", "Pull AIR", "ISO", "HVY", "HVY Base",
}

_HEAT_NEUTRAL = "background-color:#0f172a; color:#94a3b8"
_HEAT_BASE    = "background-color:#0f172a; color:#e2e8f0; font-size:12px"


def _apply_heatmap(df: "pd.DataFrame") -> "pd.io.formats.style.Styler":
    """Apply per-cell background colors to stat columns using _stat_css thresholds."""
    styler = df.style.set_properties(**{
        "background-color": "#0f172a",
        "color": "#e2e8f0",
        "font-size": "12px",
    })
    for col in df.columns:
        if col in _HEAT_COLS:
            styler = styler.apply(
                lambda s, c=col: [
                    _stat_css(c, v) or _HEAT_NEUTRAL
                    for v in s
                ],
                axis=0,
                subset=[col],
            )
    return styler


def _edge_col(edge) -> str:
    """Inline HTML text color for an edge% value."""
    try:
        edge = float(edge or 0)
    except (TypeError, ValueError):
        edge = 0.0
    if edge >= 10: return "#4ade80"
    if edge >= 5:  return "#86efac"
    if edge >= 2:  return "#f0f0f0"
    return "#f87171"


_MLB_PHOTO_BASE = (
    "https://img.mlbstatic.com/mlb-photos/image/upload"
    "/d_people:generic:headshot:67:current.png"
    "/w_{w},q_auto:best/v1/people/{pid}/headshot/67/current"
)


def _player_photo_html(player_id, size: int = 48, style: str = "") -> str:
    """Return an <img> tag for an MLB player headshot, or '' if no player_id."""
    if not player_id:
        return ""
    url = _MLB_PHOTO_BASE.format(pid=player_id, w=max(size * 2, 64))
    base = (
        f"width:{size}px;height:{size}px;border-radius:50%;"
        f"object-fit:cover;object-position:top center;"
        f"flex-shrink:0;margin-right:10px;"
    )
    return (
        f"<img src='{url}' style='{base}{style}' "
        f"onerror=\"this.src='https://img.mlbstatic.com/mlb-photos/image/upload"
        f"/d_people:generic:headshot:67:current.png/w_128,q_auto:best"
        f"/v1/people/0/headshot/67/current'\"/>"
    )


def _combo_html(parlay: dict, label: str) -> str:
    legs_html = ""
    for leg in parlay["legs"]:
        odds_str  = _fmt_american(leg.get("best_american"))
        _l_mdl    = leg.get("model_prob", 0) * 100
        _l_ev     = leg.get("ev_pct", 0)
        _l_edge   = leg.get("edge_pct", 0)
        _l_tier   = leg.get("confidence_tier", "C")
        _l_tc     = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_l_tier, "#888")
        _l_ev_c   = "#4ade80" if _l_ev >= 0 else "#f87171"
        _l_pit    = leg.get("pitcher_name", "")
        _l_pit_f  = leg.get("pitcher_factor", 1.0)
        _l_plat   = leg.get("platoon_factor", 1.0)
        _l_pit_lbl = _pitcher_label(_l_pit, _l_pit_f, _l_plat) if _l_pit else ""
        legs_html += (
            f'<div class="leg-pill">'
            f'<b>{leg["player_name"]}</b> '
            f'<span style="color:#888888">({leg.get("team","")})</span> '
            f'<span class="odds-badge">{odds_str}</span>'
            f'<span style="font-size:10px;color:#a78bfa;margin-left:6px;">{_l_mdl:.0f}%&nbsp;MDL</span>'
            f'<span style="font-size:10px;color:{_l_ev_c};margin-left:5px;">EV&nbsp;{_l_ev:+.1f}%</span>'
            f'<span style="font-size:10px;color:#60a5fa;margin-left:5px;">Edge&nbsp;{_l_edge:+.1f}%</span>'
            f'<span style="font-size:10px;color:{_l_tc};font-weight:700;margin-left:5px;">{_l_tier}</span>'
            + (f'<span style="font-size:10px;color:#94a3b8;margin-left:8px;">vs {_l_pit_lbl}</span>' if _l_pit_lbl else '')
            + f'</div>'
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


def _fanduel_url(player_name: str = "") -> str:
    if player_name:
        q = urllib.parse.quote(player_name)
        return f"https://sportsbook.fanduel.com/search?q={q}"
    return "https://sportsbook.fanduel.com/baseball/mlb?tab=player-home-runs"


def _deg_to_compass(deg: float) -> str:
    """Convert wind direction degrees to 16-point compass label."""
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[round(deg / 22.5) % 16]


def _weather_summary(player: dict) -> str:
    """Return compact weather string e.g. '78°F · 12mph SW' or '' for domes."""
    w = player.get("weather")
    if not w:
        return ""
    wf = player.get("weather_factor", 1.0)
    if wf is None:
        wf = 1.0
    # Dome teams have weather_factor exactly 1.0 from a suppressed calc; check flag too
    is_dome = player.get("is_dome", False)
    temp   = w.get("temp_f")
    speed  = w.get("wind_mph")
    deg    = w.get("wind_deg")
    if temp is None:
        return ""
    parts = [f"{temp:.0f}°F"]
    if speed is not None and not is_dome:
        compass = _deg_to_compass(deg) if deg is not None else ""
        parts.append(f"{speed:.0f} mph {compass}".strip())
    elif is_dome:
        parts.append("Dome")
    return " · ".join(parts)


def _weather_badge(player: dict) -> str:
    """Return HTML weather badge for use in cards. Empty string if no data."""
    summary = _weather_summary(player)
    if not summary:
        return ""
    wf = player.get("weather_factor", 1.0) or 1.0
    # Color-code: strong boost (>1.08) green, suppressor (<0.93) red, else grey
    color = "#4ade80" if wf >= 1.08 else "#f87171" if wf <= 0.93 else "#888"
    return (
        f"<span style='font-size:11px; color:{color};'>🌤 {summary}</span>"
    )


def _hr_env_score(player: dict) -> tuple:
    """Return (score 0–100, color, label) for combined HR environment (park × weather × platoon)."""
    pk = float(player.get("park_factor",    1.0) or 1.0)
    wf = float(player.get("weather_factor", 1.0) or 1.0)
    pf = float(player.get("platoon_factor", 1.0) or 1.0)
    score = min(100, max(0, (pk * wf * pf - 0.75) / 0.65 * 100))
    if score >= 75: return score, "#4ade80", "HOT"
    if score >= 58: return score, "#86efac", "WARM"
    if score >= 42: return score, "#888888", "NEUT"
    return score, "#f87171", "COLD"


def _pitch_attack_tags(ctx: dict, player: dict, max_tags: int = 2) -> list:
    """
    Return list of (label, css_class) showing top pitch vulnerability/attack signals.
    Green = batter wins this pitch. Red = pitcher wins. Blue = primary pitch.
    """
    from clients.pitch_mix import pitch_label as _pl
    if not ctx:
        return []
    pitch_mix       = ctx.get("pitch_mix", {})
    pitcher_arsenal = pitch_mix.get("arsenal", ctx.get("pitcher_arsenal", []))
    batter_rows     = pitch_mix.get("batter_rows", ctx.get("batter_rows", []))
    if not pitcher_arsenal:
        return []
    batter_slg = {
        br.get("pitch_type", ""): float(br.get("slg", 0.0) or 0.0)
        for br in batter_rows if (br.get("pa") or 0) >= 3
    }
    _LG_WHIFF = 0.245
    tags = []
    for px in sorted(pitcher_arsenal, key=lambda x: x.get("pitch_pct", 0), reverse=True)[:5]:
        pt    = px.get("pitch_type", "")
        lbl   = _pl(pt) if pt else pt
        use   = (px.get("pitch_pct") or 0) * 100
        whf   = float(px.get("display_whiff") or 0)
        rv    = float(px.get("display_rv100") or 0)
        hh    = float(px.get("display_hh") or 0)
        hr_r  = float(px.get("hr_rate") or 0)
        b_slg = batter_slg.get(pt, 0.0)
        _fav  = -(whf - _LG_WHIFF) * 3.0 + rv / 4.0 + (hh - 0.38) * 2.0
        if b_slg >= 0.520 or _fav >= 0.18 or hr_r >= 0.04:
            if b_slg >= 0.520:
                tag_lbl = f"{lbl} .{int(b_slg * 1000)} SLG"
            elif hr_r >= 0.04:
                tag_lbl = f"{lbl} {hr_r * 100:.1f}% HR"
            else:
                tag_lbl = f"{lbl} {use:.0f}% ✓"
            tags.append((tag_lbl, "tac-pitch-favorable"))
        elif whf >= 0.32 or _fav <= -0.20:
            tags.append((f"{lbl} {whf * 100:.0f}% whiff", "tac-pitch-vulnerable"))
        if len(tags) >= max_tags:
            break
    if not tags and pitcher_arsenal:
        top = sorted(pitcher_arsenal, key=lambda x: x.get("pitch_pct", 0), reverse=True)[0]
        pt  = top.get("pitch_type", "")
        lbl = _pl(pt) if pt else pt
        use = (top.get("pitch_pct") or 0) * 100
        tags.append((f"{lbl} {use:.0f}% primary", "tac-pitch-neutral"))
    return tags[:max_tags]


def _intelligence_card_html(
    player: dict,
    rank: int,
    ctx: dict,
    pitch_tags: list = None,
    is_steam: bool = False,
    is_live: bool = False,
    status_html: str = "",
    gt_str: str = "TBD",
    urgency_col: str = "#555",
    urgency_lbl: str = "",
    opt_active: bool = False,
    opt_selected: bool = False,
) -> str:
    """
    Render the Level 1 Tactical Intelligence Card HTML.
    Compact grid card: identity + quant pills + pitch attacks + HVY matchup bar.
    Desktop: 3-column grid. Mobile: 1-column via CSS wrap.
    """
    name     = player.get("player_name", "")
    team     = player.get("team", "")
    pit_n    = player.get("pitcher_name", "")
    pit_hand = player.get("pitcher_hand", "")
    pit_fac  = float(player.get("pitcher_factor",  1.0) or 1.0)
    plat_fac = float(player.get("platoon_factor",  1.0) or 1.0)
    spot     = player.get("lineup_spot")
    model_p  = player.get("model_prob", 0) * 100
    ev       = player.get("ev_pct")
    edge     = player.get("edge_pct")
    odds     = player.get("best_american")
    barrel   = _pf(player.get("barrel_pct"), 0.0)
    tier     = player.get("confidence_tier", "C")
    photo    = _player_photo_html(player.get("player_id"), size=34)

    # ── Value colors ──
    ev_col_      = "#4ade80" if (ev is not None and ev >= 0) else "#f87171" if ev is not None else "#64748b"
    edge_col_    = _edge_col(edge) if edge is not None else "#64748b"
    ev_display   = f"{ev:+.1f}%" if ev is not None else "—"
    edge_display = f"{edge:+.1f}%" if edge is not None else "—"
    tier_col  = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(tier, "#888")
    brl_col   = ("#4ade80" if barrel >= 10 else "#86efac" if barrel >= 8
                 else "#f0f0f0" if barrel >= 6 else "#555")
    brl_pct   = min(100, int(barrel / 18.0 * 100))

    # ── Card surface ──
    if is_live:
        acc, bg, border_s = "#f87171", "linear-gradient(145deg,#1a0000,#0e0000)", "#f87171"
    elif is_steam:
        acc, bg, border_s = "#FFD700", "linear-gradient(145deg,#0e0e00,#080800)", "#FFD700"
    elif rank <= 3:
        acc, bg, border_s = "#a78bfa", "linear-gradient(145deg,#0c0a1c,#07050f)", "#a78bfa"
    else:
        acc, bg, border_s = "#C6011F", "linear-gradient(145deg,#0c0c1c,#080808)", "#1e1e40"

    # ── Rank badge ──
    rc = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}.get(rank, "#555" if rank > 3 else "#a78bfa")
    rank_badge = (
        f"<span style='background:#1a1a30;color:{rc};font-size:9px;"
        f"font-weight:900;padding:1px 5px;border-radius:3px;"
        f"display:inline-block;text-align:center;'>#{rank}</span>"
    )

    # ── Inline badges (optimizer, steam) ──
    badges_html = ""
    if opt_active and opt_selected:
        badges_html += ("<span style='background:#0a3a0a;color:#4ade80;font-size:7px;"
                        "padding:1px 3px;border-radius:2px;margin-left:2px;'>🎯</span>")
    if is_steam:
        badges_html += ("<span style='background:#444400;color:#FFD700;font-size:7px;"
                        "padding:1px 3px;border-radius:2px;margin-left:2px;'>📈</span>")

    # ── Pitcher compact display ──
    hand_s    = "R" if pit_hand == "R" else "L" if pit_hand == "L" else ""
    plat_edge = "⚡" if plat_fac > 1.06 else ""
    if pit_fac < 0.80:    pit_col, pit_ico = "#f87171", "🔴"
    elif pit_fac < 0.92:  pit_col, pit_ico = "#fb923c", "🟠"
    elif pit_fac <= 1.08: pit_col, pit_ico = "#888",    "⬜"
    elif pit_fac <= 1.20: pit_col, pit_ico = "#facc15", "🟡"
    else:                 pit_col, pit_ico = "#4ade80", "🟢"
    pit_short   = (pit_n[:13] + "…") if len(pit_n) > 14 else pit_n
    pit_display = f"{pit_ico}{pit_short}({hand_s}){plat_edge}" if pit_n else "TBD"

    # ── Lineup spot ──
    spot_html = ""
    if spot:
        sc = "#4ade80" if spot <= 4 else "#facc15" if spot <= 6 else "#888"
        spot_html = f" <span style='color:{sc};font-size:8px;'>#{spot}</span>"
    conf_badge = "✅" if spot is not None else "⏳"

    # ── Environment score ──
    _env_score, env_col_, env_lbl = _hr_env_score(player)

    # ── HVY matchup ──
    hvy_mod = float((ctx.get("hvy_modifier") if ctx else None) or 1.0)
    if hvy_mod >= 1.20:   hvy_lbl, hvy_col = "ELITE",  "#4ade80"
    elif hvy_mod >= 1.08: hvy_lbl, hvy_col = "FAVOR",  "#86efac"
    elif hvy_mod >= 1.03: hvy_lbl, hvy_col = "SLIGHT", "#facc15"
    elif hvy_mod >= 0.97: hvy_lbl, hvy_col = "EVEN",   "#888888"
    elif hvy_mod >= 0.85: hvy_lbl, hvy_col = "TOUGH",  "#fb923c"
    else:                  hvy_lbl, hvy_col = "AVOID",  "#f87171"
    hvy_bar = min(100, max(0, int((hvy_mod - 0.75) / 0.60 * 100)))

    # ── Weather inline ──
    wf = float(player.get("weather_factor", 1.0) or 1.0)
    wsum = _weather_summary(player)
    if wsum and abs(wf - 1.0) >= 0.04:
        wc = "#4ade80" if wf >= 1.08 else "#f87171" if wf <= 0.93 else "#888"
        weather_frag = (f" <span style='font-size:9px;color:{wc};'>🌤 {wsum}</span>")
    else:
        weather_frag = ""

    # ── Pitch attack tags ──
    pitch_html = ""
    if pitch_tags:
        tag_items = "".join(
            f"<span class='tac-pitch-tag {css}'>{lbl}</span>"
            for lbl, css in pitch_tags
        )
        pitch_html = f"<div style='margin:4px 0 2px;line-height:1.6;'>{tag_items}</div>"

    odds_fmt = _fmt_american(odds) if odds else "--"

    return (
        # ── Card shell ──
        f"<div style='background:{bg};border:1px solid {border_s};border-radius:10px;"
        f"padding:10px 12px;margin-bottom:3px;position:relative;overflow:hidden;'>"

        # Top accent hairline
        f"<div style='position:absolute;top:0;left:0;right:0;height:2px;"
        f"background:linear-gradient(90deg,transparent,{acc},transparent);opacity:0.65;'></div>"

        # ── Row 1: Rank · Photo · Name/Team | Odds · Tier ──
        f"<div style='display:flex;justify-content:space-between;"
        f"align-items:flex-start;margin-bottom:5px;'>"
        f"<div style='display:flex;align-items:center;gap:5px;flex:1;min-width:0;'>"
        f"{rank_badge}{photo}"
        f"<div style='min-width:0;'>"
        f"<div style='font-size:11px;font-weight:800;color:#f0f0f0;"
        f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.2;'>"
        f"{conf_badge} {name}</div>"
        f"<div style='font-size:9px;color:#666;line-height:1.2;'>{team}{spot_html}</div>"
        f"</div></div>"
        # Right: odds + tier
        f"<div style='text-align:right;flex-shrink:0;margin-left:6px;'>"
        f"<div style='font-size:16px;font-weight:700;color:#FF6666;line-height:1;'>{odds_fmt}</div>"
        f"<div style='font-size:8px;color:{tier_col};font-weight:700;margin-top:1px;letter-spacing:0.3px;'>"
        f"{tier}-TIER{badges_html}</div>"
        f"</div></div>"

        # ── Row 2: Status / game time · Pitcher ──
        f"<div style='font-size:9px;margin-bottom:5px;line-height:1.4;'>"
        + (status_html if status_html else
           f"<span style='color:#666;'>🕐 {gt_str}</span>"
           + (f" <span style='font-weight:700;color:{urgency_col};'>{urgency_lbl}</span>"
              if urgency_lbl else ""))
        + f"<span style='margin-left:8px;'><span style='color:{pit_col};'>{pit_display}</span></span>"
        + f"</div>"

        # ── Barrel power meter ──
        + (f"<div style='background:#111;border-radius:2px;height:2px;margin:2px 0 5px;'>"
           f"<div style='background:{brl_col};width:{brl_pct}%;height:2px;border-radius:2px;'></div>"
           f"</div>"
           if barrel >= 5.0 else "")

        # ── Row 3: Stat pills — PRIMARY market signals (MDL/EV/EDGE) | SECONDARY context (BRL/ENV) ──
        + f"<div style='display:flex;gap:2px;margin-bottom:4px;'>"
        # Primary: model, EV, edge — slightly brighter bg + larger font to dominate attention
        f"<div style='flex:1;text-align:center;background:#0c0c22;border-radius:4px;padding:4px 1px;'>"
        f"<div style='font-size:13px;font-weight:700;color:#a78bfa;line-height:1.1;'>{model_p:.0f}%</div>"
        f"<div style='font-size:7px;color:#4a4a70;letter-spacing:0.3px;'>MDL</div></div>"

        f"<div style='flex:1;text-align:center;background:#0c0c22;border-radius:4px;padding:4px 1px;'>"
        f"<div style='font-size:13px;font-weight:700;color:{ev_col_};line-height:1.1;'>{ev_display}</div>"
        f"<div style='font-size:7px;color:#4a4a70;'>EV</div></div>"

        f"<div style='flex:1;text-align:center;background:#0c0c22;border-radius:4px;padding:4px 1px;"
        f"border-right:1px solid #1e1e35;'>"
        f"<div style='font-size:13px;font-weight:700;color:{edge_col_};line-height:1.1;'>{edge_display}</div>"
        f"<div style='font-size:7px;color:#4a4a70;'>EDGE</div></div>"

        # Secondary: barrel + environment — quieter background, standard size
        f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:4px;padding:4px 1px;'>"
        f"<div style='font-size:12px;font-weight:700;color:{brl_col};line-height:1.1;'>{barrel:.1f}%</div>"
        f"<div style='font-size:7px;color:#3a3a55;'>BRL</div></div>"

        f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:4px;padding:4px 1px;'>"
        f"<div style='font-size:10px;font-weight:700;color:{env_col_};line-height:1.1;'>{env_lbl}</div>"
        f"<div style='font-size:7px;color:#3a3a55;'>ENV</div></div>"
        f"</div>"

        # ── Row 4: Pitch attack intelligence tags ──
        + pitch_html

        # ── Row 5: HVY matchup bar + weather ──
        + f"<div style='display:flex;align-items:center;gap:5px;margin-top:4px;'>"
        f"<div style='font-size:8px;color:#555;letter-spacing:0.5px;white-space:nowrap;'>HVY</div>"
        f"<div style='flex:1;background:#111;border-radius:2px;height:3px;'>"
        f"<div style='background:{hvy_col};width:{hvy_bar}%;height:3px;border-radius:2px;'></div></div>"
        f"<div style='font-size:8px;font-weight:700;color:{hvy_col};'>{hvy_lbl}</div>"
        + weather_frag
        + f"</div>"

        f"</div>"  # end card shell
    )


def _elite_card_html(
    player: dict,
    ctx: dict,
    pitch_tags: list = None,
    is_live: bool = False,
    status_html: str = "",
    opt_active: bool = False,
    opt_selected: bool = False,
) -> str:
    """Dense analytical card for ELITE tab. Barrel-first, Statcast-rich, 2-col grid."""
    name     = player.get("player_name", "")
    team     = player.get("team", "")
    opp      = player.get("opponent", "")
    pit_n    = player.get("pitcher_name", "")
    pit_hand = player.get("pitcher_hand", "")
    pit_fac  = float(player.get("pitcher_factor",  1.0) or 1.0)
    plat_fac = float(player.get("platoon_factor",  1.0) or 1.0)
    spot     = player.get("lineup_spot")
    model_p  = player.get("model_prob", 0) * 100
    ev       = player.get("ev_pct")
    edge     = player.get("edge_pct")
    odds     = player.get("best_american")
    barrel   = _pf(player.get("barrel_pct"), 0.0)
    hh       = _pf(player.get("hard_hit"), 0.0)
    xslg     = _pf(player.get("xslg") or player.get("actual_slg"), 0.0)
    pull     = _pf(player.get("pull_pct"), 0.0)
    fb       = _pf(player.get("fb_pct"), 0.0)
    photo    = _player_photo_html(player.get("player_id"), size=36)

    # Barrel grade
    if barrel >= 15:
        grade, grade_col, bg = "GOAT",  "#FF4500", "linear-gradient(145deg,#1a0800,#0e0400)"
    elif barrel >= 12:
        grade, grade_col, bg = "ELITE", "#FFD700", "linear-gradient(145deg,#1a1200,#0e0a00)"
    elif barrel >= 10:
        grade, grade_col, bg = "POWER", "#4ade80", "linear-gradient(145deg,#051505,#030e08)"
    else:
        grade, grade_col, bg = "SOLID", "#86efac", "linear-gradient(145deg,#051509,#030e07)"

    border_s = "#f87171" if is_live else (grade_col + "55")

    # Pitcher compact display
    hand_s    = "R" if pit_hand == "R" else "L" if pit_hand == "L" else ""
    plat_edge = "⚡" if plat_fac > 1.06 else ""
    if pit_fac < 0.80:    pit_col, pit_ico = "#f87171", "🔴"
    elif pit_fac < 0.92:  pit_col, pit_ico = "#fb923c", "🟠"
    elif pit_fac <= 1.08: pit_col, pit_ico = "#888",    ""
    elif pit_fac <= 1.20: pit_col, pit_ico = "#facc15", "🟡"
    else:                 pit_col, pit_ico = "#4ade80", "🟢"
    pit_short   = (pit_n[:14] + "…") if len(pit_n) > 15 else pit_n
    pit_display = f"{pit_ico}{pit_short}({hand_s}){plat_edge}" if pit_n else "TBD"

    # Lineup spot
    conf_badge = "✅" if spot is not None else "⏳"
    spot_html  = ""
    if spot:
        sc = "#4ade80" if spot <= 4 else "#facc15" if spot <= 6 else "#888"
        spot_html = f" <span style='color:{sc};'>#{spot}</span>"

    # Stat coloring
    brl_pct      = min(100, int(barrel / 18.0 * 100))
    ev_col_      = "#4ade80" if (ev is not None and ev >= 0) else "#f87171" if ev is not None else "#64748b"
    edge_col_    = _edge_col(edge) if edge is not None else "#64748b"
    ev_display   = f"{ev:+.1f}%" if ev is not None else "—"
    edge_display = f"{edge:+.1f}%" if edge is not None else "—"
    brl_col   = ("#FF4500" if barrel >= 15 else "#FFD700" if barrel >= 12
                 else "#4ade80" if barrel >= 10 else "#86efac")
    hh_col    = "#4ade80" if hh >= 44 else "#86efac" if hh >= 40 else "#888"
    xslg_col  = "#4ade80" if xslg >= 0.500 else "#86efac" if xslg >= 0.450 else "#888"
    pull_col  = "#4ade80" if pull >= 42 else "#f0f0f0" if pull >= 35 else "#888"
    fb_col    = "#4ade80" if fb >= 32 else "#f0f0f0" if fb >= 26 else "#888"
    xslg_lbl  = "xSLG" if _pf(player.get("xslg"), 0.0) > 0.0 else "SLG"

    # Environment
    _env_score, env_col_, env_lbl = _hr_env_score(player)

    # HVY matchup
    hvy_mod = float((ctx.get("hvy_modifier") if ctx else None) or 1.0)
    if hvy_mod >= 1.20:   hvy_lbl, hvy_col = "ELITE",  "#4ade80"
    elif hvy_mod >= 1.08: hvy_lbl, hvy_col = "FAVOR",  "#86efac"
    elif hvy_mod >= 1.03: hvy_lbl, hvy_col = "SLIGHT", "#facc15"
    elif hvy_mod >= 0.97: hvy_lbl, hvy_col = "EVEN",   "#888888"
    elif hvy_mod >= 0.85: hvy_lbl, hvy_col = "TOUGH",  "#fb923c"
    else:                  hvy_lbl, hvy_col = "AVOID",  "#f87171"
    hvy_bar = min(100, max(0, int((hvy_mod - 0.75) / 0.60 * 100)))

    # Weather
    wf = float(player.get("weather_factor", 1.0) or 1.0)
    wsum = _weather_summary(player)
    if wsum and abs(wf - 1.0) >= 0.04:
        wc = "#4ade80" if wf >= 1.08 else "#f87171" if wf <= 0.93 else "#888"
        weather_frag = f" <span style='font-size:9px;color:{wc};'>🌤 {wsum}</span>"
    else:
        weather_frag = ""

    # Pitch tags
    pitch_html = ""
    if pitch_tags:
        tag_items = "".join(
            f"<span class='tac-pitch-tag {css}'>{lbl}</span>"
            for lbl, css in pitch_tags
        )
        pitch_html = f"<div style='margin:4px 0 2px;line-height:1.6;'>{tag_items}</div>"

    # Optimizer badge
    opt_badge = (
        "<span style='background:#0a3a0a;color:#4ade80;font-size:7px;"
        "padding:1px 3px;border-radius:2px;margin-left:3px;'>🎯 OPT</span>"
        if opt_active and opt_selected else ""
    )
    odds_fmt = _fmt_american(odds) if odds else "--"

    return (
        f"<div style='background:{bg};border:1px solid {border_s};border-radius:10px;"
        f"padding:10px 12px;margin-bottom:3px;position:relative;overflow:hidden;'>"

        # Top accent hairline
        f"<div style='position:absolute;top:0;left:0;right:0;height:2px;"
        f"background:linear-gradient(90deg,transparent,{grade_col},transparent);opacity:0.7;'></div>"

        # ── Row 1: Photo · Name/matchup | Grade + BRL% ──
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;'>"
        f"<div style='display:flex;align-items:center;gap:6px;flex:1;min-width:0;'>"
        f"{photo}"
        f"<div style='min-width:0;'>"
        f"<div style='font-size:11px;font-weight:800;color:#f0f0f0;"
        f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.2;'>"
        f"{conf_badge} {name}</div>"
        f"<div style='font-size:9px;color:#666;line-height:1.2;'>{team} vs {opp}{spot_html}</div>"
        f"</div></div>"
        f"<div style='text-align:right;flex-shrink:0;margin-left:6px;'>"
        f"<div style='font-size:20px;font-weight:900;color:{grade_col};line-height:1;'>{barrel:.1f}%</div>"
        f"<div style='font-size:8px;font-weight:700;color:{grade_col};letter-spacing:0.5px;'>"
        f"{grade}{opt_badge}</div>"
        f"</div></div>"

        # ── Barrel power meter ──
        f"<div style='background:#111;border-radius:3px;height:4px;margin:0 0 6px;'>"
        f"<div style='background:{grade_col};width:{brl_pct}%;height:4px;border-radius:3px;"
        f"box-shadow:0 0 8px {grade_col}66;'></div></div>"

        # ── Row 2: Statcast power cluster — BRL is the hero metric here ──
        f"<div style='display:flex;gap:2px;margin-bottom:5px;'>"
        f"<div style='flex:1;text-align:center;background:#0e0e0e;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:13px;font-weight:900;color:{brl_col};line-height:1.1;'>{barrel:.1f}%</div>"
        f"<div style='font-size:7px;color:#4a4a4a;letter-spacing:0.3px;'>BRL</div></div>"

        f"<div style='flex:1;text-align:center;background:#0e0e0e;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:11px;font-weight:700;color:{hh_col};line-height:1.1;'>{hh:.0f}%</div>"
        f"<div style='font-size:7px;color:#3a3a3a;'>HH%</div></div>"

        f"<div style='flex:1;text-align:center;background:#0e0e0e;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:11px;font-weight:700;color:{xslg_col};line-height:1.1;'>{xslg:.3f}</div>"
        f"<div style='font-size:7px;color:#3a3a3a;'>{xslg_lbl}</div></div>"

        f"<div style='flex:1;text-align:center;background:#0e0e0e;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:11px;font-weight:700;color:{pull_col};line-height:1.1;'>{pull:.0f}%</div>"
        f"<div style='font-size:7px;color:#3a3a3a;'>PULL</div></div>"

        f"<div style='flex:1;text-align:center;background:#0e0e0e;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:11px;font-weight:700;color:{fb_col};line-height:1.1;'>{fb:.0f}%</div>"
        f"<div style='font-size:7px;color:#3a3a3a;'>FB%</div></div>"
        f"</div>"

        # ── Row 3: Market signals — EV and EDGE are primary decision signals ──
        f"<div style='display:flex;gap:2px;margin-bottom:4px;'>"
        f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:11px;font-weight:700;color:#a78bfa;line-height:1.1;'>{model_p:.0f}%</div>"
        f"<div style='font-size:7px;color:#3a3a55;'>MDL</div></div>"

        f"<div style='flex:1;text-align:center;background:#0c0c22;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:12px;font-weight:700;color:{ev_col_};line-height:1.1;'>{ev_display}</div>"
        f"<div style='font-size:7px;color:#4a4a70;'>EV</div></div>"

        f"<div style='flex:1;text-align:center;background:#0c0c22;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:12px;font-weight:700;color:{edge_col_};line-height:1.1;'>{edge_display}</div>"
        f"<div style='font-size:7px;color:#4a4a70;'>EDGE</div></div>"

        f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:11px;font-weight:700;color:#FF6666;line-height:1.1;'>{odds_fmt}</div>"
        f"<div style='font-size:7px;color:#3a3a55;'>ODDS</div></div>"

        f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:4px;padding:3px 1px;'>"
        f"<div style='font-size:10px;font-weight:700;color:{env_col_};line-height:1.1;'>{env_lbl}</div>"
        f"<div style='font-size:7px;color:#3a3a55;'>ENV</div></div>"
        f"</div>"

        # ── Pitcher row ──
        f"<div style='font-size:9px;color:#555;margin-bottom:4px;'>"
        f"<span style='color:{pit_col};'>{pit_display}</span>"
        + (f" · <span style='color:#444;'>{status_html}</span>" if status_html else "")
        + f"</div>"

        # ── Pitch attack tags ──
        + pitch_html

        # ── HVY matchup bar + weather ──
        + f"<div style='display:flex;align-items:center;gap:5px;margin-top:3px;'>"
        f"<div style='font-size:8px;color:#555;letter-spacing:0.5px;white-space:nowrap;'>HVY</div>"
        f"<div style='flex:1;background:#111;border-radius:2px;height:3px;'>"
        f"<div style='background:{hvy_col};width:{hvy_bar}%;height:3px;border-radius:2px;'></div></div>"
        f"<div style='font-size:8px;font-weight:700;color:{hvy_col};'>{hvy_lbl}</div>"
        + weather_frag
        + f"</div>"

        f"</div>"  # end card shell
    )


@st.dialog("⚾ Player Details", width="large")
def _show_player_modal(player: dict):
    name  = player.get("player_name", "Unknown")
    team  = player.get("team", "")
    opp   = player.get("opponent", "")
    pit   = player.get("pitcher_name", "TBD")
    spot  = player.get("lineup_spot")
    sc_src = player.get("statcast_source", "none")
    _pid  = player.get("player_id", "")

    _modal_photo = _player_photo_html(_pid, size=80, style="border:2px solid #1e3a5f;")
    st.markdown(
        f"<div style='display:flex;align-items:center;margin-bottom:6px;'>"
        f"{_modal_photo}"
        f"<div>"
        f"<div style='font-size:20px; font-weight:800; color:#f0f0f0;'>{name}</div>"
        f"<div style='font-size:13px; color:#888;'>"
        f"{team} vs {opp} &nbsp;·&nbsp; vs {pit}"
        f"{f'  &nbsp;·&nbsp;  Bat #{spot}' if spot else ''}"
        f"</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Game time / status ────────────────────────────────────────────────
    _status_html, _is_live = _game_status_badge(player)
    if _status_html:
        _live_bar = "border-left:3px solid #f87171; padding-left:8px;" if _is_live else ""
        st.markdown(
            f"<div style='font-size:12px; margin-bottom:10px; {_live_bar}'>{_status_html}</div>",
            unsafe_allow_html=True,
        )

    # ── Key metrics ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Model%",   f"{player.get('model_prob', 0)*100:.1f}%")
    c2.metric("Best Odds", _fmt_american(player.get("best_american")))
    c3.metric("EV%",   f"{player.get('ev_pct'):+.1f}%" if player.get('ev_pct') is not None else "—")
    c4.metric("Edge%", f"{player.get('edge_pct'):+.1f}%" if player.get('edge_pct') is not None else "—")

    # ── Factor breakdown ──────────────────────────────────────────────────
    st.caption("Game-day factors")
    f1, f2, f3, f4, f5 = st.columns(5)
    f1.metric("Park",    f"{player.get('park_factor',    1.0):.3f}×")
    f2.metric("Pitcher", f"{player.get('pitcher_factor', 1.0):.3f}×")
    f3.metric("Weather", f"{player.get('weather_factor', 1.0):.3f}×")
    f4.metric("Platoon", f"{player.get('platoon_factor', 1.0):.3f}×")
    f5.metric("Streak",  f"{player.get('streak_factor',  1.0):.3f}×")

    # ── Weather conditions ────────────────────────────────────────────────
    _w = player.get("weather")
    if _w:
        _wtemp  = _w.get("temp_f")
        _wspeed = _w.get("wind_mph")
        _wdeg   = _w.get("wind_deg")
        _wf     = player.get("weather_factor", 1.0) or 1.0
        _wparts = []
        if _wtemp is not None:
            _wparts.append(f"🌡️ {_wtemp:.0f}°F")
        if _wspeed is not None:
            _wcomp = _deg_to_compass(_wdeg) if _wdeg is not None else ""
            _wparts.append(f"🌬️ {_wspeed:.0f} mph {_wcomp}".strip())
        if _wparts:
            _wcolor = "#4ade80" if _wf >= 1.08 else "#f87171" if _wf <= 0.93 else "#aaaaaa"
            _wimpact = "HR boost" if _wf >= 1.08 else "HR suppressor" if _wf <= 0.93 else "Neutral"
            st.markdown(
                f"<div style='background:#0d0d20; border:1px solid #1e1e40; border-radius:6px; "
                f"padding:8px 12px; margin-top:8px; display:flex; justify-content:space-between; align-items:center;'>"
                f"<span style='color:#aaa; font-size:12px;'>Conditions: "
                f"<span style='color:#f0f0f0;'>{' &nbsp;&nbsp; '.join(_wparts)}</span></span>"
                f"<span style='font-size:11px; font-weight:700; color:{_wcolor};'>{_wimpact}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Statcast power profile ────────────────────────────────────────────
    def _pct(val, mult=100, suffix="%", dec=1):
        try:
            if val in (None, "--", ""):
                return "--"
            s = str(val).strip()
            if s.endswith("%"):
                # Already formatted as a percent string (e.g. "8.5%") — just reformat
                return f"{float(s[:-1]):.{dec}f}{suffix}"
            return f"{float(s) * mult:.{dec}f}{suffix}"
        except (TypeError, ValueError):
            return "--"

    st.caption(f"Statcast power profile — source: {sc_src}")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Barrel%",    _pct(player.get("barrel_pct")))
    s2.metric("Exit Velo",  _pct(player.get("exit_velo"), mult=1, suffix="", dec=1))
    s3.metric("Hard Hit%",  _pct(player.get("hard_hit")))
    s4.metric("Sweet Spot%",_pct(player.get("sweet_spot_pct")))

    s5, s6, s7, s8 = st.columns(4)
    s5.metric("FB%",        _pct(player.get("fb_pct")))
    s6.metric("Pull%",      _pct(player.get("pull_pct")))
    s7.metric("xSLG",       _pct(player.get("xslg"), mult=1, suffix="", dec=3))
    s8.metric("xBA",        _pct(player.get("xba"),  mult=1, suffix="", dec=3))

    # ── Season stats ──────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Season PA",  player.get("season_pa", "--"))
    t2.metric("Season HR",  player.get("season_hr", "--"))
    t3.metric("Recent PA",  player.get("recent_pa", "--"))
    t4.metric("HR Rate",    f"{player.get('hr_rate', 0)*100:.2f}%" if player.get("hr_rate") else "--")

    # ── Odds by book ──────────────────────────────────────────────────────
    _pbk = player.get("prices_by_book", {})
    if _pbk:
        st.caption("Odds by sportsbook — ★ = best price")
        _BOOK_ORDER = ["fanduel", "draftkings", "betmgm", "caesars",
                       "pointsbet", "betrivers", "bet365", "bovada"]
        _best_odds_val = player.get("best_american")
        _best_book_key = player.get("best_book", player.get("best_bookmaker", "")).lower()
        _book_items = sorted(
            [(bk, v) for bk, v in _pbk.items() if v is not None],
            key=lambda x: (
                _BOOK_ORDER.index(x[0]) if x[0] in _BOOK_ORDER else 99,
            )
        )
        _bk_cols = st.columns(min(len(_book_items), 4))
        for _bi, (_bk_key, _bk_val) in enumerate(_book_items):
            _bk_label   = _bk_key.title().replace("Betmgm", "BetMGM").replace("Pointsbet", "PointsBet")
            _bk_fmt     = _fmt_american(_bk_val)
            _is_best    = (_bk_val == _best_odds_val) or (_bk_key == _best_book_key)
            _bk_color   = "#4ade80" if _is_best else "#f0f0f0"
            _bk_bg      = "#0d2a0d" if _is_best else "#0d0d20"
            _bk_border  = "#1a5c1a" if _is_best else "#1e1e40"
            _best_badge = " ★" if _is_best else ""
            with _bk_cols[_bi % 4]:
                if _bk_key == "fanduel":
                    st.link_button(
                        f"{_bk_label}{_best_badge}  {_bk_fmt}",
                        _fanduel_url(name),
                        use_container_width=True,
                    )
                else:
                    st.markdown(
                        f"<div style='background:{_bk_bg}; border:1px solid {_bk_border}; "
                        f"border-radius:6px; padding:8px 10px; text-align:center; margin-bottom:6px;'>"
                        f"<div style='font-size:10px; color:#888;'>{_bk_label}{_best_badge}</div>"
                        f"<div style='font-size:18px; font-weight:700; color:{_bk_color};'>{_bk_fmt}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    # ── Bet sizing ────────────────────────────────────────────────────────
    _bet_size   = player.get("bet_size") or player.get("bet_dollars")
    _confidence = player.get("confidence")
    _score      = player.get("score")
    if any(x is not None for x in [_bet_size, _confidence, _score]):
        st.divider()
        _eng_cols = st.columns(3)
        if _bet_size is not None:
            try:
                _eng_cols[0].metric("Suggested Bet", f"${float(_bet_size):.0f}")
            except (TypeError, ValueError):
                pass
        if _confidence is not None:
            try:
                _eng_cols[1].metric("Confidence", f"{float(_confidence):.0f}")
            except (TypeError, ValueError):
                pass
        if _score is not None:
            try:
                _eng_cols[2].metric("Score", f"{float(_score):.2f}")
            except (TypeError, ValueError):
                pass

    st.divider()

    # ── FD Slip action ────────────────────────────────────────────────────
    odds   = player.get("fanduel_american") or player.get("best_american")
    _label = f"{name} ({team}) {_fmt_american(odds)}"
    _current = st.session_state.get("fd_slip", [])
    _in_slip = _label in _current

    btn_col, fd_col = st.columns(2)
    with btn_col:
        if _in_slip:
            if st.button("✓ In Slip — Remove", type="secondary", use_container_width=True, key="modal_slip_rm"):
                st.session_state["fd_slip"] = [x for x in _current if x != _label]
                st.session_state.pop("fd_slip_select", None)
                st.rerun()
        else:
            if st.button("➕ Add to FD Slip", type="primary", use_container_width=True, key="modal_slip_add"):
                st.session_state["fd_slip"] = list(_current) + [_label]
                st.session_state.pop("fd_slip_select", None)
                _modal_src = st.session_state.get("modal_source_tab", "Player Modal")
                _modal_sec = st.session_state.get("modal_source_section", "")
                _sources = dict(st.session_state.get("fd_slip_sources", {}))
                _sources[_label] = {"tab": _modal_src, "section": _modal_sec}
                st.session_state["fd_slip_sources"] = _sources
                try:
                    from tracking import pick_tracker as _pt
                    _pt.log_pick(player, _modal_src, _modal_sec)
                except Exception:
                    pass
                st.rerun()
    with fd_col:
        st.link_button("📲 Open on FanDuel", _fanduel_url(name), use_container_width=True)

    st.divider()
    if st.button("✕ Close", use_container_width=True, key="modal_close"):
        st.rerun()


def _open_player_modal(player: dict):
    """Store player in session_state so the modal fires on the next rerun."""
    st.session_state["show_modal"] = player
    st.rerun()


def _add_legs_to_fd_slip(legs: list[dict], source_tab: str = "Parlays", source_section: str = "") -> int:
    """Merge parlay legs into the FanDuel slip and force sidebar rerender."""
    current = list(st.session_state.get("fd_slip", []))
    sources = dict(st.session_state.get("fd_slip_sources", {}))
    added = 0
    logged = []
    for p in legs:
        odds = p.get("fanduel_american") or p.get("best_american")
        label = f"{p['player_name']} ({p.get('team', '')}) {_fmt_american(odds)}"
        if label not in current:
            current.append(label)
            sources[label] = {"tab": source_tab, "section": source_section}
            added += 1
            logged.append(p)
    st.session_state["fd_slip"] = current
    st.session_state["fd_slip_sources"] = sources
    st.session_state.pop("fd_slip_select", None)
    if added:
        try:
            from tracking import pick_tracker as _pt
            for p in logged:
                _pt.log_pick(p, source_tab, source_section)
        except Exception:
            pass
        st.toast(f"✅ {added} player{'s' if added != 1 else ''} added to FD Slip!")
        st.rerun()
    return added


def _bankroll_scale() -> float:
    """Scale factor for bet sizing based on user's session bankroll vs config default."""
    session_br = st.session_state.get("bankroll_override", config.BANKROLL)
    return float(session_br) / config.BANKROLL if config.BANKROLL else 1.0


_EDT = _tz(_td(hours=-4))   # Eastern Daylight Time (Apr–Oct baseball season)


def _game_time_et(game_time_utc: str) -> "_dt.time | None":
    """Parse an ISO UTC datetime string and return the hour/minute in ET."""
    if not game_time_utc:
        return None
    try:
        dt_utc = _dt.datetime.fromisoformat(game_time_utc.replace("Z", "+00:00"))
        dt_et  = dt_utc.astimezone(_EDT)
        return _dt.time(dt_et.hour, dt_et.minute)
    except Exception:
        return None





def _gate_data(data: dict, cutoff: "int | None") -> dict:
    """Return data with all player lists filtered to games at or after cutoff ET hour."""
    if cutoff is None:
        return data
    cutoff_et_hour = (cutoff - 4) % 24
    def _keep(p):
        gt_et = _game_time_et(p.get("game_time_utc", ""))
        return gt_et is None or gt_et.hour >= cutoff_et_hour
    gated = dict(data)
    gated["all_players"] = [p for p in data.get("all_players", []) if _keep(p)]
    gated["ranked"]      = [p for p in data.get("ranked", []) if _keep(p)]
    gated["all_by_model"] = [p for p in data.get("all_by_model", []) if _keep(p)]
    gated["team_players"] = {
        team: [p for p in players if _keep(p)]
        for team, players in data.get("team_players", {}).items()
    }
    return gated


@st.cache_data(ttl=60)
def _fetch_live_status(game_pk: int) -> dict:
    """Linescore for an in-progress game, cached 60 s to avoid hammering the API."""
    try:
        from clients import mlb_stats as _ms
        return _ms.get_live_game_status(game_pk)
    except Exception:
        return {}


@st.cache_data(ttl=120, show_spinner=False)
def _cached_steam_moves() -> dict:
    """Line movement data cached 2 min — prevents disk read on every slider interaction."""
    try:
        return lm_tracker.get_movement_today()
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def _cached_pnl_results() -> list:
    """P&L results cached 5 min — prevents CSV read on every sidebar slider interaction."""
    try:
        return pnl_tracker._load_results()
    except Exception:
        return []


def _game_status_badge(player: dict) -> "tuple[str, bool]":
    """Return (html_badge, is_live) for embedding in player cards and modals.

    badge  — ready-to-embed HTML span(s)
    is_live — True when the game is currently in progress (use red card border)
    """
    gtime_utc = player.get("game_time_utc", "")
    game_pk   = player.get("game_pk")
    lineup_ok = player.get("lineup_spot") is not None
    gt_et     = _game_time_et(gtime_utc)
    if not gt_et:
        return "", False
    hour12 = gt_et.hour % 12 or 12
    ampm   = "AM" if gt_et.hour < 12 else "PM"
    gt_str = f"{hour12}:{gt_et.minute:02d} {ampm} ET"
    try:
        game_dt = _dt.datetime.fromisoformat(gtime_utc.replace("Z", "+00:00"))
        delta   = (game_dt - _dt.datetime.now(_dt.timezone.utc)).total_seconds()
    except Exception:
        return f"<span style='color:#888;'>🕐 {gt_str}</span>", False

    if delta > 60:                          # ── Upcoming ──
        h, m  = int(delta // 3600), int((delta % 3600) // 60)
        until = f"{h}h {m}m" if h else f"{m}m"
        badge = f"<span style='color:#aaa;'>🕐 {gt_str}</span> <span style='color:#f59e0b;'>· {until}</span>"
        if not lineup_ok:
            chk_dt = game_dt - _dt.timedelta(minutes=90)
            chk_et = chk_dt.astimezone(_EDT)
            ch12   = chk_et.hour % 12 or 12
            c_ampm = "AM" if chk_et.hour < 12 else "PM"
            badge += (f" <span style='color:#f59e0b;'>"
                      f"· ⏳ Lineup ~{ch12}:{chk_et.minute:02d} {c_ampm}</span>")
        return badge, False

    elif delta > -14400:                    # ── In progress ──
        live   = _fetch_live_status(game_pk) if game_pk else {}
        inning = live.get("current_inning")
        state  = live.get("inning_state", "")
        outs   = live.get("outs")
        if inning:
            def _ord(n):
                sfx = "th" if 11 <= (n % 100) <= 13 else {1:"st",2:"nd",3:"rd"}.get(n % 10, "th")
                return f"{n}{sfx}"
            arrow  = "▲" if state == "Top" else "▼" if state == "Bottom" else "—"
            outs_s = f" {outs}✕" if outs is not None else ""
            badge  = (f"<span style='color:#f87171; font-weight:800;'>● LIVE</span>"
                      f" <span style='color:#fca5a5;'>{arrow} {_ord(inning)}{outs_s}</span>")
        else:
            em    = int(-delta // 60)
            ela   = f"{em//60}h {em%60}m" if em >= 60 else f"{em}m"
            badge = (f"<span style='color:#f87171; font-weight:800;'>● LIVE</span>"
                     f" <span style='color:#888;'>· {gt_str} ({ela} ago)</span>")
        return badge, True

    return f"<span style='color:#888;'>🕐 {gt_str}</span>", False   # ── Finished ──


def _apply_ui_filters(
    players: list,
    min_ev: float,
    min_edge: float,
    cutoff_utc_hour: int | None = None,
    min_confidence: float = 0,
) -> list:
    """Re-filter all_players using sidebar thresholds (post-cache, no reload needed)."""
    import math as _math

    def _safe_float(val, default):
        try:
            v = float(val)
            return default if _math.isnan(v) or _math.isinf(v) else v
        except (TypeError, ValueError):
            return default

    result = []
    for p in players:
        if not p.get("best_american"):
            continue
        if _safe_float(p.get("ev_pct"), -999) < min_ev:
            continue
        if _safe_float(p.get("edge_pct"), -999) < min_edge:
            continue
        if _safe_float(p.get("confidence"), 0) < min_confidence:
            continue
        if _safe_float(p.get("expected_pa"), 0) < config.MIN_PA_THRESHOLD:
            continue
        if _safe_float(p.get("park_factor"), 1.0) < config.MAX_PARK_PENALTY:
            continue
        if _safe_float(p.get("weather_factor"), 1.0) < config.MAX_WEATHER_PENALTY:
            continue
        if _safe_float(p.get("pitcher_factor"), 1.0) < config.MAX_PITCHER_SUPPRESSOR:
            continue
        # Time gate: skip players whose game starts before the ET cutoff.
        # Comparison done in ET to avoid midnight-UTC rollover for late games.
        if cutoff_utc_hour is not None:
            gt_et = _game_time_et(p.get("game_time_utc", ""))
            if gt_et is not None:
                cutoff_et_hour = (cutoff_utc_hour - 4) % 24
                if gt_et.hour < cutoff_et_hour:
                    continue
        result.append(p)
    return _rank_picks(result)


def _apply_tactical_filters(players: list, tac: dict) -> list:
    """Post-sidebar filter: narrow player pool by batter-profile and contact shape thresholds.

    These filters control visibility only — they do not rerank or rescore players.
    """
    import datetime as _dti

    def _num(v, d=0.0):
        f = _pf(v, d)
        return f if np.isfinite(f) else d

    min_barrel    = tac.get("min_barrel",    0.0)
    min_hh        = tac.get("min_hh",        0.0)
    min_xslg      = tac.get("min_xslg",      0.0)
    min_iso       = tac.get("min_iso",        0.0)
    min_pull_air  = tac.get("min_pull_air",   0.0)
    min_hr_win    = tac.get("min_hr_window",  0.0)
    min_ev        = tac.get("min_ev",         0.0)
    min_edge      = tac.get("min_edge",       0.0)
    min_conf      = tac.get("min_conf",       0.0)
    min_model_prob= tac.get("min_model_prob", 0.0)
    excl_started  = tac.get("exclude_started", False)
    incl_live     = tac.get("include_live",    False)

    _now_utc = _dti.datetime.now(_dti.timezone.utc) if excl_started else None

    result = []
    for p in players:
        if _num(p.get("barrel_pct"))        < min_barrel:    continue
        if _num(p.get("hard_hit"))          < min_hh:        continue
        _xslg = _num(p.get("xslg")) or _num(p.get("actual_slg"))
        if _xslg                           < min_xslg:      continue
        if _num(p.get("xiso"))              < min_iso:       continue
        _pull_air = resolve_pull_air_pct(p)
        if _pull_air                       < min_pull_air:  continue
        if _num(p.get("sweet_spot_pct"))    < min_hr_win:    continue
        if _num(p.get("ev_pct"),   -999)   < min_ev:        continue
        if _num(p.get("edge_pct"), -999)   < min_edge:      continue
        if _num(p.get("confidence"), 0)    < min_conf:      continue
        if _num(p.get("model_prob"), 0) * 100 < min_model_prob: continue
        if excl_started and _now_utc is not None:
            _gt = p.get("game_time_utc", "")
            if _gt:
                try:
                    _gdt = _dti.datetime.fromisoformat(_gt.replace("Z", "+00:00"))
                    if _gdt <= _now_utc and not incl_live:
                        continue
                except (ValueError, TypeError):
                    pass
        result.append(p)
    return result


@st.cache_data(ttl=120, show_spinner=False)
def _build_rqt_rows(
    player_fp: tuple,
    scale: float,
    steam_frozenset: frozenset,
    pitcher_changes_items: tuple,
    _ranked: list,
    _pitcher_changes: dict,
):
    """Build row dicts and range stats for _render_qualified_table. Cached by player fingerprint."""
    import math

    def _safe(v, default="--"):
        if v is None:
            return default
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return default
        return v

    def _rng(vals, fmt=".1f", suffix="", sign=False):
        clean = [v for v in vals if v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))]
        if not clean:
            return "N/A"
        lo, hi = min(clean), max(clean)
        pfx = "+" if sign else ""
        return f"{lo:{pfx+fmt}}{suffix} → {hi:{pfx+fmt}}{suffix}"

    rows = []
    for p in _ranked:
        ev       = p.get("ev_pct", 0)
        edge     = p.get("edge_pct", 0)
        model_p  = p.get("model_prob", 0)
        conf     = p.get("confidence", 0)
        pit_fac  = p.get("pitcher_factor", 1.0)
        plat_fac = p.get("platoon_factor", 1.0)
        spot     = p.get("lineup_spot")
        bet      = p.get("bet_dollars", 0) * scale
        name     = p.get("player_name", "")
        team     = p.get("team", "")
        is_steam = name in steam_frozenset
        pc       = _pitcher_changes.get(team)
        pitcher_cell = (
            f"⚠️ NOW: {pc['new']}" if pc
            else _pitcher_label(p.get("pitcher_name", "TBD"), pit_fac, plat_fac)
        )
        _tier     = p.get("confidence_tier", "C")
        _tier_lbl = {"S": "🌟 S", "A": "✅ A", "B": "🟡 B", "C": "🔴 C"}.get(_tier, _tier)
        rows.append({
            "Tier":    _tier_lbl,
            "Rating":  ("📈 " if is_steam else "") + _pick_rating(ev, edge, model_p, conf),
            "#":       str(p.get("rank", "")),
            "Player":  name,
            "Team":    team,
            "Opp":     p.get("opponent", ""),
            "Spot":    _spot_label(spot, plat_fac),
            "Pitcher": pitcher_cell,
            "Odds":    _fmt_american(p.get("best_american")),
            "Model%":  f"{model_p*100:.1f}%",
            "Mkt%":    f"{p.get('market_no_vig_prob',0)*100:.1f}%",
            "Edge":    f"{edge:+.1f}%",
            "EV%":     f"{ev:+.1f}%",
            "Bet $":   f"${bet:.0f}",
            "Conf":    f"{conf:.0f}",
            "Brl%":    str(_safe(p.get("barrel_pct"), "--")),
            "SwSp%":   str(_safe(p.get("sweet_spot_pct"), "--")),
            "EV mph":  str(_safe(p.get("exit_velo"), "--")),
            "FB%":     str(_safe(p.get("fb_pct"), "--")),
            "GB%":     str(_safe(p.get("gb_pct"), "--")),
            "Pull%":   str(_safe(p.get("pull_pct"), "--")),
            "Score":   f"{p.get('score',0):.1f}",
        })

    evs    = [p.get("ev_pct", 0) for p in _ranked]
    edges  = [p.get("edge_pct", 0) for p in _ranked]
    models = [p.get("model_prob", 0) * 100 for p in _ranked]
    mkts   = [p.get("market_no_vig_prob", 0) * 100 for p in _ranked]
    bets   = [p.get("bet_dollars", 0) * scale for p in _ranked]
    confs  = [p.get("confidence", 0) for p in _ranked]
    scores = [p.get("score", 0) for p in _ranked]

    model_rng = _rng(models, suffix="%")
    mkt_rng   = _rng(mkts, suffix="%")
    edge_rng  = _rng(edges, sign=True, suffix="%")
    ev_rng    = _rng(evs, sign=True, suffix="%")
    bet_rng   = f"${min(bets):.0f} → ${max(bets):.0f}" if bets else "N/A"
    conf_rng  = _rng(confs, fmt=".0f")
    score_rng = _rng(scores, fmt=".1f")

    range_items = [
        ("Model%", model_rng),
        ("Mkt%",   mkt_rng),
        ("Edge",   edge_rng),
        ("EV%",    ev_rng),
        ("Bet $",  bet_rng),
        ("Conf",   conf_rng),
    ]
    return rows, range_items, model_rng, mkt_rng, edge_rng, ev_rng, bet_rng, conf_rng, score_rng


def _render_qualified_table(
    ranked: list, scale: float, min_ev: float, min_edge: float,
    steam_names: set = None, key_suffix: str = "",
):
    """Render the qualified picks dataframe with range bar, legend, and column configs."""
    import io

    _pitcher_changes = st.session_state.get("pitcher_changes", {})
    _pc_items = tuple(sorted(_pitcher_changes.items())) if _pitcher_changes else ()
    _steam_fs = frozenset(steam_names or [])
    _player_fp = tuple(
        (p.get("player_name", ""), p.get("model_prob", 0), p.get("ev_pct", 0), p.get("rank", 0))
        for p in ranked
    )
    rows, range_items, model_rng, mkt_rng, edge_rng, ev_rng, bet_rng, conf_rng, score_rng = (
        _build_rqt_rows(_player_fp, scale, _steam_fs, _pc_items, ranked, _pitcher_changes)
    )
    range_html = "".join(
        f"<span style='white-space:nowrap'>"
        f"<span style='color:#888888'>{k}:</span> "
        f"<span style='color:#f0f0f0; font-weight:600'>{v}</span>"
        f"</span>"
        for k, v in range_items
    )
    st.markdown(
        f"<div class='range-bar'>📊 Ranges &nbsp;— &nbsp;{range_html}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='font-size:11px; color:#888888; margin-bottom:8px;'>"
        "<b style='color:#f0f0f0'>Pitcher:</b> "
        "🔴 Elite suppressor &nbsp; 🟠 Tough &nbsp; ⬜ Neutral &nbsp; 🟡 Favorable &nbsp; 🟢 HR target &nbsp; ⚡ Platoon edge"
        "&nbsp;&nbsp;&nbsp;<b style='color:#f0f0f0'>Spot:</b> "
        "🟢 Premium (1-4) &nbsp; 🟡 Mid (5-6) &nbsp; 🔴 Bottom (7-9)"
        "</div>",
        unsafe_allow_html=True,
    )

    session_br = st.session_state.get("bankroll_override", config.BANKROLL)

    df = pd.DataFrame(rows)
    df = df.fillna("--")
    df = df.replace([np.nan, np.inf, -np.inf, float('inf'), -float('inf')], "--")
    df = _apply_heatmap(df)

    _tver = st.session_state.get("_table_ver", 0)
    _df_sel = st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"picks_df_{key_suffix}_{_tver}",
        column_config={
            "Tier":    st.column_config.TextColumn("Tier",
                help=(
                    "Confidence tier — requires BOTH confidence AND edge to clear the bar.\n\n"
                    "🌟 S — Conf ≥70 AND Edge ≥8%: Elite. Act with conviction.\n"
                    "✅ A — Conf ≥55 AND Edge ≥5%: Strong. Core betting targets.\n"
                    "🟡 B — Conf ≥40 AND Edge ≥3%: Solid. Worth standard size.\n"
                    "🔴 C — Below B thresholds: Noisy or thin. Reduce size or skip."
                )),
            "Rating":  st.column_config.TextColumn("Rating",
                help=(
                    "Pick quality tier based on EV%, Edge%, and model Confidence.\n\n"
                    "🌟 ONCE IN A LIFETIME — EV ≥30% + Edge ≥12% + Conf ≥65. "
                    "Rare: the model sees a large, confident mispricing vs the market. "
                    "Expect 1–3 per day at most.\n\n"
                    "🔥 STRONG EDGE — EV ≥18% + Edge ≥7% + Conf ≥50. "
                    "Clear disagreement between model and market with solid confidence. "
                    "Core betting targets most days.\n\n"
                    "✅ SOLID PLAY — EV ≥5% + Edge ≥2%. "
                    "Positive expected value with a real model edge — worth playing "
                    "at reasonable stakes. The bulk of qualified picks land here.\n\n"
                    "📊 MARGINAL — Passes filters but edge or EV is thin. "
                    "Skip unless odds improve or you have strong conviction."
                )),
            "#":       st.column_config.TextColumn("#",
                help="Composite rank: tier first (S→A→B→C), then confidence-weighted score"),
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
                help=f"Expected value per $100 wagered. Active threshold +{min_ev:.1f}%.\nRange: {ev_rng}"),
            "Bet $":   st.column_config.TextColumn("Bet $",
                help=f"Quarter-Kelly sizing on ${session_br:,.0f} bankroll (5% cap = ${session_br*config.MAX_BET_PCT:.0f} max).\nRange: {bet_rng}"),
            "Conf":    st.column_config.TextColumn("Conf",
                help=f"Confidence 0–100: sample size + Statcast availability + model/market agreement.\nRange: {conf_rng}"),
            "Brl%":    st.column_config.TextColumn("Brl%",
                help="Statcast barrel rate. League avg ~5.5%. Higher = more true HR power."),
            "SwSp%":   st.column_config.TextColumn("SwSp%",
                help="Sweet spot rate (LA 8-32°). League avg ~33%. The exact HR angle band."),
            "EV mph":  st.column_config.TextColumn("EV mph",
                help="Average exit velocity. League avg ~89 mph."),
            "FB%":     st.column_config.TextColumn("FB%",
                help="Fly ball rate (Savant pure FB, excludes popups). League avg ~26.5%. Higher = more HR opportunities."),
            "GB%":     st.column_config.TextColumn("GB%",
                help="Ground ball rate. League avg ~43%. Higher = fewer HR chances."),

            "Pull%":   st.column_config.TextColumn("Pull%",
                help="Pull rate. League avg ~40%. Pull hitters access the short porch."),
            "Score":   st.column_config.TextColumn("Score",
                help=f"Ranking score = 40% EV% + 35% Edge% + 25% Conf.\nRange: {score_rng}"),
        },
    )

    # Open player modal on row click; bump table version so selection resets after modal
    _sel_rows = getattr(getattr(_df_sel, "selection", None), "rows", [])
    if _sel_rows and 0 <= _sel_rows[0] < len(ranked):
        st.session_state["_table_ver"] = _tver + 1
        st.session_state["show_modal"] = ranked[_sel_rows[0]]
        st.session_state["modal_source_tab"] = "Picks Table"
        st.session_state["modal_source_section"] = key_suffix or "Picks Table"
        st.rerun()
    st.caption("💡 Click any row to view full player details & add to FD Slip.")

    if rows:
        csv_buf = io.StringIO()
        import csv as _csv
        writer = _csv.DictWriter(csv_buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        st.download_button(
            label="⬇️ Export CSV",
            data=csv_buf.getvalue(),
            file_name=f"picks_{_dt.date.today().isoformat()}{('_' + key_suffix) if key_suffix else ''}.csv",
            mime="text/csv",
            key=f"dl_csv_{key_suffix or 'default'}",
        )


def _render_pitch_mix_expander(ctx: dict, p: dict, key_prefix: str, expanded: bool = False,
                               slate_ts: str = "") -> None:
    """Shared pitch mix expander — lazy-loaded to reduce render pressure on long slates."""
    if not ctx:
        return

    # Lazy load gate: collapsed sections only render a cheap 2-widget placeholder.
    # Full analysis (3 HTML tables, multiple loops) only builds after the user clicks Load.
    # State anchored to slate_ts so a new date/slate resets the gate (prevents stale auto-expand).
    _uid = str(p.get("player_id") or p.get("player_name", "unk"))
    _pm_loaded_key = f"_pm_loaded_{key_prefix}_{_uid}_{slate_ts}"
    _is_loaded = st.session_state.get(_pm_loaded_key, False)

    # When caller passes expanded=True (e.g. global expand-all setting), auto-mark as loaded
    # so the expander opens directly to full content rather than the lightweight placeholder.
    if expanded and not _is_loaded:
        st.session_state[_pm_loaded_key] = True
        _is_loaded = True

    with st.expander("📊 Pitch Mix Analysis", expanded=expanded or _is_loaded):
        if not _is_loaded:
            # Lightweight placeholder — no HTML tables or loops execute here
            _prev_pit = p.get("pitcher_name", "TBD")
            _prev_n   = len((ctx.get("pitch_mix") or {}).get("arsenal", []))
            st.markdown(
                f"<div style='color:#64748b;font-size:11px;padding:2px 0;'>"
                f"vs {_prev_pit} &nbsp;·&nbsp; {_prev_n} pitch types tracked</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "▶ Load Full Analysis",
                key=f"pm_load_{key_prefix}_{_uid}_{slate_ts}",
                use_container_width=True,
            ):
                st.session_state[_pm_loaded_key] = True
                st.rerun()
            return

        # ── Full pitch mix analysis (only builds after Load is clicked) ────────
        from clients.pitch_mix import pitch_label, pitch_color
        import config as _cfg

        name        = p.get("player_name", "Unknown")
        pit_n       = p.get("pitcher_name", "TBD")
        pit_hand    = p.get("pitcher_hand", "")
        bat_side    = p.get("batter_side", "")
        pit_hand_lbl = (f" ({'RHP' if pit_hand == 'R' else 'LHP' if pit_hand == 'L' else ''})"
                        if pit_hand else "")
        bat_side_lbl = (f" ({'RHB' if bat_side == 'R' else 'LHB' if bat_side == 'L' else ''})"
                        if bat_side else "")

        pitch_mix       = ctx.get("pitch_mix", {})
        pitcher_arsenal = pitch_mix.get("arsenal", ctx.get("pitcher_arsenal", []))
        hand_splits     = pitch_mix.get("hand_splits", ctx.get("hand_splits", {}))
        h2h             = pitch_mix.get("h2h", ctx.get("h2h", {}))
        batter_rows     = pitch_mix.get("batter_rows", ctx.get("batter_rows", []))
        _data_year      = pitch_mix.get("data_year", ctx.get("data_year", _cfg.CURRENT_SEASON))
        _yr_label       = (f" ({_data_year})" if _data_year != _cfg.CURRENT_SEASON
                           else f" ({_cfg.CURRENT_SEASON})")
        _prior_note     = (f" ⚠️ *{_data_year} data — pitcher has no {_cfg.CURRENT_SEASON} starts yet*"
                           if _data_year != _cfg.CURRENT_SEASON else "")

        pitches = []

        if _prior_note:
            st.caption(_prior_note)

        st.markdown(
            "<div style='display:flex;gap:12px;font-size:10px;margin-bottom:8px;"
            "background:#0f172a;border-radius:4px;padding:5px 8px;'>"
            "<span><b style='color:#4ade80;'>■</b> Green = Batter-Favoring</span>"
            "<span><b style='color:#f87171;'>■</b> Red = Pitcher-Favoring</span>"
            "<span><b style='color:#facc15;'>■</b> Yellow = Neutral</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        # ── Arsenal table ──────────────────────────────────────────────────────
        _ars_bat_side = bat_side
        if bat_side == "S":
            _ars_bat_side = "R" if pit_hand == "L" else "L"
        _ars_vs_lbl = (f" vs {'RHB' if _ars_bat_side == 'R' else 'LHB'}"
                       if _ars_bat_side in ("R", "L") else "")
        st.markdown(f"**🔥 {pit_n}{pit_hand_lbl} Arsenal{_ars_vs_lbl}{_yr_label}**")

        if pitcher_arsenal:
            pitches = sorted(pitcher_arsenal, key=lambda x: x.get("pitch_pct", 0), reverse=True)[:6]
            _LG_WHIFF = 0.245
            _th  = ("background:#0f172a;color:#64748b;font-size:10px;"
                    "padding:4px 6px;text-align:center;border-bottom:1px solid #1e293b;")
            _th_l = _th + "text-align:left;"
            _td  = "padding:4px 6px;text-align:center;font-size:11px;"
            rows = ""
            for px in pitches:
                pt      = px.get("pitch_type", "")
                lbl     = pitch_label(pt)
                use_v   = px.get("pitch_pct", 0) * 100
                use     = f"{use_v:.0f}%"
                spd     = f"{px.get('avg_speed'):.1f}" if px.get("avg_speed") else "—"
                k_v     = px.get("k_pct")
                hr_v    = px.get("hr_rate")
                kp_s    = f"{k_v*100:.0f}%" if k_v is not None else "—"
                hrp_s   = f"{hr_v*100:.1f}%" if hr_v is not None else "—"
                whf_v   = px.get("display_whiff")
                hh_v    = px.get("display_hh")
                rv      = px.get("display_rv100")
                whf     = f"{whf_v*100:.0f}%" if whf_v is not None else "—"
                hh_p    = f"{hh_v*100:.0f}%" if hh_v is not None else "—"
                rv_s    = f"{rv:+.1f}" if rv is not None else "—"
                p_ba_v  = px.get("pitch_ba")
                p_slg_v = px.get("pitch_slg")
                p_ba_s  = f"{p_ba_v:.3f}" if p_ba_v is not None else "—"
                p_slg_s = f"{p_slg_v:.3f}" if p_slg_v is not None else "—"
                _fav = 0.0
                if whf_v is not None: _fav -= (whf_v - _LG_WHIFF) * 3.0
                if rv    is not None: _fav += rv / 4.0
                if hh_v  is not None: _fav += (hh_v - 0.38) * 2.0
                if whf_v is None and rv is None and hh_v is None:
                    kp_raw = px.get("k_pct") or 0
                    _fav = -((kp_raw - 0.22) * 2.0)
                pc     = ("#4ade80" if _fav >= 0.15 else "#f87171" if _fav <= -0.15 else "#facc15")
                use_bg = ("#14532d" if use_v >= 35 else "#166534" if use_v >= 20 else "#0f172a")
                k_bg   = ("#7f1d1d" if (k_v or 0) >= 0.28 else "#450a0a" if (k_v or 0) >= 0.22
                          else "#166534" if k_v is not None and k_v < 0.15 else "#0f172a")
                hr_bg  = ("#14532d" if (hr_v or 0) >= 0.04 else "#166534" if (hr_v or 0) >= 0.03
                          else "#7f1d1d" if hr_v is not None and (hr_v or 0) < 0.015 else "#0f172a")
                whf_bg = ("#7f1d1d" if (whf_v or 0) >= 0.30 else "#450a0a" if (whf_v or 0) >= 0.22
                          else "#166534" if (whf_v or 0) < 0.15 and whf_v is not None else "#0f172a")
                hh_bg  = ("#14532d" if (hh_v or 0) >= 0.50 else "#166534" if (hh_v or 0) >= 0.42
                          else "#7f1d1d" if (hh_v or 0) < 0.34 and hh_v is not None else "#0f172a")
                rv_bg  = ("#7f1d1d" if (rv or 0) < -1.0 else "#450a0a" if (rv or 0) < 0
                          else "#14532d" if (rv or 0) > 2.5 else "#166534" if (rv or 0) > 1.0 else "#0f172a")
                ba_bg  = ("#14532d" if (p_ba_v or 0) >= 0.310 else "#166534" if (p_ba_v or 0) >= 0.270
                          else "#7f1d1d" if p_ba_v is not None and (p_ba_v or 0) < 0.220 else "#0f172a")
                slg_bg = ("#14532d" if (p_slg_v or 0) >= 0.500 else "#166534" if (p_slg_v or 0) >= 0.420
                          else "#7f1d1d" if p_slg_v is not None and (p_slg_v or 0) < 0.320 else "#0f172a")
                rows += (
                    f"<tr>"
                    f"<td style='padding:4px 6px;'><b style='color:{pc};font-size:11px;'>{lbl}</b></td>"
                    f"<td style='background:{use_bg};color:#e2e8f0;{_td}'>{use}</td>"
                    f"<td style='background:#0f172a;color:#94a3b8;{_td}'>{spd}</td>"
                    f"<td style='background:{k_bg};color:#e2e8f0;{_td}'>{kp_s}</td>"
                    f"<td style='background:{hr_bg};color:#e2e8f0;{_td}'>{hrp_s}</td>"
                    f"<td style='background:{ba_bg};color:#e2e8f0;{_td}'>{p_ba_s}</td>"
                    f"<td style='background:{slg_bg};color:#e2e8f0;{_td}'>{p_slg_s}</td>"
                    f"<td style='background:{whf_bg};color:#e2e8f0;{_td}'>{whf}</td>"
                    f"<td style='background:{hh_bg};color:#e2e8f0;{_td}'>{hh_p}</td>"
                    f"<td style='background:{rv_bg};color:#e2e8f0;{_td}'>{rv_s}</td>"
                    f"</tr>"
                )
            st.markdown(
                "<table style='width:100%;border-collapse:collapse;background:#0f172a;"
                "border-radius:6px;overflow:hidden;'>"
                "<thead><tr style='background:#0f172a;'>"
                f"<th colspan='3' style='background:#0f172a;padding:2px 6px;border-bottom:0;'></th>"
                f"<th colspan='7' style='background:#0a1628;color:#60a5fa;font-size:9px;"
                f"letter-spacing:1px;font-weight:700;padding:3px 6px;text-align:center;"
                f"border-top:2px solid #2563eb;border-bottom:0;'>── PITCHER ALLOWED ──</th>"
                "</tr><tr>"
                f"<th style='{_th_l}'>Pitch</th>"
                f"<th style='{_th}'>Use%</th>"
                f"<th style='{_th}'>MPH</th>"
                f"<th style='{_th}border-left:1px solid #1e3a5f;'>K%</th>"
                f"<th style='{_th}'>HR%</th>"
                f"<th style='{_th}'>BA</th>"
                f"<th style='{_th}'>SLG</th>"
                f"<th style='{_th}'>Whiff%</th>"
                f"<th style='{_th}'>HH%</th>"
                f"<th style='{_th}'>RV/100</th>"
                "</tr></thead>"
                f"<tbody>{rows}</tbody></table>"
                "<div style='font-size:10px;color:#4b5563;margin-top:4px;'>"
                "Pitch: 🟢 batter-favoring · 🔴 pitcher-favoring · 🟡 neutral"
                " &nbsp;|&nbsp; K%/Whiff%: 🔴=high strikeout risk · BA/SLG/HH%: 🟢=hitter-friendly · RV/100: 🟢=positive value</div>",
                unsafe_allow_html=True,
            )

            # ── Matchup outlook bar ────────────────────────────────────────────
            _mod = ctx.get("hvy_modifier", 1.0)
            if _mod >= 1.20:
                _mi_lbl, _mi_c, _mi_icon = "Strong Batter Advantage", "#4ade80", "🟢"
            elif _mod >= 1.08:
                _mi_lbl, _mi_c, _mi_icon = "Batter Edge", "#86efac", "🟢"
            elif _mod >= 1.03:
                _mi_lbl, _mi_c, _mi_icon = "Slight Batter Edge", "#facc15", "🟡"
            elif _mod >= 0.97:
                _mi_lbl, _mi_c, _mi_icon = "Even Matchup", "#94a3b8", "⬜"
            elif _mod >= 0.92:
                _mi_lbl, _mi_c, _mi_icon = "Slight Pitcher Edge", "#fb923c", "🟠"
            elif _mod >= 0.85:
                _mi_lbl, _mi_c, _mi_icon = "Pitcher Edge", "#f87171", "🔴"
            else:
                _mi_lbl, _mi_c, _mi_icon = "Strong Pitcher Advantage", "#ef4444", "🔴"
            _bar_pct = min(100, max(0, int((_mod - 0.75) / 0.60 * 100)))
            _lbl_pos = max(8, min(88, _bar_pct))
            st.markdown(
                f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:6px;"
                f"padding:8px 12px;margin-top:8px;margin-bottom:8px;'>"
                f"<div style='display:flex;justify-content:space-between;font-size:11px;margin-bottom:5px;'>"
                f"<span style='color:#64748b;'>⚔️ Matchup Outlook</span>"
                f"<span style='color:{_mi_c};font-weight:700;'>{_mi_icon} {_mi_lbl}</span>"
                f"<span style='color:#64748b;font-size:10px;'>Modifier: {_mod:.2f}×</span>"
                f"</div>"
                f"<div style='position:relative;background:#1e293b;border-radius:4px;height:18px;'>"
                f"<div style='background:{_mi_c};width:{_bar_pct}%;height:18px;border-radius:4px;'></div>"
                f"<span style='position:absolute;top:0;left:{_lbl_pos}%;transform:translateX(-50%);"
                f"font-size:10px;font-weight:700;color:#0f172a;line-height:18px;white-space:nowrap;'>"
                f"{_bar_pct}%</span></div>"
                f"<div style='display:flex;justify-content:space-between;font-size:9px;"
                f"color:#374151;margin-top:3px;'>"
                f"<span>◀ Pitcher</span><span>Even (50%)</span><span>Batter ▶</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("No Savant arsenal data for this pitcher.")

        # ── Batter vs Pitch Types ──────────────────────────────────────────────
        _bvp_hand_lbl = (f" vs {'LHP' if pit_hand == 'L' else 'RHP'}" if pit_hand else "")
        st.markdown(f"**🎯 {name}{_bvp_hand_lbl} ({_cfg.CURRENT_SEASON})**")

        if batter_rows:
            _th2   = ("background:#0f172a;color:#64748b;font-size:10px;"
                      "padding:4px 6px;text-align:center;border-bottom:1px solid #1e293b;")
            _th2_l = _th2 + "text-align:left;"
            _td2   = "padding:4px 6px;text-align:center;font-size:11px;"

            _show_all_k = f"pm_showall_{key_prefix}_{p.get('player_id', '')}"
            _show_all   = st.session_state.get(_show_all_k, False)
            _active_bvp = batter_rows if _show_all else batter_rows[:5]

            brows = ""
            for bpt in _active_bvp:
                pt = bpt.get("pitch_type", "")
                lbl = pitch_label(pt)
                bpa = bpt.get("pa")
                if (bpa or 0) < 3:
                    pc = pitch_color(pt)
                    brows += (
                        f"<tr><td style='padding:4px 6px;'>"
                        f"<b style='color:{pc};font-size:11px;'>{lbl}</b></td>"
                        f"<td colspan='7' style='color:#374151;font-size:10px;"
                        f"text-align:center;{_td2}'>< 3 PA</td></tr>"
                    )
                    continue
                bslg   = bpt.get("slg")   # None when < 3 AB
                bba    = bpt.get("ba")    # None when < 3 AB
                biso   = bpt.get("iso")   # None when ba or slg is None
                bkpct  = bpt.get("k_pct") or 0.0
                bhr    = bpt.get("hr", 0)
                bpa    = bpa or 0
                bhrpct = bpt.get("hr_rate")  # None when < 10 PA
                # Use neutral value for colour-score when data is absent
                _b_slg = bslg if bslg is not None else 0.380
                _b_fav = (_b_slg - 0.380) * 2.0 - (bkpct - 0.22) * 1.5 + (bhr * 0.08)
                pc     = ("#4ade80" if _b_fav >= 0.15 else "#f87171" if _b_fav <= -0.15 else "#facc15")
                slg_bg = ("#14532d" if (bslg or 0) >= 0.550 else "#166534" if (bslg or 0) >= 0.450
                          else "#7f1d1d" if bslg is not None and (bslg or 0) < 0.280
                          else "#450a0a" if bslg is not None and (bslg or 0) < 0.200 else "#0f172a")
                ba_bg  = ("#14532d" if (bba or 0) >= 0.350 else "#166534" if (bba or 0) >= 0.280
                          else "#7f1d1d" if bba is not None and (bba or 0) < 0.200 else "#0f172a")
                iso_bg = ("#14532d" if (biso or 0) >= 0.250 else "#166534" if (biso or 0) >= 0.175
                          else "#7f1d1d" if biso is not None and (biso or 0) < 0.080 else "#0f172a")
                k_bg   = ("#7f1d1d" if bkpct >= 0.35 else "#450a0a" if bkpct >= 0.45
                          else "#166534" if bkpct < 0.18 else "#0f172a")
                hr_bg  = "#14532d" if bhr >= 2 else "#166534" if bhr >= 1 else "#0f172a"
                hrp_bg = ("#14532d" if (bhrpct or 0) >= 0.05 else "#166534" if (bhrpct or 0) >= 0.03
                          else "#7f1d1d" if bhrpct is not None and (bhrpct or 0) < 0.01 and bpa >= 10
                          else "#0f172a")
                # Format display strings — "—" when stat is absent due to small sample
                _bba_s  = f"{bba:.3f}"         if bba    is not None else "—"
                _bslg_s = f"{bslg:.3f}"        if bslg   is not None else "—"
                _biso_s = f"{biso:.3f}"        if biso   is not None else "—"
                _bhrp_s = f"{bhrpct*100:.1f}%" if bhrpct is not None else "—"
                brows += (
                    f"<tr>"
                    f"<td style='padding:4px 6px;'><b style='color:{pc};font-size:11px;'>{lbl}</b></td>"
                    f"<td style='background:#0f172a;color:#94a3b8;{_td2}'>{bpa}</td>"
                    f"<td style='background:{hr_bg};color:#e2e8f0;{_td2}'>{bhr}</td>"
                    f"<td style='background:{hrp_bg};color:#e2e8f0;{_td2}'>{_bhrp_s}</td>"
                    f"<td style='background:{ba_bg};color:#e2e8f0;{_td2}'>{_bba_s}</td>"
                    f"<td style='background:{slg_bg};color:#e2e8f0;{_td2}'>{_bslg_s}</td>"
                    f"<td style='background:{iso_bg};color:#e2e8f0;{_td2}'>{_biso_s}</td>"
                    f"<td style='background:{k_bg};color:#e2e8f0;{_td2}'>{bkpct*100:.0f}%</td>"
                    f"</tr>"
                )
            if brows:
                _bvp_note = "" if pitches else " (all types)"
                st.markdown(
                    "<table style='width:100%;border-collapse:collapse;background:#0f172a;"
                    "border-radius:6px;overflow:hidden;margin-top:4px;'>"
                    "<thead><tr style='background:#0f172a;'>"
                    f"<th colspan='2' style='background:#0f172a;padding:2px 6px;border-bottom:0;'></th>"
                    f"<th colspan='6' style='background:#0a1f0a;color:#4ade80;font-size:9px;"
                    f"letter-spacing:1px;font-weight:700;padding:3px 6px;text-align:center;"
                    f"border-top:2px solid #14532d;border-bottom:0;'>── RESULTS ──</th>"
                    "</tr><tr>"
                    f"<th style='{_th2_l}'>Pitch{_bvp_note}</th>"
                    f"<th style='{_th2}'>PA</th>"
                    f"<th style='{_th2}border-left:1px solid #14532d;'>HR</th>"
                    f"<th style='{_th2}'>HR%</th>"
                    f"<th style='{_th2}'>BA</th>"
                    f"<th style='{_th2}'>SLG</th>"
                    f"<th style='{_th2}'>ISO</th>"
                    f"<th style='{_th2}'>K%</th>"
                    "</tr></thead>"
                    f"<tbody>{brows}</tbody></table>"
                    "<div style='font-size:10px;color:#4b5563;margin-top:4px;'>"
                    "Pitch: 🟢=batter-favoring · 🔴=pitcher-favoring"
                    " &nbsp;|&nbsp; ISO=SLG−BA (power index) · HR%=HR per PA</div>",
                    unsafe_allow_html=True,
                )
                _sa_lbl = "▲ Fewer Pitches" if _show_all else "▼ Show All Pitches"
                if st.button(_sa_lbl, key=f"{key_prefix}_pm_sa_{p.get('player_id', '')}",
                             use_container_width=False):
                    st.session_state[_show_all_k] = not _show_all
                    st.rerun()
            else:
                st.caption("Batter has < 3 PA vs any pitch type this season.")
        else:
            st.caption("No batter split data available.")

        # ── Pitcher Splits + H2H ──────────────────────────────────────────────
        st.divider()
        _cs1, _cs2 = st.columns(2)

        with _cs1:
            st.markdown(f"**📈 {pit_n}{pit_hand_lbl} Splits{_yr_label}**")

            if pitcher_arsenal:
                _agg_tot = sum(px.get("pitch_pct", 0) for px in pitcher_arsenal)
                if _agg_tot > 0:
                    _agg_whiff = sum(
                        (px.get("display_whiff") or 0) * px.get("pitch_pct", 0)
                        for px in pitcher_arsenal if px.get("display_whiff") is not None
                    )
                    _agg_hh = sum(
                        (px.get("display_hh") or 0) * px.get("pitch_pct", 0)
                        for px in pitcher_arsenal if px.get("display_hh") is not None
                    )
                    _agg_rv = sum(
                        (px.get("display_rv100") or 0) * px.get("pitch_pct", 0)
                        for px in pitcher_arsenal if px.get("display_rv100") is not None
                    )
                    _wt_tot_w = sum(px.get("pitch_pct", 0) for px in pitcher_arsenal if px.get("display_whiff") is not None)
                    _wt_tot_h = sum(px.get("pitch_pct", 0) for px in pitcher_arsenal if px.get("display_hh") is not None)
                    _wt_tot_r = sum(px.get("pitch_pct", 0) for px in pitcher_arsenal if px.get("display_rv100") is not None)
                    _avg_w = (_agg_whiff / _wt_tot_w) if _wt_tot_w > 0 else None
                    _avg_h = (_agg_hh    / _wt_tot_h) if _wt_tot_h > 0 else None
                    _avg_r = (_agg_rv    / _wt_tot_r) if _wt_tot_r > 0 else None

                    def _pill_color(col, val):
                        if col == "whiff" and val is not None:
                            return "#f87171" if val >= 0.28 else "#4ade80" if val < 0.20 else "#facc15"
                        if col == "hh" and val is not None:
                            return "#4ade80" if val >= 0.42 else "#f87171" if val < 0.34 else "#facc15"
                        if col == "rv" and val is not None:
                            return "#4ade80" if val >= 1.0 else "#f87171" if val <= -1.0 else "#facc15"
                        return "#64748b"

                    _w_lbl = f"{_avg_w*100:.0f}%" if _avg_w is not None else "—"
                    _h_lbl = f"{_avg_h*100:.0f}%" if _avg_h is not None else "—"
                    _r_lbl = f"{_avg_r:+.1f}"    if _avg_r is not None else "—"
                    _wc = _pill_color("whiff", _avg_w)
                    _hc = _pill_color("hh",    _avg_h)
                    _rc = _pill_color("rv",     _avg_r)
                    _pill_s = ("background:#1e293b;border-radius:4px;padding:3px 8px;"
                               "text-align:center;flex:1;")
                    st.markdown(
                        f"<div style='display:flex;gap:6px;margin-bottom:6px;font-size:11px;'>"
                        f"<div style='{_pill_s}'><div style='color:#64748b;font-size:9px;'>Whiff%</div>"
                        f"<div style='color:{_wc};font-weight:700;'>{_w_lbl}</div></div>"
                        f"<div style='{_pill_s}'><div style='color:#64748b;font-size:9px;'>Hard Hit%</div>"
                        f"<div style='color:{_hc};font-weight:700;'>{_h_lbl}</div></div>"
                        f"<div style='{_pill_s}'><div style='color:#64748b;font-size:9px;'>RV/100</div>"
                        f"<div style='color:{_rc};font-weight:700;'>{_r_lbl}</div></div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            _this_hand = "L" if bat_side == "L" else "R"
            _sp_rows = ""
            for _hand, _lbl in [("Season", "Season"), ("R", "vs RHB"), ("L", "vs LHB")]:
                if _hand == "Season":
                    _sp_r  = hand_splits.get("R", {})
                    _sp_l  = hand_splits.get("L", {})
                    _sp_pa = _sp_r.get("pa", 0) + _sp_l.get("pa", 0)
                    _sp_hr = _sp_r.get("hr", 0) + _sp_l.get("hr", 0)
                    if _sp_pa == 0:
                        continue
                    _sp_slg = ((_sp_r.get("slg", 0) * _sp_r.get("pa", 0)) +
                               (_sp_l.get("slg", 0) * _sp_l.get("pa", 0))) / _sp_pa
                    _sp_iso = ((_sp_r.get("iso", 0) * _sp_r.get("pa", 0)) +
                               (_sp_l.get("iso", 0) * _sp_l.get("pa", 0))) / _sp_pa
                    _sp_ba  = ((_sp_r.get("ba", 0) * _sp_r.get("pa", 0)) +
                               (_sp_l.get("ba", 0) * _sp_l.get("pa", 0))) / _sp_pa
                    _row_bg = "#1e293b"
                    _lbl_c  = "#94a3b8"
                    _badge  = ""
                else:
                    _sp    = hand_splits.get(_hand, {})
                    _sp_pa = _sp.get("pa", 0)
                    if _sp_pa == 0:
                        _sp_rows += (
                            f"<tr style='background:#111827;'>"
                            f"<td style='color:#555;padding:4px 6px;'>{_lbl}</td>"
                            f"<td colspan='6' style='color:#444;font-size:10px;padding:4px 6px;'>no data</td></tr>"
                        )
                        continue
                    _sp_hr  = _sp.get("hr", 0)
                    _sp_ba  = _sp.get("ba",  0.0)
                    _sp_slg = _sp.get("slg", 0.0)
                    _sp_iso = _sp.get("iso", 0.0)
                    _row_bg = "#1a3a2a" if _hand == _this_hand else "#111827"
                    _lbl_c  = "#fbbf24" if _hand == _this_hand else "#94a3b8"
                    _badge  = " ◀" if _hand == _this_hand else ""
                _sp_hrr = _sp_hr / max(_sp_pa, 1)
                _ba_c   = "#4ade80" if _sp_ba  >= 0.290 else "#f87171" if _sp_ba  < 0.220 else "#f0f0f0"
                _slg_c  = "#4ade80" if _sp_slg >= 0.450 else "#f87171" if _sp_slg < 0.330 else "#f0f0f0"
                _iso_c  = "#4ade80" if _sp_iso >= 0.200 else "#f87171" if _sp_iso < 0.130 else "#f0f0f0"
                _hr_c   = "#4ade80" if _sp_hrr > 0.035  else "#f87171" if _sp_hrr < 0.018 else "#f0f0f0"
                _sp_rows += (
                    f"<tr style='background:{_row_bg};'>"
                    f"<td style='color:{_lbl_c};font-weight:700;padding:4px 6px;white-space:nowrap;'>"
                    f"{_lbl}{_badge}</td>"
                    f"<td style='padding:4px 6px;text-align:center;'>{_sp_pa}</td>"
                    f"<td style='padding:4px 6px;text-align:center;color:{_hr_c};font-weight:700;'>{_sp_hr}</td>"
                    f"<td style='padding:4px 6px;text-align:center;color:{_hr_c};'>{_sp_hrr:.3f}</td>"
                    f"<td style='padding:4px 6px;text-align:center;color:{_ba_c};'>{_sp_ba:.3f}</td>"
                    f"<td style='padding:4px 6px;text-align:center;color:{_slg_c};font-weight:700;'>{_sp_slg:.3f}</td>"
                    f"<td style='padding:4px 6px;text-align:center;color:{_iso_c};'>{_sp_iso:.3f}</td>"
                    f"</tr>"
                )
            if _sp_rows:
                st.markdown(
                    "<table style='width:100%;font-size:11px;border-collapse:collapse;"
                    "border-radius:6px;overflow:hidden;margin-bottom:8px;'>"
                    "<tr style='background:#0f172a;color:#64748b;font-size:10px;'>"
                    "<th style='padding:4px 6px;text-align:left;'>Split</th>"
                    "<th style='padding:4px 6px;text-align:center;'>PA</th>"
                    "<th style='padding:4px 6px;text-align:center;'>HR</th>"
                    "<th style='padding:4px 6px;text-align:center;'>HR/PA</th>"
                    "<th style='padding:4px 6px;text-align:center;'>BA</th>"
                    "<th style='padding:4px 6px;text-align:center;'>SLG</th>"
                    "<th style='padding:4px 6px;text-align:center;'>ISO</th>"
                    f"</tr>{_sp_rows}</table>"
                    "<div style='font-size:9px;color:#555;margin-bottom:8px;'>"
                    "🟢 green = favorable for batter &nbsp;|&nbsp; 🔴 red = favorable for pitcher &nbsp;|&nbsp; ◀ current matchup</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption("No pitcher split data available.")

        with _cs2:
            h2h_pa   = h2h.get("pa", 0)
            _bat_lbl = f"{name}{bat_side_lbl}"
            _pit_lbl = f"{pit_n}{pit_hand_lbl}"
            st.markdown(
                f"<div style='background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;"
                f"padding:8px 12px;margin-bottom:6px;'>"
                f"<div style='font-size:12px;font-weight:800;color:#f0f0f0;margin-bottom:4px;'>"
                f"⚔️ <span style='color:#60a5fa;'>{_bat_lbl}</span>"
                f" vs <span style='color:#f87171;'>{_pit_lbl}</span>"
                f" <span style='color:#64748b;font-weight:400;font-size:10px;'>(Career)</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if h2h_pa >= 1:
                try:
                    _h2h_avg = float(str(h2h.get("avg", ".000")).replace(",", "") or 0)
                    _h2h_slg = float(str(h2h.get("slg", ".000")).replace(",", "") or 0)
                    _h2h_ops = float(str(h2h.get("ops", ".000")).replace(",", "") or 0)
                except (ValueError, TypeError):
                    _h2h_avg = _h2h_slg = _h2h_ops = 0.0
                _h2h_iso = round(max(0.0, _h2h_slg - _h2h_avg), 3)
                _h2h_hr  = h2h.get("hr", 0)
                _h2h_bb  = h2h.get("bb", 0)
                _h2h_k   = h2h.get("k",  0)
                _avg_c = "#4ade80" if _h2h_avg >= 0.300 else "#f87171" if _h2h_avg < 0.200 else "#f0f0f0"
                _slg_c = "#4ade80" if _h2h_slg >= 0.500 else "#f87171" if _h2h_slg < 0.350 else "#f0f0f0"
                _iso_c = "#4ade80" if _h2h_iso >= 0.200 else "#f87171" if _h2h_iso < 0.100 else "#f0f0f0"
                _ops_c = "#4ade80" if _h2h_ops >= 0.800 else "#f87171" if _h2h_ops < 0.600 else "#f0f0f0"
                _hr_c  = "#4ade80" if _h2h_hr >= 1 else "#888"
                _k_c   = "#f87171" if _h2h_k >= int(h2h_pa * 0.30) else "#f0f0f0"
                st.markdown(
                    f"<div style='background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;"
                    f"padding:0 12px 10px;margin-bottom:4px;'>"
                    f"<div style='display:grid;grid-template-columns:repeat(7,1fr);"
                    f"font-size:9px;color:#64748b;text-align:center;"
                    f"border-bottom:1px solid #1e293b;padding:4px 0 2px;'>"
                    f"<div>PA</div><div>HR</div><div>BB</div><div>K</div>"
                    f"<div>AVG</div><div>SLG</div><div>OPS</div></div>"
                    f"<div style='display:grid;grid-template-columns:repeat(7,1fr);"
                    f"font-size:13px;font-weight:800;text-align:center;padding:6px 0 4px;'>"
                    f"<div style='color:#f0f0f0;'>{h2h_pa}</div>"
                    f"<div style='color:{_hr_c};'>{_h2h_hr}</div>"
                    f"<div style='color:#f0f0f0;'>{_h2h_bb}</div>"
                    f"<div style='color:{_k_c};'>{_h2h_k}</div>"
                    f"<div style='color:{_avg_c};'>{h2h.get('avg','.000')}</div>"
                    f"<div style='color:{_slg_c};'>{h2h.get('slg','.000')}</div>"
                    f"<div style='color:{_ops_c};'>{h2h.get('ops','.000')}</div>"
                    f"</div>"
                    f"<div style='display:grid;grid-template-columns:repeat(7,1fr);"
                    f"font-size:9px;text-align:center;padding-bottom:2px;'>"
                    f"<div></div><div></div><div></div><div></div><div></div>"
                    f"<div style='color:{_iso_c};font-size:9px;'>ISO {_h2h_iso:.3f}</div>"
                    f"<div></div></div>"
                    f"<div style='font-size:9px;color:#555;margin-top:2px;'>"
                    f"🟢 green = batter-favorable &nbsp;|&nbsp; 🔴 red = pitcher-favorable</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if h2h_pa < 5:
                    st.caption(f"⚠️ {h2h_pa} PA career — small sample, context only")
            else:
                st.markdown(
                    "<div style='background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;"
                    "padding:8px 12px;margin-bottom:4px;'>"
                    "<div style='font-size:11px;color:#475569;text-align:center;'>No career matchup history</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )


# TAB 1 — TODAY'S PICKS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ─── Full Slate "All Players" game-organized renderer ─────────────────────────

def _render_full_slate_all_players(
    all_players: list,
    qualified_names: set,
    tac_qualified_names: set,
    steam_names: set,
    status_cache: dict,
    urgency_cache: dict,
    slate_ts: str = "",
) -> None:
    """
    True operational full slate: all playable batters organized by game.
    Phase 3A: game command modules — pitcher target zone + live conditions strip.
    Filters highlight/badge rather than remove players.
    """
    from collections import defaultdict
    from data.park_factors import PARK_FACTORS as _PF

    if not all_players:
        st.info("No players in today's slate.")
        return

    # Group by game_pk (team-pair fallback for players missing game_pk)
    games: dict = defaultdict(list)
    for p in all_players:
        gk = p.get("game_pk") or f"{p.get('team', '?')}-{p.get('opponent', '?')}"
        games[gk].append(p)

    # Sort games by start time
    def _gsk(gk):
        for p in games[gk]:
            gt = _game_time_et(p.get("game_time_utc", ""))
            if gt:
                return gt.hour * 60 + gt.minute
        return 9999

    sorted_gks = sorted(games.keys(), key=_gsk)
    _n_total_games = len(sorted_gks)

    # Summary line
    n_qual  = sum(1 for p in all_players if p.get("player_name") in qualified_names)
    n_elite = sum(1 for p in all_players if _pf(p.get("barrel_pct"), 0) >= 8.0)
    n_odds  = sum(1 for p in all_players if p.get("ev_pct") is not None)

    # Page size control — limit games rendered to reduce DOM size and mobile memory
    if _n_total_games > 10:
        _fs_game_opts = [5, 10, _n_total_games]
    elif _n_total_games > 5:
        _fs_game_opts = [5, _n_total_games]
    else:
        _fs_game_opts = [_n_total_games]
    _fs_game_limit_raw = st.session_state.get("fs_game_limit", _fs_game_opts[0])
    _fs_cols = st.columns([3, 1])
    with _fs_cols[1]:
        _fs_game_limit = st.selectbox(
            "Games",
            options=_fs_game_opts,
            index=min(_fs_game_opts.index(_fs_game_limit_raw)
                      if _fs_game_limit_raw in _fs_game_opts else 0,
                      len(_fs_game_opts) - 1),
            format_func=lambda x: "All games" if x == _n_total_games else f"{x} games",
            key="fs_game_limit",
            label_visibility="collapsed",
        )
    sorted_gks_shown = sorted_gks[:_fs_game_limit]

    with _fs_cols[0]:
        st.markdown(
            f"<div style='font-size:11px;color:#888;padding-top:5px;'>"
            f"<b style='color:#eee;'>{len(all_players)}</b> players"
            f" &nbsp;·&nbsp; <b style='color:#eee;'>{len(games)}</b> games"
            f" &nbsp;·&nbsp; <span style='color:#4ade80;'>{n_qual}</span> qualified"
            f" &nbsp;·&nbsp; <span style='color:#FFD700;'>{n_elite}</span> elite"
            f" &nbsp;·&nbsp; <span style='color:#555;'>{len(all_players)-n_odds}</span> no odds"
            f"</div>",
            unsafe_allow_html=True,
        )

    if len(sorted_gks_shown) < _n_total_games:
        st.caption(
            f"Showing {len(sorted_gks_shown)} of {_n_total_games} games — "
            "select 'All games' above to expand."
        )

    # ── Game navigation strip ────────────────────────────────────────────────
    _nav_parts = []
    for _ni, gk in enumerate(sorted_gks_shown):
        _gp  = games[gk]
        _p0n = _gp[0]
        _ht  = _p0n.get("home_team", "")
        _aw  = next(
            (p.get("team", "") for p in _gp if p.get("team") != _ht),
            _p0n.get("opponent", "?"),
        )
        _gq  = sum(1 for p in _gp if p.get("player_name") in qualified_names)
        _pk0 = float(_p0n.get("park_factor", 1.0) or 1.0)
        _nav_pk_col = "#4ade80" if _pk0 >= 1.05 else "#f87171" if _pk0 <= 0.95 else "#777"
        _nav_bg = "#0e1a0e" if _gq >= 3 else "#0e0e1a" if _gq >= 1 else "#0a0a12"
        _nav_bd = "#253a25" if _gq >= 3 else "#222240" if _gq >= 1 else "#161622"
        _dot = (
            f"<span style='color:{_nav_pk_col};font-size:8px;margin-left:3px;'>●</span>"
            if abs(_pk0 - 1.0) >= 0.03 else ""
        )
        _qtag = (
            f"<span style='color:#4ade80;font-size:8px;margin-left:3px;'>{_gq}Q</span>"
            if _gq > 0 else ""
        )
        _nav_parts.append(
            f"<a href='#gm{_ni}_{slate_ts}' style='display:inline-block;"
            f"background:{_nav_bg};border:1px solid {_nav_bd};border-radius:4px;"
            f"padding:2px 8px;margin:2px 2px;font-size:10px;font-weight:700;"
            f"color:#aaa;text-decoration:none;white-space:nowrap;'>"
            f"<span style='color:#60a5fa;'>{_aw}</span>"
            f"<span style='color:#444;'>@</span>"
            f"<span style='color:#dde;'>{_ht}</span>"
            f"{_dot}{_qtag}"
            f"</a>"
        )
    if _nav_parts:
        st.markdown(
            "<div id='fs_top' style='display:flex;flex-wrap:wrap;gap:0;"
            "padding:4px 0 8px;border-bottom:1px solid #1a1a2e;margin-bottom:4px;'>"
            + "".join(_nav_parts) + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='font-size:9px;color:#333;padding:2px 4px;margin-bottom:4px;"
        "font-family:monospace;letter-spacing:0.5px;'>"
        "BRL=Barrel% &nbsp;·&nbsp; MDL=Model &nbsp;·&nbsp; "
        "EV=Expected Value &nbsp;·&nbsp; EDG=Edge &nbsp;·&nbsp; CNF=Confidence"
        "</div>",
        unsafe_allow_html=True,
    )

    def _pit_vuln(factor: float) -> tuple:
        """(label, color) for pitcher vulnerability display in Full Slate."""
        if factor >= 1.20: return "ELITE TARGET", "#4ade80"
        if factor >= 1.08: return "FAVORABLE",    "#86efac"
        if factor >= 0.92: return "NEUTRAL",       "#3a3a3a"
        if factor >= 0.80: return "TOUGH",         "#f97316"
        return "SUPPRESSOR", "#f87171"

    for _ni, gk in enumerate(sorted_gks_shown):
        game_players = sorted(
            games[gk],
            key=lambda p: (p.get("team", ""), int(p.get("lineup_spot") or 99)),
        )
        p0        = game_players[0]
        home_team = p0.get("home_team", "")

        home_batters = [p for p in game_players if p.get("team") == home_team]
        away_batters = [p for p in game_players if p.get("team") != home_team]
        away_team    = (away_batters[0].get("team", "") if away_batters
                        else p0.get("opponent", "?"))

        # home batters face the away pitcher; away batters face the home pitcher
        away_pitcher    = home_batters[0].get("pitcher_name", "TBD") if home_batters else "TBD"
        home_pitcher    = away_batters[0].get("pitcher_name", "TBD") if away_batters else "TBD"
        away_pit_factor = float(home_batters[0].get("pitcher_factor", 1.0)) if home_batters else 1.0
        home_pit_factor = float(away_batters[0].get("pitcher_factor", 1.0)) if away_batters else 1.0
        away_pit_hand   = home_batters[0].get("pitcher_hand", "") if home_batters else ""
        home_pit_hand   = away_batters[0].get("pitcher_hand", "") if away_batters else ""
        away_vuln_lbl, away_vuln_col = _pit_vuln(away_pit_factor)
        home_vuln_lbl, home_vuln_col = _pit_vuln(home_pit_factor)

        gt     = _game_time_et(p0.get("game_time_utc", ""))
        gt_str = gt.strftime("%I:%M %p ET").lstrip("0") if gt else "TBD"

        _pid0   = p0.get("player_id") or p0.get("player_name", "")
        urg_col = urgency_cache.get(_pid0, (gt_str, "#555", ""))[1]

        pk     = float(p0.get("park_factor", 1.0) or 1.0)
        wf     = float(p0.get("weather_factor", 1.0) or 1.0)
        pk_col = "#4ade80" if pk >= 1.05 else "#f87171" if pk <= 0.95 else "#888"

        # Venue name from park factors lookup
        _venue = _PF.get(home_team, {}).get("name", "")

        # HR environment score
        _, _env_col, _env_lbl = _hr_env_score(p0)

        # Live conditions strip
        _w_dict  = p0.get("weather") or {}
        _temp_f  = _w_dict.get("temp_f")
        _wind_m  = _w_dict.get("wind_mph")
        _wind_d  = _w_dict.get("wind_deg")
        _hum_pct = _w_dict.get("humidity_pct")
        _is_dome = p0.get("is_dome", False)
        _cond_parts: list = []
        if _temp_f is not None:
            _tc = "#f87171" if _temp_f < 50 else "#86efac" if _temp_f > 80 else "#888"
            _cond_parts.append(f"<span style='color:{_tc};'>{_temp_f:.0f}°F</span>")
        if _is_dome:
            _cond_parts.append("<span style='color:#475569;'>DOME</span>")
        elif _wind_m is not None and _wind_d is not None:
            _wdir  = _deg_to_compass(_wind_d)
            _wc    = "#4ade80" if wf >= 1.04 else "#f87171" if wf <= 0.96 else "#666"
            _cond_parts.append(
                f"<span style='color:{_wc};'>{_wind_m:.0f}mph {_wdir}</span>"
            )
        if _hum_pct is not None and not _is_dome:
            _hc = "#86efac" if _hum_pct > 70 else "#888"
            _cond_parts.append(f"<span style='color:{_hc};'>{_hum_pct:.0f}%RH</span>")
        _cond_parts.append(
            f"<span style='color:{_env_col};font-weight:700;"
            f"letter-spacing:0.5px;'>{_env_lbl}</span>"
        )
        _sep     = "<span style='color:#1e1e2e;margin:0 5px;'>·</span>"
        _cond_html = _sep.join(_cond_parts)

        n_game_qual = sum(1 for p in game_players if p.get("player_name") in qualified_names)

        _gh_border_col = pk_col if pk_col != "#888" else urg_col
        header_html = (
            # Game command module — anchor ID for nav strip
            f"<div id='gm{_ni}_{slate_ts}' style='background:#09090f;"
            f"border-left:3px solid {_gh_border_col};"
            f"border-top:1px solid #18182a;border-radius:4px;"
            f"margin:18px 0 0;overflow:hidden;'>"

            # Row 1 — matchup · time · park · env · qual count
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"flex-wrap:wrap;gap:4px;padding:6px 12px 3px;'>"
            f"<span style='font-size:14px;font-weight:800;color:#60a5fa;"
            f"letter-spacing:0.3px;'>{away_team} @ {home_team}</span>"
            f"<span style='font-size:11px;color:{urg_col};font-weight:600;'>{gt_str}</span>"
            f"<span style='font-size:10px;color:#888;'>Park "
            f"<span style='color:{pk_col};font-weight:700;'>{pk:.2f}×</span></span>"
            f"<span style='background:#0d0d1c;border:1px solid #1e1e30;border-radius:3px;"
            f"padding:1px 7px;font-size:10px;color:{_env_col};font-weight:700;"
            f"letter-spacing:1px;'>{_env_lbl}</span>"
            f"<span style='font-size:10px;color:{('#4ade80' if n_game_qual >= 3 else '#555')};'>"
            f"{n_game_qual} qual</span>"
            f"</div>"

            # Row 2 — venue + conditions strip
            f"<div style='display:flex;align-items:center;flex-wrap:wrap;gap:6px;"
            f"padding:2px 12px 4px;border-top:1px solid #101018;'>"
            f"<span style='font-size:9px;color:#2e2e42;letter-spacing:0.5px;"
            f"font-family:monospace;'>{_venue}</span>"
            + (f"<span style='color:#181828;'>·</span>"
               f"<span style='font-size:10px;'>{_cond_html}</span>" if _cond_parts else "")
            + f"</div>"

            # Row 3 — pitcher target zone
            f"<div style='display:flex;align-items:center;flex-wrap:wrap;gap:0;"
            f"padding:4px 12px 5px;border-top:1px solid #0e0e16;background:#06060c;'>"
            f"<span style='font-size:8px;color:#2e2e45;letter-spacing:1.5px;"
            f"text-transform:uppercase;margin-right:8px;font-family:monospace;'>TARGET</span>"
            # Home batters vs away pitcher
            f"<span style='font-size:10px;color:#a78bfa;font-weight:700;"
            f"margin-right:4px;'>{home_team}</span>"
            f"<span style='font-size:9px;color:#222233;margin-right:3px;'>vs</span>"
            f"<span style='font-size:10px;color:#c8c8e0;margin-right:3px;'>{away_pitcher}</span>"
            f"<span style='font-size:9px;color:#3a3a55;margin-right:5px;'>{away_pit_hand}</span>"
            f"<span style='font-size:9px;color:{away_vuln_col};font-weight:700;"
            f"letter-spacing:0.3px;'>{away_vuln_lbl}</span>"
            f"<span style='color:#181828;margin:0 10px;'>│</span>"
            # Away batters vs home pitcher
            f"<span style='font-size:10px;color:#60a5fa;font-weight:700;"
            f"margin-right:4px;'>{away_team}</span>"
            f"<span style='font-size:9px;color:#222233;margin-right:3px;'>vs</span>"
            f"<span style='font-size:10px;color:#c8c8e0;margin-right:3px;'>{home_pitcher}</span>"
            f"<span style='font-size:9px;color:#3a3a55;margin-right:5px;'>{home_pit_hand}</span>"
            f"<span style='font-size:9px;color:{home_vuln_col};font-weight:700;"
            f"letter-spacing:0.3px;'>{home_vuln_lbl}</span>"
            f"</div></div>"
        )

        # Batter rows for this game (list+join avoids O(n²) string copies)
        _row_parts = ["<div style='margin-bottom:2px'>"]
        for _ri, p in enumerate(game_players):
            pname  = p.get("player_name", "?")
            pteam  = p.get("team", "?")
            spot_s = str(p.get("lineup_spot")) if p.get("lineup_spot") else "?"

            brl   = _pf(p.get("barrel_pct"), 0)
            model = (p.get("model_prob") or 0) * 100
            ev    = p.get("ev_pct")
            edge  = p.get("edge_pct")
            conf  = p.get("confidence")

            brl_col   = "#FFD700" if brl >= 12 else "#4ade80" if brl >= 8 else "#60a5fa" if brl >= 5 else "#888"
            model_col = "#FFD700" if model >= 20 else "#4ade80" if model >= 15 else "#aaa"
            ev_col    = "#4ade80" if (ev or 0) > 0 else "#888"
            edge_col  = "#4ade80" if (edge or 0) > 0 else "#888"

            brl_s   = f"{brl:.1f}%" if brl else "—"
            model_s = f"{model:.1f}%"
            ev_s    = f"{ev:+.1f}%" if ev is not None else "—"
            edge_s  = f"{edge:+.1f}%" if edge is not None else "—"
            conf_s  = str(int(conf)) if conf is not None else "—"

            is_tac_qual = pname in tac_qualified_names
            is_qual     = pname in qualified_names
            is_elite    = brl >= 8.0
            is_steam    = pname in steam_names

            badges = ""
            if is_steam:
                badges += ("<span style='background:#1a0a00;border:1px solid #f97316;"
                           "color:#f97316;font-size:8px;padding:1px 4px;"
                           "border-radius:2px;margin-left:4px'>STEAM</span>")
            if is_elite:
                badges += ("<span style='background:#1a1200;border:1px solid #665500;"
                           "color:#FFD700;font-size:8px;padding:1px 4px;"
                           "border-radius:2px;margin-left:3px'>★ ELITE</span>")
            if is_tac_qual:
                badges += ("<span style='background:#0a1a0a;border:1px solid #2a6a2a;"
                           "color:#4ade80;font-size:8px;padding:1px 4px;"
                           "border-radius:2px;margin-left:3px'>✓ QUAL</span>")
            elif is_qual:
                badges += ("<span style='background:#0a0a1a;border:1px solid #2a2a5a;"
                           "color:#60a5fa;font-size:8px;padding:1px 4px;"
                           "border-radius:2px;margin-left:3px'>ODDS</span>")

            _alt_bg = "#0d0d18" if _ri % 2 == 0 else "#090910"
            row_bg  = "#0f0f1e" if is_tac_qual else "#0a0a14" if is_qual else _alt_bg
            _row_lc = "#FFD700" if brl >= 12 else "#4ade80" if is_tac_qual else "#60a5fa" if is_qual else "#1a1a28"

            _row_parts.append(
                f"<div style='display:flex;align-items:center;padding:3px 8px 3px 9px;"
                f"background:{row_bg};border-bottom:1px solid #0c0c12;"
                f"border-left:2px solid {_row_lc};gap:5px;flex-wrap:nowrap;'>"
                f"<span style='color:#555;font-size:9px;min-width:14px;text-align:right'>{spot_s}</span>"
                f"<span style='color:#eee;font-size:11px;font-weight:700;min-width:145px;"
                f"overflow:hidden;white-space:nowrap;text-overflow:ellipsis'>{pname}</span>"
                f"<span style='color:#666;font-size:10px;min-width:30px'>{pteam}</span>"
                f"<span style='color:#555;font-size:9px'>BRL</span>"
                f"<span style='color:{brl_col};font-size:11px;font-weight:600;min-width:36px'>{brl_s}</span>"
                f"<span style='color:#555;font-size:9px'>MDL</span>"
                f"<span style='color:{model_col};font-size:11px;min-width:36px'>{model_s}</span>"
                f"<span style='color:#4a4a70;font-size:9px'>EV</span>"
                f"<span style='color:{ev_col};font-size:11px;min-width:38px'>{ev_s}</span>"
                f"<span style='color:#4a4a70;font-size:9px'>EDG</span>"
                f"<span style='color:{edge_col};font-size:11px;min-width:38px'>{edge_s}</span>"
                f"<span style='color:#555;font-size:9px'>CNF</span>"
                f"<span style='color:#888;font-size:11px;min-width:24px'>{conf_s}</span>"
                f"{badges}"
                f"</div>"
            )
        _row_parts.append("</div>")
        st.markdown(header_html + "".join(_row_parts), unsafe_allow_html=True)

    # Return-to-top
    st.markdown(
        "<div style='text-align:center;padding:14px 0 6px;"
        "border-top:1px solid #16162a;margin-top:8px;'>"
        "<a href='#fs_top' style='font-size:9px;color:#333;text-decoration:none;"
        "letter-spacing:1.5px;font-family:monospace;'>▲ &nbsp;TOP</a></div>",
        unsafe_allow_html=True,
    )


def tab_picks(data: dict, min_ev: float, min_edge: float, cutoff_utc_hour: int | None = None, min_confidence: float = 0):
    all_players = data.get("all_players", [])
    _slate_ts = str(st.session_state.get("data_loaded_at", ""))
    _uif_fp = (
        _slate_ts,
        min_ev, min_edge,
        cutoff_utc_hour if cutoff_utc_hour is not None else -1,
        min_confidence,
    )
    if st.session_state.get("_uif_ranked_fp") == _uif_fp:
        ranked = st.session_state["_uif_ranked"]
    else:
        ranked = _apply_ui_filters(all_players, min_ev, min_edge, cutoff_utc_hour, min_confidence)
        st.session_state["_uif_ranked"] = ranked
        st.session_state["_uif_ranked_fp"] = _uif_fp
    stats     = data.get("stats", {})
    source    = data.get("odds_source", "none")
    quota     = data.get("odds_quota", {})
    n_batters = data.get("batter_count", 0)
    n_with_odds = data.get("n_with_odds") or stats.get("n_with_odds", 0)
    fail_reasons = data.get("fail_reasons", {})
    scale     = _bankroll_scale()

    # ── Portfolio optimizer ───────────────────────────────────────────────────
    _optimizer_on = st.session_state.get("optimizer_on", False)
    _optimizer_result = None
    _optimizer_selected_names: set[str] = set()
    if _optimizer_on and ranked:
        try:
            from portfolio.optimizer import PortfolioOptimizer, CONSTRAINT_PRESETS
            _preset_key = st.session_state.get("optimizer_preset", "moderate")
            _opt_constraints = CONSTRAINT_PRESETS.get(_preset_key)
            _ranked_fp = hash(tuple(p.get("player_name", "") for p in ranked))
            _opt_cache_key = f"opt_result_{_preset_key}_{_ranked_fp}"
            if _opt_cache_key in st.session_state:
                _optimizer_result = st.session_state[_opt_cache_key]
            else:
                _opt = PortfolioOptimizer(constraints=_opt_constraints)
                _optimizer_result = _opt.optimize(ranked)
                st.session_state[_opt_cache_key] = _optimizer_result
            st.session_state["optimizer_result"] = _optimizer_result
            _optimizer_selected_names = {
                r.get("player_name", "") for r in _optimizer_result.get("selected", [])
            }
            # Show optimizer banner
            _on = _optimizer_result["n_selected"]
            _om = _optimizer_result["n_input"]
            _osummary = (_opt_constraints.summary() if _opt_constraints
                         else _optimizer_result.get("summary", ""))
            st.markdown(
                f"<div style='background:#0a1a0a; border:1px solid #1a4a1a; border-left:4px solid #4ade80; "
                f"border-radius:6px; padding:8px 14px; margin-bottom:10px; font-size:12px;'>"
                f"<b style='color:#4ade80;'>🎯 Portfolio Optimizer Active</b> &nbsp;·&nbsp; "
                f"<span style='color:#f0f0f0;'>{_on} picks selected</span> "
                f"<span style='color:#555;'>from {_om} qualified</span> &nbsp;·&nbsp; "
                f"<span style='color:#888;'>{_osummary}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        except Exception as _oe:
            st.warning(f"Portfolio optimizer error: {_oe}")

    # Build odds quota display
    q_used      = quota.get("used")
    q_remaining = quota.get("remaining")
    if q_used is not None and q_remaining is not None:
        q_total = q_used + q_remaining
        odds_label = (
            f"<b style='color:#f0f0f0'>{q_used}</b>"
            f"<span style='color:#555'>/{q_total} used</span> "
            f"<b style='color:#{'FF6666' if q_remaining < 50 else 'f0f0f0'}'>{q_remaining}</b>"
            f"<span style='color:#555'> left</span>"
        )
    else:
        odds_label = f"<b style='color:#f0f0f0'>{source}</b>"

    st.markdown('<div class="section-header">&#9889; MAIN</div>',
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:11px;color:#555;letter-spacing:0.5px;margin:-4px 0 8px;'>"
        "Quantitative Market-Aware Intelligence &nbsp;·&nbsp; EV / Edge Ranked &nbsp;·&nbsp; "
        "Statcast Calibrated"
        "</div>",
        unsafe_allow_html=True,
    )

    # Lineup readiness + slate status
    n_confirmed  = sum(1 for p in all_players if p.get("lineup_spot"))
    n_estimated  = len(all_players) - n_confirmed
    lineup_pct   = int(100 * n_confirmed / len(all_players)) if all_players else 0
    lineup_color = "#4ade80" if lineup_pct >= 80 else "#FFD700" if lineup_pct >= 40 else "#FF6666"
    # Slate status pill — communicates whether lineups are set or projected
    if lineup_pct >= 80:
        _slate_pill = "<span style='background:#0a2a0a;color:#4ade80;font-size:10px;font-weight:700;padding:1px 7px;border-radius:10px;border:1px solid #1a4a1a;'>🟢 CONFIRMED</span>"
    elif lineup_pct >= 40:
        _slate_pill = "<span style='background:#1a1a00;color:#FFD700;font-size:10px;font-weight:700;padding:1px 7px;border-radius:10px;border:1px solid #444400;'>🟡 MIXED</span>"
    else:
        _slate_pill = "<span style='background:#0a0a2a;color:#60a5fa;font-size:10px;font-weight:700;padding:1px 7px;border-radius:10px;border:1px solid #1a1a4a;'>🔵 PROJECTED</span>"
    lineup_label = (
        f"Lineups: <b style='color:{lineup_color}'>{n_confirmed}/{len(all_players)} confirmed</b>"
        + (f" <span style='color:#888'>({n_estimated} estimated)</span>" if n_estimated else "")
        + f"  {_slate_pill}"
    )

    loaded_at    = st.session_state.get("data_loaded_at")
    age_str      = ""
    if loaded_at:
        age_min  = int((_dt.datetime.now() - loaded_at).total_seconds() / 60)
        age_str  = f" &nbsp;|&nbsp; Loaded: <b style='color:#888'>{loaded_at.strftime('%I:%M %p').lstrip('0')}</b>"
        if age_min >= 60:
            age_str += f" <span style='color:#FF6666'>({age_min//60}h old — refresh?)</span>"

    st.markdown(
        f"<div style='color:#888888; font-size:12px; margin-bottom:12px; "
        f"background:#110000; border:1px solid #330000; border-radius:6px; padding:8px 14px;'>"
        f"📅 {data.get('date','')} &nbsp;|&nbsp; "
        f"Games: <b style='color:#f0f0f0'>{stats.get('games',0)}</b> &nbsp;|&nbsp; "
        f"Players: <b style='color:#f0f0f0'>{stats.get('players',0)}</b> "
        f"<span style='color:#555'>({n_with_odds} with odds)</span> &nbsp;|&nbsp; "
        f"Qualified: <b style='color:#FF3333'>{len(ranked)}</b> "
        f"<span style='color:#555'>(EV≥{min_ev:.0f}% Edge≥{min_edge:.1f}%"
        + (f" Conf≥{min_confidence:.0f}" if min_confidence > 0 else "")
        + f")</span> &nbsp;|&nbsp; "
        f"Odds: {odds_label} &nbsp;|&nbsp; "
        f"Statcast: <b style='color:#f0f0f0'>{n_batters}</b> batters &nbsp;|&nbsp; "
        f"{lineup_label}{age_str}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Best Bet Hero Card ───────────────────────────────────────────────────
    if ranked:
        _top = ranked[0]
        _top_name  = _top.get("player_name", "")
        _top_team  = _top.get("team", "")
        _top_vs    = _top.get("pitcher_name", "")
        _top_ev    = _top.get("ev_pct", 0)
        _top_edge  = _top.get("edge_pct", 0)
        _top_model = _top.get("model_prob", 0) * 100
        _top_odds  = _top.get("best_american")
        _top_book  = _top.get("best_book", "")
        _top_bet   = _top.get("bet_dollars", 0)
        _top_spot  = _top.get("lineup_spot")
        _top_conf  = "✅ Confirmed" if _top_spot is not None else "⏳ Estimated"
        _top_ev_col = "#4ade80" if _top_ev >= 0 else "#f87171"
        _top_url    = _fanduel_url(_top_name)

        _top_tier     = _top.get("confidence_tier", "C")
        _top_tier_col = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_top_tier, "#888")
        _top_pit_lbl  = _pitcher_label(_top_vs, _top.get("pitcher_factor", 1.0), _top.get("platoon_factor", 1.0))
        _top_hand     = _top.get("pitcher_hand", "")
        _top_hand_s   = f" ({'RHP' if _top_hand == 'R' else 'LHP' if _top_hand == 'L' else ''})" if _top_hand else ""
        _top_status_html, _top_is_live = _game_status_badge(_top)
        _top_photo    = _player_photo_html(_top.get("player_id"), size=56,
                                           style="border:2px solid #FFD700;margin-bottom:4px;")
        _hc1, _hc2, _hc3, _hc4, _hc5 = st.columns([5, 2, 2, 2, 2])
        with _hc1:
            if _top_photo:
                st.markdown(_top_photo, unsafe_allow_html=True)
            if st.button(
                f"🏆  {_top_name}",
                key="hero_modal_btn",
                help=f"View full stats for {_top_name}",
                use_container_width=True,
            ):
                st.session_state["show_modal"] = _top
                st.session_state["modal_source_tab"] = "Command Center"
                st.session_state["modal_source_section"] = "Top Pick"
                st.rerun()
            _top_sub = (
                f"<div style='font-size:12px; color:#888; margin:-4px 0 2px 6px;'>"
                f"{_top_team} &nbsp;·&nbsp; vs {_top_pit_lbl}{_top_hand_s} &nbsp;·&nbsp; {_top_conf}"
                + (f" &nbsp;·&nbsp; Spot #{_top_spot}" if _top_spot else "")
                + f"</div>"
            )
            if _top_status_html:
                _top_sub += f"<div style='font-size:11px;margin:-2px 0 4px 6px;'>{_top_status_html}</div>"
            st.markdown(_top_sub, unsafe_allow_html=True)
        with _hc2:
            st.metric("Model / EV",
                      f"{_top_model:.0f}%",
                      delta=f"EV {_top_ev:+.1f}%",
                      delta_color="normal")
        with _hc3:
            st.metric("Edge%",
                      f"{_top_edge:+.1f}%",
                      delta=None)
        with _hc5:
            st.markdown(
                f"<div style='text-align:center;padding-top:8px;'>"
                f"<div style='font-size:22px;font-weight:900;color:{_top_tier_col};'>{_top_tier}</div>"
                f"<div style='font-size:11px;color:#666;'>Tier</div></div>",
                unsafe_allow_html=True,
            )
        with _hc4:
            st.metric("Odds / Bet",
                      _fmt_american(_top_odds) if _top_odds else "--",
                      delta=f"${_top_bet:.0f} suggested" if _top_bet else None,
                      delta_color="off")

        _hb1, _hb2 = st.columns([8, 2])
        with _hb2:
            st.link_button("Open on FanDuel ↗", _top_url, use_container_width=True)

        st.markdown(
            "<div style='border-top:1px solid #2a1a2a; margin:10px 0 14px;'></div>",
            unsafe_allow_html=True,
        )

    # ── Share / Export ────────────────────────────────────────────────────────
    if ranked:
        with st.expander("📤 Share Picks", expanded=False):
            _share_date  = data.get("date", _dt.date.today().isoformat())
            _share_lines = [
                f"⚾ CODEX HR PICKS — {_share_date}",
                "━" * 36,
                "",
            ]
            for _si, _sp in enumerate(ranked):
                _sname   = _sp.get("player_name", "")
                _steam   = _sp.get("team", "")
                _svs     = _sp.get("pitcher_name", "")
                _sodds   = _sp.get("best_american")
                _sbook   = _sp.get("best_book", _sp.get("best_bookmaker", "")).title()
                _smodel  = _sp.get("model_prob", 0) * 100
                _sev     = _sp.get("ev_pct", 0)
                _sedge   = _sp.get("edge_pct", 0)
                _sbet    = _sp.get("bet_size") or _sp.get("bet_dollars")
                _sconf   = "✅" if _sp.get("lineup_spot") is not None else "⏳"
                _prefix  = "🏆 #1 BEST BET" if _si == 0 else f"{_si + 1}."
                _share_lines.append(f"{_prefix} {_sconf} {_sname} ({_steam}) vs {_svs}")
                _odds_str = _fmt_american(_sodds) if _sodds else "--"
                _book_str = f" @ {_sbook}" if _sbook else ""
                _bet_str  = f" | Bet: ${float(_sbet):.0f}" if _sbet else ""
                _share_lines.append(
                    f"   {_odds_str}{_book_str} | {_smodel:.0f}% model | EV {_sev:+.1f}% | Edge {_sedge:+.1f}%{_bet_str}"
                )
                _share_lines.append("")
            _share_lines += [
                "━" * 36,
                "Generated by Codex HR Engine v4",
            ]
            _share_text = "\n".join(_share_lines)
            st.text_area(
                "Copy the text below",
                value=_share_text,
                height=min(300, 60 + len(ranked) * 55),
                label_visibility="collapsed",
            )
            st.caption("Select all text above and copy (⌘A / Ctrl+A → ⌘C / Ctrl+C).")

    all_by_model_raw = data.get("all_by_model", [])
    # Apply time gate separately so Prime tab (all prime plays) and Prime Time tab
    # (time-filtered prime plays) can show different counts and players.
    # Must compare in ET, not raw UTC — late games (9pm+ ET) cross midnight UTC and would
    # have UTC hours 01/02, failing a raw >= 23 check even though they're after the cutoff.
    if cutoff_utc_hour is not None:
        _abm_cutoff_et = (cutoff_utc_hour - 4) % 24
        all_by_model = [
            p for p in all_by_model_raw
            if (gt := _game_time_et(p.get("game_time_utc", ""))) is None or gt.hour >= _abm_cutoff_et
        ]
    else:
        all_by_model = all_by_model_raw
    PRIME_FLOOR    = 0.15
    _n_prime       = len([p for p in all_by_model_raw if p.get("model_prob", 0) >= PRIME_FLOOR])
    _n_prime_timed = len([p for p in all_by_model     if p.get("model_prob", 0) >= PRIME_FLOOR])
    _n_watch       = len([p for p in all_by_model     if p.get("model_prob", 0) < PRIME_FLOOR])

    # Compute steam moves: players whose implied prob shortened ≥2pp since first snapshot
    _steam_names: set = set()
    _steam_details: list = []   # [(name, open_odds, curr_odds, move_pct, is_ranked)]
    try:
        _lm_today = _cached_steam_moves()
        _ranked_names = {p.get("player_name") for p in ranked}
        for _lm_name, _lm_snaps in _lm_today.items():
            _lm_summ = lm_tracker.movement_summary(_lm_snaps)
            if _lm_summ and _lm_summ.get("move_pct", 0) >= 2.0:
                _steam_names.add(_lm_name)
                _steam_details.append((
                    _lm_name,
                    _lm_summ.get("opening_odds"),
                    _lm_summ.get("current_odds"),
                    _lm_summ.get("move_pct", 0),
                    _lm_name in _ranked_names,
                ))
        _steam_details.sort(key=lambda x: x[3], reverse=True)
    except Exception:
        pass

    # ── Steam move alert banner ───────────────────────────────────────────────
    if _steam_details:
        _steam_pick_names = [x[0] for x in _steam_details if x[4]]
        _steam_watch_names = [x[0] for x in _steam_details if not x[4]]
        _banner_parts = []
        if _steam_pick_names:
            _banner_parts.append(f"**📈 Sharp money on your picks: {', '.join(_steam_pick_names)}**")
        if _steam_watch_names:
            _banner_parts.append(f"Also moving: {', '.join(_steam_watch_names)}")

        with st.container():
            st.markdown(
                f"<div style='background:#1a1a00; border:1px solid #666600; border-left:4px solid #FFD700; "
                f"border-radius:6px; padding:10px 16px; margin-bottom:12px;'>"
                f"<div style='color:#FFD700; font-weight:700; font-size:13px; margin-bottom:6px;'>"
                f"⚡ LINE MOVEMENT ALERT</div>"
                + "".join(
                    f"<div style='display:flex; justify-content:space-between; align-items:center; "
                    f"margin-bottom:4px; padding:4px 8px; background:#{'111100' if x[4] else '0d0d00'}; "
                    f"border-radius:4px;'>"
                    f"<span style='color:{'#FFD700' if x[4] else '#aaaaaa'}; font-weight:{'700' if x[4] else '400'};'>"
                    f"{'✅ ' if x[4] else '○ '}{html.escape(x[0])}</span>"
                    f"<span style='color:#888; font-size:12px;'>"
                    f"{_fmt_american(x[1])} → {_fmt_american(x[2])} "
                    f"<b style='color:#FF6666'>({x[3]:+.1f}pp shorter)</b></span>"
                    f"</div>"
                    for x in _steam_details
                )
                + "<div style='color:#888; font-size:11px; margin-top:6px;'>"
                  "Lines shortening = market gaining confidence. Bet before it moves further.</div>"
                  "</div>",
                unsafe_allow_html=True,
            )

    # ── Pitcher change alert banner ───────────────────────────────────────────
    _pitcher_changes = st.session_state.get("pitcher_changes", {})
    if _pitcher_changes:
        # Which affected teams have picks in our ranked list?
        _ranked_teams = {p.get("team", "") for p in ranked}
        _opp_teams    = {p.get("opponent", "") for p in ranked}
        _affected_picks = {t for t in _pitcher_changes if t in _ranked_teams or t in _opp_teams}

        _pc_rows_html = ""
        for team, ch in _pitcher_changes.items():
            _is_pick_team = team in _affected_picks
            _pc_rows_html += (
                f"<div style='display:flex; justify-content:space-between; align-items:center; "
                f"margin-bottom:4px; padding:4px 8px; "
                f"background:#{'1a0000' if _is_pick_team else '0d0000'}; border-radius:4px;'>"
                f"<span style='color:{'#FF6666' if _is_pick_team else '#aaaaaa'}; "
                f"font-weight:{'700' if _is_pick_team else '400'};'>"
                f"{'⚠️ ' if _is_pick_team else '○ '}{team}</span>"
                f"<span style='color:#888; font-size:12px;'>"
                f"<s>{html.escape(ch['old'])}</s> → <b style='color:#FF6666'>{html.escape(ch['new'])}</b></span>"
                f"</div>"
            )
        st.markdown(
            f"<div style='background:#1a0000; border:1px solid #660000; border-left:4px solid #FF3333; "
            f"border-radius:6px; padding:10px 16px; margin-bottom:12px;'>"
            f"<div style='color:#FF3333; font-weight:700; font-size:13px; margin-bottom:6px;'>"
            f"🔄 PITCHER CHANGE DETECTED</div>"
            + _pc_rows_html
            + "<div style='color:#888; font-size:11px; margin-top:6px;'>"
              "Model probabilities were calculated using the original starters. "
              "Picks against affected teams may no longer be valid — verify before betting.</div>"
              "</div>",
            unsafe_allow_html=True,
        )

    # ── TACTICAL COMMAND CENTER ───────────────────────────────────────────────
    _tac_stat_keys = [
        "tac_min_barrel", "tac_min_hh", "tac_min_xslg", "tac_min_iso",
        "tac_min_pull_air", "tac_min_hr_window",
        "tac_min_ev", "tac_min_edge", "tac_min_conf", "tac_min_model_prob",
    ]
    # Neutral defaults: reset returns to a true no-filter state so widget state,
    # active counts, and the eligible universe stay synchronized.
    _tac_reset_defaults = {
        "tac_min_barrel":     0.0,
        "tac_min_hh":         0.0,
        "tac_min_xslg":       0.0,
        "tac_min_iso":        0.0,
        "tac_min_pull_air":   0.0,
        "tac_min_hr_window":  0.0,
        "tac_min_matchup_pct": 75,
        "tac_min_hvy_score":  0,
        "tac_min_ev":         0.0,
        "tac_min_edge":       0.0,
        "tac_min_conf":       0.0,
        "tac_min_model_prob": 0.0,
        "tac_exclude_started": False,
        "tac_include_live":   False,
    }
    def _tac_is_active(key: str) -> bool:
        val = st.session_state.get(key, _tac_reset_defaults.get(key, 0.0))
        if key == "tac_min_matchup_pct":
            return float(val or 0) > 75.0
        return float(val or 0) > 0.0

    _tac_n_active = sum(
        1 for _k in (_tac_stat_keys + ["tac_min_matchup_pct", "tac_min_hvy_score"])
        if _tac_is_active(_k)
    )
    if st.session_state.get("tac_exclude_started", False):
        _tac_n_active += 1
    _tac_panel_lbl = "⚙️  Tactical Command Center" + (
        f"  ·  {_tac_n_active} active" if _tac_n_active else "")

    with st.expander(_tac_panel_lbl, expanded=False):
        # ── Engine Identity + Preset Bar ────────────────────────────────────
        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:baseline;"
            "margin-bottom:2px;'>"
            "<div style='font-size:9px;color:#888;letter-spacing:1px;'>MAIN ENGINE PRESET</div>"
            "<div style='font-size:9px;color:#4ade80;letter-spacing:1px;'>"
            "Quantitative · Market-Aware · Selective</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        def _main_tcc_reset():
            for _rk, _rv in _tac_reset_defaults.items():
                st.session_state[_rk] = _rv
            st.session_state.pop("tac_active_preset", None)
            st.rerun()
        _fc.render_preset_bar("tac_active_preset", _fc.MAIN_PRESETS, reset_cb=_main_tcc_reset)
        st.caption(
            f"Sidebar: EV ≥ {min_ev:.0f}%  ·  Edge ≥ {min_edge:.0f}%  ·  Conf ≥ {min_confidence}  —  "
            "POWER / CONTACT / MARKET filters narrow the full Main universe.  "
            "MATCHUP EDGE controls (bottom) affect only the Matchup Edge tab."
        )

        # ── MAIN UNIVERSE FILTERS (affect Full Slate / Top Targets / Portfolio / Command Center) ──
        st.markdown(
            "<div style='font-size:9px;color:#4ade80;font-weight:700;letter-spacing:2px;"
            "margin:8px 0 4px;'>▼ MAIN UNIVERSE FILTERS — narrow all tabs</div>",
            unsafe_allow_html=True,
        )
        _tf1, _tf2, _tf3 = st.columns(3)
        with _tf1:
            st.markdown(
                "<div style='font-size:10px;color:#a78bfa;font-weight:700;"
                "letter-spacing:1px;margin-bottom:4px;'>POWER PROFILE</div>",
                unsafe_allow_html=True,
            )
            _fc.render_filter_control(
                "Barrel %", "tac_min_barrel", 0.0, 20.0, 0.0, 0.5, "%.1f",
                "Statcast barrel rate floor — 8%+ = elite power tier",
            )
            _fc.render_filter_control(
                "Hard Hit %", "tac_min_hh", 0.0, 60.0, 0.0, 0.5, "%.1f",
                "Hard-hit rate floor (exit velo ≥ 95 mph)",
            )
        with _tf2:
            st.markdown(
                "<div style='font-size:10px;color:#a78bfa;font-weight:700;"
                "letter-spacing:1px;margin-bottom:4px;'>CONTACT QUALITY</div>",
                unsafe_allow_html=True,
            )
            _fc.render_filter_control(
                "xSLG", "tac_min_xslg", 0.000, 0.700, 0.000, 0.010, "%.3f",
                "Expected slugging percentage floor — league avg ≈ .418",
            )
            _fc.render_filter_control(
                "ISO", "tac_min_iso", 0.000, 0.450, 0.000, 0.010, "%.3f",
                "Isolated power (SLG − AVG) floor — league avg ≈ .157",
            )
        with _tf3:
            st.markdown(
                "<div style='font-size:10px;color:#a78bfa;font-weight:700;"
                "letter-spacing:1px;margin-bottom:4px;'>CONTACT SHAPE</div>",
                unsafe_allow_html=True,
            )
            _fc.render_filter_control(
                "Pull Air %", "tac_min_pull_air", 0.0, 40.0, 0.0, 0.5, "%.1f",
                "Pulled-airborne contact rate floor",
            )
            _fc.render_filter_control(
                "HR Window %", "tac_min_hr_window", 0.0, 50.0, 0.0, 0.5, "%.1f",
                "Sweet-spot % floor (8–32° launch angle)",
            )

        st.markdown(
            "<div style='font-size:10px;color:#60a5fa;font-weight:700;"
            "letter-spacing:1px;margin:8px 0 4px;'>MARKET / MODEL FILTERS</div>",
            unsafe_allow_html=True,
        )
        _tm1, _tm2, _tm3, _tm4 = st.columns(4)
        with _tm1:
            _fc.render_filter_control(
                "EV %", "tac_min_ev", 0.0, 20.0, 0.0, 0.5, "%.1f",
                "Minimum expected value percentage",
            )
        with _tm2:
            _fc.render_filter_control(
                "Edge %", "tac_min_edge", 0.0, 20.0, 0.0, 0.5, "%.1f",
                "Minimum edge over market no-vig probability",
            )
        with _tm3:
            _fc.render_filter_control(
                "Confidence", "tac_min_conf", 0.0, 100.0, 0.0, 5.0, "%.0f",
                "Minimum model confidence score (0–100)",
            )
        with _tm4:
            _fc.render_filter_control(
                "Model Prob %", "tac_min_model_prob", 0.0, 30.0, 0.0, 0.5, "%.1f",
                "Minimum model probability percentage",
            )

        _te1, _te2, _te3 = st.columns(3)
        with _te1:
            st.toggle("Exclude Started Games", value=False, key="tac_exclude_started")
        with _te2:
            st.toggle("Include Live Games",    value=False, key="tac_include_live")
        with _te3:
            _tc_cutoff = st.session_state.get("cutoff_utc_hour")
            if _tc_cutoff is not None:
                _tc_et = (_tc_cutoff - 4) % 24
                _tc_h12 = _tc_et % 12 or 12
                _tc_ampm = "AM" if _tc_et < 12 else "PM"
                st.caption(f"⏰ Time gate: {_tc_h12}:00 {_tc_ampm} ET  ←  sidebar")
            else:
                st.caption("⏰ No time gate  ←  sidebar")

        # ── MATCHUP EDGE FILTERS (affect only the Matchup Edge tab) ──────────────
        st.markdown(
            "<div style='border-top:1px solid #2a1a00;margin:10px 0 6px;"
            "padding-top:8px;font-size:9px;color:#f97316;font-weight:700;"
            "letter-spacing:2px;'>▼ MATCHUP EDGE TAB ONLY — does not narrow Main/Top Targets/Full Slate</div>",
            unsafe_allow_html=True,
        )
        _tme1, _tme2 = st.columns(2)
        with _tme1:
            _fc.render_filter_control(
                "Min Matchup Modifier %", "tac_min_matchup_pct", 75, 140, 75, 1, "%d",
                "HVY modifier gate for Matchup Edge tab. 100=neutral, 110+=favorable, 120+=elite. "
                "Does NOT remove picks from Command Center, Top Targets, or Full Slate.",
            )
        with _tme2:
            _fc.render_filter_control(
                "Min HVY Score", "tac_min_hvy_score", 0, 100, 0, 1, "%d",
                "HVY composite matchup score gate (0–100) for Matchup Edge tab only. "
                "Does NOT remove picks from Command Center, Top Targets, or Full Slate.",
            )

        # ── PITCH MIX DISPLAY CONTROL ────────────────────────────────────────
        st.markdown(
            "<div style='border-top:1px solid #1a1a1a;margin:8px 0 4px;"
            "padding-top:6px;font-size:9px;color:#888;letter-spacing:1px;'>"
            "PITCH MIX DISPLAY — Command Center / Top Targets / Matchup Edge cards</div>",
            unsafe_allow_html=True,
        )
        _pm1, _pm2 = st.columns(2)
        with _pm1:
            if st.button(
                "Open All Pitch Mix",
                key="_main_pm_open",
                use_container_width=True,
                help="Expand pitch mix analysis on all visible Main cards",
            ):
                st.session_state["main_pitch_mix_expanded"] = True
                st.rerun()
        with _pm2:
            if st.button(
                "Close All Pitch Mix",
                key="_main_pm_close",
                use_container_width=True,
                help="Collapse pitch mix analysis on all visible Main cards",
            ):
                st.session_state["main_pitch_mix_expanded"] = False
                st.rerun()

    # Apply tactical batter-profile filters to narrow eligible universe
    _tac_params = {
        "min_barrel":      st.session_state.get("tac_min_barrel",    0.0),
        "min_hh":          st.session_state.get("tac_min_hh",        0.0),
        "min_xslg":        st.session_state.get("tac_min_xslg",      0.0),
        "min_iso":         st.session_state.get("tac_min_iso",        0.0),
        "min_pull_air":    st.session_state.get("tac_min_pull_air",  0.0),
        "min_hr_window":   st.session_state.get("tac_min_hr_window", 0.0),
        "min_ev":          st.session_state.get("tac_min_ev",        0.0),
        "min_edge":        st.session_state.get("tac_min_edge",      0.0),
        "min_conf":        st.session_state.get("tac_min_conf",      0.0),
        "min_model_prob":  st.session_state.get("tac_min_model_prob",0.0),
        "exclude_started": st.session_state.get("tac_exclude_started", False),
        "include_live":    st.session_state.get("tac_include_live",    False),
    }
    _any_tac_active = (
        any(_tac_params[k] > 0 for k in (
            "min_barrel", "min_hh", "min_xslg", "min_iso", "min_pull_air", "min_hr_window",
            "min_ev", "min_edge", "min_conf", "min_model_prob",
        ))
        or _tac_params["exclude_started"]
    )
    # Fingerprint-cache the tactical filter result — avoids re-filtering on every rerender
    # when TCC params and ranked list are unchanged.
    _tac_filter_fp = (_slate_ts, id(ranked), tuple(_tac_params.values()))
    if st.session_state.get("_tac_filter_fp") == _tac_filter_fp:
        _tac_ranked = st.session_state["_tac_ranked"]
    else:
        _tac_ranked = _apply_tactical_filters(ranked, _tac_params) if _any_tac_active else ranked
        st.session_state["_tac_ranked"] = _tac_ranked
        st.session_state["_tac_filter_fp"] = _tac_filter_fp

    # ── OPERATIONAL INTELLIGENCE LAYER ──────────────────────────────────────────
    _now_et = _dt.datetime.now(_EDT)
    _n_elite = len([p for p in ranked if _pf(p.get("barrel_pct"), 0) >= 8.0])
    _display_pool = (
        [p for p in _tac_ranked if p.get("player_name") in _optimizer_selected_names]
        if _optimizer_on and _optimizer_selected_names else _tac_ranked
    )

    # ── Pre-compute status + urgency once for all players (avoids O(N) re-calls per render pass)
    # Use ranked (full universe) so Top Targets tab cache-hits for players filtered out of TCC view
    _status_cache: dict = {}   # player_id → (html, is_live)
    _urgency_cache: dict = {}  # player_id → (gt_str, urgency_col, urgency_lbl)
    for _pc_p in ranked:
        _pc_pid = _pc_p.get("player_id") or _pc_p.get("player_name", "")
        _status_cache[_pc_pid] = _game_status_badge(_pc_p)
        _pc_gt = _game_time_et(_pc_p.get("game_time_utc", ""))
        if _pc_gt:
            _pc_gt_str = _pc_gt.strftime('%I:%M %p ET').lstrip('0')
            _pc_gt_dt  = _dt.datetime.combine(_now_et.date(), _pc_gt, tzinfo=_EDT)
            _pc_mins   = int((_pc_gt_dt - _now_et).total_seconds() / 60)
            if _pc_mins < 0:
                _pc_uc = "#555"; _pc_ul = ""
            elif _pc_mins < 60:
                _pc_uc = "#f87171"; _pc_ul = f"BET NOW · {_pc_mins}m"
            elif _pc_mins < 120:
                _pc_uc = "#FFD700"; _pc_ul = f"{_pc_mins}m"
            else:
                _pc_uc = "#4ade80"; _pc_ul = f"{_pc_mins // 60}h {_pc_mins % 60}m"
        else:
            _pc_gt_str = "TBD"; _pc_uc = "#555"; _pc_ul = ""
        _urgency_cache[_pc_pid] = (_pc_gt_str, _pc_uc, _pc_ul)

    # ── Pre-load pitch mix contexts (shared across Command Center / Top Targets / Matchup Edge / Full Slate)
    from clients.pitch_mix import (
        load_hvy_contexts_batch as _pm_load_batch,
        HVY_CACHE_VERSION as _PM_VER,
    )
    from clients import arsenal as _pm_ar_client
    _pm_pitcher_fp = hash(frozenset((p.get("player_id"), p.get("pitcher_id")) for p in ranked))
    _pm_ck = f"picks_pm_ctx_{data.get('date', '')}_{_PM_VER}_{_pm_pitcher_fp}"
    if _pm_ck not in st.session_state:
        with st.spinner("Loading pitch intelligence…"):
            try:
                _pm_ar = _pm_ar_client.get_pitcher_arsenal(config.CURRENT_SEASON)
            except Exception:
                _pm_ar = {}
            st.session_state[_pm_ck] = _pm_load_batch(ranked, _pm_ar)
    _pm_ctxs: dict = st.session_state.get(_pm_ck, {})
    # Alias used by Matchup Edge tab internals
    _me_ck   = _pm_ck
    _me_ctxs = _pm_ctxs

    tab_qv, tab_elite, tab_edge, tab_fs, tab_port = st.tabs([
        f"⚡  COMMAND CENTER  ({len(_display_pool)})",
        f"💎  TOP TARGETS  ({_n_elite})",
        "🎯  MATCHUP EDGE",
        f"🗂️  FULL SLATE  ({len(all_players)})",
        "📊  PORTFOLIO",
    ])

    # ── TAB 1: COMMAND CENTER ────────────────────────────────────────────────
    with tab_qv:
        _qv_pool = _display_pool[:12] if _display_pool else []
        if not _qv_pool:
            st.info(
                f"No qualified picks (EV ≥ {min_ev:.1f}%, Edge ≥ {min_edge:.1f}%). "
                "Try sliding filters left in the sidebar or click 'Force Refresh Data'."
            )
            # Diagnostic: show why picks are failing when there's odds data but 0 qualify
            if n_with_odds > 0 and fail_reasons:
                _top_fails = sorted(fail_reasons.items(), key=lambda x: x[1], reverse=True)[:5]
                _fail_html = " &nbsp;·&nbsp; ".join(
                    f"<b>{r}</b> ({n})" for r, n in _top_fails
                )
                st.markdown(
                    f"<div style='background:#1a0a00;border:1px solid #553300;border-radius:6px;"
                    f"padding:8px 14px;font-size:11px;color:#aaa;margin-top:8px;'>"
                    f"<b style='color:#FFD700;'>Diagnostic</b> — {n_with_odds} players have odds, "
                    f"top filter failures: {_fail_html}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                # Show the top 10 players with odds and their EV/edge for debugging
                _odds_players = [p for p in all_players if p.get("best_american")]
                _odds_players.sort(key=lambda x: x.get("edge_pct", -999), reverse=True)
                if _odds_players:
                    with st.expander(f"🔍 Players with odds — edge breakdown ({len(_odds_players)} players)", expanded=False):
                        import pandas as _pd
                        _diag_rows = []
                        for _dp in _odds_players[:20]:
                            _diag_rows.append({
                                "Player": _dp.get("player_name", ""),
                                "Odds": _fmt_american(_dp.get("best_american")),
                                "Model%": f"{_dp.get('model_prob',0)*100:.1f}%",
                                "Mkt NV%": f"{_dp.get('market_no_vig_prob',0)*100:.1f}%",
                                "Edge%": f"{_dp.get('edge_pct',0):+.1f}%",
                                "EV%": f"{_dp.get('ev_pct',0):+.1f}%",
                                "Fails": " | ".join(_dp.get("filter_reasons", [])),
                            })
                        st.dataframe(_pd.DataFrame(_diag_rows), use_container_width=True, hide_index=True)
        else:
            # ── Tactical scan status bar ──────────────────────────────────────
            _qv_steam_n = len(_steam_names & {p.get("player_name") for p in _display_pool})
            _qv_live_n  = sum(
                1 for p in _display_pool
                if _status_cache.get(p.get("player_id") or p.get("player_name", ""), ("", False))[1]
            )
            _qv_conf_n  = sum(1 for p in _display_pool if p.get("lineup_spot") is not None)
            st.markdown(
                f"<div style='display:flex;gap:14px;align-items:center;padding:6px 0 10px;"
                f"border-bottom:1px solid #1e1e40;margin-bottom:10px;flex-wrap:wrap;'>"
                f"<span style='color:#a78bfa;font-size:12px;font-weight:700;letter-spacing:2px;"
                f"text-transform:uppercase;'>⚡ Tactical Intel Feed</span>"
                f"<span style='color:#4ade80;font-size:11px;'>✅ {_qv_conf_n} confirmed</span>"
                + (f"<span style='color:#f87171;font-size:11px;'>🔴 {_qv_live_n} LIVE</span>" if _qv_live_n else "")
                + (f"<span style='color:#FFD700;font-size:11px;'>📈 {_qv_steam_n} steam</span>"  if _qv_steam_n else "")
                + (f"<span style='color:#4ade80;font-size:11px;'>🎯 OPT · {len(_display_pool)} selected</span>" if _optimizer_on else "")
                + f"<span style='color:#444;font-size:10px;margin-left:auto;'>"
                f"showing top {len(_qv_pool)} of {len(_display_pool)}</span>"
                + f"</div>",
                unsafe_allow_html=True,
            )

            # ── Pre-compute pitch attack tags for all visible cards ───────────
            _qv_pitch_tags: dict = {}
            for _ptag_p in _qv_pool:
                _ptag_pid = _ptag_p.get("player_id")
                _ptag_ctx = _pm_ctxs.get(_ptag_pid, {})
                _qv_pitch_tags[_ptag_pid] = _pitch_attack_tags(_ptag_ctx, _ptag_p, max_tags=2)

            # ── 3-column tactical intelligence grid ───────────────────────────
            # All 12 picks in a uniform grid — rank badge distinguishes alpha picks.
            # Desktop: 3 cards per row. Mobile: columns wrap to 1 via CSS flex.
            _QV_COLS   = 3
            _qv_ranked = list(enumerate(_qv_pool, start=1))  # [(rank, player), ...]
            _qv_rows   = [_qv_ranked[i:i + _QV_COLS] for i in range(0, len(_qv_ranked), _QV_COLS)]

            for _row_data in _qv_rows:
                _row_cols = st.columns(len(_row_data))
                for _ci, (_rank, _qp) in enumerate(_row_data):
                    with _row_cols[_ci]:
                        _qpid     = _qp.get("player_id") or _qp.get("player_name", "")
                        _ctx      = _pm_ctxs.get(_qp.get("player_id"), {})
                        _qstatus_html, _qis_live = _status_cache.get(_qpid, ("", False))
                        _qgt_str, _urgency_col, _urgency_lbl = _urgency_cache.get(_qpid, ("TBD", "#555", ""))
                        _qis_steam   = _qp.get("player_name") in _steam_names
                        _pitch_tags  = _qv_pitch_tags.get(_qp.get("player_id"), [])
                        _qspot       = _qp.get("lineup_spot")
                        _qis_opt_sel = _qp.get("player_name") in _optimizer_selected_names

                        # Modal trigger button
                        if st.button(
                            f"{'✅' if _qspot is not None else '⏳'} {_qp['player_name']}",
                            key=f"tac_btn_{_rank}",
                            use_container_width=True,
                        ):
                            st.session_state["show_modal"] = _qp
                            st.session_state["modal_source_tab"] = "Command Center"
                            st.session_state["modal_source_section"] = f"Rank #{_rank}"
                            st.rerun()

                        # Level 1 — Tactical Intelligence Card (fingerprint-cached)
                        _qv_fp = (
                            "ic", _slate_ts, _qpid, _rank,
                            _qis_live, _qis_steam, _optimizer_on, _qis_opt_sel,
                            _urgency_lbl, _qgt_str,
                            hash(_qstatus_html) if _qstatus_html else 0,
                            tuple(_pitch_tags) if _pitch_tags else (),
                        )
                        st.markdown(
                            _card_html(_qv_fp, lambda: _intelligence_card_html(
                                _qp, _rank, _ctx,
                                pitch_tags=_pitch_tags,
                                is_steam=_qis_steam,
                                is_live=_qis_live,
                                status_html=_qstatus_html,
                                gt_str=_qgt_str,
                                urgency_col=_urgency_col,
                                urgency_lbl=_urgency_lbl,
                                opt_active=_optimizer_on,
                                opt_selected=_qis_opt_sel,
                            )),
                            unsafe_allow_html=True,
                        )

                        # Level 2 — Inline Pitch Intelligence Expansion
                        _render_pitch_mix_expander(_ctx, _qp, f"qv_tac_{_rank}",
                                                   expanded=st.session_state.get("main_pitch_mix_expanded", False),
                                                   slate_ts=_slate_ts)

        if _display_pool:
            with st.expander(
                f"📋 Full Slate ({len(_display_pool)} picks)"
                + (" — Optimizer filtered" if _optimizer_on else ""),
                expanded=False,
            ):
                _render_qualified_table(_display_pool, scale, min_ev, min_edge, _steam_names, "qv_slate")
        if all_by_model:
            with st.expander(f"🌐 Full Universe ({len(all_by_model)} players with odds)", expanded=False):
                _render_qualified_table(all_by_model, scale, min_ev, min_edge, _steam_names, "qv_universe")

    # ── TAB 2: TOP TARGETS (formerly Elite) ───────────────────────────────────
    with tab_elite:
        _elite_pool = sorted(
            [p for p in ranked if _pf(p.get("barrel_pct"), 0) >= 8.0],
            key=lambda p: (_pf(p.get("barrel_pct"), 0), p.get("score") or 0),
            reverse=True,
        )
        if not _elite_pool:
            st.markdown(
                "<div style='padding:32px;text-align:center;color:#555;'>"
                "<div style='font-size:28px;margin-bottom:8px;'>💎</div>"
                "<div style='font-size:14px;'>No elite barrel picks today (barrel ≥ 8%).</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            # Pre-compute pitch tags for all elite players before the render loop
            _elite_pitch_tags: dict = {}
            for _ep_pt in _elite_pool:
                _ep_pid_pt = _ep_pt.get("player_id")
                _ep_ctx_pt = _pm_ctxs.get(_ep_pid_pt, {})
                _elite_pitch_tags[_ep_pid_pt] = _pitch_attack_tags(_ep_ctx_pt, _ep_pt, max_tags=2)

            _el_goat  = sum(1 for p in _elite_pool if _pf(p.get("barrel_pct"), 0) >= 15)
            _el_elite = sum(1 for p in _elite_pool if 12 <= _pf(p.get("barrel_pct"), 0) < 15)
            _el_power = sum(1 for p in _elite_pool if 10 <= _pf(p.get("barrel_pct"), 0) < 12)
            _el_solid = sum(1 for p in _elite_pool if 8  <= _pf(p.get("barrel_pct"), 0) < 10)
            st.markdown(
                f"<div style='display:flex;gap:16px;padding:8px 0 12px;"
                f"border-bottom:1px solid #1e1e40;margin-bottom:12px;flex-wrap:wrap;align-items:center;'>"
                f"<span style='color:#FF4500;font-weight:700;font-size:12px;'>🐐 GOAT {_el_goat}</span>"
                f"<span style='color:#FFD700;font-weight:700;font-size:12px;'>💎 ELITE {_el_elite}</span>"
                f"<span style='color:#4ade80;font-weight:700;font-size:12px;'>⚡ POWER {_el_power}</span>"
                f"<span style='color:#86efac;font-weight:700;font-size:12px;'>✅ SOLID {_el_solid}</span>"
                f"<span style='color:#444;font-size:11px;'>· barrel ≥ 8% · BRL / HH% / xSLG / Pull / FB%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── 2-column tactical intelligence grid ──────────────────────────
            _ELITE_COLS  = 2
            _el_ranked   = list(enumerate(_elite_pool, start=1))
            _el_grid_rows = [_el_ranked[i:i + _ELITE_COLS]
                             for i in range(0, len(_el_ranked), _ELITE_COLS)]

            for _el_row_data in _el_grid_rows:
                _el_row_cols = st.columns(len(_el_row_data))
                for _el_ci, (_el_rank, _ep) in enumerate(_el_row_data):
                    with _el_row_cols[_el_ci]:
                        _ep_pid   = _ep.get("player_id") or _ep.get("player_name", "")
                        _ep_ctx   = _pm_ctxs.get(_ep_pid, {})
                        _ep_ptags = _elite_pitch_tags.get(_ep_pid, [])
                        _ep_status_html, _ep_is_live = _status_cache.get(_ep_pid, ("", False))
                        _ep_brl   = _pf(_ep.get("barrel_pct"), 0.0)
                        _ep_conf  = "✅" if _ep.get("lineup_spot") is not None else "⏳"
                        if _ep_brl >= 15:   _ep_grade = "GOAT"
                        elif _ep_brl >= 12: _ep_grade = "ELITE"
                        elif _ep_brl >= 10: _ep_grade = "POWER"
                        else:               _ep_grade = "SOLID"

                        if st.button(
                            f"{_ep_conf} {_ep['player_name']} — {_ep_grade}",
                            key=f"oi_elite_{_el_rank}",
                            use_container_width=True,
                        ):
                            st.session_state["show_modal"] = _ep
                            st.session_state["modal_source_tab"] = "Top Targets"
                            st.rerun()

                        _ep_opt_sel = _ep.get("player_name") in _optimizer_selected_names
                        _ec_fp = (
                            "ec", _slate_ts, _ep_pid,
                            _ep_is_live, _optimizer_on, _ep_opt_sel,
                            hash(_ep_status_html) if _ep_status_html else 0,
                        )
                        st.markdown(
                            _card_html(_ec_fp, lambda: _elite_card_html(
                                _ep, _ep_ctx,
                                pitch_tags=_ep_ptags,
                                is_live=_ep_is_live,
                                status_html=_ep_status_html,
                                opt_active=_optimizer_on,
                                opt_selected=_ep_opt_sel,
                            )),
                            unsafe_allow_html=True,
                        )
                        _render_pitch_mix_expander(_ep_ctx, _ep, f"elite_{_el_rank}",
                                                   expanded=st.session_state.get("main_pitch_mix_expanded", False),
                                                   slate_ts=_slate_ts)

    # ── TAB 3: MATCHUP EDGE ───────────────────────────────────────────────────
    with tab_edge:
        if not ranked:
            st.info("No qualified picks — load data first.")
        else:
            from clients.pitch_mix import (
                pitch_label as _me_pitch_label,
                pitch_color as _me_pitch_color,
            )
            # _me_ctxs and _me_ck are pre-loaded before st.tabs() above

            _me_mod_active = st.session_state.get("tac_min_matchup_pct", 75) > 75
            _me_hvy_active = st.session_state.get("tac_min_hvy_score", 0) > 0
            _me_filter_note = ""
            if _me_mod_active or _me_hvy_active:
                _me_filter_parts = []
                if _me_mod_active:
                    _me_filter_parts.append(f"Modifier ≥ {st.session_state.get('tac_min_matchup_pct', 75)}%")
                if _me_hvy_active:
                    _me_filter_parts.append(f"HVY ≥ {st.session_state.get('tac_min_hvy_score', 0)}")
                _me_filter_note = (
                    f" <span style='background:#1a0d00;color:#f97316;font-size:10px;"
                    f"padding:1px 6px;border-radius:3px;border:1px solid #3a1a00;'>"
                    f"🎯 {' · '.join(_me_filter_parts)} active</span>"
                )
            _me_hdr_col, _me_ref_col = st.columns([4, 1])
            with _me_hdr_col:
                st.markdown(
                    "<span style='color:#a78bfa;font-size:13px;font-weight:700;letter-spacing:1px;'>"
                    "PITCH MATCHUP INTELLIGENCE</span>"
                    "<span style='color:#555;font-size:11px;margin-left:12px;'>"
                    "sorted by HVY modifier · tactical exploration · ranked picks only</span>"
                    + _me_filter_note,
                    unsafe_allow_html=True,
                )
            with _me_ref_col:
                if st.button("🔄 Refresh", key="me_refresh"):
                    st.session_state.pop(_me_ck, None)
                    st.rerun()

            def _me_hvy_key(p):
                # Default 0.0: players with no pitch context loaded sink to the bottom
                # instead of appearing as false-NEUTRAL (1.0) in the sort order.
                return _me_ctxs.get(p.get("player_id"), {}).get("hvy_modifier", 0.0)

            # Apply HVY modifier filter from Tactical Command Center
            _me_mod_min = st.session_state.get("tac_min_matchup_pct", 75) / 100.0

            def _me_pitch_badge(pr, label_fn, color_fn):
                """Render one pitch pill with usage%, optional whiff%, optional velo."""
                pt    = pr.get("pitch_type", "")
                usage = pr.get("pitch_usage") or 0.0
                whiff = pr.get("whiff_pct")
                speed = pr.get("avg_speed")
                stats = f"{usage:.0f}%"
                if whiff is not None:
                    stats += f" · whiff {whiff:.0f}%"
                if speed is not None:
                    stats += f" · {speed:.1f}mph"
                return (
                    "<span style='background:#1a1a2e;border:1px solid #333;border-radius:4px;"
                    f"padding:2px 6px;font-size:10px;color:{color_fn(pt)};'>"
                    f"{label_fn(pt)} {stats}</span>"
                )

            _me_sorted = sorted(_tac_ranked, key=_me_hvy_key, reverse=True)
            if _me_mod_min > 0.75:
                _me_sorted = [
                    _mp for _mp in _me_sorted
                    if _me_ctxs.get(_mp.get("player_id"), {}).get("hvy_modifier", 1.0) >= _me_mod_min
                ]

            # Page size — default 25 to prevent large DOM on mobile
            _me_n_total = len(_me_sorted)
            _me_pg_opts = [25, 50, _me_n_total] if _me_n_total > 50 else ([25, _me_n_total] if _me_n_total > 25 else [_me_n_total])
            _me_pg_opts = sorted(set(_me_pg_opts))
            _me_pg_raw  = st.session_state.get("me_page_size", _me_pg_opts[0])
            _me_pg_idx  = _me_pg_opts.index(_me_pg_raw) if _me_pg_raw in _me_pg_opts else 0
            _me_pg_cols = st.columns([3, 1])
            with _me_pg_cols[0]:
                if _me_n_total > _me_pg_opts[0]:
                    st.caption(f"Showing top {min(st.session_state.get('me_page_size', _me_pg_opts[0]), _me_n_total)} of {_me_n_total} picks")
            with _me_pg_cols[1]:
                _me_page_size = st.selectbox(
                    "Show", options=_me_pg_opts,
                    index=_me_pg_idx,
                    format_func=lambda x: "All" if x == _me_n_total else str(x),
                    key="me_page_size",
                    label_visibility="collapsed",
                )
            _me_sorted_page = _me_sorted[:_me_page_size]

            for _mi, _mp in enumerate(_me_sorted_page):
                _mp_pid   = _mp.get("player_id")
                _mp_ctx   = _me_ctxs.get(_mp_pid, {})
                _mp_mod   = _mp_ctx.get("hvy_modifier", 1.0)
                _mp_name  = _mp.get("player_name", "")
                _mp_team  = _mp.get("team", "")
                _mp_opp   = _mp.get("opponent", "")
                _mp_pit   = _mp.get("pitcher_name", "TBD")
                _mp_ev    = _mp.get("ev_pct")
                _mp_edge  = _mp.get("edge_pct")
                _mp_model = _mp.get("model_prob", 0) * 100
                _mp_odds  = _mp.get("best_american")
                _mp_brl   = _pf(_mp.get("barrel_pct"), 0.0)
                _mp_url   = _fanduel_url(_mp_name)
                _mp_photo = _player_photo_html(_mp_pid, size=40)
                _mp_status_html, _mp_is_live = _status_cache.get(
                    _mp_pid or _mp.get("player_name", ""), ("", False))
                _mp_hand  = _mp.get("pitcher_hand", "")
                _mp_hand_lbl = f" ({'RHP' if _mp_hand == 'R' else 'LHP'})" if _mp_hand else ""
                _mp_pitch_mix = _mp_ctx.get("pitch_mix", {})
                _mp_pitch_rows = _mp_pitch_mix.get("pitch_rows", _mp_ctx.get("pitch_rows", []))
                _mp_data_year  = _mp_ctx.get("data_year", config.CURRENT_SEASON)
                _mp_prior_note = (f" <span style='color:#888;font-size:9px;'>({_mp_data_year} data)</span>"
                                  if _mp_data_year != config.CURRENT_SEASON else "")
                _mp_pit_lbl = _pitcher_label(_mp_pit, _mp.get("pitcher_factor", 1.0), _mp.get("platoon_factor", 1.0))

                if _mp_mod >= 1.20:
                    _mp_lbl = "ELITE MISMATCH"; _mp_lbl_col = "#FFD700"; _mp_bg = "#1a1500"; _mp_border = "#665500"
                elif _mp_mod >= 1.05:
                    _mp_lbl = "FAVORABLE"; _mp_lbl_col = "#4ade80"; _mp_bg = "#0a150a"; _mp_border = "#224422"
                elif _mp_mod >= 0.95:
                    _mp_lbl = "NEUTRAL"; _mp_lbl_col = "#888"; _mp_bg = "#0d0d18"; _mp_border = "#252540"
                elif _mp_mod >= 0.80:
                    _mp_lbl = "UNFAVORABLE"; _mp_lbl_col = "#f87171"; _mp_bg = "#1a0a0a"; _mp_border = "#442222"
                else:
                    _mp_lbl = "AVOID"; _mp_lbl_col = "#dc2626"; _mp_bg = "#1f0505"; _mp_border = "#660000"

                _mp_mod_bar_pct = int(min(100, max(0, (_mp_mod - 0.70) / 0.70 * 100)))
                _mp_mod_bar = (
                    f"<div style='background:#1a1a1a;border-radius:3px;height:3px;margin:5px 0 3px;'>"
                    f"<div style='background:{_mp_lbl_col};width:{_mp_mod_bar_pct}%;"
                    f"height:3px;border-radius:3px;'></div></div>"
                )
                _mp_ev_col      = "#4ade80" if (_mp_ev is not None and _mp_ev >= 0) else "#f87171" if _mp_ev is not None else "#64748b"
                _mp_ev_display  = f"{_mp_ev:+.1f}%" if _mp_ev is not None else "—"
                _mp_edge_display = f"{_mp_edge:+.1f}%" if _mp_edge is not None else "—"
                _mp_edge_col    = _edge_col(_mp_edge) if _mp_edge is not None else "#64748b"
                _mp_brl_col  = "#4ade80" if _mp_brl >= 8 else "#f0f0f0"
                _mp_tier     = _mp.get("confidence_tier", "C")
                _mp_tier_col = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_mp_tier, "#888")

                if st.button(
                    f"{_mp_name} — {_mp_lbl}",
                    key=f"oi_edge_{_mi}",
                    use_container_width=True,
                ):
                    st.session_state["show_modal"] = _mp
                    st.session_state["modal_source_tab"] = "Matchup Edge"
                    st.rerun()

                _mp_wf   = float(_mp.get("weather_factor", 1.0) or 1.0)
                _mp_wsum = _weather_summary(_mp)
                if _mp_wsum and abs(_mp_wf - 1.0) >= 0.04:
                    _mp_wc = "#4ade80" if _mp_wf >= 1.08 else "#f87171" if _mp_wf <= 0.93 else "#888"
                    _mp_weather_frag = (
                        f"<span style='font-size:9px;color:{_mp_wc};margin-left:5px;'>🌤 {_mp_wsum}</span>")
                else:
                    _mp_weather_frag = ""

                # Fingerprint-cached card HTML — cache miss on live status, mod, or pitch content change.
                # Hash pitch badge content (type + usage + whiff) so any stat change triggers rebuild.
                _me_pitch_fp = hash(tuple(
                    (pr.get("pitch_type", ""), round(pr.get("pitch_usage") or 0, 1),
                     round(pr.get("whiff_pct") or -1, 1))
                    for pr in _mp_pitch_rows
                ))
                _me_fp = (
                    "me", _slate_ts, _mp_pid, _mp_is_live,
                    round(_mp_mod, 2), _me_pitch_fp,
                    hash(_mp_status_html) if _mp_status_html else 0,
                )
                def _build_me_card_html(
                    _bg=_mp_bg, _border=_mp_border, _lbl_col=_mp_lbl_col,
                    _photo=_mp_photo, _team=_mp_team, _opp=_mp_opp,
                    _pit_lbl=_mp_pit_lbl, _hand_lbl=_mp_hand_lbl,
                    _prior=_mp_prior_note, _wfrag=_mp_weather_frag,
                    _shtml=_mp_status_html, _mod=_mp_mod, _lbl=_mp_lbl,
                    _mbar=_mp_mod_bar, _model=_mp_model, _brl_col=_mp_brl_col,
                    _brl=_mp_brl, _tier_col=_mp_tier_col, _tier=_mp_tier,
                    _ev_col=_mp_ev_col, _ev_disp=_mp_ev_display,
                    _edge_col_val=_mp_edge_col, _edge_disp=_mp_edge_display,
                    _url=_mp_url, _odds=_mp_odds, _pitch_rows=_mp_pitch_rows,
                ):
                    return (
                        f"<div style='background:{_bg};border:1px solid {_border};"
                        f"border-left:3px solid {_lbl_col};border-radius:10px;"
                        f"padding:12px 16px;margin-bottom:12px;position:relative;overflow:hidden;'>"
                        f"<div style='position:absolute;top:0;left:0;right:0;height:2px;"
                        f"background:linear-gradient(90deg,transparent,{_lbl_col},transparent);opacity:0.55;'></div>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        f"<div style='display:flex;align-items:center;gap:8px;'>{_photo}"
                        f"<div><div style='font-size:12px;color:#888;'>"
                        f"{_team} vs {_opp} · {_pit_lbl}{_hand_lbl}{_prior}{_wfrag}</div>"
                        + (f"<div style='font-size:11px;margin-top:2px;'>{_shtml}</div>" if _shtml else "")
                        + f"</div></div>"
                        f"<div style='text-align:right;'>"
                        f"<div style='font-size:20px;font-weight:900;color:{_lbl_col};'>{_mod:.2f}×</div>"
                        f"<div style='font-size:10px;color:{_lbl_col};font-weight:700;'>MATCHUP: {_lbl}</div>"
                        f"</div></div>"
                        + _mbar
                        + f"<div style='display:flex;gap:2px;margin-top:6px;'>"
                        f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:5px;padding:4px 2px;'>"
                        f"<div style='font-size:12px;font-weight:700;color:#a78bfa;'>{_model:.0f}%</div>"
                        f"<div style='font-size:8px;color:#4a4a6a;'>MODEL</div></div>"
                        f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:5px;padding:4px 2px;'>"
                        f"<div style='font-size:12px;font-weight:700;color:{_brl_col};'>{_brl:.1f}%</div>"
                        f"<div style='font-size:8px;color:#4a4a6a;'>BARREL</div></div>"
                        f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:5px;padding:4px 2px;"
                        f"border-right:1px solid #1e1e35;'>"
                        f"<div style='font-size:12px;font-weight:700;color:{_tier_col};'>{_tier}</div>"
                        f"<div style='font-size:8px;color:#4a4a6a;'>QUANT</div></div>"
                        f"<div style='flex:1;text-align:center;background:#0c0c1e;border-radius:5px;padding:4px 2px;'>"
                        f"<div style='font-size:14px;font-weight:700;color:{_ev_col};'>{_ev_disp}</div>"
                        f"<div style='font-size:8px;color:#55558a;'>EV</div></div>"
                        f"<div style='flex:1;text-align:center;background:#0c0c1e;border-radius:5px;padding:4px 2px;'>"
                        f"<div style='font-size:14px;font-weight:700;color:{_edge_col_val};'>{_edge_disp}</div>"
                        f"<div style='font-size:8px;color:#55558a;'>EDGE</div></div>"
                        f"<div style='flex:1;text-align:center;background:#0c0c1e;border-radius:5px;padding:4px 2px;'>"
                        f"<a href='{_url}' target='_blank' style='text-decoration:none;'>"
                        f"<div style='font-size:14px;font-weight:700;color:#FF6666;'>{_fmt_american(_odds)}</div>"
                        f"<div style='font-size:8px;color:#55558a;'>ODDS ↗</div></a></div>"
                        f"</div>"
                        + (
                            "<div style='font-size:8px;color:#444;letter-spacing:1px;"
                            "margin-top:8px;margin-bottom:3px;'>ARSENAL</div>"
                            "<div style='display:flex;flex-wrap:wrap;gap:4px;'>"
                            + "".join(
                                _me_pitch_badge(pr, _me_pitch_label, _me_pitch_color)
                                for pr in _pitch_rows[:6]
                            )
                            + "</div>"
                            if _pitch_rows else
                            "<div style='font-size:10px;color:#555;margin-top:6px;'>"
                            "Pitch data loading…</div>"
                        )
                        + f"</div>"
                    )
                st.markdown(_card_html(_me_fp, _build_me_card_html), unsafe_allow_html=True)
                _render_pitch_mix_expander(_me_ctxs.get(_mp_pid, {}), _mp, f"me_{_mi}",
                                           expanded=st.session_state.get("main_pitch_mix_expanded", False),
                                           slate_ts=_slate_ts)

    # ── TAB 4: PORTFOLIO BUILDER ──────────────────────────────────────────────
    with tab_port:
        # ── MAIN Portfolio control bar (Phase 2C) ─────────────────────────────
        _port_preset_opts = [
            ("Moderate",       "moderate",       "Balanced deployment · stable EV distribution · moderate volatility"),
            ("Conservative",   "conservative",   "Exposure-controlled · 15 picks · 3/team cap · barrel ≥ 6%"),
            ("Barrel-Focused", "barrel_focused", "Barrel-weighted aggression · elite-heavy slate · high-upside targeting"),
            ("Relaxed",        "relaxed",        "Wide-net deployment · 30 picks · broad coverage · maximum slate"),
        ]
        _port_active_preset = st.session_state.get("optimizer_preset", "moderate")
        _port_active_entry  = next(
            (e for e in _port_preset_opts if e[1] == _port_active_preset),
            _port_preset_opts[0],
        )
        st.markdown(
            "<div style='font-size:10px;font-weight:700;letter-spacing:1.5px;"
            "color:#555;margin-bottom:6px;'>PORTFOLIO MODE</div>",
            unsafe_allow_html=True,
        )
        _pctl_cols = st.columns(4)
        for _pctl_col, (_pctl_lbl, _pctl_key, _pctl_summ) in zip(_pctl_cols, _port_preset_opts):
            with _pctl_col:
                if st.button(
                    _pctl_lbl,
                    key=f"port_ctrl_preset_{_pctl_key}",
                    type="primary" if _port_active_preset == _pctl_key else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["optimizer_preset"]        = _pctl_key
                    st.session_state["optimizer_preset_select"] = _pctl_key
                    st.rerun()
        st.markdown(
            f"<div style='padding:5px 0 10px;font-size:11px;color:#888;'>"
            f"<span style='color:#a78bfa;font-weight:700;'>Operational Intelligence</span>"
            f" &nbsp;·&nbsp; {_port_active_entry[2]}"
            f"{'&nbsp; · &nbsp;<span style=\"color:#f97316;\">Optimizer off — enable in sidebar</span>' if not _optimizer_on else ''}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<span style='color:#a78bfa;font-size:13px;font-weight:700;letter-spacing:1px;'>"
            "EXPOSURE INTELLIGENCE</span>",
            unsafe_allow_html=True,
        )
        if not _optimizer_on:
            st.info(
                "Portfolio optimizer is off. Enable it in the sidebar to see optimized slate and exposure breakdown.",
                icon="🎯",
            )
            if ranked:
                with st.expander("📊 Raw Exposure (all qualified picks)", expanded=True):
                    _pe_teams = {}
                    for _pp in ranked:
                        _t = (_pp.get("team") or "UNK").upper().strip()
                        _pe_teams[_t] = _pe_teams.get(_t, 0) + 1
                    _pe_total = len(ranked)
                    _pe_rows_html = "".join(
                        f"<div style='display:flex;justify-content:space-between;align-items:center;"
                        f"padding:3px 0;border-bottom:1px solid #1a1a1a;'>"
                        f"<span style='font-size:12px;color:#f0f0f0;font-weight:700;'>{t}</span>"
                        f"<span style='font-size:12px;color:#a78bfa;'>{n} · {n/_pe_total*100:.0f}%</span>"
                        f"</div>"
                        for t, n in sorted(_pe_teams.items(), key=lambda x: -x[1])[:10]
                    )
                    st.markdown(
                        f"<div style='background:#0d0d20;border:1px solid #1e1e40;"
                        f"border-radius:8px;padding:10px 14px;'>{_pe_rows_html}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            _opt_res  = _optimizer_result
            if not _opt_res:
                st.warning("Optimizer result not available — load today's picks first.")
            else:
                _opt_sel    = _opt_res.get("selected", [])
                _opt_rej    = _opt_res.get("cap_rejected", [])
                _opt_qf     = _opt_res.get("quality_filtered", [])
                _opt_n_in   = _opt_res.get("n_input", 0)
                _opt_n_sel  = _opt_res.get("n_selected", 0)
                _opt_stats  = _opt_res.get("stats", {})
                _opt_raw_s  = _opt_stats.get("raw", {})
                _opt_optd_s = _opt_stats.get("optimized", {})

                _pb_c1, _pb_c2, _pb_c3, _pb_c4 = st.columns(4)
                with _pb_c1:
                    st.metric("Input Picks", _opt_n_in)
                with _pb_c2:
                    st.metric("Selected", _opt_n_sel)
                with _pb_c3:
                    _ba_raw = _opt_raw_s.get("avg_barrel", 0)
                    _ba_opt = _opt_optd_s.get("avg_barrel", 0)
                    st.metric("Avg Barrel", f"{_ba_opt:.1f}%", delta=f"{_ba_opt - _ba_raw:+.1f}pp")
                with _pb_c4:
                    _ea_raw = _opt_raw_s.get("avg_ev_pct", 0)
                    _ea_opt = _opt_optd_s.get("avg_ev_pct", 0)
                    st.metric("Avg EV", f"{_ea_opt:.1f}%", delta=f"{_ea_opt - _ea_raw:+.1f}pp")

                if _opt_sel:
                    st.markdown(
                        "<div style='margin:14px 0 6px;font-size:12px;font-weight:700;"
                        "color:#4ade80;letter-spacing:1px;'>SELECTED SLATE</div>",
                        unsafe_allow_html=True,
                    )
                    # ── Phase 2D: Reason tag summary (lightweight, no new compute) ──
                    _rt_strong_brl  = sum(1 for _rp in _opt_sel if _pf(_rp.get("barrel_pct"), 0.0) >= 10)
                    _rt_brl_upside  = sum(1 for _rp in _opt_sel if 8 <= _pf(_rp.get("barrel_pct"), 0.0) < 10)
                    _rt_elite_ev    = sum(1 for _rp in _opt_sel if (_rp.get("ev_pct") or 0) >= 5)
                    _rt_tact_up     = sum(1 for _rp in _opt_sel if (
                        _rp.get("hvy_modifier") and _pf(_rp.get("hvy_modifier"), 1.0) >= 1.10
                    ))
                    _rt_steam       = sum(1 for _rp in _opt_sel if _rp.get("player_name", "") in _steam_names)
                    _rt_chips = []
                    if _rt_strong_brl:
                        _rt_chips.append(
                            f"<span style='background:#14532d;color:#4ade80;font-size:10px;"
                            f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                            f"Strong Barrel &nbsp;×{_rt_strong_brl}</span>"
                        )
                    if _rt_brl_upside:
                        _rt_chips.append(
                            f"<span style='background:#052e16;color:#86efac;font-size:10px;"
                            f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                            f"Barrel Upside &nbsp;×{_rt_brl_upside}</span>"
                        )
                    if _rt_elite_ev:
                        _rt_chips.append(
                            f"<span style='background:#1e3a5f;color:#60a5fa;font-size:10px;"
                            f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                            f"Elite EV &nbsp;×{_rt_elite_ev}</span>"
                        )
                    if _rt_tact_up:
                        _rt_chips.append(
                            f"<span style='background:#431407;color:#fb923c;font-size:10px;"
                            f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                            f"Tactical Upside &nbsp;×{_rt_tact_up}</span>"
                        )
                    if _rt_steam:
                        _rt_chips.append(
                            f"<span style='background:#1a1a00;color:#facc15;font-size:10px;"
                            f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                            f"Steam Move &nbsp;×{_rt_steam}</span>"
                        )
                    if not _rt_chips:
                        _rt_chips.append(
                            f"<span style='background:#1e1e30;color:#a78bfa;font-size:10px;"
                            f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                            f"Stable Deployment</span>"
                        )
                    st.markdown(
                        f"<div style='display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;'>"
                        f"{''.join(_rt_chips)}</div>",
                        unsafe_allow_html=True,
                    )
                    _render_qualified_table(_opt_sel, scale, min_ev, min_edge, _steam_names, "port_sel")

                st.markdown(
                    "<div style='margin:16px 0 8px;font-size:12px;font-weight:700;"
                    "color:#a78bfa;letter-spacing:1px;'>EXPOSURE BREAKDOWN</div>",
                    unsafe_allow_html=True,
                )
                _exp_c1, _exp_c2, _exp_c3 = st.columns(3)
                _exp_total = len(_opt_sel) or 1

                with _exp_c1:
                    _exp_teams = {}
                    for _pp in _opt_sel:
                        _t = (_pp.get("team") or "UNK").upper().strip()
                        _exp_teams[_t] = _exp_teams.get(_t, 0) + 1
                    _exp_team_html = "".join(
                        f"<div style='display:flex;justify-content:space-between;padding:3px 0;"
                        f"border-bottom:1px solid #1a1a1a;'>"
                        f"<span style='font-size:11px;color:#f0f0f0;font-weight:700;'>{t}</span>"
                        f"<span style='font-size:11px;color:#a78bfa;'>{n} · {n/_exp_total*100:.0f}%</span>"
                        f"</div>"
                        for t, n in sorted(_exp_teams.items(), key=lambda x: -x[1])
                    )
                    st.markdown(
                        f"<div style='background:#0d0d20;border:1px solid #1e1e40;"
                        f"border-radius:8px;padding:10px 14px;'>"
                        f"<div style='font-size:10px;color:#555;font-weight:700;"
                        f"letter-spacing:1px;margin-bottom:6px;'>TEAM</div>"
                        f"{_exp_team_html}</div>",
                        unsafe_allow_html=True,
                    )

                with _exp_c2:
                    from portfolio.optimizer import _odds_tier as _pb_odds_tier
                    _exp_odds = {}
                    for _pp in _opt_sel:
                        _ot = _pb_odds_tier(_pp)
                        _exp_odds[_ot] = _exp_odds.get(_ot, 0) + 1
                    _exp_odds_html = "".join(
                        f"<div style='display:flex;justify-content:space-between;padding:3px 0;"
                        f"border-bottom:1px solid #1a1a1a;'>"
                        f"<span style='font-size:11px;color:#f0f0f0;'>{ot}</span>"
                        f"<span style='font-size:11px;color:#a78bfa;'>{n} · {n/_exp_total*100:.0f}%</span>"
                        f"</div>"
                        for ot, n in sorted(_exp_odds.items(), key=lambda x: -x[1])
                    )
                    st.markdown(
                        f"<div style='background:#0d0d20;border:1px solid #1e1e40;"
                        f"border-radius:8px;padding:10px 14px;'>"
                        f"<div style='font-size:10px;color:#555;font-weight:700;"
                        f"letter-spacing:1px;margin-bottom:6px;'>ODDS TIER</div>"
                        f"{_exp_odds_html}</div>",
                        unsafe_allow_html=True,
                    )

                with _exp_c3:
                    def _pb_brl_tier(p):
                        b = _pf(p.get("barrel_pct"), 0.0)
                        if b >= 12: return "12%+"
                        if b >= 10: return "10-12%"
                        if b >= 8:  return "8-10%"
                        if b >= 6:  return "6-8%"
                        return "<6%"
                    _exp_brl = {}
                    for _pp in _opt_sel:
                        _bt = _pb_brl_tier(_pp)
                        _exp_brl[_bt] = _exp_brl.get(_bt, 0) + 1
                    _brl_order = ["12%+", "10-12%", "8-10%", "6-8%", "<6%"]
                    _exp_brl_html = "".join(
                        f"<div style='display:flex;justify-content:space-between;padding:3px 0;"
                        f"border-bottom:1px solid #1a1a1a;'>"
                        f"<span style='font-size:11px;color:#f0f0f0;'>{bt}</span>"
                        f"<span style='font-size:11px;color:"
                        f"{'#4ade80' if bt in ('12%+', '10-12%') else '#a78bfa'};'>"
                        f"{_exp_brl.get(bt, 0)} · {_exp_brl.get(bt, 0)/_exp_total*100:.0f}%</span>"
                        f"</div>"
                        for bt in _brl_order if bt in _exp_brl
                    )
                    st.markdown(
                        f"<div style='background:#0d0d20;border:1px solid #1e1e40;"
                        f"border-radius:8px;padding:10px 14px;'>"
                        f"<div style='font-size:10px;color:#555;font-weight:700;"
                        f"letter-spacing:1px;margin-bottom:6px;'>BARREL TIER</div>"
                        f"{_exp_brl_html}</div>",
                        unsafe_allow_html=True,
                    )

                if _opt_rej or _opt_qf:
                    with st.expander(
                        f"🚫 Rejected ({len(_opt_rej)} cap · {len(_opt_qf)} quality-filtered)",
                        expanded=False,
                    ):
                        for _rr in (_opt_rej + _opt_qf)[:30]:
                            _rr_name   = _rr.get("player_name", "")
                            _rr_team   = _rr.get("team", "")
                            _rr_reason = _rr.get("_reject_reason", "") or "—"
                            _rr_brl    = _pf(_rr.get("barrel_pct"), 0.0)
                            _rr_ev     = _rr.get("ev_pct", 0)
                            # Reason badge color — capacity vs quality rejection
                            _rr_is_cap = any(
                                kw in _rr_reason for kw in ("cap", "tier")
                            )
                            _rr_bg  = "#1e1040" if _rr_is_cap else "#2d1200"
                            _rr_clr = "#818cf8" if _rr_is_cap else "#f97316"
                            _rr_lbl = _rr_reason.split("(")[0].strip().title()
                            st.markdown(
                                f"<div style='display:flex;justify-content:space-between;"
                                f"align-items:center;padding:4px 0;border-bottom:1px solid #1a1a1a;'>"
                                f"<span style='font-size:11px;color:#888;min-width:140px;'>{_rr_team} · {_rr_name}</span>"
                                f"<span style='font-size:10px;font-weight:700;padding:2px 6px;"
                                f"border-radius:3px;background:{_rr_bg};color:{_rr_clr};'>{_rr_lbl}</span>"
                                f"<span style='font-size:11px;color:#555;'>"
                                f"BRL {_rr_brl:.1f}% · EV {_rr_ev:+.1f}%</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )


    # -- TAB 5: FULL SLATE --------------------------------------------------------
    with tab_fs:
        # TODO Phase 2 Full Slate rebuild anchors:
        # - game command module
        # - target pitcher zone
        # - player target rows
        # - live conditions panel
        # - matchup navigation strip
        # - return-to-top behavior
        # ── Mode selector: visibility ≠ qualification ────────────────────────
        # All Players: all batters organized by game; filters highlight, do not remove.
        # Qualified: sidebar EV/Edge + TCC profile filters applied.
        # Elite Targets: barrel ≥ 8% regardless of market qualification.
        _fs_mode_opts = ["All Players", "Qualified", "Elite Targets"]
        _fs_mode = st.radio(
            "slate_mode",
            options=_fs_mode_opts,
            index=_fs_mode_opts.index(
                st.session_state.get("fs_mode_sel", "All Players")
            ),
            horizontal=True,
            key="fs_mode_sel",
            label_visibility="collapsed",
        )

        _fs_qual_names     = {p.get("player_name") for p in ranked}
        _fs_tac_qual_names = {p.get("player_name") for p in _tac_ranked}

        if _fs_mode == "All Players":
            st.caption(
                "True operational full slate — all playable batters organized by game.  "
                "Filters highlight (✓ QUAL, ★ ELITE) but do not remove players.  "
                "📊 Pitch Mix intelligence available in COMMAND CENTER / TOP TARGETS / MATCHUP EDGE tabs."
            )
            _render_full_slate_all_players(
                all_players,
                _fs_qual_names,
                _fs_tac_qual_names,
                _steam_names,
                _status_cache,
                _urgency_cache,
                slate_ts=_slate_ts,
            )

        elif _fs_mode == "Qualified":
            if not _tac_ranked:
                st.info(
                    "No players eligible after current TCC + sidebar filters. "
                    "Try loosening the Tactical Command Center thresholds above, "
                    f"or slide sidebar EV/Edge below current EV ≥ {min_ev:.1f}% / Edge ≥ {min_edge:.1f}%."
                )
            else:
                _fs_sorted = sorted(
                    _tac_ranked,
                    key=lambda p: (
                        (p.get("ev_pct",    0) or 0) * 0.40 +
                        (p.get("edge_pct",  0) or 0) * 0.35 +
                        (p.get("confidence",0) or 0) * 0.25
                    ),
                    reverse=True,
                )
                st.caption(
                    f"{len(_fs_sorted)} qualified players · composite score EV×0.40 + "
                    f"Edge×0.35 + Conf×0.25 · TCC + sidebar filters applied · "
                    "📊 Pitch Mix in COMMAND CENTER / TOP TARGETS / MATCHUP EDGE tabs"
                )
                _render_qualified_table(_fs_sorted, scale, min_ev, min_edge, _steam_names, "fs_qual")

        else:  # Elite Targets
            _fs_elite = sorted(
                [p for p in all_players if _pf(p.get("barrel_pct"), 0) >= 8.0],
                key=lambda p: _pf(p.get("barrel_pct"), 0),
                reverse=True,
            )
            if not _fs_elite:
                st.info("No elite barrel (≥ 8%) batters in today's slate.")
            else:
                st.caption(
                    f"{len(_fs_elite)} elite barrel players (≥ 8%) · all playable regardless of market · "
                    "sorted by barrel rate descending"
                )
                _render_full_slate_all_players(
                    _fs_elite,
                    _fs_qual_names,
                    _fs_tac_qual_names,
                    _steam_names,
                    _status_cache,
                    _urgency_cache,
                    slate_ts=_slate_ts,
                )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TAB 2 — PARLAYS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# TAB — HITS
# ═══════════════════════════════════════════════════════════════════════════════
def tab_hits(data: dict):
    all_players = data.get("all_players", [])

    st.markdown(
        "<div style='font-size:22px; font-weight:900; color:#60a5fa; "
        "letter-spacing:2px; margin-bottom:2px;'>🏃 HITS</div>"
        "<div style='font-size:12px; color:#888; margin-bottom:12px;'>"
        "Contact quality index — xBA · Line Drive · Sweet Spot · Hard Hit · K-Factor · PA Opportunity</div>",
        unsafe_allow_html=True,
    )

    with st.expander("⚙️ Hit Thresholds", expanded=False):
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            xba_min = st.slider("Min xBA",          0.220, 0.340, 0.260, 0.005, key="hit_xba")
            ld_min  = st.slider("Min LD%",           12.0,  30.0,  20.0,  0.5,   key="hit_ld")
        with hc2:
            ss_min  = st.slider("Min Sweet Spot%",   20.0,  45.0,  28.0,  0.5,   key="hit_ss")
            hh_min  = st.slider("Min Hard Hit%",     25.0,  55.0,  35.0,  0.5,   key="hit_hh")
        with hc3:
            kf_min  = st.slider("Min K-Factor",      0.75,  1.15,  0.90,  0.01,  key="hit_kf")
            pa_min  = st.slider("Min Exp PA",         2.0,   5.0,   3.0,  0.1,   key="hit_pa")

    def _hit_metrics(p):
        xba = _pf(p.get("xba"), 0.0)
        ld  = _pf(p.get("ld_pct"))
        ss  = _pf(p.get("sweet_spot_pct"))
        hh  = _pf(p.get("hard_hit"))
        kf  = float(p.get("k_factor") or 1.0)
        pa  = float(p.get("expected_pa") or 0.0)
        return xba, ld, ss, hh, kf, pa

    def _hit_score(p):
        xba, ld, ss, hh, kf, pa = _hit_metrics(p)
        def _n(val, thr, scale):
            return min(max((val - thr) / scale + 0.5, 0.0), 1.0)
        # xBA carries 2x weight — it's the most direct hit predictor
        s = (_n(xba, xba_min, 0.05) * 2.0 +
             _n(ld,  ld_min,  5.0)         +
             _n(ss,  ss_min,  8.0)         +
             _n(hh,  hh_min,  10.0)        +
             _n(kf,  kf_min,  0.15)        +
             _n(pa,  pa_min,  1.0)) / 7.0
        return round(s * 100, 1)

    def _passes_all(p):
        xba, ld, ss, hh, kf, pa = _hit_metrics(p)
        return (xba >= xba_min and ld >= ld_min and ss >= ss_min
                and hh >= hh_min and kf >= kf_min and pa >= pa_min)

    def _hit_card(entry, key_prefix="hit"):
        p    = entry["player"]
        hsco = entry["hit"]
        xba, ld, ss, hh, kf, pa = _hit_metrics(p)
        name  = p.get("player_name", "Unknown")
        team  = p.get("team", "")
        opp   = p.get("opponent", "")
        pit_n = p.get("pitcher_name", "TBD")
        odds  = p.get("best_american")
        ev    = p.get("ev_pct", 0)
        ev_c  = "#4ade80" if ev > 0 else "#f87171"
        hc    = "#4ade80" if hsco >= 60 else "#f59e0b" if hsco >= 40 else "#f87171"
        _h_edge   = p.get("edge_pct", 0)
        _h_ec     = _edge_col(_h_edge)
        _h_tier   = p.get("confidence_tier", "C")
        _h_tc     = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_h_tier, "#888")
        _h_pit_lbl = _pitcher_label(pit_n, p.get("pitcher_factor", 1.0), p.get("platoon_factor", 1.0))
        _h_hand   = p.get("pitcher_hand", "")
        _h_hand_s = f" ({'RHP' if _h_hand == 'R' else 'LHP' if _h_hand == 'L' else ''})" if _h_hand else ""
        _h_pid = p.get("player_id") or p.get("player_name", "")
        status_html, is_live = _hit_status_cache.get(_h_pid) or _game_status_badge(p)
        border = "#f87171" if is_live else "#1e3a5f"
        status_row = (f"<div style='font-size:11px; margin:2px 0 8px;'>{status_html}</div>"
                      if status_html else "")
        _h_photo  = _player_photo_html(p.get("player_id"), size=44)
        _h_rail_c = "#4ade80" if hsco >= 60 else "#f59e0b" if hsco >= 40 else "#f87171"
        st.markdown(
            f"<div style='background:#0d0d1e; border:1px solid {border}; "
            f"border-left:3px solid {_h_rail_c}; border-radius:10px; "
            f"padding:14px 16px; margin-bottom:14px;'>"
            f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
            f"<div style='display:flex;align-items:center;'>{_h_photo}"
            f"<div style='font-size:15px; font-weight:800; color:#f0f0f0;'>{name}</div></div>"
            f"<div style='font-size:18px; font-weight:900; color:{hc};'>HIT {hsco:.0f}"
            f"<span style='font-size:11px;color:{_h_tc};font-weight:700;margin-left:8px;'>{_h_tier}-Tier</span></div>"
            f"</div>"
            f"<div style='font-size:12px; color:#888; margin:2px 0 4px;'>"
            f"{team} vs {opp} &nbsp;·&nbsp; vs {_h_pit_lbl}{_h_hand_s}</div>"
            f"{status_row}"
            f"<div style='display:grid; grid-template-columns:repeat(3,1fr); gap:6px; font-size:11px;'>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>xBA</div>{_badge(xba, xba_min, f'{xba:.3f}')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>LD%</div>{_badge(ld, ld_min, f'{ld:.1f}%')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>Sweet%</div>{_badge(ss, ss_min, f'{ss:.1f}%')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>Hard Hit</div>{_badge(hh, hh_min, f'{hh:.1f}%')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>K-Factor</div>{_badge(kf, kf_min, f'{kf:.2f}')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>Exp PA</div>{_badge(pa, pa_min, f'{pa:.1f}')}</div>"
            f"</div>"
            + (f"<div style='margin-top:8px; font-size:12px; display:flex; gap:12px; flex-wrap:wrap;'>"
               f"<span style='color:#60a5fa; font-weight:700;'>{_fmt_american(odds)}</span>"
               f"<span style='color:#a78bfa;'>MDL {p.get('model_prob',0)*100:.0f}%</span>"
               f"<span style='color:{ev_c};'>EV {ev:+.1f}%</span>"
               f"<span style='color:{_h_ec};'>Edge {_h_edge:+.1f}%</span>"
               f"</div>" if odds else "")
            + "</div>",
            unsafe_allow_html=True,
        )
        _bc, _fc = st.columns(2)
        with _bc:
            if st.button("ℹ️ Player Info",
                         key=f"{key_prefix}_modal_{p.get('player_id','')}{name[:6]}",
                         use_container_width=True, type="primary"):
                st.session_state["show_modal"] = p
                st.session_state["modal_source_tab"] = "Hits"
                st.session_state["modal_source_section"] = "Hits"
                st.rerun()
        with _fc:
            st.link_button("📲 Open on FanDuel", _fanduel_url(name), use_container_width=True)

    # ── BTS hit-probability (pure contact likelihood, separate from HIT score) ──
    def _hit_prob(p):
        """P(≥1 hit in game) = 1 - (1 - xBA)^expected_pa"""
        xba = _pf(p.get("xba"), 0.0)
        pa  = float(p.get("expected_pa") or 0.0)
        if xba <= 0 or pa <= 0:
            return 0.0
        return round((1.0 - (1.0 - xba) ** pa) * 100.0, 1)

    scored    = sorted(
        [{"player": p, "hit": _hit_score(p), "passes": _passes_all(p),
          "hit_prob": _hit_prob(p)} for p in all_players],
        key=lambda x: x["hit"], reverse=True,
    )
    qualified = [x for x in scored if x["passes"]]
    prime     = [x for x in qualified
                 if x["player"].get("best_american") and x["player"].get("ev_pct", 0) > 0]

    # Pre-build status cache for all players to avoid O(N) badge calls in card render loops
    _hit_status_cache: dict = {}
    for _hsc_entry in scored:
        _hsc_p = _hsc_entry["player"]
        _hsc_pid = _hsc_p.get("player_id") or _hsc_p.get("player_name", "")
        _hit_status_cache[_hsc_pid] = _game_status_badge(_hsc_p)

    # BTS pool: all players with a real xBA and starting lineup spot, ranked by hit probability
    bts_pool  = sorted(
        [x for x in scored if x["hit_prob"] > 0 and x["player"].get("lineup_spot")],
        key=lambda x: x["hit_prob"], reverse=True,
    )

    _hbts, _hq, _hp, _ha, _hpr = st.tabs([
        "🎯 Beat The Streak",
        "📱 Quick Picks",
        f"⚡ Picks ({len(qualified)})",
        f"📊 All ({len(scored)})",
        f"⭐ Prime ({len(prime)})",
    ])

    # ── Beat The Streak tab ──────────────────────────────────────────────────
    with _hbts:
        # Streak tracker
        if "bts_streak" not in st.session_state:
            st.session_state["bts_streak"] = 0
        if "bts_best" not in st.session_state:
            st.session_state["bts_best"] = 0
        streak = st.session_state["bts_streak"]
        best   = st.session_state["bts_best"]

        # Header / streak counter
        streak_c = "#4ade80" if streak >= 10 else "#f59e0b" if streak >= 5 else "#60a5fa"
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#0d1f3c,#0a0a1a); "
            f"border:2px solid #1e3a5f; border-radius:14px; padding:18px 22px; "
            f"margin-bottom:14px; text-align:center;'>"
            f"<div style='font-size:13px; color:#888; letter-spacing:2px; "
            f"text-transform:uppercase;'>🎯 Beat The Streak</div>"
            f"<div style='font-size:48px; font-weight:900; color:{streak_c}; "
            f"line-height:1.1;'>{streak}</div>"
            f"<div style='font-size:12px; color:#666;'>current streak</div>"
            f"<div style='font-size:11px; color:#555; margin-top:4px;'>"
            f"personal best: <b style='color:#888;'>{best}</b> &nbsp;·&nbsp; "
            f"DiMaggio's record: <b style='color:#f59e0b;'>56</b></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        _s1, _s2, _s3 = st.columns(3)
        with _s1:
            if st.button("✅ Both Hit  +1", use_container_width=True,
                         type="primary", key="bts_win"):
                st.session_state["bts_streak"] += 1
                if st.session_state["bts_streak"] > st.session_state["bts_best"]:
                    st.session_state["bts_best"] = st.session_state["bts_streak"]
                st.rerun()
        with _s2:
            if st.button("❌ Missed — Reset", use_container_width=True,
                         key="bts_lose"):
                st.session_state["bts_streak"] = 0
                st.rerun()
        with _s3:
            if st.button("🔄 Reset All", use_container_width=True, key="bts_reset"):
                st.session_state["bts_streak"] = 0
                st.session_state["bts_best"]   = 0
                st.rerun()

        st.divider()

        if not bts_pool:
            st.warning("No players with confirmed lineup spots and Statcast data available yet. "
                       "Check back after lineups post (~3–4 h before first pitch).")
        else:
            pick1 = bts_pool[0]
            pick2 = bts_pool[1] if len(bts_pool) > 1 else None

            p1      = pick1["player"]
            p1_prob = pick1["hit_prob"]
            p1_xba  = _pf(p1.get("xba"), 0.0)
            p1_pa   = float(p1.get("expected_pa") or 0)
            p1_spot = p1.get("lineup_spot") or "--"
            p1_sf   = float(p1.get("streak_factor") or 1.0)

            # ── Pick 1 card ──────────────────────────────────────────────
            pc = "#4ade80" if p1_prob >= 75 else "#f59e0b" if p1_prob >= 60 else "#60a5fa"
            st.markdown(
                f"<div style='background:#0a1628; border:2px solid {pc}; "
                f"border-radius:12px; padding:16px 20px; margin-bottom:10px;'>"
                f"<div style='font-size:11px; color:#888; letter-spacing:1px; "
                f"text-transform:uppercase; margin-bottom:4px;'>🥇 Pick 1</div>"
                f"<div style='display:flex; justify-content:space-between; align-items:baseline;'>"
                f"<div style='font-size:17px; font-weight:900; color:#f0f0f0;'>"
                f"{p1.get('player_name','')}</div>"
                f"<div style='font-size:26px; font-weight:900; color:{pc};'>"
                f"{p1_prob:.1f}%</div>"
                f"</div>"
                f"<div style='font-size:12px; color:#888; margin:2px 0 10px;'>"
                f"{p1.get('team','')} vs {p1.get('opponent','')} "
                f"&nbsp;·&nbsp; vs {p1.get('pitcher_name','TBD')} "
                f"&nbsp;·&nbsp; Spot #{p1_spot}</div>"
                f"<div style='display:grid; grid-template-columns:repeat(4,1fr); "
                f"gap:6px; font-size:11px;'>"
                f"<div class='stat-box-green'>"
                f"<div style='color:#555;'>xBA</div>"
                f"<div style='color:#f0f0f0; font-weight:700;'>{p1_xba:.3f}</div></div>"
                f"<div class='stat-box-green'>"
                f"<div style='color:#555;'>Exp PA</div>"
                f"<div style='color:#f0f0f0; font-weight:700;'>{p1_pa:.1f}</div></div>"
                f"<div class='stat-box-green'>"
                f"<div style='color:#555;'>Hot</div>"
                f"<div style='color:{'#4ade80' if p1_sf >= 1.05 else '#888'}; font-weight:700;'>"
                f"{'🔥' if p1_sf >= 1.10 else '▲' if p1_sf >= 1.05 else '—'}</div></div>"
                f"<div class='stat-box-green'>"
                f"<div style='color:#555;'>K-Fac</div>"
                f"<div style='color:#f0f0f0; font-weight:700;'>"
                f"{float(p1.get('k_factor') or 1.0):.2f}</div></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
            _pb1, _pb2 = st.columns(2)
            with _pb1:
                if st.button("ℹ️ Player Info", key="bts_p1_info",
                             use_container_width=True, type="primary"):
                    st.session_state["show_modal"] = p1
                    st.session_state["modal_source_tab"] = "Hits"
                    st.session_state["modal_source_section"] = "Beat the Shift"
                    st.rerun()
            with _pb2:
                st.link_button("📲 Open on FanDuel", _fanduel_url(p1.get("player_name", "")),
                               use_container_width=True)

            # ── Pick 2 card ──────────────────────────────────────────────
            if pick2:
                p2      = pick2["player"]
                p2_prob = pick2["hit_prob"]
                p2_xba  = _pf(p2.get("xba"), 0.0)
                p2_pa   = float(p2.get("expected_pa") or 0)
                p2_spot = p2.get("lineup_spot") or "--"
                p2_sf   = float(p2.get("streak_factor") or 1.0)
                combo   = round(p1_prob * p2_prob / 100.0, 1)

                pc2 = "#4ade80" if p2_prob >= 75 else "#f59e0b" if p2_prob >= 60 else "#60a5fa"
                st.markdown(
                    f"<div style='background:#0a1628; border:2px solid {pc2}; "
                    f"border-radius:12px; padding:16px 20px; margin-bottom:10px;'>"
                    f"<div style='font-size:11px; color:#888; letter-spacing:1px; "
                    f"text-transform:uppercase; margin-bottom:4px;'>🥈 Pick 2</div>"
                    f"<div style='display:flex; justify-content:space-between; align-items:baseline;'>"
                    f"<div style='font-size:17px; font-weight:900; color:#f0f0f0;'>"
                    f"{p2.get('player_name','')}</div>"
                    f"<div style='font-size:26px; font-weight:900; color:{pc2};'>"
                    f"{p2_prob:.1f}%</div>"
                    f"</div>"
                    f"<div style='font-size:12px; color:#888; margin:2px 0 10px;'>"
                    f"{p2.get('team','')} vs {p2.get('opponent','')} "
                    f"&nbsp;·&nbsp; vs {p2.get('pitcher_name','TBD')} "
                    f"&nbsp;·&nbsp; Spot #{p2_spot}</div>"
                    f"<div style='display:grid; grid-template-columns:repeat(4,1fr); "
                    f"gap:6px; font-size:11px;'>"
                    f"<div class='stat-box-green'>"
                    f"<div style='color:#555;'>xBA</div>"
                    f"<div style='color:#f0f0f0; font-weight:700;'>{p2_xba:.3f}</div></div>"
                    f"<div class='stat-box-green'>"
                    f"<div style='color:#555;'>Exp PA</div>"
                    f"<div style='color:#f0f0f0; font-weight:700;'>{p2_pa:.1f}</div></div>"
                    f"<div class='stat-box-green'>"
                    f"<div style='color:#555;'>Hot</div>"
                    f"<div style='color:{'#4ade80' if p2_sf >= 1.05 else '#888'}; font-weight:700;'>"
                    f"{'🔥' if p2_sf >= 1.10 else '▲' if p2_sf >= 1.05 else '—'}</div></div>"
                    f"<div class='stat-box-green'>"
                    f"<div style='color:#555;'>K-Fac</div>"
                    f"<div style='color:#f0f0f0; font-weight:700;'>"
                    f"{float(p2.get('k_factor') or 1.0):.2f}</div></div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                _pb3, _pb4 = st.columns(2)
                with _pb3:
                    if st.button("ℹ️ Player Info", key="bts_p2_info",
                                 use_container_width=True, type="primary"):
                        st.session_state["show_modal"] = p2
                        st.session_state["modal_source_tab"] = "Hits"
                        st.session_state["modal_source_section"] = "Beat the Shift"
                        st.rerun()
                with _pb4:
                    st.link_button("📲 Open on FanDuel", _fanduel_url(p2.get("player_name", "")),
                                   use_container_width=True)

                # Combined probability banner
                cc = "#4ade80" if combo >= 55 else "#f59e0b" if combo >= 40 else "#f87171"
                st.markdown(
                    f"<div style='background:#111128; border:1px solid #2a2a50; "
                    f"border-radius:8px; padding:10px 16px; margin-top:6px; "
                    f"display:flex; justify-content:space-between; align-items:center;'>"
                    f"<span style='font-size:12px; color:#888;'>Both hit combined probability</span>"
                    f"<span style='font-size:20px; font-weight:900; color:{cc};'>{combo:.1f}%</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.divider()

            # Full ranked BTS leaderboard
            st.markdown("<div style='font-size:13px; color:#888; margin-bottom:6px;'>"
                        "All players ranked by hit probability (confirmed lineup only)</div>",
                        unsafe_allow_html=True)
            bts_rows = []
            for i, entry in enumerate(bts_pool):
                pp = entry["player"]
                _bts_tier   = pp.get("confidence_tier", "")
                _bts_tier_l = {"S": "🌟 S", "A": "✅ A", "B": "🟡 B", "C": "🔴 C"}.get(_bts_tier, _bts_tier)
                bts_rows.append({
                    "#":        i + 1,
                    "Tier":     _bts_tier_l,
                    "Player":   pp.get("player_name", ""),
                    "Team":     pp.get("team", ""),
                    "Opp":      pp.get("opponent", ""),
                    "Spot":     pp.get("lineup_spot") or "--",
                    "Hit%":     entry["hit_prob"],
                    "xBA":      f"{_pf(pp.get('xba'), 0.0):.3f}",
                    "Exp PA":   f"{float(pp.get('expected_pa') or 0):.1f}",
                    "Hot":      "🔥" if float(pp.get("streak_factor") or 1.0) >= 1.10 else
                                "▲"  if float(pp.get("streak_factor") or 1.0) >= 1.05 else "",
                    "Pitcher":  pp.get("pitcher_name", "TBD"),
                })
            _bts_ver = st.session_state.get("_bts_all_ver", 0)
            _bts_sel = st.dataframe(
                pd.DataFrame(bts_rows), hide_index=True, use_container_width=True,
                on_select="rerun", selection_mode="single-row",
                key=f"bts_df_{_bts_ver}",
                column_config={
                    "Hit%": st.column_config.ProgressColumn(
                        "Hit%", min_value=0, max_value=100, format="%.1f%%"),
                },
            )
            _bts_rows = getattr(getattr(_bts_sel, "selection", None), "rows", [])
            if _bts_rows and 0 <= _bts_rows[0] < len(bts_pool):
                st.session_state["_bts_all_ver"] = _bts_ver + 1
                st.session_state["show_modal"] = bts_pool[_bts_rows[0]]["player"]
                st.session_state["modal_source_tab"] = "Hits"
                st.session_state["modal_source_section"] = "Beat the Shift"
                st.rerun()

    with _hq:
        if not qualified:
            st.info("No players meet all Hit thresholds — lower thresholds in the expander above.")
        else:
            for entry in qualified[:3]:
                _hit_card(entry, key_prefix="hq")
            if len(qualified) > 3:
                st.caption(f"Top 3 of {len(qualified)} qualified. See Picks tab for all.")

    with _hp:
        if not qualified:
            st.info("No players meet all Hit thresholds — lower thresholds in the expander above.")
        else:
            _hits_n_total = len(qualified)
            _hits_pg_opts = [25, 50, _hits_n_total] if _hits_n_total > 50 else ([25, _hits_n_total] if _hits_n_total > 25 else [_hits_n_total])
            _hits_pg_opts = sorted(set(_hits_pg_opts))
            _hits_pg_raw  = st.session_state.get("hits_hp_page_size", _hits_pg_opts[0])
            _hits_pg_idx  = _hits_pg_opts.index(_hits_pg_raw) if _hits_pg_raw in _hits_pg_opts else 0
            _hits_cols    = st.columns([3, 1])
            with _hits_cols[0]:
                st.caption(f"Top {min(st.session_state.get('hits_hp_page_size', _hits_pg_opts[0]), _hits_n_total)} of {_hits_n_total} players pass all Hit criteria — ranked by HIT score.")
            with _hits_cols[1]:
                _hits_page_size = st.selectbox(
                    "Show", options=_hits_pg_opts,
                    index=_hits_pg_idx,
                    format_func=lambda x: "All" if x == _hits_n_total else str(x),
                    key="hits_hp_page_size",
                    label_visibility="collapsed",
                )
            for entry in qualified[:_hits_page_size]:
                _hit_card(entry, key_prefix="hp")

    with _ha:
        _ha_ver = st.session_state.get("_hit_all_ver", 0)
        rows = []
        for entry in scored:
            p = entry["player"]
            xba, ld, ss, hh, kf, pa = _hit_metrics(p)
            _ha_tier     = p.get("confidence_tier", "C")
            _ha_tier_lbl = {"S": "🌟 S", "A": "✅ A", "B": "🟡 B", "C": "🔴 C"}.get(_ha_tier, _ha_tier)
            rows.append({
                "Player":   p.get("player_name", ""),
                "Team":     p.get("team", ""),
                "Tier":     _ha_tier_lbl,
                "HIT":      entry["hit"],
                "Passes":   "✅" if entry["passes"] else "",
                "MDL%":     f"{p.get('model_prob', 0)*100:.1f}%",
                "EV%":      f"{p.get('ev_pct', 0):+.1f}%",
                "Edge%":    f"{p.get('edge_pct', 0):+.1f}%",
                "xBA":      f"{xba:.3f}" if xba else "--",
                "LD%":      f"{ld:.1f}%" if ld else "--",
                "Sweet%":   f"{ss:.1f}%" if ss else "--",
                "Hard Hit": f"{hh:.1f}%" if hh else "--",
                "K-Factor": f"{kf:.2f}",
                "Exp PA":   f"{pa:.1f}",
                "Odds":     _fmt_american(p.get("best_american")),
                "Pitcher":  p.get("pitcher_name", ""),
            })
        if rows:
            _ha_sel = st.dataframe(
                pd.DataFrame(rows), hide_index=True, use_container_width=True,
                on_select="rerun", selection_mode="single-row",
                key=f"hit_all_df_{_ha_ver}",
                column_config={
                    "HIT": st.column_config.ProgressColumn(
                        "HIT", min_value=0, max_value=100, format="%.0f"),
                },
            )
            _ha_rows = getattr(getattr(_ha_sel, "selection", None), "rows", [])
            if _ha_rows and 0 <= _ha_rows[0] < len(scored):
                st.session_state["_hit_all_ver"] = _ha_ver + 1
                st.session_state["show_modal"] = scored[_ha_rows[0]]["player"]
                st.session_state["modal_source_tab"] = "Hits"
                st.session_state["modal_source_section"] = "Hits All"
                st.rerun()

    with _hpr:
        if not prime:
            st.info("No prime Hit plays — need qualified players with positive-EV odds.")
        else:
            st.caption(f"{len(prime)} players pass all Hit criteria with positive EV.")
            for entry in prime:
                _hit_card(entry, key_prefix="hpr")

# TAB — JIG
# ═══════════════════════════════════════════════════════════════════════════════
def tab_jig(data: dict):
    _cutoff = st.session_state.get("cutoff_utc_hour")
    _jig_slate_ts = str(st.session_state.get("data_loaded_at", ""))
    all_players_raw = data.get("all_players", [])
    all_players = (
        _gate_data(data, _cutoff).get("all_players", [])
        if _cutoff is not None else all_players_raw
    )

    st.markdown(
        "<div style='font-size:22px; font-weight:900; color:#a78bfa; "
        "letter-spacing:2px; margin-bottom:2px;'>⚡ JIG</div>"
        "<div style='font-size:12px; color:#888; margin-bottom:12px;'>"
        "Matchup Intelligence Workspace  ·  Pitch Exploitation  ·  "
        "Arsenal Vulnerability  ·  HR Environment Scouting</div>",
        unsafe_allow_html=True,
    )

    def _hvy_metrics(p):
        """HVY-specific metrics: xSLG, ISO, Hard Hit, Barrel, Sweet Spot (HR window), Pull AIR."""
        xslg_v   = _pf(p.get("xslg"), 0.0)
        slg      = xslg_v if xslg_v > 0.0 else _pf(p.get("actual_slg"), 0.0)
        iso      = _pf(p.get("xiso"), 0.0)
        hh       = _pf(p.get("hard_hit"))
        brl      = _pf(p.get("barrel_pct"))
        ss       = _pf(p.get("sweet_spot_pct"))   # HR launch window proxy (8–32°)
        pull_air = resolve_pull_air_pct(p)
        return slg, iso, hh, brl, ss, pull_air

    def _slg_label(p):
        return "xSLG" if _pf(p.get("xslg"), 0.0) > 0.0 else "SLG"

    def _n(val, thr, scale):
        return min(max((val - thr) / scale + 0.5, 0.0), 1.0)

    # ── JIG card helpers ──────────────────────────────────────────────────────
    # Status cache populated after scored list is built; _hvy_card reads from it
    _jig_status_cache: dict = {}

    def _hvy_card(entry, key_prefix="hvy"):
        p    = entry["player"]
        hvy  = entry["jig"]
        base = entry.get("base_jig", hvy)
        ctx  = entry.get("ctx", {})
        slg, iso, hh, brl, ss, pull_air = entry["metrics"]
        name = p.get("player_name", "Unknown")
        team = p.get("team", ""); opp = p.get("opponent", "")
        pit_n = p.get("pitcher_name", "TBD")
        odds  = p.get("best_american")

        def _market_num(key):
            raw = p.get(key)
            if raw is None:
                return None
            val = _pf(raw, None)
            return val if val is not None and np.isfinite(val) else None

        ev = _market_num("ev_pct")
        ev_c = "#4ade80" if ev is not None and ev > 0 else "#64748b" if ev is None else "#f87171"
        ev_display = f"{ev:+.1f}%" if ev is not None else "—"
        hc    = "#4ade80" if hvy >= 60 else "#f59e0b" if hvy >= 40 else "#f87171"
        mod   = ctx.get("hvy_modifier", 1.0)
        mod_c = "#4ade80" if mod > 1.0 else "#f87171" if mod < 1.0 else "#888"
        mod_s = f"{'▲' if mod > 1.0 else '▼' if mod < 1.0 else '●'} {mod*100:.0f}%"
        _hvy_tier   = p.get("confidence_tier", "C")
        _hvy_tc     = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_hvy_tier, "#888")
        _hvy_edge   = _market_num("edge_pct")
        _hvy_ec     = _edge_col(_hvy_edge) if _hvy_edge is not None else "#64748b"
        _hvy_edge_display = f"{_hvy_edge:+.1f}%" if _hvy_edge is not None else "—"
        _hvy_model  = _pf(p.get("model_prob"), 0.0) * 100
        pit_hand    = p.get("pitcher_hand", "")
        pit_hand_lbl = f" ({'RHP' if pit_hand == 'R' else 'LHP' if pit_hand == 'L' else ''})" if pit_hand else ""
        _hvy_pit_lbl = _pitcher_label(pit_n, p.get("pitcher_factor", 1.0), p.get("platoon_factor", 1.0))
        _hvy_pid = p.get("player_id") or p.get("player_name", "")
        _hvy_ctx_known = bool(
            ctx.get("pitcher_arsenal") or ctx.get("batter_vs") or
            ctx.get("hand_splits") or ctx.get("h2h")
        )
        status_html, is_live = _jig_status_cache.get(_hvy_pid) or _game_status_badge(p)
        border   = "#f87171" if is_live else "#1e3a5f"
        status_row = (f"<div style='font-size:11px;margin:2px 0 8px;'>{status_html}</div>"
                      if status_html else "")
        odds_str = (f"+{odds}" if odds and odds > 0 else str(odds)) if odds else "—"
        # Stat colors relative to league averages
        slg_c = "#4ade80" if slg >= 0.450 else "#f87171" if slg < 0.350 else "#f0f0f0"
        brl_c = "#4ade80" if brl >= 8.0   else "#f87171" if brl < 5.0   else "#f0f0f0"
        ss_c  = "#4ade80" if ss  >= 35.0  else "#f87171" if ss  < 28.0  else "#f0f0f0"
        pa_c  = "#4ade80" if pull_air >= 24.0 else "#f87171" if pull_air < 15.0 else "#f0f0f0"
        hh_c  = "#4ade80" if hh  >= 45.0  else "#f87171" if hh  < 35.0  else "#f0f0f0"
        iso_c = "#4ade80" if iso >= 0.200 else "#f87171" if iso < 0.150 else "#f0f0f0"
        slg_lbl = _slg_label(p)
        pa_str  = f"{pull_air:.1f}%" if pull_air > 0 else "—"
        _hvy_photo = _player_photo_html(p.get("player_id"), size=44)
        # ── Dual grade system: Matchup Grade (HVY score) vs Model Grade (confidence tier)
        # These are intentionally SEPARATE — great matchup + poor value, or vice versa, is a feature.
        _mt_grade, _mt_c, _mt_bg = (
            ("A+ ELITE",  "#4ade80",  "#052010") if hvy >= 70 else
            ("A FAVOR",   "#86efac",  "#041a0c") if hvy >= 55 else
            ("B MODERATE","#facc15",  "#1a1400") if hvy >= 40 else
            ("C NEUTRAL",  "#94a3b8", "#111827") if hvy >= 25 else
            ("D AVOID",    "#f87171", "#1a0505")
        )
        _mg_label = {"S": "S+ ELITE", "A": "A MODEL", "B": "B MODEL", "C": "C MODEL"}.get(_hvy_tier, f"{_hvy_tier} MODEL")
        if _hvy_ctx_known:
            _hvy_mod_bar_pct = min(100, max(0, int((mod - 0.75) / 0.60 * 100)))
            _hvy_mod_display = mod_s
            _hvy_mod_label = "HVY"
        else:
            _hvy_mod_bar_pct = 0
            mod_c = "#64748b"
            _hvy_mod_display = "UNKNOWN"
            _hvy_mod_label = "CTX"
        # Weather — game context continuity across all card types
        _hvy_wf   = float(p.get("weather_factor", 1.0) or 1.0)
        _hvy_wsum = _weather_summary(p)
        if _hvy_wsum and abs(_hvy_wf - 1.0) >= 0.04:
            _hvy_wc = "#4ade80" if _hvy_wf >= 1.08 else "#f87171" if _hvy_wf <= 0.93 else "#888"
            _hvy_weather_frag = (
                f"<span style='font-size:9px;color:{_hvy_wc};margin-left:4px;'>🌤 {_hvy_wsum}</span>")
        else:
            _hvy_weather_frag = ""

        # Session-state HTML cache keyed by (hvy_ck, player_id, hvy_score, mod, is_live).
        # mod included so a modifier change (1.12→1.08) always rebuilds the modifier bar + text,
        # even when hvy score rounds to the same value (<0.05 change in base_jig×mod).
        _hvy_html_cache = st.session_state.setdefault("_hvy_html_cache", {})
        _hvy_html_fp = (
            _hvy_ck, _hvy_pid, round(hvy, 1), round(mod, 2), is_live, _hvy_ctx_known,
            hash(status_row) if status_row else 0,
        )
        if _hvy_html_fp not in _hvy_html_cache:
            _hvy_html_cache[_hvy_html_fp] = (
                f"<div style='background:#111827;border:1px solid {border};"
                f"border-left:3px solid {_mt_c};border-radius:10px;"
                f"padding:14px 16px;margin-bottom:14px;position:relative;overflow:hidden;'>"
                # Top accent hairline — matchup grade color, shared skeleton with Command Center / Top Targets
                f"<div style='position:absolute;top:0;left:0;right:0;height:2px;"
                f"background:linear-gradient(90deg,transparent,{_mt_c},transparent);opacity:0.6;'></div>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                f"<div style='display:flex;align-items:center;'>{_hvy_photo}"
                f"<div style='font-size:15px;font-weight:800;color:#f0f0f0;'>{name}</div></div>"
                f"<div style='text-align:right;'>"
                f"<div style='font-size:17px;font-weight:900;color:{hc};margin-bottom:3px;'>HVY {hvy:.0f}"
                f"<span style='font-size:10px;color:#555;margin-left:4px;'>base {base:.0f}</span></div>"
                f"<div style='display:flex;gap:5px;justify-content:flex-end;flex-wrap:wrap;'>"
                f"<span style='font-size:9px;font-weight:700;color:{_mt_c};"
                f"background:{_mt_bg};border:1px solid {_mt_c}44;border-radius:4px;padding:2px 6px;"
                f"letter-spacing:0.5px;'>MATCHUP: {_mt_grade}</span>"
                f"<span style='font-size:9px;font-weight:700;color:{_hvy_tc};"
                f"background:#0f172a;border:1px solid {_hvy_tc}44;border-radius:4px;padding:2px 6px;"
                f"letter-spacing:0.5px;'>MODEL: {_mg_label}</span>"
                f"</div></div>"
                f"</div>"
                f"<div style='background:#0d1117;border-radius:2px;height:3px;margin:6px 0 4px;'>"
                f"<div style='background:{mod_c};width:{_hvy_mod_bar_pct}%;"
                f"height:3px;border-radius:2px;'></div></div>"
                f"<div style='font-size:12px;color:#888;margin:0 0 4px;'>"
                f"{team} vs {opp} &nbsp;·&nbsp; vs {_hvy_pit_lbl}{pit_hand_lbl}</div>"
                f"{status_row}"
                f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:4px;"
                f"font-size:11px;margin:6px 0;'>"
                f"<div class='stat-box'><div style='color:#888;'>{slg_lbl}</div>"
                f"<div style='color:{slg_c};font-weight:700;'>{slg:.3f}</div></div>"
                f"<div class='stat-box'><div style='color:#888;'>Barrel</div>"
                f"<div style='color:{brl_c};font-weight:700;'>{brl:.1f}%</div></div>"
                f"<div class='stat-box'><div style='color:#888;'>Hard Hit</div>"
                f"<div style='color:{hh_c};font-weight:700;'>{hh:.1f}%</div></div>"
                f"<div class='stat-box'><div style='color:#888;'>HR Window</div>"
                f"<div style='color:{ss_c};font-weight:700;'>{ss:.1f}%</div></div>"
                f"<div class='stat-box'><div style='color:#888;'>Pull AIR</div>"
                f"<div style='color:{pa_c};font-weight:700;'>{pa_str}</div></div>"
                f"<div class='stat-box'><div style='color:#888;'>ISO</div>"
                f"<div style='color:{iso_c};font-weight:700;'>{iso:.3f}</div></div>"
                f"</div>"
                f"<div style='display:flex;gap:2px;margin-bottom:2px;'>"
                f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:4px;padding:3px 2px;'>"
                f"<div style='font-size:13px;font-weight:700;color:#FF6666;'>{odds_str}</div>"
                f"<div style='font-size:8px;color:#555;'>ODDS</div></div>"
                f"<div style='flex:1;text-align:center;background:#0a0a18;border-radius:4px;padding:3px 2px;'>"
                f"<div style='font-size:12px;font-weight:700;color:#a78bfa;'>{_hvy_model:.0f}%</div>"
                f"<div style='font-size:8px;color:#555;'>MDL</div></div>"
                f"<div style='flex:1;text-align:center;background:#0c0c1e;border-radius:4px;padding:3px 2px;'>"
                f"<div style='font-size:13px;font-weight:700;color:{ev_c};'>{ev_display}</div>"
                f"<div style='font-size:8px;color:#4a4a70;'>EV</div></div>"
                f"<div style='flex:1;text-align:center;background:#0c0c1e;border-radius:4px;padding:3px 2px;"
                f"border-right:1px solid #1e1e35;'>"
                f"<div style='font-size:13px;font-weight:700;color:{_hvy_ec};'>{_hvy_edge_display}</div>"
                f"<div style='font-size:8px;color:#4a4a70;'>EDGE</div></div>"
                f"<div style='flex:1;text-align:center;background:#0a0a14;border-radius:4px;padding:3px 2px;'>"
                f"<div style='font-size:11px;font-weight:700;color:{mod_c};'>{_hvy_mod_display}</div>"
                f"<div style='font-size:8px;color:#444;'>{_hvy_mod_label}</div></div>"
                f"</div>"
                + (f"<div style='margin-top:4px;padding-top:3px;border-top:1px solid #1a1a2a;'>"
                   f"{_hvy_weather_frag}</div>" if _hvy_weather_frag else "")
                + f"</div>"
            )
        st.markdown(_hvy_html_cache[_hvy_html_fp], unsafe_allow_html=True)

        pitcher_arsenal = ctx.get("pitcher_arsenal", [])
        hand_splits     = ctx.get("hand_splits", {})
        h2h             = ctx.get("h2h", {})
        batter_vs       = ctx.get("batter_vs", {})
        _data_year      = ctx.get("data_year", config.CURRENT_SEASON)
        _yr_label       = f" ({_data_year})" if _data_year != config.CURRENT_SEASON else f" ({config.CURRENT_SEASON})"
        _prior_note     = (f" ⚠️ *{_data_year} data — pitcher has no {config.CURRENT_SEASON} starts yet*"
                           if _data_year != config.CURRENT_SEASON else "")
        pit_hand        = p.get("pitcher_hand", "")
        pit_hand_lbl    = f" {'RHP' if pit_hand == 'R' else 'LHP' if pit_hand == 'L' else ''}"
        bat_side        = p.get("batter_side", "")
        bat_side_lbl    = f" {'RHB' if bat_side == 'R' else 'LHB' if bat_side == 'L' else ''}"

        _render_pitch_mix_expander(ctx, p, key_prefix,
                                   expanded=st.session_state.get("jig_pitch_mix_expanded", False),
                                   slate_ts=_jig_slate_ts)

        _fb, _fc = st.columns([1, 1])
        with _fb:
            if st.button("ℹ️ Player Info",
                         key=f"{key_prefix}_modal_{p.get('player_id','')}{name[:6]}",
                         use_container_width=True, type="primary"):
                st.session_state["show_modal"] = p
                st.session_state["modal_source_tab"] = "JIG"
                st.session_state["modal_source_section"] = "JIG · Command Center"
                st.rerun()
        with _fc:
            st.link_button("📲 Open on FanDuel", _fanduel_url(name), use_container_width=True)

    def _render_hvy_views(hvy_contexts: dict, src_players: list = None):
        """Render JIG Matchup Intelligence views."""
        # JIG thresholds are independent from Main TCC thresholds.
        hvy_matchup_min = st.session_state.get("jig_tac_min_matchup_pct", 75) / 100.0
        hvy_score_min   = st.session_state.get("jig_tac_min_hvy_score", 0)

        _players = src_players if src_players is not None else all_players
        _filtered_ids = {
            p.get("player_id") or p.get("player_name", "")
            for p in _players
        }

        def _hvy_base_score(metrics):
            """xSLG 25% · Barrel 20% · ISO 15% · Pull AIR 15% · Hard Hit 15% · HR Window 10%"""
            slg, iso, hh, brl, ss, pull_air = metrics
            return round((
                _n(slg,      0.40, 0.15) * 0.25 +
                _n(brl,      5.0,  6.0)  * 0.20 +
                _n(iso,      0.15, 0.12) * 0.15 +
                _n(pull_air, 12.0, 8.0)  * 0.15 +
                _n(hh,       35.0, 12.0) * 0.15 +
                _n(ss,       28.0, 8.0)  * 0.10
            ) * 100, 1)

        def _score_jig_players(players):
            entries = []
            for p in players:
                m   = _hvy_metrics(p)
                pid = p.get("player_id")
                ctx = hvy_contexts.get(pid, {})
                mod  = ctx.get("hvy_modifier", 1.0)
                base = _hvy_base_score(m)
                hvy  = round(min(100.0, base * mod), 1)
                entries.append({
                    "player": p, "jig": hvy, "base_jig": base,
                    "metrics": m, "ctx": ctx, "passes": hvy >= hvy_score_min,
                })
            return entries

        def _passes_pitcher_vulnerability(entry):
            _splits = entry["ctx"].get("hand_splits", {})
            if not _splits:
                return True  # no data — don't penalize
            _hr_L = _splits.get("L", {}).get("hr", 0) or 0
            _hr_R = _splits.get("R", {}).get("hr", 0) or 0
            _hr_tot = _hr_L + _hr_R
            if _pit_hr_min_total > 0 and _hr_tot < _pit_hr_min_total:
                return False
            _hand = (entry["player"].get("batter_side") or
                     entry["player"].get("batter_hand") or
                     entry["player"].get("stand") or "R").upper()
            if _pit_hr_min_lhb > 0 and _hand == "L" and _hr_L < _pit_hr_min_lhb:
                return False
            if _pit_hr_min_rhb > 0 and _hand == "R" and _hr_R < _pit_hr_min_rhb:
                return False
            return True

        def _apply_jig_visibility_gates(entries):
            gated = [
                x for x in entries
                if x["ctx"].get("hvy_modifier", 1.0) >= hvy_matchup_min
            ]
            if _pit_hr_min_total > 0 or _pit_hr_min_lhb > 0 or _pit_hr_min_rhb > 0:
                gated = [x for x in gated if _passes_pitcher_vulnerability(x)]
            return gated

        # ── Build scored entries ───────────────────────────────────────────────
        # Fingerprint: data identity + pitch context identity + JIG TCC player-set params
        _jig_scored_fp = (
            str(st.session_state.get("data_loaded_at", "")),
            id(hvy_contexts), len(hvy_contexts),
            st.session_state.get("jig_tac_min_barrel",    0.0),
            st.session_state.get("jig_tac_min_hh",        0.0),
            st.session_state.get("jig_tac_min_xslg",      0.0),
            st.session_state.get("jig_tac_min_iso",        0.0),
            st.session_state.get("jig_tac_min_pull_air",  0.0),
            st.session_state.get("jig_tac_min_hr_window", 0.0),
            st.session_state.get("jig_tac_exclude_started", False),
            st.session_state.get("jig_tac_include_live",    False),
            hvy_score_min,
        )
        if st.session_state.get("_jig_scored_fp") == _jig_scored_fp:
            _entries = st.session_state["_jig_scored"]
        else:
            _entries = _score_jig_players(_players)
            st.session_state["_jig_scored"] = _entries
            st.session_state["_jig_scored_fp"] = _jig_scored_fp

        # JIG pitcher-vulnerability thresholds are independent from Main TCC thresholds.
        _pit_hr_min_total = st.session_state.get("jig_tac_min_pit_hr_total", 0)
        _pit_hr_min_lhb   = st.session_state.get("jig_tac_min_pit_hr_lhb", 0)
        _pit_hr_min_rhb   = st.session_state.get("jig_tac_min_pit_hr_rhb", 0)

        scored_all = sorted(_score_jig_players(all_players), key=lambda x: x["jig"], reverse=True)
        scored     = _apply_jig_visibility_gates(sorted(_entries, key=lambda x: x["jig"], reverse=True))
        fs_filtered = _apply_jig_visibility_gates([
            x for x in scored_all
            if (x["player"].get("player_id") or x["player"].get("player_name", "")) in _filtered_ids
        ])

        qualified = [x for x in scored if x["passes"]]
        prime     = [x for x in qualified
                     if x["player"].get("best_american") and x["player"].get("ev_pct", 0) > 0]

        # Populate JIG status cache once for the full JIG universe (avoids per-card badge calls)
        _jig_status_cache.clear()
        for _jsc_e in scored_all:
            _jsc_p = _jsc_e["player"]
            _jsc_pid = _jsc_p.get("player_id") or _jsc_p.get("player_name", "")
            _jig_status_cache[_jsc_pid] = _game_status_badge(_jsc_p)

        if _cutoff is not None and all_players_raw is not all_players:
            _raw = []
            for p in all_players_raw:
                m   = _hvy_metrics(p)
                pid = p.get("player_id")
                ctx = hvy_contexts.get(pid, {})
                hvy = round(min(100.0, _hvy_base_score(m) * ctx.get("hvy_modifier", 1.0)), 1)
                _raw.append({"player": p, "jig": hvy, "metrics": m, "ctx": ctx,
                             "passes": hvy >= hvy_score_min})
            prime = [x for x in _raw
                     if x["passes"] and x["ctx"].get("hvy_modifier", 1.0) >= hvy_matchup_min
                     and x["player"].get("best_american")
                     and x["player"].get("ev_pct", 0) > 0]

        with st.expander(f"🔍 Debug — {len(_players)} players, {len(qualified)} qualified HVY",
                         expanded=len(qualified) == 0):
            _pit_debug = ""
            if _pit_hr_min_total > 0 or _pit_hr_min_lhb > 0 or _pit_hr_min_rhb > 0:
                _pit_debug = (
                    f" | Pit HR ≥ {_pit_hr_min_total} total"
                    + (f" / ≥{_pit_hr_min_lhb} vs LHB" if _pit_hr_min_lhb > 0 else "")
                    + (f" / ≥{_pit_hr_min_rhb} vs RHB" if _pit_hr_min_rhb > 0 else "")
                )
            st.write(f"**Gate:** HVY ≥ {hvy_score_min} | Matchup Modifier ≥ {hvy_matchup_min:.2f}×{_pit_debug}  "
                     f"·  Scoring refs: xSLG 0.40 · ISO 0.15 · HH 35.0 · Brl 5.0 · SS 28.0 · PullAIR 12.0")
            _savant_ok = st.session_state.get("_hvy_savant_ok")
            _cand_n    = st.session_state.get("_hvy_candidates_n", 0)
            _ctx_with_data = sum(
                1 for ctx in hvy_contexts.values()
                if ctx.get("pitcher_arsenal") or ctx.get("batter_vs")
            )
            if _savant_ok is False:
                st.error(
                    f"⚠️ Savant unreachable — all {_cand_n} player fetches returned empty. "
                    "This usually means the server IP is being rate-limited or blocked by "
                    "Baseball Savant. Click **Refresh Pitch Data** to retry."
                )
            else:
                st.write(f"**Savant data:** {_ctx_with_data} / {len(hvy_contexts)} contexts have pitch data "
                         f"({_cand_n} candidates loaded)")

        _hq, _hp, _ha, _hfts, _hpr = st.tabs([
            f"🎯 Command Center ({len(qualified)})",
            "⚡ Top Targets",
            "💪 Matchup Edge",
            f"🗂️ Full Slate ({len(scored_all)})",
            "🔗 Portfolio",
        ])

        with _hq:
            if not qualified:
                st.info("No players meet HVY thresholds — lower thresholds above.")
            else:
                for entry in qualified[:3]:
                    _hvy_card(entry, key_prefix="hvyq")
                if len(qualified) > 3:
                    st.caption(f"Top 3 of {len(qualified)} qualified. See Top Targets tab for all.")

        with _hp:
            if not qualified:
                st.info("No players meet HVY thresholds.")
            else:
                _hp_loaded_key = f"_jig_hp_loaded_{_jig_slate_ts}"
                if not st.session_state.get(_hp_loaded_key):
                    st.markdown(
                        f"<div style='padding:18px 0;color:#888;font-size:12px;'>"
                        f"<b style='color:#a78bfa;'>{len(qualified)} qualified players</b> · "
                        f"sorted by HVY score · pitch exploitation + arsenal vulnerability"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("▶ Load Top Targets", key="load_jig_hp", type="primary"):
                        st.session_state[_hp_loaded_key] = True
                        st.rerun()
                else:
                    _hp_n_total = len(qualified)
                    _hp_pg_opts = [25, 50, _hp_n_total] if _hp_n_total > 50 else ([25, _hp_n_total] if _hp_n_total > 25 else [_hp_n_total])
                    _hp_pg_opts = sorted(set(_hp_pg_opts))
                    _hp_pg_raw  = st.session_state.get("jig_hp_page_size", _hp_pg_opts[0])
                    _hp_pg_idx  = _hp_pg_opts.index(_hp_pg_raw) if _hp_pg_raw in _hp_pg_opts else 0
                    _hp_cols    = st.columns([3, 1])
                    with _hp_cols[0]:
                        st.caption(f"Top {min(st.session_state.get('jig_hp_page_size', _hp_pg_opts[0]), _hp_n_total)} of {_hp_n_total} qualified · ranked by HVY score · pitch exploitation + arsenal vulnerability")
                    with _hp_cols[1]:
                        _hp_page_size = st.selectbox(
                            "Show", options=_hp_pg_opts,
                            index=_hp_pg_idx,
                            format_func=lambda x: "All" if x == _hp_n_total else str(x),
                            key="jig_hp_page_size",
                            label_visibility="collapsed",
                        )
                    for entry in qualified[:_hp_page_size]:
                        _hvy_card(entry, key_prefix="hvyp")

        with _ha:
            import pandas as pd
            rows = []

            def _fmt_market_pct(value):
                if value is None:
                    return "—"
                parsed = _pf(value, None)
                if parsed is None or not np.isfinite(parsed):
                    return "—"
                return f"{parsed:+.1f}%"

            for entry in scored:
                p   = entry["player"]
                slg, iso, hh, brl, ss, pull_air = entry["metrics"]
                ctx = entry.get("ctx", {})
                _ha_tier = p.get("confidence_tier", "C")
                _ha_tier_lbl = {"S": "🌟 S", "A": "✅ A", "B": "🟡 B", "C": "🔴 C"}.get(_ha_tier, _ha_tier)
                rows.append({
                    "Player":    p.get("player_name", ""),
                    "Team":      p.get("team", ""),
                    "Tier":      _ha_tier_lbl,
                    "HVY":       entry["jig"],
                    "HVY Base":  entry["base_jig"],
                    "Modifier":  f"{ctx.get('hvy_modifier', 1.0):.2f}×",
                    "Pass":      "✅" if entry["passes"] else "",
                    "MDL%":      f"{_pf(p.get('model_prob'), 0.0)*100:.1f}%",
                    "EV%":       _fmt_market_pct(p.get("ev_pct")),
                    "Edge%":     _fmt_market_pct(p.get("edge_pct")),
                    "xSLG":      f"{slg:.3f}",
                    "Barrel%":   f"{brl:.1f}",
                    "Hard Hit":  f"{hh:.1f}",
                    "HR Win%":   f"{ss:.1f}",
                    "Pull AIR":  f"{pull_air:.1f}",
                    "ISO":       f"{iso:.3f}" if iso else "--",
                    "Pitcher":   p.get("pitcher_name", ""),
                })
            if rows:
                _hvy_ver = st.session_state.get("_hvy_all_ver", 0)
                _hvy_df = _apply_heatmap(pd.DataFrame(rows))
                _sel = st.dataframe(
                    _hvy_df, hide_index=True, use_container_width=True,
                    on_select="rerun", selection_mode="single-row",
                    key=f"hvy_all_df_{_hvy_ver}",
                )
                _sel_rows = getattr(getattr(_sel, "selection", None), "rows", [])
                if _sel_rows and 0 <= _sel_rows[0] < len(scored):
                    st.session_state["_hvy_all_ver"] = _hvy_ver + 1
                    st.session_state["show_modal"] = scored[_sel_rows[0]]["player"]
                    st.session_state["modal_source_tab"] = "JIG"
                    st.session_state["modal_source_section"] = "JIG · Matchup Edge"
                    st.rerun()

            if rows:
                st.caption("Full HVY cards with pitch mix breakdown → see Full Slate tab.")

        with _hpr:
            # ── JIG Portfolio control bar (Phase 2C) ──────────────────────────
            _jport_modes = [
                ("All Prime",       "all",     "High-upside tactical deployment · all qualified JIG plays"),
                ("Barrel-Focused",  "barrel",  "Barrel-weighted aggression · barrel ≥ 8% · exploit-focused construction"),
                ("HVY Targets",     "top",     "High-conviction HVY score · top 10 by tactical matchup score"),
            ]
            _jport_mode = st.session_state.get("jig_port_mode_sel", "barrel")
            _jport_entry = next(
                (e for e in _jport_modes if e[1] == _jport_mode), _jport_modes[1]
            )
            st.markdown(
                "<div style='font-size:10px;font-weight:700;letter-spacing:1.5px;"
                "color:#555;margin-bottom:6px;'>TACTICAL DEPLOYMENT</div>",
                unsafe_allow_html=True,
            )
            _jp_cols = st.columns(3)
            for _jp_col, (_jp_lbl, _jp_key, _jp_summ) in zip(_jp_cols, _jport_modes):
                with _jp_col:
                    if st.button(
                        _jp_lbl,
                        key=f"jig_port_mode_{_jp_key}",
                        type="primary" if _jport_mode == _jp_key else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state["jig_port_mode_sel"] = _jp_key
                        st.rerun()
            st.markdown(
                f"<div style='padding:5px 0 10px;font-size:11px;color:#888;'>"
                f"<span style='color:#f97316;font-weight:700;'>Tactical Intelligence</span>"
                f" &nbsp;·&nbsp; {_jport_entry[2]}</div>",
                unsafe_allow_html=True,
            )
            # ── Pool routing — display filter only, no scoring changes ─────────
            if not prime:
                st.info("No prime JIG plays — need qualified players with positive-EV odds.")
            else:
                if _jport_mode == "barrel":
                    _jport_pool = [e for e in prime if _pf(e["player"].get("barrel_pct"), 0.0) >= 8.0]
                    _jport_empty = "No barrel ≥ 8% prime plays — switch to All Prime or lower JIG thresholds."
                elif _jport_mode == "top":
                    _jport_pool = sorted(
                        prime, key=lambda e: e["jig"], reverse=True
                    )[:10]
                    _jport_empty = "No prime plays available."
                else:
                    _jport_pool = prime
                    _jport_empty = "No prime JIG plays — need qualified players with positive-EV odds."

                # ── Phase 2D: reason chip summary ───────────────────────────────
                _jrt_brl12  = sum(1 for e in _jport_pool if _pf(e["player"].get("barrel_pct"), 0.0) >= 12)
                _jrt_brl10  = sum(1 for e in _jport_pool if 10 <= _pf(e["player"].get("barrel_pct"), 0.0) < 12)
                _jrt_elite  = sum(1 for e in _jport_pool if e["jig"] >= 75)
                _jrt_match  = sum(1 for e in _jport_pool if _pf(e["ctx"].get("hvy_modifier", 1.0), 1.0) >= 1.15)
                _jrt_chips  = []
                if _jrt_brl12:
                    _jrt_chips.append(
                        f"<span style='background:#14532d;color:#4ade80;font-size:10px;"
                        f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                        f"Elite Barrel &nbsp;×{_jrt_brl12}</span>"
                    )
                if _jrt_brl10:
                    _jrt_chips.append(
                        f"<span style='background:#052e16;color:#86efac;font-size:10px;"
                        f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                        f"Strong Barrel &nbsp;×{_jrt_brl10}</span>"
                    )
                if _jrt_elite:
                    _jrt_chips.append(
                        f"<span style='background:#431407;color:#fb923c;font-size:10px;"
                        f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                        f"HVY Elite &nbsp;×{_jrt_elite}</span>"
                    )
                if _jrt_match:
                    _jrt_chips.append(
                        f"<span style='background:#1a1040;color:#c084fc;font-size:10px;"
                        f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                        f"Favorable Matchup &nbsp;×{_jrt_match}</span>"
                    )
                if not _jrt_chips:
                    _jrt_chips.append(
                        f"<span style='background:#1e1e30;color:#a78bfa;font-size:10px;"
                        f"font-weight:700;padding:2px 7px;border-radius:4px;'>"
                        f"Longshot Value</span>"
                    )
                if _jport_pool:
                    st.markdown(
                        f"<div style='display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;'>"
                        f"{''.join(_jrt_chips)}</div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        f"{len(_jport_pool)} prime JIG picks · {_jport_entry[0].lower()} mode"
                    )
                    for entry in _jport_pool:
                        _hvy_card(entry, key_prefix="hvypr")
                else:
                    st.info(_jport_empty)

        with _hfts:
            # Phase 2A — JIG Full Slate tactical universe visibility expansion
            st.markdown(
                "<span style='color:#f97316;font-size:13px;font-weight:700;letter-spacing:1px;'>"
                "FULL SLATE</span>"
                "<span style='color:#555;font-size:11px;margin-left:12px;'>"
                "tactical battlefield · sorted by HVY score · exploit discovery</span>",
                unsafe_allow_html=True,
            )

            # ── Mode selector — visibility only, no formula or threshold changes ──
            _jig_fts_mode_opts = ["Top Tactical Targets", "Qualified / Filtered", "All Players"]
            _jig_fts_mode = st.radio(
                "jig_fs_mode",
                options=_jig_fts_mode_opts,
                index=_jig_fts_mode_opts.index(
                    st.session_state.get("jig_fts_mode_sel", "Qualified / Filtered")
                    if st.session_state.get("jig_fts_mode_sel", "Qualified / Filtered")
                    in _jig_fts_mode_opts else "Qualified / Filtered"
                ),
                horizontal=True,
                key="jig_fts_mode_sel",
                label_visibility="collapsed",
            )

            # ── Pool routing ──────────────────────────────────────────────────
            if _jig_fts_mode == "Top Tactical Targets":
                _fts_pool = qualified   # HVY ≥ threshold + modifier gate + TCC filtered
                _fts_info_html = (
                    f"<b style='color:#4ade80;'>{len(_fts_pool)} confirmed targets</b>"
                    f" &nbsp;·&nbsp; HVY ≥ {hvy_score_min}"
                    f" &nbsp;·&nbsp; modifier ≥ {hvy_matchup_min:.0%}"
                    f" &nbsp;·&nbsp; TCC batter filters applied"
                )
                _fts_empty_msg = "No top tactical targets meet current JIG thresholds — lower HVY/modifier gates or switch mode."
            elif _jig_fts_mode == "All Players":
                _fts_pool = scored_all  # full JIG universe — no modifier gate, no TCC profile filter
                _fts_n_ctx    = sum(1 for x in _fts_pool if bool(
                    x["ctx"].get("pitcher_arsenal") or
                    x["ctx"].get("batter_vs") or
                    x["ctx"].get("hand_splits")
                ))
                _fts_n_no_ctx = len(_fts_pool) - _fts_n_ctx
                _fts_info_html = (
                    f"<b style='color:#f97316;'>{len(_fts_pool)} total players</b>"
                    f" &nbsp;·&nbsp; no modifier gate &nbsp;·&nbsp; no TCC profile filter"
                    f" &nbsp;·&nbsp; <span style='color:#60a5fa;'>{_fts_n_ctx} with pitch context</span>"
                    + (f" &nbsp;·&nbsp; <span style='color:#475569;'>{_fts_n_no_ctx} no ctx · base HVY only</span>"
                       if _fts_n_no_ctx else "")
                )
                _fts_empty_msg = "No players available — refresh data or wait for lineups."
            else:  # Qualified / Filtered (default — current behavior)
                _fts_pool = fs_filtered  # modifier gate applied, TCC filtered, no HVY threshold
                _fts_info_html = (
                    f"<b style='color:#a78bfa;'>{len(_fts_pool)} players</b>"
                    f" &nbsp;·&nbsp; modifier ≥ {hvy_matchup_min:.0%} gate"
                    f" &nbsp;·&nbsp; TCC batter filters applied"
                    f" &nbsp;·&nbsp; no HVY threshold gate"
                )
                _fts_empty_msg = "No players available — refresh pitch data or lower TCC batter filters."

            if not _fts_pool:
                st.info(_fts_empty_msg)
            else:
                from collections import defaultdict as _dd
                # Mode-specific lazy gate key — switching mode requires explicit load click
                _fts_loaded_key = f"_jig_fts_loaded_{_jig_slate_ts}_{_jig_fts_mode}"
                if not st.session_state.get(_fts_loaded_key):
                    st.markdown(
                        f"<div style='padding:16px 0;font-size:12px;color:#888;'>"
                        f"{_fts_info_html}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "▶ Load Full Slate",
                        key=f"load_jig_fts_{_jig_fts_mode.replace(' ', '_')}",
                        type="primary",
                    ):
                        st.session_state[_fts_loaded_key] = True
                        st.rerun()
                else:
                    _fts_n_total = len(_fts_pool)
                    _fts_pg_opts = [25, 50, 100, _fts_n_total] if _fts_n_total > 100 else (
                        [25, 50, _fts_n_total] if _fts_n_total > 50 else (
                        [25, _fts_n_total] if _fts_n_total > 25 else [_fts_n_total]))
                    _fts_pg_opts = sorted(set(_fts_pg_opts))
                    # Per-mode pagination key — independent state per mode
                    _fts_pg_key  = f"jig_fts_page_size_{_jig_fts_mode.replace(' ', '_')}"
                    _fts_pg_raw  = st.session_state.get(_fts_pg_key, _fts_pg_opts[0])
                    _fts_pg_idx  = _fts_pg_opts.index(_fts_pg_raw) if _fts_pg_raw in _fts_pg_opts else 0
                    _fts_cols    = st.columns([3, 1])
                    with _fts_cols[0]:
                        st.markdown(
                            f"<div style='font-size:11px;color:#888;padding:2px 0;'>{_fts_info_html}</div>",
                            unsafe_allow_html=True,
                        )
                    with _fts_cols[1]:
                        _fts_page_size = st.selectbox(
                            "Show", options=_fts_pg_opts,
                            index=_fts_pg_idx,
                            format_func=lambda x: "All" if x == _fts_n_total else str(x),
                            key=_fts_pg_key,
                            label_visibility="collapsed",
                        )

                    # ── JIG game command modules ──────────────────────────────
                    # Group paginated entries by game_pk, order by top HVY score
                    _jfts_slice  = _fts_pool[:_fts_page_size]
                    _jfts_groups: dict = _dd(list)
                    for _je in _jfts_slice:
                        _jgk = (
                            _je["player"].get("game_pk") or
                            f"{_je['player'].get('team','?')}-{_je['player'].get('opponent','?')}"
                        )
                        _jfts_groups[_jgk].append(_je)
                    # Sort game groups by highest HVY score (most dangerous game first)
                    _jfts_order = sorted(
                        _jfts_groups.keys(),
                        key=lambda gk: -_jfts_groups[gk][0]["jig"],
                    )

                    _ctx_sep_shown = False  # for All Players mode cross-game ctx separator

                    def _jvuln(f):
                        if f >= 1.20: return "ELITE TARGET", "#4ade80"
                        if f >= 1.08: return "FAVORABLE",    "#86efac"
                        if f >= 0.92: return "NEUTRAL",       "#3a3a3a"
                        if f >= 0.80: return "TOUGH",         "#f97316"
                        return "SUPPRESSOR", "#f87171"

                    for _jgi, _jgk in enumerate(_jfts_order):
                        _jg_entries = _jfts_groups[_jgk]
                        _jp0        = _jg_entries[0]["player"]
                        _jg_home    = _jp0.get("home_team", "")
                        _jg_away    = next(
                            (e["player"].get("team", "") for e in _jg_entries
                             if e["player"].get("team") != _jg_home),
                            _jp0.get("opponent", "?"),
                        )
                        _jg_top_hvy = _jg_entries[0]["jig"]
                        _jg_gt      = _game_time_et(_jp0.get("game_time_utc", ""))
                        _jg_gt_str  = _jg_gt.strftime("%I:%M %p ET").lstrip("0") if _jg_gt else "TBD"
                        _jg_pid0    = _jp0.get("player_id") or _jp0.get("player_name", "")
                        _jg_urg_col = urgency_cache.get(_jg_pid0, (_jg_gt_str, "#555", ""))[1]

                        # Pitcher vulnerability (from home/away batters' pitcher_factor)
                        _jg_home_batters = [
                            e for e in _jg_entries if e["player"].get("team") == _jg_home
                        ]
                        _jg_away_batters = [
                            e for e in _jg_entries if e["player"].get("team") != _jg_home
                        ]
                        _jg_away_pit  = (
                            _jg_home_batters[0]["player"].get("pitcher_name", "TBD")
                            if _jg_home_batters else "TBD"
                        )
                        _jg_away_pf   = float(
                            _jg_home_batters[0]["player"].get("pitcher_factor", 1.0)
                            if _jg_home_batters else 1.0
                        )
                        _jg_home_pit  = (
                            _jg_away_batters[0]["player"].get("pitcher_name", "TBD")
                            if _jg_away_batters else "TBD"
                        )
                        _jg_home_pf   = float(
                            _jg_away_batters[0]["player"].get("pitcher_factor", 1.0)
                            if _jg_away_batters else 1.0
                        )
                        _jg_av_lbl, _jg_av_col = _jvuln(_jg_away_pf)
                        _jg_hv_lbl, _jg_hv_col = _jvuln(_jg_home_pf)

                        # HVY score color
                        _jg_hvy_col = (
                            "#f97316" if _jg_top_hvy >= 75 else
                            "#facc15" if _jg_top_hvy >= 60 else
                            "#888"
                        )
                        _jg_border_col = (
                            "#f97316" if _jg_top_hvy >= 75 else
                            "#facc15" if _jg_top_hvy >= 60 else
                            "#444"
                        )
                        _jg_n = len(_jg_entries)

                        st.markdown(
                            f"<div id='jgm{_jgi}_{_jig_slate_ts}' style='"
                            f"background:#08060a;border-left:3px solid {_jg_border_col};"
                            f"border-top:1px solid #180e00;border-radius:3px;"
                            f"margin:14px 0 6px;padding:5px 10px 5px;overflow:hidden;'>"
                            f"<div style='display:flex;align-items:center;"
                            f"flex-wrap:wrap;gap:5px;'>"
                            # Matchup
                            f"<span style='font-size:12px;font-weight:800;color:#f97316;"
                            f"letter-spacing:0.3px;'>{_jg_away} @ {_jg_home}</span>"
                            f"<span style='color:#2a1a00;'>·</span>"
                            f"<span style='font-size:10px;color:{_jg_urg_col};'>{_jg_gt_str}</span>"
                            f"<span style='color:#2a1a00;'>·</span>"
                            # Top HVY in game
                            f"<span style='font-size:9px;color:#3a2a00;"
                            f"letter-spacing:1px;font-family:monospace;'>HVY</span>"
                            f"<span style='font-size:12px;color:{_jg_hvy_col};"
                            f"font-weight:800;'>{_jg_top_hvy:.0f}</span>"
                            f"<span style='color:#2a1a00;'>·</span>"
                            f"<span style='font-size:9px;color:#555;'>{_jg_n} players</span>"
                            f"</div>"
                            # Pitcher target strip
                            f"<div style='margin-top:3px;font-size:9px;color:#555;"
                            f"display:flex;align-items:center;flex-wrap:wrap;gap:0;'>"
                            f"<span style='color:#3a2a00;letter-spacing:1px;"
                            f"font-family:monospace;margin-right:6px;'>TARGET</span>"
                            f"<span style='color:#a78bfa;font-weight:700;margin-right:3px;'>{_jg_home}</span>"
                            f"<span style='color:#2a1a00;margin-right:3px;'>vs</span>"
                            f"<span style='color:#9a8a9a;margin-right:4px;'>{_jg_away_pit}</span>"
                            f"<span style='color:{_jg_av_col};font-weight:700;"
                            f"letter-spacing:0.3px;'>{_jg_av_lbl}</span>"
                            f"<span style='color:#1a0a00;margin:0 8px;'>│</span>"
                            f"<span style='color:#60a5fa;font-weight:700;margin-right:3px;'>{_jg_away}</span>"
                            f"<span style='color:#2a1a00;margin-right:3px;'>vs</span>"
                            f"<span style='color:#9a8a9a;margin-right:4px;'>{_jg_home_pit}</span>"
                            f"<span style='color:{_jg_hv_col};font-weight:700;"
                            f"letter-spacing:0.3px;'>{_jg_hv_lbl}</span>"
                            f"</div></div>",
                            unsafe_allow_html=True,
                        )

                        for entry in _jg_entries:
                            # All Players mode: ctx separator crosses game boundaries
                            if _jig_fts_mode == "All Players" and not _ctx_sep_shown:
                                _has_ctx = bool(
                                    entry["ctx"].get("pitcher_arsenal") or
                                    entry["ctx"].get("batter_vs") or
                                    entry["ctx"].get("hand_splits")
                                )
                                if not _has_ctx:
                                    _ctx_sep_shown = True
                                    st.markdown(
                                        "<div style='border-top:1px solid #1e293b;"
                                        "margin:10px 0 14px;font-size:10px;color:#475569;"
                                        "padding-top:6px;letter-spacing:1px;'>"
                                        "▼ &nbsp;NO PITCH CONTEXT — base HVY only · "
                                        "matchup modifier unknown · Statcast profile strength only"
                                        "</div>",
                                        unsafe_allow_html=True,
                                    )
                            _hvy_card(entry, key_prefix="hvyfts")

                    # Return-to-top stub
                    st.markdown(
                        "<div style='text-align:center;padding:12px 0 4px;"
                        "border-top:1px solid #18100a;margin-top:6px;'>"
                        "<span style='font-size:9px;color:#2a1a00;letter-spacing:1.5px;"
                        "font-family:monospace;'>▲ &nbsp;SCROLL UP TO CHANGE MODE / FILTER</span>"
                        "</div>",
                        unsafe_allow_html=True,
                    )

    # ── JIG — Pitch Mix Intelligence ──────────────────────────────────────────
    st.caption(
        "xSLG (25%) · Barrel (20%) · ISO (15%) · Pull AIR (15%) · Hard Hit (15%) · HR Window (10%)"
        "  ·  Context: arsenal matchup · hand splits · contact shape · environment · H2H  ·  "
        "JIG Tactical Command Center controls apply only within JIG."
    )
    from clients.pitch_mix import HVY_CACHE_VERSION as _HVY_VER
    _hvy_pitcher_fp = hash(frozenset((p.get("player_id"), p.get("pitcher_id")) for p in all_players_raw))
    _hvy_ck = f"hvy_ctx_{data.get('date', '')}_{_HVY_VER}_{_hvy_pitcher_fp}"
    if _hvy_ck not in st.session_state:
        _hvy_candidates = [p for p in all_players_raw if p.get("player_id")]
        _unique_pitchers = len({p.get("pitcher_id") for p in _hvy_candidates if p.get("pitcher_id")})
        with st.spinner(
            f"Loading pitch mix data for {len(_hvy_candidates)} players "
            f"across {_unique_pitchers} pitchers…"
        ):
            from clients import arsenal as _ar_client
            from clients import pitch_mix as _pm_client
            try:
                _ar_data = _ar_client.get_pitcher_arsenal(config.CURRENT_SEASON)
            except Exception:
                _ar_data = {}
            _hvy_ctxs = _pm_client.load_hvy_contexts_batch(_hvy_candidates, _ar_data)
            _savant_ok = any(
                bool(ctx.get("pitcher_arsenal") or ctx.get("batter_vs"))
                for ctx in _hvy_ctxs.values()
            )
            st.session_state["_hvy_savant_ok"] = _savant_ok
            st.session_state["_hvy_candidates_n"] = len(_hvy_candidates)
            st.session_state[_hvy_ck] = _hvy_ctxs

    _cached_ctxs = st.session_state.get(_hvy_ck, {})
    if _cached_ctxs:
        _cand_count  = len([p for p in all_players if p.get("best_american")])
        _has_arsenal = sum(1 for _c in _cached_ctxs.values() if _c.get("pitcher_arsenal"))
        _retry_key   = f"hvy_retry_{data.get('date', '')}"
        _retry_count = st.session_state.get(_retry_key, 0)
        if _cand_count > 0 and _has_arsenal / max(_cand_count, 1) < 0.20 and _retry_count < 1:
            st.session_state[_retry_key] = _retry_count + 1
            st.session_state.pop(_hvy_ck, None)
            st.rerun()

    _col_refresh, _col_status = st.columns([1, 4])
    with _col_refresh:
        if st.button("🔄 Refresh Pitch Data", key="hvy_refresh"):
            from clients import pitch_mix as _pm_clear, arsenal as _ar_clear
            _pm_clear.clear_caches()
            _ar_clear.clear_caches()
            st.session_state.pop(_hvy_ck, None)
            # Also clear MAIN picks pitch mix cache — module caches were just wiped,
            # so MAIN must re-fetch too (not just JIG) to avoid serving stale contexts.
            for _jig_stale_k in [k for k in st.session_state if k.startswith("picks_pm_ctx_")]:
                st.session_state.pop(_jig_stale_k, None)
            st.rerun()

    # ── JIG Tactical Command Center ───────────────────────────────────────────
    _jig_tac_stat_keys = [
        "jig_tac_min_barrel", "jig_tac_min_hh", "jig_tac_min_xslg", "jig_tac_min_iso",
        "jig_tac_min_pull_air", "jig_tac_min_hr_window",
        "jig_tac_min_matchup_pct", "jig_tac_min_hvy_score",
        "jig_tac_min_pit_hr_total", "jig_tac_min_pit_hr_lhb", "jig_tac_min_pit_hr_rhb",
    ]
    _jig_tac_reset_defaults = {
        "jig_tac_min_barrel": 0.0,
        "jig_tac_min_hh": 0.0,
        "jig_tac_min_xslg": 0.0,
        "jig_tac_min_iso": 0.0,
        "jig_tac_min_pull_air": 0.0,
        "jig_tac_min_hr_window": 0.0,
        "jig_tac_min_matchup_pct": 75,
        "jig_tac_min_hvy_score": 0,
        "jig_tac_min_pit_hr_total": 0,
        "jig_tac_min_pit_hr_lhb": 0,
        "jig_tac_min_pit_hr_rhb": 0,
        "jig_tac_exclude_started": False,
        "jig_tac_include_live": False,
    }
    with st.expander("⚙️ JIG Tactical Command Center", expanded=False):
        # ── JIG Engine Identity + Preset Bar ────────────────────────────────
        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:baseline;"
            "margin-bottom:2px;'>"
            "<div style='font-size:9px;color:#888;letter-spacing:1px;'>JIG ENGINE PRESET</div>"
            "<div style='font-size:9px;color:#f97316;letter-spacing:1px;'>"
            "Tactical · Matchup-Driven · Arsenal-Focused</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        def _jig_tcc_reset():
            for _rk, _rv in _jig_tac_reset_defaults.items():
                st.session_state[_rk] = _rv
            st.session_state.pop("jig_active_preset", None)
            st.rerun()
        _fc.render_preset_bar("jig_active_preset", _fc.JIG_PRESETS, reset_cb=_jig_tcc_reset)
        st.caption("Narrow JIG player universe by batter profile + matchup context")

        st.markdown(
            "<div style='font-size:10px;color:#a78bfa;font-weight:700;"
            "letter-spacing:1px;margin:8px 0 4px;'>BATTER PROFILE FILTERS</div>",
            unsafe_allow_html=True,
        )
        _ja1, _ja2, _ja3, _ja4, _ja5, _ja6 = st.columns(6)
        with _ja1:
            _fc.render_filter_control(
                "Barrel %", "jig_tac_min_barrel", 0.0, 20.0, 0.0, 0.5, "%.1f",
                "Statcast barrel rate floor",
            )
        with _ja2:
            _fc.render_filter_control(
                "Hard Hit %", "jig_tac_min_hh", 0.0, 60.0, 0.0, 1.0, "%.1f",
                "Hard-hit rate floor (≥95mph exit velo)",
            )
        with _ja3:
            _fc.render_filter_control(
                "xSLG", "jig_tac_min_xslg", 0.000, 0.800, 0.000, 0.010, "%.3f",
                "Expected slugging percentage floor",
            )
        with _ja4:
            _fc.render_filter_control(
                "ISO", "jig_tac_min_iso", 0.000, 0.400, 0.000, 0.010, "%.3f",
                "Isolated power (SLG−AVG) floor",
            )
        with _ja5:
            _fc.render_filter_control(
                "Pull Air %", "jig_tac_min_pull_air", 0.0, 30.0, 0.0, 0.5, "%.1f",
                "Pulled-airborne contact rate floor",
            )
        with _ja6:
            _fc.render_filter_control(
                "HR Window %", "jig_tac_min_hr_window", 0.0, 50.0, 0.0, 1.0, "%.1f",
                "Sweet-spot % floor (8–32° launch angle)",
            )

        st.markdown(
            "<div style='font-size:10px;color:#a78bfa;font-weight:700;"
            "letter-spacing:1px;margin:8px 0 4px;'>MATCHUP / HVY FILTERS</div>",
            unsafe_allow_html=True,
        )
        _jb1, _jb2, _jb3 = st.columns(3)
        with _jb1:
            _fc.render_filter_control(
                "Min Matchup Modifier %", "jig_tac_min_matchup_pct", 75, 140, 75, 1, "%d",
                "HVY modifier floor — 100=neutral, 110=favorable, 120=elite mismatch",
            )
        with _jb2:
            _fc.render_filter_control(
                "Min HVY Score", "jig_tac_min_hvy_score", 0, 100, 0, 1, "%d",
                "Composite batter matchup score floor (0–100)",
            )
        with _jb3:
            _jig_cutoff = st.session_state.get("cutoff_utc_hour")
            if _jig_cutoff is not None:
                _jig_et = (_jig_cutoff - 4) % 24
                _jig_h12 = _jig_et % 12 or 12
                _jig_ampm = "AM" if _jig_et < 12 else "PM"
                st.caption(f"⏰ Time gate: {_jig_h12}:00 {_jig_ampm} ET  ←  sidebar")
            else:
                st.caption("⏰ No time gate  ←  sidebar")

        st.markdown(
            "<div style='font-size:10px;color:#f97316;font-weight:700;"
            "letter-spacing:1px;margin:8px 0 4px;'>PITCHER VULNERABILITY</div>",
            unsafe_allow_html=True,
        )
        _jv1, _jv2, _jv3 = st.columns(3)
        with _jv1:
            _fc.render_filter_control(
                "Total HR Allowed", "jig_tac_min_pit_hr_total", 0, 30, 0, 1, "%d",
                "Pitcher must have allowed ≥ N HRs total this season — 0 = no filter",
            )
        with _jv2:
            _fc.render_filter_control(
                "HR vs LHB", "jig_tac_min_pit_hr_lhb", 0, 20, 0, 1, "%d",
                "Pitcher must have allowed ≥ N HRs vs LHBs — applied only to LHBs",
            )
        with _jv3:
            _fc.render_filter_control(
                "HR vs RHB", "jig_tac_min_pit_hr_rhb", 0, 20, 0, 1, "%d",
                "Pitcher must have allowed ≥ N HRs vs RHBs — applied only to RHBs",
            )

        _jte1, _jte2 = st.columns(2)
        with _jte1:
            st.toggle("Exclude Started Games", value=False, key="jig_tac_exclude_started")
        with _jte2:
            st.toggle("Include Live Games",    value=False, key="jig_tac_include_live")

        # ── PITCH MIX DISPLAY CONTROL ────────────────────────────────────────
        st.markdown(
            "<div style='border-top:1px solid #1a1a1a;margin:8px 0 4px;"
            "padding-top:6px;font-size:9px;color:#888;letter-spacing:1px;'>"
            "PITCH MIX DISPLAY — JIG matchup cards</div>",
            unsafe_allow_html=True,
        )
        _jpm1, _jpm2 = st.columns(2)
        with _jpm1:
            if st.button(
                "Open All Pitch Mix",
                key="_jig_pm_open",
                use_container_width=True,
                help="Expand pitch mix analysis on all visible JIG cards",
            ):
                st.session_state["jig_pitch_mix_expanded"] = True
                st.rerun()
        with _jpm2:
            if st.button(
                "Close All Pitch Mix",
                key="_jig_pm_close",
                use_container_width=True,
                help="Collapse pitch mix analysis on all visible JIG cards",
            ):
                st.session_state["jig_pitch_mix_expanded"] = False
                st.rerun()

    # Build JIG-TCC-filtered player list
    _jig_tac_params = {
        "min_barrel":      st.session_state.get("jig_tac_min_barrel",    0.0),
        "min_hh":          st.session_state.get("jig_tac_min_hh",        0.0),
        "min_xslg":        st.session_state.get("jig_tac_min_xslg",      0.0),
        "min_iso":         st.session_state.get("jig_tac_min_iso",        0.0),
        "min_pull_air":    st.session_state.get("jig_tac_min_pull_air",  0.0),
        "min_hr_window":   st.session_state.get("jig_tac_min_hr_window", 0.0),
        "min_ev":          0.0,
        "min_edge":        0.0,
        "min_conf":        0.0,
        "min_model_prob":  0.0,
        "exclude_started": st.session_state.get("jig_tac_exclude_started", False),
        "include_live":    st.session_state.get("jig_tac_include_live",    False),
    }
    _any_jig_tac = (
        any(_jig_tac_params[k] > 0 for k in (
            "min_barrel", "min_hh", "min_xslg", "min_iso", "min_pull_air", "min_hr_window",
        ))
        or _jig_tac_params["exclude_started"]
    )
    _jig_filtered = _apply_tactical_filters(all_players, _jig_tac_params) if _any_jig_tac else None

    _render_hvy_views(st.session_state.get(_hvy_ck, {}), src_players=_jig_filtered)

def tab_parlays(data: dict):
    ranked          = data.get("ranked", [])
    team_players    = data.get("team_players", {})
    auto_parlays    = data.get("auto_parlays", {})
    profile_parlays = data.get("profile_parlays", [])

    # ── Profile-based parlays ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">🎯 AUTO-BASED PARLAYS</div>',
                unsafe_allow_html=True)
    st.caption(
        "Each section builds the best 3-leg combos for a specific power profile. "
        "Players are scored on the relevant Statcast signals, then ranked 60% by EV "
        "and 40% by profile fit. Requires players with both odds and Statcast data."
    )

    if not profile_parlays or all(not p.get("combos") for p in profile_parlays):
        st.warning("Not enough players with odds + Statcast data for profile parlays. "
                   "Refresh data after lineups post.")
    else:
        for pi, profile in enumerate(profile_parlays):
            pname    = profile.get("name", "")
            subtitle = profile.get("subtitle", "")
            desc     = profile.get("desc", "")
            combos   = profile.get("combos", [])

            st.markdown(
                f"<div style='margin:18px 0 4px 0;'>"
                f"<span style='font-size:16px; font-weight:700; color:#f0f0f0;'>{pname}</span>"
                f"<span style='font-size:11px; color:#888888; margin-left:10px;'>— {subtitle}</span>"
                f"</div>"
                f"<div style='font-size:11px; color:#666666; margin-bottom:8px;'>{desc}</div>",
                unsafe_allow_html=True,
            )

            if not combos:
                st.caption("Not enough qualifying players for this profile today.")
                continue

            cols = st.columns(len(combos))
            for col, combo, i in zip(cols, combos, range(1, len(combos) + 1)):
                with col:
                    ps = combo.get("profile_score", 0)
                    label = f"Combo {i}"
                    html = _combo_html(combo, label)
                    ps_line = (
                        f'<div style="margin-top:4px; font-size:10px; color:#666666;">'
                        f'Profile fit: <b style="color:#888888">{ps:.2f}</b></div>'
                    )
                    html = html.rstrip().rstrip("</div>") + ps_line + "</div>"
                    st.markdown(html, unsafe_allow_html=True)
                    if st.button("🎰 Add to FD Slip", key=f"fd_prof_{pi}_{i}",
                                 width='stretch'):
                        _add_legs_to_fd_slip(combo["legs"], source_tab="Parlays", source_section=profile.get("name", "Profile Parlay"))

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
                    pit_fac   = sel.get("pitcher_factor", 1.0)
                    plat_fac  = sel.get("platoon_factor", 1.0)
                    odds_str  = _fmt_american(sel.get("best_american"))
                    model_pct = f"{sel.get('model_prob',0)*100:.1f}%"
                    ev_val    = sel.get("ev_pct", 0)
                    edge_val  = sel.get("edge_pct", 0)
                    _mb_tier  = sel.get("confidence_tier", "C")
                    _mb_tc    = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_mb_tier, "#888")
                    _mb_ev_c  = "#4ade80" if ev_val >= 0 else "#f87171"
                    _mb_ec    = _edge_col(edge_val)
                    pitcher_lbl = _pitcher_label(sel.get("pitcher_name","TBD"), pit_fac, plat_fac)
                    st.markdown(
                        f"<div style='font-size:11px; color:#888888; margin:-8px 0 8px 0;'>"
                        f"Odds: <b style='color:#FF6666'>{odds_str}</b> &nbsp;|&nbsp; "
                        f"MDL: <b style='color:#a78bfa'>{model_pct}</b> &nbsp;|&nbsp; "
                        f"EV: <b style='color:{_mb_ev_c}'>{ev_val:+.1f}%</b> &nbsp;|&nbsp; "
                        f"Edge: <b style='color:{_mb_ec}'>{edge_val:+.1f}%</b> &nbsp;|&nbsp; "
                        f"<b style='color:{_mb_tc}'>{_mb_tier}-Tier</b><br>"
                        f"Pitcher: {pitcher_lbl}</div>",
                        unsafe_allow_html=True,
                    )
                    legs_built.append(sel)

            btn_col, fd_col = st.columns([3, 2])
            with btn_col:
                build_clicked = st.button(f"Build {n_legs}-Leg Parlay",
                                          key=f"{key_prefix}_build",
                                          type="primary", width='stretch')
            with fd_col:
                fd_clicked = st.button("🎰 Add to FD Slip",
                                       key=f"{key_prefix}_fd",
                                       width='stretch')

            if fd_clicked:
                if len(legs_built) == n_legs:
                    _add_legs_to_fd_slip(legs_built, source_tab="Parlays", source_section="Manual Builder")
                else:
                    st.error(f"Select all {n_legs} legs first.")

            if build_clicked:
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TAB 3 — PERFORMANCE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def tab_performance():
    def _pnl_box(label: str, value: str, css: str) -> str:
        return (
            f"<div style='background:{css};border-radius:8px;padding:10px 14px;"
            f"text-align:center;margin:2px;'>"
            f"<div style='font-size:11px;color:#ccc;margin-bottom:4px;'>{label}</div>"
            f"<div style='font-size:20px;font-weight:800;color:#fff;'>{value}</div>"
            f"</div>"
        )

    backend = pnl_tracker.storage_backend()
    st.markdown(
        f"<div style='font-size:11px; color:#888888; margin-bottom:12px; "
        f"background:#110000; border:1px solid #330000; border-radius:6px; padding:8px 14px;'>"
        f"Storage: <b style='color:{'#4ade80' if backend=='sheets' else '#FFD700'}'>"
        f"{'☁️ Google Sheets — persistent across deploys' if backend=='sheets' else '💾 Local CSV — resets on redeploy'}"
        f"</b></div>",
        unsafe_allow_html=True,
    )

    # Pending-picks nudge — surfaces unsettled work without blocking
    try:
        _pending_count = sum(
            1 for r in pnl_tracker._load_results()
            if r.get("profit_loss", "") in ("", None)
        )
        if _pending_count > 0:
            st.info(
                f"⏳ {_pending_count} pick{'s' if _pending_count != 1 else ''} "
                "pending settlement. Expand **Settle Yesterday's Results** below "
                "or enter results manually in the Pending Results section."
            )
    except Exception:
        pass

    # ── Recency filter ────────────────────────────────────────────────────────
    _WINDOWS = {"7D": 7, "14D": 14, "30D": 30, "All": None}
    _pw_cols = st.columns(len(_WINDOWS))
    _cur_win = st.session_state.get("perf_window", "All")
    for _wi, (_wlabel, _wdays) in enumerate(_WINDOWS.items()):
        with _pw_cols[_wi]:
            _btn_type = "primary" if _wlabel == _cur_win else "secondary"
            if st.button(_wlabel, key=f"pw_{_wlabel}", type=_btn_type,
                         use_container_width=True):
                st.session_state["perf_window"] = _wlabel
                st.rerun()
    _win_days = _WINDOWS[_cur_win]
    if _win_days:
        from datetime import date as _dclass, timedelta as _tdclass
        _cutoff_date = (_dclass.today() - _tdclass(days=_win_days)).isoformat()
        st.caption(f"Showing last {_win_days} days (since {_cutoff_date})")
    else:
        _cutoff_date = None
        st.caption("Showing all-time performance")

    # Quick-settle button — contextually placed where it's relevant
    with st.expander("✅ Settle Yesterday's Results", expanded=False):
        st.caption("Fetch yesterday's game outcomes from MLB Stats API and settle all pending picks.")
        if st.button("✅ Update Yesterday's Results", key="perf_update_yesterday"):
            with st.spinner("Fetching outcomes from MLB…"):
                try:
                    _settle_res = pnl_tracker.update_yesterday()
                    st.success(
                        f"Settled {_settle_res['settled']} pick(s). "
                        f"{_settle_res['not_found']} not found."
                    )
                except Exception as _se:
                    st.error(f"Error: {_se}")

    # Load and filter raw data once — everything below uses these filtered lists
    try:
        _all_results_raw = pnl_tracker._load_results()
        _all_picks_raw   = pnl_tracker.get_picks_log()
    except Exception as e:
        st.error(f"Error loading performance data: {e}")
        return

    if _cutoff_date:
        _all_results_raw = [r for r in _all_results_raw if r.get("date", "") >= _cutoff_date]
        _all_picks_raw   = [r for r in _all_picks_raw   if r.get("date", "") >= _cutoff_date]

    # Compute summary from filtered results
    _res_map = {r.get("player_name","") + "|" + r.get("date",""): r for r in _all_results_raw}

    def _filtered_summary(results: list) -> dict:
        total_bet, total_profit, wins, losses, pending = 0.0, 0.0, 0, 0, 0
        for row in results:
            bet = float(row.get("bet_dollars") or 0)
            pl  = row.get("profit_loss", "")
            total_bet += bet
            if pl in ("", None):
                pending += 1
            else:
                try:
                    profit = float(pl)
                    total_profit += profit
                    if profit > 0: wins += 1
                    else:          losses += 1
                except (ValueError, TypeError):
                    pending += 1
        decided = wins + losses
        return {
            "total_picks": decided + pending, "wins": wins, "losses": losses,
            "pending": pending,
            "win_rate": wins / decided if decided else 0,
            "total_wagered": total_bet, "total_profit": total_profit,
            "roi_pct": total_profit / total_bet * 100 if total_bet > 0 else 0,
        }

    summary = _filtered_summary(_all_results_raw)
    try:
        clv = clv_tracker.clv_summary()
    except Exception:
        clv = {}

    st.markdown('<div class="section-header">📊 Running P&L</div>', unsafe_allow_html=True)

    if summary and (summary.get("wins", 0) + summary.get("losses", 0)) > 0:

        win_rate  = summary.get("win_rate", 0) * 100
        roi       = summary.get("roi_pct", 0)
        net_pnl   = summary.get("total_profit", 0)
        wins      = summary.get("wins", 0)
        losses    = summary.get("losses", 0)

        win_css = ("#14532d" if win_rate >= 60 else "#166534" if win_rate >= 50
                   else "#7f1d1d" if win_rate >= 40 else "#450a0a")
        roi_css = ("#14532d" if roi >= 20 else "#166534" if roi > 0
                   else "#7f1d1d" if roi >= -10 else "#450a0a")
        pnl_css = ("#14532d" if net_pnl >= 20 else "#166534" if net_pnl > 0
                   else "#7f1d1d" if net_pnl >= -20 else "#450a0a")
        wl_css  = ("#14532d" if wins > losses else "#166534" if wins == losses
                   else "#7f1d1d" if losses <= wins * 1.5 else "#450a0a")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(_pnl_box("Total Picks",   str(summary.get("total_picks", 0)), "#1a1a2e"), unsafe_allow_html=True)
        c2.markdown(_pnl_box("Win Rate",      f"{win_rate:.1f}%",                 win_css),  unsafe_allow_html=True)
        c3.markdown(_pnl_box("Total Wagered", f"${summary.get('total_wagered',0):,.0f}", "#1a1a2e"), unsafe_allow_html=True)
        c4.markdown(_pnl_box("Net P&L",       f"${net_pnl:+,.2f}",               pnl_css),  unsafe_allow_html=True)
        c5.markdown(_pnl_box("ROI",           f"{roi:+.1f}%",                     roi_css),  unsafe_allow_html=True)

        col_w, col_l, col_p = st.columns(3)
        col_w.markdown(_pnl_box("Wins",    str(wins),                      "#14532d" if wins > 0 else "#1a1a2e"), unsafe_allow_html=True)
        col_l.markdown(_pnl_box("Losses",  str(losses),                    "#7f1d1d" if losses > 0 else "#1a1a2e"), unsafe_allow_html=True)
        col_p.markdown(_pnl_box("Pending", str(summary.get("pending", 0)), "#1a1a2e"), unsafe_allow_html=True)
    else:
        logged = _all_picks_raw
        if logged:
            pending_count = len(logged)
            backend = pnl_tracker.storage_backend()
            if backend == "csv":
                storage_note = "⚠️ Local CSV storage — picks won't survive a Streamlit Cloud restart. Configure Google Sheets for persistence."
            else:
                storage_note = f"Storage: Google Sheets"
            st.info(
                f"**{pending_count} pick{'s' if pending_count != 1 else ''} logged, no settled results yet.**  \n"
                f"After yesterday's games finish, use **Update Yesterday** in the sidebar to settle outcomes and populate P&L.  \n"
                f"{storage_note}"
            )
        else:
            st.info("No picks logged yet. Load the **Main** tab to auto-log today's selections.")

    if clv:
        st.markdown('<div class="section-header">🎯 Closing Line Value</div>',
                    unsafe_allow_html=True)
        verdict   = clv.get("verdict", "N/A")
        avg_clv   = clv.get("avg_clv_pct", 0)
        beat_close = clv.get("pct_beating_close", 0)
        clv_css   = "#14532d" if avg_clv >= 1 else "#166534" if avg_clv > 0 else "#7f1d1d" if avg_clv >= -0.5 else "#450a0a"
        beat_css  = "#14532d" if beat_close >= 60 else "#166534" if beat_close >= 50 else "#7f1d1d" if beat_close >= 40 else "#450a0a"
        v_css     = {"SHARP": "#14532d", "NEUTRAL": "#1a1a2e", "SOFT": "#450a0a"}.get(verdict, "#1a1a2e")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(_pnl_box("CLV Picks",  str(clv.get("picks_with_clv", 0)), "#1a1a2e"), unsafe_allow_html=True)
        c2.markdown(_pnl_box("Avg CLV",    f"{avg_clv:+.2f}%",               clv_css),   unsafe_allow_html=True)
        c3.markdown(_pnl_box("Beat Close", f"{beat_close:.1f}%",             beat_css),  unsafe_allow_html=True)
        c4.markdown(_pnl_box("Verdict",    verdict,                           v_css),     unsafe_allow_html=True)

    # ── P&L by Rating Tier ────────────────────────────────────────────────────
    try:
        _all_picks   = _all_picks_raw
        _all_results = _res_map
        if _all_picks and _all_results:
            def _pick_tier(ev, edge, conf):
                try:
                    ev_f = float(ev); edge_f = float(edge); conf_f = float(conf)
                except (ValueError, TypeError):
                    return "📊 MARGINAL"
                if ev_f >= 30 and edge_f >= 12 and conf_f >= 65:
                    return "🌟 ONCE IN A LIFETIME"
                if (ev_f >= 18 and edge_f >= 7 and conf_f >= 50) or \
                   (ev_f >= 12 and edge_f >= 5 and conf_f >= 50):
                    return "🔥 STRONG EDGE"
                if ev_f >= 5 and edge_f >= 2:
                    return "✅ SOLID PLAY"
                return "📊 MARGINAL"

            tier_stats: dict[str, dict] = {}
            for pick in _all_picks:
                key = pick.get("player_name", "") + "|" + pick.get("date", "")
                result = _all_results.get(key)
                if result is None:
                    continue
                tier = _pick_tier(pick.get("ev_pct", 0), pick.get("edge_pct", 0),
                                  pick.get("confidence", 0))
                pl_str = result.get("profit_loss", "")
                if pl_str == "" or pl_str is None:
                    continue
                try:
                    pl = float(pl_str)
                except (ValueError, TypeError):
                    continue
                bet_str = result.get("bet_dollars", "0") or "0"
                try:
                    bet = float(bet_str)
                except (ValueError, TypeError):
                    bet = 0.0
                ts = tier_stats.setdefault(tier, {"wins": 0, "losses": 0, "wagered": 0.0, "profit": 0.0})
                ts["wagered"] += bet
                ts["profit"]  += pl
                if pl > 0:
                    ts["wins"] += 1
                else:
                    ts["losses"] += 1

            if tier_stats:
                st.markdown('<div class="section-header">🏆 Performance by Rating Tier</div>',
                            unsafe_allow_html=True)
                _TIER_ORDER = ["🌟 ONCE IN A LIFETIME", "🔥 STRONG EDGE", "✅ SOLID PLAY", "📊 MARGINAL"]
                tier_rows = []
                for tier in _TIER_ORDER:
                    ts = tier_stats.get(tier)
                    if not ts:
                        continue
                    decided = ts["wins"] + ts["losses"]
                    wr = ts["wins"] / decided * 100 if decided else 0
                    roi = ts["profit"] / ts["wagered"] * 100 if ts["wagered"] > 0 else 0
                    tier_rows.append({
                        "Tier":    tier,
                        "Picks":   decided,
                        "Wins":    ts["wins"],
                        "Losses":  ts["losses"],
                        "Win%":    f"{wr:.1f}%",
                        "Wagered": f"${ts['wagered']:,.0f}",
                        "P&L":     f"${ts['profit']:+,.2f}",
                        "ROI":     f"{roi:+.1f}%",
                    })
                if tier_rows:
                    st.dataframe(pd.DataFrame(tier_rows), hide_index=True, use_container_width=True)
                    st.caption("Tier assigned at pick time using EV%, Edge%, and Confidence — same logic as the Rating column in Main.")
    except Exception as e:
        st.warning(f"Performance by tier unavailable: {e}")

    # ── Bankroll equity curve ─────────────────────────────────────────────────
    try:
        _eq_picks   = _all_picks_raw
        _eq_results = _res_map
        if _eq_picks and _eq_results:
            _eq_rows = []
            for pick in _eq_picks:
                key = pick.get("player_name", "") + "|" + pick.get("date", "")
                res = _eq_results.get(key)
                if res is None:
                    continue
                pl_str = res.get("profit_loss", "")
                if pl_str in ("", None):
                    continue
                try:
                    pl = float(pl_str)
                except (ValueError, TypeError):
                    continue
                _eq_rows.append({"date": pick.get("date", ""), "pl": pl})
            if _eq_rows:
                _eq_rows.sort(key=lambda r: r["date"])
                cumulative = 0.0
                eq_chart_rows = []
                for r in _eq_rows:
                    cumulative += r["pl"]
                    eq_chart_rows.append({"Date": r["date"], "Cumulative P&L ($)": round(cumulative, 2)})
                st.markdown('<div class="section-header">📈 Bankroll Equity Curve</div>',
                            unsafe_allow_html=True)
                st.line_chart(pd.DataFrame(eq_chart_rows).set_index("Date"), height=220)
                st.caption("Running cumulative P&L across all settled picks, sorted by date.")

                # ── Daily P&L bar chart ───────────────────────────────────────
                from collections import defaultdict as _dd2
                _daily: dict = _dd2(float)
                for r in _eq_rows:
                    _daily[r["date"]] += r["pl"]
                if len(_daily) >= 2:
                    _daily_dates = sorted(_daily.keys())
                    _daily_rows  = [{"Date": d, "Daily P&L ($)": round(_daily[d], 2)}
                                    for d in _daily_dates]
                    _daily_df = pd.DataFrame(_daily_rows).set_index("Date")
                    st.markdown('<div class="section-header">📊 Daily P&L</div>',
                                unsafe_allow_html=True)
                    st.bar_chart(_daily_df, height=200)
                    # Best / worst day callout
                    _best_day  = max(_daily.items(), key=lambda x: x[1])
                    _worst_day = min(_daily.items(), key=lambda x: x[1])
                    _dc1, _dc2, _dc3 = st.columns(3)
                    _dc1.metric("Best Day",  f"${_best_day[1]:+.2f}",  _best_day[0])
                    _dc2.metric("Worst Day", f"${_worst_day[1]:+.2f}", _worst_day[0])
                    _profitable_days = sum(1 for v in _daily.values() if v > 0)
                    _dc3.metric("Profitable Days",
                                f"{_profitable_days}/{len(_daily)}",
                                f"{_profitable_days/len(_daily)*100:.0f}%")
                    st.caption("Green = profitable day · Red = losing day. Each bar is the net P&L across all settled picks for that date.")
    except Exception as e:
        st.warning(f"Equity curve unavailable: {e}")

    # ── Calibration curve ─────────────────────────────────────────────────────
    try:
        _cal_picks   = _all_picks_raw
        _cal_results = _res_map
        if _cal_picks and _cal_results:
            BUCKETS = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, 100)]
            bucket_data: dict[str, list] = {f"{lo}-{hi}%": [] for lo, hi in BUCKETS}
            for pick in _cal_picks:
                key = pick.get("player_name", "") + "|" + pick.get("date", "")
                res = _cal_results.get(key)
                if res is None:
                    continue
                hr_res = res.get("hr_result", "")
                if hr_res not in ("1", "0", 1, 0):
                    continue
                try:
                    model_pct = float(pick.get("model_prob_pct", 0) or pick.get("model_prob", 0))
                    if model_pct <= 1:
                        model_pct = model_pct * 100
                    hit = int(hr_res)
                except (ValueError, TypeError):
                    continue
                for lo, hi in BUCKETS:
                    if lo <= model_pct < hi:
                        bucket_data[f"{lo}-{hi}%"].append((model_pct, hit))
                        break
            cal_rows = []
            for label, items in bucket_data.items():
                if len(items) < 3:
                    continue
                avg_pred = sum(m for m, _ in items) / len(items)
                avg_act  = sum(h for _, h in items) / len(items) * 100
                cal_rows.append({"Bucket": label, "Avg Model%": round(avg_pred, 1),
                                 "Actual HR%": round(avg_act, 1), "N": len(items)})
            if cal_rows:
                st.markdown('<div class="section-header">🎯 Model Calibration</div>',
                            unsafe_allow_html=True)
                st.caption(
                    "Each row: average model probability vs actual HR rate for picks in that probability bucket. "
                    "Well-calibrated = Avg Model% ≈ Actual HR%. "
                    "Consistent over-prediction means the model is too aggressive; under-prediction means it's conservative."
                )
                cal_df = pd.DataFrame(cal_rows)
                st.dataframe(cal_df, hide_index=True, use_container_width=True)
                st.bar_chart(cal_df.set_index("Bucket")[["Avg Model%", "Actual HR%"]], height=220)
    except Exception as e:
        st.warning(f"Calibration chart unavailable: {e}")

    # ── Manual Result Entry ───────────────────────────────────────────────────
    # Always uses unfiltered data — pending picks need resolution regardless of window
    try:
        from datetime import date as _today_cls
        _all_log     = pnl_tracker.get_picks_log()
        _all_results = {
            r.get("player_name","") + "|" + r.get("date",""): r
            for r in pnl_tracker._load_results()
        }
        _yesterday   = (_today_cls.today() - _td(days=1)).isoformat()
        _today_str   = _today_cls.today().isoformat()
        # Pending = logged but not yet in results with a definitive hr_result
        _pending = [
            r for r in _all_log
            if r.get("date", "") < _today_str            # only past picks
            and _all_results.get(
                r.get("player_name", "") + "|" + r.get("date", ""), {}
            ).get("hr_result", "") == ""
        ]
        if _pending:
            st.markdown('<div class="section-header">⏳ Pending Results</div>',
                        unsafe_allow_html=True)
            st.caption("Mark each pick Won or Lost to update P&L. The MLB API auto-settles yesterday's picks — use these buttons if a result is missing.")
            for _pr in _pending:
                _pr_name  = _pr.get("player_name", "")
                _pr_date  = _pr.get("date", "")
                _pr_odds  = _pr.get("american_odds", "")
                _pr_bet   = _pr.get("bet_dollars", "")
                _pr_team  = _pr.get("team", "")
                _pr_model = _pr.get("model_prob_pct", "")
                try:
                    _pr_odds_fmt = _fmt_american(int(float(_pr_odds))) if _pr_odds else "--"
                except (ValueError, TypeError):
                    _pr_odds_fmt = str(_pr_odds)
                _pc1, _pc2, _pc3, _pc4 = st.columns([5, 2, 1, 1])
                with _pc1:
                    st.markdown(
                        f"<div style='font-size:13px; color:#f0f0f0; font-weight:600;'>"
                        f"{_pr_name} <span style='color:#555; font-size:11px;'>({_pr_team})</span></div>"
                        f"<div style='font-size:11px; color:#888;'>"
                        f"{_pr_date} &nbsp;·&nbsp; {_pr_odds_fmt} &nbsp;·&nbsp; "
                        f"${_pr_bet} &nbsp;·&nbsp; Model {_pr_model}%</div>",
                        unsafe_allow_html=True,
                    )
                with _pc2:
                    st.write("")  # spacer
                with _pc3:
                    if st.button("✅ HR", key=f"res_win_{_pr_name}_{_pr_date}", use_container_width=True):
                        pnl_tracker.update_results(_pr_date, {_pr_name: True})
                        st.toast(f"Marked {_pr_name} ✅ HR on {_pr_date}")
                        st.rerun()
                with _pc4:
                    if st.button("❌ No", key=f"res_loss_{_pr_name}_{_pr_date}", use_container_width=True):
                        pnl_tracker.update_results(_pr_date, {_pr_name: False})
                        st.toast(f"Marked {_pr_name} ❌ No HR on {_pr_date}")
                        st.rerun()
    except Exception as _re:
        st.warning(f"Could not load pending results: {_re}")

    st.markdown('<div class="section-header">📋 Picks Log</div>', unsafe_allow_html=True)
    try:
        _log_picks   = _all_picks_raw
        _log_results = _res_map
        if _log_picks:
            _log_rows = []
            for _lp in _log_picks:
                _lp_name  = _lp.get("player_name", "")
                _lp_date  = _lp.get("date", "")
                _lp_key   = f"{_lp_name}|{_lp_date}"
                _lp_res   = _log_results.get(_lp_key, {})
                _lp_hr    = _lp_res.get("hr_result", "")
                _lp_pl    = _lp_res.get("profit_loss", "")

                # Result display
                if _lp_hr in ("1", 1):
                    _res_str = "✅ HR"
                elif _lp_hr in ("0", 0):
                    _res_str = "❌ No HR"
                elif _lp_date >= _dt.date.today().isoformat():
                    _res_str = "🔄 Today"
                else:
                    _res_str = "⏳ Pending"

                # P&L display
                try:
                    _pl_val  = float(_lp_pl)
                    _pl_str  = f"${_pl_val:+.2f}"
                except (TypeError, ValueError):
                    _pl_str  = "--"

                # Odds formatting
                try:
                    _odds_raw = _lp.get("american_odds", "")
                    _odds_fmt = _fmt_american(int(float(_odds_raw))) if _odds_raw else "--"
                except (TypeError, ValueError):
                    _odds_fmt = str(_lp.get("american_odds", "--"))

                # Bet size formatting
                try:
                    _bet_val = float(_lp.get("bet_dollars") or 0)
                    _bet_str = f"${_bet_val:.0f}"
                except (TypeError, ValueError):
                    _bet_str = "--"

                # Model prob formatting
                try:
                    _mp_raw = _lp.get("model_prob_pct", "")
                    _mp_val = float(_mp_raw)
                    _mp_str = f"{_mp_val:.1f}%"
                except (TypeError, ValueError):
                    _mp_str = "--"

                try:
                    _lp_conf = float(_lp.get("confidence", 0) or 0)
                except (TypeError, ValueError):
                    _lp_conf = 0.0
                _lp_tier = ("🌟 S" if _lp_conf >= 70 else "✅ A" if _lp_conf >= 55
                            else "🟡 B" if _lp_conf >= 40 else "🔴 C") if _lp_conf > 0 else ""
                _log_rows.append({
                    "Tier":     _lp_tier,
                    "Date":     _lp_date,
                    "Player":   _lp_name,
                    "Team":     _lp.get("team", ""),
                    "Pitcher":  _lp.get("pitcher", ""),
                    "Model%":   _mp_str,
                    "Odds":     _odds_fmt,
                    "Bet":      _bet_str,
                    "EV%":      f"{float(_lp.get('ev_pct', 0) or 0):+.1f}%",
                    "Result":   _res_str,
                    "P&L":      _pl_str,
                })

            _log_df = pd.DataFrame(_log_rows)

            # Summary footer row
            _settled = [r for r in _log_rows if r["Result"] in ("✅ HR", "❌ No HR")]
            if _settled:
                _tot_pl = sum(
                    float(_log_results.get(f"{r['Player']}|{r['Date']}", {}).get("profit_loss", 0) or 0)
                    for r in _settled
                )
                _n_win  = sum(1 for r in _settled if r["Result"] == "✅ HR")
                _wr     = _n_win / len(_settled) * 100
                st.caption(
                    f"**{len(_log_picks)} picks logged** · "
                    f"**{len(_settled)} settled** · "
                    f"Win rate: **{_wr:.0f}%** ({_n_win}W / {len(_settled) - _n_win}L) · "
                    f"Net P&L: **${_tot_pl:+.2f}**"
                )

            st.dataframe(
                _log_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Result": st.column_config.TextColumn("Result", width="small"),
                    "P&L":    st.column_config.TextColumn("P&L",    width="small"),
                    "Model%": st.column_config.TextColumn("Model%", width="small"),
                    "Odds":   st.column_config.TextColumn("Odds",   width="small"),
                    "Bet":    st.column_config.TextColumn("Bet",    width="small"),
                    "EV%":    st.column_config.TextColumn("EV%",    width="small"),
                },
            )
        else:
            st.caption("No picks logged yet — open Main tab to auto-log.")
    except Exception as e:
        st.error(f"Could not load picks log: {e}")

    # ── Model Insights & Auto-Learn ──────────────────────────────────────────
    st.divider()
    st.markdown('<div class="section-header">🧠 MODEL INSIGHTS & AUTO-LEARN</div>',
                unsafe_allow_html=True)
    try:
        from tracking import auto_learn as _al
        from tracking import pick_tracker as _pt
        import pandas as _pd_al

        _all_pt_rows = _pt.load_all()
        _pt_summary  = _pt.total_summary(_all_pt_rows)
        _pt_tab_perf = _pt.summary_by("source_tab",     _all_pt_rows)
        _pt_sec_perf = _pt.summary_by("source_section", _all_pt_rows)
        _n_settled   = _pt_summary.get("decided", 0)
        _n_total     = _pt_summary.get("picks", 0)

        if _n_total > 0:
            _ov = st.columns(5)
            _ov[0].metric("Tracked Picks", _n_total)
            _ov[1].metric("Settled", _n_settled)
            _ov[2].metric("Win Rate",  f"{_pt_summary.get('win_rate',0)*100:.1f}%" if _n_settled else "—")
            _ov[3].metric("Net P&L",   f"${_pt_summary.get('profit',0):+.2f}"       if _n_settled else "—")
            _ov[4].metric("ROI",       f"{_pt_summary.get('roi',0):+.1f}%"          if _n_settled else "—")
        else:
            st.info("No picks tracked yet. Add players to your FD Slip from any tab — "
                    "they are logged automatically with their source. "
                    "Results settle when you click **Update Yesterday** in the sidebar.")

        if _pt_tab_perf:
            with st.expander(f"📊 Performance by Tab ({len(_pt_tab_perf)} sources)", expanded=_n_settled >= 5):
                _tab_df = _pd_al.DataFrame(_pt_tab_perf).rename(columns={"source_tab": "Tab"})
                _disp = ["Tab","Picks","Wins","Losses","Pending","Win%","Net P&L","ROI%","Last Pick"]
                st.dataframe(_tab_df[_disp], hide_index=True, use_container_width=True)
                _sec_decided = [r for r in _pt_sec_perf if r["_decided"] >= 3]
                if _sec_decided:
                    st.markdown("**By Section / Strategy** (≥3 settled picks)")
                    _sec_df = _pd_al.DataFrame(_sec_decided).rename(columns={"source_section": "Section"})
                    st.dataframe(_sec_df[["Section","Picks","Wins","Losses","Win%","Net P&L","ROI%"]],
                                 hide_index=True, use_container_width=True)

        if _n_settled >= 15:
            @st.cache_data(ttl=300, show_spinner=False)
            def _cached_analyze():
                from tracking import auto_learn as _al_inner
                return _al_inner.analyze()
            _analysis = _cached_analyze()
            if _analysis.get("sufficient_data"):
                with st.expander(f"🔬 Feature Analysis ({_n_settled} settled picks)", expanded=False):
                    st.markdown("#### Which factors actually predict home runs?")
                    st.caption("Point-biserial correlation with actual HR outcomes. "
                               "Green = strong predictor. Red = may be noise or reversed.")
                    _corrs = _analysis.get("correlations", [])
                    if _corrs:
                        _corr_rows = [{"Factor": c["label"], "Correlation": f"{c['corr']:+.4f}",
                                       "Strength": c["strength"], "N": c["n"]} for c in _corrs]
                        def _cc(val):
                            try:
                                v = float(val)
                                if v >= 0.15:  return "color:#4ade80;font-weight:700"
                                if v >= 0.05:  return "color:#86efac"
                                if v <= -0.10: return "color:#f87171"
                                return "color:#888"
                            except (ValueError, TypeError):
                                return ""
                        st.dataframe(_pd_al.DataFrame(_corr_rows).style.applymap(_cc, subset=["Correlation"]),
                                     hide_index=True, use_container_width=True)

                    _calib = _analysis.get("calibration", [])
                    if _calib:
                        st.markdown("#### Model Calibration — Predicted vs Actual Hit Rate")
                        _cal_df = _pd_al.DataFrame(_calib).rename(columns={
                            "bucket": "Model%", "avg_predicted": "Predicted%",
                            "avg_actual": "Actual%", "bias_pct": "Bias(pp)", "n": "N"})
                        def _cb(val):
                            try:
                                v = float(str(val))
                                if abs(v) <= 2: return "color:#4ade80"
                                if abs(v) <= 5: return "color:#f59e0b"
                                return "color:#f87171"
                            except (ValueError, TypeError):
                                return ""
                        st.dataframe(_cal_df.style.applymap(_cb, subset=["Bias(pp)"]),
                                     hide_index=True, use_container_width=True)


                _suggestions = _analysis.get("suggestions", [])
                if _suggestions:
                    with st.expander(f"💡 Adjustment Suggestions ({len(_suggestions)})", expanded=False):
                        st.caption("Derived from your settled pick history. Click Apply to persist a change to "
                                   "learned_adjustments.json — the engine reads this on next refresh.")
                        _applied = _analysis.get("applied_adjustments", {})
                        for _sug in _suggestions:
                            _ic = {"high":"#f87171","medium":"#f59e0b","low":"#888"}.get(_sug.get("impact","low"),"#888")
                            _sid = _sug["id"]
                            _done = _sid in _applied
                            st.markdown(
                                f"<div style='background:#0d0d1a;border:1px solid #1a1a3a;"
                                f"border-radius:8px;padding:10px 14px;margin-bottom:8px;'>"
                                f"<div style='font-size:13px;font-weight:700;color:#f0f0f0;'>"
                                f"#{_sug['sid']} {_sug['title']}</div>"
                                f"<div style='font-size:11px;color:#888;margin-top:4px;'>{_sug['detail']}</div>"
                                f"<div style='font-size:10px;color:{_ic};margin-top:6px;'>"
                                f"Impact: {_sug.get('impact','?').upper()}"
                                f"{'  ·  ✅ Applied' if _done else ''}</div></div>",
                                unsafe_allow_html=True)
                            if not _done:
                                if st.button(f"✅ Apply #{_sug['sid']}", key=f"apply_{_sid}", type="primary"):
                                    if _al.apply_suggestion(_sid):
                                        st.success(f"Suggestion #{_sug['sid']} applied!")
                                        st.rerun()
                        _rc, _ = st.columns([1, 3])
                        with _rc:
                            if st.button("🔄 Reset Adjustments", key="reset_adj", type="secondary"):
                                _al.reset_adjustments()
                                st.success("Cleared.")
                                st.rerun()
        elif _n_total > 0:
            st.caption(f"💡 Feature analysis unlocks after {max(0,15-_n_settled)} more settled picks "
                       f"({_n_settled} settled so far).")
    except Exception as _al_err:
        st.caption(f"Model insights unavailable: {_al_err}")


#â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAIN
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def main():
    # Fire player detail modal if one was queued (pop so it only shows once)
    if "show_modal" in st.session_state:
        _show_player_modal(st.session_state.pop("show_modal"))

    # Read filter thresholds from session state first (sidebar sets them on each rerun)
    _min_ev   = float(st.session_state.get("min_ev",   config.MIN_EV_PCT))
    _min_edge = float(st.session_state.get("min_edge", config.MIN_EDGE_PCT))
    _min_conf = int(st.session_state.get("min_confidence", 0))


    # â"€â"€ Sidebar â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding:18px 0 14px 0;
          background: linear-gradient(180deg, rgba(198,1,31,0.18) 0%, transparent 100%);
          border-bottom: 2px solid #C6011F; margin-bottom:4px;'>
          <div style='font-size:26px; font-weight:900; color:#C6011F;
            letter-spacing:3px; text-shadow:0 0 20px rgba(198,1,31,0.7);'>⚾ Codex HR Engine</div>
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
            key="bankroll_input",
        )
        if new_br != st.session_state.get("bankroll_override"):
            st.session_state["bankroll_override"] = new_br

        # Show current bankroll = input + cumulative settled P&L
        try:
            _br_results = _cached_pnl_results()
            _br_pnl = sum(
                float(r.get("profit_loss", 0) or 0)
                for r in _br_results
                if r.get("profit_loss", "") not in ("", None)
            )
            _br_current = new_br + _br_pnl
            _br_color   = "#4ade80" if _br_pnl >= 0 else "#f87171"
            _br_today   = sum(
                float(r.get("profit_loss", 0) or 0)
                for r in _br_results
                if r.get("date", "") == _dt.date.today().isoformat()
                and r.get("profit_loss", "") not in ("", None)
            )
            _br_today_str = (f" &nbsp;·&nbsp; Today: "
                             f"<b style='color:{'#4ade80' if _br_today >= 0 else '#f87171'}'>"
                             f"${_br_today:+.0f}</b>") if _br_today != 0 else ""
            st.markdown(
                f"<div style='font-size:12px; color:#888; margin-top:2px;'>"
                f"Current: <b style='color:{_br_color}'>${_br_current:,.0f}</b>"
                f" <span style='color:#555'>(${_br_pnl:+.0f} P&L)</span>"
                f"{_br_today_str}"
                f"</div>",
                unsafe_allow_html=True,
            )
        except Exception:
            pass

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
        _min_conf = st.slider(
            "Min Confidence",
            min_value=0, max_value=80,
            value=int(st.session_state.get("min_confidence", 0)),
            step=5,
            help=(
                "Filter picks by confidence score (0 = no filter).\n\n"
                "🔴 C-Tier: 0–39  —  noisy, small sample, or weak market\n"
                "🟡 B-Tier: 40–54  —  solid, worth standard size\n"
                "✅ A-Tier: 55–69  —  strong, core targets\n"
                "🌟 S-Tier: 70+   —  elite, act with full conviction\n\n"
                "Set to 40 to hide C-Tier plays. Set to 55 for A/S only."
            ),
        )
        st.session_state["min_ev"]         = _min_ev
        st.session_state["min_edge"]       = _min_edge
        st.session_state["min_confidence"] = _min_conf

        st.divider()

        # ── Portfolio Optimizer ───────────────────────────────────────────────
        st.markdown("#### 🎯 Portfolio Optimizer")
        _opt_on = st.toggle(
            "Enable optimizer",
            value=st.session_state.get("optimizer_on", False),
            key="optimizer_on",
            help=(
                "Filters today's picks to a focused, diversified slate using the portfolio optimizer. "
                "Caps exposure per team, removes low-quality picks, and prioritizes barrel rate."
            ),
        )
        if _opt_on:
            _opt_preset = st.selectbox(
                "Preset",
                options=["moderate", "conservative", "barrel_focused", "relaxed"],
                index=["moderate", "conservative", "barrel_focused", "relaxed"].index(
                    st.session_state.get("optimizer_preset", "moderate")
                ),
                format_func=lambda x: {
                    "moderate":       "Moderate (20 picks, 4/team)",
                    "conservative":   "Conservative (15 picks, 3/team, barrel≥6%)",
                    "barrel_focused": "Barrel-Focused (15 picks, 4/team, barrel≥8%)",
                    "relaxed":        "Relaxed (30 picks, 6/team)",
                }[x],
                label_visibility="collapsed",
                key="optimizer_preset_select",
            )
            st.session_state["optimizer_preset"] = _opt_preset
            _opt_result = st.session_state.get("optimizer_result")
            if _opt_result:
                _on = _opt_result.get("n_selected", 0)
                _om = _opt_result.get("n_input", 0)
                st.caption(f"✅ {_on}/{_om} picks selected · {_opt_preset}")
        else:
            st.session_state.pop("optimizer_preset", None)

        st.divider()

        # ── Game time gate ────────────────────────────────────────────────────
        st.markdown("#### ⏰ Game Time Cutoff")
        _time_gate_on = st.toggle(
            "Only show games starting after…",
            value=st.session_state.get("time_gate_on", False),
            key="time_gate_on",
        )
        _cutoff_utc_hour: int | None = None
        if _time_gate_on:
            import datetime as _dtlib
            _cutoff_et = st.time_input(
                "Start time (Eastern Time)",
                value=st.session_state.get(
                    "time_gate_et",
                    _dtlib.time(19, 0),   # default 7:00 PM ET
                ),
                step=900,               # 15-min steps
                label_visibility="collapsed",
                key="time_gate_et",
            )
            # MLB season runs in EDT (UTC-4). Convert ET cutoff → UTC hour.
            _cutoff_utc_hour = (_cutoff_et.hour + 4) % 24
            st.caption(
                f"Showing games starting at/after {_cutoff_et.strftime('%I:%M %p').lstrip('0')} ET "
                f"({_cutoff_utc_hour:02d}:00 UTC)"
            )
        st.session_state["cutoff_utc_hour"] = _cutoff_utc_hour

        st.divider()

        # ── FanDuel Slip ──────────────────────────────────────────────────────
        st.markdown("#### 🎰 FanDuel Slip")
        _slip_data = st.session_state.get("data")
        if _slip_data:
            _fd_min_ev   = float(st.session_state.get("min_ev",   config.MIN_EV_PCT))
            _fd_min_edge = float(st.session_state.get("min_edge", config.MIN_EDGE_PCT))
            _fd_min_conf = int(st.session_state.get("min_confidence", 0))
            _fd_cutoff   = st.session_state.get("cutoff_utc_hour")
            _fd_uif_fp   = (
                str(st.session_state.get("data_loaded_at", "")),
                _fd_min_ev, _fd_min_edge,
                _fd_cutoff if _fd_cutoff is not None else -1,
                _fd_min_conf,
            )
            if st.session_state.get("_uif_ranked_fp") == _fd_uif_fp:
                _odds_players = st.session_state["_uif_ranked"]
            else:
                _odds_players = _apply_ui_filters(
                    _slip_data.get("all_players", []), _fd_min_ev, _fd_min_edge,
                    cutoff_utc_hour=_fd_cutoff,
                    min_confidence=_fd_min_conf,
                )
                st.session_state["_uif_ranked"] = _odds_players
                st.session_state["_uif_ranked_fp"] = _fd_uif_fp
            if not _odds_players:
                _odds_players = sorted(
                    [p for p in _slip_data.get("all_players", []) if p.get("best_american")],
                    key=lambda x: x.get("score", 0), reverse=True,
                )

            def _slip_label(p):
                odds = p.get("fanduel_american") or p.get("best_american")
                return f"{p['player_name']} ({p.get('team', '')}) {_fmt_american(odds)}"

            _slip_opts = [_slip_label(p) for p in _odds_players]
            _slip_map  = {_slip_label(p): p for p in _odds_players}
            _current   = [s for s in st.session_state.get("fd_slip", []) if s in _slip_opts]

            _selected = st.multiselect(
                "Add to slip",
                options=_slip_opts,
                default=_current,
                placeholder="Search players…",
                label_visibility="collapsed",
                key="fd_slip_select",
            )
            st.session_state["fd_slip"] = _selected

            if _selected:
                _slip_now_et = _dt.datetime.now(_EDT)
                # Sort slip by game time so earliest games appear first
                _selected_sorted = sorted(
                    _selected,
                    key=lambda s: (
                        (lambda t: t.hour * 60 + t.minute if t else 9999)(
                            _game_time_et(_slip_map[s].get("game_time_utc", ""))
                        )
                    )
                )
                for i, s in enumerate(_selected_sorted):
                    p = _slip_map[s]
                    fd_odds   = p.get("fanduel_american")
                    best_odds = p.get("best_american")
                    odds_val  = fd_odds if fd_odds else best_odds
                    odds_lbl  = "FD" if fd_odds else "Best"
                    ev        = p.get("ev_pct", 0)
                    edge      = p.get("edge_pct", 0)
                    ev_color  = "#4ade80" if ev >= 0 else "#f87171"
                    edge_color = _edge_col(edge)
                    url       = _fanduel_url(p["player_name"])

                    # Game time + urgency
                    _sgt = _game_time_et(p.get("game_time_utc", ""))
                    if _sgt:
                        _sgt_str = _sgt.strftime('%I:%M %p ET').lstrip('0')
                        _sgt_dt  = _dt.datetime.combine(_slip_now_et.date(), _sgt, tzinfo=_EDT)
                        _smins   = int((_sgt_dt - _slip_now_et).total_seconds() / 60)
                        if _smins < 0:
                            _surg_col = "#555"
                            _surg_lbl = "In progress"
                        elif _smins < 60:
                            _surg_col = "#FF6666"
                            _surg_lbl = f"BET NOW · {_smins}m"
                        elif _smins < 120:
                            _surg_col = "#FFD700"
                            _surg_lbl = f"{_smins}m"
                        else:
                            _surg_col = "#4ade80"
                            _surg_lbl = f"{_smins//60}h {_smins%60}m"
                        _time_html = (
                            f"<span style='color:#888; font-size:10px;'>🕐 {_sgt_str}</span>"
                            f"  <span style='color:{_surg_col}; font-size:10px; "
                            f"font-weight:700;'>{_surg_lbl}</span>"
                        )
                    else:
                        _time_html = "<span style='color:#555; font-size:10px;'>🕐 TBD</span>"

                    _c_card, _c_rm = st.columns([9, 1])
                    with _c_card:
                        st.markdown(
                            f"<div style='background:#0a0a1a; border:1px solid #1a1a3a; "
                            f"border-radius:6px; padding:7px 10px; margin-bottom:2px; font-size:12px;'>"
                            f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                            f"<span><b style='color:#f0f0f0'>{p['player_name']}</b> "
                            f"<span style='color:#555; font-size:11px'>{p.get('team','')}</span></span>"
                            f"<a href='{url}' target='_blank' "
                            f"style='color:#4488ff; font-size:11px; background:#0d0d2a; "
                            f"padding:2px 8px; border-radius:4px; border:1px solid #1a2a66; "
                            f"text-decoration:none;'>FD →</a>"
                            f"</div>"
                            f"<div style='margin-top:3px;'>{_time_html}</div>"
                            f"<div style='color:#888; margin-top:2px;'>"
                            f"{odds_lbl}: <b style='color:#FF6666'>{_fmt_american(odds_val)}</b>"
                            f" &nbsp;|&nbsp; EV: <b style='color:{ev_color}'>{ev:+.1f}%</b>"
                            f" &nbsp;|&nbsp; Edge: <b style='color:{edge_color}'>{edge:+.1f}%</b>"
                            f"</div></div>",
                            unsafe_allow_html=True,
                        )
                    with _c_rm:
                        if st.button("✕", key=f"slip_rm_{i}", help=f"Remove {p['player_name']}"):
                            _new_slip = [x for x in _selected if x != s]
                            st.session_state["fd_slip"] = _new_slip
                            st.session_state.pop("fd_slip_select", None)
                            st.rerun()
                # ── Parlay Summary ────────────────────────────────────────
                if len(_selected) >= 2:
                    _slip_players = [_slip_map[s] for s in _selected]
                    _par_dec = 1.0
                    _par_model_prob = 1.0
                    _par_valid = True
                    for _sp in _slip_players:
                        _sp_odds = _sp.get("fanduel_american") or _sp.get("best_american")
                        _sp_model = _sp.get("model_prob", 0)
                        if _sp_odds:
                            _o = int(_sp_odds)
                            _par_dec *= (_o / 100 + 1) if _o >= 100 else (100 / abs(_o) + 1)
                        else:
                            _par_valid = False
                        _par_model_prob *= _sp_model if _sp_model > 0 else 0.0
                    if _par_valid and _par_dec > 1:
                        _par_pct = _par_model_prob * 100
                        _par_implied = 1.0 / _par_dec * 100
                        _par_ev = (_par_model_prob * _par_dec - 1) * 100
                        _par_ev_col = "#4ade80" if _par_ev >= 0 else "#f87171"
                        _par_am = int((_par_dec - 1) * 100) if _par_dec >= 2 else int(-100 / (_par_dec - 1))
                        st.markdown(
                            f"<div style='background:#0d1a0d; border:1px solid #1a3a1a; "
                            f"border-radius:8px; padding:10px 12px; margin:8px 0 6px; font-size:12px;'>"
                            f"<div style='color:#4ade80; font-weight:700; margin-bottom:6px;'>"
                            f"📐 {len(_selected)}-Leg Parlay</div>"
                            f"<div style='display:flex; justify-content:space-between; margin-bottom:4px;'>"
                            f"<span style='color:#888;'>Combined odds</span>"
                            f"<span style='color:#f0f0f0; font-weight:700;'>{_fmt_american(_par_am)}</span>"
                            f"</div>"
                            f"<div style='display:flex; justify-content:space-between; margin-bottom:4px;'>"
                            f"<span style='color:#888;'>$10 → payout</span>"
                            f"<span style='color:#f0f0f0; font-weight:700;'>${10 * _par_dec:.0f}</span>"
                            f"</div>"
                            f"<div style='display:flex; justify-content:space-between; margin-bottom:4px;'>"
                            f"<span style='color:#888;'>Model hit prob</span>"
                            f"<span style='color:#a78bfa; font-weight:700;'>{_par_pct:.1f}%</span>"
                            f"</div>"
                            f"<div style='display:flex; justify-content:space-between;'>"
                            f"<span style='color:#888;'>Parlay EV</span>"
                            f"<span style='color:{_par_ev_col}; font-weight:700;'>{_par_ev:+.1f}%</span>"
                            f"</div></div>",
                            unsafe_allow_html=True,
                        )

                # ── Scratch check ─────────────────────────────────────────
                _scratched = st.session_state.get("scratched_ids", set())
                for s in _selected:
                    _p = _slip_map[s]
                    if _p.get("player_id") in _scratched:
                        st.error(f"⚠️ {_p['player_name']} may be SCRATCHED")
                if st.button("🔍 Check for Scratches", width='stretch',
                             key="check_scratches"):
                    with st.spinner("Checking lineups…"):
                        try:
                            from clients.mlb_stats import get_confirmed_lineup_player_ids
                            confirmed = get_confirmed_lineup_player_ids()
                            if not confirmed:
                                st.info("No lineups posted yet — check back closer to first pitch.")
                            else:
                                slip_pids = {_slip_map[s].get("player_id") for s in _selected}
                                scratched_ids = {pid for pid in slip_pids if pid and pid not in confirmed}
                                st.session_state["scratched_ids"] = scratched_ids
                                if scratched_ids:
                                    names = [_slip_map[s]["player_name"]
                                             for s in _selected
                                             if _slip_map[s].get("player_id") in scratched_ids]
                                    st.error(f"⚠️ Possibly scratched: {', '.join(names)}")
                                else:
                                    st.success("All slip players confirmed in posted lineups ✓")
                                    st.session_state["scratched_ids"] = set()
                        except Exception as ex:
                            st.warning(f"Lineup check failed: {ex}")
                # ── Pitcher change check ───────────────────────────────────
                if st.button("🔄 Check Pitcher Changes", width='stretch',
                             key="check_pitchers"):
                    with st.spinner("Checking starters…"):
                        try:
                            from clients.mlb_stats import get_today_pitcher_map
                            old_map = st.session_state.get("pitcher_map_at_load", {})
                            new_map = get_today_pitcher_map()
                            changes = {}
                            for team, info in new_map.items():
                                old_info = old_map.get(team, {})
                                if old_info.get("id") and info.get("id") and old_info["id"] != info["id"]:
                                    changes[team] = {"old": old_info.get("name", "?"), "new": info.get("name", "?")}
                            st.session_state["pitcher_changes"] = changes
                            if changes:
                                for team, ch in changes.items():
                                    st.error(f"⚠️ {team}: {ch['old']} → {ch['new']}")
                            else:
                                st.success("No pitcher changes detected ✓")
                        except Exception as ex:
                            st.warning(f"Pitcher check failed: {ex}")
                if st.button("📋 Save for Results Tracking", width='stretch',
                             key="log_fd_slip",
                             help="Log these picks before placing bets on FanDuel — required to track P&L and closing line value."):
                    slip_players = [_slip_map[s] for s in _selected]
                    try:
                        n = pnl_tracker.log_slip_picks(slip_players)
                        if n:
                            st.success(f"Logged {n} pick{'s' if n != 1 else ''} to Performance tab!")
                        else:
                            st.info("All selected players already logged today.")
                    except Exception as e:
                        st.error(f"Log failed: {e}")
                    # Also log to unified pick_tracker with source context
                    try:
                        from tracking import pick_tracker as _pt
                        _sources = st.session_state.get("fd_slip_sources", {})
                        for _s in _selected:
                            _sp = _slip_map.get(_s)
                            if _sp:
                                _src = _sources.get(_s, {})
                                _pt.log_pick(_sp,
                                             _src.get("tab", "FD Slip"),
                                             _src.get("section", "Manual Selection"))
                    except Exception:
                        pass
                st.link_button(
                    "📲 FanDuel HR Props", _fanduel_url(),
                    width='stretch', type="primary",
                )
                if not st.session_state.get("clear_slip_confirm"):
                    if st.button("🗑️ Clear Slip", width='stretch', key="clear_fd_slip"):
                        st.session_state["clear_slip_confirm"] = True
                        st.rerun()
                else:
                    st.warning("Remove all picks from the slip?")
                    _cc1, _cc2 = st.columns(2)
                    with _cc1:
                        if st.button("✅ Yes, clear", key="clear_slip_yes", use_container_width=True):
                            st.session_state["fd_slip"] = []
                            st.session_state.pop("fd_slip_select", None)
                            st.session_state.pop("clear_slip_confirm", None)
                            st.rerun()
                    with _cc2:
                        if st.button("❌ Cancel", key="clear_slip_no", use_container_width=True):
                            st.session_state.pop("clear_slip_confirm", None)
                            st.rerun()
            else:
                st.caption("Search above to add players to your slip.")
                st.link_button("📲 Browse FanDuel HR Props", _fanduel_url(), width='stretch')
        else:
            st.caption("Refresh data to build your slip.")
            st.link_button("📲 Browse FanDuel HR Props", _fanduel_url(), width='stretch')

        st.divider()

        loaded_at = st.session_state.get("data_loaded_at")
        if loaded_at:
            age_min = int((_dt.datetime.now() - loaded_at).total_seconds() / 60)
            age_str = f"{age_min}m ago" if age_min < 60 else f"{age_min // 60}h {age_min % 60}m ago"
            st.caption(f"Data loaded {age_str} ({loaded_at.strftime('%I:%M %p').lstrip('0')})")

        _sc_stats = st.session_state["data"].get("stats", {}) if "data" in st.session_state else {}
        if _sc_stats.get("players"):
            _sc_cur  = _sc_stats.get("sc_current", 0)
            _sc_bl   = _sc_stats.get("sc_blended", 0)
            _sc_pr   = _sc_stats.get("sc_prior", 0)
            _sc_no   = _sc_stats.get("sc_none", 0)
            _sc_tot  = _sc_stats.get("players", 1)
            _pit_sc  = _sc_stats.get("pit_sc_count", 0)
            _pit_tot = _sc_stats.get("pit_total", 1) or 1
            _batter_cov = round((_sc_cur + _sc_bl + _sc_pr) / _sc_tot * 100)
            _pit_cov    = round(_pit_sc / _pit_tot * 100)
            with st.expander(
                f"📡 Coverage — batters {_batter_cov}% / pitchers {_pit_cov}%",
            ):
                st.caption(
                    "Current = 2026 season Statcast. "
                    "Blended = 2026 + 2025 regression. "
                    "Prior = 2025 only. "
                    "None = no Statcast, uses park/pitcher factors only."
                )
                st.caption(
                    f"**Batter Statcast:** {_sc_cur} current · {_sc_bl} blended · "
                    f"{_sc_pr} prior · {_sc_no} none  \n"
                    f"**Pitcher Statcast:** {_pit_sc}/{_pit_tot} ({_pit_cov}%)"
                )

        if st.button("🔄 Force Refresh Data", width='stretch'):
            from clients import mlb_stats as _ms, statcast as _sc
            _ms.clear_all_caches()
            _sc.clear_all_caches()
            st.cache_data.clear()
            for k in ["data", "cache_key", "data_loaded_at"]:
                st.session_state.pop(k, None)
            st.rerun()

        # ── Auto-refresh ──────────────────────────────────────────────────────
        _ar_on = st.toggle(
            "⟳ Auto-refresh",
            value=st.session_state.get("auto_refresh_on", False),
            key="auto_refresh_on",
            help="Automatically reload odds & lineups on a timer.",
        )
        if _ar_on:
            _ar_interval = st.select_slider(
                "Every",
                options=[5, 10, 15, 30, 60],
                value=st.session_state.get("auto_refresh_interval", 15),
                format_func=lambda x: f"{x} min",
                label_visibility="collapsed",
            )
            st.session_state["auto_refresh_interval"] = _ar_interval
            _ar_loaded = st.session_state.get("data_loaded_at")
            if _ar_loaded:
                _ar_elapsed = int((_dt.datetime.now() - _ar_loaded).total_seconds() / 60)
                _ar_remain  = max(0, _ar_interval - _ar_elapsed)
                st.caption(
                    f"Refreshes every {_ar_interval} min · "
                    f"next in ~{_ar_remain} min"
                )
        _auto_refresh_ticker()

        st.divider()

        if st.button("✅ Update Yesterday's Results", width='stretch'):
            with st.spinner("Fetching outcomes from MLB…"):
                try:
                    result = pnl_tracker.update_yesterday()
                    st.success(
                        f"Settled {result['settled']} pick(s). "
                        f"{result['not_found']} not found."
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.button("📸 Capture Closing Lines (CLV)", width='stretch',
                     help="Fetch today's current odds and compute Closing Line Value for logged picks. Run ~30 min before first pitch."):
            with st.spinner("Capturing closing lines…"):
                try:
                    _today_str = _dt.date.today().isoformat()
                    _clv_result = clv_tracker.fetch_and_compute_clv(_today_str)
                    _clv_n = _clv_result if isinstance(_clv_result, int) else len(_clv_result or [])
                    st.success(f"CLV captured for {_clv_n} pick(s).")
                except Exception as e:
                    st.error(f"CLV capture failed: {e}")

        st.divider()

        # ── Push Notifications ────────────────────────────────────────────────
        with st.expander("🔔 Push Notifications (ntfy.sh)"):
            try:
                from tracking import notify as _notify
                import os as _notify_os
                _cur_topic = _notify_os.getenv("NTFY_TOPIC", "").strip()
                st.markdown(
                    "**Setup:** Install the free [ntfy app](https://ntfy.sh) on your phone, "
                    "enter your topic below, then subscribe to it in the app. "
                    "You'll get a notification for every HR and a daily summary when you settle results."
                )
                _new_topic = st.text_input(
                    "ntfy Topic",
                    value=st.session_state.get("ntfy_topic", _cur_topic),
                    placeholder="e.g. mlb-hr-my-secret-topic",
                    help="Pick something hard to guess — anyone who knows it can subscribe.",
                )
                if _new_topic != st.session_state.get("ntfy_topic", _cur_topic):
                    st.session_state["ntfy_topic"] = _new_topic
                    _notify_os.environ["NTFY_TOPIC"] = _new_topic

                _topic_live = st.session_state.get("ntfy_topic", _cur_topic)
                if _topic_live:
                    # Always keep env var in sync so _notify._topic() reads it correctly
                    _notify_os.environ["NTFY_TOPIC"] = _topic_live
                    st.success(f"Notifications active — topic: `{_topic_live}`")
                    if st.button("Send test notification", key="ntfy_test"):
                        ok = _notify.send_hr_hit("Test Player", "MLB", "+600", 60.0, "test")
                        if ok:
                            st.success("Test sent! Check your phone.")
                        else:
                            st.error("Failed — check your topic name and internet connection.")
                else:
                    st.info("Enter a topic to enable notifications.")
            except Exception as _ne:
                st.error(f"Notify error: {_ne}")

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
        # API key status + last error
        # API key input
        _saved_key = config.ODDS_API_KEY or ""
        _ui_key = st.text_input(
            "Odds API Key",
            value=st.session_state.get("odds_api_key_input", _saved_key),
            type="password",
            key="odds_api_key_input",
            placeholder="Paste key from the-odds-api.com",
        )
        if _ui_key and _ui_key != config.ODDS_API_KEY:
            import os, re as _re
            if not _re.match(r'^[a-f0-9]{32}$', _ui_key.lower()):
                st.warning("Invalid key format (expected 32 hex characters).")
            else:
                os.environ["ODDS_API_KEY"] = _ui_key
                config.ODDS_API_KEY = _ui_key
                from clients import odds_api as _oapi_mod
                _oapi_mod._last_error = ""
                st.caption("Key updated — click Force Refresh to apply.")
        elif config.ODDS_API_KEY:
            st.caption("Odds API key active.")
        else:
            st.caption("No API key — get one free at the-odds-api.com")
        st.caption(f"Active EV filter: {_min_ev:.1f}%")
        st.caption(f"Active Edge filter: {_min_edge:.1f}%")
        if _min_conf > 0:
            _tier_hint = {0: "", 40: " (B+ only)", 55: " (A/S only)", 70: " (S only)"}.get(_min_conf, "")
            st.caption(f"Active Confidence filter: {_min_conf}{_tier_hint}")
        backend = pnl_tracker.storage_backend()
        st.caption(f"Storage: {'☁️ Sheets' if backend == 'sheets' else '💾 Local CSV'}")


    # ── Banner ────────────────────────────────────────────────────────────────
    _banner = Path(__file__).parent / "assets" / "banner.png"
    if _banner.exists():
        st.image(str(_banner), use_container_width=True)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "⚾  MAIN",
        "⚡  JIG",
        "🔥  26",
        "🧩  ADVANCED STRATEGIES",
        "🏃  HITS",
        "📊  PERFORMANCE",
    ])

    with tab1:
        try:
            data = get_data()
            tab_picks(data, _min_ev, _min_edge,
                      cutoff_utc_hour=st.session_state.get("cutoff_utc_hour"),
                      min_confidence=_min_conf)
        except Exception as _e:
            st.error(f"Picks tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

    with tab2:
        try:
            tab_jig(get_data())
        except Exception as _e:
            st.error(f"JIG tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

    with tab3:
        st.markdown(
            "<div style='padding:40px 20px;text-align:center;'>"
            "<div style='font-size:32px;font-weight:900;color:#FF6666;"
            "letter-spacing:4px;text-shadow:0 0 30px rgba(255,100,50,0.6);'>"
            "🔥 26</div>"
            "<div style='font-size:14px;color:#666;margin-top:12px;letter-spacing:2px;'>"
            "ALTERNATIVE POWER-PROFILE METHODOLOGY</div>"
            "<div style='font-size:12px;color:#444;margin-top:24px;max-width:480px;"
            "margin-left:auto;margin-right:auto;line-height:1.8;'>"
            "A simplified explosive-bat philosophy.<br>"
            "Separate from the Main quantitative engine.<br>"
            "Coming in a future session."
            "</div></div>",
            unsafe_allow_html=True,
        )

    with tab4:
        try:
            tab_advanced_strategies(
                _gate_data(get_data(), st.session_state.get("cutoff_utc_hour")),
                parlays_callback=tab_parlays,
            )
        except Exception as _e:
            st.error(f"Advanced strategies tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

    with tab5:
        try:
            tab_hits(_gate_data(get_data(), st.session_state.get("cutoff_utc_hour")))
        except Exception as _e:
            st.error(f"Hits tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

    with tab6:
        try:
            tab_performance()
        except Exception as _e:
            st.error(f"Performance tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())


if __name__ == "__main__":
    try:
        main()
    except Exception as _top_e:
        st.error(f"App crash: {_top_e}")
        if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

