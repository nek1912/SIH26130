"""Seed data for verified Gujarat government support/incentive schemes.

All schemes are sourced from the Gujarat Industrial Policy 2020 (GIP 2020),
an official Government of Gujarat policy announced on 07 August 2020.
Source: https://static.investindia.gov.in/s3fs-public/2020-08/Gujarat%20Industrial%20Policy%202020.pdf

The scheme details (percentages, thresholds, conditions) are taken directly
from the official policy document and government resolutions. No amounts
or eligibility criteria are invented.
"""
from __future__ import annotations

from app.incentives.models import (
    RequiredInfo,
    SchemeBenefit,
    SchemeCategory,
    SupportScheme,
)
from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityOp,
    NotNode,
    OrNode,
    SourceRef,
)


def _leaf(field: str, op: str, value: object) -> ApplicabilityCondition:
    return ApplicabilityCondition(field=field, op=ApplicabilityOp(op), value=value)


def _and(*nodes: object) -> AndNode:
    return AndNode(conditions=list(nodes))


def _or(*nodes: object) -> OrNode:
    return OrNode(conditions=list(nodes))


def _not(node: object) -> NotNode:
    return NotNode(condition=node)


def _ref(source_id: str, citation: str) -> list[SourceRef]:
    return [SourceRef(source_id=source_id, citation_span=citation)]


def load_incentive_schemes() -> list[SupportScheme]:
    """Return all verified Gujarat incentive schemes from GIP 2020.

    Source: Gujarat Industrial Policy 2020 (Government of Gujarat)
    Checked: 2026-09-16
    """
    return [
        # ── MSME Capital Subsidy ──
        SupportScheme(
            id="INC-MSME-CAP",
            name="MSME Capital Subsidy",
            authority="Government of Gujarat / Industries Commissionerate",
            category=SchemeCategory.CAPITAL_SUBSIDY,
            description=(
                "Capital subsidy for MSMEs on eligible term loan amount, "
                "based on taluka category. As per GIP 2020, MSMEs investing "
                "up to INR 50 crore in Plant & Machinery are eligible."
            ),
            eligibility_conditions=[
                _leaf("entity_type", "in", ["pvt-ltd", "partnership", "llp", "proprietorship"]),
            ],
            required_info=[
                RequiredInfo(
                    field_name="term_loan_amount",
                    description="Eligible term loan amount from a bank or financial institution",
                ),
                RequiredInfo(
                    field_name="fci_amount",
                    description="Fixed Capital Investment (FCI) excluding land",
                ),
                RequiredInfo(
                    field_name="taluka_category",
                    description="Taluka category (1=backward, 2=developing, 3=mature)",
                ),
            ],
            benefits=[
                SchemeBenefit(
                    description=(
                        "Category 1: 25% of eligible term loan, max INR 35 lakhs"
                        " (additional INR 10 lakhs if FCI > 10 Cr)"
                    ),
                ),
                SchemeBenefit(
                    description=(
                        "Category 2: 20% of eligible term loan, max INR 30 lakhs"
                        " (additional INR 7.5 lakhs if FCI > 10 Cr)"
                    ),
                ),
                SchemeBenefit(
                    description=(
                        "Category 3: 10% of eligible term loan, max INR 10 lakhs"
                        " (additional INR 5 lakhs if FCI > 10 Cr)"
                    ),
                ),
            ],
            source_refs=_ref(
                "S33",
                "Gujarat Industrial Policy 2020 — MSME Capital and Interest Subsidy scheme",
            ),
            version="1",
        ),
        # ── MSME Interest Subsidy ──
        SupportScheme(
            id="INC-MSME-INT",
            name="MSME Interest Subsidy",
            authority="Government of Gujarat / Industries Commissionerate",
            category=SchemeCategory.INTEREST_SUBSIDY,
            description=(
                "Interest subsidy on term loans for MSME manufacturing units. "
                "Additional 1% for SC/ST/women/startup/young entrepreneurs. "
                "Maximum interest subsidy capped at 9%; unit must bear minimum 2%."
            ),
            eligibility_conditions=[
                _leaf("entity_type", "in", ["pvt-ltd", "partnership", "llp", "proprietorship"]),
            ],
            required_info=[
                RequiredInfo(
                    field_name="term_loan_amount",
                    description="Term loan amount disbursed by a bank or financial institution",
                ),
                RequiredInfo(
                    field_name="taluka_category",
                    description="Taluka category (1=backward, 2=developing, 3=mature)",
                ),
            ],
            benefits=[
                SchemeBenefit(
                    description="Category 1: 7% of term loan, max INR 35 lakhs/year for 7 years",
                ),
                SchemeBenefit(
                    description="Category 2: 6% of term loan, max INR 30 lakhs/year for 6 years",
                ),
                SchemeBenefit(
                    description="Category 3: 5% of term loan, max INR 25 lakhs/year for 5 years",
                ),
            ],
            source_refs=_ref(
                "S33",
                "Gujarat Industrial Policy 2020 — MSME Interest Subsidy scheme",
            ),
            version="1",
        ),
        # ── Large Industry Capital Subsidy ──
        SupportScheme(
            id="INC-LARGE-CAP",
            name="Capital Subsidy to Large Industries and Thrust Sector",
            authority="Government of Gujarat / Industries Commissionerate",
            category=SchemeCategory.CAPITAL_SUBSIDY,
            description=(
                "Capital subsidy for large industrial units based on eligible "
                "Fixed Capital Investment (FCI) excluding land. Gujarat is the "
                "first state to de-link incentives from SGST. No upper ceiling "
                "on incentive amount."
            ),
            eligibility_conditions=[
                _leaf("entity_type", "in", ["pvt-ltd", "public-ltd", "partnership", "llp"]),
            ],
            required_info=[
                RequiredInfo(
                    field_name="fci_amount",
                    description="Fixed Capital Investment (FCI) excluding land",
                ),
                RequiredInfo(
                    field_name="taluka_category",
                    description="Taluka category (1=backward, 2=developing, 3=mature)",
                ),
                RequiredInfo(
                    field_name="sector_type",
                    description="General sector or Thrust sector classification",
                ),
            ],
            benefits=[
                SchemeBenefit(
                    description=(
                        "Category 1: 12% of FCI (thrust) / 10% of FCI (general),"
                        " 10 annual instalments, max INR 40 Cr/year"
                    ),
                ),
                SchemeBenefit(
                    description=(
                        "Category 2: 10% of FCI (thrust) / 8% of FCI (general)"
                    ),
                ),
                SchemeBenefit(
                    description=(
                        "Category 3: 6% of FCI (thrust) / 4% of FCI (general)"
                    ),
                ),
            ],
            source_refs=_ref(
                "S33",
                "Gujarat Industrial Policy 2020 — Capital Subsidy to Large"
                " Industries and Thrust Sector",
            ),
            version="1",
        ),
        # ── Electricity Duty Exemption ──
        SupportScheme(
            id="INC-ELEC-DUTY",
            name="Electricity Duty Exemption",
            authority="Government of Gujarat",
            category=SchemeCategory.TAX_CONCESSION,
            description=(
                "Electricity duty exemption for 5 years for all new industrial "
                "units set up during the operative period of GIP 2020."
            ),
            eligibility_conditions=[
                _leaf("new_project", "eq", True),
            ],
            required_info=[],
            benefits=[
                SchemeBenefit(
                    description=(
                        "Electricity duty exemption for 5 years from date"
                        " of commercial production"
                    ),
                ),
            ],
            source_refs=_ref(
                "S33",
                "Gujarat Industrial Policy 2020 — Electricity Duty"
                " Exemption for all units",
            ),
            version="1",
        ),
        # ── Power Connection Charges Subsidy (MSME) ──
        SupportScheme(
            id="INC-POWER-CHG",
            name="Power Connection Charges Subsidy for MSMEs",
            authority="Government of Gujarat / Industries Commissionerate",
            category=SchemeCategory.INFRASTRUCTURE,
            description=(
                "35% reimbursement of power connection charges paid to "
                "distribution licensees for LT/HT service line, up to INR 5 lakh."
            ),
            eligibility_conditions=[
                _leaf("entity_type", "in", ["pvt-ltd", "partnership", "llp", "proprietorship"]),
            ],
            required_info=[
                RequiredInfo(
                    field_name="power_connection_charges",
                    description="Charges paid to DISCOM for LT/HT service line connection",
                ),
            ],
            benefits=[
                SchemeBenefit(
                    description="35% of connection charges paid to DISCOM, max INR 5 lakh",
                ),
            ],
            source_refs=_ref(
                "S33",
                "Gujarat Industrial Policy 2020 — Power Connection Charges for MSMEs",
            ),
            version="1",
        ),
        # ── Quality Certification Assistance ──
        SupportScheme(
            id="INC-QUALITY",
            name="Quality Certification Assistance",
            authority="Government of Gujarat / Industries Commissionerate",
            category=SchemeCategory.QUALITY_CERTIFICATION,
            description=(
                "Support for quality certifications under ZED scheme, "
                "ISI/WHO-GMP/Hallmark and other national/international "
                "certifications from Quality Council of India."
            ),
            eligibility_conditions=[],
            required_info=[],
            benefits=[
                SchemeBenefit(
                    description="50% of fee payable to international certification authority",
                ),
                SchemeBenefit(
                    description="50% cost of equipment and machinery for certification",
                ),
            ],
            source_refs=_ref(
                "S33",
                "Gujarat Industrial Policy 2020 — Quality Certification scheme",
            ),
            version="1",
        ),
    ]


