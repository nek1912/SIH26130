-- ─────────────────────────────────────────────────────────────
-- 008: canonical workbook code on approvals.
--
-- Stores the frozen workbook approval code (A01–A18) alongside each
-- approvals row so seed-model identity (applicability rules, dependencies,
-- document requirements) can be resolved without inventing UUID mappings.
-- Nullable: pre-existing manually entered rows carry no verified code and
-- must be human-mapped before they receive one (see
-- docs/approval-identity-verification.md). Uniqueness enforced only where
-- a code is present, so unresolved rows coexist safely.
-- ─────────────────────────────────────────────────────────────

alter table approvals add column if not exists code text;

create unique index if not exists idx_approvals_code_unique
  on approvals(code) where code is not null;
