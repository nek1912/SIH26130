Task 6: Add ReadinessCard to Staff Application Detail

**Files:**
- Modify: `frontend/src/pages/staff/ApplicationDetailPage.tsx`

## Implementation

Add a "Readiness / Next Action" card to the staff application detail page. This card shows the orchestration result: overall status, blockers, next action, and per-approval breakdown.

### 1. Add imports

Add `ApplicationOrchestration` to the type imports at the top of the file.

### 2. Add state and data fetching

After the existing `sla` state (around line 59), add:
```typescript
const [orchestration, setOrchestration] = useState<ApplicationOrchestration | null>(null)
```

After the existing SLA useEffect (around line 86), add:
```typescript
useEffect(() => {
  if (!id) return
  api.orchestration.get(id).then(setOrchestration).catch(() => {})
}, [id])
```

### 3. Add ReadinessCard component

Add a new Card component after the SLA Status card and before the Application Details card. The card should show:

**Header:** "Readiness / Next Action"

**Content:**
1. **Overall Status Badge** — color-coded:
   - READY: green (`bg-green-100 text-green-800`)
   - BLOCKED_BY_DEPENDENCY / BLOCKED_BY_DOCUMENTS: red (`bg-red-100 text-red-800`)
   - REVIEW_REQUIRED: yellow (`bg-yellow-100 text-yellow-800`)
   - INSUFFICIENT_DATA / NOT_APPLICABLE: gray (`bg-gray-100 text-gray-800`)

2. **Next Action** (if present):
   - Description text
   - Affected approval ID (if present)

3. **Blockers** (if any):
   - List each blocker with: type badge, description, action_required
   - Color-code by type (dependency=red, document=orange, review=yellow)

4. **Per-Approval Summary** (collapsed/expandable):
   - Show approval ID, status badge, document_readiness
   - Only show approvals that are NOT not_applicable

### 4. Place the card

Insert after the SLA Status card (around line 370, after the `)}` closing the SLA card).

### Style

Use existing UI components: Card, CardContent, CardHeader, CardTitle, Button, Badge patterns from the file. Use the same Tailwind classes used throughout the file.

## Verification

Run: `cd frontend && npx tsc --noEmit && npx vite build`
Expected: tsc 0 errors, build success

## Commit

```bash
git add frontend/src/pages/staff/ApplicationDetailPage.tsx
git commit -m "feat(orchestration): add readiness card to staff application detail"
```
