# Approval Identity Verification Package (read-only)

Status: **OPEN — no mapping asserted.** This document stages the decision; it
asserts nothing. Every row below is `UNRESOLVED` until a human completes it
against the live database through an authorized path.

Source of workbook columns (verbatim, read-only extraction 2026-09-25):
`SIH_130_Gujarat_Chemical_Final_Verified_Dataset.xlsx`, sheet
`Approval_Register` (18 rows; headers `id`, `approval`, `stage`,
`authority`, `relevance`, `verified data / applicability note`,
`verification_status`, `official_source_url`, `last_checked`).
Only `id`, `approval`, `authority`, `verification_status` are reproduced here.

Supabase connection was unavailable from the agent environment
(DNS resolution failure on a read-only select; credentials never printed),
so all DB-side fields are blank. Complete them via Supabase Dashboard
(Table Editor on `approvals`, or SQL Editor — read-only query below) or
another authorized database-access path.

## Required database fields (exact)

```sql
select id, name, authority, active from approvals order by name;
```

For each row record exactly: `approvals.id` (UUID), `approvals.name`,
`approvals.authority`, `approvals.active`.

## Mapping table (workbook side frozen; DB side blank)

| Workbook Code | Workbook Approval (exact) | Workbook Authority (exact) | Workbook verification_status | DB UUID | DB name | DB authority | DB active | Mapping decision | Evidence / source |
|---|---|---|---|---|---|---|---|---|---|
| A01 | GIDC Plan Approval | GIDC | VERIFIED |  |  |  |  | UNRESOLVED |  |
| A02 | GIDC Water Connection | GIDC | VERIFIED |  |  |  |  | UNRESOLVED |  |
| A03 | GIDC Drainage Connection | GIDC | VERIFIED |  |  |  |  | UNRESOLVED |  |
| A04 | GPCB Consent to Establish (CTE) | GPCB via IFP/XGN | VERIFIED AS IFP PROCEDURE; GOVERNING RULE EXTRACTION PENDING |  |  |  |  | UNRESOLVED |  |
| A05 | Environmental Clearance — EIA item 5(f) candidate | MoEFCC / SEIAA / SEAC as applicable | VERIFIED FRAMEWORK; EXACT SCENARIO APPLICABILITY PENDING FACTS |  |  |  |  | UNRESOLVED |  |
| A06 | Gujarat Fire Safety Plan Approval / Fire Safety Certificate | State Fire Prevention Services / competent fire authority | VERIFIED |  |  |  |  | UNRESOLVED |  |
| A07 | Factory establishment registration / licence under OSH&WC | Labour & Employment / DISH / ShramSetu | VERIFIED PORTAL + NATIONAL BASELINE; GUJARAT DETAIL PENDING |  |  |  |  | UNRESOLVED |  |
| A08 | Building & Other Construction Workers registration | Labour & Employment | VERIFIED AS IFP SERVICE |  |  |  |  | UNRESOLVED |  |
| A09 | HT Electricity Connection | Applicable DISCOM | VERIFIED |  |  |  |  | UNRESOLVED |  |
| A10 | Electrical installation inspection/certification | CEICED / Electrical Inspector | VERIFIED FRAMEWORK; DETAILED CHECKLIST PENDING |  |  |  |  | UNRESOLVED |  |
| A11 | Hazardous & Other Waste authorization | GPCB / SPCB | VERIFIED FRAMEWORK; SCHEDULE MAPPING PENDING WASTE LIST |  |  |  |  | UNRESOLVED |  |
| A12 | MSIHC compliance | Factory / environment / district authorities as applicable | VERIFIED FRAMEWORK; CHEMICAL-SPECIFIC THRESHOLDS PENDING |  |  |  |  | UNRESOLVED |  |
| A13 | Chemical Accidents Rules compliance | Relevant state/district emergency authorities | VERIFIED FRAMEWORK; DETAILED THRESHOLDS PENDING |  |  |  |  | UNRESOLVED |  |
| A14 | Building Use (BU) Permission | Urban Development / appropriate local authority | VERIFIED AS IFP SERVICE; CURRENT GOVERNING PROCEDURE SHOULD BE REFETCHED |  |  |  |  | UNRESOLVED |  |
| A15 | Lift approval/inspection | Electrical Inspector / lift authority | CONDITIONAL; DETAILED RULE PENDING |  |  |  |  | UNRESOLVED |  |
| A16 | Boiler approval/registration | Boiler authority | PENDING PRIMARY DATA |  |  |  |  | UNRESOLVED |  |
| A17 | PESO licence/permission for petroleum storage | PESO | VERIFIED FRAMEWORK; SCENARIO SUBSTANCE DATA PENDING |  |  |  |  | UNRESOLVED |  |
| A18 | CGWA groundwater NOC | Central Ground Water Authority | VERIFIED FRAMEWORK |  |  |  |  | UNRESOLVED |  |

