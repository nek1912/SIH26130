# Task 5: Add Frontend Orchestration Types and API

## Summary

Added TypeScript types and API client method for the orchestration subsystem to the React frontend.

## Changes

### `frontend/src/types/api.ts`
- Added `OrchestrationStatus` union type (7 status values)
- Added `BlockerDetail` interface
- Added `DocumentReadinessSummary` interface
- Added `ApprovalOrchestration` interface
- Added `NextAction` interface
- Added `ApplicationOrchestration` interface

### `frontend/src/lib/api.ts`
- Added `ApplicationOrchestration` to imports
- Added `orchestration.get(appId)` method to the `api` object

## Verification
- `npx tsc --noEmit` passed with 0 errors
