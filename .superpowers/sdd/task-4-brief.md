Task 4: Create Orchestration API Endpoint

**Files:**
- Create: `backend/app/api/orchestration.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_orchestration_api.py`

**Interfaces:**
- Consumes: `orchestrate_application_full()` from `app.orchestration.service`
- Consumes: seed data (approval rules, dependencies, authorities, document requirements)
- Consumes: existing repositories (applications, project_facts, documents)
- Produces: `GET /applications/{id}/orchestration` endpoint

## Implementation

### 1. Create `backend/app/api/orchestration.py`

Follow the exact pattern from `backend/app/api/applications.py` (SLA endpoint at line 163).

```python
"""Orchestration endpoint — readiness/blocking status for an application."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    get_applications_repository,
    get_documents_repository,
    get_project_facts_repository,
)
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.orchestration.service import orchestrate_application_full
from app.repositories.applications import ApplicationsRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.seed.approvals import load_approval_rules, load_approval_authorities
from app.seed.dependencies import load_approval_dependencies
from app.seed.documents import load_document_requirements

router = APIRouter()


@router.get("/applications/{application_id}/orchestration")
async def get_application_orchestration(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    facts_repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    docs_repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get orchestration readiness status for an application.

    Returns per-approval readiness, blockers, next action, and overall status.
    """
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    project_id = application.get("project_id")
    approval_id = application.get("approval_id")

    # Load project facts
    facts = {}
    if project_id:
        facts_record = facts_repo.get_by_project(project_id)
        if facts_record:
            facts = {k: v for k, v in facts_record.items() if k not in ("id", "project_id", "created_at", "updated_at")}

    # Load documents
    uploaded_docs = docs_repo.list_for_application(str(application_id)) if docs_repo else []
    doc_requirements = load_document_requirements()

    # Load seed data
    rules = load_approval_rules()
    authorities = load_approval_authorities()
    dependencies = load_approval_dependencies()

    # Determine which approvals have been obtained (approved status)
    # For now, no approvals are "obtained" since this is a per-application view
    obtained: set[str] = set()

    # Determine all approval IDs to evaluate
    all_approval_ids = [f"A{i:02d}" for i in range(1, 19)]

    # Run orchestration
    result = orchestrate_application_full(
        application_id=str(application_id),
        project_facts=facts,
        approval_rules=rules,
        approval_authorities=authorities,
        dependencies=dependencies,
        all_approval_ids=all_approval_ids,
        document_requirements=doc_requirements,
        uploaded_documents=uploaded_docs,
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=obtained,
    )

    return result.model_dump()
```

### 2. Register router in `backend/app/main.py`

Add to imports: `from app.api import orchestration`
Add to routers: `app.include_router(orchestration.router, tags=["orchestration"])`

### 3. Create `backend/tests/test_orchestration_api.py`

Write minimal API tests:
1. `test_orchestration_endpoint_returns_200` — Mock auth, call endpoint, verify 200 + response shape
2. `test_orchestration_endpoint_returns_401` — No auth token, verify 401
3. `test_orchestration_endpoint_returns_404` — Non-existent application, verify 404

Follow existing API test patterns from `backend/tests/test_api_projects.py` or `backend/tests/test_sla_api.py`.

## Verification

1. Run new tests: `cd backend && python -m pytest tests/test_orchestration_api.py -v`
2. Run full suite: `cd backend && python -m pytest tests/ --tb=short -q`
3. Run ruff: `cd backend && python -m ruff check app/ tests/`

## Commit

```bash
git add backend/app/api/orchestration.py backend/app/main.py backend/tests/test_orchestration_api.py
git commit -m "feat(orchestration): add GET /applications/{id}/orchestration endpoint"
```
