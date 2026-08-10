"""`FinancialPeriod`/`MarketSnapshot` extraction (Investment Case Engine
v1 slice).

A small, read-only projection over already-ingested `BusinessRecord`s,
exposing exactly the raw fields the current provider integrations
actually populate -- never a field this codebase's providers do not
supply. Per SEC EDGAR's own real tag coverage
(`atlas.business_data_providers.sec_edgar._CONCEPT_TAGS`): revenue,
free cash flow, capital expenditure, share buybacks, share issuance,
and dividends. Net income, EPS, and raw cash/debt balances are
deliberately absent below -- no provider in this codebase currently
supplies them, and fabricating a field no provider populates would
violate this sprint's own "do not invent fields unsupported by current
provider contracts" instruction. Per Alpha Vantage's own coverage: the
current share price, shares outstanding, and currency.

Distinct from `atlas.analysis_engine.business_facts`/`valuation.facts`:
those extract canonical, evaluator-ready *facts* for Growth/Valuation's
own reasoning; this module extracts the same underlying numbers for
direct, unevaluated display -- "what does Atlas actually know," not
"what has Atlas concluded from it."
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["FinancialPeriod", "MarketSnapshot", "extract_financial_history", "extract_market_snapshot"]


@dataclass(frozen=True)
class FinancialPeriod:
    """One fiscal period's raw, structural fundamentals -- exactly the
    metadata keys `SecEdgarFundamentalsProvider.fetch` populates.
    `None` on any field means this period's own SEC filing did not
    report it (or a fallback tag could not be resolved), never a
    computed or assumed zero."""

    period_start: date | None
    period_end: date | None
    revenue: float | None
    free_cash_flow: float | None
    capital_expenditure: float | None
    share_buybacks: float | None
    share_issuance: float | None
    dividends: float | None
    currency: str | None


@dataclass(frozen=True)
class MarketSnapshot:
    """The most recent current-market-data snapshot -- exactly the
    metadata keys `AlphaVantageMarketDataProvider.fetch` populates."""

    as_of: datetime
    share_price: float | None
    shares_outstanding: float | None
    currency: str | None


def extract_financial_history(business_records: tuple[BusinessRecord, ...]) -> tuple[FinancialPeriod, ...]:
    """Every `FINANCIAL_STATEMENT` record among `business_records`
    (the caller's already-`latest_versions`-filtered set), oldest period
    first -- a natural chronological reading order for a history view."""
    statements = [
        record for record in business_records if record.document_type is SourceKind.FINANCIAL_STATEMENT
    ]
    statements.sort(key=lambda record: record.period_end or record.published_at.date())
    periods: list[FinancialPeriod] = []
    for record in statements:
        metadata = record.metadata
        periods.append(
            FinancialPeriod(
                period_start=record.period_start,
                period_end=record.period_end,
                revenue=metadata.get("revenue"),
                free_cash_flow=metadata.get("free_cash_flow"),
                capital_expenditure=metadata.get("capital_expenditure"),
                share_buybacks=metadata.get("share_buybacks"),
                share_issuance=metadata.get("share_issuance"),
                dividends=metadata.get("dividends"),
                currency=metadata.get("currency"),
            )
        )
    return tuple(periods)


def extract_market_snapshot(business_records: tuple[BusinessRecord, ...]) -> MarketSnapshot | None:
    """Returns `None` if no `MARKET_DATA_SNAPSHOT` record exists among
    `business_records` -- never a snapshot with every field blank. Where
    more than one is present (a current snapshot plus historical ones,
    ATLAS-032), the most recently published one wins."""
    snapshots = [
        record for record in business_records if record.document_type is SourceKind.MARKET_DATA_SNAPSHOT
    ]
    if not snapshots:
        return None
    latest = max(snapshots, key=lambda record: record.published_at)
    metadata = latest.metadata
    return MarketSnapshot(
        as_of=latest.published_at,
        share_price=metadata.get("share_price"),
        shares_outstanding=metadata.get("shares_outstanding"),
        currency=metadata.get("currency"),
    )
