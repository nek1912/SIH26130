import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { Application, WorkflowResult, ConsistencyResult } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

interface WorkflowAction {
  key: string
  label: string
  apiCall: (id: string, reason?: string) => Promise<unknown>
  variant: 'default' | 'destructive' | 'outline'
  needsRole?: string
}

const WORKFLOW_ACTIONS: WorkflowAction[] = [
  { key: 'submit', label: 'Submit', apiCall: (id) => api.workflow.submit(id), variant: 'default' },
  { key: 'advance', label: 'Advance Review', apiCall: (id) => api.workflow.advance(id), variant: 'outline', needsRole: 'REVIEWER' },
  { key: 'request-info', label: 'Request Info', apiCall: (id) => api.workflow.requestInfo(id), variant: 'outline', needsRole: 'REVIEWER' },
  { key: 'respond', label: 'Respond to Query', apiCall: (id) => api.workflow.respond(id), variant: 'default' },
  { key: 'approve', label: 'Approve', apiCall: (id, r) => api.workflow.approve(id, r), variant: 'default', needsRole: 'MANAGER' },
  { key: 'refuse', label: 'Refuse', apiCall: (id, r) => api.workflow.refuse(id, r), variant: 'destructive', needsRole: 'MANAGER' },
  { key: 'withdraw', label: 'Withdraw', apiCall: (id) => api.workflow.withdraw(id), variant: 'destructive' },
]

// Maps current status → available action keys (matches backend TRANSITION_RULES)
const STATUS_TRANSITIONS: Record<string, string[]> = {
  draft: ['submit', 'withdraw'],
  submitted: ['advance'],
  under_review: ['advance', 'request-info', 'approve', 'refuse'],
  returned: ['respond', 'withdraw'],
  incomplete: ['respond', 'withdraw'],
  awaiting_inspection: ['advance', 'withdraw'],
  awaiting_consultation: ['advance', 'withdraw'],
  awaiting_hearing: ['advance', 'withdraw'],
  awaiting_documents: ['respond', 'withdraw'],
  awaiting_payment: ['respond', 'withdraw'],
}

const REASON_ACTIONS = new Set(['approve', 'refuse', 'request-info'])

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { role } = useAuth()
  const navigate = useNavigate()
  const [application, setApplication] = useState<Application | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState('')
  const [reason, setReason] = useState('')
  const [actionError, setActionError] = useState('')
  const [consistency, setConsistency] = useState<ConsistencyResult | null>(null)
  const [consistencyLoading, setConsistencyLoading] = useState(false)

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
    api.consistency.get(id).then(setConsistency).catch(() => {})
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

  const handleAction = async (action: WorkflowAction) => {
    if (!id) return
    setActionLoading(action.key)
    setActionError('')
    try {
      const result = await action.apiCall(id, reason || undefined) as WorkflowResult
      setApplication((prev) =>
        prev ? { ...prev, status: result.new_status, current_stage: result.current_stage } : prev,
      )
      setReason('')
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = err.message
        if (err.status === 409) setActionError(`Conflict: ${detail}`)
        else if (err.status === 403) setActionError(`Permission denied: ${detail}`)
        else if (err.status === 422) setActionError(`Validation: ${detail}`)
        else setActionError(detail)
      } else {
        setActionError(err instanceof Error ? err.message : 'Action failed')
      }
    } finally {
      setActionLoading('')
    }
  }

  if (loading) return <LoadingSpinner className="mt-12" />
  if (error && !application) return <div className="mt-12 text-center text-destructive">{error}</div>
  if (!application) return <div className="mt-12 text-center text-muted-foreground">Application not found</div>

  const availableActionKeys = STATUS_TRANSITIONS[application.status] ?? []
  const availableActions = WORKFLOW_ACTIONS.filter((a) => {
    if (!availableActionKeys.includes(a.key)) return false
    if (a.needsRole && role !== a.needsRole && role !== 'ADMIN') return false
    return true
  })
  const needsReason = availableActions.some((a) => REASON_ACTIONS.has(a.key))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Application {application.reference_number}</h1>
          <p className="font-mono text-xs text-muted-foreground">{application.id}</p>
        </div>
        <Button variant="outline" onClick={() => navigate(-1)}>Back</Button>
      </div>

      {(error || actionError) && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {actionError || error}
        </div>
      )}

      {/* Status and Actions */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Current Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2">
              <StatusBadge status={application.status} />
            </div>
            {application.current_stage && (
              <div className="text-sm">
                <span className="text-muted-foreground">Workflow Stage: </span>
                <span className="font-medium">{application.current_stage}</span>
              </div>
            )}
            {application.assigned_officer_id && (
              <div className="text-sm">
                <span className="text-muted-foreground">Assigned Officer: </span>
                <span className="font-mono text-xs">{application.assigned_officer_id}</span>
              </div>
            )}
            {application.decision_outcome && (
              <div className="text-sm">
                <span className="text-muted-foreground">Decision: </span>
                <span className="font-medium capitalize">{application.decision_outcome}</span>
              </div>
            )}
            {application.decision_reason && (
              <div className="text-sm">
                <span className="text-muted-foreground">Reason: </span>
                {application.decision_reason}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Available Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {availableActions.length === 0 ? (
              <p className="text-sm text-muted-foreground">No actions available for current status.</p>
            ) : (
              <>
                {needsReason && (
                  <div className="space-y-1">
                    <Label htmlFor="reason">Reason {REASON_ACTIONS.has(availableActions[0]?.key) ? '(required for approve/refuse)' : ''}</Label>
                    <Input
                      id="reason"
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="Optional reason or notes"
                    />
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  {availableActions.map((action) => (
                    <Button
                      key={action.key}
                      variant={action.variant}
                      size="sm"
                      onClick={() => handleAction(action)}
                      disabled={actionLoading === action.key}
                    >
                      {actionLoading === action.key ? 'Processing...' : action.label}
                    </Button>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Application Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Project</dt>
              <dd className="font-mono text-xs">{application.project_id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Approval</dt>
              <dd className="font-mono text-xs">{application.approval_id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Applicant</dt>
              <dd className="font-mono text-xs">{application.applicant_id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Created</dt>
              <dd>{new Date(application.created_at).toLocaleString()}</dd>
            </div>
          </dl>
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
