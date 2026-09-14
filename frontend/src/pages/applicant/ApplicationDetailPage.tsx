import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/lib/api'
import type { Application, WorkflowResult } from '@/types/api'
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

  useEffect(() => {
    if (!id) return
    api.applications
      .get(id)
      .then((data) => setApplication(data as Application))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

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
    </div>
  )
}
