# Known Gaps / Parked

**Last Updated:** 2026-06-25

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

## Full Slate Lineup-Hydration Degradation + No Pipeline Observability

**Discovered:** 2026-06-23, Full Slate completeness audit (read-only — nothing changed).

**Diagnosis updated:** 2026-06-23, az-stl timing check (read-only — nothing changed). VERDICT: MIXED — timing confirmed correct behavior for az-stl + a real secondary partial-hydration failure identified.

**Real finding (actionable):**
Some games hydrate with suspiciously few batters. On the 2026-06-23 slate: az-stl returned only 2 batters for an entire game; nyy-det 4, kc-tb 5, lad-min 5 (low). Root cause is now partially understood — see resolved diagnosis below.

**Resolved: az-stl timing check (was open question)**

1. **TIMING — confirmed correct behavior, not a bug:**
   - Slate built 12:37 PM ET; az-stl first pitch 7:45 PM ET (7h gap). Lineups typically post ~2–4h before first pitch. At slate-build time, az-stl's lineup was NOT posted. Roster fallback (`get_team_active_roster`) fired by design. This half is correct behavior.
   - NOTE on re-testing: `/api/slate` has a 12h TTL — re-pulling returns the SAME cached slate. You cannot observe self-healing by re-pulling. Diagnosis was done by timestamp reasoning. Today's az-stl slate will NOT re-hydrate (cache); tomorrow's 14:05 UTC cron rebuilds fresh.

2. **PARTIAL HYDRATION FAILURE — the real find:**
   - The other late games whose lineups also weren't posted (kc-tb, nyy-det, lad-min) got 5–6 players from their roster fallbacks. az-stl got only 1 per team (Carroll/AZ, Walker/STL — both stars with bulletproof Statcast). If it were pure timing, az-stl would look like the others (~5–6 survivors). Instead AZ and STL each resolved to a single viable player → the roster fallback for those two teams returned or resolved PARTIAL or degraded data, not the expected ~13–15 non-pitchers.
   - Both survivors had `best_american: null` (no HR props in The Odds API at build time), so they fail `filters.py:62` Rule 7 and appear in `leaderboard_rows` only because that endpoint serves `all_players`, not `qualified`.

3. **ROOT PROBLEM — no observability (this is what to fix):**
   - Cannot determine from code alone WHICH mechanism failed for AZ/STL — roster call errored vs returned partial vs returned full-then-gutted-downstream — because all three drop points are SILENT. Three silent-drop locations, all missing log statements:
     - `mlb_stats.py:633–634` — `except Exception: return []` (roster fetch failure swallowed)
     - `pipeline.py:637` — `if not lineup: continue` (team skipped, no log)
     - `pipeline.py:120–121` — `if season_pa==0 and recent_pa==0: return None` (player dropped, no log)
   - Matches the original audit's `pipeline_stats` observability proposal from a second angle.

**Proposed fix (next focused session — NOT done, protected surface, gated):**
Add ADDITIVE LOGGING ONLY at the three points above — print/log statements, ZERO logic change — so the next hydration failure is fully diagnosable from cron output alone. Pipeline is the most-gated surface: do as its own scoped session, reviewed line-by-line, confirmed purely additive before commit. Not urgent (nothing on fire; cache rebuilds tomorrow; observability only pays off on next occurrence). Optional later: a min-batters-per-game warning flag, and/or surfacing roster-fallback counts, once logging confirms the mechanism.

**Separate thread (do not conflate):**
`leaderboard_rows_jig` came back empty on this slate. Could be a real JIG build failure OR legitimately no qualifying JIG rows for this slate. Needs its own read-only check — is JIG supposed to have data here? Not part of the batter-count question.

**Audit misreads — do NOT act on these:**
- "~170 missing batters / expected 15×18=270" is a phantom target. The pipeline models bettable HR threats, not every lineup spot. The `season_pa==0 AND recent_pa==0` drop is CORRECT, intended behavior — you cannot compute HR probability for a player with zero batting data. ~100 modelable batters across 15 games is plausibly correct. Do NOT "fix" the PA filter; it is working as designed.
- The frontend display caps (HR Threat Cards `slice(0,4)`, Escalation top 8) are intentional summary-panel limits, not data loss. ThreatRankings renders all rows uncapped. Not a bug.

**Next session order:**
1. Additive logging at the three silent-drop points (gated, pipeline surface).
2. Decide on `pipeline_stats` observability in `/api/slate` payload (separate gate — touches API shape).
3. Separate JIG-empty check.

**Status:** Parked. Diagnosis complete (read-only). az-stl open question resolved. Pipeline is a protected surface — no action until gated.

---

## Arsenal Velocity Data Gap — Pitch-Arsenal-Stats Endpoint Carries No Velocity Column

**Discovered:** 2026-06-24, deployed pipeline logging (4e15147) surfaced `[arsenal] stats endpoint: 690 pitchers loaded for year=2026, fastball avg_speed: 0/690 pitchers` on first production run. Read-only deep diagnostic followed.

**Verdict:** Code/mapping mismatch, but DORMANT — touches no live scoring. Not urgent.

**Findings:**
- The Savant pitch-arsenal-stats endpoint (`arsenal.py:231 _fetch_arsenal_from_stats`) does NOT contain a velocity column — confirmed for both 2026 and 2025 (identical schemas). The code looks for `mph` / `avg_speed` / `pitch_speed_mean` / `avg_mph`; none exist in the CSV. The code comment claiming the CSV "uses mph" is wrong for the current schema.
- Decisive test: 2025 has the same schema (no velocity), so this is NOT a 2026 seasonal-availability gap — it is a permanent endpoint/mapping mismatch. Velocity was likely never carried by this endpoint, or the endpoint schema changed.
- The 0/690 count: `arsenal.py:254–257` counts pitchers where `avg_speed is not None`; since every row resolves to `speed=None`, the count is 0.

