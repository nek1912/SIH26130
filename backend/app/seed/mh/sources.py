"""Maharashtra v5 batch-1 + batch-2 + location-cluster source corpus (Phase 5).

Display/citation metadata ONLY — sources explain assertions, they
never alter deterministic decisions. Twenty-two records: the exact set
referenced by the 26 batch-1 + batch-2 + location-cluster rules, 2 dependencies,
4 documents, the DOC-012 evidence record, and the 10 batch-1 SLA rows.
All remaining v5 sources are deferred to the source-pack phase.

Field mapping (documented, verbatim where v5 speaks):
- ``id`` / ``title`` / ``authority`` / ``source_type`` / ``url``:
  exact v5 ``source_id`` / ``title`` / ``issuing_authority`` /
  ``source_type`` / ``url`` (OFFICIAL_PRIMARY, OFFICIAL_PORTAL,
  CENTRAL_RULES, COURT_ORDER preserved as-is).
- ``trust_tier``: v5 ``tier`` verbatim (T1/T2/T3) — no upgrade, no
  downgrade. ``source_class`` "Official": all 13 are
  government-published (gazette/Act/ministry/portal/court).
- ``checked_date``: v5 ``accessed`` verbatim.
- ``notes``: effective/expiry dates, exact locators, final status,
  plus labeled PROVES / DOES_NOT_PROVE assertions (kept distinct).
"""
from __future__ import annotations

from app.regulatory.models import SourceRecord

MH_DEFERRED_SOURCES_NOTE = (
    "166 of 188 v5 sources deferred to the source-pack phase; "
    "only batch-1 + batch-2 + location-cluster-referenced records are loaded."
)


def _S(
    id: str,
    title: str,
    authority: str,
    source_type: str,
    url: str,
    tier: str,
    checked: str,
    effective: str,
    expiry: str,
    locators: str,
    proves: str,
    does_not_prove: str,
    status: str,
) -> SourceRecord:
    notes = (
        f"Effective: {effective}; Expiry/repeal: {expiry}. "
        f"Exact locators: {locators}. "
        f"PROVES: {proves} "
        f"DOES_NOT_PROVE: {does_not_prove} "
        f"Register status: {status}."
    )
    return SourceRecord(
        id=id,
        title=title,
        authority=authority,
        source_type=source_type,
        url=url,
        jurisdiction="IN-MH",
        source_class="Official",
        notes=notes,
        checked_date=checked,
        trust_tier=tier,
        content_hash="",
    )


