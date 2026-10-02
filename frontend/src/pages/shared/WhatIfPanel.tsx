import { useState } from 'react'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type { WhatIfResponse } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ApprovalDiffList } from '@/pages/shared/ApprovalDiffList'
import { statusBadge } from '@/pages/shared/statusBadges'
import { Disclosure } from '@/components/shared/Disclosure'
import { Select } from '@/components/ui/select'
import { TextInput } from '@/components/ui/textInput'

interface WhatIfPanelProps {
  applicationId: string
}

type FieldKind = 'number' | 'boolean' | 'string'

const SUPPORTED_FIELDS: { name: string; kind: FieldKind; hint: string }[] = [
  { name: 'production_capacity', kind: 'number', hint: 'MTPA, e.g. 30000' },
  { name: 'plot_area_sqm', kind: 'number', hint: 'sqm, e.g. 8000' },
  { name: 'builtup_area_sqm', kind: 'number', hint: 'sqm' },
  { name: 'power_demand', kind: 'number', hint: 'kVA' },
  { name: 'workers_total', kind: 'number', hint: 'count' },
  { name: 'building_height', kind: 'number', hint: 'metres' },
  { name: 'effluent_generation', kind: 'number', hint: 'KLD' },
  { name: 'ETP_capacity', kind: 'number', hint: 'KLD' },
  { name: 'groundwater_use', kind: 'boolean', hint: 'true / false' },
  { name: 'lift_present', kind: 'boolean', hint: 'true / false' },
  { name: 'boiler_present', kind: 'boolean', hint: 'true / false' },
  { name: 'hazardous_process', kind: 'boolean', hint: 'true / false' },
  { name: 'hazardous_chemicals_handled', kind: 'boolean', hint: 'true / false' },
  { name: 'new_project', kind: 'boolean', hint: 'true / false' },
  { name: 'industry_type', kind: 'string', hint: 'e.g. textiles' },
]

interface OverrideRow {
  field: string
  raw: string
  asUnknown: boolean
  customName: string
  customKind: FieldKind
}

const CUSTOM = '__custom'

// Custom mode lets MH (F-*) and any future keys through without
// duplicating a fact registry in the UI: the backend validates every
// override against the persisted pack vocabulary and 422s unknowns.
// GJ presets stay as one-click shortcuts.
function resolveSpec(row: OverrideRow): { name: string; kind: FieldKind } | null {
  if (row.field === CUSTOM) {
    const name = row.customName.trim()
    if (!name) return null
    return { name, kind: row.customKind }
  }
  const spec = SUPPORTED_FIELDS.find((f) => f.name === row.field)
  return spec ? { name: spec.name, kind: spec.kind } : null
}

function parseRow(row: OverrideRow, rowField: string): { ok: true; value: unknown } | { ok: false; error: string } {
  if (row.asUnknown) return { ok: true, value: null }
  const spec = resolveSpec(row)
  if (!spec) {
    return row.field === CUSTOM
      ? { ok: false, error: 'Enter a custom fact key (e.g. F-PET-02)' }
      : { ok: false, error: `Unsupported field: ${rowField}` }
  }
  const trimmed = row.raw.trim()
  if (spec.kind === 'boolean') {
    if (trimmed === 'true') return { ok: true, value: true }
    if (trimmed === 'false') return { ok: true, value: false }
    return { ok: false, error: `${spec.name} must be true or false (or mark as unknown)` }
  }
  if (spec.kind === 'number') {
    if (trimmed === '') return { ok: false, error: `${spec.name} needs a number` }
    const n = Number(trimmed)
    if (!Number.isFinite(n)) return { ok: false, error: `${spec.name} must be a number` }
    return { ok: true, value: n }
  }
  if (trimmed === '') return { ok: false, error: `${spec.name} needs a value` }
  return { ok: true, value: trimmed }
}

