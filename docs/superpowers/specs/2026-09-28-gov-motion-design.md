# Minimal Local Government Motion System — Design

**Date:** 2026-09-28
**Status:** Approved for write-up (user-approved all 8 sections)
**Scope:** Review-first design of the ChatGPT-proposed SIH motion pipeline; installs docs + project-local skill only. No runtime, tooling, or page-animation changes.

## Goal

Give the SIH Gujarat industrial-approvals portal a single restrained motion source-of-truth that improves usability and clarity (wizard orientation, validation feedback, applicability-state disclosure) without adding runtime dependencies, external skill clones, reference tooling, or spectacle. Success means motion has a concrete UX job and never delays task completion or data.

## Context reviewed

- Locked stack: React + TypeScript + Vite + Tailwind CSS; FastAPI; Supabase; REST/OpenAPI. No animation library in `frontend/package.json`.
- Current motion primitives: Tailwind `fade-in` / `slide-in` tokens + spinner in `frontend/src/app.css` and `LoadingSpinner`.
- No `.motion/` or `.opencode/` exists; `SIH-Gov-Motion-Kit/sih-gov-motion-kit/` is untracked input containing `MOTION.md`, `GOV-MOTION-SYSTEM.md` (skill source with `gov-motion-reference` frontmatter), `SIH-GOV-MOTION-PROMPTS.md`, `README.md`, `install-sih-gov-motion.ps1`.
- No local MotionLens captures or reference sites exist.
- PRD acceptance tests do not mention motion; quality bar rejects visually attractive CRUD with no domain logic.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Approach | A — Minimal local source-of-truth | Passes AGENTS.md anti-overengineering gate; matches existing complexity; works with zero captures |
| Runtime deps | None (CSS/Tailwind/WAAPI only) | No MVP sequencing/scroll need forces GSAP/WebGL; RULES.md requires verification + necessity |
| Skill footprint | Project-local `gov-motion-reference` only | No Emil/GSAP/motion-ref clones; no license drift or maintenance |
| Reference tooling | Documented future opt-in, not installed | No MotionVault/MotionLens clone/build with no refs to process |
| Command | No `/gov-motion` command yet | Add only after manual skill use proves value |
| Page animation | None in this design | Future animations require `MOTION_SPEC.md` + audit |

Alternatives rejected: B (full kit install — speculative weight with no refs); C (ad-hoc only — no shared posture, risks motion-only state signals and missed reduced-motion paths).

## Section 1 — Scope & non-goals

In scope: project-local motion posture (`MOTION.md`), project-local `gov-motion-reference` skill, `MOTION_SPEC.md` template + audit checklist, per-area guardrails for the existing Vite + Tailwind frontend. Covers wizard orientation, validation feedback, applicability-state disclosure (`APPLIES / DOES_NOT_APPLY / CONDITIONAL / INSUFFICIENT_DATA`), dependency/readiness focus, document expand/collapse, dashboard restraint. CSS/Tailwind/WAAPI only.

Explicitly out: cloning/building MotionVault/MotionLens now; cloning Emil/GSAP/motion-ref skills; installing any animation runtime (GSAP, Three.js); any `/gov-motion` command; any reference capture; any page animation implementation. MotionLens workflow is future opt-in only. No backend, migration, or API changes.

## Section 2 — Architecture (files only, no tooling)

```text
.motion/MOTION.md
  ← copied from SIH-Gov-Motion-Kit/sih-gov-motion-kit/MOTION.md (verbatim unless the implementation plan records an explicit reduction)
  ← site-wide reusable source of truth, updated only for reusable patterns

.opencode/skills/gov-motion-reference/SKILL.md
  ← kit GOV-MOTION-SYSTEM.md → .opencode/skills/gov-motion-reference/SKILL.md (content verbatim, path renamed)
  ← offline evidence rule, clean-room rule, ladder, accessibility gates

docs/superpowers/specs/2026-09-28-gov-motion-design.md
  ← this design

docs/motion/MOTION_SPEC.template.md
  ← per-animation spec template (trigger/purpose/states/evidence class/fallback) with embedded audit checklist section
  ← single file containing two artifacts (template + checklist); created only when a non-trivial animation is proposed, not upfront per page

frontend/src/app.css (untouched in this design)
  ← existing fade-in/slide-in tokens + spinner remain the only motion primitives
```

No `.motion/tools/`, no `.motion/references/` content, no `.opencode/commands/gov-motion.md`, no `SIH-GOV-MOTION-PROMPTS.md` copy, no `.gitignore` change. Untracked `SIH-Gov-Motion-Kit/` stays as reference input, not installed output. `MOTION.md` is read-before-change; only reusable discoveries update it, never one-off timings.

## Section 3 — Motion posture & hard gates

Calm, trustworthy, restrained. Priority: task completion > clarity > accessibility > trust > feedback > polish. Animate only with a concrete UX job (orientation, hierarchy, feedback, continuity, comprehension, perceived responsiveness).

Hard gates (all must pass, else reduce/remove motion):

1. Essential info understandable with motion disabled; motion/color never the sole state signal — critical for `APPLIES / DOES_NOT_APPLY / CONDITIONAL / INSUFFICIENT_DATA` (text + structure + semantics carry meaning; `INSUFFICIENT_DATA` never implies certainty).
2. `prefers-reduced-motion` honored for all non-essential motion; task completable without motion; keyboard focus order, touch/mobile, no hover-only disclosure preserved.
3. No flashing, no unexpected movement of critical content; persistent moving content gets pause/stop/hide.
4. Prefer transform/opacity for ordinary UI; height/clip-path disclosure allowed when implemented accessibly; interruptible repeated interactions; no delay to primary actions or numeric values.
5. Banned by default (needs explicit justification + spec): particles, cursor followers, magnetic buttons, heavy parallax, animated background blobs, continuous decorative loops, WebGL hero scenes, page-wide fade-up, delayed counters, theatrical page transitions.

