"""Pydantic models for dynamic forms, conditional rules, and documents.

Ported from Digital-Permit-Platform/src/types/module.ts.

These define the JSON-driven module schema: field types for dynamic forms,
multi-section form wizard structures, conditional display rules, document
requirements, and workflow stage types.

Source: Digital-Permit-Platform/src/types/module.ts (152 lines)
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any

# ─────────────────────────────────────────────────────────────
# Field types
# Source: Digital-Permit-Platform/src/types/module.ts
# ─────────────────────────────────────────────────────────────


class FieldType(StrEnum):
    TEXT = "text"
    TEXTAREA = "textarea"
    DATE = "date"
    CHECKBOX = "checkbox"
    SELECT = "select"
    RADIO = "radio"
    POSTCODE = "postcode"
    ADDRESS = "address"
    NUMBER = "number"
    CURRENCY = "currency"
    UPLOAD = "upload"
    EMAIL = "email"
    PHONE = "phone"
    REPEATABLE = "repeatable"


# ─────────────────────────────────────────────────────────────
# Conditional rules — operators
# Source: Digital-Permit-Platform/src/types/module.ts
# ─────────────────────────────────────────────────────────────


class ConditionalOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    LT = "lt"
    CONTAINS = "contains"
    EXISTS = "exists"


# ─────────────────────────────────────────────────────────────
# Plain data classes (not Pydantic models — these are JSON
# structure definitions stored in the database, not API contracts)
# ─────────────────────────────────────────────────────────────


class ConditionalRule:
    """Conditional display / requirement rule."""

    def __init__(self, field: str, operator: str, value: Any = None) -> None:
        self.field = field
        self.operator = operator
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        return {"field": self.field, "operator": self.operator, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConditionalRule:
        return cls(field=data["field"], operator=data["operator"], value=data.get("value"))


class FieldValidation:
    """Field-level validation rules."""

    def __init__(
        self,
        min_length: int | None = None,
        max_length: int | None = None,
        min: float | None = None,
        max: float | None = None,
        pattern: str | None = None,
        pattern_message: str | None = None,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.min = min
        self.max = max
        self.pattern = pattern
        self.pattern_message = pattern_message

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.min_length is not None:
            d["minLength"] = self.min_length
        if self.max_length is not None:
            d["maxLength"] = self.max_length
        if self.min is not None:
            d["min"] = self.min
        if self.max is not None:
            d["max"] = self.max
        if self.pattern is not None:
            d["pattern"] = self.pattern
        if self.pattern_message is not None:
            d["patternMessage"] = self.pattern_message
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FieldValidation:
        return cls(
            min_length=data.get("minLength"),
            max_length=data.get("maxLength"),
            min=data.get("min"),
            max=data.get("max"),
            pattern=data.get("pattern"),
            pattern_message=data.get("patternMessage"),
        )


class SelectOption:
    """A select/radio option."""

    def __init__(self, value: str, label: str) -> None:
        self.value = value
        self.label = label

    def to_dict(self) -> dict[str, str]:
        return {"value": self.value, "label": self.label}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> SelectOption:
        return cls(value=data["value"], label=data["label"])


class FormField:
    """A single field in a form section."""

    def __init__(
        self,
        key: str,
        label: str,
        type: str,
        hint: str | None = None,
        placeholder: str | None = None,
        required: bool | None = None,
        validation: FieldValidation | None = None,
        options: list[SelectOption] | None = None,
        conditional_on: ConditionalRule | None = None,
        repeatable_schema: list[FormField] | None = None,
        max_repeats: int | None = None,
        default_value: Any = None,
    ) -> None:
        self.key = key
        self.label = label
        self.type = type
        self.hint = hint
        self.placeholder = placeholder
        self.required = required
        self.validation = validation
        self.options = options
        self.conditional_on = conditional_on
        self.repeatable_schema = repeatable_schema
        self.max_repeats = max_repeats
        self.default_value = default_value

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "type": self.type,
        }
        if self.hint is not None:
            d["hint"] = self.hint
        if self.placeholder is not None:
            d["placeholder"] = self.placeholder
        if self.required is not None:
            d["required"] = self.required
        if self.validation is not None:
            d["validation"] = self.validation.to_dict()
        if self.options is not None:
            d["options"] = [o.to_dict() for o in self.options]
        if self.conditional_on is not None:
            d["conditionalOn"] = self.conditional_on.to_dict()
        if self.repeatable_schema is not None:
            d["repeatableSchema"] = [f.to_dict() for f in self.repeatable_schema]
        if self.max_repeats is not None:
            d["maxRepeats"] = self.max_repeats
        if self.default_value is not None:
            d["defaultValue"] = self.default_value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FormField:
        validation = None
        if data.get("validation"):
            validation = FieldValidation.from_dict(data["validation"])

        options = None
        if data.get("options"):
            options = [SelectOption.from_dict(o) for o in data["options"]]

        conditional_on = None
        if data.get("conditionalOn"):
            conditional_on = ConditionalRule.from_dict(data["conditionalOn"])

        repeatable_schema = None
        if data.get("repeatableSchema"):
            repeatable_schema = [FormField.from_dict(f) for f in data["repeatableSchema"]]

        return cls(
            key=data["key"],
            label=data["label"],
            type=data["type"],
            hint=data.get("hint"),
            placeholder=data.get("placeholder"),
            required=data.get("required"),
            validation=validation,
            options=options,
            conditional_on=conditional_on,
            repeatable_schema=repeatable_schema,
            max_repeats=data.get("maxRepeats"),
            default_value=data.get("defaultValue"),
        )


class FormSection:
    """A section in the multi-step form wizard."""

    def __init__(
        self,
        key: str,
        title: str,
        fields: list[FormField],
        description: str | None = None,
        conditional_on: ConditionalRule | None = None,
    ) -> None:
        self.key = key
        self.title = title
        self.fields = fields
        self.description = description
        self.conditional_on = conditional_on

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "key": self.key,
            "title": self.title,
            "fields": [f.to_dict() for f in self.fields],
        }
        if self.description is not None:
            d["description"] = self.description
        if self.conditional_on is not None:
            d["conditionalOn"] = self.conditional_on.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FormSection:
        conditional_on = None
        if data.get("conditionalOn"):
            conditional_on = ConditionalRule.from_dict(data["conditionalOn"])
        return cls(
            key=data["key"],
            title=data["title"],
            fields=[FormField.from_dict(f) for f in data["fields"]],
            description=data.get("description"),
            conditional_on=conditional_on,
        )


# ─────────────────────────────────────────────────────────────
# Document requirements
# Source: Digital-Permit-Platform/src/types/module.ts
# ─────────────────────────────────────────────────────────────


class DocumentRequirement:
    """Document requirement definition."""

    def __init__(
        self,
        key: str,
        label: str,
        required: bool,
        description: str | None = None,
        conditional_on: ConditionalRule | None = None,
        accepted_mime_types: list[str] | None = None,
        max_size_mb: int | None = None,
        verification_status: str = "needs_council_confirmation",
    ) -> None:
        self.key = key
        self.label = label
        self.required = required
        self.description = description
        self.conditional_on = conditional_on
        self.accepted_mime_types = accepted_mime_types
        self.max_size_mb = max_size_mb
        self.verification_status = verification_status

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "required": self.required,
            "verificationStatus": self.verification_status,
        }
        if self.description is not None:
            d["description"] = self.description
        if self.conditional_on is not None:
            d["conditionalOn"] = self.conditional_on.to_dict()
        if self.accepted_mime_types is not None:
            d["acceptedMimeTypes"] = self.accepted_mime_types
        if self.max_size_mb is not None:
            d["maxSizeMb"] = self.max_size_mb
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentRequirement:
        conditional_on = None
        if data.get("conditionalOn"):
            conditional_on = ConditionalRule.from_dict(data["conditionalOn"])
        return cls(
            key=data["key"],
            label=data["label"],
            required=data["required"],
            description=data.get("description"),
            conditional_on=conditional_on,
            accepted_mime_types=data.get("acceptedMimeTypes"),
            max_size_mb=data.get("maxSizeMb"),
            verification_status=data.get(
                "verificationStatus", "needs_council_confirmation"
            ),
        )


# ─────────────────────────────────────────────────────────────
# Workflow stages
# Source: Digital-Permit-Platform/src/types/module.ts
# ─────────────────────────────────────────────────────────────


class WorkflowStageType(StrEnum):
    VALIDATION = "validation"
    REVIEW = "review"
    INSPECTION = "inspection"
    CONSULTATION = "consultation"
    HEARING = "hearing"
    TRAINING = "training"
    DECISION = "decision"
    CUSTOM = "custom"


class WorkflowStage:
    """Workflow stage definition."""

    def __init__(
        self,
        key: str,
        label: str,
        order: int,
        type: str,
        sla_business_days: int | None = None,
        reminder_days: int | None = None,
        auto_transitions: list[dict[str, Any]] | None = None,
        required_actions: list[str] | None = None,
        visible_to_applicant: bool | None = None,
    ) -> None:
        self.key = key
        self.label = label
        self.order = order
        self.type = type
        self.sla_business_days = sla_business_days
        self.reminder_days = reminder_days
        self.auto_transitions = auto_transitions
        self.required_actions = required_actions
        self.visible_to_applicant = visible_to_applicant

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "order": self.order,
            "type": self.type,
        }
        if self.sla_business_days is not None:
            d["slaBusinessDays"] = self.sla_business_days
        if self.reminder_days is not None:
            d["reminderDays"] = self.reminder_days
        if self.auto_transitions is not None:
            d["autoTransitions"] = self.auto_transitions
        if self.required_actions is not None:
            d["requiredActions"] = self.required_actions
        if self.visible_to_applicant is not None:
            d["visibleToApplicant"] = self.visible_to_applicant
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowStage:
        return cls(
            key=data["key"],
            label=data["label"],
            order=data["order"],
            type=data["type"],
            sla_business_days=data.get("slaBusinessDays"),
            reminder_days=data.get("reminderDays"),
            auto_transitions=data.get("autoTransitions"),
            required_actions=data.get("requiredActions"),
            visible_to_applicant=data.get("visibleToApplicant"),
        )
