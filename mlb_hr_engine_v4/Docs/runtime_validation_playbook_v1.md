# Runtime Validation Playbook v1
## MLB HR Engine — Master Stabilization

**Date:** 2026-05-20  
**Step:** 12 of 12  
**Owner:** Claude (doctrine)  
**Version:** v1.0 — Post-Step-12

---

## Purpose

Defines how future runtime validation must be performed before any system can be declared stable. Establishes the evidence standard required to promote a system from UNSTABLE or CAUTION to SAFE in `known_good_baseline_definition.md`.

**Core Rejection:** "Works on my machine," visual assumptions without runtime proof, and partial validation presented as full validation are not acceptable evidence of stability.

---

## Validation Authority

The following parties share validation responsibility:

| Role | Responsibility |
|---|---|
| Codex | Runs the app, executes AppTest, provides runtime evidence |
| Claude | Reviews evidence against doctrine, confirms checklist compliance, updates baseline |
| Neither | Declares stability without evidence from the other |

A system is not SAFE until both parties have confirmed evidence against the relevant playbook section.

---

## Evidence Standards

### What Counts as Evidence

| Evidence Type | Acceptable For |
|---|---|
| AppTest bounded validation (specific route/function, no full app rerun) | Functional correctness of isolated component |
| Live browser validation (human observation of runtime behavior) | UX continuity, card rendering, scroll, modal, full slate |
| Log output confirming function executed and returned expected value | Data pipeline correctness, API fetch, cache hit/miss |
| `reports/daily_YYYY-MM-DD.txt` generated without error | `ops_daily.py` pipeline integrity |
| `audit_pitch_mix.py` — all 7 tests pass | Pitch mix data foundation correctness |
| `analyze_calibration.py` output showing Brier improvement on held-out data | Calibration parameter validity |
| `monitoring_dashboard.py Phase 4` showing drift within threshold | Calibration drift status |

### What Does Not Count as Evidence

| Claim | Why Rejected |
|---|---|
| "I reviewed the code and it looks correct" | Code review is not runtime validation |
| "The logic is identical to the prior working version" | Logic similarity does not guarantee identical runtime behavior |
| "It worked when I tested manually once" | Single-pass manual test is not repeatable evidence |
| "The test suite passed" | Test suites verify code correctness, not feature correctness or UX continuity |
| "No error was thrown" | Absence of exception does not confirm correct behavior |
| "Visual inspection of the rendered card" without runtime data | Visual assumptions without runtime proof rejected |
| Partial validation on one tab presented as validation for all tabs | Partial validation is partial — must be scoped exactly |

---

## Section 1: Bounded AppTest Validation

**Use for:** Isolated component correctness (filter logic, scoring function, data transformation).  
**Do not use for:** Full app state, UX continuity, session_state interactions.

### Required Protocol

1. Identify the specific function or component under test
2. Construct a bounded test: fixed input → expected output
3. Run without launching full Streamlit server
4. Confirm output matches expected value
5. Confirm no session_state keys are modified as side effect

### Scope Declaration Required

Every AppTest result must declare its scope:
- "This validates `_apply_tactical_filters()` with min_barrel=0.08 correctly reduces pick list."
- NOT: "This validates the filter system."

Scope creep in test claims is a validation failure.

---

## Section 2: Live Browser Validation

**Use for:** Card rendering, scroll behavior, modal interaction, Full Slate layout, tab continuity, mobile viewport.

### Required Protocol

1. Start Streamlit server with production config
2. Load today's date slate (or a known test date)
3. Navigate to the specific surface under validation
4. Observe and document runtime behavior — not code behavior
5. Capture screenshot or explicit log confirmation where possible

### Minimum Scenarios for UX Continuity Validation

