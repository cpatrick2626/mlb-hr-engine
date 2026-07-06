# Operator Pick Workflow — Strategy Doctrine

Date captured: 2026-07-06
Source: Operator (Kylar), verbatim session description
Status: SEED DOC — captured as-is; Fable 5 Strategy-section design mission will formalize this into the Strategy rail.

---

## Overview

The operator places **2× $10 bets per day** — one MAIN pick ticket, one JIG pick ticket — placed in the morning so the full day's slate is available. Each ticket draws its top players from a funnel, then fills role-based slots.

---

## Morning Funnel — First 4 Picks (MAIN, then JIG)

The same funnel applies to both MAIN and JIG. For each pick:

1. **Player View** → sort by highest TM (True Matchup score).
2. Check the **player dot color** → GREEN dot required to proceed.
3. Open **AEI (Arsenal Edge Intel)** → confirm data loads (note: AEI can be slow / TBD on load times).
4. Check **pitcher rating** in AEI.
   - **FLAG:** The operator currently bypasses pitchers labeled "TOUGH." This is the pick-bypass gate that the AEI relabel targets. A pitcher rated TOUGH on their season aggregate can still be an excellent specific matchup for a given batter — the arsenal edge reads the specific matchup, not the general season grade. Wording was causing good picks to be faded.
5. If pitcher rating passes → review in order:
   - **H2H** (head-to-head history)
   - **Pitcher's most-thrown pitches** — operator explicitly hunts this
   - **Batter's HR-by-pitch-type**
6. If all checks pass → add to ticket.

**JIG variation:** Same funnel; operator tries to pick all-different players from MAIN picks.

---

## Role-Based Picks (after top 4)

After the first 4 picks from the funnel, role slots are filled in this order:

- **PRIME** — mostly $1, occasionally $5–$10.
  - If all top PRIME-labeled players are already taken in the first 8 picks: leave PRIME unmarked and select a top APEX/ELITE player with high TM / high HR% probability and **no role label** as the PRIME selection.
- **EXPLOSIVE** — same TM → dot → AEI funnel.
- **ADVANTAGE** — same funnel.
- **WILDCARD** — same funnel.

---

## Cross-Ticket Rule

Operator **tries to pick all-different players across all tickets** (MAIN + JIG combined).

**Operator flag:** This is possibly suboptimal. If the same player is the highest-EV pick on both MAIN and JIG, avoiding them on one ticket may reduce expected value. Formalization of this rule is deferred to the Strategy-section design mission.

---

## Data Reliance

Operator relies **100% on displayed board data**. No external research or off-board sources are used in the pick workflow. Implications:

- Every signal that affects picks must be clearly labeled to its scope (season-grade vs matchup-specific vs batter-tier) or it creates pick gates (see AEI TOUGH bypass, above).
- Data load failures (slow AEI, null matchup) directly cause picks to be skipped or degraded.
- The board's visual language (dot color, tier label, role label) is a direct input to pick decisions — palette collisions and ambiguous labels have immediate betting consequences.

---

## Open Questions / Strategy Design Seeds

These are unsettled questions the operator flagged as wanting to explore:

1. **Is all-different-players the right rule?** Or should the best pick be doubled across tickets when EV is highest?
2. **How to best exploit all available data to build winning tickets?** Operator wants to formalize this — starting point for Fable 5 Strategy-section design mission.
3. **AEI TOUGH bypass:** Should the board distinguish season-grade TOUGH from matchup-specific MISMATCH more forcefully in the AEI UI, so the bypass gate disappears naturally?
4. **Role slot optimization:** Are EXPLOSIVE/ADVANTAGE/WILDCARD selections following the same funnel optimal, or should role slots use different filters?

---

## Related Doctrine

- `AGENTS.md` — MAIN/JIG separation; scoring rules
- `MASTER_TCC_DOCTRINE.md` — TCC orchestration; what the operator sees and acts on
- `wiki/doctrine/ticket-roles.md` — PRIME/EXPLOSIVE/ADVANTAGE/WILDCARD role definitions
- `wiki/doctrine/visual-design-doctrine.md` — dot color, tier label, AEI panel design
- `FULL_SLATE_UX_DOCTRINE.md` — palette collision rule; signal-scope labeling rule
- `wiki/doctrine/true-matchup-score.md` — TM score (0–100 composite)
