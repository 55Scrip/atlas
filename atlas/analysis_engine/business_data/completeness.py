"""Data completeness predicate (Company Data Foundation v1).

A pure, deterministic structural checklist over already-ingested
`BusinessRecord`s -- "do I have the minimum data package required for a
first Investment Case," never a numeric score, never an opaque
0-100 rating. Every field on `DataCompleteness` is a direct structural
fact (a `SourceKind` present or absent, a period count), the same
"facts, not judgments" discipline this whole package already applies to
`BusinessRecord` itself.

**Why this exists.** `atlas.alpha.business_data_refresh.service
.ensure_company_enriched`'s own freshness gate was, before this sprint,
"does this company have at least one persisted `BusinessRecord` of any
kind" -- true even for a company with a single stray
`MARKET_DATA_SNAPSHOT` and nothing else, which then permanently blocked
any future enrichment attempt for that company. `is_minimally_complete`
below is the real, narrow improvement that gate now checks instead: has
Atlas actually recovered company identity or fundamentals from *some*
provider, not merely "was any request ever made." See that module's own
docstring for exactly how this bounds retries (it stops the moment
either provider succeeds with real identity/fundamentals; it does not
retry forever for a company neither provider can ever serve).
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["DataCompleteness", "assess_data_completeness"]


@dataclass(frozen=True)
class DataCompleteness:
    """A structural checklist, not a score. Every field is independently
    meaningful -- a caller that only cares about one dimension (e.g. "do
    we have any fundamentals history at all") reads that field directly
    rather than inferring it from a collapsed number."""

    has_company_profile: bool
    has_financial_statements: bool
    financial_statement_period_count: int
    has_market_snapshot: bool
    is_minimally_complete: bool
    """`True` when Atlas has recovered real company identity
    (`COMPANY_PROFILE`) or at least one real fundamentals period
    (`FINANCIAL_STATEMENT`) for this company -- the narrow "worth
    treating as enriched" predicate `ensure_company_enriched` uses.
    Deliberately does NOT require `has_market_snapshot`: a company with
    real fundamentals but no market data (e.g. Alpha Vantage
    unconfigured) still has a materially useful first Investment Case;
    a company with only a market snapshot and nothing else does not."""


def assess_data_completeness(business_records: tuple[BusinessRecord, ...]) -> DataCompleteness:
    """Deterministic: identical `business_records` always produce a
    deeply equal `DataCompleteness`. Reads only `document_type`/
    `period_end`/`period_start` -- never a `metadata` value, since this
    predicate answers "which kinds of document exist," never "how good
    is the data inside them" (a different, evaluator-level question
    this module deliberately does not answer)."""
    has_profile = any(record.document_type is SourceKind.COMPANY_PROFILE for record in business_records)
    statement_periods = {
        record.period_end or record.period_start
        for record in business_records
        if record.document_type is SourceKind.FINANCIAL_STATEMENT
    }
    has_statements = len(statement_periods) > 0
    has_market = any(record.document_type is SourceKind.MARKET_DATA_SNAPSHOT for record in business_records)
    return DataCompleteness(
        has_company_profile=has_profile,
        has_financial_statements=has_statements,
        financial_statement_period_count=len(statement_periods),
        has_market_snapshot=has_market,
        is_minimally_complete=has_profile or has_statements,
    )
