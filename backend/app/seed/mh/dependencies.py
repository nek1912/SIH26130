"""Maharashtra v5 batch-1 dependencies (Phase 4).

Only v5 dependency rows that are BOTH explicitly routable
(VERIFIED / VERIFIED_CONDITIONAL, non-inferred or workflow-explicit,
never UNKNOWN / REQUIRES_CONFIRMATION / FACILITATION) AND touch a
batch-1 approval as dependent or prerequisite enter the pack.

Full-register triage (34 rows):
- INCLUDED: DEP-009 (split into two approval-to-approval edges below;
  HOWM r.6 Form 1 is accompanied by CTE and CTO).
- OUT_OF_BATCH_SCOPE (dependent and prerequisite outside batch-1):
  DEP-003, DEP-004, DEP-005, DEP-006, DEP-007, DEP-008, DEP-010,
  DEP-011, DEP-014, DEP-016, DEP-017, DEP-018, DEP-019, DEP-021,
  DEP-023, DEP-024, DEP-025, DEP-026, DEP-031, DEP-032, DEP-033,
  DEP-034.
- NON_APPROVAL_ENDPOINT (an endpoint is an activity, document, or
  event — not an approval — so it can never satisfy readiness and
  would hard-block permanently): DEP-001, DEP-012, DEP-015, DEP-022,
  DEP-027, DEP-028, DEP-029, DEP-030.
- NOT_ROUTABLE_STATUS: DEP-002 (UNKNOWN, inferred practice), DEP-013
  (REQUIRES_OFFICIAL_CONFIRMATION).
- FACILITATION (never a readiness edge): DEP-020 (MAITRI CAF).

Note on DEP-009 prerequisites: APR-008/APR-009 have no batch-1
rules, so in batch-1 scope they are satisfied only via the
obtained-approvals set. That is engine-correct behavior (unknown
prerequisite blocks) and is covered by scenario tests.
"""
from __future__ import annotations

from app.rules.dependency_models import ApprovalDependency

MH_DEP_DEFERRED: dict[str, str] = {
    "DEP-001": "target is an activity (construction), not an approval",
    "DEP-002": "UNKNOWN status + inferred practice + out of batch scope",
    "DEP-003": "out of batch-1 scope",
    "DEP-004": "out of batch-1 scope (bundled MIDC service)",
    "DEP-005": "out of batch-1 scope",
    "DEP-006": "out of batch-1 scope",
    "DEP-007": "out of batch-1 scope",
    "DEP-008": "out of batch-1 scope",
    "DEP-010": "out of batch-1 scope",
    "DEP-011": "out of batch-1 scope",
    "DEP-012": "target is an activity (dewatering works), not an approval",
    "DEP-013": "REQUIRES_OFFICIAL_CONFIRMATION",
    "DEP-014": "out of batch-1 scope",
    "DEP-015": "UNKNOWN status + target is an activity (boiler use)",
    "DEP-016": "out of batch-1 scope",
    "DEP-017": "out of batch-1 scope",
    "DEP-018": "out of batch-1 scope",
    "DEP-019": "YES_INFERRED portal workflow ordering (APR-029 plot holder -> APR-030 "
                 "building permission), not a stated legal precondition; MEDIUM confidence T3 "
                 "service-list evidence (SRC-043) only; dependent (APR-030) out of batch-1 scope",
    "DEP-020": "FACILITATION_ONLY (MAITRI CAF) — never a readiness edge",
    "DEP-021": "out of batch-1 scope",
    "DEP-022": "target is an activity (abstraction), not an approval",
    "DEP-023": "out of batch-1 scope",
    "DEP-024": "out of batch-1 scope",
    "DEP-025": "out of batch-1 scope",
    "DEP-026": "out of batch-1 scope",
    "DEP-027": "prerequisite is an inspection event, not an approval",
    "DEP-028": "prerequisite is a plan approval, not an approval",
    "DEP-029": "prerequisite is a DA NOC, not an approval",
    "DEP-030": "prerequisite is an SC recommendation, not an approval",
    "DEP-031": "out of batch-1 scope",
    "DEP-032": "endpoints are events, not approvals",
    "DEP-033": "endpoints are land-use decisions, not approvals",
    "DEP-034": "endpoints are zone decisions, not approvals",
}


def load_mh_approval_dependencies() -> list[ApprovalDependency]:
    """Return the batch-1 MH dependency edges (DEP-009 × 2)."""
    return [
        ApprovalDependency(
            approval_id="APR-010",
            prerequisite_approval_id="APR-008",
            relationship="document_prerequisite",
            source_ref="SRC-013 r.6",
            evidence=(
                "DEP-009: HOWM r.6 Form 1 application is accompanied "
                "by CTE (APR-008)."
            ),
            confidence="explicit",
        ),
        ApprovalDependency(
            approval_id="APR-010",
            prerequisite_approval_id="APR-009",
            relationship="document_prerequisite",
            source_ref="SRC-013 r.6",
            evidence=(
                "DEP-009: HOWM r.6 Form 1 application is accompanied "
                "by CTO (APR-009)."
            ),
            confidence="explicit",
        ),
    ]
