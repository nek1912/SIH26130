"""MH remaining-inventory consistency pins (audit sweep, 2026-09-29).

Inventory-only: no pack logic, engine semantics, facts, or rule
contents are changed here. Every expectation is derived from the
CURRENT working-tree registers (v5 CSVs are read-only reference;
code sets in app.seed.mh.approvals are authoritative for status).

Working-tree baseline pinned here:
- MH active 26, MH deferred 60, MH confirmation 26, MH facts 128,
  GJ active 19, DEFAULT_JURISDICTION IN-GJ.
- R-015's deferral entry arrived in the working tree from the
  parallel consent-category audit (R-013/R-014/R-015/R-017); R-021's
  entry arrived from the R-021 closure audit. Both are asserted
  separately so those clusters' outcomes stay adjustable without
  rewriting every count.
"""
from __future__ import annotations

from app.rules.facts import MH_FACTS, mh_fact_keys
from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ConditionNode,
    LiteralNode,
    NotNode,
    OrNode,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_DO_NOT_IMPLEMENT_RULE_IDS,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    MH_UNKNOWN_RULE_IDS,
    load_mh_approval_rules,
)
from app.seed.pack import (
    DEFAULT_JURISDICTION,
    IN_GJ,
    load_regulatory_pack,
)

# v5 register holds R-001..R-105 exactly.
REGISTER_IDS = {f"R-{i:03d}" for i in range(1, 106)}

# R-015 is owned by the parallel consent-category audit; every other
# deferred entry predates this sweep.
DEFERRED_MINUS_CONSENT_CHAIN = set(MH_DEFERRED_RULES) - {"R-015"}

# The six register-IMPLEMENTATION_SAFE rules with no explicit code
# triage (not active, deferred, confirmation-gated, DNI, or UNKNOWN).
# R-021 was triaged by the parallel MSIHC session (deferred 60th entry);
# R-054 was triaged by a follow-up session implementing the R-054 audit's
# recommendation (deferred 61st entry). The remaining four still lack an
# explicit code entry (default-deny _encode() refuses them with the generic
# "not IMPLEMENTATION_SAFE", which is safe but reason-free).
UNTRIAGED_SAFE_IDS = frozenset(
    {"R-059", "R-071", "R-072", "R-076"}
)


def _leaf_fields(node: ConditionNode) -> set[str]:
    if isinstance(node, ApplicabilityCondition):
        return {node.field}
    if isinstance(node, (AndNode, OrNode)):
        out: set[str] = set()
        for child in node.conditions:
            out |= _leaf_fields(child)
        return out
    if isinstance(node, NotNode):
        return _leaf_fields(node.condition)
    if isinstance(node, LiteralNode):
        return set()
    raise AssertionError(f"unknown node {node!r}")


class TestInventoryCounts:
    def test_baseline_counts(self):
        assert len(MH_INCLUDED_RULE_IDS) == 26
        assert len(load_mh_approval_rules()) == 26
        # 59 at EC-core time + R-021 (parallel MSIHC session) + R-054
        # (follow-up implementing the R-054 audit recommendation).
        assert len(MH_DEFERRED_RULES) == 61
        assert len(MH_REQUIRES_CONFIRMATION_RULE_IDS) == 26
        assert len(MH_FACTS) == 128
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19
        assert DEFAULT_JURISDICTION == IN_GJ

    def test_consent_chain_r015_deferred_in_working_tree(self):
        assert "R-015" in MH_DEFERRED_RULES
        assert len(DEFERRED_MINUS_CONSENT_CHAIN) == 60

    def test_register_arithmetic(self):
        active = set(MH_INCLUDED_RULE_IDS)
        deferred = set(MH_DEFERRED_RULES)
        conf = set(MH_REQUIRES_CONFIRMATION_RULE_IDS)
        dni = set(MH_DO_NOT_IMPLEMENT_RULE_IDS)
        unk = set(MH_UNKNOWN_RULE_IDS)
        triaged = active | deferred | conf | dni | unk
        assert triaged | set(UNTRIAGED_SAFE_IDS) == REGISTER_IDS
        assert triaged & set(UNTRIAGED_SAFE_IDS) == set()
        assert len(REGISTER_IDS) == 105


