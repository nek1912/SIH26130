# Gov Motion System Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install the approved minimal local motion source-of-truth (docs + project-local skill only) with zero behavior changes.

**Architecture:** Copy two kit files verbatim to their tracked locations and create one new template file containing the MOTION_SPEC template plus embedded audit checklist. No tooling, runtimes, commands, or page animation.

**Tech Stack:** Markdown files only; PowerShell for file operations; git for verification. No npm/pip, no migrations, no API/backend/frontend code changes.

## Global Constraints

- No new runtime dependencies (no GSAP, no Three.js, no animation library; CSS/Tailwind/WAAPI only).
- Do not clone, build, or install MotionVault/MotionLens (no `.motion/tools/`, no `.motion/references/` content).
- Do not clone Emil, GSAP, or motion-ref skills; only project-local `gov-motion-reference` skill.
- Do not create `.opencode/commands/gov-motion.md` or any `/gov-motion` command.
- Do not implement any page animation or modify any frontend/backend behavior.
- No `npm`/`pip` adds, no migrations, no API/backend changes, no `frontend/src` changes, no `.gitignore` change.
- `.motion/MOTION.md` is copied from `SIH-Gov-Motion-Kit/sih-gov-motion-kit/MOTION.md` verbatim; any trimming required by the approved scope must be explicitly documented in the commit message (auditable, no silent edits).
- `.opencode/skills/gov-motion-reference/SKILL.md` content is verbatim from kit `GOV-MOTION-SYSTEM.md`, path renamed only.
- Design document `docs/superpowers/specs/2026-09-28-gov-motion-design.md` already exists — implementation plan must not recreate or modify it.
- A URL alone is never evidence; agent must not browse/fetch (skill rule, no action needed in this plan).
- Evidence classes `EXACT / OBSERVED / INFERRED / DEFAULT` and hard gates from Sections 3 and 5 apply to future motion work, not to this install.
- Verification runs via the project's existing frontend scripts/config where applicable; this plan touches no frontend code so build checks are a no-regression gate only.

---

## File structure

- Create: `.motion/MOTION.md` — site-wide motion source of truth; verbatim copy of kit `MOTION.md`; read-before-change in future work; updated only for reusable patterns.
- Create: `.opencode/skills/gov-motion-reference/SKILL.md` — project-local skill; verbatim content of kit `GOV-MOTION-SYSTEM.md`; offline evidence rule, clean-room rule, ladder, accessibility gates.
- Create: `docs/motion/MOTION_SPEC.template.md` — single file with two sections: (A) per-animation MOTION_SPEC template, (B) audit checklist; created now as empty template, filled per-animation only when non-trivial motion is later proposed.
- Existing (do not touch): `docs/superpowers/specs/2026-09-28-gov-motion-design.md`, `frontend/src/app.css`, `frontend/package.json`, all `backend/` files.
- Must not exist after plan: `.motion/tools/`, `.motion/references/` content, `.opencode/commands/gov-motion.md`, `SIH-GOV-MOTION-PROMPTS.md` copy at repo root.

---

### Task 1: Install `.motion/MOTION.md` verbatim

**Files:**
- Create: `.motion/MOTION.md`
- Source: `SIH-Gov-Motion-Kit/sih-gov-motion-kit/MOTION.md`
- Test: file exists and `git diff --no-index` against source shows no content difference

**Interfaces:**
- Consumes: kit source file (60 lines, motion posture + component defaults + audit checklist).
- Produces: tracked `.motion/MOTION.md` used by Task 3 template references and all future motion work.

- [ ] **Step 1: Confirm source exists and show expected line count**

Run:

```powershell
Test-Path -LiteralPath "SIH-Gov-Motion-Kit/sih-gov-motion-kit/MOTION.md"
(Get-Content -LiteralPath "SIH-Gov-Motion-Kit/sih-gov-motion-kit/MOTION.md").Count
Test-Path -LiteralPath ".motion/MOTION.md"
```

