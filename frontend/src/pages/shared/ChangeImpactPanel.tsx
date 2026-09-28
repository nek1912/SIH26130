import { useState } from 'react'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/errors'
import type { ChangeDescriptor, ChangeKind, ImpactRehearseResponse } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ApprovalDiffList } from '@/pages/shared/ApprovalDiffList'
import { classificationBadge, statusBadge } from '@/pages/shared/statusBadges'
import { Disclosure } from '@/components/shared/Disclosure'
import { Select } from '@/components/ui/select'
import { TextInput } from '@/components/ui/textInput'

interface ChangeImpactPanelProps {
  applicationId: string
}

const KINDS: ChangeKind[] = [
  'RULE_CHANGE',
  'DOCUMENT_REQUIREMENT_CHANGE',
  'DEPENDENCY_CHANGE',
  'EVIDENCE_STATUS_CHANGE',
  'SOURCE_METADATA_CHANGE',
]

const EVIDENCE_STATUSES = ['VERIFIED', 'PARTIAL', 'NOT_ESTABLISHED', 'CONFLICTING']

function parseJson(raw: string): { ok: true; value: Record<string, unknown> } | { ok: false; error: string } {
  try {
    const v = JSON.parse(raw) as unknown
    if (typeof v !== 'object' || v === null || Array.isArray(v)) {
      return { ok: false, error: 'Must be a JSON object' }
    }
    return { ok: true, value: v as Record<string, unknown> }
  } catch {
    return { ok: false, error: 'Invalid JSON' }
  }
}

