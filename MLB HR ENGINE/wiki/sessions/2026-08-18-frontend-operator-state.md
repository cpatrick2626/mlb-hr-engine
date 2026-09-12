# Frontend operator state

Status: shipped on `main`.

## Odds-pending banner

`OddsPendingBanner` is operator-disabled in `frontend/assets/js/a6cd8ef6-2b53-4016-a340-66b69a8928bd.js`. The component returns `null` immediately, so the banner is hidden. Its implementation remains in place; remove the single early return to re-enable it. This is frontend display behavior only and does not change odds collection, scoring, ranking, or API contracts. Shipped in commit `5d31593`.

## Home-PC Graphify state

Graphify is installed and maintained only on the home PC. It is gitignored and cannot be refreshed from the work laptop. On the home PC, run:

```powershell
graphify update mlb_hr_engine_v4
```

The required refresh completed on 2026-08-18. The graph is built from `d71a2ad` and contains 2,564 nodes, 4,784 edges, and 130 communities. It includes `/api/live-state/{game_pk}` and `get_live_game_state()`.

That is historical state for the 2026-08-18 snapshot. As of 2026-09-12, the primary graph is STALE against current `main`; inspect source directly and do not regenerate without explicit operator authorization.

Because `graphify-out/` is gitignored, this status applies only to the home-PC checkout. Re-run the command after future backend/API/pipeline/schema changes.
