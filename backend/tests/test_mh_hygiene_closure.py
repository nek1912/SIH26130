"""Supplementary closure tests for the hygiene quartet (R-059/R-071/R-072/R-076).

Companion to test_mh_residual_hygiene.py (parallel session), which covers
register identity, non-approval targets, source sanity, consumer absence,
and fact linkage. This file adds ONLY incremental coverage:

- R-059 legal-basis pin (PSI criteria not located) + structural
  NOT_COMPUTED posture of the incentives engine (no monetary fields).
- R-071 "Do not return FALSE" polarity pin + TRUE-from date pin.
- R-076 deadline-layer note (fixed-date mechanics exist; CMP-006 has no
  executable consumer and "EC granted" is unmodeled).
- Terminal documentary dispositions (no code status changes).

Dispositions (documentary; status sets intentionally unchanged):
R-059 DNI-as-ApprovalRule, R-071 documented-hygiene, R-072 DNI-as-
ApprovalRule (twin of CMP-014 DNI), R-076 documented-hygiene (facet of
CMP-006). See docs/audits/audit_mh_remaining_hygiene_closure.md.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.incentives.models import SchemeRelevance
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
)


def _get_csv_dir() -> Path:
    backend_dir = Path(__file__).resolve().parent.parent
    root_dir = backend_dir.parent
    for path in root_dir.iterdir():
        if "UdyamDwaar MH Chemical Pack" in path.name and path.is_dir():
            csv_path = path / "csv"
            if csv_path.exists():
                return csv_path
    pytest.skip("Authoritative CSV directory not found")


def _register_row(filename: str, key: str, value: str) -> dict[str, str]:
    csv_dir = _get_csv_dir()
    with open(csv_dir / filename, encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return next(r for r in reader if r.get(key) == value)


class TestR059NoCriteriaToCompute:
    """The hard stop rests on absent criteria, not on a computed zero."""

    def test_legal_basis_is_not_located(self):
        row = _register_row("rules.csv", "rule_id", "R-059")
        assert row["legal_basis"] == "PSI under IISP 2025 not located"

    def test_incentive_relevance_carries_no_monetary_value(self):
        """SchemeRelevance has no amount/rate/tenure fields: the engine
        cannot present a computed incentive value by construction."""
        fields = set(SchemeRelevance.model_fields.keys())
        assert fields == {
            "scheme_id", "scheme_name", "relevance", "reason",
            "triggered_conditions", "missing_info", "source_refs",
        }

    def test_r059_not_an_approval_candidate(self):
        assert "R-059" not in MH_INCLUDED_RULE_IDS
        assert "R-059" not in MH_DEFERRED_RULES


class TestR071PolarityNote:
    """The register forbids the only dangerous reading explicitly."""

    def test_do_not_return_false_pinned(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-071")
        assert row["notes"] == "Do not return FALSE"

    def test_true_from_commencement_date(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-071")
        assert row["effective_date"] == "2014-06-01"
        assert row["effective_date_status"] == "EXACT_DATE"

    def test_r071_not_an_approval_candidate(self):
        assert "R-071" not in MH_INCLUDED_RULE_IDS
        assert "R-071" not in MH_DEFERRED_RULES


class TestR072TwinOfDni:
    """R-072 mirrors CMP-014, which is already DO_NOT_IMPLEMENT_YET."""

    def test_cmp014_dni_covers_assignment_duty(self):
        row = _register_row("compliance.csv", "compliance_id", "CMP-014")
        assert row["implement_status"] == "DO_NOT_IMPLEMENT_YET"
        assert "assigned" in row["trigger_event"]

    def test_r072_not_an_approval_candidate(self):
        assert "R-072" not in MH_INCLUDED_RULE_IDS
        assert "R-072" not in MH_DEFERRED_RULES


class TestR076DeadlineLayerNote:
    """The June/December pair belongs to CMP-006.frequency_deadline, which
    has no executable consumer: compliance.csv is documentary in this
    system (no compliance engine consumes it)."""

    def test_no_compliance_consumer_in_pack(self):
        from app.seed.pack import load_regulatory_pack

        pack = load_regulatory_pack("IN-MH")
        assert pack.consistency_rules is not None  # pack loads; no compliance dimension
        assert "CMP-006" not in {
            r.approval_id for r in pack.approval_rules
        }

    def test_ec_granted_state_unmodeled(self):
        from app.rules.facts import MH_FACTS

        assert "EC granted" not in MH_FACTS
        assert "F-EC-01" not in MH_FACTS

    def test_r076_not_an_approval_candidate(self):
        assert "R-076" not in MH_INCLUDED_RULE_IDS
        assert "R-076" not in MH_DEFERRED_RULES
