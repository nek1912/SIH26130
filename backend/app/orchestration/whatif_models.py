"""What-If response models (Pydantic v2)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.orchestration.models import (
    ApplicationOrchestration,
    BlockerDetail,
    NextAction,
)


class WhatIfRequest(BaseModel):
    """Temporary fact overrides. None = fact temporarily unknown/removed."""

    fact_overrides: dict[str, Any] = Field(default_factory=dict)
    include_unchanged: bool = False


class ApprovalDiff(BaseModel):
    approval_id: str
    baseline_applicability: str
    whatif_applicability: str
    baseline_status: str
    whatif_status: str
    baseline_dependency: str
    whatif_dependency: str
    added_blockers: list[BlockerDetail] = Field(default_factory=list)
    removed_blockers: list[BlockerDetail] = Field(default_factory=list)
    baseline_explanation: str
    whatif_explanation: str


class WhatIfComparison(BaseModel):
    changed_approvals: list[ApprovalDiff] = Field(default_factory=list)
    unchanged_approvals: list[str] = Field(default_factory=list)
    added_blockers: list[BlockerDetail] = Field(default_factory=list)
    removed_blockers: list[BlockerDetail] = Field(default_factory=list)
    overall_baseline: str
    overall_whatif: str
    next_action_baseline: NextAction | None = None
    next_action_whatif: NextAction | None = None
    no_change: bool = True


class WhatIfResponse(BaseModel):
    application_id: str
    baseline: ApplicationOrchestration
    what_if: ApplicationOrchestration
    diff: WhatIfComparison
    applied_overrides: dict[str, Any] = Field(default_factory=dict)
    note: str = (
        "Stateless recalculation: persisted project facts, uploaded documents, "
        "consistency results, SLA inputs, and evidence records are unchanged. "
        "Uploaded documents, consistency outcomes, and SLA state are held "
        "constant and are not re-derived from temporary facts."
    )
