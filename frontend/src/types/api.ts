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
