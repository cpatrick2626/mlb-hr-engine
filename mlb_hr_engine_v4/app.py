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


st.set_page_config(
    page_title="Codex HR Engine",
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
    from datetime import date as _date
    from pipeline import load_game_data
    target_date = config.TARGET_DATE or _date.today().strftime("%Y-%m-%d")

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
    return ""

def _stat_badge(col: str, val) -> str:
    """Return emoji-prefixed value so quality shows without Styler (works with column_config)."""
    css = _stat_css(col, val)
    if css == _DARK_GREEN: return f"💚 {val}"
    if css == _GREEN:      return f"🟢 {val}"
    if css == _RED:        return f"🔴 {val}"
    if css == _DARK_RED:   return f"⛔ {val}"
    return str(val)


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


@st.dialog("⚾ Player Details", width="large")
def _show_player_modal(player: dict):
    name  = player.get("player_name", "Unknown")
    team  = player.get("team", "")
    opp   = player.get("opponent", "")
    pit   = player.get("pitcher_name", "TBD")
    spot  = player.get("lineup_spot")
    sc_src = player.get("statcast_source", "none")

    st.markdown(
        f"<div style='font-size:20px; font-weight:800; color:#f0f0f0;'>{name}</div>"
        f"<div style='font-size:13px; color:#888; margin-bottom:6px;'>"
        f"{team} vs {opp} &nbsp;·&nbsp; vs {pit}"
        f"{f'  &nbsp;·&nbsp;  Bat #{spot}' if spot else ''}"
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
    c3.metric("EV%",      f"{player.get('ev_pct', 0):+.1f}%")
    c4.metric("Edge%",    f"{player.get('edge_pct', 0):+.1f}%")

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
    """Return data with all_players and ranked filtered to games at or after cutoff ET hour."""
    if cutoff is None:
        return data
    cutoff_et_hour = (cutoff - 4) % 24
    def _keep(p):
        gt_et = _game_time_et(p.get("game_time_utc", ""))
        return gt_et is None or gt_et.hour >= cutoff_et_hour
    gated = dict(data)
    gated["all_players"] = [p for p in data.get("all_players", []) if _keep(p)]
    gated["ranked"]      = [p for p in data.get("ranked", []) if _keep(p)]
    return gated


@st.cache_data(ttl=60)
def _fetch_live_status(game_pk: int) -> dict:
    """Linescore for an in-progress game, cached 60 s to avoid hammering the API."""
    try:
        from clients import mlb_stats as _ms
        return _ms.get_live_game_status(game_pk)
    except Exception:
        return {}


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


def _render_qualified_table(
    ranked: list, scale: float, min_ev: float, min_edge: float,
    steam_names: set = None, key_suffix: str = "",
):
    """Render the qualified picks dataframe with range bar, legend, and column configs."""
    import math
    import io

    def safe_val(v, default="--"):
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

    _pitcher_changes = st.session_state.get("pitcher_changes", {})
    rows = []
    for p in ranked:
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
        is_steam = steam_names and name in steam_names
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
            "Model%":  _stat_badge("Model%", f"{model_p*100:.1f}%"),
            "Mkt%":    f"{p.get('market_no_vig_prob',0)*100:.1f}%",
            "Edge":    _stat_badge("Edge", f"{edge:+.1f}%"),
            "EV%":     _stat_badge("EV%", f"{ev:+.1f}%"),
            "Bet $":   f"${bet:.0f}",
            "Conf":    _stat_badge("Conf", f"{conf:.0f}"),
            "Brl%":    _stat_badge("Brl%", str(safe_val(p.get("barrel_pct"), "--"))),
            "SwSp%":   _stat_badge("SwSp%", str(safe_val(p.get("sweet_spot_pct"), "--"))),
            "EV mph":  _stat_badge("EV mph", str(safe_val(p.get("exit_velo"), "--"))),
            "FB%":     _stat_badge("FB%", str(safe_val(p.get("fb_pct"), "--"))),
            "GB%":     _stat_badge("GB%", str(safe_val(p.get("gb_pct"), "--"))),
            "Pull%":   str(safe_val(p.get("pull_pct"), "--")),
            "Score":   f"{p.get('score',0):.1f}",
        })

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

    ev_rng    = _rng(evs, sign=True, suffix="%")
    edge_rng  = _rng(edges, sign=True, suffix="%")
    model_rng = _rng(models, suffix="%")
    mkt_rng   = _rng(mkts, suffix="%")
    bet_rng   = f"${min(bets):.0f} → ${max(bets):.0f}" if bets else "N/A"
    conf_rng  = _rng(confs, fmt=".0f")
    score_rng = _rng(scores, fmt=".1f")

    session_br = st.session_state.get("bankroll_override", config.BANKROLL)

    df = pd.DataFrame(rows)
    df = df.fillna("--")
    df = df.replace([np.nan, np.inf, -np.inf, float('inf'), -float('inf')], "--")

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


