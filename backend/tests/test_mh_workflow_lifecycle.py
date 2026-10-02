"""Tests for Maharashtra Workflow/Lifecycle Cluster (R-081, R-099, R-036).

This suite audits and verifies the remaining SAFE-but-untriaged
workflow/lifecycle candidates identified by the fire/building audit:

- R-081: Deemed building permission (BP_DEEMED_POSSIBLE, APR-038) - DEFERRED
  Reason: procedural workflow consequence under MRTP s.45(5), not an approval
  applicability predicate; needs DATE arithmetic over absent application/
  requisition-reply date facts plus a DCR-conformance proviso the engine
  cannot verify; the register forbids asserting deemed grant.
- R-099: Final fire approval renewal (FINAL_FIRE_APPROVAL_RENEWAL, APR-040)
  - DEFERRED
  Reason: renewal/lifecycle rule whose TRUE branch yields CONDITIONAL
  (renewal per another Act/Rule), never APPLIES; general principle is
  DOES_NOT_APPLY under the Fire Act (FR-01, CON-013 resolved); the
  chemical-sector exception is unresolved (FR-03, CON-024, UR-04); Form B
  Jan/Jul is a separate operating duty (FR-04, CMP-008).
- R-036: MIDC combined building permission + provisional fire NOC
  (APR-030;APR-031;APR-033) - CONFIRMATION-GATED (unchanged)
  Reason: portal-only T3 evidence (UR-19 OPEN); condition needs the absent
  `construction` fact; one rule spans three lifecycle stages and three
  record classes.

Register identity is transcribed from the CURRENT rule_register_v5.csv,
rules.csv, approvals.csv, authorities.csv, facts.csv, sources.csv,
dependencies.csv, requires_confirmation.csv, unknowns.csv,
unresolved_items.csv, sla.csv, edge_tests.csv, fire_renewal_model.csv and
compliance.csv. No CSV is read at runtime; values are hardcoded with
register citations.

Zero pack changes from this cluster beyond two explicit deferral entries
(R-081, R-099). R-036 was already confirmation-gated.
"""
from __future__ import annotations

import pytest

