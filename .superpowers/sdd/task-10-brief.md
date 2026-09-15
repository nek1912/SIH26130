## Task 10: Frontend SLA Display â€” Staff Page

**Files:**
- Modify: `frontend/src/pages/staff/ApplicationDetailPage.tsx`

**Interfaces:**
- Consumes: `api.applications.getSla()` from Task 8
- Produces: SLA card on staff application detail page

- [ ] **Step 1: Add SLA state and fetch**

Same pattern as Task 9 â€” add SlaInfo import, state, and useEffect.

- [ ] **Step 2: Add SLA card JSX**

Add after the "Current Status" / "Available Actions" grid and before the "Details" card. Use the same SLA card JSX from Task 9.

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Verify build**

Run: `cd frontend && npx vite build`
Expected: Build success

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/staff/ApplicationDetailPage.tsx
git commit -m "feat: add SLA status card to staff application detail page"
```

---

