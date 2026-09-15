# Task 1 Report: Database Migration — workflow_events + extraction_status

## Status: BLOCKED — Critical Schema Conflicts

The SQL in the task brief cannot be applied as-is. Two conflicts with the existing migration chain will cause failures.

---

## Conflict 1: `workflow_events` table already exists

The table is created in `001_initial_schema.sql` (lines 254–265):

```sql
create table workflow_events (
  id                uuid primary key default gen_random_uuid(),
  application_id    uuid not null references applications(id) on delete cascade,
  from_stage        text,
  to_stage          text not null,
  action            text not null,
  performed_by_id   uuid,
  metadata          jsonb,
  created_at        timestamptz not null default now()
);
```

The task brief's `CREATE TABLE workflow_events` will fail with "relation already exists."

**Column name mismatch:**
| Brief wants | 001 has | Python code uses |
|---|---|---|
| `from_status` | `from_stage` | `from_stage` (engine.py:176) |
| `to_status` | `to_stage` | `to_stage` (engine.py:177) |
| `performed_by` (NOT NULL UUID) | `performed_by_id` (nullable UUID) | `performed_by` (engine.py:179) |

The Python `WorkflowEvent` dataclass and SLA code are aligned with the 001 schema (`from_stage`/`to_stage`), not the brief.

---

## Conflict 2: `extraction_status` on `documents` — type mismatch

The brief adds `extraction_status TEXT DEFAULT 'pending'` to `documents`.

However, migration 003 already creates an `extraction_status` enum type:
```sql
create type extraction_status as enum ('pending', 'completed', 'failed', 'unsupported');
```

This enum is used on `document_requirements.extraction_status` and `extraction_results.status`, but NOT on the `documents` table itself.

Adding a raw `TEXT` column named `extraction_status` to `documents` creates a naming collision risk and inconsistent typing with the existing enum.

---

## Recommendation

The plan needs to be revised before this migration can be created. Options:

1. **If workflow_events is already correct** in 001: Skip the CREATE TABLE entirely. The existing table matches the Python code. Only add the index if needed.

2. **If the column rename is desired** (`from_stage` → `from_status`): This requires updating the Python `WorkflowEvent` dataclass, SLA code, and engine code to match. That's a larger scope change.

3. **For extraction_status on documents**: Use the existing `extraction_status` enum type (not `TEXT`) for consistency, or clarify why a TEXT column is preferred.

---

## Files involved
- `supabase/migrations/001_initial_schema.sql` — existing workflow_events table (lines 254–265)
- `supabase/migrations/003_document_extraction.sql` — extraction_status enum (line 5)
- `backend/app/workflow/engine.py` — WorkflowEvent dataclass (line 170–181)
- `backend/app/workflow/sla.py` — SLA computation reads `toStage` from events (line 139)
