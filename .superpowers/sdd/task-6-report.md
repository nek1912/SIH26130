# Task 6: Add ReadinessCard to Staff Application Detail

## Status: DONE

## Changes

Modified: `frontend/src/pages/staff/ApplicationDetailPage.tsx`

### What was done:
1. Added `ApplicationOrchestration` to type imports from `@/types/api`
2. Added `orchestration` state via `useState<ApplicationOrchestration | null>(null)`
3. Added `useEffect` to fetch orchestration data via `api.orchestration.get(id)`
4. Added ReadinessCard component after the SLA Status card, before the Application Details card

### ReadinessCard features:
- **Overall Status Badge**: Color-coded by status (green=READY, red=BLOCKED_*, yellow=REVIEW_REQUIRED, gray=others)
- **Explanation text**: Shows `orchestration.explanation`
- **Next Action**: Blue callout box with description and affected approval ID (if present)
- **Per-Approval Summary**: Expandable `<details>` showing each approval's status badge, explanation, document readiness, and blocker count. Filters out NOT_APPLICABLE approvals.

## Verification

- `npx tsc --noEmit`: 0 errors
- `npx vite build`: success (538.46 kB JS, 23.99 kB CSS)

## Commit

```
f529ecb feat(orchestration): add readiness card to staff application detail
```

## Concerns

None.
