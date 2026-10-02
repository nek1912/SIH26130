"""P0 exception-role contract tests (§18 of the design audit).

Pure composition tests against ``summarize_by_approval`` with local
``ApprovalComposition`` objects — no pack, seed, or production rule
changes required. Each row: INPUT → ROLE → rule verdict →
APPROVAL consequence + WHY. These tests precede any rule migration
and must stay green through it (defaults-green proof) and after it
(the contract the migration implements).
"""
from __future__ import annotations

from app.rules.applicability import summarize_by_approval
from app.rules.models import (
    ApplicabilityEvaluation,
    ApprovalComposition,
    SourceRef,
)


def _ev(
    rule_id: str,
    approval_id: str,
    result: str,
    reason: str = "",
) -> ApplicabilityEvaluation:
    return ApplicabilityEvaluation(
        rule_id=rule_id,
        approval_id=approval_id,
        result=result,
        reason=reason or f"{rule_id} evaluated {result}",
        required_inputs=[],
        missing_inputs=[],
        authority="",
        source_references=[
            SourceRef(source_id="SRC-PROBE", citation_span="probe")
        ],
    )


def _comp(
    approval_id: str,
    triggers: list[str] | None = None,
    exemptions: list[str] | None = None,
    classifications: list[str] | None = None,
) -> dict[str, ApprovalComposition]:
    return {
        approval_id: ApprovalComposition(
            approval_id=approval_id,
            triggers=list(triggers or []),
            exemptions=list(exemptions or []),
            classifications=list(classifications or []),
        )
    }


def _run(
    approval_id: str,
    evals: list[ApplicabilityEvaluation],
    **groups: list[str],
) -> ApplicabilityEvaluation:
    out = summarize_by_approval(evals, compositions=_comp(approval_id, **groups))
    assert set(out) == {approval_id}
    return out[approval_id]


class TestTriggerRows:
    """§18 rows 1-3: ordinary trigger behavior is unchanged."""

    def test_row01_trigger_true_applies(self):
        got = _run("A", [_ev("T1", "A", "applies")], triggers=["T1"])
        assert got.result == "applies"
        assert got.rule_id == "T1"

    def test_row02_trigger_false_does_not_apply(self):
        got = _run("A", [_ev("T1", "A", "does_not_apply")], triggers=["T1"])
        assert got.result == "does_not_apply"

    def test_row03_trigger_unknown_insufficient(self):
        got = _run(
            "A", [_ev("T1", "A", "insufficient_data")], triggers=["T1"]
        )
        assert got.result == "insufficient_data"

    def test_row03b_trigger_conditional_stays_conditional(self):
        got = _run("A", [_ev("T1", "A", "conditional")], triggers=["T1"])
        assert got.result == "conditional"

    def test_trigger_false_wins_over_trigger_unknown(self):
        """Legacy priority preserved inside the trigger group."""
        got = _run(
            "A",
            [
                _ev("T1", "A", "insufficient_data"),
                _ev("T2", "A", "does_not_apply"),
            ],
            triggers=["T1", "T2"],
        )
        assert got.result == "does_not_apply"
        assert got.rule_id == "T2"


