"""Deterministic approval dependency engine.

Given a set of approval dependencies and applicability results,
computes readiness status for each approval:
- Which approvals are READY to proceed
- Which are BLOCKED by unmet prerequisites
- What stage number each approval belongs to
- Full traceability for every decision

This engine is deterministic and separate from RAG/LLM logic.
No LLM calls are made during evaluation.

Readiness semantics:
- NOT_APPLICABLE: approval does not apply.
- PENDING_EVALUATION: applicability is conditional/insufficient_data.
- READY: approval has no prerequisites, or all prerequisites are
  either NOT_APPLICABLE or themselves READY (and obtainable).
  Note: "ready" means the approval CAN be applied for, not that
  it has been obtained. For dependency checking, a prerequisite
  that is READY satisfies the dependency because it is obtainable.
- BLOCKED: at least one prerequisite is not satisfied.

Algorithm:
1. Build adjacency list from dependency edges
2. Detect cycles (DFS with coloring)
3. Topological sort (Kahn's algorithm)
4. Stage assignment (longest path from root, cycle-safe)
5. Readiness evaluation in topological order
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from app.rules.dependency_models import (
    ApprovalDependency,
    ApprovalReadiness,
    DependencyGraph,
    ReadinessStatus,
)


def _build_adjacency(
    dependencies: list[ApprovalDependency],
) -> dict[str, list[str]]:
    """Build adjacency list: approval_id → list of prerequisite_approval_ids.

    If A depends on B, then adj[A] contains B.
    """
    adj: dict[str, list[str]] = defaultdict(list)
    for dep in dependencies:
        adj[dep.approval_id].append(dep.prerequisite_approval_id)
    return dict(adj)


def _detect_cycles(
    adj: dict[str, list[str]], all_nodes: set[str]
) -> list[str] | None:
    """Detect cycles using DFS with three-color marking.

    Returns the cycle path if found, None otherwise.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in all_nodes}
    parent: dict[str, str | None] = {n: None for n in all_nodes}

    def dfs(node: str) -> list[str] | None:
        color[node] = GRAY
        for neighbor in adj.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                cycle = [neighbor, node]
                current = node
                while parent[current] is not None and parent[current] != neighbor:
                    current = parent[current]  # type: ignore[assignment]
                    cycle.append(current)
                cycle.reverse()
                cycle.append(neighbor)
                return cycle
            if color[neighbor] == WHITE:
                parent[neighbor] = node
                result = dfs(neighbor)
                if result is not None:
                    return result
        color[node] = BLACK
        return None

    for node in all_nodes:
        if color[node] == WHITE:
            result = dfs(node)
            if result is not None:
                return result
    return None


def _topological_sort(
    adj: dict[str, list[str]], all_nodes: set[str]
) -> list[str] | None:
    """Kahn's algorithm for topological sort.

    Returns the sorted list if acyclic, None if cyclic.
    """
    in_degree: dict[str, int] = {n: 0 for n in all_nodes}
    for node, prereqs in adj.items():
        for p in prereqs:
            if p in in_degree:
                in_degree[node] += 1

    queue: deque[str] = deque()
    for node, deg in in_degree.items():
        if deg == 0:
            queue.append(node)

    result: list[str] = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for other, prereqs in adj.items():
            if node in prereqs:
                in_degree[other] -= 1
                if in_degree[other] == 0:
                    queue.append(other)

    if len(result) != len(all_nodes):
        return None
    return result


def _assign_stages(
    adj: dict[str, list[str]],
    all_nodes: set[str],
    topo_order: list[str] | None = None,
) -> dict[str, int]:
    """Assign stage numbers based on longest path from root.

    Stage 0 = no prerequisites.
    Stage N = max(stage of all prerequisites) + 1.
    """
    stages: dict[str, int] = {}

    if topo_order is not None:
        for node in topo_order:
            prereqs = adj.get(node, [])
            if not prereqs:
                stages[node] = 0
            else:
                max_prereq = max(
                    stages.get(p, 0) for p in prereqs if p in all_nodes
                )
                stages[node] = max_prereq + 1
    else:
        IN_PROGRESS = -1

        def compute_stage(node: str) -> int:
            if node in stages and stages[node] != IN_PROGRESS:
                return stages[node]
            if stages.get(node) == IN_PROGRESS:
                stages[node] = 0
                return 0
            stages[node] = IN_PROGRESS
            prereqs = adj.get(node, [])
            if not prereqs:
                stages[node] = 0
                return 0
            max_prereq_stage = max(
                compute_stage(p) for p in prereqs if p in all_nodes
            )
            stages[node] = max_prereq_stage + 1
            return stages[node]

        for node in all_nodes:
            compute_stage(node)

    return stages


