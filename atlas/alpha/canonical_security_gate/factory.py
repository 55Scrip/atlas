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
