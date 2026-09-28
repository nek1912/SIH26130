-- ─────────────────────────────────────────────────────────────
-- 011: approvals.workflow_definition (application-read column).
--
-- The application (`ApplicationsRepository.get_approval_stages`) and
-- the Phase 5 design docs read `workflow_definition` JSONB from the
-- approvals table, but no migration 001–010 creates it. Demonstrated
-- on real PostgreSQL: SELECT workflow_definition fails with
-- UndefinedColumn, which breaks GET /applications/{id}/orchestration
-- and GET /applications/{id}/sla for any row with approval_id set.
-- Additive only; NULL means "no workflow definition configured",
-- which existing code already maps to empty stages.
-- ─────────────────────────────────────────────────────────────

alter table approvals
  add column if not exists workflow_definition jsonb;
