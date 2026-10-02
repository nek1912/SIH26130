import { useState, type FormEvent } from 'react'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type { ProjectFacts } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { TextInput } from '@/components/ui/textInput'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  MH_FACT_FIELDS,
  CANONICAL_MH_FACTS,
  toFormValue,
  fromFormValue,
  type MhFieldKind,
} from '@/pages/shared/mhFacts'

interface MhFactsEditorProps {
  projectId: string
  existing: ProjectFacts | null
  onSaved: (facts: ProjectFacts) => void
}

function emptyForm(): Record<string, string> {
  const form: Record<string, string> = {}
  for (const f of MH_FACT_FIELDS) form[f.key] = ''
  return form
}

function formFromRecord(record: ProjectFacts | null): Record<string, string> {
  const form = emptyForm()
  const stored = record?.facts_json as Record<string, unknown> | undefined
  if (stored && typeof stored === 'object') {
    for (const f of MH_FACT_FIELDS) {
      if (stored[f.key] !== undefined) form[f.key] = toFormValue(stored[f.key], f.kind)
    }
  }
  return form
}

function FieldInput({
  fieldKey,
  kind,
  value,
  onChange,
}: {
  fieldKey: string
  kind: MhFieldKind
  value: string
  onChange: (v: string) => void
}) {
  if (kind === 'boolean') {
    return (
      <Select value={value} onChange={(e) => onChange(e.target.value)} aria-label={fieldKey}>
        <option value="">Unset</option>
        <option value="true">True</option>
        <option value="false">False</option>
      </Select>
    )
  }
  if (kind === 'json') {
    return (
      <textarea
        className="w-full rounded-md border px-2 py-1 font-mono text-xs"
        rows={3}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder='e.g. [{"chemical": "Toluene"}]'
        aria-label={fieldKey}
      />
    )
  }
  return (
    <TextInput
      className="w-full"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Unset"
      aria-label={fieldKey}
    />
  )
}

export function MhFactsEditor({ projectId, existing, onSaved }: MhFactsEditorProps) {
  const [entityType, setEntityType] = useState(existing?.entity_type ?? 'pvt-ltd')
  const [sector, setSector] = useState(existing?.sector ?? 'chemical')
  const [form, setForm] = useState<Record<string, string>>(() => formFromRecord(existing))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [savedAt, setSavedAt] = useState('')

  const setField = (key: string, v: string) =>
    setForm((f) => ({ ...f, [key]: v }))

  const fillCanonical = () => {
    const next = emptyForm()
    for (const f of MH_FACT_FIELDS) {
      if (CANONICAL_MH_FACTS[f.key] !== undefined) {
        next[f.key] = toFormValue(CANONICAL_MH_FACTS[f.key], f.kind)
      }
    }
    setForm(next)
    setError('')
  }

  const handleSave = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSavedAt('')
    const factsJson: Record<string, unknown> = {}
    for (const f of MH_FACT_FIELDS) {
      const parsed = fromFormValue(form[f.key] ?? '', f.kind)
      if (!parsed.ok) {
        setError(`${f.key}: ${parsed.error}`)
        return
      }
      if (parsed.value !== undefined) factsJson[f.key] = parsed.value
    }
    setSaving(true)
    try {
      const updated = (await api.projects.upsertFacts(
        projectId,
        {
          entity_type: entityType,
          sector,
          jurisdictions: ['IN-MH'],
          headcount: 0,
          annual_turnover_inr: 0,
        },
        factsJson,
      )) as ProjectFacts
      onSaved(updated)
      setSavedAt(new Date().toLocaleTimeString())
    } catch (err) {
      // Backend validation (unknown fact, wrong type) surfaces verbatim —
      // never silently substituted.
      setError(getErrorMessage(err, 'Failed to save facts'))
    } finally {
      setSaving(false)
    }
  }

  const groups = [...new Set(MH_FACT_FIELDS.map((f) => f.group))]

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle>Maharashtra Project Facts (IN-MH registry)</CardTitle>
        <Button variant="outline" size="sm" type="button" onClick={fillCanonical}>
          Fill canonical demo values
        </Button>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSave} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
          )}
          {savedAt && (
            <div className="rounded-md bg-green-50 p-2 text-xs text-green-700">
              Saved at {savedAt}. Empty fields are unset (treated as missing, never false).
            </div>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="mh-entity-type">Entity Type</Label>
              <Input
                id="mh-entity-type"
                value={entityType}
                onChange={(e) => setEntityType(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="mh-sector">Sector</Label>
              <Input
                id="mh-sector"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                required
              />
            </div>
          </div>
          {groups.map((group) => (
            <fieldset key={group} className="space-y-2 rounded-md border p-3">
              <legend className="px-1 text-xs font-medium text-muted-foreground">{group}</legend>
              {MH_FACT_FIELDS.filter((f) => f.group === group).map((f) => (
                <div key={f.key} className="grid grid-cols-[110px_1fr] items-center gap-2">
                  <Label htmlFor={`mh-${f.key}`} className="font-mono text-[11px]" title={f.label}>
                    {f.key}
                  </Label>
                  <FieldInput
                    fieldKey={f.key}
                    kind={f.kind}
                    value={form[f.key] ?? ''}
                    onChange={(v) => setField(f.key, v)}
                  />
                </div>
              ))}
            </fieldset>
          ))}
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? 'Saving...' : 'Save Facts'}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Hover a fact key for its meaning. Empty fields stay unset (missing,
            never false). The server validates every value against the IN-MH registry.
          </p>
        </form>
      </CardContent>
    </Card>
  )
}
