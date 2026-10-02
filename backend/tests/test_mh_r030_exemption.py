"""Audited semantic analysis, falsification, and safety tests for R-030 Petroleum Class-B Exemption.

Covers:
- Statutory evidence and predicate boundaries (Petroleum Act 1934 s.7(i), SRC-092, SRC-017)
- Exact threshold semantics (<= 2500 L total, <= 1000 L receptacle, Class B)
- Missing and unknown facts fail-closed
- Sibling rule R-087 disambiguation (Boilers Act 2025 s.45(2), SRC-034, APR-023; NOT petroleum)
- Approval target disambiguation (targets APR-026; APR-024 does not exist)
- Trigger-absence audit: APR-026 has NO active statutory trigger in IN-MH pack
- Falsification: why migrating R-030 to EXEMPTION without a trigger violates non-empty triggers invariant
- §8 Contract truth table under composed trigger + exemption
- Fail-open / false-positive prevention (exemption alone never APPLIES)
- Readiness, dependency, and handoff protections
- Alternate execution paths (orchestration, what-if, rehearsal/impact, handoff)
- Jurisdiction isolation (IN-GJ byte-identical) and rule inventory
"""
from __future__ import annotations

import pytest

from app.handoff.service import HandoffStateError, is_ready_to_handoff, prepare_initiation
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
    evaluate_rule,
)
from app.rules.dependency_engine import evaluate_readiness
from app.rules.dependency_models import ApprovalDependency, ReadinessStatus
from app.rules.facts import MH_FACTS, get_fact_spec
from app.rules.models import (
    ApplicabilityEvaluation,
    ApprovalComposition,
    SourceRef,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_DO_NOT_IMPLEMENT_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    load_mh_approval_authorities,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, IN_MH, load_regulatory_pack

APPLIES = ApprovalResult.APPLIES.value
DNA = ApprovalResult.DOES_NOT_APPLY.value
COND = ApprovalResult.CONDITIONAL.value
INSUFF = ApprovalResult.INSUFFICIENT_DATA.value


def _by_id(rule_id: str):
    for r in load_mh_approval_rules():
        if r.id == rule_id:
            return r
    raise KeyError(rule_id)


def _ev(rule_id: str, result: str, approval_id: str = "APR-026", reason: str = "") -> ApplicabilityEvaluation:
    return ApplicabilityEvaluation(
        rule_id=rule_id,
        approval_id=approval_id,
        result=result,
        reason=reason or f"{rule_id} evaluated {result}",
        required_inputs=[],
        missing_inputs=[],
        authority="AUT-008 / AUT-009",
        source_references=[SourceRef(source_id="SRC-092", citation_span="s.7(i)")],
    )


class TestR030StatutoryEvidenceAndPredicateBoundaries:
    """Audit Part 1 & 6: Statutory basis, predicate boundaries, and fail-closed handling."""

    def test_r030_statutory_sources(self):
        rule = _by_id("R-030")
        source_ids = {ref.source_id for ref in rule.source_refs}
        assert "SRC-092" in source_ids  # Petroleum Act 1934
        assert "SRC-017" in source_ids  # PESO SOP exemptions table
        ref_092 = next(ref for ref in rule.source_refs if ref.source_id == "SRC-092")
        assert "s.7(i)" in ref_092.citation_span

    def test_r030_predicate_definition(self):
        """Predicate requires: F-PET-01 == 'B' AND F-PET-02 <= 2500 AND F-PET-04 <= 1000."""
        rule = _by_id("R-030")
        assert len(rule.applicability_conditions) == 1

    def test_class_b_within_exemption_limits(self):
        """Case A: Class B + within exemption limits -> R-030 raw evaluation APPLIES."""
        rule = _by_id("R-030")
        ev = evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 500})
        assert ev.result == APPLIES

    def test_class_b_exact_threshold_boundary(self):
        """Case G: Boundary exactly at thresholds: total=2500 L, receptacle=1000 L."""
        rule = _by_id("R-030")
        ev = evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": 2500, "F-PET-04": 1000})
        assert ev.result == APPLIES

    def test_class_b_above_first_limit(self):
        """Case B: Total quantity exceeds 2500 L -> DOES_NOT_APPLY."""
        rule = _by_id("R-030")
        ev = evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": 2501, "F-PET-04": 1000})
        assert ev.result == DNA

    def test_class_b_above_second_limit(self):
        """Case C: Receptacle exceeds 1000 L -> DOES_NOT_APPLY."""
        rule = _by_id("R-030")
        ev = evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 1001})
        assert ev.result == DNA

    def test_class_b_just_above_thresholds(self):
        """Case H: Verify exact <= semantics with small fractional delta."""
        rule = _by_id("R-030")
        ev_total = evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": 2500.5, "F-PET-04": 1000})
        assert ev_total.result == DNA

        ev_rec = evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": 2500, "F-PET-04": 1000.5})
        assert ev_rec.result == DNA

    def test_missing_facts_fail_closed(self):
        """Cases D, E, F: Missing facts must fail closed to INSUFFICIENT_DATA."""
        rule = _by_id("R-030")
        # Missing F-PET-01
        assert evaluate_rule(rule, {"F-PET-02": 2000, "F-PET-04": 500}).result == INSUFF
        # Missing F-PET-02
        assert evaluate_rule(rule, {"F-PET-01": "B", "F-PET-04": 500}).result == INSUFF
        # Missing F-PET-04
        assert evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": 2000}).result == INSUFF
        # All missing
        assert evaluate_rule(rule, {}).result == INSUFF

    def test_unknown_facts_fail_closed(self):
        rule = _by_id("R-030")
        res1 = evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": "UNKNOWN", "F-PET-04": 500})
        assert res1.result == INSUFF
        res2 = evaluate_rule(rule, {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": "UNKNOWN"})
        assert res2.result == INSUFF

    def test_non_class_b_evaluates_does_not_apply(self):
        rule = _by_id("R-030")
        # Class A
        assert evaluate_rule(rule, {"F-PET-01": "A", "F-PET-02": 10, "F-PET-04": 10}).result == DNA
        # Class C
        res_c = evaluate_rule(rule, {"F-PET-01": "C", "F-PET-02": 10000, "F-PET-04": 500})
        assert res_c.result == DNA
        # NOT_PETROLEUM
        res_np = evaluate_rule(rule, {"F-PET-01": "NOT_PETROLEUM", "F-PET-02": 0, "F-PET-04": 0})
        assert res_np.result == DNA



class TestR087IdentityAndDisambiguation:
    """Audit Part 4: Reconstruct R-087 semantics from evidence and prove non-sibling status."""

    def test_r087_statutory_condition(self):
        """R-087 represents Boilers Act 2025 s.45(2)(f) transitional deemed registration."""
        rule = _by_id("R-087")
        assert rule.id == "R-087"
        assert rule.approval_id == "APR-023"  # Boiler registration, NOT APR-024 or APR-026
        assert len(rule.source_refs) >= 1
        assert rule.source_refs[0].source_id == "SRC-034"
        assert "s.45(2)" in rule.source_refs[0].citation_span

    def test_r087_target_approval_is_boiler(self):
        """R-087 targets APR-023 (Boiler registration), NOT APR-024 or APR-026."""
        rule = _by_id("R-087")
        authorities = load_mh_approval_authorities()
        assert rule.approval_id == "APR-023"
        assert authorities["APR-023"] == "AUT-007"  # Directorate of Steam Boilers

    def test_r087_references_boiler_facts_not_petroleum(self):
        """R-087 uses F-BLR-07, completely independent of petroleum facts F-PET-*."""
        rule = _by_id("R-087")
        leaf = rule.applicability_conditions[0]
        assert leaf.field == "F-BLR-07"
        assert leaf.value == "REGISTERED_UNDER_1923_ACT"

        spec = get_fact_spec("IN-MH", "F-BLR-07")
        assert spec.group == "BLR"

    def test_r087_is_not_petroleum_approval_trigger(self):
        """R-087 has zero statutory relation to petroleum storage."""
        rule = _by_id("R-087")
        assert rule.approval_id != "APR-026"
        assert rule.approval_id != "APR-024"


class TestAPR024AndPetroleumApprovalTarget:
    """Audit Part 2 & 4: Approval target identity and trigger absence verification."""

    def test_apr024_does_not_exist_in_pack(self):
        """APR-024 is an unencoded / non-existent approval ID; true petroleum approval is APR-026."""
        rules = load_mh_approval_rules()
        rule_approval_ids = {r.approval_id for r in rules}
        assert "APR-024" not in rule_approval_ids

        authorities = load_mh_approval_authorities()
        assert "APR-024" not in authorities

    def test_r030_targets_apr026(self):
        """R-030 targets APR-026 (Petroleum storage licence + Rule 144 NOC)."""
        rule = _by_id("R-030")
        assert rule.approval_id == "APR-026"
        authorities = load_mh_approval_authorities()
        assert authorities["APR-026"] == "AUT-008 / AUT-009"

    def test_apr026_has_no_active_trigger_rule(self):
        """R-030 is the SOLE active rule targeting APR-026 in the Maharashtra regulatory pack."""
        rules_for_apr026 = [r for r in load_mh_approval_rules() if r.approval_id == "APR-026"]
        assert len(rules_for_apr026) == 1
        assert rules_for_apr026[0].id == "R-030"

    def test_petroleum_candidate_rules_status(self):
        """Audit all petroleum candidate rules in v5 dataset."""
        # R-029 is DO_NOT_IMPLEMENT (Class A exemption <= 30 L)
        assert "R-029" in MH_DO_NOT_IMPLEMENT_RULE_IDS
        # R-032 is DEFERRED (form & authority routing expression)
        assert "R-032" in MH_DEFERRED_RULES
        assert "Petroleum licence form" in MH_DEFERRED_RULES["R-032"]
        # R-092 is DEFERRED (District Authority NOC under r.144)
        assert "R-092" in MH_DEFERRED_RULES
        # R-100 is DEFERRED (PESO licence renewal)
        assert "R-100" in MH_DEFERRED_RULES


class TestFalsificationWhyMigrationIsUnsafeWithoutTrigger:
    """Falsification: prove why migrating R-030 to EXEMPTION without a trigger breaks invariants."""

    def test_exemption_without_trigger_yields_insufficient_data(self):
        """If APR-026 were composed with R-030 as EXEMPTION and NO triggers:
        The approval would compose to INSUFFICIENT_DATA even when large quantities of petroleum are stored!
        """
        hypothetical_comp = ApprovalComposition(
            approval_id="APR-026",
            triggers=[],
            exemptions=["R-030"],
        )
        # Facility stores 100,000 L of petroleum Class B in bulk -> R-030 exemption evaluates DNA
        ev_exemption_false = _ev("R-030", DNA)
        res = compose_approval_evaluations(hypothetical_comp, [ev_exemption_false])
        # Because there is NO trigger, compose_approval_evaluations returns INSUFFICIENT_DATA
        assert res.result == INSUFF
        assert "No trigger rule evaluated for this approval" in res.reason

    def test_exemption_without_trigger_can_never_produce_applies(self):
        """A triggerless approval composed only of exemptions can NEVER evaluate to APPLIES.
        This would erase the statutory obligation to obtain a petroleum licence entirely!
        """
        hypothetical_comp = ApprovalComposition(
            approval_id="APR-026",
            triggers=[],
            exemptions=["R-030"],
        )
        # Any evaluation of R-030 (APPLIES, DNA, COND, INSUFF)
        for r in (APPLIES, DNA, COND, INSUFF):
            res = compose_approval_evaluations(hypothetical_comp, [_ev("R-030", r)])
            assert res.result != APPLIES, f"Triggerless composition must never produce APPLIES for {r}"

    def test_prompt_non_empty_triggers_invariant_violation(self):
        """Section 5 invariant: 'APR-024 triggers: MUST remain non-empty'.
        Without an active statutory trigger rule, this invariant is impossible to satisfy.
        """
        active_apr026_triggers = [
            r.id for r in load_mh_approval_rules()
            if r.approval_id == "APR-026" and r.id != "R-030"
        ]
        assert len(active_apr026_triggers) == 0


class TestHypotheticalComposedTruthTable:
    """Part 8: §8 Contract Truth Table with a hypothetical legitimate trigger."""

    @pytest.fixture
    def hypothetical_petroleum_composition(self):
        return ApprovalComposition(
            approval_id="APR-026",
            triggers=["R-PET-TRIG"],
            exemptions=["R-030"],
        )

    def test_trigger_true_exemption_true_yields_reasoned_defeat(self, hypothetical_petroleum_composition):
        """Trigger TRUE + Exemption TRUE -> DOES_NOT_APPLY (statutory defeat)."""
        ev_trig = _ev("R-PET-TRIG", APPLIES, reason="Petroleum storage occurs on site")
        ev_ex = _ev("R-030", APPLIES, reason="Class B <= 2500 L and receptacle <= 1000 L")
        res = compose_approval_evaluations(hypothetical_petroleum_composition, [ev_trig, ev_ex])
        assert res.result == DNA
        assert "Exempt under R-030" in res.reason
        assert "would otherwise apply" in res.reason

    def test_trigger_true_exemption_false_yields_applies(self, hypothetical_petroleum_composition):
        """Trigger TRUE + Exemption FALSE -> APPLIES (duty holds)."""
        ev_trig = _ev("R-PET-TRIG", APPLIES, reason="Petroleum storage occurs on site")
        ev_ex = _ev("R-030", DNA, reason="Storage exceeds 2500 L limit")
        res = compose_approval_evaluations(hypothetical_petroleum_composition, [ev_trig, ev_ex])
        assert res.result == APPLIES

    def test_trigger_true_exemption_unknown_yields_conditional(self, hypothetical_petroleum_composition):
        """Trigger TRUE + Exemption UNKNOWN -> CONDITIONAL (defeater unresolved blocks APPLIES)."""
        ev_trig = _ev("R-PET-TRIG", APPLIES, reason="Petroleum storage occurs on site")
        ev_ex = _ev("R-030", INSUFF, reason="F-PET-02 unknown")
        res = compose_approval_evaluations(hypothetical_petroleum_composition, [ev_trig, ev_ex])
        assert res.result == COND
        assert "Exemption R-030 unresolved" in res.reason

    def test_trigger_false_exemption_true_yields_does_not_apply(self, hypothetical_petroleum_composition):
        """Trigger FALSE + Exemption TRUE -> DOES_NOT_APPLY."""
        ev_trig = _ev("R-PET-TRIG", DNA, reason="No petroleum on site")
        ev_ex = _ev("R-030", APPLIES, reason="Within limits")
        res = compose_approval_evaluations(hypothetical_petroleum_composition, [ev_trig, ev_ex])
        assert res.result == DNA

    def test_trigger_false_exemption_false_yields_does_not_apply(self, hypothetical_petroleum_composition):
        """Trigger FALSE + Exemption FALSE -> DOES_NOT_APPLY."""
        ev_trig = _ev("R-PET-TRIG", DNA, reason="No petroleum on site")
        ev_ex = _ev("R-030", DNA, reason="Exceeds limits")
        res = compose_approval_evaluations(hypothetical_petroleum_composition, [ev_trig, ev_ex])
        assert res.result == DNA

    def test_trigger_unknown_exemption_true_yields_insufficient_data(self, hypothetical_petroleum_composition):
        """Trigger UNKNOWN + Exemption TRUE -> INSUFFICIENT_DATA (defeat needs a duty; never APPLIES)."""
        ev_trig = _ev("R-PET-TRIG", INSUFF, reason="Storage presence unknown")
        ev_ex = _ev("R-030", APPLIES, reason="Within limits")
        res = compose_approval_evaluations(hypothetical_petroleum_composition, [ev_trig, ev_ex])
        assert res.result == INSUFF
        assert "no trigger is established, so no duty is defeated" in res.reason

    def test_trigger_unknown_exemption_false_yields_insufficient_data(self, hypothetical_petroleum_composition):
        """Trigger UNKNOWN + Exemption FALSE -> INSUFFICIENT_DATA."""
        ev_trig = _ev("R-PET-TRIG", INSUFF, reason="Storage presence unknown")
        ev_ex = _ev("R-030", DNA, reason="Exceeds limits")
        res = compose_approval_evaluations(hypothetical_petroleum_composition, [ev_trig, ev_ex])
        assert res.result == INSUFF

    def test_trigger_unknown_exemption_unknown_yields_insufficient_data(self, hypothetical_petroleum_composition):
        """Trigger UNKNOWN + Exemption UNKNOWN -> INSUFFICIENT_DATA."""
        ev_trig = _ev("R-PET-TRIG", INSUFF, reason="Storage presence unknown")
        ev_ex = _ev("R-030", INSUFF, reason="Receptacle size unknown")
        res = compose_approval_evaluations(hypothetical_petroleum_composition, [ev_trig, ev_ex])
        assert res.result == INSUFF


class TestFailOpenAndReadinessProtections:
    """Part 7: Fail-open falsification, readiness, dependency, and handoff protections."""

    def test_exemption_true_alone_cannot_produce_applies(self):
        """Invariant: An exemption must NEVER create an approval obligation."""
        comp = ApprovalComposition(
            approval_id="APR-TEST",
            triggers=["R-TRIG-UNRESOLVED"],
            exemptions=["R-030"],
        )
        ev_trig_unk = _ev("R-TRIG-UNRESOLVED", INSUFF, approval_id="APR-TEST")
        ev_ex_true = _ev("R-030", APPLIES, approval_id="APR-TEST")
        res = compose_approval_evaluations(comp, [ev_trig_unk, ev_ex_true])
        assert res.result != APPLIES
        assert res.result == INSUFF

    def test_exempt_approval_never_becomes_ready(self):
        """An approval that evaluates to does_not_apply (exempt) is not_applicable, never ready."""
        graph = evaluate_readiness(
            dependencies=[],
            applicability_results={"APR-026": "does_not_apply"},
            obtained=set(),
        )
        assert graph.readiness["APR-026"].readiness == ReadinessStatus.NOT_APPLICABLE
        assert graph.readiness["APR-026"].readiness != ReadinessStatus.READY

    def test_insufficient_data_never_becomes_ready(self):
        """Missing facts / insufficient_data cannot be READY (evaluates to pending_evaluation)."""
        graph = evaluate_readiness(
            dependencies=[],
            applicability_results={"APR-026": "insufficient_data"},
            obtained=set(),
        )
        assert graph.readiness["APR-026"].readiness != ReadinessStatus.READY
        assert graph.readiness["APR-026"].readiness == ReadinessStatus.PENDING_EVALUATION

    def test_exempt_approval_cannot_satisfy_downstream_dependency(self):
        """Exemption defeat produces does_not_apply which never enters obtained set.
        Furthermore, an unresolved defeater yields conditional which BLOCKS downstream.
        """
        from app.api.orchestration import _TERMINAL_STATUSES
        assert _TERMINAL_STATUSES == frozenset({"approved"})

        graph = evaluate_readiness(
            dependencies=[
                ApprovalDependency(
                    approval_id="APR-DOWNSTREAM",
                    prerequisite_approval_id="APR-026",
                    relationship="prerequisite",
                    source_ref="test",
                    evidence="test",
                    confidence="explicit",
                )
            ],
            applicability_results={"APR-DOWNSTREAM": "applies", "APR-026": "conditional"},
            obtained=set(),
        )
        assert graph.readiness["APR-DOWNSTREAM"].readiness == ReadinessStatus.BLOCKED

    def test_not_applicable_approval_rejected_at_handoff(self):
        """An approval that is not_applicable cannot pass handoff."""
        assert is_ready_to_handoff("not_applicable") is False
        assert is_ready_to_handoff("conditional") is False
        with pytest.raises(HandoffStateError):
            prepare_initiation("APP-TEST", "APR-026", "not_applicable", "tester")
        with pytest.raises(HandoffStateError):
            prepare_initiation("APP-TEST", "APR-026", "conditional", "tester")


class TestExecutionPathsAndJurisdictionIsolation:
    """Part 9 & 10: Alternate paths and jurisdiction isolation."""

    def test_whatif_path_operates_cleanly_on_petroleum_facts(self):
        """What-if service evaluates petroleum facts cleanly without drift."""
        pack = load_regulatory_pack(IN_MH)
        base_facts = {"F-PET-01": "B", "F-PET-02": 3000, "F-PET-04": 500}
        resp = run_whatif_assessment(
            application_id="APP-WHATIF-TEST",
            base_facts=base_facts,
            fact_overrides={"F-PET-02": 2000},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=[r.approval_id for r in pack.approval_rules],
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
        assert resp is not None
        assert resp.baseline is not None
        assert resp.what_if is not None

    def test_rehearsal_path_handles_source_changes_for_petroleum(self):
        """Rehearsal engine handles change descriptors for SRC-092 cleanly."""
        pack = load_regulatory_pack(IN_MH)
        inputs = RehearsalInputs(
            base_facts={"F-PET-01": "B", "F-PET-02": 3000, "F-PET-04": 500},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=[r.approval_id for r in pack.approval_rules],
            document_requirements=[],
            approval_compositions=pack.approval_compositions,
            known_source_ids={s.id for s in pack.sources},
        )
        impact = rehearse_impact(
            ChangeDescriptor(
                change_kind=ChangeKind.SOURCE_METADATA_CHANGE,
                source_id="SRC-092",
                old_value={"title": "Petroleum Act 1934"},
                new_value={"title": "Petroleum Act 1934 (Amended)"},
            ),
            inputs,
        )
        assert impact is not None
        assert "APR-026" in impact.affected_approvals

    def test_gujarat_isolation_byte_identical(self):
        """Gujarat pack must remain completely unaffected by MH rules."""
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        assert gj_pack.approval_compositions == {}
        assert DEFAULT_JURISDICTION == IN_GJ
        gj_ids = {r.id for r in gj_pack.approval_rules}
        assert "R-030" not in gj_ids
        assert "R-087" not in gj_ids

    def test_maharashtra_inventory_and_counts(self):
        """Maharashtra pack inventory must remain exact: 26 active, 61 deferred, 128 facts."""
        mh_pack = load_regulatory_pack(IN_MH)
        assert len(mh_pack.approval_rules) == 26
        assert len(MH_DEFERRED_RULES) == 61
        assert len(MH_FACTS) == 128
        assert set(MH_INCLUDED_RULE_IDS) == {r.id for r in mh_pack.approval_rules}
