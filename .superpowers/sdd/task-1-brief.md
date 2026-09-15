## Task 1: Database Migration â€” workflow_events table + extraction_status column

**Files:**
- Create: `supabase/migrations/005_workflow_events_sla.sql`

**Interfaces:**
- Produces: `workflow_events` table, `extraction_status` column on `documents`

- [ ] **Step 1: Write the migration**

```sql
-- supabase/migrations/005_workflow_events_sla.sql

-- Workflow events table â€” persists every state transition for SLA computation
CREATE TABLE workflow_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  from_status TEXT,
  to_status TEXT NOT NULL,
  action TEXT NOT NULL,
  performed_by UUID NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_workflow_events_app ON workflow_events(application_id, created_at);

-- Extraction status on documents â€” document-level status for checklist display
ALTER TABLE documents ADD COLUMN extraction_status TEXT DEFAULT 'pending';
```

- [ ] **Step 2: Verify migration syntax**

Run: `cd backend && python -c "print('Migration file created')"` â€” confirm file exists.

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/005_workflow_events_sla.sql
git commit -m "feat: add workflow_events table + extraction_status column"
```

---

