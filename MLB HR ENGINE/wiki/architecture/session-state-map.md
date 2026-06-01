# Session State Map

## Summary

Streamlit's `session_state` is a protected surface in the MLB HR Engine. Each key has a defined owner (room or system component). Cross-room writes are prohibited. Routing and modal state are closed surfaces per `PHASE3_REFINEMENT_DOCTRINE.md`. This page tracks known ownership boundaries — Claude Code should populate this via repo audit before any session_state work.

## Key Points

### Ownership Rules
- Each room owns its session_state keys. A room may read shared/global keys but must not write to another room's keys.
- Routing keys (navigation state, current room) are owned by the routing layer — closed surface.
- Modal state keys are owned by the modal architecture — closed surface.
- Hydration keys (data freshness, load status) are owned by the hydration logic — closed surface.
- Cache keys are documented separately in [Cache Ownership Map](cache-ownership-map.md).

### Known Protected Key Groups
| Key Group | Owner | Status |
|-----------|-------|--------|
| Routing/navigation state | Routing architecture | CLOSED — no modification without authorization |
| Modal open/close state | Modal architecture | CLOSED — no modification without authorization |
| Hydration/load state | Hydration logic | CLOSED — no modification without authorization |
| Cache state | Cache ownership layer | CLOSED — see Cache Ownership Map |
| MAIN pick results | MAIN pipeline surface | Protected |
| JIG pick results | JIG pipeline surface | Protected |

**Note:** Full key inventory requires Claude Code audit of `app.py` and `pipeline.py`. This stub reflects known protected categories from doctrine.

## FD Slip Reference Keys

- `min_ev` and `min_edge` feed FD Slip at line `10365`
- Cannot remove without touching routing
- Default set to `0.0`
- Display-reference only

## Cross-References

- [Cache Ownership Map](cache-ownership-map.md)
- [Pipeline Data Flow](pipeline-data-flow.md)
- [Room Governance](../doctrine/room-governance.md)
- [MAIN/JIG Separation Rules](../doctrine/main-jig-separation.md)
