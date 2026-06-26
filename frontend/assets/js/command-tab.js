/* HR Engine — COMMAND Tab (cmt-*)
   Engine-aware tactical overview. Four panels. Engine toggle: MAIN (red) / JIG (cyan).
   Reads window globals only — no fetch, no backend change, no scoring math.
   LOCKED: hrprob read directly (already ×100-equivalent). Never read hrpa here. */

// ---- helpers ----
function cmtFmt1(v)   { return v != null ? Number(v).toFixed(1) : "—"; }
function cmtFmt2(v)   { return v != null ? Number(v).toFixed(2) : "—"; }

function cmtTimeAgo(ts) {
  if (!ts) return null;
  try {
    const diff = Math.round((Date.now() - new Date(ts).getTime()) / 60000);
    if (diff < 1)  return "just now";
    if (diff < 60) return diff + "m ago";
    return Math.floor(diff / 60) + "h " + (diff % 60) + "m ago";
  } catch (_) { return null; }
}

function cmtOpponent(row, games) {
  if (!games || !row.gameId) return null;
  const g = games.find(g => g.id === row.gameId);
  if (!g || !g.teams) return null;
  return g.teams.find(t => t !== row.teamAbbr) || null;
}

function cmtGameTime(row, games) {
  if (!games || !row.gameId) return null;
  const g = games.find(g => g.id === row.gameId);
  return g ? (g.time || null) : null;
}

function cmtHrFactor(row, games) {
  if (!games || !row.gameId) return null;
  const g = games.find(g => g.id === row.gameId);
  return (g && g.hrFactor != null) ? g.hrFactor : null;
}

const CMT_ESC = {
  APEX:   { label: "CRITICAL",  priority: 0, color: "#ff3344" },
  ELITE:  { label: "HIGH",      priority: 1, color: "#ff8a93" },
  EDGE:   { label: "ELEVATED",  priority: 1, color: "#1aff66" },
  SIGNAL: { label: "MODERATE",  priority: 2, color: "#3b6fff" },
  WATCH:  { label: "LOW",       priority: 3, color: "#ffb020" },
};

const CMT_TIER_ACCENT = {
  APEX:   "#ff3344",
  ELITE:  "#ff8a93",
  EDGE:   "#1aff66",
  SIGNAL: "#3b6fff",
  WATCH:  "#ffb020",
  COLD:   "#3a4642",
};

// ============================================================
// PANEL 1 — SLATE COMMAND STRIP  [NEUTRAL]
// ============================================================
function CmtCommandStrip({ mainRows, games, generatedAt }) {
  const apexCount     = mainRows.filter(r => r.tier === "APEX").length;
  const elevatedCount = mainRows.filter(r => r.tier === "ELITE" || r.tier === "EDGE").length;
  const activeCount   = mainRows.filter(r => r.tier !== "COLD").length;
  const timeAgo       = cmtTimeAgo(generatedAt);
  const stale         = generatedAt && (Date.now() - new Date(generatedAt).getTime()) > 720 * 60000;
  const date          = generatedAt
    ? new Date(generatedAt).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })
    : "—";
  const hasData = mainRows.length > 0;

  const Cell = ({ label, val, warn, apex }) => (
    <div className="cmt-strip__cell">
      <span className="cmt-strip__eye">{label}</span>
      <span className={`cmt-strip__val${warn ? " cmt-strip__val--warn" : apex ? " cmt-strip__val--apex" : ""}`}>
        {val}
      </span>
    </div>
  );
  const Sep = () => <div className="cmt-strip__sep" />;

  return (
    <div className="cmt-strip">
      <span className="cmt-chip cmt-chip--neutral">NEUTRAL</span>
      <Cell label="DATE"      val={date} />
      <Sep />
      <Cell label="GAMES"     val={hasData ? games.length || "—" : "—"} />
      <Sep />
      <Cell label="BATTERS"   val={hasData ? mainRows.length : "—"} />
      <Sep />
      <Cell label="CRITICAL"  val={hasData ? apexCount : "—"} apex={apexCount > 0} />
      <Sep />
      <Cell label="ELEVATED"  val={hasData ? elevatedCount : "—"} />
      <Sep />
      <Cell label="ACTIVE"    val={hasData ? activeCount : "—"} />
      <div className="cmt-strip__push" />
      {timeAgo && (
        <Cell label="SYNCED" val={timeAgo} warn={stale} />
      )}
    </div>
  );
}

