# MOTION_SPEC template (copy per animation; do not fill upfront per page)

> Copy this file to the target's spec location when a non-trivial animation is proposed. Fill every field or mark `N/A (reason)`. Classify each timing/behavior claim as EXACT / OBSERVED / INFERRED / DEFAULT. Never present INFERRED/DEFAULT as exact.

## A. Reference-derived behavior record

- Component:
- Trigger:
- Purpose (orientation / hierarchy / feedback / continuity / comprehension / responsiveness):
- Evidence (local paths only — CaptureReport.json when available + screenshots/recording/notes; URL alone is not evidence):
- Evidence strength (EXACT / OBSERVED / INFERRED / DEFAULT per claim):
- Affected element(s):
- Start state:
- End state:
- Properties (prefer transform/opacity for ordinary UI):
- Duration:
- Delay:
- Stagger:
- Easing:
- Transform origin:
- Scroll relationship:
- Interruption behavior:
- Desktop behavior:
- Mobile/touch behavior (no hover-only functionality):
- Reduced-motion behavior (task completable without motion):
- Fallback (static/readable state):

## Reference facts vs. decisions

- EXACT REFERENCE FACTS:
- OBSERVED BEHAVIOR:
- INFERRED BEHAVIOR:
- IMPLEMENTATION DECISIONS:
- REJECTED_FOR_CONTEXT (reference spectacle inappropriate to government UI):
- UNKNOWN / NOT OBSERVABLE:

## B. Audit checklist (BLOCKER / IMPORTANT / MINOR / PASS per line)

- [ ] Clear UX purpose; task completion > clarity > accessibility > trust > feedback > polish
- [ ] Usable without motion; motion/color never the sole state signal (applicability states use text + structure + semantics; INSUFFICIENT_DATA never implies certainty)
- [ ] Reduced-motion path verified; no delay to primary actions or numeric values
- [ ] No flashing; no unexpected movement of critical content; persistent motion has pause/stop/hide
- [ ] Keyboard focus order preserved; touch/mobile works without hover
- [ ] Interruptible repeated interactions; no layout-thrash loops
- [ ] Reference fidelity labeled (EXACT / OBSERVED / INFERRED / DEFAULT / UNKNOWN); no exact-reproduction claim without evidence
- [ ] Scope: only requested motion changed; tokens/utilities reused; no unrelated refactors; no new dependencies
- [ ] Verification: project frontend scripts/config checks pass; diff inspected
