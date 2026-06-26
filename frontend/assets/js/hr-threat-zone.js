/* HR Engine — HR Threat Zone
   Desktop: Primary HR Threat Zone — top 5 batters by MAIN model HR probability (hrprob).
   Mobile:  Top HR Threats strip — top 3 compact tap-friendly cards.
   Receives rows prop already filtered/sorted upstream by Stage.
   Display-only — no scoring changes, no API calls, no new formulas.
   Step 2a: "Add to Ticket" button calls POST /api/tickets/leg with user JWT.
   Ticket state lives in HRThreatZone (shared across cards so 2nd+ leg reuses same ticket_id). */

const HRTZ_TIER_COLOR = {
  APEX:   "#ff3344",
  ELITE:  "#ff8a93",
  EDGE:   "#1aff66",
  SIGNAL: "#3b6fff",
  WATCH:  "#ffb020",
  COLD:   "#6b7872",
};

function hrtzLabels(row) {
  const tags = [];
  if      (row.tier === "APEX")  tags.push({ t: "APEX",    c: "#ff3344" });
  else if (row.tier === "ELITE") tags.push({ t: "ELITE",   c: "#ff8a93" });
  if (row.barrel != null && row.barrel >= 8)   tags.push({ t: "BARREL",   c: "#1aff66" });
  else if (row.barrel != null && row.barrel >= 6) tags.push({ t: "BARREL+", c: "#6dffae" });
  if (row.hh != null && row.hh >= 45)           tags.push({ t: "HH ELITE", c: "#00d9ff" });
  return tags.slice(0, 3);
}

function hrtzFmtProb(v) {
  return v != null ? Number(v).toFixed(1) + "%" : "—";
}

