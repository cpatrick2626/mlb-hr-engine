---
name: matchup-quality-two-axis-spec
description: Matchup-quality two-axis fix spec — DANGER polarity inversion diagnosis, batter-threat / pitcher-vulnerability axis separation (DANGER→TARGET), full consumer inventory, phased migration plan with protected-surface gates
metadata:
  type: roadmap
---

# Matchup Quality — Two-Axis Fix Spec

**Status: DESIGN — approved, Phase 1 authorized. 2026-07-06.**
**Designer:** Claude Fable 5 (read-only design mission, 2026-07-06)
**Scope:** `matchup_quality` producer + all consumers. MAIN-side display signal only. No JIG/HVY involvement.

---

## 1. Confirmed Diagnosis

### 1.1 Primary defect — DANGER polarity inversion

The producer (`mlb_hr_engine_v4/pipeline.py:38` `_matchup_quality_tier`) assigns `DANGER` when `pitcher_hr9 >= PITCHER_VULNERABILITY_HR9_THRESHOLD` (2.2, `config.py:258`). Per the producer's own comment this means **"extreme pitcher vulnerability — gives up 2.2+ HR/9 = top 5% vulnerable."** That is the batter's *best* pitcher-side condition on the slate.

Every consumer renders `DANGER` as the batter's *worst* condition:

- `frontend/assets/js/full-slate-matrix.js:22` — `DANGER: { q: 0, color: "#ef4444" }` (0 of 4 quadrants, red)
- `full-slate-matrix.js:52` — legend text: *"pitcher strongly favored (0/4)"*
- `app.py:4914` — 0 filled pips; `app.py:4924` — tooltip: *"DANGER MATCHUP: Unfavorable matchup — pitcher dominant"*
- `app.py:5536` — `("#ef4444", "DANGER MATCHUP")` red label
- `full-slate-matrix.js:1561` — "matchup" focus filter keeps only `ELITE`/`STRONG`, so DANGER rows are *excluded* from the matchup-hunting view
- `32ab40c7-….js:12` — builder rank formula grants +6 only to `ELITE`/`STRONG`

Net effect: the batter facing the most homer-prone pitcher on the slate is displayed as the worst matchup on the slate, colored red, given zero quadrants, filtered out of the matchup focus view, and denied the rank bonus. The signal is exactly inverted at the point of operator decision.

### 1.2 Structural defect — axis conflation + short-circuit

`_matchup_quality_tier` mixes two different subjects in one field:

- **Batter threat** — `model_prob` + `barrel_pct` drive ELITE / STRONG / AVG / WEAK. Subject: the batter. Polarity: higher = better.
- **Pitcher vulnerability** — `pitcher_hr9` drives DANGER. Subject: the pitcher. Polarity (as consumed): red = bad for batter — inverted.

The DANGER check runs **first** and short-circuits (`pipeline.py:72-74`). A `model_prob = 0.20` batter (would be ELITE) facing a 2.3 HR/9 pitcher — plausibly the single best cell on the slate — is returned as `DANGER` and rendered as worst-of-slate. The conflation guarantees that the strongest compound situations are systematically mislabeled; the polarity inversion guarantees they are mislabeled in the most damaging direction.

### 1.3 Bonus findings (3)

1. **The inversion is codified in the documentation-of-record, not just styling.** Both legend/tooltip systems (`FSM_MATCHUP_DESC.DANGER` at `full-slate-matrix.js:52`, and `app.py:4924`) describe DANGER as "pitcher strongly favored / pitcher dominant" — the precise opposite of the producer's semantics. An operator reading the legend is actively misinformed; this is not recoverable by learning the color scheme.
2. **AEI pitcher-card mislabeling in the same vocabulary namespace.** The Arsenal Edge Intel pitcher card (`full-slate-matrix.js:~1197`) labeled a *season* HR/9 grade vs an average batter as "PITCHER VULNERABILITY," overloading the same term this spec's Axis 2 needs. Relabeled to "SEASON HR/9 GRADE" with a scope caption in commit `a186b9e` (ratified during the design mission).
3. **The polarity bug leaks into an ordering formula.** The builder rank function (`frontend/assets/js/32ab40c7-….js:12`) adds +6 when `r.quality ∈ {ELITE, STRONG}`. Because the DANGER short-circuit steals rows that would otherwise be ELITE/STRONG, the inversion silently depresses the builder ordering of top compound targets. Post-fix constraint: TARGET must **not** be added as a numeric bonus here (see §3.3 double-count rule) — restoring the correct `quality` value is the entire fix for this formula.

