# MOTION.md — SIH Government Service Motion System

## Motion identity
Calm, trustworthy, restrained, purposeful, responsive.
Motion exists to improve orientation, continuity, feedback, hierarchy, and comprehension.

## Evidence policy
Reference evidence lives under `.motion/references/<reference>/`.
Classify values as EXACT, OBSERVED, INFERRED, or DEFAULT. Never claim an inferred value is exact.

## Global rules
1. Animate only when motion has a clear job.
2. Reuse existing motion tokens and utilities.
3. Prefer transform/opacity for ordinary UI motion.
4. Make repeated interaction motion interruptible.
5. Essential information must remain understandable without motion.
6. Respect `prefers-reduced-motion`.
7. Avoid unnecessary parallax, large moving backgrounds, flashing, cursor theatrics, and decorative infinite loops.
8. Do not delay access to important services or data.

## Component defaults
### Header/navigation
Subtle state changes; trigger-origin dropdowns; obvious keyboard focus.

### Hero
One restrained entrance hierarchy. Primary actions usable without waiting.

### Forms/wizard
Animate step/state changes only as orientation or feedback. Preserve user position and focus. Validation is immediate.

### Approval results
For APPLIES / DOES_NOT_APPLY / CONDITIONAL / INSUFFICIENT_DATA, motion may reveal or connect supporting detail but must never be the sole state signal.

### Process/dependency views
Animate actual progression or focus. Static fallback remains readable. No fake moving connectors.

### Documents/evidence
Quick predictable expansion. Authority/date/source remain accessible without motion.

### Dashboard
Do not delay current values with animated counters. Use chart entrance only when it aids comprehension.

## Scroll motion
Default: minimal. Use only when it improves orientation, progress, or comprehension. Non-essential scroll motion needs a reduced-motion/static path.

## Responsive
No hover-only behavior on mobile. Simplify large-distance motion and touch-sensitive scroll choreography. Preserve function and hierarchy.

## Audit checklist
[ ] clear purpose
[ ] usable without motion
[ ] reduced-motion path
[ ] no flashing
[ ] no hover-only interaction
[ ] keyboard focus preserved
[ ] mobile/touch correct
[ ] local reference evidence available
[ ] no fabricated exact values
[ ] no unnecessary dependency
[ ] relevant verification passes