function HRThreatCard({ row, rank, compact, onAdd, addStatus }) {
  const tc   = HRTZ_TIER_COLOR[row.tier] || "#6b7872";
  const tags = hrtzLabels(row);
  const prob = hrtzFmtProb(row.hrprob);
  const name = row.name || "—";
  const lastName = name.replace("…", "").split(" ").slice(-1)[0] || name;
  const pitcherLast = row.pitcher_name
    ? row.pitcher_name.replace("…", "").split(" ").slice(-1)[0]
    : null;

  const status = addStatus || 'idle';
  const btnLabel = status === 'loading' ? '…'
    : status === 'added'  ? '✓'
    : status === 'error'  ? '!'
    : status === 'noauth' ? 'LOGIN'
    : '+';
  const btnTitle = status === 'noauth' ? 'Sign in to add'
    : status === 'added'  ? 'Added to ticket'
    : status === 'error'  ? 'Error — click to retry'
    : 'Add to ticket';

  return (
    <div className={`hrtz-card${compact ? " hrtz-card--compact" : ""}`}
         style={{ "--tc": tc }}>
      <div className="hrtz-card__rank">#{rank}</div>
      <div className="hrtz-card__body">
        <div className="hrtz-card__name">{compact ? lastName : name}</div>
        <div className="hrtz-card__meta">
          {row.teamAbbr  ? <span className="hrtz-card__team">{row.teamAbbr}</span>       : null}
          {pitcherLast   ? <span className="hrtz-card__vs">vs {pitcherLast}</span>        : null}
        </div>
        {tags.length > 0 && (
          <div className="hrtz-card__tags">
            {tags.map((tag, i) => (
              <span key={i} className="hrtz-card__tag"
                    style={{ color: tag.c, boxShadow: `inset 0 0 0 1px ${tag.c}55` }}>
                {tag.t}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="hrtz-card__stat">
        <div className="hrtz-card__prob">{prob}</div>
        <div className="hrtz-card__prob-lbl">HR PROB</div>
        {!compact && <div className="hrtz-card__tier">{row.tier || "—"}</div>}
        <button
          className={`hrtz-card__add hrtz-card__add--${status}`}
          onClick={() => onAdd && onAdd(row)}
          disabled={status === 'loading' || status === 'added'}
          title={btnTitle}
        >
          {btnLabel}
        </button>
      </div>
    </div>
  );
}

function HRThreatZone({ rows, isJigContext }) {
  const sorted  = [...(rows || [])].sort((a, b) => (b.hrprob || 0) - (a.hrprob || 0));
  const desktop = sorted.slice(0, 5);
  const mobile  = sorted.slice(0, 3);

  // Ticket state — shared across all cards so 2nd+ leg appends to the same ticket
  const [ticketId, setTicketId] = React.useState(null);
  const [legs, setLegs] = React.useState([]);          // [{n, name, teamAbbr, tier, hrprob, barrel, hh, pitcher_name, id}] — session only
  const [cardStatus, setCardStatus] = React.useState({}); // {rowKey: 'idle'|'loading'|'added'|'error'|'noauth'}
  const [slipOpen, setSlipOpen] = React.useState(false);

  const addLeg = async (row) => {
    const key = row.id || row.name;
    const cur = cardStatus[key] || 'idle';

    // Already in-flight or done — no-op (button is disabled for these states)
    if (cur === 'loading' || cur === 'added') return;

    // Not logged in — open sign-in modal and stop
    if (cur === 'noauth') {
      const authBtn = document.querySelector('#auth-root button');
      if (authBtn) authBtn.click();
      return;
    }

    setCardStatus(s => ({ ...s, [key]: 'loading' }));

    if (!window.__hrAuth?.authFetch) {
      setCardStatus(s => ({ ...s, [key]: 'noauth' }));
      return;
    }

    const body = {
      board:        row._board || 'main',
      name:         row.name,
      model_prob:   row.model_prob,
      tier:         row.tier,
      generated_at: window.SLATE_GENERATED_AT || null,
    };
    if (row.model_tier_rank != null) body.model_tier_rank = row.model_tier_rank;
    // First leg: omit ticket_id → backend opens new ticket and returns ticket_id
    // Subsequent legs: pass the ticket_id returned from the first leg
    if (ticketId) body.ticket_id = ticketId;
    // Calibration fields — sent when available on the row; backend writes NULL for omitted fields
    if (row.id)           body.player_id = row.id;
    if (row.teamAbbr)     body.team      = row.teamAbbr;
    if (row.pitcher_name) body.pitcher   = row.pitcher_name;
    // opponent: not in row shape — omitted (NULL server-side)
    // market_odds_american / market_prob: not on row — omitted (NULL server-side, no source yet)

    try {
      const res = await window.__hrAuth.authFetch(
        'https://mlb-hr-api.fly.dev/api/tickets/leg',
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      );
      if (res._noAuth) {
        setCardStatus(s => ({ ...s, [key]: 'noauth' }));
        const authBtn = document.querySelector('#auth-root button');
        if (authBtn) authBtn.click();
        return;
      }
      if (!res.ok) {
        setCardStatus(s => ({ ...s, [key]: 'error' }));
        return;
      }
      const data = await res.json();
      if (!ticketId) setTicketId(data.ticket_id);
      setLegs(l => [...l, {
        n:            l.length + 1,
        name:         row.name,
        teamAbbr:     row.teamAbbr,
        tier:         row.tier,
        hrprob:       row.hrprob,
        barrel:       row.barrel,
        hh:           row.hh,
        pitcher_name: row.pitcher_name,
        id:           row.id,
      }]);
      setCardStatus(s => ({ ...s, [key]: 'added' }));
    } catch (_e) {
      setCardStatus(s => ({ ...s, [key]: 'error' }));
    }
  };

  const removeLeg = (n) => setLegs(ls => ls.filter(l => l.n !== n));

  if (!desktop.length) return null;

  const label = isJigContext ? "JIG TOP TARGETS"       : "PRIMARY HR THREAT ZONE";
  const sub   = isJigContext ? "ranked by JIG score"   : "ranked by MAIN model HR probability · display only";

  return (
    <div className={`hrtz-zone${isJigContext ? " hrtz-zone--jig" : ""}`}>
      <div className="hrtz-zone__head">
        <span className="hrtz-zone__label">{label}</span>
        <span className="hrtz-zone__sub">{sub}</span>
      </div>

      {/* Desktop: top 5 */}
      <div className="hrtz-desktop">
        {desktop.map((row, i) => (
          <HRThreatCard key={row.name || i} row={row} rank={i + 1} compact={false}
            onAdd={addLeg} addStatus={cardStatus[row.id || row.name] || 'idle'} />
        ))}
      </div>

      {/* Mobile: top 3 compact */}
      <div className="hrtz-mobile">
        {mobile.map((row, i) => (
          <HRThreatCard key={row.name || i} row={row} rank={i + 1} compact={true}
            onAdd={addLeg} addStatus={cardStatus[row.id || row.name] || 'idle'} />
        ))}
      </div>

      {/* Session tray — shows legs added this session + VIEW TICKET button */}
      {legs.length > 0 && (
        <div className="hrtz-tray">
          <span className="hrtz-tray__head">TICKET · {legs.length} LEG{legs.length !== 1 ? 'S' : ''}</span>
          <div className="hrtz-tray__legs">
            {legs.map((leg, i) => (
              <div key={i} className="hrtz-tray__leg">
                <span className="hrtz-tray__name">{leg.name}</span>
                <span className="hrtz-tray__tier">{leg.tier}</span>
              </div>
            ))}
          </div>
          <button
            className="hrtz-tray__view-btn"
            onClick={() => setSlipOpen(true)}
          >
            VIEW TICKET →
          </button>
        </div>
      )}

      {/* Ticket Command Slip overlay — portal to body, zero routing change */}
      {slipOpen && window.TicketCommandSlip && React.createElement(
        window.TicketCommandSlip,
        { legs, ticketId, onClose: () => setSlipOpen(false), onRemoveLeg: removeLeg }
      )}
    </div>
  );
}
