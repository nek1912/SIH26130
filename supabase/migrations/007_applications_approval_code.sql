-- ─────────────────────────────────────────────────────────────
-- 007: persist the workbook approval code (e.g. A01) on applications.
--
-- The orchestration endpoint and the sibling obtained-approvals lookup
-- resolve seed-model identity (applicability rules, dependencies, document
-- requirements) through approval_code. The code cannot be derived from
-- approval_id: the approvals table carries no canonical code column and
-- approval UUIDs are environment-random with no mapping to workbook codes.
--
-- Nullable: rows created before this migration carry no code and will hit
-- the endpoint's explicit 422 until re-associated. New rows store the code
-- at creation (POST /applications already requires it as a query param).
-- ─────────────────────────────────────────────────────────────

alter table applications add column if not exists approval_code text;
