"""Composition wiring for the `BusinessRecord` store (ATLAS-031).

Same shared-engine pattern every other repository's dependencies
module uses -- one physical `atlas.db` file, reused via `decision`'s
own `get_decision_engine`.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


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
    set," not two."""
    return (SecEdgarFundamentalsProvider(), AlphaVantageMarketDataProvider())
