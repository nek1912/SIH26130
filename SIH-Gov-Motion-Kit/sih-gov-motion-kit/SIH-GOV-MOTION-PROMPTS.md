# SIH Government Motion Prompt Pack

These prompts assume the coding agent has NO web-search requirement.

## A. Reference → MOTION_SPEC.md

You are the motion-analysis engineer for an Indian government service website.

Do not browse the web. Read only local project code, `.motion/MOTION.md`, and local reference evidence.

Inputs:
- `.motion/references/<reference>/CaptureReport.json` if available
- screenshots/contact sheet
- local recording
- existing target component
- `.motion/MOTION.md`

Tasks:
1. Classify every observation EXACT / OBSERVED / INFERRED / DEFAULT.
2. Extract trigger, purpose, target, start/end states, properties, duration, delay, stagger, easing, origin, scroll relationship, interruption, responsive behavior, reduced-motion behavior.
3. Separate reference facts from implementation decisions.
4. Reject reference behaviors that conflict with the government-service posture.
5. Choose the least complex implementation technique that can reproduce the useful behavior.
6. Do not copy reference source code, assets, branding, or copy.
7. Do not invent exact timing/easing when evidence is insufficient.
8. Produce `MOTION_SPEC.md`; do not write application code yet.

## B. MOTION_SPEC.md → implementation

Read `MOTION.md`, the local reference evidence, `MOTION_SPEC.md`, the target component, and `package.json`.

Implement only the specified motion. Reuse existing motion utilities/tokens. Prefer CSS/WAAPI before a new library. Use GSAP only when a concrete capability justifies it. Add reduced-motion, preserve keyboard/touch behavior, and avoid unrelated refactors.

After implementation run the narrowest relevant verification available and report exactly what was verified and what remains uncertain.

## C. Government motion audit

Audit only motion/interaction behavior. Check purpose, frequency, timing, easing, transform origin, interruption, performance, reduced motion, hover/touch, accessibility, government context, reference fidelity, and scope. Report BLOCKER / IMPORTANT / MINOR / PASS. Do not rewrite unrelated code.

## D. Regression comparison

Compare the final implementation against `MOTION_SPEC.md`, `.motion/MOTION.md`, and local evidence. Identify reference-preserved behavior, intentional deviations, accidental deviations, and unknowns caused by missing evidence.

## E. Page-specific guidance

### Homepage
Keep ownership/trust and primary service actions immediately usable. Use one restrained entrance hierarchy. No spectacle-first hero.

### Application/onboarding wizard
Motion communicates step changes, validation, saved state, and progress. Never sacrifice orientation or focus for transition effects.

### Approval applicability
Results APPLIES / DOES_NOT_APPLY / CONDITIONAL / INSUFFICIENT_DATA must remain understandable without motion or color alone. Animate only supporting disclosure or transition.

### Process/dependency flow
Animate actual progress/focus, not decorative movement. Static state must remain readable.

### Documents/evidence
Use predictable expansion. Never hide authority/date/source information behind motion-only disclosure.

### Dashboard
Do not make users wait for important numbers. Keep repeated-visit motion density low.
