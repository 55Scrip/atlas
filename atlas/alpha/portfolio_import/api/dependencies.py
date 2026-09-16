"""Composition wiring for the unified import preview endpoint.

Reuses `atlas.alpha.portfolio.api.dependencies.get_alpha_portfolio_store`
read-only, exactly like `portfolio_fit`/other Alpha packages already
compose across module boundaries -- only to read the current holdings'
tickers for against-existing-portfolio duplicate detection; nothing
here ever writes to that store.

`get_security_discovery_indexes` is reused directly from
`security_discovery`'s own composition module -- same process-local
cached `SecTitleIndexSource` singleton every other caller of that
service shares, not a second fetch/cache built here.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_import.alias_store import ResolvedAliasStore
from atlas.alpha.portfolio_import.alias_table import create_resolved_alias_table
from atlas.alpha.portfolio_import.resolution_service import DiscoverFn, LookupAliasFn
from atlas.alpha.portfolio_import.service import PortfolioImportPreviewService
from atlas.alpha.security_discovery.api.dependencies import get_security_discovery_indexes
from atlas.alpha.security_discovery.models import SecurityCandidate
from atlas.alpha.security_discovery.service import (
    TickerIndex,
    TitleIndex,
    discover_security_candidates,
)
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_portfolio_import_preview_service() -> PortfolioImportPreviewService:
    return PortfolioImportPreviewService()


def get_resolved_alias_store(
    engine: Engine = Depends(get_decision_engine),
) -> ResolvedAliasStore:
    create_resolved_alias_table(engine)
    return ResolvedAliasStore(engine)


def get_resolved_alias_lookup_fn(
    store: ResolvedAliasStore = Depends(get_resolved_alias_store),
) -> LookupAliasFn:
    return store.lookup


def get_existing_tickers(
    store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
) -> frozenset[str]:
    state = store.get()
    if state is None:
        return frozenset()
    return frozenset(holding.ticker for holding in state.holdings)


def get_security_discovery_fn(
    indexes: tuple[TitleIndex, TickerIndex] = Depends(get_security_discovery_indexes),
) -> DiscoverFn:
    title_index, ticker_index = indexes

    def _discover(query: str) -> tuple[SecurityCandidate, ...]:
        return discover_security_candidates(query, title_index=title_index, ticker_index=ticker_index)

    return _discover


def get_import_identity_resolver(engine: Engine = Depends(get_decision_engine)):
    """The seam that turns a captured ISIN into a security.

    Delegates entirely to `canonical_security_gate.factory`, the sanctioned
    integration boundary -- this package must never import
    `canonical_security` or `canonical_security_resolution` itself, exactly
    as `business_data_refresh` must not (see both packages' own
    integration-safety guard tests). The preview service receives a plain
    callable and keeps no dependency on the security master, the canonical
    aggregate or the provider.
    """
    from atlas.alpha.canonical_security_gate.factory import build_import_identity_resolver

    return build_import_identity_resolver(engine)
