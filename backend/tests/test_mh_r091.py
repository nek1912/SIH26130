"""R-091 MAH-derivation closure pins (T7, outcome B).

R-091 stays deferred as an ApprovalRule and partially implemented via
``derive_mah_status()`` (M3/M4 exact-name col-3 join + M7 quantity + M9
fail-closed outcome). These tests pin the evidence-gated boundary so no
future change can silently widen it:

- R-091 cannot be encoded (deferred gate rejects it first).
- No active rule targets APR-012 (the R-091 lifecycle home).
- F-PRC-03 is derived-only and its sole active consumer is the
  informational R-002 CLASSIFICATION — no decisive rule reads it, so a
  missing input can never flip an approval to APPLIES.
- Downstream MSIHC duties (R-019/R-020/R-021) stay deferred.
- F-HAZ-04 (installation/distance matrix) exists in the registry but is
  not consumed by the derivation (M8/R-061 spatial gap, documented).
- Split-quantity behavior is pinned as the documented M8 limitation:
  per-entry comparison, no cross-entry summation (changing this needs
  installation/distance evidence + R-061 spatial support).

Evidence: rules.csv R-091 (DERIVE, VERIFIED_CONDITIONAL), M1..M9
(msihc_mapping_steps.csv: M2 unselected, M5 S1-TOX blocked, M8
conditional), CON-021 cell gating (V5-0270), UNK-035 (post-2000
currency open), ET-127/ET-128. Full record:
docs/audits/audit_mh_r091_derivation.md.
"""
from __future__ import annotations

import pytest

from app.rules.derivations import derive_mah_status, derive_mh_facts
from app.rules.facts import MH_JURISDICTION, get_fact_spec
from app.rules.models import AndNode, ApplicabilityCondition, NotNode, OrNode
from app.seed.mh.approvals import MH_DEFERRED_RULES, load_mh_approval_rules


def _fields_in(node) -> set[str]:
    if isinstance(node, ApplicabilityCondition):
        return {node.field}
    if isinstance(node, (AndNode, OrNode)):
        out: set[str] = set()
        for child in node.conditions:
            out |= _fields_in(child)
        return out
    if isinstance(node, NotNode):
        return _fields_in(node.condition)
    return set()


def _rule_fields(rule) -> set[str]:
    out: set[str] = set()
    for cond in rule.applicability_conditions:
        out |= _fields_in(cond)
    return out


class TestR091DeferredGate:
    def test_r091_in_deferred_with_partial_note(self):
        assert "R-091" in MH_DEFERRED_RULES
        assert "derive_mah_status" in MH_DEFERRED_RULES["R-091"]

    def test_r091_not_active(self):
        assert "R-091" not in {r.id for r in load_mh_approval_rules()}

    def test_encode_rejects_r091(self):
        from app.seed.mh.approvals import _encode

        with pytest.raises(ValueError, match="deferred"):
            _encode("R-091", "APR-012", [], [])


class TestNoApr012Rule:
    def test_no_active_rule_targets_apr012(self):
        assert "APR-012" not in {r.approval_id for r in load_mh_approval_rules()}

    def test_fprc03_consumers_are_classification_only(self):
        consumers = [
            r for r in load_mh_approval_rules() if "F-PRC-03" in _rule_fields(r)
        ]
        assert [(r.id, r.role.value) for r in consumers] == [("R-002", "classification")]

    def test_downstream_duties_still_deferred(self):
        for rid in ("R-019", "R-020", "R-021"):
            assert rid in MH_DEFERRED_RULES, rid
        assert {r.id for r in load_mh_approval_rules()} & {"R-019", "R-020", "R-021"} == set()

    def test_fprc03_spec_is_derived_only(self):
        spec = get_fact_spec(MH_JURISDICTION, "F-PRC-03")
        assert spec.derived is True


class TestInstallationMatrixUnconsumed:
    def test_fhaz04_registered_but_ignored_by_derivation(self):
        spec = get_fact_spec(MH_JURISDICTION, "F-HAZ-04")
        assert "R-091" in spec.used_in
        base = {
            "F-HAZ-01": [{"chemical": "Toluene", "max_qty_t": 20.0}],
            "F-HAZ-02": [{"chemical": "Toluene", "col3_t": 200.0}],
        }
        with_matrix = dict(base, **{
            "F-HAZ-04": [{"chemical": "Toluene", "installation_id": "U-2",
                           "distance_m": 300, "max_qty_t": 500.0}],
        })
        # M8/R-061 spatial gap: installation/distance evidence cannot move
        # the derivation today; both branches agree (documented partial).
        assert derive_mh_facts(with_matrix) == derive_mh_facts(base)

    def test_split_quantity_documents_m8_limitation(self):
        # Same chemical split across entries below a shared threshold:
        # per-entry comparison (no cross-entry summation without
        # installation/distance evidence — M8/R-061 deferred).
        inv = [{"chemical": "X", "max_qty_t": 60.0},
               {"chemical": "X", "max_qty_t": 60.0}]
        mapping = [{"chemical": "X", "col3_t": 100.0}]
        assert derive_mah_status(inv, mapping) is False