// ============================================================
// PANEL 2 — PRIMARY HR THREAT ZONE  [MAIN red / JIG cyan]
// ============================================================
function CmtPill({ label, val, color, barrel, env }) {
  const cls = barrel ? "cmt-pill cmt-pill--barrel"
            : env    ? "cmt-pill cmt-pill--env"
            :          "cmt-pill";
  return (
    <span className={cls} style={color ? { "--pc": color } : undefined}>
      {label && <span className="cmt-pill__lbl">{label}</span>}
      <span className="cmt-pill__val">{val}</span>
    </span>
  );
}

function useSlipState() {
  const [state, setState] = React.useState(() => window.__hrSlip.getState());
  React.useEffect(() => {
    return window.__hrSlip.subscribe(() => setState(window.__hrSlip.getState()));
  }, []);
  return state;
}

function CmtThreatCard({ row, rank, engine, games, isTop, onAdd, addStatus }) {
  const isJig    = engine === "jig";
  const accentC  = isJig ? "#00d9ff" : "#ff3344";
  const tierC    = CMT_TIER_ACCENT[row.tier] || "#3a4642";
  const opp      = cmtOpponent(row, games);
  const gameTime = cmtGameTime(row, games);
  const hrFactor = cmtHrFactor(row, games);
  const hvyFlag  = row.opphr != null && Number(row.opphr) >= 1.3;

  // LOCKED: read hrprob directly — it is already ×100
  const hrProbDisplay = row.hrprob != null ? Number(row.hrprob).toFixed(1) + "%" : "—";

  const slipStatus = addStatus || 'idle';
  const slipLabel  = slipStatus === 'loading' ? '…'
    : slipStatus === 'added'  ? '✓'
    : slipStatus === 'error'  ? '!'
    : slipStatus === 'noauth' ? '🔒'
    : '+';
  const slipTitle  = slipStatus === 'added'  ? 'Added to slip'
    : slipStatus === 'noauth' ? 'Sign in to add'
    : 'Add to slip';

  return (
    <div
      className={`cmt-card${isTop ? " cmt-card--top" : ""}`}
      style={{
        "--ac": accentC,
        "--tier-c": tierC,
        boxShadow: isTop
          ? `0 0 0 1px ${accentC}55, 0 0 20px ${accentC}1a`
          : undefined,
      }}
    >
      <div className="cmt-card__hairline" style={{ background: tierC, boxShadow: `0 0 6px ${tierC}88` }} />

      {isTop && (
        <React.Fragment>
          <span className="cmt-card__corner cmt-card__corner--tl" style={{ "--cc": accentC }} />
          <span className="cmt-card__corner cmt-card__corner--tr" style={{ "--cc": accentC }} />
          <span className="cmt-card__corner cmt-card__corner--bl" style={{ "--cc": accentC }} />
          <span className="cmt-card__corner cmt-card__corner--br" style={{ "--cc": accentC }} />
        </React.Fragment>
      )}

      <div className="cmt-card__rank">#{rank}</div>

      <div className="cmt-card__body">
        <div className="cmt-card__name">{row.name || "—"}</div>
        <div className="cmt-card__meta">
          {row.teamAbbr && <span className="cmt-card__team">{row.teamAbbr}</span>}
          {opp          && <span className="cmt-card__opp">vs {opp}</span>}
          {gameTime     && <span className="cmt-card__time">{gameTime}</span>}
        </div>

        {/* PRIMARY pills */}
        <div className="cmt-card__pills">
          {!isJig ? (
            <CmtPill label="HR PROB" val={hrProbDisplay} color={accentC} />
          ) : (
            <React.Fragment>
              <CmtPill label="JIG IDX" val={row.jigScore != null ? Number(row.jigScore).toFixed(0) : "—"} color={accentC} />
              {row.quality && <CmtPill label="MATCHUP" val={row.quality} color={accentC} />}
              {hvyFlag && <span className="cmt-pill cmt-pill--hvy">HVY</span>}
            </React.Fragment>
          )}
        </div>

        {/* SECONDARY pills */}
        <div className="cmt-card__secondary">
          {row.barrel != null && <CmtPill label="BARREL" val={cmtFmt1(row.barrel) + "%"} barrel />}
          {row.hh     != null && <CmtPill label="HH"     val={cmtFmt1(row.hh) + "%"} />}
          {hrFactor   != null && <CmtPill label="ENV"    val={cmtFmt2(hrFactor)} env />}
        </div>

        <div className="cmt-card__tier-row">
          <span className="cmt-card__tier-lbl">{isJig ? "MODEL TIER" : "TIER"}</span>
          <span className="cmt-card__tier-val" style={{ color: tierC }}>{row.tier || "—"}</span>
        </div>

        <button
          className={`cmt-card__add cmt-card__add--${slipStatus}`}
          onClick={e => { e.stopPropagation(); onAdd && onAdd(row); }}
          disabled={slipStatus === 'loading' || slipStatus === 'added'}
          title={slipTitle}
        >{slipLabel}</button>
      </div>
    </div>
  );
}

