# Vault Architecture Audit
_Generated 2026-05-23_

---

## 1. Full Folder Hierarchy

```
mlb-hr-engine-master/                          ← REPO ROOT
├── .agents/skills/                            ← Claude Code plugin skills (caveman, cavecrew, etc.)
├── .claude/                                   ← Claude Code settings.json, settings.local.json
├── .devcontainer/devcontainer.json
├── .github/workflows/
├── .streamlit/secrets.toml.example            ← ROOT-LEVEL streamlit config (separate from v4)
├── docs/                                      ← lowercase — 57 spec/doctrine files
├── Docs/                                      ← TitleCase — 55 spec/doctrine files (DUPLICATE)
├── logs/ops_daily_log.txt
├── reports/                                   ← Mixed: step docs, screenshots, validation txts, logs
├── supabase/                                  ← ORPHAN — no CLAUDE.md reference
├── mlb_hr_engine_v1/                          ← Legacy; used by compare.py --dump-json only
├── mlb_hr_engine_v2/                          ← Legacy; used by compare.py --dump-json only
├── mlb_hr_engine_v3/                          ← Semi-retired
├── mlb_hr_engine_v4/                          ← PRODUCTION (see below)
├── analyze_*.py (12 scripts)                  ← Analysis scripts at root, all import from v4
├── audit_*.py (3 scripts)
├── compare.py, compare_2026_hrs.py
├── test_*.py (5 test scripts)
├── ops_daily.py                               ← Operational scripts at root, all operate on v4
├── monitoring_dashboard.py
├── capture_closing_lines.py
├── optimize_daily.py
├── settle_pick_tracker.py
├── *.txt (10 output files)                    ← Analysis output scattered at root
├── *.png (8 validation screenshots)           ← Screenshots scattered at root
├── streamlit_*.log / streamlit_*.pid          ← 10 process logs + 1 PID at root
├── FULL_SLATE_UX_DOCTRINE.md                  ← Doctrine at root (should be in docs/)
├── MASTER_TCC_DOCTRINE.md
├── PHASE3_REFINEMENT_DOCTRINE.md
├── ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md
├── AGENTS.md
├── ANALYSIS_INDEX.md
├── MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md
├── OPTIMIZATION_RESULTS_FINAL.md
├── OPTIMIZATION_RESULTS_UPDATE1.md
├── OPTIMIZATION_RESULTS_UPDATE2.md
├── OPTIMIZATION_RESULTS_UPDATE3.md
├── OPS_DAILY_SETUP.md
├── OPTIMIZATION_QUICK_START.md
├── CLAUDE.md
├── requirements.txt                           ← DUPLICATE (also exists in each engine version)
├── Dockerfile
├── fly.toml
├── run_ops_daily.bat
├── schedule_task.ps1
├── skills-lock.json
├── fb_pct_raw_data.csv                        ← Data file at root
├── 2026-04-22T02-16_export.csv                ← Data file at root
├── "New Text Document.txt"                    ← STRAY
└── "tore app.py."                             ← STRAY broken filename

mlb_hr_engine_v4/
├── api/                                       ← FastAPI backend (auth, cache, cron, main)
├── assets/banner.png
├── backtest/                                  ← Package: calibration, feature_importance, outcomes, runner
├── backtest.py                                ← CLI entry script (AMBIGUOUS — same name as backtest/ pkg)
├── clients/                                   ← mlb_stats, odds_api, weather, statcast, pitch_mix, arsenal, pull_air, session_utils
├── components/
│   ├── hr/                                    ← DUPLICATE of frontend/components/hr/ (same 3 TSX files)
│   │   ├── hr-threat-card.tsx
│   │   ├── hr-threat-card-header.tsx
│   │   └── hr-threat-card-metrics.tsx
│   └── sub_room_rail.py                       ← Python file inside components/ (mixed language)
├── data/                                      ← park_factors.py, odds_cache.json
├── Docs/
│   ├── 01_SPECS/                              ← architecture, component-rules, product-spec, scoring-engine, ui-system
│   ├── 02_RAW/                                ← daily_matchups, notes, pitch_mix, screenshots, statcast, weather (all empty)
│   ├── 03_LLM_WIKI/
│   │   ├── build-log/TASK-001-build-log.md
│   │   ├── daily/ (empty)
│   │   ├── matchups/ (empty)
│   │   ├── pitchers/ (empty)
│   │   ├── players/ (empty)
│   │   ├── systems/ (empty)
│   │   ├── threat-models/ (empty)
│   │   ├── system_governance/mlb_hr_engine_operating_doctrine.md
│   │   └── tactical_systems/                  ← Barrel_Quality, Confidence_Tiering, Environmental_Leverage,
│   │                                             Hard_Hit_Danger, HR_Threat_Escalation, Market_Inefficiency,
│   │                                             Pitch_Mix_Exploitation, Pitcher_Fatigue (each: doctrine/overview/translation)
│   ├── 04_SYSTEMS/ (empty)
│   ├── 05_MODELS/ (empty)
│   ├── 06_UI/ (empty)
│   ├── 07_OPERATIONS/command-aliases.md
│   ├── 08_TASKS/                              ← TASK-001, TASK-002, TASK-003
│   ├── 09_DECISIONS/TASK-001-threat-card-decisions.md
│   ├── 99_ARCHIVE/ (empty)
│   ├── AGENTS.md
│   ├── MASTER_ROADMAP.md
│   ├── MAIN_JIG_FULL_SLATE_REBUILD_PLAN.md
│   ├── TASK-001-threat-card.md                ← DUPLICATE of Docs/08_TASKS/TASK-001-threat-card.md
│   └── *_doctrine_v1.md (7 loose doctrine files at Docs/ root, not in numbered dirs)
├── engine/                                    ← calibration, ev, filters, market, probability, sizing, trust, vig
├── frontend/                                  ← Next.js / Tailwind app
│   ├── app/                                   ← globals.css, layout.tsx, page.tsx
│   ├── components/
│   │   ├── dashboard/                         ← command-header, escalation-feed, matchup-intel, panel, pitcher-vulnerability, threat-rankings
│   │   └── hr/                                ← DUPLICATE of components/hr/ above (same 3 TSX files)
│   ├── next.config.mjs, tailwind.config.ts, tsconfig.json, package.json
│   └── node_modules/, .next/                  ← Build artifacts (should be gitignored)
├── output/                                    ← display, parlay, ranker
├── pipeline.py
├── portfolio/                                 ← correlation, exposure, metrics, optimizer, sizing
├── strategies/                                ← arbitrage, correlation, hedge, stacks, staking, value_decay (ORPHAN?)
├── tracking/                                  ← pick_tracker, pnl, clv, sheets, drift_monitor, data_integrity,
│                                                 line_snapshots, line_movement, auto_learn, adaptive_weights,
│                                                 notify, strategy_log + CSV data files
├── tests/                                     ← test_pull_air_pct.py, test_weather_guard.py (2 files only)
├── investigation_state.py
├── nav_state.py
├── navigation_continuity.py
├── filter_controls.py
├── strategies_ui.py
├── streamlit_8505.*.log                       ← Process logs inside v4 (also exist at root)
├── playwright_*.png                           ← Screenshots inside v4
└── "ChatGPT Image Apr 22, 2026, 08_09_52 AM.png"  ← Stray image
```

