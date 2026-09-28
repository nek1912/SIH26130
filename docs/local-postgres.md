# Local PostgreSQL development database

The backend runs against a completely local PostgreSQL database. No
Supabase project is required for development.

## Setup

1. Install PostgreSQL 16/17 and create the database:

```sql
CREATE DATABASE gaia_dev;
```

2. Apply migrations in lexical order with `ON_ERROR_STOP`:

```powershell
$env:PGPASSWORD = 'postgres'
foreach ($m in @('001_initial_schema','002_document_requirements',
'003_document_extraction','004_consistency','005_rag_sources',
'006_documents_extraction_status','007_applications_approval_code',
'008_approvals_code','009_approval_handoffs','010_persisted_jurisdiction',
'011_approval_workflow_definition','012_application_applicant_id')) {
  psql -h localhost -p 5432 -U postgres -d gaia_dev `
    -v ON_ERROR_STOP=1 `
    -f "supabase/migrations/$m.sql"
}
```

Migration 001 references `auth.users`; on a bare PostgreSQL instance
create the stub first (Supabase provides it natively):

```sql
CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE IF NOT EXISTS auth.users (id uuid PRIMARY KEY);
```

Insert a local identity row per developer user as needed; application
`applicant_id` values must reference it.

3. Configure the backend (never commit real credentials):

```env
DATABASE_URL=postgresql://postgres:<password>@localhost:5432/gaia_dev
LOCAL_STORAGE_DIR=data/uploads
AUTH_JWT_SECRET=<local-dev-secret-min-32-chars>
```

4. Seed the approval catalog (idempotent):

```powershell
cd backend
python scripts/verify_local_db.py --seed-catalog
```

5. Run the repeatable verification (14 checks):

```powershell
cd backend
python ..\scripts\verify_local_db.py --seed-catalog --write
```

## Authentication (local development)

Auth is standalone HS256 JWT verification (PyJWT) — no Supabase
dependency. Ownership (applicant vs staff roles) and RBAC are
unchanged. Mint a local dev token with the configured secret:

```python
import jwt, datetime
secret = "<AUTH_JWT_SECRET>"
tok = jwt.encode({
    "sub": "<user-uuid>",
    "email": "dev@local",
    "app_metadata": {"role": "APPLICANT"},  # or REVIEWER/MANAGER/ADMIN
    "aud": "authenticated",
    "exp": datetime.datetime.now(datetime.timezone.utc)
         + datetime.timedelta(hours=1),
}, secret, algorithm="HS256")
```

No development auth bypass exists by design; `DEV`-style backdoors
must never be added.

## Document storage

Uploaded bytes live under `backend/data/uploads/` (git-ignored) via
the `app.storage` adapter boundary (`DocumentStorage` protocol +
`LocalFileStorage`). Metadata stays in PostgreSQL. A future object
store replaces the adapter without touching document-domain logic.

## Regulatory search

PostgreSQL full-text search (`tsvector` + GIN, migration 005) with
`ts_rank_cd` ranking. No pgvector, embeddings, or LLM involved.

## Notes

- Migrations 011/012 backfill genuine application-read columns
  (`approvals.workflow_definition`, `applications.applicant_id`)
  that the code and design docs already required; they were absent
  from 001–010.
- `project_facts.jurisdictions[]` remains applicant entity data and
  never selects the regulatory pack; persisted
  `jurisdiction`/`pack_version` on projects/applications does.
