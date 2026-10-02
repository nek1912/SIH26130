# Frontend SIH Demo Readiness Audit

**Audit Date**: 2026-09-29  
**Auditor**: Antigravity Assistant  
**Scope**: React Frontend (`frontend/src/`) evaluated strictly against the required 15-step SIH demo journey.  
**Strict Boundary**: Frontend audit only. No backend modifications, no rule changes, no invented regulatory claims.

---

## 1. Executive Summary

The React frontend currently features strong implementations for:
- Document management (upload, extraction status, deterministic validation findings).
- Cross-document consistency checks (`ConsistencyPanel`).
- Statutory RAG & citations (`RegulatoryAssistant` with verified sources and excerpts).
- Machine-readable evidence gap traceability (`EvidenceGapNote` for G0-R5 records).
- SLA timeline tracking (`SLACard`).
- Government handoff tracking (`HandoffPanel` with portal links, external reference recording, and staff verification).

However, the **pre-application assessment and approval discovery journey** (Steps 2–6) is largely **BROKEN or MISSING** in the frontend, preventing an applicant from evaluating a Maharashtra project, viewing an approvals matrix, understanding applicability classifications (`APPLIES` / `DOES_NOT_APPLY` / `CONDITIONAL` / `INSUFFICIENT_DATA`), or tuning Maharashtra parameters in What-If:

| Status | Count | Steps |
|---|:---:|---|
| **WORKING** | 5 | 1 (Login), 10 (Required Documents), 12 (Source/Evidence), 14 (Readiness), 15 (Government Handoff) |
| **PARTIAL** | 5 | 7 (Open Approval), 8 (See Why It Applies), 9 (See Authority), 11 (See Dependency), 13 (What-If — GJ only) |
| **MISSING** | 3 | 4 (Run Assessment), 5 (View Approval Dashboard), 6 (Understand Applicability States) |
| **BROKEN** | 2 | 2 (Create MH Project), 3 (Enter MH Project Facts) |

---

## 2. Detailed Audit by Demo Journey Step

### Step 1: Login
- **Classification**: **WORKING**
- **Component / Page**: `frontend/src/pages/auth/LoginPage.tsx`, `frontend/src/contexts/AuthContext.tsx`
- **API Used**: `supabase.auth.signInWithPassword({ email, password })`
- **Issue**: None. Email/password authentication, role extraction (`app_metadata.role`), session persistence, and role-based redirect (`/projects` for APPLICANT, `/queue` for staff) work properly.
- **Smallest Fix**: Ensure seed demo credentials (applicant and staff/reviewer) are documented for demo presentation.
- **Priority**: N/A (Working)

---

### Step 2: Create / Select Maharashtra Project
- **Classification**: **BROKEN** (Creation) / **PARTIAL** (Selection)
- **Component / Page**: `frontend/src/pages/applicant/ProjectCreatePage.tsx`, `frontend/src/pages/applicant/ProjectListPage.tsx`
- **API Used**:
  - `POST /projects` (`api.projects.create`)
  - `GET /projects?applicant_id={userId}` (`api.projects.list`)
- **Issue**:
  1. `ProjectCreatePage.tsx` only has input fields for `name` and `description`. There is no State/Jurisdiction selector.
  2. The backend `POST /projects` endpoint derives jurisdiction from the server default (`DEFAULT_JURISDICTION = "IN-GJ"`). Creating a project in the UI will create a Gujarat project, not a Maharashtra project.
  3. `ProjectListPage.tsx` lists project cards showing `name`, `description`, and `created_at`, but fails to display the project's `jurisdiction` or `pack_version`. An applicant cannot distinguish between Maharashtra and Gujarat projects.
- **Smallest Fix**:
  1. In `ProjectListPage.tsx`, display a badge for project jurisdiction (e.g. `IN-MH` vs `IN-GJ`).
  2. In `ProjectCreatePage.tsx`, add a State/Jurisdiction selector (or quick preset for "Maharashtra Chemical Unit Demo Project").
  3. Provide a fallback/quick-load button to select a pre-seeded Maharashtra project if backend `POST /projects` remains fixed to the server default.
