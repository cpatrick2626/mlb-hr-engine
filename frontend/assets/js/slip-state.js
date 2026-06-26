/* HR Engine — Shared Slip State
   Holds ticket session (ticketId, legs, cardStatus) across all board surfaces.
   Plain JS — no JSX, no Babel. Must load before any React component bundles. */
(function () {
  var _state = {
    ticketId: null,
    legs: [],
    cardStatus: {},
    isOpen: false,
  };
  var _listeners = [];

  function _notify() {
    _listeners.forEach(function (fn) { fn(); });
  }

  function getState() {
    return {
      ticketId:   _state.ticketId,
      legs:       _state.legs.slice(),
      cardStatus: Object.assign({}, _state.cardStatus),
      isOpen:     _state.isOpen,
    };
  }

  function openSlip() {
    _state.isOpen = true;
    _notify();
  }

  function closeSlip() {
    _state.isOpen = false;
    _notify();
  }

  function subscribe(fn) {
    _listeners.push(fn);
    return function () {
      _listeners = _listeners.filter(function (l) { return l !== fn; });
    };
  }

  /* Pure builder — takes a normalized row and current ticketId, returns POST body.
     Normalized row fields: player_id, name, team, pitcher, model_prob (decimal),
     tier, model_tier_rank, board. */
  function buildLegPayload(row, ticketId) {
    var body = {
      board:        row.board,
      name:         row.name,
      model_prob:   row.model_prob,
      tier:         row.tier,
      generated_at: window.SLATE_GENERATED_AT || null,
    };
    if (row.model_tier_rank != null) body.model_tier_rank = row.model_tier_rank;
    if (ticketId)      body.ticket_id = ticketId;
    if (row.player_id) body.player_id = row.player_id;
    if (row.team)      body.team      = row.team;
    if (row.pitcher)   body.pitcher   = row.pitcher;
    return body;
  }

  /* addLeg — normalized row shape:
       player_id, name, teamAbbr, team, pitcher, pitcher_name,
       model_prob (decimal), tier, model_tier_rank, board,
       hrprob, barrel, hh  */
  async function addLeg(row) {
    var key = row.player_id || row.name;
    var cur = _state.cardStatus[key] || 'idle';

    if (cur === 'loading' || cur === 'added') return;

    if (cur === 'noauth') {
      var authBtn = document.querySelector('#auth-root button');
      if (authBtn) authBtn.click();
      return;
    }

    _state.cardStatus = Object.assign({}, _state.cardStatus, { [key]: 'loading' });
    _notify();

    if (!window.__hrAuth || !window.__hrAuth.authFetch) {
      _state.cardStatus = Object.assign({}, _state.cardStatus, { [key]: 'noauth' });
      _notify();
      return;
    }

    var body = buildLegPayload(row, _state.ticketId);

    try {
      var res = await window.__hrAuth.authFetch(
        'https://mlb-hr-api.fly.dev/api/tickets/leg',
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      );
      if (res._noAuth) {
        _state.cardStatus = Object.assign({}, _state.cardStatus, { [key]: 'noauth' });
        _notify();
        var authBtn = document.querySelector('#auth-root button');
        if (authBtn) authBtn.click();
        return;
      }
      if (!res.ok) {
        _state.cardStatus = Object.assign({}, _state.cardStatus, { [key]: 'error' });
        _notify();
        return;
      }
      var data = await res.json();
      if (!_state.ticketId) _state.ticketId = data.ticket_id;
      var n = _state.legs.length + 1;
      _state.legs = _state.legs.concat([{
        n:            n,
        name:         row.name,
        teamAbbr:     row.teamAbbr,
        tier:         row.tier,
        hrprob:       row.hrprob,
        barrel:       row.barrel,
        hh:           row.hh,
        pitcher_name: row.pitcher_name,
        id:           row.player_id,
      }]);
      _state.cardStatus = Object.assign({}, _state.cardStatus, { [key]: 'added' });
      _notify();
    } catch (_e) {
      _state.cardStatus = Object.assign({}, _state.cardStatus, { [key]: 'error' });
      _notify();
    }
  }

  function removeLeg(n) {
    _state.legs = _state.legs.filter(function (l) { return l.n !== n; });
    _notify();
  }

  window.__hrSlip = {
    getState:        getState,
    subscribe:       subscribe,
    addLeg:          addLeg,
    removeLeg:       removeLeg,
    buildLegPayload: buildLegPayload,
    openSlip:        openSlip,
    closeSlip:       closeSlip,
  };
})();
