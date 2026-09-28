import { useState } from 'react'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type { HandoffListResponse, HandoffRecord, ReadyApprovalHandoff } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { badgeVariantClasses } from '@/components/ui/badgeVariants'
import { Select } from '@/components/ui/select'
import { TextInput } from '@/components/ui/textInput'

interface HandoffPanelProps {
  applicationId: string
  staffView?: boolean
}

// Mirrors the backend transition table; the server remains authoritative.
const NEXT_STATES: Record<string, string[]> = {
  handed_off: [],
  submitted_externally: ['under_external_review', 'approved_external', 'rejected_external', 'returned_for_correction'],
  under_external_review: ['approved_external', 'rejected_external', 'returned_for_correction'],
  returned_for_correction: [],
  approved_external: [],
  rejected_external: [],
}

function VerificationBadge({ h }: { h: HandoffRecord }) {
  if (h.verification === 'staff_verified') {
    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badgeVariantClasses.ready}`}>
        Staff verified
      </span>
    )
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badgeVariantClasses.review}`}>
      Reported by applicant — unverified
    </span>
  )
}

function PortalCta({ r }: { r: ReadyApprovalHandoff }) {
  if (r.portal_kind === 'portal') {
    return (
      <a
        className="text-sm font-medium text-blue-700 underline"
        href={r.portal_url}
        target="_blank"
        rel="noreferrer"
      >
        Open official portal
      </a>
    )
  }
  return (
    <a
      className="text-sm font-medium text-blue-700 underline"
      href={r.portal_url}
      target="_blank"
      rel="noreferrer"
    >
      Open official reference (portal link not verified in this dataset)
    </a>
  )
}

