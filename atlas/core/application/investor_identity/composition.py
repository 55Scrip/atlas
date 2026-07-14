"""Composition for Investor Identity (ATLAS-009B).

`resolve_investor_identity` is the one shared, reusable entry point:
any composition root holding an Engine — today's conversation, or a
future Reflection History / bootstrap CLI — can call it and get the
same UserId, with no conversation or Decision required. It imports no
SQLAlchemy table objects and issues no raw persistence statements
itself — those stay entirely inside the infrastructure layer.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.domain.decision.value_objects import UserId
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.investor_identity.sqlalchemy_repository import (
    SqlAlchemyInvestorIdentityRepository,
)
from atlas.core.infrastructure.persistence.investor_identity.table import (
    create_investor_identity_table,
)


def resolve_investor_identity(engine: Engine) -> UserId:
    """Resolve the store's single durable Investor Identity.

    Guarantees both tables this capability needs exist first — callers
    never need to know or coordinate table creation themselves.
    """
    create_investor_identity_table(engine)
    create_decision_table(engine)
    return SqlAlchemyInvestorIdentityRepository(engine).resolve()
