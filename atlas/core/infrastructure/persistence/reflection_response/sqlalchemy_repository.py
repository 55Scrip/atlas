"""SQLAlchemy-backed ReflectionResponseRepository.

Implements the append-only contract literally: `add` is the only write
operation, and it is always an INSERT. There is no update method to call
by accident.

JSON encoding of the nested provenance fields is purely an
infrastructure-layer serialization detail — the domain model itself
(atlas.core.domain.reflection_response.value_objects) stays strongly
typed and is never aware that JSON is involved.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ReflectionResponseId,
    ResponseText,
)
from atlas.core.infrastructure.persistence.reflection_response.table import (
    reflection_responses_table,
)


def _pattern_membership_to_dict(snapshot: PatternMembershipSnapshot) -> dict[str, Any]:
    return {
        "strategy_name": snapshot.strategy_name,
        "member_decision_ids": [str(decision_id) for decision_id in snapshot.member_decision_ids],
    }


def _pattern_membership_from_dict(data: Mapping[str, Any]) -> PatternMembershipSnapshot:
    return PatternMembershipSnapshot(
        strategy_name=data["strategy_name"],
        member_decision_ids=tuple(
            DecisionId(uuid.UUID(value)) for value in data["member_decision_ids"]
        ),
    )


class SqlAlchemyReflectionResponseRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, reflection_response: ReflectionResponse) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                insert(reflection_responses_table).values(**_to_row(reflection_response))
            )

    def get(self, reflection_response_id: ReflectionResponseId) -> ReflectionResponse | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(reflection_responses_table).where(
                        reflection_responses_table.c.id == str(reflection_response_id)
                    )
                )
                .mappings()
                .first()
            )
        return _to_entity(row) if row is not None else None


def _to_row(reflection_response: ReflectionResponse) -> dict[str, Any]:
    provenance = reflection_response.provenance
    return {
        "id": str(reflection_response.id),
        "decision_id": str(reflection_response.decision_id),
        "response_text": reflection_response.response_text.value,
        "reflection_description": provenance.reflection_description,
        "coaching_question_text": provenance.coaching_question_text,
        "grounding_pattern_json": json.dumps(
            _pattern_membership_to_dict(provenance.grounding_pattern)
        ),
        "strategy_signature_patterns_json": json.dumps(
            [_pattern_membership_to_dict(p) for p in provenance.strategy_signature_patterns]
        ),
        "reasoning_context_subject": provenance.reasoning_context_subject,
        "reasoning_context_decision_type": provenance.reasoning_context_decision_type,
        "reasoning_context_confidence": provenance.reasoning_context_confidence,
        "recorded_at": reflection_response.recorded_at.isoformat(),
    }


def _to_entity(row: Mapping[str, Any]) -> ReflectionResponse:
    provenance = ProvenanceSnapshot(
        reflection_description=row["reflection_description"],
        coaching_question_text=row["coaching_question_text"],
        grounding_pattern=_pattern_membership_from_dict(json.loads(row["grounding_pattern_json"])),
        strategy_signature_patterns=tuple(
            _pattern_membership_from_dict(data)
            for data in json.loads(row["strategy_signature_patterns_json"])
        ),
        reasoning_context_subject=row["reasoning_context_subject"],
        reasoning_context_decision_type=row["reasoning_context_decision_type"],
        reasoning_context_confidence=row["reasoning_context_confidence"],
    )
    return ReflectionResponse(
        id=ReflectionResponseId(uuid.UUID(row["id"])),
        decision_id=DecisionId(uuid.UUID(row["decision_id"])),
        response_text=ResponseText(row["response_text"]),
        provenance=provenance,
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
    )