function CmtThreatZone({ mainRows, jigRows, games, engine }) {
  const isJig = engine === "jig";
  const src   = isJig ? jigRows : mainRows;
  const cards = (isJig
    ? [...src].sort((a, b) => (b.jigScore || 0) - (a.jigScore || 0))
    : [...src]
  ).slice(0, 6);

  const { cardStatus } = useSlipState();

  const handleAdd = (row) => {
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
      board:           isJig ? 'jig' : 'main',
      hrprob:          row.hrprob,
      barrel:          row.barrel,
      hh:              row.hh,
    });
  };

  const accentC = isJig ? "#00d9ff" : "#ff3344";
  const chipCls = isJig ? "cmt-chip--jig" : "cmt-chip--main";

  return (
    <div className="cmt-zone" style={{ "--ac": accentC }}>
      <div className="cmt-zone__head">
        <span className={`cmt-chip ${chipCls}`}>{isJig ? "JIG" : "MAIN"}</span>
        <span className="cmt-zone__label">PRIMARY HR THREAT ZONE</span>
        <span className="cmt-zone__sub">
          {isJig ? "JIG SCORE DESC · TOP 6" : "MAIN HR PROB DESC · TOP 6"}
        </span>
      </div>
      <div className="cmt-zone__cards">
        {cards.length === 0
          ? <div className="cmt-empty">NO DATA</div>
          : cards.map((row, i) => (
              <CmtThreatCard
                key={row.name || i}
                row={row} rank={i + 1}
                engine={engine} games={games}
                isTop={i === 0}
                onAdd={handleAdd}
                addStatus={cardStatus[row.id || row.name] || 'idle'}
              />
            ))}
      </div>
    </div>
  );
}

// ============================================================
// PANEL 3 — PITCHER VULNERABILITY STRIP  [NEUTRAL]
// ============================================================
function cmtPvsDedupe(rows) {
  const seen = new Map();
  for (const r of rows) {
    const key = r.pitcher_id != null ? "id:" + r.pitcher_id
              : r.pitcher_name        ? "nm:" + r.pitcher_name
              : null;
    if (key && !seen.has(key)) seen.set(key, r);
  }
  return [...seen.values()];
}

function cmtPvsBucket(opphr) {
  if (opphr == null) return { label: "PENDING",     color: "#6b7872" };
  if (opphr >= 1.3)  return { label: "EXPLOITABLE", color: "#1aff66" };
  if (opphr >= 0.9)  return { label: "ELEVATED",    color: "#ffb020" };
  return               { label: "STANDARD",    color: "#6b7872" };
}

function CmtPvsStrip({ mainRows }) {
  const pitchers = cmtPvsDedupe(mainRows)
    .sort((a, b) => {
      const ao = a.opphr ?? -1, bo = b.opphr ?? -1;
      if (bo !== ao) return bo - ao;
      return (b.pitcher_barrel_allowed ?? -1) - (a.pitcher_barrel_allowed ?? -1);
    })
    .slice(0, 7);

  return (
    <div className="cmt-pvs">
      <div className="cmt-pvs__head">
        <span className="cmt-chip cmt-chip--neutral">NEUTRAL</span>
        <span className="cmt-pvs__label">PITCHER VULNERABILITY</span>
        <span className="cmt-pvs__sub">HR/9 DESCENDING · NEUTRAL · deduped by pitcher</span>
      </div>
      <div className="cmt-pvs__cards">
        {pitchers.length === 0
          ? <div className="cmt-empty">NO DATA</div>
          : pitchers.map((p, i) => {
              const bucket = cmtPvsBucket(p.opphr);
              const barW   = p.opphr != null
                ? Math.min(100, Math.round((Number(p.opphr) / 2.0) * 100))
                : 0;
              const key    = p.pitcher_id != null ? "id:" + p.pitcher_id
                           : p.pitcher_name        ? "nm:" + p.pitcher_name
                           : "idx:" + i;
              return (
                <div key={key} className="cmt-pvs__card" style={{ "--tc": bucket.color }}>
                  <div className="cmt-pvs__name">{p.pitcher_name || "—"}</div>
                  <div className="cmt-pvs__hr9">{cmtFmt2(p.opphr)}</div>
                  <div className="cmt-pvs__bar-wrap">
                    <div className="cmt-pvs__bar" style={{ width: barW + "%", background: bucket.color }} />
                  </div>
                  <div className="cmt-pvs__badge">{bucket.label}</div>
                </div>
              );
            })}
      </div>
    </div>
  );
}

