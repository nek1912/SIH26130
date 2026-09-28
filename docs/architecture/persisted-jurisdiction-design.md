# Persisted Jurisdiction / Pack-Version Design (Phase 9 — DESIGN ONLY)

Status: **approved and implemented in Phase 10** (migration
`010_persisted_jurisdiction.sql` written, unapplied pending staging;
read paths resolve per-row identity; `DEFAULT_JURISDICTION` still
`IN-GJ`). The design below is unchanged; implementation notes are in
`ARCHITECTURE.md` §42.

## 1. Current-state problem

The decision path resolves regulatory data from the process-global
`DEFAULT_JURISDICTION` (`IN-GJ`) via `load_regulatory_pack()` /
`get_active_jurisdiction()`. Persisted rows carry no regulatory
identity (verified against migrations 001–009):

- `projects`: id, name, description, applicant_id, status. No jurisdiction.
- `applications`: id, reference_number (unique), project_id → projects,
  approval_id → approvals, approval_code text (bare `A04`/`APR-006`,
  nullable, migration 007), status enum, stages/decisions. No
  jurisdiction, no pack version.
- `project_facts`: unique(project_id); typed columns +
  `facts_json`. `jurisdictions text[]` is applicant-supplied entity
  data, unread by the decision path — it is NOT a scope marker.
- `documents`, `document_requirements`, `workflow_events`,
  `approval_handoffs`: FK → applications(id) (cascade), no jurisdiction.
- `instruments`/`sources` carry metadata `jurisdiction` columns only.
- No table has any version/pack column for decisions made.

Consequence: flipping the global default would reinterpret every
historical GJ row against the MH pack — orchestration 422s on `A04`,
D0X keys orphan against DOC-xxx requirements, GJ handoff lookups
void, GJ-coded creates seed zero requirements silently. N-2
(A01–A18 ↔ APR/CMP) is additionally unresolved with zero verified
mappings, so no code translation can repair old rows either.

## 2. Proposed invariant

> **A persisted application's (`jurisdiction`, `pack_version`) pair —
> never the global default — determines the RegulatoryPack used for
> every regulatory interpretation of that application.**

Canonical values (existing codebase conventions, not new inventions):

- `jurisdiction`: `"IN-GJ"` | `"IN-MH"` (matches the `Jurisdiction`
  pattern and `seed.pack` constants).
- `pack_version`: `"gj-legacy-unversioned"` (the GJ seed corpus has no
  version constant anywhere in the repo — this name states that fact
  instead of inventing history) | `"mh-v5-batch1"` (matches encoded
  `ApprovalRule.version == "v5"` and the batch-1 scope).

## 3. Entity ownership of jurisdiction

`applications` is the authoritative regulatory scope:

```text
Project (creation-time guard scope)
  └── Application (authoritative scope)
       ├── jurisdiction        (NOT NULL after backfill)
       ├── pack_version        (NOT NULL after backfill)
       └── approval_code       (unchanged, validated per §10)
```

`projects` carries `jurisdiction` (creation guard, §5).
`project_facts` carries NO jurisdiction column (inherits project
scope; validated per evaluation, §4). `documents`,
`document_requirements`, `workflow_events`, `approval_handoffs`
carry NO jurisdiction columns (inherit via `application_id` FK, §12).

## 4. Pack-version semantics

- `jurisdiction` answers "which legal/regulatory jurisdiction?"
- `pack_version` answers "which encoded dataset/interpretation?"
- Resolution table (code constants at implementation time):

```text
(IN-GJ, gj-legacy-unversioned) → GJ seed pack
(IN-MH, mh-v5-batch1)          → MH v5 batch-1 pack
anything else                  → reject (422, fail closed)
```

`pack_version` is what makes historical reproducibility possible
when a jurisdiction later gains a second pack (e.g. `mh-v5-batch2`):
old rows keep resolving to the pack they were decided under.

## 5. Record-resolution algorithm

```text
resolve_regulatory_pack_for_application(application):
  1. read application.jurisdiction, application.pack_version
  2. if either is NULL (pre-migration row) → reject with explicit
     "unscoped record" error (never fall back to the default)
  3. look up (jurisdiction, pack_version) in the release table
  4. unknown combination → reject (422, fail closed)
  5. return load_regulatory_pack(jurisdiction) pinned to pack_version
```

Call sites (implementation phase): `_load_baseline_inputs`
(replaces the jurisdiction parameter source), What-If (via baseline),
rehearsal (via baseline + pack registries), handoff readiness +
portal resolution (via baseline pack), document seeding at creation
(from the project scope, §9). `get_active_jurisdiction()` remains
solely the NEW-record default (§9), never the read path.

## 6. Legacy backfill strategy

Every existing row predates MH production, so the backfill is
deterministic and total:

- `projects` without jurisdiction → `IN-GJ`.
- `applications` without jurisdiction/pack_version →
  (`IN-GJ`, `gj-legacy-unversioned`).
- `project_facts`, `documents`, `document_requirements`,
  `workflow_events`, `approval_handoffs`: NO columns (FK inheritance).
- Completeness gate: zero applications with NULL jurisdiction and
  zero with unknown (jurisdiction, pack_version) pairs before the
  columns become NOT NULL and before any default flip.
- A-codes are NEVER rewritten to APR/CMP (constraint §18).

## 7. New-record creation strategy

- `POST /projects`: server sets `jurisdiction = DEFAULT_JURISDICTION`
  at creation. The client NEVER supplies it.
- `POST /applications`: inherits the parent project's jurisdiction;
  mismatch → 422. `pack_version` is derived server-side from the
  release table for that jurisdiction.