| Scenario | Required Observation |
|---|---|
| Initial page load | Sidebar renders; picks present; no exception in log |
| Tab switch (MAIN → JIG → Full Slate → Performance) | Filter state preserved across all tabs |
| TCC filter change (barrel threshold adjustment) | Pick list updates within 2 seconds; no page reload |
| Pitch mix expander (collapsed → load → expanded) | Load button required; full content appears after click |
| Quick View card scroll | 12 cards visible; rank badges correct; photos load |
| Elite tab sort | Picks sorted by barrel_pct descending; secondary sort by score |
| Matchup Edge sort | Picks sorted by hvy_modifier descending; missing-context picks at bottom |
| Full Slate All Players mode | All starters displayed; game-organized; filters do not remove players |
| Auto-refresh | Session_state keys preserved; operator filter state intact |
| Mobile viewport (375px) | No horizontal overflow; all cards legible |

---

## Section 3: Rerun-Loop Detection

**Use for:** Confirming no runaway rerender triggered by a new component or session_state write.

### Required Protocol

1. Load the app with the new component active
2. Perform one user action (slider change, tab click, button press)
3. Observe Streamlit rerun count in server log
4. **PASS:** ≤ 2 reruns per user action
5. **CONDITIONAL:** 3 reruns (investigate but acceptable if all are user-caused)
6. **FAIL:** > 3 reruns or continuous rerun without user action

### Known Rerun Budget

Streamlit triggers one rerun per widget interaction. Acceptable rerun count per action:
- Filter slider/number_input: 1 rerun (widget state change)
- Tab switch: 1 rerun
- Lazy gate load button: 1 rerun (gate opens) + 1 rerun if cache miss (acceptable = 2 total)
- Auto-refresh: 1 rerun (scheduled)
- Any action triggering > 2 reruns: investigate before declaring stable

---

## Section 4: Full Slate Validation

**Use for:** Confirming Full Slate displays correct player populations in all 3 modes.

### Required Protocol Per Mode

| Mode | Required Evidence |
|---|---|
| All Players | Count matches total starters from schedule; no TCC filters applied; game headers present |
| Qualified | Count matches `_tac_ranked` with active TCC params; no additional players shown |
| Elite Targets | All displayed players have barrel_pct ≥ 0.08; sub-elite not shown |

### Additional Full Slate Checks

- Tab count label shows `len(all_players)` (total slate), not filtered count
- Game-organized view: each game group has correct pitcher attribution
- Missing-odds players: shown in All Players but excluded from FD Slip

---

## Section 5: Deployment Tray Validation

**Use for:** Confirming FD Slip and deployment workflow integrity.

### Required Protocol

1. Add 3–5 picks to FD Slip
2. Confirm game time cards show ET timezone suffix
3. Confirm Clear Slip requires two-step confirmation
4. Log picks via "Save for Results Tracking" button
5. Confirm pick appears in pick_tracker.csv with correct schema
6. Confirm `pick_id` is deterministic SHA1[:12] (repeat log of same pick does not duplicate)
7. Confirm `sportsbook` field populated from `best_bookmaker` fallback

---

## Section 6: Modal Validation

**Use for:** Confirming modal open/close does not corrupt engine state.  
*(Applicable after Phase 4 of post-stabilization sequence.)*

### Required Protocol

1. Open player detail modal from MAIN engine
2. Confirm modal renders player Statcast profile, odds, CLV
3. Close modal
4. Confirm active player in MAIN is unchanged
5. Confirm TCC filter state is unchanged
6. Confirm JIG state is unchanged
7. Confirm scroll position restored to triggering card (not page top)

---

## Section 7: Shell Continuity Validation

**Use for:** Confirming app shell integrity after any change to `app.py`.

### Required Protocol

1. Fresh session (clear session_state)
2. Load picks for today's date
3. Confirm:
   - Sidebar fully renders (CLV button, optimizer toggle, P&L summary)
   - All 4 MAIN tabs render without exception (QUICK VIEW / ELITE / MATCHUP EDGE / PORTFOLIO)
   - Full Slate tab renders with correct mode selector
   - JIG section renders with correct mode selector
   - Performance tab renders settled picks (or empty state with guidance)