**Blast radius — essentially zero:**
- `arsenal_matchup_factor` (IS in live HR scoring): UNAFFECTED — uses `rv_per100`, whiff, usage, PA; does not read velocity. Working correctly.
- `pitcher_velo_decline_factor` (the velocity consumer): returns `1.0` / neutral for all 690 pitchers — but grep confirms it is NOT wired into `pipeline.py` or `engine/`. Only called by `scripts/analysis/analyze_2026_full.py` (research script). Dormant signal returning neutral, zero live consequence.
- Display (`app.py:4290`): renders `"—"` when velocity is null. Correct defensive handling.
- NULL-AS-ZERO trap: NOT present. Empty velocity handled defensively everywhere; no numeric contamination, no fake zeros.

**Correctness risk today:** NONE. Live scoring (MAIN/JIG) does not consume velocity. The gap is cosmetically visible (blank velocity in UI, shown as `"—"`) only.

**The real fix (deferred — data-sourcing project, NOT a field-name tweak):**
Velocity is NOT available from `pitch-arsenal-stats`, and the alternate `pitch-arsenals` endpoint's 2026 velocity columns are also empty. A working velocity source would need a different Savant endpoint (statcast search or pitch-level aggregation), then wiring into `_fetch_arsenal_from_stats`. Do NOT pursue until a feature actually needs velocity.

**Link to parked work:** Directly affects the parked Arsenal Exploit Score. If/when that feature is built and wants pitch velocity as an input, this sourcing gap must be resolved first. Whoever builds Arsenal Exploit should read this entry — velocity is not currently available from the arsenal client.

**Status:** Parked. Read-only diagnostic. Nothing changed. No fix attempted (correctly — dormant, non-urgent, and the fix is a data-sourcing task for a future gated session).

**Cross-ref:** `wiki/architecture/pitch-mix-data-availability.md`

---


## Probable-Pitcher Labeling — `pitcher_confirmed` Misnomer

**Discovered:** 2026-06-23, probable-pitcher audit (read-only).

**Findings:**
- Pipeline fetches `MLB probablePitcher` at `mlb_stats.py:165`, extracted at ~184–185. This feeds into full scoring. No roster fallback exists for probable pitcher; "TBD" appears when MLB posts no probable — correct behavior by design.
- `pitcher_confirmed` (`pipeline.py:302`) is a misnomer: it is set `True` for merely-probable pitchers (not confirmed starters). A player flagged `pitcher_confirmed=True` may still be scratched pre-game.
- **Proposed rename:** `pitcher_status ∈ {PROBABLE, TBD, CONFIRMED}` — surface the distinction rather than flatten it to a boolean. `CONFIRMED` reserved for when a real confirmation signal exists (not currently sourced).
- **Blast radius of rename:** touches `pipeline.py:302` (assignment), `api/main.py:454` (payload serialization — PROTECTED), and any `app.py` display sites reading `pitcher_confirmed`. Scoring logic is unaffected — the field is metadata only.

**Status:** Deferred. Scoring unaffected. Rename is a gated change (touches protected surfaces: `pipeline.py`, `api/main.py`). Do not rename until operator explicitly authorizes a scoped session that reviews all three touch points.

---
## hr-threat-zone.js Displays `hrpa` as "HR PROB" Instead of `hrprob` — Display Bug

**Discovered:** 2026-06-24, pre-commit audit of live hr-threat-zone.js bundle.

**What:** `frontend/assets/js/hr-threat-zone.js` reads `row.hrpa` (the raw season HR/PA rate = `season_hr / season_pa`, a small decimal e.g. 0.045) and multiplies it ×100 (`hrtzFmtProb`, ~line 33), displaying the result labeled **"HR PROB"** in the Primary HR Threat Zone panel.

**Why it's wrong:** The model HR probability is the separate field `row.hrprob` — already expressed as a percentage (e.g. `14.2`). `hrpa` is NOT the model probability; it is the raw season batting-average-for-HR, a fundamentally different quantity. The live threat-zone panel therefore shows the HR/PA rate masquerading as model HR probability — mislabeled and numerically incorrect for that panel.

**Scope / impact:** Display-only on the existing hr-threat-zone.js bundle. No scoring impact. The correct field (`hrprob`) is already used in `full-slate-matrix.js`. The new COMMAND tab build (`command-tab.js`) also uses `hrprob` correctly and does not inherit this bug.

**Fix applied:** `hr-threat-zone.js` updated to read `hrprob` directly, display `hrprob.toFixed(1) + "%"` without ×100, and sort by `hrprob` descending. Four-line surgical edit — comment, formatter, read field, sort key. Vercel auto-deploys on push.

**Status:** RESOLVED — commit `6807532` (2026-06-25). Schwarber shows ~19.1% (was 8.6%), matching COMMAND tab and Full Slate Matrix. Only `frontend/assets/js/hr-threat-zone.js` changed. No scoring, API, or other bundles touched.

---

## Cross-References

- [[deploy-runbook]] — deploy surface truth
- [[ticket-roles]] — role calibration
- [[design-pitch-mix-analysis]] — pitch mix data wiring
- [[tier-vocabulary]] — JIG tier vocabulary
