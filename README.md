# Gujarat Industrial Approval Intelligence (GAIA)

**Smart India Hackathon 2026 — Problem Statement 26130**

A narrow Gujarat-focused industrial approvals assistant that helps applicants understand which approvals may apply, why they apply, what is needed, and what action is next.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS v4 |
| Backend | FastAPI + Python |
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth (JWT, RBAC) |
| API | REST (OpenAPI from FastAPI) |

## Project Structure

```
SIH26130/
├── backend/
│   └── app/
│       ├── api/          # FastAPI routes (health, projects, approvals, applications, workflow)
│       ├── auth/         # JWT verification, RBAC, ownership checks
│       ├── core/         # Settings (Pydantic BaseSettings)
│       ├── db/           # Supabase client factory
│       ├── repositories/ # Database access layer (CRUD + filtered queries)
│       ├── rules/        # Applicability engine, deadline rules, validation
│       ├── forms/        # Dynamic form model, conditional logic
│       ├── workflow/     # Status machine, transitions, SLA, assignments
│       ├── audit/        # Audit trail (append-only)
│       └── main.py       # FastAPI app with CORS
├── frontend/
│   └── src/
│       ├── lib/          # Supabase client, API client
│       ├── types/        # TypeScript types matching backend
│       ├── contexts/     # Auth context (session, role)
│       ├── components/   # UI (Button, Card, Badge), layout (Sidebar, Topbar), shared (StatusBadge)
│       └── pages/
│           ├── auth/     # Login
│           ├── applicant/# Projects, applications, status timeline
│           └── staff/    # Application queue, workflow actions
├── supabase/
│   └── migrations/       # SQL schema (12 tables)
└── docs/
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Supabase project ([supabase.com](https://supabase.com))

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -e ".[dev]"
cp .env.example .env          # Fill in Supabase keys
uvicorn app.main:app --reload
```

API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env          # Fill in Supabase URL + anon key
npm run dev
```

App at [http://localhost:5173](http://localhost:5173)

### 3. Environment Variables

**Backend** (`backend/.env`):
| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (optional) |
| `AUTH_JWT_SECRET` | JWT secret from Supabase dashboard → Settings → API |
| `AUTH_JWT_AUDIENCE` | `authenticated` (default) |

**Frontend** (`frontend/.env`):
| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key |
| `VITE_API_URL` | Backend URL (`http://localhost:8000`) |

## Features Implemented

### Applicant Flow
- Login with email/password (Supabase Auth)
- Create and manage industrial projects
- Edit project facts (entity type, sector, jurisdictions, headcount, turnover)
- Submit applications for specific approvals
- View application status with visual workflow timeline
- Take actions: submit, respond to queries, withdraw

### Staff Flow
- Application queue with status filters and pagination
- Application detail with workflow actions
- Role-based action visibility (Reviewer, Manager, Admin)
- Request information, advance review, approve, refuse
- Reason input for decisions
- Structured error handling (401/403/409/422)

### Backend
- 14-status workflow state machine with 22 transition rules
- RBAC: 4 roles (Applicant, Reviewer, Manager, Admin), 18 permissions
- Deterministic applicability engine (Applicable / Not Applicable / Conditional / Unknown)
- SLA computation with Indian fiscal year awareness
- Audit trail for all material state changes
- JWT verification (Supabase-compatible HS256)

## Running Tests

```bash
# Backend (263 tests)
cd backend
python -m pytest tests/ -v

# Backend lint
python -m ruff check app/ tests/

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend lint
npx oxlint

# Frontend build
npx vite build
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/projects` | `application:create` | Create project |
| GET | `/projects/{id}` | `view_own/view_team/view_all` | Get project |
| POST | `/projects/{id}/facts` | `application:create` | Upsert project facts |
| GET | `/projects/{id}/applications` | `view_own/view_team/view_all` | List project applications |
| GET | `/applications` | `view_team/view_all` | List all applications (staff, with filters) |
| GET | `/applications/{id}` | `view_own/view_team/view_all` | Get application |
| POST | `/applications` | `application:create` | Create application |
| POST | `/applications/{id}/submit` | `application:create` | Submit draft |
| POST | `/applications/{id}/advance` | `application:review` | Advance review |
| POST | `/applications/{id}/request-info` | `application:review` | Request information |
| POST | `/applications/{id}/respond` | `application:create` | Respond to query |
| POST | `/applications/{id}/assign` | `application:assign` | Assign officer |
| POST | `/applications/{id}/approve` | `application:decide` | Approve |
| POST | `/applications/{id}/refuse` | `application:decide` | Refuse |
| POST | `/applications/{id}/withdraw` | `application:create` | Withdraw |

## Current Status

- **Phase 1 complete**: Backend foundation, 12-table schema, pure logic engines, 119 tests
- **Phase 2A complete**: FastAPI routes + Supabase data layer, 137 tests
- **Phase 2B complete**: Auth integration — JWT, RBAC, ownership, 185 tests
- **Phase 2C complete**: Workflow engine — transitions, stages, audit, 253 tests
- **Phase 3A complete**: Frontend foundation — Vite SPA, auth, routing, 263 tests
- **Phase 3B complete**: Staff workflow UI, applicant timeline, facts editing, 263 tests

**Next**: Phase 3C — Document management, SLA display, workflow event history

## License

MIT
