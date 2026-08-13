---
date: 2026-08-11
agent: Claude Code
task: Community Bet Slips Phase 2 — Room UI
commit: 5c10a9d
---

## Summary

Built the full Community room UI on top of the Phase 1 backend foundation. All read access is now public (no auth); write actions (post, username edit) remain JWT-gated.

## Changes

### Backend (`mlb_hr_engine_v4/api/main.py`)
- `GET /api/community/posts` — removed `require_auth` dependency and the `_profile_for_user` profile-gate call. Now open read. Returns username + app_number only; never email or user_id.
- `POST /api/community/posts` and `PATCH /api/profile/username` unchanged — still JWT-gated.

### Frontend

| File | Change |
|------|--------|
| `0ead2d7a-98fd-4c05-9412-e8c9b12b1861.js` | Added `community` entry to ENGINES: icon=users, color=#9b59f5, expandable, subs=[Bet Slips, Profile] |
| `cfdd4178-a139-4f84-b282-b84f76971c49.js` | Stage routes `community/betSlips` → CommunityBoard, `community/profile` → CommunityProfile |
| `community-board.js` (new) | CommunityBoard + CommunityProfile + CommUserBox + CommSlipCard |
| `ticket-command.js` | Community post banner after submit done; username prompt (skippable); no more auto-close |
| `a6cd8ef6-2b53-4016-a340-66b69a8928bd.js` | Added community to mobile bottomNav |
| `index.html` | CSS for comm-board, comm-profile, tcs-comm-banner; script tag for community-board.js |

## Architecture invariants upheld
- No email or auth user_id ever returned in API responses or rendered in UI
- Grouping keyed on stable app_number (rename-safe)
- No scoring/pipeline/MAIN/JIG surface touched
- Community = social layer only

## Validation checklist
- [ ] Logged-out: Community nav visible, board renders, hover username shows #NNNN, no Post action
- [ ] Logged-in: Post to Community button after slip submit; username prompt (skippable); profile edit
- [ ] Profile: app_number read-only, username editable, uniqueness enforced (409 shown as error)
- [ ] Board: per-user boxes by stable app_number; rename keeps box intact
- [ ] Regression: MAIN/JIG/EV/SHARE/filters intact

## Deploy
- Fly.io: needs deploy for `GET /api/community/posts` read-gate change — NOT done, operator to execute
- Vercel: auto-deploy from push — frontend changes live on next build
