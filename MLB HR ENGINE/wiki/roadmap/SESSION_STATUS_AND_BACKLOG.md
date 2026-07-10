# Session Status & Prioritized Backlog (as of 2026-07-09)

Purpose: one-page next-session handoff. Backlog grouped by shared infrastructure so builds are efficient — do one cluster at a time.

---

## Shipped this session (committed + deployed) — RESOLVED

- **prob_scale calibration 0.88 → 1.12** — validated on 3,828 rows, live on Fly volume. AUTO_LEARN_FROZEN=True set.
- **MIN_EV_PCT 3.0 → 14.0** (commit `865f66d`) — normalizes ~8-9 picks/slate at lifted probabilities.
- **picks RLS** — `alter table public.picks enable row level security;` on prod. Anon gap closed on 4,590 rows.
- **Strategy rail honesty** (commit `77f8354`) — fabricated HR ENV SCORE removed; honest labels + HEURISTIC tags; hr_env_score write stopped.
- **CRON_SECRET realignment** — settle + CLV crons were 401ing since ~June 16. Secret realigned on Fly + GitHub Actions.
- **July 8 legs settle backfill** — 30 legs (6 HR / 24 no) settled manually via `settle_legs.py --commit --date 2026-07-08`.
- **Auto-settlement workflow** (commit `c7805e2`) — `settle_legs.yml` runs daily at 10:00 UTC; old `daily_settle.yml` disabled.
- Splits display + SPLIT SCOPE toggle + three-way batter card + fabricated platoon multiplier retired (prior session).
- FanDuel event deep-links + name normalization (prior session).
- Player-name dot §12 relabel MATCHUP → BATTER THREAT (prior session).
- Tooling: code-reviewer subagent + Supabase read-only MCP (prior session).

---

## Backlog — grouped by shared foundation

### Cluster 2 — Calibration & learning loop
*Fable-tier, scoring surface. Shares calibration machinery + settled data. Do as ONE focused session.*

- **Auto-learner remainder-bucket bug fix** — DONE (commit `e36ee4a`, 2026-07-10). Count-weighting fix; computes correct 1.21→1.12. Dormant behind AUTO_LEARN_FROZEN.
- **Raise adaptive min_ev_pct clamp** (currently 8.0) before unfreezing auto-learn — else EV floor drops below 14 automatically. OPEN.
- **Phase 2 calibration: Platt refit (two-tier A+B, CV-validated)** — SCOPED + twice-confirmed (Fable + Codex, 2026-07-10), WAITING for post-1.12 real data. See `wiki/roadmap/PHASE2_PLATT_REFIT_PLAN.md` for full scoping doc, candidate coefficients, pass criteria, and rollout coupling notes.
- **Prerequisite:** keep AUTO_LEARN_FROZEN until min_ev_pct clamp fixed AND Phase 2 refit executed (or explicitly skipped). OPEN.

### Cluster 4 — Ops hardening & data pipeline reliability
*Shares settlement / cron infra.*

- **pick_tracker auto-settlement** — fix hardcoded-path bug (`TRACKING_DATA_DIR` ignored, hardcodes `ROOT/tracking/pick_tracker.csv`; prod uses `/data` volume). Investigate prod `/data/pick_tracker.csv` state, backfill May 31→present, then auto-wire (mirror `settle_legs.yml`). This refreshes the CALIBRATION dataset — feeds Cluster 2.
- **CLV going-forward** — verify capture runs now that auth is fixed; accept June–July gap as unrecoverable.
- **Workflow diagnostic hardening** — switch settle / CLV curls to `-Ssf` (show HTTP status). The June outage went unnoticed 3 weeks partly because `-sf` hid 401 status.
- **FanDuel deep-link efficacy verification** — once FD appears on odds feed.

### Cluster 1 — "Show the user their own picks"
*Shares tickets / legs data + auth + settlement.*

**SPLIT A — uses EXISTING data, buildable now:**
- LIVE TARGETS banner rebuild (today's committed picks + game-level status).
- "My Slips" history view (today + past submitted slips, grouped by ticket, with settlement results — meaningful now that settlement works).

**SPLIT B — needs NEW live-data infra, separate prereq:**
- HR-hit notification toggle.
- Batter-coming-up notification + live pitch/batter tracker.
- Requires a live in-game data source + polling/push layer the pregame-only architecture lacks. Do NOT scope as a banner add-on — it is a separate infra tier.

### Cluster 3 — STRATEGY room + honest signals
*Shares real-data-grounded display. Scoped in `strategy-section-spec.md` §11.*

- **STRATEGY room rebuild** — phased P1-P5 port: lift odds/EV/parlay math, adapt builders, rebuild composites as transparent filters, ledger-based per-strategy tracking.
- **Analyst agents** — fold into STRATEGY P5, consume typed outputs, non-authoritative until ledger-validated (n≥200).
- **Arsenal Edge Exploit surface / Batter Card** — shares Phase B backend prereq: expose stranded arsenal data.

### Cross-cutting / lower priority

- Multi-season splits (display-only lens; MODERATE feasibility; cache is make-or-break; needs one `statSplits` historical probe). Lower priority.
- AEI thin-sample tag (cosmetic).

---

## Standing awareness

- **prob_scale = 1.12** on Fly volume (`/data/learned_adjustments.json`). AUTO_LEARN_FROZEN=True in `pipeline.py`. Do not unfreeze until Cluster 2 bucket bug + clamp are fixed.
- `legs.player_id` is TEXT, `picks.player_id` is INTEGER — cast needed when joining.
- `pick_tracker.csv` is stale after May 31 (calibration dataset, not the legs ledger). Prod CSV lives on `/data` volume.
- Tooling: use `@code-reviewer` before protected-surface commits; Supabase MCP is read-only for direct ledger queries.

## Source anchors

- Session detail: `wiki/sessions/2026-07-09-calibration-rollout-settlement-repair.md`
- Calibration finding: `wiki/log.md` 2026-07-08 `prob_scale=0.88 calibration re-audit`
- Strategy port reference: `wiki/roadmap/strategy-section-spec.md` §11
- Recent commits: `git log --oneline -10` from `c7805e2`
