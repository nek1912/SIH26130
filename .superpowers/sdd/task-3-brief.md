Task 3: Write Orchestration Service Tests

**Files:**
- Create: `backend/tests/test_orchestration_service.py`

**Interfaces:**
- Consumes: `orchestrate_application()` and `orchestrate_application_full()` from `app.orchestration.service`
- Consumes: seed data from `app.seed.approvals`, `app.seed.dependencies`, `app.seed.documents`

## Test Cases Required

Create `backend/tests/test_orchestration_service.py` with the following test classes and methods:

### Class: TestOrchestrationStatusComputation

1. `test_ready_when_all_clear` — Approval with applies + no deps + all docs valid = READY
   - Use A04 (GPCB CTE) with full facts (industry_type matches, etc.)
   - Pass empty document_requirements (no docs needed)
   - Assert status == OrchestrationStatus.READY

2. `test_blocked_by_dependency` — Approval blocked by unmet prerequisite = BLOCKED_BY_DEPENDENCY
   - Use A03 (GIDC Drainage) which depends on A04 and A02
   - Don't include A04 or A02 in obtained_approvals
   - Assert status == OrchestrationStatus.BLOCKED_BY_DEPENDENCY
   - Assert blockers contain dependency type

3. `test_insufficient_data_when_facts_missing` — Missing project facts = INSUFFICIENT_DATA
   - Use A01 (GIDC Plan) with empty project_facts {}
   - Assert status == OrchestrationStatus.INSUFFICIENT_DATA

4. `test_blocked_by_documents_when_missing` — Mandatory docs not uploaded = BLOCKED_BY_DOCUMENTS
   - Use A04 with full facts (so applicability = applies)
   - Pass document_requirements with D05 as mandatory, but no uploaded_documents
   - Assert status == OrchestrationStatus.BLOCKED_BY_DOCUMENTS

5. `test_review_required_when_consistency_issues` — Consistency REVIEW_REQUIRED = REVIEW_REQUIRED
   - Use A04 with full facts, no dependency blockers, all docs valid
   - Pass consistency_result with outcome="REVIEW_REQUIRED"
   - Assert status == OrchestrationStatus.REVIEW_REQUIRED

6. `test_not_applicable_when_does_not_apply` — Applicability does_not_apply = NOT_APPLICABLE
   - Use A01 with facts that make it NOT apply (wrong industry_type)
   - Assert status == OrchestrationStatus.NOT_APPLICABLE

7. `test_dependency_chain_progression` — A04→A02→A03 chain
   - A04: no deps, should be READY
   - A02: depends on A04, with A04 in obtained → should be READY
   - A03: depends on A04 and A02, with both obtained → should be READY

### Class: TestDocumentReadiness

8. `test_all_docs_valid` — When all mandatory docs uploaded and valid
   - Pass document_requirements with D05, uploaded_documents with D05 having status valid
   - Assert document_readiness == "all_valid"

9. `test_mandatory_doc_missing` — When mandatory doc not uploaded
   - Pass document_requirements with D05 (mandatory), no uploaded_documents
   - Assert blocking == True for D05

10. `test_conditional_doc_not_blocking` — Conditional doc missing is not a blocker
    - Pass document_requirements with a conditional doc, not uploaded
    - Assert blocking == False

### Class: TestNextAction

11. `test_next_action_upload_document` — First action is upload when docs missing
    - A04 with no docs uploaded
    - Assert next_action.action_type == "upload_document"

12. `test_next_action_validate_document` — After upload, validate
    - A04 with D05 uploaded but not validated
    - Assert next_action.action_type involves validation

### Class: TestApplicationOrchestration

13. `test_full_orchestration_overall_status` — Overall status is worst case
    - Multiple approvals, one BLOCKED_BY_DEPENDENCY
    - Assert overall_status == BLOCKED_BY_DEPENDENCY

14. `test_full_orchestration_total_blockers` — Counts all blockers across approvals
    - Multiple approvals with various blockers
    - Assert total_blockers matches sum

15. `test_full_orchestration_next_action` — Picks highest priority next action
    - Multiple approvals with different next actions
    - Assert next_action is the highest priority one

### Class: TestEdgeCases

16. `test_empty_inputs` — Empty everything doesn't crash
    - All parameters empty/None
    - Assert returns valid ApplicationOrchestration

17. `test_sla_breached_adds_blocker` — Breached SLA adds blocker
    - Pass sla_info with state="breached"
    - Assert SLA breached blocker present

## Test Style

Follow existing test patterns in the repo. Use plain functions (not unittest classes), pytest style. Import from `app.orchestration.service` and `app.orchestration.models`. Use `app.seed.approvals.load_approval_rules()`, `app.seed.approvals.load_approval_authorities()`, `app.seed.dependencies.load_approval_dependencies()` for seed data.

## Verification

After writing all tests:
1. Run: `cd backend && python -m pytest tests/test_orchestration_service.py -v`
2. All tests must pass
3. Run full suite: `cd backend && python -m pytest tests/ --tb=short -q`
4. No regressions

## Commit

```bash
git add backend/tests/test_orchestration_service.py
git commit -m "test(orchestration): add comprehensive orchestration service tests"
```
