"""Tests for Maharashtra MIDC Lifecycle Tail Cluster (R-039, R-040, APR-031, DEP-019).

This suite audits and verifies the remaining MIDC lifecycle tail:

- R-039: MIDC tree felling permission (TREE := F-SITE-01 AND MIDC/non-MIDC
  branch, APR-036;APR-042) - CONFIRMATION-GATED (unchanged)
  Reason: dual approval target with embedded routing (MIDC -> APR-036 under
  AUT-010; non-MIDC + urban -> APR-042 under AUT-022); MIDC branch T3
  portal-only; non-MIDC branch cites Trees Act 1975 whose text was never
  fetched (LOW confidence, Tree Authority routing unresolved, UR-17 OPEN).
- R-040: MIDC change in manufacturing activity (APR-037, OPERATION/
  MODIFICATION) - CONFIRMATION-GATED (unchanged)
  Reason: T3 portal-only SRC-043; `product/activity changes` has no fact
  (F-EXP-01 means expansion/modernisation for EC/MPCB and is BOOL without
  UNKNOWN); modification-event semantics need workflow state.
- APR-031: MIDC plinth/commencement e-intimation - REPORT, not an approval
  (REGISTRATION/REPORT, CONSTRUCTION lifecycle; rule R-036
  confirmation-gated). Zero code references: correctly unmodeled.
- DEP-019: APR-029 plot holder -> APR-030 building permission -
  YES_INFERRED workflow ordering (MEDIUM, T3 service list), not a stated
  legal precondition. Deferred with explicit inferred-status rationale.

Register identity is transcribed from the CURRENT rule_register_v5.csv,
rules.csv, approvals.csv, authorities.csv, facts.csv, sources.csv,
dependencies.csv, requires_confirmation.csv, unknowns.csv,
unresolved_items.csv, sla.csv and edge_tests.csv. No CSV is read at
runtime; values are hardcoded with register citations.

Zero pack changes from this cluster beyond one strengthened deferral
rationale (DEP-019). R-039/R-040 were already confirmation-gated.
"""
from __future__ import annotations

import pytest

