/* HR Engine — form control primitives for the Tactical Command Center. */

const HelpIcon = () => (
  <span className="hr-help" title="Filter help">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.5 9a2.5 2.5 0 015 0c0 1.5-2.5 2-2.5 3.5" strokeLinecap="round" />
      <circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
    </svg>
  </span>
);

const FieldLabel = ({ children, unit }) => (
  <div className="hr-field__label">
    <span>{children}{unit && <span className="hr-field__unit"> {unit}</span>}</span>
    <HelpIcon />
  </div>
);

/* Numeric stepper: label + value field + −/+ buttons. Fully functional. */
const Stepper = ({ label, unit, value: initial = 0, step = 0.1, decimals = 1, min = 0, max = 9999, onChange }) => {
  const [value, setValue] = React.useState(initial);
  const clamp = (v) => Math.min(max, Math.max(min, v));
  const fmt = (v) => v.toFixed(decimals);
  const update = (v) => { const c = clamp(v); setValue(c); onChange && onChange(c); };
  return (
    <div className="hr-field">
      <FieldLabel unit={unit}>{label}</FieldLabel>
      <div className="hr-stepper">
        <input
          className="hr-stepper__input"
          value={fmt(value)}
          onChange={(e) => {
            const n = parseFloat(e.target.value);
            if (!isNaN(n)) update(n);
          }}
        />
        <button className="hr-stepper__btn" onClick={() => update(+(value - step).toFixed(4))}>−</button>
        <button className="hr-stepper__btn" onClick={() => update(+(value + step).toFixed(4))}>+</button>
      </div>
    </div>
  );
};

/* iOS-style toggle. */
const Toggle = ({ label, on: initial = false }) => {
  const [on, setOn] = React.useState(initial);
  return (
    <button className={`hr-toggle ${on ? "is-on" : ""}`} onClick={() => setOn(!on)}>
      <span className="hr-toggle__label">{label}</span>
      <span className="hr-toggle__track"><span className="hr-toggle__knob" /></span>
    </button>
  );
};

/* Dropdown select (cosmetic — opens a small native-style list). */
const Dropdown = ({ label, unit, options = ["Any"], value: initial, onChange }) => {
  const [open, setOpen] = React.useState(false);
  const [value, setValue] = React.useState(initial || options[0]);
  return (
    <div className="hr-field">
      {label && <FieldLabel unit={unit}>{label}</FieldLabel>}
      <div className="hr-select" onClick={() => setOpen((o) => !o)}>
        <span>{value}</span>
        <Icon name="chevron" size={14} color="var(--fg-3)" />
        {open && (
          <div className="hr-select__menu">
            {options.map((o) => (
              <div
                key={o}
                className={`hr-select__opt ${o === value ? "is-sel" : ""}`}
                onClick={(e) => { e.stopPropagation(); setValue(o); setOpen(false); onChange && onChange(o); }}
              >{o}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

Object.assign(window, { HelpIcon, FieldLabel, Stepper, Toggle, Dropdown });
