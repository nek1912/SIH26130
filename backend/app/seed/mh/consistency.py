"""Maharashtra v5 batch-1 consistency rules (Phase 6) — none.

STOP outcome, reported explicitly per the Phase 6 brief: a full
register-wide search of all 73 v5 CSVs found ZERO records stating a
cross-document field-consistency relationship (no "field X in DOC-A
must equal field X in DOC-B" for DOC-001/002/003/008 or any other
batch-1 document). The adjacent files are decision paths
(howm_decision_path), checklists, compliance obligations, and
rule-level edge tests — none of which is a consistency rule.

Encoding the Phase-5 report's cross-check *areas* (CTE/CTO numbers,
validity windows, occupier identity) without a v5 record would be
invention, so nothing is transcribed. The loader returns [] and the
MH pack carries no consistency rules until v5 provides them.
"""
from __future__ import annotations

from app.consistency.models import ConsistencyRule

MH_DEFERRED_CONSISTENCY_NOTE = (
    "No v5 cross-document consistency records exist for the batch-1 "
    "documents (register-wide search, 73 CSVs, zero hits); nothing "
    "transcribed. Cross-check areas from the Phase-5 report (CTE/CTO "
    "numbers, validity windows, occupier identity) remain unsupported "
    "by source data."
)


def load_mh_consistency_rules() -> list[ConsistencyRule]:
    """Return the batch-1 MH consistency rules: none (see module note)."""
    return []