---

## 2. Duplicate Taxonomy Analysis

| # | Duplicate | Location A | Location B | Severity |
|---|-----------|-----------|-----------|---------|
| D1 | Entire doc library | `docs/` (root, lowercase) | `Docs/` (root, TitleCase) | **CRITICAL** — ~55 identical files in two dirs |
| D2 | HR threat card TSX | `mlb_hr_engine_v4/components/hr/*.tsx` (3 files) | `mlb_hr_engine_v4/frontend/components/hr/*.tsx` (3 files) | **CRITICAL** — exact duplicates |
| D3 | TASK-001 threat card | `mlb_hr_engine_v4/Docs/TASK-001-threat-card.md` | `mlb_hr_engine_v4/Docs/08_TASKS/TASK-001-threat-card.md` | HIGH |
| D4 | Sizing module | `mlb_hr_engine_v4/engine/sizing.py` (core Kelly) | `mlb_hr_engine_v4/portfolio/sizing.py` (strategy backtest) | MEDIUM — different purpose but same namespace concept |
| D5 | Correlation module | `mlb_hr_engine_v4/strategies/correlation.py` | `mlb_hr_engine_v4/portfolio/correlation.py` | HIGH — likely different impls for same concept |
| D6 | Backtest entry | `mlb_hr_engine_v4/backtest.py` (CLI script) | `mlb_hr_engine_v4/backtest/runner.py` (package) | MEDIUM — ambiguous naming |
| D7 | requirements.txt | Root `requirements.txt` | `mlb_hr_engine_v4/requirements.txt` | MEDIUM — divergence risk |
| D8 | Streamlit logs | `mlb_hr_engine_v4/streamlit_8505.*.log` | Root `streamlit_*.log` (8505, step3, gate2, gate3, etc.) | LOW — noise |
| D9 | AGENTS.md | Root `AGENTS.md` | `mlb_hr_engine_v4/Docs/AGENTS.md` | LOW |

