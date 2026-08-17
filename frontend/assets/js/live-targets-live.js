/* HR Engine — Live Targets banner: real live-state wiring (Phase 2a).

   Resolves each LIVE_TARGETS entry to a real game_pk by matching its display
   name against already-loaded slate rows (LEADERBOARD_ROWS / LEADERBOARD_ROWS_JIG),
   which carry game_pk from the Phase 1 backend join (see
   mlb_hr_engine_v4/api/ticket_history.py::_match_game). Ambiguous or no match
   -> unresolved, never guessed. Polls /api/live-state/{game_pk} for each
   resolved game_pk on the same cadence as live-alerts.js's LA_POLL_INTERVAL_MS
   (20s, aligned to the endpoint's LIVE_STATE_CACHE_TTL_SECONDS). */
(function () {
  const LT_POLL_INTERVAL_MS = 20000;
  const LT_API_BASE = "https://mlb-hr-api.fly.dev";
  const DIACRITIC_RE = new RegExp("[̀-ͯ]", "g");

  function normalize(s) {
    return (s || "")
      .normalize("NFD").replace(DIACRITIC_RE, "")
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function resolveGamePk(target) {
    const key = normalize(target.name);
    if (!key) return null;
    const rows = [
      ...(window.LEADERBOARD_ROWS || []),
      ...(window.LEADERBOARD_ROWS_JIG || []),
    ];
    const matches = rows.filter(
      (r) => r && r.game_pk != null && normalize(r.name).includes(key)
    );
    const gamePks = [...new Set(matches.map((r) => r.game_pk))];
    return gamePks.length === 1 ? gamePks[0] : null;
  }

  function ordinalSuffix(n) {
    const v = n % 100;
    if (v >= 11 && v <= 13) return "TH";
    switch (n % 10) {
      case 1: return "ST";
      case 2: return "ND";
      case 3: return "RD";
      default: return "TH";
    }
  }

  function inningLabel(state) {
    if (state.inning == null) return null;
    const half = state.inning_half === "Bottom" ? "BOT" : state.inning_half === "Top" ? "TOP" : "";
    return `${half} ${state.inning}${ordinalSuffix(state.inning)}`.trim();
  }

  function scoreLabel(state) {
    if (!state.score || state.score.home == null || state.score.away == null) return null;
    return `${state.score.away}-${state.score.home}`;
  }

  async function fetchLiveState(gamePk) {
    try {
      const res = await fetch(`${LT_API_BASE}/api/live-state/${gamePk}`);
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      return null;
    }
  }

  async function refresh() {
    const targets = window.LIVE_TARGETS || [];
    const gamePkByTarget = {};
    const distinctGamePks = new Set();
    targets.forEach((t) => {
      const pk = resolveGamePk(t);
      gamePkByTarget[t.id] = pk;
      if (pk != null) distinctGamePks.add(pk);
    });

    const stateByGamePk = {};
    await Promise.all(
      [...distinctGamePks].map(async (pk) => {
        stateByGamePk[pk] = await fetchLiveState(pk);
      })
    );

    const next = {};
    targets.forEach((t) => {
      const pk = gamePkByTarget[t.id];
      const live = pk != null ? stateByGamePk[pk] : null;
      if (!live || !live.status) {
        next[t.id] = { resolved: false, status: null, inningLabel: null, scoreLabel: null, gamePk: pk ?? null };
        return;
      }
      next[t.id] = {
        resolved: true,
        status: live.status, // "Live" | "Final" | "Preview" | other MLB abstract states
        inningLabel: inningLabel(live),
        scoreLabel: scoreLabel(live),
        gamePk: pk,
      };
    });

    window.LIVE_TARGETS_STATE = next;
    window.dispatchEvent(new CustomEvent("liveTargetsStateUpdated", { detail: next }));
  }

  refresh();
  setInterval(refresh, LT_POLL_INTERVAL_MS);
  window.addEventListener("hrEngineDataLoaded", refresh);
})();