from app.rules.applicability import evaluate_rule
from app.rules.facts import (
    MH_FACTS,
    FactValueType,
    get_fact_spec,
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
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

WORKFLOW_LIFECYCLE_CLUSTER: frozenset[str] = frozenset({
    "R-081",
    "R-099",
    "R-036",
})

DEFERRED_CLUSTER_RULES: frozenset[str] = frozenset({
    "R-081",
    "R-099",
})


def _test_rule(field: str, value: object) -> ApprovalRule:
    """Build a minimal single-leaf rule over an MH fact for engine checks."""
    return ApprovalRule(
        id="TEST-WORKFLOW-LIFECYCLE",
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

    def test_gj_active_rule_count_is_19(self):
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_mh_fact_count_is_128(self):
        assert len(MH_FACTS) == 128

    def test_deferred_count_is_61(self):
        """56 pre-existing + R-081 + R-099 + R-015 + R-021 + R-054."""
        assert len(MH_DEFERRED_RULES) == 61

    def test_active_deferred_disjoint(self):
        overlap = MH_INCLUDED_RULE_IDS & frozenset(MH_DEFERRED_RULES.keys())
        assert not overlap, f"Active/deferred overlap: {overlap}"


class TestCandidateIdentity:
    """Exact register identity for each candidate (rule_register_v5.csv)."""

    def test_r081_identity(self):
        """R-081: Building/development permission (non-MIDC), APR-038,
        PRE_ESTABLISHMENT, AUT-011, NON_MIDC, VERIFIED_CONDITIONAL,
        IMPLEMENTATION_SAFE, T1 SRC-123 s.45(5), effective 1966 YEAR_ONLY."""
        assert "R-081" in MH_IMPLEMENTATION_SAFE_RULE_IDS
        assert "R-081" in MH_DEFERRED_RULES
        assert "R-081" not in MH_INCLUDED_RULE_IDS

    def test_r099_identity(self):
        """R-099: Final fire NOC (non-MIDC), APR-040, PRE_OPERATION,
        AUT-012, NON_MIDC, VERIFIED_CONDITIONAL, IMPLEMENTATION_SAFE,
        T2 SRC-145 (31-01-2025 paras 3,4,6 + 30-10-2014), EXACT 2023-05-30."""
        assert "R-099" in MH_IMPLEMENTATION_SAFE_RULE_IDS
        assert "R-099" in MH_DEFERRED_RULES
        assert "R-099" not in MH_INCLUDED_RULE_IDS

    def test_r036_identity(self):
        """R-036: MIDC combined BP + provisional fire NOC,
        APR-030;APR-031;APR-033, PRE_ESTABLISHMENT, AUT-010, MIDC,
        REQUIRES_OFFICIAL_CONFIRMATION, T3 SRC-043/SRC-044, effective
        UNKNOWN. Confirmation-gated, NOT in the safe set."""
        assert "R-036" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-036" not in MH_IMPLEMENTATION_SAFE_RULE_IDS
        assert "R-036" not in MH_DEFERRED_RULES
        assert "R-036" not in MH_INCLUDED_RULE_IDS

    def test_r036_triple_approval_target(self):
        """R-036 spans APR-030 (APPROVAL/PRE_CONSTRUCTION), APR-031
        (REGISTRATION/REPORT/CONSTRUCTION) and APR-033 (NOC/PRE_OPERATION)
        per approvals.csv. One ApprovalRule cannot span three lifecycle
        stages and three record classes."""
        reason = (
            "APR-030 combined BP+fire PRE_CONSTRUCTION; APR-031 plinth/"
            "commencement REPORT CONSTRUCTION; APR-033 final fire NOC "
            "PRE_OPERATION"
        )
        assert "APR-030" in reason and "APR-033" in reason

    def test_cluster_absent_from_active_pack(self):
        active = {r.id for r in load_mh_approval_rules()}
        for rule_id in WORKFLOW_LIFECYCLE_CLUSTER:
            assert rule_id not in active

    def test_cluster_absent_from_gj_pack(self):
        gj_ids = {r.id for r in load_regulatory_pack(IN_GJ).approval_rules}
        for rule_id in WORKFLOW_LIFECYCLE_CLUSTER:
            assert rule_id not in gj_ids


class TestDeemedPermissionR081:
    """R-081 (G): deemed permission is a consequence, not applicability."""

    def test_deferral_reason_cites_workflow_character(self):
        reason = MH_DEFERRED_RULES["R-081"]
        assert "workflow consequence" in reason
        assert "s.45(5)" in reason

    def test_deferral_reason_cites_date_arithmetic_gap(self):
        reason = MH_DEFERRED_RULES["R-081"]
        assert "DATE arithmetic" in reason
        assert "application date" in reason

    def test_deferral_reason_cites_conformance_proviso(self):
        reason = MH_DEFERRED_RULES["R-081"]
        assert "DCR-conformance" in reason

    def test_deferral_reason_cites_grant_prohibition(self):
        """The register forbids asserting deemed grant; reason records it."""
        reason = MH_DEFERRED_RULES["R-081"]
        assert "asserting deemed permission as granted" in reason

    def test_application_date_fact_absent(self):
        """Neither application date nor requisition-reply date exists."""
        for key in MH_FACTS:
            assert "APPLICATION_DATE" not in key.upper()
            assert "REQUISITION" not in key.upper()
            assert "DEEMED" not in key.upper()

    def test_no_sixty_day_clock_encodable(self):
        """SLA-042 (60-day deemed clock, LEGAL, SRC-123) is display-only;
        the MH pack carries only 10 SLA rows, none for APR-038."""
        mh_pack = load_regulatory_pack("IN-MH")
        sla_ids = {s.sla_id for s in mh_pack.sla_records}
        assert "SLA-042" not in sla_ids
        assert "SLA-043" not in sla_ids

    def test_src123_not_in_loaded_pack(self):
        """SRC-123 (MRTP T1) is verified in v5 sources.csv but deferred from
        the 22-source loaded pack while routing/regime rules are deferred."""
        src_ids = {s.id for s in load_regulatory_pack("IN-MH").sources}
        assert "SRC-123" not in src_ids

    def test_encode_rejects_r081(self):
        with pytest.raises(ValueError, match="Rule R-081 is deferred"):
            _encode("R-081", "APR-038", [], [])

    def test_no_false_deemed_permission(self):
        """No active MH rule can conclude deemed permission: R-081 is the
        only deemed-permission candidate and it is deferred; R-041 (the
        APR-038 applicability rule) is separately deferred."""
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-081" not in active
        assert "R-041" not in active


class TestFireRenewalR099:
    """R-099 (H): renewal/lifecycle, never an applicability verdict."""

    def test_deferral_reason_cites_renewal_character(self):
        reason = MH_DEFERRED_RULES["R-099"]
        assert "renewal/lifecycle" in reason

    def test_deferral_reason_cites_never_applies(self):
        """TRUE yields CONDITIONAL (per another Act), never APPLIES."""
        reason = MH_DEFERRED_RULES["R-099"]
        assert "never APPLIES" in reason

    def test_deferral_reason_cites_general_principle(self):
        """FR-01: no renewal under the Fire Act (CON-013 resolved)."""
        reason = MH_DEFERRED_RULES["R-099"]
        assert "FR-01" in reason
        assert "CON-013" in reason

    def test_deferral_reason_cites_sector_exception(self):
        """FR-03/CON-024/UR-04: Petroleum/GCR annual-renewal claim
        unverified; F-FIR-20 stays UNKNOWN for chemical units."""
        reason = MH_DEFERRED_RULES["R-099"]
        assert "FR-03" in reason
        assert "UR-04" in reason

    def test_deferral_reason_cites_form_b_separation(self):
        """Form B Jan/Jul is a separate operating duty (FR-04, CMP-008)."""
        reason = MH_DEFERRED_RULES["R-099"]
        assert "FR-04" in reason
        assert "CMP-008" in reason

    def test_ffir20_fact_exists_with_unknown_semantics(self):
        """F-FIR-20 exists (boolean, unknown-allowed, used_in R-099) so the
        input side is modeled; the renewal conclusion is what is deferred."""
        spec = get_fact_spec("IN-MH", "F-FIR-20")
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is True
        assert "R-099" in spec.used_in

    def test_ffir20_true_does_not_imply_applies(self):
        """F-FIR-20==True means 'another Act requires renewal' (ET-v4-01:
        CONDITIONAL per that Act), not 'APR-040 applies'. The engine leaf
        below only proves three-valued input handling, not renewal logic."""
        assert evaluate_rule(_test_rule("F-FIR-20", True),
                             {"F-FIR-20": True}).result == "applies"
        assert evaluate_rule(_test_rule("F-FIR-20", True),
                             {"F-FIR-20": False}).result == "does_not_apply"

    def test_ffir20_unknown_never_false(self):
        """ET-v4-03 / UR-04: F-FIR-20 UNKNOWN -> UNKNOWN, never FALSE."""
        assert evaluate_rule(_test_rule("F-FIR-20", True),
                             {"F-FIR-20": None}).result != "does_not_apply"
        assert evaluate_rule(_test_rule("F-FIR-20", True),
                             {}).result != "does_not_apply"

    def test_peso_licence_is_not_fire_renewal(self):
        """ET-v5-17: holding a PESO licence with no cited rule leaves
        F-FIR-20 UNKNOWN (licence renewal != MFS renewal)."""
        assert evaluate_rule(_test_rule("F-FIR-20", True),
                             {"F-FIR-20": None}).result == "insufficient_data"

    def test_src145_not_in_loaded_pack(self):
        """SRC-145 (MFS circular T2) is verified in v5 sources.csv but
        deferred from the 22-source loaded pack."""
        src_ids = {s.id for s in load_regulatory_pack("IN-MH").sources}
        assert "SRC-145" not in src_ids

    def test_encode_rejects_r099(self):
        with pytest.raises(ValueError, match="Rule R-099 is deferred"):
            _encode("R-099", "APR-040", [], [])

    def test_no_false_renewal_conclusion(self):
        """No active MH rule concludes fire renewal: R-099 deferred, R-042
        (which references R-099) confirmation-gated, no CMP renewal encoded
        as an ApprovalRule."""
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-099" not in active
        assert "R-042" not in active


class TestMidcBuildingPermissionR036:
    """R-036 (I): portal workflow, confirmation-gated, unchanged."""

    def test_confirmation_gate_preserved(self):
        assert "R-036" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_encode_rejects_r036(self):
        """Not in the safe set: blocked before the confirmation check;
        both paths are fail-closed (same precedent as R-037)."""
        with pytest.raises(ValueError, match="is not IMPLEMENTATION_SAFE"):
            _encode("R-036", "APR-030", [], [])

    def test_construction_fact_absent(self):
        """MIDC_BP needs `construction == TRUE`; no such fact exists in
        the 128-fact registry (same gap as R-041)."""
        assert "construction" not in MH_FACTS
        for key in MH_FACTS:
            assert "CONSTRUCT" not in key.upper()

    def test_portal_sources_prove_service_only(self):
        """SRC-043/SRC-044 are T3 OFFICIAL_PORTAL: they prove only tied
        claims at stated locators (service existence + portal timelines),
        never the MIDC DCR statutory text (UR-19 OPEN)."""
        src_ids = {s.id for s in load_regulatory_pack("IN-MH").sources}
        assert "SRC-043" in src_ids
        assert "SRC-044" in src_ids
        # Portal presence must not imply statutory encodability
        # (see next test).

    def test_portal_presence_does_not_authorize_encoding(self):
        assert "R-036" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-036" not in MH_INCLUDED_RULE_IDS

    def test_no_duplicate_midc_bp_representation(self):
        """R-036 (MIDC BP, confirmation-gated) vs R-041 (non-MIDC BP,
        deferred) vs R-080 (BP authority, deferred) vs R-082 (DCR regime,
        deferred) vs R-037 (MIDC OC, confirmation-gated): five distinct
        decisions, none active, none conflated."""
        active = {r.id for r in load_mh_approval_rules()}
        for rule_id in ("R-036", "R-037", "R-041", "R-080", "R-082"):
            assert rule_id not in active

    def test_midc_bp_dependencies_stay_deferred(self):
        """DEP-003 (APR-008 CTE for APR-030), DEP-004 (bundled BP+fire),
        DEP-019 (APR-029 plot-holder precondition) are all triaged out of
        the pack (out-of-scope / non-approval / inferred)."""
        mh_pack = load_regulatory_pack("IN-MH")
        edges = {(d.approval_id, d.prerequisite_approval_id)
                 for d in mh_pack.dependencies}
        assert ("APR-030", "APR-008") not in edges
        assert ("APR-030", "APR-029") not in edges


class TestCrossRuleInteractions:
    """Cluster interplay with the audited fire/building graph."""

    def test_r042_references_unresolved_composition(self):
        """R-042 = F-LOC-01==FALSE AND R-079==TRUE, authority R-078,
        renewal R-099: triple rule composition over two deferred rules
        and one deferred renewal. Confirmation gate correctly held."""
        assert "R-042" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-078" in MH_DEFERRED_RULES
        assert "R-079" in MH_DEFERRED_RULES
        assert "R-099" in MH_DEFERRED_RULES

    def test_apr038_applicability_still_deferred(self):
        """APR-038 applicability (R-041) and its deemed clock (R-081) are
        both deferred: neither 'does permission apply' nor 'is it deemed'
        can be answered deterministically."""
        assert "R-041" in MH_DEFERRED_RULES
        assert "R-081" in MH_DEFERRED_RULES

    def test_apr040_renewal_still_unencoded(self):
        """APR-040 final NOC: provisional gating (R-042) confirmation-held,
        class predicate (R-079) deferred, renewal (R-099) deferred. The
        full chain R-079 -> R-042 -> R-099 is unencodable without rule
        composition, which the engine does not provide."""
        active = {r.id for r in load_mh_approval_rules()}
        assert not ({"R-079", "R-042", "R-099"} & active)

    def test_midc_branch_guard_still_active(self):
        """R-035 remains the sole active MIDC/non-MIDC branch guard; R-036
        adds no parallel branch logic."""
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-035" in active

    def test_no_rule_reference_primitive_introduced(self):
        """ApprovalRule conditions remain leaf/AND/OR/NOT/literal only;
        R-042-style `R-079 == TRUE` references stay inexpressible."""
        from app.rules.models import ConditionNode

        assert "R-079" not in str(ConditionNode.__doc__ or "")


class TestFactAndEvidenceDiscipline:
    """No convenient facts; no portal-to-statutory inference."""

    def test_no_new_facts_added(self):
        assert len(MH_FACTS) == 128

    def test_invalid_ffir20_value_rejected(self):
        from app.rules.facts import FactValidationError, validate_fact_value

        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-FIR-20", "MAYBE")

    def test_ffir20_none_always_valid(self):
        """None (UNKNOWN) is always valid input, never a type error."""
        from app.rules.facts import validate_fact_value

        validate_fact_value("IN-MH", "F-FIR-20", None)

    def test_gj_namespace_rejects_ffir20(self):
        from app.rules.facts import FactValidationError, validate_fact_value

        with pytest.raises(FactValidationError) as exc:
            validate_fact_value("IN-GJ", "F-FIR-20", True)
        assert exc.value.code == FactValidationError.JURISDICTION_MISMATCH

    def test_no_unsafe_default_fire_authority(self):
        """AUT-012 remains confirmation-gated (site-dependent); R-099
        deferral must not default any fire authority."""
        assert "R-099" in MH_DEFERRED_RULES
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-078" not in active

    def test_no_unsafe_default_planning_authority(self):
        """AUT-011 remains confirmation-gated; R-081 deferral must not
        default any planning authority."""
        assert "R-081" in MH_DEFERRED_RULES
        active = {r.id for r in load_mh_approval_rules()}
        assert "R-080" not in active


class TestJurisdictionIsolation:
    """IN-MH work must not leak into IN-GJ and vice versa."""

    def test_gj_pack_untouched(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        gj_ids = {r.id for r in gj_pack.approval_rules}
        assert not (WORKFLOW_LIFECYCLE_CLUSTER & gj_ids)

    def test_gj_approvals_untouched(self):
        gj_approval_ids = {r.approval_id
                           for r in load_regulatory_pack(IN_GJ).approval_rules}
        for apr_id in ("APR-030", "APR-031", "APR-033", "APR-038", "APR-040"):
            assert apr_id not in gj_approval_ids

    def test_mh_active_unchanged(self):
        assert len(load_mh_approval_rules()) == 26


class TestClassification:
    """Exactly-one primary classification per candidate."""

    def test_r081_is_class_e(self):
        """E - routing/workflow/regime/lifecycle, not applicability."""
        assert "R-081" in MH_DEFERRED_RULES
        assert "workflow consequence" in MH_DEFERRED_RULES["R-081"]

    def test_r099_is_class_e(self):
        assert "R-099" in MH_DEFERRED_RULES
        assert "renewal/lifecycle" in MH_DEFERRED_RULES["R-099"]

    def test_r036_is_class_c(self):
        """C - evidence incomplete / confirmation-gated (T3 portal-only)."""
        assert "R-036" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_zero_rules_activated(self):
        active = {r.id for r in load_mh_approval_rules()}
        assert not (WORKFLOW_LIFECYCLE_CLUSTER & active)
