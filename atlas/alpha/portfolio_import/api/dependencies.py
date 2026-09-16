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

    Built here rather than inside the import package because identity lives
    behind `canonical_security_gate` -- the sanctioned boundary, the same one
    `business_data_refresh` goes through. The preview service receives a
    plain callable and keeps no dependency on the security master, the
    canonical aggregate or the provider.

    A real provider call happens only when a row carries a valid ISIN *and*
    the master cannot already answer it, so a ticker-only import and a
    re-import both cost nothing.
    """
    from atlas.alpha.canonical_security_gate.import_resolution import (
        ImportedIdentity,
        resolve_imported_identity,
    )
    from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalSecurityRepository
    from atlas.alpha.canonical_security.table import create_canonical_security_tables
    from atlas.alpha.security_identity_evidence.openfigi_adapter import map_isin

    create_canonical_security_tables(engine)
    master = SqlAlchemyCanonicalSecurityRepository(engine)

    def resolve(*, ticker, company_name, isin, market, account_currency):
        return resolve_imported_identity(
            ImportedIdentity(
                ticker=ticker, company_name=company_name, isin=isin,
                market=market, account_currency=account_currency,
            ),
            master=master,
            map_isin_fn=map_isin,
        )

    return resolve
