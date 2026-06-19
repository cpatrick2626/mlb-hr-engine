# Session: Supabase Gap Recovery Audit — Jun 1–17
**Date:** 2026-06-18
**Agent:** Claude Code (ROOM 08 — RUNTIME & STABILITY COMMAND)
**Task:** READ-ONLY Supabase audit. Query picks + pipeline_runs for Jun 1–17. Classify recoverability.

---

## A. Picks Table — Row Counts Jun 1–17

**Result: ZERO rows for any date Jun 1–17.**

The `picks` table contains data only for three May dates:

| Date | qualified=True | qualified=False | source_tab | confidence_tier | logged_at |
|------|---------------|-----------------|------------|-----------------|-----------|
| 2026-05-13 | 3 | 378 | Engine | None | 2026-06-16 |
| 2026-05-15 | 0 | 385 | Engine | None | 2026-06-16 |
| 2026-05-17 | 10 | 224 | Engine | None | 2026-06-16 |

**Critical observations:**
- All three backfill dates were `logged_at: 2026-06-16` — manually inserted on Jun 16
- `source_tab='Engine'` (NOT 'cron') — these did NOT come from the cron write path
- `confidence_tier=None` on all rows — pre-tier schema
- `qualified=False` rows on May 15/17 have `ev_pct=0.0`, `bet_dollars=10.0` — test/debug artifacts, not real deployed picks
- **No deployed-state indicator in picks schema** (no `deployed`, `fd_deployed`, `slip` columns)

## B. Picks Table Schema — Full Column List

```
id, date, player_id, player_name, team, opponent, pitcher, lineup_spot,
model_prob_pct, market_prob_pct, ev_pct, edge_pct, american_odds, bet_dollars,
barrel_pct, xslg, park_factor, pitcher_factor, confidence_tier, qualified,
filter_reasons, source_tab, hr_result, profit_loss,
opening_american, opening_no_vig_pct, closing_american, closing_no_vig_pct,
clv_pp, clv_pct_rel, beats_close, engine_version, logged_at
```

**Settlement fields present:** `hr_result`, `profit_loss`, `clv_pp`, `clv_pct_rel`, `beats_close` — same settlement layer as pick_tracker.csv.

**Deployed-state indicator: ABSENT.** Schema has NO `deployed`, `fd_deployed`, `slip`, or ticket-level column. Same fundamental limitation as local pick_tracker.csv — cannot distinguish engine-qualified from operator-deployed.

## C. Pipeline_Runs Table — Jun 1–17

**ALL pipeline_runs dates in system:**

| Date | qualified | notes |
|------|-----------|-------|
| 2026-06-13 | 0 | n_with_odds=66, but 0 cleared filters |
| 2026-06-14 | 4 | full ranked payload present |
| 2026-06-15 | 7 | full ranked payload present |
| 2026-06-16 | 10 | full ranked payload present |
| 2026-06-17 | 0 | n_with_odds=0 — no odds data that day |
| 2026-06-18 | 2 | today |

**Jun 1–12: NO pipeline_runs rows.** Cron did not run or results were not stored. Permanently lost.

### Jun 14 Qualified Picks (from pipeline_runs payload)

| Player | Team | Tier | EV% | Edge% | Bet$ | Odds | Pitcher |
|--------|------|------|-----|-------|------|------|---------|
| Jake Burger | TEX | A | 29.85 | 5.38 | $12.67 | +600 | Connelly Early |
| Wyatt Langford | TEX | A | 28.77 | 5.42 | $12.87 | +950 | Connelly Early |
| Josh Jung | TEX | A | 28.80 | 5.66 | $13.59 | +1050 | Connelly Early |
| Kyle Higashioka | TEX | B | 25.63 | 3.96 | $8.54 | +750 | Connelly Early |

### Jun 15 Qualified Picks (from pipeline_runs payload)

