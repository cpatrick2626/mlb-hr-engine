/* HR Engine — "All Batters" leaderboard / matchup table.
   Reveals: 4-tier system (SIGNAL/ELITE/EDGE/WATCH), matchup-quality donut gauge,
   and conditional-format heatmap cells (solid fills + tinted text). */

const TIER_STYLES = {
  APEX:   { color: "#ff3344", ring: "rgba(255,51,68,0.7)",   dot: "#ff3344" },
  SIGNAL: { color: "#3b6fff", ring: "rgba(59,111,255,0.6)",  dot: "#3b6fff" },
  ELITE:  { color: "#ff8a93", ring: "rgba(255,138,147,0.6)", dot: "#ff8a93" },
  EDGE:   { color: "#1aff66", ring: "rgba(26,255,102,0.6)",  dot: "#1aff66" },
  WATCH:  { color: "#ffb020", ring: "rgba(255,176,32,0.6)",  dot: "#ffb020" },
  COLD:   { color: "#6b7872", ring: "rgba(107,120,114,0.5)", dot: "#6b7872" },
};

const TierBadge = ({ tier }) => {
  const s = TIER_STYLES[tier] || TIER_STYLES.SIGNAL;
  return (
    <span className="hr-tierbadge" style={{ color: s.color, boxShadow: `inset 0 0 0 1.5px ${s.ring}` }}>
      {tier}
    </span>
  );
};

/* Donut gauge: fill 0..1, color follows quality. */
const MatchupGauge = ({ quality }) => {
  const map = {
    ELITE:  { pct: 1.0,  color: "#4ade80", label: "ELITE MATCHUP" },
    STRONG: { pct: 0.82, color: "#1aff66", label: "STRONG MATCHUP" },
    AVG:    { pct: 0.5,  color: "#ffb020", label: "AVG MATCHUP" },
    WEAK:   { pct: 0.28, color: "#ff7a45", label: "WEAK MATCHUP" },
  };
  const q = map[quality] || map.AVG;
  const r = 9, c = 2 * Math.PI * r;
  return (
    <div className="hr-gauge">
      <svg width="26" height="26" viewBox="0 0 26 26">
        <circle cx="13" cy="13" r={r} fill="none" stroke="rgba(180,220,200,0.12)" strokeWidth="3.5" />
        <circle
          cx="13" cy="13" r={r} fill="none"
          stroke={q.color} strokeWidth="3.5" strokeLinecap="round"
          strokeDasharray={`${c * q.pct} ${c}`}
          transform="rotate(-90 13 13)"
          style={{ filter: `drop-shadow(0 0 3px ${q.color}99)` }}
        />
      </svg>
      <span className="hr-gauge__label" style={{ color: q.color }}>{q.label}</span>
    </div>
  );
};

/* Column definitions with threshold-based colorize.
   mode: "solid" = saturated cell fill, "tint" = colored text, "plain" = white, "empty" = dashes. */
const COLS = [
  { key: "pa",      head: "PA",       mode: "plain" },
  { key: "avg",     head: "AVG",      mode: "solid", hi: 0.270, lo: 0.230, fmt: (v) => v.toFixed(3).replace(/^0/, "") },
  { key: "slg",     head: "SLG",      mode: "emptyred" },
  { key: "babip",   head: "BABIP",    mode: "solid", hi: 0.310, lo: 0.265, fmt: (v) => v.toFixed(3).replace(/^0/, "") },
  { key: "gb",      head: "GB%",      mode: "tint",  hi: 40,  lo: 37,  fmt: (v) => v.toFixed(1) + "%" },
  { key: "hh",      head: "HH%",      mode: "tint",  hi: 42,  lo: 35,  fmt: (v) => v.toFixed(1) + "%" },
  { key: "ld",      head: "LD%",      mode: "tint",  hi: 25,  lo: 20,  fmt: (v) => v.toFixed(1) + "%" },
  { key: "barrel",  head: "BARREL%",  mode: "tint",  hi: 5.0, lo: 3.5, fmt: (v) => v.toFixed(1) + "%" },
  { key: "ev",      head: "EV",       mode: "tint",  hi: 90,  lo: 87,  fmt: (v) => v.toFixed(1) },
  { key: "la",      head: "LA°",      mode: "tint",  hi: 10,  lo: 7,   fmt: (v) => v.toFixed(1) + "°" },
  { key: "pull",    head: "PULL%",    mode: "tint",  hi: 38,  lo: 32,  fmt: (v) => v.toFixed(1) + "%" },
  { key: "center",  head: "CENTER%",  mode: "tint",  hi: 40,  lo: 35,  fmt: (v) => v.toFixed(1) + "%" },
  { key: "opphr",   head: "OPP HR/9", mode: "tint",  hi: 1.5, lo: 1.0, fmt: (v) => v.toFixed(2) },
  { key: "xwoba",   head: "xwOBA",    mode: "tint",  hi: 0.330, lo: 0.290, fmt: (v) => v.toFixed(3).replace(/^0/, "") },
  { key: "hrpa",    head: "HR/PA",    mode: "plain", fmt: (v) => v.toFixed(3) },
  { key: "fanduel", head: "FANDUEL",  mode: "empty" },
];