def load_mh_sources() -> list[SourceRecord]:
    """Return the batch-1 + batch-2 + location-cluster referenced MH sources (22)."""
    return [
        _S(
            "SRC-001",
            "EIA Notification 2006 - consolidated as on 13-07-2026",
            "MoEFCC (PARIVESH)",
            "OFFICIAL_PRIMARY",
            "https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/"
            "IA_DOCS/1018_23072026010355.pdf",
            "T1", "2026-09-26",
            "2006-09-14 (consolidated to 13-07-2026)", "-",
            "Schedule items 5(f) & footnote 76; 7(c) Notes 1-2; 8(a) "
            "Notes & footnote 98; GC; SC; para 7(ii)(b)",
            "Verbatim Schedule items 5(b),5(e),5(f),5(h),7(c),8(a),8(b); "
            "General & Specific Conditions; para 7(ii)(a)-(c); footnote 98 "
            "records SC quashing of 8(a) Note 1 (S.O.523(E) 29-01-2025)",
            "Paras 9 (validity) and 10 (post-EC monitoring) were not "
            "extracted; does not state whether a 5(f) project also needs "
            "8(a) EC; does not identify which estates are 'notified'",
            "VERIFIED",
        ),
        _S(
            "SRC-013",
            "Hazardous and Other Wastes (Management and Transboundary "
            "Movement) Rules 2016 - principal text",
            "MoEFCC (India Code)",
            "OFFICIAL_PRIMARY",
            "https://upload.indiacode.nic.in/showfile"
            "?actid=AC_CH_60_926_00001_00001_1558607117075&type=rule"
            "&filename=final_hwm_rules_2016__english_.pdf",
            "T1", "2026-09-26", "2016-04-04", "-",
            "r.3, r.4, r.5, r.6, r.9, r.19; Schedule I processes "
            "1,5,19,20,21,23,26,27,28,29,33,34,35,36,37",
            "HOWM Rules 2016 principal text: r.3 definitions; r.4 "
            "occupier duties; r.5 State duties; r.19 manifest Form 10 "
            "seven copies; Schedule I process list with waste stream "
            "numbers",
            "Amendments after 04-04-2016 (2016-2025) are not consolidated "
            "in this file; does not map any specific unit's stream to "
            "an entry",
            "VERIFIED",
        ),
        _S(
            "SRC-017",
            "PESO - SOP under Petroleum Rules 2002",
            "PESO",
            "OFFICIAL_PRIMARY",
            "https://www.peso.gov.in/sites/default/files/2025-01/"
            "Petroleum%20Rules%202002%20-%20SOP.pdf",
            "T3", "2026-09-26", "2025-01", "-",
            "Exemptions and forms tables",
            "PESO SOP: petroleum licence forms/authorities table; "
            "Class A <=30 L and Class B <=2500 L (non-bulk, receptacle "
            "<=1000 L) exemptions as summarised",
            "SOP is not the Rules text; Class A 30 L exemption not "
            "verified against Petroleum Rules 2002 text",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-026",
            "MoLE document on contract labour under OSH Code (Feb 2026)",
            "MoLE",
            "OFFICIAL_PRIMARY",
            "https://www.labour.gov.in/static/uploads/2026/02/"
            "83978455025732b99b0165def80ab171.pdf",
            "T3", "2026-09-26", "2026-02", "-",
            "see rules.csv source_locator",
            "Only the claims tied to this source in rules.csv / "
            "approvals.csv, at the locator stated there. v1 note: "
            "Contract labour applicability >=50",
            "Anything beyond those locators; Maharashtra implementation "
            "status unless the source is a Maharashtra authority; "
            "currency after the doc_date",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-031",
            "Labour Department RTS services list",
            "GoM Labour Dept",
            "OFFICIAL_PORTAL",
            "https://labour.maharashtra.gov.in/en/labour-rts-services",
            "T3", "2026-09-26", "2026", "-",
            "see rules.csv source_locator",
            "Only the claims tied to this source in rules.csv / "
            "approvals.csv, at the locator stated there. v1 note: "
            "Notified RTS timelines for DISH, S&E, CLRA, BOCW, ISMW, "
            "Boilers",
            "Anything beyond those locators; Maharashtra implementation "
            "status unless the source is a Maharashtra authority; "
            "currency after the doc_date",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-034",
            "Boilers Act 2025 (Act 12 of 2025) - Gazette text",
            "Gazette of India",
            "OFFICIAL_PRIMARY",
            "https://egazette.gov.in/writeReadData/2025/262299.pdf",
            "T1", "2026-09-26", "2025-05-01 (per SRC-032)", "-",
            "s.1(3),(4); s.2(c),(g),(h),(r); s.6; s.8",
            "Boilers Act 2025 s.1(3)-(4) application; s.2(c) 'boiler' "
            "with exclusions (<25 L; <1 kg/cm2 design AND working gauge "
            "pressure; water heated below 100 C); s.2(h) economiser; "
            "s.2(r) steam-pipe; s.6 welders; s.8 inspection during "
            "manufacture",
            "Registration/certificate section numbers and procedure were "
            "not extracted; Maharashtra state rules under the 2025 Act",
            "VERIFIED",
        ),
        _S(
            "SRC-043",
            "MIDC services portal - all services with timelines",
            "MIDC",
            "OFFICIAL_PORTAL",
            "https://services.midcindia.org/Services/"
            "AllServicesPortalAnon.aspx",
            "T3", "2026-09-26", "2026", "-",
            "see rules.csv source_locator",
            "Only the claims tied to this source in rules.csv / "
            "approvals.csv, at the locator stated there. v1 note: Live "
            "application system",
            "Anything beyond those locators; Maharashtra implementation "
            "status unless the source is a Maharashtra authority; "
            "currency after the doc_date",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-044",
            "MIDC - Planning & pre-operations page",
            "MIDC",
            "OFFICIAL_PORTAL",
            "https://www.midcindia.org/en/customers/"
            "planning-pre-operations/",
            "T3", "2026-09-26", "2026", "-",
            "see rules.csv source_locator",
            "Only the claims tied to this source in rules.csv / "
            "approvals.csv, at the locator stated there. v1 note: "
            "Timelines differ from SRC-043",
            "Anything beyond those locators; Maharashtra implementation "
            "status unless the source is a Maharashtra authority; "
            "currency after the doc_date",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-052",
            "CGWA consolidated guidelines (2020 + amendment "
            "S.O. 1509(E) 29-03-2023)",
            "CGWA",
            "OFFICIAL_PRIMARY",
            "https://cgwa-noc.gov.in/landingpage/Guidlines/"
            "ConsolidateGuidline.pdf",
            "T1", "2026-09-26", "2023-03-29", "-",
            "see rules.csv source_locator",
            "Only the claims tied to this source in rules.csv / "
            "approvals.csv, at the locator stated there. v1 note: "
            "Exemptions; OE restrictions; flow meter intimation 30 days; "
            "no decision timeline stated",
            "Anything beyond those locators; Maharashtra implementation "
            "status unless the source is a Maharashtra authority; "
            "currency after the doc_date",
            "VERIFIED",
        ),
        _S(
            "SRC-081",
            "Occupational Safety, Health and Working Conditions Code "
            "2020 (Act 37 of 2020) - text",
            "India Code / MoLJ",
            "OFFICIAL_PRIMARY",
            "https://www.indiacode.nic.in/bitstream/123456789/22041/1/"
            "2020-37.pdf",
            "T1", "2026-09-26", "2025-11-21", "-",
            "s.2(1)(v),(w),(zf); s.3; s.6; s.10; s.22; s.45; s.82",
            "s.2(1) definitions incl. establishment (10 workers), "
            "factory (20 with power / 40 without, state-number proviso), "
            "inter-State migrant worker; s.3 registration within 60 days; "
            "s.22 safety officers (factory >=500; hazardous-process "
            "factory >=250); s.45 contract labour Part applies at >=50",
            "Maharashtra prescribed time limits, forms, fees (rules are "
            "draft); the pre-Code Maharashtra factory number for the "
            "s.2(1)(w) proviso",
            "VERIFIED",
        ),
        _S(
            "SRC-100",
            "Insecticides Act 1968 - text (India Code)",
            "India Code",
            "OFFICIAL_PRIMARY",
            "https://www.indiacode.nic.in/bitstream/123456789/11671/1/"
            "3)_the_insecticides_act_1968_not_ocr.pdf",
            "T1", "2026-09-26", "1968", "-",
            "s.13",
            "s.13: any person desiring to manufacture, sell, stock or "
            "distribute any insecticide applies to the licensing officer "
            "for a licence",
            "Maharashtra licensing officer identity; Insecticides Rules "
            "forms",
            "VERIFIED",
        ),
        _S(
            "SRC-102",
            "Central Motor Vehicles Rules 1989 - text (India Code)",
            "India Code",
            "OFFICIAL_PRIMARY",
            "https://upload.indiacode.nic.in/showfile"
            "?actid=AC_CEN_30_42_00009_198859_1517807326286&type=rule"
            "&filename=Cmvr1989.pdf",
            "T1", "2026-09-26", "1989 (as amended)", "-",
            "r.129",
            "r.129-r.137: owner of a goods carriage transporting "
            "dangerous or hazardous goods must comply with listed duties",
            "Consignor-specific duties beyond r.131; any 2022+ VTS "
            "amendment status",
            "VERIFIED",
        ),
        _S(
            "SRC-085",
            "Boiler Operation Engineers' Rules 2025 - G.S.R. 705(E) "
            "22-09-2025 (Gazette No.621, 23-09-2025)",
            "DPIIT, MoCI",
            "OFFICIAL_PRIMARY",
            "https://egazette.gov.in/writeReadData/2025/266452.pdf",
            "T1", "2026-09-26", "2025-09-23", "-",
            "Rules 1-4 and committee rules",
            "Final rules under Boilers Act 2025 s.39; BOE required "
            "above 1,000 m2 heating surface (single/battery/within "
            "50 m)",
            "Boiler registration procedure; Maharashtra services",
            "VERIFIED",
        ),
        _S(
            "SRC-092",
            "Petroleum Act 1934 - text (PESO)",
            "PESO",
            "OFFICIAL_PRIMARY",
            "https://peso.gov.in/web/sites/default/files/2019-12/"
            "PR_Act_full.pdf",
            "T1", "2026-09-26", "1934", "-",
            "s.2, s.3, s.7",
            "s.2(b)-(d) Class A (<23 C), B (23 to <65 C), C (65 to "
            "<93 C) flash point; s.3 licence requirement; s.7 no licence "
            "for Class B <= 2,500 L at one place with no receptacle > "
            "1,000 L, and Class C <= 45,000 L stored per rules",
            "Class A small-quantity exemption (in Rules, not Act); "
            "bulk/non-bulk definitions; Rule 144 NOC",
            "VERIFIED",
        ),
        _S(
            "SRC-135",
            "E-Waste (Management) Rules 2022 (CPCB copy)",
            "MoEFCC",
            "CENTRAL_RULES",
            "https://cpcb.nic.in/uploads/Projects/E-Waste/"
            "e-waste_rules_2022.pdf",
            "T1", "2026-09-26", "01-04-2023", "",
            "r.3 'bulk consumer'; r.8",
            "Bulk consumer = >=1,000 units of Sch I EEE in a FY; duty to "
            "hand over e-waste only to registered "
            "producer/refurbisher/recycler",
            "Post-2022 amendments",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-179",
            "Supreme Court - Vanashakti v Union of India, WP(C) "
            "166/2025, judgment 05-08-2025 (PARIVESH upload)",
            "Supreme Court of India",
            "COURT_ORDER",
            "https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/"
            "IA_DOCS/1002_01092025113231.pdf",
            "T1", "26-09-2026", "05-08-2025", "",
            "operative directions",
            "Note 1 under item 8(a) quashed (already reflected in R-007)",
            "5(f)+8(a) combination",
            "VERIFIED",
        ),
        _S(
            "SRC-117",
            "Petroleum Rules 2002 - full text (PESO)",
            "PESO / MoCI",
            "CENTRAL_RULES",
            "https://peso.gov.in/web/sites/default/files/2019-12/"
            "PR-2002-English-full.pdf",
            "T1", "26-09-2026", "", "",
            "r.2, r.42, r.62, r.131, r.144, First Schedule",
            "Definitions (container <=1,000 L, tank, bulk); Form XII/XIII "
            "(DA), XV/XVI (Controller) scopes; plan approval; DA NOC "
            "within 3 months",
            "A Class A <=30 L storage exemption (not found in rules "
            "text; r.42 30 L relates to vessels); amendments after 2019 "
            "upload",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-136",
            "Maharashtra Labour Dept - services with time limits (Labour "
            "Commissioner, DISH, Steam Boilers)",
            "Labour Dept, GoM",
            "PORTAL_PAGE",
            "https://labour.maharashtra.gov.in/en/services",
            "T3", "26-09-2026", "", "",
            "DISH rows 1-7; Boilers rows 1-29; Labour Commissioner rows "
            "1-23",
            "Portal SLAs: DISH licence MAH/hazardous 30 d, other 7 d; "
            "plan approval 30 d; boiler registration 30 d; CLRA/BOCW/ISMW "
            "7-15 d - all citing pre-Code Acts",
            "That the cited pre-Code Acts are current law (they are "
            "repealed; services are PORTAL_LEGACY)",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-112",
            "CRZ Notification 2019 - G.S.R. 37(E) 18-01-2019 (MCZMA copy)",
            "MoEFCC",
            "NOTIFICATION",
            "https://www.mczma.gov.in/sites/default/files/CRZ%20Notification%202019.pdf",
            "T1", "26-09-2026", "18-01-2019", "",
            "paras 3, 4(i), 4(ii), 4(xi), 5.1.2(v), 7, 8, Annexure-II",
            "CRZ extents, prohibited activities (new industry, hazardous storage "
            "except Annexure-II, groundwater), clearance routing and 60-day timelines",
            "Whether a site is in CRZ (requires CZMP geospatial fact); "
            "Maharashtra CZMP approval status per stretch",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-113",
            "Van (Sanrakshan Evam Samvardhan) Rules 2023",
            "MoEFCC",
            "CENTRAL_RULES",
            "https://forestsclearance.nic.in/writereaddata/Rules/"
            "VanSanrakshanEvamSamvardhanRules2023.pdf",
            "T1", "26-09-2026", "01-12-2023", "",
            "r.9, r.10",
            "Two-stage approval, online through State; RO/REC up to 40 ha",
            "Whether a site includes forest land (geospatial/land-record fact)",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-114",
            "MoEFCC note incl. Supreme Court order 04-12-2006 WP(C) 460/2004 "
            "(NBWL recommendation)",
            "MoEFCC / Supreme Court",
            "ORDER",
            "https://forestsclearance.nic.in/writereaddata/Addinfo/"
            "0_0_10117125912181NONFOREST.PDF",
            "T2", "26-09-2026", "04-12-2006", "",
            "order text",
            "EC projects within ESZ or within 10 km of NP/WLS (where ESZ not "
            "notified) need Standing Committee NBWL recommendation",
            "Any later modification of the 10 km default by individual ESZ "
            "notifications",
            "VERIFIED_CONDITIONAL",
        ),
        _S(
            "SRC-120",
            "HOWM Rules 2016 - text incl. Schedule II (copy hosted by DPCC)",
            "MoEFCC (host: DPCC)",
            "CENTRAL_RULES",
            "https://dpccocmms.nic.in/SPCB_DOCUMENTS/HWM_RULES_2016.pdf",
            "T2", "26-09-2026", "04-04-2016", "",
            "r.3(17); Schedule II Class A/B/C",
            "Class A TCLP limits, Class B limits, C1 flash point <60 C, "
            "C2 pH <=2 or >=12.5, C3 reactive",
            "Post-2016 amendments to Schedule II; whether a specific waste "
            "exceeds limits (lab data)",
            "VERIFIED_CONDITIONAL",
        ),
    ]


MH_LOADED_SOURCE_IDS: frozenset[str] = frozenset({
    "SRC-001", "SRC-013", "SRC-017", "SRC-026", "SRC-031", "SRC-034",
    "SRC-043", "SRC-044", "SRC-052", "SRC-081", "SRC-085", "SRC-092",
    "SRC-100", "SRC-102", "SRC-112", "SRC-113", "SRC-114", "SRC-117",
    "SRC-120", "SRC-135", "SRC-136", "SRC-179",
})
