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

from fastapi import Depends, Request
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


def get_security_discovery_fn(request: Request) -> DiscoverFn:
    """`(query) -> candidates`, with the SEC-backed index built on first
    actual use rather than on every request.

    This deliberately does **not** `Depends(get_security_discovery_indexes)`.
    That dependency calls `SecTitleIndexSource.entries()` eagerly, so
    resolving it built a ~10,000-entry SEC-backed index for *every* import
    preview -- including the common case this endpoint exists to serve: a
    broker export whose rows already carry a Ticker column, where
    `resolve_row` never consults `discover` at all (it is reached only by
    the `elif company_name` branch, after the local registry and the
    learned-alias step). A pasted file with tickers therefore used to
    depend on SEC being reachable for no reason, and a transient outage
    returned a bare 500 on the product's first screen.

    `request` is taken so that dropping the `Depends` does not also drop
    the override seam. `dependency_overrides` is how this endpoint's own
    tests swap the real SEC source for a fixed index, and FastAPI applies
    it only to dependencies it resolves itself -- so a plain module-level
    call here would silently ignore an override that is visibly set, which
    is the same shape of bug as an `ATLAS_CORE_DB_PATH` that is honoured
    everywhere except the running application. The override is therefore
    looked up explicitly, at the moment the index is actually needed.

    The indexes are memoised per request. On the happy path the underlying
    `SecTitleIndexSource` already caches process-wide, so this changes
    nothing; it matters when SEC is *down*, because a failed fetch is
    deliberately not cached (so recovery needs no restart) and
    `resolve_row` can consult `discover` more than once for a single
    unnamed row. Without this, an import of twenty name-only rows during
    an outage would pay the 10-second timeout once per attempt instead of
    once per request -- which is the cost the eager dependency used to
    have, and no worse.
    """
    indexes: list[tuple[TitleIndex, TickerIndex]] = []

    def _resolve_indexes() -> tuple[TitleIndex, TickerIndex]:
        provider = request.app.dependency_overrides.get(
            get_security_discovery_indexes, get_security_discovery_indexes
        )
        return provider()

    def _discover(query: str) -> tuple[SecurityCandidate, ...]:
        if not indexes:
            indexes.append(_resolve_indexes())
        title_index, ticker_index = indexes[0]
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
