"""Pydantic models for regulatory obligations and related concepts.

Ported from Compliance Grid TypeScript schemas. These are the source-of-truth
shapes for the CKG domain layer. All models use Pydantic v2 with strict validation.

Source: compliance-grid/src/schemas/obligation.ts, applicability-condition.ts,
        deadline-rule.ts, entity-profile.ts, instrument.ts, source.ts,
        frequency.ts, penalty.ts, instrument-ref.ts, jurisdiction.ts
"""
from __future__ import annotations

import re
from datetime import date
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

# ─────────────────────────────────────────────────────────────
# Jurisdiction — ISO 3166-2 India format
# Source: compliance-grid/src/schemas/jurisdiction.ts
# ─────────────────────────────────────────────────────────────

JURISDICTION_RE = re.compile(r"^IN(-[A-Z]{2})?$")


class Jurisdiction(str):
    """Indian jurisdiction: 'IN' (national) or 'IN-XX' (state, ISO 3166-2)."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise TypeError("jurisdiction must be a string")
        if not JURISDICTION_RE.match(v):
            raise ValueError(
                f"jurisdiction must be 'IN' (national) or 'IN-XX' (state), got '{v}'"
            )
        return v


# ─────────────────────────────────────────────────────────────
# Enums
# Source: compliance-grid/src/schemas/*.ts
# ─────────────────────────────────────────────────────────────


class ObligationType(StrEnum):
    FILING = "filing"
    REGISTRATION = "registration"
    RECORD_KEEPING = "record-keeping"
    DISPLAY = "display"
    NOTIFICATION = "notification"
    PAYMENT = "payment"
    INSPECTION_READINESS = "inspection-readiness"


class ApplicabilityOp(StrEnum):
    EQ = "eq"
    IN = "in"
    GTE = "gte"
    LTE = "lte"
    GT = "gt"
    LT = "lt"


class Frequency(StrEnum):
    ONE_TIME = "one-time"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half-yearly"
    ANNUAL = "annual"
    EVENT_DRIVEN = "event-driven"


class InstrumentType(StrEnum):
    ACT = "Act"
    RULE = "Rule"
    NOTIFICATION = "Notification"


class EntityType(StrEnum):
    PROPRIETORSHIP = "proprietorship"
    PARTNERSHIP = "partnership"
    LLP = "llp"
    PVT_LTD = "pvt-ltd"
    PUBLIC_LTD = "public-ltd"
    OPC = "opc"
    HUF = "huf"
    TRUST = "trust"
    SOCIETY = "society"


class TrustTier(StrEnum):
    GAZETTE = "gazette"
    GOVT_PORTAL = "govt-portal"
    SECONDARY = "secondary"
    UNVERIFIED = "unverified"


# ─────────────────────────────────────────────────────────────
# Value objects
# Source: compliance-grid/src/schemas/*.ts
# ─────────────────────────────────────────────────────────────


class MinMax(BaseModel):
    """A numeric range with min/max. max must be >= min."""

    min: float = Field(ge=0)
    max: float = Field(ge=0)

    @model_validator(mode="after")
    def check_max_gte_min(self) -> MinMax:
        if self.max < self.min:
            raise ValueError(f"max ({self.max}) must be >= min ({self.min})")
        return self


class Penalty(BaseModel):
    """Penalty for non-compliance. From compliance-grid/src/schemas/penalty.ts."""

    has_imprisonment: bool
    imprisonment_months: MinMax | None = None
    fine_inr: MinMax | None = None


class SourceRef(BaseModel):
    """Pointer from an obligation to a location within a registered Source.

    From compliance-grid/src/schemas/obligation.ts.
    Anti-hallucination invariant: source_refs must be non-empty at the
    Obligation level.
    """

    source_id: str = Field(min_length=1)
    citation_span: str = Field(min_length=1)


class FetchRecipe(BaseModel):
    """Extensible description of how to crawl/retrieve a source.

    From compliance-grid/src/schemas/source.ts.
    """

    kind: str = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Applicability conditions
# Source: compliance-grid/src/schemas/applicability-condition.ts
# ─────────────────────────────────────────────────────────────


class ApplicabilityCondition(BaseModel):
    """Structured predicate for applicability evaluation.

    Multiple conditions on an obligation are AND-combined.
    """

    field: str = Field(min_length=1)
    op: ApplicabilityOp
    value: Any


# ─────────────────────────────────────────────────────────────
# Deadline rules — discriminated union on 'kind'
# Source: compliance-grid/src/schemas/deadline-rule.ts
# ─────────────────────────────────────────────────────────────


class FixedDateRule(BaseModel):
    kind: Literal["fixed-date"]
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)


class PeriodOffsetRule(BaseModel):
    kind: Literal["period-offset"]
    days: int = Field(ge=0)


class EventOffsetRule(BaseModel):
    kind: Literal["event-offset"]
    days: int = Field(ge=0)
    event: str = Field(min_length=1)


DeadlineRule = Annotated[
    FixedDateRule | PeriodOffsetRule | EventOffsetRule,
    Field(discriminator="kind"),
]


# ─────────────────────────────────────────────────────────────
# Instrument
# Source: compliance-grid/src/schemas/instrument.ts
# ─────────────────────────────────────────────────────────────


class InstrumentRef(BaseModel):
    """Pointer from an obligation to an instrument + optional section.

    From compliance-grid/src/schemas/instrument-ref.ts.
    """

    instrument_id: str = Field(min_length=1)
    section: str | None = None


class Instrument(BaseModel):
    """Legal source document (Act, Rule, Notification).

    From compliance-grid/src/schemas/instrument.ts.
    """

    id: str = Field(min_length=1)
    type: InstrumentType
    title: str = Field(min_length=1)
    jurisdiction: str  # validated as IN or IN-XX at the DB/API layer
    citation: str = Field(min_length=1)


# ─────────────────────────────────────────────────────────────
# Source — external web/document source
# Source: compliance-grid/src/schemas/source.ts
# ─────────────────────────────────────────────────────────────


class Source(BaseModel):
    id: str = Field(min_length=1)
    jurisdiction: str
    domain: str = Field(min_length=1)
    url: str
    fetch_recipe: FetchRecipe
    trust_tier: TrustTier
    last_seen: str  # ISO datetime
    content_hash: str = Field(min_length=1)


# ─────────────────────────────────────────────────────────────
# Entity Profile
# Source: compliance-grid/src/schemas/entity-profile.ts
# ─────────────────────────────────────────────────────────────


class EntityProfile(BaseModel):
    """Per-organisation entity facts used for applicability matching.

    Fields: sector, entity_type, jurisdictions, headcount,
    annual_turnover_inr, incorporation_date, registered_state.
    """

    entity_id: str = Field(min_length=1)
    org_id: str = Field(min_length=1)
    entity_type: EntityType
    sector: str = Field(min_length=1)
    jurisdictions: list[str] = Field(min_length=1)
    headcount: int = Field(ge=0)
    annual_turnover_inr: float = Field(ge=0)
    incorporation_date: date | None = None
    registered_state: str | None = None


# ─────────────────────────────────────────────────────────────
# Obligation — the core regulatory rule node
# Source: compliance-grid/src/schemas/obligation.ts
# ─────────────────────────────────────────────────────────────


class Obligation(BaseModel):
    """A single regulatory obligation extracted from an instrument.

    Anti-hallucination invariant: source_refs must be non-empty.
    """

    canonical_id: str = Field(min_length=1)
    instrument_ref: InstrumentRef
    type: ObligationType
    summary: str = Field(min_length=1)
    applicability_conditions: list[ApplicabilityCondition]
    frequency: Frequency
    deadline_rule: DeadlineRule
    proof_types: list[str]
    penalty: Penalty
    source_refs: list[SourceRef] = Field(min_length=1)
    version: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class ObligationCandidate(BaseModel):
    """What the extraction agent produces before deterministic gates assign
    canonical_id and version.

    Same as Obligation minus canonical_id and version.
    """

    instrument_ref: InstrumentRef
    type: ObligationType
    summary: str = Field(min_length=1)
    applicability_conditions: list[ApplicabilityCondition]
    frequency: Frequency
    deadline_rule: DeadlineRule
    proof_types: list[str]
    penalty: Penalty
    source_refs: list[SourceRef] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


# ─────────────────────────────────────────────────────────────
# Approval rules — our domain extension
# (not from Compliance Grid, but shaped to link obligations
# to the application workflow)
# ─────────────────────────────────────────────────────────────


class ApprovalResult(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"
