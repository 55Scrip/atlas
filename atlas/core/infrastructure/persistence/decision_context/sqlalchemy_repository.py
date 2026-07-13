"""SQLAlchemy-backed DecisionContextRepository.

`add` is the only write operation and is always an INSERT. The
`decision_id` column's UNIQUE constraint enforces "at most one
DecisionContext per Decision" at the database level too, translated back
into the domain's own DuplicateDecisionContextError so infrastructure
details never leak past this module.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.entity import DecisionContext
from atlas.core.domain.decision_context.exceptions import DuplicateDecisionContextError
from atlas.core.domain.decision_context.value_objects import (
    AlternativesConsidered,
    ContextId,
    Situation,
    Uncertainties,
)
from atlas.core.infrastructure.persistence.decision_context.table import decision_contexts_table


class SqlAlchemyDecisionContextRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, context: DecisionContext) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(insert(decision_contexts_table).values(**_to_row(context)))
        except IntegrityError as exc:
            raise DuplicateDecisionContextError(
                f"DecisionContext already exists for Decision {context.decision_id}"
            ) from exc

    def get_by_decision_id(self, decision_id: DecisionId) -> DecisionContext | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(decision_contexts_table).where(
                    decision_contexts_table.c.decision_id == str(decision_id)
                )
            ).mappings().first()
        return _to_context(row) if row is not None else None


def _to_row(context: DecisionContext) -> dict[str, Any]:
    return {
        "context_id": str(context.context_id),
        "decision_id": str(context.decision_id),
        "situation": context.situation.value,
        "portfolio_relevance": context.portfolio_relevance,
        "capital_considerations": context.capital_considerations,
        "alternatives_considered": json.dumps(list(context.alternatives_considered)),
        "uncertainties": json.dumps(list(context.uncertainties)),
        "captured_at": context.captured_at.isoformat(),
        "recorded_at": context.recorded_at.isoformat(),
    }


def _to_context(row: Mapping[str, Any]) -> DecisionContext:
    return DecisionContext(
        context_id=ContextId(uuid.UUID(row["context_id"])),
        decision_id=DecisionId(uuid.UUID(row["decision_id"])),
        situation=Situation(row["situation"]),
        captured_at=datetime.fromisoformat(row["captured_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        portfolio_relevance=row["portfolio_relevance"],
        capital_considerations=row["capital_considerations"],
        alternatives_considered=AlternativesConsidered(tuple(json.loads(row["alternatives_considered"]))),
        uncertainties=Uncertainties(tuple(json.loads(row["uncertainties"]))),
    )
