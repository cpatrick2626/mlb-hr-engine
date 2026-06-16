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

---

## Key Data Facts

- **Re-queryable:** raw baseball history (pitch-level, splits, game logs, H2H, bullpen) available from Savant / MLB API back to 2015. **Not use-it-or-lose-it.** No warehouse needed.
- **Use-it-or-lose-it (now captured):**
  - Daily predictions → `full_slate_log.csv` (cloud, Fly volume)
  - Closing odds → CLV capture (cloud, GitHub Actions)
  - Settlement → `picks_log.csv` (cloud, GitHub Actions)
