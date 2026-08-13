/* HR Engine — Live Alerts (Phase 1, Layer 3: "your batter is coming up").
   Source: GET /api/my-tickets (watchlist) + GET /api/live-state/{game_pk} (poll).
   No push infra, no notifications table — client poll while this tab is open,
   toast via the same DOM pattern used elsewhere (hr-lb-fd-toast / md-qp-fd-toast).
   Fails silent on any gap (no game_pk, no live data, request error) — a missed
   alert is acceptable, a wrong-game alert is not. */

(() => {
  const LA_API = 'https://mlb-hr-api.fly.dev';
  const LA_POLL_INTERVAL_MS = 20000;       // matches the server's live-state TTL (api/main.py LIVE_STATE_CACHE_TTL_SECONDS)
  const LA_WATCHLIST_REFRESH_MS = 120000;  // re-pull /api/my-tickets so newly-submitted legs get watched without a page reload

  let watchlist = [];          // [{leg_id, player_id, player_name, game_pk}]
  const firedLegIds = new Set();  // fire-once-per-leg dedup for this session
  let pollTimer = null;
  let watchlistTimer = null;

  function laToast(message) {
    let el = document.getElementById('live-alerts-toast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'live-alerts-toast';
      el.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);' +
        'background:#0e1f16;border:1px solid #1aff66;color:#e0ffe8;padding:10px 18px;' +
        'border-radius:8px;font-size:13px;font-family:inherit;z-index:9999;pointer-events:none;' +
        'transition:opacity .3s;white-space:nowrap;';
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.style.opacity = '1';
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.style.opacity = '0'; }, 4500);
  }

  /* Pull the caller's pending legs and keep only ones with a resolved game_pk
     and player_id. A leg with no game_pk means api/ticket_history.py couldn't
     uniquely resolve it (e.g. an unresolved doubleheader) — skip it rather
     than guess. */
  async function refreshWatchlist() {
    if (!window.__hrAuth?.authFetch) return;
    try {
      const res = await window.__hrAuth.authFetch(`${LA_API}/api/my-tickets`);
      if (!res || res._noAuth || !res.ok) { watchlist = []; return; }
      const data = await res.json().catch(() => ({}));
      const tickets = Array.isArray(data.tickets) ? data.tickets : [];
      const next = [];
      for (const ticket of tickets) {
        for (const leg of (Array.isArray(ticket.legs) ? ticket.legs : [])) {
          if (!leg || leg.settlement_status !== 'pending') continue;
          if (!leg.game_pk || !leg.player_id) continue;
          next.push({
            leg_id: leg.leg_id,
            player_id: String(leg.player_id),
            player_name: leg.player_name || 'Your batter',
            game_pk: leg.game_pk,
          });
        }
      }
      watchlist = next;
    } catch (_) {
      // fail silent — a stale watchlist just means no new alerts this cycle
    }
  }

  async function pollOnce() {
    if (watchlist.length === 0) return;
    const gamePks = Array.from(new Set(watchlist.map((w) => w.game_pk)));
    const stateByGamePk = {};
    await Promise.all(gamePks.map(async (gamePk) => {
      try {
        const res = await fetch(`${LA_API}/api/live-state/${gamePk}`);
        if (!res.ok) return;
        stateByGamePk[gamePk] = await res.json().catch(() => null);
      } catch (_) {
        // fail silent for this game_pk only — other games still get checked
      }
    }));

    for (const leg of watchlist) {
      if (firedLegIds.has(leg.leg_id)) continue;
      const state = stateByGamePk[leg.game_pk];
      if (!state) continue;
      const batter = state.current_batter;
      const onDeck = state.on_deck;
      const dueUp =
        (batter && String(batter.id) === leg.player_id) ||
        (onDeck && String(onDeck.id) === leg.player_id);
      if (!dueUp) continue;
      firedLegIds.add(leg.leg_id);
      laToast(`${leg.player_name} is coming up`);
    }
  }

  function start() {
    if (pollTimer) return;
    refreshWatchlist().then(pollOnce);
    pollTimer = setInterval(pollOnce, LA_POLL_INTERVAL_MS);
    watchlistTimer = setInterval(refreshWatchlist, LA_WATCHLIST_REFRESH_MS);
  }

  function stop() {
    clearInterval(pollTimer); pollTimer = null;
    clearInterval(watchlistTimer); watchlistTimer = null;
    watchlist = [];
    firedLegIds.clear();
  }

  function init() {
    const sb = window.__hrAuth?.sb;
    if (!sb) return;
    sb.auth.getSession().then(({ data }) => { if (data.session) start(); });
    sb.auth.onAuthStateChange((_e, session) => { if (session) start(); else stop(); });
  }

  if (window.__hrAuth) {
    init();
  } else {
    // auth.js loads immediately before this file and sets window.__hrAuth
    // synchronously — this only guards against an unexpected load-order change.
    const guard = setInterval(() => {
      if (window.__hrAuth) { clearInterval(guard); init(); }
    }, 200);
  }
})();
