# Workflow Events Repository Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix code review issues in WorkflowEventsRepository: remove redundant create method, add missing type annotation, remove unused imports, and replace hardcoded table name.

**Architecture:** Minor targeted changes to two files: the repository implementation and its test file. No new functionality added, only cleanup.

**Tech Stack:** Python, Supabase Client, pytest, unittest.mock.

## Global Constraints

- Use current stable releases and official documentation.
- Do not introduce deprecated APIs, packages, setup patterns, or framework syntax.
- Preserve existing working functionality unless the task explicitly changes it.
- Never put secrets in source control.

---

### Task 1: Fix WorkflowEventsRepository

**Files:**
- Modify: `backend/app/repositories/workflow_events.py`
- Test: `backend/tests/test_workflow_events_repo.py` (existing tests should still pass)

**Interfaces:**
- Consumes: BaseRepository class, Supabase Client type.
- Produces: Updated WorkflowEventsRepository class with typed __init__, removed create method, and self.table_name usage.

- [ ] **Step 1: Read current file and understand changes needed**

Read `backend/app/repositories/workflow_events.py` and `backend/app/repositories/base.py` to confirm BaseRepository.create method matches the one we will delete.

- [ ] **Step 2: Remove redundant create method**

Delete lines 26-29 (the create method) from `workflow_events.py`. The inherited BaseRepository.create does the same thing.

- [ ] **Step 3: Add Client type annotation to __init__**

Change line 12 from `def __init__(self, client):` to `def __init__(self, client: Client):`. Add import for Client from supabase (if not already present). The file currently imports from app.repositories.base, which imports Client. We need to import Client directly from supabase.

Add import: `from supabase import Client` after line 3.

- [ ] **Step 4: Replace hardcoded table name with self.table_name**

In `list_for_application` method, change line 18 `self.client.table("workflow_events")` to `self.client.table(self.table_name)`. Also line 24? Actually line 24 is `return result.data or []`. Wait, the hardcoded string appears only in line 18. The create method (which we deleted) also had hardcoded string. So only one occurrence.

- [ ] **Step 5: Run tests to verify changes don't break existing functionality**

Run: `cd D:\SIH\backend && python -m pytest tests/test_workflow_events_repo.py -v`
Expected: All three tests pass.

- [ ] **Step 6: Commit changes**

```bash
git add backend/app/repositories/workflow_events.py
git commit -m "fix: remove redundant create method, add Client type annotation, use self.table_name"
```

### Task 2: Clean up test imports

**Files:**
- Modify: `backend/tests/test_workflow_events_repo.py`

**Interfaces:**
- Consumes: unittest.mock.MagicMock, patch, pytest.
- Produces: Test file with only necessary imports.

- [ ] **Step 1: Remove unused imports**

Remove `patch` from line 4 (currently `from unittest.mock import MagicMock, patch`). Remove `pytest` from line 7 (currently `import pytest`). The file does not use pytest directly; it uses class-based tests without pytest fixtures.

- [ ] **Step 2: Run tests to ensure they still pass**

Run: `cd D:\SIH\backend && python -m pytest tests/test_workflow_events_repo.py -v`
Expected: All three tests pass.

- [ ] **Step 3: Commit changes**

```bash
git add backend/tests/test_workflow_events_repo.py
git commit -m "chore: remove unused imports from workflow events tests"
```

### Task 3: Verify full backend test suite

**Files:**
- No new files.

**Interfaces:**
- Consumes: Existing test suite.
- Produces: Confirmation that all backend tests pass.

- [ ] **Step 1: Run full backend test suite**

Run: `cd D:\SIH\backend && python -m pytest tests/ -v`
Expected: All tests pass (or at least no new failures introduced).

- [ ] **Step 2: Commit any incidental changes (if any)**

If any other files were modified unintentionally, revert them. If none, skip.

- [ ] **Step 3: Final report**

Provide status, commits, test results.

---

## Self-Review

1. **Spec coverage:** All four issues addressed: redundant create method removed, Client type added, unused imports removed, hardcoded table name replaced.

2. **Placeholder scan:** No placeholders found.

3. **Type consistency:** The type annotation uses `Client` from supabase, consistent with BaseRepository. The method signatures remain unchanged.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-15-workflow-events-repository-fixes.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**