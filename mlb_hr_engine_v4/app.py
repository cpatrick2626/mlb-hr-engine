"""
Codex HR Engine — Streamlit Dashboard
"""

import sys
import traceback as _tb
import urllib.parse
from pathlib import Path

import streamlit as st
import pandas as pd

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

sys.path.insert(0, str(Path(__file__).parent))

import config
from engine.market import american_to_decimal, decimal_to_american
from engine.ev import expected_value_pct
from output.parlay import _evaluate_parlay, parlay_bet_size
from output.ranker import rank_picks as _rank_picks
from tracking import pnl as pnl_tracker, clv as clv_tracker

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
    color: #777777 !important; font-size: 10px !important;
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


# ── Data loading ──────────────────────────────────────────────────────────────
def get_data():
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
                st.session_state["data"]      = data
                st.session_state["cache_key"] = target_date
                _status.update(
                    label=(f"✅ Loaded — {data['stats'].get('players', 0)} players, "
                           f"{data['stats'].get('qualified', 0)} qualified"),
                    state="complete", expanded=False,
                )

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
                _status.update(label="❌ Load failed — see error below", state="error")
                st.error(f"Failed to load game data: {e}")
                st.code(_tb.format_exc())
                st.session_state["data"] = {
                    "ranked": [], "qualified": [], "date": target_date, "stats": {},
                    "odds_source": "error", "batter_data": {},
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
        if raw < 36:  return _DARK_GREEN
        if raw < 44:  return _GREEN
        if raw < 50:  return _RED
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


def _add_legs_to_fd_slip(legs: list[dict]) -> int:
    """Merge parlay legs into the FanDuel slip. Returns count of newly added players."""
    current = list(st.session_state.get("fd_slip", []))
    added = 0
    for p in legs:
        odds = p.get("fanduel_american") or p.get("best_american")
        label = f"{p['player_name']} ({p.get('team', '')}) {_fmt_american(odds)}"
        if label not in current:
            current.append(label)
            added += 1
    st.session_state["fd_slip"] = current
    st.session_state["fd_slip_select"] = current
    return added


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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TAB 1 — TODAY'S PICKS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def tab_picks(data: dict, min_ev: float, min_edge: float):
    all_players = data.get("all_players", [])
    ranked    = _apply_ui_filters(all_players, min_ev, min_edge)
    stats     = data.get("stats", {})
    source    = data.get("odds_source", "none")
    n_batters = len(data.get("batter_data", {}))
    scale     = _bankroll_scale()

    st.markdown('<div class="section-header">&#9889; TODAY\'S QUALIFIED PICKS</div>',
                unsafe_allow_html=True)

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
                "Model%":   _stat_badge("Model%", f"{model_p*100:.1f}%"),
                "Mkt%":     f"{p.get('market_no_vig_prob',0)*100:.1f}%",
                "Edge":     _stat_badge("Edge", f"{edge:+.1f}%"),
                "EV%":      _stat_badge("EV%", f"{ev:+.1f}%"),
                "Bet $":    f"${bet:.0f}",
                "Conf":     _stat_badge("Conf", f"{conf:.0f}"),
                "Brl%":     _stat_badge("Brl%", p.get("barrel_pct", "--")),
                "SwSp%":    _stat_badge("SwSp%", p.get("sweet_spot_pct", "--")),
                "EV mph":   _stat_badge("EV mph", p.get("exit_velo", "--")),
                "FB%":      _stat_badge("FB%", p.get("fb_pct", "--")),
                "GB%":      _stat_badge("GB%", p.get("gb_pct", "--")),
                "Pull%":    p.get("pull_pct", "--"),
                "Score":    f"{p.get('score',0):.1f}",
            })

        # â"€â"€ Range stats bar â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
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

        # â"€â"€ Legend â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
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
            width='stretch',
            hide_index=True,
            column_config={
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

    st.markdown(
        '<div class="section-header" title="'
        "Raw model output for every starting batter today, ranked by HR probability. "
        "No EV or market filter — this is pure model signal. "
        "Use it to find matchup targets before odds are posted, or to cross-check "
        "why a player did or didn't make the qualified picks list."
        '">'
        "All Players \u2014 Model Probabilities"
        "&nbsp;<span style='font-size:13px; opacity:0.45; cursor:help;'>&#9432;</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    all_by_model = data.get("all_by_model", [])
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

        def _extract(col, p, pit_fac, plat_fac):
            m = p.get
            if col == "Player":       return m("player_name", "")
            if col == "Team":         return m("team", "")
            if col == "Spot":         return _spot_label(m("lineup_spot"), plat_fac)
            if col == "Vs":           return _pitcher_label(m("pitcher_name", "TBD"), pit_fac, plat_fac)
            if col == "Model%":       return _stat_badge("Model%", f"{m('model_prob',0)*100:.1f}%")
            if col == "Brl%":         return _stat_badge("Brl%", m("barrel_pct", "--"))
            if col == "SwSp%":        return _stat_badge("SwSp%", m("sweet_spot_pct", "--"))
            if col == "FB%":          return _stat_badge("FB%", m("fb_pct", "--"))
            if col == "GB%":          return _stat_badge("GB%", m("gb_pct", "--"))
            if col == "LD%":          return m("ld_pct", "--")
            if col == "Pull%":        return m("pull_pct", "--")
            if col == "Oppo%":        return m("oppo_pct", "--")
            if col == "Hard Hit%":    return m("hard_hit", "--")
            if col == "Exit Velo":    return _stat_badge("Exit Velo", m("exit_velo", "--"))
            if col == "Launch Angle": return m("avg_launch_angle", "--")
            if col == "PwrMult":      return _stat_badge("PwrMult", f"{m('statcast_power_mult', 1):.2f}")
            if col == "Park":         return f"{m('park_factor', 1):.2f}"
            if col == "Pitcher":      return f"{m('pitcher_factor', 1):.2f}"
            if col == "Weather":      return f"{m('weather_factor', 1):.2f}"
            if col == "Platoon":      return f"{m('platoon_factor', 1):.2f}"
            if col == "Season PA":    return m("season_pa", "--")
            if col == "Season HR":    return m("season_hr", "--")
            if col == "Recent PA":    return m("recent_pa", "--")
            if col == "HR Rate":      return f"{m('hr_rate',0)*100:.2f}%"
            if col == "Streak":       return f"{m('streak_factor', 1):.2f}"
            if col == "K Factor":     return f"{m('k_factor', 1):.2f}"
            if col == "Pitcher HR/9": return f"{m('pitcher_hr9', 0):.2f}"
            if col == "Exp PA":       return f"{m('expected_pa', 3.8):.1f}"
            if col == "Odds":         return _fmt_american(m("best_american")) if m("best_american") else "--"
            if col == "Mkt%":         return f"{m('market_no_vig_prob',0)*100:.1f}%" if m("market_no_vig_prob") else "--"
            if col == "Edge%":        return f"{m('edge_pct',0):+.1f}%" if m("edge_pct") is not None else "--"
            if col == "EV%":          return f"{m('ev_pct',0):+.1f}%" if m("ev_pct") is not None else "--"
            if col == "Confidence":   return f"{m('confidence',0):.0f}" if m("confidence") is not None else "--"
            return "--"

        _COL_HELP = {
            "Model%":       "Poisson HR probability for today's game: P(HR≥1) = 1−e^(−λ). Accounts for batter power, park, pitcher, weather, and platoon.",
            "Brl%":         "Barrel rate (Statcast). Balls hit 98+ mph at 26-30° launch angle. League avg ~8%. Strong predictor of HR power.",
            "SwSp%":        "Sweet spot rate — balls hit at 8-32° launch angle. League avg ~34%. Higher = more balls in the HR window.",
            "FB%":          "Fly ball rate (% of batted balls). League avg ~36%. More fly balls = more HR opportunities.",
            "GB%":          "Ground ball rate. High GB% suppresses HR output — grounders don't leave the park. League avg ~44%.",
            "LD%":          "Line drive rate. League avg ~21%. Line drives don't go for HRs often but signal solid contact.",
            "Pull%":        "Pull rate. League avg ~40%. Pull hitters access the short porch and benefit more from wind.",
            "Oppo%":        "Opposite-field rate. Low pull%, high oppo% = contact hitter profile; harder to hit HRs to the deep part of the park.",
            "Hard Hit%":    "Hard-hit rate — balls hit 95+ mph exit velocity. League avg ~38%. Correlates with power output.",
            "Exit Velo":    "Average exit velocity (mph). League avg ~88 mph. 90+ is above average; 95+ is elite power territory.",
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
            "Pitcher HR/9": "Pitcher's HR allowed per 9 innings this season. League avg = 1.35. Above 1.5 = HR-prone; below 1.0 = HR suppressor.",
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
                "Brl%  ·  Barrel Rate — % of batted balls hit 98+ mph at 26-30° launch angle. "
                "League avg ~8%. Single strongest Statcast predictor of HR power. "
                "Effect: higher barrel% → larger power multiplier → higher model probability.",
            "SwSp%":
                "SwSp%  ·  Sweet Spot Rate — % of batted balls hit at 8-32° launch angle. "
                "League avg ~34%. More balls in this optimal window = more HR opportunities. "
                "Effect: contributes 10% weight to the Statcast power multiplier.",
            "FB%":
                "FB%  ·  Fly Ball Rate — % of batted balls that are fly balls. "
                "League avg ~36%. Only fly balls can leave the park. "
                "Effect: 15% weight in power multiplier; also scales how much park factor applies to this batter.",
            "GB%":
                "GB%  ·  Ground Ball Rate — % of batted balls that are grounders. "
                "League avg ~44%. Grounders almost never become HRs. "
                "Effect: high GB% suppresses the power multiplier and limits park factor benefit.",
            "LD%":
                "LD%  ·  Line Drive Rate — % of batted balls that are line drives. "
                "League avg ~21%. Signals solid contact quality but not HR trajectory. "
                "Effect: informational only — not directly used in the HR probability model.",
            "Pull%":
                "Pull%  ·  Pull Rate — % of batted balls pulled to the strong side. "
                "League avg ~40%. Pull hitters access the shorter porch and benefit more from wind. "
                "Effect: 8% weight in the power multiplier.",
            "Oppo%":
                "Oppo%  ·  Opposite-Field Rate — % of batted balls hit to the weak side. "
                "High oppo% signals a contact/gap hitter, not a HR profile. "
                "Effect: informational — model uses pull%, not oppo%, in the power multiplier.",
            "Hard Hit%":
                "Hard Hit%  ·  Hard-Hit Rate — % of batted balls hit 95+ mph exit velocity. "
                "League avg ~38%. Strong correlation with HR output and overall power. "
                "Effect: 10% weight in the Statcast power multiplier.",
            "Exit Velo":
                "Exit Velo  ·  Average Exit Velocity (mph) — how hard the batter hits the ball. "
                "League avg ~88 mph. 90+ = above average; 95+ = elite power hitter. "
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
                "League avg = 1.35. Above 1.5 = HR-prone target. Below 1.0 = strong HR suppressor. "
                "Effect: feeds into the pitcher HR factor; also triggers a +4pt confidence bonus if > 1.4.",
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
        default_visible = st.session_state.get(
            "model_visible_cols",
            ["Brl%", "SwSp%", "FB%", "GB%", "Pull%", "Exit Velo", "PwrMult", "Park", "Pitcher"],
        )
        with st.expander("⚙️ Customize columns", expanded=False):
            st.caption("Each option shows the full stat name, description, and how it affects the model. "
                       "Player · Team · Spot · Vs · Model% are always shown.")
            selected_toggle = st.multiselect(
                "Select columns to display:",
                options=_TOGGLE_COLS,
                default=default_visible,
                format_func=lambda c: _COL_FULL.get(c, c),
                key="model_col_picker",
            )
            st.session_state["model_visible_cols"] = selected_toggle

        visible_cols = _FIXED_COLS + selected_toggle

        def _model_rows(players):
            rows = []
            for p in players:
                pit_fac  = p.get("pitcher_factor", 1.0)
                plat_fac = p.get("platoon_factor", 1.0)
                rows.append({c: _extract(c, p, pit_fac, plat_fac) for c in visible_cols})
            return rows

        prime = [p for p in all_by_model if p.get("model_prob", 0) >= PRIME_FLOOR]
        watch = [p for p in all_by_model if p.get("model_prob", 0) < PRIME_FLOOR][:20]

        if prime:
            st.markdown(
                '<div style="margin:10px 0 4px 0;" '
                'title="'
                "PRIME TARGETS are players where the model computes a 15%+ HR probability for today's game. "
                "This means multiple factors are stacking in their favor: strong power metrics (barrel%, exit velo, FB%), "
                "a hitter-friendly park, a pitcher who gives up fly balls, and/or a favorable platoon split. "
                "These are the names to prioritize when shopping for HR prop lines. "
                "Not all will have listed odds — some may only appear in the WATCH LIST if the market hasn't priced them yet."
                '">'
                "<span style='font-size:14px; font-weight:800; color:#FFD700; letter-spacing:1.5px;'>"
                "&#11088; PRIME TARGETS</span>"
                "&nbsp;&nbsp;<span style='font-size:11px; color:#888; font-style:italic;'>"
                f"Model HR probability \u226515% \u00b7 {len(prime)} players \u00b7 hover for details"
                "</span></div>",
                unsafe_allow_html=True,
            )
            st.dataframe(
                pd.DataFrame(_model_rows(prime)),
                width='stretch', hide_index=True,
                column_config=_col_cfg,
            )

        if watch:
            st.markdown(
                '<div style="margin:14px 0 4px 0;" '
                'title="'
                "WATCH LIST players have a model HR probability below 15%. "
                "The model sees a plausible scenario — manageable pitcher, decent park, some power — "
                "but the profile is limited by a weak power metric (low barrel%, high GB%), a small sample size, "
                "or a neutral park suppressing the ceiling. "
                "Long-shot value plays often live here: the odds can be +1000 or better on a player "
                "the model gives 8-12%, which creates big EV if the market is sleeping on a matchup."
                '">'
                "<span style='font-size:14px; font-weight:800; color:#9E9E9E; letter-spacing:1.5px;'>"
                "&#128203; WATCH LIST</span>"
                "&nbsp;&nbsp;<span style='font-size:11px; color:#666; font-style:italic;'>"
                f"Model HR probability &lt;15% \u00b7 {len(watch)} players shown \u00b7 hover for details"
                "</span></div>",
                unsafe_allow_html=True,
            )
            st.dataframe(
                pd.DataFrame(_model_rows(watch)),
                width='stretch', hide_index=True,
                column_config=_col_cfg,
            )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TAB 2 — PARLAYS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
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
                        n = _add_legs_to_fd_slip(combo["legs"])
                        st.success(f"+{n} player{'s' if n != 1 else ''} added to FanDuel slip!")

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
                    n = _add_legs_to_fd_slip(legs_built)
                    st.success(f"+{n} player{'s' if n != 1 else ''} added to FanDuel slip!")
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

    st.markdown('<div class="section-header">📊 Running P&L</div>', unsafe_allow_html=True)
    try:
        summary = pnl_tracker.pnl_summary()
        clv     = clv_tracker.clv_summary()
    except Exception as e:
        st.error(f"Error loading performance data: {e}")
        return

    if summary:

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
        st.info("No results logged yet. Picks are auto-logged when Today's Picks tab loads.")

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

    st.markdown('<div class="section-header">📋 Picks Log</div>', unsafe_allow_html=True)
    try:
        rows = pnl_tracker.get_picks_log()
        if rows:
            st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
        else:
            st.caption("No picks logged yet — open Today's Picks tab to auto-log.")
    except Exception as e:
        st.error(f"Could not load picks log: {e}")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# MAIN
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def main():
    # Read filter thresholds from session state first (sidebar sets them on each rerun)
    _min_ev   = float(st.session_state.get("min_ev",   config.MIN_EV_PCT))
    _min_edge = float(st.session_state.get("min_edge", config.MIN_EDGE_PCT))

    # ── Banner ────────────────────────────────────────────────────────────────
    _banner = Path(__file__).parent / "assets" / "banner.png"
    if _banner.exists():
        st.image(str(_banner), use_container_width=True)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs([
        "📋  TODAY'S PICKS",
        "🎰  PARLAYS",
        "📊  PERFORMANCE",
    ])

    with tab1:
        try:
            data = get_data()
            tab_picks(data, _min_ev, _min_edge)
        except Exception as _e:
            st.error(f"Picks tab error: {_e}")
            st.code(_tb.format_exc())

    with tab2:
        try:
            data = get_data()
            tab_parlays(data)
        except Exception as _e:
            st.error(f"Parlays tab error: {_e}")
            st.code(_tb.format_exc())

    with tab3:
        try:
            tab_performance()
        except Exception as _e:
            st.error(f"Performance tab error: {_e}")
            st.code(_tb.format_exc())

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

        # ── FanDuel Slip ──────────────────────────────────────────────────────
        st.markdown("#### 🎰 FanDuel Slip")
        _slip_data = st.session_state.get("data")
        if _slip_data:
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
                for s in _selected:
                    p = _slip_map[s]
                    fd_odds   = p.get("fanduel_american")
                    best_odds = p.get("best_american")
                    odds_val  = fd_odds if fd_odds else best_odds
                    odds_lbl  = "FD" if fd_odds else "Best"
                    ev        = p.get("ev_pct", 0)
                    ev_color  = "#4ade80" if ev >= 0 else "#f87171"
                    url       = _fanduel_url(p["player_name"])
                    st.markdown(
                        f"<div style='background:#0a0a1a; border:1px solid #1a1a3a; "
                        f"border-radius:6px; padding:7px 10px; margin-bottom:5px; font-size:12px;'>"
                        f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                        f"<span><b style='color:#f0f0f0'>{p['player_name']}</b> "
                        f"<span style='color:#555; font-size:11px'>{p.get('team','')}</span></span>"
                        f"<a href='{url}' target='_blank' "
                        f"style='color:#4488ff; font-size:11px; background:#0d0d2a; "
                        f"padding:2px 8px; border-radius:4px; border:1px solid #1a2a66; "
                        f"text-decoration:none;'>Open FD →</a>"
                        f"</div>"
                        f"<div style='color:#888; margin-top:3px;'>"
                        f"{odds_lbl}: <b style='color:#FF6666'>{_fmt_american(odds_val)}</b>"
                        f" &nbsp;|&nbsp; EV: <b style='color:{ev_color}'>{ev:+.1f}%</b>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
                if st.button("📋 Log to Picks Tracker", width='stretch',
                             key="log_fd_slip"):
                    slip_players = [_slip_map[s] for s in _selected]
                    try:
                        n = pnl_tracker.log_slip_picks(slip_players)
                        if n:
                            st.success(f"Logged {n} pick{'s' if n != 1 else ''} to Performance tab!")
                        else:
                            st.info("All selected players already logged today.")
                    except Exception as e:
                        st.error(f"Log failed: {e}")
                st.link_button(
                    "📲 FanDuel HR Props", _fanduel_url(),
                    width='stretch', type="primary",
                )
                if st.button("🗑️ Clear Slip", width='stretch', key="clear_fd_slip"):
                    st.session_state["fd_slip"] = []
                    st.session_state.pop("fd_slip_select", None)
                    st.rerun()
            else:
                st.caption("Search above to add players to your slip.")
                st.link_button("📲 Browse FanDuel HR Props", _fanduel_url(), width='stretch')
        else:
            st.caption("Refresh data to build your slip.")
            st.link_button("📲 Browse FanDuel HR Props", _fanduel_url(), width='stretch')

        st.divider()

        if st.button("🔄 Force Refresh Data", width='stretch'):
            st.cache_data.clear()
            for k in ["data", "cache_key", "data_loaded_at"]:
                st.session_state.pop(k, None)
            st.rerun()

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

