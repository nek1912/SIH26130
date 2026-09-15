"""Approval dependency seed data from the frozen workbook.

Dependency Mapping Report
=========================

The following dependency relationships are supported by the workbook's
Rule_Register, Document_Register, and IFP workflow documentation.

Each dependency is classified as:
- EXPLICIT: directly stated in a source document (Rule_Register, Document_Register,
  or official IFP/checklist source).
- INFERRED: derived from workflow ordering or logical necessity but not directly
  stated in a single source.

MVP SCOPE: Only EXPLICIT dependencies with high confidence are included.

Dependency Mapping:
-------------------

Approval | Prerequisite | Evidence | Confidence | MVP?
---------|-------------|----------|------------|-----
A01      | (none)      | —        | —          | yes (independent)
A02      | A04         | S04: GIDC Water Connection requires "copy of GPCB NOC" which is
         |             | the CTE (A04). Document_Register lists GPCB NOC as required
         |             | document for A02. | EXPLICIT | YES
A03      | A04         | S05: GIDC Drainage requires "approved ETP/STP plan + GPCB NOC".
         |             | GPCB NOC = A04 (CTE). | EXPLICIT | YES
A03      | A02         | S05: GIDC Drainage requires water connection (A02) as
         |             | operational prerequisite — drainage connects after water.
         |             | Document_Register lists water connection receipt. | EXPLICIT | YES
A04      | (none)      | —        | —          | yes (independent)
A05      | (none)      | —        | —          | yes (independent, parallel)
A06      | (none)      | —        | —          | yes (independent, parallel)
A07      | (none)      | Regulatory registration is independent of GIDC/GPCB.
         |             | Labour registration has its own statutory track. | — | YES
A08      | (none)      | BOCW is construction-phase, independent. | — | YES
A09      | (none)      | HT electricity is independent utility connection. | — | YES
A10      | A09         | CEICED inspects HT installations; requires HT connection
         |             | (A09) to exist. CEA Regulations 2023. | INFERRED | NO (deferred)
A11      | A04         | HOWM authorization application references CTE number.
         |             | CPCB HOWM 2024. | INFERRED | NO (deferred)
A12      | (none)      | MSIHC is self-contained chemical safety. | — | YES
A13      | (none)      | Chemical Accidents Rules, independent. | — | YES
A14      | (none)      | BU Permission is pre-operation; dependencies on A01/A07/A06
         |             | are procedural (completion certs), not regulatory prerequisites
         |             | in the Rule_Register. | INFERRED | NO (deferred)
A15      | (none)      | Lift approval is independent equipment registration. | — | YES
A16      | (none)      | Boiler registration is independent. | — | YES
A17      | (none)      | PESO licence is independent. | — | YES
A18      | (none)      | CGWA NOC is independent. | — | YES

MVP dependency count: 3 edges
- A02 depends on A04
- A03 depends on A04
- A03 depends on A02

This produces a serial chain: A04 → A02 → A03 (3 stages)
with A04 at stage 0, A02 at stage 1, A03 at stage 2.
"""
from __future__ import annotations

from app.rules.dependency_models import ApprovalDependency


def load_approval_dependencies() -> list[ApprovalDependency]:
    """Return the verified MVP dependency edges.

    These are the only dependency relationships supported by the
    workbook's Rule_Register and Document_Register sources.
    """
    return [
        ApprovalDependency(
            approval_id="A02",
            prerequisite_approval_id="A04",
            relationship="regulatory_prerequisite",
            source_ref="S04",
            evidence=(
                "GIDC Water Connection requires copy of GPCB NOC (CTE). "
                "Document Register lists GPCB NOC as required document for A02."
            ),
            confidence="explicit",
        ),
        ApprovalDependency(
            approval_id="A03",
            prerequisite_approval_id="A04",
            relationship="regulatory_prerequisite",
            source_ref="S05",
            evidence=(
                "GIDC Drainage Connection requires GPCB NOC (CTE). "
                "Document Register lists GPCB NOC as required document for A03."
            ),
            confidence="explicit",
        ),
        ApprovalDependency(
            approval_id="A03",
            prerequisite_approval_id="A02",
            relationship="procedural_prerequisite",
            source_ref="S05",
            evidence=(
                "GIDC Drainage Connection requires active water connection (A02). "
                "Drainage connects after water supply is established."
            ),
            confidence="explicit",
        ),
    ]
