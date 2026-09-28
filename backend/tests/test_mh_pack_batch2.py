"""MH batch-2 safe rules: R-073 / R-086 / R-087 (boiler lifecycle).

Evidence (in-repo v5 only):
- R-073 BOE_REQUIRED := F-BLR-06 > 1000 m2 (BOE Rules 2025, SRC-085;
  ET-096 strict >). Operating condition, not registration.
- R-086 BOILER_REGISTRATION := R-028 boiler tree AND
  F-BLR-07 == NOT_REGISTERED (Boilers Act 2025 s.12, SRC-034).
  Registration; restates the R-028 tree exactly (no rule-reference
  primitive exists) — coupling pinned below.
- R-087 BOILER_EXISTING := F-BLR-07 == REGISTERED_UNDER_1923_ACT ->
  deemed registered (s.45(2)(f); ET-122). Transitional status.

Blocked (evidence insufficient for deterministic encoding; also
pinned in MH_DEFERRED_RULES so _encode refuses them):
- R-075: needs an EC-grant-date fact (absent) + date arithmetic
  (unsupported primitive).
- R-088: needs event facts (accident/move/alteration/direction/order;
  absent) + date comparison.
- R-100/R-101/R-102: "APPLIES if unit holds such a licence (input)"
  (SSC-01..03) but no licence-held fact exists.
- R-103: needs new-licence + application-date facts (absent);
  gas-only encoding would over-apply against ET-v5-12.
- R-104: needs licence-held/purpose/filling-plant facts (absent).
"""
from __future__ import annotations

from datetime import date

from app.rules.applicability import evaluate_rule
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import IN_GJ, IN_MH, load_regulatory_pack


def _by_id():
    rules = {r.id: r for r in load_mh_approval_rules()}
    assert "R-073" in rules
    assert "R-086" in rules
    assert "R-087" in rules
    return rules


def _eval(rule_id, facts, evaluation_date=None):
    return evaluate_rule(
        _by_id()[rule_id], facts, evaluation_date=evaluation_date
    )


class TestPackContents:
    def test_batch2_included(self):
        assert {"R-073", "R-086", "R-087"} <= set(MH_INCLUDED_RULE_IDS)
        assert len(load_mh_approval_rules()) == 26

    def test_batch2_source_refs(self):
        rules = _by_id()
        assert rules["R-073"].source_refs[0].source_id == "SRC-085"
        assert rules["R-086"].source_refs[0].source_id == "SRC-034"
        assert rules["R-087"].source_refs[0].source_id == "SRC-034"

    def test_no_new_approval_identities(self):
        pack = load_regulatory_pack(IN_MH)
        assert pack.approval_authorities["APR-023"] == "AUT-007"
        assert {r.approval_id for r in load_mh_approval_rules()} <= set(
            pack.approval_authorities
        )

    def test_gj_pack_untouched(self):
        gj_ids = {
            r.id
            for r in load_regulatory_pack(IN_GJ).approval_rules
        }
        assert {"R-073", "R-086", "R-087"} & gj_ids == set()


class TestR073BoeRequired:
    def test_applies_above_1000(self):
        assert _eval("R-073", {"F-BLR-06": 1000.1}).result == "applies"

    def test_not_applies_at_exactly_1000(self):
        # ET-096: strict >.
        assert _eval("R-073", {"F-BLR-06": 1000}).result == (
            "does_not_apply"
        )

    def test_not_applies_below(self):
        assert _eval("R-073", {"F-BLR-06": 500}).result == (
            "does_not_apply"
        )

    def test_missing_is_insufficient(self):
        result = _eval("R-073", {})
        assert result.result == "insufficient_data"
        assert result.missing_inputs == ["F-BLR-06"]

    def test_unknown_is_insufficient(self):
        assert _eval("R-073", {"F-BLR-06": "UNKNOWN"}).result == (
            "insufficient_data"
        )

    def test_before_effective_from(self):
        result = _eval(
            "R-073", {"F-BLR-06": 1500},
            evaluation_date=date(2025, 9, 22),
        )
        assert result.result == "does_not_apply"
        assert "not in force" in result.reason

    def test_exactly_effective_from(self):
        assert _eval(
            "R-073", {"F-BLR-06": 1500},
            evaluation_date=date(2025, 9, 23),
        ).result == "applies"

    def test_in_window(self):
        assert _eval(
            "R-073", {"F-BLR-06": 1500},
            evaluation_date=date(2026, 3, 1),
        ).result == "applies"

    def test_missing_date_preserves_behavior(self):
        assert _eval("R-073", {"F-BLR-06": 1500}).result == "applies"


_BOILER_FACTS = {
    "F-BLR-04": True,
    "F-BLR-01": 30,
    "F-BLR-05": 2,
    "F-BLR-02": 2,
    "F-BLR-03": 150,
}


