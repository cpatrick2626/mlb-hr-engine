# Visual Design Doctrine

**Platform Identity:** Cinematic Tactical MLB Intelligence  
**Last Updated:** 2026-05-26

## Platform IS

- Tactical
- Cinematic
- Predictive
- Machine-driven
- Operationally believable
- Premium
- Immersive
- Escalation-focused

## Platform IS NOT

- Generic sportsbook UI
- Fantasy dashboard
- Spreadsheet analytics
- Flat SaaS design
- Cartoon cyberpunk

---

## Summary

The MLB HR Engine dashboard uses a cinematic HUD aesthetic — dark backgrounds, restrained glow effects, and a clear escalation hierarchy that communicates signal strength through visual weight rather than color noise. The design prioritizes operational clarity and tactical readability over decoration. Glow, color saturation, and animation are used sparingly and only to communicate intelligence escalation.

## Key Points

- **Cinematic HUD:** Dark background (near-black), card-based layout, high-contrast text. Operator should feel like they are in an ops center, not a spreadsheet.
- **Restrained glow:** Glow effects reserved for high-confidence signals and escalation states. Default state is minimal glow. Overuse degrades signal hierarchy.
- **Escalation hierarchy:** Visual weight increases with signal strength. Low-confidence picks are visually quiet. High-confidence picks with strong environmental conditions escalate via color intensity, border weight, and subtle animation.
- **Semantic green barrel palette:** Green is specifically the barrel/hard-hit quality signal color. Not generic "good."
- **Corner brackets:** Used to frame threat cards. Part of the HUD identity — do not remove.
- **Pulse animations:** Reserved for the highest escalation tier only.
- **Intelligence transparency:** Operator must always be able to see why a pick is scored the way it is. No hidden composite signals in the visual layer.

## Typography Rules

- Dense, readable, operationally credible
- Monospace or tabular figures for stat columns
- Hierarchy enforced by weight and size, not decoration
- No oversized headers that waste vertical space

## Layout Rules

- Avoid: flat layouts, stat overload, oversized whitespace,
  duplicated logic, cluttered dashboards
- Prioritize: fast scan readability, intelligence density,
  modular component reuse, responsive tactical feedback
- All UI must feel operationally believable

## Reference Visuals

- `!fl` — Full Slate Intelligence Matrix
- `!cd` — Main Command Center Dashboard
- `!JB` — JIG Builder All-In-One

Mockups in: `raw\assets\`  
Locked specs in: `mlb_hr_engine_v4\_design\`

## Cross-References

- [Room Governance](room-governance.md) — room-specific visual surfaces
- [MAIN Model Doctrine](main-model-doctrine.md) — what signals the visual layer surfaces
- [JIG Tactical Doctrine](jig-tactical-doctrine.md) — JIG-specific display rules (HVY signal display-only)