// ============================================================
// PANEL 4 — ESCALATION FEED  [MAIN — visible in both modes]
// ============================================================
function CmtEscFeed({ mainRows }) {
  const enriched = mainRows
    .map(r => ({ row: r, meta: CMT_ESC[r.tier] || null }))
    .filter(e => e.meta !== null)
    .sort((a, b) => {
      if (a.meta.priority !== b.meta.priority) return a.meta.priority - b.meta.priority;
      return (b.row.hrprob || 0) - (a.row.hrprob || 0);
    })
    .slice(0, 8);

  return (
    <div className="cmt-esc">
      <div className="cmt-esc__head">
        <span className="cmt-chip cmt-chip--main">MAIN</span>
        <span className="cmt-esc__label">ESCALATION FEED</span>
        <span className="cmt-esc__sub">current level only · no timestamps · MAIN</span>
      </div>
      <div className="cmt-esc__rows">
        {enriched.length === 0
          ? <div className="cmt-empty">NO DATA</div>
          : enriched.map((e, i) => {
              const liveFlag = e.row.gameStatus === "Live";
              return (
                <div
                  key={i}
                  className={`cmt-esc__row${i >= 3 ? " cmt-esc__row--dim" : ""}`}
                  style={{ "--tc": e.meta.color }}
                >
                  <span className="cmt-esc__dot" />
                  <span className="cmt-esc__level">{e.meta.label}</span>
                  <span className="cmt-esc__name">{e.row.player || e.row.name || "—"}</span>
                  {(e.row.team || e.row.teamAbbr) && (
                    <span className="cmt-esc__team">{e.row.team || e.row.teamAbbr}</span>
                  )}
                  {liveFlag && <span className="cmt-esc__live">LIVE</span>}
                </div>
              );
            })}
      </div>
    </div>
  );
}

// ============================================================
// ROOT — COMMAND TAB
// ============================================================
function CommandTabPanel() {
  const snap = () => ({
    mainRows: Array.isArray(window.LEADERBOARD_ROWS)     ? window.LEADERBOARD_ROWS     : [],
    jigRows:  Array.isArray(window.LEADERBOARD_ROWS_JIG) ? window.LEADERBOARD_ROWS_JIG : [],
    games:    Array.isArray(window.SLATE_GAMES)          ? window.SLATE_GAMES          : [],
    genAt:    window.SLATE_GENERATED_AT || null,
  });

  const [data,   setData]   = React.useState(snap);
  const [engine, setEngine] = React.useState("main");

  React.useEffect(() => {
    const handler = () => setData(snap());
    window.addEventListener("hrEngineDataLoaded", handler);
    return () => window.removeEventListener("hrEngineDataLoaded", handler);
  }, []);

  const { mainRows, jigRows, games, genAt } = data;
  const accentC = engine === "jig" ? "#00d9ff" : "#ff3344";

  return (
    <div className="cmt-root md-room">
      {/* Header: title + engine toggle */}
      <div className="cmt-header">
        <div className="cmt-header__brand">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
               style={{ filter: `drop-shadow(0 0 5px ${accentC}88)` }}>
            <circle cx="12" cy="12" r="10" stroke={accentC} strokeWidth="1.5" />
            <path d="M5 8 Q12 12 19 8 M5 16 Q12 12 19 16" stroke={accentC} strokeWidth="1.2" strokeLinecap="round" />
            <circle cx="12" cy="12" r="2.5" fill={accentC} />
          </svg>
          <span className="cmt-header__name">COMMAND</span>
          <span className="cmt-header__sub">tactical overview</span>
        </div>
        <div className="cmt-etoggle">
          <button
            className={`cmt-etoggle__btn${engine === "main" ? " cmt-etoggle__btn--on cmt-etoggle__btn--main" : ""}`}
            onClick={() => setEngine("main")}
          >MAIN</button>
          <button
            className={`cmt-etoggle__btn${engine === "jig" ? " cmt-etoggle__btn--on cmt-etoggle__btn--jig" : ""}`}
            onClick={() => setEngine("jig")}
          >JIG</button>
        </div>
      </div>

      {/* P1 — Slate Command Strip [NEUTRAL] */}
      <CmtCommandStrip mainRows={mainRows} games={games} generatedAt={genAt} />

      {/* P2 — HR Threat Zone [MAIN/JIG] */}
      <CmtThreatZone mainRows={mainRows} jigRows={jigRows} games={games} engine={engine} />

      {/* P3 — Pitcher Vulnerability Strip [NEUTRAL] */}
      <CmtPvsStrip mainRows={mainRows} />

      {/* P4 — Escalation Feed [MAIN, shown in both modes] */}
      <CmtEscFeed mainRows={mainRows} />
    </div>
  );
}

Object.assign(window, { CommandTabPanel });
