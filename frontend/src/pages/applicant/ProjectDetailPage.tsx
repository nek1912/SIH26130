import { useEffect, useState, type FormEvent } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Project, ProjectFacts, Application } from '@/types/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [facts, setFacts] = useState<ProjectFacts | null>(null)
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Facts editing state
  const [editingFacts, setEditingFacts] = useState(false)
  const [factsForm, setFactsForm] = useState({
    entity_type: '',
    sector: '',
    jurisdictions: '',
    headcount: 0,
    annual_turnover_inr: 0,
  })
  const [factsSaving, setFactsSaving] = useState(false)
  const [factsError, setFactsError] = useState('')

  useEffect(() => {
    if (!id) return
    Promise.all([
      api.projects.get(id),
      api.projects.getFacts(id).catch(() => null),
      api.projects.getApplications(id).catch(() => []),
    ])
      .then(([p, f, apps]) => {
        setProject(p as Project)
        const fData = f as ProjectFacts | null
        setFacts(fData)
        if (fData) {
          setFactsForm({
            entity_type: fData.entity_type ?? '',
            sector: fData.sector ?? '',
            jurisdictions: fData.jurisdictions?.join(', ') ?? '',
            headcount: fData.headcount ?? 0,
            annual_turnover_inr: fData.annual_turnover_inr ?? 0,
          })
        }
        setApplications(apps as Application[])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  const handleFactsSave = async (e: FormEvent) => {
    e.preventDefault()
    if (!id) return
    setFactsSaving(true)
    setFactsError('')
    try {
      const jurisdictions = factsForm.jurisdictions
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
      const updated = await api.projects.upsertFacts(id, {
        entity_type: factsForm.entity_type,
        sector: factsForm.sector,
        jurisdictions,
        headcount: factsForm.headcount,
        annual_turnover_inr: factsForm.annual_turnover_inr,
      }) as ProjectFacts
      setFacts(updated)
      setEditingFacts(false)
    } catch (err) {
      setFactsError(err instanceof Error ? err.message : 'Failed to save facts')
    } finally {
      setFactsSaving(false)
    }
  }

  if (loading) return <LoadingSpinner className="mt-12" />
  if (error) return <div className="mt-12 text-center text-destructive">{error}</div>
  if (!project) return <div className="mt-12 text-center text-muted-foreground">Project not found</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          {project.description && (
            <p className="text-muted-foreground">{project.description}</p>
          )}
        </div>
        <Link to="/projects">
          <Button variant="outline">Back to Projects</Button>
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Project Facts */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Project Facts</CardTitle>
            {!editingFacts && (
              <Button variant="outline" size="sm" onClick={() => setEditingFacts(true)}>
                Edit
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {editingFacts ? (
              <form onSubmit={handleFactsSave} className="space-y-3">
                {factsError && (
                  <div className="rounded-md bg-destructive/10 p-2 text-xs text-destructive">{factsError}</div>
                )}
                <div className="space-y-1">
                  <Label htmlFor="entity_type">Entity Type</Label>
                  <Input
                    id="entity_type"
                    value={factsForm.entity_type}
                    onChange={(e) => setFactsForm((f) => ({ ...f, entity_type: e.target.value }))}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="sector">Sector</Label>
                  <Input
                    id="sector"
                    value={factsForm.sector}
                    onChange={(e) => setFactsForm((f) => ({ ...f, sector: e.target.value }))}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="jurisdictions">Jurisdictions (comma-separated)</Label>
                  <Input
                    id="jurisdictions"
                    value={factsForm.jurisdictions}
                    onChange={(e) => setFactsForm((f) => ({ ...f, jurisdictions: e.target.value }))}
                    placeholder="e.g. Gujarat, Ahmedabad"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="headcount">Headcount</Label>
                  <Input
                    id="headcount"
                    type="number"
                    min={0}
                    value={factsForm.headcount}
                    onChange={(e) => setFactsForm((f) => ({ ...f, headcount: Number(e.target.value) }))}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="turnover">Annual Turnover (INR)</Label>
                  <Input
                    id="turnover"
                    type="number"
                    min={0}
                    value={factsForm.annual_turnover_inr}
                    onChange={(e) => setFactsForm((f) => ({ ...f, annual_turnover_inr: Number(e.target.value) }))}
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" size="sm" disabled={factsSaving}>
                    {factsSaving ? 'Saving...' : 'Save'}
                  </Button>
                  <Button type="button" variant="outline" size="sm" onClick={() => setEditingFacts(false)}>
                    Cancel
                  </Button>
                </div>
              </form>
            ) : facts ? (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Entity Type</dt>
                  <dd>{facts.entity_type}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Sector</dt>
                  <dd>{facts.sector}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Jurisdictions</dt>
                  <dd>{facts.jurisdictions?.join(', ') ?? '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Headcount</dt>
                  <dd>{facts.headcount}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Annual Turnover</dt>
                  <dd>₹{facts.annual_turnover_inr?.toLocaleString()}</dd>
                </div>
              </dl>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">No facts recorded yet.</p>
                <Button variant="outline" size="sm" onClick={() => setEditingFacts(true)}>
                  Add Facts
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Applications */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Applications</CardTitle>
            <Link to={`/projects/${id}/applications`}>
              <Button variant="outline" size="sm">View All</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {applications.length === 0 ? (
              <p className="text-sm text-muted-foreground">No applications yet.</p>
            ) : (
              <div className="space-y-2">
                {applications.slice(0, 5).map((app) => (
                  <Link key={app.id} to={`/applications/${app.id}`} className="flex items-center justify-between rounded-md border p-2 text-sm hover:bg-accent">
                    <div>
                      <span className="font-mono text-xs">{app.reference_number}</span>
                      {app.current_stage && (
                        <span className="ml-2 text-xs text-muted-foreground">({app.current_stage})</span>
                      )}
                    </div>
                    <StatusBadge status={app.status} />
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
