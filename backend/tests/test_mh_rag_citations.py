"""T5: Maharashtra RAG / source-citation wiring (deterministic, no LLM).

Verifies the complete evidence chain using only stored pack evidence:

    rule -> source_refs -> pack SourceRecord -> retrieval -> explanation
    -> API (additive citations, jurisdiction-filtered).

No embeddings, no vector DB, no LLM. RAG retrieves; rules decide.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

from app.db.postgres import PostgresDB
from app.handoff.service import is_ready_to_handoff, prepare_initiation
from app.orchestration.service import orchestrate_application_full
from app.orchestration.whatif import run_whatif_assessment
from app.regulatory.evidence import EvidenceStatus
from app.regulatory.explanation import (
    answer_query,
    explain_approval,
    explain_orchestration_with_citations,
)
from app.regulatory.impact import RehearsalInputs, rehearse_impact
from app.regulatory.impact_models import ChangeDescriptor, ChangeKind
from app.regulatory.models import Citation, EvidenceState
from app.regulatory.retrieval import (
    filter_rules_by_effective_date,
    get_approval_citations,
    get_approval_source_ids,
    get_pack_citations_for_source_ids,
    get_pack_source_by_id,
    get_rule_source_ids,
    search_pack_sources,
)
from app.rules.models import RuleRole
from app.seed.mh.scenario import load_canonical_mh_scenario
from app.seed.pack import (
    DEFAULT_JURISDICTION,
    IN_GJ,
    IN_MH,
    load_regulatory_pack,
)


def _mh_pack():
    return load_regulatory_pack(IN_MH)


def _gj_pack():
    return load_regulatory_pack(IN_GJ)


def _mock_db():
    return MagicMock(spec=PostgresDB)


# 1. MH rule -> source lookup
class TestMhRuleSourceLookup:
    def test_r002_maps_to_src001(self):
        pack = _mh_pack()
        assert get_rule_source_ids(pack.approval_rules, "R-002") == ["SRC-001"]

    def test_r077_maps_to_src052(self):
        pack = _mh_pack()
        assert get_rule_source_ids(pack.approval_rules, "R-077") == ["SRC-052"]

    def test_r030_maps_to_act_and_sop(self):
        pack = _mh_pack()
        ids = get_rule_source_ids(pack.approval_rules, "R-030")
        assert ids == ["SRC-092", "SRC-017"]

    def test_unknown_rule_returns_empty(self):
        pack = _mh_pack()
        assert get_rule_source_ids(pack.approval_rules, "R-999") == []

    def test_every_active_rule_has_usable_source(self):
        pack = _mh_pack()
        by_id = {s.id for s in pack.sources}
        missing = []
        for r in pack.approval_rules:
            for ref in r.source_refs:
                if ref.source_id not in by_id:
                    missing.append((r.id, ref.source_id))
        assert missing == []


# 2. MH approval -> source lookup
class TestMhApprovalSourceLookup:
    def test_apr043_cites_three_rules_one_source(self):
        pack = _mh_pack()
        ids = get_approval_source_ids(pack.approval_rules, "APR-043")
        assert ids == ["SRC-052"]

    def test_apr010_cites_two_sources(self):
        pack = _mh_pack()
        ids = get_approval_source_ids(pack.approval_rules, "APR-010")
        assert ids == ["SRC-013", "SRC-120"]

    def test_apr023_cites_boiler_sources(self):
        pack = _mh_pack()
        ids = get_approval_source_ids(pack.approval_rules, "APR-023")
        assert "SRC-034" in ids and "SRC-085" in ids

    def test_unknown_approval_empty(self):
        pack = _mh_pack()
        assert get_approval_citations(pack.sources, pack.approval_rules, "APR-999") == []

    def test_approval_citations_only_associated(self):
        pack = _mh_pack()
        cites = get_approval_citations(pack.sources, pack.approval_rules, "APR-006")
        assert [c.source_id for c in cites] == ["SRC-001"]
        assert all(c.jurisdiction == "IN-MH" for c in cites)


# 3. source metadata serialization
class TestSourceMetadataSerialization:
    def test_pack_citation_carries_metadata(self):
        pack = _mh_pack()
        cites = get_pack_citations_for_source_ids(
            pack.sources, ["SRC-001"], {"SRC-001": "Item 5(f)"}
        )
        assert len(cites) == 1
        c = cites[0]
        assert c.source_id == "SRC-001"
        assert c.title and c.authority and c.url.startswith("https://")
        assert c.jurisdiction == "IN-MH"
        assert c.checked_date == "2026-09-26"
        assert c.trust_tier == "T1"
        assert c.provision == "Item 5(f)"

    def test_missing_metadata_is_none_not_invented(self):
        c = Citation(
            source_id="X", title="T", authority="A", url="https://x",
            source_type="S", excerpt="E", relevance_rank=1.0,
        )
        assert c.jurisdiction is None
        assert c.provision is None
        assert c.url == "https://x"

    def test_official_url_preserved_not_fabricated(self):
        pack = _mh_pack()
        src = get_pack_source_by_id(pack.sources, "SRC-052")
        assert src is not None
        assert "cgwa-noc.gov.in" in src.url
        cites = get_pack_citations_for_source_ids(pack.sources, ["SRC-052"])
        assert cites[0].url == src.url


# 4/5/6. verified / conditional / partial display
class TestEvidenceStatusDisplay:
    def test_verified_source_display(self):
        pack = _mh_pack()
        cites = get_pack_citations_for_source_ids(pack.sources, ["SRC-001"])
        assert cites[0].trust_tier == "T1"
        exp = explain_approval(
            _mock_db(), "APR-006", pack.approval_rules,
            "APPLIES", "triggered",
            jurisdiction=IN_MH, pack_sources=list(pack.sources),
        )
        assert "verified" in exp.answer.lower()

    def test_conditional_source_display(self):
        pack = _mh_pack()
        cites = get_pack_citations_for_source_ids(pack.sources, ["SRC-017"])
        assert cites[0].trust_tier == "T3"
        exp = explain_approval(
            _mock_db(), "APR-026", pack.approval_rules,
            "APPLIES", "triggered",
            jurisdiction=IN_MH, pack_sources=list(pack.sources),
        )
        assert "conditional" in exp.answer.lower()

    def test_partial_evidence_for_conditional_result(self):
        pack = _mh_pack()
        exp = explain_approval(
            _mock_db(), "APR-001", pack.approval_rules,
            "CONDITIONAL", "needs data",
            jurisdiction=IN_MH, pack_sources=list(pack.sources),
        )
        assert exp.evidence_state == EvidenceState.PARTIAL


# 7/8. missing / nonexistent source
class TestMissingSources:
    def test_missing_source_returns_empty(self):
        pack = _mh_pack()
        assert get_pack_citations_for_source_ids(pack.sources, ["SRC-999"]) == []

    def test_nonexistent_source_id_is_none(self):
        pack = _mh_pack()
        assert get_pack_source_by_id(pack.sources, "NOPE") is None

    def test_explain_unknown_approval_has_no_citations(self):
        pack = _mh_pack()
        exp = explain_approval(
            _mock_db(), "APR-999", pack.approval_rules,
            "unknown", "", jurisdiction=IN_MH,
            pack_sources=list(pack.sources),
        )
        assert exp.citations == []


# 9/10/11. jurisdiction filtering
class TestJurisdictionIsolation:
    def test_mh_search_never_returns_gj(self):
        pack = _mh_pack()
        cites = search_pack_sources(pack.sources, "groundwater", limit=5)
        assert cites
        assert all(c.jurisdiction == "IN-MH" for c in cites)
        assert all(not c.source_id.startswith("S0") for c in cites)

    def test_gj_pack_has_no_mh_sources(self):
        gj = _gj_pack()
        ids = {s.id for s in gj.sources}
        assert "SRC-001" not in ids
        assert "S01" in ids

    def test_no_mh_to_gj_fallback(self):
        # DB holds no SRC-xxx rows; MH explain must use pack, never GJ Sxx.
        db = _mock_db()
        db.fetch_all.return_value = []
        pack = _mh_pack()
        exp = explain_approval(
            db, "APR-006", pack.approval_rules, "APPLIES", "r",
            jurisdiction=IN_MH, pack_sources=list(pack.sources),
        )
        assert [c.source_id for c in exp.citations] == ["SRC-001"]
        assert all(c.jurisdiction == "IN-MH" for c in exp.citations)

    def test_gj_isolation_preserved(self):
        gj = _gj_pack()
        cites = search_pack_sources(gj.sources, "GIDC water", limit=5)
        assert cites
        assert all(c.jurisdiction == "IN-GJ" for c in cites)

    def test_answer_query_mh_uses_pack_not_db(self):
        db = _mock_db()
        pack = _mh_pack()
        exp = answer_query(
            db, "groundwater NOC", limit=5,
            jurisdiction=IN_MH, pack_sources=list(pack.sources),
        )
        assert exp.citations
        assert all(c.jurisdiction == "IN-MH" for c in exp.citations)
        # Pack path never touches the DB chunk table.
        assert db.fetch_all.call_count == 0


# 12/13. evaluation-date + supersession handling
class TestEffectiveDateHandling:
    def test_none_date_preserves_behavior(self):
        pack = _mh_pack()
        assert len(filter_rules_by_effective_date(pack.approval_rules, None)) == 26

    def test_before_effective_excludes_rule_evidence(self):
        pack = _mh_pack()
        scoped = filter_rules_by_effective_date(pack.approval_rules, date(2020, 1, 1))
        ids = {r.id for r in scoped}
        # R-002 effective 2014 stays; boiler R-028 (2025) excluded.
        assert "R-002" in ids
        assert "R-028" not in ids
        assert get_rule_source_ids(scoped, "R-028") == []

    def test_after_effective_includes_rule(self):
        pack = _mh_pack()
        scoped = filter_rules_by_effective_date(pack.approval_rules, date(2026, 1, 1))
        assert "R-028" in {r.id for r in scoped}

    def test_no_silent_supersession_choice(self):
        # R-018 (SRC-013) and R-096 (SRC-120) both cite APR-010;
        # evidence lookup returns both, never picks one silently.
        pack = _mh_pack()
        cites = get_approval_citations(pack.sources, pack.approval_rules, "APR-010")
        assert sorted(c.source_id for c in cites) == ["SRC-013", "SRC-120"]


# 14/15/16/17. explanation per result (never invents law)
class TestExplanationResults:
    def _explain(self, result):
        pack = _mh_pack()
        return explain_approval(
            _mock_db(), "APR-006", pack.approval_rules, result, "reason",
            jurisdiction=IN_MH, pack_sources=list(pack.sources),
        )

    def test_applies_explanation_with_source(self):
        exp = self._explain("APPLIES")
        assert "applies" in exp.answer.lower()
        assert exp.citations
        assert exp.evidence_state == EvidenceState.SUFFICIENT

    def test_does_not_apply_explanation_with_source(self):
        exp = self._explain("DOES_NOT_APPLY")
        assert "does not apply" in exp.answer.lower()
        assert exp.evidence_state == EvidenceState.SUFFICIENT

    def test_conditional_explanation_with_source(self):
        exp = self._explain("CONDITIONAL")
        assert "conditionally" in exp.answer.lower()
        assert exp.evidence_state == EvidenceState.PARTIAL

    def test_insufficient_data_never_claims_decision(self):
        exp = self._explain("INSUFFICIENT_DATA")
        assert exp.evidence_state == EvidenceState.INSUFFICIENT
        lowered = exp.answer.lower()
        assert "insufficient" in lowered
        assert "approval required" not in lowered
        assert "not required" not in lowered

    def test_no_mandatory_claims_without_evidence(self):
        pack = _mh_pack()
        exp = answer_query(
            _mock_db(), "groundwater", jurisdiction=IN_MH,
            pack_sources=list(pack.sources),
        )
        lowered = exp.answer.lower()
        for banned in (" must ", " shall ", "mandatory", "deadline"):
            assert banned not in lowered


# 18/19/20. citations never change decisions/readiness/handoff
class TestRagMustNotDecide:
    def _orchestrate(self, facts):
        pack = _mh_pack()
        return orchestrate_application_full(
            application_id="T5",
            project_facts=dict(facts),
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=sorted({r.approval_id for r in pack.approval_rules}),
            document_requirements=pack.document_requirements,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval=None,
            approval_compositions=pack.approval_compositions,
        )

    def test_no_citation_changing_applicability(self):
        facts = load_canonical_mh_scenario()
        before = self._orchestrate(facts)
        pack = _mh_pack()
        cites = get_approval_citations(pack.sources, pack.approval_rules, "APR-006")
        assert cites
        after = self._orchestrate(facts)
        assert before.approvals["APR-006"].applicability_result == (
            after.approvals["APR-006"].applicability_result
        )

    def test_no_citation_changing_readiness(self):
        facts = load_canonical_mh_scenario()
        result = self._orchestrate(facts)
        assert result.approvals["APR-006"].status.value == "ready"
        assert result.approvals["APR-010"].status.value != "ready"

    def test_no_citation_changing_handoff(self):
        assert is_ready_to_handoff("ready") is True
        assert is_ready_to_handoff("blocked_by_documents") is False
        # Handoff gate depends only on readiness, never on citations.
        assert is_ready_to_handoff("insufficient_data") is False


# 21. What-If source preservation
class TestWhatIfSourcePreservation:
    def test_whatif_preserves_rule_sources(self):
        pack = _mh_pack()
        facts = load_canonical_mh_scenario()
        before_ids = get_approval_source_ids(pack.approval_rules, "APR-003")
        result = run_whatif_assessment(
            application_id="T5",
            base_facts=dict(facts),
            fact_overrides={"F-BLD-01": 90000},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=sorted({r.approval_id for r in pack.approval_rules}),
            document_requirements=pack.document_requirements,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval=None,
            jurisdiction=IN_MH,
            approval_compositions=pack.approval_compositions,
        )
        after_ids = get_approval_source_ids(pack.approval_rules, "APR-003")
        assert before_ids == after_ids == ["SRC-001", "SRC-179"]
        assert result.baseline is not None and result.what_if is not None


# 22/23. regulatory impact + rehearsal source preservation
class TestImpactRehearsalPreservation:
    def _inputs(self):
        pack = _mh_pack()
        facts = load_canonical_mh_scenario()
        return RehearsalInputs(
            base_facts=dict(facts),
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=sorted({r.approval_id for r in pack.approval_rules}),
            document_requirements=pack.document_requirements,
            approval_compositions=pack.approval_compositions,
            known_source_ids={s.id for s in pack.sources},
            evidence_registry=list(pack.evidence_gaps),
            evidence_hints=dict(pack.evidence_hints),
        )

    def test_source_metadata_change_preserves_sources(self):
        inputs = self._inputs()
        change = ChangeDescriptor(
            change_kind=ChangeKind.SOURCE_METADATA_CHANGE,
            source_id="SRC-001",
            old_value={"title": "a"},
            new_value={"title": "b"},
        )
        impact = rehearse_impact(change, inputs)
        assert "SRC-001" in impact.source_ids
        assert "APR-001" in impact.affected_approvals

    def test_rehearsal_unknown_source_rejected(self):
        inputs = self._inputs()
        change = ChangeDescriptor(
            change_kind=ChangeKind.SOURCE_METADATA_CHANGE,
            source_id="S01",
            old_value={"title": "a"},
            new_value={"title": "b"},
        )
        try:
            rehearse_impact(change, inputs)
        except Exception as exc:
            assert "Unknown source_id" in str(exc)
        else:
            raise AssertionError("GJ source must not rehearse in MH scope")


# 24. handoff source preservation + regression pins
class TestHandoffAndRegressionPins:
    def test_handoff_preserves_ready_gate(self):
        pack = _mh_pack()
        entry = pack.get_portal_entry("APR-006")
        assert entry is not None
        record = prepare_initiation("app", "APR-006", "ready", "tester", entry)
        assert record["status"] == "handed_off"
        try:
            prepare_initiation("app", "APR-010", "blocked_by_dependency", "t", entry)
        except Exception as exc:
            assert "only READY" in str(exc)
        else:
            raise AssertionError("non-ready handoff must fail")

    def test_roles_and_compositions_unchanged(self):
        pack = _mh_pack()
        roles = {r.id: r.role for r in pack.approval_rules}
        assert roles["R-002"] == RuleRole.CLASSIFICATION
        assert roles["R-043"] == RuleRole.EXEMPTION
        assert roles["R-044"] == RuleRole.EXEMPTION
        assert roles["R-030"] == RuleRole.TRIGGER
        assert roles["R-035"] == RuleRole.TRIGGER
        assert roles["R-077"] == RuleRole.TRIGGER
        # T4 result preserved: R-087 EXEMPTION under APR-023.
        assert roles["R-087"] == RuleRole.EXEMPTION
        assert set(pack.approval_compositions) == {"APR-001", "APR-043", "APR-023"}

    def test_default_jurisdiction_and_gj_isolation(self):
        assert DEFAULT_JURISDICTION == IN_GJ
        gj = _gj_pack()
        assert gj.approval_compositions == {}
        assert len(gj.approval_rules) == 19

    def test_orchestration_citation_enrichment(self):
        pack = _mh_pack()
        result = explain_orchestration_with_citations(
            _mock_db(), "APR-006", pack.approval_rules, "Status: READY",
            jurisdiction=IN_MH, pack_sources=list(pack.sources),
        )
        assert result.citations
        assert "SRC-001" in [c.source_id for c in result.citations]
        assert "Status: READY" in result.answer

    def test_api_models_accept_new_fields(self):
        c = Citation(
            source_id="SRC-001", title="T", authority="A",
            url="https://example.com", source_type="S",
            excerpt="E", relevance_rank=1.0, jurisdiction="IN-MH",
            checked_date="2026-09-26", trust_tier="T1", provision="s.1",
        )
        assert c.model_dump()["provision"] == "s.1"
        assert uuid4() is not None
        assert EvidenceStatus.NOT_ESTABLISHED.value == "NOT_ESTABLISHED"
