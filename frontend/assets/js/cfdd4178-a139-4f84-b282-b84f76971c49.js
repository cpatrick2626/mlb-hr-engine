/* HR Engine — Stage: the persistent "big open area" where rooms render.
   Full Slate = live leaderboard. Other lenses fall back to a radar scope. */

const RadarScope = ({ engineName, lensName, accent }) =>
<div className="md-radar">
    <svg className="md-radar__svg" viewBox="0 0 800 800" fill="none">
      {/* concentric range rings */}
      {[120, 200, 280, 350].map((r, i) =>
    <circle key={r} cx="400" cy="400" r={r}
    stroke="rgba(0,217,255,0.14)" strokeWidth={i === 3 ? 1 : 1} />
    )}
      <circle cx="400" cy="400" r="368" stroke="rgba(0,217,255,0.10)" strokeWidth="1" strokeDasharray="2 7" />
      {/* crosshair axes */}
      <line x1="400" y1="40" x2="400" y2="760" stroke="rgba(0,217,255,0.08)" strokeWidth="1" strokeDasharray="3 6" />
      <line x1="40" y1="400" x2="760" y2="400" stroke="rgba(0,217,255,0.06)" strokeWidth="1" strokeDasharray="3 6" />
      {/* baseball diamond / infield */}
      <g stroke="rgba(0,217,255,0.30)" strokeWidth="1.5" fill="none">
        <path d="M400 520 L300 420 L400 320 L500 420 Z" />
        <path d="M300 420 L210 300 M500 420 L590 300" strokeWidth="1" opacity="0.6" />
        <path d="M260 360 A200 200 0 0 1 540 360" strokeWidth="1" opacity="0.4" />
      </g>
      {/* bases */}
      {[[400, 520], [300, 420], [400, 320], [500, 420]].map(([x, y], i) =>
    <circle key={i} cx={x} cy={y} r="5" fill={accent} opacity="0.85"
    style={{ filter: `drop-shadow(0 0 5px ${accent})` }} />
    )}
      {/* home plate marker */}
      <rect x="392" y="524" width="16" height="16" rx="2" fill="none" stroke={accent} strokeWidth="1.5" transform="rotate(45 400 532)" />
      {/* sweep */}
      <g className="md-radar__sweep">
        <defs>
          <linearGradient id="md-sweepgrad" x1="400" y1="400" x2="760" y2="400" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="rgba(0,217,255,0.0)" />
            <stop offset="1" stopColor="rgba(0,217,255,0.22)" />
          </linearGradient>
        </defs>
        <path d="M400 400 L760 400 A360 360 0 0 0 690 190 Z" fill="url(#md-sweepgrad)" />
        <line x1="400" y1="400" x2="760" y2="400" stroke="rgba(0,217,255,0.5)" strokeWidth="1.5" />
      </g>
    </svg>
    <div className="md-radar__caption">
      <div className="md-radar__room"><span className="accent">{engineName}</span> · {lensName}</div>
      <div className="md-radar__status">Module standing by — calibrating model</div>
    </div>
  </div>;


const RoomHead = ({ eyebrow, title, right }) =>
<div className="md-room__head" data-comment-anchor="7500c9f86a-div-49-3">
    <div className="md-room__titles">
      <div className="md-room__eyebrow">{eyebrow}</div>
      <div className="md-room__title">{title}</div>
    </div>
    {right}
  </div>;


/* ---- JIG Builder (a lightweight build console) ---- */
const JigBuilder = ({ eyebrow }) =>
<div className="md-room" data-comment-anchor="672910cafa-div-60-1">
    <RoomHead eyebrow={eyebrow} title="JIG Builder"
  right={<div className="md-room__chips"><span className="md-room__chip is-on">CONFIGURE</span><span className="md-room__chip">SIMULATE</span><span className="md-room__chip">DEPLOY</span></div>} />
    <div className="md-jig">
      <div className="md-jig__config">
        <div className="md-jig__sec">PARAMETERS</div>
        <Stepper label="Min HR Env Score" value={7.5} step={0.1} decimals={1} max={10} />
        <Stepper label="Min Barrel %" value={5.0} step={0.5} decimals={1} max={100} />
        <Dropdown label="Handedness Split" options={["Any", "LHB vs RHP", "RHB vs LHP", "Same-Side"]} />
        <Toggle label="Confirmed Lineups Only" on={true} />
        <Toggle label="Live Games Only" on={false} />
      </div>
      <div className="md-jig__preview">
        <div className="md-jig__sec">JIG PREVIEW — 4 LEGS</div>
        {[
      ["AARON JUDGE", "NYY", "9.6"], ["KYLE SCHWARBER", "PHI", "9.1"],
      ["SHOHEI OHTANI", "LAD", "8.8"], ["YORDAN ÁLVAREZ", "HOU", "8.4"]].
      map(([n, t, s]) =>
      <div className="md-jig__leg" key={n}>
            <span className="md-jig__leg-dot" />
            <span className="md-jig__leg-name">{n}</span>
            <span className="md-jig__leg-team">{t}</span>
            <span className="md-jig__leg-score">{s}</span>
          </div>
      )}
        <div className="md-jig__combined">COMBINED EDGE <b>+412</b></div>
      </div>
    </div>
  </div>;


