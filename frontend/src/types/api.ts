export type SystemRole = 'APPLICANT' | 'REVIEWER' | 'MANAGER' | 'ADMIN'

export type ApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'awaiting_inspection'
  | 'awaiting_consultation'
  | 'awaiting_hearing'
  | 'awaiting_documents'
  | 'awaiting_payment'
  | 'approved'
  | 'refused'
  | 'withdrawn'
  | 'incomplete'
  | 'returned'
  | 'cancelled'

export interface Project {
  id: string
  name: string
  description: string | null
  applicant_id: string
  created_at: string
  // Persisted regulatory identity (server-stamped; never client-inferred).
  jurisdiction?: string | null
  pack_version?: string | null
}

export interface ProjectFacts {
  id: string
  project_id: string
  entity_type: string
  sector: string
  jurisdictions: string[]
  headcount: number
  annual_turnover_inr: number
  // Extended IN-MH fact registry payload (F-* keys), if recorded.
  facts_json?: Record<string, unknown> | null
}

export interface Approval {
  id: string
  active: boolean
  name?: string
  description?: string
  rules?: ApprovalRule[]
  // Canonical workbook/catalog code (A01… / APR-xxx) when seeded.
  code?: string | null
}

export interface ApprovalRule {
  id: string
  approval_id: string
  condition?: string
}

export interface Obligation {
  canonical_id: string
  instrument_ref: string
  type: string
  summary: string
  applicability_conditions: unknown[]
  frequency: string
  deadline_rule: unknown
  proof_types: string[]
  penalty: string
  source_refs: unknown[]
  version: string
  confidence: number
}

export interface Application {
  id: string
  project_id: string
  approval_id: string
  // Pack approval code (APR-xxx / Axx); authoritative for assessment scope.
  approval_code?: string | null
  jurisdiction?: string | null
  pack_version?: string | null
  status: ApplicationStatus
  applicant_id: string
  reference_number: string
  current_stage: string | null
  assigned_officer_id: string | null
  decision_outcome: string | null
  decision_reason: string | null
  created_at: string
  updated_at?: string
}

export interface SlaInfo {
  stage_key: string
  stage_label: string
  sla_business_days: number
  entered_at: string
  due_date: string
  used_business_days: number
  remaining_business_days: number
  overdue_business_days: number
  state: 'on_track' | 'due_soon' | 'due_today' | 'breached'
}

