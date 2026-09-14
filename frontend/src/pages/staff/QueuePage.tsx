import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Application, ApplicationStatus } from '@/types/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

const STATUS_OPTIONS: { value: ApplicationStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'returned', label: 'Returned' },
  { value: 'incomplete', label: 'Incomplete' },
  { value: 'awaiting_inspection', label: 'Awaiting Inspection' },
  { value: 'awaiting_consultation', label: 'Awaiting Consultation' },
  { value: 'awaiting_hearing', label: 'Awaiting Hearing' },
  { value: 'awaiting_documents', label: 'Awaiting Documents' },
  { value: 'awaiting_payment', label: 'Awaiting Payment' },
  { value: 'approved', label: 'Approved' },
  { value: 'refused', label: 'Refused' },
  { value: 'withdrawn', label: 'Withdrawn' },
  { value: 'draft', label: 'Draft' },
  { value: 'cancelled', label: 'Cancelled' },
]

const PAGE_SIZE = 20

export function QueuePage() {
  const [applications, setApplications] = useState<Application[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    const params: Record<string, unknown> = { page, page_size: PAGE_SIZE }
    if (statusFilter) params.status = statusFilter

    api.applications
      .list(params)
      .then((data) => {
        if (!cancelled) {
          setApplications(data.items as Application[])
          setTotal(data.total)
        }
      })
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [page, statusFilter])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Application Queue</h1>
          <p className="text-sm text-muted-foreground">{total} application{total !== 1 ? 's' : ''}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <div className="space-y-1">
          <Label htmlFor="status-filter">Status</Label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            className="flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <Button variant="outline" onClick={() => { setStatusFilter(''); setPage(1) }}>
          Clear Filters
        </Button>
      </div>

      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      {loading ? (
        <LoadingSpinner className="mt-12" />
      ) : applications.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No applications match the current filters.
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
                      Project: {app.project_id.slice(0, 8)}...
                    </p>
                    {app.current_stage && (
                      <p className="text-xs text-muted-foreground">
                        Stage: {app.current_stage}
                      </p>
                    )}
                    {app.assigned_officer_id && (
                      <p className="text-xs text-muted-foreground">
                        Assigned: {app.assigned_officer_id.slice(0, 8)}...
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <StatusBadge status={app.status} />
                    <span className="text-xs text-muted-foreground">
                      {new Date(app.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