---

## 2. Corrected Model — Two Independent Axes

### 2.1 Axis 1 — Batter threat (`matchup_quality`, existing field)

Value space: **ELITE / STRONG / AVG / WEAK** — the DANGER branch is removed; everything else in `_matchup_quality_tier` is unchanged:

- ELITE: `model_prob >= MATCHUP_QUALITY_ELITE_THRESHOLD` (0.15)
- STRONG: `model_prob >= MATCHUP_QUALITY_STRONG_THRESHOLD` (0.10)
- WEAK: `model_prob < MATCHUP_QUALITY_AVG_THRESHOLD` (0.05) OR `barrel_pct < 0.04`
- AVG: everything else

No threshold values change. No new constants.

### 2.2 Axis 2 — Pitcher vulnerability (`pitcher_vuln`, new field)

Value space: **TARGET / NEUTRAL**.

- TARGET: `pitcher_hr9 >= PITCHER_VULNERABILITY_HR9_THRESHOLD` (2.2 — existing constant, `config.py:258`, value unchanged)
- NEUTRAL: otherwise (including null/missing `pitcher_hr9` — missing data is never TARGET)

Produced in `pipeline.py` alongside `matchup_quality`, carried through the profile dict, and mapped into `/api/slate` leaderboard rows in `api/main.py`.

### 2.3 The axes do NOT numerically combine — double-count rule

`pitcher_hr9` already feeds `model_prob` (it is a MAIN model input to λ). Axis 1's thresholds therefore *already reflect* pitcher vulnerability once, through the model. Any arithmetic that combines Axis 1 and Axis 2 — composite score, tier promotion, additive rank bonus keyed on TARGET — counts the same pitcher signal twice. **Banned:** numeric combination of the axes anywhere. **Allowed:** co-presentation (a TARGET badge next to the quality gauge) and boolean OR-conditions in filters (§2.5).

### 2.4 Vocabulary — ratified judgment call #1: DANGER → TARGET

- `DANGER` is rejected: its consumed polarity is inverted, and it remains the correct label for the *per-stat heatmap worst band* (§4) — reusing it here would perpetuate the collision.
- `PRIME` is rejected: it collides with the roles layer (`config.py:388-420` ROLE_PRIME_* / roles.py PRIME + EXPLOSIVE ticket roles) — a second vocabulary collision in the same UI.
- `TARGET` is adopted: it matches the AEI/tactical wording already in the product (a vulnerable pitcher is a *target*), reads with correct polarity (green/good for batter), and is unclaimed in every existing label namespace (tiers, roles, heatmap bands, TM bands).

### 2.5 No tier promotion — ratified judgment call #2

TARGET does **not** promote the Axis 1 tier (AVG + TARGET ≠ STRONG). Rationale: `pitcher_hr9` already lifts `model_prob`, which already lifts the Axis 1 tier through its thresholds — promotion would double-count (§2.3). The legitimate concern (post-fix, former-DANGER rows must not vanish from hunting views) is handled by **OR-conditions, not scores**: the FSM "matchup" focus filter becomes `quality ∈ {ELITE, STRONG} OR pitcher_vuln === "TARGET"`, and equivalent OR-conditions apply wherever quality gates surfacing. This restores visibility without touching any numeric ranking or probability.

---

## 3. Consumer Inventory (17) + Per-Consumer Migration