## Section 4 — Per-area behavior (guardrails, not implementation)

- **Landing/home:** one restrained entrance hierarchy; primary actions usable without waiting; resting page complete with animation disabled. No animated hero backgrounds, particles, or loops.
- **Project wizard / application stages:** motion only for step change, progress, validation, saved-state feedback. Preserve visual + keyboard position; no theatrical page transitions; validation understandable with reduced motion.
- **Applicability results (`APPLIES / DOES_NOT_APPLY / CONDITIONAL / INSUFFICIENT_DATA`):** motion may reveal supporting evidence only; never animates one state into another unless underlying state changed; `INSUFFICIENT_DATA` never implies certainty.
- **Dependencies / orchestration / readiness:** animate actual progression/focus only; no decorative moving connectors; static graph readable; never implies completion when workflow is incomplete.
- **Documents / evidence / consistency / regulatory citations:** quick predictable expand/collapse; title, authority, source/ref, date, status, and findings available without motion; never hide legally important info behind motion-only disclosure.
- **Dashboard / queue / SLA card:** frequently revisited — keep motion density low; no count-up delays on numbers; motion only for changed-data, loading, hierarchy, or new-visualization reveal; reduced-motion/static path required.

## Section 5 — Evidence classification & future reference workflow

Every non-trivial motion claim uses four classes: `EXACT` (measured from local capture/code), `OBSERVED` (seen in screenshot/recording but not measured), `INFERRED` (reasonable interpretation), `DEFAULT` (conservative fallback). Never present `INFERRED`/`DEFAULT` as exact. Clean-room: reproduce behavioral characteristics (trigger, purpose, states, properties, timing, origin, interruption, responsive/reduced-motion behavior) — never copy source, assets, branding, or copy.

No captures exist today, so no `.motion/references/` content is created in this design. When a reference is later proposed, the workflow is: local reference evidence (`CaptureReport.json` when available + screenshots/recording/notes under `.motion/references/<name>/`; MotionLens does not cover every animation type, particularly Canvas/WebGL) → `MOTION_SPEC.md` (facts vs. decisions split, `REJECTED_FOR_CONTEXT` for spectacle inappropriate to government UI) → implement → audit. A URL alone is never evidence; the agent must not browse/fetch. `MOTION.md` updates only for reusable patterns, never one-off timings.

## Section 6 — Implementation ladder & existing-stack rule

Ladder (lowest complexity that satisfies the spec wins):

1. CSS transitions/keyframes via existing Tailwind tokens (`app.css` fade/slide) → 2. WAAPI / CSS scroll-driven → 3. existing project utilities → 4. stop and re-spec. No step 4 = GSAP/new library in this design; any future GSAP proposal must pass the `AGENTS.md` gate (concrete MVP need, why stack cannot satisfy it, maintenance cost) plus `RULES.md` dependency verification in a separate design.

Existing-stack rule: before any motion change, inspect `frontend/package.json`, `app.css` tokens, target component, and shared panels (`SLACard`, `DocumentChecklist`, `ConsistencyPanel`, `OrchestrationPanel`, `RegulatoryAssistant`, `IncentiveSchemes`); reuse tokens/utilities; surgical changes only; no unrelated refactors; no mixing of competing animation approaches.

## Section 7 — Verification & audit gate

No motion is "done" without: relevant frontend checks run via the project's existing frontend scripts/config (currently `tsc`, `oxlint`, `vite build` — named as current defaults, not hardcoded binaries), diff inspection showing only the requested motion, reduced-motion path verified, keyboard/touch/mobile check, no delay to primary actions or data, and reference-fidelity labeling (`EXACT` / `OBSERVED` / `INFERRED` / `DEFAULT` / `UNKNOWN`) where a reference was used. Audit verdicts: `BLOCKER / IMPORTANT / MINOR / PASS` across purpose, timing, easing, origin, interruption, performance (no layout-thrash loops), accessibility, government context, and scope. Never claim "exact reproduction" or "tested" without evidence.

## Section 8 — Rollout & what stays out

Installs (docs + skill only): `.motion/MOTION.md`, `.opencode/skills/gov-motion-reference/SKILL.md`, `docs/motion/MOTION_SPEC.template.md` (containing spec template + audit checklist as two sections in one file), this design document. No `npm`/`pip` adds, no migrations, no API/backend changes, no frontend behavior changes. Total new tracked surface: two tracked configuration/skill files + two motion documentation artifacts, plus this design document.

Explicitly deferred with re-entry conditions: MotionVault/MotionLens clone + build (only if a real reference needing structural extraction appears); Emil/GSAP/motion-ref skills (only if a concrete sequencing/scroll choreography need passes the gates); any runtime lib (only via separate design passing `AGENTS.md` gate + `RULES.md` verification); `/gov-motion` command (only after the skill proves useful manually); any page animation (only via `MOTION_SPEC.md` + audit).

Anti-overengineering gate answers recorded: (1) MVP need = consistent, accessible orientation/feedback without new deps; (2) existing stack suffices (Tailwind/WAAPI); (3) cost = two tracked configuration/skill files + two motion documentation artifacts, plus this design document, with no runtime maintenance.

## Next step

Invoke `writing-plans` skill to create the implementation plan (docs/skill/template creation only, no behavior changes).
