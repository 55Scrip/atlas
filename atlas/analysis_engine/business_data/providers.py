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
from datetime import datetime
from typing import Protocol, runtime_checkable

from atlas.analysis_engine.business_data.models import RawBusinessDocument

__all__ = ["BusinessDataProvider", "StaticBusinessDataProvider"]


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
