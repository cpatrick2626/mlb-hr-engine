-- Migration 004: document live Phase 2 change — tickets.user_id
--
-- user_id was added live during Phase 2 (require_auth stamping in add_leg).
-- This migration makes the schema reproducible from scratch via supabase db push.
-- Idempotent: ADD COLUMN IF NOT EXISTS is safe to re-run.

ALTER TABLE tickets ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);
