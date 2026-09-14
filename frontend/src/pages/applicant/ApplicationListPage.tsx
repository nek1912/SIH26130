import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Application } from '@/types/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Applications</h1>
        <div className="flex gap-3">
          <Link to={`/projects/${projectId}/submit`}>
            <Button>New Application</Button>
          </Link>
          <Link to={`/projects/${projectId}`}>
            <Button variant="outline">Back to Project</Button>
          </Link>
        </div>
      </div>
      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}
      {applications.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No applications yet. Submit your first application for this project.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {applications.map((app) => (
            <Link key={app.id} to={`/applications/${app.id}`}>
              <Card className="transition-colors hover:border-primary/50">
                <CardContent className="flex items-center justify-between py-4">
                  <div className="space-y-1">
                    <p className="font-mono text-sm font-medium">{app.reference_number}</p>
                    <p className="text-xs text-muted-foreground">
                      Created {new Date(app.created_at).toLocaleDateString()}
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
