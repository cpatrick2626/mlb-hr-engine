-- Migration 007: per-user TCC build persistence
--
-- WRITE-SEPARATE from engine/scoring tables. MAIN and JIG filter state stays
-- in separate JSONB columns and no engine table is referenced.

CREATE TABLE IF NOT EXISTS tcc_builds (
  build_id       uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid         REFERENCES auth.users(id),
  name           text,
  main_filters   jsonb,
  jig_filters    jsonb,
  schema_version int,
  created_at     timestamptz  DEFAULT now(),
  updated_at     timestamptz  DEFAULT now(),
  UNIQUE (user_id, name)
);

-- FastAPI uses the service-role key and enforces JWT ownership. Keep direct
-- anon/authenticated table access closed, matching the migration 003 pattern.
ALTER TABLE tcc_builds ENABLE ROW LEVEL SECURITY;
