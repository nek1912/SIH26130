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
# Applicability conditions — recursive condition tree
# Supports AND, OR, NOT with arbitrary nesting.
# Source: compliance-grid/src/schemas/applicability-condition.ts
# ─────────────────────────────────────────────────────────────


class ApplicabilityCondition(BaseModel):
    """Leaf predicate for applicability evaluation.

    Evaluates a single field against a value using an operator.
    """

    kind: Literal["condition"] = "condition"
    field: str = Field(min_length=1)
    op: ApplicabilityOp
    value: Any


class AndNode(BaseModel):
    """Logical AND of multiple condition nodes.

    Result is TRUE only if ALL children are TRUE.
    Result is FALSE if any child is FALSE.
    Result is INSUFFICIENT_DATA if no child is FALSE but at least one is INSUFFICIENT_DATA.
    """

    kind: Literal["and"] = "and"
    conditions: list[ConditionNode] = Field(min_length=1)


class OrNode(BaseModel):
    """Logical OR of multiple condition nodes.

    Result is TRUE if any child is TRUE.
    Result is FALSE only if ALL children are FALSE.
    Result is INSUFFICIENT_DATA if no child is TRUE but at least one is INSUFFICIENT_DATA.
    """

    kind: Literal["or"] = "or"
    conditions: list[ConditionNode] = Field(min_length=1)


class NotNode(BaseModel):
    """Logical NOT of a single condition node.

    Result is TRUE if child is FALSE.
    Result is FALSE if child is TRUE.
    Result is INSUFFICIENT_DATA if child is INSUFFICIENT_DATA.
    """

    kind: Literal["not"] = "not"
    condition: ConditionNode


class LiteralNode(BaseModel):
    """Explicit UNKNOWN / NOT_APPLICABLE condition literal.

    - ``"unknown"`` evaluates to INSUFFICIENT_DATA (None): the condition
      cannot currently be established. It never becomes FALSE.
    - ``"not_applicable"`` evaluates to a distinct NOT_APPLICABLE
      sentinel: the rule/branch explicitly does not apply. It is not
      Python False and propagates explicitly through AND/OR/NOT.

    These literals are different from the CONDITIONAL applicability
    result (which describes partial evaluation across trees).
    """

    kind: Literal["literal"] = "literal"
    value: Literal["unknown", "not_applicable"]


# Sentinel produced when a LiteralNode("not_applicable") is evaluated.
# Distinct from True/False/None so identity checks (``is True``,
# ``is False``, ``is None``) across existing consumers keep working and
# fail closed (unknown-like) wherever the sentinel is unhandled.
NotApplicable = Literal["not_applicable"]
NOT_APPLICABLE: NotApplicable = "not_applicable"


# Forward reference resolution — Pydantic v2 handles this via
# the model_rebuild() call at the end of this file.
ConditionNode = Annotated[
    ApplicabilityCondition | AndNode | OrNode | NotNode | LiteralNode,
    Field(discriminator="kind"),
]


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
    applicability_conditions: list[ConditionNode]
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
    applicability_conditions: list[ConditionNode]
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
    APPLIES = "applies"
    DOES_NOT_APPLY = "does_not_apply"
    CONDITIONAL = "conditional"
    INSUFFICIENT_DATA = "insufficient_data"


class RuleRole(StrEnum):
    """Semantic role of an approval rule (P0 exception-role design).

    - TRIGGER: ordinary approval-trigger rule. TRUE means the duty or
      approval attaches. This is the compatibility default: every rule
      built without an explicit role behaves exactly as before.
    - EXEMPTION: duty-defeat rule. TRUE means the duty is negated or
      relieved for the matched scope (with an explicit reason); FALSE
      carries no information (it must never read as "duty attaches");
      UNKNOWN blocks an otherwise applicable trigger from reporting
      APPLIES. An EXEMPTION output can never produce APPLIES, alone or
      combined — only the approval composition layer may turn
      TRIGGER TRUE + EXEMPTION TRUE into a reasoned DOES_NOT_APPLY.
    - CLASSIFICATION: informational category input (e.g. small-unit or
      branch determination feeding a category composer). Never directly
      approval-decisive; consumed only through explicitly named
      composition. Unconsumed classification output is informational.

    Roles are explicit and auditable: they are assigned per rule in the
    seed layer, never inferred from names, approvals, predicates, or
    descriptions. GUARD / ROUTING / LIFECYCLE / WORKFLOW are
    deliberately NOT roles — those semantics stay outside the
    applicability engine.
    """

    TRIGGER = "trigger"
    EXEMPTION = "exemption"
    CLASSIFICATION = "classification"


