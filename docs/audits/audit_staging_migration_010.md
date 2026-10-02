# Audit — Staging Migration 010 (T6)

Date: 2026-10-02. Verdict: **BLOCKED — STAGING ENVIRONMENT NOT AVAILABLE/VERIFIABLE.**
Migration 010 was statically validated end-to-end but NOT executed: no staging
database identity exists anywhere in the repository, and substituting local
PostgreSQL is explicitly forbidden. No regulatory rules, no frontend, and no
migration history were modified by this task.

## 1. Repository commit

- HEAD: `74023c4` (`feat(mh): finalize regulatory implementation baseline`), branch `main`.
- Working tree at audit time is DIRTY with concurrent unrelated WIP (T3/T4 owners):
  modified `backend/app/api/applications.py`, `backend/app/api/projects.py`,
  `backend/app/seed/mh/approvals.py` (T4: R-087→EXEMPTION + APR-023 composition),
  `backend/tests/test_mh_exception_role_contract.py`,
  `backend/tests/test_mh_exception_semantics.py`,
  `backend/tests/test_mh_r044_exemption.py`;
  untracked `backend/tests/test_api_mh_demo_contract.py` (T3),
  `backend/tests/test_mh_r087_semantics.py` (T4).
- T6 touched none of these files. No commit was made (per task instruction).

## 2. Migration 010 purpose — PASS (statically verified)

File: `supabase/migrations/010_persisted_jurisdiction.sql` (83 lines).
Persisted regulatory identity: adds nullable `jurisdiction` + `pack_version`
to `projects` and `applications`, deterministically backfills every existing
row to `('IN-GJ', 'gj-legacy-unversioned')`, runs a validating DO block that
raises on any NULL or out-of-domain value, then enforces NOT NULL, value
CHECKs (`IN-GJ`/`IN-MH`), and per-table jurisdiction indexes.
Additive only; A-codes untouched; facts/documents/events/handoffs inherit via
existing FKs with no new columns. Data-changing ONLY in the scoped sense
(backfill of the 4 new columns); no reinterpretation, no deletes.

## 3. Migration dependency/order verification — PASS

- `supabase/migrations/` contains exactly `001`–`012`, contiguous, no duplicate
  numbers, no gaps: 001 initial schema → 002 document requirements →
  003 document extraction → 004 consistency → 005 RAG sources →
  006 extraction status → 007 applications.approval_code →
  008 approvals.code → 009 approval_handoffs → 010 persisted jurisdiction →
  011 approvals.workflow_definition → 012 applications.applicant_id.
- 010 depends only on `projects`/`applications` (created in 001). 011/012 are
  later independent additive columns. No file renamed or reordered.

## 4. Target environment verification — BLOCKED

No staging database identity exists in the repository:

- `backend/app/core/config.py` default: local `gaia_dev` PostgreSQL only.
- `backend/.env.example`: local `gaia_dev` placeholder only.
- `docs/local-postgres.md`: local setup only; canonical procedure is
  `psql` lexical order with `ON_ERROR_STOP`.
- Repo-wide search for staging identifiers/connection strings: no staging
  host, name, config file, or CI/CD staging target (ARCHITECTURE.md §§40/44
  confirm "no linked hosted staging project available (NOT VERIFIED)").
- Per task §5: **STAGING DATABASE NOT VERIFIED**. Local `gaia_dev` was used
  strictly as a read-only reference and never as a staging substitute.

## 5. Pre-migration migration state

- Staging: UNKNOWN (no target; nothing executed, nothing partially applied).
- Local reference (`gaia_dev`, PostgreSQL 18.3, 21 public tables): all four
  010 identity columns present and NOT NULL, both CHECKs
  (`chk_projects_jurisdiction`, `chk_applications_jurisdiction`) present,
  both indexes present. No migration-state table exists anywhere
  (`schema_migrations`/`alembic_version` absent) — migration state is
  established by schema inspection, matching `scripts/verify_local_db.py`.

## 6. Safety checks — PASS

- Destructive-pattern scan over all 12 migration files
  (`DROP DATABASE|DROP SCHEMA|TRUNCATE|DELETE FROM|DROP TABLE|DROP COLUMN`):
  zero matches.
- 010 itself contains no destructive SQL: `ADD COLUMN IF NOT EXISTS`,
  scoped `UPDATE` backfill of the new columns only, validating DO block
  (raises, never deletes), `SET NOT NULL`, CHECKs, `CREATE INDEX IF NOT
  EXISTS`. No `DROP DATABASE` / `TRUNCATE` / reset was executed by T6.

## 7. Backup/rollback status — NOT_APPLICABLE (no execution) / documented

- The repo provides no backup mechanism and no down migration (forward-only
  by design). The 010 header documents schema-level rollback as dropping
  the added columns. Recorded here so the future staging run can plan
  backup through the deployment environment's own supported mechanism.

## 8. Dry-run/validation — PASS (static; no runner exists)

- No dry-run tooling exists (no migration framework; canonical procedure is
  manual `psql`). Static validation instead: 010 references only
  `projects`/`applications` plus its own new columns; ADD CONSTRAINT has no
  `IF NOT EXISTS`, so re-application would fail loudly rather than
  silently double-apply — repeatability is therefore proven via
  migration-state inspection, never via re-execution.
- Prior live-fire evidence (not re-run by T6): ARCHITECTURE.md §43 records
  001–010 applied cleanly in order on a disposable PostgreSQL 18.3 database
  (dropped afterwards), and the same objects are present on local `gaia_dev`.

## 9. Migration execution result — BLOCKED

