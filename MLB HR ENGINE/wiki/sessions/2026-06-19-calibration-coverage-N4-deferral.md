# Calibration Coverage N=4 — Deferral
**Date:** 2026-06-19  
**Status:** DEFERRED — below threshold  
**Owner:** Claude Code (Sonnet 4.6)

---

## Finding

Deployed-pick calibration attempted against engine predictions.  
Calibratable N = 4 unique player-dates (6 leg appearances). Far below the n<200 threshold (CLAUDE.md rule). NOT directional, NOT conclusive — no calibration artifact built.

---

## Data

- Deployed settled legs: 1,417 (254 hit / 1,163 miss), May 12–Jun 18.
- Engine pipeline_runs payloads exist only Jun 13–18; non-empty ranked on 4 dates (Jun 14/15/16/18); 23 total ranked entries.
- Only 6 deployed legs (4 player-dates) matched an engine ranked entry.

---

## Two Compounding Gaps

**Gap 1 — Engine history sparse.**  
No pipeline_runs before Jun 13, so all May 12–Jun 12 deployed legs (1,373) have nothing to match. This is the dominant gap.

**Gap 2 — Engine ranks narrowly vs deployed volume.**  
On engine dates, engine ranked ~4–10 players/day. Operator deployed ~37/day. ~138 deployed legs on those dates were never ranked by the engine — operator deployed well beyond engine recommendations.

---

## Behavioral Observation (not a finding — flagged for later)

On dates with engine output, operator deployed ~37 players vs ~8 ranked. ~80% of deployments are picks the engine did not surface. Improving engine calibration only affects the ~20% the engine actually ranks.

Worth analyzing separately: results of engine-ranked picks vs operator's off-engine picks. **Deferred.**

---

## Supersedes

This deferral **SUPERSEDES** the earlier "no demonstrable edge" calibration finding, which was computed on qualified-not-deployed picks and is invalid. Do not cite the old finding.

---

## Path Forward

1. `deployed_picks_backfilled.csv` has the OUTCOME side ready (committed via backfill tools).
2. Calibration needs engine prediction history to accumulate. Each forward pipeline run adds ~4–10 matchable points.
3. **Real fix:** build Ticket/Data Capture (live, forward) so future deployments are captured WITH engine snapshot at deploy time — making calibration automatic, not forensic.
4. **Re-run calibration target:** late July 2026 (N approaching threshold), ASSUMING live capture is operational to feed it.

---

## Cross-References

- `wiki/projects/ticket-data-capture-phase1-architecture.md` — capture layer that fixes this going forward
- `wiki/doctrine/feedback-loop-architecture.md` — feedback loop context
- `wiki/sessions/2026-06-19-bet-history-parser-backfill.md` — parser + backfill session (outcome side ready)
