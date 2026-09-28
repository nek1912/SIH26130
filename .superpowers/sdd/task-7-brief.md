Task 7: Add ReadinessCard to Applicant Application Detail

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`

## Implementation

Add a simplified "Readiness / Next Action" card to the applicant application detail page. This is a simpler version than the staff page — show status, next action, and blockers; hide internal dependency details.

### 1. Add imports

Add `ApplicationOrchestration` to the type imports at the top of the file.

### 2. Add state and data fetching

After the existing `sla` state, add:
```typescript
const [orchestration, setOrchestration] = useState<ApplicationOrchestration | null>(null)
```

After the existing SLA useEffect, add:
```typescript
useEffect(() => {
  if (!id) return
  api.orchestration.get(id).then(setOrchestration).catch(() => {})
}, [id])
```

### 3. Add ReadinessCard component

Add a Card after the SLA Status card and before the Actions card. Simplified for applicants:

**Header:** "Next Steps"

**Content:**
1. **Overall Status Badge** — same color scheme as staff page
2. **Next Action** (if present):
   - Description text
   - Affected approval ID (if present)
3. **Blockers** (if any):
   - Show user-friendly descriptions
   - Don't show internal dependency graph details
   - Focus on actionable items: "Upload document X", "Wait for prerequisite approval Y"

### 4. Place the card

Insert after the SLA Status card (around line 341, after the `)}` closing the SLA card), before the Actions card.

### Style

Use existing UI components. Keep it simpler than the staff version — no per-approval breakdown, no expandable sections.

## Verification

Run: `cd frontend && npx tsc --noEmit && npx vite build`
Expected: tsc 0 errors, build success

## Commit

```bash
git add frontend/src/pages/applicant/ApplicationDetailPage.tsx
git commit -m "feat(orchestration): add readiness card to applicant application detail"
```
