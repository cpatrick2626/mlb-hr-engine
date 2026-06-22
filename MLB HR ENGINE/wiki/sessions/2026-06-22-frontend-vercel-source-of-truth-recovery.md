# Frontend / Vercel Source-of-Truth Recovery
**Date:** 2026-06-22  
**Status:** COMPLETE — root frontend/ restored; Vercel unblocked  
**Owner:** Claude Code (Sonnet 4.6)

---

## What Happened

Commit `cedfd89` ("chore: remove dead trees, stale artifacts, and junk") deleted every tracked file from the root `frontend/` directory. That directory is the Vercel Root Directory for the `mlb-hr-engine` project — configured in the Vercel dashboard, not in any file in the repo. The deletion was made on the basis that `frontend/` appeared DEAD per in-repo references (no imports in Python, not in `Dockerfile`, not in `fly.toml`, not in GitHub workflows). All Vercel deploys since `cedfd89` were failing. The live UI board was frozen on the last pre-deletion Vercel build.

Commits between `cedfd89` and the restore (`bd1f7e8`, `b62951b`, `ec6ab1b`, `f274841`) did not touch `frontend/`, so the failure persisted silently for multiple sessions.

---

## Root Cause

Vercel's Root Directory setting lives in the Vercel dashboard — not in any file that can be read by a repo-side audit. A repo-only scan (`Dockerfile`, `fly.toml`, workflows, Python imports) cannot detect this dependency.

The deletion logic was sound for repo-visible consumers. The invisible consumer (Vercel dashboard config) was not checked.

---

## Governance Lesson

> **"DEAD per the repo" ≠ "DEAD per everything that consumes the repo."**

Before deleting any top-level directory — especially `frontend/`, `public/`, `static/`, `dist/`, `out/` — verify:

1. **Vercel dashboard** → Project Settings → Root Directory (or Framework Preset path)
2. **Netlify / Render / Railway / Fly.io** configs for static-asset or build output paths
3. **CI workflows** (`.github/workflows/`) for explicit path references
4. Only delete after all external-service configs are confirmed clear

This rule applies even when the directory has no Python imports, no Dockerfile COPY instructions, and no fly.toml references.

---

## Recovery

Restore method: `git checkout cedfd89~1 -- frontend/` (restores all deleted files from the commit immediately before the deletion).

**Restore commit:** `e619711` — pushed to `origin/main`. Vercel picked it up automatically on push. No Vercel dashboard changes required.

Fully recoverable because the deletion was a commit (not a force-push that rewrote history) and the files were committed before deletion.

---

## Surface Map (current as of e619711)

### LIVE static production — root `frontend/`

- **Type:** Static HTML/JS/CSS — no build step, no package.json, no framework
- **Vercel Root Directory:** `frontend` (dashboard setting)
- **Files:** `index.html` (~3,887 lines, self-contained Master Dashboard), `image-slot.js`, `assets/js/full-slate-matrix.js`, `assets/js/jig-command.js`, ~10 bundled JS files, 35 Barlow font files
- **Status:** Restored and operational

### Next.js tactical shell — `mlb_hr_engine_v4/frontend/`

- **Type:** Next.js 14 — requires `next build`
- **Vercel Root Directory:** NOT the current target
- **Status: MIXED** — rankings panels (`ThreatRankingsTable` MAIN + JIG) fetch live from `/api/slate`; all other panels (`EscalationFeed`, `HRThreatCard`, `PitcherVulnerabilityPanel`, `MatchupIntelPanel`) render hardcoded `MOCK_*` constants; `CommandHeader` has hardcoded date (`"Saturday, May 23 2026"`), hardcoded `slateCount={87}`, hardcoded `activeThreats={14}`; strategy/hits/performance/ops workspaces are STANDBY stubs
- **NOT production-ready for operator use**

### Do NOT repoint Vercel Root Directory to `mlb_hr_engine_v4/frontend/` until:

1. All data panels wired to real `/api/slate` fields (EscalationFeed, HRThreatCard, PitcherVulnerabilityPanel, MatchupIntelPanel)
2. CommandHeader `date`, `slateCount`, `activeThreats` replaced with live values
3. Fly.io cold-start handling confirmed adequate
4. Full operator sign-off on cutover

---

## Key Commits

| Commit | Message | Role |
|--------|---------|------|
| `cedfd89` | chore: remove dead trees, stale artifacts, and junk | **The deletion — broke Vercel** |
| `bd1f7e8` | docs(scratch): 2026-06-22 session summary | cedfd89~1 — last good state |
| `e619711` | restore: static dashboard to frontend/ (Vercel recovery after cedfd89) | **Restore — Vercel unblocked** |
| `bc2864f` | docs(scratch): frontend/Vercel source-of-truth audit | Audit doc (local scratch only) |

---

## Audit Source

Full findings (9 findings, 3 recovery options) in: `.scratch/2026-06-22-frontend-vercel-audit.md`

---

## Cross-References

- `wiki/doctrine/build-log-and-spec-status.md` — Frontend / Vercel Source-of-Truth Recovery section
- `wiki/doctrine/production-surface-truth.md` — production surface ownership (if updated)
- `CLAUDE.md` §10 — Frontend Surface doctrine (static vs Next.js distinction)
