# Feature Backlog

> Every feature must answer: **does this improve our ability to identify HR opportunities?** If no, challenge it.

---

## Priority 0 — Validation First (Real #1)

Before anything else matters:

- Capture loop **DONE + cloud-native** (commits `5bb17b4`, `0e115dc`).
- Accumulate data. Re-run calibration monthly.
- Target: **2,000+ settled picks** before acting on any calibration or threshold findings.
- Nothing downstream is trustworthy until the engine is validated.

See [[2026-06-15-validation-and-capture-loop]] for calibration audit findings and capture architecture.

---

## Done / In Production

| Item | Status | Notes |
|------|--------|-------|
| Agent layer — Explainability v1 | LIVE | Template-grounded tier/role badge tooltips |
| Governance agents (advisory, etc.) | DESIGNED | Design doc in vault; not yet built |
| Ticket roles (PRIME/EXPLOSIVE/ADVANTAGE/WILDCARD) | LIVE | Both boards; see [[ticket-roles]] |
| Pitch Mix — real data | LIVE | De-fabricated 2026-06-15; see [[design-pitch-mix-analysis]] |
| HR Threat Gauge — radial (0.29 ceiling) | LIVE | Pie replaced; see [[2026-06-15-roles-pitchmix-gauge-session]] |
| "All means all" | VERIFIED | Full Slate shows ~all players; only incidental profile-error drops (minor observability cleanup possible, not urgent) |
| Strategy Rail honesty remediation | LIVE | `77f8354`: removed fabricated HR ENV SCORE, relabeled heuristics, stopped fabricated rail score capture |

---

## Build-Worthy Later

Features worth building — but only after validation baseline is healthy:

| Feature | Why It Qualifies |
|---------|-----------------|
| Momentum / recent-form layer | Real signal if properly weighted; needs validated baseline to test against |
| Pitch Mix expansion (fastball/breaking/offspeed exploit) | Extends existing real-data modal; high ceiling |
| Ranking transparency ("why A > B") | Pairs with Explainability Agent; helps operator trust rankings |
| Design / architecture / product doctrine docs | Infrastructure, not product — low urgency |

---

## Parked (Heavy / Downstream of Validation + Data)

Build only after engine is validated AND sample is healthy:

- Batter-vs-pitcher simulation engine
- Bullpen intelligence
- Pitcher mistake DB
- Batter attack DB
- Fatigue / pitch-count modeling
- User-customizable dashboards

---

## Considerations (No Decision Yet)

| Item | Note |
|------|------|
| Platform independence / portability audit | Fly + Claude-workflow + Savant deps — assess after validation phase |
| Domain governance agents (advisory) | Later; already designed in agent doc |
| External model benchmarking | Log THE BAT X HR projections vs ours for ~30d — but **only after our own calibration sample is healthy**. "Different" ≠ "better"; outcomes + closing line are the real benchmarks |

### Cross-project capability awareness (2026-08-13)

These are external production/support capabilities, not MLB scoring features. Mission Control OS owns governance, approvals, Result Cards, and worker routing; Build Intelligence Atlas / AI Capability Foundry own capability metadata and qualification; Hermes owns scheduled execution. MLB HR ENGINE remains the owner of its data, formulas, payloads, UX, and production truth.

| Capability | MLB use | Dependencies | Risks / protected boundary | Next action |
|---|---|---|---|---|
| Mission Control cloud worker lane | Bounded docs, research, validation, or media tasks from an immutable repository snapshot | Accepted Mission Control `WorkerAdapter` contract and a cloud-capable provider | Cloud cannot see local-only/uncommitted state; never auto-commit/push/upload; no scoring, calibration, ranking, filter, payload, `config.py`, or `pipeline.py` authority | No MLB implementation now; wait for the simulated Mission Control contract to pass |
| Evidence/Result Card + security review | One receipt for objective/actions/files/diff/tests/risks/git/deploy state; read-only-first threat review | Mission Control Result Card and security-worker contracts | Findings are advisory; operator approval before any patch/deploy; MLB acceptance and production proof remain separate | Adopt only through a future read-only pilot against an explicitly authorized snapshot |
| Remotion motion graphics | Deterministic daily recap/shareable cards from already-approved, immutable slate/ticket/result data | Isolated template project, asset/license review, approved input contract, Foundry qualification | **Display/media only**; must not calculate or alter `model_prob`, EV, tiers, rank, JIG/HVY, settlement, or payloads. Remotion uses a custom source-available license and is free only for eligible users/organizations | Park until validation priorities are healthy; then write one docs-only storyboard and input manifest before any install |
| Sites | Interactive research report or disposable capability dashboard | Approved non-sensitive source snapshot and freshness label | Prototype/report only; never migrate the established MLB app, replace Vercel/Fly, or become production truth | Use only for a separately approved short-lived report |

No runtime code, package, provider, scheduler, formula, scoring path, or deployment state was changed for this awareness update.

---

## Strategy Section (added 2026-07-06)

Strategy spec (`wiki/roadmap/strategy-section-spec.md`) is written and gate-ready. §9 contains seven operator decisions that are currently un-gated. Recommended sequencing:

| Priority | Item | Reason |
|----------|------|--------|
| 1st | Authorize snapshot-wiring in isolation | History clock is unrecoverable — delay kills calibration audit trail permanently |
| Done | Rail remediation | Shipped in `77f8354`; HR ENV SCORE removed and remaining non-authoritative rail groupings tagged HEURISTIC |
| Next gate | Strategy-room UI + protected Stage routing branch | Snapshot-wiring + rail remediation have shipped; still requires separate protected Stage routing authorization |

Strategy-room UI or routing branch still requires separate protected authorization before implementation.

---

## UX Integrity Backlog (added 2026-07-06)

| Item | Priority | Notes |
|------|----------|-------|
| FSM scope-labeling audit | MEDIUM | Walk every FSM_COLS entry under pitch-mix ON/OFF: which columns rescope to vs-this-pitcher, which stay season-wide, confirm each is labeled to its scope. Confirm hrfb / hrpa / iso / etc. Systemic fix for four-incident scope-collision pattern (see `FULL_SLATE_UX_DOCTRINE.md §12`). |

---

## Key Data Facts

- **Re-queryable:** raw baseball history (pitch-level, splits, game logs, H2H, bullpen) available from Savant / MLB API back to 2015. **Not use-it-or-lose-it.** No warehouse needed.
- **Use-it-or-lose-it (now captured):**
  - Daily predictions → `full_slate_log.csv` (cloud, Fly volume)
  - Closing odds → CLV capture (cloud, GitHub Actions)
  - Settlement → `picks_log.csv` (cloud, GitHub Actions)
