import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type { Application, ApplicationOrchestration, PackApprovalCode } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { statusBadge } from '@/pages/shared/statusBadges'

// Project-level MH assessment dashboard (T3).
//
// Read-only projection: approval codes + authorities come from the
// project's persisted pack; per-approval statuses come from each
// application's own orchestration response. The frontend never
// computes applicability or readiness — it only renders backend results.
export function MhAssessmentPanel({ projectId }: { projectId: string }) {
  const navigate = useNavigate()
  const [codes, setCodes] = useState<PackApprovalCode[]>([])
  const [apps, setApps] = useState<Application[]>([])
  const [statusByApp, setStatusByApp] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [assessing, setAssessing] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([
      api.projects.getApprovalCodes(projectId),
      api.projects.getApplications(projectId).catch(() => []),
    ])
      .then(([pack, applications]) => {
        if (cancelled) return
        setCodes(pack.approvals)
        const list = applications as Application[]
        setApps(list)
        // Overall readiness per assessed approval, straight from the backend.
        Promise.all(
          list.map((a) =>
            api.orchestration
              .get(a.id)
              .then((o) => ({ id: a.id, status: (o as ApplicationOrchestration).overall_status }))
              .catch(() => ({ id: a.id, status: 'unavailable' })),
          ),
        ).then((rows) => {
          if (cancelled) return
          const map: Record<string, string> = {}
          for (const r of rows) map[r.id] = r.status
          setStatusByApp(map)
        })
      })
      .catch((err) => {
        if (!cancelled) setError(getErrorMessage(err, 'Failed to load assessment data'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  const assess = async (code: string) => {
    setError('')
    setAssessing(code)
    try {
      const app = (await api.applications.create(projectId, code)) as { id: string }
      navigate(`/applications/${app.id}`)
    } catch (err) {
      setError(getErrorMessage(err, `Failed to assess ${code}`))
    } finally {
      setAssessing('')
    }
  }

  const appByCode = new Map(apps.map((a) => [a.approval_code ?? '', a]))

  if (loading) return <LoadingSpinner />
  if (error && codes.length === 0) {
    return <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Approval Assessment (IN-MH pack)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
        )}
        {codes.length === 0 ? (
          <p className="text-sm text-muted-foreground">No assessable approvals in this pack.</p>
        ) : (
          codes.map((c) => {
            const app = appByCode.get(c.approval_code)
            const status = app ? statusByApp[app.id] : undefined
            return (
              <div
                key={c.approval_code}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-2 text-sm"
              >
                <div>
                  <span className="font-mono text-xs">{c.approval_code}</span>
                  {c.authority && (
                    <span className="ml-2 text-xs text-muted-foreground">{c.authority}</span>
                  )}
                  {status && (
                    <span
                      className={`ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusBadge(status)}`}
                    >
                      {status.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
                {app ? (
                  <Link to={`/applications/${app.id}`}>
                    <Button variant="outline" size="sm">
                      Open assessment
                    </Button>
                  </Link>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={assessing === c.approval_code}
                    onClick={() => assess(c.approval_code)}
                  >
                    {assessing === c.approval_code ? 'Assessing...' : 'Run assessment'}
                  </Button>
                )}
              </div>
            )
          })
        )}
        <p className="text-xs text-muted-foreground">
          Assessment creates one application per approval and evaluates it with
          the persisted IN-MH pack. Detail pages show applicability, blockers,
          documents, What-If, and handoff.
        </p>
      </CardContent>
    </Card>
  )
}
