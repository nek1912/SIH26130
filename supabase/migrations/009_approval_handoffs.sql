-- ─────────────────────────────────────────────────────────────
-- 009: manual government handoff tracking.
--
-- UdyamDwaar is NOT a government portal. This table records the
-- applicant's MANUAL progress on external authority systems
-- (IFP/GIDC/GPCB/PESO/PARIVESH/CGWA/...). No row here implies any
-- machine submission to, or response from, a government system:
-- every status is either applicant-reported or staff-verified.
--
-- applications.status stays the UdyamDwaar-internal workflow and is
-- never derived from, nor written by, handoff state.
-- ─────────────────────────────────────────────────────────────

create table if not exists approval_handoffs (
  id                    uuid primary key default gen_random_uuid(),
  application_id        uuid not null references applications(id) on delete cascade,
  approval_code         text not null,
  authority             text not null,
  external_system       text not null,
  portal_url            text not null,
  status                text not null
                        check (status in (
                          'handed_off',
                          'submitted_externally',
                          'under_external_review',
                          'approved_external',
                          'rejected_external',
                          'returned_for_correction'
                        )),
  external_reference    text,
  submitted_at          timestamptz,
  last_external_update_at timestamptz,
  applicant_note        text,
  reported_by           uuid,
  verification          text not null default 'user_reported'
                        check (verification in ('user_reported', 'staff_verified')),
  verified_by           uuid,
  verified_at           timestamptz,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index if not exists idx_handoffs_application
  on approval_handoffs(application_id);

create index if not exists idx_handoffs_approval
  on approval_handoffs(application_id, approval_code);

-- One active handoff per (application, approval). Terminal states
-- (approved_external, rejected_external) are history and may be
-- superseded by a fresh handoff.
create unique index if not exists idx_handoffs_single_active
  on approval_handoffs(application_id, approval_code)
  where status in (
    'handed_off',
    'submitted_externally',
    'under_external_review',
    'returned_for_correction'
  );