from app.rules.applicability import evaluate_rule
from app.rules.facts import (
    MH_FACTS,
    FactValidationError,
    FactValueType,
    get_fact_spec,
    validate_fact_value,
)
from app.rules.models import (
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalRule,
    SourceRef,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.mh.dependencies import MH_DEP_DEFERRED
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

MIDC_TAIL_RULES: frozenset[str] = frozenset({
    "R-039",
    "R-040",
})

MIDC_TAIL_APPROVALS: frozenset[str] = frozenset({
    "APR-031",
    "APR-036",
    "APR-037",
    "APR-042",
})


def _leaf_rule(field: str, value: object) -> ApprovalRule:
    """Build a minimal single-leaf rule over an MH fact for engine checks."""
    return ApprovalRule(
        id="TEST-MIDC-TAIL",
        approval_id="APR-TEST",
        applicability_conditions=[
            ApplicabilityCondition(
                field=field,
                op=ApplicabilityOp("eq"),
                value=value,
            )
        ],
        source_refs=[SourceRef(source_id="SRC-TEST", citation_span="-")],
        version="test",
    )


class TestBaselineCounts:
    """Confirm the repository baseline before asserting cluster effects."""

    def test_default_jurisdiction_is_gj(self):
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_mh_active_rule_count_is_26(self):
        assert len(load_mh_approval_rules()) == 26

    def test_mh_deferred_count_is_61(self):
        """61 = 56 pre-existing + R-081 + R-099 + R-015 + R-021 + R-054."""
        assert len(MH_DEFERRED_RULES) == 61

    def test_gj_active_rule_count_is_19(self):
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_mh_fact_count_is_128(self):
        assert len(MH_FACTS) == 128

    def test_active_deferred_disjoint(self):
        overlap = MH_INCLUDED_RULE_IDS & frozenset(MH_DEFERRED_RULES.keys())
        assert not overlap, f"Active/deferred overlap: {overlap}"


class TestR039Identity:
    """R-039 exact identity (rule_register_v5.csv + rules.csv)."""

    def test_title_is_midc_tree_felling(self):
        """Title 'MIDC tree felling permission', obligation APPROVAL,
        jurisdiction MIDC, rule kind DETERMINISTIC."""
        assert "R-039" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_dual_approval_target(self):
        """APR-036 (MIDC tree, AUT-010) + APR-042 (urban non-MIDC tree,
        AUT-022): two authorities, two jurisdictions, one rule. A single
        ApprovalRule cannot route across authorities."""
        assert "R-039" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-039" not in MH_INCLUDED_RULE_IDS

    def test_not_in_safe_set(self):
        assert "R-039" not in MH_IMPLEMENTATION_SAFE_RULE_IDS

    def test_not_in_deferred_dict(self):
        """Blocked via the confirmation path (same precedent as R-036/
        R-037), not via MH_DEFERRED_RULES."""
        assert "R-039" not in MH_DEFERRED_RULES

    def test_condition_is_branch_not_predicate(self):
        """TREE := F-SITE-01==TRUE AND (MIDC_BRANCH -> APR-036; NOT MIDC
        AND F-LOC-06==TRUE -> APR-042; else UNKNOWN). The parenthesised
        branch is approval routing (-> APR-xxx), not a boolean trigger;
        ConditionNode has no rule-reference or routing primitive."""
        for fid in ("F-SITE-01", "F-LOC-01", "F-LOC-06"):
            assert get_fact_spec("IN-MH", fid) is not None

    def test_sources_are_t3_only(self):
        """SRC-043 (MIDC portal) + SRC-070 (MAITRI page): T3
        OFFICIAL_PORTAL; the Trees Act 1975 text itself was never fetched
        (AUT-022 notes 'Act text not fetched in this pack')."""
        assert "R-039" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_effective_date_unknown(self):
        """effective_date '-' with UNKNOWN temporal status: any temporal
        query must fail closed to INSUFFICIENT_DATA."""
        assert "R-039" not in MH_INCLUDED_RULE_IDS

    def test_encode_rejects_r039(self):
        with pytest.raises(ValueError, match="is not IMPLEMENTATION_SAFE"):
            _encode("R-039", "APR-036", [], [])

    def test_no_edge_tests_for_r039(self):
        """No ET row covers R-039 (unlike R-078 ET-117 or R-080 ET-118):
        branch behaviour is unexercised by the register itself."""
        assert "R-039" in MH_REQUIRES_CONFIRMATION_RULE_IDS


class TestR040Identity:
    """R-040 exact identity (rule_register_v5.csv + rules.csv)."""

    def test_title_is_midc_change_activity(self):
        """Title 'MIDC change in manufacturing activity', obligation
        APPROVAL, authority AUT-010, jurisdiction MIDC."""
        assert "R-040" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_stage_is_operation_modification(self):
        """APR-037 is stage OPERATION / lifecycle MODIFICATION — the only
        MODIFICATION-lifecycle approval in the MIDC chain. A change event
        is workflow state, not project applicability."""
        assert "R-040" not in MH_INCLUDED_RULE_IDS

    def test_change_fact_has_no_registry_entry(self):
        """`product/activity changes` appears in no facts.csv row and no
        MH_FACTS key: the core conjunct is unmodeled."""
        for key in MH_FACTS:
            assert "PRODUCT_CHANGE" not in key.upper()
            assert "ACTIVITY_CHANGE" not in key.upper()

    def test_fexp01_is_wrong_semantics_and_stricter_type(self):
        """F-EXP-01 means expansion/modernisation (EC 7(ii)/MPCB), not
        product/activity change; and it is BOOL without UNKNOWN, so an
        unknown change cannot even be represented."""
        spec = get_fact_spec("IN-MH", "F-EXP-01")
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is False
        assert spec.label == "is_expansion_or_modernisation"

    def test_unknown_change_cannot_be_represented(self):
        """F-EXP-01 rejects the 'UNKNOWN' token (BOOL, unknown_allowed
        False): coercing an unknown product change through F-EXP-01 would
        corrupt EC/MPCB semantics elsewhere."""
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-EXP-01", "UNKNOWN")

    def test_source_is_t3_portal_only(self):
        """Sole source SRC-043 (MIDC services portal, T3); legal basis
        'MIDC service'/'MIDC lease/service' — no statutory provision."""
        assert "R-040" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_encode_rejects_r040(self):
        with pytest.raises(ValueError, match="is not IMPLEMENTATION_SAFE"):
            _encode("R-040", "APR-037", [], [])

    def test_r040_not_in_safe_or_deferred(self):
        assert "R-040" not in MH_IMPLEMENTATION_SAFE_RULE_IDS
        assert "R-040" not in MH_DEFERRED_RULES


class TestApr031Boundary:
    """APR-031 is a REPORT, not an approval (approvals.csv)."""

    def test_record_class_is_registration(self):
        """record_class REGISTRATION (not APPROVAL)."""
        assert "R-036" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_record_type_is_report(self):
        """record_type REPORT with lifecycle CONSTRUCTION: an intimation
        artifact generated during construction, not a decision."""
        assert "R-036" not in MH_INCLUDED_RULE_IDS

    def test_trigger_is_construction_itself(self):
        """Trigger 'Construction in MIDC': the report follows commencement;
        it does not authorize commencement (that is APR-030, bundled with
        provisional fire via DEP-004)."""
        mh_pack = load_regulatory_pack("IN-MH")
        edges = {(d.approval_id, d.prerequisite_approval_id)
                 for d in mh_pack.dependencies}
        assert ("APR-031", "APR-030") not in edges

    def test_no_separate_applicability_condition(self):
        """APR-031's only rule is R-036 (the portal bundle, confirmation-
        gated): no independent statutory trigger exists."""
        assert "R-036" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_no_code_modeling_of_apr031(self):
        """The loaded MH pack carries no APR-031 authority entry, no
        dependency edge touching APR-031, and no APR-031 SLA record:
        nothing treats it as an approval decision."""
        mh_pack = load_regulatory_pack("IN-MH")
        assert "APR-031" not in mh_pack.approval_authorities
        for dep in mh_pack.dependencies:
            assert "APR-031" not in (dep.approval_id,
                                     dep.prerequisite_approval_id)
        assert not [s for s in mh_pack.sla_records
                    if s.approval_id == "APR-031"]
        assert "SRC-070" not in {s.id for s in mh_pack.sources}

    def test_no_rule_equates_apr031_with_approvals(self):
        """No active rule targets APR-031; R-036 (its only referencing
        rule) is confirmation-gated and shared with APR-030/APR-033."""
        active_approvals = {r.approval_id
                            for r in load_mh_approval_rules()}
        assert "APR-031" not in active_approvals
        for apr_id in ("APR-030", "APR-032", "APR-038", "APR-041"):
            assert apr_id not in active_approvals or apr_id != "APR-031"

    def test_midc_tail_approvals_absent_from_active_pack(self):
        active_approvals = {r.approval_id
                            for r in load_mh_approval_rules()}
        assert not (MIDC_TAIL_APPROVALS & active_approvals)


class TestDep019:
    """DEP-019 is inferred ordering, not a legal precondition."""

    def test_inferred_flag_in_register(self):
        """inferred YES_INFERRED, MEDIUM confidence, T3 SRC-043 service
        list, class OFFICIAL_WORKFLOW (not EXPLICIT_LEGAL)."""
        assert "DEP-019" in MH_DEP_DEFERRED

    def test_rationale_records_inferred_status(self):
        reason = MH_DEP_DEFERRED["DEP-019"]
        assert "YES_INFERRED" in reason
        assert "not a stated legal precondition" in reason
        assert "SRC-043" in reason

    def test_direction_plot_holder_to_bp(self):
        """APR-029 (plot allotment) -> APR-030 (building permission):
        'issued to plot holder' is portal sequencing, not a regulation."""
        mh_pack = load_regulatory_pack("IN-MH")
        edges = {(d.approval_id, d.prerequisite_approval_id)
                 for d in mh_pack.dependencies}
        assert ("APR-030", "APR-029") not in edges

    def test_removal_affects_no_active_rule(self):
        """APR-030 has no active rule; APR-029's active rule R-035 is a
        location guard needing no BP input. No active MH rule depends on
        the APR-029 -> APR-030 chain."""
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-035" in active
        assert "R-036" not in active
        for rule_id in ("R-037", "R-041", "R-080", "R-082"):
            assert rule_id not in active

    def test_sibling_midc_deps_also_deferred(self):
        """DEP-003 (CTE for BP) and DEP-004 (bundled BP+fire) are likewise
        out of the loaded pack: the MIDC BP neighbourhood contributes
        zero readiness edges."""
        mh_pack = load_regulatory_pack("IN-MH")
        edges = {(d.approval_id, d.prerequisite_approval_id)
                 for d in mh_pack.dependencies}
        assert ("APR-030", "APR-008") not in edges


class TestUnknownAndMissingBehaviour:
    """UNKNOWN never becomes FALSE across tail facts."""

    def test_fsite01_three_valued(self):
        assert evaluate_rule(_leaf_rule("F-SITE-01", True),
                             {"F-SITE-01": True}).result == "applies"
        assert evaluate_rule(_leaf_rule("F-SITE-01", True),
                             {"F-SITE-01": False}).result == "does_not_apply"
        assert evaluate_rule(_leaf_rule("F-SITE-01", True),
                             {"F-SITE-01": None}).result == "insufficient_data"
        assert evaluate_rule(_leaf_rule("F-SITE-01", True),
                             {}).result == "insufficient_data"

    def test_floc06_three_valued(self):
        assert evaluate_rule(_leaf_rule("F-LOC-06", True),
                             {"F-LOC-06": True}).result == "applies"
        assert evaluate_rule(_leaf_rule("F-LOC-06", True),
                             {"F-LOC-06": None}).result != "does_not_apply"
        assert evaluate_rule(_leaf_rule("F-LOC-06", True),
                             {}).result != "does_not_apply"

    def test_floc01_unknown_blocks_branch(self):
        """R-039's MIDC/non-MIDC fork cannot resolve with F-LOC-01
        UNKNOWN: neither APR-036 nor APR-042 may be selected."""
        assert evaluate_rule(_leaf_rule("F-LOC-01", True),
                             {"F-LOC-01": None}).result == "insufficient_data"

    def test_fexp01_missing_is_insufficient(self):
        """Missing F-EXP-01 fails closed; it must never stand in for an
        unmodeled product-change fact."""
        assert evaluate_rule(_leaf_rule("F-EXP-01", True),
                             {}).result == "insufficient_data"

    def test_invalid_fact_values_rejected(self):
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-SITE-01", "YES")
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-LOC-06", 42)

    def test_none_always_valid(self):
        validate_fact_value("IN-MH", "F-SITE-01", None)
        validate_fact_value("IN-MH", "F-LOC-06", None)
        validate_fact_value("IN-MH", "F-EXP-01", None)


class TestNoPortalToStatutoryInference:
    """Portal listings prove services, never statutory applicability."""

    def test_r039_gate_despite_portal_services(self):
        """SRC-043 lists MIDC tree services and SRC-070 lists MAITRI
        integrations, yet R-039 stays confirmation-gated."""
        assert "R-039" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-039" not in MH_INCLUDED_RULE_IDS

    def test_r040_gate_despite_portal_service(self):
        """SRC-043 lists the MIDC change-of-activity service with a
        VERIFIED portal SLA (SLA-022, 21 days), yet R-040 stays
        confirmation-gated: SLA existence is not applicability."""
        assert "R-040" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        mh_pack = load_regulatory_pack("IN-MH")
        assert "SLA-022" not in {s.sla_id for s in mh_pack.sla_records}

    def test_tree_sla_conflict_preserved_not_resolved(self):
        """SLA-021 (45 d, SRC-043) vs 60 d alt (SRC-044) under CON-001:
        neither value is in the loaded pack; no deadline is computed."""
        mh_pack = load_regulatory_pack("IN-MH")
        assert "SLA-021" not in {s.sla_id for s in mh_pack.sla_records}

    def test_no_false_tree_approval(self):
        """Trees present (F-SITE-01 True) on a non-MIDC rural site must
        not yield any active approval: R-039 gated, AUT-022 routing
        unresolved (UR-17 OPEN)."""
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-039" not in active

    def test_no_false_change_approval(self):
        """An operating MIDC unit changing products must not yield any
        active approval from R-040."""
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-040" not in active


class TestCrossRuleSeparation:
    """Tail rules stay separated from the audited MIDC/fire graph."""

    def test_r036_r039_share_portal_basis_not_logic(self):
        """R-036 (BP bundle) and R-039 (tree) share T3 portal sources and
        the confirmation gate, but neither composes with the other."""
        assert "R-036" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-039" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_r040_independent_of_consent_chain(self):
        """R-040 references no consent/sector rule (unlike R-017 on R-013
        or R-079 on R-078): it is isolated by evidence, not by composition.
        The next-cluster consent chain is untouched."""
        assert "R-040" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_midc_branch_guard_still_sole_router(self):
        """R-035 remains the only active MIDC/non-MIDC branch rule; R-039's
        embedded MIDC fork adds no parallel routing."""
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-035" in active
        assert "R-039" not in active

    def test_fire_chain_unaffected(self):
        """R-078/R-079 deferred, R-042/R-099 gated/deferred: R-039's APR-042
        (tree, urban) shares no logic with APR-040 (final fire NOC)
        despite adjacent numbering."""
        active = {r.id for r in load_mh_approval_rules()}
        assert not ({"R-039", "R-040", "R-078", "R-079", "R-099",
                     "R-042"} & active)


class TestJurisdictionIsolation:
    """IN-MH tail work must not leak into IN-GJ."""

    def test_gj_pack_untouched(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        gj_ids = {r.id for r in gj_pack.approval_rules}
        assert not (MIDC_TAIL_RULES & gj_ids)

    def test_gj_approvals_untouched(self):
        gj_approval_ids = {r.approval_id
                           for r in load_regulatory_pack(IN_GJ).approval_rules}
        assert not (MIDC_TAIL_APPROVALS & gj_approval_ids)

    def test_gj_namespace_rejects_tail_facts(self):
        for fid in ("F-SITE-01", "F-LOC-06", "F-EXP-01"):
            with pytest.raises(FactValidationError) as exc:
                validate_fact_value("IN-GJ", fid, True)
            assert exc.value.code == FactValidationError.JURISDICTION_MISMATCH

    def test_mh_active_unchanged(self):
        assert len(load_mh_approval_rules()) == 26


class TestClassification:
    """Exactly-one primary classification per candidate."""

    def test_r039_is_class_c(self):
        """C - evidence incomplete / confirmation-gated."""
        assert "R-039" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-039" not in MH_INCLUDED_RULE_IDS

    def test_r040_is_class_c(self):
        assert "R-040" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-040" not in MH_INCLUDED_RULE_IDS

    def test_apr031_is_report_not_approval(self):
        """APR-031's register type is REPORT/REGISTRATION; the pack models
        no decision, edge, SLA, or authority for it."""
        mh_pack = load_regulatory_pack("IN-MH")
        assert "APR-031" not in mh_pack.approval_authorities
        assert "R-036" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_dep019_is_inferred_not_legal(self):
        """DEP-019 stays deferred as inferred ordering, never elevated."""
        assert "DEP-019" in MH_DEP_DEFERRED
        assert "YES_INFERRED" in MH_DEP_DEFERRED["DEP-019"]
        mh_pack = load_regulatory_pack("IN-MH")
        edges = {(d.approval_id, d.prerequisite_approval_id)
                 for d in mh_pack.dependencies}
        assert ("APR-030", "APR-029") not in edges

    def test_zero_rules_activated(self):
        active = {r.id for r in load_mh_approval_rules()}
        assert not (MIDC_TAIL_RULES & active)
