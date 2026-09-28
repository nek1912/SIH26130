---
name: gov-motion-reference
description: Evidence-first motion system for an Indian government service website. Use for reference-based animation work, MotionLens CaptureReport analysis, motion specification, implementation, and audit. Never browse or invent reference behavior.
license: MIT
compatibility: opencode
---

# Government Motion Reference Skill

## Offline evidence rule
Do not browse, search, fetch, or infer motion from a URL. A URL is only an identifier. Use local MotionLens `CaptureReport.json`, screenshots/contact sheets, recordings, existing code, and `MOTION.md`.

Classify evidence as EXACT, OBSERVED, INFERRED, or DEFAULT. Never turn weak evidence into exact timing/easing/keyframe claims.

## Clean-room rule
Reproduce observable motion behavior, not source code, assets, branding, copy, or proprietary implementation. Translate trigger, purpose, affected elements, start/end states, properties, timing, easing, stagger, origin, scroll relationship, interruption, responsive behavior, and reduced-motion behavior.

## Government posture
The site is a public-service interface, not a creative showcase. Priorities: task completion > clarity > accessibility > trust > feedback > polish.

Default qualities: calm, trustworthy, predictable, restrained, purposeful.

Do not default to particles, cursor followers, magnetic buttons, heavy parallax, WebGL hero scenes, page-wide fade-up, decorative infinite loops, delayed animated counters, or motion-only disclosure. A reference containing such effects is not permission to use them.

## Implementation ladder
1. CSS transitions/keyframes.
2. WAAPI or supported CSS scroll-driven animation.
3. Existing animation library already in the project.
4. GSAP only when timelines, scroll choreography, complex interruption, SVG/path motion, or another concrete capability requires it.
5. Three.js/R3F/WebGL only when functionally justified.

Do not add a runtime dependency merely because a skill exists.

## Existing-stack rule
Inspect `package.json`, existing motion utilities, tokens, and components first. Preserve architecture. No unrelated refactor.

## Accessibility gates
- Honor `prefers-reduced-motion` for non-essential movement.
- Preserve information and task completion without motion.
- Never use motion or color as the sole state signal.
- No hover-only functionality; touch/mobile must work without hover.
- Preserve keyboard focus and logical focus order.
- Avoid unexpected movement of important content.
- Avoid flashing.
- For persistent moving/blinking/scrolling information, provide the applicable pause/stop/hide mechanism.

## Reference-analysis record
For every significant reference-derived behavior record:
- evidence
- evidence strength
- component
- trigger
- purpose
- properties
- timing/easing
- stagger/delay
- scroll relationship
- interruption
- mobile behavior
- reduced-motion behavior
- exact vs inferred values
- rejected behaviors
- fallback

## Completion gate
Do not report motion complete until relevant build/typecheck/lint passes, reduced-motion and keyboard/touch behavior are correct, no unrelated changes were made, and reference-derived claims are traceable to local evidence.
