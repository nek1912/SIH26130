## Task 8: Frontend Types and API Client

**Files:**
- Modify: `frontend/src/types/api.ts` (add SlaInfo, extraction_status)
- Modify: `frontend/src/lib/api.ts` (add applications.getSla)

**Interfaces:**
- Consumes: Backend SLA endpoint from Task 5
- Produces: TypeScript types + API client method for frontend

- [ ] **Step 1: Add SlaInfo type to api.ts**

```typescript
// Add to frontend/src/types/api.ts â€” after the Application interface

export interface SlaInfo {
  stage_key: string
  stage_label: string
  sla_business_days: number
  entered_at: string
  due_date: string
  used_business_days: number
  remaining_business_days: number
  overdue_business_days: number
  state: 'on_track' | 'due_soon' | 'due_today' | 'breached'
}
```

- [ ] **Step 2: Add extraction_status to UploadedDocument**

```typescript
// Modify UploadedDocument interface in frontend/src/types/api.ts
// Add extraction_status field:

export interface UploadedDocument {
  id: string
  application_id: string
  requirement_key: string
  original_filename: string
  storage_path: string
  mime_type: string
  file_size_bytes: number
  status: 'pending_upload' | 'uploaded' | 'verified' | 'rejected' | 'virus_detected' | 'expired'
  extraction_status: ExtractionStatus | null  // NEW
  rejection_reason: string | null
  uploaded_by_user_id: string | null
  created_at: string
}
```

- [ ] **Step 3: Add applications.getSla to API client**

```typescript
// Add to api.applications in frontend/src/lib/api.ts

  applications: {
    // ... existing methods ...
    getSla: (appId: string) =>
      request<SlaInfo | null>(`/applications/${appId}/sla`),
  },
```

Also add `SlaInfo` to the imports at the top of api.ts:
```typescript
import type {
  DocumentRequirement,
  UploadedDocument,
  UploadResult,
  ExtractionResult,
  ValidationResult,
  ExtractionSummary,
  ConsistencyResult,
  SlaInfo,
} from '../types/api'
```

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/lib/api.ts
git commit -m "feat: add SlaInfo type and getSla API client method"
```

---

