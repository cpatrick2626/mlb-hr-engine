# Modal Governance v1
## MLB HR ENGINE — Modal & Overlay Doctrine

**Owner:** Claude (UX Doctrine)
**Codex:** Implementation
**Status:** Documentation Only — No Runtime Code

---

## 1. Core Rule

**Default to inline expansion. Modals are the exception, not the pattern.**

Every modal adds: focus trap overhead, state management risk, rerender surface, and cognitive interruption. A modal is only justified when the content is contextually detached from the current view AND user intent is unambiguous AND the action is modal in nature (confirmation, detail deep-dive).

---

## 2. When Modals Are Allowed

| Trigger | Modal Allowed | Reason |
|---|---|---|
| Deployment confirmation (Clear Slip) | YES | Destructive, irreversible, requires explicit user intent |
| Suppression override confirmation | YES | Rare, significant override, must be deliberate |
| Player detail deep-dive | YES | Full stats payload does not belong inline in a card |
| Full Slate investigation (single player from game row) | YES | Expands a compact row into full context without disrupting the full slate scan |

**All other patterns:** use inline expansion, expanders, or additional columns.

---

## 3. When Inline Expansion Is Preferred

| Pattern | Use Instead |
|---|---|
| Pitch mix analysis | `st.expander` with lazy-load gate |
| Barrel/power stats breakdown | Expandable card section |
| HVY modifier detail | Inline below HVY card header |
| Filter explanations | `st.help` tooltips on labels |
| Portfolio optimizer results | Portfolio tab section |
| P&L detail | Performance tab inline |
| Arsenal data | Pitch Mix expander within card |
| Game context (weather, park) | Card footer strip, always visible |

**Rule:** If the content logically belongs to the card, it expands within the card. If it belongs to a different screen entirely, it's a tab switch, not a modal.

---

## 4. Modal Priority Hierarchy

When two modal triggers could fire simultaneously, priority order:

```
1. Deployment confirmation (Clear Slip two-step) — BLOCKS all others
2. Player detail modal — standard priority
3. Full Slate investigation modal — standard priority
4. Suppression override — standard priority
```

**Stack limit: 1 modal at a time. No nested modals under any circumstance.**

If a second modal trigger fires while one is open: the second trigger is ignored. The user must close the current modal first. No stacking. No queue.

---

## 5. Deployment Confirmation Modal Rules

**Trigger:** "Clear Slip" first press
**Form:** Two-step inline confirmation (not a full modal):
- Step 1: Button changes to "Confirm Clear" + red warning text
- Step 2: Confirm press clears slip

**Why inline, not modal:** Streamlit st.dialog adds rerun surface. Two-step inline is lower risk, same safety guarantee.

**Full modal** is NOT used for Clear Slip. This keeps the confirmation within the deployment tray where attention already is.

**Deployment confirmation for individual picks (Save for Results Tracking):** Single-step inline. No modal. Pick tracking is additive, not destructive.

---

## 6. Suppression Override Modal Rules

**Trigger:** User explicitly enables a filtered-out pick (suppressed by EV/edge/barrel floor)

**Required modal content:**
- Player name + current model prob
- Why pick was suppressed (which filter failed, by how much)
- Warning: "This pick is below minimum qualification thresholds."
- Two buttons: OVERRIDE ANYWAY | CANCEL

**Dismissal:** Modal closes. Session override stored in session_state. Does not persist to CSV. Override cleared on next data refresh.

**Forbidden:** Modal must not trigger a data reload. Modal must not change any model values. Override is display/filter only.

---

## 7. Player Detail Modal Rules

**Trigger:** "Detail" button on any card type

**Required content:**
- Full Statcast profile (barrel, xSLG, FB%, hard hit, EV, sweet spot, pull%)
- Season context (PA, HR, HR rate)
- Calibrated model probability + raw pre-calibration probability
- Market odds snapshot (best book, no-vig prob, edge)
- Weather + park factor display
- HVY modifier if available
- Platoon split

**Forbidden in player detail modal:**
- FD Slip add button (belongs in card, not modal)
- Filter controls
- Any state mutations beyond "add to slip" (which should be removed from modal entirely)
- Routing or tab change triggers

**Size:** 80% viewport width max, 90% height max. Internally scrollable. Closes on backdrop click or X button.

---

## 8. Full Slate Investigation Modal Rules

**Trigger:** Row click or expand icon on Full Slate compact row

**Required content:**
- Identical to player detail modal content
- Plus: full game context (opposing pitcher full stats, lineup position, park diagram if available)
- Contextual header shows: "GAME: AWAY @ HOME · TIME · PARK"

**Forbidden:**
- Full Slate modal must not trigger HVY computation if not already loaded
- Must not trigger a new data fetch
- Displays only what is already in the player dict at render time

---

## 9. Modal Stacking Limits

**Rule: Maximum 1 modal open at any time. Zero exceptions.**

Rationale: Streamlit's `st.dialog` has significant rerun implications. Nested modals create compounding rerender surfaces, state ownership ambiguity, and z-index/focus-trap conflicts. The platform cannot safely support modal stacks.

**Implementation requirement:** Before any modal is opened, check for existing open modal. If one exists, block the new trigger. Do not queue.

---

## 10. Forbidden Modal Patterns

The following patterns are prohibited regardless of use case:

| Forbidden Pattern | Why |
|---|---|
| Modal spawned by another modal | Creates stacking — blocked by §9 |
| Modal that triggers a data reload / rerun | Rerun closes the modal in Streamlit |
| Modal that owns session_state that outlives modal close | State leak; causes ghost effects on rerender |
| Modal triggered by route change | Route changes belong to tab nav, not modals |
| Modal used for filter controls | Filters belong in TCC sidebar |
| Modal used for success/info notifications | Use inline toast or st.success |
| Decorative/cinematic overlay (no action required) | Pure noise; forbidden |
| Giant welcome/onboarding modal | Not a production ops tool |
| Modal auto-opened on page load | Aggressive; forbidden |
| Modal that disables the deployment tray | Tray must remain accessible |
| Modal that changes model output or scores | Model is read-only in UI layer |
| Auto-dismissing modals (countdown close) | User controls modal close |

---

## 11. Modal Sizing Standards

| Type | Max Width | Max Height | Scroll |
|---|---|---|---|
| Player Detail | 80vw | 90vh | Internal |
| Full Slate Investigation | 80vw | 90vh | Internal |
| Suppression Override | 480px | auto | None needed |
| Deployment Confirmation | Inline only (no full modal) | — | — |

---

## 12. State Ownership Rule

**Modals are stateless viewers. They display data; they do not own it.**

The only valid modal-to-state interaction: triggering an action already defined in session_state (e.g., adding to FD Slip). The modal itself never writes new state keys. It reads and displays. Actions are passed through existing handlers.

---

*Documentation only. No implementation. No app.py changes. No session_state changes.*
