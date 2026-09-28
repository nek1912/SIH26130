import { useState } from 'react'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type { Citation, RegulatoryExplanation } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface RegulatoryAssistantProps {
  approvalId?: string
  applicationId?: string // reserved for future context-aware queries
}

export function RegulatoryAssistant({ approvalId, applicationId: _applicationId }: RegulatoryAssistantProps) {
  const [query, setQuery] = useState('')
  const [explanation, setExplanation] = useState<RegulatoryExplanation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    setExplanation(null)
    try {
      const result = await api.regulatory.explain(query.trim())
      setExplanation(result)
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Query failed'))
    } finally {
      setLoading(false)
    }
  }

  const handleExplainApproval = async () => {
    if (!approvalId) return
    setLoading(true)
    setError('')
    setExplanation(null)
    try {
      const result = await api.regulatory.explainApproval(approvalId)
      setExplanation(result)
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Explanation failed'))
    } finally {
      setLoading(false)
    }
  }

  const evidenceColor = (state: string) => {
    if (state === 'sufficient') return 'bg-green-50 text-green-700 border-green-200'
    if (state === 'partial') return 'bg-yellow-50 text-yellow-700 border-yellow-200'
    return 'bg-gray-50 text-gray-700 border-gray-200'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Regulatory Assistant</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Ask a regulatory question..."
            className="flex-1 rounded-md border px-3 py-1.5 text-sm"
          />
          <Button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            variant="default"
            className="text-sm"
          >
            {loading ? 'Searching...' : 'Search'}
          </Button>
          {approvalId && (
            <Button
              onClick={handleExplainApproval}
              disabled={loading}
              variant="outline"
              className="text-sm"
            >
              Explain Approval
            </Button>
          )}
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {explanation && (
          <div className="space-y-3">
            <div className="rounded border border-gray-200 bg-gray-50 p-3 text-sm">
              {explanation.answer}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">Evidence:</span>
              <span
                className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${evidenceColor(explanation.evidence_state)}`}
              >
                {explanation.evidence_state}
              </span>
            </div>

            {explanation.citations.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-medium text-muted-foreground">
                  Sources ({explanation.citations.length}):
                </span>
                {explanation.citations.map((c: Citation) => (
                  <div
                    key={c.source_id}
                    className="rounded border border-gray-200 p-2 text-xs"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="font-medium">{c.title}</span>
                        <span className="ml-2 text-muted-foreground">
                          ({c.authority})
                        </span>
                      </div>
                      <a
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="shrink-0 text-blue-600 underline hover:text-blue-800"
                      >
                        link
                      </a>
                    </div>
                    {c.excerpt && (
                      <p className="mt-1 text-muted-foreground">{c.excerpt}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {explanation.citations.length === 0 && (
              <p className="text-xs text-muted-foreground">
                No sources found in the regulatory dataset.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
