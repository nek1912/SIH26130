import { useCallback, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type {
  Application,
  ConsistencyResult,
  DocumentRequirement,
  UploadedDocument,
  ExtractionSummary,
  SlaInfo,
  ApplicationOrchestration,
} from '@/types/api'

export interface ApplicationDetailData {
  application: Application | null
  setApplication: React.Dispatch<React.SetStateAction<Application | null>>
  loading: boolean
  error: string
  docRequirements: DocumentRequirement[]
  uploadedDocs: UploadedDocument[]
  extractionSummary: ExtractionSummary[]
  docLoading: boolean
  docError: string
  refreshDocs: () => void
  consistency: ConsistencyResult | null
  consistencyLoading: boolean
  consistencyError: string
  runConsistency: () => Promise<void>
  sla: SlaInfo | null
  setSla: React.Dispatch<React.SetStateAction<SlaInfo | null>>
  orchestration: ApplicationOrchestration | null
  setOrchestration: React.Dispatch<React.SetStateAction<ApplicationOrchestration | null>>
  projectFacts: Record<string, unknown> | null
}

// Shared data flow for applicant + staff application detail pages.
// Mirrors the exact fetch behavior previously duplicated in both pages:
// application get, parallel document refresh, independent consistency/SLA/
// orchestration gets, and project-facts lookup keyed on application.project_id.
// Role-specific state (timeline, reason/actions, navigation) stays in the pages.
export function useApplicationDetailData(id: string | undefined): ApplicationDetailData {
  const [application, setApplication] = useState<Application | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [docRequirements, setDocRequirements] = useState<DocumentRequirement[]>([])
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
  const [extractionSummary, setExtractionSummary] = useState<ExtractionSummary[]>([])
  const [docLoading, setDocLoading] = useState(false)
  const [docError, setDocError] = useState('')
  const [consistency, setConsistency] = useState<ConsistencyResult | null>(null)
  const [consistencyLoading, setConsistencyLoading] = useState(false)
  const [consistencyError, setConsistencyError] = useState('')
  const [sla, setSla] = useState<SlaInfo | null>(null)
  const [orchestration, setOrchestration] = useState<ApplicationOrchestration | null>(null)
  const [projectFacts, setProjectFacts] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    if (!id) return
    api.applications
      .get(id)
      .then((data) => setApplication(data as Application))
      .catch((err) => setError(getErrorMessage(err, 'Failed to load application')))
      .finally(() => setLoading(false))
  }, [id])

  const refreshDocs = useCallback(() => {
    if (!id) return
    setDocLoading(true)
    Promise.all([
      api.documents.listRequirements(id),
      api.documents.list(id),
      api.documents.getExtractionSummary(id),
    ])
      .then(([reqs, docs, summary]) => {
        setDocRequirements(reqs as DocumentRequirement[])
        setUploadedDocs(docs as UploadedDocument[])
        setExtractionSummary(summary as ExtractionSummary[])
      })
      .catch((err) => setDocError(getErrorMessage(err, 'Failed to load documents')))
      .finally(() => setDocLoading(false))
  }, [id])

  useEffect(() => { if (id) refreshDocs() }, [id, refreshDocs])

  useEffect(() => {
    if (!id) return
    api.consistency.get(id).then(setConsistency).catch(() => {})
  }, [id])

  useEffect(() => {
    if (!id) return
    api.applications.getSla(id).then(setSla).catch(() => {})
  }, [id])

  useEffect(() => {
    if (!id) return
    api.orchestration.get(id).then(setOrchestration).catch(() => {})
  }, [id])

  useEffect(() => {
    if (!application?.project_id) return
    api.projects
      .getFacts(application.project_id)
      .then((data) => setProjectFacts(data as Record<string, unknown>))
      .catch(() => {})
  }, [application?.project_id])

  const runConsistency = useCallback(async () => {
    if (!id) return
    setConsistencyLoading(true)
    setConsistencyError('')
    try {
      const result = await api.consistency.check(id)
      setConsistency(result)
    } catch (err) {
      setConsistencyError(getErrorMessage(err, 'Consistency check failed'))
    } finally {
      setConsistencyLoading(false)
    }
  }, [id])

  return {
    application,
    setApplication,
    loading,
    error,
    docRequirements,
    uploadedDocs,
    extractionSummary,
    docLoading,
    docError,
    refreshDocs,
    consistency,
    consistencyLoading,
    consistencyError,
    runConsistency,
    sla,
    setSla,
    orchestration,
    setOrchestration,
    projectFacts,
  }
}
