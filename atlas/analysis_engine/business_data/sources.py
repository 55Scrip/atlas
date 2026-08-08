"""Source taxonomy (ATLAS-022, Phase 5) -- the one closed vocabulary for
"what kind of business document is this," across every provider Atlas
will ever connect.

**This supersedes `atlas.analysis_engine.business.ExternalSourceKind`**
(ATLAS-021), which was itself explicitly reserved and never constructed
pending this sprint -- its own docstring said "named now so a future
ingestion adapter does not need to widen this enum." That future sprint
is this one. Per the Phase 1 audit, `ExternalSourceKind` is removed
(not kept alongside this enum, and no mapping function translates
between them) -- `business.ExternalBusinessRecord.source_kind` now
types directly against `SourceKind` below, so there is exactly one
taxonomy for this concept in the repository, never two.

Eleven members, not the eight named as "Examples" in this sprint's own
Phase 5 list -- three carried forward from `ExternalSourceKind` because
they cover document types Phase 3 explicitly names but Phase 5's
example list does not distinguish: `FINANCIAL_STATEMENT` (a standalone
statement, distinct from a full `ANNUAL_REPORT`), `COMPANY_FILING`
(Phase 3's "SEC filing," distinct from a scheduled annual/quarterly
report), and `TRANSCRIPT` folding in Phase 3's "investor day" and
"capital markets day" alongside earnings calls (same document shape --
a transcribed spoken event -- not a separate category). Avoiding
free-text classification (Phase 5's own instruction) means every real
document type this sprint's design phases named needs a member here,
not just the ones in the shorter example list.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["SourceKind"]


class SourceKind(str, Enum):
    """A closed, growing set. A future provider that surfaces a document
    type not yet named here must add a member, the same discipline
    every other closed taxonomy in this codebase already follows
    (`atlas.analysis_engine.contracts.RiskCategory`,
    `atlas.decision_engine.contracts.EvidenceGapKind`). `UNKNOWN` is the
    deliberate, honest escape hatch for "a real document exists but its
    type could not be determined" -- never a rejection reason by
    itself; see `validation.py`."""

    ANNUAL_REPORT = "annual_report"
    QUARTERLY_REPORT = "quarterly_report"
    FINANCIAL_STATEMENT = "financial_statement"
    COMPANY_FILING = "company_filing"
    TRANSCRIPT = "transcript"
    PRESS_RELEASE = "press_release"
    INVESTOR_PRESENTATION = "investor_presentation"
    MACRO_REPORT = "macro_report"
    NEWS = "news"
    MANUAL_DOCUMENT = "manual_document"
    UNKNOWN = "unknown"
