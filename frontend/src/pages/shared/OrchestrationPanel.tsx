import type { ApplicationOrchestration, BlockerDetail } from '@/types/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { statusBadge } from '@/pages/shared/statusBadges'
import { Disclosure } from '@/components/shared/Disclosure'

interface OrchestrationPanelProps {
  orchestration: ApplicationOrchestration
  staffView?: boolean
}

// Machine-readable G0-R5 evidence traceability from the backend.
// Rendered only for INSUFFICIENT_DATA blockers built from evidence gaps,
// so "cannot establish applicability" stays visually distinct from other
// blocker kinds. All wording comes verbatim from the API response.
function EvidenceGapNote({ blocker }: { blocker: BlockerDetail }) {
  if (!blocker.evidence_id) return null
  return (
    <div className="mt-2 rounded border border-red-200 bg-white/60 p-2">
      <p className="text-xs font-medium text-red-800">
        Evidence <span className="font-mono">{blocker.evidence_id}</span>
        {blocker.evidence_status && (
          <span className="ml-1 rounded bg-red-100 px-1.5 py-0.5 font-mono text-[10px] text-red-700">
            {blocker.evidence_status}
          </span>
        )}
      </p>
      {blocker.unresolved_question && (
        <p className="mt-1 text-xs text-red-700">{blocker.unresolved_question}</p>
      )}
    </div>
  )
}

export function OrchestrationPanel({ orchestration, staffView = false }: OrchestrationPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{staffView ? 'Readiness / Next Action' : 'Next Steps'}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${statusBadge(orchestration.overall_status)}`}
          >
            {orchestration.overall_status.replace(/_/g, ' ')}
          </span>
          <span className="text-xs text-muted-foreground">
            {orchestration.total_blockers} blocker{orchestration.total_blockers !== 1 ? 's' : ''}
          </span>
        </div>

        <p className="text-sm text-muted-foreground">{orchestration.explanation}</p>

        {orchestration.next_action && (
          <div className="rounded-md bg-blue-50 p-3 text-sm">
            <p className="font-medium text-blue-800">Next Action</p>
            <p className="text-blue-700">{orchestration.next_action.description}</p>
            {orchestration.next_action.affected_approval_id && (
              <p className="mt-1 text-xs text-blue-600">
                Affected approval: <span className="font-mono">{orchestration.next_action.affected_approval_id}</span>
              </p>
            )}
          </div>
        )}

        {staffView ? (
          Object.entries(orchestration.approvals).length > 0 && (
            <Disclosure
              defaultOpen
              summary={`Per-Approval Summary (${Object.keys(orchestration.approvals).length})`}
            >
              <div className="mt-2 space-y-2">
                {Object.entries(orchestration.approvals).map(([key, approval]) => {
                  if (approval.status === 'not_applicable') return null
                  return (
                    <div key={key} className="rounded-md border p-3 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">{approval.approval_id}</span>
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusBadge(approval.status)}`}
                        >
                          {approval.status.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{approval.explanation}</p>
                      <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
                        <span>Documents: {approval.document_readiness}</span>
                        {approval.blockers.length > 0 && (
                          <span className="text-red-600">{approval.blockers.length} blocker{approval.blockers.length !== 1 ? 's' : ''}</span>
                        )}
                      </div>
                      {approval.blockers.filter((b) => b.evidence_id).map((b, bi) => (
                        <EvidenceGapNote key={bi} blocker={b} />
                      ))}
                    </div>
                  )
                })}
              </div>
            </Disclosure>
          )
        ) : (
          // Applicant view: one card per assessed approval. Every value is
          // rendered verbatim from the backend orchestration response —
          // applicability, readiness, reason, documents, dependencies,
          // blockers (with source/evidence), and next action all come
          // from the server. Nothing is computed here.
          Object.entries(orchestration.approvals).length > 0 && (
            <div className="space-y-2">
              {Object.entries(orchestration.approvals).map(([key, approval]) => (
                <div key={key} className="rounded-md border p-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs text-muted-foreground">{approval.approval_id}</span>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusBadge(approval.status)}`}
                    >
                      {approval.status.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      applicability: <span className="font-medium">{approval.applicability_result.replace(/_/g, ' ')}</span>
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{approval.explanation}</p>
                  <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
                    <span>Documents: {approval.document_readiness}</span>
                    <span>Dependencies: {approval.dependency_readiness}</span>
                  </div>
                  {approval.blockers.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {approval.blockers.map((blocker, idx) => (
                        <div key={idx} className="rounded-md bg-red-50 p-2 text-sm">
                          <p className="text-red-800">{blocker.description}</p>
                          {(blocker.source_ref || blocker.evidence) && (
                            <p className="mt-1 text-xs text-red-600">
                              {[blocker.source_ref, blocker.evidence].filter(Boolean).join(' — ')}
                            </p>
                          )}
                          {blocker.action_required && (
                            <p className="mt-1 text-xs text-red-600">{blocker.action_required}</p>
                          )}
                          <EvidenceGapNote blocker={blocker} />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )
        )}
      </CardContent>
    </Card>
  )
}