| # | Consumer | Location | Today | Migration |
|---|----------|----------|-------|-----------|
| 1 | Producer `_matchup_quality_tier` | `pipeline.py:38-89` | 5-value, DANGER short-circuit first | Remove DANGER branch → 4-value; docstring updated |
| 2 | Profile assembly | `pipeline.py:290, 342` | writes `matchup_quality` | Also write `pitcher_vuln` (TARGET/NEUTRAL) |
| 3 | Threshold constants | `config.py:255-258` | comment says "→ DANGER" | Comment-only edit: "→ TARGET (pitcher_vuln axis)"; values unchanged |
| 4 | API row mapper | `api/main.py:460-462, 480` | `mq_map` incl. DANGER → `quality` | Drop DANGER from map (fallback AVG already handles stragglers); add `pitcherVuln` field to row |
| 5 | FSM quadrant map | `full-slate-matrix.js:17-24` `FSM_MATCHUP` + `_ORDER` | DANGER: q=0 red | 4-key order; keep DANGER key as legacy-neutral grey for stale cache (§5) |
| 6 | FSM legend text | `full-slate-matrix.js:47-53` `FSM_MATCHUP_DESC` | DANGER "pitcher strongly favored (0/4)" | 4 corrected descriptions; add TARGET badge description |
| 7 | FSM player dot | `full-slate-matrix.js:423` | quality color, grey fallback | Unchanged logic; benefits automatically |
| 8 | FSM game-card MQ label | `full-slate-matrix.js:745, 775` | `row.quality` + `FSM_MATCHUP.AVG` fallback | Unchanged logic; add TARGET badge adjacent |
| 9 | FSM matchup focus filter | `full-slate-matrix.js:1561` | `["ELITE","STRONG"].includes(r.quality)` | OR `r.pitcher_vuln === "TARGET"` (§2.5) |
| 10 | FSM legend key row | `full-slate-matrix.js:1641-1643` | 5 keys | 4 keys + TARGET badge key |
| 11 | AEI pitcher card tier chip | `full-slate-matrix.js:~1197` | "SEASON HR/9 GRADE" (relabeled `a186b9e`) | Done in design mission; optionally surface TARGET badge here too |
| 12 | Command tab pill | `command-tab.js:186` | `CmtPill label="MATCHUP" val={row.quality}` | Unchanged logic; add TARGET pill when set |
| 13 | Matchup donut gauge | `c0092a94-….js:24, 174` | quality→fill/color map w/ AVG fallback | Drop DANGER entry (fallback covers stale); polarity correct after producer fix |
| 14 | Builder rank formula | `32ab40c7-….js:12` | +6 if quality ELITE/STRONG | **No change** — do NOT add a TARGET bonus (double-count rule §2.3) |
| 15 | Streamlit player detail MQ | `app.py:3257` (+ MATCHUP section ~3719) | 5-value badge | 4-value + TARGET badge |
| 16 | Streamlit quadrant pips + tooltips | `app.py:4907-4924` | DANGER=0 pips, "pitcher dominant" tooltip | 4-level pips; corrected tooltip text; TARGET tooltip added |
| 17 | Streamlit MQ pie + MATCHUP KEY + filter | `app.py:5411, 5532-5539, 5203-5215`; `config.py:379-386` `FS_MQ_PIE_COLORS` | 5-slice pie, DANGER red slice, 5-key legend | 4-slice pie; keep DANGER color key for stale data one cycle; legend + filter options updated |

---

## 4. Explicit Non-Targets — do NOT rename

These use ELITE/STRONG/…/DANGER *vocabulary* but are separate systems with **correct polarity**. They are out of scope; renaming them would be scope creep and would break operator muscle memory:

