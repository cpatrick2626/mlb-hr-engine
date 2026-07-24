/* HR Engine — Tactical Command Center, scoped to the stage (big open area).
   Renders inside the room frame so the shell stays visible.
   Tweak filters here, then APPLY TO ROOM — the change affects the room you're in
   and is saved (persists when you navigate away and come back). */

const StageCommand = ({ engine, lens, onClose, initialFilters, roomFilters, onApply }) => {
  const ctx = lens ? `${engine.name} · ${lens.name}` : `${engine.name}${engine.suffix ? " " + engine.suffix : ""}`;
  const accent = engine.color;

  const engineDefaults = engine.id === "jig"
    ? { ...FILTER_DEFAULTS, sortKey: "jigScore", sortDir: "Descending" }
    : FILTER_DEFAULTS;
  const seed = { ...engineDefaults, ...(initialFilters || {}) };
  const [draft, setDraft] = React.useState(seed);
  const [resetKey, setResetKey] = React.useState(0);
  const [justApplied, setJustApplied] = React.useState(false);
  const ccRef = React.useRef(null);
  const stickyHeadRef = React.useRef(null);
  const { preset, feedback, builds, loadOpen, busy, setLoadOpen, doSave, doLoad, applyBuild } = useTccBuildSaver({ roomFilters, onApplyFilters: onApply });

  React.useLayoutEffect(() => {
    const cc = ccRef.current;
    const head = stickyHeadRef.current;
    if (!cc || !head) return undefined;
    const syncStickyHeight = () => {
      cc.style.setProperty("--md-cc-sticky-head-height", `${Math.ceil(head.getBoundingClientRect().height)}px`);
    };
    syncStickyHeight();
    const observer = typeof ResizeObserver === "function" ? new ResizeObserver(syncStickyHeight) : null;
    observer?.observe(head);
    window.addEventListener("resize", syncStickyHeight);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", syncStickyHeight);
      cc.style.removeProperty("--md-cc-sticky-head-height");
    };
  }, []);

  const set = (patch) => { setDraft((d) => ({ ...d, ...patch })); setJustApplied(false); };
  const active = countActiveFilters(draft);

  const visibleSortOptions = SORT_OPTIONS.filter((o) => o.key !== "jigScore" || engine.id === "jig");
  const sortLabel = (visibleSortOptions.find((o) => o.key === draft.sortKey) || visibleSortOptions[0]).label;

  const doReset = () => { setDraft({ ...FILTER_DEFAULTS }); setResetKey((k) => k + 1); setJustApplied(false); };
  const doApply = () => { onApply(draft); setJustApplied(true); setTimeout(() => onClose(), 650); };

  return (
    <div className="md-cc" ref={ccRef}>
      <div className="md-cc__sticky-head" ref={stickyHeadRef}>
        <div className="md-cc__bar">
          <div className="md-cc__titlewrap">
            <span className="md-cc__logo" style={{ color: accent }}><Icon name="gear" size={18} color="currentColor" /></span>
            <span className="md-cc__title">Tactical Command Center</span>
            <span className="md-cc__ctx" style={{ "--ctx-color": accent }}>TUNING <b>{ctx}</b></span>
          </div>
          <div className="md-cc__baractions">
            <div className="md-cc__build-actions">
              <span className="md-cc__filters" data-on={active > 0}>
                <Icon name="filter" size={13} color="currentColor" /> {active} ACTIVE
              </span>
              <button className="md-cc__reset" onClick={doReset}>RESET</button>
              {feedback && <span className={`jig-bar__flash jig-bar__flash--${feedback.kind}`} role="status" aria-live="polite">{feedback.kind === "success" ? "✓ " : ""}{feedback.text}</span>}
              <button className="hr-btn hr-btn--ghost" onClick={doSave} disabled={busy !== null}>{busy === "save" ? "SAVING…" : "SAVE BUILD"}</button>
              <div className="jig-load">
                <button className="hr-btn hr-btn--ghost" onClick={doLoad} disabled={busy !== null} aria-expanded={loadOpen}>{busy === "load" ? "LOADING…" : "LOAD BUILD"}</button>
                {loadOpen && (
                  <div className="jig-load__menu" role="dialog" aria-label="Saved TCC builds">
                    <div className="jig-load__head"><span>SAVED BUILDS</span><button className="jig-load__close" onClick={() => setLoadOpen(false)} aria-label="Close saved builds">×</button></div>
                    <div className="jig-load__list">
                      {builds.map((build) => <button className="jig-load__item" key={build.build_id || build.name} onClick={() => applyBuild(build)}><span>{build.name}</span><span className="jig-load__apply">APPLY</span></button>)}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="md-cc__apply-actions">
              <button className="md-cc__apply" onClick={doApply}>
                {justApplied ? "✓ APPLIED" : "APPLY TO ROOM"}
              </button>
              <button className="md-cc__close" onClick={onClose} title="Close">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="md-cc__body">
      {!lens && (
        <div className="md-cc__note">This room has no filterable slate — tuning applies to MAIN and JIG lenses (Full Slate, Top Targets).</div>
      )}

      <div className="md-cc__grid" key={resetKey}>
        <FilterPanel num="1" title="BATTER POWER & CONTACT" cols={2}>
          <Stepper label="ISO" value={draft.minISO} step={0.005} decimals={3} max={1} onChange={(v) => set({ minISO: v })} />
          <Stepper label="xSLG" value={draft.minXSLG} step={0.005} decimals={3} max={1} onChange={(v) => set({ minXSLG: v })} />
          <Stepper label="Barrel %" value={draft.minBarrel} step={0.5} decimals={1} max={100} onChange={(v) => set({ minBarrel: v })} />
          <Stepper label="Hard Hit %" value={draft.minHH} step={0.5} decimals={1} max={100} onChange={(v) => set({ minHH: v })} />
          <Stepper label="Avg Exit Velocity" unit="(MPH)" value={draft.minEV} step={0.5} decimals={1} max={120} onChange={(v) => set({ minEV: v })} />
          <Stepper label="HR/FB %" value={draft.minHRFB} step={0.5} decimals={1} max={100} onChange={(v) => set({ minHRFB: v })} />
        </FilterPanel>

        <FilterPanel num="2" title="LAUNCH & CONTACT SHAPE" cols={2}>
          <Stepper label="Pull Air %" value={draft.minPullAir} step={0.5} decimals={1} max={100} onChange={(v) => set({ minPullAir: v })} />
          <Stepper label="Launch Angle" unit="(°)" value={draft.minLaunchAngle} step={0.5} decimals={1} min={-20} max={60} onChange={(v) => set({ minLaunchAngle: v })} />
          <Stepper label="HR Window %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Sweet Spot %" value={draft.minSweet} step={0.5} decimals={1} max={100} onChange={(v) => set({ minSweet: v })} />
          <Stepper label="Fly Ball %" value={draft.minFB} step={0.5} decimals={1} max={100} onChange={(v) => set({ minFB: v })} />
        </FilterPanel>

        <FilterPanel num="3" title="MATCHUP & SPLITS" cols={2}>
          <Stepper label="vs RHP ISO" value={draft.minRHPISO} step={0.005} decimals={3} max={1} onChange={(v) => set({ minRHPISO: v })} />
          <Stepper label="vs LHP ISO" value={draft.minLHPISO} step={0.005} decimals={3} max={1} onChange={(v) => set({ minLHPISO: v })} />
          <Stepper label="Pitch Type Damage %" value={0} step={0.5} decimals={1} max={100} />
          {engine.id === "jig"
            ? <Stepper label="Min Matchup Modifier %" value={draft.minMatchupModifier} step={1} decimals={0} min={75} max={140} onChange={(v) => set({ minMatchupModifier: v })} />
            : <Stepper label="Min Matchup Modifier %" value={75} step={1} decimals={0} max={100} />}
          <Stepper label="Min HVY Score" value={0} step={1} decimals={0} max={100} />
        </FilterPanel>

        <FilterPanel num="4" title="PITCHER VULNERABILITY" cols={2}>
          <Stepper label="Total HR Allowed" value={draft.minPitcherHRAllowed} step={1} decimals={0} max={100} onChange={(v) => set({ minPitcherHRAllowed: v })} />
          <Stepper label="HR/9" value={draft.minHR9} step={0.01} decimals={2} max={10} onChange={(v) => set({ minHR9: v })} />
          <Stepper label="Barrel % Allowed" value={draft.minBarrelAllowed} step={0.5} decimals={1} max={100} onChange={(v) => set({ minBarrelAllowed: v })} />
          <Stepper label="Hard Hit % Allowed" value={draft.minHHAllowed} step={0.5} decimals={1} max={100} onChange={(v) => set({ minHHAllowed: v })} />
          <Stepper label="Fly Ball % Allowed" value={draft.minFBAllowed} step={0.5} decimals={1} max={100} onChange={(v) => set({ minFBAllowed: v })} />
          <Stepper label="Pull Damage Allowed %" value={0} step={0.5} decimals={1} max={100} />
        </FilterPanel>

        <FilterPanel num="5" title="ENVIRONMENT" cols={2}>
          <Stepper label="Park HR Factor" value={0} step={0.5} decimals={1} max={200} />
          <Stepper label="Wind" unit="(MPH)" value={draft.minWindMph} step={0.5} decimals={1} max={60} onChange={(v) => set({ minWindMph: v })} />
          <Dropdown label="Wind Direction" value={draft.windDirection} options={["Any", "N", "NE", "E", "SE", "S", "SW", "W", "NW"]} onChange={(v) => set({ windDirection: v })} />
          <Stepper label="Temperature" unit="(°F)" value={draft.minTempF} step={1} decimals={1} min={0} max={120} onChange={(v) => set({ minTempF: v })} />
          <Dropdown label="Air Density" options={["Any", "Low", "Average", "High"]} />
        </FilterPanel>

        <FilterPanel num="6" title="ADVANCED HR SIGNALS" cols={2}>
          <Stepper label="Contact Shape Score" value={0} step={1} decimals={0} max={100} />
          <Stepper label="Arsenal Matchup Score" value={0} step={1} decimals={0} max={100} />
          <Stepper label="Opp Field Weakness %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Lifted Hard Hit %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="EV Trend" unit="(7G)" value={0} step={0.5} decimals={1} min={-50} max={50} />
        </FilterPanel>

        <FilterPanel num="7" title="MOMENTUM & RECENCY" cols={2}>
          <Stepper label="Recent HRs" unit="(10G)" value={draft.minRecentHRs} step={1} decimals={0} max={50} onChange={(v) => set({ minRecentHRs: v })} />
          <Stepper label="Recent Hard Hit %" unit="(7G)" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Recent Barrel %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Hot Streak Indicator" value={draft.minStreakFactor} step={0.01} decimals={2} min={0.89} max={1.12} onChange={(v) => set({ minStreakFactor: v })} />
          <Stepper label="Recent EV Trend" unit="(7G)" value={0} step={0.5} decimals={1} min={-50} max={50} />
        </FilterPanel>

        <FilterPanel num="8" title="GAME CONTEXT" cols={1} className="hr-panel-cc--toggles">
          <Toggle label="Exclude Started Games" on={draft.excludeStarted} onChange={(v) => set({ excludeStarted: v })} />
          <Toggle label="Include Live Games" on={draft.includeLive} onChange={(v) => set({ includeLive: v })} />
          <Toggle label="Confirmed Lineups Only" on={draft.confirmedLineupsOnly} onChange={(v) => set({ confirmedLineupsOnly: v })} />
          <Toggle label="Pre-Lineup Pool" on={draft.preLineupPool} onChange={(v) => set({ preLineupPool: v })} />
        </FilterPanel>

        <FilterPanel num="9" title="OUTPUT CONTROL" cols={2}>
          <Stepper label="Min Projected HR %" value={draft.minHRProb} step={0.5} decimals={1} max={100} onChange={(v) => set({ minHRProb: v })} />
          <Stepper label="Min Confidence %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Max Players" value={draft.maxPlayers} step={1} decimals={0} min={1} max={75} onChange={(v) => set({ maxPlayers: v })} />
          <Dropdown label="Sort By" value={sortLabel} options={visibleSortOptions.map((o) => o.label)}
            onChange={(label) => set({ sortKey: (visibleSortOptions.find((o) => o.label === label) || visibleSortOptions[0]).key })} />
          <Dropdown label="Sort Direction" value={draft.sortDir} options={["Descending", "Ascending"]}
            onChange={(v) => set({ sortDir: v })} />
        </FilterPanel>
      </div>

      <div className="md-cc__foot">
        <span className="md-cc__foot-brand"><LiveDot size={6} /> COMMAND SYSTEM</span>
        <span>SCOPE: <b style={{ color: accent }}>{ctx}</b></span>
        <span>{active > 0 ? `${active} FILTER${active > 1 ? "S" : ""} STAGED — APPLY TO SAVE` : `BUILD: ${preset}`}</span>
        <span style={{ marginLeft: "auto" }}>SOURCE: MLB STATS API</span>
      </div>
      </div>
    </div>
  );
};

Object.assign(window, { StageCommand });