- **Priority**: **P0**

---

### Step 3: Enter Project Facts
- **Classification**: **BROKEN**
- **Component / Page**: `frontend/src/pages/applicant/ProjectDetailPage.tsx`
- **API Used**:
  - `GET /projects/{id}/facts` (`api.projects.getFacts`)
  - `POST /projects/{id}/facts` (`api.projects.upsertFacts`)
- **Issue**:
  1. `ProjectDetailPage.tsx` only presents input fields for 5 legacy flat fields: `entity_type`, `sector`, `jurisdictions`, `headcount`, `annual_turnover_inr`.
  2. The Maharashtra regulatory pack uses 128 registered facts (`F-LOC-01`, `F-HAZ-01`, `F-ENV-01`, `F-INC-02`, etc.) validated in `facts_json`. The UI contains no form fields, inputs, or key-value editors for `facts_json`.
  3. Bug in `frontend/src/lib/api.ts` (`api.projects.upsertFacts`):
     ```ts
     upsertFacts: (projectId: string, facts: Record<string, unknown>) =>
       request<unknown>(`/projects/${projectId}/facts${toQuery(facts)}`, { method: 'POST' }),
     ```
     `api.ts` serializes facts into the query string! The backend `POST /projects/{id}/facts` endpoint expects `facts_json` as a JSON request body (`Body(default=None)`). Even if a caller passed `facts_json`, it would be lost or malformed.
  4. Placeholder text under jurisdictions reads `"e.g. Gujarat, Ahmedabad"`, with no Maharashtra guidance.
- **Smallest Fix**:
  1. Fix `api.projects.upsertFacts` in `lib/api.ts` to transmit data as a JSON body `POST` request.
  2. In `ProjectDetailPage.tsx`, add a structured section for key Maharashtra project facts (e.g. Plot Area `F-LOC-01`, Chemical Hazard `F-HAZ-01`, Pollution Category `F-ENV-01`, Investment `F-INC-02`, Power Demand `F-PRC-01`).
- **Priority**: **P0**

---

### Step 4: Run Assessment
- **Classification**: **MISSING**
- **Component / Page**: `frontend/src/pages/applicant/ProjectDetailPage.tsx`
- **API Used**: None currently wrapped at project level (`POST /approvals/evaluate` exists in backend but is unwired in frontend `lib/api.ts`).
- **Issue**:
  - There is no "Run Assessment" or "Evaluate Approvals" action on the project page.
  - An applicant is currently forced to navigate to "Applications" -> "New Application" (`/projects/:id/submit`), blindly select a single approval type from a static list, and submit a draft application before any assessment or orchestration can be executed.
  - The core PRD workflow (`Project facts → applicability rules → approval graph → documents/workflow/SLA → next action`) is disconnected at the project level.
- **Smallest Fix**:
  1. Add `api.approvals.evaluate(facts)` to `frontend/src/lib/api.ts`.
  2. Add a primary "Run Regulatory Assessment" button in `ProjectDetailPage.tsx` that calls `POST /approvals/evaluate` with the saved facts and reveals the assessed approval list.
- **Priority**: **P0**

---

### Step 5: View Approval Dashboard
- **Classification**: **MISSING**
- **Component / Page**: `frontend/src/pages/applicant/ProjectDetailPage.tsx` (or new `/projects/:id/approvals`)
- **API Used**: `POST /approvals/evaluate` or `GET /applications/{id}/orchestration`
- **Issue**:
  - No approval matrix or dashboard exists in the frontend.
  - The user cannot view the complete landscape of evaluated approvals for their project (e.g. MPCB CTE, MIDC Building Approval, Factory License, Fire NOC, Hazardous Waste Authorization, Petroleum Storage).
  - Existing lists are limited to `ApplicationListPage` (already created applications) and `QueuePage` (staff queue).
