# Local Evidence Register

**Updated:** 2026-09-12
**Purpose:** Index important PC-only or untracked evidence without copying its contents. Preserve local files; this register does not authorize staging, committing, deletion, or movement.

| Item | Classification | State | Purpose / handling | Loss risk | Review or commit decision needed |
|---|---|---|---|---|---|
| `MLB_HR_ENGINE_SYSTEM_INTELLIGENCE_AUDIT_2026-09-11.md` | SUPPORTING EVIDENCE | Untracked | Recent system audit; use as supporting evidence and verify against current source before acting. | High | Yes — review before any later commit. |
| `.MD/MLB_HR_ENGINE_PROJECT_HANDOFF.md` | HISTORICAL | Retained | Prior project handoff and research snapshot. Superseded calibration/parlay/PM claims are marked in-file; retain for provenance. | High | No — included as historical context in this scoped local commit. |
| `MLB HR ENGINE/wiki/sessions/2026-08-18-repository-graphify-obsidian-sync.md` | HISTORICAL | Indexed | Records the August 18 Graphify refresh and repo review. Its fresh status applies only to that snapshot; current Graphify is stale. | Medium | No — included with current freshness correction. |
| `mlb_hr_engine_v4/scripts/analysis/HR_DISTRIBUTION_BY_RANK_2026-09-10.md` | SUPPORTING EVIDENCE | Untracked | September rank-distribution study; retain as research evidence, not scoring authorization. | High | Yes — review before any later commit. |
| `mlb_hr_engine_v4/scripts/analysis/HR_DISTRIBUTION_FULLSEASON_2026-09-10.md` | SUPPORTING EVIDENCE | Untracked | September full-season rank study; retain as research evidence, not scoring authorization. | High | Yes — review before any later commit. |
| `mlb_hr_engine_v4/scripts/analysis/PHASE1_MAIN_REVALIDATION_2026-09-10.md` | SUPPORTING EVIDENCE | Untracked | September MAIN revalidation report; calibration remains frozen pending new evidence and explicit authorization. | High | Yes — review before any later commit. |
| `mlb_hr_engine_v4/scripts/analysis/analyze_live_calibration_output.txt` | GENERATED | Untracked | Analysis output associated with local evaluation; preserve unchanged, but do not treat it as ratification. | Medium | No — generated output; retain locally. |
| `.codex/` | LOCAL TOOLING | Mixed | `.codex/hooks.json` repairs invocation through the existing Git for Windows Bash executable. Other local Codex config/scripts remain untracked. Whether Codex loads this file remains unverified. | High | Hook repair included; review remaining local files separately. |
| `skills-lock.json` | LOCAL TOOLING | Tracked | Contains 42 entries; 24 skill names are absent from the active `.agents/skills/` and `skills/` trees. No active tooling consumer was found. Treat it as a drifted historical install record, not a proven active registry. Left unchanged. | Medium | Yes — decide registry semantics before any future update. |
| `.claude/settings.local.json` | LOCAL TOOLING | Ignored local file | Legacy machine-local settings contain old paths and broad mutating permissions. Not active repo governance; inspected and left unchanged. | Low | No — do not commit or broaden permissions. |
| `.agents/Hermes-Knowledge-20260721.zip` | CROSS-PROJECT CONTAMINATION | Untracked | Archive contains Ronan/Flag Game material. Do not extract, move, delete, or treat as active MLB authority. | Medium | No — preserve as-is; exclude from MLB authority. |
| `MLB HR ENGINE/.obsidian/plugins/vault-intelligence/model-cache.json` | GENERATED | Tracked, modified | Obsidian plugin cache churn. Existing local modification preserved; do not copy its contents into project documentation. | Low | No — generated cache; retain local state. |
| `supabase/.temp/cli-latest` | OPERATIONAL NOISE | Untracked | Local Supabase CLI metadata. Do not publish or copy contents. | Low | No — operational temp file. |
| `supabase/.temp/linked-project.json` | OPERATIONAL NOISE | Untracked | Local Supabase project-link metadata. Do not publish or copy contents. | Medium | No — operational temp file; avoid copying identifiers. |
| `mlb_hr_engine_v4/graphify-out/` | GENERATED | Local generated output; freshness is STALE | Primary Graphify output. Generated locally, non-authoritative while stale; inspect source directly. Do not regenerate under this task. | Medium | No — generated output; no commit decision in this pass. |
| `graphify-out/` | GENERATED | Legacy/ambiguous local output; manifest exists, `graph.json` absent | Secondary output location; not the primary configured Graphify destination. Treat as non-authoritative unless separately verified. | Low | No — leave unchanged. |

## Preservation notes

- No evidence contents or secrets were copied into this register.
- The Hermes ZIP remains an unopened archive; no archive extraction was performed.
- September analysis reports and operational temp files remain untracked and were not staged. The governance reconciliation and hook repair are being handled in a separate scoped local commit.
