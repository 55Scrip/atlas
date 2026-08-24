"""Composition wiring for the `BusinessRecord` store (ATLAS-031).

Same shared-engine pattern every other repository's dependencies
module uses -- one physical `atlas.db` file, reused via `decision`'s
own `get_decision_engine`.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.price_refresh import PriceRefreshCoordinator
from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.sec_edgar import SecEdgarFilingHistoryProvider, SecEdgarFundamentalsProvider
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


@lru_cache
def get_price_refresh_coordinator() -> PriceRefreshCoordinator:
    """Internal Alpha Stabilization 1 (MSFT price root cause fix): one
    shared, process-lifetime coordinator (`@lru_cache`, the identical
    pattern `get_decision_engine` already established) -- its whole
    purpose is deduping/serializing across *different* requests, so it
    must be the same instance every request gets, never a fresh one
    per request the way most other `Depends()` providers here are."""
    return PriceRefreshCoordinator()


def get_alpha_vantage_quota_tracker(
    engine: Engine = Depends(get_decision_engine),
) -> AlphaVantageQuotaTracker:
    """Internal Alpha Stabilization 1 (MSFT price root cause fix): the
    one shared, persisted daily call-budget tracker -- see that
    class's own module docstring for why 25/day, confirmed live
    against the real key."""
    return AlphaVantageQuotaTracker(engine)


def get_business_record_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyBusinessRecordRepository:
    create_business_record_table(engine)
    return SqlAlchemyBusinessRecordRepository(engine)


def get_canonical_security_identity_gate(
    engine: Engine = Depends(get_decision_engine),
) -> CanonicalSecurityIdentityGate:
    """Sprint O -- the one production wiring point for
    `CanonicalSecurityIdentityGate`. Same shared-engine pattern every
    other dependency function in this module already uses (one
    physical `atlas.db` file). Delegates entirely to
    `canonical_security_gate.factory.build_identity_gate` rather than
    constructing `SqlAlchemyCanonicalSecurityRepository`/
    `SqlAlchemyResolutionRepository` here directly -- this module must
    only ever import `canonical_security_gate`, never
    `canonical_security`/`canonical_security_resolution` themselves
    (see those packages' own integration-safety guard tests)."""
    return build_identity_gate(engine)


def get_default_business_data_providers() -> tuple[BusinessDataProvider, ...]:
    """The one place a real, network-calling provider instance is
    constructed for automatic enrichment (Investment Case Engine v1
    slice). `atlas.business_data_providers` is architecturally confined
    to this package (`tests/test_architecture_boundaries.py
    ::test_only_business_data_refresh_imports_business_data_providers`)
    -- callers elsewhere (Watchlist, Portfolio) depend on this function,
    never on the concrete provider classes directly, so that boundary
    is never crossed. Mirrors `cli.py::main`'s own default construction
    exactly -- one real definition of "the current default provider
    set," not two.

    Takes **no** `Depends()`-injected parameters, deliberately -- this
    function must stay callable as a plain function with zero
    arguments, the same contract it already had, because
    `atlas.alpha.portfolio.api.router._run_bulk_enrichment_in_background`
    already calls it directly (never through FastAPI's own dependency
    resolution) from Starlette's background-task thread, the identical
    reason that module's own `get_decision_engine()` call is also a
    plain call, not a `Depends()`. Adding a required `Depends()`
    parameter here broke that real call site (confirmed by the full
    test suite) -- the fix is this function resolving its own
    `AlphaVantageQuotaTracker` internally, via the same plain
    `get_decision_engine()` call already proven safe to make directly.

    Internal Alpha Stabilization 1 (MSFT price root cause fix): the
    Alpha Vantage instance's `on_request` is wired to the shared,
    persisted quota tracker -- every real call any caller of this
    function makes (full enrichment, ingestion refresh, ...) counts
    against the same real daily budget the new price-only refresh also
    respects. `cli.py::main`'s own separate construction is not wired
    to this tracker -- a real, small, disclosed gap (CLI usage is
    manual/developer-only, not a live-app request path)."""
    quota = AlphaVantageQuotaTracker(get_decision_engine())
    return (
        SecEdgarFundamentalsProvider(),
        AlphaVantageMarketDataProvider(on_request=quota.record_call),
        SecEdgarFilingHistoryProvider(),
    )


def get_alpha_vantage_price_provider() -> AlphaVantageMarketDataProvider:
    """Internal Alpha Stabilization 1 (MSFT price root cause fix): a
    dedicated instance for `price_refresh.refresh_price_only`, wired to
    the identical shared quota tracker `get_default_business_data
    _providers` uses (both construct their own `AlphaVantageQuotaTracker`
    the same way, but both read/write the same persisted table, so
    they agree on the real remaining budget regardless). Kept separate
    from that function (rather than fishing the Alpha Vantage instance
    out of its returned tuple) so price-only refresh never accidentally
    depends on the other two providers being constructed too. No
    `Depends()` parameters, for the identical "must stay a plain,
    directly-callable function" reason as `get_default_business_data
    _providers` above -- this one is also captured into a `Background
    Tasks` closure, not resolved fresh on a background thread."""
    quota = AlphaVantageQuotaTracker(get_decision_engine())
    return AlphaVantageMarketDataProvider(on_request=quota.record_call)


#: `SecEdgarFundamentalsProvider`/`AlphaVantageMarketDataProvider` were
#: both built before the Knowledge Provider contract existed
#: (`atlas.alpha.knowledge_provider`) and do not declare a real
#: `.provider_id` attribute -- their own id string only ever appears
#: as a literal inside each provider's own `fetch()` body, on the
#: `RawBusinessDocument`s it constructs. This small, class-keyed
#: fallback (confined to this module -- the one place already allowed
#: to import `atlas.business_data_providers`, per `tests
#: .test_architecture_boundaries::test_only_business_data_refresh_
#: imports_business_data_providers`) bridges that gap for
#: `atlas.alpha.knowledge_orchestration`'s own capability registry
#: without modifying either provider class. Any future provider that
#: properly declares `.provider_id` (like `SecEdgarFilingHistory
#: Provider` already does) never needs an entry here at all.
_LEGACY_PROVIDER_IDS: dict[type, str] = {
    SecEdgarFundamentalsProvider: "sec_edgar",
    AlphaVantageMarketDataProvider: "alpha_vantage",
}


def get_default_business_data_providers_by_id(
    providers: tuple[BusinessDataProvider, ...] = Depends(get_default_business_data_providers),
) -> dict[str, BusinessDataProvider]:
    """Automatic Knowledge Ingestion / Orchestration Frameworks. The
    same default provider set as `get_default_business_data_providers`,
    keyed by the stable id string `atlas.alpha.knowledge_orchestration
    .capability.PROVIDER_CAPABILITIES` uses -- never a second provider
    set, never a second construction path."""
    keyed: dict[str, BusinessDataProvider] = {}
    for provider in providers:
        provider_id = getattr(provider, "provider_id", None) or _LEGACY_PROVIDER_IDS.get(type(provider))
        if provider_id is not None:
            keyed[provider_id] = provider
    return keyed
