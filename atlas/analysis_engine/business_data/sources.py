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

Twelve members, not the eight named as "Examples" in ATLAS-022's own
Phase 5 list -- three carried forward from `ExternalSourceKind` because
they cover document types ATLAS-022's Phase 3 explicitly names but its
Phase 5 example list does not distinguish: `FINANCIAL_STATEMENT` (a
standalone statement, distinct from a full `ANNUAL_REPORT`),
`COMPANY_FILING` (ATLAS-022 Phase 3's "SEC filing," distinct from a
scheduled annual/quarterly report), and `TRANSCRIPT` folding in
"investor day" and "capital markets day" alongside earnings calls (same
document shape -- a transcribed spoken event -- not a separate
category). Avoiding free-text classification (Phase 5's own
instruction) means every real document type named across both sprints
needs a member here, not just the ones in the shorter example list.
`MARKET_DATA_SNAPSHOT` (ATLAS-024) is the twelfth, added when Valuation
needed a document type for current market data.
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

    MARKET_DATA_SNAPSHOT = "market_data_snapshot"
    """ATLAS-024: a canonical record of *current market data* (share
    price, shares outstanding) as of a point in time -- deliberately
    still a `BusinessRecord`, ingested through the identical
    validate/normalize/version pipeline every other document uses, not
    a second parallel "MarketRecord" type. Phase 5's "fundamental
    company data vs. current market data" boundary is real and
    enforced -- but it lives in which *fact taxonomy* reads a record's
    `metadata` (`atlas.analysis_engine.business_facts` for fundamentals,
    `atlas.analysis_engine.valuation.facts` for this), not in a second
    ingestion system. One canonical data layer, two disjoint fact
    vocabularies reading from it."""

    COMPANY_PROFILE = "company_profile"
    """Investment Case Engine v1 slice: a canonical record of a
    company's own descriptive identity (name, exchange, sector,
    industry, country, description) as currently reported by a
    provider -- structural in the same sense every other member here
    is: this taxonomy member says such a document exists and where it
    came from, never what a downstream reader should conclude from it.
    Deliberately a distinct kind from `MARKET_DATA_SNAPSHOT`: identity
    fields describe *what the company is*, not *what it is worth right
    now* -- conflating the two into one document type would make a
    consumer that wants only identity (or only market data) filter by
    field presence instead of by `document_type`, the exact ambiguity
    this taxonomy exists to avoid."""