- **Per-stat heatmap bands** — `config.py:296-302` `FS_HEATMAP_COLORS`, `:361-375` text colors/shadows; `full-slate-matrix.js:142-150` bucket functions, `:634` `FSM_BUCKET_COLOR`. There DANGER = worst band of a *stat*, which is correct. Untouched.
- **TM_BANDS** — `full-slate-matrix.js:27-33`, true_matchup_score bands (operator-approved, "honest 0–100, do not rescale"). Uses COLD not DANGER anyway. Untouched.
- **FS tier system** — APEX/ELITE/EDGE/SIGNAL/WATCH/COLD (`config.py:263-279` `FS_TIER_THRESHOLDS`), model_prob display tier. Shares the word ELITE with Axis 1 but is a distinct, correctly-signed system. Untouched.
- **AEE label colors** — `full-slate-matrix.js:641` references `FSM_BUCKET_COLOR.DANGER` as a color token only. Untouched.

---

## 5. Migration Safety

- **Value space shrinks, does not change.** `row.quality` goes from {ELITE, STRONG, AVG, WEAK, DANGER} to the subset {ELITE, STRONG, AVG, WEAK}. No surviving value changes meaning, so consumers that don't special-case DANGER need zero edits.
- **Stale-cache fallbacks.** Cached `/api/slate` payloads and Supabase snapshots may carry `quality: "DANGER"` and lack `pitcherVuln` for one cache/snapshot cycle after Phase 1 deploys. Rules: (a) frontend maps keep a DANGER key rendering as **neutral grey**, not red, during the transition; (b) missing `pitcher_vuln`/`pitcherVuln` is always treated as NEUTRAL; (c) existing `|| fallback` patterns (`full-slate-matrix.js:423, 745`; `api/main.py:462`; gauge map) already degrade gracefully.
- **No new constants or thresholds.** Axis 2 reuses `PITCHER_VULNERABILITY_HR9_THRESHOLD` (2.2) verbatim. `config.py` numeric values are untouched (comment edits only).
- **No model impact.** `model_prob`, EV, edge, sizing, filters in `engine/`, and JIG scoring are untouched. This is a display-classification fix plus one additive payload field.

---

## 6. Phased Plan

