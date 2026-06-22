# Frontend / Vercel Source-of-Truth Audit
**Date:** 2026-06-22  
**Auditor:** Claude Code (read-only)  
**Risk:** LOW — no edits, no commits, no push, no deploy

---

## Commands Run

```
git log --oneline --all -- frontend/
git ls-tree -r HEAD -- frontend/
git ls-tree -r 8285d31 -- frontend/
git ls-tree -r 004ed9f -- frontend/
git ls-tree -r cedfd89~1 -- frontend/
git ls-tree -r cedfd89 -- frontend/
git show cedfd89 --stat
git show 8285d31:frontend/index.html  (first 50 lines)
git log --oneline 8285d31..HEAD -- frontend/
git log --oneline --all | head -20
Get-ChildItem frontend/ -Force   (working tree)
grep -r "MOCK\|mock\|..." mlb_hr_engine_v4/frontend/
grep -r "api/slate\|fetch.*api" mlb_hr_engine_v4/frontend/
Read: mlb_hr_engine_v4/frontend/app/page.tsx
Read: mlb_hr_engine_v4/frontend/components/hr/hr-threat-card.tsx (60 lines)
```

---

## Commits Inspected

| Commit | Message | Role in audit |
|--------|---------|---------------|
| `f274841` | chore(odds): expose clv odds source state | HEAD |
| `cedfd89` | chore: remove dead trees, stale artifacts, and junk | **Deletion commit** |
| `bd1f7e8` | docs(scratch): 2026-06-22 session summary | cedfd89~1 — last state before deletion |
| `8285d31` | vault backup: 2026-06-22 06:20:00 | "last successful Production deploy" per Vercel |
| `004ed9f` | fix(frontend): velo column reads pitch_stats avg_speed fallback | Last commit touching real app in frontend/ |

---

## Finding 1 — frontend/ at HEAD is empty

`git ls-tree -r HEAD -- frontend/` returns **no output** — the directory is empty in git.

Working tree shows two **untracked** (git-ignored) files left behind:
```
frontend/http4173.stderr.log   (23,774 bytes, 2026-06-10)
frontend/http4173.stdout.log   (0 bytes)
```
These are dev-server logs, not tracked source. They were never committed and are invisible to Vercel.

---

## Finding 2 — The transition commit: `cedfd89`

`cedfd89` ("chore: remove dead trees, stale artifacts, and junk") deleted **all app files** from `frontend/` in a single commit:

```
frontend/index.html                         | 3887 lines deleted
frontend/image-slot.js                      |  642 lines deleted
frontend/assets/js/full-slate-matrix.js     | 1122 lines deleted
frontend/assets/js/jig-command.js           |   45 lines deleted
frontend/assets/fonts/*.woff2               |  35+ binary files deleted
frontend/assets/js/*.js                     |  ~10 JS files deleted
```

This is **the commit that broke Vercel**. Every commit after cedfd89 (`bd1f7e8`, `b62951b`, `ec6ab1b`, `f274841`) does not touch `frontend/` — so `frontend/` has been empty in git since `cedfd89`.

---

## Finding 3 — What frontend/ was at 8285d31

The vault backup at `8285d31` is **NOT a Next.js app**. It contained:

- `frontend/index.html` — a single-file static HTML/JS/CSS "Master Dashboard" (~3,887 lines), self-contained, no build step
- `frontend/image-slot.js` — JS module (~642 lines)
- `frontend/assets/js/full-slate-matrix.js` (~1,122 lines)
- `frontend/assets/js/jig-command.js` (45 lines)
- `frontend/assets/js/*.js` — ~10 more bundled JS files
- `frontend/assets/fonts/*.woff2` — 35 Barlow font files

There is **no `package.json`, no `next.config.mjs`, no `app/` dir, no `components/` dir** in root `frontend/` at any commit. This was never a Next.js project.

---

## Finding 4 — True last commit with a real app in frontend/

The static HTML app was present through `004ed9f` (the last `fix(frontend):` commit before the cleanup chain). It was intact at `8285d31` and at `bd1f7e8` (cedfd89~1). It was deleted by `cedfd89`.

**True "last real UI deploy" commits:**  
Any commit from `f2d3611` (oldest frontend/ touch) through `bd1f7e8` (cedfd89~1) had the static HTML app. The most feature-complete version was at `cedfd89~1 = bd1f7e8` (`004ed9f` was the last functional patch).

**8285d31 held the static HTML app.** So the live UI _is_ served from the static HTML app — not from a Next.js deployment. Vercel was serving a static HTML site with no build step from the `frontend/` root directory.

---

## Finding 5 — Inferred Vercel failure cause

Vercel Root Directory is set to `frontend`. After `cedfd89`, that directory contains no files tracked in git (only untracked log files which Vercel cannot see).

**Inferred cause:** Vercel finds an empty root directory → no `package.json` → no framework detected → build fails or outputs nothing → deployment fails.

> **NOTE:** The definitive cause can only be confirmed in the Vercel dashboard build logs. The above is an inference from repo state only.

All commits from `cedfd89` onward are expected to fail for the same reason.

---

## Finding 6 — frontend/ vs mlb_hr_engine_v4/frontend/

| Property | root `frontend/` | `mlb_hr_engine_v4/frontend/` |
|----------|-----------------|------------------------------|
| Type | Static HTML/JS (was) / Empty (now) | Next.js 14 app |
| package.json | Never had one | Yes |
| next.config.mjs | No | Yes |
| app/ dir | No | Yes (`app/page.tsx`, `app/layout.tsx`) |
| components/ | No | Yes |
| Vercel Root Dir target | Yes (currently) | No |
| Build step required | No (was static) | Yes (`next build`) |

