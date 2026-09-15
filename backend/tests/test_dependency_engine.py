"""Comprehensive tests for the dependency engine.

Covers:
- independent approvals run in parallel
- prerequisite blocks dependent approval
- prerequisite satisfied (obtained) makes dependent approval READY
- DOES_NOT_APPLY prerequisite does not create a blocker
- INSUFFICIENT_DATA/CONDITIONAL prerequisite is handled explicitly
- multi-level dependency produces correct stages
- independent branches share the same stage where appropriate
- cycle detection
- missing dependency definition
- deterministic ordering
- traceability
- integration with existing applicability results
- workbook-backed dependency/blocker scenario
"""
from __future__ import annotations

from app.rules.applicability import (
    evaluate_approval_applicability,
    summarize_by_approval,
)
from app.rules.dependency_engine import (
    _assign_stages,
    _build_adjacency,
    _detect_cycles,
    _topological_sort,
    evaluate_readiness,
)
from app.rules.dependency_models import (
    ApprovalDependency,
    DependencyGraph,
    ReadinessStatus,
)
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.dependencies import load_approval_dependencies
from app.seed.scenario import load_scenario


def _dep(approval_id: str, prereq: str, **kwargs) -> ApprovalDependency:
    return ApprovalDependency(approval_id=approval_id, prerequisite_approval_id=prereq, **kwargs)


# ============================================================
# 1. Independent approvals run in parallel
# ============================================================


class TestIndependentApprovalsParallel:
    def test_no_dependencies_all_ready(self):
        """Approvals with no dependencies are all READY at stage 0."""
        deps: list[ApprovalDependency] = []
        applicability = {"A01": "applies", "A04": "applies", "A07": "applies"}
        graph = evaluate_readiness(deps, applicability)

        for aid in ("A01", "A04", "A07"):
            assert graph.readiness[aid].readiness == ReadinessStatus.READY
            assert graph.readiness[aid].stage == 0

    def test_all_independent_share_stage_0(self):
        """All independent approvals end up in stage 0."""
        deps: list[ApprovalDependency] = []
        applicability = {f"A{i:02d}": "applies" for i in range(1, 10)}
        graph = evaluate_readiness(deps, applicability)

        stage_0_ids = set(graph.stages.get(0, []))
        expected_ids = {f"A{i:02d}" for i in range(1, 10)}
        assert stage_0_ids == expected_ids


# ============================================================
# 2. Prerequisite blocks dependent approval
# ============================================================


