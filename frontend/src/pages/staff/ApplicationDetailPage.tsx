import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import { formatDateTime } from '@/lib/format'
import { useAuth } from '@/contexts/AuthContext'
import type { WorkflowResult } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { SLACard } from '@/pages/shared/SLACard'
import { OrchestrationPanel } from '@/pages/shared/OrchestrationPanel'
import { ChangeImpactPanel } from '@/pages/shared/ChangeImpactPanel'
import { HandoffPanel } from '@/pages/shared/HandoffPanel'
import { useApplicationDetailData } from '@/pages/shared/useApplicationDetailData'
import { DetailPageHeader, DetailBottomSections } from '@/pages/shared/ApplicationDetailShared'

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
  const [actionLoading, setActionLoading] = useState('')
  const [reason, setReason] = useState('')
  const [actionError, setActionError] = useState('')
  const {
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
  } = useApplicationDetailData(id)

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
      // Re-fetch dependent data after status change
      api.applications.getSla(id).then(setSla).catch(() => {})
      api.orchestration.get(id).then(setOrchestration).catch(() => {})
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = err.message
        if (err.status === 409) setActionError(`Conflict: ${detail}`)
        else if (err.status === 403) setActionError(`Permission denied: ${detail}`)
        else if (err.status === 422) setActionError(`Validation: ${detail}`)
        else setActionError(detail)
      } else {
        setActionError(getErrorMessage(err, 'Action failed'))
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
      <DetailPageHeader
        referenceNumber={application.reference_number}
        objectId={application.id}
        approvalCode={application.approval_code}
        jurisdiction={application.jurisdiction}
        onBack={() => navigate(-1)}
      />

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

      {sla && <SLACard sla={sla} />}

      {orchestration && <OrchestrationPanel orchestration={orchestration} staffView />}

      {id && <HandoffPanel applicationId={id} staffView />}

      {id && <ChangeImpactPanel applicationId={id} />}

      {/* Application Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">Project</dt>
              <dd className="break-all font-mono text-xs">{application.project_id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Approval</dt>
              <dd className="break-all font-mono text-xs">{application.approval_id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Applicant</dt>
              <dd className="break-all font-mono text-xs">{application.applicant_id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Created</dt>
              <dd>{formatDateTime(application.created_at)}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <DetailBottomSections
        applicationId={id!}
        approvalId={application.approval_id}
        projectFacts={projectFacts}
        docRequirements={docRequirements}
        uploadedDocs={uploadedDocs}
        extractionSummary={extractionSummary}
        docLoading={docLoading}
        docError={docError}
        onRefreshDocs={refreshDocs}
        consistency={consistency}
        consistencyLoading={consistencyLoading}
        consistencyError={consistencyError}
        onRunConsistency={runConsistency}
      />
    </div>
  )
}
