# HR Engine Visual Design Tokens
Source: HR_Engine_Design_System-handoff (2026-05-26)
Status: CANONICAL — these override all previous color guesses

## Color Tokens
  Green (advantage/live/hit):
    --green-500: #1aff66  (core neon green)
    --green-300: #6dffae  (medium green)
    --green-glow: rgba(26,255,102,0.55)

  Red (danger/cold/pitcher):
    --red-500:   #ff3344  (core neon red)
    --red-300:   #ff8a93  (medium red)
    --red-glow:  rgba(255,51,68,0.55)

  Cyan (neutral/info):
    --cyan-500:  #00d9ff

  Blue (signal tier):
    --blue-500:  #3b6fff

  Amber (watch/warning):
    --amber-500: #ffb020

## Surface Colors
    --bg-void:     #04070a  (page background)
    --bg-base:     #0a1014  (primary panel)
    --bg-raised:   #0e1519  (raised card)
    --bg-elevated: #131b21  (hover/chip)

## Text Colors
    --fg-1: #f1f5f3  (primary — player names)
    --fg-2: #b8c2c0  (secondary — labels)
    --fg-3: #6b7872  (tertiary — captions)

## Heatmap Ramp
    --heat-cold: #2a0a10  (pitcher favored)
    --heat-cool: #6a1622
    --heat-mid:  #2a1e1a  (neutral)
    --heat-warm: #0e3a20
    --heat-hot:  #14c451  (batter favored)

## Typography
    Display: Barlow Condensed 800, uppercase, tracking 0.08em
    Stats:   JetBrains Mono, tabular-nums
    Body:    Barlow

## Tier Pill Spec
    Style: inset 0 0 0 1.5px rgba(color, 0.6)
    Background: rgba(8,12,16,0.6)
    Font: Barlow Condensed 800, 12px, uppercase, tracking 0.12em

## Files in Design System
    colors_and_type.css — all tokens
    preview/components-tiers.html — tier pill specimens
    preview/components-heatcells.html — heatmap cell specimens
    preview/components-table.html — table specimens
    ui_kits/hr-engine/ — full React component kit
      StatTable.jsx, BatterCard.jsx, CommandCenter.jsx,
      MatchupCenter.jsx, QuickPicks.jsx, Header.jsx
