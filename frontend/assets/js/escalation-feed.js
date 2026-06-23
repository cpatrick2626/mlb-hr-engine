/* HR Engine — Escalation Feed (esc-*)
   Vertical priority list: top MAIN threats ranked by tier → hrpa.
   Source: rows prop (LEADERBOARD_ROWS, post-filter).
   MAIN-only — returns null when isJigContext is true.
   Display-only — no scoring math, no API calls, no new fetch. */

const ESC_LEVEL = {
  APEX:   { label: "CRITICAL", priority: 0, color: "#ff3344" },
  ELITE:  { label: "HIGH",     priority: 1, color: "#ff8a93" },
  EDGE:   { label: "HIGH",     priority: 1, color: "#1aff66" },
  SIGNAL: { label: "MODERATE", priority: 2, color: "#3b6fff" },
  WATCH:  { label: "LOW",      priority: 3, color: "#ffb020" },
  // COLD: excluded (no entry → filtered out)
};

function escHeadline(row) {
  const barrel = row.barrel != null ? Number(row.barrel) : null;
  const hh     = row.hh     != null ? Number(row.hh)     : null;
  const opphr  = row.opphr  != null ? Number(row.opphr)  : null;
  const hrpa   = row.hrpa   != null ? Number(row.hrpa)   : null;

  if (barrel !== null && barrel >= 8)   return "BARREL " + barrel.toFixed(1) + "%";
  if (hh     !== null && hh     >= 45)  return "HH " + hh.toFixed(1) + "%";
  if (opphr  !== null && opphr  >= 1.3) return "HVY PITCHER " + opphr.toFixed(2) + " HR/9";
  if (hrpa   !== null)                  return "HR PROB " + (hrpa * 100).toFixed(1) + "%";
  return null;
}

function EscRow({ row, meta }) {
  const headline = escHeadline(row);
  if (headline === null) return null;
  const name = row.player || row.name || "—";
  const team = row.team   || "";

  return (
    <div className="esc-row" style={{ "--tc": meta.color }}>
      <span className="esc-row__level">{meta.label}</span>
      <span className="esc-row__name">{name}</span>
      {team && <span className="esc-row__team">{team}</span>}
      <span className="esc-row__stat">{headline}</span>
      <span className="esc-row__badge">LIVE</span>
    </div>
  );
}

function EscalationFeed({ rows, isJigContext }) {
  if (isJigContext) return null;

  const src = Array.isArray(rows) ? rows : [];

  const enriched = src
    .map(r => ({ row: r, meta: ESC_LEVEL[r.tier] || null }))
    .filter(e => e.meta !== null); // COLD and unknown tiers excluded

  if (!enriched.length) return null;

  enriched.sort((a, b) => {
    if (a.meta.priority !== b.meta.priority) return a.meta.priority - b.meta.priority;
    const ah = a.row.hrpa != null ? Number(a.row.hrpa) : 0;
    const bh = b.row.hrpa != null ? Number(b.row.hrpa) : 0;
    return bh - ah;
  });

  const desktop = enriched.slice(0, 8);
  const mobile  = enriched.slice(0, 5);

  return (
    <div className="esc-feed">
      <div className="esc-feed__head">
        <span className="esc-feed__label">ESCALATION FEED</span>
        <span className="esc-feed__sub">threat priority · MAIN · display only</span>
      </div>
      <div className="esc-desktop">
        {desktop.map((e, i) => (
          <EscRow key={i} row={e.row} meta={e.meta} />
        ))}
      </div>
      <div className="esc-mobile">
        {mobile.map((e, i) => (
          <EscRow key={i} row={e.row} meta={e.meta} />
        ))}
      </div>
    </div>
  );
}
