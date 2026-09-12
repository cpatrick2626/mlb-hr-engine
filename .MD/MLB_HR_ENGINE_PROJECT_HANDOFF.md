# MLB HR ENGINE — FULL PROJECT HANDOFF

> **HISTORICAL SNAPSHOT — superseded 2026-09-12.** Preserve the original studies and operator notes below as evidence, but do not treat the former top-band calibration fix as queued or warranted, and do not treat parlay construction as future product direction. Current doctrine: MAIN calibration is FROZEN pending new evidence plus explicit operator authorization; north star is +EV single-leg HR bets at longer odds; parlay construction/grading/product expansion is RETIRED / INVALIDATED. Current PM authority: ChatGPT — MLB HR Engine Project Manager / Command Center.

_Written 2026-09-11. Read this first in any fresh chat to continue with full context._
_Operator: Kylar (GitHub: cpatrick2626). PM-drafts-packets / coding-agents-execute / operator-gates-all-commits model._

---

## 0. TL;DR — WHERE THINGS STAND RIGHT NOW

- **Working machine:** Home PC, `C:\MLB HR Engine\mlb-hr-engine-master`, on branch line **`cda4f51`+** (design tokens, live-state, mobile fixes — a DIFFERENT line than earlier "session" work; that older work is orphaned in a laptop reflog). PC is synced with `origin/main`.
- **Odds pipeline: FIXED and LIVE** after a 4-bug saga. Board now shows ODDS / IMP% / EDGE / EV% populated on players who have lines. BUT — see the big caveat below.
- **THE BIG CAVEAT (most important current fact):** The odds are **BetRivers, NOT FanDuel.** The Odds API plan does NOT carry FanDuel at all. The operator bets FanDuel. So the EV column is **BetRivers-based, an approximation** — not the operator's real book. Prices differ meaningfully (e.g. McGonigle +400 BetRivers vs +490 FanDuel). A frontend labeling commit (fb262ee, NOT deployed) adds "· BETRIVERS" to the odds so the source is honest.
- **The model deep-dive is DONE** (3 studies). Verdict: model is sound; the loss driver is bet STRUCTURE (parlays), proven a 3rd time; the board overstates top HR-prob ~4-8pts.
- ~~One protected build still queued: the top-band calibration fix (Part B).~~ SUPERSEDED: calibration is frozen; no refit is queued or approved.

---

## 1. THE ODDS PIPELINE SAGA (this session's big fix)

The odds column had been dark. Operator's instinct ("we never finished setting this up") was RIGHT — there were **FOUR separate breaks**, all now found and fixed:

1. **Dead Odds API key** → replaced with a new working key (confirmed via direct API test).
2. **Key not in both places** → set in BOTH Fly secret (`flyctl secrets set ODDS_API_KEY=...`) AND GitHub Actions secret (Settings→Secrets→Actions). The pipeline uses the GitHub one; the live API uses the Fly one. Both needed it.
3. **Skip-guard destroyed its own cache** → `cron.py` overwrote freshly-fetched odds with an empty sentinel on the next "skip" run. Fixed: commit **`0bb2ecc`** (preserve fresh props cache) — DEPLOYED.
4. **Payload discarded non-FanDuel odds** → `api/main.py:~1396` read ONLY `fanduel_american` (null when FanDuel absent), throwing away valid `best_american` lines. Fixed: commit **`cf67df0`** (prefer fanduel_american, fall back to best_american, publish odds_bookmaker) — DEPLOYED (Fly machine v147). This was the last link; odds went live after it.

**Result:** `/api/slate` now returns ~88/410 rows with odds (fills in more as games enter the ~4h window). EV computes. Confirmed live examples: Rafael Flores +510 EV +29%, Pete Crow-Armstrong +300 EV −7%.

### The unresolved coverage issue (BetRivers vs FanDuel)
- Diagnostic (Sol) confirmed: raw Odds API response returns **BetRivers only**; `fanduel` key is ABSENT upstream. Not a code bug — **the-odds-api.com's bookmaker directory does not include FanDuel.** (https://the-odds-api.com/sports-odds-data/bookmaker-apis.html)
- So: board EV is BetRivers-based. Operator bets FanDuel. Prices differ.
- **Fix applied (NOT deployed):** commit `fb262ee` labels odds as "· BETRIVERS" on the board so it's honest. Ratify + `git push` (frontend → Vercel) to deploy.
- **To get REAL FanDuel odds:** need a DIFFERENT odds provider that covers FanDuel MLB HR props (research task, not yet done), OR accept BetRivers as a proxy and manually verify FanDuel before betting.

### Known minor pipeline bug (not blocking)
- `multiseason_splits_cache.json` save fails every run (`[Errno 2] No such file or directory ...cache.tmp`). Stats cache never persists → recomputed every run (slower, more MLB API load). Worth fixing later.

---

## 2. THE MODEL DEEP-DIVE (done — findings are solid)

Three read-only studies ran (files in `mlb_hr_engine_v4/scripts/analysis/`):
`PHASE1_MAIN_REVALIDATION_*.md`, `HR_DISTRIBUTION_BY_RANK_*.md`, `HR_DISTRIBUTION_FULLSEASON_*.md`.

