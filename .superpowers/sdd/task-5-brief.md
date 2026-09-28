Task 5: Add Frontend Orchestration Types and API

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/lib/api.ts`

## Implementation

### 1. Add TypeScript types to `frontend/src/types/api.ts`

Add the following types at the end of the file (before the last line):

```typescript
export type OrchestrationStatus =
  | 'READY'
  | 'BLOCKED_BY_DEPENDENCY'
  | 'BLOCKED_BY_DOCUMENTS'
  | 'REVIEW_REQUIRED'
  | 'INSUFFICIENT_DATA'
  | 'COMPLETE'
  | 'NOT_APPLICABLE'

export interface BlockerDetail {
  blocker_type: string
  description: string
  affected_approval_id: string | null
  affected_document_key: string | null
  source_ref: string
  evidence: string
  action_required: string
}

export interface DocumentReadinessSummary {
  requirement_key: string
  document_name: string
  readiness: string
  extraction_status: string | null
  validation_outcome: string | null
  blocking: boolean
  reason: string
}

export interface ApprovalOrchestration {
  approval_id: string
  status: OrchestrationStatus
  applicability_result: string
  dependency_readiness: string
  document_readiness: string
  consistency_outcome: string | null
  sla_state: string | null
  blockers: BlockerDetail[]
  documents: DocumentReadinessSummary[]
  explanation: string
  next_action: string
}

export interface NextAction {
  action_type: string
  description: string
  affected_approval_id: string | null
  affected_document_key: string | null
  link_section: string
}

export interface ApplicationOrchestration {
  application_id: string
  overall_status: OrchestrationStatus
  approvals: Record<string, ApprovalOrchestration>
  total_blockers: number
  next_action: NextAction | null
  stage_number: number | null
  explanation: string
}
```

### 2. Add API client method to `frontend/src/lib/api.ts`

Add to the `api` object (after the `consistency` block, before the closing `}`):

```typescript
orchestration: {
  get: (appId: string) =>
    request<ApplicationOrchestration>(`/applications/${appId}/orchestration`),
},
```

Also add `ApplicationOrchestration` to the imports at the top of the file (it's already importing from `../types/api`).

## Verification

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

## Commit

```bash
git add frontend/src/types/api.ts frontend/src/lib/api.ts
git commit -m "feat(orchestration): add frontend types and API client method"
```
