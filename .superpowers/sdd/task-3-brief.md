## Task 3: Register workflow events dependency

**Files:**
- Modify: `backend/app/api/deps.py`

**Interfaces:**
- Consumes: `WorkflowEventsRepository` from Task 2
- Produces: `get_workflow_events_repository()` FastAPI dependency

- [ ] **Step 1: Add the dependency**

```python
# Add to backend/app/api/deps.py â€” add import at top and function at bottom

# Add to imports:
from app.repositories.workflow_events import WorkflowEventsRepository

# Add function at bottom:
def get_workflow_events_repository(
    client: Client = Depends(get_db_client),
) -> WorkflowEventsRepository:
    """Get workflow events repository dependency."""
    return WorkflowEventsRepository(client)
```

- [ ] **Step 2: Verify import works**

Run: `cd backend && python -c "from app.api.deps import get_workflow_events_repository; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/deps.py
git commit -m "feat: register WorkflowEventsRepository dependency"
```

---

