# Task 7-9 Report: Consistency Frontend Integration

## What Was Implemented

### TypeScript Types (`frontend/src/types/api.ts`)
- `ConsistencyOutcome` — union type: `VALID | REVIEW_REQUIRED | INSUFFICIENT_DATA`
- `ConsistencyFinding` — interface for individual rule findings with `rule_id`, `canonical_field`, `outcome`, `observed_values`, `expected_relationship`, `message`, `source_ref`
- `ConsistencyResult` — top-level result with `application_id`, `outcome`, `findings[]`, `checked_at`, `rule_version`

### API Client (`frontend/src/lib/api.ts`)
- Extracted `authHeaders()` helper (async, returns auth headers from Supabase session) — reused by `request()` and new consistency methods
- `api.consistency.check(appId)` — POST to trigger consistency check, returns `ConsistencyResult`
- `api.consistency.get(appId)` — GET latest result, returns `null` on 404

### Staff ApplicationDetailPage (`frontend/src/pages/staff/ApplicationDetailPage.tsx`)
- Added `consistency` and `consistencyLoading` state
- Added `useEffect` to fetch existing consistency result on mount
- Added `handleRunConsistency` handler
- Added "Cross-Document Consistency" card after the Details card with outcome badge, findings table, and "Run Check" button

### Applicant ApplicationDetailPage (`frontend/src/pages/applicant/ApplicationDetailPage.tsx`)
- Same state, handlers, and JSX as staff page
- Added after the Document Checklist card
- Matches applicant page styling conventions (Card/CardHeader/CardContent pattern)

## Build Results

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | ✅ Pass — no errors |
| `npx oxlint` | ✅ Pass — only pre-existing warnings (QueuePage setState-in-effect, AuthContext export) |
| `npx vite build` | ✅ Pass — built in 1.43s |

## Files Changed

| File | Changes |
|------|---------|
| `frontend/src/types/api.ts` | +18 lines (3 new types) |
| `frontend/src/lib/api.ts` | +16 lines (authHeaders helper + 2 API methods) |
| `frontend/src/pages/staff/ApplicationDetailPage.tsx` | +73 lines (state, effects, handlers, JSX section) |
| `frontend/src/pages/applicant/ApplicationDetailPage.tsx` | +73 lines (state, effects, handlers, JSX section) |

## Commit

```
eaed918 feat(consistency): add frontend types, API client, and consistency UI
```

## Concerns

- The `authHeaders()` helper was added as an async function since the existing codebase had no shared auth header utility. This is a minor refactor but improves consistency across the API client.
- Pre-existing lint warnings in `QueuePage.tsx` (setState in effect) and `AuthContext.tsx` (multi-export) were not addressed as they are outside scope.
- Build chunk size warning (526 KB) is pre-existing and unrelated to this change.