class TestExemptionRows:
    """§18 rows 4-9: exemption polarity."""

    def test_row04_exemption_true_alone_never_applies(self):
        got = _run(
            "A",
            [_ev("T1", "A", "does_not_apply"), _ev("E1", "A", "applies")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "does_not_apply"

    def test_row04b_exemption_true_without_triggers_never_applies(self):
        got = _run("A", [_ev("E1", "A", "applies")], exemptions=["E1"])
        assert got.result == "insufficient_data"

    def test_row05_exemption_false_alone_never_negates(self):
        got = _run(
            "A",
            [_ev("T1", "A", "does_not_apply"), _ev("E1", "A", "does_not_apply")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "does_not_apply"
        assert got.rule_id == "T1"

    def test_row06_exemption_unknown_alone_insufficient(self):
        got = _run(
            "A", [_ev("E1", "A", "insufficient_data")], exemptions=["E1"]
        )
        assert got.result == "insufficient_data"

    def test_row07_exemption_true_defeats_with_reason(self):
        got = _run(
            "A",
            [_ev("T1", "A", "applies"), _ev("X1", "A", "applies", "duty relieved")],
            triggers=["T1"],
            exemptions=["X1"],
        )
        assert got.result == "does_not_apply"
        assert got.rule_id == "X1"
        assert "Exempt under X1" in got.reason
        assert "duty relieved" in got.reason
        assert "T1" in got.reason

    def test_row08_exemption_false_trigger_applies(self):
        got = _run(
            "A",
            [_ev("T1", "A", "applies"), _ev("X1", "A", "does_not_apply")],
            triggers=["T1"],
            exemptions=["X1"],
        )
        assert got.result == "applies"
        assert got.rule_id == "T1"

    def test_row09_exemption_unknown_blocks_applies(self):
        got = _run(
            "A",
            [_ev("T1", "A", "applies"), _ev("X1", "A", "insufficient_data")],
            triggers=["T1"],
            exemptions=["X1"],
        )
        assert got.result == "conditional"
        assert got.rule_id == "X1"


class TestCombinationRows:
    """§18 rows 10-15: trigger × exemption matrix."""

    def test_row10_trigger_true_exemption_true_defeats(self):
        got = _run(
            "A",
            [_ev("T1", "A", "applies"), _ev("E1", "A", "applies", "exempt")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "does_not_apply"
        assert "Exempt under E1" in got.reason

    def test_row11_trigger_true_exemption_false_applies(self):
        got = _run(
            "A",
            [_ev("T1", "A", "applies"), _ev("E1", "A", "does_not_apply")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "applies"

    def test_row12_trigger_true_exemption_unknown_conditional(self):
        got = _run(
            "A",
            [_ev("T1", "A", "applies"), _ev("E1", "A", "conditional")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "conditional"

    def test_row13_trigger_unknown_exemption_true_not_applies(self):
        got = _run(
            "A",
            [_ev("T1", "A", "insufficient_data"), _ev("E1", "A", "applies")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "insufficient_data"
        assert "E1" in got.reason

    def test_row14_trigger_unknown_exemption_false_unknown(self):
        got = _run(
            "A",
            [_ev("T1", "A", "insufficient_data"), _ev("E1", "A", "does_not_apply")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "insufficient_data"

    def test_row15_trigger_unknown_exemption_unknown(self):
        got = _run(
            "A",
            [_ev("T1", "A", "insufficient_data"), _ev("E1", "A", "conditional")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "conditional"

    def test_trigger_false_exemption_true_no_duty(self):
        got = _run(
            "A",
            [_ev("T1", "A", "does_not_apply"), _ev("E1", "A", "applies")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "does_not_apply"
        assert got.rule_id == "T1"


class TestClassificationRows:
    """§18 rows 16-17: classification never decides alone."""

    def test_row16_classification_true_trigger_unknown_insufficient(self):
        got = _run(
            "A",
            [_ev("C1", "A", "applies")],
            classifications=["C1"],
        )
        assert got.result == "insufficient_data"

    def test_row17_classification_false_trigger_unknown_insufficient(self):
        got = _run(
            "A",
            [_ev("C1", "A", "does_not_apply")],
            classifications=["C1"],
        )
        assert got.result == "insufficient_data"

    def test_named_but_unevaluated_rule_is_unknown_pressure(self):
        got = _run(
            "A",
            [_ev("C1", "A", "applies")],
            triggers=["T9"],
            classifications=["C1"],
        )
        assert got.result == "insufficient_data"
        assert "T9" in got.reason


class TestReadinessProtectionRows:
    """§18 rows 18-19: defeat/unknown can never manufacture readiness."""

    def test_row18_defeat_verdict_is_does_not_apply(self):
        """Orchestration maps does_not_apply to NOT_APPLICABLE (never
        READY); the composition layer guarantees defeat surfaces only
        in that vocabulary - no new result is invented anywhere."""
        got = _run(
            "A",
            [_ev("T1", "A", "applies"), _ev("E1", "A", "applies")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result == "does_not_apply"
        assert got.result != "applies"

    def test_row19_unknown_defeater_withholds_ready(self):
        got = _run(
            "A",
            [_ev("T1", "A", "applies"), _ev("E1", "A", "insufficient_data")],
            triggers=["T1"],
            exemptions=["E1"],
        )
        assert got.result in ("conditional", "insufficient_data")

    def test_legacy_path_untouched_without_composition(self):
        """No composition entry → legacy priority, byte-identical."""
        out = summarize_by_approval(
            [_ev("E1", "A", "applies"), _ev("T1", "A", "does_not_apply")]
        )
        assert out["A"].result == "applies"
        assert out["A"].rule_id == "E1"


class TestRoleLint:
    """Lint protection: roles are explicit and composition-consistent.

    Every built rule has an expected audited role (new builders fail
    here until listed); every non-TRIGGER built rule must be named in
    some pack composition; every composed approval's built rules must
    be fully named with roles agreeing with the composition lists.
    """

    EXPECTED_ROLES = {
        "R-002": "classification",
        "R-007": "trigger",
        "R-009": "trigger",
        "R-011": "trigger",
        "R-012": "trigger",
        "R-018": "trigger",
        "R-026": "trigger",
        "R-028": "trigger",
        "R-030": "trigger",  # migration blocked: APR-026 has no active trigger rule
        "R-035": "trigger",
        "R-043": "exemption",
        "R-044": "exemption",
        "R-046": "trigger",
        "R-056": "trigger",
        "R-067": "trigger",
        "R-070": "trigger",
        "R-073": "trigger",
        "R-077": "trigger",
        "R-083": "trigger",
        "R-084": "trigger",
        "R-086": "trigger",
        "R-087": "trigger",
        "R-089": "trigger",
        "R-093": "trigger",
        "R-094": "trigger",
        "R-096": "trigger",
    }

    def test_every_built_rule_has_expected_role(self):
        from app.seed.mh.approvals import load_mh_approval_rules

        rules = {r.id: r for r in load_mh_approval_rules()}
        assert set(rules) == set(self.EXPECTED_ROLES)
        for rid, expected in self.EXPECTED_ROLES.items():
            assert rules[rid].role.value == expected, rid

    def test_non_trigger_rules_all_composed(self):
        from app.seed.mh.approvals import load_mh_approval_compositions

        named: set[str] = set()
        for comp in load_mh_approval_compositions().values():
            named |= set(comp.triggers) | set(comp.exemptions)
            named |= set(comp.classifications)
        non_trigger = {
            rid for rid, role in self.EXPECTED_ROLES.items() if role != "trigger"
        }
        assert non_trigger <= named

    def test_compositions_name_built_rules_with_matching_roles(self):
        from app.seed.mh.approvals import (
            load_mh_approval_compositions,
            load_mh_approval_rules,
        )

        roles = {r.id: r.role.value for r in load_mh_approval_rules()}
        by_approval: dict[str, set[str]] = {}
        for r in load_mh_approval_rules():
            by_approval.setdefault(r.approval_id, set()).add(r.id)
        for aid, comp in load_mh_approval_compositions().items():
            named = (
                set(comp.triggers)
                | set(comp.exemptions)
                | set(comp.classifications)
            )
            assert named <= set(roles), (aid, named - set(roles))
            assert named == by_approval.get(aid, set()), (
                aid,
                named ^ by_approval.get(aid, set()),
            )
            for rid in comp.triggers:
                assert roles[rid] == "trigger", rid
            for rid in comp.exemptions:
                assert roles[rid] == "exemption", rid
            for rid in comp.classifications:
                assert roles[rid] == "classification", rid

    def test_pack_serves_seed_compositions_gj_empty(self):
        from app.seed.mh.approvals import load_mh_approval_compositions
        from app.seed.pack import IN_GJ, IN_MH, load_regulatory_pack

        mh = load_regulatory_pack(IN_MH)
        assert mh.approval_compositions == load_mh_approval_compositions()
        assert set(mh.approval_compositions) == {"APR-001", "APR-043"}  # APR-026 blocked
        assert load_regulatory_pack(IN_GJ).approval_compositions == {}


class TestR044Migration:
    """R-044 domestic-exemption migration (data-only role flip).

    Predicate, facts, sources, dates untouched (rule-level pins in the
    utilities/GW suites stand). Only the approval-composition reading
    changes: APR-043 composition is now triggers [R-077] + exemptions
    [R-043, R-044]. Probed against the live pack composition.
    """

    def _comp(self):
        from app.seed.pack import IN_MH, load_regulatory_pack

        return load_regulatory_pack(IN_MH).approval_compositions["APR-043"]

    def _evals(self, facts):
        from app.rules.applicability import evaluate_approval_applicability
        from app.seed.mh.approvals import load_mh_approval_rules

        rules = [r for r in load_mh_approval_rules() if r.approval_id == "APR-043"]
        return evaluate_approval_applicability(rules, facts)

    def test_role_is_exemption(self):
        from app.seed.mh.approvals import load_mh_approval_rules

        assert next(
            r for r in load_mh_approval_rules() if r.id == "R-044"
        ).role.value == "exemption"

    def test_true_alone_never_applies(self):
        out = summarize_by_approval(
            self._evals({"F-WAT-06": "DOMESTIC_ONLY", "F-WAT-05": 5}),
            compositions={"APR-043": self._comp()},
        )["APR-043"]
        assert out.result == "insufficient_data"

    def test_false_alone_never_does_not_apply(self):
        out = summarize_by_approval(
            self._evals({"F-WAT-06": "INDUSTRIAL", "F-WAT-05": 50}),
            compositions={"APR-043": self._comp()},
        )["APR-043"]
        # Triggers unknown (GW-01/EXP-01/INC-01 missing), R-043
        # unevaluable too → unknown outcome, never a negative verdict.
        assert out.result == "insufficient_data"

    def test_unknown_never_disappears(self):
        out = summarize_by_approval(
            self._evals({"F-WAT-05": 5}),
            compositions={"APR-043": self._comp()},
        )["APR-043"]
        assert out.result == "insufficient_data"

    def test_trigger_true_exemption_true_defeats_with_reason(self):
        out = summarize_by_approval(
            self._evals(
                {
                    "F-GW-01": "OVER_EXPLOITED",
                    "F-EXP-01": True,
                    "F-INC-01": "LARGE",
                    "F-WAT-06": "DOMESTIC_ONLY",
                    "F-WAT-05": 5,
                }
            ),
            compositions={"APR-043": self._comp()},
        )["APR-043"]
        assert out.result == "does_not_apply"
        assert "Exempt under R-044" in out.reason

    def test_trigger_true_exemption_false_applies(self):
        out = summarize_by_approval(
            self._evals(
                {
                    "F-GW-01": "OVER_EXPLOITED",
                    "F-EXP-01": True,
                    "F-INC-01": "LARGE",
                    "F-WAT-06": "INDUSTRIAL",
                    "F-WAT-05": 50,
                }
            ),
            compositions={"APR-043": self._comp()},
        )["APR-043"]
        assert out.result == "applies"
        assert out.rule_id == "R-077"

    def test_trigger_true_exemption_unknown_conditional(self):
        out = summarize_by_approval(
            self._evals(
                {
                    "F-GW-01": "OVER_EXPLOITED",
                    "F-EXP-01": True,
                    "F-INC-01": "LARGE",
                    "F-WAT-05": 5,
                }
            ),
            compositions={"APR-043": self._comp()},
        )["APR-043"]
        # R-044 unevaluable (F-WAT-06 missing) → unknown defeater blocks.
        assert out.result == "conditional"

    def test_defeat_never_ready(self):
        from app.orchestration.service import orchestrate_application

        pack_rules = __import__(
            "app.seed.pack", fromlist=["load_regulatory_pack"]
        ).load_regulatory_pack("IN-MH")
        out = orchestrate_application(
            application_id="T",
            approval_id="APR-043",
            project_facts={
                "F-GW-01": "OVER_EXPLOITED",
                "F-EXP-01": True,
                "F-INC-01": "LARGE",
                "F-WAT-06": "DOMESTIC_ONLY",
                "F-WAT-05": 5,
            },
            approval_rules=pack_rules.approval_rules,
            approval_authorities=pack_rules.approval_authorities,
            dependencies=pack_rules.dependencies,
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            approval_compositions=pack_rules.approval_compositions,
        )
        assert out.applicability_result == "does_not_apply"
        assert out.status.value == "not_applicable"
        assert out.status.value != "ready"

    def test_r044_defeat_cannot_satisfy_approval_dependency(self):
        """R-044 defeat does not add to obtained_approvals and cannot satisfy DEP-009."""
        from app.rules.dependency_engine import evaluate_readiness
        from app.rules.dependency_models import ReadinessStatus
        from app.seed.pack import IN_MH, load_regulatory_pack

        pack = load_regulatory_pack(IN_MH)
        graph = evaluate_readiness(
            pack.dependencies,
            {
                "APR-010": "applies",
                "APR-008": "applies",
                "APR-009": "applies",
                "APR-043": "does_not_apply",
            },
            obtained=set(),
        )
        assert graph.readiness["APR-010"].readiness == ReadinessStatus.BLOCKED