export function HandoffPanel({ applicationId, staffView = false }: HandoffPanelProps) {
  const [data, setData] = useState<HandoffListResponse | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const [reference, setReference] = useState<Record<string, string>>({})
  const [reportTo, setReportTo] = useState<Record<string, string>>({})

  const refresh = async () => {
    try {
      const res = (await api.handoffs.list(applicationId)) as HandoffListResponse
      setData(res)
    } catch (err) {
      setError(getErrorMessage(err, 'Could not load handoffs'))
    }
  }

  const [expanded, setExpanded] = useState(false)

  const toggle = (open: boolean) => {
    setExpanded(open)
    if (open && !data) refresh().catch(() => {})
  }

  const mutate = async (key: string, fn: () => Promise<unknown>) => {
    setError('')
    setBusy(key)
    try {
      await fn()
      await refresh()
    } catch (err) {
      setError(getErrorMessage(err, 'Handoff update failed'))
    } finally {
      setBusy('')
    }
  }

  const handoffsByApproval = new Map((data?.handoffs ?? []).map((h) => [h.approval_code, h]))

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {staffView ? 'External Handoff Tracking' : 'Apply on the Official Portal'}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <details
          open={expanded ? true : undefined}
          onToggle={(e) => toggle((e.target as HTMLDetailsElement).open)}
        >
          <summary className="cursor-pointer text-sm font-medium">
            Government handoff {data ? `(${data.handoffs.length} recorded)` : ''}
          </summary>
        <div className="mt-2 space-y-4">
        <p className="text-xs text-muted-foreground">
          UdyamDwaar does not submit applications to the government. Apply on the
          authority&apos;s official portal below, then record your external reference
          here. Documents prepared here are not sent anywhere automatically.
        </p>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
        )}

        {data?.ready_approvals.map((r) => {
          const h = handoffsByApproval.get(r.approval_code)
          return (
            <div key={r.approval_code} className="rounded-md border p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-muted-foreground">{r.approval_code}</span>
                <span className="font-medium">{r.external_system}</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">Authority: {r.authority}</p>
              <div className="mt-2"><PortalCta r={r} /></div>
              {r.missing_documents.length > 0 && (
                <p className="mt-1 text-xs text-yellow-800">
                  Still to prepare here: {r.missing_documents.join(', ')}
                </p>
              )}

              {!h && (
                <div className="mt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy === `init-${r.approval_code}`}
                    onClick={() => mutate(`init-${r.approval_code}`, () => api.handoffs.initiate(applicationId, r.approval_code))}
                  >
                    {busy === `init-${r.approval_code}` ? 'Saving...' : 'Initiate handoff'}
                  </Button>
                </div>
              )}

              {h && (
                <div className="mt-2 space-y-2 rounded-md bg-muted/40 p-2">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="rounded bg-gray-100 px-2 py-0.5 font-medium">
                      {h.status.replace(/_/g, ' ')}
                    </span>
                    <VerificationBadge h={h} />
                    {h.currently_ready === false && (
                      <span className="text-yellow-800">
                        Note: this approval is no longer READY — record kept as history.
                      </span>
                    )}
                  </div>
                  {h.external_reference && (
                    <p className="text-xs">External reference: <span className="font-mono">{h.external_reference}</span></p>
                  )}

                  {(h.status === 'handed_off' || h.status === 'returned_for_correction') && (
                    <div className="flex flex-wrap items-center gap-2">
                      <TextInput
                        className="w-52"
                        placeholder="External reference from portal"
                        value={reference[h.id] ?? ''}
                        onChange={(e) => setReference((m) => ({ ...m, [h.id]: e.target.value }))}
                      />
                      <Button
                        size="sm"
                        disabled={busy === `sub-${h.id}`}
                        onClick={() => mutate(`sub-${h.id}`, () =>
                          api.handoffs.recordSubmission(applicationId, h.id, reference[h.id] ?? ''),
                        )}
                      >
                        {busy === `sub-${h.id}` ? 'Saving...' : 'Record external submission'}
                      </Button>
                    </div>
                  )}

                  {(NEXT_STATES[h.status] ?? []).length > 0 && (
                    <div className="flex flex-wrap items-center gap-2">
                      <Select
                        value={reportTo[h.id] ?? NEXT_STATES[h.status][0]}
                        onChange={(e) => setReportTo((m) => ({ ...m, [h.id]: e.target.value }))}
                      >
                        {NEXT_STATES[h.status].map((s) => (
                          <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
                        ))}
                      </Select>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busy === `rep-${h.id}`}
                        onClick={() => mutate(`rep-${h.id}`, () =>
                          api.handoffs.reportStatus(applicationId, h.id, reportTo[h.id] ?? NEXT_STATES[h.status][0]),
                        )}
                      >
                        {busy === `rep-${h.id}` ? 'Saving...' : 'Report external status'}
                      </Button>
                    </div>
                  )}

                  {staffView && h.status !== 'handed_off' && h.verification !== 'staff_verified' && (
                    <div className="flex flex-wrap items-center gap-2">
                      <Button
                        size="sm"
                        disabled={busy === `ver-${h.id}`}
                        onClick={() => mutate(`ver-${h.id}`, () =>
                          api.handoffs.verify(applicationId, h.id, h.status),
                        )}
                      >
                        {busy === `ver-${h.id}` ? 'Verifying...' : `Verify as ${h.status.replace(/_/g, ' ')}`}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {data && data.ready_approvals.length === 0 && data.handoffs.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No approval is currently READY for external handoff.
          </p>
        )}

        {data && data.handoffs.length > 0 && data.ready_approvals.length === 0 && (
          <div className="space-y-2">
            {data.handoffs.map((h) => (
              <div key={h.id} className="rounded-md border p-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-muted-foreground">{h.approval_code}</span>
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium">
                    {h.status.replace(/_/g, ' ')}
                  </span>
                  <VerificationBadge h={h} />
                </div>
                {h.external_reference && (
                  <p className="mt-1 text-xs">External reference: <span className="font-mono">{h.external_reference}</span></p>
                )}
              </div>
            ))}
          </div>
        )}
        </div>
        </details>
      </CardContent>
    </Card>
  )
}
