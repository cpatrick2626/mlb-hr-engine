/* HR Engine — Slate Command Strip
   Slim status strip beneath the top bar: MAIN/JIG live status, batter count, APEX
   threat count, game count, environment (from SLATE_GAMES if present), generated time.
   Reads window globals populated by the /api/slate fetch in MasterDashboard.
   Display-only — no scoring, no API calls, no new fetch. */

function SlateCommandStrip() {
  const snapshot = () => {
    const main  = Array.isArray(window.LEADERBOARD_ROWS)     ? window.LEADERBOARD_ROWS     : [];
    const jig   = Array.isArray(window.LEADERBOARD_ROWS_JIG) ? window.LEADERBOARD_ROWS_JIG : [];
    const games = Array.isArray(window.SLATE_GAMES)          ? window.SLATE_GAMES          : [];
    return {
      mainCount:   main.length,
      jigCount:    jig.length,
      apexCount:   main.filter(r => r.tier === "APEX").length,
      gameCount:   games.length,
      envStr:      (games.find(g => g.weather) || {}).weather || null,
      generatedAt: window.SLATE_GENERATED_AT || null,
    };
  };

  const [d, setD]       = React.useState(snapshot);
  const [phase, setPhase] = React.useState("pending"); // pending | live | failed

  React.useEffect(() => {
    if ((window.LEADERBOARD_ROWS || []).length > 0) {
      setD(snapshot());
      setPhase("live");
    }
    const handler = (e) => {
      setD(snapshot());
      setPhase(e.detail && e.detail._fetchFailed ? "failed" : "live");
    };
    window.addEventListener("hrEngineDataLoaded", handler);
    return () => window.removeEventListener("hrEngineDataLoaded", handler);
  }, []);

  const fmtTs = (ts) => {
    if (!ts) return null;
    try {
      return new Date(ts).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: true });
    } catch (_) { return null; }
  };

  const ts = fmtTs(d.generatedAt);

  if (phase === "pending") {
    return (
      <div className="scs-strip scs-strip--pending">
        <span className="scs-pulse" />
        <span className="scs-acquiring">ACQUIRING SLATE</span>
      </div>
    );
  }

  const Sep = () => <div className="scs-sep" />;

  const Cell = ({ eye, val, valClass, title }) => (
    <div className="scs-cell" title={title || undefined}>
      <span className="scs-eye">{eye}</span>
      <span className={`scs-val${valClass ? " " + valClass : ""}`}>{val}</span>
    </div>
  );

  const dash = "—";

  return (
    <div className={`scs-strip scs-strip--${phase}`}>
      <Cell eye="MAIN"
            val={d.mainCount > 0 ? "LIVE" : "PENDING"}
            valClass={d.mainCount > 0 ? "scs-val--main-live" : "scs-val--warn"} />
      <Sep />
      <Cell eye="JIG"
            val={d.jigCount > 0 ? "LIVE" : "PENDING"}
            valClass={d.jigCount > 0 ? "scs-val--jig-live" : "scs-val--warn"} />
      <Sep />
      <Cell eye="BATTERS"
            val={d.mainCount > 0 ? d.mainCount : dash} />
      <Sep />
      <Cell eye="APEX THREATS"
            val={d.mainCount > 0 ? d.apexCount : dash}
            valClass={d.apexCount > 0 ? "scs-val--apex" : ""} />
      <Sep />
      <Cell eye="GAMES"
            val={d.gameCount > 0 ? d.gameCount : dash} />

      {d.envStr && (
        <React.Fragment>
          <Sep />
          <Cell eye="ENVIRONMENT"
                val={d.envStr.length > 22 ? d.envStr.slice(0, 21) + "…" : d.envStr}
                valClass="scs-val--env"
                title={d.envStr} />
        </React.Fragment>
      )}

      <div className="scs-push" />

      {ts && (
        <Cell eye="GENERATED" val={ts} valClass="scs-val--ts" />
      )}
    </div>
  );
}
