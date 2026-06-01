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

const LeaderRow = ({ row, onOpen }) => (
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
      const { cls, text } = cellStyle(col, row[col.key]);
      return <td key={col.key} className={`hr-lb__cell ${cls}`}>{text}</td>;
    })}
  </tr>
);

const Leaderboard = ({ rows, onOpen }) => (
  <div className="hr-lb">
    <table className="hr-lb__table">
      <thead>
        <tr>
          <th className="hr-lb__th-tier">TIER</th>
          <th className="hr-lb__th-player">PLAYER</th>
          <th className="hr-lb__th-gauge">MATCHUP QUALITY</th>
          {COLS.map((c) => <th key={c.key} className={c.key === "opphr" ? "hr-lb__th-opp" : ""}>{c.head}</th>)}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => <LeaderRow key={r.id} row={r} onOpen={onOpen} />)}
      </tbody>
    </table>
  </div>
);

Object.assign(window, { Leaderboard, LeaderRow, TierBadge, MatchupGauge });
