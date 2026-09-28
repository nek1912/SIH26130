"""Maharashtra v5 batch-1 + batch-2 approval rules (IMPLEMENTATION_SAFE only).

Transcription of ``rule_register_v5.csv`` rows whose
``implementation_status`` is IMPLEMENTATION_SAFE AND whose condition
uses only currently supported primitives (boolean/numeric/enum
comparisons, AND/OR/NOT). No rule text, condition, source, date,
authority, or approval code is invented: every builder cites the v5
record it transcribes. Batch 2 adds the boiler-lifecycle rules
R-073/R-086/R-087; rules whose conditions reference facts the
registry does not carry (R-075, R-088, R-100..R-104) stay deferred
with reasons instead of being partially encoded.

Classification sets below are transcribed from the same register
(76 safe / 26 requires-confirmation / 3 do-not-implement) plus the
machine summary's UNKNOWN rules (R-015, R-052, R-074). The loader
asserts every encoded rule is safe and none is held/excluded —
fail-closed against accidental activation.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalRule,
    NotNode,
    OrNode,
    SourceRef,
)

MH_IMPLEMENTATION_SAFE_RULE_IDS: frozenset[str] = frozenset({
    "R-001", "R-002", "R-003", "R-004", "R-007", "R-008", "R-009",
    "R-011", "R-012", "R-013", "R-014", "R-015", "R-017", "R-018",
    "R-019", "R-020", "R-021", "R-024", "R-026", "R-027", "R-028",
    "R-030", "R-031", "R-032", "R-033", "R-035", "R-041", "R-043",
    "R-044", "R-045", "R-046", "R-047", "R-050", "R-054", "R-055",
    "R-056", "R-059", "R-060", "R-061", "R-062", "R-064", "R-065",
    "R-066", "R-067", "R-070", "R-071", "R-072", "R-073", "R-075",
    "R-076", "R-077", "R-078", "R-079", "R-080", "R-081", "R-082",
    "R-083", "R-084", "R-085", "R-086", "R-087", "R-088", "R-089",
    "R-091", "R-092", "R-093", "R-094", "R-095", "R-096", "R-099",
    "R-100", "R-101", "R-102", "R-103", "R-104", "R-105",
})

MH_REQUIRES_CONFIRMATION_RULE_IDS: frozenset[str] = frozenset({
    "R-005", "R-006", "R-010", "R-022", "R-023", "R-025", "R-034",
    "R-036", "R-037", "R-038", "R-039", "R-040", "R-042", "R-048",
    "R-049", "R-051", "R-052", "R-053", "R-057", "R-063", "R-068",
    "R-069", "R-074", "R-090", "R-097", "R-098",
})

MH_DO_NOT_IMPLEMENT_RULE_IDS: frozenset[str] = frozenset({
    "R-016", "R-029", "R-058",
})

# UNKNOWN rules per the v5 machine summary. R-015 is a safe
# guard-rule whose correct implementation emits UNKNOWN (needs the
# cardinality-guard construct); R-052/R-074 are UNKNOWN status.
MH_UNKNOWN_RULE_IDS: frozenset[str] = frozenset({
    "R-015", "R-052", "R-074",
})

# Batch-1 deferrals among otherwise-safe candidates (exact reasons in
# the Phase 3 report; none of these enters the pack).
# Batch-2 additions: rules whose applicability conditions reference
# facts the registry does not carry (or primitives the engine does
# not support). Encoding a subset (e.g. gas-only R-103) would
# over-apply against the documented edge tests, so they stay out and
# _encode() refuses them fail-closed.
MH_DEFERRED_RULES: dict[str, str] = {
    "R-001": "note forbids auto-FALSE on FORMULATION_ONLY; needs "
             "non-falsing set-membership",
    "R-031": "s.4-compliance clause has no registry fact; encoding "
             "class+qty alone would over-apply the exemption",
    "R-045": "cross-rule exemption refs (R-043/R-044) plus OE block; "
             "needs rule composition",
    "R-047": "LICENSEE := F-LOC-08 is authority routing with no "
             "applicability predicate",
    "R-050": "package-marking conjunct has no registry fact",
    "R-064": "condition text truncated in register; UNK-033 open",
    "R-065": "schedule-quantity clauses need list quantifiers",
    "R-066": "Schedule A membership needs a table lookup",
    "R-027": "contractor worker-count fact not in registry "
             "(F-LAB-03 mapping would be guessing); applicant is "
             "principal employer, not contractor",
    "R-075": "EC grant-date fact absent from registry; DATE "
             "arithmetic unsupported by condition primitives",
    "R-088": "accident/move/alteration/direction/prohibition event "
             "facts absent; date comparison unsupported — partial "
             "encoding would over-apply",
    "R-100": "licence-held input fact absent (SSC-01: APPLIES if unit "
             "holds such a Petroleum licence)",
    "R-101": "licence-held input fact absent (SSC-02: APPLIES if unit "
             "holds Form E/F/G)",
    "R-102": "licence-held input fact absent (SSC-03: APPLIES if unit "
             "holds LS-1A/LS-1B)",
    "R-103": "new-licence + application-date facts absent; gas-only "
             "encoding would over-apply against ET-v5-12",
    "R-104": "licence-held/purpose/filling-plant facts absent "
             "(GCR r.48 sale-vs-own-use + Form G branches)",
    "R-060": "requires existential quantifier (EXISTS) unsupported by "
             "condition primitives",
    "R-061": "requires 500m multi-installation aggregation unsupported "
             "by condition primitives",
    "R-085": "EC_REQUIRED precondition is not represented in the fact "
             "registry; no EC fact or rule-composition primitive exists",
    "R-091": "implemented partially via derive_mah_status() for F-PRC-03; "
             "direct ApprovalRule deferred due to unselected M2 external "
             "identity service and unconfirmed CON-021 thresholds",
    "R-041": "construction fact absent from registry; authority R-080 and "
             "DCR R-082 require cross-rule composition; dual approval target "
             "APR-038/041",
    "R-078": "authority routing expression computing FIRE_AUTHORITY string; "
             "no applicability predicate (mirrors R-047)",
    "R-079": "Schedule-I building class predicate requires composition with "
             "non-MIDC guard F-LOC-01==False and fire authority R-078 under R-042; "
             "standalone encoding under APR-039 would over-apply to MIDC estates "
             "(mirrors R-031/R-103)",
    "R-080": "authority routing expression computing BP_AUTHORITY string; "
             "no applicability predicate (mirrors R-047)",
    "R-082": "regulation regime selector (UDCPR vs own DCR), not an approval "
             "applicability predicate; encoding under APR-038 would falsely "
             "negate building permission in excluded jurisdictions",
    "R-003": "Category determination (CAT_BASE := A | B), not an approval "
             "applicability predicate; both Cat A and B require Prior EC "
             "(APR-001); encoding as an approval rule would falsely negate "
             "EC for Category B units; requires cross-rule composition with R-002",
    "R-004": "General Condition category escalation rule modifying appraisal "
             "authority, not an approval applicability predicate; requires "
             "cross-rule composition with R-003 and existential sub-fact "
             "evaluation over F-LOC-07",
    "R-008": "meta-rule declaring General Condition category escalation inoperative "
             "for Item 8(a); not an independent approval applicability predicate; "
             "encoding under APR-003 would contradict R-007",
    "R-013": "requires rule composition with R-014 sector lookup and unmodeled "
             "fact MPCB_CATEGORY; standalone encoding cannot evaluate against "
             "F-MPCB-01 codes without lookup engine capability; multi-code "
             "cardinality guard R-015 emits UNKNOWN",
    "R-014": "sector classification lookup function (operator LOOKUP), not an "
             "approval applicability predicate; full sector table not digitized; "
             "multi-activity cardinality guard R-015 emits UNKNOWN",
    "R-019": "MSIHC site notification (r.7) requires existential quantifier "
             "(EXISTS c:) over F-HAZ-01, multi-schedule evaluation (Sch 3 col 3 "
             "vs Sch 2 col 3), aggregation across storage units, and dynamic "
             "authority routing per Sch 5 unsupported by condition primitives",
    "R-020": "MSIHC safety report (r.10-12) requires existential quantifier "
             "(EXISTS c:) over F-HAZ-01, column 4 threshold lookup, and "
             "aggregation unsupported by condition primitives; unconfirmed "
             "col 4 values (UR-01); targets APR-012 with different lifecycle/frequency",
    "R-022": "statutory definition of factory under OSH Code s.2(1)(w), not an "
             "approval applicability predicate; dual target APR-015 (plan approval) "
             "and APR-016 (licence); sub-threshold (<20/<40) cannot safely evaluate "
             "to FALSE due to saved s.85 hazardous-process notifications (ET-017); "
             "requires official confirmation (UNK-029)",
    "R-023": "licence category / fee schedule selector (DISH_LICENCE_CATEGORY := "
             "'MAH/HAZARDOUS' | 'OTHER'), not an approval applicability predicate; "
             "outputs string classification; 'hazardous process' criterion unencoded; "
             "requires official confirmation",
    "R-090": "BOCW registration under OSH Code s.2(1)(h) contains statutory "
             "exclusion for construction related to a factory; whether new factory "
             "construction falls within exclusion is unresolved in MH (ET-126 "
             "requires UNKNOWN); exception fact unmodeled; requires official confirmation",
    "R-038": "utility service request (MIDC-RTS-01) rather than statutory "
             "approval applicability predicate; dual target APR-034 (water) "
             "and APR-035 (drainage) conflated with divergent conditions; "
             "requires set-membership on F-WAT-01 enum-set; statutory regulations "
             "unread (UR-19 open; T3 portal evidence only SRC-043); "
             "requires official confirmation",
    "R-048": "state-notified self-certification voltage threshold F-ELE-02 "
             "is unestablished in Maharashtra (UNK-005 open; central 11 kV "
             "cannot be applied per ET-050/ET-101); RTS 2018 notification (SRC-041) "
             "cites superseded CEA 2010 regulations; conflates approval applicability "
             "with inspection workflow and dynamic officer hierarchy routing; "
             "requires official confirmation",
    "R-052": "no statutory source cited (source_id: -); classified UNKNOWN in "
             "v5 machine summary and register; estate-level CETP existence, "
             "hydraulic capacity, and effluent acceptance are unmodeled site-specific "
             "facts (UNK-011 open); contractual/infrastructure arrangement or "
             "consent condition rather than independent statutory approval "
             "applicability predicate",
    "R-053": "statutory legal basis explicitly unresearched across all v5 datasets "
             "('Not researched' in rules/approvals/authorities); backed solely by "
             "T3 MAITRI portal list (SRC-070); competent WRD authority routing "
             "unverified (UR-17 open); distinguishes river/surface source without "
             "authoritative basin GIS layer; requires official confirmation",
    "R-097": "statutory prohibition condition (CND-024) under MH Groundwater Act "
             "2009 s.8(1), not an approval application; complete village list for "
             "80 notified watersheds unencoded in GIS layer (UR-15 open; partial "
             "machine parse); post-2015 order currency unconfirmed; unconfirmed "
             "location must fail closed to INSUFFICIENT_DATA per ET-v5-24, "
             "never DOES_NOT_APPLY; requires official confirmation",
    "R-032": "Petroleum licence form and authority routing expression "
             "(PET_FORM := 'XII (DA)' | 'XIII (DA)' | 'XVI (PESO)' | 'XV (PESO)'), "
             "not an approval applicability predicate; multiple classes combination rules "
             "unmodeled (SOP); cannot be expressed by ConditionNode boolean primitives",
    "R-033": "Gas cylinder storage licence exemption (GCR_EXEMPT under r.44) requires "
             "list iteration and per-group quantifiers over F-GAS-01; LPG exemption "
             "under r.44(c) is legally ambiguous (UNK-016, PT-05); gas classification "
             "unmodeled (UNK-039); unread GCR amendments remain (UR-10)",
    "R-034": "SMPV(U) Rules 2016 r.2 definition and r.45 licence trigger require "
             "existential quantifier (EXISTS) over F-PV-01 list and process vessel "
             "exclusion filtering (r.3 16-hr feed rule); official status is "
             "REQUIRES_OFFICIAL_CONFIRMATION due to unread amendments (UR-10)",
    "R-062": "CTO validity rule under GSR 62/63 (CTO_VALIDITY := 'VALID_TILL_CANCELLED'), "
             "a lifecycle validity rule rather than an approval applicability predicate; "
             "CTO grant date fact absent from registry; Maharashtra implementation "
             "unconfirmed (UNK-032); prompt candidate Biomedical Waste is inapplicable "
             "to synthetic organic chemical manufacturing (zero BMW rules/approvals in domain)",
    "R-092": "Petroleum DA NOC under r.144 requires rule composition with R-032 "
             "(form and authority routing) which is deferred; cannot be evaluated "
             "standalone without licensing authority and form determination",
    "R-051": "AAI height clearance NOC under GSR 751(E) requires 3D GIS spatial "
             "coordinates, obstacle limitation surface (OLS) geometry, and CCZM "
             "permissible elevation grid lookup unsupported by condition primitives; "
             "unmodeled aerodrome dataset; status REQUIRES_OFFICIAL_CONFIRMATION "
             "(SRC-063/SRC-104)",
    "R-068": "bulk drug / API manufacturing licence under Drugs Rules 1945 Part VII "
             "requires official confirmation (form numbers not re-extracted; UNK-036 open; "
             "UR-11 open for MH FDA authority routing); applies only if unit manufactures "
             "statutorily defined drug under s.3(b) (F-DRG-01); status "
             "REQUIRES_OFFICIAL_CONFIRMATION (SRC-101)",
    "R-069": "explosives manufacturing licence under Explosives Rules 2008 requires "
             "expert substance classification as explosive (peso_gating note); possession "
             "thresholds not extracted (UNKNOWN for possession-only); separation-distance "
             "geometry (Sch VII) unsupported by condition primitives; status "
             "REQUIRES_OFFICIAL_CONFIRMATION (SRC-107/SRC-119)",
    "R-095": "ODS registration duty (CND-022) under ODS Rules 2000 r.8 is a compliance "
             "condition / registration obligation rather than an approval applicability predicate; "
             "producer (r.3) and seller (r.6) branches unmodeled in fact registry; "
             "post-2000 amendments unverified; status VERIFIED_CONDITIONAL (SRC-127)",
    "R-105": "planning zone permissibility (PS-02) under MRTP Act s.44 and UDCPR "
             "Reg. 1.4(iii) is a planning workflow gate, not an approval applicability predicate; "
             "never returns APPLIES/DOES_NOT_APPLY (emits CONDITIONAL AUTHORITY_SITE_DEPENDENT "
             "when 4 facts supplied, else INSUFFICIENT_DATA per ET-v5-21/22); site DP/RP "
             "zoning data unmodeled; status VERIFIED_CONDITIONAL (SRC-123/SRC-124)",
}


def _leaf(field: str, op: str, value: Any) -> ApplicabilityCondition:
    return ApplicabilityCondition(field=field, op=ApplicabilityOp(op), value=value)


def _and(*nodes: Any) -> AndNode:
    return AndNode(conditions=list(nodes))


def _or(*nodes: Any) -> OrNode:
    return OrNode(conditions=list(nodes))


def _not(node: Any) -> NotNode:
    return NotNode(condition=node)


def _refs(*pairs: tuple[str, str]) -> list[SourceRef]:
    return [
        SourceRef(source_id=source_id, citation_span=citation)
        for source_id, citation in pairs
    ]


def _encode(
    rule_id: str,
    approval_id: str,
    conditions: list[Any],
    source_refs: list[SourceRef],
    effective_from: date | None = None,
    effective_to: date | None = None,
) -> ApprovalRule:
    """Build one batch-1 rule, enforcing the safe-only boundary."""
    if rule_id in MH_DEFERRED_RULES:
        raise ValueError(f"Rule {rule_id} is deferred: {MH_DEFERRED_RULES[rule_id]}")
    if rule_id not in MH_IMPLEMENTATION_SAFE_RULE_IDS:
        raise ValueError(f"Rule {rule_id} is not IMPLEMENTATION_SAFE")
    if rule_id in MH_REQUIRES_CONFIRMATION_RULE_IDS:
        raise ValueError(f"Rule {rule_id} requires confirmation")
    if rule_id in MH_DO_NOT_IMPLEMENT_RULE_IDS:
        raise ValueError(f"Rule {rule_id} is do-not-implement")
    if rule_id in MH_UNKNOWN_RULE_IDS:
        raise ValueError(f"Rule {rule_id} is UNKNOWN")
    return ApprovalRule(
        id=rule_id,
        approval_id=approval_id,
        applicability_conditions=conditions,
        source_refs=source_refs,
        version="v5",
        effective_from=effective_from,
        effective_to=effective_to,
    )


# -- R-002: small-unit exception (all three required; 25 exactly = NOT small)
def _r002() -> ApprovalRule:
    return _encode(
        "R-002", "APR-001",
        [_and(
            _leaf("F-PRC-01", "lt", 25),
            _leaf("F-PRC-02", "lt", 25),
            _leaf("F-PRC-03", "eq", False),
        )],
        _refs(("SRC-001",
               "Item 5(f) column 5 (inserted by S.O.1223(E) 27-03-2020; "
               "footnote 76)")),
        effective_from=date(2014, 6, 25),
    )


# -- R-007: EC 8(a) built-up range [20000, 150000) m2
def _r007() -> ApprovalRule:
    return _encode(
        "R-007", "APR-003",
        [_and(
            _leaf("F-BLD-01", "gte", 20000),
            _leaf("F-BLD-01", "lt", 150000),
        )],
        _refs(("SRC-001", "Item 8(a)"), ("SRC-179", "Item 8(a)")),
        effective_from=date(2006, 9, 14),
    )


# -- R-009: EC 8(b) area OR built-up (either TRUE wins even if other UNKNOWN)
def _r009() -> ApprovalRule:
    return _encode(
        "R-009", "APR-004",
        [_or(
            _leaf("F-BLD-03", "gte", 50),
            _leaf("F-BLD-01", "gte", 150000),
        )],
        _refs(("SRC-001", "Item 8(b)")),
        effective_from=date(2006, 9, 14),
    )


# -- R-011: 5(b) pesticide-technical product set
def _r011() -> ApprovalRule:
    return _encode(
        "R-011", "APR-006",
        [_leaf("F-PRD-02", "in", ["PESTICIDE_TECHNICAL"])],
        _refs(("SRC-001", "Item 5(b)")),
        effective_from=date(2006, 9, 14),
    )


# -- R-012: 5(h) integrated-paint product set
def _r012() -> ApprovalRule:
    return _encode(
        "R-012", "APR-007",
        [_leaf("F-PRD-02", "in", ["PAINT_INTEGRATED"])],
        _refs(("SRC-001", "Item 5(h)")),
        effective_from=date(2006, 9, 14),
    )


# -- R-018: HW authorisation on generation
def _r018() -> ApprovalRule:
    return _encode(
        "R-018", "APR-010",
        [_leaf("F-HW-01", "eq", True)],
        _refs(("SRC-013", "Rule 6(1)")),
        effective_from=date(2016, 4, 4),
    )


# -- R-026: CLRA principal-employer registration (threshold plus the
# -- s.45(2) intermittent/casual exception, F-LAB-09 == FALSE; missing
# -- exception fact fails closed)
def _r026() -> ApprovalRule:
    return _encode(
        "R-026", "APR-019",
        [_and(
            _leaf("F-LAB-03", "gte", 50),
            _leaf("F-LAB-09", "eq", False),
        )],
        _refs(("SRC-081", "OSH Code 2020 s.45(2)"),
               ("SRC-026", "OSH Code 2020 s.45(2)")),
        effective_from=date(2025, 11, 21),
    )


# -- R-028: Boilers Act 2025 s.2(c) definition with dual NOT exclusions;
# -- three-valued propagation yields UNKNOWN exactly when an unknown
# -- operand could flip the result
def _r028() -> ApprovalRule:
    return _encode(
        "R-028", "APR-023",
        [_and(
            _leaf("F-BLR-04", "eq", True),
            _leaf("F-BLR-01", "gte", 25),
            _not(_and(
                _leaf("F-BLR-05", "lt", 1),
                _leaf("F-BLR-02", "lt", 1),
            )),
            _not(_leaf("F-BLR-03", "lt", 100)),
        )],
        _refs(("SRC-034", "Boilers Act 2025 s.2(c)")),
        effective_from=date(2025, 5, 1),
    )


# -- R-030: petroleum Class-B exemption triple (effective 2002 is
# -- YEAR_ONLY: window omitted rather than inventing month/day precision)
def _r030() -> ApprovalRule:
    return _encode(
        "R-030", "APR-026",
        [_and(
            _leaf("F-PET-01", "eq", "B"),
            _leaf("F-PET-02", "lte", 2500),
            _leaf("F-PET-04", "lte", 1000),
        )],
        _refs(("SRC-092", "Petroleum Act 1934 s.7(i)"),
               ("SRC-017", "PESO SOP exemptions table")),
    )


# -- R-035: MIDC branch guard
def _r035() -> ApprovalRule:
    return _encode(
        "R-035", "APR-029",
        [_leaf("F-LOC-01", "eq", True)],
        _refs(("SRC-043", "-")),
    )


# -- R-043: CGWA MSE exemption (F-INC-01 derived; missing fails closed)
def _r043() -> ApprovalRule:
    return _encode(
        "R-043", "APR-043",
        [_and(
            _leaf("F-INC-01", "in", ["MICRO", "SMALL"]),
            _leaf("F-WAT-05", "lt", 10),
        )],
        _refs(("SRC-052", "Exemptions list")),
        effective_from=date(2020, 9, 24),
    )


# -- R-044: CGWA domestic exemption
def _r044() -> ApprovalRule:
    return _encode(
        "R-044", "APR-043",
        [_and(
            _leaf("F-WAT-06", "eq", "DOMESTIC_ONLY"),
            _leaf("F-WAT-05", "lte", 5),
        )],
        _refs(("SRC-052", "Exemptions list")),
        effective_from=date(2020, 9, 24),
    )


# -- R-046: dewatering NOC trigger
def _r046() -> ApprovalRule:
    return _encode(
        "R-046", "APR-044",
        [_leaf("F-WAT-08", "eq", True)],
        _refs(("SRC-052", "-")),
        effective_from=date(2020, 9, 24),
    )


# -- R-056: HW utilisation r.9 (effective 2016 is YEAR_ONLY: omitted)
def _r056() -> ApprovalRule:
    return _encode(
        "R-056", "APR-054",
        [_leaf("F-HW-03", "eq", True)],
        _refs(("SRC-013", "Rule 9")),
    )


# -- R-067: insecticide manufacture (effective 1968 YEAR_ONLY: omitted)
def _r067() -> ApprovalRule:
    return _encode(
        "R-067", "APR-055",
        [_leaf("F-INS-01", "eq", True)],
        _refs(("SRC-100", "s.13")),
    )


# -- R-070: safety-officer headcount bands by hazardous-process limb
def _r070() -> ApprovalRule:
    return _encode(
        "R-070", "CMP-018",
        [_or(
            _and(
                _leaf("F-LAB-07", "eq", False),
                _leaf("F-LAB-01", "gte", 500),
            ),
            _and(
                _leaf("F-LAB-07", "eq", True),
                _leaf("F-LAB-01", "gte", 250),
            ),
        )],
        _refs(("SRC-081", "s.22(2)")),
        effective_from=date(2025, 11, 21),
    )


# -- R-089: ISMW headcount (12-month window is measurement guidance)
def _r089() -> ApprovalRule:
    return _encode(
        "R-089", "APR-022",
        [_leaf("F-LAB-08", "gte", 10)],
        _refs(("SRC-081", "s.59")),
        effective_from=date(2025, 11, 21),
    )


# -- R-093: CMVR consignor duties trigger (effective 1993 YEAR_ONLY)
def _r093() -> ApprovalRule:
    return _encode(
        "R-093", "CMP-024",
        [_leaf("F-TRN-01", "eq", True)],
        _refs(("SRC-102", "r.131")),
    )


# -- R-094: bulk e-waste handover threshold
def _r094() -> ApprovalRule:
    return _encode(
        "R-094", "CMP-025",
        [_leaf("F-EEE-01", "gte", 1000)],
        _refs(("SRC-135", "r.3; r.8")),
        effective_from=date(2023, 4, 1),
    )


# -- R-073: Boiler Operation Engineer requirement (operating
# -- condition, not registration): total heating surface strictly
# -- above 1000 m2 (ET-096: 1000 exactly is NOT above)
def _r073() -> ApprovalRule:
    return _encode(
        "R-073", "APR-023",
        [_leaf("F-BLR-06", "gt", 1000)],
        _refs(("SRC-085", "BOE rule")),
        effective_from=date(2025, 9, 23),
    )


# -- R-086: boiler registration Trigger: the R-028 boiler-definition
# -- tree restated exactly (no rule-reference primitive exists) AND
# -- the unit is not registered. Kept in sync with _r028 by the
# -- mirror test in test_mh_pack_batch2.py; any drift fails loudly.
def _r086() -> ApprovalRule:
    return _encode(
        "R-086", "APR-023",
        [_and(
            _leaf("F-BLR-04", "eq", True),
            _leaf("F-BLR-01", "gte", 25),
            _not(_and(
                _leaf("F-BLR-05", "lt", 1),
                _leaf("F-BLR-02", "lt", 1),
            )),
            _not(_leaf("F-BLR-03", "lt", 100)),
            _leaf("F-BLR-07", "eq", "NOT_REGISTERED"),
        )],
        _refs(("SRC-034", "s.12(1)-(6)")),
        effective_from=date(2025, 5, 1),
    )


# -- R-087: 1923-Act-registered boilers are deemed registered
# -- (transitional status, s.45(2)(f)); certificate continues per
# -- s.45(2)(g) — the date itself is tracked in F-BLR-08, not decided
def _r087() -> ApprovalRule:
    return _encode(
        "R-087", "APR-023",
        [_leaf("F-BLR-07", "eq", "REGISTERED_UNDER_1923_ACT")],
        _refs(("SRC-034", "s.45(2)")),
        effective_from=date(2025, 5, 1),
    )


# -- R-077: CGWA NOC for groundwater abstraction (over-exploited assessment unit)
# -- CASE: F-GW-01 == 'OVER_EXPLOITED' AND (
# --   (F-EXP-01 == False AND F-INC-01 NOT IN {MICRO, SMALL, MEDIUM})
# --   OR F-EXP-01 == True
# -- )
def _r077() -> ApprovalRule:
    return _encode(
        "R-077", "APR-043",
        [_and(
            _leaf("F-GW-01", "eq", "OVER_EXPLOITED"),
            _or(
                _and(
                    _leaf("F-EXP-01", "eq", False),
                    _not(_leaf("F-INC-01", "in", ["MICRO", "SMALL", "MEDIUM"])),
                ),
                _leaf("F-EXP-01", "eq", True),
            ),
        )],
        _refs(("SRC-052", "para 4.1")),
        effective_from=date(2020, 9, 24),
    )


# -- R-083: Coastal Regulation Zone (CRZ Notification 2019)
# -- CRZ := F-GEO-01 IN {CRZ-I, CRZ-II, CRZ-III, CRZ-IV}
def _r083() -> ApprovalRule:
    return _encode(
        "R-083", "LOC-CRZ",
        [_leaf("F-GEO-01", "in", ["CRZ-I", "CRZ-II", "CRZ-III", "CRZ-IV"])],
        _refs(("SRC-112", "paras 4(i), 4(ii), 4(xi)")),
        effective_from=date(2019, 1, 18),
    )


# -- R-084: Forest land involved (Van Adhiniyam 1980 / Rules 2023)
# -- FOREST := F-LOC-15 == True
def _r084() -> ApprovalRule:
    return _encode(
        "R-084", "LOC-FOREST",
        [_leaf("F-LOC-15", "eq", True)],
        _refs(("SRC-113", "r.9, r.10")),
        effective_from=date(2023, 12, 1),
    )


# -- R-096: Hazardous waste authorisation Schedule II characteristic test
# -- HW_SCH2_TEST := F-HW-04 contains matching characteristics
def _r096() -> ApprovalRule:
    return _encode(
        "R-096", "APR-010",
        [_leaf("F-HW-04", "in", [
            "CLASS_A", "CLASS_B", "CLASS_C1", "CLASS_C2", "CLASS_C3",
            "CLASS_A_TCLP", "CLASS_C1_FLAMMABLE", "CLASS_C2_CORROSIVE",
            "CLASS_C3_REACTIVE", "HAZARDOUS", "MEETS_SCHEDULE_II",
        ])],
        _refs(("SRC-120", "Schedule II Class A/B/C")),
        effective_from=date(2016, 4, 4),
    )


_MH_RULE_BUILDERS = (
    _r002, _r007, _r009, _r011, _r012, _r018, _r026, _r028, _r030,
    _r035, _r043, _r044, _r046, _r056, _r067, _r070, _r089, _r093,
    _r094, _r073, _r086, _r087,
    _r077, _r083, _r084, _r096,
)

MH_INCLUDED_RULE_IDS: frozenset[str] = frozenset({
    "R-002", "R-007", "R-009", "R-011", "R-012", "R-018", "R-026",
    "R-028", "R-030", "R-035", "R-043", "R-044", "R-046", "R-056",
    "R-067", "R-070", "R-089", "R-093", "R-094",
    "R-073", "R-086", "R-087",
    "R-077", "R-083", "R-084", "R-096",
})


def load_mh_approval_rules() -> list[ApprovalRule]:
    """Return the 26 batch-1 + batch-2 + location-cluster MH rules (safe-only, fail-closed)."""
    rules = [build() for build in _MH_RULE_BUILDERS]
    ids = [r.id for r in rules]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate MH rule IDs in batch 1")
    if set(ids) != set(MH_INCLUDED_RULE_IDS):
        raise ValueError("MH batch contents drifted from MH_INCLUDED_RULE_IDS")
    return rules


def load_mh_approval_authorities() -> dict[str, str]:
    """Approval/display authority strings transcribed from v5 records."""
    return {
        "APR-001": "AUT-001 (Cat A) / AUT-002 (Cat B)",
        "APR-003": "AUT-002",
        "APR-004": "AUT-002",
        "APR-006": "AUT-001",
        "APR-007": "AUT-002",
        "APR-010": "AUT-003",
        "APR-019": "AUT-006",
        "APR-022": "AUT-006",
        "APR-023": "AUT-007",
        "APR-026": "AUT-008 / AUT-009",
        "APR-029": "AUT-010",
        "APR-043": "AUT-013",
        "APR-044": "AUT-013",
        "APR-054": "AUT-003 (CPCB approval if no SOP)",
        "APR-055": "Licensing officer (State; identity in MH UNKNOWN)",
        "CMP-018": "",
        "CMP-024": "",
        "CMP-025": "",
        "LOC-CRZ": "MCZMA / MoEFCC",
        "LOC-FOREST": "MoEFCC / Regional Office / State Forest Dept",
    }
