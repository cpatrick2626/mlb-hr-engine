import itertools
import streamlit as st

# ── Module-level helpers (moved here so cached functions below are stable) ──

def _ato_d(american) -> float:
    american = int(american)
    if not american:
        return 1.01
    if american >= 100:
        return (american / 100.0) + 1
    return (100.0 / abs(american)) + 1


def _dta(decimal: float) -> int:
    if decimal >= 2.0:
        return int((decimal - 1) * 100)
    return int(-100 / (decimal - 1))


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


# ── Module-level cached computations ────────────────────────────────────────
# IMPORTANT: These MUST be at module level. Defining @st.cache_data functions
# inside another function re-registers them on every call, causing cache misses
# every render. Moving them here makes the function object stable across reruns.

@st.cache_data(ttl=120, show_spinner=False)
def _cached_strategy_perf(mtime: float):
    try:
        from tracking import strategy_log as _sl
        return _sl.summary(), _sl.all_picks()
    except Exception:
        return [], []


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_corr_parlays(player_ids: tuple, _all_players: list):
    try:
        from strategies import find_correlated_parlays
    except ImportError:
        return []
    return find_correlated_parlays(
        players=_all_players,
        max_legs=3,
        min_correlation=0.15,
        min_individual_prob=0.08,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_power_parlays(player_ids: tuple, _all_players: list):
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
        return (
            min(brl / 18.0, 1.0) * 0.40 +
            max(0.0, (ev - 85.0) / 15.0) * 0.30 +
            max(0.0, (50.0 - gb) / 30.0) * 0.20 +
            max(0.0, (pf - 1.0) / 0.5) * 0.10
        )

    candidates = [p for p in _all_players if p.get("model_prob", 0) >= 0.08 and p.get("best_american")]
    if not candidates:
        return []
    scored = sorted(candidates, key=_power_score, reverse=True)[:20]
    parlays = []
    for n_legs in (2, 3):
        pool = scored if n_legs == 2 else scored[:12]
        for combo in itertools.combinations(pool, n_legs):
            base_prob = parlay_odds = 1.0
            for p in combo:
                base_prob *= p.get("model_prob", 0)
                parlay_odds *= _ato_d(p["best_american"])
            ev = (parlay_odds * base_prob) - 1
            if ev > 0:
                parlays.append({
                    "legs":         [p["player_name"] for p in combo],
                    "teams":        [p.get("team", "") for p in combo],
                    "power_scores": [round(_power_score(p), 3) for p in combo],
                    "barrel_pcts":  [_to_float(p.get("barrel_pct") or p.get("brl_pct")) for p in combo],
                    "exit_velos":   [_to_float(p.get("exit_velo")) for p in combo],
                    "base_prob":    base_prob,
                    "parlay_odds":  parlay_odds,
                    "american_odds": _dta(parlay_odds),
                    "ev_pct":       ev * 100,
                    "n_legs":       n_legs,
                })
    return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_park_parlays(player_ids: tuple, _all_players: list):
    from collections import defaultdict
    park_players = sorted(
        [p for p in _all_players
         if p.get("park_factor", 1.0) >= 1.08
         and p.get("model_prob", 0) >= 0.07
         and p.get("best_american")],
        key=lambda p: p.get("park_factor", 1.0) * p.get("model_prob", 0),
        reverse=True,
    )[:25]
    parlays = []
    for n_legs in (2, 3):
        pool = park_players if n_legs == 2 else park_players[:15]
        for combo in itertools.combinations(pool, n_legs):
            base_prob = parlay_odds = 1.0
            avg_park = sum(p.get("park_factor", 1.0) for p in combo) / len(combo)
            for p in combo:
                base_prob *= p.get("model_prob", 0)
                parlay_odds *= _ato_d(p["best_american"])
            park_boost = 1.0 + (avg_park - 1.0) * 0.5
            adj_prob = min(base_prob * park_boost, 0.25)
            ev = (parlay_odds * adj_prob) - 1
            if ev > 0:
                parlays.append({
                    "legs":         [p["player_name"] for p in combo],
                    "teams":        [p.get("team", "") for p in combo],
                    "park_factors": [round(p.get("park_factor", 1.0), 3) for p in combo],
                    "avg_park":     round(avg_park, 3),
                    "park_boost":   round(park_boost, 3),
                    "base_prob":    base_prob,
                    "adj_prob":     adj_prob,
                    "parlay_odds":  parlay_odds,
                    "american_odds": _dta(parlay_odds),
                    "ev_pct":       ev * 100,
                    "n_legs":       n_legs,
                })
    return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_pitcher_targets(player_ids: tuple, _all_players: list):
    from collections import defaultdict
    by_pitcher = defaultdict(list)
    for p in _all_players:
        if p.get("model_prob", 0) < 0.07 or not p.get("best_american"):
            continue
        pid_name = p.get("pitcher_name", "TBD")
        if pid_name and pid_name != "TBD":
            by_pitcher[pid_name].append(p)
    parlays = []
    for pitcher_name, hitters in by_pitcher.items():
        if len(hitters) < 2:
            continue
        avg_pit_fac = sum(h.get("pitcher_factor", 1.0) for h in hitters) / len(hitters)
        avg_pit_hr9 = sum(h.get("pitcher_hr9", 0.0) for h in hitters) / len(hitters)
        if avg_pit_fac < 1.05 and avg_pit_hr9 < 1.2:
            continue
        hitters_sorted = sorted(hitters, key=lambda h: h.get("model_prob", 0), reverse=True)
        for n_legs in (2, 3):
            pool = hitters_sorted[:min(n_legs + 3, len(hitters_sorted))]
            for combo in itertools.combinations(pool, n_legs):
                base_prob = parlay_odds = 1.0
                for h in combo:
                    base_prob *= h.get("model_prob", 0)
                    parlay_odds *= _ato_d(h["best_american"])
                corr_boost = 1.0 + 0.08 * (n_legs - 1)
                adj_prob = min(base_prob * corr_boost, 0.30)
                ev = (parlay_odds * adj_prob) - 1
                if ev > 0:
                    parlays.append({
                        "pitcher_name":  pitcher_name,
                        "pitcher_factor": round(avg_pit_fac, 3),
                        "pitcher_hr9":    round(avg_pit_hr9, 2),
                        "legs":           [h["player_name"] for h in combo],
                        "teams":          [h.get("team", "") for h in combo],
                        "model_probs":    [round(h.get("model_prob", 0) * 100, 1) for h in combo],
                        "odds_each":      [h["best_american"] for h in combo],
                        "corr_boost":     corr_boost,
                        "base_prob":      base_prob,
                        "adj_prob":       adj_prob,
                        "parlay_odds":    parlay_odds,
                        "american_odds":  _dta(parlay_odds),
                        "ev_pct":         ev * 100,
                        "n_legs":         n_legs,
                    })
    return _diverse_top(sorted(parlays, key=lambda x: x["ev_pct"], reverse=True))


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_stars_aligned(player_ids: tuple, _all_players: list):
    def _alignment_score(p) -> float:
        park   = p.get("park_factor",    1.0)
        pit    = p.get("pitcher_factor", 1.0)
        wx     = p.get("weather_factor", 1.0)
        plat   = p.get("platoon_factor", 1.0)
        streak = p.get("streak_factor",  1.0)
        raw = park * pit * wx * plat * streak
        penalty = sum(max(0.0, 1.0 - f) for f in [park, pit, wx, plat, streak])
        return raw - penalty * 0.5

    candidates = sorted(
        [p for p in _all_players
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
            base_prob = parlay_odds = 1.0
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


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_multi_edge(player_ids: tuple, _all_players: list):
    _THRESHOLDS = {
        "park":    ("park_factor",    1.05),
        "pitcher": ("pitcher_factor", 1.05),
        "platoon": ("platoon_factor", 1.05),
        "weather": ("weather_factor", 1.04),
        "streak":  ("streak_factor",  1.03),
    }
    candidates = []
    for p in _all_players:
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
            "_confirmed":    confirmed,
            "_edge_count":   len(confirmed),
            "_edge_product": round(edge_product, 4),
        })
    return sorted(candidates, key=lambda x: (x["_edge_count"], x["_edge_product"]), reverse=True)[:15]


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
        import os as _os

        _sl_mtime = _os.path.getmtime(_sl.LOG_PATH) if _sl.LOG_PATH.exists() else 0.0
        _perf_data, _all_picks = _cached_strategy_perf(_sl_mtime)
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
                    try:
                        _pk_conf = float(_pk.get("confidence", 0) or 0)
                    except (TypeError, ValueError):
                        _pk_conf = 0.0
                    _pk_tier = ("🌟 S" if _pk_conf >= 70 else "✅ A" if _pk_conf >= 55
                                else "🟡 B" if _pk_conf >= 40 else "🔴 C") if _pk_conf > 0 else ""
                    _pick_rows.append({
                        "Tier":       _pk_tier,
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
            "Stars Aligned",
            "Multi-Edge Confirmation",
            "Player Edge Rankings",
            "Confidence Rankings",
            "Power Profile Parlays",
            "Pitcher Target Parlays",
            "Park Monster Parlays",
            "Correlation Parlays",
        ],
        help="Choose an advanced betting strategy to analyze"
    )

    try:
        from strategies import (
            find_correlated_parlays,
        )

        all_players = sorted(
            data.get("all_players", []),
            key=lambda p: (
                {"S": 0, "A": 1, "B": 2, "C": 3}.get(p.get("confidence_tier", "C"), 3),
                -p.get("score", 0),
            ),
        )
        ranked = data.get("ranked", [])

        # Build lookup for modal triggers — set session_state["show_modal"]; fired by main()
        _player_map = {p["player_name"]: p for p in all_players if p.get("player_name")}

        _MLB_PHOTO_TPL = (
            "https://img.mlbstatic.com/mlb-photos/image/upload"
            "/d_people:generic:headshot:67:current.png"
            "/w_96,q_auto:best/v1/people/{pid}/headshot/67/current"
        )

        def _player_row(player_name: str, team: str, meta: str, modal_key: str):
            """Render a player as a clickable button (opens modal) + stats caption + FD link."""
            _pdata = _player_map.get(player_name, {})
            _mdl   = _pdata.get("model_prob", 0) * 100
            _ev    = _pdata.get("ev_pct", 0)
            _edge  = _pdata.get("edge_pct", 0)
            _tier  = _pdata.get("confidence_tier", "")
            _pit   = _pdata.get("pitcher_name", "")
            _pit_f = _pdata.get("pitcher_factor", 1.0)
            _plat  = _pdata.get("platoon_factor", 1.0)
            _pit_hand = _pdata.get("pitcher_hand", "")
            _pit_hand_s = f" ({'RHP' if _pit_hand=='R' else 'LHP' if _pit_hand=='L' else ''})" if _pit_hand else ""
            _tier_col = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_tier, "#888")
            _ev_col   = "#4ade80" if _ev >= 0 else "#f87171"
            _pid      = _pdata.get("player_id", "")
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
                _stats_html = ""
                if _pid:
                    _photo_url = _MLB_PHOTO_TPL.format(pid=_pid)
                    _stats_html += (
                        f"<img src='{_photo_url}' style='width:32px;height:32px;"
                        f"border-radius:50%;object-fit:cover;object-position:top center;"
                        f"vertical-align:middle;margin-right:6px;' "
                        f"onerror=\"this.style.display='none'\"/>"
                    )
                if _mdl > 0:
                    _stats_html += f"<span style='color:#a78bfa;'>MDL {_mdl:.0f}%</span>  ·  "
                if _ev != 0 or _edge != 0:
                    _stats_html += (
                        f"<span style='color:{_ev_col};'>EV {_ev:+.1f}%</span>  ·  "
                        f"<span style='color:#60a5fa;'>Edge {_edge:+.1f}%</span>  ·  "
                    )
                if _tier:
                    _stats_html += f"<span style='color:{_tier_col};font-weight:700;'>{_tier}-Tier</span>"
                if _pit:
                    _stats_html += (
                        f"  ·  <span style='color:#94a3b8;font-size:10px;'>vs "
                        f"{'🟢' if _pit_f > 1.08 else '🟡' if _pit_f > 0.97 else '🔴'} "
                        f"{_pit}{_pit_hand_s}</span>"
                    )
                _base_meta = f"{'  ·  '.join(_parts)}" if _parts else ""
                if _base_meta or _stats_html:
                    st.markdown(
                        f"<div style='font-size:11px; color:#888888; margin:-6px 0 4px 8px; "
                        f"display:flex; align-items:center; flex-wrap:wrap; gap:4px;'>"
                        + (_base_meta + ("  ·  " if _base_meta and _stats_html else "") if _base_meta else "")
                        + _stats_html
                        + f"</div>",
                        unsafe_allow_html=True,
                    )
            with _rc2:
                st.link_button("FD →", _fd_url(player_name), use_container_width=True)

        if strategy_type == "Correlation Parlays":
            st.markdown("### 🔗 Correlation-Based Parlays")
            st.info("Same-team players facing the same pitcher — correlation bonus applied to EV")

            _cache_key = tuple(p.get("player_name", "") for p in all_players)
            corr_parlays = _diverse_top(_cached_corr_parlays(_cache_key, all_players))

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

        elif strategy_type == "Power Profile Parlays":
            st.markdown("### ⚡ Power Profile Parlays")
            st.info("Players with elite barrel%, high exit velocity, and low GB% — pure power metrics vs weak pitchers")

            _pp_key = tuple(p.get("player_name", "") for p in all_players)
            power_parlays = _cached_power_parlays(_pp_key, all_players)

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

        elif strategy_type == "Park Monster Parlays":
            st.markdown("### 🏟️ Park Monster Parlays")
            st.info("Players in the most hitter-friendly parks — Coors, Great American, Fenway, etc. — where the ball flies")

            _park_key = tuple(p.get("player_name", "") for p in all_players)
            park_parlays = _cached_park_parlays(_park_key, all_players)

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

            _pt_key = tuple(p.get("player_name", "") for p in all_players)
            pt_parlays = _cached_pitcher_targets(_pt_key, all_players)

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

        elif strategy_type == "Stars Aligned":
            st.markdown("### ⭐ Stars Aligned")
            st.info(
                "Players where every game-day factor is working in their favor: "
                "hitter-friendly park, HR-prone pitcher, favorable weather, and a platoon edge. "
                "These are the 'everything is right today' plays — rare but highest-conviction."
            )

            _sa_key = tuple(p.get("player_name", "") for p in all_players)
            sa_parlays = _cached_stars_aligned(_sa_key, all_players)

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

        elif strategy_type == "Player Edge Rankings":
            st.markdown("### 📊 Player Edge Rankings")
            st.info(
                "Today's qualified picks ranked from highest Edge% to lowest. "
                "Edge% = model probability − market no-vig probability. "
                "The larger the gap, the stronger the model's conviction vs. the market price."
            )

            # Sort qualified picks by edge descending
            edge_ranked = sorted(
                ranked,
                key=lambda p: float(p.get("edge_pct") or 0),
                reverse=True,
            )

            if not edge_ranked:
                st.warning("No qualified picks today. Load data from the Picks tab first.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())
            else:
                _er_min = st.slider(
                    "Min Edge%", -20.0, 20.0, 0.0, 0.5, key="er_min_edge",
                    help="Filter to only show picks with at least this much edge"
                )
                _er_filtered = [p for p in edge_ranked if float(p.get("edge_pct") or 0) >= _er_min]

                st.caption(
                    f"{len(edge_ranked)} qualified picks · "
                    f"{len(_er_filtered)} shown · sorted highest Edge% → lowest"
                )

                if not _er_filtered:
                    st.warning(f"No qualified picks with Edge ≥ {_er_min:.1f}%.")
                else:
                    for i, p in enumerate(_er_filtered, 1):
                        _er_name  = p.get("player_name", "")
                        _er_team  = p.get("team", "")
                        _er_pit   = p.get("pitcher_name", "TBD")
                        _er_edge  = float(p.get("edge_pct") or 0)
                        _er_ev    = float(p.get("ev_pct") or 0)
                        _er_model = float(p.get("model_prob") or 0) * 100
                        _er_mkt   = float(p.get("market_no_vig_prob") or 0) * 100
                        _er_odds  = p.get("best_american")
                        _er_conf  = float(p.get("confidence") or 0)
                        _er_tier  = p.get("confidence_tier", "C")

                        if _er_edge >= 10:  _er_ec = "#4ade80"
                        elif _er_edge >= 5: _er_ec = "#86efac"
                        elif _er_edge >= 2: _er_ec = "#f0f0f0"
                        else:               _er_ec = "#f87171"

                        _er_tier_col = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_er_tier, "#888")
                        _er_label = (
                            f"#{i}  {_er_name}  ({_er_team})"
                            f"  |  Edge {_er_edge:+.1f}%"
                            f"  |  EV {_er_ev:+.1f}%"
                            f"  |  Model {_er_model:.1f}%"
                            f"  |  Tier {_er_tier}"
                        )

                        with st.expander(_er_label):
                            _ec1, _ec2, _ec3, _ec4 = st.columns(4)
                            with _ec1:
                                st.metric("Edge%", f"{_er_edge:+.1f}%")
                            with _ec2:
                                st.metric("EV%", f"{_er_ev:+.1f}%")
                            with _ec3:
                                st.metric("Model%", f"{_er_model:.1f}%")
                            with _ec4:
                                st.metric("Market%", f"{_er_mkt:.1f}%" if _er_mkt else "--")

                            _ec5, _ec6, _ec7 = st.columns(3)
                            with _ec5:
                                st.metric("Best Odds", _fmt_american(_er_odds))
                            with _ec6:
                                st.metric("Confidence", f"{_er_conf:.0f}")
                            with _ec7:
                                st.metric("Tier", _er_tier)

                            _player_row(
                                _er_name, _er_team,
                                f"Edge {_er_edge:+.1f}% · EV {_er_ev:+.1f}% · Conf {_er_conf:.0f} · {_er_pit}",
                                f"modal_er_{i}",
                            )
                            if st.button("📲 Add to FD Slip", key=f"fd_er_{i}"):
                                n = _add_to_fd_slip([_er_name], all_players)
                                if not n:
                                    st.info("Already in slip.")

        elif strategy_type == "Confidence Rankings":
            st.markdown("### 🎯 Confidence Rankings")
            st.info(
                "Today's qualified picks ranked from highest Confidence to lowest. "
                "Confidence (0–100) reflects sample size, Statcast data quality, "
                "model/market agreement, barrel rate, and pitcher HR/9. "
                "High-confidence picks are ones the model is most certain about — "
                "regardless of how big the edge or EV is."
            )

            _TIER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3}
            conf_ranked = sorted(
                ranked,
                key=lambda p: (
                    float(p.get("confidence") or 0),
                    -_TIER_ORDER.get(p.get("confidence_tier", "C"), 3),
                    float(p.get("edge_pct") or 0),
                ),
                reverse=True,
            )

            if not conf_ranked:
                st.warning("No qualified picks today. Load data from the Picks tab first.")
                st.link_button("📲 Browse FanDuel HR Props", _fd_url())
            else:
                _cr_min = st.slider(
                    "Min Confidence", 0, 100, 40, 5, key="cr_min_conf",
                    help="Filter to picks with at least this confidence score"
                )
                _cr_filtered = [p for p in conf_ranked if float(p.get("confidence") or 0) >= _cr_min]

                st.caption(
                    f"{len(conf_ranked)} qualified picks · "
                    f"{len(_cr_filtered)} shown · sorted highest Confidence → lowest"
                )

                if not _cr_filtered:
                    st.warning(f"No qualified picks with Confidence ≥ {_cr_min}.")
                else:
                    for i, p in enumerate(_cr_filtered, 1):
                        _cr_name  = p.get("player_name", "")
                        _cr_team  = p.get("team", "")
                        _cr_pit   = p.get("pitcher_name", "TBD")
                        _cr_conf  = float(p.get("confidence") or 0)
                        _cr_edge  = float(p.get("edge_pct") or 0)
                        _cr_ev    = float(p.get("ev_pct") or 0)
                        _cr_model = float(p.get("model_prob") or 0) * 100
                        _cr_mkt   = float(p.get("market_no_vig_prob") or 0) * 100
                        _cr_odds  = p.get("best_american")
                        _cr_tier  = p.get("confidence_tier", "C")

                        # Confidence color scale
                        if _cr_conf >= 70:   _cr_cc = "#4ade80"
                        elif _cr_conf >= 55: _cr_cc = "#86efac"
                        elif _cr_conf >= 40: _cr_cc = "#facc15"
                        else:                _cr_cc = "#f87171"

                        _cr_tier_col = {"S": "#FFD700", "A": "#4ade80", "B": "#facc15", "C": "#f87171"}.get(_cr_tier, "#888")
                        _cr_label = (
                            f"#{i}  {_cr_name}  ({_cr_team})"
                            f"  |  Conf {_cr_conf:.0f}"
                            f"  |  Tier {_cr_tier}"
                            f"  |  Edge {_cr_edge:+.1f}%"
                            f"  |  EV {_cr_ev:+.1f}%"
                        )

                        with st.expander(_cr_label):
                            # Prominent confidence badge
                            _cr_bar = min(100, max(0, int(_cr_conf)))
                            st.markdown(
                                f"<div style='background:#0f172a;border:1px solid #1e293b;"
                                f"border-radius:8px;padding:10px 14px;margin-bottom:8px;'>"
                                f"<div style='display:flex;justify-content:space-between;"
                                f"align-items:center;margin-bottom:6px;'>"
                                f"<span style='font-size:12px;color:#94a3b8;'>Confidence Score</span>"
                                f"<span style='font-size:26px;font-weight:900;color:{_cr_cc};'>"
                                f"{_cr_conf:.0f}</span>"
                                f"<span style='font-size:13px;font-weight:700;color:{_cr_tier_col};'>"
                                f"Tier {_cr_tier}</span></div>"
                                f"<div style='background:#1e293b;border-radius:3px;height:6px;'>"
                                f"<div style='background:{_cr_cc};width:{_cr_bar}%;height:6px;"
                                f"border-radius:3px;'></div></div>"
                                f"<div style='font-size:9px;color:#374151;margin-top:2px;'>"
                                f"0 ──────────────── 50 ──────────────── 100</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                            _cc1, _cc2, _cc3, _cc4 = st.columns(4)
                            with _cc1:
                                st.metric("Edge%", f"{_cr_edge:+.1f}%")
                            with _cc2:
                                st.metric("EV%", f"{_cr_ev:+.1f}%")
                            with _cc3:
                                st.metric("Model%", f"{_cr_model:.1f}%")
                            with _cc4:
                                st.metric("Market%", f"{_cr_mkt:.1f}%" if _cr_mkt else "--")

                            _cc5, _cc6 = st.columns(2)
                            with _cc5:
                                st.metric("Best Odds", _fmt_american(_cr_odds))
                            with _cc6:
                                st.metric("vs Pitcher", _cr_pit)

                            _player_row(
                                _cr_name, _cr_team,
                                f"Conf {_cr_conf:.0f} · Tier {_cr_tier} · Edge {_cr_edge:+.1f}% · EV {_cr_ev:+.1f}% · {_cr_pit}",
                                f"modal_cr_{i}",
                            )
                            if st.button("📲 Add to FD Slip", key=f"fd_cr_{i}"):
                                n = _add_to_fd_slip([_cr_name], all_players)
                                if not n:
                                    st.info("Already in slip.")

        elif strategy_type == "Multi-Edge Confirmation":
            st.markdown("### 🔬 Multi-Edge Confirmation")
            st.info(
                "Players simultaneously clearing 3 or more independent edge criteria: "
                "park factor ≥1.05, pitcher factor ≥1.05, platoon factor ≥1.05, "
                "weather factor ≥1.04, streak factor ≥1.03. "
                "Each confirmed edge is independent — stacking them materially increases conviction."
            )

            _me_key = tuple(p.get("player_name", "") for p in all_players)
            me_players = _cached_multi_edge(_me_key, all_players)

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

    except ImportError as e:
        st.error("Advanced strategies module not found. Strategies are being developed.")
        st.code(str(e))
    except Exception as e:
        st.error(f"Error in advanced strategies: {e}")
        st.code(_tb.format_exc())