Expected: `True`, `60`, `False` (source present, destination absent).

- [ ] **Step 2: Create directory and copy verbatim**

Run:

```powershell
New-Item -ItemType Directory -Force -Path ".motion" | Out-Null
Copy-Item -LiteralPath "SIH-Gov-Motion-Kit/sih-gov-motion-kit/MOTION.md" -Destination ".motion/MOTION.md" -Force
Get-Content -LiteralPath ".motion/MOTION.md" -TotalCount 5
```

Expected: first 5 lines show `# MOTION.md — SIH Government Service Motion System`, blank, `## Motion identity`, `Calm, trustworthy, restrained, purposeful, responsive.`, `Motion exists to improve orientation, continuity, feedback, hierarchy, and comprehension.`

- [ ] **Step 3: Verify verbatim (no silent edits)**

Run:

```powershell
git diff --no-index -- SIH-Gov-Motion-Kit/sih-gov-motion-kit/MOTION.md .motion/MOTION.md; if ($LASTEXITCODE -eq 0) { "IDENTICAL" } else { "DIFFERENT" }
```

Expected: `IDENTICAL`. If `DIFFERENT`, delete destination and repeat Step 2; do not hand-edit. If trimming is required by approved scope, document the exact removed lines in the commit message (auditable).

- [ ] **Step 4: Commit**

```bash
git add .motion/MOTION.md
git commit -m "feat(motion): add MOTION.md source-of-truth (verbatim from kit)"
```

Expected: commit succeeds; `git status --short .motion/` shows clean.

---

### Task 2: Install `gov-motion-reference` skill verbatim

**Files:**
- Create: `.opencode/skills/gov-motion-reference/SKILL.md`
- Source: `SIH-Gov-Motion-Kit/sih-gov-motion-kit/GOV-MOTION-SYSTEM.md`
- Test: file exists and `git diff --no-index` against source shows no content difference

**Interfaces:**
- Consumes: kit `GOV-MOTION-SYSTEM.md` (66 lines including `gov-motion-reference` frontmatter).
- Produces: project-local OpenCode skill consumed by future reference analysis, implementation, and audit work.

- [ ] **Step 1: Confirm source is the skill source (no SKILL.md in kit)**

Run:

```powershell
Test-Path -LiteralPath "SIH-Gov-Motion-Kit/sih-gov-motion-kit/GOV-MOTION-SYSTEM.md"
Test-Path -LiteralPath "SIH-Gov-Motion-Kit/sih-gov-motion-kit/SKILL.md"
Get-Content -LiteralPath "SIH-Gov-Motion-Kit/sih-gov-motion-kit/GOV-MOTION-SYSTEM.md" -TotalCount 6
Test-Path -LiteralPath ".opencode/skills/gov-motion-reference/SKILL.md"
```

Expected: `True`, `False`, frontmatter lines (`---`, `name: gov-motion-reference`, `description:`, `license: MIT`, `compatibility: opencode`, `---`), then `False`.

- [ ] **Step 2: Create directory and copy with path rename only**

Run:

```powershell
New-Item -ItemType Directory -Force -Path ".opencode/skills/gov-motion-reference" | Out-Null
Copy-Item -LiteralPath "SIH-Gov-Motion-Kit/sih-gov-motion-kit/GOV-MOTION-SYSTEM.md" -Destination ".opencode/skills/gov-motion-reference/SKILL.md" -Force
Get-Content -LiteralPath ".opencode/skills/gov-motion-reference/SKILL.md" -TotalCount 6
```

Expected: same 6 frontmatter lines as source; no content edits.

- [ ] **Step 3: Verify verbatim**

Run:

```powershell
git diff --no-index -- SIH-Gov-Motion-Kit/sih-gov-motion-kit/GOV-MOTION-SYSTEM.md .opencode/skills/gov-motion-reference/SKILL.md; if ($LASTEXITCODE -eq 0) { "IDENTICAL" } else { "DIFFERENT" }
```

