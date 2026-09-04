"""Sprint O -- production wiring factory for `CanonicalSecurityIdentityGate`.

The one place outside this package's own tests that constructs the
gate's dependencies from a live SQLAlchemy `Engine`. Every production
caller (`atlas.alpha.business_data_refresh.api.dependencies`,
`atlas.alpha.business_data_refresh.cli`) calls `build_identity_gate`
rather than importing `atlas.alpha.canonical_security`/
`canonical_security_resolution` directly -- this package is the sole
sanctioned integration boundary the updated guard tests in both of
those packages' own test directories document and enforce.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.alpha.canonical_security.repository import (
    SqlAlchemyCanonicalIssuerRepository,
    SqlAlchemyCanonicalSecurityRepository,
)
from atlas.alpha.canonical_security.table import create_canonical_security_tables
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.canonical_security_resolution.repository import SqlAlchemyResolutionRepository
from atlas.alpha.canonical_security_resolution.service import CanonicalSecurityResolutionService
from atlas.alpha.canonical_security_resolution.table import create_resolution_tables

__all__ = ["build_identity_gate"]


def build_identity_gate(engine: Engine) -> CanonicalSecurityIdentityGate:
    """Creates both the Sprint M (`canonical_securities`/...) and
    Sprint N (`resolution_records`/`resolution_evidence`) table sets on
    first use, exactly like every other dependency-construction
    function in this codebase creates its own tables (e.g.
    `business_data_refresh.api.dependencies.get_business_record_repository`)."""
    create_canonical_security_tables(engine)
    create_resolution_tables(engine)
    return CanonicalSecurityIdentityGate(
        resolution_service=CanonicalSecurityResolutionService(),
        canonical_security_repository=SqlAlchemyCanonicalSecurityRepository(engine),
        canonical_issuer_repository=SqlAlchemyCanonicalIssuerRepository(engine),
        resolution_repository=SqlAlchemyResolutionRepository(engine),
    )


def build_provider_symbol_resolver(engine):
    """The sanctioned seam for provider symbol routing, built here for
    the same reason `build_identity_gate` is: `business_data_refresh`
    may not import `canonical_security` directly, so this package hands
    it a plain callable instead of a domain object.

    Returns `(canonical_ticker, provider_name) -> symbol to send`. The
    routing table is read once, here, rather than per request. Routes
    are stored facts; nothing in this path derives one spelling from
    another, and a ticker with no stored route goes out unchanged.
    """
    from atlas.alpha.canonical_security.provider_routing import (
        build_routing_table,
        load_routes,
        resolve_provider_symbol,
    )
    from atlas.alpha.canonical_security.table import create_canonical_security_tables

    create_canonical_security_tables(engine)
    with engine.connect() as connection:
        routing_table = build_routing_table(load_routes(connection))

    def resolve(canonical_ticker: str, provider_name: str | None) -> str:
        return resolve_provider_symbol(canonical_ticker, provider_name, routing_table=routing_table)

    return resolve
