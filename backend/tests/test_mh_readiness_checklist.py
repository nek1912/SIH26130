"""Phase 8 Gate A readiness checklist (explicit IN-MH context only).

This suite proves the MH runtime is TECHNICALLY ready. It does not
flip the default and does not resolve N-2 / persisted-data safety —
those gates are evaluated in the Phase 8 report, not here. API-level
coverage lives in test_mh_api_e2e.py; this file pins pack + engine
gate criteria.
"""
from __future__ import annotations

from datetime import date

from app.orchestration.whatif import apply_fact_overrides
from app.rules.applicability import evaluate_rule
from app.rules.facts import MH_FACTS
from app.rules.models import LiteralNode
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_DO_NOT_IMPLEMENT_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    MH_UNKNOWN_RULE_IDS,
    load_mh_approval_rules,
)
from app.seed.mh.sources import MH_LOADED_SOURCE_IDS
from app.seed.pack import IN_MH, load_regulatory_pack


def _pack():
    return load_regulatory_pack(IN_MH)


class TestRegulatoryDataGate:
    def test_pack_loads_with_19_safe_rules(self):
        pack = _pack()
        assert {r.id for r in pack.approval_rules} == set(
            MH_INCLUDED_RULE_IDS
        )

    def test_held_unknown_dni_excluded(self):
        packed = {r.id for r in _pack().approval_rules}
        assert packed & MH_REQUIRES_CONFIRMATION_RULE_IDS == set()
        assert packed & MH_DO_NOT_IMPLEMENT_RULE_IDS == set()
        assert packed & MH_UNKNOWN_RULE_IDS == set()
        assert packed & set(MH_DEFERRED_RULES) == set()

    def test_sources_portals_deps_docs_evidence_sla_resolve(self):
        pack = _pack()
        assert {s.id for s in pack.sources} == set(MH_LOADED_SOURCE_IDS)
        assert len(pack.portal_entries) == 14
        assert len(pack.dependencies) == 2
        assert len(pack.document_requirements) == 4
        assert len(pack.evidence_gaps) == 3
        assert len(pack.sla_records) == 10
        rule_srcs = {
            ref.source_id
            for r in pack.approval_rules
            for ref in r.source_refs
        }
        assert rule_srcs <= {s.id for s in pack.sources}

    def test_consistency_intentionally_empty(self):
        assert _pack().consistency_rules == []

    def test_registry_covers_rule_facts(self):
        from tests.test_mh_pack import _leaf_fields

        known = set(MH_FACTS)
        for rule in _pack().approval_rules:
            fields: set[str] = set()
            for tree in rule.applicability_conditions:
                fields |= _leaf_fields(tree)
            assert fields <= known, rule.id


class TestEngineGate:
    def test_unknown_literal_fail_closed(self):
        from app.rules.models import ApprovalRule

        rule = ApprovalRule(
            id="CHK", approval_id="APR-001",
            applicability_conditions=[LiteralNode(value="unknown")],
            version="v5",
        )
        assert evaluate_rule(rule, {}).result == "insufficient_data"

    def test_not_applicable_semantics(self):
        from app.rules.models import ApprovalRule

        rule = ApprovalRule(
            id="CHK", approval_id="APR-001",
            applicability_conditions=[
                LiteralNode(value="not_applicable")
            ],
            version="v5",
        )
        assert evaluate_rule(rule, {}).result == "does_not_apply"

    def test_effective_window(self):
        rule = next(
            r for r in load_mh_approval_rules() if r.id == "R-094"
        )
        facts = {"F-EEE-01": 1000}
        assert evaluate_rule(
            rule, facts, evaluation_date=date(2023, 4, 1)
        ).result == "applies"
        assert evaluate_rule(
            rule, facts, evaluation_date=date(2023, 3, 31)
        ).result == "does_not_apply"

    def test_whatif_mh_registry(self):
        merged = apply_fact_overrides(
            {"F-BLD-01": 30000}, {"F-BLD-01": 1000},
            jurisdiction=IN_MH,
        )
        assert merged == {"F-BLD-01": 1000}

    def test_rehearsal_inputs_from_pack(self):
        from app.regulatory.impact import RehearsalInputs

        pack = _pack()
        inputs = RehearsalInputs(
            base_facts={},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=sorted(
                {r.approval_id for r in pack.approval_rules}
            ),
            document_requirements=pack.document_requirements,
            known_source_ids={s.id for s in pack.sources},
            evidence_registry=list(pack.evidence_gaps),
            evidence_hints=dict(pack.evidence_hints),
        )
        assert inputs.known_source_ids is not None
        assert "SRC-001" in inputs.known_source_ids
