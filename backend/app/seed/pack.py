"""Jurisdiction-aware regulatory pack boundary (Phase 1 scaffold).

Single authoritative interface through which runtime code obtains
regulatory-pack data:

    load_regulatory_pack(jurisdiction) -> RegulatoryPack

The pack carries exactly the structures the engines already consume
(rules, authorities, dependencies, document requirements, consistency
rules, incentive schemes, sources, evidence gaps + surfacing hints,
portal catalog). No second domain model is introduced: every field
reuses an existing engine/service contract type.

Phase 1 behavior:
- "IN-GJ" returns the existing Gujarat seed data (unchanged).
- "IN-MH" returns the batch-1 Maharashtra v5 pack (safe-only
  encoded rules, authorities, batch-1 dependencies, document
  requirements, advisory evidence gaps, batch-1-referenced sources,
  batch-1 portal catalog, batch-1 SLA display metadata; consistency
  is empty by source evidence, incentives populate later).
- Any other jurisdiction raises UnknownJurisdictionError. Unknown
  jurisdictions never silently fall back to Gujarat.

Cutover point: DEFAULT_JURISDICTION below. Production resolves to
IN-GJ during the scaffold phase. Flipping the default is the isolated
future cutover step (only after the MH pack passes integration tests).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.consistency.models import ConsistencyRule
from app.incentives.models import SupportScheme
from app.regulatory.evidence import EvidenceRecord
from app.regulatory.models import SourceRecord
from app.rules.dependency_models import ApprovalDependency
from app.rules.models import ApprovalRule
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.consistency import load_consistency_rules
from app.seed.dependencies import load_approval_dependencies
from app.seed.documents import load_document_requirements
from app.seed.evidence_gaps import EVIDENCE_TO_APPROVALS, load_evidence_gaps
from app.seed.handoff import all_portal_entries
from app.seed.incentives import load_incentive_schemes
from app.seed.mh.approvals import (
    load_mh_approval_authorities,
    load_mh_approval_rules,
)
from app.seed.mh.consistency import load_mh_consistency_rules
from app.seed.mh.dependencies import load_mh_approval_dependencies
from app.seed.mh.documents import load_mh_document_requirements
from app.seed.mh.evidence import (
    MH_EVIDENCE_HINTS,
    load_mh_evidence_gaps,
)
from app.seed.mh.portals import load_mh_portal_entries
from app.seed.mh.slas import load_mh_sla_records
from app.seed.mh.sources import load_mh_sources
from app.seed.sources import load_regulatory_sources
from app.workflow.sla import SlaMetadata

IN_GJ = "IN-GJ"
IN_MH = "IN-MH"

_KNOWN_JURISDICTIONS = frozenset({IN_GJ, IN_MH})

# Production resolving jurisdiction for NEW records. IN-GJ until the
# gated cutover. Existing persisted records NEVER resolve from this
# constant (see resolve_persisted_pack); changing it affects only
# records created afterwards. No other file carries a default
# jurisdiction; this constant is the single cutover point.
DEFAULT_JURISDICTION = IN_GJ

# Pack-version identity (Phase 9 design). The GJ corpus has no version
# constant anywhere in the repo, so the legacy name states that fact
# instead of inventing history. MH matches the encoded rule version.
GJ_LEGACY_PACK_VERSION = "gj-legacy-unversioned"
MH_PACK_VERSION = "mh-v5-batch1"

# Release table: (jurisdiction, pack_version) -> jurisdiction loader key.
# The ONLY supported combinations. Anything else is rejected, never
# defaulted, never inferred.
PACK_RELEASES: dict[tuple[str, str], str] = {
    (IN_GJ, GJ_LEGACY_PACK_VERSION): IN_GJ,
    (IN_MH, MH_PACK_VERSION): IN_MH,
}

# Default pack version per jurisdiction, for NEW records only.
DEFAULT_PACK_VERSIONS: dict[str, str] = {
    IN_GJ: GJ_LEGACY_PACK_VERSION,
    IN_MH: MH_PACK_VERSION,
}


class UnknownJurisdictionError(ValueError):
    """Raised when a jurisdiction has no known regulatory pack (API -> 422)."""

    def __init__(self, jurisdiction: Any) -> None:
        self.jurisdiction = jurisdiction
        super().__init__(
            f"Unknown jurisdiction {jurisdiction!r}; "
            f"known packs: {sorted(_KNOWN_JURISDICTIONS)}"
        )


class UnknownPackError(ValueError):
    """Raised for unknown (jurisdiction, pack_version) pairs (API -> 422).

    Never carries a fallback pack: callers must fail closed.
    """

    def __init__(self, jurisdiction: Any, pack_version: Any) -> None:
        self.jurisdiction = jurisdiction
        self.pack_version = pack_version
        super().__init__(
            f"Unknown regulatory pack ({jurisdiction!r}, {pack_version!r}); "
            f"supported: {sorted(PACK_RELEASES)}"
        )


def resolve_persisted_pack(
    jurisdiction: Any, pack_version: Any
) -> RegulatoryPack:
    """Authoritative pack resolver for persisted record identity.

    Accepts ONLY exact release-table pairs. Missing values, unknown
    jurisdictions, unknown versions, and mismatched combinations all
    raise UnknownPackError. Never consults DEFAULT_JURISDICTION, never
    infers from approval codes or fact vocabularies.
    """
    loader_key = PACK_RELEASES.get((jurisdiction, pack_version))
    if loader_key is None:
        raise UnknownPackError(jurisdiction, pack_version)
    return load_regulatory_pack(loader_key)


@dataclass(frozen=True)
class RegulatoryPack:
    """One jurisdiction's regulatory inputs for the decision pipeline.

    Field types mirror the existing engine/service contracts; the pack
    only groups them behind a jurisdiction boundary. Helpers implement
    the same filtering the seed modules provide (per-approval doc
    requirements, per-approval evidence gaps, per-code portal entries)
    so callers never need the seed modules directly.
    """

    jurisdiction: str
    approval_rules: list[ApprovalRule] = field(default_factory=list)
    approval_authorities: dict[str, str] = field(default_factory=dict)
    dependencies: list[ApprovalDependency] = field(default_factory=list)
    document_requirements: list[dict[str, Any]] = field(default_factory=list)
    consistency_rules: list[ConsistencyRule] = field(default_factory=list)
    incentive_schemes: list[SupportScheme] = field(default_factory=list)
    sources: list[SourceRecord] = field(default_factory=list)
    evidence_gaps: list[EvidenceRecord] = field(default_factory=list)
    evidence_hints: dict[str, list[str]] = field(default_factory=dict)
    portal_entries: list[dict[str, str]] = field(default_factory=list)
    # Display-only SLA declarations (no deadlines computed from these).
    sla_records: list[SlaMetadata] = field(default_factory=list)

    def get_requirements_for_approval(
        self, approval_id: str
    ) -> list[dict[str, Any]]:
        """Document requirements applying to an approval code."""
        return [
            req
            for req in self.document_requirements
            if approval_id in req.get("approval_ids", [])
        ]

    def get_gaps_for_approval(self, approval_code: str) -> list[EvidenceRecord]:
        """Evidence gaps potentially relevant to an approval code.

        Hint-only helper for fail-closed surfacing; not an
        applicability rule (same contract as the seed helper).
        """
        wanted = {
            eid
            for eid, codes in self.evidence_hints.items()
            if approval_code in codes
        }
        return [g for g in self.evidence_gaps if g.evidence_id in wanted]

    def get_portal_entry(self, approval_code: str) -> dict[str, str] | None:
        """Portal catalog entry for an approval code, or None if unmapped."""
        for entry in self.portal_entries:
            if entry.get("approval_code") == approval_code:
                return dict(entry)
        return None


def _load_gj_pack() -> RegulatoryPack:
    """Return the existing Gujarat regulatory data, unchanged."""
    return RegulatoryPack(
        jurisdiction=IN_GJ,
        approval_rules=load_approval_rules(),
        approval_authorities=load_approval_authorities(),
        dependencies=load_approval_dependencies(),
        document_requirements=load_document_requirements(),
        consistency_rules=load_consistency_rules(),
        incentive_schemes=load_incentive_schemes(),
        sources=load_regulatory_sources(),
        evidence_gaps=load_evidence_gaps(),
        evidence_hints={eid: list(codes) for eid, codes in EVIDENCE_TO_APPROVALS.items()},
        portal_entries=all_portal_entries(),
    )


def _empty_mh_pack() -> RegulatoryPack:
    """Batch-1 Maharashtra pack (Phase 6).

    Contains the safe-only encoded rules, their authorities, the
    batch-1 dependency edges, document requirements, advisory
    evidence gaps, the batch-1-referenced source corpus, the
    batch-1 portal catalog, and batch-1 SLA display metadata.
    Consistency rules are empty by source evidence (no v5
    cross-document consistency records exist for batch-1 documents).
    Incentive schemes populate in a later phase; until then that
    dimension is empty and fails closed.
    """
    return RegulatoryPack(
        jurisdiction=IN_MH,
        approval_rules=load_mh_approval_rules(),
        approval_authorities=load_mh_approval_authorities(),
        dependencies=load_mh_approval_dependencies(),
        document_requirements=load_mh_document_requirements(),
        evidence_gaps=load_mh_evidence_gaps(),
        evidence_hints={eid: list(codes) for eid, codes in MH_EVIDENCE_HINTS.items()},
        sources=load_mh_sources(),
        portal_entries=load_mh_portal_entries(),
        consistency_rules=load_mh_consistency_rules(),
        sla_records=load_mh_sla_records(),
    )


def load_regulatory_pack(jurisdiction: str) -> RegulatoryPack:
    """Load the regulatory pack for a jurisdiction.

    Accepted values: "IN-GJ" (existing Gujarat data), "IN-MH"
    (batch-1 safe-only v5 rules). Anything else raises
    UnknownJurisdictionError; there is no silent default.
    """
    if jurisdiction == IN_GJ:
        return _load_gj_pack()
    if jurisdiction == IN_MH:
        return _empty_mh_pack()
    raise UnknownJurisdictionError(jurisdiction)
