/* Shared utility classes for components.
   Component scope rules: any class starting with `hr-` is owned by HR Engine UI kit. */

const Pill = ({ kind = "neutral", children, style }) => {
  const palettes = {
    live:    { bg: "rgba(26,255,102,0.08)", color: "#1aff66", ring: "rgba(26,255,102,0.45)" },
    target:  { bg: "rgba(255,51,68,0.08)",  color: "#ff3344", ring: "rgba(255,51,68,0.45)" },
    tier:    { bg: "#1aff66", color: "#04070a", ring: "transparent", glow: "0 0 12px rgba(26,255,102,0.45)" },
    dm:      { bg: "var(--bg-elevated)", color: "#00d9ff", ring: "rgba(0,217,255,0.5)" },
    info:    { bg: "var(--bg-elevated)", color: "#7ce8ff", ring: "rgba(0,217,255,0.3)" },
    warn:    { bg: "rgba(255,176,32,0.08)", color: "#ffb020", ring: "rgba(255,176,32,0.45)" },
    neutral: { bg: "var(--bg-elevated)", color: "var(--fg-1)", ring: "rgba(180,220,200,0.16)" },
    dark:    { bg: "transparent", color: "var(--fg-2)", ring: "rgba(180,220,200,0.16)" },
  };
  const p = palettes[kind] || palettes.neutral;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "3px 10px",
      fontFamily: "var(--font-display)", fontWeight: 700,
      fontSize: 11, lineHeight: 1,
      textTransform: "uppercase", letterSpacing: "0.1em",
      borderRadius: 999,
      background: p.bg, color: p.color,
      boxShadow: `0 0 0 1px ${p.ring}${p.glow ? `, ${p.glow}` : ""}`,
      ...style,
    }}>{children}</span>
  );
};

const LiveDot = ({ size = 8 }) => (
  <span style={{
    display: "inline-block",
    width: size, height: size,
    borderRadius: "50%",
    background: "#1aff66",
    boxShadow: "0 0 8px rgba(26,255,102,0.8), 0 0 2px #fff",
    animation: "hr-pulse 1.8s ease-in-out infinite",
  }} />
);

const Icon = ({ name, size = 16, color = "currentColor", strokeWidth = 1.8 }) => {
  const paths = {
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/></>,
    wrench:   <><path d="M14 3l-1.5 1.5a4 4 0 105.5 5.5L19.5 8.5l-2-2zM3 21l8-8M11 13l1 1"/></>,
    play:     <><circle cx="12" cy="12" r="9"/><polygon points="10,8 16,12 10,16" fill={color} stroke="none"/></>,
    target:   <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill={color}/></>,
    bar:      <><line x1="6" y1="20" x2="6" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="18" y1="20" x2="18" y2="14"/></>,
    check:    <><path d="M9 12l2 2 4-4"/><rect x="3" y="3" width="18" height="18" rx="2"/></>,
    users:    <><circle cx="9" cy="7" r="4"/><path d="M2 22a7 7 0 0114 0M16 11a4 4 0 010-8M22 22a7 7 0 00-6-7"/></>,
    filter:   <><line x1="4" y1="6" x2="20" y2="6"/><line x1="7" y1="12" x2="17" y2="12"/><line x1="10" y1="18" x2="14" y2="18"/></>,
    chevron:  <><polyline points="6,9 12,15 18,9"/></>,
    chevronR: <><polyline points="9,6 15,12 9,18"/></>,
    crosshair:<><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><circle cx="12" cy="12" r="3"/></>,
    trend:    <><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></>,
    clock:    <><circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/></>,
    pin:      <><path d="M12 22s7-6 7-12a7 7 0 10-14 0c0 6 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></>,
    home:     <><path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></>,
    dashring: <><circle cx="12" cy="12" r="9" strokeDasharray="3 3"/><circle cx="12" cy="12" r="2.2" fill={color} stroke="none"/></>,
    gear:     <><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/></>,
    bolt:     <><polygon points="13,2 4,14 11,14 10,22 19,9 12,9" fill={color} stroke={color} strokeWidth="0.5" strokeLinejoin="round"/></>,
    star:     <><polygon points="12,3 14.6,9 21,9.5 16,13.8 17.6,20 12,16.4 6.4,20 8,13.8 3,9.5 9.4,9"/></>,
    diamond:  <><path d="M12 3l9 9-9 9-9-9z"/><circle cx="12" cy="12" r="2" fill={color} stroke="none"/></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  );
};

Object.assign(window, { Pill, LiveDot, Icon });
