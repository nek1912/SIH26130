"""MH batch-1 pack dimensions: deps/docs/evidence + scenarios (Phase 4).

Scenarios use real MH pack data through the real orchestration path:
A clean READY, B missing dependency, C missing document, D evidence
gap, E DOES_NOT_APPLY, F INSUFFICIENT_DATA.
"""
from __future__ import annotations

from pathlib import Path

from app.orchestration.service import orchestrate_application_full
from app.rules.dependency_engine import evaluate_readiness
from app.seed.mh.dependencies import (
    MH_DEP_DEFERRED,
    load_mh_approval_dependencies,
)
from app.seed.mh.documents import (
    MH_DEFERRED_DOCUMENTS,
    load_mh_document_requirements,
)
from app.seed.mh.evidence import (
    MH_EVIDENCE_HINTS,
    load_mh_evidence_gaps,
)
from app.seed.pack import IN_GJ, IN_MH, load_regulatory_pack


def _mh_scope():
    pack = load_regulatory_pack(IN_MH)
    return pack, sorted({r.approval_id for r in pack.approval_rules})


def _run(pack, aids, facts, **kwargs):
    params = {
        "application_id": "MH-DIM",
        "project_facts": dict(facts),
        "approval_rules": pack.approval_rules,
        "approval_authorities": pack.approval_authorities,
        "dependencies": pack.dependencies,
        "all_approval_ids": list(aids),
        "document_requirements": pack.document_requirements,
        "uploaded_documents": [],
        "extraction_results": [],
        "validation_results": [],
        "consistency_result": None,
        "sla_info": None,
        "obtained_approvals": set(),
        "evidence_gaps_by_approval": {
            aid: pack.get_gaps_for_approval(aid) for aid in aids
        },
    }
    params.update(kwargs)
    return orchestrate_application_full(**params)


class TestMHDependencies:
    def test_two_explicit_edges_loaded(self):
        deps = load_mh_approval_dependencies()
        assert len(deps) == 2
        assert {(d.approval_id, d.prerequisite_approval_id) for d in deps} == {
            ("APR-010", "APR-008"),
            ("APR-010", "APR-009"),
        }

    def test_edges_carry_dep009_traceability(self):
        for dep in load_mh_approval_dependencies():
            assert "DEP-009" in dep.evidence
            assert dep.confidence == "explicit"
            assert dep.relationship == "document_prerequisite"
            assert dep.source_ref == "SRC-013 r.6"

    def test_all_34_register_rows_triaged(self):
        # 34 register rows = DEP-009 (loaded as 2 edges) + 33 deferred.
        assert len(MH_DEP_DEFERRED) == 33
        assert "DEP-020" in MH_DEP_DEFERRED  # facilitation never an edge
        assert "DEP-002" in MH_DEP_DEFERRED  # UNKNOWN never a hard blocker
        assert "DEP-013" in MH_DEP_DEFERRED  # ROC never a hard blocker

    def test_graph_integrity(self):
        deps = load_mh_approval_dependencies()
        pairs = [(d.approval_id, d.prerequisite_approval_id) for d in deps]
        assert len(set(pairs)) == len(pairs)
        assert all(a != p for a, p in pairs)
        graph = evaluate_readiness(
            deps,
            {"APR-010": "applies", "APR-008": "applies",
             "APR-009": "applies"},
            obtained=set(),
        )
        assert graph.has_cycles is False
        assert graph.readiness["APR-010"].readiness.value == "blocked"
        freed = evaluate_readiness(
            deps,
            {"APR-010": "applies", "APR-008": "applies",
             "APR-009": "applies"},
            obtained={"APR-008", "APR-009"},
        )
        assert freed.readiness["APR-010"].readiness.value == "ready"


class TestMHDocuments:
    def test_four_verified_rows_loaded(self):
        reqs = load_mh_document_requirements()
        assert {r["requirement_key"] for r in reqs} == {
            "DOC-001", "DOC-002", "DOC-003", "DOC-008"
        }

    def test_approval_refs_resolve_to_batch_scope(self):
        pack = load_regulatory_pack(IN_MH)
        batch = {r.approval_id for r in pack.approval_rules} | {
            "APR-030", "APR-032"
        }
        for req in load_mh_document_requirements():
            assert req["approval_ids"], req["requirement_key"]
            assert set(req["approval_ids"]) <= batch, req["requirement_key"]
            assert any(
                a in {r.approval_id for r in pack.approval_rules}
                for a in req["approval_ids"]
            ), req["requirement_key"]

    def test_mandatory_levels_and_traceability(self):
        for req in load_mh_document_requirements():
            assert req["requirement_level"] == "required", req["requirement_key"]
            assert req["document_name"], req["requirement_key"]
            assert req["source_basis"], req["requirement_key"]
            assert req["source_url"].startswith("https://"), req[
                "requirement_key"
            ]

    def test_no_invented_requirements(self):
        deferred = set(MH_DEFERRED_DOCUMENTS)
        assert deferred == {
            "DOC-004", "DOC-005", "DOC-006", "DOC-007", "DOC-009",
            "DOC-010", "DOC-011", "DOC-012",
        }
        loaded = {r["requirement_key"] for r in load_mh_document_requirements()}
        assert loaded & deferred == set()

    def test_apr043_left_empty_explicitly(self):
        pack = load_regulatory_pack(IN_MH)
        assert pack.get_requirements_for_approval("APR-043") == []


