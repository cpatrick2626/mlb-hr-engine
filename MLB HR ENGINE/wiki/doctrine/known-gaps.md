# Known Gaps / Parked

**Last Updated:** 2026-06-15

Items that are real gaps but NOT currently authorized for action. Check here before opening new issues on the same items.

---

## xFIP Doc/Code Mismatch

**Gap:** `formulas/pitcher-vulnerability.md` documents a 4% xFIP weight. The actual model (`engine/probability.py`) does NOT use xFIP — uses K/GB/BB suppressor instead.

**Options:**
- Fix doc to match code (documentation-only change), OR
- Add xFIP to model (scoring change, requires n≥200 settled-pick gate per operator doctrine).

**Status:** Parked. Operator decision needed before action.

---

## Silent Neutral Default for Unknown Pitchers

**Gap:** Pitchers with no Savant / MLB Stats API data silently default all vulnerability components to 1.0 (neutral, zero impact on score). No flag, no log entry, no UI indicator.

**Impact:** A batter facing an unknown pitcher scores as if the pitcher is perfectly league-average, invisibly. Operator cannot detect this condition from the dashboard.

**Status:** Parked. Observability gap — no urgency until data coverage degrades.

---

## Dead app.py (Streamlit)

**Gap:** The Streamlit dashboard (`mlb_hr_engine_v4/app.py`) is non-production and out of sync with current codebase:
- Uses stale `foundation`/`ceiling` role keys (renamed to `prime`/`explosive` in production).
- Generates false-positive audit flags when code is scanned.

**Recommended action:** Deprecate or delete `app.py` to stop false-positive audit noise.

**Status:** Parked pending explicit operator authorization.

Cross-ref: [[deploy-runbook]] — Streamlit listed as DEAD/NON-PRODUCTION there.

---

## Pitch Mix Modal Blank Fields

**Gap:** Velo column and pitcher-panel HR/9 render blank in some cases.

**Status:** Unverified — unknown if these are wiring bugs or just unpopulated data from the source. Needs a targeted audit session.

---

## JIG_TIER_THRESHOLDS Calibration Epoch Mismatch

**Gap:** `JIG_TIER_THRESHOLDS` were calibrated to an old scoring epoch where `jigScore` distribution was wider. In the current epoch, most players score as JIG-APEX. Distribution is over-concentrated at the top.

**Impact:** Latent. Ticket roles correctly gate on FS tier (not JIG tier), so role assignment is unaffected. JIG display ordering may not differentiate well.

**Status:** Parked. Low urgency until operator wants sharper JIG tier discrimination.

---

## Rooms Governance / Claude Projects Mismatch

**Gap:** The rooms governance model was designed around ChatGPT Projects. It does not map cleanly to Claude Projects — room boundaries, context isolation, and output routing rules have subtle incompatibilities.

**Status:** Open structural question. No immediate action item.

---

## opphr vs pitcher_hr9 Field Name Ambiguity

**Gap:** Two different field names appear to reference the same pitcher HR/9 value:
- `opphr` — accessed as `row.opphr` in FSM_COLS (confirmed in the leaderboard row payload from `/api/slate`)
- `pitcher_hr9` — accessed as `row.pitcher_hr9` in `FsmPitchMix` (full-slate-matrix.js) for the pitcher tier label

**Discovered:** 2026-06-23, during Phase 2A audit (Pitcher Vulnerability Strip build for live board). The Pitcher Vulnerability Strip (pvs-*) uses `opphr` exclusively (confirmed column).

**Risk:** If the two fields are computed differently (e.g., different epochs, normalizations, or null-handling), the PVS strip bucket labels may diverge from the FsmPitchMix pitcher tier label for the same pitcher. Currently unverified whether they are identical values under different keys or genuinely distinct.

**Status:** Parked. Needs one targeted backend audit to confirm field identity or divergence. No frontend action until backend resolves. Using `opphr` is safe for display purposes (it's the confirmed FSM column with established bucket thresholds).

**Cross-ref:** `wiki/sessions/2026-06-23-pvs-live-board-build.md`

---

## Cross-References

- [[deploy-runbook]] — deploy surface truth
- [[ticket-roles]] — role calibration
- [[design-pitch-mix-analysis]] — pitch mix data wiring
- [[tier-vocabulary]] — JIG tier vocabulary
