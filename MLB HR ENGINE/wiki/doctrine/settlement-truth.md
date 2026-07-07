# Settlement Truth — Verification Doctrine

Status: DOCTRINE — earned during the Phase S2 settlement arc (2026-07-06 → 2026-07-07). Governs any process that writes or reasons about settled outcomes (`legs.hr_result` and anything downstream of it: ledger, calibration, threshold decisions).

---

## 1. Anchor settlement truth to EXTERNAL, unfalsifiable facts

Settlement conclusions must be anchored to facts the system cannot have corrupted itself:

- the **box score** (MLB Stats API, keyed by MLBAM person ID),
- the **starting pitcher** on the proposed date (pitcher-anchor cross-check),
- **`engine_generated_at`** (the slate the operator was actually looking at).

Never the wall clock. Never internal consistency between our own columns.

This arc proved the rule empirically. Every wrong conclusion came from reasoning about internal state:

- the suspected "resolver bug" was actually a `leg_date` bug (UTC off-by-one at capture time);
- the suspected "void" was that same off-by-one — the player played, on the other date;
- the suspected "bad player_id" was clean — the ID was fine, the date was wrong.

Every correct conclusion came from an external anchor: the box score said who batted, the probable pitcher confirmed which date a leg belonged to, and `engine_generated_at` said which slate the pick was made against. The durable capture fix (commit `761105c`) encodes this: `leg_date`/`tickets.date` derive from `engine_generated_at` in ET; the server clock is a fallback only when that anchor is absent.

## 2. Verify against real data; never trust a self-reported PASS

A settlement path is not correct because its logic traces correctly. It is correct when its output matches reality row-by-row.

- **Dry-run + operator hand-check against real box scores comes before any write path exists.** During this arc, the hand-check caught what confident logic-tracing got wrong; the write path (`--commit`) was only built after the dry-run output survived that check (settlement-job-spec §6 gate).
- Agents do not self-judge settlement correctness. "Dry-run ran clean" is a report, not a verdict — the verdict belongs to a comparison against external truth.

## 3. Writes to the calibration source of truth are gated

`hr_result` feeds calibration; a wrong settlement silently poisons it and is worse than no settlement. Therefore every write path follows the gate pattern proven in `api/settle_legs.py`:

- **dry-run is the default mode**; writing requires an explicit `--commit`;
- **first live run is single-date**, verified row-by-row in Supabase before any bulk run;
- **idempotent write-once**: `UPDATE ... WHERE settlement_status = 'pending'` — a settled row can never flip; re-running a commit writes 0 rows;
- **minimal write surface**: exactly three columns (`hr_result`, `settlement_status`, `settled_at`), nothing else, no inserts, no deletes;
- when in doubt, the resolver leaves a leg `pending` and reports it — it never guesses.

## Cross-References

- [[settlement-job-spec]] (`wiki/roadmap/settlement-job-spec.md`) — the shipped resolver design record; §6 is the verification gate this doctrine generalizes
- [[supabase-schema]] (`wiki/architecture/supabase-schema.md`) — `legs` status convention (void keeps `hr_result` NULL), calibration triad, `leg_date` derivation rule
- [[ticket-slip-system]] — slip capture layer feeding settlement
