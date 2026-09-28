"""G0-R5 evidence gap register — 12 unresolved regulatory facts.

Machine-readable transcription of Gap-Closure Pass G0-R5 Final (cut-off
25.09.2026). Records evidence state only; creates no applicability rules
and asserts no thresholds, authorities, SLAs, exemptions, or legal
conclusions. Values below repeat G0-R5 wording; nothing is upgraded.
"""
from __future__ import annotations

from datetime import date

from app.regulatory.evidence import EvidenceRecord, EvidenceStatus


def load_evidence_gaps() -> list[EvidenceRecord]:
    """Return the 12 unresolved G0-R5 evidence records."""
    return [
        EvidenceRecord(
            evidence_id="G0R5-OSH-01",
            subject="OSH Rules 2025 Extra 87 / Extra 163 / later amendments / authority mapping",
            status=EvidenceStatus.PARTIAL,
            verified_scope=(
                "G0-R4 already encoded content stands. Private copies seen only: "
                "Extra 87 (alp.consulting, lawrbit); Extra 56 GR/2026/48 s.46 "
                "(simpliance). No official Gujarat host read."
            ),
            unresolved_question=(
                "Official gazette copy of Extra 87 not read; final notification "
                "for Extra 163 (13.12.2025 draft, saralweb private host) not found; "
                "official amendment list to 25.09.2026 not found; no "
                "establishment-specific Chief Inspector mapping."
            ),
            source_reference=(
                "G0-R5 §1 rows A1-A4; egazette.gujarat.gov.in "
                "unreachable (DNS failure)"
            ),
            effective_date=None,
            notes=(
                "Only what G0-R4 already encoded; add nothing new. "
                "No establishment-level authority inference."
            ),
            flags=["do_not_encode", "official_gazette_unread", "no_authority_inference"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-FIRE-R25",
            subject="Fire GH/V/80 of 2024 (24.06.2024) Rule 25 amendment text",
            status=EvidenceStatus.PARTIAL,
            verified_scope=(
                "Secondary summaries (complinity, ksandk) cite an egazette.gujarat "
                "link; text not on the official fire portal."
            ),
            unresolved_question="Official text of amended Rule 25 not read.",
            source_reference=(
                "G0-R5 §1 row D1; egazette.gujarat.gov.in docid 202406242013100447 unreachable"
            ),
            effective_date=None,
            notes="Renewal procedure summarised by secondary sources is not verified.",
            flags=["do_not_encode_rule25_text"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-FIRE-RENEWAL",
            subject=(
                "Fire Safety Certificate renewal period: Form B13.3 (2 years) "
                "vs FSCoP FAQ (3 years)"
            ),
            status=EvidenceStatus.CONFLICTING,
            verified_scope=(
                "Form B13.3 wording VERIFIED from 2nd Amendment Rules 2023, GH/V/245 "
                "of 2023 (14.12.2023) on the official fire portal: Form B 13.3 "
                "'Fire Safety Certificate Renewal (See rule 25)', 'renewed for a "
                "period of two (2) years'. The FSCoP FAQ mentions 3 years."
            ),
            unresolved_question=(
                "How Form B13.3 relates to the Rule 25 text (D1); which renewal "
                "period governs. Form wording only; no renewal rule encoded."
            ),
            source_reference="https://gujfiresafetycop.in/uploads/GFPLSM.pdf ; G0-R5 §§2.D, 3, 6",
            effective_date=None,
            notes="Conflict recorded without resolution: 2 years (Form B13.3) vs 3 years (FAQ).",
            flags=["conflict_2y_vs_3y", "form_wording_only", "rule25_unverified"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-EODB-2026",
            subject="Gujarat Ease of Doing Business Act 2026 assent/commencement/effect",
            status=EvidenceStatus.NOT_ESTABLISHED,
            verified_scope=(
                "News only: passed by the Assembly 11.09.2026; "
                "Gazette Part IV No.37 (10.09.2026) = NIL."
            ),
            unresolved_question="Assent, Act number, commencement, effectiveness by 25.09.2026.",
            source_reference="G0-R5 §1 row D3",
            effective_date=None,
            notes="Do not encode.",
            flags=["do_not_encode"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-ELEC-VOLTAGE",
            subject="Gujarat notified voltage under CEA Safety Regulations 2023",
            status=EvidenceStatus.NOT_ESTABLISHED,
            verified_scope=(
                "CEA 'notified voltage' PDF is a central Gazette of India item, "
                "not Gujarat's. No Gujarat instrument found on live or archived "
                "ceiced pages."
            ),
            unresolved_question="Gujarat notification (value, authority, date).",
            source_reference=(
                "G0-R5 §1 row E; CEA central PDF "
                "https://cea.nic.in/wp-content/uploads/page/2020/07/"
                "notified_voltage_self%20certification.pdf "
                "(read, not Gujarat)"
            ),
            effective_date=None,
            notes="Do not use the CEA default or another state's value.",
            flags=["do_not_encode", "do_not_use_cea_default", "do_not_use_other_state_value"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-CGDCR-CONSOL",
            subject="Current consolidated CGDCR",
            status=EvidenceStatus.NOT_ESTABLISHED,
            verified_scope=(
                "Proposals and s.122 orders found (GH/V/67 of 2022, GH/V/125 of 2022, "
                "GH/V/166 of 2026 as PROPOSAL + s.122 order). Separately verified: "
                "final Sr.22 only (GH/V/104 of 2021, 18.11.2021) and Chapter 12 Tall "
                "Buildings (GH/V/46 of 2021, 27.05.2021)."
            ),
            unresolved_question=(
                "Official consolidated text; final sanctions for the 2022/2023/2024 "
                "proposals; 28.07.2026 proposal finality; other serials of the "
                "2020 proposal."
            ),
            source_reference="G0-R5 §1 rows F1, F2, F7",
            effective_date=None,
            notes=(
                "Proposal is not final. GH/V/166 of 2026 status = "
                "PROPOSAL + s.122 order, not final."
            ),
            flags=["do_not_encode", "proposal_is_not_final"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-GIDC-GDCR",
            subject="Separate GIDC GDCR text",
            status=EvidenceStatus.NOT_ESTABLISHED,
            verified_scope=(
                "GIDC/ATP/128, 22.12.2017 verified: CGDCR-2017 applies in all GIDC "
                "estates (D-9). Only the applicability circular verified."
            ),
            unresolved_question=(
                "A separate GIDC GDCR text not found (the GIDC 'GDCR' link points "
                "to the GIDC Act PDF)."
            ),
            source_reference=(
                "https://gidc.gujarat.gov.in/pdf/Circular/Circular-%20ATP%20dtd%2022.12.2017.pdf "
                "; G0-R5 §1 row F6"
            ),
            effective_date=None,
            notes="Only the 22.12.2017 applicability circular may be cited; no GDCR text encoded.",
            flags=["do_not_encode", "applicability_circular_only"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-GW-JURISDICTION",
            subject="Groundwater post-29-03-2023 current jurisdiction (Gujarat under CGWA)",
            status=EvidenceStatus.PARTIAL,
            verified_scope=(
                "VERIFIED as of 29.03.2023: S.O.1509(E) Annexure VIII lists "
                "'7. Gujarat' among States/UTs regulated by CGWA."
            ),
            unresolved_question=(
                "Dated current portal list (the Annexure VIII list is stated to be "
                "'dynamic' and updated on the web portal; the CGWB regulation page "
                "is undated)."
            ),
            source_reference=(
                "https://cgwb.gov.in/sites/default/files/2023-05/"
                "new-guideline_for-ground-water-regulation.pdf "
                "; G0-R5 §1 row G3"
            ),
            effective_date=date(2023, 3, 29),
            notes=(
                "Date-bound: Gujarat under CGWA as of 29.03.2023; "
                "current-date jurisdiction PARTIAL."
            ),
            flags=["date_bound_2023-03-29", "dynamic_list"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-GW-NO-EXTRACTION",
            subject="No-groundwater-extraction implies no-NOC rule",
            status=EvidenceStatus.NOT_ESTABLISHED,
            verified_scope=(
                "NOC duty text VERIFIED: industries 'abstracting ground water' "
                "(S.O.3289(E) 24.09.2020, in force immediately); Para 1.0 exemptions "
                "(i)-(vii) listed across S.O.3289(E) and S.O.1509(E). No clause "
                "expressly addresses 'no extraction'."
            ),
            unresolved_question=(
                "No express no-extraction exemption found. Must not map "
                "'groundwater = false' to 'no NOC' from these texts alone."
            ),
            source_reference="G0-R5 §1 row G5, §6; S.O.3289(E); S.O.1509(E)",
            effective_date=None,
            notes=(
                "Must remain NOT_ESTABLISHED. Encode the scope words only; "
                "no 'no NOC' rule. Fail closed to INSUFFICIENT_DATA."
            ),
            flags=["must_remain_not_established", "do_not_map_false_to_no_noc", "fail_closed"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-LIFT-RULES",
            subject="Lift Rules 2001 principal text / 2014 amendment / 2013 Act commencement",
            status=EvidenceStatus.PARTIAL,
            verified_scope=(
                "VERIFIED text: 2002 Amendment Rules (Extra 169, 11.06.2002); 2007 "
                "Amendment Rules (Extra 357, 27.12.2007); Gujarat Act 13 of 2013 "
                "text (Extra 13, 10.04.2013, assented 10.04.2013). CEI lift FAQ "
                "(licence 5 years, Annexure X, 30 days) is a supporting admin page only."
            ),
            unresolved_question=(
                "Principal Lifts Rules 2001 official text not read (live 403, not "
                "archived); 2014 amendment (No.GJ/2014/15/LFT/12-2006/3524/K, "
                "05.02.2014) official text not read (private copy only); commencement "
                "notification for Act 13 of 2013 s.1(2) not found; erection, licence, "
                "inspection, renewal and authority cannot be fully reconstructed."
            ),
            source_reference=(
                "G0-R5 §1 rows H1-H5; archived ceiced PDFs; ceiced.gujarat.gov.in/lift FAQ"
            ),
            effective_date=None,
            notes=(
                "Only the Act and amendment facts above; in-force status "
                "of Act 13 of 2013 not established."
            ),
            flags=["principal_text_unread", "commencement_unknown", "faq_supporting_only"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-MSIHC-AUTHORITY",
            subject="MSIHC Schedule 5 row 4 post-OSH-Code authority mapping",
            status=EvidenceStatus.NOT_ESTABLISHED,
            verified_scope=(
                "Existing text VERIFIED: 'Chief Inspector of Factories appointed "
                "under the Factories Act, 1948' (MoEF consolidated). S.O.2882 "
                "(03.10.1994) and S.O.57(E) (19.01.2000) read; S.O.57(E) r.13 leaves "
                "row 4 unchanged."
            ),
            unresolved_question=(
                "Any post-OSH-Code amending instrument for row 4; MoEF rules page "
                "lists no post-OSH amendment."
            ),
            source_reference="https://moef.gov.in/uploads/2017/08/hsmd_met_0.pdf ; G0-R5 §1 row C5",
            effective_date=None,
            notes="Existing text only; no substitution.",
            flags=["do_not_encode", "existing_text_only", "no_substitution"],
        ),
        EvidenceRecord(
            evidence_id="G0R5-VGIP-2026",
            subject=(
                "Gujarat Industrial Policy 2026 (VGIP) parent GR / effective date / "
                "supersession / transitional provisions"
            ),
            status=EvidenceStatus.NOT_ESTABLISHED,
            verified_scope="Only scheme GRs of 08.09.2026 via secondary sources and news seen.",
            unresolved_question=(
                "Parent GR, effective date, supersession of IP 2020, transitional "
                "provisions, whether the 08.09.2026 scheme GRs are subordinate, "
                "any later parent GR."
            ),
            source_reference="G0-R5 §1 row I; ic.gujarat.gov.in unreachable",
            effective_date=None,
            notes="Do not encode.",
            flags=["do_not_encode"],
        ),
    ]


# Surfacing hints (not legal determinations): which approval codes an
# evidence gap is potentially relevant to when orchestration surfaces
# INSUFFICIENT_DATA. These hints never create applicability rules.
EVIDENCE_TO_APPROVALS: dict[str, list[str]] = {
    "G0R5-OSH-01": ["A07"],
    "G0R5-FIRE-R25": ["A06"],
    "G0R5-FIRE-RENEWAL": ["A06"],
    "G0R5-EODB-2026": [],
    "G0R5-ELEC-VOLTAGE": ["A09", "A10"],
    "G0R5-CGDCR-CONSOL": ["A01", "A14"],
    "G0R5-GIDC-GDCR": ["A01", "A02", "A03"],
    "G0R5-GW-JURISDICTION": ["A18"],
    "G0R5-GW-NO-EXTRACTION": ["A18"],
    "G0R5-LIFT-RULES": ["A15"],
    "G0R5-MSIHC-AUTHORITY": ["A12"],
    "G0R5-VGIP-2026": [],
}


def get_gaps_for_approval(approval_code: str) -> list[EvidenceRecord]:
    """Return gap records potentially relevant to an approval code.

    Hint-only helper for orchestration surfacing; not an applicability rule.
    """
    wanted = {
        eid for eid, codes in EVIDENCE_TO_APPROVALS.items() if approval_code in codes
    }
    return [g for g in load_evidence_gaps() if g.evidence_id in wanted]
