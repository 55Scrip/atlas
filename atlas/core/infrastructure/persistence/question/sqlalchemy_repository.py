"""SQLAlchemy-backed QuestionRepository.

`add` is the only write operation and is always an INSERT. No foreign
keys, no uniqueness constraint beyond the primary key.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.question.entity import Question
from atlas.core.domain.question.value_objects import QuestionId, Statement
from atlas.core.infrastructure.persistence.question.table import questions_table


class SqlAlchemyQuestionRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, question: Question) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(questions_table).values(**_to_row(question)))

    def get(self, question_id: QuestionId) -> Question | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(questions_table).where(questions_table.c.question_id == str(question_id))
            ).mappings().first()
        return _to_question(row) if row is not None else None

    def list_all(self) -> list[Question]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(questions_table).order_by(questions_table.c.recorded_at)
            ).mappings().all()
        questions = [_to_question(row) for row in rows]
        # raised_at preserves its investor-supplied offset (not
        # normalized to UTC), so a text-based ORDER BY on that column
        # would not reflect true chronological order across mixed
        # offsets. Sort here instead, comparing tz-aware datetimes.
        questions.sort(key=lambda q: (q.raised_at, q.recorded_at, q.id.value))
        return questions


def _to_row(question: Question) -> dict[str, Any]:
    return {
        "question_id": str(question.id),
        "statement": question.statement.value,
        "note": question.note,
        "raised_at": question.raised_at.isoformat(),
        "recorded_at": question.recorded_at.isoformat(),
    }


def _to_question(row: Mapping[str, Any]) -> Question:
    return Question(
        id=QuestionId(uuid.UUID(row["question_id"])),
        statement=Statement(row["statement"]),
        raised_at=datetime.fromisoformat(row["raised_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        note=row["note"],
    )
