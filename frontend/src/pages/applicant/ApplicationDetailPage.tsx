import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/lib/api'
import type { Application, WorkflowResult, DocumentRequirement, UploadedDocument, ExtractionSummary, ConsistencyResult, SlaInfo } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

// Ordered workflow stages for timeline display
const STAGE_ORDER = [
  { key: 'draft', label: 'Draft' },
  { key: 'submitted', label: 'Submitted' },
  { key: 'under_review', label: 'Under Review' },
  { key: 'returned', label: 'Returned for Info' },
  { key: 'incomplete', label: 'Incomplete' },
  { key: 'awaiting_inspection', label: 'Inspection' },
  { key: 'awaiting_consultation', label: 'Consultation' },
  { key: 'awaiting_hearing', label: 'Hearing' },
  { key: 'awaiting_documents', label: 'Documents' },
  { key: 'awaiting_payment', label: 'Payment' },
  { key: 'approved', label: 'Approved' },
  { key: 'refused', label: 'Refused' },
]

function getStageIndex(status: string): number {
  const idx = STAGE_ORDER.findIndex((s) => s.key === status)
  return idx >= 0 ? idx : 0
}

const STATUS_ACTIONS: Record<string, { key: string; label: string; variant: 'default' | 'destructive' }[]> = {
  draft: [{ key: 'submit', label: 'Submit Application', variant: 'default' }],
  returned: [{ key: 'respond', label: 'Respond to Query', variant: 'default' }],
  incomplete: [{ key: 'respond', label: 'Respond to Query', variant: 'default' }],
}

const WITHDRAW_STATUSES = new Set(['submitted', 'under_review', 'awaiting_inspection', 'awaiting_consultation', 'awaiting_hearing'])