| Phase | Scope | Protection | DONE MEANS |
|-------|-------|-----------|------------|
| **0 — Baseline** | Run pipeline for a live date; record `matchup_quality` distribution, list of DANGER rows, and a `/api/slate` payload snapshot | none | Baseline artifact saved for Phase 1 diff |
| **1 — Producer + API** ⚠ PROTECTED | `pipeline.py` (remove DANGER branch, emit `pitcher_vuln`), `api/main.py` (map field, trim mq_map), `config.py` comment | pipeline is canonical data-assembly; **operator sign-off — GRANTED (this doc's header)** | Payload diff vs Phase 0: only former-DANGER rows change quality (to their model_prob tier); `pitcherVuln` present on every row; no other field differs |
| **2 — Frontend (root `frontend/`)** | Consumers #5-#13 per table; #14 explicitly no-change | live Vercel surface — verify on laptop+phone per house practice | Legend/desc corrected; TARGET badge renders; focus filter OR-condition works; stale-cache DANGER renders grey |
| **3 — Streamlit `app.py`** ⚠ PROTECTED | Consumers #15-#17 | CLOSED surface per `PHASE3_REFINEMENT_DOCTRINE.md` — **separate operator authorization required before starting** | Pips/pie/legend/tooltips corrected; no session_state/routing/cache touched |
| **4 — Docs** | Wiki concept pages (matchup escalation, pitcher vulnerability), this page → Status: SHIPPED, `graphify update` | doc gate per `AGENTS.md` | Wiki + index + log updated |

Phases deploy in order; Phase 2 must not ship before Phase 1 is live (frontend would show TARGET badges that never populate).

---

## 7. Protected-Surface Sign-Off List

| Surface | Phase | Status |
|---------|-------|--------|
| `pipeline.py` producer (canonical data-assembly entrypoint) | 1 | **Authorized 2026-07-06** (header) |
| `api/main.py` payload shape (additive field, value-space shrink) | 1 | **Authorized 2026-07-06** (header) |
| `config.py` — comment-only edit; **no threshold value changes** | 1 | Authorized (comment scope only) |
| Root `frontend/` live production JS | 2 | Standard change control; verify deployed |
| `app.py` Streamlit UI (closed surface) | 3 | **NOT yet authorized — gate before Phase 3** |
| `FS_MQ_PIE_COLORS` + Streamlit display dicts | 3 | With Phase 3 authorization |
| MAIN/JIG separation | all | **No change** — both axes are MAIN-side display; no HVY blending; JIG untouched |
| session_state / cache / routing / hydration | all | **Untouched** — out of scope by design |

---

## 8. Phase 1 Implementation Prompt

> **Task:** Implement Phase 1 of `wiki/roadmap/matchup-quality-two-axis-spec.md` (producer + API). Design is ratified; do not redesign.
>
> 1. `mlb_hr_engine_v4/pipeline.py` — in `_matchup_quality_tier` (line ~38): delete the DANGER short-circuit branch (`if pitcher_hr9 >= PITCHER_VULNERABILITY_HR9_THRESHOLD: return "DANGER"`). Update the docstring: return set is {ELITE, STRONG, AVG, WEAK}; note that pitcher vulnerability moved to the separate `pitcher_vuln` field. All other logic and thresholds unchanged.
> 2. `mlb_hr_engine_v4/pipeline.py` — where the profile dict is assembled (~line 290/342), compute and emit `"pitcher_vuln": "TARGET" if float(pitcher_hr9 or 0.0) >= PITCHER_VULNERABILITY_HR9_THRESHOLD else "NEUTRAL"`. Missing/null hr9 is NEUTRAL, never TARGET.
> 3. `mlb_hr_engine_v4/api/main.py` — in the leaderboard row mapper (~line 460): remove `"DANGER": "DANGER"` from `mq_map` (keep the `.get(..., "AVG")` fallback); add `"pitcherVuln": p.get("pitcher_vuln", "NEUTRAL")` to the emitted row. Mirror in the JIG row mapper if it carries `quality`.
> 4. `mlb_hr_engine_v4/config.py:258` — comment-only: change "→ DANGER (top 5% vulnerable)" to "→ TARGET on the pitcher_vuln axis (top 5% vulnerable)". Do not change the value. Update the `config.py:253` tier-list comment to the 4-value set.
> 5. **Do NOT:** add TARGET to any numeric score/rank/tier promotion; touch frontend JS or app.py (Phases 2/3); change any threshold value; touch JIG/HVY.
>
> **Validate (DONE MEANS):** run the pipeline for a live date and diff the `/api/slate` payload against the Phase 0 baseline — every row has `pitcherVuln`; only former-DANGER rows changed `quality`, each to the tier its `model_prob` dictates; zero other diffs. Report changed files, commands, validation output, protected surfaces touched.

---

## 9. Ratified Judgment Calls (record)

1. **DANGER → TARGET** (not PRIME): PRIME collides with the roles layer (`config.py` ROLE_PRIME_*, ticket roles PRIME/EXPLOSIVE); TARGET matches the AEI/tactical wording already in the UI and carries correct polarity. Ratified 2026-07-06.
2. **No tier promotion for TARGET**: `pitcher_hr9` already feeds `model_prob`, which already sets the Axis 1 tier — promotion would double-count the pitcher signal. Surfacing of former-DANGER rows is restored by filter/rank-boost **OR-conditions** (boolean gating, e.g. FSM focus filter), never numeric combination. Ratified 2026-07-06.

---

## Cross-References

- `wiki/architecture/matchup-intel-field-gap.md` — pitcher-vulnerability panel wiring status
- `wiki/doctrine/main-jig-separation.md` — isolation rules (this spec is MAIN-display only)
- `PHASE3_REFINEMENT_DOCTRINE.md` — closed-surface gate for Phase 3
- Commits: `db70636` (FSM player dot polarity fix), `a186b9e` (AEI "SEASON HR/9 GRADE" relabel — shipped during the design mission)
