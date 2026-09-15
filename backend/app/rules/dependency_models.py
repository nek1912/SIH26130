"""Data models for the approval dependency engine.

Separate from applicability logic. Applicability answers:
  "Does this approval/rule apply?"

Dependency engine answers:
  "Given applicable approvals and their prerequisites,
   is this approval ready to proceed?"

Models:
- ApprovalDependency: a directed edge (prerequisite → dependent)
- ReadinessStatus: enum for BLOCKED / READY / NOT_APPLICABLE / PENDING_EVALUATION
- ApprovalReadiness: per-approval readiness result with traceability
- DependencyCycleError: raised when a cycle is detected
- DependencyGraph: the full evaluation result
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ReadinessStatus(StrEnum):
    """Readiness status for an applicable approval."""

    READY = "ready"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"
    PENDING_EVALUATION = "pending_evaluation"


class ApprovalDependency(BaseModel):
    """A directed prerequisite edge: approval_id depends on prerequisite_approval_id.

    Attributes:
        approval_id: the dependent approval.
        prerequisite_approval_id: the approval that must be obtained first.
        relationship: optional label (e.g. "regulatory_prerequisite",
            "procedural_prerequisite").
        source_ref: traceability to the source that defines this dependency.
        evidence: short description of why this dependency exists.
        confidence: "explicit" if directly stated in workbook/sources,
            "inferred" if derived from workflow ordering.
    """

    approval_id: str = Field(min_length=1)
    prerequisite_approval_id: str = Field(min_length=1)
    relationship: str = "regulatory_prerequisite"
    source_ref: str = Field(default="", min_length=0)
    evidence: str = Field(default="", min_length=0)
    confidence: str = Field(default="explicit", pattern="^(explicit|inferred)$")


class ApprovalReadiness(BaseModel):
    """Per-approval readiness result with full traceability.

    Attributes:
        approval_id: the approval this result concerns.
        applicability: the applicability outcome from the applicability engine.
        readiness: BLOCKED, READY, NOT_APPLICABLE, or PENDING_EVALUATION.
        blocking_prerequisites: prerequisite approval_ids that are not satisfied.
        ready_prerequisites: prerequisite approval_ids that are satisfied.
        stage: topological stage number (0 = no prerequisites).
        explanation: human-readable explanation of the readiness status.
        dependency_trace: list of dependency records that contribute to this result.
    """

    approval_id: str = Field(min_length=1)
    applicability: str = Field(
        default="",
        description="Applicability outcome: applies/does_not_apply/conditional/insufficient_data",
    )
    readiness: ReadinessStatus = ReadinessStatus.PENDING_EVALUATION
    blocking_prerequisites: list[str] = Field(default_factory=list)
    ready_prerequisites: list[str] = Field(default_factory=list)
    stage: int = Field(ge=0, default=0)
    explanation: str = ""
    dependency_trace: list[dict[str, Any]] = Field(default_factory=list)


class DependencyCycleError(Exception):
    """Raised when a cyclic dependency is detected in the approval graph."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        cycle_str = " → ".join(cycle)
        super().__init__(f"Cyclic dependency detected: {cycle_str}")


class DependencyGraph(BaseModel):
    """Full dependency evaluation result.

    Attributes:
        readiness: per-approval readiness results.
        stages: mapping of stage number → list of approval_ids at that stage.
        total_stages: number of stages in the dependency graph.
        has_cycles: whether cycles were detected (should be False in valid graphs).
        errors: list of validation errors (cycles, missing definitions, etc.).
        dependency_count: total number of dependency edges.
    """

    readiness: dict[str, ApprovalReadiness] = Field(default_factory=dict)
    stages: dict[int, list[str]] = Field(default_factory=dict)
    total_stages: int = Field(ge=0, default=0)
    has_cycles: bool = False
    errors: list[str] = Field(default_factory=list)
    dependency_count: int = Field(ge=0, default=0)
