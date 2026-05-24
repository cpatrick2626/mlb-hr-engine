# Operational Audio — Future Doctrine — MLB HR ENGINE
**Version:** 1.0
**Step:** 9/12 — Tactical Animation, Motion Governance & Investigation Atmosphere
**Status:** Future Doctrine Only — No Implementation Authorized
**Implementation Phase:** Not before v5 or explicit operator request

---

## 1. Governing Statement

This document defines audio doctrine for a future version of MLB HR ENGINE in which optional, operator-controlled audio signals are available.

**Audio is not planned for current implementation.** Nothing in this document authorizes, requests, or implies imminent audio development. This is architectural thinking — doctrine established so that if audio is ever added, it is added correctly.

---

## 2. Core Restraint Principle

Audio in an operational intelligence platform must obey a single governing law:

**Audio communicates only what visual signal cannot communicate fast enough.**

The test for any audio signal: *Is there a case where the operator cannot be looking at the screen and still needs to receive this information?*

If no: audio signal does not exist.

If yes: audio signal may exist, must be minimal, and must be opt-in.

There is no case where audio enriches a signal that visual rendering already delivers adequately. Redundant audio is noise.

---

## 3. Audio Categories — Permitted Future Signals

### 3.1 Escalation Alert (Subtle)

**Trigger:** New CRITICAL tier threat appears during active session  
**Sound character:** Single soft tone — not sharp, not alarming  
**Frequency:** Mid-range (400–600Hz) — avoids ear fatigue range  
**Duration:** 180ms tone, no reverb, no tail  
**Volume:** Low-default (operator-configurable)  
**Purpose:** Operator is not watching screen; new CRITICAL entered field  

**Requirements:**
- Not a "beep" — closer to a soft notification chime
- Must not startle — must gently redirect attention
- Must not repeat — fires once per CRITICAL entry, not per render

---

### 3.2 Suppression Confirmation (Optional)

**Trigger:** Operator confirms suppression of a threat  
**Sound character:** Very soft downward tone — two-note descend  
**Frequency:** 500Hz → 350Hz over 120ms  
**Duration:** 120ms  
**Volume:** Very low — nearly subliminal  
**Purpose:** Tactile confirmation of decision made, threat removed  

**Requirements:**
- Communicates finality without celebration
- Should feel like a door softly closing
- Not a "success" sound — neutral confirmation

---

### 3.3 Deployment Confirmation (Optional)

**Trigger:** Operator commits deployment  
**Sound character:** Single clean mid-range tone  
**Frequency:** 520Hz, 200ms  
**Duration:** 200ms with 100ms soft fade  
**Volume:** Low-to-mid (operator-configurable)  
**Purpose:** The most consequential action gets the only "weighted" audio signal  

**Requirements:**
- This is the only audio signal that may carry slight weight/presence
- Still not dramatic — clean and certain, not triumphant
- Must not feel like a reward — feels like a confirmation of commitment

---

### 3.4 Trust Degradation Indicator (Future, Speculative)

**Trigger:** Active bet's trust score degrades significantly post-deployment  
**Sound character:** Very subtle low harmonic shift — barely perceivable  
**Frequency:** 300Hz, 150ms, low volume  
**Purpose:** Background awareness signal during live monitoring  

**Requirements:**
- Operator must first opt in to live monitoring audio specifically
- Not an alarm — a signal
- Cannot fire more than once per 5-minute window per position
- This signal is the most speculative in this document — implementation only if live monitoring is a confirmed future feature

---

## 4. Explicitly Rejected Audio Behaviors

### The following audio patterns are permanently forbidden:

**Casino audio patterns:**
- Coins, chimes, jackpot sounds
- Any sound that communicates reward or winning
- Audio that increases in frequency or intensity with activity volume
- "Level up" style sounds

**Hype audio:**
- Dramatic orchestral swells
- Music tracks (background or event-triggered)
- Sports broadcast audio cues
- Crowd noise, bat crack, any sports-literal sound
- Electronic "power up" sounds

**Constant notifications:**
- Notification sounds on every feed item
- Notification sounds on every badge increment
- Audio feedback on hover
- Audio feedback on click (unless deployment confirmation specifically)
- Tick/tick/tick ambient audio

**Sci-fi alarm patterns:**
- Klaxon
- Red alert tones
- Escalating alarm sequences
- Siren-style audio
- Any sound that creates anxiety rather than communicates state

**Volume-variable audio:**
- Sounds that get louder as more escalations accumulate
- Audio that changes pitch to indicate urgency level in real-time
- Any audio behavior that mimics a trading floor or casino floor at high activity

---

## 5. Optionality Architecture

Audio must be **off by default** and opt-in at every level.

### Required Controls:

| Control | Location | Default |
|---------|----------|---------|
| Master audio enable/disable | Settings panel | OFF |
| Escalation alerts | Settings panel (only visible if master ON) | ON (when master enabled) |
| Suppression confirmation | Settings panel (only visible if master ON) | OFF |
| Deployment confirmation | Settings panel (only visible if master ON) | ON (when master enabled) |
| Volume control | Settings panel (only visible if master ON) | 30% of max |

### Optionality rules:

- Audio never enables itself on update
- Settings persist across sessions
- No "try audio" prompt or upsell
- No audio during onboarding without explicit opt-in
- Audio settings must be findable within 2 clicks from any view

---

## 6. Accessibility Requirements

Any future audio implementation must satisfy:

**Non-audio equivalents must exist for every signal:**
Every audio signal maps to a visual signal that already exists. Audio is additive, not primary. An operator running with audio disabled loses nothing operationally.

**Volume is always operator-controlled:**
System audio controls must not be circumvented. No "force audio" logic.

**Audio must not trigger tinnitus risk:**
No sustained high-frequency tones (>2kHz). No piercing frequencies. Max duration: 300ms for any single sound.

**Screen reader compatibility:**
If audio is implemented, it must not conflict with screen reader audio output. Audio signals should use Web Audio API or similar and must respect OS-level audio routing.

**Sensitive environment consideration:**
Operators may be in public spaces, offices, or shared environments. Default-off and low-volume default respect this reality.

---

## 7. Non-Intrusive Behavior Rules

**Rule 1: Audio never demands action.**
No audio signal should create anxiety or urgency that compels the operator to act immediately. Audio informs — it does not coerce.

**Rule 2: Audio never fires during focus-protected states.**
If the operator is mid-deployment, no audio fires. If the operator is in JIG deep read state, escalation audio is queued but does not fire until JIG exit.

**Rule 3: Audio cooldown mirrors animation cooldown.**
Escalation audio: 800ms cooldown minimum between signals.  
No audio signal fires within 600ms of a preceding signal.

**Rule 4: Audio never loops.**
Every audio event is a single-shot trigger. Nothing loops, pulses, or continues.

**Rule 5: Audio follows the deployment suppression rule.**
All audio suppressed during active deployment flow. Zero exception.

---

## 8. Future Implementation Guidance (When Authorized)

When audio implementation is eventually authorized:

- Use Web Audio API for precision timing control
- Audio files should be under 200ms in all cases (no long soundscapes)
- Use mono audio (not spatial/stereo) — consistency across hardware
- Preload audio assets — no network latency on signal
- Test in multiple environments: headphones, laptop speakers, external monitors with built-in speakers
- Implement settings persistence via existing session_state architecture (Codex domain)
- Never ship audio-enabled as a default in a new deployment

---

*Audio is a power that this platform does not yet need.*
*When it is added, it must communicate with the discipline of a single word spoken in a quiet room.*
*Not a sound system. Not a mood. One word. Then silence.*