- **Smallest Fix**:
  - Add an "Approvals Matrix" section or tab on `ProjectDetailPage.tsx` displaying all evaluated approvals, their issuing authority, and status.
- **Priority**: **P0**

---

### Step 6: Understand APPLIES / DOES_NOT_APPLY / CONDITIONAL / INSUFFICIENT_DATA
- **Classification**: **MISSING**
- **Component / Page**: `frontend/src/pages/shared/OrchestrationPanel.tsx`, `frontend/src/pages/shared/statusBadges.ts`
- **API Used**: `POST /approvals/evaluate` / `GET /applications/{id}/orchestration` (`applicability_result`)
- **Issue**:
  1. The 4 statutory applicability outcomes (`APPLIES`, `DOES_NOT_APPLY`, `CONDITIONAL`, `INSUFFICIENT_DATA`) are completely absent from the UI presentation.
  2. The frontend conflates statutory applicability with operational orchestration status (`ready`, `blocked_by_dependency`, `blocked_by_documents`, `review_required`, `insufficient_data`).
  3. `OrchestrationPanel.tsx` explicitly hides non-applicable approvals:
     ```tsx
     if (approval.status === 'not_applicable') return null
     ```
     This makes it impossible for an entrepreneur to see which clearances they are exempt from (a key single-window requirement).
  4. In applicant view (`staffView = false`), the per-approval summary is omitted entirely (only blockers are rendered).
- **Smallest Fix**:
  1. Add color-coded badge variants for the 4 applicability states:
     - `APPLIES`: Emerald/Green
     - `DOES_NOT_APPLY`: Slate/Gray (kept visible with exemption note)
     - `CONDITIONAL`: Amber/Yellow
     - `INSUFFICIENT_DATA`: Purple/Orange
  2. Remove the filter hiding `not_applicable` approvals in `OrchestrationPanel.tsx`.
  3. Display the statutory `applicability_result` alongside operational readiness.
- **Priority**: **P0**

---

### Step 7: Open an Approval
- **Classification**: **PARTIAL**
- **Component / Page**: `frontend/src/pages/shared/OrchestrationPanel.tsx`, `frontend/src/pages/applicant/ApplicationDetailPage.tsx`
- **API Used**: `GET /applications/{id}` (Applications only; `GET /approvals/{id}` exists in backend but is not used in UI)
- **Issue**:
  - The UI only permits opening an *application* (`/applications/:id`).
  - An applicant cannot click on an *approval* row from an assessment dashboard to view its details, prerequisite rules, or required documents prior to filing an application.
  - In `OrchestrationPanel.tsx`, approval cards are non-interactive div cards.
- **Smallest Fix**:
  - Make approval rows in the dashboard/orchestration panel clickable to open an Approval Detail Drawer or Modal showing authority, category, legal reference, and required documents.
- **Priority**: **P1**

---

### Step 8: See Why It Applies
- **Classification**: **PARTIAL**
- **Component / Page**: `frontend/src/pages/shared/OrchestrationPanel.tsx`
- **API Used**: `GET /applications/{id}/orchestration`
- **Issue**:
  - `OrchestrationPanel.tsx` (line 85) renders only a generic sentence: `<p>{approval.explanation}</p>`.
  - It does not disclose the rule ID or the specific project facts that satisfied the rule condition (e.g. `plot_area > 5000` or `hazardous_process = true`).
  - In applicant view (`staffView = false`), even this explanation is hidden because applicant view only renders blockers.
- **Smallest Fix**:
  - In `OrchestrationPanel.tsx`, render the per-approval card for both applicant and staff views.
  - Display the rule code and triggered condition facts in the explanation section.
- **Priority**: **P0**

---

