/* HR Engine — Tactical Command Center, scoped to the stage (big open area).
   Renders inside the room frame so the shell stays visible.
   Tweak filters here, then APPLY TO ROOM — the change affects the room you're in
   and is saved (persists when you navigate away and come back). */

const StageCommand = ({ engine, lens, onClose, initialFilters, onApply }) => {
  const ctx = lens ? `${engine.name} · ${lens.name}` : `${engine.name}${engine.suffix ? " " + engine.suffix : ""}`;
  const accent = engine.color;

  const seed = { ...FILTER_DEFAULTS, ...(initialFilters || {}) };
  const [draft, setDraft] = React.useState(seed);
  const [resetKey, setResetKey] = React.useState(0);
  const [justApplied, setJustApplied] = React.useState(false);

  const set = (patch) => { setDraft((d) => ({ ...d, ...patch })); setJustApplied(false); };
  const active = countActiveFilters(draft);

  const sortLabel = (SORT_OPTIONS.find((o) => o.key === draft.sortKey) || SORT_OPTIONS[0]).label;

  const doReset = () => { setDraft({ ...FILTER_DEFAULTS }); setResetKey((k) => k + 1); setJustApplied(false); };
  const doApply = () => { onApply(draft); setJustApplied(true); setTimeout(() => onClose(), 650); };

  return (
    <div className="md-cc">
      <div className="md-cc__bar">
        <div className="md-cc__titlewrap">
          <span className="md-cc__logo" style={{ color: accent }}><Icon name="gear" size={18} color="currentColor" /></span>
          <span className="md-cc__title">Tactical Command Center</span>
          <span className="md-cc__ctx" style={{ "--ctx-color": accent }}>TUNING <b>{ctx}</b></span>
        </div>
        <div className="md-cc__baractions">
          <span className="md-cc__filters" data-on={active > 0}>
            <Icon name="filter" size={13} color="currentColor" /> {active} ACTIVE
          </span>
          <button className="md-cc__reset" onClick={doReset}>RESET</button>
          <button className="md-cc__apply" onClick={doApply}>
            {justApplied ? "✓ APPLIED" : "APPLY TO ROOM"}
          </button>
          <button className="md-cc__close" onClick={onClose} title="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
          </button>
        </div>
      </div>

      {!lens && (
        <div className="md-cc__note">This room has no filterable slate — tuning applies to MAIN and JIG lenses (Full Slate, Top Targets).</div>
      )}

      <div className="md-cc__grid" key={resetKey}>
        <FilterPanel num="1" title="BATTER POWER & CONTACT" cols={2}>
          <Stepper label="ISO" value={0} step={0.005} decimals={3} max={1} />
          <Stepper label="xSLG" value={0} step={0.005} decimals={3} max={1} />
          <Stepper label="Barrel %" value={draft.minBarrel} step={0.5} decimals={1} max={100} onChange={(v) => set({ minBarrel: v })} />
          <Stepper label="Hard Hit %" value={draft.minHH} step={0.5} decimals={1} max={100} onChange={(v) => set({ minHH: v })} />
          <Stepper label="Avg Exit Velocity" unit="(MPH)" value={draft.minEV} step={0.5} decimals={1} max={120} onChange={(v) => set({ minEV: v })} />
          <Stepper label="HR/FB %" value={0} step={0.5} decimals={1} max={100} />
        </FilterPanel>

        <FilterPanel num="2" title="LAUNCH & CONTACT SHAPE" cols={2}>
          <Stepper label="Pull Air %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Launch Angle" unit="(°)" value={0} step={0.5} decimals={1} min={-20} max={60} />
          <Stepper label="HR Window %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Sweet Spot %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Fly Ball %" value={0} step={0.5} decimals={1} max={100} />
        </FilterPanel>

        <FilterPanel num="3" title="MATCHUP & SPLITS" cols={2}>
          <Stepper label="vs RHP ISO" value={0} step={0.005} decimals={3} max={1} />
          <Stepper label="vs LHP ISO" value={0} step={0.005} decimals={3} max={1} />
          <Stepper label="Pitch Type Damage %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Min Matchup Modifier %" value={75} step={1} decimals={0} max={100} />
          <Stepper label="Min HVY Score" value={0} step={1} decimals={0} max={100} />
        </FilterPanel>

        <FilterPanel num="4" title="PITCHER VULNERABILITY" cols={2}>
          <Stepper label="Total HR Allowed" value={0} step={1} decimals={0} max={100} />
          <Stepper label="HR/9" value={0} step={0.01} decimals={2} max={10} />
          <Stepper label="Barrel % Allowed" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Hard Hit % Allowed" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Fly Ball % Allowed" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Pull Damage Allowed %" value={0} step={0.5} decimals={1} max={100} />
        </FilterPanel>

        <FilterPanel num="5" title="ENVIRONMENT" cols={2}>
          <Stepper label="Park HR Factor" value={0} step={0.5} decimals={1} max={200} />
          <Stepper label="Wind" unit="(MPH)" value={0} step={0.5} decimals={1} max={60} />
          <Dropdown label="Wind Direction" options={["Any", "Out to LF", "Out to CF", "Out to RF", "In from LF", "In from RF"]} />
          <Stepper label="Temperature" unit="(°F)" value={0} step={1} decimals={1} min={0} max={120} />
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
          <Stepper label="Recent HRs" unit="(7G)" value={0} step={1} decimals={0} max={50} />
          <Stepper label="Recent Hard Hit %" unit="(7G)" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Recent Barrel %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Hot Streak Indicator" value={0} step={1} decimals={0} max={100} />
          <Stepper label="Recent EV Trend" unit="(7G)" value={0} step={0.5} decimals={1} min={-50} max={50} />
        </FilterPanel>

        <FilterPanel num="8" title="GAME CONTEXT" cols={1} className="hr-panel-cc--toggles">
          <Toggle label="Exclude Started Games" on={false} />
          <Toggle label="Include Live Games" on={true} />
          <Toggle label="No Time Gate" on={false} />
          <Toggle label="Confirmed Lineups Only" on={false} />
          <Toggle label="Pre-Lineup Pool" on={true} />
        </FilterPanel>

        <FilterPanel num="9" title="OUTPUT CONTROL" cols={2}>
          <Stepper label="Min Projected HR %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Min Confidence %" value={0} step={0.5} decimals={1} max={100} />
          <Stepper label="Max Players" value={draft.maxPlayers} step={1} decimals={0} min={1} max={75} onChange={(v) => set({ maxPlayers: v })} />
          <Dropdown label="Sort By" value={sortLabel} options={SORT_OPTIONS.map((o) => o.label)}
            onChange={(label) => set({ sortKey: (SORT_OPTIONS.find((o) => o.label === label) || SORT_OPTIONS[0]).key })} />
          <Dropdown label="Sort Direction" value={draft.sortDir} options={["Descending", "Ascending"]}
            onChange={(v) => set({ sortDir: v })} />
        </FilterPanel>
      </div>

      <div className="md-cc__foot">
        <span className="md-cc__foot-brand"><LiveDot size={6} /> COMMAND SYSTEM</span>
        <span>SCOPE: <b style={{ color: accent }}>{ctx}</b></span>
        <span>{active > 0 ? `${active} FILTER${active > 1 ? "S" : ""} STAGED — APPLY TO SAVE` : "ADJUST FILTERS, THEN APPLY TO ROOM"}</span>
        <span style={{ marginLeft: "auto" }}>SOURCE: MLB STATS API</span>
      </div>
    </div>
  );
};

Object.assign(window, { StageCommand });