export interface WorkflowEvent {
  id: string
  application_id: string
  from_stage: string | null
  to_stage: string
  action: string
  performed_by: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface WorkflowResult {
  application_id: string
  previous_status: ApplicationStatus
  new_status: ApplicationStatus
  current_stage: string | null
  workflow_event: WorkflowEvent
}

export interface AssignResult {
  application_id: string
  assigned_officer_id: string
}

export interface AuthUser {
  id: string
  email: string
  role: SystemRole
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface DocumentRequirement {
  id: string
  application_id: string
  requirement_key: string
  document_name: string
  approval_id: string
  domain: string
  requirement_level: 'required' | 'mandatory' | 'conditional'
  readiness: 'pending' | 'uploaded' | 'valid' | 'invalid' | 'review_required'
  accepted_mime_types: string[] | null
  max_size_mb: number | null
  description: string | null
  source_basis: string | null
  source_url: string | null
  document_role: string | null
  uploaded_document_id: string | null
  rejection_reason: string | null
  created_at: string
  updated_at: string
}

export interface UploadedDocument {
  id: string
  application_id: string
  requirement_key: string
  original_filename: string
  storage_path: string
  mime_type: string
  file_size_bytes: number
  status: 'pending_upload' | 'uploaded' | 'verified' | 'rejected' | 'virus_detected' | 'expired'
  extraction_status: ExtractionStatus | null
  rejection_reason: string | null
  uploaded_by_user_id: string | null
  created_at: string
}

export interface UploadResult {
  document: UploadedDocument
  requirement: DocumentRequirement
}

export type ExtractionStatus = 'pending' | 'completed' | 'failed' | 'unsupported'

export type ValidationOutcome = 'VALID' | 'INVALID' | 'REVIEW_REQUIRED' | 'INSUFFICIENT_DATA'

export interface ExtractedField {
  id: string
  document_id: string
  application_id: string
  field_name: string
  field_value: unknown
  field_type: string
  extraction_method: string
  confidence: number
  extracted_at: string
  metadata: Record<string, unknown>
}

export interface ExtractionResult {
  document_id: string
  application_id: string
  extraction_status: ExtractionStatus
  field_count: number
  errors: string[]
  metadata: Record<string, unknown>
}

export interface FieldFinding {
  field_name: string
  rule_id: string
  rule_description: string
  outcome: ValidationOutcome
  expected: unknown
  actual: unknown
  message: string
  source_ref: string
}

export interface ValidationResult {
  document_id: string
  requirement_key: string
  outcome: ValidationOutcome
  finding_count: number
  findings: FieldFinding[]
  source_refs: string[]
}

export interface ExtractionSummary {
  requirement_key: string
  document_name: string
  domain: string
  readiness: string
  extraction_status: ExtractionStatus | null
  validation_outcome: ValidationOutcome | null
  has_document: boolean
  extraction: unknown
  validation: unknown
  finding_count: number
  findings: FieldFinding[]
}

export type ConsistencyOutcome = 'VALID' | 'REVIEW_REQUIRED' | 'INSUFFICIENT_DATA'

export interface ConsistencyFinding {
  rule_id: string
  canonical_field: string
  outcome: ConsistencyOutcome
  observed_values: Record<string, unknown>
  expected_relationship: string
  message: string
  source_ref: string
}

export interface ConsistencyResult {
  application_id: string
  outcome: ConsistencyOutcome
  findings: ConsistencyFinding[]
  checked_at: string
  rule_version: string
}

export type OrchestrationStatus =
  | 'ready'
  | 'blocked_by_dependency'
  | 'blocked_by_documents'
  | 'review_required'
  | 'insufficient_data'
  | 'complete'
  | 'not_applicable'

export interface BlockerDetail {
  blocker_type: string
  description: string
  affected_approval_id: string | null
  affected_document_key: string | null
  source_ref: string
  evidence: string
  action_required: string
  // Structured G0-R5 evidence traceability (backend BlockerDetail).
  // Present only on INSUFFICIENT_DATA blockers built from evidence gaps.
  evidence_id?: string | null
  evidence_status?: string | null
  unresolved_question?: string | null
}

export interface DocumentReadinessSummary {
  requirement_key: string
  document_name: string
  readiness: string
  extraction_status: string | null
  validation_outcome: string | null
  blocking: boolean
  reason: string
}

export interface ApprovalOrchestration {
  approval_id: string
  status: OrchestrationStatus
  applicability_result: string
  dependency_readiness: string
  document_readiness: string
  consistency_outcome: string | null
  sla_state: string | null
  blockers: BlockerDetail[]
  documents: DocumentReadinessSummary[]
  explanation: string
  next_action: string
}

export interface NextAction {
  action_type: string
  description: string
  affected_approval_id: string | null
  affected_document_key: string | null
  link_section: string
}

export interface ApplicationOrchestration {
  application_id: string
  overall_status: OrchestrationStatus
  approvals: Record<string, ApprovalOrchestration>
  total_blockers: number
  next_action: NextAction | null
  stage_number: number | null
  explanation: string
}

// ── What-If Recalculation (stateless, backend is source of truth) ──

export interface WhatIfRequest {
  fact_overrides: Record<string, unknown>
  include_unchanged?: boolean
}

export interface ApprovalDiff {
  approval_id: string
  baseline_applicability: string
  whatif_applicability: string
  baseline_status: string
  whatif_status: string
  baseline_dependency: string
  whatif_dependency: string
  added_blockers: BlockerDetail[]
  removed_blockers: BlockerDetail[]
  baseline_explanation: string
  whatif_explanation: string
}

export interface WhatIfComparison {
  changed_approvals: ApprovalDiff[]
  unchanged_approvals: string[]
  added_blockers: BlockerDetail[]
  removed_blockers: BlockerDetail[]
  overall_baseline: string
  overall_whatif: string
  next_action_baseline: NextAction | null
  next_action_whatif: NextAction | null
  no_change: boolean
}

export interface WhatIfResponse {
  application_id: string
  baseline: ApplicationOrchestration
  what_if: ApplicationOrchestration
  diff: WhatIfComparison
  applied_overrides: Record<string, unknown>
  note: string
}

// ── Regulatory Change Rehearsal (stateless, staff-only) ──

export type ChangeKind =
  | 'RULE_CHANGE'
  | 'DOCUMENT_REQUIREMENT_CHANGE'
  | 'DEPENDENCY_CHANGE'
  | 'EVIDENCE_STATUS_CHANGE'
  | 'SOURCE_METADATA_CHANGE'

export type ImpactClassification = 'RESULT_CHANGED' | 'SOURCE_RELEVANT' | 'NO_IMPACT'

export interface ChangeDescriptor {
  change_kind: ChangeKind
  source_id?: string | null
  rule_id?: string | null
  requirement_key?: string | null
  evidence_id?: string | null
  old_value?: Record<string, unknown> | null
  new_value?: Record<string, unknown> | null
  old_status?: string | null
  new_status?: string | null
}

export interface ProjectImpact {
  classification: ImpactClassification
  affected_approvals: string[]
  affected_rule_ids: string[]
  source_ids: string[]
  baseline_overall: string
  new_overall: string
  diffs: ApprovalDiff[]
  baseline_results: Record<string, { status: string; applicability: string; dependency: string }>
  new_results: Record<string, { status: string; applicability: string; dependency: string }>
  reason: string
  evidence_caveats: string[]
  change: ChangeDescriptor
}

export interface ImpactRehearseResponse extends ProjectImpact {
  application_id: string
}

// ── MH demo: pack approval codes projected per project ──

export interface PackApprovalCode {
  approval_code: string
  authority: string
}

export interface PackApprovalCodes {
  jurisdiction: string
  pack_version: string | null
  approvals: PackApprovalCode[]
}

// ── Manual Government Handoff (no integration; all statuses reported/verified) ──

export type HandoffStatus =
  | 'handed_off'
  | 'submitted_externally'
  | 'under_external_review'
  | 'approved_external'
  | 'rejected_external'
  | 'returned_for_correction'

export interface HandoffRecord {
  id: string
  application_id: string
  approval_code: string
  authority: string
  external_system: string
  portal_url: string
  portal_kind: 'portal' | 'reference'
  status: HandoffStatus
  external_reference: string | null
  submitted_at: string | null
  last_external_update_at: string | null
  applicant_note: string | null
  reported_by: string | null
  verification: 'user_reported' | 'staff_verified'
  verified_by: string | null
  verified_at: string | null
  currently_ready?: boolean
}

export interface ReadyApprovalHandoff {
  approval_code: string
  authority: string
  external_system: string
  portal_url: string
  portal_kind: 'portal' | 'reference'
  document_readiness: string
  missing_documents: string[]
}

export interface HandoffListResponse {
  handoffs: HandoffRecord[]
  ready_approvals: ReadyApprovalHandoff[]
}

// ── Regulatory / RAG ──

export interface Source {
  id: string
  jurisdiction: string
  domain: string
  url: string
  trust_tier: string
  title: string
  authority: string
  source_type: string
  source_class: string
  notes: string
  checked_date: string
}

export interface SourceChunk {
  id: string
  source_id: string
  chunk_text: string
  chunk_index: number
  metadata: Record<string, unknown>
}

export interface Citation {
  source_id: string
  title: string
  authority: string
  url: string
  source_type: string
  excerpt: string
  relevance_rank: number
}

export type EvidenceState = 'sufficient' | 'insufficient' | 'partial'

export interface RegulatoryExplanation {
  answer: string
  citations: Citation[]
  evidence_state: EvidenceState
  query: string
  approval_id: string | null
  application_id: string | null
}

export interface SourceStatus {
  source_count: number
  chunk_count: number
}

// ── Incentive Schemes ──

export type SchemeCategory =
  | 'capital_subsidy'
  | 'interest_subsidy'
  | 'tax_concession'
  | 'infrastructure'
  | 'msme_support'
  | 'quality_certification'
  | 'energy'
  | 'employment'
  | 'general'

export type RelevanceState =
  | 'potentially_relevant'
  | 'not_relevant'
  | 'conditional'
  | 'insufficient_data'

export interface RequiredInfo {
  field_name: string
  description: string
  source_ref: { source_id: string; citation_span: string } | null
}

export interface SchemeBenefit {
  description: string
  source_ref: { source_id: string; citation_span: string } | null
}

export interface SupportScheme {
  id: string
  name: string
  authority: string
  category: SchemeCategory
  description: string
  eligibility_conditions: unknown[]
  required_info: RequiredInfo[]
  benefits: SchemeBenefit[]
  source_refs: { source_id: string; citation_span: string }[]
  version: string
  active: boolean
}

export interface SchemeRelevance {
  scheme_id: string
  scheme_name: string
  relevance: RelevanceState
  reason: string
  triggered_conditions: string[]
  missing_info: string[]
  source_refs: { source_id: string; citation_span: string }[]
}

export interface ProjectIncentiveAssessment {
  project_id: string
  assessments: SchemeRelevance[]
  relevant_count: number
  conditional_count: number
  insufficient_count: number
  not_relevant_count: number
  explanation: string
}
