# UdyamDwaar / GAIA — Industrial Approval Intelligence Platform

**Smart India Hackathon 2026 — Problem Statement 26130**

A deterministic regulatory-intelligence and handoff-preparation assistant for industrial projects (focused on synthetic organic chemical manufacturing) in **Maharashtra (Primary: IN-MH)** and **Gujarat (Legacy/Baseline: IN-GJ)**. It assesses which approvals may apply from structured project facts against versioned, source-cited rules, and prepares — but never performs — government portal submissions. It is not a single-window portal and issues no approvals.

---

## 1. Overview & Mission

Navigating statutory clearances for industrial establishments across state and central departments in India is historically fraught with regulatory opacity, non-linear dependencies, ambiguous thresholds, and bureaucratic delays. 

**UdyamDwaar (GAIA)** narrows this down by evaluating structured project facts against versioned, source-cited rules with explicit fail-closed handling of missing evidence. Rather than relying on non-deterministic LLM hallucinations for statutory mandates, the platform couples pure-logic rule evaluators with an official-source grounded retrieval system used only for explanation, never for decisions:

$$\text{Project Facts} \longrightarrow \text{Deterministic Rules} \longrightarrow \text{Approval Graph} \longrightarrow \text{Readiness \& SLA} \longrightarrow \text{Next Action}$$

---

## 2. Architecture & Capabilities