010 was NOT applied: `BLOCKED — STAGING ENVIRONMENT NOT AVAILABLE/VERIFIABLE`.
No staging start/end, no version change, nothing partially applied.

## 10. Post-migration schema verification — NOT_APPLICABLE (staging)

No staging schema to compare. Local reference state (see §5) matches 010's
expected objects exactly; this is recorded as a reference only, not as
staging proof.

## 11. Data verification — NO DATA TRANSFORMATION (staging)

Nothing executed, so no staging row counts exist to compare. Reference only:
local catalog holds A01–A18 exactly once (`verify_local_db.py` check 5).

## 12. Application compatibility — PASS (local reference)

`python scripts/verify_local_db.py` (read-only mode, local `gaia_dev` only):
**8/8 checks passed** — connectivity; 16/16 tables; identity columns NOT
NULL; both CHECKs; catalog A01–A18 exactly once; Dahej mapping; FTS+GIN;
12 GJ evidence gaps code-seeded. (The FTS check inserts/deletes a self-
cleaning `VERIFY-1` row on local only; sanctioned by task §11.)

## 13. Canonical scenario result — PASS (pure, local)

`verify_local_db.py` check 10 (frozen Dahej facts through
`orchestrate_application_full`): READY = {A05, A08, A11, A16, A17};
BLOCKED_BY_DOCUMENTS = {A04, A13}; A18 NOT_APPLICABLE; overall
BLOCKED_BY_DOCUMENTS. Complete path (facts → applicability → graph →
dependencies → readiness → evidence → next action → handoff prep) unbroken.
No government submission occurred or was claimed.

## 14. Regulatory regression result — PASS (counts/roles/compositions intact)

From code (`load_regulatory_pack`), worktree values (HEAD values in brackets
where T4 WIP differs; T6 changed nothing):

- MH active 26 (HEAD 26) · deferred 61 (61) · confirmation set 26
  (15 overlap deferred → 11 confirmation-only) · DNI 3 · UNKNOWN 3 ·
  hygiene-terminal 4 in no set · inventory 26+61+11+3+4 = 105 exact.
- Roles: worktree TRIGGER 22 / EXEMPTION 3 (R-043, R-044, R-087-T4-WIP) /
  CLASSIFICATION 1 (R-002). HEAD: TRIGGER 23 / EXEMPTION 2 / CLASSIFICATION 1.
- R-002 = CLASSIFICATION + APR-001 composition (unchanged). R-043/R-044 =
  EXEMPTION in APR-043 with trigger R-077 (unchanged). R-030 = TRIGGER,
  APR-026 uncomposed (STOP verdict intact). R-035 = TRIGGER (unchanged).
  R-077 = TRIGGER in APR-043 (unchanged). R-087: HEAD TRIGGER; worktree
  EXEMPTION with APR-023 (T:R-028,R-073,R-086) — in-progress T4, not T6.
- GJ: 19 rules, 0 compositions, `DEFAULT_JURISDICTION = "IN-GJ"` — isolated.

## 15. Local/staging distinction — PASS (explicit)

LOCAL (`gaia_dev`, PG 18.3, 010 objects present) and STAGING (unknown,
unverified, untouched) are reported separately. No local state was copied
anywhere; no local migration was altered to match anything.

## 16. Test results

- Committed HEAD `74023c4` (clean detached worktree, `pytest tests/ -q`):
  **2348 passed, 0 failed** — matches the T6 baseline exactly.
- Current worktree (HEAD + T3/T4 WIP, point-in-time — the tree is being
  concurrently modified, see §1): **2358 passed, 3 failed**; all 3 in
  untracked T3 file `tests/test_api_mh_demo_contract.py`
  (`test_mh_codes_with_authorities`: 20 codes vs expected 19;
  `test_facts_json_body_accepted_and_validated`: missing `facts_json`;
  `test_invalid_mh_fact_rejected`: 200 vs expected 422). Pre-existing WIP
  inconsistency, unrelated to migration 010 (mocked-API tests, no DB).
  Safe next action: T3 owner reconciles implementation vs expectations; T6
  must not fix (out of scope; would touch API/regulatory surface).

## 17. Ruff result

`ruff check app/ tests/`: **20 × E501**, identical count on HEAD and
worktree — all pre-existing at HEAD, confined to
`tests/test_mh_canonical_scenario.py` and `tests/test_mh_r030_exemption.py`.
Nothing introduced by T6 (T6 changed no code).

## 18. OpenAPI/startup result — PASS (imports + schema generation)

- HEAD: 52 paths; worktree 53 (delta is the T3 WIP
  `approval-codes` endpoint); `/health` present; orchestration + seed
  endpoints present. Generation proves imports, router wiring, and pool
  module load. No staging server exists to probe; none started.

## 19. Security/redaction notes — PASS

No secrets read (`.env` files never opened), none printed, none committed.
All identifiers reported are non-secret metadata (hostnames `localhost`,
database names, PG version, object names). No command output contained
credentials.

## 20. Remaining limitations

1. Staging migration 010 still unexecuted — needs a verified staging target
   plus the environment's own backup; then re-run this checklist live.
2. No migration-state table and no dry-runner — state via schema inspection.
3. Concurrent T3/T4 WIP in the working tree (see §1); T6 deliberately did
   not touch, verify, or gate on it beyond recording test impact.
4. 3 failing tests + 20 ruff E501s are pre-existing/WIP-owned, not T6's to fix.

Next task: T4/T3 owners land their WIP and commit; then re-attempt T6 staging
execution once a staging database is identified and verified.