class TestR086Registration:
    def test_applies_unregistered_boiler(self):
        facts = dict(_BOILER_FACTS, **{"F-BLR-07": "NOT_REGISTERED"})
        assert _eval("R-086", facts).result == "applies"

    def test_not_applies_when_registered(self):
        facts = dict(
            _BOILER_FACTS, **{"F-BLR-07": "REGISTERED_UNDER_2025_ACT"}
        )
        assert _eval("R-086", facts).result == "does_not_apply"

    def test_not_applies_when_not_a_boiler(self):
        facts = {"F-BLR-04": False, "F-BLR-07": "NOT_REGISTERED"}
        assert _eval("R-086", facts).result == "does_not_apply"

    def test_missing_status_is_insufficient(self):
        assert _eval("R-086", dict(_BOILER_FACTS)).result == (
            "insufficient_data"
        )

    def test_unknown_status_is_insufficient(self):
        facts = dict(_BOILER_FACTS, **{"F-BLR-07": "UNKNOWN"})
        assert _eval("R-086", facts).result == "insufficient_data"

    def test_before_effective_from(self):
        facts = dict(_BOILER_FACTS, **{"F-BLR-07": "NOT_REGISTERED"})
        result = _eval(
            "R-086", facts, evaluation_date=date(2025, 4, 30)
        )
        assert result.result == "does_not_apply"
        assert "not in force" in result.reason

    def test_exactly_effective_from(self):
        facts = dict(_BOILER_FACTS, **{"F-BLR-07": "NOT_REGISTERED"})
        assert _eval(
            "R-086", facts, evaluation_date=date(2025, 5, 1)
        ).result == "applies"

    def test_in_window(self):
        facts = dict(_BOILER_FACTS, **{"F-BLR-07": "NOT_REGISTERED"})
        assert _eval(
            "R-086", facts, evaluation_date=date(2026, 1, 15)
        ).result == "applies"

    def test_missing_date_preserves_behavior(self):
        facts = dict(_BOILER_FACTS, **{"F-BLR-07": "NOT_REGISTERED"})
        assert _eval("R-086", facts).result == "applies"

    def test_boiler_limb_mirrors_r028(self):
        # R-086 restates the R-028 tree exactly: with registration held
        # at NOT_REGISTERED, both rules must agree on every input.
        rules = _by_id()
        samples = [
            dict(_BOILER_FACTS),
            {"F-BLR-04": False, "F-BLR-01": 30, "F-BLR-05": 2,
             "F-BLR-02": 2, "F-BLR-03": 150},
            {"F-BLR-04": True, "F-BLR-01": 10, "F-BLR-05": 2,
             "F-BLR-02": 2, "F-BLR-03": 150},
            {"F-BLR-04": True},
            {},
        ]
        for facts in samples:
            r028 = evaluate_rule(rules["R-028"], facts).result
            r086 = evaluate_rule(
                rules["R-086"],
                dict(facts, **{"F-BLR-07": "NOT_REGISTERED"}),
            ).result
            assert r028 == r086, facts


class TestR087Existing:
    def test_applies_1923_registered(self):
        facts = {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"}
        assert _eval("R-087", facts).result == "applies"

    def test_not_applies_not_registered(self):
        facts = {"F-BLR-07": "NOT_REGISTERED"}
        assert _eval("R-087", facts).result == "does_not_apply"

    def test_not_applies_2025_registered(self):
        facts = {"F-BLR-07": "REGISTERED_UNDER_2025_ACT"}
        assert _eval("R-087", facts).result == "does_not_apply"

    def test_missing_is_insufficient(self):
        assert _eval("R-087", {}).result == "insufficient_data"

    def test_unknown_is_insufficient(self):
        assert _eval("R-087", {"F-BLR-07": "UNKNOWN"}).result == (
            "insufficient_data"
        )

    def test_before_effective_from(self):
        result = _eval(
            "R-087", {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
            evaluation_date=date(2025, 4, 30),
        )
        assert result.result == "does_not_apply"
        assert "not in force" in result.reason

    def test_exactly_effective_from(self):
        assert _eval(
            "R-087", {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
            evaluation_date=date(2025, 5, 1),
        ).result == "applies"

    def test_in_window(self):
        assert _eval(
            "R-087", {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"},
            evaluation_date=date(2026, 6, 1),
        ).result == "applies"

    def test_missing_date_preserves_behavior(self):
        facts = {"F-BLR-07": "REGISTERED_UNDER_1923_ACT"}
        assert _eval("R-087", facts).result == "applies"


class TestBlockedBatch2:
    def test_blocked_ids_documented_and_refused(self):
        import pytest

        blocked = {
            "R-075": "EC grant-date fact absent; DATE arithmetic unsupported",
            "R-088": "accident/move/alteration/direction/order event facts absent",
            "R-100": "licence-held input fact absent (SSC-01)",
            "R-101": "licence-held input fact absent (SSC-02)",
            "R-102": "licence-held input fact absent (SSC-03)",
            "R-103": "new-licence + application-date facts absent",
            "R-104": "licence-held/purpose/filling-plant facts absent",
        }
        for rule_id in blocked:
            assert rule_id in MH_DEFERRED_RULES, rule_id
            assert rule_id not in MH_INCLUDED_RULE_IDS, rule_id
            with pytest.raises(ValueError):
                _encode(rule_id, "APR-X", [], [])

    def test_blocked_absent_from_pack(self):
        packed = {r.id for r in load_mh_approval_rules()}
        assert {
            "R-075", "R-088", "R-100", "R-101", "R-102", "R-103",
            "R-104",
        } & packed == set()


class TestBatch2Orchestration:
    def test_apr023_applies_with_boiler_facts(self):
        from app.orchestration.service import orchestrate_application_full

        pack = load_regulatory_pack(IN_MH)
        facts = dict(
            _BOILER_FACTS,
            **{
                "F-BLR-06": 1500,
                "F-BLR-07": "NOT_REGISTERED",
                "F-BLR-08": "2026-12-31",
            },
        )
        orch = orchestrate_application_full(
            application_id="TEST",
            project_facts=facts,
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=["APR-023"],
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval=None,
        )
        assert orch.approvals["APR-023"].applicability_result == "applies"
