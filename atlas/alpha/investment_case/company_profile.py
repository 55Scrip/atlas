"""`CompanyProfile` extraction (Investment Case Engine v1 slice).

A small, read-only projection over already-ingested `BusinessRecord`s --
exactly the same "reuse the currently supported financial data
structures" discipline `business_facts.extraction`/`valuation.facts`
already establish for Growth/Valuation, applied here to the newly-added
`SourceKind.COMPANY_PROFILE` document type instead. Never imports a
provider, never makes a network call, never fabricates a field: a
company with no ingested `COMPANY_PROFILE` record (SEC EDGAR has none;
Alpha Vantage's OVERVIEW came back empty; the provider is unconfigured)
simply has no `CompanyProfile` -- an honest `None`, not a guessed one.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["CompanyProfile", "extract_company_profile"]


@dataclass(frozen=True)
class CompanyProfile:
    """Descriptive company identity, as currently known -- every field
    beyond `ticker` is `None` unless a provider actually reported it.
    No sector/industry taxonomy is normalized or validated here; the
    value is passed through exactly as the provider reported it."""

    ticker: str
    name: str | None
    exchange: str | None
    sector: str | None
    industry: str | None
    country: str | None
    description: str | None
    as_of: datetime
    currency: str | None = None
    """(Company Data Foundation v1) The provider's own reported
    reporting currency (e.g. Alpha Vantage's OVERVIEW `Currency`
    field) -- descriptive identity, distinct from a specific financial
    fact's own `currency` metadata key on `FinancialPeriod`/
    `MarketSnapshot`, which always wins when both are known."""
    fiscal_year_end: str | None = None
    """(Company Data Foundation v1) The provider's own reported fiscal
    year-end month (e.g. `"December"`) -- passed through exactly as
    reported, never normalized into a date."""


def extract_company_profile(
    ticker: str, business_records: tuple[BusinessRecord, ...]
) -> CompanyProfile | None:
    """Returns `None` if no `COMPANY_PROFILE` record exists for this
    company among `business_records` (the caller's already-`latest_
    versions`-filtered set) -- never a `CompanyProfile` with every field
    blank. Where more than one profile record is somehow present, the
    most recently published one wins, matching every other "latest wins"
    rule in this codebase."""
    profile_records = tuple(
        record for record in business_records if record.document_type is SourceKind.COMPANY_PROFILE
    )
    if not profile_records:
        return None
    latest = max(profile_records, key=lambda record: record.published_at)
    metadata = latest.metadata
    return CompanyProfile(
        ticker=ticker,
        name=metadata.get("name"),
        exchange=metadata.get("exchange"),
        sector=metadata.get("sector"),
        industry=metadata.get("industry"),
        country=metadata.get("country"),
        description=metadata.get("description"),
        as_of=latest.published_at,
        currency=metadata.get("currency"),
        fiscal_year_end=metadata.get("fiscal_year_end"),
    )
