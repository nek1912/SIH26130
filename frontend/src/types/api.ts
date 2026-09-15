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

export type ApplicabilityResult = 'APPLICABLE' | 'NOT_APPLICABLE' | 'CONDITIONAL' | 'UNKNOWN'

export interface Project {
  id: string
  name: string
  description: string | null
  applicant_id: string
  created_at: string
}

export interface ProjectFacts {
  id: string
  project_id: string
  entity_type: string
  sector: string
  jurisdictions: string[]
  headcount: number
  annual_turnover_inr: number
}

export interface Approval {
  id: string
  active: boolean
  name?: string
  description?: string
  rules?: ApprovalRule[]
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

export interface ObligationApplicabilityResponse {
  obligation: Obligation
  result: ApplicabilityResult
  triggered_conditions: unknown[]
  evaluation_timestamp: string
}

export interface Application {
  id: string
  project_id: string
  approval_id: string
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
