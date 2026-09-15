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
    create: (name: string, description?: string, applicantId?: string) =>
      request<unknown>(`/projects${toQuery({ name, description, applicant_id: applicantId })}`, { method: 'POST' }),
    getFacts: (projectId: string) => request<unknown>(`/projects/${projectId}/facts`),
    upsertFacts: (projectId: string, facts: Record<string, unknown>) =>
      request<unknown>(`/projects/${projectId}/facts${toQuery(facts)}`, { method: 'POST' }),
    getApplications: (projectId: string) => request<unknown[]>(`/projects/${projectId}/applications`),
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
    create: (projectId: string, approvalId: string) =>
      request<unknown>(`/applications${toQuery({ project_id: projectId, approval_id: approvalId })}`, { method: 'POST' }),
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
}
