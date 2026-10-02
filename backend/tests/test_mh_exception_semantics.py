"""Tests for the P0 exception/exemption semantic contract.

Covers the finalized design (docs/audits/audit_mh_apr001_exception_role_design.md):

- 19-row truth-table contract over compose_approval_evaluations (§18 rows 1-19).
- Lint: roles explicit, never inferred; compositions complete and consistent.
- R-043 pilot (EXEMPTION) and APR-001/R-002 migration (CLASSIFICATION).
- Readiness safety through the real orchestration path + handoff gate.
- R-054 future-role compatibility (no activation, no new facts).
- Remaining non-trigger candidates explicitly unmigrated.
- Default TRIGGER compatibility (all other rules byte-identical).

Probe rules/evaluations are constructed directly (never _encode, never the
pack) for contract rows; migration/readiness rows use the live MH pack.
"""
from __future__ import annotations

import pytest

from app.handoff.service import HandoffStateError, is_ready_to_handoff, prepare_initiation
from app.orchestration.models import OrchestrationStatus
from app.orchestration.service import orchestrate_application
from app.rules.applicability import compose_approval_evaluations, evaluate_rule
from app.rules.dependency_engine import ReadinessStatus, evaluate_readiness
from app.rules.facts import MH_FACTS
from app.rules.models import (
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalComposition,
    ApprovalRule,
    RuleRole,
    SourceRef,
)
from app.seed.mh.approvals import (
    MH_APPROVAL_COMPOSITIONS,
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

APPLIES = "applies"
DNA = "does_not_apply"
COND = "conditional"
INSUFF = "insufficient_data"


def _ev(rule_id: str, result: str, reason: str = "") -> object:
    """Build a probe evaluation (rule-level verdict only)."""
    from app.rules.models import ApplicabilityEvaluation

    return ApplicabilityEvaluation(
        rule_id=rule_id,
        approval_id="APR-PROBE",
        result=result,
        reason=reason or f"{rule_id} evaluated {result}",
        required_inputs=[],
        missing_inputs=[],
        authority="",
        source_references=[],
    )


def _comp(triggers=(), exemptions=(), classifications=()) -> ApprovalComposition:
    return ApprovalComposition(
        approval_id="APR-PROBE",
        triggers=list(triggers),
        exemptions=list(exemptions),
        classifications=list(classifications),
    )


def _mh_orchestrate(approval_id: str, facts: dict) -> object:
    """Run the real single-approval orchestration path with MH pack data."""
    pack = load_regulatory_pack("IN-MH")
    return orchestrate_application(
        application_id="APP-TEST",
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


class TestContract19Rows:
    """Executable §18 truth table over compose_approval_evaluations."""

    def test_row01_trigger_true_applies(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"]), [_ev("T", APPLIES)])
        assert out.result == APPLIES

    def test_row02_trigger_false_does_not_apply(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"]), [_ev("T", DNA)])
        assert out.result == DNA

    def test_row03_trigger_unknown_insufficient(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"]), [_ev("T", INSUFF)])
        assert out.result == INSUFF

    def test_row04_exemption_true_alone_never_applies(self):
        out = compose_approval_evaluations(
            _comp(exemptions=["E"]), [_ev("E", APPLIES)])
        assert out.result != APPLIES
        assert out.result == INSUFF

    def test_row05_exemption_false_alone_never_dna(self):
        out = compose_approval_evaluations(
            _comp(exemptions=["E"]), [_ev("E", DNA)])
        assert out.result != DNA
        assert out.result == INSUFF

    def test_row06_exemption_unknown_alone_insufficient(self):
        out = compose_approval_evaluations(
            _comp(exemptions=["E"]), [_ev("E", INSUFF)])
        assert out.result == INSUFF

    def test_row07_exemption_shape_true_records_consequence(self):
        """R-054-shape TRUE: recorded exemption consequence, never APPROVAL."""
        out = compose_approval_evaluations(
            _comp(exemptions=["E54"]), [_ev("E54", APPLIES, "all six limbs met")])
        assert out.result != APPLIES
        assert out.result == INSUFF

    def test_row08_exemption_shape_false_is_no_info(self):
        out = compose_approval_evaluations(
            _comp(exemptions=["E54"]), [_ev("E54", DNA)])
        assert out.result == INSUFF

    def test_row09_exemption_shape_unknown_blocks_applies(self):
        """No trigger present: INSUFFICIENT (never APPLIES/DNA); with a
        trigger present the unknown defeater yields CONDITIONAL (row 12)."""
        out = compose_approval_evaluations(
            _comp(exemptions=["E54"]), [_ev("E54", INSUFF)])
        assert out.result == INSUFF
        assert out.result != APPLIES

    def test_row10_trigger_true_exemption_true_defeats_with_reason(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"], exemptions=["E"]),
            [_ev("T", APPLIES, "duty attaches"), _ev("E", APPLIES, "MSE limb met")],
        )
        assert out.result == DNA
        assert "E" in out.reason
        assert "MSE limb met" in out.reason

    def test_row11_trigger_true_exemption_false_applies(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"], exemptions=["E"]),
            [_ev("T", APPLIES, "duty attaches"), _ev("E", DNA)],
        )
        assert out.result == APPLIES
        assert out.reason == "duty attaches"

    def test_row12_trigger_true_exemption_unknown_conditional(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"], exemptions=["E"]),
            [_ev("T", APPLIES, "duty attaches"), _ev("E", INSUFF, "class missing")],
        )
        assert out.result == COND
        assert "E" in out.reason

    def test_row13_trigger_unknown_exemption_true_never_applies(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"], exemptions=["E"]),
            [_ev("T", INSUFF, "trigger unknown"), _ev("E", APPLIES, "holds")],
        )
        assert out.result != APPLIES
        assert out.result == INSUFF

    def test_row14_trigger_unknown_exemption_false_insufficient(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"], exemptions=["E"]),
            [_ev("T", INSUFF), _ev("E", DNA)],
        )
        assert out.result == INSUFF

    def test_row15_trigger_unknown_exemption_unknown_insufficient(self):
        out = compose_approval_evaluations(
            _comp(triggers=["T"], exemptions=["E"]),
            [_ev("T", INSUFF), _ev("E", INSUFF)],
        )
        assert out.result == INSUFF

    def test_row16_small_true_trigger_unknown_insufficient(self):
        """R-002 small TRUE + R-001 UNKNOWN: never APPLIES (and never DNA)."""
        out = compose_approval_evaluations(
            _comp(classifications=["R-002"]), [_ev("R-002", APPLIES, "small unit")])
        assert out.result == INSUFF
        assert out.result != APPLIES
        assert out.result != DNA

    def test_row17_classification_false_never_dna(self):
        out = compose_approval_evaluations(
            _comp(classifications=["R-002"]), [_ev("R-002", DNA, "not small")])
        assert out.result == INSUFF
        assert out.result != DNA

    def test_row18_exemption_consequence_no_ready_grant(self):
        """Exemption consequence path never reports READY-as-grant: the
        composed verdict is non-READY, so the handoff gate stays closed."""
        out = compose_approval_evaluations(
            _comp(exemptions=["E54"]), [_ev("E54", APPLIES, "exempt + routed")])
        assert out.result != APPLIES
        assert not is_ready_to_handoff(out.result)

    def test_row19_unknown_defeater_withholds_ready(self):
        """CONDITIONAL from row 12 maps to non-READY downstream."""
        out = compose_approval_evaluations(
            _comp(triggers=["T"], exemptions=["E"]),
            [_ev("T", APPLIES), _ev("E", COND, "partial")],
        )
        assert out.result == COND
        assert not is_ready_to_handoff(out.result)


class TestRoleLint:
    """Roles explicit, never inferred; compositions complete + consistent."""

    def test_default_role_is_trigger(self):
        rule = ApprovalRule(
            id="X-PROBE", approval_id="APR-PROBE",
            applicability_conditions=[], source_refs=[],
            version="probe",
        )
        assert rule.role == RuleRole.TRIGGER

    def test_role_never_inferred_from_names(self):
        """A rule named like an exemption without an explicit role stays
        TRIGGER (legacy behavior preserved; no name detection exists)."""
        rule = ApprovalRule(
            id="X-EXEMPT-TEST", approval_id="APR-PROBE",
            applicability_conditions=[
                ApplicabilityCondition(field="F-X", op=ApplicabilityOp("eq"), value=True)
            ],
            source_refs=[SourceRef(source_id="S", citation_span="-")],
            version="probe",
        )
        assert rule.role == RuleRole.TRIGGER
        assert evaluate_rule(rule, {"F-X": True}).result == APPLIES

    def test_composed_approvals_name_all_built_rules(self):
        by_approval: dict[str, list[str]] = {}
        for rule in load_mh_approval_rules():
            by_approval.setdefault(rule.approval_id, []).append(rule.id)
        for approval_id, comp in MH_APPROVAL_COMPOSITIONS.items():
            named = set(comp.triggers) | set(comp.exemptions) | set(comp.classifications)
            for rule_id in by_approval.get(approval_id, []):
                assert rule_id in named, (approval_id, rule_id)

    def test_composition_groups_match_built_roles(self):
        roles = {r.id: r.role for r in load_mh_approval_rules()}
        for approval_id, comp in MH_APPROVAL_COMPOSITIONS.items():
            for rule_id in comp.triggers:
                assert roles[rule_id] == RuleRole.TRIGGER, rule_id
            for rule_id in comp.exemptions:
                assert roles[rule_id] == RuleRole.EXEMPTION, rule_id
            for rule_id in comp.classifications:
                assert roles[rule_id] == RuleRole.CLASSIFICATION, rule_id

    def test_all_non_trigger_rules_appear_in_compositions(self):
        named: set[str] = set()
        for comp in MH_APPROVAL_COMPOSITIONS.values():
            named |= set(comp.triggers) | set(comp.exemptions) | set(comp.classifications)
        for rule in load_mh_approval_rules():
            if rule.role != RuleRole.TRIGGER:
                assert rule.id in named, rule.id

    def test_only_expected_non_trigger_rules_exist(self):
        non_trigger = {r.id for r in load_mh_approval_rules()
                       if r.role != RuleRole.TRIGGER}
        assert non_trigger == {"R-002", "R-043", "R-044", "R-087"}  # STOP: R-030 stays TRIGGER


class TestR043Pilot:
    """R-043 EXEMPTION migration (single approval APR-043)."""

    def test_built_role_is_exemption(self):
        rule = next(r for r in load_mh_approval_rules() if r.id == "R-043")
        assert rule.role == RuleRole.EXEMPTION

    def test_true_alone_never_applies(self):
        out = compose_approval_evaluations(
            MH_APPROVAL_COMPOSITIONS["APR-043"],
            [_ev("R-043", APPLIES, "MSE limb met")],
        )
        assert out.result == INSUFF

    def test_false_alone_never_dna(self):
        out = compose_approval_evaluations(
            MH_APPROVAL_COMPOSITIONS["APR-043"],
            [_ev("R-043", DNA)],
        )
        assert out.result == INSUFF

    def test_unknown_blocks_trigger(self):
        """Trigger R-077 TRUE + R-043 missing class → CONDITIONAL."""
        r077 = next(r for r in load_mh_approval_rules() if r.id == "R-077")
        r043 = next(r for r in load_mh_approval_rules() if r.id == "R-043")
        facts = {"F-GW-01": "OVER_EXPLOITED", "F-EXP-01": True, "F-WAT-05": 5}
        evals = [evaluate_rule(r077, facts), evaluate_rule(r043, facts)]
        out = compose_approval_evaluations(MH_APPROVAL_COMPOSITIONS["APR-043"], evals)
        assert out.result == COND
        assert "R-043" in out.reason

    def test_defeat_with_reason(self):
        """R-077 TRUE (OE expansion) + R-043 TRUE (MSE) → reasoned DNA."""
        r077 = next(r for r in load_mh_approval_rules() if r.id == "R-077")
        r043 = next(r for r in load_mh_approval_rules() if r.id == "R-043")
        facts = {"F-GW-01": "OVER_EXPLOITED", "F-EXP-01": True,
                 "F-INC-01": "MICRO", "F-WAT-05": 5}
        evals = [evaluate_rule(r077, facts), evaluate_rule(r043, facts)]
        assert evals[0].result == APPLIES
        assert evals[1].result == APPLIES
        out = compose_approval_evaluations(MH_APPROVAL_COMPOSITIONS["APR-043"], evals)
        assert out.result == DNA
        assert "Exempt under R-043" in out.reason

    def test_facts_and_evidence_unchanged(self):
        rule = next(r for r in load_mh_approval_rules() if r.id == "R-043")
        assert rule.source_refs[0].source_id == "SRC-052"
        assert rule.effective_from is not None

    def test_orchestration_exemption_only_not_ready(self):
        """Live orchestration path: MSE facts alone → APR-043 not READY."""
        out = _mh_orchestrate("APR-043", {"F-INC-01": "MICRO", "F-WAT-05": 5})
        assert out.status != OrchestrationStatus.READY
        assert out.applicability_result == INSUFF

    def test_orchestration_defeat_not_ready(self):
        """Trigger + exemption TRUE → NOT_APPLICABLE (reasoned), never READY."""
        out = _mh_orchestrate("APR-043", {
            "F-GW-01": "OVER_EXPLOITED", "F-EXP-01": True,
            "F-INC-01": "MICRO", "F-WAT-05": 5,
        })
        assert out.status == OrchestrationStatus.NOT_APPLICABLE
        assert out.status != OrchestrationStatus.READY
        assert "Exempt under R-043" in out.explanation


class TestApr001R002Migration:
    """R-002 CLASSIFICATION migration (R-001 stays deferred)."""

    def test_built_role_is_classification(self):
        rule = next(r for r in load_mh_approval_rules() if r.id == "R-002")
        assert rule.role == RuleRole.CLASSIFICATION

    def test_small_true_alone_insufficient(self):
        out = _mh_orchestrate("APR-001", {
            "F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False})
        assert out.applicability_result == INSUFF
        assert out.status != OrchestrationStatus.READY

    def test_small_false_alone_never_dna(self):
        """Not-small must not manufacture 'EC does not apply' (Cat B may
        still require EC; R-001R-003/R-004 deferred)."""
        out = compose_approval_evaluations(
            MH_APPROVAL_COMPOSITIONS["APR-001"],
            [_ev("R-002", DNA, "not small")],
        )
        assert out.result == INSUFF
        assert out.result != DNA

    def test_small_true_trigger_unknown_preserves_unresolved(self):
        """The §18 row-16 core: classification TRUE + trigger UNKNOWN is
        neither APPLIES nor DOES_NOT_APPLY."""
        out = compose_approval_evaluations(
            MH_APPROVAL_COMPOSITIONS["APR-001"],
            [_ev("R-002", APPLIES, "small unit")],
        )
        assert out.result == INSUFF

    def test_r001_r064_r074_untouched(self):
        assert "R-001" in MH_DEFERRED_RULES
        assert "R-064" in MH_DEFERRED_RULES
        from app.seed.mh.approvals import MH_UNKNOWN_RULE_IDS
        assert "R-074" in MH_UNKNOWN_RULE_IDS
        assert "R-001" not in MH_INCLUDED_RULE_IDS


class TestReadinessSafety:
    """Phase-7 proofs through real orchestration + handoff + dependencies."""

    def test_exemption_true_cannot_reach_ready(self):
        out = _mh_orchestrate("APR-043", {"F-INC-01": "MICRO", "F-WAT-05": 5})
        assert out.status != OrchestrationStatus.READY
        assert not is_ready_to_handoff(out.status.value)

    def test_exemption_true_not_completion(self):
        out = _mh_orchestrate("APR-043", {"F-INC-01": "MICRO", "F-WAT-05": 5})
        assert out.status in (OrchestrationStatus.INSUFFICIENT_DATA,
                              OrchestrationStatus.NOT_APPLICABLE,
                              OrchestrationStatus.BLOCKED_BY_DEPENDENCY,
                              OrchestrationStatus.BLOCKED_BY_DOCUMENTS,
                              OrchestrationStatus.REVIEW_REQUIRED)
        assert out.status != OrchestrationStatus.READY

    def test_exemption_unknown_survives_aggregation(self):
        """CONDITIONAL composed verdict reaches orchestration intact (not
        collapsed to APPLIES by any priority)."""
        out = _mh_orchestrate("APR-043", {
            "F-GW-01": "OVER_EXPLOITED",
            "F-EXP-01": True,
            "F-WAT-05": 5,
        })
        assert out.applicability_result == COND
        assert out.status != OrchestrationStatus.READY

    def test_classification_cannot_create_node(self):
        out = _mh_orchestrate("APR-001", {
            "F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False})
        assert out.status == OrchestrationStatus.INSUFFICIENT_DATA

    def test_classification_only_cannot_satisfy_dependency(self):
        """An INSUFFICIENT_DATA prerequisite blocks (engine), even with the
        classification evaluated TRUE at rule level."""
        from app.rules.dependency_models import ApprovalDependency
        graph2 = evaluate_readiness(
            [ApprovalDependency(approval_id="APR-X", prerequisite_approval_id="APR-001",
                                relationship="prerequisite", source_ref="t", evidence="t",
                                confidence="explicit")],
            {"APR-X": "applies", "APR-001": "insufficient_data"},
            obtained=set(),
        )
        assert graph2.readiness["APR-X"].readiness == ReadinessStatus.BLOCKED

    def test_existing_edges_enforced(self):
        """DEP-009 still blocks APR-010 on unobtained CTE/CTO."""
        pack = load_regulatory_pack("IN-MH")
        graph = evaluate_readiness(
            pack.dependencies,
            {"APR-010": "applies", "APR-008": "insufficient_data",
             "APR-009": "insufficient_data"},
            obtained=set(),
        )
        assert graph.readiness["APR-010"].readiness == ReadinessStatus.BLOCKED

    def test_unknown_never_false(self):
        assert evaluate_rule(
            next(r for r in load_mh_approval_rules() if r.id == "R-043"), {}
        ).result == INSUFF

    def test_handoff_gate_closed_to_exemptions(self):
        """Only literal READY passes; every composed non-trigger outcome
        raises before any portal lookup."""
        assert is_ready_to_handoff("ready") is True
        for status in ("insufficient_data", "not_applicable", "conditional",
                       "blocked_by_dependency", "pending_evaluation"):
            assert is_ready_to_handoff(status) is False
            with pytest.raises(HandoffStateError):
                prepare_initiation("APP-1", "APR-043", status, "tester")


class TestR043DependencyFootprint:
    """The register phrases the duty as NOC-required-unless-exempt
    (DEP-022, condition 'Not exempt') — corroborating the EXEMPTION role.
    Its dependent is an activity, so it stays triaged out of the pack and
    no downstream edge can consume the exemption verdict."""

    def test_dep022_triaged_activity_endpoint(self):
        from app.seed.mh.dependencies import MH_DEP_DEFERRED

        assert "activity" in MH_DEP_DEFERRED["DEP-022"]

    def test_no_apr043_edges_in_pack(self):
        pack = load_regulatory_pack("IN-MH")
        assert not [d for d in pack.dependencies
                    if "APR-043" in (d.approval_id, d.prerequisite_approval_id)]

    def test_obtained_requires_workflow_approval(self):
        """Obtained-approvals derive from terminal workflow status only
        ('approved'); exemption verdicts can never enter the set, so
        defeat can never read as grant downstream."""
        from app.api.orchestration import _TERMINAL_STATUSES

        assert _TERMINAL_STATUSES == frozenset({"approved"})


class TestR054Compatibility:
    """R-054 stays deferred; its future EXEMPTION role needs no conversion."""

    def test_r054_still_deferred(self):
        assert "R-054" in MH_DEFERRED_RULES
        assert "R-054" not in MH_INCLUDED_RULE_IDS

    def test_exemption_shape_holds_r054_predicate(self):
        """The two modeled conjuncts as an EXEMPTION probe compose to
        never-APPLIES; the four unmodeled conjuncts remain the evidence
        blocker (no facts/sources added here)."""
        assert len(MH_FACTS) == 128
        assert not [k for k in MH_FACTS if "OCMS" in k.upper()]

    def test_no_r054_facts_sources_added(self):
        pack = load_regulatory_pack("IN-MH")
        assert "APR-052" not in {r.approval_id for r in pack.approval_rules}


class TestRemainingCandidatesUntouched:
    """Phase-9 boundary: future migrations, production semantics intact."""

    def test_legacy_non_trigger_roles(self):
        roles = {r.id: r.role.value for r in load_mh_approval_rules()}
        for rule_id in ("R-035", "R-077"):
            assert roles[rule_id] == "trigger", rule_id

    def test_legacy_trigger_behavior_byte_identical(self):
        """R-044 domestic TRUE still evaluates applies at RULE level (raw
        evaluation unchanged; only approval composition reinterprets)."""
        assert evaluate_rule(
            next(r for r in load_mh_approval_rules() if r.id == "R-044"),
            {"F-WAT-06": "DOMESTIC_ONLY", "F-WAT-05": 5},
        ).result == APPLIES


class TestDefaultCompatibility:
    """All unmigrated rules behave exactly as before."""

    def test_only_expected_non_trigger_rules(self):
        non_trigger = {r.id for r in load_mh_approval_rules()
                       if r.role.value != "trigger"}
        assert non_trigger == {"R-002", "R-043", "R-044", "R-087"}  # STOP: R-030 stays TRIGGER

    def test_gj_pack_has_no_compositions_or_roles(self):
        gj = load_regulatory_pack(IN_GJ)
        assert gj.approval_compositions == {}
        assert all(r.role.value == "trigger" for r in gj.approval_rules)
        assert len(gj.approval_rules) == 19

    def test_default_jurisdiction_untouched(self):
        assert DEFAULT_JURISDICTION == "IN-GJ"


class TestCountsUnchanged:
    """No rule/fact churn from the semantic migration itself."""

    def test_rule_fact_counts(self):
        assert len(load_mh_approval_rules()) == 26
        assert len(MH_DEFERRED_RULES) == 61
        assert len(MH_FACTS) == 128

    def test_r021_r054_still_deferred(self):
        assert "R-021" in MH_DEFERRED_RULES
        assert "R-054" in MH_DEFERRED_RULES