class TestStatusSetHygiene:
    def test_active_disjoint_from_deferred_and_confirmation(self):
        active = set(MH_INCLUDED_RULE_IDS)
        assert active & set(MH_DEFERRED_RULES) == set()
        assert active & set(MH_REQUIRES_CONFIRMATION_RULE_IDS) == set()
        assert active & set(MH_DO_NOT_IMPLEMENT_RULE_IDS) == set()
        assert active & set(MH_UNKNOWN_RULE_IDS) == set()

    def test_all_status_sets_subset_of_register(self):
        for rid in (
            set(MH_INCLUDED_RULE_IDS)
            | set(MH_DEFERRED_RULES)
            | set(MH_REQUIRES_CONFIRMATION_RULE_IDS)
            | set(MH_DO_NOT_IMPLEMENT_RULE_IDS)
            | set(MH_UNKNOWN_RULE_IDS)
            | set(MH_IMPLEMENTATION_SAFE_RULE_IDS)
        ):
            assert rid in REGISTER_IDS, rid

    def test_no_gj_identity_in_mh_sets(self):
        gj_ids = {r.id for r in load_regulatory_pack(IN_GJ).approval_rules}
        assert gj_ids & set(MH_INCLUDED_RULE_IDS) == set()
        assert gj_ids & set(MH_DEFERRED_RULES) == set()
        assert gj_ids & set(MH_REQUIRES_CONFIRMATION_RULE_IDS) == set()
        # Namespaces are disjoint by construction (A/py vs R/APR).
        for rid in set(MH_INCLUDED_RULE_IDS) | set(MH_DEFERRED_RULES):
            assert rid.startswith("R-"), rid

    def test_dni_and_unknown_sets(self):
        assert set(MH_DO_NOT_IMPLEMENT_RULE_IDS) == {"R-016", "R-029", "R-058"}
        assert set(MH_UNKNOWN_RULE_IDS) == {"R-015", "R-052", "R-074"}
        assert len(MH_IMPLEMENTATION_SAFE_RULE_IDS) == 76


class TestActiveRuleClosure:
    def test_every_active_rule_leaf_is_a_known_mh_fact(self):
        known = set(mh_fact_keys())
        assert known == set(MH_FACTS)
        for rule in load_mh_approval_rules():
            for cond in rule.applicability_conditions:
                missing = _leaf_fields(cond) - known
                assert not missing, (rule.id, missing)

    def test_no_active_rule_references_another_rule(self):
        for rule in load_mh_approval_rules():
            for cond in rule.applicability_conditions:
                for field in _leaf_fields(cond):
                    assert field.startswith("F-"), (rule.id, field)

    def test_every_active_rule_source_resolves_in_mh_corpus(self):
        corpus = {s.id for s in load_regulatory_pack("IN-MH").sources}
        assert len(corpus) == 22
        for rule in load_mh_approval_rules():
            for ref in rule.source_refs:
                assert ref.source_id in corpus, (rule.id, ref.source_id)

    def test_every_active_rule_approval_has_authority_string(self):
        authorities = load_regulatory_pack("IN-MH").approval_authorities
        for rule in load_mh_approval_rules():
            assert rule.approval_id in authorities, rule.id


class TestKnownBlockedReadiness:
    def test_apr010_prereqs_have_no_active_rule(self):
        """DEP-009 (APR-008/APR-009 -> APR-010) is fail-closed by absence.

        Neither CTE (APR-008) nor CTO (APR-009) has an active rule, so
        R-018/R-096 can be APPLIES yet never READY until the consent
        chain lands. That is safe blocking, not an unsafe dependency.
        """
        active_approvals = {r.approval_id for r in load_mh_approval_rules()}
        assert "APR-008" not in active_approvals
        assert "APR-009" not in active_approvals
        assert "APR-010" in active_approvals
        prereqs = {
            d.prerequisite_approval_id
            for d in load_regulatory_pack("IN-MH").dependencies
            if d.approval_id == "APR-010"
        }
        assert prereqs == {"APR-008", "APR-009"}
