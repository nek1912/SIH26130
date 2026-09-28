"""Data models for Gujarat government support/incentive schemes.

Models are designed to reuse the existing recursive ConditionNode system
for eligibility evaluation. Every user-visible claim must be traceable
to an authoritative source.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.rules.models import ConditionNode, SourceRef


class SchemeCategory(StrEnum):
    """Categories of government support schemes."""
    CAPITAL_SUBSIDY = "capital_subsidy"
    INTEREST_SUBSIDY = "interest_subsidy"
    TAX_CONCESSION = "tax_concession"
    INFRASTRUCTURE = "infrastructure"
    MSME_SUPPORT = "msme_support"
    QUALITY_CERTIFICATION = "quality_certification"
    ENERGY = "energy"
    EMPLOYMENT = "employment"
    GENERAL = "general"


class RelevanceState(StrEnum):
    """Deterministic relevance assessment result."""
    POTENTIALLY_RELEVANT = "potentially_relevant"
    NOT_RELEVANT = "not_relevant"
    CONDITIONAL = "conditional"
    INSUFFICIENT_DATA = "insufficient_data"


class RequiredInfo(BaseModel):
    """A piece of information needed for a complete eligibility assessment.

    This does NOT invent facts — it lists what the authoritative source
    says is needed to determine eligibility.
    """
    field_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_ref: SourceRef | None = None


class SchemeBenefit(BaseModel):
    """A specific benefit described by the authoritative source.

    Only included if the source provides explicit amounts, percentages,
    or conditions. No invented figures.
    """
    description: str = Field(min_length=1)
    source_ref: SourceRef | None = None


class SupportScheme(BaseModel):
    """A verified government support/incentive scheme.

    All fields come from authoritative sources. If the source does not
    provide specific eligibility thresholds, those fields are absent
    (not guessed).
    """
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    authority: str = Field(min_length=1)
    category: SchemeCategory
    description: str = Field(min_length=1)
    eligibility_conditions: list[ConditionNode] = Field(default_factory=list)
    required_info: list[RequiredInfo] = Field(default_factory=list)
    benefits: list[SchemeBenefit] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(min_length=1)
    version: str = Field(min_length=1)
    active: bool = True


class SchemeRelevance(BaseModel):
    """Result of evaluating a single scheme against project facts."""
    scheme_id: str
    scheme_name: str
    relevance: RelevanceState
    reason: str
    triggered_conditions: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)


class ProjectIncentiveAssessment(BaseModel):
    """Complete incentive assessment for a project across all schemes."""
    project_id: str
    assessments: list[SchemeRelevance]
    relevant_count: int
    conditional_count: int
    insufficient_count: int
    not_relevant_count: int
    explanation: str


class IncentiveAssessmentRequest(BaseModel):
    """Request to assess incentive relevance for a project."""
    project_facts: dict[str, Any]
    scheme_ids: list[str] | None = None
