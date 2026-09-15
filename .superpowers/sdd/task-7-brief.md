## Task 7: Trigger Background Extraction on Upload

**Files:**
- Modify: `backend/app/api/documents.py` (add BackgroundTasks to upload endpoint)

**Interfaces:**
- Consumes: `run_extraction_background()` from Task 6
- Produces: Upload returns immediately, extraction runs in background

- [ ] **Step 1: Modify upload endpoint**

In `backend/app/api/documents.py`:

1. Add import at top:
```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
```

2. Add `BackgroundTasks` parameter to `upload_document` endpoint:
```python
@router.post("/applications/{application_id}/documents/{requirement_key}/upload")
async def upload_document(
    application_id: str,
    requirement_key: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),  # NEW
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
        )
    ),
):
```

3. After the audit record creation (before `return`), add:
```python
    # Trigger background extraction
    from app.extraction.background import run_extraction_background
    background_tasks.add_task(
        run_extraction_background, document["id"], application_id
    )
```

- [ ] **Step 2: Verify syntax**

Run: `cd backend && python -c "from app.api.documents import router; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Run existing document tests**

Run: `cd backend && python -m pytest tests/test_document_upload.py -v`
Expected: All tests PASS (BackgroundTasks is a no-op in TestClient by default)

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/documents.py
git commit -m "feat: trigger background extraction on document upload"
```

---

