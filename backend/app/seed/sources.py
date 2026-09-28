"""Seed data for the 32 verified Gujarat regulatory sources (S01-S32).

Extracted from the frozen workbook Sources sheet. All sources are classified
as Official and verified as of 2026-09-15.
"""
from __future__ import annotations

from app.regulatory.models import SourceRecord


def _s(
    id: str,
    title: str,
    authority: str,
    source_type: str,
    url: str,
    notes: str = "",
    checked: str = "2026-09-15",
    source_class: str = "Official",
    trust_tier: str = "govt-portal",
) -> SourceRecord:
    return SourceRecord(
        id=id,
        title=title,
        authority=authority,
        source_type=source_type,
        url=url,
        jurisdiction="IN-GJ",
        source_class=source_class,
        notes=notes,
        checked_date=checked,
        trust_tier=trust_tier,
        content_hash="",
    )


def load_regulatory_sources() -> list[SourceRecord]:
    """Return all 32 verified Gujarat regulatory sources from the workbook."""
    return [
        _s(
            "S01",
            "Gujarat IFP Pre-Establishment",
            "Government of Gujarat / IFP",
            "portal catalogue",
            "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_establishment_approvals.jsp?pagedisp=static",
            "Use as service catalogue; underlying legal rule may sit elsewhere",
        ),
        _s(
            "S02",
            "Gujarat IFP Pre-Operation",
            "Government of Gujarat / IFP",
            "portal catalogue",
            "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_operation_approvals.jsp?pagedisp=static",
            "Service catalogue",
        ),
        _s(
            "S03",
            "GIDC Plan Approval",
            "GIDC",
            "web page",
            "https://gidc.gujarat.gov.in/Pages/Contents/application-for-plan-approval",
            "Risk table + documents + SLA; page contains stale physical verification text",
        ),
        _s(
            "S04",
            "GIDC Water Connection",
            "GIDC",
            "web page",
            "https://gidc.gujarat.gov.in/Pages/Contents/application-for-water-connection",
            "Chemical-unit GPCB NOC + quantity checks",
        ),
        _s(
            "S05",
            "GIDC Drainage Connection",
            "GIDC",
            "web page",
            "https://gidc.gujarat.gov.in/Pages/Contents/application-for-drainage-connection",
            "ETP/STP + GPCB + quantity consistency",
        ),
        _s(
            "S06",
            "GIDC Amendment Circular 28-01-2026",
            "GIDC",
            "PDF circular",
            "https://gidc.gujarat.gov.in/Document/LinkManagment/Circulars/amendment-circular29012026110303.pdf",
            "Fresh plan/water/drainage: no physical site investigation",
        ),
        _s(
            "S07",
            "Fire Regulations 2023",
            "Government of Gujarat",
            "Gazette PDF",
            "https://gujfiresafetycop.in/uploads/regulations2023.pdf",
            "Current listed regulations",
        ),
        _s(
            "S08",
            "Fire Safety FAQ",
            "Government of Gujarat",
            "portal FAQ",
            "https://fscop.gujfiresafetycop.in/Front/FAQ.aspx",
            "Applicability + FSPA/FSCA/renewal process; some FAQ text still says 2022",
        ),
        _s(
            "S09",
            "ShramSetu Online Application",
            "Gujarat Commissionerate of Labour",
            "portal",
            "https://shramsetu.gujarat.gov.in/Pages/OnlineApplication",
            "Current OSH&WC registration/licence portal",
        ),
        _s(
            "S10",
            "OSH&WC Central Rules 2026",
            "Ministry of Labour & Employment",
            "Gazette PDF",
            "https://www.labour.gov.in/static/uploads/2026/05/ee246f790cad0b8e99c3828f34fa09a6.pdf",
            "Correct Occupational Safety, Health and Working Conditions (Central) Rules, 2026",
        ),
        _s(
            "S11",
            "CEA Safety & Electric Supply Regulations 2023",
            "CEICED Gujarat",
            "official rules page",
            "https://ceiced.gujarat.gov.in/rules/central-electricity-authoritymeasures-relating-to-safety-and-electric-supply-regulations-2023?lang=English",
            "Governing regulation page",
        ),
        _s(
            "S12",
            "GERC Fourth Amendment 2024 - Supply Code",
            "GERC",
            "official order PDF",
            "https://gercin.org/wp-content/uploads/2024/09/Order-No.-8-of-2024-dtd.-25.09.pdf",
            "LT 150 kVA option + HT band",
        ),
        _s(
            "S13",
            "GERC explanatory/SoR 4th amendment",
            "GERC",
            "official PDF",
            "https://gercin.org/wp-content/uploads/2024/09/SoR-GERC-Elec.-Supply-Code-Related-Matters-4th-Amendment-Regulations-2024.pdf",
            "Amendment rationale",
        ),
        _s(
            "S14",
            "PARIVESH KYA",
            "MoEFCC",
            "official portal",
            "https://parivesh.nic.in/kya/",
            "Tentative approvals; current dynamic rules",
        ),
        _s(
            "S15",
            "PARIVESH current chemical proposal record",
            "MoEFCC / PARIVESH",
            "official proposal PDF",
            "https://parivesh.nic.in/utildoc/1229805218_1780038080480.pdf",
            "5(f) standard conditions/current proposal evidence",
        ),
        _s(
            "S16",
            "CPCB HOWM 2024 Amendment",
            "CPCB / MoEFCC",
            "Gazette PDF",
            "https://cpcb.nic.in/uploads/hwmd/HOWM-Ninth-Amendment-Rules-2024.pdf",
            "Current rule update in retained dataset",
        ),
        _s(
            "S17",
            "CPCB Hazardous chemical integrated guidance",
            "CPCB / MoEFCC",
            "official guidance PDF",
            "https://cpcb.nic.in/uploads/Guidelines_integrated_guidance_framework.pdf",
            "MSIHC mechanism and definitions",
        ),
        _s(
            "S18",
            "PESO petroleum storage licence requirement",
            "PESO / DPIIT",
            "official page/PDF",
            "https://www.peso.gov.in/web/en/requirement-license-under-petroleum-rules-2002-storage-petroleum",
            "Use with exact substance/class/quantity",
        ),
        _s(
            "S19",
            "CGWA consolidated guidelines",
            "CGWA / Ministry of Jal Shakti",
            "official PDF",
            "https://cgwa-noc.gov.in/landingpage/Guidlines/ConsolidateGuidline.pdf",
            "Groundwater NOC branch",
        ),
        _s(
            "S20",
            "Gujarat GERC supply-code copy",
            "PGVCL / GERC",
            "official utility-hosted PDF",
            "https://www.pgvcl.com/download/REGULATION/SupplyCode.pdf",
            "Official utility copy of supply code; use GERC source for regulatory amendments",
        ),
        _s(
            "S21",
            "PARIVESH EIA Notification index",
            "MoEFCC / PARIVESH",
            "official notification index",
            "https://environmentclearance.nic.in/report/View_EIA_Notifications.aspx",
            "Lists S.O.1533(E) 14-09-2006 and subsequent "
            "EIA notifications/amendments retained by the portal",
        ),
        _s(
            "S22",
            "EIA Notification 2006 - S.O.1533(E)",
            "MoEFCC / PARIVESH",
            "Gazette notification",
            "https://cpc.parivesh.nic.in/",
            "Primary EIA Notification source; "
            "item 5(f) is the starting point for synthetic organic chemicals",
        ),
        _s(
            "S23",
            "EIA amendment - S.O.389(E), 28-01-2026",
            "MoEFCC / PARIVESH",
            "Gazette notification",
            "https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/IA_DOCS/1001_03022026060156.pdf",
            "Current 2026 EIA amendment relevant to version control",
        ),
        _s(
            "S24",
            "GIDC FY 2026-27 allotment price / estate list",
            "GIDC",
            "official estate directory",
            "https://gidc.gujarat.gov.in/allotmentprice",
            "Dahej and Dahej-II are listed under Bharuch district",
        ),
        _s(
            "S25",
            "GIDC Engineering current circular list",
            "GIDC",
            "official circular index",
            "https://gidc.gujarat.gov.in/Pages/Contents/Engineering",
            "Confirms the 28-01-2026 physical-touchpoint amendment is current",
        ),
        _s(
            "S26",
            "GIDC Dahej / Vagra useful-links evidence",
            "GIDC",
            "official page",
            "https://gidc.gujarat.gov.in/Pages/Contents/useful_links",
            "Dahej SEZ is identified in Vagra Taluka, Bharuch district",
        ),
        _s(
            "S27",
            "GIDC Bharuch contact jurisdiction",
            "GIDC",
            "official contact page",
            "https://gidc.gujarat.gov.in/Pages/Contents/Contactus",
            "Dahej/Vilayat/Saykha grouped under Bharuch R&B jurisdiction",
        ),
        _s(
            "S28",
            "Torrent Power Ltd - Distribution Dahej FY2026-27 tariff order",
            "GERC",
            "official tariff order",
            "https://gercin.org/wp-content/uploads/2026/03/TPL-D-Dahej-2587-2025-Tariff-Order-for-FY-2026-27-dtd.-25.3.2026.pdf",
            "Current license-area evidence for Dahej SEZ",
        ),
        _s(
            "S29",
            "Bharuch district public utilities",
            "District Bharuch / Government of Gujarat",
            "official district portal",
            "https://bharuch.nic.in/public-utilities/",
            "Lists DGVCL as district electricity utility contact",
        ),
        _s(
            "S30",
            "CEICED official checklist index",
            "CEICED Gujarat",
            "official checklist page",
            "https://ceiced.gujarat.gov.in/rcps-act-gujarat",
            "Current page lists electrical installation and lift/escalator checklists",
        ),
        _s(
            "S31",
            "Gujarat Directorate of Boilers - Acts & Rules",
            "Directorate of Boilers, Gujarat",
            "official rules index",
            "https://boiler.gujarat.gov.in/acts-rules.htm",
            "Lists Gujarat Boiler Rules, 1966 and Economiser Rules, 1968",
        ),
        _s(
            "S33",
            "Gujarat Industrial Policy 2020",
            "Government of Gujarat / Industries Commissionerate",
            "official policy PDF",
            "https://static.investindia.gov.in/s3fs-public/2020-08/Gujarat%20Industrial%20Policy%202020.pdf",
            "Capital subsidy, interest subsidy, electricity duty exemption for industries",
        ),
    ]


