---
name: ux-command-center
description: "Use for TCC/dashboard UX decisions, operator-facing layout, cinematic/tactical command-center visual hierarchy, Full Slate battlefield surface work, and board degraded-state handling."
---

# /ux-command-center

PURPOSE: Domain lens for operator UX — tactical command-center layout, battlefield hierarchy, operator-facing visual surfaces.

## LENS

This skill is a domain lens, not a loop pointer. Domain UX judgment lives here:

- TCC = cinematic, high-density, intelligence-forward. Operator scans → deploys without friction.
- Visual hierarchy: APEX threats surface first; degraded states (LOADING / PIPELINE PENDING / BOARD OFFLINE) are explicit, never silent.
- Operator reads pick rows; operator does not reconstruct from raw data.
- Full Slate = battlefield surface; card hierarchy (tier → model_prob → JIG signal → market) is fixed unless doctrine changes.
- Claude Design is the canonical visual authority. Do not propose layout changes without explicit operator authorization.
- HVY is display-only on JIG side; it must never influence MAIN tier or model_prob.

## PROCEDURE (review and handoff)

For review-and-handoff flow, see LOOPS.md §8. Do not duplicate here.