# TAB 1 — TODAY'S PICKS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def tab_picks(data: dict, min_ev: float, min_edge: float, cutoff_utc_hour: int | None = None, min_confidence: float = 0):
    all_players = data.get("all_players", [])
    ranked    = _apply_ui_filters(all_players, min_ev, min_edge, cutoff_utc_hour, min_confidence)
    stats     = data.get("stats", {})
    source    = data.get("odds_source", "none")
    quota     = data.get("odds_quota", {})
    n_batters = data.get("batter_count", 0)
    scale     = _bankroll_scale()

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

    st.markdown('<div class="section-header">&#9889; TODAY\'S PICKS</div>',
                unsafe_allow_html=True)

    # Lineup readiness
    n_confirmed  = sum(1 for p in all_players if p.get("lineup_spot"))
    n_estimated  = len(all_players) - n_confirmed
    lineup_pct   = int(100 * n_confirmed / len(all_players)) if all_players else 0
    lineup_color = "#4ade80" if lineup_pct >= 80 else "#FFD700" if lineup_pct >= 40 else "#FF6666"
    lineup_label = (
        f"Lineups: <b style='color:{lineup_color}'>{n_confirmed}/{len(all_players)} confirmed</b>"
        + (f" <span style='color:#888'>({n_estimated} estimated)</span>" if n_estimated else "")
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
        f"Players: <b style='color:#f0f0f0'>{stats.get('players',0)}</b> &nbsp;|&nbsp; "
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

        _hc1, _hc2, _hc3 = st.columns([6, 2, 2])
        with _hc1:
            if st.button(
                f"🏆  {_top_name}",
                key="hero_modal_btn",
                help=f"View full stats for {_top_name}",
                use_container_width=True,
            ):
                st.session_state["show_modal"] = _top
                st.session_state["modal_source_tab"] = "Quick View"
                st.session_state["modal_source_section"] = "Top Pick"
                st.rerun()
            st.markdown(
                f"<div style='font-size:12px; color:#888; margin:-4px 0 2px 6px;'>"
                f"{_top_team} vs {_top_vs} &nbsp;·&nbsp; {_top_conf} &nbsp;·&nbsp; "
                f"Spot #{_top_spot if _top_spot else '?'}"
                f"</div>",
                unsafe_allow_html=True,
            )
        with _hc2:
            st.metric("Model / EV",
                      f"{_top_model:.0f}%",
                      delta=f"EV {_top_ev:+.1f}%",
                      delta_color="normal")
        with _hc3:
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
                _sbet    = _sp.get("bet_size") or _sp.get("bet_dollars")
                _sconf   = "✅" if _sp.get("lineup_spot") is not None else "⏳"
                _prefix  = "🏆 #1 BEST BET" if _si == 0 else f"{_si + 1}."
                _share_lines.append(f"{_prefix} {_sconf} {_sname} ({_steam}) vs {_svs}")
                _odds_str = _fmt_american(_sodds) if _sodds else "--"
                _book_str = f" @ {_sbook}" if _sbook else ""
                _bet_str  = f" | Bet: ${float(_sbet):.0f}" if _sbet else ""
                _share_lines.append(
                    f"   {_odds_str}{_book_str} | {_smodel:.0f}% model | EV {_sev:+.1f}%{_bet_str}"
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
        _lm_today = lm_tracker.get_movement_today()
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

    sub1, sub2, sub3, sub4, sub5 = st.tabs([
        f"⚡ Picks ({len(ranked)})",
        f"📊 All ({len(all_by_model)})",
        f"⭐ Prime ({_n_prime})",
        f"⏰ Prime Time ({_n_prime_timed})",
        f"📋 Watch ({min(_n_watch, 20)})",
    ])

    # ── TAB: Qualified Picks ─────────────────────────────────────────────────
    with sub1:
        roster_confirmed = [p for p in ranked if p.get("lineup_spot") is not None]
        _quick_tab, _timeline_tab, _slate_tab, _confirmed_tab, _movement_tab, _odds_cmp_tab = st.tabs([
            "📱 Quick View",
            "⏰ By Game Time",
            f"📊 All Picks ({len(ranked)})",
            f"✅ Confirmed ({len(roster_confirmed)})",
            "📊 Line Movement",
            "📊 Odds",
        ])

        with _quick_tab:
            _quick_pool = ranked[:10] if ranked else []
            if not _quick_pool:
                st.info(
                    f"No qualified picks (EV ≥ {min_ev:.1f}%, Edge ≥ {min_edge:.1f}%). "
                    "Try sliding both filters left in the sidebar — or click 'Force Refresh Data' "
                    "to reload market odds."
                )
            else:
                _now_et = _dt.datetime.now(_EDT)
                st.caption("Top picks — tap player name to view details & add to FD Slip.")
                for _qi, _qp in enumerate(_quick_pool):
                    _qev      = _qp.get("ev_pct", 0)
                    _qodds    = _qp.get("best_american")
                    _qmodel   = _qp.get("model_prob", 0) * 100
                    _qteam    = _qp.get("team", "")
                    _qvs      = _qp.get("pitcher_name", "")
                    _qspot    = _qp.get("lineup_spot")
                    _qbet     = _qp.get("bet_size") or _qp.get("bet_dollars")
                    _qev_col  = "#4ade80" if _qev >= 0 else "#f87171"
                    _qconf    = "✅" if _qspot is not None else "⏳"
                    _qtier    = _qp.get("confidence_tier", "C")
                    _qtier_col = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_qtier, "#888")
                    _qurl     = _fanduel_url(_qp["player_name"])
                    _qis_steam = _qp.get("player_name") in _steam_names

                    # Game time + urgency
                    _qgt = _game_time_et(_qp.get("game_time_utc", ""))
                    if _qgt:
                        _qgt_str  = _qgt.strftime('%I:%M %p ET').lstrip('0')
                        _qgt_dt   = _dt.datetime.combine(_now_et.date(), _qgt, tzinfo=_EDT)
                        _mins_to  = int((_qgt_dt - _now_et).total_seconds() / 60)
                        if _mins_to < 0:
                            _urgency_col = "#555"
                            _urgency_lbl = "In progress"
                        elif _mins_to < 60:
                            _urgency_col = "#FF6666"
                            _urgency_lbl = f"BET NOW — {_mins_to}m"
                        elif _mins_to < 120:
                            _urgency_col = "#FFD700"
                            _urgency_lbl = f"{_mins_to}m to game"
                        else:
                            _urgency_col = "#4ade80"
                            _urgency_lbl = f"{_mins_to // 60}h {_mins_to % 60}m"
                    else:
                        _qgt_str  = "TBD"
                        _urgency_col = "#555"
                        _urgency_lbl = ""

                    _steam_border = "#666600" if _qis_steam else "#1e1e40"
                    _steam_bg     = "#1a1a00" if _qis_steam else "#0d0d20"
                    _steam_badge  = "<span style='background:#444400;color:#FFD700;font-size:10px;padding:1px 6px;border-radius:4px;margin-left:6px;'>📈 STEAM</span>" if _qis_steam else ""
                    _qweather     = _weather_badge(_qp)

                    if st.button(
                        f"{_qconf} {_qp['player_name']}",
                        key=f"qv_modal_{_qi}",
                        use_container_width=True,
                    ):
                        st.session_state["show_modal"] = _qp
                        st.session_state["modal_source_tab"] = "Quick View"
                        st.session_state["modal_source_section"] = "Quick View"
                        st.rerun()
                    _spot_str = f" · Bat #{_qspot}" if _qspot else ""
                    _bet_str  = f"<span style='color:#888;font-size:11px;'> · Bet ${float(_qbet):.0f}</span>" if _qbet else ""
                    st.markdown(
                        f"<div style='background:{_steam_bg}; border:1px solid {_steam_border}; border-radius:10px; "
                        f"padding:10px 16px; margin-bottom:10px;'>"
                        # row 1: matchup + steam badge + odds link
                        f"<div style='display:flex; justify-content:space-between; align-items:flex-start;'>"
                        f"<div style='font-size:13px; color:#888;'>{_qteam} vs {_qvs}{_spot_str}{_steam_badge}</div>"
                        f"<a href='{_qurl}' target='_blank' style='text-decoration:none;'>"
                        f"<div style='text-align:right;'>"
                        f"<div style='font-size:20px; font-weight:700; color:#FF6666;'>{_fmt_american(_qodds)}</div>"
                        f"<div style='font-size:11px; color:#888;'>best odds ↗</div>"
                        f"</div></a>"
                        f"</div>"
                        # row 2: game time urgency + weather
                        f"<div style='margin:4px 0 8px; display:flex; justify-content:space-between; align-items:center;'>"
                        f"<span>"
                        f"<span style='font-size:12px; color:#888;'>🕐 {_qgt_str}</span>"
                        + (f"  <span style='font-size:11px; font-weight:700; color:{_urgency_col};'>· {_urgency_lbl}</span>" if _urgency_lbl else "")
                        + f"</span>"
                        + (f"<span>{_qweather}</span>" if _qweather else "")
                        + f"</div>"
                        # row 3: stat boxes
                        f"<div style='display:flex; gap:10px;'>"
                        f"<div style='text-align:center; flex:1; background:#0a0a18; border-radius:6px; padding:6px 4px;'>"
                        f"<div style='font-size:18px; font-weight:700; color:#a78bfa;'>{_qmodel:.0f}%</div>"
                        f"<div style='font-size:10px; color:#666;'>Model</div>"
                        f"</div>"
                        f"<div style='text-align:center; flex:1; background:#0a0a18; border-radius:6px; padding:6px 4px;'>"
                        f"<div style='font-size:18px; font-weight:700; color:{_qev_col};'>{_qev:+.1f}%</div>"
                        f"<div style='font-size:10px; color:#666;'>EV</div>"
                        f"</div>"
                        f"<div style='text-align:center; flex:1; background:#0a0a18; border-radius:6px; padding:6px 4px;'>"
                        f"<div style='font-size:18px; font-weight:700; color:{_qtier_col};'>{_qtier}</div>"
                        f"<div style='font-size:10px; color:#666;'>Tier</div>"
                        f"</div>"
                        f"</div>"
                        + (f"<div style='margin-top:6px; text-align:right;'>{_bet_str}</div>" if _qbet else "")
                        + f"</div>",
                        unsafe_allow_html=True,
                    )

        with _timeline_tab:
            # Pool: qualified picks + all players with odds, deduplicated, sorted by game time
            _tl_seen: set = set()
            _tl_pool: list = []
            for _p in ranked:
                _n = _p.get("player_name", "")
                if _n not in _tl_seen:
                    _tl_seen.add(_n)
                    _tl_pool.append((_p, True))   # (player_dict, is_pick)
            for _p in all_players:
                _n = _p.get("player_name", "")
                if _n not in _tl_seen and _p.get("best_american"):
                    _tl_seen.add(_n)
                    _tl_pool.append((_p, False))  # has odds but didn't qualify

            if not _tl_pool:
                st.info("No players with odds yet — load data first.")
            else:
                # Group by rounded game time (nearest 5 min)
                from collections import defaultdict as _dd
                _tl_groups: dict = _dd(list)
                _tl_sort_key: dict = {}
                for _p, _is_pick in _tl_pool:
                    _gt = _game_time_et(_p.get("game_time_utc", ""))
                    if _gt:
                        # Round down to 5-min slot for grouping
                        _slot_min = (_gt.hour * 60 + _gt.minute // 5 * 5)
                        _slot_lbl = f"{_gt.strftime('%I:%M %p').lstrip('0')} ET"
                    else:
                        _slot_min = 9999
                        _slot_lbl = "Time TBD"
                    _tl_groups[_slot_lbl].append((_p, _is_pick))
                    _tl_sort_key[_slot_lbl] = _slot_min

                _now_et = _dt.datetime.now(_EDT)
                _now_min = _now_et.hour * 60 + _now_et.minute
                _sorted_slots = sorted(_tl_groups.keys(), key=lambda s: _tl_sort_key[s])
                _n_pick_slots = sum(1 for s in _sorted_slots if any(ip for _, ip in _tl_groups[s]))
                st.caption(
                    f"{len(_tl_pool)} players across {len(_sorted_slots)} game times · "
                    f"{len(ranked)} qualified picks · ✅ = pass filters · ○ = has odds only"
                )
                for _slot_lbl in _sorted_slots:
                    _slot_players = _tl_groups[_slot_lbl]
                    _slot_min_val = _tl_sort_key[_slot_lbl]
                    _n_picks_in   = sum(1 for _, ip in _slot_players if ip)
                    _is_past      = _slot_min_val < _now_min and _slot_min_val != 9999
                    _is_next      = not _is_past and _slot_min_val != 9999 and all(
                        _tl_sort_key[s] <= _slot_min_val or _tl_sort_key[s] == 9999
                        for s in _sorted_slots if _tl_sort_key[s] < _slot_min_val
                    )
                    _pick_tag = f"  {_n_picks_in} pick{'s' if _n_picks_in != 1 else ''}" if _n_picks_in else "  watch only"
                    _past_tag = "  ⚫ past" if _is_past else ""
                    _hdr_col  = "#888" if _is_past else ("#FFD700" if _n_picks_in else "#555")
                    st.markdown(
                        f"<div style='background:#0d0d20; border-left:3px solid {_hdr_col}; "
                        f"padding:6px 12px; margin:10px 0 4px; border-radius:0 6px 6px 0;'>"
                        f"<span style='color:{_hdr_col}; font-weight:700; font-size:14px;'>"
                        f"🕐 {_slot_lbl}</span>"
                        f"<span style='color:#555; font-size:12px;'>{_pick_tag}{_past_tag}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    for _tli, (_p, _is_pick) in enumerate(_slot_players):
                        _tl_name  = _p.get("player_name", "")
                        _tl_team  = _p.get("team", "")
                        _tl_vs    = _p.get("pitcher_name", "")
                        _tl_odds  = _p.get("best_american")
                        _tl_ev    = _p.get("ev_pct", 0)
                        _tl_model = _p.get("model_prob", 0) * 100
                        _tl_conf  = "✅" if _is_pick else "○"
                        _tl_ev_col = "#4ade80" if _tl_ev >= 0 else "#f87171"
                        _tl_name_col = "#f0f0f0" if _is_pick else "#888"
                        _tc1, _tc2 = st.columns([7, 3])
                        with _tc1:
                            if st.button(
                                f"{_tl_conf} {_tl_name}",
                                key=f"tl_modal_{_slot_lbl}_{_tli}",
                                use_container_width=True,
                                disabled=_is_past,
                            ):
                                st.session_state["show_modal"] = _p
                                st.session_state["modal_source_tab"] = "By Game Time"
                                st.session_state["modal_source_section"] = "By Game Time"
                                st.rerun()
                            st.markdown(
                                f"<div style='font-size:11px; color:#666; margin:-4px 0 2px 6px;'>"
                                f"{_tl_team} vs {_tl_vs}"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        with _tc2:
                            st.markdown(
                                f"<div style='text-align:right; padding-top:4px;'>"
                                f"<span style='color:#FF6666; font-weight:700;'>{_fmt_american(_tl_odds) if _tl_odds else '--'}</span>"
                                f"<span style='color:#555; font-size:10px;'> odds</span><br>"
                                f"<span style='color:#a78bfa; font-size:11px;'>{_tl_model:.0f}% mdl</span>"
                                + (f"  <span style='color:{_tl_ev_col}; font-size:11px;'>{_tl_ev:+.1f}% EV</span>" if _is_pick else "")
                                + f"</div>",
                                unsafe_allow_html=True,
                            )

        with _slate_tab:
            if not ranked:
                with_odds = [p for p in all_players if p.get("best_american")]
                if not with_odds:
                    st.warning("No market odds available — sportsbooks stop offering HR props once games are in progress.")
                    st.info(f"Pipeline found {len(all_players)} players. Run the app before first pitch to get live odds.")
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
                _render_qualified_table(ranked, scale, min_ev, min_edge,
                                        steam_names=_steam_names, key_suffix="slate")

        with _confirmed_tab:
            if not roster_confirmed:
                st.info(
                    "No roster-confirmed picks pass current filters yet.  \n"
                    "Lineups typically post 1–2 hours before first pitch. "
                    "Players without a confirmed lineup spot receive an 18% model discount."
                )
            else:
                _render_qualified_table(roster_confirmed, scale, min_ev, min_edge,
                                        steam_names=_steam_names, key_suffix="confirmed")

        # ── Line Movement tab ─────────────────────────────────────────────────
        with _movement_tab:
            try:
                movement = lm_tracker.get_movement_today()
            except Exception:
                movement = {}
            if not movement:
                st.info(
                    "No line movement data yet today.  \n"
                    "Data is logged each time the app loads or refreshes. "
                    "Reload after ~30 min to see intraday movement."
                )
            else:
                mv_rows = []
                for name, snaps in movement.items():
                    summ = lm_tracker.movement_summary(snaps)
                    if not summ:
                        continue
                    open_o = summ["opening_odds"]
                    curr_o = summ["current_odds"]
                    move   = summ["move_pct"]
                    dirn   = summ["direction"]
                    move_color = "#4ade80" if move > 0.5 else ("#f87171" if move < -0.5 else "#888888")
                    mv_rows.append({
                        "Player":   name,
                        "Open":     _fmt_american(open_o),
                        "Now":      _fmt_american(curr_o),
                        "Move":     f"{move:+.1f}%",
                        "Signal":   dirn,
                        "Snaps":    summ["n_snapshots"],
                    })
                if mv_rows:
                    st.caption(
                        "Line movement since first load today. "
                        "▲ shortened = market gaining confidence (sharp agreement). "
                        "▼ lengthened = market fading."
                    )
                    # Build a name→player lookup from all_players for modal support
                    _mv_player_map = {p.get("player_name", ""): p for p in all_players}
                    _mv_tver = st.session_state.get("_table_ver", 0)
                    _mv_sel = st.dataframe(
                        pd.DataFrame(mv_rows), hide_index=True, use_container_width=True,
                        on_select="rerun", selection_mode="single-row",
                        key=f"mv_df_{_mv_tver}",
                    )
                    _mv_rows_sel = getattr(getattr(_mv_sel, "selection", None), "rows", [])
                    if _mv_rows_sel and 0 <= _mv_rows_sel[0] < len(mv_rows):
                        _mv_name = mv_rows[_mv_rows_sel[0]]["Player"]
                        _mv_p    = _mv_player_map.get(_mv_name)
                        if _mv_p:
                            st.session_state["_table_ver"] = _mv_tver + 1
                            st.session_state["show_modal"] = _mv_p
                            st.session_state["modal_source_tab"] = "Line Movement"
                            st.session_state["modal_source_section"] = "Line Movement"
                            st.rerun()
                else:
                    st.info("Not enough snapshots yet to show movement.")

        # ── Odds Comparison tab ───────────────────────────────────────────────
        with _odds_cmp_tab:
            odds_pool = ranked if ranked else [p for p in all_players if p.get("prices_by_book")]
            if not odds_pool:
                st.info("No odds data available.")
            else:
                # Collect all book names present across any player
                all_books: list[str] = []
                seen: set[str] = set()
                # Preferred order first, then any extras
                _PREF = ["fanduel", "draftkings", "betmgm", "caesars", "pointsbet", "betrivers", "bet365"]
                for bk in _PREF:
                    if any(bk in p.get("prices_by_book", {}) for p in odds_pool):
                        all_books.append(bk)
                        seen.add(bk)
                for p in odds_pool:
                    for bk in p.get("prices_by_book", {}).keys():
                        if bk not in seen:
                            all_books.append(bk)
                            seen.add(bk)
                cmp_rows = []
                for p in odds_pool:
                    pbk = p.get("prices_by_book", {})
                    row = {
                        "Player": p.get("player_name", ""),
                        "Team":   p.get("team", ""),
                        "EV%":    f"{p.get('ev_pct', 0):+.1f}%",
                        "Best":   _fmt_american(p.get("best_american")),
                        "@":      p.get("best_bookmaker", ""),
                    }
                    for bk in all_books:
                        row[bk.title()] = _fmt_american(pbk.get(bk)) if bk in pbk else "--"
                    cmp_rows.append(row)
                st.caption("Best odds per sportsbook for each qualified pick.")
                _oc_tver = st.session_state.get("_table_ver", 0)
                _oc_sel = st.dataframe(
                    pd.DataFrame(cmp_rows), hide_index=True, use_container_width=True,
                    on_select="rerun", selection_mode="single-row",
                    key=f"odds_cmp_df_{_oc_tver}",
                )
                _oc_rows_sel = getattr(getattr(_oc_sel, "selection", None), "rows", [])
                if _oc_rows_sel and 0 <= _oc_rows_sel[0] < len(odds_pool):
                    st.session_state["_table_ver"] = _oc_tver + 1
                    st.session_state["show_modal"] = odds_pool[_oc_rows_sel[0]]
                    st.session_state["modal_source_tab"] = "Odds"
                    st.session_state["modal_source_section"] = "Odds Comparison"
                    st.rerun()

    if all_by_model:
        PRIME_FLOOR = 0.15

        # â"€â"€ All available columns (name -> extractor) â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
        _FIXED_COLS   = ["Player", "Team", "Spot", "Vs", "Model%"]
        _TOGGLE_COLS  = [
            "Brl%", "SwSp%", "FB%", "GB%", "LD%", "Pull%", "Oppo%",
            "Hard Hit%", "Exit Velo", "Launch Angle",
            "PwrMult", "Park", "Pitcher", "Weather", "Platoon",
            "Season PA", "Season HR", "Recent PA", "HR Rate",
            "Streak", "K Factor", "Pitcher HR/9", "Exp PA",
            "Odds", "Mkt%", "Edge%", "EV%", "Confidence",
        ]
        _ALL_COLS = _FIXED_COLS + _TOGGLE_COLS

        def _safe(v, default="--"):
            """Return string; map None/NaN/non-finite to default."""
            if v is None:
                return default
            try:
                import math
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    return default
            except Exception:
                pass
            return str(v)

        def _extract(col, p, pit_fac, plat_fac):
            m = p.get
            if col == "Player":       return _safe(m("player_name"), "")
            if col == "Team":         return _safe(m("team"), "")
            if col == "Spot":         return _spot_label(m("lineup_spot"), plat_fac)
            if col == "Vs":           return _pitcher_label(m("pitcher_name", "TBD"), pit_fac, plat_fac)
            if col == "Model%":       return _stat_badge("Model%", f"{(m('model_prob') or 0)*100:.1f}%")
            if col == "Brl%":         return _stat_badge("Brl%", _safe(m("barrel_pct")))
            if col == "SwSp%":        return _stat_badge("SwSp%", _safe(m("sweet_spot_pct")))
            if col == "FB%":          return _stat_badge("FB%", _safe(m("fb_pct")))
            if col == "GB%":          return _stat_badge("GB%", _safe(m("gb_pct")))
            if col == "LD%":          return _safe(m("ld_pct"))
            if col == "Pull%":        return _safe(m("pull_pct"))
            if col == "Oppo%":        return _safe(m("oppo_pct"))
            if col == "Hard Hit%":    return _safe(m("hard_hit"))
            if col == "Exit Velo":    return _stat_badge("Exit Velo", _safe(m("exit_velo")))
            if col == "Launch Angle":
                v = m("avg_launch_angle")
                return f"{v:.1f}" if isinstance(v, (int, float)) and v == v else "--"
            if col == "PwrMult":
                v = m("statcast_power_mult") or 1.0
                return _stat_badge("PwrMult", f"{v:.2f}")
            if col == "Park":         return f"{m('park_factor') or 1:.3f}"
            if col == "Pitcher":      return f"{m('pitcher_factor') or 1:.3f}"
            if col == "Weather":      return f"{m('weather_factor') or 1:.3f}"
            if col == "Platoon":      return f"{m('platoon_factor') or 1:.3f}"
            if col == "Season PA":    return _safe(m("season_pa"), "0")
            if col == "Season HR":    return _safe(m("season_hr"), "0")
            if col == "Recent PA":    return _safe(m("recent_pa"), "0")
            if col == "HR Rate":      return f"{(m('hr_rate') or 0)*100:.2f}%"
            if col == "Streak":       return f"{m('streak_factor') or 1:.3f}"
            if col == "K Factor":     return f"{m('k_factor') or 1:.3f}"
            if col == "Pitcher HR/9": return f"{m('pitcher_hr9') or 0:.2f}"
            if col == "Exp PA":       return f"{m('expected_pa') or 3.8:.1f}"
            if col == "Odds":         return _fmt_american(m("best_american")) if m("best_american") else "--"
            if col == "Mkt%":         return f"{(m('market_no_vig_prob') or 0)*100:.1f}%" if m("market_no_vig_prob") else "--"
            if col == "Edge%":        return f"{m('edge_pct',0):+.1f}%" if m("edge_pct") is not None else "--"
            if col == "EV%":          return f"{m('ev_pct',0):+.1f}%" if m("ev_pct") is not None else "--"
            if col == "Confidence":   return f"{m('confidence',0):.0f}" if m("confidence") is not None else "--"
            return "--"

        _COL_HELP = {
            "Model%":       "Poisson HR probability for today's game: P(HR≥1) = 1−e^(−λ). Accounts for batter power, park, pitcher, weather, and platoon.",
            "Brl%":         "Barrel rate (Statcast brl_pa). Balls hit 98+ mph at 26-30° launch angle. League avg ~5.5%. Strong predictor of HR power.",
            "SwSp%":        "Sweet spot rate — balls hit at 8-32° launch angle. League avg ~33%. Higher = more balls in the HR window.",
            "FB%":          "Fly ball rate — Savant pure FB% (excludes popups). League avg ~26.5%. More fly balls = more HR opportunities.",
            "GB%":          "Ground ball rate. High GB% suppresses HR output — grounders don't leave the park. League avg ~43%.",
            "LD%":          "Line drive rate. League avg ~23%. Line drives don't go for HRs often but signal solid contact.",
            "Pull%":        "Pull rate. League avg ~39%. Pull hitters access the short porch and benefit more from wind.",
            "Oppo%":        "Opposite-field rate. Low pull%, high oppo% = contact hitter profile; harder to hit HRs to the deep part of the park.",
            "Hard Hit%":    "Hard-hit rate — balls hit 95+ mph exit velocity. League avg ~40%. Correlates with power output.",
            "Exit Velo":    "Average exit velocity (mph). League avg ~89 mph. 90+ is above average; 95+ is elite power territory.",
            "Launch Angle": "Average launch angle (degrees). Optimal HR zone is 25-35°. Too low = grounders; too high = pop-ups.",
            "PwrMult":      "Statcast composite power multiplier (0.45–1.75). Blends barrel%, FB%, xSLG, pull%, sweet spot, hard-hit%, and exit velo. 1.0 = league average.",
            "Park":         "Park HR factor for today's stadium. 1.0 = neutral. Coors = 1.28, Petco = 0.89. Applied to batter's fly-ball tendency.",
            "Pitcher":      "Combined pitcher HR factor (0.55–1.60). Blends HR/FB rate, Statcast contact quality allowed, K%, and GB%. Above 1.0 = pitcher allows more HRs than average.",
            "Weather":      "Weather factor (0.80–1.20). Combines temperature (hot air = ball carries) and wind (blowing out = HR boost). 1.0 = neutral conditions.",
            "Platoon":      "Platoon split factor. Bayesian-shrunk HR rate vs this pitcher's handedness divided by overall rate. Above 1.0 = batter has a platoon advantage today.",
            "Season PA":    "Plate appearances this season. Larger sample = more reliable HR rate estimate.",
            "Season HR":    "Home runs hit this season.",
            "Recent PA":    "Plate appearances in the last 20 games. Used to weight recent form vs full-season rate.",
            "HR Rate":      "Final blended HR/PA rate used as model input. Combines Bayesian-regressed season rate with Statcast power multiplier.",
            "Streak":       "Hot/cold streak factor (0.93–1.08). Compares last 10-game HR rate to season average. Capped at ±8% influence.",
            "K Factor":     "Batter strikeout suppressor (0.85–1.00). High K% reduces balls in play and HR opportunities. One-sided — never boosts contact hitters.",
            "Pitcher HR/9": "Pitcher's HR allowed per 9 innings this season. League avg = 1.09. Above 1.4 = HR-prone; below 0.8 = HR suppressor.",
            "Exp PA":       "Expected plate appearances today based on lineup spot. Top of order = ~4.5 PA; bottom = ~3.2 PA. Unknown lineup = 3.8 default.",
            "Odds":         "Best available American odds across all tracked books. Higher number = longer shot = bigger payout if correct.",
            "Mkt%":         "No-vig market implied probability — raw implied prob divided by (1 + 7.5% vig). Represents the book's true estimated HR probability.",
            "Edge%":        "Model probability minus market no-vig probability. Positive edge means the model sees more HR probability than the market is pricing.",
            "EV%":          "Expected value percentage: [p × (decimal odds − 1) − (1 − p)] × 100. Positive EV = profitable long-run bet at these odds.",
            "Confidence":   "Model confidence score (0–100). Based on sample size (season + recent PA), edge signal-to-noise ratio, Statcast data availability, barrel rate, and pitcher HR/9.",
        }

        _col_cfg = {
            c: st.column_config.TextColumn(c, help=_COL_HELP[c])
            for c in _COL_HELP
        }

        # Full names + descriptions shown in the dropdown for each toggleable column
        _COL_FULL = {
            "Brl%":
                "Brl%  ·  Barrel Rate (Statcast brl_pa) — % of PA resulting in a barrel (98+ mph at 26-30°). "
                "League avg ~5.5%. Single strongest Statcast predictor of HR power. "
                "Effect: higher barrel% → larger power multiplier → higher model probability.",
            "SwSp%":
                "SwSp%  ·  Sweet Spot Rate — % of batted balls hit at 8-32° launch angle. "
                "League avg ~33%. More balls in this optimal window = more HR opportunities. "
                "Effect: contributes 10% weight to the Statcast power multiplier.",
            "FB%":
                "FB%  ·  Fly Ball Rate — Savant pure FB% (excludes popups). "
                "League avg ~26.5%. Only fly balls can leave the park. "
                "Effect: 15% weight in power multiplier; also scales how much park factor applies to this batter.",
            "GB%":
                "GB%  ·  Ground Ball Rate — % of batted balls that are grounders. "
                "League avg ~43%. Grounders almost never become HRs. "
                "Effect: high GB% suppresses the power multiplier and limits park factor benefit.",
            "LD%":
                "LD%  ·  Line Drive Rate — % of batted balls that are line drives. "
                "League avg ~23%. Signals solid contact quality but not HR trajectory. "
                "Effect: informational only — not directly used in the HR probability model.",
            "Pull%":
                "Pull%  ·  Pull Rate — % of batted balls pulled to the strong side. "
                "League avg ~39%. Pull hitters access the shorter porch and benefit more from wind. "
                "Effect: 8% weight in the power multiplier.",
            "Oppo%":
                "Oppo%  ·  Opposite-Field Rate — % of batted balls hit to the weak side. "
                "High oppo% signals a contact/gap hitter, not a HR profile. "
                "Effect: informational — model uses pull%, not oppo%, in the power multiplier.",
            "Hard Hit%":
                "Hard Hit%  ·  Hard-Hit Rate — % of batted balls hit 95+ mph exit velocity. "
                "League avg ~40%. Strong correlation with HR output and overall power. "
                "Effect: 10% weight in the Statcast power multiplier.",
            "Exit Velo":
                "Exit Velo  ·  Average Exit Velocity (mph) — how hard the batter hits the ball. "
                "League avg ~89 mph. 90+ = above average; 95+ = elite power hitter. "
                "Effect: 5% weight in the power multiplier; also gates how much barrel% is trusted.",
            "Launch Angle":
                "Launch Angle  ·  Average Launch Angle (degrees) — upward trajectory of batted balls. "
                "Optimal HR zone: 25-35°. Too low = grounders; too high = pop-ups. "
                "Effect: informational — not directly in the model but correlates strongly with barrel%.",
            "PwrMult":
                "PwrMult  ·  Statcast Power Multiplier (0.45–1.75) — composite of all 7 Statcast signals: "
                "barrel% (38%), FB% (15%), xSLG (14%), sweet spot (10%), hard-hit% (10%), pull% (8%), exit velo (5%). "
                "1.0 = league average. Effect: multiplied into the batter's HR rate before park/pitcher adjustments.",
            "Park":
                "Park  ·  Park HR Factor — historical HR rate at today's stadium vs league average. "
                "1.0 = neutral. Coors = 1.28 (most HR-friendly). Petco = 0.89 (most suppressive). Oracle = 0.83. "
                "Effect: multiplied into the combined factor; scaled by this batter's fly-ball tendency.",
            "Pitcher":
                "Pitcher  ·  Pitcher HR Factor (0.55–1.60) — how homer-prone today's starter is. "
                "Blends HR/FB rate (40%), Statcast contact quality allowed (40%), K%+GB% suppressor (20%). "
                "Effect: multiplied into the combined factor. Above 1.0 = pitcher gives up more HRs than average.",
            "Weather":
                "Weather  ·  Weather Factor (0.80–1.20) — impact of temperature and wind on HR probability. "
                "Hot air is thinner = ball carries farther. Wind blowing out = strong boost; in = suppressor. "
                "Effect: multiplied into the combined factor. Dome teams always receive 1.0.",
            "Platoon":
                "Platoon  ·  Platoon Split Factor — batter's HR rate vs this pitcher's hand vs their overall rate. "
                "Bayesian-shrunk using actual split PA counts (50-PA standard constant). "
                "Effect: multiplied into the combined factor. Above 1.0 = batter has a platoon advantage today.",
            "Season PA":
                "Season PA  ·  Season Plate Appearances — total PA this season. "
                "Effect: drives how much the model regresses toward league average. "
                "Low PA → heavy regression toward 0.033 HR/PA; high PA → model trusts the actual rate.",
            "Season HR":
                "Season HR  ·  Season Home Runs — total HRs hit this season. "
                "Combined with Season PA to compute the raw season HR/PA rate before Bayesian adjustment.",
            "Recent PA":
                "Recent PA  ·  Recent Plate Appearances — PA in the last 20 games. "
                "Effect: determines whether recent form gets blended into the rate. "
                "Requires ≥20 recent PA for the recent rate to carry any weight (30% weight, season 70%).",
            "HR Rate":
                "HR Rate  ·  Blended HR/PA Rate — the model's final adjusted rate before game-day factors. "
                "Combines Bayesian-regressed season rate, recent form blend, and Statcast power multiplier. "
                "Effect: this is λ before being multiplied by park, pitcher, weather, platoon, and expected PA.",
            "Streak":
                "Streak  ·  Hot/Cold Streak Factor (0.93–1.08) — last 10-game HR rate vs full-season average. "
                "Capped at ±8% to avoid overreacting to small samples. Requires ≥8 recent PA and ≥30 season PA. "
                "Effect: multiplied into the adjusted rate before the Poisson calculation.",
            "K Factor":
                "K Factor  ·  Strikeout Suppressor (0.85–1.00) — high K% = fewer balls in play = fewer HR chances. "
                "One-sided: only suppresses above league avg K% (22.5%). Never boosts contact hitters. "
                "Effect: multiplied into the adjusted rate. Max suppression is −15% at very high K%.",
            "Pitcher HR/9":
                "Pitcher HR/9  ·  HRs Allowed per 9 Innings — season figure for today's starter. "
                "League avg = 1.09. Above 1.4 = HR-prone target. Below 0.8 = strong HR suppressor. "
                "Effect: feeds into the pitcher HR factor; also triggers a +4pt confidence bonus if > 1.36.",
            "Exp PA":
                "Exp PA  ·  Expected Plate Appearances — how many times this batter will bat today. "
                "Lineup spot 1 = ~4.5 PA. Spot 9 = ~3.2 PA. Unknown lineup = 3.8 default. "
                "Effect: directly scales λ — more PA = higher HR probability even at the same HR/PA rate.",
            "Odds":
                "Odds  ·  Best Available American Odds — highest payout line across all tracked sportsbooks. "
                "Higher number = longer shot = bigger payout if the bet wins. "
                "Effect: determines the decimal odds used in the EV% calculation.",
            "Mkt%":
                "Mkt%  ·  Market No-Vig Probability — the book's true estimated HR probability after vig removal. "
                "Formula: raw implied prob ÷ (1 + 7.5% vig). HR props carry 7-10% juice on retail books. "
                "Effect: used as the baseline. Model probability above this = positive edge.",
            "Edge%":
                "Edge%  ·  Model Edge — model probability minus market no-vig probability. "
                "Uses the full model probability (not the EV-capped version). "
                "Effect: primary odds-independent signal. Positive edge = model sees a mispriced line.",
            "EV%":
                "EV%  ·  Expected Value % — [p × (decimal odds−1) − (1−p)] × 100. "
                "Capped: model prob is limited to 1.4× market before calculation, preventing long-shot odds "
                "from inflating EV into the hundreds. Max ~45%. Positive EV = profitable long-run.",
            "Confidence":
                "Confidence  ·  Model Confidence Score (0–100) — how much to trust this probability estimate. "
                "Built from: sample size (35 pts), recent PA (20 pts), edge signal-to-noise (28 pts), "
                "Statcast availability (+8), barrel >12% (+5), pitcher HR/9 >1.4 (+4). "
                "Effect: gates the OIAL and STRONG EDGE ratings — low confidence can't achieve top tiers.",
        }

        # â"€â"€ Column selector â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
        # Column selection persists via session_state; widget lives in All Players tab
        _default_cols = ["Brl%", "SwSp%", "FB%", "GB%", "Pull%", "Exit Velo", "PwrMult", "Park", "Pitcher"]
        selected_toggle = st.session_state.get("model_col_picker", _default_cols)
        visible_cols = _FIXED_COLS + selected_toggle

        def _model_rows(players):
            rows = []
            for p in players:
                pit_fac  = p.get("pitcher_factor", 1.0)
                plat_fac = p.get("platoon_factor", 1.0)
                rows.append({c: _extract(c, p, pit_fac, plat_fac) for c in visible_cols})
            return rows

        _model_df_idx = [0]  # mutable counter for unique keys across calls

        def _render_model_df(players):
            if not players:
                st.info("No players in this view.")
                return
            _model_df_idx[0] += 1
            _mtver = st.session_state.get("_table_ver", 0)
            _df_key = f"model_df_{_model_df_idx[0]}_{_mtver}"
            df = pd.DataFrame(_model_rows(players))
            df = df.fillna("--").replace([np.nan, np.inf, -np.inf, float('inf'), -float('inf')], "--")
            _msel = st.dataframe(df, width='stretch', hide_index=True, column_config=_col_cfg,
                                 on_select="rerun", selection_mode="single-row", key=_df_key)
            _mrows = getattr(getattr(_msel, "selection", None), "rows", [])
            if _mrows and 0 <= _mrows[0] < len(players):
                st.session_state["_table_ver"] = _mtver + 1
                st.session_state["show_modal"] = players[_mrows[0]]
                st.session_state["modal_source_tab"] = "All Players"
                st.session_state["modal_source_section"] = "All Players"
                st.rerun()

        prime      = [p for p in all_by_model_raw if p.get("model_prob", 0) >= PRIME_FLOOR][:60]
        prime_time = [p for p in all_by_model     if p.get("model_prob", 0) >= PRIME_FLOOR][:60]
        watch      = [p for p in all_by_model     if p.get("model_prob", 0) < PRIME_FLOOR][:20]

        # Shared search bar — filters all three model tabs simultaneously
        _search_query = st.text_input(
            "🔍 Search players",
            value=st.session_state.get("model_search", ""),
            placeholder="Name or team (e.g. 'Judge', 'NYY', 'Schwarber')…",
            key="model_search",
            label_visibility="collapsed",
        )
        _sq = _search_query.strip().lower()

        def _apply_search(players):
            if not _sq:
                return players
            return [
                p for p in players
                if _sq in (p.get("player_name") or "").lower()
                or _sq in (p.get("team") or "").lower()
                or _sq in (p.get("opponent") or "").lower()
            ]

        with sub2:
            with st.expander("⚙️ Customize columns", expanded=False):
                st.caption("Each option shows the full stat name, description, and how it affects the model. "
                           "Player · Team · Spot · Vs · Model% are always shown.")
                st.multiselect(
                    "Select columns to display:",
                    options=_TOGGLE_COLS,
                    default=selected_toggle,
                    format_func=lambda c: _COL_FULL.get(c, c),
                    key="model_col_picker",
                )
            _all_filtered = _apply_search(all_by_model)
            if _sq and not _all_filtered:
                st.info(f'No players matching "{_search_query}".')
            else:
                # Cap at 100 only when not searching
                _all_display = _all_filtered if _sq else _all_filtered[:100]
                if not _sq and len(all_by_model) > 100:
                    st.caption(f"Showing top 100 of {len(all_by_model)} players by model probability. Use the search box above to find specific players.")
                _render_model_df(_all_display)

        with sub3:
            _prime_filtered = _apply_search(prime)
            if not _prime_filtered:
                st.info(f"No {'matches for \"' + _search_query + '\"' if _sq else 'players with ≥15% model HR probability today'}.")
            else:
                st.caption(f"⭐ {len(_prime_filtered)} player{'s' if len(_prime_filtered) != 1 else ''} with model HR probability ≥ 15%{' matching search' if _sq else ''}.")
                _render_model_df(_prime_filtered)

        with sub4:
            _ptf_filtered = _apply_search(prime_time)
            _ptf_et = ((cutoff_utc_hour - 4) % 24) if cutoff_utc_hour is not None else None
            if _ptf_et is not None:
                _ptf_h12  = _ptf_et % 12 or 12
                _ptf_ampm = "AM" if _ptf_et < 12 else "PM"
                _ptf_label = f"games at/after {_ptf_h12}:00 {_ptf_ampm} ET"
            else:
                _ptf_label = None
            if not _ptf_filtered:
                if cutoff_utc_hour is None:
                    st.info("No game start time selected. Set 'Only show games starting after…' in the sidebar to filter prime plays by game time.")
                else:
                    st.info(f"No prime players for {_ptf_label}{' matching \"' + _search_query + '\"' if _sq else ''}.")
            else:
                _ptf_hdr = (f"⏰ {len(_ptf_filtered)} prime player{'s' if len(_ptf_filtered) != 1 else ''} "
                            + (f"for {_ptf_label}" if _ptf_label else "— no time filter active")
                            + (" matching search" if _sq else "") + ".")
                st.caption(_ptf_hdr)
                _render_model_df(_ptf_filtered)

        with sub5:
            _watch_filtered = _apply_search(watch)
            if not _watch_filtered:
                st.info(f"No {'matches for \"' + _search_query + '\"' if _sq else 'watch list players today'}.")
            else:
                st.caption(f"📋 {len(_watch_filtered)} player{'s' if len(_watch_filtered) != 1 else ''} with model HR probability < 15%{' matching search' if _sq else ''}.")
                _render_model_df(_watch_filtered)


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
        status_html, is_live = _game_status_badge(p)
        border = "#f87171" if is_live else "#1e3a5f"
        status_row = (f"<div style='font-size:11px; margin:2px 0 8px;'>{status_html}</div>"
                      if status_html else "")
        st.markdown(
            f"<div style='background:#0d0d1e; border:1px solid {border}; border-radius:10px; "
            f"padding:14px 16px; margin-bottom:10px;'>"
            f"<div style='display:flex; justify-content:space-between; align-items:baseline;'>"
            f"<div style='font-size:15px; font-weight:800; color:#f0f0f0;'>{name}</div>"
            f"<div style='font-size:18px; font-weight:900; color:{hc};'>HIT {hsco:.0f}</div>"
            f"</div>"
            f"<div style='font-size:12px; color:#888; margin:2px 0 4px;'>"
            f"{team} vs {opp} &nbsp;·&nbsp; vs {pit_n}</div>"
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
            + (f"<div style='margin-top:8px; font-size:12px; display:flex; gap:16px;'>"
               f"<span style='color:#60a5fa; font-weight:700;'>{_fmt_american(odds)}</span>"
               f"<span style='color:{ev_c};'>EV {ev:+.1f}%</span>"
               f"<span style='color:#888;'>HR Prob {p.get('model_prob',0)*100:.1f}%</span>"
               f"</div>" if odds else "")
            + "</div>",
            unsafe_allow_html=True,
        )
        _bc, _fc = st.columns(2)
        with _bc:
            if st.button("ℹ️ Player Info",
                         key=f"{key_prefix}_modal_{p.get('player_id','')}{name[:6]}",
                         use_container_width=True, type="primary"):
                _jig_src = "JIG AI" if "ai" in key_prefix else ("JIG Way" if "way" in key_prefix else "JIG")
                st.session_state["show_modal"] = p
                st.session_state["modal_source_tab"] = _jig_src
                st.session_state["modal_source_section"] = _jig_src
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
                bts_rows.append({
                    "#":        i + 1,
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
            st.caption(f"{len(qualified)} players pass all Hit criteria — ranked by HIT score.")
            for entry in qualified:
                _hit_card(entry, key_prefix="hp")

    with _ha:
        _ha_ver = st.session_state.get("_hit_all_ver", 0)
        rows = []
        for entry in scored:
            p = entry["player"]
            xba, ld, ss, hh, kf, pa = _hit_metrics(p)
            rows.append({
                "Player":   p.get("player_name", ""),
                "Team":     p.get("team", ""),
                "HIT":      entry["hit"],
                "Passes":   "✅" if entry["passes"] else "",
                "xBA":      f"{xba:.3f}" if xba else "--",
                "LD%":      f"{ld:.1f}%" if ld else "--",
                "Sweet%":   f"{ss:.1f}%" if ss else "--",
                "Hard Hit": f"{hh:.1f}%" if hh else "--",
                "K-Factor": f"{kf:.2f}",
                "Exp PA":   f"{pa:.1f}",
                "Odds":     _fmt_american(p.get("best_american")),
                "EV%":      f"{p.get('ev_pct', 0):+.1f}%",
                "HR Prob":  f"{p.get('model_prob', 0)*100:.1f}%",
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
    all_players_raw = data.get("all_players", [])
    all_players = (
        _gate_data(data, _cutoff).get("all_players", [])
        if _cutoff is not None else all_players_raw
    )

    st.markdown(
        "<div style='font-size:22px; font-weight:900; color:#FF6666; "
        "letter-spacing:2px; margin-bottom:2px;'>⚙️ JIG</div>"
        "<div style='font-size:12px; color:#888; margin-bottom:12px;'>"
        "Power contact index — xSLG · ISO · Hard Hit · Barrel · Launch Angle · Pull% · Pitcher Mix</div>",
        unsafe_allow_html=True,
    )

    _JIG_SLIDER_KEYS = ["jig_slg","jig_iso","jig_hh","jig_brl","jig_la","jig_pull","jig_pit","jig_score"]
    with st.expander("⚙️ JIG Thresholds", expanded=False):
        if st.button("↺ Reset to defaults", key="jig_reset"):
            for _k in _JIG_SLIDER_KEYS:
                st.session_state.pop(_k, None)
            st.rerun()
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            slg_min    = st.slider("Min xSLG",          0.00, 0.70, 0.40, 0.01, key="jig_slg")
            iso_min    = st.slider("Min ISO",            0.00, 0.45, 0.15, 0.01, key="jig_iso")
        with tc2:
            hh_min     = st.slider("Min Hard Hit%",      0.0, 60.0, 35.0, 0.5,  key="jig_hh")
            brl_min    = st.slider("Min Barrel%",         0.0, 25.0,  5.0, 0.5,  key="jig_brl")
        with tc3:
            la_min     = st.slider("Min Launch Angle°",  0.0, 25.0, 10.0, 0.5,  key="jig_la")
            pull_min   = st.slider("Min Pull%",          0.0, 60.0, 38.0, 0.5,  key="jig_pull")
            pit_min    = st.slider("Min Pitcher Factor", 0.70, 1.30, 0.95, 0.01, key="jig_pit")
        score_min  = st.slider("Min JIG Score (Picks gate)", 0, 100, 40, 1, key="jig_score")

    def _jig_metrics(p):
        # Prefer xSLG (Statcast expected); fall back to actual season SLG
        xslg_v = _pf(p.get("xslg"), 0.0)
        slg  = xslg_v if xslg_v > 0.0 else _pf(p.get("actual_slg"), 0.0)
        iso  = _pf(p.get("xiso"), 0.0)
        hh   = _pf(p.get("hard_hit"))
        brl  = _pf(p.get("barrel_pct"))
        la   = _pf(p.get("avg_launch_angle"))
        pull = _pf(p.get("pull_pct"))
        pit  = _pf(p.get("pitcher_factor"), 1.0)
        return slg, iso, hh, brl, la, pull, pit

    def _slg_label(p):
        return "xSLG" if _pf(p.get("xslg"), 0.0) > 0.0 else "SLG"

    def _n(val, thr, scale):
        return min(max((val - thr) / scale + 0.5, 0.0), 1.0)

    def _jig_ai_score(metrics):
        # AI-optimized: barrel-first weighting based on HR-prediction importance
        slg, iso, hh, brl, la, pull, pit = metrics
        return round((
            _n(brl,  brl_min,  6.0)  * 0.25 +
            _n(slg,  slg_min,  0.15) * 0.20 +
            _n(pit,  pit_min,  0.15) * 0.20 +
            _n(hh,   hh_min,   12.0) * 0.15 +
            _n(iso,  iso_min,  0.12) * 0.10 +
            _n(pull, pull_min, 8.0)  * 0.07 +
            _n(la,   la_min,   10.0) * 0.03
        ) * 100, 1)

    def _jig_way_score(metrics):
        # The JIG Way: SLG → Pitcher → Pull% → ISO → Barrel% → Hard Hit → Launch
        slg, iso, hh, brl, la, pull, pit = metrics
        return round((
            _n(slg,  slg_min,  0.15) * 0.25 +
            _n(pit,  pit_min,  0.15) * 0.20 +
            _n(pull, pull_min, 8.0)  * 0.15 +
            _n(iso,  iso_min,  0.12) * 0.15 +
            _n(brl,  brl_min,  6.0)  * 0.10 +
            _n(hh,   hh_min,   12.0) * 0.10 +
            _n(la,   la_min,   10.0) * 0.05
        ) * 100, 1)

    def _jig_card(entry, key_prefix="jig"):
        p   = entry["player"]
        jig = entry["jig"]
        slg, iso, hh, brl, la, pull, pit = entry["metrics"]
        name  = p.get("player_name", "Unknown")
        team  = p.get("team", "")
        opp   = p.get("opponent", "")
        pit_n = p.get("pitcher_name", "TBD")
        odds  = p.get("best_american")
        ev    = p.get("ev_pct", 0)
        ev_c  = "#4ade80" if ev > 0 else "#f87171"
        jc    = "#4ade80" if jig >= 60 else "#f59e0b" if jig >= 40 else "#f87171"
        status_html, is_live = _game_status_badge(p)
        border = "#f87171" if is_live else "#1e3a5f"
        status_row = (f"<div style='font-size:11px; margin:2px 0 8px;'>{status_html}</div>"
                      if status_html else "")
        st.markdown(
            f"<div style='background:#0d0d1e; border:1px solid {border}; border-radius:10px; "
            f"padding:14px 16px; margin-bottom:10px;'>"
            f"<div style='display:flex; justify-content:space-between; align-items:baseline;'>"
            f"<div style='font-size:15px; font-weight:800; color:#f0f0f0;'>{name}</div>"
            f"<div style='font-size:18px; font-weight:900; color:{jc};'>JIG {jig:.0f}</div>"
            f"</div>"
            f"<div style='font-size:12px; color:#888; margin:2px 0 4px;'>"
            f"{team} vs {opp} &nbsp;·&nbsp; vs {pit_n}</div>"
            f"{status_row}"
            f"<div style='display:grid; grid-template-columns:repeat(4,1fr); gap:6px; font-size:11px;'>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>{_slg_label(p)}</div>{_badge(slg, slg_min, f'{slg:.3f}')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>ISO</div>{_badge(iso, iso_min, f'{iso:.3f}')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>Hard Hit</div>{_badge(hh, hh_min, f'{hh:.1f}%')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>Barrel</div>{_badge(brl, brl_min, f'{brl:.1f}%')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>Launch°</div>{_badge(la, la_min, '--' if p.get('avg_launch_angle') in (None, '--') else f'{la:.1f}°')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>Pull%</div>{_badge(pull, pull_min, '--' if p.get('pull_pct') in (None, '--') else f'{pull:.1f}%')}</div>"
            f"<div class='stat-box'>"
            f"<div style='color:#666;'>Pit Fac</div>{_badge(pit, pit_min, f'{pit:.3f}x')}</div>"
            f"</div>"
            + (f"<div style='margin-top:8px; font-size:12px; display:flex; gap:16px;'>"
               f"<span style='color:#FF6666; font-weight:700;'>{_fmt_american(odds)}</span>"
               f"<span style='color:{ev_c};'>EV {ev:+.1f}%</span>"
               f"<span style='color:#888;'>Model {p.get('model_prob',0)*100:.1f}%</span>"
               f"</div>" if odds else "")
            + "</div>",
            unsafe_allow_html=True,
        )
        _bc, _fc = st.columns(2)
        with _bc:
            if st.button("ℹ️ Player Info", key=f"{key_prefix}_modal_{p.get('player_id','')}{name[:6]}",
                         use_container_width=True, type="primary"):
                st.session_state["show_modal"] = p
                st.rerun()
        with _fc:
            st.link_button("📲 Open on FanDuel", _fanduel_url(name), use_container_width=True)

    def _render_jig_views(score_fn, key_sfx):
        _entries = []
        for p in all_players:
            m = _jig_metrics(p)   # compute once; reused in card, debug, and All tab
            s = score_fn(m)
            _entries.append({"player": p, "jig": s, "metrics": m, "passes": s >= score_min})
        scored    = sorted(_entries, key=lambda x: x["jig"], reverse=True)
        qualified = [x for x in scored if x["passes"]]
        prime_timed = [x for x in qualified
                       if x["player"].get("best_american") and x["player"].get("ev_pct", 0) > 0]

        # Prime (unfiltered) — rescore raw players when time gate is active
        if _cutoff is not None and all_players_raw is not all_players:
            _raw_entries = []
            for p in all_players_raw:
                m = _jig_metrics(p)
                s = score_fn(m)
                _raw_entries.append({"player": p, "jig": s, "metrics": m, "passes": s >= score_min})
            _raw_qual = [x for x in _raw_entries if x["passes"]]
            prime = [x for x in _raw_qual
                     if x["player"].get("best_american") and x["player"].get("ev_pct", 0) > 0]
        else:
            prime = prime_timed

        with st.expander(f"🔍 Debug — {len(all_players)} players, {len(qualified)} qualified", expanded=len(qualified)==0):
            st.write(f"**Gate:** JIG ≥ {score_min} | slg {slg_min} iso {iso_min} hh {hh_min} brl {brl_min} la {la_min} pull {pull_min} pit {pit_min}")
            if all_players:
                dbg = []
                for entry in scored[:20]:
                    p = entry["player"]
                    slg, iso, hh, brl, la, pull, pit = entry["metrics"]
                    dbg.append({
                        "Name": p.get("player_name","")[:18], "JIG": entry["jig"],
                        "passes": entry["passes"],
                        "slg→": round(slg,3), "iso→": round(iso,3),
                        "hh→": round(hh,1),   "brl→": round(brl,1),
                        "la→": round(la,1),   "pull→": round(pull,1),
                        "pit→": round(pit,3),
                    })
                st.dataframe(pd.DataFrame(dbg), hide_index=True, use_container_width=True)
            else:
                st.warning("all_players is EMPTY — pipeline returned no players.")

        # Read time-gate info for Prime Time tab label
        _jig_cutoff = st.session_state.get("cutoff_utc_hour")
        if _jig_cutoff is not None:
            _jig_et_h  = (_jig_cutoff - 4) % 24
            _jig_h12   = _jig_et_h % 12 or 12
            _jig_ampm  = "AM" if _jig_et_h < 12 else "PM"
            _jig_time_label = f"{_jig_h12}:00 {_jig_ampm} ET"
        else:
            _jig_time_label = None

        _jq, _jp, _ja, _jpr, _jpt = st.tabs([
            "📱 Quick Picks",
            f"⚡ Picks ({len(qualified)})",
            f"📊 All ({len(scored)})",
            f"⭐ Prime ({len(prime)})",
            f"⏰ Prime Time ({len(prime_timed)})",
        ])

        with _jq:
            if not qualified:
                st.info("No players meet all JIG thresholds — lower thresholds in the expander above.")
            else:
                for entry in qualified[:3]:
                    _jig_card(entry, key_prefix=f"jq_{key_sfx}")
                if len(qualified) > 3:
                    st.caption(f"Top 3 of {len(qualified)} qualified. See Picks tab for all.")

        with _jp:
            if not qualified:
                st.info("No players meet all JIG thresholds — lower thresholds in the expander above.")
            else:
                st.caption(f"{len(qualified)} players pass all JIG criteria — ranked by JIG score.")
                for entry in qualified:
                    _jig_card(entry, key_prefix=f"jp_{key_sfx}")

        with _ja:
            _ja_ver = st.session_state.get(f"_jig_all_ver_{key_sfx}", 0)
            rows = []
            for entry in scored:
                p = entry["player"]
                slg, iso, hh, brl, la, pull, pit = entry["metrics"]
                rows.append({
                    "Player":   p.get("player_name", ""),
                    "Team":     p.get("team", ""),
                    "JIG":      entry["jig"],
                    "Passes":   "✅" if entry["passes"] else "",
                    "xSLG":     f"{slg:.3f}",
                    "ISO":      f"{iso:.3f}" if iso else "--",
                    "Hard Hit": f"{hh:.1f}%" if hh else "--",
                    "Barrel":   f"{brl:.1f}%" if brl else "--",
                    "Launch°":  f"{la:.1f}" if la else "--",
                    "Pull%":    f"{pull:.1f}%" if pull else "--",
                    "Pit Fac":  f"{pit:.3f}",
                    "Odds":     _fmt_american(p.get("best_american")),
                    "EV%":      f"{p.get('ev_pct',0):+.1f}%",
                    "Model%":   f"{p.get('model_prob',0)*100:.1f}%",
                })
            if rows:
                _ja_sel = st.dataframe(
                    pd.DataFrame(rows), hide_index=True, use_container_width=True,
                    on_select="rerun", selection_mode="single-row",
                    key=f"jig_all_df_{key_sfx}_{_ja_ver}",
                    column_config={
                        "JIG": st.column_config.ProgressColumn("JIG", min_value=0, max_value=100, format="%.0f"),
                    },
                )
                _ja_rows = getattr(getattr(_ja_sel, "selection", None), "rows", [])
                if _ja_rows and 0 <= _ja_rows[0] < len(scored):
                    st.session_state[f"_jig_all_ver_{key_sfx}"] = _ja_ver + 1
                    _jig_all_src = "JIG AI" if key_sfx == "ai" else "JIG Way"
                    st.session_state["show_modal"] = scored[_ja_rows[0]]["player"]
                    st.session_state["modal_source_tab"] = _jig_all_src
                    st.session_state["modal_source_section"] = _jig_all_src
                    st.rerun()

        with _jpr:
            if not prime:
                st.info("No prime JIG plays — need qualified players with positive-EV odds.")
            else:
                st.caption(f"{len(prime)} players pass all JIG criteria with positive EV.")
                for entry in prime:
                    _jig_card(entry, key_prefix=f"jpr_{key_sfx}")

        with _jpt:
            if _jig_cutoff is None:
                st.info("No game start time selected. Set 'Only show games starting after…' in the sidebar to show prime JIG plays for later games only.")
            elif not prime_timed:
                st.info(f"No prime JIG plays for games at/after {_jig_time_label}.")
            else:
                st.caption(
                    f"⏰ {len(prime_timed)} prime JIG player{'s' if len(prime_timed) != 1 else ''} "
                    f"for games at/after {_jig_time_label} — ranked by JIG score."
                )
                for entry in prime_timed:
                    _jig_card(entry, key_prefix=f"jpt_{key_sfx}")

    # ── HVY Pitch Mix helpers ─────────────────────────────────────────────────

    def _hvy_card(entry, key_prefix="hvy"):
        p    = entry["player"]
        hvy  = entry["jig"]
        base = entry.get("base_jig", hvy)
        ctx  = entry.get("ctx", {})
        slg, iso, hh, brl, la, pull, pit = entry["metrics"]
        name = p.get("player_name", "Unknown")
        team = p.get("team", ""); opp = p.get("opponent", "")
        pit_n = p.get("pitcher_name", "TBD")
        odds  = p.get("best_american")
        ev    = p.get("ev_pct", 0)
        ev_c  = "#4ade80" if ev > 0 else "#f87171"
        hc    = "#4ade80" if hvy >= 60 else "#f59e0b" if hvy >= 40 else "#f87171"
        mod   = ctx.get("hvy_modifier", 1.0)
        mod_c = "#4ade80" if mod > 1.0 else "#f87171" if mod < 1.0 else "#888"
        mod_s = f"{'▲' if mod > 1.0 else '▼' if mod < 1.0 else '●'} {mod:.2f}×"
        status_html, is_live = _game_status_badge(p)
        border   = "#f87171" if is_live else "#1e3a5f"
        status_row = (f"<div style='font-size:11px;margin:2px 0 8px;'>{status_html}</div>"
                      if status_html else "")
        odds_str = (f"+{odds}" if odds and odds > 0 else str(odds)) if odds else "—"
        st.markdown(
            f"<div style='background:#111827;border:1px solid {border};border-radius:10px;"
            f"padding:14px 16px;margin-bottom:6px;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline;'>"
            f"<div style='font-size:15px;font-weight:800;color:#f0f0f0;'>{name}</div>"
            f"<div style='font-size:18px;font-weight:900;color:{hc};'>HVY {hvy:.0f}"
            f"<span style='font-size:10px;color:#666;margin-left:4px;'>(Way {base:.0f})</span></div>"
            f"</div>"
            f"<div style='font-size:12px;color:#888;margin:2px 0 4px;'>"
            f"{team} vs {opp} &nbsp;·&nbsp; vs {pit_n}</div>"
            f"{status_row}"
            f"<div style='display:flex;gap:14px;font-size:12px;margin-bottom:4px;'>"
            f"<span style='color:#f0f0f0;font-weight:700;'>{odds_str}</span>"
            f"<span>EV: <b style='color:{ev_c};'>{ev:+.1f}%</b></span>"
            f"<span>Edge: <b style='color:#60a5fa;'>{p.get('edge_pct',0):+.1f}%</b></span>"
            f"<span style='font-size:10px;color:{mod_c};'>Modifier: {mod_s}</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        pitcher_arsenal = ctx.get("pitcher_arsenal", [])
        hand_splits     = ctx.get("hand_splits", {})
        h2h             = ctx.get("h2h", {})
        batter_vs       = ctx.get("batter_vs", {})
        _data_year      = ctx.get("data_year", config.CURRENT_SEASON)
        _yr_label       = f" ({_data_year})" if _data_year != config.CURRENT_SEASON else f" ({config.CURRENT_SEASON})"
        _prior_note     = (f" ⚠️ *{_data_year} data — pitcher has no {config.CURRENT_SEASON} starts yet*"
                           if _data_year != config.CURRENT_SEASON else "")

        from clients.pitch_mix import pitch_label, pitch_color

        with st.expander("📊 Pitch Mix Analysis", expanded=True):
            if _prior_note:
                st.caption(_prior_note)
            _c1, _c2 = st.columns([3, 2])

            with _c1:
                # ── Arsenal table ──────────────────────────────────────────────
                st.markdown(f"**🔥 Pitcher Arsenal{_yr_label}**")
                if pitcher_arsenal:
                    pitches = sorted(pitcher_arsenal, key=lambda x: x.get("pitch_pct", 0), reverse=True)[:6]
                    rows = ""
                    for px in pitches:
                        pt   = px.get("pitch_type", "")
                        lbl  = pitch_label(pt)
                        pc   = pitch_color(pt)
                        use  = f"{px.get('pitch_pct', 0)*100:.0f}%"
                        spd  = f"{px.get('avg_speed'):.1f}" if px.get("avg_speed") else "—"
                        whf  = f"{px.get('whiff_pct')*100:.0f}%" if px.get("whiff_pct") is not None else "—"
                        hh_p = f"{px.get('hard_hit_pct')*100:.0f}%" if px.get("hard_hit_pct") is not None else "—"
                        rv   = px.get("rv_per100")
                        rv_s = f"{rv:+.1f}" if rv is not None else "—"
                        rv_c = "#f87171" if (rv or 0) > 0 else "#4ade80" if (rv or 0) < 0 else "#888"
                        rows += (
                            f"<tr><td><b style='color:{pc};'>{lbl}</b></td>"
                            f"<td>{use}</td><td>{spd}</td><td>{whf}</td><td>{hh_p}</td>"
                            f"<td style='color:{rv_c};font-size:10px;'>{rv_s}</td></tr>"
                        )
                    st.markdown(
                        "<table style='width:100%;font-size:11px;border-collapse:collapse;'>"
                        "<tr style='color:#888;border-bottom:1px solid #333;'>"
                        "<th align='left'>Pitch</th><th>Use%</th><th>MPH</th>"
                        "<th>Whiff</th><th>HH%</th><th>RV/100</th></tr>"
                        f"{rows}</table>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("No Savant arsenal data for this pitcher.")

                # ── Batter vs pitch types ──────────────────────────────────────
                st.markdown("**🎯 Batter vs These Pitches (2026)**")
                if pitcher_arsenal and batter_vs:
                    brows = ""
                    for px in pitches[:5]:
                        pt  = px.get("pitch_type", "")
                        lbl = pitch_label(pt)
                        pc  = pitch_color(pt)
                        bpt = batter_vs.get(pt, {})
                        if bpt.get("pa", 0) < 3:
                            brows += (f"<tr><td><b style='color:{pc};'>{lbl}</b></td>"
                                      f"<td colspan='5' style='color:#555;'>< 3 PA</td></tr>")
                            continue
                        bslg = bpt.get("slg", 0.0)
                        slg_c = "#4ade80" if bslg > 0.450 else "#f87171" if bslg < 0.300 else "#f0f0f0"
                        brows += (
                            f"<tr><td><b style='color:{pc};'>{lbl}</b></td>"
                            f"<td>{bpt['pa']}</td>"
                            f"<td>{bpt['hr']}</td>"
                            f"<td>{bpt.get('ba', 0):.3f}</td>"
                            f"<td style='color:{slg_c};'>{bslg:.3f}</td>"
                            f"<td>{bpt.get('k_pct',0)*100:.0f}%</td></tr>"
                        )
                    if brows:
                        st.markdown(
                            "<table style='width:100%;font-size:11px;border-collapse:collapse;margin-top:4px;'>"
                            "<tr style='color:#888;border-bottom:1px solid #333;'>"
                            "<th align='left'>Pitch</th><th>PA</th><th>HR</th>"
                            "<th>BA</th><th>SLG</th><th>K%</th></tr>"
                            f"{brows}</table>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No batter split data available.")

            with _c2:
                # ── Pitcher splits vs LHB / RHB ───────────────────────────────
                st.markdown(f"**📈 Pitcher Splits{_yr_label}**")
                bside = p.get("batter_side", "R")
                this_hand = "L" if bside == "L" else "R"
                for hand, lbl in [("R", "vs RHB"), ("L", "vs LHB")]:
                    sp = hand_splits.get(hand, {})
                    sp_pa = sp.get("pa", 0)
                    if sp_pa == 0:
                        st.markdown(
                            f"<div style='background:#1a2332;border-radius:6px;"
                            f"padding:6px 10px;margin-bottom:6px;'>"
                            f"<span style='font-size:11px;color:#555;'>{lbl}: no data</span>"
                            f"</div>", unsafe_allow_html=True)
                        continue
                    sp_hr  = sp.get("hr", 0)
                    sp_hrr = sp_hr / sp_pa
                    sp_slg = sp.get("slg", 0.0)
                    sp_iso = sp.get("iso", 0.0)
                    hdr_c  = "#fbbf24" if hand == this_hand else "#888"
                    hr_c   = "#f87171" if sp_hrr > 0.035 else "#4ade80" if sp_hrr < 0.020 else "#ccc"
                    badge  = " ← batter" if hand == this_hand else ""
                    st.markdown(
                        f"<div style='background:#1a2332;border-radius:6px;"
                        f"padding:7px 10px;margin-bottom:6px;'>"
                        f"<div style='font-size:11px;font-weight:700;color:{hdr_c};'>"
                        f"{lbl}{badge}</div>"
                        f"<div style='font-size:11px;color:#ccc;'>"
                        f"PA: <b>{sp_pa}</b> &nbsp; HR: <b style='color:{hr_c};'>{sp_hr}</b>"
                        f" &nbsp; HR/PA: <b>{sp_hrr:.3f}</b><br>"
                        f"SLG: <b>{sp_slg:.3f}</b> &nbsp; ISO: <b>{sp_iso:.3f}</b>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )

                # ── Head-to-head ───────────────────────────────────────────────
                st.markdown("**⚔️ Head-to-Head (Career)**")
                h2h_pa = h2h.get("pa", 0)
                if h2h_pa >= 1:
                    try:
                        ops_f = float(str(h2h.get("ops", ".000")).replace(",", "") or 0)
                    except (ValueError, TypeError):
                        ops_f = 0.0
                    ops_c = "#4ade80" if ops_f > 0.800 else "#f87171" if ops_f < 0.600 else "#ccc"
                    st.markdown(
                        f"<div style='background:#1a2332;border-radius:6px;padding:7px 10px;'>"
                        f"<div style='font-size:11px;color:#ccc;'>"
                        f"PA: <b>{h2h_pa}</b> &nbsp; HR: <b>{h2h.get('hr',0)}</b>"
                        f" &nbsp; K: <b>{h2h.get('k',0)}</b> &nbsp; BB: <b>{h2h.get('bb',0)}</b><br>"
                        f"AVG: <b>{h2h.get('avg','.000')}</b> &nbsp;"
                        f"SLG: <b>{h2h.get('slg','.000')}</b> &nbsp;"
                        f"OPS: <b style='color:{ops_c};'>{h2h.get('ops','.000')}</b>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
                    if h2h_pa < 5:
                        st.caption(f"⚠️ Only {h2h_pa} PA — small sample, treat as context only")
                else:
                    st.markdown(
                        "<div style='background:#1a2332;border-radius:6px;padding:7px 10px;'>"
                        "<div style='font-size:11px;color:#555;'>"
                        "No career matchup history recorded</div></div>",
                        unsafe_allow_html=True,
                    )

        _fb, _fc = st.columns([1, 1])
        with _fb:
            if st.button("ℹ️ Player Info",
                         key=f"{key_prefix}_modal_{p.get('player_id','')}{name[:6]}",
                         use_container_width=True, type="primary"):
                st.session_state["show_modal"] = p
                st.session_state["modal_source_tab"] = "HVY Pitch Mix"
                st.session_state["modal_source_section"] = "HVY Pitch Mix"
                st.rerun()
        with _fc:
            st.link_button("📲 Open on FanDuel", _fanduel_url(name), use_container_width=True)

    def _render_hvy_views(hvy_contexts: dict):
        """Render HVY Pitch Mix views — JIG Way × pitch matchup modifier."""
        _entries = []
        for p in all_players:
            m   = _jig_metrics(p)
            pid = p.get("player_id")
            ctx = hvy_contexts.get(pid, {})
            mod = ctx.get("hvy_modifier", 1.0)
            base = _jig_way_score(m)
            hvy  = round(min(100.0, base * mod), 1)
            _entries.append({
                "player": p, "jig": hvy, "base_jig": base,
                "metrics": m, "ctx": ctx, "passes": hvy >= score_min,
            })

        scored    = sorted(_entries, key=lambda x: x["jig"], reverse=True)
        qualified = [x for x in scored if x["passes"]]
        prime     = [x for x in qualified
                     if x["player"].get("best_american") and x["player"].get("ev_pct", 0) > 0]

        if _cutoff is not None and all_players_raw is not all_players:
            _raw = []
            for p in all_players_raw:
                m   = _jig_metrics(p)
                pid = p.get("player_id")
                ctx = hvy_contexts.get(pid, {})
                hvy = round(min(100.0, _jig_way_score(m) * ctx.get("hvy_modifier", 1.0)), 1)
                _raw.append({"player": p, "jig": hvy, "metrics": m, "ctx": ctx, "passes": hvy >= score_min})
            prime = [x for x in _raw
                     if x["passes"] and x["player"].get("best_american") and x["player"].get("ev_pct", 0) > 0]

        _hvy_cutoff = st.session_state.get("cutoff_utc_hour")
        if _hvy_cutoff is not None:
            _h12  = (_hvy_cutoff - 4) % 24
            _tlbl = f"{_h12 % 12 or 12}:00 {'AM' if _h12 < 12 else 'PM'} ET"
        else:
            _tlbl = None

        with st.expander(f"🔍 Debug — {len(all_players)} players, {len(qualified)} qualified HVY",
                         expanded=len(qualified) == 0):
            st.write(f"**Gate:** HVY ≥ {score_min} | "
                     f"slg {slg_min} iso {iso_min} hh {hh_min} brl {brl_min} "
                     f"la {la_min} pull {pull_min} pit {pit_min}")

        _hq, _hp, _ha, _hpr = st.tabs([
            "📱 Quick Picks",
            f"⚡ Picks ({len(qualified)})",
            "📋 All Players",
            "🏆 Prime Picks",
        ])

        with _hq:
            if not qualified:
                st.info("No players meet all JIG thresholds — lower thresholds above.")
            else:
                for entry in qualified[:3]:
                    _hvy_card(entry, key_prefix="hvyq")
                if len(qualified) > 3:
                    st.caption(f"Top 3 of {len(qualified)} qualified. See Picks tab for all.")

        with _hp:
            if not qualified:
                st.info("No players meet all JIG thresholds.")
            else:
                st.caption(f"{len(qualified)} players pass all HVY criteria — ranked by HVY score.")
                for entry in qualified:
                    _hvy_card(entry, key_prefix="hvyp")

        with _ha:
            import pandas as pd
            rows = []
            for entry in scored:
                p   = entry["player"]
                slg, iso, hh, brl, la, pull, pit = entry["metrics"]
                ctx = entry.get("ctx", {})
                rows.append({
                    "Player":   p.get("player_name", ""),
                    "Team":     p.get("team", ""),
                    "HVY":      entry["jig"],
                    "Way Base": entry["base_jig"],
                    "Modifier": f"{ctx.get('hvy_modifier', 1.0):.2f}×",
                    "Pass":     "✅" if entry["passes"] else "",
                    "xSLG":     f"{slg:.3f}",
                    "ISO":      f"{iso:.3f}" if iso else "--",
                    "HH%":      f"{hh:.1f}",
                    "Brl%":     f"{brl:.1f}",
                    "Pitcher":  p.get("pitcher_name", ""),
                })
            if rows:
                _hvy_ver = st.session_state.get("_hvy_all_ver", 0)
                _sel = st.dataframe(
                    pd.DataFrame(rows), hide_index=True, use_container_width=True,
                    on_select="rerun", selection_mode="single-row",
                    key=f"hvy_all_df_{_hvy_ver}",
                    column_config={
                        "HVY": st.column_config.ProgressColumn("HVY", min_value=0, max_value=100, format="%.0f"),
                    },
                )
                _sel_rows = getattr(getattr(_sel, "selection", None), "rows", [])
                if _sel_rows and 0 <= _sel_rows[0] < len(scored):
                    st.session_state["_hvy_all_ver"] = _hvy_ver + 1
                    st.session_state["show_modal"] = scored[_sel_rows[0]]["player"]
                    st.session_state["modal_source_tab"] = "HVY Pitch Mix"
                    st.session_state["modal_source_section"] = "HVY Pitch Mix"
                    st.rerun()

        with _hpr:
            if not prime:
                st.info("No prime HVY plays — need qualified players with positive-EV odds.")
            else:
                st.caption(f"{len(prime)} prime HVY picks with positive EV.")
                for entry in prime:
                    _hvy_card(entry, key_prefix="hvypr")

    # ── Outer tabs ────────────────────────────────────────────────────────────

    _outer_ai, _outer_way, _outer_hvy = st.tabs(["⚡ JIG AI", "🎯 The JIG Way", "🔥 HVY Pitch Mix"])

    with _outer_ai:
        st.caption("Barrel (25%) · xSLG (20%) · Pitcher (20%) · Hard Hit (15%) · ISO (10%) · Pull% (7%) · Launch (3%)")
        _render_jig_views(_jig_ai_score, "ai")

    with _outer_way:
        st.caption("xSLG (25%) · Pitcher (20%) · Pull% (15%) · ISO (15%) · Barrel (10%) · Hard Hit (10%) · Launch (5%)")
        _render_jig_views(_jig_way_score, "way")

    with _outer_hvy:
        st.caption("JIG Way base · Pitcher pitch mix · Batter vs pitch types · Head-to-head · Handedness splits")
        from clients.pitch_mix import HVY_CACHE_VERSION as _HVY_VER
        _hvy_ck = f"hvy_ctx_{data.get('date', '')}_{_HVY_VER}"
        if _hvy_ck not in st.session_state:
            with st.spinner("Loading pitch mix & matchup data for top picks..."):
                from clients import arsenal as _ar_client
                from clients import pitch_mix as _pm_client
                try:
                    _ar_data = _ar_client.get_pitcher_arsenal(config.CURRENT_SEASON)
                except Exception:
                    _ar_data = {}
                _top_hvy = [p for p in all_players if p.get("best_american")][:30]
                _hvy_ctxs = _pm_client.load_hvy_contexts_batch(_top_hvy, _ar_data)
                for _p in all_players:
                    _pid = _p.get("player_id")
                    if _pid and _pid not in _hvy_ctxs:
                        _hvy_ctxs[_pid] = {}
                st.session_state[_hvy_ck] = _hvy_ctxs

        _col_refresh, _ = st.columns([1, 4])
        with _col_refresh:
            if st.button("🔄 Refresh Pitch Data", key="hvy_refresh"):
                st.session_state.pop(_hvy_ck, None)
                st.rerun()

        _render_hvy_views(st.session_state.get(_hvy_ck, {}))

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
            st.info("No picks logged yet. Load the **Today's Picks** tab to auto-log today's selections.")

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
                    st.caption("Tier assigned at pick time using EV%, Edge%, and Confidence — same logic as the Rating column in Today's Picks.")
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

                _log_rows.append({
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
            st.caption("No picks logged yet — open Today's Picks tab to auto-log.")
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

                    _jig = _analysis.get("jig_comparison", {})
                    if _jig.get("ai") and _jig.get("way"):
                        st.markdown("#### JIG AI vs The JIG Way")
                        _jc1, _jc2 = st.columns(2)
                        with _jc1:
                            st.metric("⚡ JIG AI", _jig["ai"].get("Win%","—"),
                                      delta=_jig["ai"].get("ROI%","—"), delta_color="normal")
                            st.caption(f"{_jig['ai'].get('Picks',0)} picks · {_jig['ai'].get('Net P&L','—')}")
                        with _jc2:
                            st.metric("🎯 The JIG Way", _jig["way"].get("Win%","—"),
                                      delta=_jig["way"].get("ROI%","—"), delta_color="normal")
                            st.caption(f"{_jig['way'].get('Picks',0)} picks · {_jig['way'].get('Net P&L','—')}")

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
        )
        if new_br != st.session_state.get("bankroll_override"):
            st.session_state["bankroll_override"] = new_br

        # Show current bankroll = input + cumulative settled P&L
        try:
            _br_results = pnl_tracker._load_results()
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
            _odds_players = _apply_ui_filters(
                _slip_data.get("all_players", []), _fd_min_ev, _fd_min_edge,
                cutoff_utc_hour=st.session_state.get("cutoff_utc_hour"),
                min_confidence=_fd_min_conf,
            )
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
                    ev_color  = "#4ade80" if ev >= 0 else "#f87171"
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋  TODAY'S PICKS",
        "📊  PERFORMANCE",
        "🎯  ADVANCED STRATEGIES",
        "⚙️  JIG",
        "🏃  HITS",
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
            tab_performance()
        except Exception as _e:
            st.error(f"Performance tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

    with tab3:
        try:
            tab_advanced_strategies(
                _gate_data(get_data(), st.session_state.get("cutoff_utc_hour")),
                parlays_callback=tab_parlays,
            )
        except Exception as _e:
            st.error(f"Advanced strategies tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

    with tab4:
        try:
            tab_jig(get_data())
        except Exception as _e:
            st.error(f"JIG tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

    with tab5:
        try:
            tab_hits(_gate_data(get_data(), st.session_state.get("cutoff_utc_hour")))
        except Exception as _e:
            st.error(f"Hits tab error: {_e}")
            if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())


if __name__ == "__main__":
    try:
        main()
    except Exception as _top_e:
        st.error(f"App crash: {_top_e}")
        if __import__("os").getenv("DEBUG") == "true":
                    st.code(_tb.format_exc())