# ─────────────────────────────────────────────────────────────
# Approval Rule — links an approval to applicability conditions
# and source references. Maps to the approval_rules table.
# ─────────────────────────────────────────────────────────────


class ApprovalRule(BaseModel):
    """A rule that determines whether an approval applies to a project.

    Each rule links an approval to a set of applicability conditions.
    Multiple rules can exist for the same approval (any matching rule
    makes the approval applicable).

    The ``role`` carries the P0 exception-role semantics: TRIGGER rules
    behave exactly as before (compatibility default); EXEMPTION and
    CLASSIFICATION rules are interpreted only through explicit approval
    composition and can never produce APPLIES on their own.
    """

    id: str = Field(min_length=1)
    approval_id: str = Field(min_length=1)
    obligation_id: str | None = None
    applicability_conditions: list[ConditionNode]
    source_refs: list[SourceRef] = Field(default_factory=list)
    version: str = Field(min_length=1)
    active: bool = True
    role: RuleRole = RuleRole.TRIGGER
    # Effective window (both optional, open-ended when absent).
    # Evaluated only when an evaluation_date is supplied; None
    # evaluation_date preserves existing behavior (always evaluated).
    effective_from: date | None = None
    effective_to: date | None = None


class ApprovalComposition(BaseModel):
    """Explicit per-approval composition of role-typed rule outputs.

    Names the trigger, exemption, and classification rule IDs whose
    evaluations combine into one approval verdict via the §8 truth
    table (see ``compose_approval_evaluations``). Lists must be
    pairwise disjoint; every named ID must be a built rule of the same
    pack. Approvals without an entry use the legacy priority
    aggregation unchanged.
    """

    approval_id: str = Field(min_length=1)
    triggers: list[str] = Field(default_factory=list)
    exemptions: list[str] = Field(default_factory=list)
    classifications: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_disjoint(self) -> ApprovalComposition:
        seen: set[str] = set()
        for group in (
            self.triggers,
            self.exemptions,
            self.classifications,
        ):
            for rule_id in group:
                if rule_id in seen:
                    raise ValueError(
                        f"rule {rule_id!r} appears in more than one "
                        f"composition group for {self.approval_id!r}"
                    )
                seen.add(rule_id)
        return self


# ─────────────────────────────────────────────────────────────
# Applicability Evaluation — detailed result for a single rule
# evaluation against project facts
# ─────────────────────────────────────────────────────────────


class ApplicabilityEvaluation(BaseModel):
    """Detailed result of evaluating an approval rule against project facts.

    Every evaluation includes:
    - rule_id: the rule that was evaluated
    - approval_id: the approval this rule relates to
    - result: APPLIES, DOES_NOT_APPLY, CONDITIONAL, or INSUFFICIENT_DATA
    - reason: human-readable explanation of why this result was produced
    - required_inputs: all fact fields required by this rule's conditions
    - missing_inputs: fact fields that were required but not provided
    - authority: the authority responsible for this approval (from approval)
    - source_references: regulatory source citations for this rule
    """

    rule_id: str
    approval_id: str
    result: str  # "applies" | "does_not_apply" | "conditional" | "insufficient_data"
    reason: str
    required_inputs: list[str]
    missing_inputs: list[str]
    authority: str
    source_references: list[SourceRef]


class ApprovalEvaluationRequest(BaseModel):
    """Request to evaluate approval applicability for a project."""

    project_facts: dict[str, Any]
    approval_ids: list[str] | None = None  # Optional filter: evaluate only specific approvals


class ApprovalEvaluationResponse(BaseModel):
    """Response containing evaluation results for all evaluated rules."""

    evaluations: list[ApplicabilityEvaluation]
    summary: dict[str, int]  # Count of each result type


# Resolve forward references for the recursive ConditionNode type.
AndNode.model_rebuild()
OrNode.model_rebuild()
NotNode.model_rebuild()
