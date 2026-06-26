/* HR Engine — HR Threat Zone
   Desktop: Primary HR Threat Zone — top 5 batters by MAIN model HR probability (hrprob).
   Mobile:  Top HR Threats strip — top 3 compact tap-friendly cards.
   Receives rows prop already filtered/sorted upstream by Stage.
   Display-only — no scoring changes, no API calls, no new formulas.
   Step 2a: "Add to Ticket" button delegates to window.__hrSlip.addLeg().
   Ticket state lives in window.__hrSlip (shared across all surfaces). */

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

function useSlipState() {
  const [state, setState] = React.useState(() => window.__hrSlip.getState());
  React.useEffect(() => {
    return window.__hrSlip.subscribe(() => setState(window.__hrSlip.getState()));
  }, []);
  return state;
}

function HRThreatZone({ rows, isJigContext }) {
  const sorted  = [...(rows || [])].sort((a, b) => (b.hrprob || 0) - (a.hrprob || 0));
  const desktop = sorted.slice(0, 5);
  const mobile  = sorted.slice(0, 3);

  const { ticketId, legs, cardStatus } = useSlipState();

  const addLeg = (row) => {
    window.__hrSlip.addLeg({
      player_id:       row.id,
      name:            row.name,
      teamAbbr:        row.teamAbbr,
      team:            row.teamAbbr,
      pitcher:         row.pitcher_name,
      pitcher_name:    row.pitcher_name,
      model_prob:      row.model_prob,
      tier:            row.tier,
      model_tier_rank: row.model_tier_rank,
      board:           row._board || 'main',
      hrprob:          row.hrprob,
      barrel:          row.barrel,
      hh:              row.hh,
    });
  };

  const removeLeg = (n) => window.__hrSlip.removeLeg(n);

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
            onClick={() => window.__hrSlip.openSlip()}
          >
            VIEW TICKET →
          </button>
        </div>
      )}

    </div>
  );
}
