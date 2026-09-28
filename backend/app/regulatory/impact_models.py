"""Change-impact rehearsal models (Pydantic v2).

Stateless rehearsal only: descriptors of proposed regulatory changes plus
the deterministic impact verdict. No persistence, no monitoring.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.orchestration.whatif_models import ApprovalDiff


class ChangeKind(StrEnum):
    RULE_CHANGE = "RULE_CHANGE"
    DOCUMENT_REQUIREMENT_CHANGE = "DOCUMENT_REQUIREMENT_CHANGE"
    DEPENDENCY_CHANGE = "DEPENDENCY_CHANGE"
    EVIDENCE_STATUS_CHANGE = "EVIDENCE_STATUS_CHANGE"
    SOURCE_METADATA_CHANGE = "SOURCE_METADATA_CHANGE"


class ImpactClassification(StrEnum):
    RESULT_CHANGED = "RESULT_CHANGED"
    SOURCE_RELEVANT = "SOURCE_RELEVANT"
    NO_IMPACT = "NO_IMPACT"


class ChangeDescriptor(BaseModel):
    """One proposed regulatory change to rehearse (never applied)."""

    change_kind: ChangeKind
    source_id: str | None = None
    rule_id: str | None = None
    requirement_key: str | None = None
    evidence_id: str | None = None
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    old_status: str | None = None
    new_status: str | None = None

    @model_validator(mode="after")
    def check_required_fields(self) -> ChangeDescriptor:
        kind = self.change_kind
        if kind == ChangeKind.RULE_CHANGE:
            if not self.rule_id or self.old_value is None or self.new_value is None:
                raise ValueError("RULE_CHANGE needs rule_id, old_value, new_value")
        elif kind == ChangeKind.DOCUMENT_REQUIREMENT_CHANGE:
            if not self.requirement_key or self.old_value is None or self.new_value is None:
                raise ValueError(
                    "DOCUMENT_REQUIREMENT_CHANGE needs requirement_key, old_value, new_value"
                )
        elif kind == ChangeKind.DEPENDENCY_CHANGE:
            if self.old_value is None and self.new_value is None:
                raise ValueError("DEPENDENCY_CHANGE needs old_value and/or new_value")
        elif kind == ChangeKind.EVIDENCE_STATUS_CHANGE:
            if not self.evidence_id or not self.old_status or not self.new_status:
                raise ValueError(
                    "EVIDENCE_STATUS_CHANGE needs evidence_id, old_status, new_status"
                )
        elif kind == ChangeKind.SOURCE_METADATA_CHANGE:
            if not self.source_id or self.old_value is None or self.new_value is None:
                raise ValueError(
                    "SOURCE_METADATA_CHANGE needs source_id, old_value, new_value"
                )
        return self


class ProjectImpact(BaseModel):
    """Deterministic verdict for one change rehearsed against one scope."""

    classification: ImpactClassification
    affected_approvals: list[str] = Field(default_factory=list)
    affected_rule_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    baseline_overall: str = ""
    new_overall: str = ""
    diffs: list[ApprovalDiff] = Field(default_factory=list)
    baseline_results: dict[str, dict[str, str]] = Field(default_factory=dict)
    new_results: dict[str, dict[str, str]] = Field(default_factory=dict)
    reason: str = ""
    evidence_caveats: list[str] = Field(default_factory=list)
    change: ChangeDescriptor


class ImpactRehearseRequest(BaseModel):
    """Staff rehearsal request: explicit application + one change."""

    application_id: str
    change: ChangeDescriptor
    include_unchanged: bool = False