Expected: `IDENTICAL`. If `DIFFERENT`, redo Step 2 without edits.

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/gov-motion-reference/SKILL.md
git commit -m "feat(motion): add gov-motion-reference skill (verbatim from kit GOV-MOTION-SYSTEM.md)"
```

Expected: commit succeeds; `git status --short .opencode/` shows clean.

---

### Task 3: Create `docs/motion/MOTION_SPEC.template.md` with embedded audit checklist

**Files:**
- Create: `docs/motion/MOTION_SPEC.template.md`
- Test: file exists; `Select-String` finds zero `TBD|TODO|XXX|FIXME`; both `## A.` and `## B.` sections present

**Interfaces:**
- Consumes: `.motion/MOTION.md` and skill from Tasks 1–2 (referenced by path only, not modified).
- Produces: empty per-animation template filled only when non-trivial motion is later proposed; audit checklist used by future verification gates.

- [ ] **Step 1: Create directory and write the exact template file**

Run (file content is exact — write verbatim):

```powershell
New-Item -ItemType Directory -Force -Path "docs/motion" | Out-Null
```

Then create `docs/motion/MOTION_SPEC.template.md` with this exact content:

```markdown
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
```

- [ ] **Step 2: Verify no placeholders and both sections present**

Run:

```powershell
Test-Path -LiteralPath "docs/motion/MOTION_SPEC.template.md"
Select-String -LiteralPath "docs/motion/MOTION_SPEC.template.md" -Pattern "TBD|TODO|XXX|FIXME" | Measure-Object | Select-Object -ExpandProperty Count
Select-String -LiteralPath "docs/motion/MOTION_SPEC.template.md" -Pattern "^## A\.|^## B\." | Select-Object LineNumber, Line
```

Expected: `True`, `0`, two matches for `## A.` and `## B.`.

- [ ] **Step 3: Commit**

```bash
git add docs/motion/MOTION_SPEC.template.md
git commit -m "feat(motion): add MOTION_SPEC template with embedded audit checklist"
```

Expected: commit succeeds.

---

### Task 4: Final scope and no-regression gate

**Files:**
- Modify: none (verification only)
- Test: `git status`, forbidden-path checks, design-doc untouched check

**Interfaces:**
- Consumes: deliverables of Tasks 1–3.
- Produces: verified clean scope; proof that deferred items stayed out.

- [ ] **Step 1: Prove only the three intended files changed**

Run:

```powershell
git log --oneline -4
git status --short
```

Expected: last 3 commits are the Task 1–3 commits plus the prior spec-clarification commit; `git status --short` shows no modified/untracked files except possibly nothing (clean). Any other modified file is a scope violation — revert it.

- [ ] **Step 2: Prove deferred items stayed out**

Run:

```powershell
Test-Path -LiteralPath ".motion/tools"
Test-Path -LiteralPath ".motion/references"
Test-Path -LiteralPath ".opencode/commands/gov-motion.md"
Test-Path -LiteralPath "SIH-GOV-MOTION-PROMPTS.md"
git status --short frontend/ backend/ supabase/
```

Expected: `False`, `False`, `False`, `False` (no tooling, no references content, no command, no prompts copy at root), and no output for the `git status` scope (no frontend/backend/supabase changes).

- [ ] **Step 3: Prove design doc was not recreated or modified**

Run:

```powershell
git log --oneline -1 -- docs/superpowers/specs/2026-09-28-gov-motion-design.md
git status --short docs/superpowers/specs/2026-09-28-gov-motion-design.md
```

Expected: last commit touching the design doc is `docs: clarify motion spec artifact count and MOTION.md verbatim rule`; status shows clean (no modifications in this plan).

- [ ] **Step 4: No commit (gate only)**

No commit in this task. If all checks pass, report the three created files, the verification outputs, and remaining uncertainty (none expected). If any check fails, stop and report before proceeding.

---
