// IN-MH fact entry support (T3).
//
// Curated subset of the 128-fact MH registry covering the canonical demo
// drivers. The backend remains the validator — unknown/invalid values
// surface as 422 errors verbatim. CANONICAL_MH_FACTS mirrors
// backend/app/seed/mh/scenario.py (fill aid only; facts always submit
// through the real endpoint, never bypass validation).

export type MhFieldKind = 'boolean' | 'number' | 'string' | 'string-list' | 'json'

export interface MhFieldSpec {
  key: string
  label: string
  kind: MhFieldKind
  group: string
}

export const MH_FACT_FIELDS: MhFieldSpec[] = [
  // Location & site
  { key: 'F-LOC-01', label: 'Site in MIDC estate', kind: 'boolean', group: 'Location & site' },
  { key: 'F-LOC-04', label: 'Taluka', kind: 'string', group: 'Location & site' },
  { key: 'F-LOC-05', label: 'Planning authority', kind: 'string', group: 'Location & site' },
  { key: 'F-LOC-11', label: 'District', kind: 'string', group: 'Location & site' },
  { key: 'F-LOC-12', label: 'Industrial estate name', kind: 'string', group: 'Location & site' },
  { key: 'F-LOC-15', label: 'Forest land involved', kind: 'boolean', group: 'Location & site' },
  { key: 'F-GEO-01', label: 'CRZ category of site', kind: 'string', group: 'Location & site' },
  { key: 'F-SITE-01', label: 'Trees to fell', kind: 'boolean', group: 'Location & site' },
  // Products & process
  { key: 'F-PRD-01', label: 'Product in EIA 5(f) scope', kind: 'boolean', group: 'Products & process' },
  { key: 'F-PRD-02', label: 'Product type special (comma-separated)', kind: 'string-list', group: 'Products & process' },
  { key: 'F-PRD-03', label: 'Process mode', kind: 'string', group: 'Products & process' },
  { key: 'F-PRC-01', label: 'Water consumption (m³/day)', kind: 'number', group: 'Products & process' },
  { key: 'F-PRC-02', label: 'Fuel consumption (TPD)', kind: 'number', group: 'Products & process' },
  { key: 'F-BLD-01', label: 'Built-up area (m²)', kind: 'number', group: 'Products & process' },
  { key: 'F-BLD-03', label: 'Project area (ha)', kind: 'number', group: 'Products & process' },
  // Hazardous inventory
  { key: 'F-HAZ-01', label: 'Chemical inventory (JSON list)', kind: 'json', group: 'Hazardous inventory' },
  { key: 'F-HAZ-02', label: 'Schedule data (JSON list)', kind: 'json', group: 'Hazardous inventory' },
  // Petroleum
  { key: 'F-PET-01', label: 'Petroleum class', kind: 'string', group: 'Petroleum storage' },
  { key: 'F-PET-02', label: 'Petroleum quantity (L)', kind: 'number', group: 'Petroleum storage' },
  { key: 'F-PET-04', label: 'Max receptacle (L)', kind: 'number', group: 'Petroleum storage' },
  // Water & boiler
  { key: 'F-WAT-01', label: 'Water source (comma-separated)', kind: 'string-list', group: 'Water & boiler' },
  { key: 'F-WAT-02', label: 'Effluent generated', kind: 'boolean', group: 'Water & boiler' },
  { key: 'F-WAT-03', label: 'Discharge mode', kind: 'string', group: 'Water & boiler' },
  { key: 'F-WAT-05', label: 'Groundwater abstraction (m³/day)', kind: 'number', group: 'Water & boiler' },
  { key: 'F-WAT-08', label: 'Construction dewatering', kind: 'boolean', group: 'Water & boiler' },
  { key: 'F-GW-01', label: 'CGWB assessment unit category', kind: 'string', group: 'Water & boiler' },
  { key: 'F-BLR-04', label: 'Steam for external use', kind: 'boolean', group: 'Water & boiler' },
  // Labour
  { key: 'F-LAB-01', label: 'Max workers any day (12 mo)', kind: 'number', group: 'Labour' },
  { key: 'F-LAB-02', label: 'Manufacturing with power', kind: 'boolean', group: 'Labour' },
  { key: 'F-LAB-03', label: 'Max contract labour', kind: 'number', group: 'Labour' },
  { key: 'F-LAB-07', label: 'Hazardous process (First Schedule)', kind: 'boolean', group: 'Labour' },
  { key: 'F-LAB-08', label: 'Interstate migrant workers', kind: 'number', group: 'Labour' },
  { key: 'F-LAB-09', label: 'Intermittent/casual work only', kind: 'boolean', group: 'Labour' },
  // Waste & environment
  { key: 'F-HW-01', label: 'Hazardous waste generated', kind: 'boolean', group: 'Waste & environment' },
  { key: 'F-HW-03', label: 'HW utilisation/recovery on-site', kind: 'boolean', group: 'Waste & environment' },
  { key: 'F-EEE-01', label: 'Schedule-I EEE units used in FY', kind: 'number', group: 'Waste & environment' },
  // Expansion & incentives
  { key: 'F-EXP-01', label: 'Expansion/modernisation', kind: 'boolean', group: 'Expansion & incentives' },
  { key: 'F-INC-02', label: 'Plant & machinery investment (₹ cr)', kind: 'number', group: 'Expansion & incentives' },
  { key: 'F-INC-09', label: 'Turnover (₹ cr)', kind: 'number', group: 'Expansion & incentives' },
  // Other regimes
  { key: 'F-INS-01', label: 'Manufactures insecticide', kind: 'boolean', group: 'Other regimes' },
  { key: 'F-TRN-01', label: 'Consigns CMVR Table-III goods by road', kind: 'boolean', group: 'Other regimes' },
]