### Step 9: See Authority
- **Classification**: **PARTIAL**
- **Component / Page**: `frontend/src/pages/shared/OrchestrationPanel.tsx`, `frontend/src/pages/applicant/ApplicationDetailPage.tsx`
- **API Used**: `GET /applications/{id}/orchestration` (returns authorities map), `GET /approvals`
- **Issue**:
  - `OrchestrationPanel.tsx` renders `approval.approval_id`, `approval.status`, and `approval.explanation`, but completely omits the issuing authority (e.g. MPCB, MIDC, DISH, PESO).
  - Authority is currently only visible inside `HandoffPanel.tsx` (when an approval is ready for handoff) and within `RegulatoryAssistant.tsx` source citation pills.
- **Smallest Fix**:
  - Add an authority badge/label to the approval card header in `OrchestrationPanel.tsx` and on `ApplicationDetailPage.tsx`.
- **Priority**: **P1**

---

### Step 10: See Required Documents
- **Classification**: **WORKING**
- **Component / Page**: `frontend/src/pages/shared/DocumentChecklist.tsx`
- **API Used**:
  - `GET /applications/{id}/document-requirements` (`api.documents.listRequirements`)
  - `GET /applications/{id}/documents` (`api.documents.list`)
  - `GET /applications/{id}/extraction-summary` (`api.documents.getExtractionSummary`)
- **Issue**: None for the application journey. `DocumentChecklist` displays required documents, requirement levels (`required`, `mandatory`, `conditional`), readiness states, upload controls, extraction status, and deterministic validation findings.
- **Smallest Fix**: N/A (Working).
- **Priority**: N/A (Working)

---

### Step 11: See Dependency
- **Classification**: **PARTIAL**
- **Component / Page**: `frontend/src/pages/shared/OrchestrationPanel.tsx`
- **API Used**: `GET /applications/{id}/orchestration`
- **Issue**:
  - The backend dependency engine computes topological stage ordering and detects dependency blockers.
  - When an approval is blocked, `OrchestrationPanel.tsx` shows a blocker message (e.g. "Requires GPCB NOC (A04) to be obtained first").
  - However, the overall dependency chain (e.g. Stage 0: MPCB CTE → Stage 1: MIDC Water → Stage 2: MPCB CTO) is not visually laid out.
  - The field `approval.dependency_readiness` returned by the API is not displayed.
- **Smallest Fix**:
  - Display `dependency_readiness` and prerequisite approval tags (e.g. `Prerequisites: [A04]`) directly on each approval card in `OrchestrationPanel.tsx`.
- **Priority**: **P1**

---

### Step 12: See Source / Evidence
- **Classification**: **WORKING**
- **Component / Page**:
  - `frontend/src/pages/shared/RegulatoryAssistant.tsx`
  - `frontend/src/pages/shared/OrchestrationPanel.tsx` (`EvidenceGapNote`)
  - `frontend/src/pages/shared/DocumentChecklist.tsx` (Validation source refs)
- **API Used**:
  - `POST /regulatory/explain` (`api.regulatory.explain`)
  - `GET /regulatory/approval/{id}/explanation` (`api.regulatory.explainApproval`)
  - `GET /applications/{id}/orchestration` (G0-R5 evidence gap fields: `evidence_id`, `evidence_status`, `unresolved_question`)
- **Issue**: None. Citations include official authority, URL link, excerpt, and evidence state (`sufficient`, `partial`). Verified G0-R5 gap notes display verbatim machine-readable traceability.
- **Smallest Fix**: N/A (Working).
- **Priority**: N/A (Working)

---

### Step 13: Use What-If
- **Classification**: **PARTIAL** (Working for Gujarat) / **BROKEN** (for Maharashtra)
- **Component / Page**: `frontend/src/pages/shared/WhatIfPanel.tsx`, `frontend/src/pages/shared/ApprovalDiffList.tsx`
- **API Used**: `POST /applications/{id}/orchestration/what-if` (`api.orchestration.whatIf`)
- **Issue**:
  1. The What-If simulation mechanics and diff presentation (`ApprovalDiffList` displaying baseline → what-if status, applicability changes, added/removed blockers) work well.
  2. However, `SUPPORTED_FIELDS` in `WhatIfPanel.tsx` (lines 19–35) is hardcoded exclusively to the 15 legacy Gujarat parameters (`production_capacity`, `plot_area_sqm`, `boiler_present`, etc.).
  3. `parseRow()` in line 46 explicitly rejects any key not in `SUPPORTED_FIELDS`:
     ```ts
     if (!spec) return { ok: false, error: `Unsupported field: ${row.field}` }
     ```
  4. For a Maharashtra project, entering or simulating Maharashtra facts (`F-LOC-01`, `F-HAZ-01`, `F-ENV-01`, `F-INC-02`, etc.) is completely blocked by client-side validation.
