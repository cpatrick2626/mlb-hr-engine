/* HR Engine — JIG BUILDER lens.
   Shows the Full Slate Intelligence Matrix with a Save / Load builder bar on top. */

function JigCommand({ engine, lens, onOpenPlayer }) {
  const rows = window.LEADERBOARD_ROWS || [];
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
      <FullSlateMatrix rows={rows} total={rows.length} onOpen={onOpenPlayer} />
    </div>
  );
}

Object.assign(window, { JigCommand });
