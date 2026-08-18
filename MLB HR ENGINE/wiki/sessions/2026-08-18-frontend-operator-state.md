# Frontend operator state

Status: shipped on `main`.

## Odds-pending banner

`OddsPendingBanner` is operator-disabled in `frontend/assets/js/a6cd8ef6-2b53-4016-a340-66b69a8928bd.js`. The component returns `null` immediately, so the banner is hidden. Its implementation remains in place; remove the single early return to re-enable it. This is frontend display behavior only and does not change odds collection, scoring, ranking, or API contracts. Shipped in commit `5d31593`.

## Home-PC Graphify flag

Graphify is installed and maintained only on the home PC. It is gitignored and cannot be refreshed from the work laptop. On the home PC, run:

```powershell
graphify update mlb_hr_engine_v4
```

The refresh is required because `/api/live-state/{game_pk}` and `get_live_game_state()` were added to the backend in Phase 1. Until that home-PC update runs, treat the Graphify view of the backend API as stale.
