---
date: 2026-08-12
agent: Claude Code
task: Leg score snapshot at add time (TM/JIG, Signal, Edge, Confidence)
commit: d696a63
---

## Summary

`addLeg()` now snapshots five score fields onto the client-side leg object at the moment the leg is added. These values are frozen at add time and displayed in the pick card for the life of the session. New legs only — legs added before this commit show `"—"` for all five fields.

---

## Fields snapshotted

| Field | Source on row | Description |
|---|---|---|
| `true_matchup_score` | `row.true_matchup_score` | MAIN TM score (0–100); used when `board !== "jig"` |
| `jig_score` | `row.jig_score` | JIG score; used when `board === "jig"` |
| `edge` | `row.edge` | EV edge (decimal; displayed as ±pp) |
| `arsenal_edge_score` | `row.arsenal_edge_score` | Arsenal edge 0–10 (displayed as Signal) |
| `arsenal_edge_confidence` | `row.arsenal_edge_confidence` | Arsenal confidence 0–1 (displayed as %) |

**Files:** `frontend/assets/js/slip-state.js`, `frontend/assets/js/destination-picker.js`

---

## Storage scope

- **Client-side only** — fields live on the in-memory leg object in `window.__hrSlip` state.
- **No DB column** — not written to `legs` table, not included in the `POST /api/tickets/leg` body.
- **No POST field** — `buildLegPayload()` is unchanged; these fields are not sent to the server.
- Old legs (added before this commit) have `null` for all five fields; the pick card renders `"—"`.

---

## Distinction from the earlier signal_snapshot path (July)

A prior capture path (July, commit context: `signal_snapshot` key in `buildLegPayload`) passed a `signal_snapshot` blob through the POST body. That path is still in `buildLegPayload` — if `row.signal_snapshot` is set it is included in the server POST. The Aug 12 snapshot is **separate and additive**: it appends five explicit named fields directly to the client leg object rather than embedding them in a server-side blob. The two paths coexist. The pick card reads the Aug 12 named fields (not the July signal_snapshot blob) for its per-leg display.

---

## Protected surfaces

- No model probability, EV, tier, ranking, or server-side scoring logic touched.
- No schema change.
- MAIN/JIG separation upheld: TM and JIG scores are read from the row, not blended.
