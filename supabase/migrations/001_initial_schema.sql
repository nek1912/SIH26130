-- ═══════════════════════════════════════════════════════════════
-- SIH 26130 — Initial schema
-- Merges patterns from Digital-Permit-Platform (configuration-driven
-- modules, JSONB configs, audit trail) and Compliance-Grid
-- (obligations, instruments, applicability conditions, sources).
-- ═══════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────
-- PROJECTS
-- ─────────────────────────────────────────────────────────────

create table projects (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  description   text,
  applicant_id  uuid not null references auth.users(id),
  status        text not null default 'active'
                check (status in ('active', 'archived')),
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index idx_projects_applicant on projects(applicant_id);
create index idx_projects_status on projects(status);

-- ─────────────────────────────────────────────────────────────
-- PROJECT FACTS — structured facts about the project
-- used for applicability evaluation
-- ─────────────────────────────────────────────────────────────

create table project_facts (
  id            uuid primary key default gen_random_uuid(),
  project_id    uuid not null references projects(id) on delete cascade,
  entity_type   text not null
                check (entity_type in (
                  'proprietorship','partnership','llp','pvt-ltd',
                  'public-ltd','opc','huf','trust','society'
                )),
  sector        text not null,
  jurisdictions text[] not null default '{}',
  headcount     integer not null default 0 check (headcount >= 0),
  annual_turnover_inr numeric not null default 0 check (annual_turnover_inr >= 0),
  incorporation_date date,
  registered_state text,
  facts_json    jsonb not null default '{}',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),

  unique (project_id)
);

create index idx_project_facts_project on project_facts(project_id);

-- ─────────────────────────────────────────────────────────────
-- INSTRUMENTS — legal source documents (Acts, Rules,
-- Notifications) from which obligations are derived.
-- From Compliance Grid.
-- ─────────────────────────────────────────────────────────────

