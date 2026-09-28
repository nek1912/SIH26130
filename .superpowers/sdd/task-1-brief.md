Task 1: Create Orchestration Data Models

**Files:**
- Create: `backend/app/orchestration/__init__.py`
- Create: `backend/app/orchestration/models.py`

**Interfaces:**
- Produces: `OrchestrationStatus`, `BlockerType`, `BlockerDetail`, `DocumentReadinessSummary`, `ApprovalOrchestration`, `NextAction`, `ApplicationOrchestration`

- [ ] **Step 1: Create module init**

```python
"""Approval orchestration — combines all engines into readiness assessments."""
```

- [ ] **Step 2: Create orchestration models**

Create `backend/app/orchestration/models.py` with the following types:

**OrchestrationStatus** (StrEnum): READY, BLOCKED_BY_DEPENDENCY, BLOCKED_BY_DOCUMENTS, REVIEW_REQUIRED, INSUFFICIENT_DATA, COMPLETE, NOT_APPLICABLE

**BlockerType** (StrEnum): dependency, document_missing, document_invalid, document_review_required, extraction_failed, consistency_review, insufficient_data, sla_breached

**BlockerDetail** (BaseModel): blocker_type (BlockerType), description (str), affected_approval_id (str|None), affected_document_key (str|None), source_ref (str), evidence (str), action_required (str)

**DocumentReadinessSummary** (BaseModel): requirement_key (str), document_name (str), readiness (str), extraction_status (str|None), validation_outcome (str|None), blocking (bool), reason (str)

**ApprovalOrchestration** (BaseModel): approval_id (str), status (OrchestrationStatus), applicability_result (str), dependency_readiness (str), document_readiness (str), consistency_outcome (str|None), sla_state (str|None), blockers (list[BlockerDetail]), documents (list[DocumentReadinessSummary]), explanation (str), next_action (str)

**NextAction** (BaseModel): action_type (str), description (str), affected_approval_id (str|None), affected_document_key (str|None), link_section (str)

**ApplicationOrchestration** (BaseModel): application_id (str), overall_status (OrchestrationStatus), approvals (dict[str, ApprovalOrchestration]), total_blockers (int), next_action (NextAction|None), stage_number (int|None), explanation (str)

- [ ] **Step 3: Verify imports**

Run: `cd backend && python -c "from app.orchestration.models import OrchestrationStatus, ApplicationOrchestration; print('OK')"`

- [ ] **Step 4: Commit**

```bash
git add backend/app/orchestration/
git commit -m "feat(orchestration): add orchestration data models"
```