class TestMHEvidence:
    def test_three_advisory_records_loaded(self):
        gaps = load_mh_evidence_gaps()
        assert {g.evidence_id for g in gaps} == {"UR-06", "UR-11", "DOC-012"}

    def test_hints_resolve_to_batch_approvals(self):
        pack = load_regulatory_pack(IN_MH)
        batch = {r.approval_id for r in pack.approval_rules}
        assert set(MH_EVIDENCE_HINTS) == {"UR-06", "UR-11", "DOC-012"}
        for eid, codes in MH_EVIDENCE_HINTS.items():
            assert set(codes) <= batch, eid
        assert [g.evidence_id for g in pack.get_gaps_for_approval("APR-001")] == [
            "UR-06"
        ]
        assert [g.evidence_id for g in pack.get_gaps_for_approval("APR-055")] == [
            "UR-11"
        ]
        assert [g.evidence_id for g in pack.get_gaps_for_approval("APR-043")] == [
            "DOC-012"
        ]
        assert pack.get_gaps_for_approval("APR-006") == []

    def test_gap_statuses_are_never_applies(self):
        statuses = {g.status.value for g in load_mh_evidence_gaps()}
        assert statuses <= {"NOT_ESTABLISHED", "PARTIAL"}
        assert "VERIFIED" not in statuses


class TestScenarios:
    def test_a_applies_with_prerequisites_available_is_ready(self):
        pack, aids = _mh_scope()
        result = _run(pack, aids, {"F-PRD-02": ["PESTICIDE_TECHNICAL"]})
        orch = result.approvals["APR-006"]
        assert orch.applicability_result == "applies"
        assert orch.status.value == "ready"
        assert orch.blockers == []

    def test_b_missing_dependency_blocks(self):
        pack, aids = _mh_scope()
        blocked = _run(pack, aids, {"F-HW-01": True})
        orch = blocked.approvals["APR-010"]
        assert orch.applicability_result == "applies"
        assert orch.status.value == "blocked_by_dependency"
        # The dependency dimension drives status + explanation while
        # the missing mandatory DOC-001/002/003 surface as document
        # blockers alongside (status priority ranks the dependency).
        assert "Dependencies:" in orch.explanation
        assert "blocked" in orch.explanation
        assert {b.affected_document_key for b in orch.blockers} == {
            "DOC-001", "DOC-002", "DOC-003"
        }
        # Obtained CTE/CTO unblock the dependency dimension; the
        # missing mandatory DOC-001/002/003 then surface as documents.
        freed = _run(
            pack, aids, {"F-HW-01": True},
            obtained_approvals={"APR-008", "APR-009"},
        )
        orch = freed.approvals["APR-010"]
        assert orch.status.value == "blocked_by_documents"
        assert any(
            b.affected_document_key == "DOC-001" for b in orch.blockers
        )

    def test_c_missing_required_document_blocks(self):
        pack, aids = _mh_scope()
        result = _run(
            pack, aids,
            {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 900},
        )
        orch = result.approvals["APR-026"]
        assert orch.applicability_result == "applies"
        assert orch.status.value == "blocked_by_documents"
        assert any(
            b.affected_document_key == "DOC-008" for b in orch.blockers
        )

    def test_d_evidence_gap_fails_closed(self):
        pack, aids = _mh_scope()
        result = _run(
            pack, aids,
            {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False},
        )
        orch = result.approvals["APR-001"]
        # Deterministic applicability still decides ...
        assert orch.applicability_result == "applies"
        # ... but the UR-06 gap fails the overall status closed.
        assert orch.status.value == "insufficient_data"
        assert any(
            b.evidence_id == "UR-06" for b in orch.blockers
        )

    def test_e_does_not_apply_creates_no_blockers(self):
        pack, aids = _mh_scope()
        result = _run(pack, aids, {"F-BLD-01": 1000})
        orch = result.approvals["APR-003"]
        assert orch.applicability_result == "does_not_apply"
        assert orch.status.value == "not_applicable"
        assert orch.blockers == []

    def test_f_insufficient_stays_distinguishable(self):
        pack, aids = _mh_scope()
        result = _run(pack, aids, {})
        orch = result.approvals["APR-010"]
        assert orch.applicability_result == "insufficient_data"
        assert orch.status.value == "insufficient_data"
        assert orch.applicability_result != "does_not_apply"


class TestIsolation:
    def test_gj_pack_dimensions_unchanged(self):
        pack = load_regulatory_pack(IN_GJ)
        assert len(pack.dependencies) == 3
        assert len(pack.document_requirements) == 17
        assert len(pack.evidence_gaps) == 12
        assert len(pack.portal_entries) == 18

    def test_mh_dims_contain_no_gj_ids(self):
        pack = load_regulatory_pack(IN_MH)
        dep_ids = {d.approval_id for d in pack.dependencies} | {
            d.prerequisite_approval_id for d in pack.dependencies
        }
        doc_approvals = {
            a for r in pack.document_requirements for a in r["approval_ids"]
        }
        hint_targets = {
            a for codes in MH_EVIDENCE_HINTS.values() for a in codes
        }
        for ident in dep_ids | doc_approvals | hint_targets:
            assert not ident.startswith("A0"), ident
        assert {r["requirement_key"] for r in pack.document_requirements} == {
            "DOC-001", "DOC-002", "DOC-003", "DOC-008"
        }
        assert {r["requirement_key"] for r in pack.document_requirements} & {
            "D01", "D02",
        } == set()

    def test_mh_modules_import_no_gj_seed(self):
        import app.seed.mh.dependencies as mh_deps
        import app.seed.mh.documents as mh_docs
        import app.seed.mh.evidence as mh_evidence

        for module in (mh_deps, mh_docs, mh_evidence):
            source = Path(module.__file__).read_text(encoding="utf-8")
            assert "app.seed.approvals" not in source, module.__name__
            assert "app.seed.handoff" not in source, module.__name__
            assert "IN-GJ" not in source, module.__name__