- **Smallest Fix**:
  - Add Maharashtra fact definitions to `SUPPORTED_FIELDS` in `WhatIfPanel.tsx` (or make the field selection responsive to the application's jurisdiction).
- **Priority**: **P0**

---

### Step 14: View Readiness
- **Classification**: **WORKING**
- **Component / Page**:
  - `frontend/src/pages/shared/OrchestrationPanel.tsx`
  - `frontend/src/pages/shared/SLACard.tsx`
  - `frontend/src/pages/applicant/ApplicationDetailPage.tsx`
- **API Used**:
  - `GET /applications/{id}/orchestration`
  - `GET /applications/{id}/sla`
- **Issue**:
  - Overall readiness status pill, blocker count, explanation, next action banner, and SLA status card (`on_track`, `due_soon`, `breached`) are rendered accurately.
  - Minor limitation: In `ApplicantApplicationDetailPage.tsx`, `OrchestrationPanel` is invoked with `staffView = false`, which hides the per-approval status list and only renders blockers.
- **Smallest Fix**:
  - Enable per-approval status disclosure in applicant view so the applicant can see which clearances are `READY` vs `BLOCKED`.
- **Priority**: **P1**

---

### Step 15: Prepare Government Handoff
- **Classification**: **WORKING**
- **Component / Page**: `frontend/src/pages/shared/HandoffPanel.tsx`
- **API Used**:
  - `GET /applications/{id}/handoffs` (`api.handoffs.list`)
  - `POST /applications/{id}/handoffs/initiate` (`api.handoffs.initiate`)
  - `POST /applications/{id}/handoffs/{id}/record-submission` (`api.handoffs.recordSubmission`)
  - `POST /applications/{id}/handoffs/{id}/report-status` (`api.handoffs.reportStatus`)
  - `POST /applications/{id}/handoffs/{id}/verify` (`api.handoffs.verify`)
- **Issue**:
  - None. Fully compliant with architectural and regulatory boundaries:
    - Explicit non-integration disclosure ("UdyamDwaar does not submit applications to the government...").
    - Direct official portal links / reference links.
    - Missing documents alert before handoff.
    - Handoff initiation, portal reference input, and applicant-reported status tracking.
    - Staff verification workflow with clear audit badge (`Staff verified` vs `Reported by applicant — unverified`).
- **Smallest Fix**: N/A (Working).
- **Priority**: N/A (Working)

---

## 3. SIH Demo Readiness Matrix

| Step # | Demo Journey Step | Classification | Primary Component | API Endpoint | Priority |
|:---:|---|:---:|---|---|:---:|
| 1 | Login | **WORKING** | `LoginPage.tsx` | Supabase Auth | N/A |
| 2 | Create/select Maharashtra project | **BROKEN / PARTIAL** | `ProjectCreatePage.tsx`, `ProjectListPage.tsx` | `POST /projects`, `GET /projects` | **P0** |
| 3 | Enter project facts | **BROKEN** | `ProjectDetailPage.tsx`, `lib/api.ts` | `POST /projects/{id}/facts` | **P0** |
| 4 | Run assessment | **MISSING** | `ProjectDetailPage.tsx` | `POST /approvals/evaluate` | **P0** |
| 5 | View approval dashboard | **MISSING** | `ProjectDetailPage.tsx` | `POST /approvals/evaluate` | **P0** |
| 6 | Understand APPLIES / DOES_NOT_APPLY / CONDITIONAL / INSUFFICIENT_DATA | **MISSING** | `OrchestrationPanel.tsx`, `statusBadges.ts` | `GET /orchestration` | **P0** |
| 7 | Open an approval | **PARTIAL** | `OrchestrationPanel.tsx` | `GET /approvals/{id}` | **P1** |
| 8 | See why it applies | **PARTIAL** | `OrchestrationPanel.tsx` | `GET /orchestration` | **P0** |
| 9 | See authority | **PARTIAL** | `OrchestrationPanel.tsx`, `ApplicationDetailPage.tsx` | `GET /orchestration` | **P1** |
| 10 | See required documents | **WORKING** | `DocumentChecklist.tsx` | `GET /document-requirements` | N/A |
| 11 | See dependency | **PARTIAL** | `OrchestrationPanel.tsx` | `GET /orchestration` | **P1** |
| 12 | See source/evidence | **WORKING** | `RegulatoryAssistant.tsx`, `OrchestrationPanel.tsx` | `POST /regulatory/explain` | N/A |
| 13 | Use What-If | **PARTIAL / BROKEN (MH)** | `WhatIfPanel.tsx` | `POST /orchestration/what-if` | **P0** |
| 14 | View readiness | **WORKING** | `OrchestrationPanel.tsx`, `SLACard.tsx` | `GET /orchestration`, `GET /sla` | **P1** |
| 15 | Prepare government handoff | **WORKING** | `HandoffPanel.tsx` | `GET/POST /handoffs` | N/A |

---

## 4. Priority P0 Remediations for SIH Demo

To achieve demo readiness without altering backend rules:

1. **Fix `api.projects.upsertFacts` in `frontend/src/lib/api.ts` (P0)**:
   - Send `facts_json` in the JSON request body rather than query parameters.

2. **Add Maharashtra Project Facts Form on `ProjectDetailPage.tsx` (P0)**:
   - Provide form fields for key Maharashtra demo facts:
     - `F-LOC-01` (MIDC Industrial Area vs outside)
     - `F-HAZ-01` (Hazardous chemicals handled)
     - `F-ENV-01` (Pollution category: Red/Orange/Green/White)
     - `F-INC-02` (Plant & Machinery Investment in INR)
     - `F-PRC-01` (Manufacturing process type)

3. **Add "Run Assessment" & Approvals Matrix on `ProjectDetailPage.tsx` (P0)**:
   - Add a "Run Assessment" trigger that evaluates project facts and displays the approval matrix directly on the project page before forcing application creation.

4. **Surface the 4 Statutory Applicability States in `OrchestrationPanel.tsx` (P0)**:
   - Render `APPLIES`, `DOES_NOT_APPLY`, `CONDITIONAL`, and `INSUFFICIENT_DATA` badges.
   - Stop hiding `not_applicable` approvals so non-applicability / exemptions can be demonstrated.
   - Enable per-approval summary for applicants as well as staff.

5. **Update `WhatIfPanel.tsx` to Support Maharashtra Facts (P0)**:
   - Include Maharashtra fact keys in `SUPPORTED_FIELDS` with appropriate boolean/number/string types so demo parameter adjustments function without validation errors.

6. **Display State / Jurisdiction Badge on Project Cards (P0)**:
   - Display `jurisdiction` (`IN-MH` / `IN-GJ`) on project cards in `ProjectListPage.tsx` and in `ProjectDetailPage.tsx` header.

---

## 5. Toolchain & Build Observations

- **TypeScript 6 Deprecation (TS5101)**: `frontend/tsconfig.app.json` contains `"baseUrl": "."`, which triggers `error TS5101: Option 'baseUrl' is deprecated and will stop functioning in TypeScript 7.0` during `tsc -b`. To restore clean `npm run build` execution, specify `"ignoreDeprecations": "6.0"` or modernize path aliases to remove `baseUrl`.