const HR_LB_FD_URL = "https://sportsbook.fanduel.com/search";

/* Normalize a display name for FD search URL only — strips generational suffixes
   (Jr./Sr./II/III/IV) and accent-folds to ASCII. Display name is never mutated. */
function fdSearchName(displayName) {
  return (displayName || "")
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/,?\s*(Jr\.?|Sr\.?|II|III|IV)\s*$/i, "")
    .trim();
}

function hrLbFanDuelUrl(term) {
  const q = fdSearchName(term);
  return q
    ? `${HR_LB_FD_URL}?q=${encodeURIComponent(q)}`
    : "https://sportsbook.fanduel.com/baseball/mlb?tab=player-home-runs";
}

function hrLbOpenFanduel(e, playerName) {
  e.stopPropagation();
  e.preventDefault();
  const term = playerName;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(term).catch(() => {});
  }
  window.open(hrLbFanDuelUrl(term), "_blank", "noopener");
  let el = document.getElementById("hr-lb-fd-toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "hr-lb-fd-toast";
    el.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a2030;border:1px solid #3b6fff;color:#e0e8ff;padding:10px 18px;border-radius:8px;font-size:13px;font-family:inherit;z-index:9999;pointer-events:none;transition:opacity .3s;white-space:nowrap;";
    document.body.appendChild(el);
  }
  el.textContent = "Copied FanDuel search: " + term;
  el.style.opacity = "1";
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.opacity = "0"; }, 2800);
}

function cellStyle(col, value) {
  if (value == null) return { cls: "", text: "—", style: {} };
  if (col.mode === "empty") return { cls: "is-empty", text: "—", style: {} };
  if (col.mode === "emptyred") return { cls: "fill-empty-red", text: "—", style: {} };
  const text = col.fmt ? col.fmt(value) : String(value);
  if (col.mode === "plain") return { cls: "", text, style: {} };

  const good = value >= col.hi;
  const bad  = value <= col.lo;
  if (col.mode === "solid") {
    if (good) return { cls: "fill-green", text, style: {} };
    if (bad)  return { cls: "fill-red",   text, style: {} };
    return { cls: "", text, style: {} };
  }
  // tint
  if (good) return { cls: "tint-green", text, style: {} };
  if (bad)  return { cls: "tint-red",   text, style: {} };
  return { cls: "", text, style: {} };
}

const LB_SLIP_COLORS = {
  idle:   { border: 'rgba(59,111,255,0.6)',  color: '#3b6fff' },
  loading:{ border: 'rgba(107,120,114,0.4)', color: '#6b7872' },
  added:  { border: 'rgba(26,255,102,0.6)',  color: '#1aff66' },
  error:  { border: 'rgba(255,51,68,0.6)',   color: '#ff3344' },
  noauth: { border: 'rgba(255,176,32,0.5)',  color: '#ffb020' },
};
const LB_SLIP_GLYPH = { idle: '+', loading: '…', added: '✓', error: '!', noauth: '⚿' };
const LB_SLIP_TITLE = { idle: 'Add to slip', loading: 'Adding…', added: 'Added to slip', error: 'Error — retry', noauth: 'Log in to add' };

