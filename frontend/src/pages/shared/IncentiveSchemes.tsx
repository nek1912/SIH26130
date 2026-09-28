import { useState } from 'react'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type { ProjectIncentiveAssessment, SchemeRelevance } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { badgeVariantClasses } from '@/components/ui/badgeVariants'

interface IncentiveSchemesProps {
  projectFacts: Record<string, unknown>
}

const RELEVANCE_COLORS: Record<string, string> = {
  potentially_relevant: badgeVariantClasses.ready,
  conditional: badgeVariantClasses.review,
  insufficient_data: badgeVariantClasses.neutral,
  not_relevant: badgeVariantClasses.blocked,
}

const RELEVANCE_LABELS: Record<string, string> = {
  potentially_relevant: 'Potentially Relevant',
  conditional: 'Conditional',
  insufficient_data: 'Insufficient Data',
  not_relevant: 'Not Relevant',
}

function AssessmentRow({ assessment }: { assessment: SchemeRelevance }) {
  return (
    <div className="rounded-md border p-3">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">
              {assessment.scheme_name}
            </span>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                RELEVANCE_COLORS[assessment.relevance] ?? badgeVariantClasses.neutral
              }`}
            >
              {RELEVANCE_LABELS[assessment.relevance] ?? assessment.relevance}
            </span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {assessment.reason}
          </p>
          {assessment.missing_info.length > 0 && (
            <p className="mt-1 text-xs text-yellow-600">
              Missing: {assessment.missing_info.join(', ')}
            </p>
          )}
        </div>
      </div>
      {assessment.source_refs.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {assessment.source_refs.map((ref) => (
            <span
              key={ref.source_id}
              className="inline-block rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700"
            >
              {ref.source_id}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function IncentiveSchemes({ projectFacts }: IncentiveSchemesProps) {
  const [assessment, setAssessment] = useState<ProjectIncentiveAssessment | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAssess = async () => {
    setLoading(true)
    setError('')
    setAssessment(null)
    try {
      const result = await api.incentives.assess(projectFacts)
      setAssessment(result)
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Assessment failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>
            Government Support &amp; Incentive Schemes
          </CardTitle>
          <Button
            onClick={handleAssess}
            disabled={loading}
            variant="outline"
            size="sm"
          >
            {loading ? 'Assessing...' : 'Check Eligibility'}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-xs text-muted-foreground">
          Gujarat Industrial Policy 2020 — verified scheme eligibility based on
          project facts. Final eligibility remains with the competent authority.
        </p>

        {error && (
          <div className="rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {assessment && (
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-xs">
              {assessment.relevant_count > 0 && (
                <span className="text-green-700 font-medium">
                  {assessment.relevant_count} potentially relevant
                </span>
              )}
              {assessment.conditional_count > 0 && (
                <span className="text-yellow-700 font-medium">
                  {assessment.conditional_count} conditional
                </span>
              )}
              {assessment.insufficient_count > 0 && (
                <span className="text-gray-600 font-medium">
                  {assessment.insufficient_count} need more info
                </span>
              )}
              {assessment.not_relevant_count > 0 && (
                <span className="text-red-600 font-medium">
                  {assessment.not_relevant_count} not relevant
                </span>
              )}
            </div>

            <div className="space-y-2">
              {assessment.assessments
                .filter((a) => a.relevance !== 'not_relevant')
                .map((a) => (
                  <AssessmentRow key={a.scheme_id} assessment={a} />
                ))}
            </div>

            {assessment.assessments.every(
              (a) => a.relevance === 'not_relevant',
            ) && (
              <p className="text-sm text-muted-foreground">
                No schemes found potentially relevant based on available project
                facts.
              </p>
            )}

            <p className="text-xs text-muted-foreground italic">
              {assessment.explanation}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