### Core Subsystems

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                   React 19 + TypeScript + Vite Frontend                      │
│      (Applicant Portal, Staff Review Queue, What-If Simulator, Assistant)    │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ REST / OpenAPI
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                          FastAPI Backend (Python 3.11)                       │
├──────────────────────────────┬───────────────────────────────┬───────────────┤
│    Rules & Applicability     │   Dependency & Orchestration  │ Documents &   │
│  - Fact Registry (128 facts) │  - DAG Topological Sort       │ Consistency   │
│  - IN-MH Pack (26 active)    │  - Stage Assignment           │ - Extraction  │
│  - IN-MH Pack (61 deferred)  │  - Blocker Diagnostics        │ - Validation  │
│  - IN-GJ Pack (19 active)    │  - What-If Simulation Engine  │ - Cross-Doc   │
│  - Fact Derivations Engine   │  - Manual Handoff Records     │   Consistency │
├──────────────────────────────┴───────────────────────────────┴───────────────┤
│            Regulatory RAG Assistant & Incentives Intelligence                │
│  - PostgreSQL tsvector full-text search with official source tiering         │
│  - Deterministic Support Scheme & Subsidy Assessment Engine                  │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│             PostgreSQL (Local / Supabase) + Storage Layer                    │
│      (13 Schema Migrations, Connection Pooling, Append-Only Audit Trail)     │
└──────────────────────────────────────────────────────────────────────────────┘
```

1. **Deterministic Regulatory Engine**:
   - Evaluates boolean, numeric, enum, and enum-set predicates with strict fail-closed handling for missing or unverified parameters (`INSUFFICIENT_DATA`).
   - Pure-logic tree structure (`ConditionNode`, `AndNode`, `OrNode`, `NotNode`).
   - Derived facts layer for composite determinations (e.g. MSME classification under R-057, Major Accident Hazard status under MSIHC / R-091).

2. **Jurisdiction-Scoped Regulatory Packs**:
    - **Maharashtra (`IN-MH`, Primary SIH Jurisdiction)**:
      - **26 Active Rules** covering: EC small-unit facet (R-002) + EIA 8(a) range (R-007); hazardous-waste authorization (R-018/R-096); forest (R-084) and CRZ (R-083) location triggers; CGWA groundwater abstraction (R-077) with MSE/domestic exemptions (R-043/R-044); petroleum storage rule (R-030, TRIGGER retained per STOP verdict); MIDC branch guard (R-035); boiler definition/registration/BOE/deemed-registration (R-028/R-073/R-086, exemption R-087); plus establishment/consent-adjacent and waste/role duties (R-009/R-011/R-012/R-026/R-046/R-056/R-067/R-070/R-089/R-093/R-094). CTE/CTO sector triggers (R-013/R-014/R-017) remain deferred — no full consent coverage is claimed.
      - **61 Gated & Deferred Rules**: Strictly held in `MH_DEFERRED_RULES` with verified rationale against premature activation (spatial GIS dependencies, unextracted state forms, lookup cardinality, ODS compliance duties, planning gates).
     - **128 Fact Registry**: Code-defined, strictly typed IN-MH facts in `app/rules/facts.py`.
     - **22 Verified Sources**: Grounded in official Primary (T1), Secondary (T2), and Portal (T3) sources.
   - **Gujarat (`IN-GJ`, Legacy/Regression Baseline)**:
     - 19 active rules, 32 verified regulatory sources, 6 verified GIP 2020 incentive schemes.
     - `DEFAULT_JURISDICTION = "IN-GJ"` preserved as the immutable global baseline cutover constant.

3. **Approval Dependency Graph & Orchestration**:
   - Computes per-approval readiness with the exact backend vocabulary (`ready`, `blocked_by_dependency`, `blocked_by_documents`, `review_required`, `insufficient_data`, `complete`, `not_applicable`) — never synonyms.
   - Cycle detection and topological ordering across pre-establishment, pre-construction, and pre-operation stages.
   - Surfaces unverified evidence gaps and documentation blockers in real time.

4. **Document Extraction, Validation & Consistency**:
   - Deterministic extraction for PDF, CSV, and Excel uploads.
   - Automated rule validation across document domains.
   - Cross-document consistency engine detecting discrepancies across project filings (e.g. capacity or site coordinates differing between DPR, EIA, and CTE applications).

5. **What-If Scenario Simulation**:
   - Interactive policy sandbox allowing industrial planners to simulate modifications (e.g. increasing plant capital investment, changing chemical inventory, relocating from MIDC to non-MIDC zone) and immediately view the delta on approvals, dependencies, and SLAs.

6. **Grounded Regulatory RAG Assistant**:
   - Source-grounded regulatory queries backed by PostgreSQL `tsvector` full-text search and GIN indexing over official legislation and notifications. Templates explain; the engine never calls an LLM for statutory facts, and retrieval never overrides rule decisions.

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4 | Ultra-responsive SPA for applicants and department officers |
| **Backend** | FastAPI, Python 3.11, Pydantic v2 | High-performance asynchronous REST API |
| **Database** | PostgreSQL (Local / Supabase) | Relational persistence, connection pooling (`psycopg_pool`), tsvector search |
| **Auth** | Supabase Auth / PyJWT (HS256) | Role-Based Access Control (`Applicant`, `Reviewer`, `Manager`, `Admin`) |
| **Storage** | Local Filesystem / Supabase Storage | Document upload, extraction, and validation store |
| **Code Quality** | Pytest, Ruff, Oxlint, TypeScript Compiler | Backend suite green (see §8), Ruff clean on implementation code, 0 TypeScript errors |

---

## 4. Repository Structure

```
SIH26130/
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (projects, approvals, applications, workflow,
│   │   │                    # documents, extraction, consistency, orchestration,
│   │   │                    # regulatory, incentives, handoffs, whatif)
│   │   ├── auth/            # JWT verification, RBAC, ownership guards
│   │   ├── consistency/     # Cross-document consistency engine
│   │   ├── core/            # Configuration and BaseSettings
│   │   ├── db/              # Postgres connection pool and client factories
│   │   ├── extraction/      # Document extraction & deterministic validation
│   │   ├── handoff/         # Manual government-handoff tracking (records only, no portal calls)
│   │   ├── incentives/      # Government support & subsidy assessment engine
│   │   ├── orchestration/   # Approval readiness, blocker diagnosis & What-If engine
│   │   ├── regulatory/      # Regulatory RAG retrieval and template explanations
│   │   ├── repositories/    # Database persistence and repository layer
│   │   ├── rules/           # Applicability engine, fact registry (IN-MH 128 facts),
│   │   │                    # derivations, dependency DAG
│   │   ├── seed/            # Regulatory packs (IN-MH, IN-GJ), sources, portals, SLAs
│   │   └── workflow/        # 14-status state machine, transitions, SLA calculator
│   └── tests/               # Backend test suites (see §8 for current count)
├── frontend/
│   └── src/
│       ├── components/      # UI primitives, layout (Sidebar, Topbar), shared widgets
│       ├── contexts/        # Auth and application session context
│       ├── lib/             # API client and authentication interceptors
│       ├── pages/           # Applicant portal, staff queue, detail views, what-if, assistant
│       └── types/           # Type definitions matching backend schemas
├── supabase/
│   └── migrations/          # 13 ordered SQL migrations (schema, tables, indexes)
└── docs/                    # Architecture records, audit reports, and design specs
```

---

## 5. Quick Start Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **PostgreSQL 14+** (Local or Supabase)

---

### Step 1: Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell / CMD
# source .venv/bin/activate     # macOS / Linux

# Install dependencies in editable mode
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
# Edit backend/.env with your DATABASE_URL or Supabase credentials

# Start backend server
uvicorn app.main:app --reload --port 8000
```

FastAPI OpenAPI interactive docs available at:  
👉 **http://localhost:8000/docs**

---

### Step 2: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend application available at:  
👉 **http://localhost:5173**

---

### Step 3: Run Verification Checks

```bash
# Run backend test suite (see §8 for the current passing count)
cd backend
python -m pytest

# Run Python code quality & linting
python -m ruff check app/ tests/

# Run frontend TypeScript type checking
cd ../frontend
npx tsc --noEmit
```

---

## 6. Primary API Endpoints

| Category | Method | Path | Description |
|---|---|---|---|
| **Health** | `GET` | `/health` | Service liveness and database connectivity |
| **Projects** | `POST` | `/projects` | Create industrial project profile |
| | `GET` | `/projects/{id}` | Retrieve project details and jurisdiction |
| | `POST` | `/projects/{id}/facts` | Upsert project facts (strictly typed per jurisdiction) |
| **Approvals** | `GET` | `/approvals` | List regulatory catalog approvals |
| | `POST` | `/approvals/seed` | Seed canonical approval catalog |
| **Applications** | `POST` | `/applications` | Instantiate approval application workflow |
| | `GET` | `/applications/{id}` | Get application status, timeline, and officer notes |
| | `POST` | `/applications/{id}/submit` | Transition draft to submitted |
| | `POST` | `/applications/{id}/advance` | Officer advancement through scrutiny |
| **Orchestration** | `GET` | `/applications/{id}/orchestration` | Comprehensive readiness assessment and blockers |
| **What-If** | `POST` | `/applications/{id}/orchestration/what-if` | Simulate fact changes without persisting (same-pack baseline + alt) |
| **Consistency** | `POST` | `/applications/{id}/consistency/check` | Cross-document field consistency audit |
| **Extraction** | `POST` | `/applications/{id}/documents/{doc_id}/extract` | Deterministic document parsing and validation |
| **Regulatory RAG**| `GET` | `/sources` | List official legislative sources (optional `?jurisdiction=`) |
| | `POST` | `/regulatory/explain` | Cited explanation for a regulatory query (templates only, never a legal determination) |
| | `GET` | `/regulatory/approval/{id}/explanation` | Source-grounded explanation for one approval |
| **Incentives** | `POST` | `/incentives/assess` | Deterministic eligibility check for support schemes |
| **Handoffs** | `GET` | `/applications/{id}/handoffs` | List READY approvals + recorded manual external progress |
| | `POST` | `/applications/{id}/handoffs/initiate` | Record intent to apply on the official portal (READY only; no government submission occurs) |

---

## 7. Regulatory Clusters Audited (Maharashtra Pack)

| Cluster | Key Audited Rules | Status & Determinations |
|---|---|---|
| **Environmental & Consent** | R-002, R-003, R-004, R-007, R-008, R-013, R-014 | `R-002`, `R-007` active; `R-003`, `R-004`, `R-008`, `R-013`, `R-014` deferred (category escalation, multi-activity lookup guards). |
| **Location & Land Triggers** | R-077, R-083, R-084, R-096, R-091, R-060, R-061, R-085 | `R-077` (CGWA), `R-083` (CRZ), `R-084` (Forest), `R-096` (HW Sch II) active; `R-091` derived via `derive_mah_status()`; others deferred. |
| **Labour, Factory & Safety** | R-019, R-020, R-022, R-023, R-027, R-070, R-090 | `R-070` (Safety Officer) active; others deferred (DISH category selector, OSH Code draft status, BOCW factory exception). |
| **Utilities, Water & Power**| R-038, R-048, R-052, R-053, R-097 | All 5 deferred fail-closed (utility workflow requests, voltage thresholds, CETP capacity, groundwater prohibition). |
| **Safety, Hazardous & Transport** | R-030, R-032, R-033, R-034, R-035, R-062, R-092 | `R-030` (Petroleum Class B exemption) and `R-035` (MIDC plot allotment) active; others deferred (form routing, SMPV, GCR). |
| **Sector-Specific Clearances** | R-051, R-068, R-069, R-095, R-105 | All 5 deferred fail-closed (AAI height GIS, FDA drug licensing, PESO explosive rules, ODS compliance duties, planning gates). |

---

## 8. Verification & Test Metrics

- **Total Backend Tests**: **2476 passed** (0 failures; 2348 T2 baseline + 62 T4 + 13 T3 + 44 T5 + 9 T7)
- **Code Linter**: **Ruff** — clean on implementation code (20 pre-existing line-length findings confined to two older test files)
- **Type Checker**: **TypeScript clean** (`tsc --noEmit` exited with code 0)
- **Active Rules**: 26 (IN-MH), 19 (IN-GJ)
- **Deferred Rules**: 61 (IN-MH, fail-closed in `MH_DEFERRED_RULES`)
- **Jurisdiction Isolation**: Strictly verified; zero bleed between state packs.

---

## 9. License

This repository is developed for **Smart India Hackathon 2026** (Problem Statement 26130).  
Licensed under the [MIT License](LICENSE).
