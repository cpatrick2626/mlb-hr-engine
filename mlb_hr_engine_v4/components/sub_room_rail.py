"""Sub-room rail — Phase 3 shell navigation.

Horizontal button strip for MAIN and JIG sub-room navigation.
STRATEGY / HITS / PERFORMANCE: early return, no height reserved.
State: nav_state.set_active_sub_room via Streamlit-owned st.button clicks.
"""
from __future__ import annotations

import streamlit as st
import nav_state as _navstate


def render_sub_room_rail() -> None:
    """Render sub-room rail above the banner.

    No-op for sections without sub-rooms (STRATEGY / HITS / PERFORMANCE).
    """
    active_section = _navstate.get_active_section(st.session_state)
    sub_rooms = _navstate.sub_rooms_for_section(active_section)

    if not sub_rooms:
        return

    active_sub = _navstate.get_active_sub_room(st.session_state)
    cols = st.columns(len(sub_rooms))

    for i, sub in enumerate(sub_rooms):
        with cols[i]:
            if st.button(
                sub,
                key=f"_srail_{active_section}_{i}",
                type="primary" if sub == active_sub else "secondary",
                use_container_width=True,
            ):
                _navstate.set_active_sub_room(st.session_state, sub)
