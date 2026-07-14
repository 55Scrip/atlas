"""Composition root for Reflection History (ATLAS-010).

Not imported by pattern_recognition/strategy_signature/decision_reflection/
decision_coach/decision_timeline's own composition roots — Reflection
History is read-isolated from every other Understanding capability,
exactly as Reflection Response itself is (ATLAS-009-D §12).

Deliberately does not resolve or bootstrap Investor Identity.
create_reflection_history_tables ensures only the schema this module
reads from exists; build_reflection_history_query only wires objects
given an already-resolved owner. Investor Identity's own bootstrap
(atlas.core.application.investor_identity.composition.resolve_investor_identity),
which can perform one-time writes on an uninitialized or legacy store,
is a separate, explicit prerequisite step the caller (cli.py) performs
first — never hidden inside either function here.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.reflection_history.query import ReflectionHistoryQuery
from atlas.core.application.reflection_response.composition import (
    create_reflection_response_tables,
)
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.reflection_response.sqlalchemy_repository import (
    SqlAlchemyReflectionResponseRepository,
)


def create_reflection_history_tables(engine: Engine) -> None:
    """Ensure the tables Reflection History reads from exist.

    Purely a schema-existence concern — Reflection History itself never
    writes a row into any of them.
    """
    create_reflection_response_tables(engine)
    create_decision_table(engine)


def build_reflection_history_query(
    engine: Engine, owner_user_id: UserId
) -> ReflectionHistoryQuery:
    """Assemble a read-only ReflectionHistoryQuery for an already-resolved
    owner. Performs no writes and does not resolve or bootstrap Investor
    Identity itself — the caller must call
    resolve_investor_identity(engine) first, as a separate, explicit
    prerequisite step, and pass its result in here.
    """
    repository = SqlAlchemyReflectionResponseRepository(engine)
    return ReflectionHistoryQuery(repository, owner_user_id)