def source_to_dict(source: SourceRecord) -> dict:
    """Convert a SourceRecord to a database-insertable dict."""
    return {
        "id": source.id,
        "jurisdiction": source.jurisdiction,
        "domain": source.source_type,
        "url": source.url,
        "fetch_recipe": {},
        "trust_tier": source.trust_tier,
        "content_hash": source.content_hash or f"seed-{source.id}",
        "title": source.title,
        "authority": source.authority,
        "source_type": source.source_type,
        "source_class": source.source_class,
        "notes": source.notes,
        "checked_date": source.checked_date,
    }


def source_to_chunks(source: SourceRecord) -> list[dict]:
    """Generate searchable text chunks for a source.

    Each source gets 1-3 chunks depending on content richness:
    - Primary chunk: title + authority + source type
    - Secondary chunk: notes (if substantive)
    - Tertiary chunk: URL domain context
    """
    chunks: list[dict] = []

    # Primary chunk: core identity
    primary = f"{source.title} — {source.authority} ({source.source_type})"
    chunks.append({
        "source_id": source.id,
        "chunk_text": primary,
        "chunk_index": 0,
        "metadata": {"role": "identity"},
    })

    # Secondary chunk: notes/annotation
    if source.notes and len(source.notes) > 10:
        chunks.append({
            "source_id": source.id,
            "chunk_text": f"{source.title}: {source.notes}",
            "chunk_index": 1,
            "metadata": {"role": "annotation"},
        })

    # Tertiary chunk: jurisdictional context
    jurisdiction_note = f"Gujarat ({source.jurisdiction}) regulatory source — {source.source_class}"
    chunks.append({
        "source_id": source.id,
        "chunk_text": jurisdiction_note,
        "chunk_index": len(chunks),
        "metadata": {"role": "jurisdiction"},
    })

    return chunks