## Verification decision field

- `VERIFIED_EXACT` — human reviewed the DB row against this workbook row and
  the identity is exact. Record the evidence (row values + reviewer + date).
- `UNRESOLVED` — default. No determination made.
- `REJECTED` — the DB row does not correspond to this workbook row (record why;
  do not remap it elsewhere without fresh evidence).

## Explicit rule (binding)

Only an exact, human-reviewed identity match may receive `VERIFIED_EXACT`.
Do not infer identity from UUID values, row ordering, frontend position,
document requirements, approximate/similar names, or user input. A wrong
mapping silently attaches the wrong rules, dependencies, and documents to
real applications. When in doubt, leave `UNRESOLVED`.

Note: several workbook rows carry qualified statuses (framework-only,
pending facts/thresholds). Verification of the *identity* mapping is
independent of those data-completeness qualifiers, but record the row's
workbook `verification_status` alongside the decision so downstream
consumers inherit the correct confidence.

## Downstream consequence (binding)

- An approval whose `code` remains NULL stays unresolved: application
  creation cannot attach it, and `GET /applications/{id}/orchestration`
  must fail closed (explicit 422) rather than guess.
- No backfill, reseed, `GET /approvals` change, or UI wiring may proceed for
  a row until its decision reads `VERIFIED_EXACT` with evidence.

## Information required from the database owner to continue

For every row in `approvals`: `id`, `name`, `authority`, `active`
(the SQL above), plus confirmation of which rows (if any) were seeded from
a known source versus entered manually. No secrets are needed — public
schema fields only, delivered through the Dashboard or another authorized
read path.

## Project domain decision (recorded 2026-09-25; no code, schema, seed, or data changed)

"The A01–A18 records in Approval_Register constitute the canonical approval
identity catalog for this SIH application.
`backend/app/seed/approval_catalog.py` is a machine-readable transcription
of those catalog records. The catalog establishes approval identity only; it
does not establish applicability. Applicability remains determined by the
existing deterministic ApprovalRule/ConditionNode engine."

Further recorded points:

- Approval codes (A01–A18) are the stable domain identifiers; database UUIDs
  are generated persistence identifiers. No UUID→code mapping is inferred
  from existing rows.
- The live Supabase `approvals` table was verified empty (read-only select;
  zero rows), so there are no existing rows to re-identify. The canonical
  seed therefore creates the approval rows for a fresh database; the mapping
  table above stays `UNRESOLVED` because there is nothing to map.
- Workbook `verification_status` values are preserved per row exactly as
  listed (several rows carry framework-only or pending-data qualifiers).
  No regulatory verification status is upgraded here, and no claim is made
  that the approvals are universally applicable.
- Regulatory source PDFs are NOT required to establish this identity
  catalog. PDFs and source references remain a separate RAG/evidence concern
  (retrieval, citations, explanations) and are unaffected by this decision.
