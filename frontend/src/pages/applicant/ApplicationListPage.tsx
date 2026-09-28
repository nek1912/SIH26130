import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Application } from '@/types/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { PageHeader } from '@/components/shared/PageHeader'
import { EmptyState } from '@/components/shared/EmptyState'
import { formatDate } from '@/lib/format'

export function ApplicationListPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!projectId) return
    api.projects
      .getApplications(projectId)
      .then((data) => setApplications(data as Application[]))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [projectId])

  if (loading) return <LoadingSpinner className="mt-12" />

  return (
    <div className="space-y-6">
      <PageHeader
        title="Applications"
        actions={
          <>
            <Link to={`/projects/${projectId}/submit`}>
              <Button>New Application</Button>
            </Link>
            <Link to={`/projects/${projectId}`}>
              <Button variant="outline">Back to Project</Button>
            </Link>
          </>
        }
      />
      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}
      {applications.length === 0 ? (
        <EmptyState message="No applications yet. Submit your first application for this project." />
      ) : (
        <div className="space-y-3">
          {applications.map((app) => (
            <Link key={app.id} to={`/applications/${app.id}`}>
              <Card className="transition-colors hover:border-primary/50 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
                <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
                  <div className="min-w-0 space-y-1">
                    <p className="break-all font-mono text-sm font-medium">{app.reference_number}</p>
                    <p className="text-xs text-muted-foreground">
                      Created {formatDate(app.created_at)}
                    </p>
                    {app.current_stage && (
                      <p className="text-xs text-muted-foreground">
                        Stage: {app.current_stage}
                      </p>
                    )}
                    {app.decision_outcome && (
                      <p className="text-xs text-muted-foreground">
                        Decision: <span className="capitalize">{app.decision_outcome}</span>
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <StatusBadge status={app.status} />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
