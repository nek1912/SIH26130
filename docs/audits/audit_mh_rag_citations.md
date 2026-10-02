# T5 — Maharashtra RAG / Source-Citation Wiring Audit

Date: 2026-10-02. Scope: backend citation wiring only. No rule,
role, composition, GJ, frontend, or migration changes.

Principle: deterministic rules decide; RAG retrieves; templates
explain; human authority decides. Missing evidence fails closed.

## 1. Existing RAG/source architecture

- `SourceRecord` (pack + DB): id/title/authority/source_type/url/
  jurisdiction/source_class/notes/checked_date/trust_tier.
- DB retrieval: PostgreSQL tsvector/GIN (`source_chunks.tsv`,
  `ts_rank_cd`), `SourcesRepository`, `retrieval.py`
  (`search_chunks`, `get_citations_for_source_ids`).
- Explanation: template-only `explanation.py` (`explain_approval`,
  `answer_query`, `explain_orchestration_with_citations`), never
  calls the applicability engine.
- API: `GET /sources`, `GET /sources/{id}`, `POST /sources/seed`,
  `POST /regulatory/explain`, `GET /regulatory/approval/{id}/
  explanation`, `GET /regulatory/orchestration/{id}/citations`,
  `POST /regulatory/changes/rehearse` (already pack-aware).
- Pack boundary: `load_regulatory_pack(IN-GJ)` 19 rules / 32
  sources; `load_regulatory_pack(IN-MH)` 26 rules / 22 sources;
  `DEFAULT_JURISDICTION = "IN-GJ"` preserved.

## 2. Gap identified

MH evidence existed in the pack but was unreachable:

1. DB holds GJ rows only; `SRC-xxx` lookups returned `[]`.
2. `orchestration_citations` used `get_active_jurisdiction`
   (IN-GJ default), not the application's persisted pack.
3. `answer_query` searched GJ chunks only; hardcoded
   "Gujarat regulatory dataset" strings.
4. `GET /sources` had no jurisdiction filter; MH rows invisible.
5. `Citation` lacked jurisdiction/provision/trust metadata.

Result (pre-T5): MH `citations: []`, GJ contamination risk on
free-text queries. Deterministic decisions were unaffected
(boundary correct) — demo polish only.

## 3. Source-reference inventory

All 26 active MH rules resolve within the MH pack
(missing = []):

- APR-001: R-002 → SRC-001
- APR-003: R-007 → SRC-001, SRC-179
- APR-004: R-009 → SRC-001; APR-006: R-011 → SRC-001
- APR-007: R-012 → SRC-001
- APR-010: R-018 → SRC-013; R-096 → SRC-120
- APR-019: R-026 → SRC-081, SRC-026
- APR-023: R-028/R-086/R-087 → SRC-034; R-073 → SRC-085
- APR-026: R-030 → SRC-092, SRC-017
- APR-029: R-035 → SRC-043
- APR-043: R-077/R-043/R-044/R-046 → SRC-052
- APR-044: R-046 → SRC-052; APR-054: R-056 → SRC-013
- APR-055: R-067 → SRC-100; CMP-018: R-070 → SRC-081
- APR-022: R-089 → SRC-081; CMP-024: R-093 → SRC-102
- CMP-025: R-094 → SRC-135
- LOC-CRZ: R-083 → SRC-112; LOC-FOREST: R-084 → SRC-113

No silent additions: only stored v5 refs wired.

## 4. MH coverage

- COMPLETE: 26/26 active rules (all source_refs resolve to the
  22-record MH corpus; 17 distinct refs).
- PARTIAL: none at rule level (R-091 derivation stays PARTIAL
  by design, out of T5 scope).
- MISSING: none for active rules. 166/188 v5 sources remain
  deferred with their rules by design (not evidence gaps).
- Deferred rules untouched; none reactivated for citations.

## 5. Missing evidence

- Active rules: none missing.
- Structural: `SourceRecord` carries no structured
  effective_from/to or evidence-status enum (dates/status live
  in `notes` verbatim). Exposed as unavailable (None), never
  invented.
- DB: MH rows not seeded (intentional — no migration needed;
  pack serves MH citations in-memory).

## 6. Retrieval implementation

Added to `retrieval.py` (deterministic, no embeddings/LLM/
vector DB):

- `pack_source_to_citation`, `get_pack_source_by_id`,
  `get_pack_citations_for_source_ids` (order-preserving,
  missing stays missing),
- `get_rule_source_ids`, `get_approval_source_ids`,
  `get_approval_provisions`, `get_approval_citations`,
- `search_pack_sources` (token-overlap rank, source_id
  tiebreak; pack-scoped so GJ/MH cannot mix),
- `filter_rules_by_effective_date` (None date = all rules),
- `search_chunks_for_jurisdiction` (DB JOIN filter; None =
  legacy behavior).
- DB `get_citations_for_source_ids` now populates additive
  jurisdiction/checked_date/trust_tier fields.

## 7. API wiring (additive, no breaking changes)

- `Citation`: + `jurisdiction`, `checked_date`, `trust_tier`,
  `provision` (all optional, default None).
- `ExplanationRequest`: + optional `jurisdiction`.
- `GET /sources`: + optional `?jurisdiction=` (omitted =
  legacy `get_all_sources`).
- `POST /regulatory/explain`: request jurisdiction wins,
  else active default; MH uses pack search only.
- `GET /regulatory/approval/{id}/explanation`: + optional
  `?evaluation_date=YYYY-MM-DD`; passes pack sources +
  jurisdiction to `explain_approval`.
