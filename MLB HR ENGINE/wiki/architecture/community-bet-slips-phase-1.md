# Community Bet Slips — Phase 1 backend foundation

Status: implemented in source, not deployed. The operator must run Supabase migration `012_community_bet_slips.sql` manually, then deploy Fly before endpoints are available.

## Boundary

This is a social/capture layer only. It reads frozen `tickets` and `legs` snapshots and writes only `profiles` and `community_posts`. It does not write to MAIN/JIG scoring, probability, tiers, pipeline, slate payloads, or warehouse/calibration data.

## Identity

- `profiles.app_number` is assigned by a PostgreSQL sequence during the `auth.users` signup trigger. The sequence is concurrency-safe and `profiles_app_number_unique` enforces uniqueness.
- A database trigger rejects every later `app_number` update. The API exposes no mutation route for it.
- `profiles.username` is editable only by its owner through `PATCH /api/profile/username`; the database enforces case-insensitive uniqueness.
- Public feed grouping uses immutable `community_posts.user_id` internally. The response exposes only `username` and permanent `app_number`, never email or auth user ID.

## Community publication

`community_posts` is a separate one-to-one publication record for a ticket. This keeps public attribution and publication time separate from ticket capture/settlement. `POST /api/community/posts` requires a JWT, verifies ticket ownership, and requires a completed/deployed ticket. `GET /api/community/posts` also requires a JWT and returns all posts grouped by stable identity.

## Phase 2 prerequisite

Run the migration in the Supabase Dashboard SQL editor, verify new signups receive consecutive app numbers, then deploy Fly. Frontend Community room/navigation work is explicitly deferred to Phase 2.
