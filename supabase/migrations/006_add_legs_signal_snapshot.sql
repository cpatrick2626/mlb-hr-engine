-- Migration 006: pick-time signal snapshot on legs (Strategy spec §5, Phase S1-a)
-- Additive only: nullable, no default, no backfill. Existing rows stay NULL.
-- Run in Supabase Dashboard SQL Editor.

ALTER TABLE legs ADD COLUMN IF NOT EXISTS signal_snapshot jsonb;

COMMENT ON COLUMN legs.signal_snapshot IS
  'Pick-time signal state displayed on the adding surface (snapshot_version 1, all fields nullable). Records displayed signals only; never a computed composite. See wiki/roadmap/strategy-section-spec.md §5.';
