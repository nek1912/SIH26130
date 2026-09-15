-- supabase/migrations/004_consistency.sql
-- Cross-document consistency engine tables

create type consistency_outcome as enum ('VALID', 'REVIEW_REQUIRED', 'INSUFFICIENT_DATA');

create table consistency_results (
  id                  uuid primary key default gen_random_uuid(),
  application_id      uuid not null references applications(id) on delete cascade,
  outcome             consistency_outcome not null,
  checked_at          timestamptz not null default now(),
  rule_version        text not null default '1',
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create table consistency_findings (
  id                  uuid primary key default gen_random_uuid(),
  result_id           uuid not null references consistency_results(id) on delete cascade,
  application_id      uuid not null references applications(id) on delete cascade,
  rule_id             text not null,
  canonical_field     text not null,
  outcome             consistency_outcome not null,
  observed_values     jsonb not null default '{}',
  expected_relationship text not null,
  message             text not null default '',
  source_ref          text not null default '',
  created_at          timestamptz not null default now()
);

create index idx_consistency_results_app on consistency_results(application_id);
create index idx_consistency_findings_app on consistency_findings(application_id);
create index idx_consistency_findings_result on consistency_findings(result_id);
