"""Provider abstraction (ATLAS-022, Phase 4).

The Analysis Engine must never depend on a specific provider -- every
future data source (SEC EDGAR, Companies House, Financial Modeling
Prep, Polygon, Alpha Vantage, a manual-upload form, anything not yet
named) implements this one interface and nothing downstream changes.

**No external API integration happens in this sprint.** The Phase 1
audit found a real, live, network-calling provider already in the
repository -- `atlas.providers.yahoo.YahooFinanceProvider` -- but it is
part of the legacy CLI tree (confirmed unreachable from the live
FastAPI app), returns the fabricated-shape `CompanyAnalysis` type
ATLAS-021 already ruled out, and feeds hand-rolled point-based scoring
functions. It is not reused here, and this module's own `Protocol` is
deliberately named `BusinessDataProvider` rather than a bare
`Provider` or `CompanyDataProvider`, so it is never mistaken for -- or
confused with -- that legacy interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable

from atlas.analysis_engine.business_data.models import RawBusinessDocument

__all__ = [
    "BusinessDataProvider",
    "HistoricalMarketDataProvider",
    "CompanyProfileProvider",
    "StaticBusinessDataProvider",
]


@runtime_checkable
class BusinessDataProvider(Protocol):
    """The one stable contract every future provider implements.
    `evaluated_at` is accepted (never a wall-clock read inside a
    conforming provider) so a real implementation can bound freshness
    or a time range deterministically, the same discipline every other
    `evaluated_at`/`generated_at` parameter in this codebase already
    follows. Returns raw, unvalidated documents -- `validation.py` is
    always the next stage, never something a provider does itself.
    """

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        ...


@runtime_checkable
class HistoricalMarketDataProvider(Protocol):
    """(ATLAS-032) An optional, second capability a market-data
    provider may additionally implement -- checked for at the
    orchestration layer (`atlas.alpha.business_data_refresh.service
    .refresh_company_data`) via `isinstance` against this
    `runtime_checkable` Protocol, exactly the same pattern
    `BusinessDataProvider` itself already establishes. Deliberately not
    folded into `BusinessDataProvider.fetch` itself: fundamentals
    providers (SEC EDGAR) have no historical-price concept at all, and
    forcing every provider to implement a method it can never
    meaningfully serve would be a worse interface than an optional,
    duck-typed capability a caller can check for.

    `filing_dates` names the dates a caller already knows it needs
    historical price coverage for (typically every distinct
    fundamental's own `published_at` date) -- the provider never
    invents its own list of dates to fetch; the caller's own knowledge
    of what it needs stays the caller's responsibility, keeping this
    provider a dumb, stateless translator of "give me prices for these
    dates" into real API calls, same as `fetch` itself.
    """

    def fetch_historical_snapshots(
        self, *, company_identifier: str, filing_dates: tuple[date, ...], evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        ...


@runtime_checkable
class CompanyProfileProvider(Protocol):
    """(Investment Case Engine v1 slice) An optional, second capability
    a provider may additionally implement -- checked for at the
    orchestration layer (`refresh_company_data`) via `isinstance`
    against this `runtime_checkable` Protocol, the identical pattern
    `HistoricalMarketDataProvider` already establishes. Deliberately
    not folded into `BusinessDataProvider.fetch` itself: a fundamentals
    provider (SEC EDGAR) has no company-identity concept to serve, and
    a provider that already fetches identity fields as a byproduct of
    another call it makes (e.g. Alpha Vantage's `OVERVIEW`) should be
    free to serve this from that same, already-fetched response rather
    than being forced to originate a second network call it doesn't
    need.

    Returns `()` (never fabricates) when no identity fields are known
    for `company_identifier`, mirroring `BusinessDataProvider.fetch`'s
    own honest-absence contract.
    """

    def fetch_company_profile(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        ...


@dataclass(frozen=True)
class StaticBusinessDataProvider:
    """A real, working `BusinessDataProvider` backed by an in-memory
    tuple supplied at construction -- not a mock standing in for
    something unfinished: it genuinely provides exactly the documents
    it was given, deterministically, every call, with no network or
    file I/O anywhere in it. Exists to (a) prove the Provider contract
    is real and testable today, and (b) demonstrate exactly where a
    future SEC/EDGAR/Companies House/FMP/manual-upload provider plugs
    in -- implement this same one method, return `RawBusinessDocument`
    tuples, and every downstream stage (validation, normalization,
    versioning, Analysis Engine wiring) needs no change at all.
    """

    documents: tuple[RawBusinessDocument, ...] = ()

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        del evaluated_at  # a static provider has no freshness window to bound; a real one would use it
        return tuple(document for document in self.documents if document.company == company_identifier)