export function ChangeImpactPanel({ applicationId }: ChangeImpactPanelProps) {
  const [kind, setKind] = useState<ChangeKind>('SOURCE_METADATA_CHANGE')
  const [sourceId, setSourceId] = useState('S07')
  const [ruleId, setRuleId] = useState('')
  const [requirementKey, setRequirementKey] = useState('')
  const [evidenceId, setEvidenceId] = useState('')
  const [oldStatus, setOldStatus] = useState('PARTIAL')
  const [newStatus, setNewStatus] = useState('VERIFIED')
  const [oldJson, setOldJson] = useState('{}')
  const [newJson, setNewJson] = useState('{}')
  const [result, setResult] = useState<ImpactRehearseResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const buildChange = (): ChangeDescriptor | null => {
    if (kind === 'SOURCE_METADATA_CHANGE') {
      if (!sourceId.trim()) { setError('source_id is needed'); return null }
      const o = parseJson(oldJson); if (!o.ok) { setError(`old metadata: ${o.error}`); return null }
      const n = parseJson(newJson); if (!n.ok) { setError(`new metadata: ${n.error}`); return null }
      return { change_kind: kind, source_id: sourceId.trim(), old_value: o.value, new_value: n.value }
    }
    if (kind === 'EVIDENCE_STATUS_CHANGE') {
      if (!evidenceId.trim()) { setError('evidence_id is needed'); return null }
      return { change_kind: kind, evidence_id: evidenceId.trim(), old_status: oldStatus, new_status: newStatus }
    }
    if (kind === 'RULE_CHANGE') {
      if (!ruleId.trim()) { setError('rule_id is needed'); return null }
      const o = parseJson(oldJson); if (!o.ok) { setError(`old rule: ${o.error}`); return null }
      const n = parseJson(newJson); if (!n.ok) { setError(`new rule: ${n.error}`); return null }
      return { change_kind: kind, rule_id: ruleId.trim(), old_value: o.value, new_value: n.value }
    }
    if (kind === 'DOCUMENT_REQUIREMENT_CHANGE') {
      if (!requirementKey.trim()) { setError('requirement_key is needed'); return null }
      const o = parseJson(oldJson); if (!o.ok) { setError(`old requirement: ${o.error}`); return null }
      const n = parseJson(newJson); if (!n.ok) { setError(`new requirement: ${n.error}`); return null }
      return { change_kind: kind, requirement_key: requirementKey.trim(), old_value: o.value, new_value: n.value }
    }
    const o = parseJson(oldJson); if (!o.ok) { setError(`old dependency: ${o.error}`); return null }
    let nValue: Record<string, unknown> | null = null
    if (newJson.trim() !== '' && newJson.trim() !== 'null') {
      const n = parseJson(newJson); if (!n.ok) { setError(`new dependency: ${n.error}`); return null }
      nValue = n.value
    }
    return { change_kind: kind, old_value: o.value, new_value: nValue }
  }

  const run = async () => {
    setError('')
    setResult(null)
    const change = buildChange()
    if (!change) return
    setLoading(true)
    try {
      const res = (await api.regulatory.rehearseChange(applicationId, change)) as ImpactRehearseResponse
      setResult(res)
    } catch (err) {
      setError(getErrorMessage(err, 'Rehearsal failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Regulatory Change Rehearsal (staff, never saved)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Disclosure summary="Rehearse a proposed regulatory change">
          <div className="mt-3 space-y-2">
            <label className="flex items-center gap-2 text-sm">
              Change kind
              <Select
                value={kind}
                onChange={(e) => setKind(e.target.value as ChangeKind)}
              >
                {KINDS.map((k) => (
                  <option key={k} value={k}>{k}</option>
                ))}
              </Select>
            </label>

            {kind === 'SOURCE_METADATA_CHANGE' && (
              <TextInput
                className="w-40"
                placeholder="source_id, e.g. S07"
                value={sourceId}
                onChange={(e) => setSourceId(e.target.value)}
              />
            )}
            {kind === 'RULE_CHANGE' && (
              <TextInput
                className="w-48"
                placeholder="rule_id, e.g. R-EIA-001"
                value={ruleId}
                onChange={(e) => setRuleId(e.target.value)}
              />
            )}
            {kind === 'DOCUMENT_REQUIREMENT_CHANGE' && (
              <TextInput
                className="w-48"
                placeholder="requirement_key, e.g. D15"
                value={requirementKey}
                onChange={(e) => setRequirementKey(e.target.value)}
              />
            )}
            {kind === 'EVIDENCE_STATUS_CHANGE' && (
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <TextInput
                  className="w-48"
                  placeholder="evidence_id, e.g. G0R5-FIRE-R25"
                  value={evidenceId}
                  onChange={(e) => setEvidenceId(e.target.value)}
                />
                <Select value={oldStatus} onChange={(e) => setOldStatus(e.target.value)}>
                  {EVIDENCE_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </Select>
                <span aria-hidden>→</span>
                <Select value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
                  {EVIDENCE_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </Select>
              </div>
            )}

            {kind !== 'EVIDENCE_STATUS_CHANGE' && (
              <div className="grid gap-2 md:grid-cols-2">
                <label className="text-xs text-muted-foreground">
                  Old representation (JSON object{kind === 'DEPENDENCY_CHANGE' ? '; edge {approval_id, prerequisite_approval_id}' : ''})
                  <textarea
                    className="mt-1 h-24 w-full rounded-md border p-2 font-mono text-xs"
                    value={oldJson}
                    onChange={(e) => setOldJson(e.target.value)}
                  />
                </label>
                <label className="text-xs text-muted-foreground">
                  New representation (JSON object{kind === 'DEPENDENCY_CHANGE' ? '; empty/null removes the edge' : ''})
                  <textarea
                    className="mt-1 h-24 w-full rounded-md border p-2 font-mono text-xs"
                    value={newJson}
                    onChange={(e) => setNewJson(e.target.value)}
                  />
                </label>
              </div>
            )}

            <Button size="sm" onClick={run} disabled={loading}>
              {loading ? 'Rehearsing...' : 'Rehearse'}
            </Button>
            <p className="text-xs text-muted-foreground">
              Stateless rehearsal against this application only. Nothing is saved;
              metadata-only changes can never alter a regulatory result.
            </p>
          </div>
        </Disclosure>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
        )}

        {result && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${classificationBadge(result.classification)}`}>
                {result.classification.replace(/_/g, ' ')}
              </span>
              <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${statusBadge(result.baseline_overall)}`}>
                {result.baseline_overall.replace(/_/g, ' ')}
              </span>
              <span aria-hidden>→</span>
              <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${statusBadge(result.new_overall)}`}>
                {result.new_overall.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">{result.reason}</p>
            {result.affected_approvals.length > 0 && (
              <p className="text-xs text-muted-foreground">
                Affected approvals: {result.affected_approvals.join(', ')}
                {result.affected_rule_ids.length > 0 && (
                  <> · Rules: {result.affected_rule_ids.join(', ')}</>
                )}
              </p>
            )}
            {result.evidence_caveats.length > 0 && (
              <div className="space-y-1">
                {result.evidence_caveats.map((c, i) => (
                  <p key={i} className="text-xs text-yellow-800">{c}</p>
                ))}
              </div>
            )}
            {result.diffs.length > 0 && <ApprovalDiffList diffs={result.diffs} />}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