| Player | Team | Tier | EV% | Edge% | Bet$ | Odds | Pitcher |
|--------|------|------|-----|-------|------|------|---------|
| Juan Soto | NYM | A | 27.89 | 6.49 | $19.92 | +350 | Chase Burns |
| Marcus Semien | NYM | A | 29.78 | 5.89 | $14.18 | +650 | Chase Burns |
| Mike Trout | LAA | B | 16.32 | 2.92 | $9.72 | +420 | Ryne Nelson |
| Zach Neto | LAA | B | 13.29 | 3.39 | $7.22 | +460 | Ryne Nelson |
| Joc Pederson | TEX | B | 17.30 | 3.28 | $6.65 | +650 | Mike Paredes |
| Wade Meckler | LAA | B | 22.93 | 3.26 | $6.74 | +850 | Ryne Nelson |
| Josh Jung | TEX | B | 28.80 | 4.36 | $10.03 | +1050 | Mike Paredes |

### Jun 16 Qualified Picks (from pipeline_runs payload)

| Player | Team | Tier | EV% | Edge% | Bet$ | Odds | Pitcher |
|--------|------|------|-----|-------|------|------|---------|
| Joc Pederson | TEX | S | 29.78 | 10.44 | $27.31 | +650 | Zebby Matthews |
| Juan Soto | NYM | A | 27.89 | 6.49 | $19.92 | +350 | Brady Singer |
| Marcus Semien | NYM | A | 29.78 | 5.75 | $13.78 | +650 | Brady Singer |
| Brett Sullivan | COL | A | 28.80 | 5.22 | $12.28 | +900 | Edward Cabrera |
| Josh Jung | TEX | A | 28.80 | 5.41 | $12.91 | +1050 | Zebby Matthews |
| Jared Young | NYM | B | 12.03 | 2.89 | $6.69 | +450 | Brady Singer |
| Carson Benge | NYM | B | 15.22 | 3.33 | $6.62 | +575 | Brady Singer |
| Jake Burger | TEX | B | 11.16 | 2.63 | $0 | +600 | Zebby Matthews |
| Wyatt Langford | TEX | B | 28.77 | 3.85 | $8.53 | +950 | Zebby Matthews |
| Kyle Manzardo | CLE | C | 10.03 | 2.31 | $0 | +650 | Robert Gasser |

## D. Why No Jun Picks in Picks Table?

The cron write path (`cron.py → insert_picks()`) silently failed for ALL Jun 13–18 runs. Evidence:
- `store_picks()` succeeded (pipeline_runs rows exist)
- `insert_picks()` is wrapped in `except Exception as e: print(...)` — non-fatal, swallowed
- Likely schema mismatch or constraint violation (upsert key is `date,player_id,source_tab`)
- The backfill on Jun 16 (`source_tab='Engine'`) was a manual insert, NOT from cron

**This is a separate bug** from the pick_tracker.csv silent failure. Both write paths have been failing independently.

## E. Recoverability Classification

| Date Range | Classification | Detail |
|------------|---------------|--------|
| Jun 1–12 | **EMPTY** | No pipeline_runs, no picks. Permanently unrecoverable. |
| Jun 13 | **EMPTY (qualified=0)** | Engine ran, 0 picks passed filters. Nothing to recover. |
| Jun 14 | **PRESENT-BUT-QUALIFIED-ONLY** | 4 picks in pipeline_runs payload. No deployed indicator. |
| Jun 15 | **PRESENT-BUT-QUALIFIED-ONLY** | 7 picks in pipeline_runs payload. No deployed indicator. |
| Jun 16 | **PRESENT-BUT-QUALIFIED-ONLY** | 10 picks in pipeline_runs payload. No deployed indicator. |
| Jun 17 | **EMPTY (qualified=0)** | No odds data (n_with_odds=0). Nothing to recover. |

**Verdict: PRESENT-BUT-QUALIFIED-ONLY for Jun 14–16. No deployed-state anywhere in Supabase.**

Supabase has the same limitation as local logs — `qualified=True` means engine-cleared the filter, NOT that the operator placed a FD slip. No Supabase table carries ticket-level or deployment-confirmation data.

---

## Open Actions (for operator decision)

1. **Calibration gap decision:** Jun 1–12 permanently lost. Jun 14–16 picks are engine-qualified. Operator must confirm which (if any) were actually deployed to treat as calibration data.
2. **insert_picks bug:** cron write path to `picks` table silently failing. Investigate constraint mismatch. Separate fix.
3. **Deployed-state schema:** `picks` table needs a `fd_deployed` boolean (or equivalent) to prevent this problem going forward. Currently no table in Supabase tracks ticket placement.

---

## Files Touched
- READ ONLY. No writes, no schema changes, no commits.
- Temp query scripts created and deleted.
