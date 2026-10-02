"""MH R-087 deemed-registration semantic migration (T4).

R-087 (Boilers Act 2025 s.45(2)(f), SRC-034, APR-023) is a
transitional deeming provision: boilers registered under the 1923
Act are deemed registered under the 2025 Act. As TRIGGER it
inverted the duty (TRUE demanded fresh s.12 registration); as
EXEMPTION it defeats an otherwise triggered APR-023 duty.

Covers: predicate, source/semantic interpretation, role,
APR-023 composition, threshold boundaries, missing/UNKNOWN,
fail-open falsification, readiness/dependency/handoff, What-If,
jurisdiction isolation, R-030 non-relationship, and regressions
of R-030 / R-043 / R-044 / R-077.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.handoff.service import (
    HandoffStateError,
    is_ready_to_handoff,
    prepare_initiation,
)
from app.orchestration.service import orchestrate_application
from app.orchestration.whatif import run_whatif_assessment
from app.regulatory.impact import (
    ChangeDescriptor,
    ChangeKind,
    RehearsalInputs,
    rehearse_impact,
)
from app.rules.applicability import (
    ApprovalResult,
    compose_approval_evaluations,
    evaluate_approval_applicability,
    evaluate_rule,
    summarize_by_approval,
)
from app.rules.dependency_engine import evaluate_readiness
from app.rules.dependency_models import (
    ApprovalDependency,
    ReadinessStatus,
)
from app.rules.facts import MH_FACTS, get_fact_spec
from app.rules.models import (
    ApplicabilityEvaluation,
    ApprovalComposition,
    RuleRole,
    SourceRef,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    load_mh_approval_authorities,
    load_mh_approval_compositions,
    load_mh_approval_rules,
)
from app.seed.pack import (
    DEFAULT_JURISDICTION,
    IN_GJ,
    IN_MH,
    load_regulatory_pack,
)

APPLIES = ApprovalResult.APPLIES.value
DNA = ApprovalResult.DOES_NOT_APPLY.value
COND = ApprovalResult.CONDITIONAL.value
INSUFF = ApprovalResult.INSUFFICIENT_DATA.value

_BOILER = {
    "F-BLR-04": True,
    "F-BLR-01": 30,
    "F-BLR-05": 2,
    "F-BLR-02": 2,
    "F-BLR-03": 150,
}


def _by_id(rule_id: str):
    for r in load_mh_approval_rules():
        if r.id == rule_id:
            return r
    raise KeyError(rule_id)


def _ev(
    rule_id: str,
    result: str,
    reason: str = "",
) -> ApplicabilityEvaluation:
    return ApplicabilityEvaluation(
        rule_id=rule_id,
        approval_id="APR-023",
        result=result,
        reason=reason or f"{rule_id} evaluated {result}",
        required_inputs=[],
        missing_inputs=[],
        authority="AUT-007",
        source_references=[
            SourceRef(source_id="SRC-034", citation_span="s.45(2)")
        ],
    )


def _orch(approval_id: str, facts: dict):
    pack = load_regulatory_pack(IN_MH)
    return orchestrate_application(
        application_id="T4-PROBE",
        approval_id=approval_id,
        project_facts=facts,
        approval_rules=pack.approval_rules,
        approval_authorities=pack.approval_authorities,
        dependencies=pack.dependencies,
        document_requirements=[],
        uploaded_documents=[],
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=set(),
        approval_compositions=pack.approval_compositions,
    )


class TestR087Predicate:
    def test_predicate_is_single_enum_leaf(self):
        rule = _by_id("R-087")
        assert len(rule.applicability_conditions) == 1
        leaf = rule.applicability_conditions[0]
        assert leaf.field == "F-BLR-07"
        assert leaf.op.value == "eq"
        assert leaf.value == "REGISTERED_UNDER_1923_ACT"

    def test_true_when_1923_registered(self):
        ev = evaluate_rule(
            _by_id("R-087"),
            {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
        )
        assert ev.result == APPLIES

    def test_false_when_not_registered(self):
        ev = evaluate_rule(
            _by_id("R-087"), {"F-BLR-07": "NOT_REGISTERED"}
        )
        assert ev.result == DNA

    def test_false_when_2025_registered(self):
        ev = evaluate_rule(
            _by_id("R-087"),
            {"F-BLR-07": "REGISTERED_UNDER_2025_ACT"},
        )
        assert ev.result == DNA

    def test_missing_fails_closed(self):
        ev = evaluate_rule(_by_id("R-087"), {})
        assert ev.result == INSUFF
        assert ev.missing_inputs == ["F-BLR-07"]

    def test_unknown_token_fails_closed(self):
        ev = evaluate_rule(
            _by_id("R-087"), {"F-BLR-07": "UNKNOWN"}
        )
        assert ev.result == INSUFF

    def test_none_fails_closed(self):
        ev = evaluate_rule(_by_id("R-087"), {"F-BLR-07": None})
        assert ev.result == INSUFF

    def test_certificate_date_not_in_predicate(self):
        # F-BLR-08 tracks certificate currency (s.45(2)(g));
        # it is not an applicability input.
        rule = _by_id("R-087")
        assert rule.applicability_conditions[0].field == "F-BLR-07"
        ev = evaluate_rule(
            rule,
            {
                "F-BLR-07": "REGISTERED_UNDER_1923_ACT",
                "F-BLR-08": "2026-12-31",
            },
        )
        assert ev.result == APPLIES

    def test_before_effective_window(self):
        ev = evaluate_rule(
            _by_id("R-087"),
            {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
            evaluation_date=date(2025, 4, 30),
        )
        assert ev.result == DNA
        assert "not in force" in ev.reason

    def test_effective_from_boundary(self):
        ev = evaluate_rule(
            _by_id("R-087"),
            {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
            evaluation_date=date(2025, 5, 1),
        )
        assert ev.result == APPLIES

    def test_missing_date_preserves_behavior(self):
        ev = evaluate_rule(
            _by_id("R-087"),
            {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
        )
        assert ev.result == APPLIES


class TestR087SourceAndSemantics:
    def test_source_is_src034_s45(self):
        rule = _by_id("R-087")
        assert rule.source_refs[0].source_id == "SRC-034"
        assert "s.45(2)" in rule.source_refs[0].citation_span
        assert rule.effective_from == date(2025, 5, 1)

    def test_targets_apr023_aut007(self):
        rule = _by_id("R-087")
        assert rule.approval_id == "APR-023"
        assert load_mh_approval_authorities()["APR-023"] == "AUT-007"

    def test_uses_boiler_fact_group(self):
        spec = get_fact_spec("IN-MH", "F-BLR-07")
        assert spec.group == "BLR"

    def test_is_not_petroleum(self):
        rule = _by_id("R-087")
        assert rule.approval_id not in ("APR-024", "APR-026")
        assert rule.applicability_conditions[0].field == "F-BLR-07"

    def test_is_not_classification(self):
        assert _by_id("R-087").role != RuleRole.CLASSIFICATION

    def test_deeming_relieves_fresh_registration(self):
        # s.45(2)(f): deemed registered -> no s.12 duty.
        # Composition-level proof lives in the truth-table
        # suite; here the raw rule fires on the status.
        ev = evaluate_rule(
            _by_id("R-087"),
            {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
        )
        assert ev.result == APPLIES


class TestR087RoleAndComposition:
    def test_role_is_exemption(self):
        assert _by_id("R-087").role == RuleRole.EXEMPTION

    def test_predicate_unmodified(self):
        rule = _by_id("R-087")
        assert rule.source_refs[0].source_id == "SRC-034"
        assert rule.effective_from == date(2025, 5, 1)
        assert rule.approval_id == "APR-023"

    def test_apr023_composition_names_all_rules(self):
        comp = load_mh_approval_compositions()["APR-023"]
        assert comp.triggers == ["R-028", "R-073", "R-086"]
        assert comp.exemptions == ["R-087"]
        assert comp.classifications == []

    def test_composition_roles_match_builders(self):
        roles = {r.id: r.role.value for r in load_mh_approval_rules()}
        assert roles["R-028"] == "trigger"
        assert roles["R-073"] == "trigger"
        assert roles["R-086"] == "trigger"
        assert roles["R-087"] == "exemption"

    def test_triggers_non_empty(self):
        comp = load_mh_approval_compositions()["APR-023"]
        assert len(comp.triggers) > 0

    def test_pack_serves_composition(self):
        pack = load_regulatory_pack(IN_MH)
        assert pack.approval_compositions["APR-023"].exemptions == [
            "R-087"
        ]

    def test_apr026_still_uncomposed(self):
        assert "APR-026" not in load_mh_approval_compositions()

    def test_r030_stays_trigger(self):
        assert _by_id("R-030").role == RuleRole.TRIGGER


class TestR030NonRelationship:
    def test_different_approvals_and_authorities(self):
        assert _by_id("R-030").approval_id == "APR-026"
        assert _by_id("R-087").approval_id == "APR-023"
        auths = load_mh_approval_authorities()
        assert auths["APR-026"] == "AUT-008 / AUT-009"
        assert auths["APR-023"] == "AUT-007"

    def test_disjoint_fact_groups(self):
        from app.rules.applicability import _collect_required_inputs

        assert _collect_required_inputs(_by_id("R-030")) == [
            "F-PET-01",
            "F-PET-02",
            "F-PET-04",
        ]
        assert _collect_required_inputs(_by_id("R-087")) == ["F-BLR-07"]

    def test_r030_raw_trigger_behavior_intact(self):
        ev = evaluate_rule(
            _by_id("R-030"),
            {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 500},
        )
        assert ev.result == APPLIES

    def test_r030_boundary_intact(self):
        ev = evaluate_rule(
            _by_id("R-030"),
            {"F-PET-01": "B", "F-PET-02": 2500, "F-PET-04": 1000},
        )
        assert ev.result == APPLIES
        ev2 = evaluate_rule(
            _by_id("R-030"),
            {"F-PET-01": "B", "F-PET-02": 2501, "F-PET-04": 1000},
        )
        assert ev2.result == DNA


class TestComposedTruthTable:
    def _compose(self, evals):
        pack = load_regulatory_pack(IN_MH)
        comp = pack.approval_compositions["APR-023"]
        return compose_approval_evaluations(comp, evals)

    def test_trigger_true_exemption_true_defeats(self):
        res = self._compose(
            [
                _ev("R-028", APPLIES, "boiler definition met"),
                _ev("R-073", DNA, "surface below threshold"),
                _ev("R-086", DNA, "already registered"),
                _ev("R-087", APPLIES, "deemed registered s.45(2)(f)"),
            ]
        )
        assert res.result == DNA
        assert "Exempt under R-087" in res.reason
        assert "would otherwise apply" in res.reason

    def test_trigger_true_exemption_false_applies(self):
        res = self._compose(
            [
                _ev("R-028", APPLIES),
                _ev("R-073", DNA),
                _ev("R-086", APPLIES),
                _ev("R-087", DNA),
            ]
        )
        assert res.result == APPLIES

    def test_trigger_true_exemption_unknown_conditional(self):
        res = self._compose(
            [
                _ev("R-028", APPLIES),
                _ev("R-073", DNA),
                _ev("R-086", INSUFF),
                _ev("R-087", INSUFF),
            ]
        )
        assert res.result == COND
        assert "R-087" in res.reason

    def test_trigger_false_exemption_true_still_dna(self):
        res = self._compose(
            [
                _ev("R-028", DNA),
                _ev("R-073", DNA),
                _ev("R-086", DNA),
                _ev("R-087", APPLIES),
            ]
        )
        assert res.result == DNA

    def test_trigger_false_exemption_false_dna(self):
        res = self._compose(
            [
                _ev("R-028", DNA),
                _ev("R-073", DNA),
                _ev("R-086", DNA),
                _ev("R-087", DNA),
            ]
        )
        assert res.result == DNA

    def test_trigger_unknown_exemption_true_never_applies(self):
        res = self._compose(
            [
                _ev("R-028", INSUFF),
                _ev("R-073", INSUFF),
                _ev("R-086", INSUFF),
                _ev("R-087", APPLIES),
            ]
        )
        assert res.result == INSUFF
        assert res.result != APPLIES

    def test_trigger_unknown_exemption_false_stays_unknown(self):
        res = self._compose(
            [
                _ev("R-028", INSUFF),
                _ev("R-073", INSUFF),
                _ev("R-086", INSUFF),
                _ev("R-087", DNA),
            ]
        )
        assert res.result == INSUFF

    def test_live_deemed_boiler_defeated(self):
        facts = dict(
            _BOILER, **{"F-BLR-06": 1500, "F-BLR-07": "REGISTERED_UNDER_1923_ACT"}
        )
        out = _orch("APR-023", facts)
        assert out.applicability_result == "does_not_apply"

    def test_live_unregistered_boiler_applies(self):
        facts = dict(
            _BOILER, **{"F-BLR-06": 500, "F-BLR-07": "NOT_REGISTERED"}
        )
        out = _orch("APR-023", facts)
        assert out.applicability_result == "applies"

    def test_live_unknown_defeater_blocks(self):
        facts = dict(_BOILER, **{"F-BLR-06": 1500})
        out = _orch("APR-023", facts)
        assert out.applicability_result == "conditional"


class TestFailOpenFalsification:
    def test_missing_never_false_negative(self):
        out = _orch("APR-023", {})
        assert out.applicability_result == "insufficient_data"
        assert out.applicability_result != "does_not_apply"

    def test_unknown_never_coerced_false(self):
        ev = evaluate_rule(
            _by_id("R-087"), {"F-BLR-07": "UNKNOWN"}
        )
        assert ev.result == INSUFF
        assert ev.result != DNA

    def test_exemption_true_alone_never_applies(self):
        comp = ApprovalComposition(
            approval_id="APR-023",
            triggers=["R-028"],
            exemptions=["R-087"],
        )
        res = compose_approval_evaluations(
            comp, [_ev("R-028", INSUFF), _ev("R-087", APPLIES)]
        )
        assert res.result != APPLIES

    def test_no_triggerless_composition(self):
        for comp in load_mh_approval_compositions().values():
            if comp.exemptions or comp.classifications:
                assert len(comp.triggers) > 0 or (
                    comp.approval_id == "APR-001"
                    and comp.classifications == ["R-002"]
                )
        assert "APR-026" not in load_mh_approval_compositions()

    def test_non_applicable_never_ready(self):
        graph = evaluate_readiness(
            dependencies=[],
            applicability_results={"APR-023": "does_not_apply"},
            obtained=set(),
        )
        assert graph.readiness["APR-023"].readiness == (
            ReadinessStatus.NOT_APPLICABLE
        )

    def test_exempted_cannot_satisfy_dependency(self):
        from app.api.orchestration import _TERMINAL_STATUSES

        assert _TERMINAL_STATUSES == frozenset({"approved"})
        graph = evaluate_readiness(
            dependencies=[
                ApprovalDependency(
                    approval_id="APR-DOWN",
                    prerequisite_approval_id="APR-023",
                    relationship="prerequisite",
                    source_ref="test",
                    evidence="test",
                    confidence="explicit",
                )
            ],
            applicability_results={
                "APR-DOWN": "applies",
                "APR-023": "conditional",
            },
            obtained=set(),
        )
        assert graph.readiness["APR-DOWN"].readiness == (
            ReadinessStatus.BLOCKED
        )

    def test_unresolved_never_handoff(self):
        assert is_ready_to_handoff("conditional") is False
        assert is_ready_to_handoff("not_applicable") is False
        with pytest.raises(HandoffStateError):
            prepare_initiation(
                "APP-T", "APR-023", "conditional", "tester"
            )


class TestReadinessDependencyHandoff:
    def test_applies_becomes_ready(self):
        facts = dict(
            _BOILER, **{"F-BLR-06": 500, "F-BLR-07": "NOT_REGISTERED"}
        )
        out = _orch("APR-023", facts)
        assert out.applicability_result == "applies"
        assert out.status.value == "ready"

    def test_defeat_becomes_not_applicable(self):
        facts = dict(
            _BOILER,
            **{
                "F-BLR-06": 500,
                "F-BLR-07": "REGISTERED_UNDER_1923_ACT",
            },
        )
        out = _orch("APR-023", facts)
        assert out.applicability_result == "does_not_apply"
        assert out.status.value == "not_applicable"
        assert out.status.value != "ready"

    def test_unresolved_stays_unresolved(self):
        out = _orch("APR-023", {})
        assert out.applicability_result == "insufficient_data"
        assert out.status.value == "insufficient_data"
        assert out.status.value != "ready"

    def test_canonical_no_boiler_still_dna(self):
        out = _orch("APR-023", {"F-BLR-04": False})
        assert out.applicability_result == "does_not_apply"
        assert out.status.value == "not_applicable"


class TestExecutionPaths:
    def test_direct_evaluation_path(self):
        pack = load_regulatory_pack(IN_MH)
        rules = [
            r for r in pack.approval_rules if r.approval_id == "APR-023"
        ]
        evals = evaluate_approval_applicability(
            rules, {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"}
        )
        assert {e.rule_id for e in evals} == {
            "R-028",
            "R-073",
            "R-086",
            "R-087",
        }

    def test_approval_summary_path(self):
        pack = load_regulatory_pack(IN_MH)
        rules = [
            r for r in pack.approval_rules if r.approval_id == "APR-023"
        ]
        facts = dict(
            _BOILER, **{"F-BLR-06": 500, "F-BLR-07": "NOT_REGISTERED"}
        )
        evals = evaluate_approval_applicability(rules, facts)
        out = summarize_by_approval(
            evals, compositions=pack.approval_compositions
        )["APR-023"]
        assert out.result == APPLIES

    def test_whatif_flip_path(self):
        pack = load_regulatory_pack(IN_MH)
        base = dict(
            _BOILER, **{"F-BLR-06": 500, "F-BLR-07": "NOT_REGISTERED"}
        )
        resp = run_whatif_assessment(
            application_id="APP-WHATIF-R087",
            base_facts=base,
            fact_overrides={"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=["APR-023"],
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval={},
            fact_provenance={},
            jurisdiction=IN_MH,
            approval_compositions=pack.approval_compositions,
        )
        assert resp.baseline.approvals["APR-023"].applicability_result == (
            "applies"
        )
        assert resp.what_if.approvals["APR-023"].applicability_result == (
            "does_not_apply"
        )

    def test_rehearsal_path(self):
        pack = load_regulatory_pack(IN_MH)
        inputs = RehearsalInputs(
            base_facts=dict(
                _BOILER,
                **{"F-BLR-06": 500, "F-BLR-07": "NOT_REGISTERED"},
            ),
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=["APR-023"],
            document_requirements=[],
            approval_compositions=pack.approval_compositions,
            known_source_ids={s.id for s in pack.sources},
        )
        impact = rehearse_impact(
            ChangeDescriptor(
                change_kind=ChangeKind.SOURCE_METADATA_CHANGE,
                source_id="SRC-034",
                old_value={"title": "Boilers Act 2025"},
                new_value={"title": "Boilers Act 2025 (amended)"},
            ),
            inputs,
        )
        assert "APR-023" in impact.affected_approvals

    def test_handoff_path(self):
        assert is_ready_to_handoff("ready") is True
        assert is_ready_to_handoff("not_applicable") is False
        with pytest.raises(HandoffStateError):
            prepare_initiation(
                "APP-T", "APR-023", "not_applicable", "tester"
            )

    def test_pack_path(self):
        pack = load_regulatory_pack(IN_MH)
        assert "R-087" in {r.id for r in pack.approval_rules}
        assert pack.approval_compositions["APR-023"].triggers == [
            "R-028",
            "R-073",
            "R-086",
        ]


class TestJurisdictionIsolation:
    def test_gj_untouched(self):
        gj = load_regulatory_pack(IN_GJ)
        assert len(gj.approval_rules) == 19
        assert gj.approval_compositions == {}
        assert all(r.role.value == "trigger" for r in gj.approval_rules)
        assert DEFAULT_JURISDICTION == IN_GJ

    def test_no_gj_source_leakage(self):
        gj_ids = {
            r.id for r in load_regulatory_pack(IN_GJ).approval_rules
        }
        assert "R-087" not in gj_ids
        assert "R-030" not in gj_ids

    def test_mh_counts(self):
        mh = load_regulatory_pack(IN_MH)
        assert len(mh.approval_rules) == 26
        assert len(MH_DEFERRED_RULES) == 61
        assert len(MH_FACTS) == 128
        assert set(MH_INCLUDED_RULE_IDS) == {
            r.id for r in mh.approval_rules
        }


class TestSiblingRegressions:
    def test_r043_r044_still_exemption(self):
        roles = {r.id: r.role.value for r in load_mh_approval_rules()}
        assert roles["R-043"] == "exemption"
        assert roles["R-044"] == "exemption"
        comp = load_mh_approval_compositions()["APR-043"]
        assert comp.triggers == ["R-077"]
        assert comp.exemptions == ["R-043", "R-044"]

    def test_r077_still_trigger(self):
        assert _by_id("R-077").role == RuleRole.TRIGGER

    def test_r035_still_trigger(self):
        assert _by_id("R-035").role == RuleRole.TRIGGER
        assert _by_id("R-035").approval_id == "APR-029"