---

## 3. Conflicting Structure Analysis

| # | Conflict | Description |
|---|---------|-------------|
| C1 | **doc casing war** | `docs/` and `Docs/` coexist at root. On Windows (case-insensitive FS) these may resolve to same dir depending on tool. Git tracks both as distinct paths. One was created as copy or rename-in-progress. |
| C2 | **TSX components split across two trees** | `v4/components/hr/` (outside frontend) suggests pre-frontend draft or copy left behind. `v4/frontend/components/hr/` is the active Next.js location. Both have identical content — only frontend version is wired. |
| C3 | **Python mixed into components/** | `v4/components/sub_room_rail.py` (Python Streamlit module) sits inside a `components/` dir with TSX files. Language boundary violation. |
| C4 | **Analysis scripts at root operate on v4 internals** | All 12 `analyze_*.py` scripts import from `mlb_hr_engine_v4.*`. They belong inside v4 but were placed at root for CLI convenience. Creates a dangling import relationship. |
| C5 | **Operations scripts at root, data at v4** | `ops_daily.py`, `settle_pick_tracker.py`, etc. read/write `v4/tracking/*.csv`. Scripts are detached from the module they operate on. |
| C6 | **Doctrine files in three locations** | Root (`MASTER_TCC_DOCTRINE.md`, etc.), `docs/`/`Docs/` (snake_case spec files), and `v4/Docs/` (numbered + loose). No single canonical home. |
| C7 | **reports/ is a junk drawer** | Contains: `.md` step execution notes, `.png` screenshots, `.txt` validation reports, `.log` Streamlit process logs, `.png` JIG diagnostic images — no taxonomy. |
| C8 | **tracking/ contains both code and live data** | Python modules and production CSVs (`pick_tracker.csv`, `clv_log.csv`, `line_snapshots.csv`, `picks_log.csv`) coexist. CSVs should be in `data/` or excluded from repo. |
| C9 | **strategies/ module not wired** | `v4/strategies/` (6 modules) appears disconnected from `pipeline.py` and `app.py`. `portfolio/` module handles similar concerns and IS wired. |
| C10 | **api/ backend exists alongside Streamlit app** | `v4/api/` (FastAPI) and `v4/app.py` (Streamlit) serve overlapping purposes. Only Streamlit is documented as production. FastAPI wiring unclear. |

---

## 4. Recommended Canonical Architecture

```
mlb-hr-engine-master/
├── CLAUDE.md
├── AGENTS.md
├── README.md
├── requirements.txt                    ← Root only; versioned engines use relative path or this one
├── Dockerfile
├── fly.toml
├── compare.py                          ← Legitimate root: cross-version tool
├── docs/                               ← SINGLE canonical doc root (lowercase, all content merged)
│   ├── specs/                          ← Product/architecture specs
│   ├── doctrines/                      ← All doctrine files (flat, snake_case, no ALLCAPS)
│   ├── tactical_systems/               ← LLM Wiki tactical system docs
│   ├── operations/                     ← Ops playbooks, daily workflow, CLV setup
│   └── archive/
├── mlb_hr_engine_v1/                   ← Frozen; no changes
├── mlb_hr_engine_v2/                   ← Frozen; no changes
├── mlb_hr_engine_v3/                   ← Frozen; no changes
└── mlb_hr_engine_v4/                   ← Production
    ├── config.py
    ├── pipeline.py
    ├── main.py
    ├── app.py
    ├── backtest.py                     ← Rename to backtest_cli.py to avoid pkg collision
    ├── api/
    ├── backtest/
    ├── clients/
    ├── data/
    ├── engine/
    ├── output/
    ├── portfolio/
    ├── tracking/
    │   ├── *.py                        ← Code only
    │   └── data/                       ← Move CSVs here; gitignore *.csv
    ├── scripts/                        ← All analysis/ops scripts moved from root
    │   ├── analyze_*.py
    │   ├── audit_*.py
    │   ├── ops_daily.py
    │   ├── monitoring_dashboard.py
    │   ├── capture_closing_lines.py
    │   ├── optimize_daily.py
    │   └── settle_pick_tracker.py
    ├── tests/
    ├── frontend/                       ← Next.js app only
    │   ├── app/
    │   └── components/
    │       ├── dashboard/
    │       └── hr/                     ← SINGLE location for TSX cards
    ├── reports/                        ← Generated outputs only (.txt, .png screenshots)
    └── Docs/                           ← v4-internal living docs (numbered structure)
        ├── 01_SPECS/
        ├── 03_LLM_WIKI/
        ├── 07_OPERATIONS/
        ├── 08_TASKS/
        └── 09_DECISIONS/
```

---

## 5. Migration Plan

**Phase 1 — Kill duplicates (no logic changes)**

1. Merge `docs/` and `Docs/` at root → keep `docs/` (lowercase). Diff both dirs first; Docs/ appears to be a copy of docs/ with minor additions. Absorb unique files from `Docs/` into `docs/`, delete `Docs/`.
2. Delete `mlb_hr_engine_v4/components/hr/` (the 3 TSX files outside frontend/). Canonical location: `frontend/components/hr/`.
3. Delete `mlb_hr_engine_v4/Docs/TASK-001-threat-card.md` (loose). Keep `Docs/08_TASKS/TASK-001-threat-card.md`.
4. Delete stray files: `"New Text Document.txt"`, `"tore app.py."`, `"ChatGPT Image Apr 22, 2026, 08_09_52 AM.png"`.
5. Move `mlb_hr_engine_v4/Docs/*.md` (7 loose doctrine files at Docs/ root) into `docs/doctrines/` at repo root.

**Phase 2 — Relocate scripts**

6. Create `mlb_hr_engine_v4/scripts/` directory.
7. Move all `analyze_*.py`, `audit_*.py`, `ops_daily.py`, `monitoring_dashboard.py`, `capture_closing_lines.py`, `optimize_daily.py`, `settle_pick_tracker.py` from root → `mlb_hr_engine_v4/scripts/`.
8. Update `run_ops_daily.bat` and `schedule_task.ps1` paths accordingly.
9. Update `CLAUDE.md` commands to reference `py -3.12 scripts/ops_daily.py`.

**Phase 3 — Separate tracking data from code**

10. Create `mlb_hr_engine_v4/tracking/data/`.
11. Move `*.csv` and `*.json` from `tracking/` → `tracking/data/`.
12. Update all CSV path constants in `tracking/*.py`.
13. Add `tracking/data/*.csv` to `.gitignore` (live data, not source).

**Phase 4 — Root output cleanup**

14. Move root `*.txt` analysis outputs → `mlb_hr_engine_v4/reports/`.
15. Move root `*.png` validation screenshots → `mlb_hr_engine_v4/reports/`.
16. Move root `streamlit_*.log` / `*.pid` → `mlb_hr_engine_v4/reports/` or gitignore.
17. Move `fb_pct_raw_data.csv`, `2026-04-22T02-16_export.csv` → `mlb_hr_engine_v4/tracking/data/`.

**Phase 5 — Resolve language boundary**

18. Move `mlb_hr_engine_v4/components/sub_room_rail.py` → `mlb_hr_engine_v4/output/sub_room_rail.py` (Streamlit display layer lives in output/).
19. Remove empty `mlb_hr_engine_v4/components/` directory.

**Phase 6 — Rename to remove collision**

20. Rename `mlb_hr_engine_v4/backtest.py` → `mlb_hr_engine_v4/backtest_cli.py` to end naming collision with `backtest/` package.

---

## 6. Files/Folders That Should Move

| Item | Current Location | Target |
|------|-----------------|--------|
| `analyze_*.py` (12) | repo root | `mlb_hr_engine_v4/scripts/` |
| `audit_*.py` (3) | repo root | `mlb_hr_engine_v4/scripts/` |
| `ops_daily.py` | repo root | `mlb_hr_engine_v4/scripts/` |
| `monitoring_dashboard.py` | repo root | `mlb_hr_engine_v4/scripts/` |
| `capture_closing_lines.py` | repo root | `mlb_hr_engine_v4/scripts/` |
| `optimize_daily.py` | repo root | `mlb_hr_engine_v4/scripts/` |
| `settle_pick_tracker.py` | repo root | `mlb_hr_engine_v4/scripts/` |
| `*.txt` output files (10) | repo root | `mlb_hr_engine_v4/reports/` |
| `*.png` screenshots (8) | repo root | `mlb_hr_engine_v4/reports/` |
| `streamlit_*.log` / `.pid` (11) | repo root | `mlb_hr_engine_v4/reports/` |
| `fb_pct_raw_data.csv` | repo root | `mlb_hr_engine_v4/tracking/data/` |
| `2026-04-22T02-16_export.csv` | repo root | `mlb_hr_engine_v4/tracking/data/` |
| `tracking/*.csv` (5 CSVs) | `tracking/` | `tracking/data/` |
| `tracking/learned_adjustments.json` | `tracking/` | `tracking/data/` |
| `Docs/` (root) | repo root | Merge into `docs/` then delete |
| `FULL_SLATE_UX_DOCTRINE.md` | repo root | `docs/doctrines/` |
| `MASTER_TCC_DOCTRINE.md` | repo root | `docs/doctrines/` |
| `PHASE3_REFINEMENT_DOCTRINE.md` | repo root | `docs/doctrines/` |
| `ROOM_06_DEPLOYMENT_FD_SLIP_TRACKING_DOCTRINE.md` | repo root | `docs/doctrines/` |
| `MLB_HR_ENGINE_V4_OPTIMIZATION_ANALYSIS.md` | repo root | `docs/archive/` |
| `OPTIMIZATION_RESULTS_*.md` (4) | repo root | `docs/archive/` |
| `v4/components/hr/*.tsx` (3) | `components/hr/` | DELETE (dupe of `frontend/components/hr/`) |
| `v4/Docs/TASK-001-threat-card.md` (loose) | `Docs/` | DELETE (dupe of `Docs/08_TASKS/`) |
| `v4/Docs/*_doctrine_v1.md` (7 loose) | `v4/Docs/` root | `docs/doctrines/` at repo root |
| `v4/components/sub_room_rail.py` | `components/` | `v4/output/` |
| `v4/backtest.py` | `v4/` | Rename to `v4/backtest_cli.py` |

---

## 7. Orphan Systems

| System | Location | Status | Evidence |
|--------|---------|--------|---------|
| `strategies/` module | `v4/strategies/` (6 files) | **ORPHAN** — not imported by pipeline.py or app.py; portfolio/ does similar work | No reference in CLAUDE.md |
| `api/` FastAPI backend | `v4/api/` (auth, cache, cron, main) | **ORPHAN?** — separate from Streamlit; wiring unclear | Not in CLAUDE.md operational docs |
| `tracking/auto_learn.py` | `v4/tracking/` | **ORPHAN** — not mentioned in any doctrine | No CLAUDE.md reference |
| `tracking/adaptive_weights.py` | `v4/tracking/` | **ORPHAN** — not mentioned in any doctrine | No CLAUDE.md reference |
| `tracking/notify.py` | `v4/tracking/` | **ORPHAN** | No CLAUDE.md reference |
| `tracking/strategy_log.py` | `v4/tracking/` | **ORPHAN** | No CLAUDE.md reference |
| `tracking/line_movement.py` + `line_movement_log.csv` | `v4/tracking/` | **ORPHAN** | No CLAUDE.md reference |
| `supabase/` | repo root | **ORPHAN** — no reference anywhere | Not in CLAUDE.md, no imports found |
| `.devcontainer/` | repo root | **DORMANT** — separate from Dockerfile/fly.toml | Exists alongside two other deploy targets |
| `mlb_hr_engine_v3/` | repo root | **SEMI-ORPHAN** — not used by compare.py | compare.py only uses v1/v2 |
| `v4/Docs/02_RAW/` subdirs | `v4/Docs/02_RAW/` | **EMPTY SHELL** — 5 subdirs all empty | daily_matchups, notes, pitch_mix, screenshots, statcast, weather |
| `v4/Docs/04_SYSTEMS/`, `05_MODELS/`, `06_UI/`, `99_ARCHIVE/` | `v4/Docs/` | **EMPTY SHELLS** | All empty |
| `v4/Docs/03_LLM_WIKI/daily/`, `matchups/`, `pitchers/`, `players/`, `systems/`, `threat-models/` | `v4/Docs/03_LLM_WIKI/` | **EMPTY SHELLS** | All empty |

---

## 8. Naming Convention Inconsistencies

| # | Inconsistency | Examples | Canonical Standard |
|---|--------------|---------|-------------------|
| N1 | **Directory casing at root** | `docs/` (lowercase) vs `Docs/` (TitleCase) — same content | Use `docs/` everywhere (lowercase) |
| N2 | **Doc file naming split** | Root doctrines: `FULL_SLATE_UX_DOCTRINE.md` (ALLCAPS) vs `docs/`: `spec_bankroll_command_layer_v1.md` (snake) vs `v4/Docs/01_SPECS/`: `architecture.md` (kebab/lower) | Use `snake_case.md` everywhere; no ALLCAPS filenames |
| N3 | **Analysis script prefixes** | `analyze_*.py`, `audit_*.py`, `compare_*.py`, `test_*.py` — four different prefixes for similar analysis tools | `analyze_*.py` for all standalone analysis; `test_*.py` for pytest only |
| N4 | **Python in TSX component dir** | `components/sub_room_rail.py` alongside `components/hr/*.tsx` | Python in `output/` or `engine/`; TSX in `frontend/components/` only |
| N5 | **Tracking CSV names** | `pick_tracker.csv` + `picks_log.csv` + `picks_log.csv.bak` — three files for pick data | `pick_tracker.csv` is canonical (S25); `picks_log.csv` is legacy; consolidate |
| N6 | **Reports step numbering** | `step3_*.md`, `step04_*.md`, `step3_execution_isolation_notes.md` — inconsistent zero-padding | `step_NN_*.md` (zero-padded two-digit) |
| N7 | **backtest module/script collision** | `backtest.py` (script) + `backtest/` (package) at same level | Rename script to `backtest_cli.py` |
| N8 | **Streamlit log location** | Logs in `v4/`, root, and `reports/` simultaneously | `reports/` only; gitignore `*.log`, `*.pid` |
| N9 | **Doctrine version suffix** | `spec_bankroll_command_layer_v1.md` (versioned) vs `architecture.md` (unversioned) | Version suffix only for immutable specs; living docs unversioned |
| N10 | **requirements.txt duplication** | `requirements.txt` at root AND `v4/requirements.txt` AND `v4/requirements-api.txt` | Root `requirements.txt` points to v4; v4 is canonical; api deps in `requirements-api.txt` only if FastAPI is wired |

---

## Summary Severity Matrix

| Category | Critical | High | Medium | Low |
|----------|---------|------|--------|-----|
| Duplicates | 2 (D1 docs/, D2 TSX) | 2 | 3 | 2 |
| Conflicts | 3 (C1 doc war, C2 TSX split, C4 root scripts) | 4 | 3 | — |
| Orphans | — | 3 (strategies/, api/, supabase/) | 4 | 7 empty shells |
| Naming | — | 3 (N2, N4, N7) | 5 | 2 |

**Immediate actions (no logic risk):** D1 doc merge, D2 TSX delete, Phase 4 root cleanup.  
**Before next feature work:** Phase 2 script relocation, N7 backtest rename.  
**Lower priority:** Phase 3 tracking data separation, orphan audit of `strategies/` and `api/`.
