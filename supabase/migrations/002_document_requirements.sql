-- supabase/migrations/002_document_requirements.sql
-- Document requirements per application (seeded from workbook Document_Register).

create type document_readiness as enum (
  'pending', 'uploaded', 'valid', 'invalid', 'review_required'
);

create table document_requirements (
  id                  uuid primary key default gen_random_uuid(),
  application_id      uuid not null references applications(id) on delete cascade,
  requirement_key     text not null,
  document_name       text not null,
  approval_id         text not null,
  domain              text not null,
  requirement_level   text not null default 'required',
  readiness           document_readiness not null default 'pending',
  accepted_mime_types jsonb,
  max_size_mb         integer,
  description         text,
  source_basis        text,
  source_url          text,
  document_role       text,
  uploaded_document_id uuid references documents(id),
  rejection_reason    text,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create unique index idx_doc_req_app_key on document_requirements(application_id, requirement_key);
create index idx_doc_req_application on document_requirements(application_id);
create index idx_doc_req_readiness on document_requirements(readiness);