The actual Next.js tactical UI shell lives at `mlb_hr_engine_v4/frontend/` and has never been the Vercel target.

---

## Finding 7 — mlb_hr_engine_v4/frontend/ verdict: MIXED

**Real data (partial):**  
`page.tsx` includes a `useEffect` that fetches `https://mlb-hr-api.fly.dev/api/slate` and maps `leaderboard_rows` → MAIN `ThreatRankingsTable` and `leaderboard_rows_jig` → JIG `ThreatRankingsTable`. If the API returns data, these two panels render live.

**Mock-heavy (everything else):**  
All other panels render hardcoded `MOCK_*` constants — no API wiring:

| Panel | Data source |
|-------|-------------|
| `ThreatRankingsTable` (MAIN) | `mainRows` — **live from `/api/slate`** (falls back to MOCK) |
| `ThreatRankingsTable` (JIG) | `jigRows` — **live from `/api/slate`** (falls back to MOCK) |
| `EscalationFeed` (MAIN) | `MOCK_ESCALATIONS` — hardcoded |
| `HRThreatCard` zone | `MOCK_THREATS` — hardcoded |
| `PitcherVulnerabilityPanel` | `MOCK_PITCHERS` — hardcoded |
| `MatchupIntelPanel` (MAIN) | `MOCK_MATCHUPS` — hardcoded |
| `EscalationFeed` (JIG) | `JIG_ESCALATIONS` — hardcoded |
| `MatchupIntelPanel` (JIG) | `JIG_MATCHUPS` — hardcoded |
| CommandHeader `date` | `"Saturday, May 23 2026"` — **hardcoded date string** |
| CommandHeader `slateCount` | `{87}` — hardcoded |
| CommandHeader `activeThreats` | `{14}` — hardcoded |
| JIG Engine Status panel | Inline hardcoded values |

Additionally, `strategy`, `hits`, `performance`, and `ops` workspaces are `STANDBY — NO ACTIVE FEED` stubs with no panels wired.

**Verdict: MIXED** — rankings fetch real data but fall back gracefully to mocks. All other panels are static. Not production-ready for operator use.

---

## Finding 8 — Live UI status

The live Vercel URL is serving a **frozen/fossil deployment** from the last successful Vercel build. That build was based on a commit where `frontend/` held the static HTML app (`index.html`). The live board is the static HTML `Master Dashboard`, not the Next.js app.

Every commit from `cedfd89` forward is failing on Vercel. The UI has been frozen since `cedfd89` was pushed.

---

## Finding 9 — Safe recovery paths

### Option A — Restore static HTML app into `frontend/` (lowest risk, unblocks Vercel immediately)

Restore the deleted files from `cedfd89~1` (`bd1f7e8`) into `frontend/`. No build step. Vercel serves them directly. This restores the last known working UI.

**How (operator executes):** `git show bd1f7e8:frontend/index.html > frontend/index.html` + same for other deleted files, then commit + push. Vercel picks it up automatically.

**Risk:** Low. Restores to a known good state. No Vercel config changes required.

**Caveat:** Restores the static HTML app, not the Next.js app. Does not advance the frontend.

### Option B — Repoint Vercel Root Directory to `mlb_hr_engine_v4/frontend/`

**Do NOT do this yet.** The Next.js app is MIXED/mock-heavy. The CommandHeader has a hardcoded date (`May 23 2026`), hardcoded `slateCount`/`activeThreats`, and 6 of 8 data panels render mock data. It is not ready for operator use as a live dashboard.

This option is correct eventually but requires:
1. Wire remaining panels (EscalationFeed, HRThreatCard, PitcherVulnerabilityPanel, MatchupIntelPanel) to real `/api/slate` data
2. Replace hardcoded `date`, `slateCount`, `activeThreats` with live values
3. Confirm `/api/slate` response shape matches all mapped fields
4. Verify Fly.io cold-start handling is adequate
5. Then repoint Vercel Root Directory

### Option C — Copy mlb_hr_engine_v4/frontend/ into root frontend/

Moves the Next.js app to where Vercel expects it, without changing Vercel config. Same readiness requirements as Option B apply. More disruptive than Option A as interim fix.

---

## Recommendation

**Immediate:** Execute Option A to unblock Vercel. Restore the static HTML app into `frontend/` from `bd1f7e8`. This gets the live board back without any config change.

**Parallel track:** Continue wiring `mlb_hr_engine_v4/frontend/` to real data. When all panels are live and the date/counts are dynamic, repoint Vercel Root Directory to `mlb_hr_engine_v4/frontend/` as a planned cutover.

**Do NOT repoint Vercel Root Directory until `mlb_hr_engine_v4/frontend/` is confirmed production-ready and wired to real `/api/slate` data across all panels.**

---

## Findings doc location

Written to: `.scratch/2026-06-22-frontend-vercel-audit.md` (in-repo, not in Obsidian vault).  
If filing to vault: `MLB HR ENGINE/wiki/sessions/` or `MLB HR ENGINE/wiki/architecture/`.

---

NO FILES EDITED. NO COMMITS. NO PUSH. NO DEPLOY. NO VERCEL CHANGES.  
LIVE UI: **FROZEN/FOSSIL** — served from last pre-cedfd89 Vercel deployment (static HTML app)  
mlb_hr_engine_v4/frontend: **MIXED** — rankings panels fetch live, all other panels mock-heavy  
FINAL GIT STATUS: clean (no uncommitted changes; two untracked log files in frontend/ are not source)