def scheme_to_dict(scheme: SupportScheme) -> dict:
    """Convert a SupportScheme to a serialisable dict for API responses."""
    return {
        "id": scheme.id,
        "name": scheme.name,
        "authority": scheme.authority,
        "category": scheme.category.value,
        "description": scheme.description,
        "eligibility_conditions": [
            _condition_to_dict(c) for c in scheme.eligibility_conditions
        ],
        "required_info": [ri.model_dump() for ri in scheme.required_info],
        "benefits": [b.model_dump() for b in scheme.benefits],
        "source_refs": [sr.model_dump() for sr in scheme.source_refs],
        "version": scheme.version,
        "active": scheme.active,
    }


def _condition_to_dict(node: object) -> dict:
    """Recursively convert a ConditionNode to a plain dict."""
    if isinstance(node, ApplicabilityCondition):
        return {
            "kind": "condition",
            "field": node.field,
            "op": node.op.value,
            "value": node.value,
        }
    if isinstance(node, AndNode):
        return {
            "kind": "and",
            "conditions": [_condition_to_dict(c) for c in node.conditions],
        }
    if isinstance(node, OrNode):
        return {
            "kind": "or",
            "conditions": [_condition_to_dict(c) for c in node.conditions],
        }
    if isinstance(node, NotNode):
        return {
            "kind": "not",
            "condition": _condition_to_dict(node.condition),
        }
    return {}
