# PROJECT_MISSION.md

> AUTHORITATIVE north-star. What MLB HR Engine is, is not, and how we know it's working. Read this first. Portable across all agents.

---

## Mission (the one objective)

Pick the correct HR players and build winning HR tickets. The engine prioritizes **prediction accuracy**, matchup danger, HR probability, barrel quality, pitcher vulnerability, and environment — NOT market value or odds-edge systems.

---

## Priority Hierarchy (in order)

1. **Pick the right HR players** — accuracy of HR prediction is the foundation
2. **Build the strongest tickets** — structure picks into deployable tickets
3. **Use MAIN / JIG / roles** to structure choices
4. **Track results to improve the engine** — the feedback loop
5. **Market/value layer is DEFERRED** — added only if the operator explicitly chooses it later. It must never contaminate primary HR ranking, consistent with existing Primary Ranking Doctrine and `DOCTRINE_RANKING_RULE`.

---

## What MLB HR Engine IS

- An HR-probability prediction + ticket-construction system
- Model-driven: Statcast/Poisson, prediction-first
- Two-lens: MAIN = HR likelihood, JIG = tactical exploitability

---

## What MLB HR Engine IS NOT

- Not a market/odds-edge or EV-maximization system; that layer is deferred and optional
- Not a sportsbook clone, fantasy dashboard, or spreadsheet
- Market data is display-only context, never a ranking input

---

## How We Know It's Working (success criteria)

- **PRIMARY:** engine-ranked picks hit HRs at a rate that beats a naive baseline (e.g., random qualified hitters), measured on DEPLOYED picks
- Prediction accuracy tracked via feedback loop: deployed pick → actual HR outcome → calibration
- **Open question, honest:** "pick the right players" and "build winning tickets" can diverge. Correct picks can still lose inside multi-leg parlays. Ticket structure — leg count, role mix — must be evaluated by results, not assumed. This is what priority #4 exists to answer.

---

## Known Reality (as of 2026-06-20)

- The feedback loop was historically non-functional because capture was broken; now being rebuilt through Ticket/Data Capture. Calibration deferred because N=4.
- Deployed bet history to date: net negative; per-leg HR hit rate approximately 18%.
- Whether the engine has true edge is **UNRESOLVED** pending real deployed-pick calibration. Do not claim edge until the data shows it.

---

## Non-Negotiable Invariants

Link to existing doctrine — do not restate here.

| Invariant | Authoritative source |
|-----------|---------------------|
| MAIN / JIG / HVY separation | [`AGENTS.md`](AGENTS.md), [`MLB HR ENGINE/wiki/doctrine/main-jig-separation.md`](MLB%20HR%20ENGINE/wiki/doctrine/main-jig-separation.md) |
| `model_tier_rank` = pure HR probability; market never contaminates rank | `DOCTRINE_RANKING_RULE` in `AGENTS.md`, Primary Ranking Doctrine |
| `config.py` = source of truth for parameters | [`CLAUDE.md §6`](CLAUDE.md) |
| `pipeline.py` = canonical assembly entrypoint | [`CLAUDE.md §9`](CLAUDE.md) |
| Operational discipline | [`LOOPS.md`](LOOPS.md) |
| Repo doctrine is authoritative; agent skills are secondary | [`CLAUDE.md`](CLAUDE.md) |

---

## Cross-References

- [`AGENTS.md`](AGENTS.md) — MAIN/JIG/HVY doctrine, pitch-mix integrity, scoring rules
- [`LOOPS.md`](LOOPS.md) — operational discipline and loop hygiene
- [`CLAUDE.md`](CLAUDE.md) — behavioral guidelines, module map, invariants
- [`MLB HR ENGINE/wiki/doctrine/feedback-loop-architecture.md`](MLB%20HR%20ENGINE/wiki/doctrine/feedback-loop-architecture.md) — feedback loop design
- [`MLB HR ENGINE/wiki/projects/ticket-data-capture-phase1-architecture.md`](MLB%20HR%20ENGINE/wiki/projects/ticket-data-capture-phase1-architecture.md) — ticket capture phase 1
- Calibration deferral: noted above under Known Reality (N=4; no threshold changes until n≥200 settled real picks per `CLAUDE.md §13`)
