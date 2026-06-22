/* HR Engine — JIG BUILDER lens.
   Shows the Full Slate Intelligence Matrix with a Save / Load builder bar on top. */

function JigCommand({ engine, lens, onOpenPlayer }) {
  // Phase A stopgap: prefer raw slate rows if exposed; otherwise use JIG-side rows.
  // Do not default JIG Builder to MAIN leaderboard rows.
  const rawRows =
    Array.isArray(window.SLATE_ROWS_RAW) ? window.SLATE_ROWS_RAW :
    Array.isArray(window.RAW_SLATE_ROWS) ? window.RAW_SLATE_ROWS :
    Array.isArray(window.LEADERBOARD_ROWS_RAW) ? window.LEADERBOARD_ROWS_RAW :
    null;
  const builderRows =
    rawRows ||
    (Array.isArray(window.LEADERBOARD_ROWS_JIG) ? window.LEADERBOARD_ROWS_JIG :
    // Last-resort degraded fallback only if raw/JIG rows are missing entirely.
    (Array.isArray(window.LEADERBOARD_ROWS) ? window.LEADERBOARD_ROWS : []));
  const [preset, setPreset] = React.useState("DEFAULT TACTICAL");
  const [flash, setFlash] = React.useState("");

  const doSave = () => { setFlash("SAVED"); setTimeout(() => setFlash(""), 1100); };
  const doLoad = () => { setFlash("LOADED"); setTimeout(() => setFlash(""), 1100); };

  return (
    <div className="md-room jig-room">
      <div className="jig-bar">
        <div className="jig-bar__id">
          <span className="jig-bar__title">JIG BUILDER</span>
          <span className="jig-bar__preset"><span className="jig-bar__k">BUILD</span> {preset}</span>
        </div>
        <div className="jig-bar__actions">
          {flash && <span className="jig-bar__flash">✓ {flash}</span>}
          <button className="hr-btn hr-btn--ghost" onClick={doSave}>SAVE BUILDER</button>
          <button className="hr-btn hr-btn--ghost" onClick={doLoad}>LOAD BUILDER</button>
        </div>
      </div>
      <div className="jig-banner" role="status" aria-live="polite">
        <div className="jig-banner__title">JIG BUILDER · PHASE A WORKSPACE</div>
        <div className="jig-banner__sub">Current source: JIG scored slate rows. Raw unscored Builder feed is not exposed yet.</div>
      </div>
      <FullSlateMatrix rows={builderRows} total={builderRows.length} onOpen={onOpenPlayer} builderMode={true} />
    </div>
  );
}

Object.assign(window, { JigCommand });