export function WhatIfPanel({ applicationId }: WhatIfPanelProps) {
  const [rows, setRows] = useState<OverrideRow[]>([
    { field: CUSTOM, raw: '', asUnknown: false, customName: 'F-PET-02', customKind: 'number' },
  ])
  const [result, setResult] = useState<WhatIfResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const addRow = () => setRows((r) => [...r, { field: CUSTOM, raw: '', asUnknown: false, customName: '', customKind: 'string' }])
  const removeRow = (idx: number) => setRows((r) => r.filter((_, i) => i !== idx))
  const updateRow = (idx: number, patch: Partial<OverrideRow>) =>
    setRows((r) => r.map((row, i) => (i === idx ? { ...row, ...patch } : row)))

  const run = async () => {
    setError('')
    setResult(null)
    const overrides: Record<string, unknown> = {}
    for (const row of rows) {
      const parsed = parseRow(row, row.field)
      if (!parsed.ok) {
        setError(parsed.error)
        return
      }
      const spec = resolveSpec(row)
      if (!spec) {
        setError('Enter a custom fact key (e.g. F-PET-02)')
        return
      }
      overrides[spec.name] = parsed.value
    }
    if (Object.keys(overrides).length === 0) {
      setError('Add at least one fact override')
      return
    }
    setLoading(true)
    try {
      const res = (await api.orchestration.whatIf(applicationId, overrides)) as WhatIfResponse
      setResult(res)
    } catch (err) {
      setError(getErrorMessage(err, 'What-if failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>What If (temporary, never saved)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Disclosure summary="Try temporary fact changes">
          <div className="mt-3 space-y-2">
            {rows.map((row, idx) => {
              const spec = resolveSpec(row)
              const isCustom = row.field === CUSTOM
              return (
                <div key={idx} className="flex flex-wrap items-center gap-2">
                  <Select
                    value={row.field}
                    onChange={(e) => updateRow(idx, { field: e.target.value })}
                  >
                    {SUPPORTED_FIELDS.map((f) => (
                      <option key={f.name} value={f.name}>
                        {f.name}
                      </option>
                    ))}
                    <option value={CUSTOM}>Custom fact…</option>
                  </Select>
                  {isCustom && (
                    <>
                      <TextInput
                        className="w-36"
                        placeholder="Fact key, e.g. F-PET-02"
                        value={row.customName}
                        onChange={(e) => updateRow(idx, { customName: e.target.value })}
                      />
                      <Select
                        value={row.customKind}
                        onChange={(e) =>
                          updateRow(idx, { customKind: e.target.value as FieldKind })
                        }
                      >
                        <option value="number">number</option>
                        <option value="boolean">boolean</option>
                        <option value="string">string</option>
                      </Select>
                    </>
                  )}
                  <TextInput
                    className="w-40"
                    placeholder={spec ? `${spec.kind} value` : 'value'}
                    value={row.raw}
                    disabled={row.asUnknown}
                    onChange={(e) => updateRow(idx, { raw: e.target.value })}
                  />
                  <label className="flex items-center gap-1 text-xs text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={row.asUnknown}
                      onChange={(e) => updateRow(idx, { asUnknown: e.target.checked })}
                    />
                    unknown
                  </label>
                  <Button variant="outline" size="sm" onClick={() => removeRow(idx)}>
                    Remove
                  </Button>
                </div>
              )
            })}
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={addRow}>
                Add fact
              </Button>
              <Button size="sm" onClick={run} disabled={loading}>
                {loading ? 'Recalculating...' : 'Recalculate'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Overrides are temporary and never change the saved project. Documents,
              consistency results, and SLA inputs stay as they are.
            </p>
          </div>
        </Disclosure>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
        )}

        {result && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm">
              <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${statusBadge(result.diff.overall_baseline)}`}>
                {result.diff.overall_baseline.replace(/_/g, ' ')}
              </span>
              <span aria-hidden>→</span>
              <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${statusBadge(result.diff.overall_whatif)}`}>
                {result.diff.overall_whatif.replace(/_/g, ' ')}
              </span>
            </div>

            {result.diff.no_change ? (
              <p className="text-sm text-muted-foreground">
                No regulatory impact for these temporary values.
              </p>
            ) : (
              <div className="space-y-2">
                <ApprovalDiffList diffs={result.diff.changed_approvals} />
                {(result.diff.next_action_baseline?.action_type !== result.diff.next_action_whatif?.action_type ||
                  result.diff.next_action_baseline?.affected_approval_id !== result.diff.next_action_whatif?.affected_approval_id) && (
                  <p className="text-xs text-muted-foreground">
                    Next action: {result.diff.next_action_baseline?.description ?? 'none'} →{' '}
                    {result.diff.next_action_whatif?.description ?? 'none'}
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