// Canonical Sahyadri demo values (mirror of CANONICAL_MH_SCENARIO_FACTS).
// Used only to pre-fill the form; submission still goes through validation.
export const CANONICAL_MH_FACTS: Record<string, unknown> = {
  'F-LOC-01': true,
  'F-LOC-04': 'Daund',
  'F-LOC-05': 'MIDC',
  'F-LOC-11': 'Pune',
  'F-LOC-12': 'MIDC Kurkumbh',
  'F-LOC-15': false,
  'F-GEO-01': 'NOT_IN_CRZ',
  'F-SITE-01': false,
  'F-PRD-01': true,
  'F-PRD-02': ['PESTICIDE_TECHNICAL'],
  'F-PRD-03': 'SYNTHESIS',
  'F-PRC-01': 10.0,
  'F-PRC-02': 10.0,
  'F-BLD-01': 12000.0,
  'F-BLD-03': 2.5,
  'F-HAZ-01': [
    { chemical: 'Toluene', cas: '108-88-3', max_qty_t: 20.0, storage_type: 'PROCESS' },
  ],
  'F-HAZ-02': [
    { chemical: 'Toluene', schedule: 'Sch 3 Part I', col3_t: 200.0, col4_t: 2000.0 },
  ],
  'F-PET-01': 'B',
  'F-PET-02': 2000.0,
  'F-PET-04': 900.0,
  'F-WAT-01': ['MIDC'],
  'F-WAT-02': true,
  'F-WAT-03': 'CETP',
  'F-WAT-05': 0.0,
  'F-WAT-08': false,
  'F-GW-01': 'SAFE',
  'F-BLR-04': false,
  'F-LAB-01': 60,
  'F-LAB-02': true,
  'F-LAB-03': 60,
  'F-LAB-07': true,
  'F-LAB-08': 0,
  'F-LAB-09': false,
  'F-HW-01': true,
  'F-HW-03': false,
  'F-EEE-01': 50.0,
  'F-EXP-01': false,
  'F-INC-02': 15.0,
  'F-INC-09': 50.0,
  'F-INS-01': false,
  'F-TRN-01': false,
}

// Form state keeps every field as a string; '' means "unset" (key omitted,
// so the backend treats it as missing → INSUFFICIENT_DATA, never FALSE).
export function toFormValue(value: unknown, kind: MhFieldKind): string {
  if (value === undefined || value === null) return ''
  if (kind === 'boolean') return value === true ? 'true' : value === false ? 'false' : ''
  if (kind === 'json') return JSON.stringify(value)
  if (Array.isArray(value)) return value.map(String).join(', ')
  return String(value)
}

export function fromFormValue(
  raw: string,
  kind: MhFieldKind,
): { ok: true; value?: unknown } | { ok: false; error: string } {
  const trimmed = raw.trim()
  if (trimmed === '') return { ok: true }
  if (kind === 'boolean') {
    if (trimmed === 'true') return { ok: true, value: true }
    if (trimmed === 'false') return { ok: true, value: false }
    return { ok: false, error: `must be true, false, or empty (unset), got '${trimmed}'` }
  }
  if (kind === 'number') {
    const n = Number(trimmed)
    if (!Number.isFinite(n)) return { ok: false, error: `must be a number, got '${trimmed}'` }
    return { ok: true, value: n }
  }
  if (kind === 'string-list') {
    const items = trimmed.split(',').map((s) => s.trim()).filter(Boolean)
    if (items.length === 0) return { ok: true }
    return { ok: true, value: items }
  }
  if (kind === 'json') {
    try {
      return { ok: true, value: JSON.parse(trimmed) }
    } catch {
      return { ok: false, error: 'must be valid JSON' }
    }
  }
  return { ok: true, value: trimmed }
}