- `GET /regulatory/orchestration/{id}/citations`: resolves
  the application's persisted `(jurisdiction, pack_version)`
  via `resolve_persisted_pack` when the application parses;
  else falls back to active jurisdiction (legacy contract
  for non-UUID callers/tests preserved). Never crosses
  jurisdictions.
- No LLM added; result semantics unchanged; no field renamed.

## 8. Citation representation

`Citation` reuses the existing model (no duplicate). Exposes
where available: source_id, title, authority, provision
(rule citation_span), source_type, jurisdiction, checked_date,
trust_tier, url (official locator verbatim). Effective date /
evidence-status enum have no structured store → None
(unavailable). No internal DB details; no fabricated URLs.

## 9. Jurisdiction isolation

Verified by `test_mh_rag_citations.py` + live TestClient:

- IN-MH → MH pack sources only (`SRC-xxx`, `IN-MH`).
- IN-GJ → GJ sources only (`Sxx`, `IN-GJ`).
- MH free-text uses pack search with zero DB calls.
- MH explain with empty DB returns pack citations, never GJ.
- `rehearse_impact` with MH `known_source_ids` rejects GJ
  `S01` as unknown (no fallback).
- Cross-contamination tests: MH search never returns `S0x`;
  GJ pack contains no `SRC-xxx`.

## 10. Effective-date handling

- Rules carry `effective_from` (e.g. R-002 2014-06-25, R-028
  2025-05-01); `evaluation_date` query param filters
  not-in-force rules from evidence lookup.
- None date preserves behavior (all 26 rules).
- Sources have no structured effective dates → unavailable,
  not invented. Overlapping APR-010 sources (SRC-013 +
  SRC-120) both returned; no silent supersession choice.

## 11. Evidence-status handling

- `trust_tier` preserved verbatim (T1 vs T2/T3 vs
  GJ `govt-portal`); never upgraded.
- Answer qualifier: any T2/T3 → "Includes conditional
  evidence…"; all-T1 → "Based on verified evidence.";
  GJ tier → no claim (legacy wording preserved).
- `EvidenceState` SUFFICIENT/PARTIAL/INSUFFICIENT reflects
  citation presence + result type, not a law verdict.
- PARTIAL/UNVERIFIED never presented as verified law.

## 12. Explanation behavior

- APPLIES / DOES_NOT_APPLY / CONDITIONAL / INSUFFICIENT_DATA
  templates unchanged in decision wording; only citation
  summary + jurisdiction label + qualifier added.
- INSUFFICIENT_DATA never converted to "required" /
  "not required" (tested).
- No "must/shall/mandatory/deadline" claims in generated
  text (tested); system evaluation framed as evaluation,
  law framed via cited sources.
- RAG never decides: no applicability-engine calls from
  retrieval/explanation; orchestration/What-If/readiness/
  handoff results byte-identical with/without citations.

## 13. Tests

`backend/tests/test_mh_rag_citations.py` — 44 tests:

rule→source (5), approval→source (5), metadata/URL (3),
verified/conditional/partial (3), missing/nonexistent (3),
jurisdiction isolation + no-fallback (5), effective-date +
supersession (4), four result explanations + claim safety
(5), RAG-must-not-decide (3), What-If preservation (1),
impact/rehearsal preservation (2), handoff + regression pins
(5). Live TestClient checks: MH approval explanation cites
`SRC-001/IN-MH/T1`; persisted MH application cites `SRC-052`
under active IN-GJ; `GET /sources?jurisdiction=IN-MH`
filters.

## 14. Regression results

- Focused: 112 passed (regulatory suites + T5).
- Full: `pytest tests/ -q` → **2467 passed, 0 failed**
  (2423 T4 baseline + 44 T5).
- `ruff check app/ tests/`: 20 × E501, all pre-existing in
  untracked/concurrent files; zero on T5-touched lines.
  T5 files: `ruff check` clean.
- OpenAPI: 53 paths; regulatory/source paths intact;
  additive query/body fields only.
- Pins: R-002 CLASSIFICATION, R-043/R-044 EXEMPTION, R-030 /
  R-035 / R-077 TRIGGER unchanged; R-087 EXEMPTION + APR-023
  composition (T4) preserved; APR-001/APR-043 preserved;
  GJ compositions {}; DEFAULT_JURISDICTION IN-GJ; MH 26 /
  GJ 19 rules; MH 22 sources.
- Frontend untouched (T3 owns UI concurrently).

## 15. Limitations

- MH citations served from in-memory pack; DB `sources` /
  `source_chunks` remain GJ-only (no migration by design).
- Source effective dates / evidence-status enum unstructured
  (notes-only) → citation fields None where unavailable.
- Pack text search is token-overlap over title/authority/
  notes (inspectable); no semantic/vector ranking (not
  needed — rule refs already pinpoint evidence).
- `orchestration_citations` persisted-pack resolution is
  best-effort for non-UUID legacy callers (falls back to
  active jurisdiction, still same-jurisdiction sources).
- Frontend citation display stays T3's scope (no UI changes
  here).

## 16. What remains intentionally deferred

- Seeding MH sources/chunks into PostgreSQL (would need a
  data-seed decision, not a schema migration; not required
  while pack fallback satisfies citations).
- R-013/R-014/R-015 lookup/composition chain (T7), R-091
  full rule (T8), APR-001 consumer (T9), engine primitives
  (T10+), staging migration execution (T6 ops).
- Full MH regulatory coverage (61 deferred + 11
  confirmation-gated stay fail-closed by evidence).

Status: IMPLEMENTED (chain works end-to-end for stored
evidence). No PARTIAL remains on wired paths; remaining
PARTIALs (R-091, frontend journey) are out of T5 scope.
