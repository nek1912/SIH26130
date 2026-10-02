-- ─────────────────────────────────────────────────────────────
-- 013: portal_kind on approval_handoffs.
--
-- The handoff preparation path persists the pack portal entry kind
-- ('portal' vs 'reference') so the UI can distinguish a verified
-- portal CTA from an unverified reference link. The column was
-- written by app/handoff/service.py::prepare_initiation but never
-- migrated, so live initiation failed with UndefinedColumn while
-- mocked tests stayed green. Additive only; existing rows backfill
-- to 'portal'.
-- ─────────────────────────────────────────────────────────────

alter table approval_handoffs
  add column if not exists portal_kind text not null default 'portal';

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'approval_handoffs_portal_kind_check'
  ) then
    alter table approval_handoffs
      add constraint approval_handoffs_portal_kind_check
      check (portal_kind in ('portal', 'reference'));
  end if;
end
$$;