const LbSlipBtn = ({ status, onClick, label }) => {
  const s = status || 'idle';
  const c = LB_SLIP_COLORS[s] || LB_SLIP_COLORS.idle;
  const disabled = s === 'loading' || s === 'added';
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      title={LB_SLIP_TITLE[s]}
      aria-label={"Add " + label + " to slip"}
      style={{
        background: 'transparent',
        border: '1px solid ' + c.border,
        borderRadius: '3px',
        cursor: disabled ? 'default' : 'pointer',
        fontSize: '13px',
        fontWeight: '700',
        width: '24px',
        height: '24px',
        padding: '0',
        lineHeight: '1',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'inherit',
        color: c.color,
        transition: 'border-color .15s, color .15s',
        flexShrink: 0,
      }}>
      {LB_SLIP_GLYPH[s]}
    </button>
  );
};

const LeaderRow = ({ row, onOpen, onAddLeg, slipStatus = 'idle' }) => (
  <tr className="hr-lb__row" onClick={() => onOpen(row.id)}>
    <td className="hr-lb__tier"><TierBadge tier={row.tier} /></td>
    <td className="hr-lb__player">
      <span className="hr-lb__dot" style={{ background: TIER_STYLES[row.tier].dot }} />
      <span className="hr-lb__pcol">
        <span className="hr-lb__name">{row.name}</span>
        <span className="hr-lb__meta">{row.teamAbbr} <span className="hr-lb__bar">|</span> {row.bats}</span>
      </span>
    </td>
    <td className="hr-lb__gauge"><MatchupGauge quality={row.quality} /></td>
    {COLS.map((col) => {
      if (col.key === "fanduel") {
        return (
          <td key="fanduel" className="hr-lb__cell hr-lb__cell--fd" onClick={(e) => e.stopPropagation()}>
            <a href="#" className="hr-lb__fd-link" onClick={(e) => { e.stopPropagation(); e.preventDefault(); window.__hrSlip && window.__hrSlip.requestAdd({ player_id: row.id, name: row.name, teamAbbr: row.teamAbbr, team: row.teamAbbr, pitcher: row.pitcher_name, pitcher_name: row.pitcher_name, model_prob: row.model_prob, tier: row.tier, model_tier_rank: row.model_tier_rank, board: 'main', hrprob: row.hrprob, barrel: row.barrel, hh: row.hh }); }}>FD</a>
          </td>
        );
      }
      const { cls, text } = cellStyle(col, row[col.key]);
      return <td key={col.key} className={`hr-lb__cell ${cls}`}>{text}</td>;
    })}
    <td className="hr-lb__cell hr-lb__cell--slip" onClick={(e) => e.stopPropagation()}>
      <LbSlipBtn status={slipStatus} onClick={() => onAddLeg(row)} label={row.name} />
    </td>
  </tr>
);

const Leaderboard = ({ rows, onOpen, tierHeaderLabel = "TIER" }) => {
  const [slipState, setSlipState] = React.useState(() => window.__hrSlip ? window.__hrSlip.getState() : { cardStatus: {} });
  React.useEffect(() => {
    if (!window.__hrSlip) return;
    return window.__hrSlip.subscribe(() => setSlipState(window.__hrSlip.getState()));
  }, []);
  const { cardStatus } = slipState;

  const handleAddLeg = (row) => {
    if (!window.__hrSlip) return;
    window.__hrSlip.requestAdd({
      player_id:       row.id,
      name:            row.name,
      teamAbbr:        row.teamAbbr,
      team:            row.teamAbbr,
      pitcher:         row.pitcher_name,
      pitcher_name:    row.pitcher_name,
      model_prob:      row.model_prob,
      tier:            row.tier,
      model_tier_rank: row.model_tier_rank,
      board:           'main',
      hrprob:          row.hrprob,
      barrel:          row.barrel,
      hh:              row.hh,
    });
  };

  return (
    <div className="hr-lb">
      <table className="hr-lb__table">
        <thead>
          <tr>
            <th className="hr-lb__th-tier">{tierHeaderLabel}</th>
            <th className="hr-lb__th-player">PLAYER</th>
            <th className="hr-lb__th-gauge">MATCHUP QUALITY</th>
            {COLS.map((c) => <th key={c.key} className={c.key === "opphr" ? "hr-lb__th-opp" : ""}>{c.head}</th>)}
            <th className="hr-lb__th-slip"></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <LeaderRow
              key={r.id}
              row={r}
              onOpen={onOpen}
              onAddLeg={handleAddLeg}
              slipStatus={cardStatus[r.id || r.name] || 'idle'}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};

Object.assign(window, { Leaderboard, LeaderRow, TierBadge, MatchupGauge });
