import type { ConsistencyResult } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { badgeVariantClasses } from '@/components/ui/badgeVariants'
import { formatDateTime } from '@/lib/format'

interface ConsistencyPanelProps {
  consistency: ConsistencyResult | null
  loading: boolean
  error?: string
  onRunCheck: () => void
}

const OUTCOME_VARIANT: Record<string, 'ready' | 'review' | 'neutral'> = {
  VALID: 'ready',
  REVIEW_REQUIRED: 'review',
}

const FINDING_VARIANT: Record<string, 'readySoft' | 'reviewSoft' | 'neutralSoft'> = {
  VALID: 'readySoft',
  REVIEW_REQUIRED: 'reviewSoft',
}

export function ConsistencyPanel({ consistency, loading, error, onRunCheck }: ConsistencyPanelProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Cross-Document Consistency</CardTitle>
          <Button variant="outline" size="sm" onClick={onRunCheck} disabled={loading}>
            {loading ? 'Checking...' : 'Run Check'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-3 rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
        )}
        {consistency ? (
          <div>
            <div className="mb-3 flex items-center gap-2">
              <span
                className={`inline-block rounded px-2 py-1 text-xs font-medium ${badgeVariantClasses[OUTCOME_VARIANT[consistency.outcome] ?? 'neutral']}`}
              >
                {consistency.outcome}
              </span>
              <span className="text-xs text-muted-foreground">
                Checked: {formatDateTime(consistency.checked_at)}
              </span>
            </div>

            {consistency.findings.length > 0 ? (
              <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <caption className="sr-only">Cross-document consistency findings</caption>
                <thead>
                  <tr className="border-b">
                    <th scope="col" className="py-1 text-left">Rule</th>
                    <th scope="col" className="py-1 text-left">Field</th>
                    <th scope="col" className="py-1 text-left">Status</th>
                    <th scope="col" className="py-1 text-left">Message</th>
                  </tr>
                </thead>
                <tbody>
                  {consistency.findings.map((f) => (
                    <tr key={f.rule_id} className="border-b">
                      <td scope="row" className="py-1 font-mono">{f.rule_id}</td>
                      <td className="py-1">{f.canonical_field}</td>
                      <td className="py-1">
                        <span
                          className={`inline-block rounded px-1.5 py-0.5 text-xs ${badgeVariantClasses[FINDING_VARIANT[f.outcome] ?? 'neutralSoft']}`}
                        >
                          {f.outcome}
                        </span>
                      </td>
                      <td className="py-1 text-muted-foreground">{f.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No findings.</p>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No consistency check performed yet.</p>
        )}
      </CardContent>
    </Card>
  )
}
