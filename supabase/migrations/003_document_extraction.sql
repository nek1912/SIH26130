-- supabase/migrations/003_document_extraction.sql
-- Document extraction and deterministic validation tables.

-- Extraction status enum
create type extraction_status as enum (
  'pending', 'completed', 'failed', 'unsupported'
);

-- Validation outcome enum
create type validation_outcome as enum (
  'VALID', 'INVALID', 'REVIEW_REQUIRED', 'INSUFFICIENT_DATA'
);

-- Extracted fields from documents
create table extracted_fields (
  id                  uuid primary key default gen_random_uuid(),
  document_id         uuid not null references documents(id) on delete cascade,
  application_id      uuid not null references applications(id) on delete cascade,
  field_name          text not null,
  field_value         jsonb,
  field_type          text not null default 'string',
  extraction_method   text not null default '',
  confidence          numeric not null default 1.0
                      check (confidence >= 0 and confidence <= 1),
  extracted_at        timestamptz not null default now(),
  metadata            jsonb not null default '{}',
  created_at          timestamptz not null default now()
);

create index idx_extracted_fields_document on extracted_fields(document_id);
create index idx_extracted_fields_application on extracted_fields(application_id);
create unique index idx_extracted_fields_doc_name on extracted_fields(document_id, field_name);

-- Extraction results summary
create table extraction_results (
  id                  uuid primary key default gen_random_uuid(),
  document_id         uuid not null references documents(id) on delete cascade,
  application_id      uuid not null references applications(id) on delete cascade,
  status              extraction_status not null default 'pending',
  errors              jsonb not null default '[]',
  metadata            jsonb not null default '{}',
  extracted_at        timestamptz not null default now(),
  created_at          timestamptz not null default now()
);

create index idx_extraction_results_document on extraction_results(document_id);
create index idx_extraction_results_application on extraction_results(application_id);
create unique index idx_extraction_results_doc on extraction_results(document_id);

-- Validation findings
create table validation_findings (
  id                  uuid primary key default gen_random_uuid(),
  document_id         uuid not null references documents(id) on delete cascade,
  application_id      uuid not null references applications(id) on delete cascade,
  field_name          text not null,
  rule_id             text not null,
  rule_description    text not null,
  outcome             validation_outcome not null,
  expected            jsonb,
  actual              jsonb,
  message             text not null default '',
  source_ref          text not null default '',
  created_at          timestamptz not null default now()
);

create index idx_validation_findings_document on validation_findings(document_id);
create index idx_validation_findings_application on validation_findings(application_id);
create index idx_validation_findings_outcome on validation_findings(outcome);

-- Validation results summary
create table validation_results (
  id                  uuid primary key default gen_random_uuid(),
  document_id         uuid not null references documents(id) on delete cascade,
  application_id      uuid not null references applications(id) on delete cascade,
  requirement_key     text not null,
  outcome             validation_outcome not null,
  rule_version        text not null default '1',
  source_refs         jsonb not null default '[]',
  validated_at        timestamptz not null default now(),
  created_at          timestamptz not null default now()
);

create index idx_validation_results_document on validation_results(document_id);
create index idx_validation_results_application on validation_results(application_id);
create index idx_validation_results_outcome on validation_results(outcome);
create unique index idx_validation_results_doc on validation_results(document_id);

-- Add extraction/validation status to document_requirements
alter table document_requirements
  add column extraction_status extraction_status default null,
  add column validation_outcome validation_outcome default null;
