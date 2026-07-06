# Session: Matchup Two-Axis Fix + Player Dot + AEI Relabel — 2026-07-06

Date: 2026-07-06
Agent: Claude Code (execution)
Owner: Operator (Kylar)
Project: MLB HR ENGINE — MATCHUP / FULL SLATE BOARD / AEI
Risk Class: MEDIUM (pipeline + frontend); LOW (docs)
Phase: Matchup two-axis Phases 1+2 shipped; Phase 3 (Streamlit) deferred
Status: COMPLETE / SHIPPED (pipeline Fly, display Vercel)

## Scope

Four workstreams this session:

1. **Player dot fix** (`db70636`) — dot now shows matchup quality, matching legend polarity.
2. **AEI relabel** (code live, committed under mislabeled message `a186b9e` — see note below) — "PITCHER VULNERABILITY" → "SEASON HR/9 GRADE" + framing caption.
3. **Matchup two-axis spec** (`8c7377d`, reconstructed + code-verified) + **Phase 1** (`7cdcb61`, Fly) — removed inverted DANGER classification; added pitcher_vuln axis.
4. **Matchup two-axis Phase 2** (`252bf41`, Vercel) — display: TARGET green ring/tag/legend, DANGER removed, JIG TARGET pill, latent donut bug fixed.

---

## Commits (chronological, this session)

| Commit | Summary |
|--------|---------|
| `db70636` | fix(fsm): player dot shows matchup quality (FSM_MATCHUP), matching legend polarity |
| `a186b9e` | **[MISLABELED — see note]** commit message says "matchup spec" but diff is the AEI relabel |
| `8c7377d` | docs(roadmap): matchup two-axis spec (reconstructed + code-verified) |
| `7cdcb61` | fix(pipeline): matchup-quality two-axis Phase 1 — DANGER removed, pitcherVuln axis added |
| `252bf41` | feat(fsm): matchup two-axis Phase 2 — TARGET display (green ring/tag/legend), JIG pill, donut fix |

---

## 1. Player Dot Fix (`db70636`)

**Bug:** Player dots were colored by team-color with tier-color fallback, where red = APEX (best HR threat). The matchup quality legend also used red = bad-for-hitter. Both palettes lived on the same board, causing red to mean the opposite thing in two adjacent visual contexts. A player in an excellent matchup could show a red dot (APEX tier), contradicting the legend that says red = bad matchup.

**Fix:** Dot color now reads `row.quality` / `FSM_MATCHUP` directly, matching the legend polarity. Null matchup → neutral grey.

**Applies to:** MAIN + JIG boards.

**Verified:** Green dots visible on good-matchup players, consistent with legend.

**Doctrine note:** See `FULL_SLATE_UX_DOCTRINE.md § Palette Collision Rule` — this was the canonical incident that prompted that rule.

---

## 2. AEI Relabel — "PITCHER VULNERABILITY" → "SEASON HR/9 GRADE"

**Code is live and correct.** The change relabels the Arsenal Edge Intel header and adds a framing caption.

**New label:** `SEASON HR/9 GRADE`
**New caption:** `SEASON GRADE VS AVG BATTER · ARSENAL EDGE READS THIS MATCHUP`

**Motivation:** The old label "PITCHER VULNERABILITY" created a wording-driven pick gate: operators reading "TOUGH" on a pitcher's season grade were bypassing good picks. A pitcher rated TOUGH on their full-season aggregate can still be a favorable specific matchup for a given batter's arsenal exploitation — which is exactly what the Arsenal Edge (AEI) analysis measures. The relabel separates the season-aggregate grade from the matchup-specific verdict, so operators don't fade a pick based on the wrong signal scope.

### Commit message anomaly — RECORD FOR FUTURE-YOU

`a186b9e` message reads: *"docs(roadmap): matchup-quality two-axis fix spec — Fable 5 design"*. The actual diff in this commit is the AEI relabel code change. What happened: a `git add` failed silently; the already-staged AEI relabel change committed under a roadmap-doc message. The code is correct and live. The message is mislabeled. This is not a cherry-pick or revert risk — it is a cosmetic commit-message mismatch only.

---

## 3. Matchup Two-Axis Fix — Spec + Phase 1

### Root cause: inverted DANGER classification

High `pitcher_hr9` (i.e., the pitcher gives up home runs at a high rate) was being labeled as a *worst-matchup* (DANGER). This is backwards — high pitcher_hr9 is favorable for the batter.

### Design decisions ratified

- **DANGER → TARGET:** Label matches AEI wording; avoids collision with PRIME role name.
- **No tier promotion:** pitcher_vuln is a separate axis. Folding it into the batter tier rank formula would triple-count pitcher_hr9 (already feeds `model_prob` via the pipeline).
- **Two-axis model:** Batter tier (ELITE/STRONG/AVG/WEAK) and pitcher vulnerability (TARGET / not-TARGET) are independent dimensions displayed separately.

### Phase 1 (`7cdcb61`) — pipeline, Fly-deployed

- Removed inverted DANGER classification.
- Added `pitcher_vuln` field: `TARGET` when `pitcher_hr9 >= 2.2`, else blank.
- API key: `pitcherVuln` (camelCase, per React convention).
- Batter tiers (ELITE/STRONG/AVG/WEAK) and all scoring math: **unchanged**.
- Regression: **0 changes across 208 real baseline rows** (verified before deploy).
- Live end-to-end after fresh pipeline run: 208 rows both MAIN and JIG, **ZERO DANGER**, `pitcherVuln` present on all rows.

### Phase 2 (`252bf41`) — display, Vercel-deployed

- DANGER removed from all display surfaces.
- TARGET: green ring on player dot, `·TARGET` card tag, legend entry.
- Focus-filter: OR condition (TARGET qualifies even without other elevation flags).
- Latent donut bug fixed: ELITE tier was incorrectly rendering as AVG in donut chart.
- JIG: TARGET pill added.
- Rank boost: **NOT changed** — double-count rule preserved; `pitcher_hr9` already feeds `model_prob`.

---

## 4. Phase 3 — Deferred

Streamlit `app.py` still has DANGER in pie chart and tooltips. Deferred — low priority since React (root `frontend/`) is the live production surface. Needs separate auth session.

---

## Backlog (recorded this session)

| Item | Priority |
|------|----------|
| AEI relabel pass — neutralize TOUGH/VULNERABLE/HR TARGET → neutral HR/9 descriptors; make arsenal MISMATCH verdict the headline, season grade subordinate; fixes pick-bypass gate | HIGH |
| Fable 5 Strategy-section design mission — exploit-data-to-build-winning-tickets (seeded by `operator-pick-workflow.md`) | MEDIUM |
| Phase 3 Streamlit DANGER cleanup (pie/tooltip in `app.py`) | LOW |
| `flyctl` auto-update broken — symlink perm error; fix requires admin shell | MAINTENANCE |
| Dead JIG Builder Steppers (30 of 46 filter fields no onChange/predicate) | DEFERRED |
| UX queue: sticky stats header, stat-in-cell, persistent horizontal scrollbar, TCC-mobile sticky APPLY TO ROOM, mobile drag-reorder columns w/ per-user persistence | DEFERRED |
| Fly health check (no CHECKS on machine) | MAINTENANCE |
| Node 20 deprecation on GH Actions | MAINTENANCE |

---

## Protected Surfaces — No Changes

- `config.py` thresholds: unchanged
- MAIN/JIG separation: preserved
- HVY pitch-mix modifier: display-only, not touched
- Scoring/rank formula: unchanged (rank boost for pitcher_vuln deliberately omitted)
- session_state, cache, routing: not touched
