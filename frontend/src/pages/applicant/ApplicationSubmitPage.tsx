import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Approval } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

export function ApplicationSubmitPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [selected, setSelected] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.approvals
      .list()
      .then((data) => setApprovals(data as Approval[]))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const handleSubmit = async () => {
    if (!projectId || !selected) return
    setSubmitting(true)
    setError('')
    try {
      const app = await api.applications.create(projectId, selected) as { id: string }
      navigate(`/applications/${app.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create application')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingSpinner className="mt-12" />

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h1 className="text-2xl font-bold">Submit Application</h1>
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Select Approval</CardTitle>
          <CardDescription>Choose the approval type for this application.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
          )}
          {approvals.length === 0 ? (
            <p className="text-sm text-muted-foreground">No approvals available.</p>
          ) : (
            <div className="space-y-2">
              {approvals.map((approval) => (
                <label
                  key={approval.id}
                  className={`flex cursor-pointer items-center rounded-md border p-3 transition-colors ${
                    selected === approval.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/30'
                  }`}
                >
                  <input
                    type="radio"
                    name="approval"
                    value={approval.id}
                    checked={selected === approval.id}
                    onChange={() => setSelected(approval.id)}
                    className="mr-3"
                  />
                  <div>
                    <p className="text-sm font-medium">{approval.name ?? approval.id}</p>
                    {approval.description && (
                      <p className="text-xs text-muted-foreground">{approval.description}</p>
                    )}
                  </div>
                </label>
              ))}
            </div>
          )}
          <div className="flex gap-3 pt-2">
            <Button onClick={handleSubmit} disabled={!selected || submitting}>
              {submitting ? 'Submitting...' : 'Submit Application'}
            </Button>
            <Button variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