create table instruments (
  id            text primary key,
  type          text not null check (type in ('Act', 'Rule', 'Notification')),
  title         text not null,
  jurisdiction  text not null check (jurisdiction ~ '^IN(-[A-Z]{2})?$'),
  citation      text not null,
  created_at    timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────
-- SOURCES — external web/document sources from which
-- regulatory content is fetched. From Compliance Grid.
-- ─────────────────────────────────────────────────────────────

create table sources (
  id            text primary key,
  jurisdiction  text not null check (jurisdiction ~ '^IN(-[A-Z]{2})?$'),
  domain        text not null,
  url           text not null,
  fetch_recipe  jsonb not null default '{}',
  trust_tier    text not null
                check (trust_tier in ('gazette','govt-portal','secondary','unverified')),
  last_seen     timestamptz not null default now(),
  content_hash  text not null,
  created_at    timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────
-- OBLIGATIONS — the core regulatory rule nodes.
-- From Compliance Grid. Anti-hallucination invariant:
-- source_refs must be non-empty.
-- ─────────────────────────────────────────────────────────────

create table obligations (
  id                    uuid primary key default gen_random_uuid(),
  canonical_id          text not null unique,
  instrument_id         text not null references instruments(id),
  section               text,
  type                  text not null
                        check (type in (
                          'filing','registration','record-keeping','display',
                          'notification','payment','inspection-readiness'
                        )),
  summary               text not null,
  applicability_conditions jsonb not null default '[]',
  frequency             text not null
                        check (frequency in (
                          'one-time','monthly','quarterly','half-yearly',
                          'annual','event-driven'
                        )),
  deadline_rule         jsonb not null,
  proof_types           text[] not null default '{}',
  penalty               jsonb not null default '{}',
  source_refs           jsonb not null default '[]',
  version               text not null default '1',
  confidence            numeric not null default 1.0
                        check (confidence >= 0 and confidence <= 1),
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index idx_obligations_instrument on obligations(instrument_id);
create index idx_obligations_canonical on obligations(canonical_id);
create index idx_obligations_type on obligations(type);

-- ─────────────────────────────────────────────────────────────
-- ENTITY PROFILES — per-organisation entity facts used for
-- applicability matching. From Compliance Grid.
-- ─────────────────────────────────────────────────────────────

create table entity_profiles (
  id                    uuid primary key default gen_random_uuid(),
  org_id                uuid not null,
  entity_type           text not null
                        check (entity_type in (
                          'proprietorship','partnership','llp','pvt-ltd',
                          'public-ltd','opc','huf','trust','society'
                        )),
  sector                text not null,
  jurisdictions         text[] not null default '{}',
  headcount             integer not null default 0 check (headcount >= 0),
  annual_turnover_inr   numeric not null default 0 check (annual_turnover_inr >= 0),
  incorporation_date    date,
  registered_state      text,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index idx_entity_profiles_org on entity_profiles(org_id);

-- ─────────────────────────────────────────────────────────────
-- APPROVALS — the approval catalogue. Each row is a type
-- of clearance/permit that may apply to a project.
-- ─────────────────────────────────────────────────────────────

create table approvals (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  authority     text not null,
  description   text,
  category      text not null default 'general',
  active        boolean not null default true,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────
-- APPROVAL RULES — rules that determine whether an approval
-- applies to a project. Links an approval to applicability
-- conditions and source references.
-- ─────────────────────────────────────────────────────────────

create table approval_rules (
  id                    uuid primary key default gen_random_uuid(),
  approval_id           uuid not null references approvals(id) on delete cascade,
  obligation_id         uuid references obligations(id),
  applicability_conditions jsonb not null default '[]',
  source_refs           jsonb not null default '[]',
  version               text not null default '1',
  active                boolean not null default true,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index idx_approval_rules_approval on approval_rules(approval_id);
create index idx_approval_rules_obligation on approval_rules(obligation_id);

-- ─────────────────────────────────────────────────────────────
-- APPLICATIONS — a specific applicant's request for an
-- approval. Adapted from Digital-Permit-Platform.
-- ─────────────────────────────────────────────────────────────

create type application_status as enum (
  'draft', 'submitted', 'under_review', 'awaiting_inspection',
  'awaiting_consultation', 'awaiting_hearing',
  'awaiting_documents', 'awaiting_payment',
  'approved', 'refused', 'withdrawn',
  'incomplete', 'returned', 'cancelled'
);

create table applications (
  id                    uuid primary key default gen_random_uuid(),
  reference_number      text unique not null,
  project_id            uuid not null references projects(id),
  approval_id           uuid not null references approvals(id),
  status                application_status not null default 'draft',
  current_stage         text,
  answers               jsonb not null default '{}',
  submitted_at          timestamptz,
  decided_at            timestamptz,
  decision_outcome      text,
  decision_reason       text,
  assigned_officer_id   uuid,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index idx_applications_project on applications(project_id);
create index idx_applications_approval on applications(approval_id);
create index idx_applications_status on applications(status);
create index idx_applications_ref on applications(reference_number);

-- ─────────────────────────────────────────────────────────────
-- DOCUMENTS — uploaded documents linked to applications.
-- From Digital-Permit-Platform.
-- ─────────────────────────────────────────────────────────────

create type document_status as enum (
  'pending_upload', 'uploaded', 'verified', 'rejected',
  'virus_detected', 'expired'
);

create table documents (
  id                  uuid primary key default gen_random_uuid(),
  application_id      uuid not null references applications(id) on delete cascade,
  requirement_key     text not null,
  original_filename   text not null,
  storage_path        text not null default 'db',
  mime_type           text not null,
  file_size_bytes     integer not null,
  status              document_status not null default 'uploaded',
  rejection_reason    text,
  uploaded_by_user_id uuid,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create index idx_documents_application on documents(application_id);

-- ─────────────────────────────────────────────────────────────
-- WORKFLOW EVENTS — immutable transition log.
-- From Digital-Permit-Platform.
-- ─────────────────────────────────────────────────────────────

create table workflow_events (
  id                uuid primary key default gen_random_uuid(),
  application_id    uuid not null references applications(id) on delete cascade,
  from_stage        text,
  to_stage          text not null,
  action            text not null,
  performed_by_id   uuid,
  metadata          jsonb,
  created_at        timestamptz not null default now()
);

create index idx_workflow_events_application on workflow_events(application_id);

-- ─────────────────────────────────────────────────────────────
-- AUDIT LOG — immutable append-only trail.
-- From Digital-Permit-Platform.
-- ─────────────────────────────────────────────────────────────

create table audit_log (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid,
  application_id    uuid,
  action            text not null,
  entity_type       text not null,
  entity_id         text not null,
  previous_values   jsonb,
  new_values        jsonb,
  ip_address        text,
  user_agent        text,
  created_at        timestamptz not null default now()
);

create index idx_audit_log_application on audit_log(application_id);
create index idx_audit_log_user on audit_log(user_id);
create index idx_audit_log_entity on audit_log(entity_type, entity_id);
create index idx_audit_log_created on audit_log(created_at);