def evaluate_readiness(
    dependencies: list[ApprovalDependency],
    applicability_results: dict[str, str],
    all_approval_ids: list[str] | None = None,
    obtained: set[str] | None = None,
) -> DependencyGraph:
    """Evaluate readiness for all approvals given dependencies and applicability.

    Args:
        dependencies: list of prerequisite edges.
        applicability_results: mapping of approval_id → applicability outcome.
        all_approval_ids: optional complete list of approval IDs.
        obtained: set of approval_ids that have been obtained/completed.
            A prerequisite is satisfied if it is NOT_APPLICABLE or in obtained.

    Returns:
        DependencyGraph with full readiness results, stage assignments,
        and any errors detected.
    """
    if obtained is None:
        obtained = set()

    all_nodes: set[str] = set(all_approval_ids or [])
    for dep in dependencies:
        all_nodes.add(dep.approval_id)
        all_nodes.add(dep.prerequisite_approval_id)
    for aid in applicability_results:
        all_nodes.add(aid)

    adj = _build_adjacency(dependencies)

    errors: list[str] = []
    for dep in dependencies:
        if dep.prerequisite_approval_id not in all_nodes:
            errors.append(
                f"Dependency on unknown approval '{dep.prerequisite_approval_id}' "
                f"from '{dep.approval_id}'"
            )

    cycle = _detect_cycles(adj, all_nodes)
    if cycle is not None:
        errors.append(f"Cyclic dependency: {' → '.join(cycle)}")

    topo_order = _topological_sort(adj, all_nodes)
    stage_map = _assign_stages(adj, all_nodes, topo_order)

    dep_lookup: dict[str, list[ApprovalDependency]] = defaultdict(list)
    for dep in dependencies:
        dep_lookup[dep.approval_id].append(dep)

    eval_order = topo_order if topo_order is not None else sorted(all_nodes)

    readiness: dict[str, ApprovalReadiness] = {}
    stages_output: dict[int, list[str]] = defaultdict(list)

    for approval_id in eval_order:
        applicability = applicability_results.get(approval_id, "")

        if applicability == "does_not_apply":
            readiness[approval_id] = ApprovalReadiness(
                approval_id=approval_id,
                applicability=applicability,
                readiness=ReadinessStatus.NOT_APPLICABLE,
                stage=stage_map.get(approval_id, 0),
                explanation="Approval does not apply; dependencies not evaluated.",
            )
            stages_output[stage_map.get(approval_id, 0)].append(approval_id)
            continue

        if applicability in ("conditional", "insufficient_data"):
            readiness[approval_id] = ApprovalReadiness(
                approval_id=approval_id,
                applicability=applicability,
                readiness=ReadinessStatus.PENDING_EVALUATION,
                stage=stage_map.get(approval_id, 0),
                explanation=(
                    f"Applicability is '{applicability}'; "
                    "readiness cannot be determined until applicability resolves."
                ),
            )
            stages_output[stage_map.get(approval_id, 0)].append(approval_id)
            continue

        prereqs = adj.get(approval_id, [])
        if not prereqs:
            readiness[approval_id] = ApprovalReadiness(
                approval_id=approval_id,
                applicability=applicability,
                readiness=ReadinessStatus.READY,
                stage=stage_map.get(approval_id, 0),
                explanation="No prerequisites; approval is ready to proceed.",
            )
            stages_output[stage_map.get(approval_id, 0)].append(approval_id)
            continue

        blocking: list[str] = []
        satisfied: list[str] = []
        trace: list[dict[str, Any]] = []

        for prereq_id in prereqs:
            prereq_applicability = applicability_results.get(prereq_id, "")
            deps_for_trace = dep_lookup.get(approval_id, [])
            matching_deps = [
                d for d in deps_for_trace if d.prerequisite_approval_id == prereq_id
            ]
            source_ref = matching_deps[0].source_ref if matching_deps else ""
            evidence = matching_deps[0].evidence if matching_deps else ""

            trace.append(
                {
                    "prerequisite_approval_id": prereq_id,
                    "prerequisite_applicability": prereq_applicability,
                    "source_ref": source_ref,
                    "evidence": evidence,
                }
            )

            if prereq_applicability == "does_not_apply":
                satisfied.append(prereq_id)
            elif prereq_applicability in ("applies", ""):
                if prereq_id in obtained:
                    satisfied.append(prereq_id)
                else:
                    blocking.append(prereq_id)
            elif prereq_applicability in ("conditional", "insufficient_data"):
                blocking.append(prereq_id)
            else:
                blocking.append(prereq_id)

        if blocking:
            readiness[approval_id] = ApprovalReadiness(
                approval_id=approval_id,
                applicability=applicability,
                readiness=ReadinessStatus.BLOCKED,
                blocking_prerequisites=blocking,
                ready_prerequisites=satisfied,
                stage=stage_map.get(approval_id, 0),
                explanation=(
                    f"Blocked by: {', '.join(blocking)}. "
                    f"Satisfied: {', '.join(satisfied) if satisfied else 'none'}."
                ),
                dependency_trace=trace,
            )
        else:
            readiness[approval_id] = ApprovalReadiness(
                approval_id=approval_id,
                applicability=applicability,
                readiness=ReadinessStatus.READY,
                blocking_prerequisites=[],
                ready_prerequisites=satisfied,
                stage=stage_map.get(approval_id, 0),
                explanation="All prerequisites satisfied; approval is ready to proceed.",
                dependency_trace=trace,
            )

        stages_output[stage_map.get(approval_id, 0)].append(approval_id)

    sorted_stages = dict(sorted(stages_output.items()))

    return DependencyGraph(
        readiness=readiness,
        stages=sorted_stages,
        total_stages=max(sorted_stages.keys(), default=-1) + 1,
        has_cycles=cycle is not None,
        errors=errors,
        dependency_count=len(dependencies),
    )
