import { supabase } from './supabase'
import type {
  DocumentRequirement,
  UploadedDocument,
  UploadResult,
  ExtractionResult,
  ValidationResult,
  ExtractionSummary,
  ConsistencyResult,
  SlaInfo,
  ApplicationOrchestration,
  WhatIfResponse,
  ChangeDescriptor,
  ImpactRehearseResponse,
  HandoffListResponse,
  HandoffRecord,
  PackApprovalCodes,
  Source,
  SourceChunk,
  RegulatoryExplanation,
  SourceStatus,
  SupportScheme,
  ProjectIncentiveAssessment,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function authHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession()
  const headers: Record<string, string> = {}
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }
  return headers
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseHeaders = await authHeaders()
  const headers: Record<string, string> = {
    ...baseHeaders,
    ...(options.headers as Record<string, string>),
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (res.status === 401) {
    window.location.href = '/login'
    throw new ApiError(401, 'Unauthorized')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail ?? res.statusText)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

function toQuery(params: Record<string, unknown>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
  if (entries.length === 0) return ''
  const qs = new URLSearchParams()
  for (const [k, v] of entries) {
    if (Array.isArray(v)) {
      for (const item of v) qs.append(k, String(item))
    } else {
      qs.set(k, String(v))
    }
  }
  return `?${qs.toString()}`
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  projects: {
    list: (userId: string) => request<unknown[]>(`/projects${toQuery({ applicant_id: userId })}`),
    get: (id: string) => request<unknown>(`/projects/${id}`),
    create: (name: string, description?: string, applicantId?: string, jurisdiction?: string) =>
      request<unknown>(`/projects${toQuery({ name, description, applicant_id: applicantId, requested_jurisdiction: jurisdiction })}`, { method: 'POST' }),
    getFacts: (projectId: string) => request<unknown>(`/projects/${projectId}/facts`),
    // Contract: legacy typed fields travel as query params; the extended
    // IN-MH registry payload travels as an embedded JSON body
    // ({"facts_json": {...}}) — the backend silently drops a bare-dict body
    // when complex query params are present (FastAPI body embedding).
    upsertFacts: (
      projectId: string,
      legacy: Record<string, unknown>,
      factsJson?: Record<string, unknown>,
    ) =>
      request<unknown>(`/projects/${projectId}/facts${toQuery(legacy)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ facts_json: factsJson ?? null }),
      }),
    getApplications: (projectId: string) => request<unknown[]>(`/projects/${projectId}/applications`),
    getApprovalCodes: (projectId: string) =>
      request<PackApprovalCodes>(`/projects/${projectId}/approval-codes`),
  },

  approvals: {
    list: () => request<unknown[]>('/approvals'),
    get: (id: string) => request<unknown>(`/approvals/${id}`),
  },

  obligations: {
    list: () => request<unknown[]>('/obligations'),
    applicable: (profile: Record<string, unknown>) =>
      request<unknown[]>(`/obligations/applicable${toQuery(profile)}`, { method: 'POST' }),
  },

  applications: {
    list: (params: { status?: string; assigned_to?: string; applicant_id?: string; page?: number; page_size?: number } = {}) =>
      request<{ items: unknown[]; total: number; page: number; page_size: number }>(`/applications${toQuery(params)}`),
    get: (id: string) => request<unknown>(`/applications/${id}`),
    // approval_code is the authoritative assessment identity; approval_id
    // (approvals-table UUID) is optional — the server links the pack
    // catalog row when it is omitted.
    create: (projectId: string, approvalCode: string, approvalId?: string) =>
      request<unknown>(`/applications${toQuery({ project_id: projectId, approval_id: approvalId, approval_code: approvalCode })}`, { method: 'POST' }),
    getSla: (appId: string) =>
      request<SlaInfo | null>(`/applications/${appId}/sla`),
  },

  workflow: {
    submit: (appId: string) =>
      request<unknown>(`/applications/${appId}/submit`, { method: 'POST' }),
    advance: (appId: string) =>
      request<unknown>(`/applications/${appId}/advance`, { method: 'POST' }),
    requestInfo: (appId: string) =>
      request<unknown>(`/applications/${appId}/request-info`, { method: 'POST' }),
    respond: (appId: string) =>
      request<unknown>(`/applications/${appId}/respond`, { method: 'POST' }),
    assign: (appId: string, officerId: string) =>
      request<unknown>(`/applications/${appId}/assign${toQuery({ officer_id: officerId })}`, { method: 'POST' }),
    approve: (appId: string, reason?: string) =>
      request<unknown>(`/applications/${appId}/approve${toQuery({ reason })}`, { method: 'POST' }),
    refuse: (appId: string, reason?: string) =>
      request<unknown>(`/applications/${appId}/refuse${toQuery({ reason })}`, { method: 'POST' }),
    withdraw: (appId: string) =>
      request<unknown>(`/applications/${appId}/withdraw`, { method: 'POST' }),
  },

  documents: {
    listRequirements: (appId: string) =>
      request<DocumentRequirement[]>(`/applications/${appId}/document-requirements`),
    list: (appId: string) =>
      request<UploadedDocument[]>(`/applications/${appId}/documents`),
    upload: async (appId: string, reqKey: string, file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const { data: { session } } = await supabase.auth.getSession()
      const headers: Record<string, string> = {}
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
      }
      const res = await fetch(
        `${API_BASE}/applications/${appId}/documents/${reqKey}/upload`,
        { method: 'POST', headers, body: formData },
      )
      if (res.status === 401) {
        window.location.href = '/login'
        throw new ApiError(401, 'Unauthorized')
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }))
        throw new ApiError(res.status, body.detail ?? res.statusText)
      }
      return res.json() as Promise<UploadResult>
    },
    get: (appId: string, docId: string) =>
      request<UploadedDocument>(`/applications/${appId}/documents/${docId}`),
    delete: (appId: string, docId: string) =>
      request<{ deleted: boolean }>(`/applications/${appId}/documents/${docId}`, { method: 'DELETE' }),
    extract: (appId: string, docId: string) =>
      request<ExtractionResult>(`/applications/${appId}/documents/${docId}/extract`, { method: 'POST' }),
    validate: (appId: string, docId: string) =>
      request<ValidationResult>(`/applications/${appId}/documents/${docId}/validate`, { method: 'POST' }),
    getExtraction: (appId: string, docId: string) =>
      request<{ document_id: string; extraction: unknown; fields: unknown[] }>(
        `/applications/${appId}/documents/${docId}/extraction`,
      ),
    getValidation: (appId: string, docId: string) =>
      request<{ document_id: string; validation: unknown; findings: unknown[] }>(
        `/applications/${appId}/documents/${docId}/validation`,
      ),
    getExtractionSummary: (appId: string) =>
      request<ExtractionSummary[]>(`/applications/${appId}/extraction-summary`),
  },

  consistency: {
    check: (appId: string) =>
      request<ConsistencyResult>(`/applications/${appId}/consistency/check`, { method: 'POST' }),
    get: async (appId: string): Promise<ConsistencyResult | null> => {
      const headers = await authHeaders()
      const res = await fetch(`${API_BASE}/applications/${appId}/consistency`, { headers })
      if (res.status === 404) return null
      if (!res.ok) throw new ApiError(res.status, `Get consistency failed: ${res.status}`)
      return res.json()
    },
  },

  orchestration: {
    get: (appId: string) =>
      request<ApplicationOrchestration>(`/applications/${appId}/orchestration`),
    whatIf: (appId: string, factOverrides: Record<string, unknown>, includeUnchanged = false) =>
      request<WhatIfResponse>(`/applications/${appId}/orchestration/what-if`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fact_overrides: factOverrides, include_unchanged: includeUnchanged }),
      }),
  },

  regulatory: {
    listSources: (limit = 100, offset = 0) =>
      request<Source[]>(`/sources${toQuery({ limit, offset })}`),
    getSource: (id: string) =>
      request<{ source: Source; chunks: SourceChunk[] }>(`/sources/${id}`),
    getSourceStatus: () =>
      request<SourceStatus>('/sources/status'),
    seedSources: () =>
      request<{ sources_seeded: number; chunks_seeded: number; total_sources: number; total_chunks: number }>(
        '/sources/seed', { method: 'POST' },
      ),
    explain: (query: string, limit = 5) =>
      request<RegulatoryExplanation>('/regulatory/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit }),
      }),
    explainApproval: (approvalId: string, applicability = 'unknown', reason = '') =>
      request<RegulatoryExplanation>(
        `/regulatory/approval/${approvalId}/explanation${toQuery({ applicability, reason })}`,
      ),
    orchestrationCitations: (appId: string, approvalId: string, explanation = '') =>
      request<RegulatoryExplanation>(
        `/regulatory/orchestration/${appId}/citations${toQuery({ approval_id: approvalId, explanation })}`,
      ),
    rehearseChange: (applicationId: string, change: ChangeDescriptor) =>
      request<ImpactRehearseResponse>('/regulatory/changes/rehearse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ application_id: applicationId, change }),
      }),
  },

  incentives: {
    list: (category?: string) =>
      request<SupportScheme[]>(`/incentives${toQuery({ category })}`),
    get: (schemeId: string) =>
      request<SupportScheme>(`/incentives/${schemeId}`),
    assess: (projectFacts: Record<string, unknown>, schemeIds?: string[]) =>
      request<ProjectIncentiveAssessment>('/incentives/assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_facts: projectFacts, scheme_ids: schemeIds }),
      }),
  },

  handoffs: {
    list: (appId: string) =>
      request<HandoffListResponse>(`/applications/${appId}/handoffs`),
    initiate: (appId: string, approvalCode: string) =>
      request<HandoffRecord>(`/applications/${appId}/handoffs/initiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approval_code: approvalCode }),
      }),
    recordSubmission: (appId: string, handoffId: string, externalReference: string, note?: string) =>
      request<HandoffRecord>(`/applications/${appId}/handoffs/${handoffId}/record-submission`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ external_reference: externalReference, applicant_note: note ?? null }),
      }),
    reportStatus: (appId: string, handoffId: string, toStatus: string, note?: string) =>
      request<HandoffRecord>(`/applications/${appId}/handoffs/${handoffId}/report-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_status: toStatus, applicant_note: note ?? null }),
      }),
    verify: (appId: string, handoffId: string, verifiedStatus: string) =>
      request<HandoffRecord>(`/applications/${appId}/handoffs/${handoffId}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verified_status: verifiedStatus }),
      }),
  },
}
