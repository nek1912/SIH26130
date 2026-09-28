import type { ApprovalDiff } from '@/types/api'
import { statusBadge } from '@/pages/shared/statusBadges'

export function ApprovalDiffList({ diffs }: { diffs: ApprovalDiff[] }) {
  return (
    <div className="space-y-2">
      {diffs.map((c) => (
        <div key={c.approval_id} className="rounded-md border p-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-muted-foreground">{c.approval_id}</span>
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusBadge(c.whatif_status)}`}>
              {c.baseline_status.replace(/_/g, ' ')} → {c.whatif_status.replace(/_/g, ' ')}
            </span>
          </div>
          {c.baseline_applicability !== c.whatif_applicability && (
            <p className="mt-1 text-xs text-muted-foreground">
              Applicability: {c.baseline_applicability} → {c.whatif_applicability}
            </p>
          )}
          {c.baseline_dependency !== c.whatif_dependency && (
            <p className="mt-1 text-xs text-muted-foreground">
              Dependencies: {c.baseline_dependency} → {c.whatif_dependency}
            </p>
          )}
          {c.added_blockers.length > 0 && (
            <div className="mt-1 space-y-1">
              {c.added_blockers.map((b, i) => (
                <p key={i} className="text-xs text-red-700">+ {b.description}</p>
              ))}
            </div>
          )}
          {c.removed_blockers.length > 0 && (
            <div className="mt-1 space-y-1">
              {c.removed_blockers.map((b, i) => (
                <p key={i} className="text-xs text-green-700">− {b.description}</p>
              ))}
            </div>
          )}
          <p className="mt-1 text-xs text-muted-foreground">{c.whatif_explanation}</p>
        </div>
      ))}
    </div>
  )
}