const Stage = ({ engine, lens, ccOpen, onCloseCC, appliedFilters, onApplyFilters, onClearFilters, onOpenPlayer }) => {
  const eyebrow = `${engine.name}${engine.suffix ? " " + engine.suffix : ""}${lens ? "  /  " + lens.name.toUpperCase() : ""}`;
  const [mainRows, setMainRows] = React.useState([]);
  const [jigRows, setJigRows] = React.useState([]);
  const [fetchDone, setFetchDone] = React.useState(false);
  const [fetchFailed, setFetchFailed] = React.useState(false);
  React.useEffect(() => {
    const hydrateRows = () => {
      const nextMainRows = Array.isArray(window.LEADERBOARD_ROWS) ? window.LEADERBOARD_ROWS : [];
      const nextJigRows = Array.isArray(window.LEADERBOARD_ROWS_JIG) ? window.LEADERBOARD_ROWS_JIG : [];
      setMainRows(nextMainRows);
      setJigRows(nextJigRows);
    };
    hydrateRows();
    const onDataLoaded = (e) => {
      hydrateRows();
      setFetchFailed(!!(e.detail && e.detail._fetchFailed));
      setFetchDone(true);
    };
    window.addEventListener("hrEngineDataLoaded", onDataLoaded);
    return () => window.removeEventListener("hrEngineDataLoaded", onDataLoaded);
  }, []);
  let body;

  // Active-filter status shown on the room header (count + result count + clear).
  const filterStatus = (shown, total) => {
    const n = countActiveFilters(appliedFilters);
    if (n === 0) return null;
    return (
      <React.Fragment>
        <span className="md-room__fbadge">{n} FILTER{n > 1 ? "S" : ""} ACTIVE</span>
        <button className="md-room__clear" onClick={onClearFilters}>CLEAR</button>
      </React.Fragment>);

  };

  if (ccOpen) {
    body =
    <StageCommand
      key={`${engine.id}/${lens ? lens.id : "_"}`}
      engine={engine}
      lens={lens}
      initialFilters={appliedFilters}
      onApply={onApplyFilters}
      onClose={onCloseCC} />;


  } else if (lens && lens.id === "fullSlate") {
    if (!fetchDone) {
      body = <div className="md-room" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 11, letterSpacing: "0.22em", color: "var(--fg-3)", textTransform: "uppercase", marginBottom: 8 }}>LOADING SLATE DATA</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--fg-4)", letterSpacing: "0.08em" }}>Fetching picks from HR Engine API…</div>
        </div>
      </div>;
    } else {
      const sourceRows = engine.id === "jig" ? jigRows : mainRows;
      const rows = applyRoomFilters(sourceRows, appliedFilters);
      const nf = countActiveFilters(appliedFilters);
      if (sourceRows.length === 0) {
        const isPipelineEmpty = !fetchFailed;
        body = <div className="md-room" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ textAlign: "center", maxWidth: 420 }}>
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 9, letterSpacing: "0.28em", color: isPipelineEmpty ? "var(--amber-500)" : "var(--red-500)", textTransform: "uppercase", marginBottom: 6 }}>{isPipelineEmpty ? "PIPELINE PENDING" : "BOARD OFFLINE"}</div>
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 16, letterSpacing: "0.1em", color: "var(--fg-1)", textTransform: "uppercase", marginBottom: 10 }}>{isPipelineEmpty ? "NO SLATE DATA" : "API CONNECTION FAILED"}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--fg-3)", lineHeight: 1.6 }}>{isPipelineEmpty ? "Pipeline has not run for today's slate. Trigger: POST /api/pipeline/run with X-Cron-Secret header." : "Could not reach HR Engine API. Check connection or refresh to retry."}</div>
          </div>
        </div>;
      } else {
        body = <React.Fragment>
          <HRThreatZone rows={rows} isJigContext={engine.id === "jig"} />
          <PitcherVulnerabilityStrip rows={rows} isJigContext={engine.id === "jig"} />
          <EscalationFeed rows={rows} isJigContext={engine.id === "jig"} />
          <div className="md-room">
            <FullSlateMatrix
            rows={rows}
            total={sourceRows.length}
            onOpen={onOpenPlayer}
            filterNote={nf > 0 ? `${nf} ACTIVE FILTER${nf > 1 ? "S" : ""}` : "NO ACTIVE FILTERS"}
            isJigContext={engine.id === "jig"} />
          </div>
        </React.Fragment>;
      }
    }

  } else if (lens && lens.id === "topTargets") {
    const targetSourceRows = engine.id === "jig" ? jigRows : mainRows;
    const base = targetSourceRows.filter((r) => r.tier === "ELITE" || r.tier === "EDGE");
    const rows = applyRoomFilters(base, appliedFilters);
    body =
    <div className="md-room">
        <RoomHead eyebrow={eyebrow} title="Top Targets"
      right={<div className="md-room__meta"><span>{rows.length} / {base.length} TARGETS</span>{filterStatus()}</div>} />
        <Leaderboard rows={rows} onOpen={onOpenPlayer} tierHeaderLabel={engine.id === "jig" ? "MODEL TIER" : "TIER"} />
      </div>;

  } else if (engine.id === "command") {
    body = <CommandTabPanel />;
  } else if (lens && lens.id === "builder") {
    body = <JigCommand engine={engine} lens={lens} onOpenPlayer={onOpenPlayer} />;
  } else if (lens && lens.id === "arsenal") {
    const arsenalRows = engine.id === "jig" ? jigRows : mainRows;
    body = (
      <div className="md-room">
        <ArsenalEdgeExploit rows={applyRoomFilters(arsenalRows, appliedFilters)} />
      </div>
    );
  } else {
    body = <RadarScope engineName={engine.name + (engine.suffix ? " " + engine.suffix : "")} lensName={lens ? lens.name : "Overview"} accent={engine.color} />;
  }

  return (
    <div className="md-stage">
      <div className="md-stage__body">{body}</div>
    </div>);

};

Object.assign(window, { Stage, RadarScope, JigBuilder, RoomHead });
