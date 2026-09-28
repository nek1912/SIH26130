-- ─────────────────────────────────────────────────────────────
-- 012: applications.applicant_id (application-creation column).
--
-- The application (`POST /applications`) writes applicant_id and the
-- ownership check (`check_application_ownership`) reads it, but no
-- migration 001–011 creates the column. Demonstrated on real
-- PostgreSQL: INSERT with applicant_id fails with UndefinedColumn,
-- which breaks application creation end to end. Additive only;
-- NULL means "no owner set", which existing ownership logic already
-- denies by default for applicants. Mirrors projects.applicant_id.
-- ─────────────────────────────────────────────────────────────

alter table applications
  add column if not exists applicant_id uuid references auth.users(id);
