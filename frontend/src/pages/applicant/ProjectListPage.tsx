import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import type { Project } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { PageHeader } from '@/components/shared/PageHeader'
import { EmptyState } from '@/components/shared/EmptyState'
import { formatDate } from '@/lib/format'

export function ProjectListPage() {
  const { session } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!session?.user?.id) return
    api.projects
      .list(session.user.id)
      .then((data) => setProjects(data as Project[]))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [session])

  if (loading) return <LoadingSpinner className="mt-12" />

  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        actions={
          <Link to="/projects/new">
            <Button>New Project</Button>
          </Link>
        }
      />
      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}
      {projects.length === 0 ? (
        <EmptyState message="No projects yet. Create your first project to get started." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link key={project.id} to={`/projects/${project.id}`}>
              <Card className="transition-colors hover:border-primary/50 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
                <CardHeader>
                  <CardTitle className="flex flex-wrap items-center gap-2">
                    {project.name}
                    {project.jurisdiction && (
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[10px] font-medium ${
                          project.jurisdiction === 'IN-MH'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {project.jurisdiction}
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {project.description ?? 'No description'}
                  </p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Created {formatDate(project.created_at)}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
