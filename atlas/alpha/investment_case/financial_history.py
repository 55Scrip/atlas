"""`FinancialPeriod`/`MarketSnapshot` extraction (Investment Case Engine
v1 slice; extended Company Data Foundation v1).

A small, read-only projection over already-ingested `BusinessRecord`s,
exposing exactly the raw fields the current provider integrations
actually populate -- never a field this codebase's providers do not
supply. Per SEC EDGAR's own real tag coverage
(`atlas.business_data_providers.sec_edgar._DURATION_CONCEPT_TAGS`/
`_INSTANT_CONCEPT_TAGS`): revenue, operating income, net income, EPS,
free cash flow, capital expenditure, share buybacks, share issuance,
dividends, cash, total debt, and shares outstanding. Per Alpha
Vantage's own coverage: the current share price, shares outstanding,
and currency, plus company identity (name/exchange/sector/industry/
country/description/currency/fiscal year end, see
`company_profile.py`).

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
    operating_income: float | None
    net_income: float | None
    eps: float | None
    free_cash_flow: float | None
    capital_expenditure: float | None
    share_buybacks: float | None
    share_issuance: float | None
    dividends: float | None
    cash: float | None
    total_debt: float | None
    shares_outstanding: float | None
    currency: str | None


@dataclass(frozen=True)
class MarketSnapshot:
    """The most recent current-market-data snapshot -- exactly the
    metadata keys `AlphaVantageMarketDataProvider.fetch` populates,
    plus `market_cap`, deterministically derived here (never persisted
    -- see this sprint's own "do not persist a derived metric if it
    can be cheaply and deterministically recomputed" instruction) as
    `share_price * shares_outstanding` whenever both are known."""

    as_of: datetime
    share_price: float | None
    shares_outstanding: float | None
    currency: str | None
    market_cap: float | None = None
    #: Internal Alpha Stabilization 1 (MSFT price root cause fix): the
    #: real trading day this price is *from* (the record's own
    #: `period_end`) -- distinct from `as_of` (`published_at`, when
    #: Atlas happened to fetch it). Freshness is judged against this,
    #: never against `as_of` -- see `atlas.analysis_engine.business
    #: _data.freshness.is_price_fresh`.
    trading_day: date | None = None


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
                operating_income=metadata.get("operating_income"),
                net_income=metadata.get("net_income"),
                eps=metadata.get("eps"),
                free_cash_flow=metadata.get("free_cash_flow"),
                capital_expenditure=metadata.get("capital_expenditure"),
                share_buybacks=metadata.get("share_buybacks"),
                share_issuance=metadata.get("share_issuance"),
                dividends=metadata.get("dividends"),
                cash=metadata.get("cash"),
                total_debt=metadata.get("total_debt"),
                shares_outstanding=metadata.get("shares_outstanding"),
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
    share_price = metadata.get("share_price")
    shares_outstanding = metadata.get("shares_outstanding")
    market_cap = (
        share_price * shares_outstanding
        if isinstance(share_price, (int, float)) and isinstance(shares_outstanding, (int, float))
        else None
    )
    return MarketSnapshot(
        as_of=latest.published_at,
        share_price=share_price,
        shares_outstanding=shares_outstanding,
        currency=metadata.get("currency"),
        market_cap=market_cap,
        trading_day=latest.period_end,
    )
