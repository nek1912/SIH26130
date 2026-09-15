## Task 9: Frontend SLA Display â€” Applicant Page

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`

**Interfaces:**
- Consumes: `api.applications.getSla()` from Task 8
- Produces: SLA card on applicant application detail page

- [ ] **Step 1: Add SLA state and fetch**

In `frontend/src/pages/applicant/ApplicationDetailPage.tsx`:

1. Add import for SlaInfo:
```typescript
import type { Application, WorkflowResult, DocumentRequirement, UploadedDocument, ExtractionSummary, ConsistencyResult, SlaInfo } from '@/types/api'
```

2. Add state:
```typescript
const [sla, setSla] = useState<SlaInfo | null>(null)
```

3. Add useEffect to fetch SLA:
```typescript
useEffect(() => {
  if (!id) return
  api.applications.getSla(id).then(setSla).catch(() => {})
}, [id])
```

- [ ] **Step 2: Add SLA card JSX**

Add after the "Next Action / Hint" card and before the "Actions" card:

```tsx
{/* SLA Status */}
{sla && (
  <Card>
    <CardHeader>
      <CardTitle className="text-base">SLA Status</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="flex items-center gap-4">
        <div>
          <p className="text-sm font-medium">{sla.stage_label}</p>
          <p className="text-xs text-muted-foreground">
            Target: {sla.sla_business_days} business days
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm">
            Due: {new Date(sla.due_date).toLocaleDateString()}
          </p>
          <p className="text-xs text-muted-foreground">
            {sla.remaining_business_days > 0
              ? `${sla.remaining_business_days} days remaining`
              : `${sla.overdue_business_days} days overdue`}
          </p>
        </div>
        <span
          className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
            sla.state === 'on_track'
              ? 'bg-green-100 text-green-800'
              : sla.state === 'due_soon' || sla.state === 'due_today'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
          }`}
        >
          {sla.state === 'on_track'
            ? 'On Track'
            : sla.state === 'due_soon'
              ? 'Due Soon'
              : sla.state === 'due_today'
                ? 'Due Today'
                : 'Breached'}
        </span>
      </div>
    </CardContent>
  </Card>
)}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Verify build**

Run: `cd frontend && npx vite build`
Expected: Build success

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/applicant/ApplicationDetailPage.tsx
git commit -m "feat: add SLA status card to applicant application detail page"
```

---

