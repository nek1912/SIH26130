import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Approval, PackApprovalCode, Project } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

interface Option {
  key: string
  code: string
  title: string
  subtitle?: string
  approvalId?: string
}

export function ApplicationSubmitPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [options, setOptions] = useState<Option[]>([])
  const [jurisdiction, setJurisdiction] = useState('')
  const [selected, setSelected] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!projectId) return
    api.projects
      .get(projectId)
      .then(async (p) => {
        const project = p as Project
        setJurisdiction(project.jurisdiction ?? '')
        if (project.jurisdiction === 'IN-MH') {
          // Pack-driven: codes come from the persisted project pack, never
          // hardcoded. The server links the catalog row at creation.
          const pack = await api.projects.getApprovalCodes(projectId)
          setOptions(
            pack.approvals.map((c: PackApprovalCode) => ({
              key: c.approval_code,
              code: c.approval_code,
              title: c.approval_code,
              subtitle: c.authority || undefined,
            })),
          )
        } else {
          const data = (await api.approvals.list()) as Approval[]
          setOptions(
            data.map((approval) => ({
              key: approval.id,
              code: approval.code ?? '',
              title: approval.name ?? approval.id,
              subtitle: approval.description,
              approvalId: approval.id,
            })),
          )
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [projectId])

  const handleSubmit = async () => {
    if (!projectId || !selected) return
    const opt = options.find((o) => o.key === selected)
    if (!opt || !opt.code) {
      setError('Selected approval carries no pack code — cannot assess.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const app = (await api.applications.create(
        projectId,
        opt.code,
        opt.approvalId,
      )) as { id: string }
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
          <CardDescription>
            {jurisdiction === 'IN-MH'
              ? 'Choose the Maharashtra approval to assess. Assessment never mutates saved facts.'
              : 'Choose the approval type for this application.'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
          )}
          {options.length === 0 ? (
            <p className="text-sm text-muted-foreground">No approvals available.</p>
          ) : (
            <div className="space-y-2">
              {options.map((option) => (
                <label
                  key={option.key}
                  className={`flex cursor-pointer items-center rounded-md border p-3 transition-colors ${
                    selected === option.key
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/30'
                  }`}
                >
                  <input
                    type="radio"
                    name="approval"
                    value={option.key}
                    checked={selected === option.key}
                    onChange={() => setSelected(option.key)}
                    className="mr-3"
                  />
                  <div>
                    <p className="font-mono text-sm font-medium">{option.title}</p>
                    {option.subtitle && (
                      <p className="text-xs text-muted-foreground">{option.subtitle}</p>
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
