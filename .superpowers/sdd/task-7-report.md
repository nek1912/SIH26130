# Task 7: Add ReadinessCard to Applicant Application Detail — Report

## Status: DONE

## Commit
`0b12cb5` — feat(orchestration): add readiness card to applicant application detail

## Changes
Modified `frontend/src/pages/applicant/ApplicationDetailPage.tsx`:
- Added `ApplicationOrchestration` to the type import
- Added `orchestration` state and `useEffect` fetching via `api.orchestration.get(id)`
- Added a simplified "Next Steps" card after SLA Status and before Actions

## Card Contents
1. **Overall Status Badge** — color-coded: READY (green), BLOCKED (red), REVIEW_REQUIRED (yellow), other (gray)
2. **Blocker count** — displayed next to the badge
3. **Explanation** — shown as muted text
4. **Next Action** — blue highlighted box with description and affected approval ID if present
5. **Blockers** — red boxes per blocker with user-friendly `description` and `action_required` fields; hides internal dependency graph details

## Verification
- `tsc --noEmit`: 0 errors
- `vite build`: success (540 kB JS, 24 kB CSS)