- Core invariant: flipping `DEFAULT_JURISDICTION` IN-GJ → IN-MH
  changes only NEW projects/applications. Every existing row keeps
  resolving per §§2–5.

## 8. GJ-after-cutover behavior

Existing GJ application (`IN-GJ`, `gj-legacy-unversioned`) after the
flip: orchestration, What-If, rehearsal, handoff, and document reads
resolve the GJ pack exactly as today. No 422, no silent migration,
no reinterpretation.

## 9. MH-after-cutover behavior

New project/application after the flip: (`IN-MH`, `mh-v5-batch1`);
MH pack, MH fact vocabulary, MH portals, MH evidence. Pre-flip
explicit-MH records (test/demo scope) keep working unchanged.

## 10. GJ-coded-create behavior

Validation invariant (implementation phase):

```text
approval_code ∈ pack(jurisdiction).approval_ids  else  422
```

`IN-MH` + `A04` → 422 invalid-approval-code-for-jurisdiction.
`IN-GJ` + `APR-006` → 422. No silent reinterpretation, no N-2
guessing. (Today creation validates nothing and orchestration 422s
later; the design moves validation to creation without changing the
error philosophy.)

## 11. What-If behavior

What-If resolves the application's persisted pair (§5) and validates
overrides against that jurisdiction's registry (already implemented
for explicit contexts in Phase 2; the persisted pair becomes the
source of the context). GJ application + MH global default → GJ
What-If. No cross-pack comparison except as an explicit future
capability.

## 12. Document behavior

Requirements seeded at creation from the creation-time pack stay
with the application row (they already do). Reads resolve the
application's pack. GJ documents keep GJ keys; MH documents keep
DOC-xxx keys. No key translation layer.

## 13. Handoff behavior

Portal resolution reads the application's pack catalog
(`pack.get_portal_entry`), never the global default. Existing GJ
handoffs → GJ catalog; new MH handoffs → MH catalog. The manual,
no-integration character of handoff is unchanged.

## 14. Migration sequence (future reviewed phase; NOT this phase)

1. Additive columns: `projects.jurisdiction`; `applications.jurisdiction`,
   `applications.pack_version` (all NULLABLE initially).
2. Backfill legacy rows per §6 (single transaction, auditable counts).
3. Validate: zero NULLs, zero unknown pairs, GJ spot-checks resolve.
4. Enforce NOT NULL + indexes on (`jurisdiction`) / pair checks.
5. Rewire read paths to §5 (behind tests TEST-01…17).
6. Re-verify GJ suite + MH suites green.
7. Only then is a default flip even discussable.

## 15. Constraints

All existing UUIDs, reference numbers, A-codes, document keys,
workflow event IDs, and handoff IDs are preserved bit-for-bit. No
destructive migration. No GJ data deleted or converted. GJ becomes a
quarantined historical/runtime pack selected per-row, never by default.

## 16. Security/authorization implications

No RBAC/ownership changes: applicants still see own records, staff
still see team/all (existing `check_*_ownership` untouched). No RLS
(the repo intentionally uses backend-only DB access). Jurisdiction
is never client-writable: creation derives it server-side from the
default/project scope; no endpoint accepts a jurisdiction field;
staff get no override endpoint. Validation failures are 422s through
existing error shapes.

## 17. API impact (implementation phase; no change in this phase)

- `POST /projects`: response gains `jurisdiction` (server-set).
- `POST /projects/{id}/facts`: facts validated against the project's
  pack vocabulary on write (currently unvalidated) — new 422s only
  for cross-vocabulary writes.
- `POST /applications`: gains creation-time approval_code-vs-pack
  validation (422); response gains `jurisdiction`, `pack_version`.
- `GET .../orchestration`, `POST .../what-if`,
  `POST /regulatory/changes/rehearse`, handoff routes, document
  seeding: no contract change; pack source switches from global
  default to persisted pair (observable only via content, and only
  for rows whose persisted pair differs from the old default path).

## 18. Frontend impact (no implementation in this phase)

- No user-controlled jurisdiction selector unless product orders one.
- MH fact form must be generated from the 128-field registry (§13
  verified sufficient: key/type/enum/unit/unknown/group/description).
- Approval IDs, What-If fields, and portal catalogs are
  jurisdiction-specific per application; empty dimensions
  (consistency, incentives) need explicit "not in current scope"
  wording, never silent emptiness.
- Pre-existing must-fix: `OrchestrationPanel` UPPERCASE vs backend
  lowercase status enums (display-only today); GJ-only WhatIfPanel
  field list; dead `ApplicabilityResult` type vs `applies`/… wire
  values.

## 19. Rollback strategy

Because jurisdiction is per-row authoritative, rollback is a default
flip-back with zero data rewrite: GJ rows keep resolving GJ, MH rows
keep resolving MH, and only NEW records follow the restored default.
No backfill to undo (backfill wrote true historical values). The
migration itself rolls back by dropping the added columns only if no
MH-production rows depend on them yet; otherwise it stays as the
multi-pack foundation.

## 20. Open decisions requiring stakeholder approval

1. N-2 mapping (unchanged: zero verified matches; architecture works
   with or without it — §22 of the phase brief).
2. Demo scenario + portal/reference label wording + held-incentives
   display (carried from Phase 8).
3. Legacy-record interpretation policy (quarantined-history confirmed
   as the intended posture).
4. Exact `pack_version` strings (`gj-legacy-unversioned`,
   `mh-v5-batch1` proposed).
5. Project-level `jurisdiction` column acceptability (vs
   application-only + first-application-wins alternative, rejected
   here for allowing mixed-vocabulary facts to accumulate silently).
6. Backfill execution window + verifier.
