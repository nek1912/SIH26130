-- ─────────────────────────────────────────────────────────────
-- 010: persisted regulatory jurisdiction / pack identity.
--
-- Applications become the authoritative regulatory scope:
-- (jurisdiction, pack_version) determines the RegulatoryPack used
-- for every regulatory interpretation of that application.
-- Projects carry jurisdiction as the creation guard (CASE-A: one
-- jurisdiction per project). Facts, documents, requirements,
-- workflow events, and handoffs inherit through existing foreign
-- keys and gain NO new columns.
--
-- Canonical values (Phase 9 design):
--   jurisdiction IN ('IN-GJ', 'IN-MH')
--   pack_version IN ('gj-legacy-unversioned', 'mh-v5-batch1')
--
-- Sequence in this file: add nullable columns -> deterministic
-- backfill of legacy rows (all predate MH production, so IN-GJ) ->
-- completeness validation (fails loudly) -> NOT NULL + indexes.
-- Additive only. Rollback at schema level = drop the added columns.
-- A-codes are never rewritten; no data is reinterpreted.
-- ─────────────────────────────────────────────────────────────

alter table projects add column if not exists jurisdiction text;
alter table projects add column if not exists pack_version text;
alter table applications add column if not exists jurisdiction text;
alter table applications add column if not exists pack_version text;

-- Deterministic backfill: every existing row is a legacy GJ row.
update projects
   set jurisdiction = 'IN-GJ',
       pack_version = 'gj-legacy-unversioned'
 where jurisdiction is null or pack_version is null;

update applications
   set jurisdiction = 'IN-GJ',
       pack_version = 'gj-legacy-unversioned'
 where jurisdiction is null or pack_version is null;

-- Completeness validation: refuse to proceed with unscoped rows.
do $$
begin
  if exists (
    select 1 from projects
     where jurisdiction is null or pack_version is null
  ) then
    raise exception 'backfill incomplete: projects with NULL jurisdiction/pack_version remain';
  end if;
  if exists (
    select 1 from applications
     where jurisdiction is null or pack_version is null
  ) then
    raise exception 'backfill incomplete: applications with NULL jurisdiction/pack_version remain';
  end if;
  if exists (
    select 1 from projects
     where jurisdiction not in ('IN-GJ', 'IN-MH')
  ) then
    raise exception 'unexpected project jurisdiction value';
  end if;
  if exists (
    select 1 from applications
     where jurisdiction not in ('IN-GJ', 'IN-MH')
  ) then
    raise exception 'unexpected application jurisdiction value';
  end if;
end $$;

alter table projects alter column jurisdiction set not null;
alter table projects alter column pack_version set not null;
alter table applications alter column jurisdiction set not null;
alter table applications alter column pack_version set not null;

alter table projects
  add constraint chk_projects_jurisdiction
  check (jurisdiction in ('IN-GJ', 'IN-MH'));
alter table applications
  add constraint chk_applications_jurisdiction
  check (jurisdiction in ('IN-GJ', 'IN-MH'));

create index if not exists idx_projects_jurisdiction
  on projects(jurisdiction);
create index if not exists idx_applications_jurisdiction
  on applications(jurisdiction);