class TestPrerequisiteBlocks:
    def test_single_dependency_blocks(self):
        """A02 depends on A04. A04 applies but not obtained → A02 BLOCKED."""
        deps = [_dep("A02", "A04")]
        applicability = {"A02": "applies", "A04": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A04"].readiness == ReadinessStatus.READY
        assert graph.readiness["A02"].readiness == ReadinessStatus.BLOCKED
        assert "A04" in graph.readiness["A02"].blocking_prerequisites

    def test_dependency_chain_blocks(self):
        """A04 → A02 → A03. None obtained. A02 and A03 are BLOCKED."""
        deps = [
            _dep("A02", "A04"),
            _dep("A03", "A02"),
        ]
        applicability = {"A04": "applies", "A02": "applies", "A03": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A04"].readiness == ReadinessStatus.READY
        assert graph.readiness["A02"].readiness == ReadinessStatus.BLOCKED
        assert graph.readiness["A03"].readiness == ReadinessStatus.BLOCKED


# ============================================================
# 3. Prerequisite satisfied (obtained) makes dependent READY
# ============================================================


class TestPrerequisiteSatisfied:
    def test_obtained_prerequisite_unblocks(self):
        """When prerequisite is obtained, dependent becomes READY."""
        deps = [_dep("A02", "A04")]
        applicability = {"A02": "applies", "A04": "applies"}
        obtained = {"A04"}
        graph = evaluate_readiness(deps, applicability, obtained=obtained)

        assert graph.readiness["A04"].readiness == ReadinessStatus.READY
        assert graph.readiness["A02"].readiness == ReadinessStatus.READY
        assert "A04" in graph.readiness["A02"].ready_prerequisites

    def test_chain_resolves_when_all_obtained(self):
        """A04 → A02 → A03: all become READY when all are obtained."""
        deps = [
            _dep("A02", "A04"),
            _dep("A03", "A02"),
        ]
        applicability = {"A04": "applies", "A02": "applies", "A03": "applies"}
        obtained = {"A04", "A02", "A03"}
        graph = evaluate_readiness(deps, applicability, obtained=obtained)

        assert graph.readiness["A04"].readiness == ReadinessStatus.READY
        assert graph.readiness["A02"].readiness == ReadinessStatus.READY
        assert graph.readiness["A03"].readiness == ReadinessStatus.READY

    def test_partial_chain_resolves(self):
        """A04 → A02 → A03: only A04 obtained → A02 READY, A03 BLOCKED."""
        deps = [
            _dep("A02", "A04"),
            _dep("A03", "A02"),
        ]
        applicability = {"A04": "applies", "A02": "applies", "A03": "applies"}
        obtained = {"A04"}
        graph = evaluate_readiness(deps, applicability, obtained=obtained)

        assert graph.readiness["A04"].readiness == ReadinessStatus.READY
        assert graph.readiness["A02"].readiness == ReadinessStatus.READY
        assert graph.readiness["A03"].readiness == ReadinessStatus.BLOCKED


# ============================================================
# 4. DOES_NOT_APPLY prerequisite does not create a blocker
# ============================================================


class TestDoesNotApplyPrerequisite:
    def test_does_not_apply_not_a_blocker(self):
        """If prerequisite DOES_NOT_APPLY, it is not a blocker."""
        deps = [_dep("A02", "A04")]
        applicability = {"A02": "applies", "A04": "does_not_apply"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A04"].readiness == ReadinessStatus.NOT_APPLICABLE
        assert graph.readiness["A02"].readiness == ReadinessStatus.READY
        assert graph.readiness["A02"].blocking_prerequisites == []

    def test_mixed_prereq_some_not_applicable(self):
        """A03 depends on A02 and A04. A04 does_not_apply, A02 obtained."""
        deps = [
            _dep("A03", "A02"),
            _dep("A03", "A04"),
        ]
        applicability = {"A02": "applies", "A03": "applies", "A04": "does_not_apply"}
        obtained = {"A02"}
        graph = evaluate_readiness(deps, applicability, obtained=obtained)

        assert graph.readiness["A03"].readiness == ReadinessStatus.READY


# ============================================================
# 5. INSUFFICIENT_DATA/CONDITIONAL prerequisite is handled explicitly
# ============================================================


class TestConditionalPrerequisite:
    def test_insufficient_data_prerequisite_blocks(self):
        """If prerequisite has INSUFFICIENT_DATA, dependent is BLOCKED."""
        deps = [_dep("A02", "A04")]
        applicability = {"A02": "applies", "A04": "insufficient_data"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A04"].readiness == ReadinessStatus.PENDING_EVALUATION
        assert graph.readiness["A02"].readiness == ReadinessStatus.BLOCKED
        assert "A04" in graph.readiness["A02"].blocking_prerequisites

    def test_conditional_prerequisite_blocks(self):
        """If prerequisite has CONDITIONAL, dependent is BLOCKED."""
        deps = [_dep("A03", "A02")]
        applicability = {"A02": "conditional", "A03": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A02"].readiness == ReadinessStatus.PENDING_EVALUATION
        assert graph.readiness["A03"].readiness == ReadinessStatus.BLOCKED

    def test_conditional_dependent_pending(self):
        """An approval with CONDITIONAL applicability is PENDING_EVALUATION."""
        deps: list[ApprovalDependency] = []
        applicability = {"A05": "conditional"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A05"].readiness == ReadinessStatus.PENDING_EVALUATION


# ============================================================
# 6. Multi-level dependency produces correct stages
# ============================================================


class TestMultiLevelStages:
    def test_linear_chain_stages(self):
        """A04 → A02 → A03 produces stages 0, 1, 2."""
        deps = [
            _dep("A02", "A04"),
            _dep("A03", "A02"),
        ]
        applicability = {"A04": "applies", "A02": "applies", "A03": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A04"].stage == 0
        assert graph.readiness["A02"].stage == 1
        assert graph.readiness["A03"].stage == 2
        assert graph.total_stages == 3

    def test_diamond_stages(self):
        """Diamond: A01 → A02, A01 → A03, A02+A03 → A04. Stages: 0, 1, 1, 2."""
        deps = [
            _dep("A02", "A01"),
            _dep("A03", "A01"),
            _dep("A04", "A02"),
            _dep("A04", "A03"),
        ]
        applicability = {
            "A01": "applies",
            "A02": "applies",
            "A03": "applies",
            "A04": "applies",
        }
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A01"].stage == 0
        assert graph.readiness["A02"].stage == 1
        assert graph.readiness["A03"].stage == 1
        assert graph.readiness["A04"].stage == 2
        assert graph.total_stages == 3


# ============================================================
# 7. Independent branches share the same stage
# ============================================================


class TestSharedStages:
    def test_parallel_branches_same_stage(self):
        """Two independent branches at the same depth share a stage."""
        deps = [
            _dep("A02", "A01"),
            _dep("A04", "A03"),
        ]
        applicability = {
            "A01": "applies",
            "A02": "applies",
            "A03": "applies",
            "A04": "applies",
        }
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A01"].stage == 0
        assert graph.readiness["A03"].stage == 0
        assert graph.readiness["A02"].stage == 1
        assert graph.readiness["A04"].stage == 1


# ============================================================
# 8. Cycle detection
# ============================================================


class TestCycleDetection:
    def test_simple_cycle(self):
        """A → B → A is detected as a cycle."""
        deps = [_dep("A", "B"), _dep("B", "A")]
        applicability = {"A": "applies", "B": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.has_cycles is True
        assert len(graph.errors) > 0
        assert "Cyclic dependency" in graph.errors[0]

    def test_three_node_cycle(self):
        """A → B → C → A is detected."""
        deps = [_dep("A", "B"), _dep("B", "C"), _dep("C", "A")]
        applicability = {"A": "applies", "B": "applies", "C": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.has_cycles is True

    def test_no_false_positive_on_acyclic(self):
        """A04 → A02 → A03 is not a cycle."""
        deps = [_dep("A02", "A04"), _dep("A03", "A02")]
        applicability = {"A04": "applies", "A02": "applies", "A03": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.has_cycles is False
        assert graph.errors == []


# ============================================================
# 9. Missing dependency definition
# ============================================================


class TestMissingDefinition:
    def test_prerequisite_not_in_applicability(self):
        """Prerequisite not in applicability results → BLOCKED."""
        deps = [_dep("A02", "A04")]
        applicability = {"A02": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.readiness["A02"].readiness == ReadinessStatus.BLOCKED


# ============================================================
# 10. Deterministic ordering
# ============================================================


class TestDeterministicResults:
    def test_same_input_same_output(self):
        """Running evaluate_readiness twice with same input produces identical results."""
        deps = [_dep("A02", "A04"), _dep("A03", "A02")]
        applicability = {"A04": "applies", "A02": "applies", "A03": "applies"}

        g1 = evaluate_readiness(deps, applicability)
        g2 = evaluate_readiness(deps, applicability)

        for aid in applicability:
            assert g1.readiness[aid].readiness == g2.readiness[aid].readiness
            assert g1.readiness[aid].stage == g2.readiness[aid].stage

    def test_stage_ordering_is_stable(self):
        """Stage assignment is consistent across runs."""
        deps = [_dep("A02", "A04"), _dep("A03", "A02")]
        applicability = {"A04": "applies", "A02": "applies", "A03": "applies"}

        stages_list = []
        for _ in range(5):
            g = evaluate_readiness(deps, applicability)
            stages_list.append(
                {aid: g.readiness[aid].stage for aid in applicability}
            )

        assert all(s == stages_list[0] for s in stages_list)


# ============================================================
# 11. Traceability
# ============================================================


class TestTraceability:
    def test_dependency_trace_recorded(self):
        """Each dependency edge is recorded in the trace."""
        deps = [_dep("A02", "A04", source_ref="S04", evidence="test evidence")]
        applicability = {"A04": "applies", "A02": "applies"}
        graph = evaluate_readiness(deps, applicability)

        trace = graph.readiness["A02"].dependency_trace
        assert len(trace) == 1
        assert trace[0]["prerequisite_approval_id"] == "A04"
        assert trace[0]["source_ref"] == "S04"
        assert trace[0]["evidence"] == "test evidence"

    def test_dependency_count(self):
        """Graph records the total number of dependency edges."""
        deps = [_dep("A02", "A04"), _dep("A03", "A04"), _dep("A03", "A02")]
        applicability = {"A04": "applies", "A02": "applies", "A03": "applies"}
        graph = evaluate_readiness(deps, applicability)

        assert graph.dependency_count == 3

    def test_readiness_explanation_present(self):
        """Every readiness result has a non-empty explanation."""
        deps = [_dep("A02", "A04")]
        applicability = {"A04": "applies", "A02": "applies"}
        graph = evaluate_readiness(deps, applicability)

        for aid in applicability:
            assert graph.readiness[aid].explanation


# ============================================================
# 12. Integration with existing applicability results
# ============================================================


class TestApplicabilityIntegration:
    def test_full_scenario_evaluation(self):
        """Run applicability then dependency evaluation on the workbook scenario."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        dependencies = load_approval_dependencies()

        evaluations = evaluate_approval_applicability(rules, scenario, authorities)
        aggregated = summarize_by_approval(evaluations)
        applicability = {aid: ev.result for aid, ev in aggregated.items()}

        graph = evaluate_readiness(dependencies, applicability)

        assert isinstance(graph, DependencyGraph)
        assert len(graph.readiness) > 0
        assert graph.has_cycles is False
        assert graph.errors == []

        expected_ids = {f"A{i:02d}" for i in range(1, 19)}
        assert set(graph.readiness.keys()) == expected_ids

    def test_does_not_apply_approvals_are_not_applicable(self):
        """Approvals that don't apply get NOT_APPLICABLE readiness."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        dependencies = load_approval_dependencies()

        evaluations = evaluate_approval_applicability(rules, scenario, authorities)
        aggregated = summarize_by_approval(evaluations)
        applicability = {aid: ev.result for aid, ev in aggregated.items()}

        graph = evaluate_readiness(dependencies, applicability)

        for aid, r in graph.readiness.items():
            if applicability.get(aid) == "does_not_apply":
                assert r.readiness == ReadinessStatus.NOT_APPLICABLE, (
                    f"{aid} should be NOT_APPLICABLE"
                )


# ============================================================
# 13. Workbook-backed dependency/blocker scenario
# ============================================================


class TestWorkbookDependencyScenario:
    def test_a03_blocked_by_a02_and_a04(self):
        """A03 (drainage) is blocked by A02 (water) and A04 (CTE) when none obtained."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        dependencies = load_approval_dependencies()

        evaluations = evaluate_approval_applicability(rules, scenario, authorities)
        aggregated = summarize_by_approval(evaluations)
        applicability = {aid: ev.result for aid, ev in aggregated.items()}

        assert applicability.get("A02") == "applies"
        assert applicability.get("A03") == "applies"
        assert applicability.get("A04") == "applies"

        graph = evaluate_readiness(dependencies, applicability)

        assert graph.readiness["A04"].readiness == ReadinessStatus.READY
        assert graph.readiness["A04"].stage == 0

        # A02 depends on A04 which is not obtained → BLOCKED
        assert graph.readiness["A02"].readiness == ReadinessStatus.BLOCKED
        assert graph.readiness["A02"].stage == 1

        # A03 depends on A02 (BLOCKED) and A04 (not obtained) → BLOCKED
        assert graph.readiness["A03"].readiness == ReadinessStatus.BLOCKED
        assert graph.readiness["A03"].stage == 2

    def test_a03_unblocked_when_prerequisites_obtained(self):
        """A03 becomes READY when A04 and A02 are obtained."""
        dependencies = load_approval_dependencies()
        applicability = {"A02": "applies", "A03": "applies", "A04": "applies"}
        obtained = {"A04", "A02"}

        graph = evaluate_readiness(dependencies, applicability, obtained=obtained)

        assert graph.readiness["A04"].readiness == ReadinessStatus.READY
        assert graph.readiness["A02"].readiness == ReadinessStatus.READY
        assert graph.readiness["A03"].readiness == ReadinessStatus.READY

    def test_a03_blocked_when_a04_does_not_apply(self):
        """A03 is not blocked by A04 when A04 does not apply, but blocked by A02."""
        dependencies = load_approval_dependencies()
        applicability = {"A02": "applies", "A03": "applies", "A04": "does_not_apply"}

        graph = evaluate_readiness(dependencies, applicability)

        assert graph.readiness["A04"].readiness == ReadinessStatus.NOT_APPLICABLE
        # A02 depends on A04 which is NOT_APPLICABLE → A02 is READY
        assert graph.readiness["A02"].readiness == ReadinessStatus.READY
        # A03 depends on A02 (READY but not obtained) and A04 (NOT_APPLICABLE)
        # A02 not obtained → A03 BLOCKED
        assert graph.readiness["A03"].readiness == ReadinessStatus.BLOCKED

    def test_stage_numbering_from_workbook(self):
        """Workbook dependency chain produces correct stage numbering."""
        dependencies = load_approval_dependencies()
        applicability = {f"A{i:02d}": "applies" for i in range(1, 19)}

        graph = evaluate_readiness(dependencies, applicability)

        assert graph.readiness["A04"].stage == 0
        assert graph.readiness["A02"].stage == 1
        assert graph.readiness["A03"].stage == 2

        for i in [1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]:
            aid = f"A{i:02d}"
            assert graph.readiness[aid].stage == 0, f"{aid} should be stage 0"

    def test_parallel_independent_approvals_in_stage_0(self):
        """Most approvals are independent and share stage 0."""
        dependencies = load_approval_dependencies()
        applicability = {f"A{i:02d}": "applies" for i in range(1, 19)}

        graph = evaluate_readiness(dependencies, applicability)

        stage_0 = set(graph.stages.get(0, []))
        assert "A01" in stage_0
        assert "A04" in stage_0
        assert "A05" in stage_0
        assert "A06" in stage_0
        assert "A07" in stage_0
        assert "A02" not in stage_0
        assert "A03" not in stage_0


# ============================================================
# 14. Edge cases
# ============================================================


class TestEdgeCases:
    def test_empty_dependencies(self):
        """Empty dependency list works correctly."""
        graph = evaluate_readiness([], {"A01": "applies"})
        assert graph.readiness["A01"].readiness == ReadinessStatus.READY
        assert graph.dependency_count == 0

    def test_empty_applicability(self):
        """Empty applicability with dependencies produces results for known nodes."""
        deps = [_dep("A02", "A04")]
        graph = evaluate_readiness(deps, {})
        assert "A02" in graph.readiness
        assert "A04" in graph.readiness

    def test_self_dependency_detected_as_cycle(self):
        """A self-dependency (A02 depends on A02) is a cycle."""
        deps = [_dep("A02", "A02")]
        applicability = {"A02": "applies"}
        graph = evaluate_readiness(deps, applicability)
        assert graph.has_cycles is True


# ============================================================
# 15. Internal algorithm tests
# ============================================================


class TestInternalAlgorithms:
    def test_build_adjacency(self):
        """Adjacency list correctly maps dependent → prereqs."""
        deps = [_dep("A02", "A04"), _dep("A03", "A02")]
        adj = _build_adjacency(deps)
        assert adj["A02"] == ["A04"]
        assert adj["A03"] == ["A02"]

    def test_detect_cycles_none(self):
        """No cycle in a linear chain."""
        adj = {"A02": ["A04"], "A03": ["A02"], "A04": []}
        assert _detect_cycles(adj, {"A02", "A03", "A04"}) is None

    def test_detect_cycles_found(self):
        """Cycle detected in A → B → A."""
        adj = {"A": ["B"], "B": ["A"]}
        cycle = _detect_cycles(adj, {"A", "B"})
        assert cycle is not None
        assert len(cycle) >= 2

    def test_topological_sort_linear(self):
        """Topological sort of linear chain."""
        adj = {"A02": ["A04"], "A03": ["A02"], "A04": []}
        order = _topological_sort(adj, {"A02", "A03", "A04"})
        assert order is not None
        assert order.index("A04") < order.index("A02")
        assert order.index("A02") < order.index("A03")

    def test_topological_sort_cyclic(self):
        """Topological sort returns None for cyclic graph."""
        adj = {"A": ["B"], "B": ["A"]}
        assert _topological_sort(adj, {"A", "B"}) is None

    def test_assign_stages_linear(self):
        """Stage assignment for linear chain."""
        adj = {"A02": ["A04"], "A03": ["A02"], "A04": []}
        stages = _assign_stages(adj, {"A02", "A03", "A04"})
        assert stages["A04"] == 0
        assert stages["A02"] == 1
        assert stages["A03"] == 2

    def test_assign_stages_diamond(self):
        """Stage assignment for diamond graph."""
        adj = {
            "A02": ["A01"],
            "A03": ["A01"],
            "A04": ["A02", "A03"],
            "A01": [],
        }
        stages = _assign_stages(adj, {"A01", "A02", "A03", "A04"})
        assert stages["A01"] == 0
        assert stages["A02"] == 1
        assert stages["A03"] == 1
        assert stages["A04"] == 2