**Findings:**
- **MAIN model is SOUND — no drift.** AUC 0.649 (was 0.650). Calibration honest on the lineup-confirmed betting population. The engine is NOT why hitting declined.
- **Model works as a TOP-40 FILTER, not a fine ranker.** Full-season (15,489 obs): top-5 ~16.5%, top-10 ~17.9%, top-40 ~15.7%, rank 41+ drops to ~9.7% (the cliff). Top 5/10/40 all statistically the same ~15-18% — CIs overlap. The model can say "in the good group" but NOT "#3 > #10."
- **Board OVERSTATES top HR-prob ~4-8 points** (shown 22-28% → real ~16-18%). Confirmed twice. Inflates EV on exactly the plays bet most.
- **Structure is the leak, again (3rd proof).** Sep FanDuel export = ~all 3-4 leg parlays at +11,000 to +265,000 combined odds. Near-total $0 returns.
- **Only MAIN is validated.** JIG, TM, Arsenal Edge/AEE, SIGNAL, HVY, roles, pitcher-vuln, strategy rails = displayed but NEVER validated to predict HRs.
- **Label bugs:** SIGNAL % = AEE sample support (NOT probability); TM sorts despite "display-only"; HOT STREAK uses power not streaks; etc.

---

## 3. THE BETTING RULE (data-backed, usable — with the odds caveat)

> **HISTORICAL SNAPSHOT — superseded:** The single-leg guidance remains aligned with current product direction, but its specific thresholds and examples are not revalidated here. The 2-leg parlay guidance below is RETIRED / INVALIDATED; do not use it as product direction.

**~~Parlay construction~~ — RETIRED / INVALIDATED as product direction.** The following historical proposal is not current guidance: 1–4 leg combinations from positive-EV picks and related construction advice. Preserve for provenance only.

**CRITICAL CAVEAT:** the EV shown is **BetRivers-based, not FanDuel.** Until a FanDuel odds source exists, use the board to find CANDIDATES, then **manually check FanDuel's actual odds and recompute** before betting. BetRivers is a rough proxy, not exact.

---

## 4. GIT / COMMIT STATE

Recent commits on `cda4f51` line (newest first):
- `cf67df0` — payload publishes best_american fallback (odds fix, DEPLOYED)
- `0bb2ecc` — preserve fresh props cache (odds fix, DEPLOYED)
- `fb262ee` — frontend BetRivers labeling (COMMITTED, NOT pushed/deployed — ratify + `git push`)
- `aca1991` / `969d882` / `d12fdbd` / `4ad9f24` — wiki checkpoints
- `26a7332` — RANK+PROJECTION sort fix
- `34fd6ab` — mobile clipboard FanDuel handoff (see §6)
- `cda4f51` — base (design tokens)

**Commit discipline:** scoped `git add` (never `-A`), `--no-gpg-sign`, leave Obsidian/wiki/tracking/`node_modules`/analysis-output churn unstaged.
**Deploy:** Fly = manual (`flyctl deploy --app mlb-hr-api`, flyctl on PATH via WinGet). Frontend = Vercel auto on push to main.

---

## 5. IMMEDIATE NEXT ACTIONS (priority)

1. **Deploy the BetRivers labeling** (`git push` — commit fb262ee) so the board honestly shows the odds source. Low-risk, frontend-only.
2. **Decide the FanDuel odds question:** research whether an odds provider covers FanDuel MLB HR props (to make EV match the real book), OR accept BetRivers-as-proxy + manual FanDuel verification. This is the biggest open item for real betting accuracy.
3. ~~Part B — top-band calibration fix (protected, warranted).~~ RETIRED from this handoff: calibration is frozen. Any future recalibration requires new evidence and explicit operator authorization.
4. **Behavioral (no build):** bet +EV singles from the top-10, verify FanDuel prices, drop the 3-4 leg parlays.

---

## 6. OTHER CONTEXT / SMALLER ITEMS

- **FanDuel search hand-off:** the `?q=` app deep-link died (FanDuel removed URL-param search pre-fill from their app). Reverted to clipboard-copy + paste (commit `34fd6ab`). Works via paste on mobile now. Not recoverable to true auto-fill (FanDuel-side change).
- **Multi-machine untangle:** all "session" work (Community rich slips, wager persistence, honest grade engine, earlier skip-guard) is on an ORPHANED line in a laptop reflog (`3a06cd1`), NOT on the current PC line (`cda4f51`). The PC line went a different direction. If any of that work is wanted, cherry-pick from reflog. The odds skip-guard IS present on `cda4f51` (merged in).
- **Data assets:** warehouse `batter_stat_history` ~177K labeled rows (Jul 21–Sep 8, dedupes to ~15-17K canonical obs), still capturing. App does NOT store real bet odds/execution/P&L — real results come only from FanDuel exports.
- **Frontend note:** `odds_bookmaker` field is now published but the deployed frontend may not yet render the label until fb262ee ships.

---

## 7. ONE-LINE SUMMARY FOR A FRESH CHAT

"HISTORICAL, SUPERSEDED: MLB HR bet tool (FastAPI/Fly + React/Vercel + Supabase), PC branch cda4f51. Odds pipeline FIXED after a 4-bug saga (dead key, secrets, cache self-destruct, payload discarding odds) — board then showed ODDS/EV. BUT the Odds API only had BetRivers, NOT FanDuel — EV was a BetRivers approximation; fb262ee labeled this. Deep-dive reported model sound (AUC 0.65, top-40 filter, limited fine ranking), board overstatement, and parlay losses. Historical behavior note: shortlist +EV singles, verify FanDuel price, skip parlays. Old next steps to push fb262ee or run Part B calibration are superseded. Current calibration is frozen and no refit is queued."
