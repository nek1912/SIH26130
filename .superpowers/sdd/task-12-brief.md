## Task 12: Full Test Suite and Verification

**Files:**
- No new files â€” verification only

**Interfaces:**
- Consumes: All previous tasks
- Produces: Clean test suite, no regressions

- [ ] **Step 1: Run backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests PASS (including new tests from Tasks 2, 4, 5, 6)

- [ ] **Step 2: Run backend lint**

Run: `cd backend && python -m ruff check app/ tests/`
Expected: All checks PASS

- [ ] **Step 3: Run frontend checks**

Run: `cd frontend && npx tsc --noEmit && npx oxlint && npx vite build`
Expected: 0 TypeScript errors, lint clean, build success

- [ ] **Step 4: Run full backend test count**

Run: `cd backend && python -m pytest tests/ --co -q | tail -1`
Expected: Count should be 527+ (existing) + new tests from this phase

- [ ] **Step 5: Final commit with all changes**

```bash
git add -A
git commit -m "feat: Phase 5 complete â€” SLA display + background extraction

- Persist workflow events to DB for SLA computation
- GET /applications/{id}/sla endpoint
- Background extraction on upload via FastAPI BackgroundTasks
- Extraction status (pending/running/succeeded/failed/unsupported) on documents
- SLA status card on applicant and staff application detail pages
- Idempotent extraction with error handling
- 527+ backend tests passing, frontend builds clean"
```

---

## Summary

| Task | Deliverable | Tests |
|------|-------------|-------|
| 1 | DB migration | â€” |
| 2 | WorkflowEventsRepository | 3 |
| 3 | Dependency registration | â€” |
| 4 | Event persistence on transitions | 3 |
| 5 | SLA API endpoint | 2+ |
| 6 | Background extraction job | 3 |
| 7 | Upload â†’ background extraction trigger | â€” |
| 8 | Frontend types + API client | â€” |
| 9 | Applicant SLA card | â€” |
| 10 | Staff SLA card | â€” |
| 11 | Extraction status badges | â€” |
| 12 | Full verification | â€” |

