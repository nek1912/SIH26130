"""Workflow stage definitions and configuration.

A workflow is an ordered list of stages. Each stage has a type, optional
SLA target, and optional visibility settings. The workflow definition is
stored as a JSONB column in the database (matching the DPP pattern) and
parsed into these Pydantic models at runtime.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class StageType(StrEnum):
    """Workflow stage types — maps to application status."""

    VALIDATION = "validation"
    REVIEW = "review"
    INSPECTION = "inspection"
    CONSULTATION = "consultation"
    HEARING = "hearing"
    TRAINING = "training"
    DECISION = "decision"
    CUSTOM = "custom"


class WorkflowStage(BaseModel):
    """A single stage in a workflow definition."""

    key: str = Field(..., description="Unique stage identifier (slug)")
    label: str = Field(..., description="Human-readable stage name")
    order: int = Field(..., description="Position in the workflow (0-based)")
    type: StageType = Field(..., description="Stage type — determines status mapping")
    sla_business_days: int | None = Field(
        None, description="Target working days to complete this stage"
    )
    reminder_days: int | None = Field(
        None, description="Days before SLA deadline to send reminder"
    )
    visible_to_applicant: bool = Field(
        True, description="Whether the applicant can see this stage"
    )
    required_actions: list[str] = Field(
        default_factory=list, description="Actions required before advancing"
    )


class WorkflowDefinition(BaseModel):
    """Complete workflow configuration for an approval type.

    Stored as JSONB in the approvals table (workflow_definition column).
    """

    stages: list[WorkflowStage] = Field(
        ..., description="Ordered list of workflow stages"
    )
    version: int = Field(1, description="Schema version for forward compatibility")

    def get_stage(self, key: str) -> WorkflowStage | None:
        """Find a stage by its key."""
        return next((s for s in self.stages if s.key == key), None)

    def get_stage_by_order(self, order: int) -> WorkflowStage | None:
        """Find a stage by its order position."""
        return next((s for s in self.stages if s.order == order), None)

    def get_first_stage(self) -> WorkflowStage | None:
        """Return the first stage (lowest order)."""
        if not self.stages:
            return None
        return min(self.stages, key=lambda s: s.order)

    def get_next_stage(self, current_key: str) -> WorkflowStage | None:
        """Return the stage after the given current stage key."""
        current = self.get_stage(current_key)
        if current is None:
            return None
        next_order = current.order + 1
        return self.get_stage_by_order(next_order)

    def is_terminal(self, stage_key: str) -> bool:
        """Check if a stage is the last in the workflow."""
        current = self.get_stage(stage_key)
        if current is None:
            return False
        return self.get_next_stage(stage_key) is None