4. Switch between all tabs — confirm no filter state cleared on any switch
5. Confirm parent orchestration intact: MAIN TCC change does not affect JIG TCC state

---

## Section 8: Mobile-Width Validation

**Use for:** Confirming mobile rendering at ≤ 768px viewport.

### Required Protocol

1. Open browser DevTools; set viewport to 375px wide
2. Load app
3. Confirm:
   - No horizontal scroll required for any card
   - All stat pills visible (may wrap; must not overflow)
   - All label text ≥ 10px (zoom test)
   - Tap targets: buttons ≥ 44×44px (standard mobile touch target)
4. Navigate to Full Slate
5. Confirm game-organized view renders without overflow
6. If drawer system implemented: confirm drawer open/close cycle without rerender

---

## Section 9: Degraded-Data Validation

**Use for:** Confirming engine handles partial data correctly without crashing.

### Required Protocol

1. Simulate Statcast unavailable (mock empty response from `clients/statcast.py`)
2. Confirm app loads with neutral power_mult (1.0) and blended-source indicator
3. Simulate Odds API unavailable (mock empty response from `clients/odds_api.py`)
4. Confirm app loads with fallback to `manual_odds.csv` or empty market data state
5. Simulate pitcher arsenal unavailable (mock empty from `clients/pitch_mix.py`)
6. Confirm HVY modifier defaults to 1.0 (neutral); missing-context players sorted to bottom
7. Simulate lineup not yet confirmed (< 1 hour before game)
8. Confirm PROJECTED slate indicator shown; picks generated from projected lineup

---

## Section 10: Trust-State Validation

**Use for:** Confirming trust-state indicators behave correctly.

### Required Protocol

1. Load a date with blended-source players (prior-year Statcast)
2. Confirm blended-source indicator visible on affected picks
3. Run `monitoring_dashboard.py Phase 4`
4. Confirm drift alerts correctly identify any bucket exceeding threshold
5. Trigger odds API key validation with a malformed key (< 32 hex chars)
6. Confirm rejection message displayed; no silent bad API request
7. Load a pick with American odds in (−100, 100) range
8. Confirm pick rejected with log entry; does not enter model

---

## Section 11: Escalation Continuity Validation

**Use for:** Confirming escalation surfaces correctly without corrupting engine state.

### Required Protocol

1. Trigger STEAM alert (or simulate with mock steam move data)
2. Confirm STEAM badge appears on affected picks in Quick View
3. Confirm STEAM alert does not reorder picks (only badges added)
4. Confirm escalation remains in tray — does not replace main engine view
5. Confirm active player selection unchanged after STEAM event
6. Confirm Full Slate is not collapsed by STEAM event

---

## Validation Scope Declaration Template

Every validation claim must include:

```
VALIDATION CLAIM
System: [name of system]
Evidence Type: [AppTest / Live Browser / Log / Script]
Scope: [specific function / route / tab / component]
Date: [YYYY-MM-DD]
Result: [PASS / CONDITIONAL / FAIL]
Evidence: [what was observed / what output confirmed]
Limitations: [what was NOT validated in this pass]
```

Validations without a scope declaration and limitations statement are not accepted.

---

## Validation Anti-Patterns (Explicitly Rejected)

| Anti-Pattern | Rejection Reason |
|---|---|
| "Works on my machine" | Not reproducible; not documented; not evidence |
| "I tested it and it looked fine" | Visual assumption without runtime proof |
| "The code logic is correct therefore it works" | Code correctness ≠ runtime correctness |
| "All tests pass" | Test suites verify code paths, not feature behavior or UX continuity |
| "It worked before and this change is minor" | Minor changes in Streamlit can cause unexpected rerun cascades |
| "I validated the Quick View tab so the whole app is stable" | Partial validation is not full validation |
| "The baseline is the same" | Baseline comparison without runtime re-verification is insufficient after any code change |

---

*Created: 2026-05-20 — Step 12 Final Stabilization Closeout*