export function ApplicantApplicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [application, setApplication] = useState<Application | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState('')
  const [actionError, setActionError] = useState('')
  const [docRequirements, setDocRequirements] = useState<DocumentRequirement[]>([])
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
  const [extractionSummary, setExtractionSummary] = useState<ExtractionSummary[]>([])
  const [docLoading, setDocLoading] = useState(false)
  const [docError, setDocError] = useState('')
  const [uploadingKey, setUploadingKey] = useState('')
  const [extractingDocId, setExtractingDocId] = useState('')
  const [validatingDocId, setValidatingDocId] = useState('')
  const [consistency, setConsistency] = useState<ConsistencyResult | null>(null)
  const [consistencyLoading, setConsistencyLoading] = useState(false)
  const [sla, setSla] = useState<SlaInfo | null>(null)

  useEffect(() => {
    if (!id) return
    api.applications
      .get(id)
      .then((data) => setApplication(data as Application))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
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
      .catch((err) => setDocError(err.message))
      .finally(() => setDocLoading(false))
  }, [id])

  useEffect(() => {
    if (!id) return
    api.consistency.get(id).then(setConsistency).catch(() => {})
  }, [id])

  useEffect(() => {
    if (!id) return
    api.applications.getSla(id).then(setSla).catch(() => {})
  }, [id])

  const handleRunConsistency = async () => {
    if (!id) return
    setConsistencyLoading(true)
    try {
      const result = await api.consistency.check(id)
      setConsistency(result)
    } catch (err) {
      console.error('Consistency check failed', err)
    } finally {
      setConsistencyLoading(false)
    }
  }

  const handleUpload = async (reqKey: string, file: File) => {
    if (!id) return
    setUploadingKey(reqKey)
    setDocError('')
    try {
      const result = await api.documents.upload(id, reqKey, file)
      setUploadedDocs((prev) => {
        const filtered = prev.filter((d) => d.requirement_key !== reqKey)
        return [result.document, ...filtered]
      })
      setDocRequirements((prev) =>
        prev.map((r) => (r.requirement_key === reqKey ? result.requirement : r)),
      )
    } catch (err) {
      if (err instanceof ApiError) setDocError(err.message)
      else setDocError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploadingKey('')
    }
  }

  const handleDeleteDoc = async (docId: string, reqKey: string) => {
    if (!id) return
    try {
      await api.documents.delete(id, docId)
      setUploadedDocs((prev) => prev.filter((d) => d.id !== docId))
      setDocRequirements((prev) =>
        prev.map((r) =>
          r.requirement_key === reqKey
            ? { ...r, readiness: 'pending' as const, uploaded_document_id: null }
            : r,
        ),
      )
    } catch (err) {
      if (err instanceof ApiError) setDocError(err.message)
      else setDocError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  const handleExtract = async (docId: string) => {
    if (!id) return
    setExtractingDocId(docId)
    setDocError('')
    try {
      await api.documents.extract(id, docId)
      // Refresh extraction summary
      const summary = await api.documents.getExtractionSummary(id)
      setExtractionSummary(summary as ExtractionSummary[])
    } catch (err) {
      if (err instanceof ApiError) setDocError(err.message)
      else setDocError(err instanceof Error ? err.message : 'Extraction failed')
    } finally {
      setExtractingDocId('')
    }
  }

  const handleValidate = async (docId: string) => {
    if (!id) return
    setValidatingDocId(docId)
    setDocError('')
    try {
      await api.documents.validate(id, docId)
      // Refresh extraction summary
      const summary = await api.documents.getExtractionSummary(id)
      setExtractionSummary(summary as ExtractionSummary[])
    } catch (err) {
      if (err instanceof ApiError) setDocError(err.message)
      else setDocError(err instanceof Error ? err.message : 'Validation failed')
    } finally {
      setValidatingDocId('')
    }
  }

  const handleAction = async (actionKey: string) => {
    if (!id) return
    setActionLoading(actionKey)
    setActionError('')
    try {
      let result: WorkflowResult
      if (actionKey === 'submit') result = await api.workflow.submit(id) as WorkflowResult
      else if (actionKey === 'respond') result = await api.workflow.respond(id) as WorkflowResult
      else if (actionKey === 'withdraw') result = await api.workflow.withdraw(id) as WorkflowResult
      else return
      setApplication((prev) =>
        prev ? { ...prev, status: result.new_status, current_stage: result.current_stage } : prev,
      )
    } catch (err) {
      if (err instanceof ApiError) setActionError(err.message)
      else setActionError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setActionLoading('')
    }
  }

  if (loading) return <LoadingSpinner className="mt-12" />
  if (error && !application) return <div className="mt-12 text-center text-destructive">{error}</div>
  if (!application) return <div className="mt-12 text-center text-muted-foreground">Application not found</div>

  const currentIdx = getStageIndex(application.status)
  const isTerminal = application.status === 'approved' || application.status === 'refused' || application.status === 'withdrawn' || application.status === 'cancelled'
  const actions = STATUS_ACTIONS[application.status] ?? []
  const canWithdraw = WITHDRAW_STATUSES.has(application.status)

  // Determine next action hint
  let nextActionHint = ''
  if (application.status === 'draft') nextActionHint = 'Submit your application to begin the review process.'
  else if (application.status === 'submitted') nextActionHint = 'Your application is queued for review.'
  else if (application.status === 'under_review') nextActionHint = 'Your application is being reviewed by an officer.'
  else if (application.status === 'returned') nextActionHint = 'Additional information has been requested. Please respond.'
  else if (application.status === 'incomplete') nextActionHint = 'Your application is incomplete. Please respond with the required information.'
  else if (application.status === 'approved') nextActionHint = 'Your application has been approved!'
  else if (application.status === 'refused') nextActionHint = 'Your application has been refused.'
  else if (application.status === 'withdrawn') nextActionHint = 'You have withdrawn this application.'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Application {application.reference_number}</h1>
          <p className="font-mono text-xs text-muted-foreground">{application.id}</p>
        </div>
        <Button variant="outline" onClick={() => navigate(-1)}>Back</Button>
      </div>

      {actionError && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{actionError}</div>
      )}

      {/* Status Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Application Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
            <div className="space-y-4">
              {STAGE_ORDER.map((stage, idx) => {
                const isCurrent = stage.key === application.status
                const isPast = idx < currentIdx && !isTerminal
                const isCompleted = isPast || (isTerminal && idx <= currentIdx)
                const isFailedTerminal = isTerminal && (application.status === 'refused' || application.status === 'cancelled') && idx === currentIdx

                return (
                  <div key={stage.key} className="relative flex items-center gap-4 pl-10">
                    <div
                      className={`absolute left-2.5 h-3 w-3 rounded-full border-2 ${
                        isCurrent
                          ? 'border-primary bg-primary'
                          : isFailedTerminal
                            ? 'border-destructive bg-destructive'
                            : isCompleted
                              ? 'border-primary bg-primary/20'
                              : 'border-border bg-background'
                      }`}
                    />
                    <div>
                      <p className={`text-sm font-medium ${isCurrent ? 'text-foreground' : 'text-muted-foreground'}`}>
                        {stage.label}
                      </p>
                      {isCurrent && (
                        <StatusBadge status={application.status} />
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Next Action / Hint */}
      {nextActionHint && (
        <Card>
          <CardContent className="py-4">
            <p className="text-sm">{nextActionHint}</p>
          </CardContent>
        </Card>
      )}

      {/* SLA Status */}
      {sla && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">SLA Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div>
                <p className="text-sm font-medium">{sla.stage_label}</p>
                <p className="text-xs text-muted-foreground">
                  Target: {sla.sla_business_days} business days
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm">
                  Due: {new Date(sla.due_date).toLocaleDateString()}
                </p>
                <p className="text-xs text-muted-foreground">
                  {sla.remaining_business_days > 0
                    ? `${sla.remaining_business_days} days remaining`
                    : `${sla.overdue_business_days} days overdue`}
                </p>
              </div>
              <span
                className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                  sla.state === 'on_track'
                    ? 'bg-green-100 text-green-800'
                    : sla.state === 'due_soon' || sla.state === 'due_today'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                }`}
              >
                {sla.state === 'on_track'
                  ? 'On Track'
                  : sla.state === 'due_soon'
                    ? 'Due Soon'
                    : sla.state === 'due_today'
                      ? 'Due Today'
                      : 'Breached'}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      {!isTerminal && (actions.length > 0 || canWithdraw) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {actions.map((action) => (
                <Button
                  key={action.key}
                  variant={action.variant}
                  size="sm"
                  onClick={() => handleAction(action.key)}
                  disabled={actionLoading === action.key}
                >
                  {actionLoading === action.key ? 'Processing...' : action.label}
                </Button>
              ))}
              {canWithdraw && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleAction('withdraw')}
                  disabled={actionLoading === 'withdraw'}
                >
                  {actionLoading === 'withdraw' ? 'Processing...' : 'Withdraw Application'}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Created</dt>
              <dd>{new Date(application.created_at).toLocaleString()}</dd>
            </div>
            {application.current_stage && (
              <div>
                <dt className="text-muted-foreground">Current Stage</dt>
                <dd className="font-medium">{application.current_stage}</dd>
              </div>
            )}
            {application.assigned_officer_id && (
              <div>
                <dt className="text-muted-foreground">Assigned Officer</dt>
                <dd className="font-mono text-xs">{application.assigned_officer_id}</dd>
              </div>
            )}
            {application.decision_outcome && (
              <div>
                <dt className="text-muted-foreground">Decision</dt>
                <dd className="font-medium capitalize">{application.decision_outcome}</dd>
              </div>
            )}
            {application.decision_reason && (
              <div>
                <dt className="text-muted-foreground">Reason</dt>
                <dd>{application.decision_reason}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Document Checklist */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Document Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          {docLoading ? (
            <LoadingSpinner className="py-4" />
          ) : docError ? (
            <div className="text-sm text-destructive">{docError}</div>
          ) : docRequirements.length === 0 ? (
            <p className="text-sm text-muted-foreground">No document requirements for this application.</p>
          ) : (
            <div className="space-y-3">
              {docRequirements.map((req) => {
                const uploaded = uploadedDocs.find((d) => d.requirement_key === req.requirement_key)
                const summary = extractionSummary.find((s) => s.requirement_key === req.requirement_key)
                const extractionStatus = summary?.extraction_status
                const validationOutcome = summary?.validation_outcome
                return (
                  <div
                    key={req.requirement_key}
                    className="rounded-md border p-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-muted-foreground">{req.requirement_key}</span>
                          <span className="text-sm font-medium truncate">{req.document_name}</span>
                          <span
                            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                              req.requirement_level === 'mandatory'
                                ? 'bg-red-100 text-red-800'
                                : req.requirement_level === 'conditional'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-blue-100 text-blue-800'
                            }`}
                          >
                            {req.requirement_level}
                          </span>
                          <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                            {req.domain}
                          </span>
                        </div>
                        {uploaded ? (
                          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{uploaded.original_filename}</span>
                            <span>({(uploaded.file_size_bytes / 1024).toFixed(1)} KB)</span>
                            <StatusBadge status={uploaded.status === 'verified' ? 'approved' : uploaded.status === 'rejected' ? 'refused' : 'submitted'} />
                          </div>
                        ) : (
                          <p className="mt-1 text-xs text-muted-foreground">Not uploaded</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        {uploaded ? (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleExtract(uploaded.id)}
                              disabled={extractingDocId === uploaded.id}
                            >
                              {extractingDocId === uploaded.id ? 'Extracting...' : 'Extract'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleValidate(uploaded.id)}
                              disabled={validatingDocId === uploaded.id}
                            >
                              {validatingDocId === uploaded.id ? 'Validating...' : 'Validate'}
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDeleteDoc(uploaded.id, req.requirement_key)}
                            >
                              Remove
                            </Button>
                          </>
                        ) : (
                          <label className="cursor-pointer">
                            <input
                              type="file"
                              className="hidden"
                              accept={req.accepted_mime_types?.join(',')}
                              onChange={(e) => {
                                const file = e.target.files?.[0]
                                if (file) handleUpload(req.requirement_key, file)
                              }}
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={uploadingKey === req.requirement_key}
                              asChild
                            >
                              <span>
                                {uploadingKey === req.requirement_key ? 'Uploading...' : 'Upload'}
                              </span>
                            </Button>
                          </label>
                        )}
                      </div>
                    </div>

                    {/* Extraction/Validation Status */}
                    {(extractionStatus || validationOutcome) && (
                      <div className="mt-2 flex items-center gap-3 text-xs">
                        {extractionStatus && (
                          <span
                            className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
                              extractionStatus === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : extractionStatus === 'failed'
                                  ? 'bg-red-100 text-red-800'
                                  : extractionStatus === 'unsupported'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            Extraction: {extractionStatus}
                          </span>
                        )}
                        {validationOutcome && (
                          <span
                            className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
                              validationOutcome === 'VALID'
                                ? 'bg-green-100 text-green-800'
                                : validationOutcome === 'INVALID'
                                  ? 'bg-red-100 text-red-800'
                                  : validationOutcome === 'REVIEW_REQUIRED'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            Validation: {validationOutcome}
                          </span>
                        )}
                        {summary?.finding_count ? (
                          <span className="text-muted-foreground">
                            {summary.finding_count} finding{summary.finding_count !== 1 ? 's' : ''}
                          </span>
                        ) : null}
                      </div>
                    )}

                    {/* Validation Findings */}
                    {summary?.findings && summary.findings.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {summary.findings.map((finding, idx) => (
                          <div
                            key={idx}
                            className={`text-xs p-2 rounded ${
                              finding.outcome === 'VALID'
                                ? 'bg-green-50 text-green-700'
                                : finding.outcome === 'INVALID'
                                  ? 'bg-red-50 text-red-700'
                                  : finding.outcome === 'REVIEW_REQUIRED'
                                    ? 'bg-yellow-50 text-yellow-700'
                                    : 'bg-gray-50 text-gray-700'
                            }`}
                          >
                            <span className="font-medium">{finding.rule_id}:</span> {finding.message}
                            {finding.source_ref && (
                              <span className="ml-1 text-muted-foreground">({finding.source_ref})</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cross-Document Consistency */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Cross-Document Consistency</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRunConsistency}
              disabled={consistencyLoading}
            >
              {consistencyLoading ? 'Checking...' : 'Run Check'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {consistency ? (
            <div>
              <div className="mb-3 flex items-center gap-2">
                <span
                  className={`inline-block rounded px-2 py-1 text-xs font-medium ${
                    consistency.outcome === 'VALID'
                      ? 'bg-green-100 text-green-800'
                      : consistency.outcome === 'REVIEW_REQUIRED'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {consistency.outcome}
                </span>
                <span className="text-xs text-muted-foreground">
                  Checked: {new Date(consistency.checked_at).toLocaleString()}
                </span>
              </div>

              {consistency.findings.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="py-1 text-left">Rule</th>
                      <th className="py-1 text-left">Field</th>
                      <th className="py-1 text-left">Status</th>
                      <th className="py-1 text-left">Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {consistency.findings.map((f) => (
                      <tr key={f.rule_id} className="border-b">
                        <td className="py-1">{f.rule_id}</td>
                        <td className="py-1">{f.canonical_field}</td>
                        <td className="py-1">
                          <span
                            className={`inline-block rounded px-1.5 py-0.5 text-xs ${
                              f.outcome === 'VALID'
                                ? 'bg-green-50 text-green-700'
                                : f.outcome === 'REVIEW_REQUIRED'
                                  ? 'bg-yellow-50 text-yellow-700'
                                  : 'bg-gray-50 text-gray-700'
                            }`}
                          >
                            {f.outcome}
                          </span>
                        </td>
                        <td className="py-1 text-muted-foreground">{f.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-sm text-muted-foreground">No findings.</p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No consistency check performed yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
