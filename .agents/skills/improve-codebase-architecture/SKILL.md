---
name: improve-codebase-architecture
description: Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
disable-model-invocation: true
---

# Improve Codebase Architecture → MLB-HR-ENGINE-ARCHITECT + project architecture doctrine

**Authoritative source:** `AGENTS.md` → MLB-HR-ENGINE-ARCHITECT skill + MAIN/JIG/HVY doctrine gates in `CLAUDE.md` §6–7

All architectural candidates must pass the MAIN/JIG separation gate and PHASE3_REFINEMENT_DOCTRINE closed-surface check before being proposed.

## Preserved mechanics (use alongside the authoritative procedure)

- **HTML report:** write to `<tmpdir>/architecture-review-<timestamp>.html`; Tailwind + Mermaid via CDN; open with `xdg-open` (Linux) / `open` (macOS) / `start` (Windows)
- **Card format per candidate:** Files · Problem · Solution · Benefits (locality/leverage framing) · Before/After diagram · Recommendation strength badge (`Strong` / `Worth exploring` / `Speculative`)
- **ADR conflict:** mark candidates that contradict existing ADRs with a warning callout; only surface when friction is real enough to warrant reopening — don't list every theoretically forbidden refactor
- **HTML scaffold:** `HTML-REPORT.md` in this skill's directory has the full template + diagram patterns
- **Grilling loop:** after user picks a candidate, continue with the grilling + domain-modeling workflow per LOOPS §5; update domain glossary inline as decisions crystallize
