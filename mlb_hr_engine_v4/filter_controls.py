"""
filter_controls.py — Production-grade filter control helpers for Main, JIG, and future engines.

Controls use st.number_input (native +/- buttons, direct keyboard entry, precision stepping).
Widget keys are identical to existing slider keys — session_state values transfer directly.
Preset system allows engine-specific default tactical profiles.
"""
import streamlit as st


# ── Engine Default Presets ────────────────────────────────────────────────────

MAIN_PRESETS: dict = {
    "operational": {
        "label": "Operational",
        "color": "#4ade80",
        "help": "Default: no batter-profile floor — sidebar EV/Edge gates qualify picks",
        "values": {
            "tac_min_barrel": 0.0,
            "tac_min_hh": 0.0,
            "tac_min_xslg": 0.0,
            "tac_min_iso": 0.0,
            "tac_min_pull_air": 0.0,
            "tac_min_hr_window": 0.0,
            "tac_min_ev": 0.0,
            "tac_min_edge": 0.0,
            "tac_min_conf": 0.0,
            "tac_min_model_prob": 0.0,
        },
    },
    "selective": {
        "label": "Selective",
        "color": "#60a5fa",
        "help": "Barrel ≥ 5%, Hard Hit ≥ 35% — restricts to power-contact profile batters",
        "values": {
            "tac_min_barrel": 5.0,
            "tac_min_hh": 35.0,
            "tac_min_xslg": 0.0,
            "tac_min_iso": 0.0,
            "tac_min_pull_air": 0.0,
            "tac_min_hr_window": 0.0,
            "tac_min_ev": 0.0,
            "tac_min_edge": 0.0,
            "tac_min_conf": 0.0,
            "tac_min_model_prob": 0.0,
        },
    },
    "elite": {
        "label": "Elite Only",
        "color": "#FFD700",
        "help": "Barrel ≥ 8%, Hard Hit ≥ 40%, EV ≥ 2%, Edge ≥ 1.5%",
        "values": {
            "tac_min_barrel": 8.0,
            "tac_min_hh": 40.0,
            "tac_min_xslg": 0.0,
            "tac_min_iso": 0.0,
            "tac_min_pull_air": 0.0,
            "tac_min_hr_window": 0.0,
            "tac_min_ev": 2.0,
            "tac_min_edge": 1.5,
            "tac_min_conf": 0.0,
            "tac_min_model_prob": 0.0,
        },
    },
}

JIG_PRESETS: dict = {
    "all_tactical": {
        "label": "All Tactical",
        "color": "#4ade80",
        "help": "Default: full JIG universe — broad matchup exploration, no profile gate",
        "values": {
            "jig_tac_min_barrel": 0.0,
            "jig_tac_min_hh": 0.0,
            "jig_tac_min_xslg": 0.0,
            "jig_tac_min_iso": 0.0,
            "jig_tac_min_pull_air": 0.0,
            "jig_tac_min_hr_window": 0.0,
            "jig_tac_min_matchup_pct": 75,
            "jig_tac_min_hvy_score": 0,
        },
    },
    "selective": {
        "label": "Selective",
        "color": "#60a5fa",
        "help": "Barrel ≥ 5%, neutral matchup or better (modifier ≥ 100%)",
        "values": {
            "jig_tac_min_barrel": 5.0,
            "jig_tac_min_hh": 35.0,
            "jig_tac_min_xslg": 0.0,
            "jig_tac_min_iso": 0.0,
            "jig_tac_min_pull_air": 0.0,
            "jig_tac_min_hr_window": 0.0,
            "jig_tac_min_matchup_pct": 100,
            "jig_tac_min_hvy_score": 0,
        },
    },
    "matchup_plus": {
        "label": "Matchup+",
        "color": "#f97316",
        "help": "Elite matchup: modifier ≥ 110%, HVY score ≥ 40, Barrel ≥ 6%",
        "values": {
            "jig_tac_min_barrel": 6.0,
            "jig_tac_min_hh": 38.0,
            "jig_tac_min_xslg": 0.0,
            "jig_tac_min_iso": 0.0,
            "jig_tac_min_pull_air": 0.0,
            "jig_tac_min_hr_window": 0.0,
            "jig_tac_min_matchup_pct": 110,
            "jig_tac_min_hvy_score": 40,
        },
    },
}


# ── Control Renderer ──────────────────────────────────────────────────────────

def render_filter_control(
    label: str,
    key: str,
    min_val,
    max_val,
    default,
    step,
    fmt: str = "%.1f",
    help_text: str = "",
):
    """
    Production-grade filter control using st.number_input.
    Provides native +/- step buttons and direct keyboard entry.
    Keys match existing slider keys — session_state compatible.

    For integer controls: pass int min_val/max_val/step.
    For float controls: pass float min_val/max_val/step.
    """
    current = st.session_state.get(key, default)
    if isinstance(step, int) and isinstance(min_val, int) and isinstance(max_val, int):
        try:
            current = int(current or default)
        except (TypeError, ValueError):
            current = int(default)
    else:
        try:
            current = float(current)
        except (TypeError, ValueError):
            current = float(default)
    return st.number_input(
        label,
        min_value=min_val,
        max_value=max_val,
        value=current,
        step=step,
        format=fmt,
        key=key,
        help=help_text,
    )


# ── Preset Bar ────────────────────────────────────────────────────────────────

def render_preset_bar(preset_key_ss: str, presets: dict, reset_cb=None) -> None:
    """
    Render a row of one-click preset buttons with an optional Reset button.

    preset_key_ss: session_state key tracking which preset is active (for highlighting).
    presets: dict of {preset_id: {label, color, help, values}}.
    reset_cb: callable to invoke when Reset is clicked (typically sets all keys to 0).
    """
    active = st.session_state.get(preset_key_ss, "")
    n_cols = len(presets) + (1 if reset_cb else 0)
    cols = st.columns(n_cols)
    for i, (pk, pdef) in enumerate(presets.items()):
        with cols[i]:
            color = pdef.get("color", "#888")
            is_active = pk == active
            btn_style = (
                f"background:{'#0a1a0a' if is_active else 'transparent'};"
                f"border:1px solid {color if is_active else '#333'};"
                f"color:{color};padding:2px 8px;border-radius:3px;"
                f"font-size:11px;font-weight:{'700' if is_active else '400'};"
            )
            # Use Streamlit button — active state tracked via session_state
            if st.button(
                pdef["label"],
                key=f"_preset_{preset_key_ss}_{pk}",
                help=pdef.get("help", ""),
                use_container_width=True,
            ):
                for k, v in pdef["values"].items():
                    st.session_state[k] = v
                st.session_state[preset_key_ss] = pk
                st.rerun()
    if reset_cb is not None:
        with cols[-1]:
            if st.button("↺ Reset", key=f"_preset_reset_{preset_key_ss}", use_container_width=True):
                reset_cb()
