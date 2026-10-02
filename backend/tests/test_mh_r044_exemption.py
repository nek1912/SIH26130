"""Audited regression & safety tests for R-044 domestic exemption migration.

Covers PARTS 4-10 of the R-044 migration task:
- Multi-exemption truth table (10 rows)
- Polarity regression (fail-open falsification)
- R-043 + R-044 interaction matrix (7 combinations)
- R-077 trigger preservation and composition
- Readiness / dependency / handoff safety
- Alternate paths (orchestration, what-if, rehearsal, handoff, direct)
- Inventory / counts verification.
"""
from __future__ import annotations

import pytest

from app.handoff.service import HandoffStateError, is_ready_to_handoff, prepare_initiation
from app.orchestration.models import OrchestrationStatus
from app.orchestration.service import (
    orchestrate_application,
)
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
from app.rules.facts import MH_FACTS
from app.rules.models import (
    ApplicabilityEvaluation,
    RuleRole,
    SourceRef,
)
from app.seed.mh.approvals import (
    MH_APPROVAL_COMPOSITIONS,
    MH_DEFERRED_RULES,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, IN_MH, load_regulatory_pack

APPLIES = ApprovalResult.APPLIES.value
DNA = ApprovalResult.DOES_NOT_APPLY.value
COND = ApprovalResult.CONDITIONAL.value
INSUFF = ApprovalResult.INSUFFICIENT_DATA.value


def _ev(rule_id: str, result: str, reason: str = "") -> ApplicabilityEvaluation:
    return ApplicabilityEvaluation(
        rule_id=rule_id,
        approval_id="APR-043",
        result=result,
        reason=reason or f"{rule_id} evaluated {result}",
        required_inputs=[],
        missing_inputs=[],
        authority="AUT-013",
        source_references=[SourceRef(source_id="SRC-052", citation_span="probe")],
    )


class TestR044SemanticConfirmation:
    """Part 1 & 3: Role identity, predicate, and metadata integrity."""

    def test_r044_role_is_exemption(self):
        rule = next(r for r in load_mh_approval_rules() if r.id == "R-044")
        assert rule.role == RuleRole.EXEMPTION
        assert rule.approval_id == "APR-043"

    def test_r044_predicate_unmodified(self):
        rule = next(r for r in load_mh_approval_rules() if r.id == "R-044")
        assert rule.source_refs[0].source_id == "SRC-052"
        assert rule.effective_from is not None
        # Evaluates applies when domestic and <= 5
        ev_true = evaluate_rule(rule, {"F-WAT-06": "DOMESTIC_ONLY", "F-WAT-05": 5})
        assert ev_true.result == APPLIES
        # Evaluates does_not_apply when > 5
        ev_false1 = evaluate_rule(rule, {"F-WAT-06": "DOMESTIC_ONLY", "F-WAT-05": 6})
        assert ev_false1.result == DNA
        # Evaluates does_not_apply when INDUSTRIAL
        ev_false2 = evaluate_rule(rule, {"F-WAT-06": "INDUSTRIAL", "F-WAT-05": 5})
        assert ev_false2.result == DNA
        # Evaluates insufficient_data when missing
        ev_unk = evaluate_rule(rule, {})
        assert ev_unk.result == INSUFF


class TestAPR043CompositionSafety:
    """Part 2 & 4: Composition structure, disjointness, and truth table."""

    def test_composition_structure(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        assert comp.approval_id == "APR-043"
        assert comp.triggers == ["R-077"]
        assert comp.exemptions == ["R-043", "R-044"]
        assert comp.classifications == []

    def test_groups_are_disjoint(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        t_set = set(comp.triggers)
        e_set = set(comp.exemptions)
        c_set = set(comp.classifications)
        assert t_set & e_set == set()
        assert t_set & c_set == set()
        assert e_set & c_set == set()

    def test_all_referenced_rules_exist_in_pack(self):
        mh_rules = {r.id: r for r in load_mh_approval_rules()}
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        for rid in comp.triggers + comp.exemptions + comp.classifications:
            assert rid in mh_rules
            assert mh_rules[rid].approval_id in ("APR-043", "APR-001")

    # Multi-exemption 10 truth-table rows
    def test_tt_row01_trigger_true_both_exemptions_false(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", APPLIES), _ev("R-043", DNA), _ev("R-044", DNA)]
        )
        assert out.result == APPLIES
        assert out.rule_id == "R-077"

    def test_tt_row02_trigger_true_r043_true_r044_false(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", APPLIES), _ev("R-043", APPLIES, "MSE exempt"), _ev("R-044", DNA)]
        )
        assert out.result == DNA
        assert "Exempt under R-043" in out.reason

    def test_tt_row03_trigger_true_r043_false_r044_true(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp,
            [
                _ev("R-077", APPLIES),
                _ev("R-043", DNA),
                _ev("R-044", APPLIES, "domestic exempt"),
            ],
        )
        assert out.result == DNA
        assert "Exempt under R-044" in out.reason

    def test_tt_row04_trigger_true_both_exemptions_true(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp,
            [
                _ev("R-077", APPLIES),
                _ev("R-043", APPLIES, "MSE exempt"),
                _ev("R-044", APPLIES, "domestic exempt"),
            ],
        )
        assert out.result == DNA
        # First evaluated exemption in list wins
        assert "Exempt under R-043" in out.reason

    def test_tt_row05_trigger_true_r043_unknown_r044_false(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp,
            [
                _ev("R-077", APPLIES),
                _ev("R-043", INSUFF, "missing facts"),
                _ev("R-044", DNA),
            ],
        )
        assert out.result == COND
        assert "R-043" in out.reason

    def test_tt_row06_trigger_true_r043_false_r044_unknown(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp,
            [
                _ev("R-077", APPLIES),
                _ev("R-043", DNA),
                _ev("R-044", INSUFF, "missing facts"),
            ],
        )
        assert out.result == COND
        assert "R-044" in out.reason

    def test_tt_row07_trigger_true_both_exemptions_unknown(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp,
            [_ev("R-077", APPLIES), _ev("R-043", INSUFF), _ev("R-044", INSUFF)],
        )
        assert out.result == COND

    def test_tt_row08_trigger_false_any_exemptions(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        for r43 in (APPLIES, DNA, INSUFF):
            for r44 in (APPLIES, DNA, INSUFF):
                out = compose_approval_evaluations(
                    comp,
                    [
                        _ev("R-077", DNA, "safe unit"),
                        _ev("R-043", r43),
                        _ev("R-044", r44),
                    ],
                )
                assert out.result == DNA, (r43, r44)
                assert out.rule_id == "R-077"

    def test_tt_row09_trigger_unknown_exemption_true(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp,
            [
                _ev("R-077", INSUFF, "missing GW-01"),
                _ev("R-043", DNA),
                _ev("R-044", APPLIES, "domestic exempt"),
            ],
        )
        assert out.result == INSUFF
        assert "no trigger is established" in out.reason
        assert out.result != APPLIES

    def test_tt_row10_trigger_unknown_exemptions_unknown(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", INSUFF), _ev("R-043", INSUFF), _ev("R-044", INSUFF)]
        )
        assert out.result == INSUFF
        assert out.result != APPLIES


class TestPolarityRegression:
    """Part 5: Falsification of old fail-open and fail-closed defects."""

    def test_r044_true_alone_never_applies(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-044", APPLIES, "domestic exempt")]
        )
        assert out.result == INSUFF
        assert out.result != APPLIES

    def test_r044_false_alone_never_dna(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-044", DNA, "industrial")]
        )
        assert out.result == INSUFF
        assert out.result != DNA

    def test_trigger_true_plus_r044_true_produces_reasoned_dna(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", APPLIES, "OE unit"), _ev("R-044", APPLIES, "domestic <=5")]
        )
        assert out.result == DNA
        assert "Exempt under R-044" in out.reason

    def test_trigger_true_plus_r044_unknown_never_applies(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", APPLIES, "OE unit"), _ev("R-044", INSUFF, "missing facts")]
        )
        assert out.result == COND
        assert out.result != APPLIES


class TestR043R044Interaction:
    """Part 6: Interaction matrix of multiple exemptions under trigger TRUE."""

    @pytest.mark.parametrize(
        ("r043_res", "r044_res", "expected_res", "expected_reason_substr"),
        [
            (APPLIES, APPLIES, DNA, "Exempt under R-043"),
            (APPLIES, DNA, DNA, "Exempt under R-043"),
            (DNA, APPLIES, DNA, "Exempt under R-044"),
            (DNA, DNA, APPLIES, "R-077"),
            (INSUFF, DNA, COND, "R-043"),
            (DNA, INSUFF, COND, "R-044"),
            (INSUFF, INSUFF, COND, "unresolved"),
        ],
    )
    def test_exemption_combinations(
        self, r043_res, r044_res, expected_res, expected_reason_substr
    ):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp,
            [
                _ev("R-077", APPLIES, "OE unit"),
                _ev("R-043", r043_res, "MSE test"),
                _ev("R-044", r044_res, "domestic test"),
            ],
        )
        assert out.result == expected_res
        assert expected_reason_substr in out.reason or expected_reason_substr in out.rule_id


class TestR077TriggerPreservation:
    """Part 7: R-077 remains sole trigger for APR-043."""

    def test_r077_is_trigger(self):
        rule = next(r for r in load_mh_approval_rules() if r.id == "R-077")
        assert rule.role == RuleRole.TRIGGER
        assert rule.approval_id == "APR-043"

    def test_r077_true_r044_true_defeat(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", APPLIES), _ev("R-043", DNA), _ev("R-044", APPLIES)]
        )
        assert out.result == DNA

    def test_r077_true_r044_unknown_conditional(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", APPLIES), _ev("R-043", DNA), _ev("R-044", INSUFF)]
        )
        assert out.result == COND

    def test_r077_false_r044_true_no_duty(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", DNA), _ev("R-043", DNA), _ev("R-044", APPLIES)]
        )
        assert out.result == DNA
        assert out.rule_id == "R-077"

    def test_r077_unknown_r044_true_never_applies(self):
        comp = MH_APPROVAL_COMPOSITIONS["APR-043"]
        out = compose_approval_evaluations(
            comp, [_ev("R-077", INSUFF), _ev("R-043", DNA), _ev("R-044", APPLIES)]
        )
        assert out.result == INSUFF
        assert out.result != APPLIES


class TestReadinessDependencyHandoff:
    """Part 8: Downstream lifecycle protection."""

    def test_exemption_defeat_never_ready(self):
        pack = load_regulatory_pack(IN_MH)
        out = orchestrate_application(
            application_id="APP-R044-1",
            approval_id="APR-043",
            project_facts={
                "F-GW-01": "OVER_EXPLOITED",
                "F-EXP-01": True,
                "F-INC-01": "LARGE",
                "F-WAT-06": "DOMESTIC_ONLY",
                "F-WAT-05": 5,
            },
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
        assert out.applicability_result == DNA
        assert out.status == OrchestrationStatus.NOT_APPLICABLE
        assert out.status != OrchestrationStatus.READY

    def test_exemption_defeat_cannot_satisfy_dependency(self):
        # Exemption defeat produces does_not_apply / not_applicable, which never
        # enters the obtained set (only approved terminal status enters obtained).
        from app.api.orchestration import _TERMINAL_STATUSES
        assert _TERMINAL_STATUSES == frozenset({"approved"})

        # Furthermore, an UNKNOWN defeater yields conditional which BLOCKS downstream
        graph = evaluate_readiness(
            [
                ApprovalDependency(
                    approval_id="APR-DOWNSTREAM",
                    prerequisite_approval_id="APR-043",
                    relationship="prerequisite",
                    source_ref="test",
                    evidence="test",
                    confidence="explicit",
                )
            ],
            {"APR-DOWNSTREAM": "applies", "APR-043": "conditional"},
            obtained=set(),
        )
        assert graph.readiness["APR-DOWNSTREAM"].readiness == ReadinessStatus.BLOCKED

    def test_handoff_rejects_exemption_defeat(self):
        assert is_ready_to_handoff("not_applicable") is False
        with pytest.raises(HandoffStateError):
            prepare_initiation("APP-1", "APR-043", "not_applicable", "tester")

    def test_handoff_rejects_exemption_conditional(self):
        assert is_ready_to_handoff("conditional") is False
        with pytest.raises(HandoffStateError):
            prepare_initiation("APP-1", "APR-043", "conditional", "tester")


class TestAlternatePaths:
    """Part 9: Consistency across orchestration, what-if, rehearsal, handoff."""

    def _inputs(self):
        pack = load_regulatory_pack(IN_MH)
        return {
            "application_id": "APP-043-ALT",
            "facts": {
                "F-GW-01": "OVER_EXPLOITED",
                "F-EXP-01": True,
                "F-INC-01": "LARGE",
                "F-WAT-06": "DOMESTIC_ONLY",
                "F-WAT-05": 5,
            },
            "rules": pack.approval_rules,
            "authorities": pack.approval_authorities,
            "dependencies": pack.dependencies,
            "all_approval_ids": [r.approval_id for r in pack.approval_rules],
            "doc_requirements": [],
            "uploaded_docs": [],
            "extraction_results": [],
            "validation_results": [],
            "consistency_result": None,
            "sla_info": None,
            "obtained": set(),
            "evidence_gaps_by_approval": {},
            "fact_provenance": {},
            "pack": pack,
        }

    def test_whatif_path_consumes_exemption(self):
        inputs = self._inputs()
        resp = run_whatif_assessment(
            application_id=inputs["application_id"],
            base_facts=inputs["facts"],
            fact_overrides={"F-WAT-06": "INDUSTRIAL"},
            approval_rules=inputs["rules"],
            approval_authorities=inputs["authorities"],
            dependencies=inputs["dependencies"],
            all_approval_ids=inputs["all_approval_ids"],
            document_requirements=inputs["doc_requirements"],
            uploaded_documents=inputs["uploaded_docs"],
            extraction_results=inputs["extraction_results"],
            validation_results=inputs["validation_results"],
            consistency_result=inputs["consistency_result"],
            sla_info=inputs["sla_info"],
            obtained_approvals=inputs["obtained"],
            evidence_gaps_by_approval=inputs["evidence_gaps_by_approval"],
            fact_provenance=inputs["fact_provenance"],
            jurisdiction=IN_MH,
            approval_compositions=inputs["pack"].approval_compositions,
        )
        # Baseline was domestic -> does_not_apply (Exempt under R-044)
        assert resp.baseline.approvals["APR-043"].applicability_result == DNA
        # What-if overridden to INDUSTRIAL -> applies (trigger R-077 holds, no exemption)
        assert resp.what_if.approvals["APR-043"].applicability_result == APPLIES

    def test_rehearsal_path_consumes_exemption(self):
        inputs = self._inputs()
        pack = inputs["pack"]
        impact = rehearse_impact(
            ChangeDescriptor(
                change_kind=ChangeKind.SOURCE_METADATA_CHANGE,
                source_id="SRC-052",
                old_value={"title": "CGWA guidelines"},
                new_value={"title": "CGWA guidelines (updated)"},
            ),
            RehearsalInputs(
                base_facts=inputs["facts"],
                approval_rules=inputs["rules"],
                approval_authorities=inputs["authorities"],
                dependencies=inputs["dependencies"],
                all_approval_ids=inputs["all_approval_ids"],
                document_requirements=inputs["doc_requirements"],
                uploaded_documents=inputs["uploaded_docs"],
                extraction_results=inputs["extraction_results"],
                validation_results=inputs["validation_results"],
                consistency_result=inputs["consistency_result"],
                sla_info=inputs["sla_info"],
                obtained_approvals=inputs["obtained"],
                evidence_gaps_by_approval=inputs["evidence_gaps_by_approval"],
                approval_compositions=dict(pack.approval_compositions),
                known_source_ids={s.id for s in pack.sources},
                evidence_registry=list(pack.evidence_gaps),
                evidence_hints=dict(pack.evidence_hints),
            ),
        )
        assert "APR-043" in impact.affected_approvals
        assert impact.baseline_results["APR-043"]["applicability"] == DNA


class TestCountsAndInventory:
    """Part 10 & 12: Inventory counts and unmigrated candidate verification."""

    def test_inventory_counts(self):
        rules = load_mh_approval_rules()
        assert len(rules) == 26
        assert len(MH_DEFERRED_RULES) == 61
        assert len(MH_FACTS) == 128
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_unmigrated_candidates_untouched(self):
        roles = {r.id: r.role.value for r in load_mh_approval_rules()}
        assert roles["R-002"] == "classification"
        assert roles["R-043"] == "exemption"
        assert roles["R-044"] == "exemption"
        for rid in ("R-030", "R-035", "R-077"):
            assert roles[rid] == "trigger", rid  # R-030 blocked: no APR-026 trigger encoded


