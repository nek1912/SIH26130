"""MH source corpus + portal catalog (Phase 5).

Display/citation/navigation metadata only. Nothing here may alter a
deterministic decision: sources explain assertions, portal entries
navigate to external workflows/references.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.orchestration.service import orchestrate_application_full
from app.seed.mh.portals import (
    is_portal_cta,
    load_mh_portal_entries,
)
from app.seed.mh.sources import MH_LOADED_SOURCE_IDS, load_mh_sources
from app.seed.pack import IN_GJ, IN_MH, load_regulatory_pack

_SRC_RE = re.compile(r"SRC-\d+")


def _mh_sources_by_id():
    return {s.id: s for s in load_mh_sources()}


class TestSourceCorpus:
    def test_sources_loaded(self):
        sources = load_mh_sources()
        assert len(sources) == 22
        assert {s.id for s in sources} == set(MH_LOADED_SOURCE_IDS)
        assert MH_LOADED_SOURCE_IDS == {
            "SRC-001", "SRC-013", "SRC-017", "SRC-026", "SRC-031",
            "SRC-034", "SRC-043", "SRC-044", "SRC-052", "SRC-081",
            "SRC-085", "SRC-092", "SRC-100", "SRC-102", "SRC-112",
            "SRC-113", "SRC-114", "SRC-117", "SRC-120", "SRC-135",
            "SRC-136", "SRC-179",
        }

    def test_tiers_preserved_verbatim(self):
        by_id = _mh_sources_by_id()
        assert by_id["SRC-001"].trust_tier == "T1"
        assert by_id["SRC-017"].trust_tier == "T3"
        assert by_id["SRC-044"].trust_tier == "T3"
        assert by_id["SRC-120"].trust_tier == "T2"
        assert {s.trust_tier for s in by_id.values()} <= {"T1", "T2", "T3"}

    def test_source_types_preserved(self):
        by_id = _mh_sources_by_id()
        assert by_id["SRC-001"].source_type == "OFFICIAL_PRIMARY"
        assert by_id["SRC-043"].source_type == "OFFICIAL_PORTAL"
        assert by_id["SRC-179"].source_type == "COURT_ORDER"
        assert by_id["SRC-135"].source_type == "CENTRAL_RULES"

    def test_jurisdiction_and_class(self):
        for source in load_mh_sources():
            assert source.jurisdiction == "IN-MH", source.id
            assert source.authority, source.id
            assert source.title, source.id
            assert source.checked_date, source.id

    def test_urls_exact_and_present(self):
        by_id = _mh_sources_by_id()
        assert by_id["SRC-001"].url == (
            "https://parivesh.nic.in/publicdocument/"
            "UPLOAD_OM_NOTIFICATION/IA_DOCS/1018_23072026010355.pdf"
        )
        assert by_id["SRC-179"].url == (
            "https://parivesh.nic.in/publicdocument/"
            "UPLOAD_OM_NOTIFICATION/IA_DOCS/1002_01092025113231.pdf"
        )
        for source in by_id.values():
            assert source.url.startswith("https://"), source.id
            assert "UNKNOWN" not in source.url, source.id

    def test_prove_and_does_not_prove_distinct(self):
        for source in load_mh_sources():
            assert "PROVES:" in source.notes, source.id
            assert "DOES_NOT_PROVE:" in source.notes, source.id
        assert "8(a) EC" in _mh_sources_by_id()["SRC-001"].notes
        assert "DOES_NOT_PROVE" in _mh_sources_by_id()["SRC-179"].notes


class TestSourceResolution:
    def test_every_rule_sourceref_resolves(self):
        by_id = _mh_sources_by_id()
        pack = load_regulatory_pack(IN_MH)
        for rule in pack.approval_rules:
            assert rule.source_refs, rule.id
            for ref in rule.source_refs:
                assert ref.source_id in by_id, (rule.id, ref.source_id)
                assert ref.citation_span, (rule.id, ref.source_id)

    def test_dependency_sources_resolve(self):
        by_id = _mh_sources_by_id()
        for dep in load_regulatory_pack(IN_MH).dependencies:
            sid = dep.source_ref.split()[0]
            assert sid in by_id, dep.source_ref

    def test_document_sources_resolve(self):
        by_id = _mh_sources_by_id()
        for req in load_regulatory_pack(IN_MH).document_requirements:
            sids = set(_SRC_RE.findall(req["source_basis"]))
            assert sids, req["requirement_key"]
            assert sids <= set(by_id), (req["requirement_key"], sids)
            assert req["source_url"].startswith("https://")

    def test_evidence_source_claims_resolve_where_claimed(self):
        by_id = _mh_sources_by_id()
        assert "SRC-052" in by_id
        gaps = {
            g.evidence_id: g
            for g in load_regulatory_pack(IN_MH).evidence_gaps
        }
        assert "SRC-052" in (
            gaps["DOC-012"].verified_scope + gaps["DOC-012"].source_reference
        )
        # UR records claim register references, not SRC IDs (explicitly
        # allowed: no SRC invented for them).
        assert "UR-06" in gaps["UR-06"].source_reference
        assert "UR-11" in gaps["UR-11"].source_reference


class TestPortalCatalog:
    def test_14_entries_two_kinds_only(self):
        entries = load_mh_portal_entries()
        assert len(entries) == 14
        kinds = {e["portal_kind"] for e in entries}
        assert kinds <= {"portal", "reference"}

    def test_portal_entries_have_usable_urls(self):
        for entry in load_mh_portal_entries():
            if entry["portal_kind"] == "portal":
                assert is_portal_cta(entry), entry["portal_id"]
                assert entry["portal_url"].startswith("https://")

    def test_reference_entries_are_not_ctas(self):
        refs = [
            e for e in load_mh_portal_entries()
            if e["portal_kind"] == "reference"
        ]
        assert refs, "expected reference entries"
        for entry in refs:
            assert not is_portal_cta(entry), entry["portal_id"]

    def test_por003_style_missing_url_is_never_a_cta(self):
        missing = {
            "portal_kind": "portal",
            "portal_url": "UNKNOWN (portal URL not located)",
        }
        assert not is_portal_cta(missing)
        empty = {"portal_kind": "reference", "portal_url": ""}
        assert not is_portal_cta(empty)
        # And the loader itself refuses portal-kind entries without URLs.
        assert all(
            is_portal_cta(e)
            for e in load_mh_portal_entries()
            if e["portal_kind"] == "portal"
        )

    def test_no_duplicate_portal_keys(self):
        keys = [
            (e["approval_code"], e["portal_id"])
            for e in load_mh_portal_entries()
        ]
        assert len(set(keys)) == len(keys)

    def test_portal_ids_are_mh_only(self):
        for entry in load_mh_portal_entries():
            assert entry["portal_id"].startswith("POR-"), entry
            assert entry["approval_code"].startswith(
                ("APR-", "CMP-")
            ), entry

    def test_expected_batch1_coverage(self):
        by_approval: dict[str, list] = {}
        for entry in load_mh_portal_entries():
            by_approval.setdefault(entry["approval_code"], []).append(entry)
        assert {e["portal_id"] for e in by_approval["APR-001"]} == {"POR-001"}
        assert {e["portal_id"] for e in by_approval["APR-010"]} == {
            "POR-002", "POR-008"
        }
        assert {e["portal_id"] for e in by_approval["APR-026"]} == {"POR-007"}
        assert {e["portal_id"] for e in by_approval["APR-043"]} == {"POR-010"}
        portal_kinds = {
            e["portal_id"]: e["portal_kind"] for e in load_mh_portal_entries()
        }
        assert portal_kinds["POR-001"] == "portal"
        assert portal_kinds["POR-002"] == "portal"
        assert portal_kinds["POR-007"] == "portal"
        assert portal_kinds["POR-010"] == "portal"
        assert portal_kinds["POR-005"] == "reference"
        assert portal_kinds["POR-006"] == "reference"
        assert portal_kinds["POR-008"] == "reference"
        assert portal_kinds["POR-008G"] == "reference"

    def test_no_maitri_entry(self):
        entries = load_mh_portal_entries()
        assert not any(e["portal_id"] == "POR-013" for e in entries)
        assert not any("MAITRI" in e["external_system"] for e in entries)

    def test_no_gj_portal_urls(self):
        gj = load_regulatory_pack(IN_GJ).portal_entries
        gj_urls = {e["portal_url"] for e in gj}
        for entry in load_mh_portal_entries():
            assert entry["portal_url"] not in gj_urls, entry["portal_id"]


class TestEndToEndTraceability:
    def test_rule_to_source_chain(self):
        pack = load_regulatory_pack(IN_MH)
        by_id = _mh_sources_by_id()
        rule = next(r for r in pack.approval_rules if r.id == "R-030")
        ref = next(
            s for s in rule.source_refs if s.source_id == "SRC-017"
        )
        source = by_id[ref.source_id]
        assert "PESO" in source.title
        assert "Class B" in source.notes

    def test_dependency_to_source_to_portal_chain(self):
        pack = load_regulatory_pack(IN_MH)
        by_id = _mh_sources_by_id()
        dep = next(
            d for d in pack.dependencies
            if d.prerequisite_approval_id == "APR-008"
        )
        assert dep.source_ref.split()[0] == "SRC-013"
        assert "Hazardous and Other Wastes" in by_id["SRC-013"].title
        portals = [
            e for e in pack.portal_entries
            if e["approval_code"] == "APR-010"
            and e["portal_kind"] == "portal"
        ]
        assert portals and portals[0]["portal_id"] == "POR-002"

    def test_document_to_source_to_portal_chain(self):
        pack = load_regulatory_pack(IN_MH)
        by_id = _mh_sources_by_id()
        req = next(
            r for r in pack.document_requirements
            if r["requirement_key"] == "DOC-008"
        )
        assert "SRC-017" in req["source_basis"]
        assert "PESO" in by_id["SRC-017"].title
        assert req["source_url"] == by_id["SRC-017"].url
        portals = [
            e for e in pack.portal_entries
            if e["approval_code"] == "APR-026"
        ]
        assert len(portals) == 1
        assert portals[0]["portal_url"].startswith("https://online.peso")

    def test_evidence_to_source_chain(self):
        pack = load_regulatory_pack(IN_MH)
        by_id = _mh_sources_by_id()
        gaps = {g.evidence_id: g for g in pack.evidence_gaps}
        assert "SRC-052" in gaps["DOC-012"].verified_scope
        assert "CGWA" in by_id["SRC-052"].title
        portals = [
            e for e in pack.portal_entries
            if e["approval_code"] == "APR-043"
            and e["portal_kind"] == "portal"
        ]
        assert portals and portals[0]["portal_id"] == "POR-010"


class TestIsolation:
    def test_gj_sources_and_portals_unchanged(self):
        pack = load_regulatory_pack(IN_GJ)
        assert len(pack.sources) == 32
        assert {s.id for s in pack.sources} == {
            f"S{i:02d}" for i in list(range(1, 32)) + [33]
        }
        assert len(pack.portal_entries) == 18

    def test_mh_source_ids_are_mh_only(self):
        mh_ids = {s.id for s in load_regulatory_pack(IN_MH).sources}
        assert all(i.startswith("SRC-") for i in mh_ids)
        gj_ids = {s.id for s in load_regulatory_pack(IN_GJ).sources}
        assert mh_ids & gj_ids == set()

    def test_mh_source_modules_import_no_gj_seed(self):
        import app.seed.mh.portals as mh_portals
        import app.seed.mh.sources as mh_sources

        for module in (mh_portals, mh_sources):
            source = Path(module.__file__).read_text(encoding="utf-8")
            assert "app.seed.sources" not in source, module.__name__
            assert "app.seed.handoff" not in source, module.__name__
            assert "IN-GJ" not in source, module.__name__


class TestDecisionsUnchanged:
    def _run(self, facts):
        pack = load_regulatory_pack(IN_MH)
        aids = sorted({r.approval_id for r in pack.approval_rules})
        return orchestrate_application_full(
            application_id="MH-P5",
            project_facts=dict(facts),
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=aids,
            document_requirements=pack.document_requirements,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval={
                aid: pack.get_gaps_for_approval(aid) for aid in aids
            },
            approval_compositions=pack.approval_compositions,
        )

    def test_ready_case_unchanged_with_sources_loaded(self):
        result = self._run({"F-PRD-02": ["PESTICIDE_TECHNICAL"]})
        orch = result.approvals["APR-006"]
        assert orch.applicability_result == "applies"
        assert orch.status.value == "ready"

    def test_evidence_case_unchanged_with_sources_loaded(self):
        result = self._run(
            {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False}
        )
        orch = result.approvals["APR-001"]
        # P0 MIGRATION (§16 design): R-002 CLASSIFICATION alone →
        # INSUFFICIENT_DATA (see test_apr001_evidence_fail_closed).
        assert orch.applicability_result == "insufficient_data"
        assert orch.status.value == "insufficient_data"
        assert any(b.evidence_id == "UR-06" for b in orch.blockers)
