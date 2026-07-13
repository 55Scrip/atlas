"""Repository interface for the Question aggregate.

Insert-only: no update, no delete. No foreign keys — Question is the
root of the Core Loop and references nothing upstream.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.question.entity import Question
from atlas.core.domain.question.value_objects import QuestionId


class QuestionRepository(Protocol):
    def add(self, question: Question) -> None:
        """Insert a new Question."""
        ...

    def get(self, question_id: QuestionId) -> Question | None:
        """Return a single Question by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Question]:
        """Return every Question ever raised, in chronological order:
        raised_at ascending, then recorded_at ascending, then question_id
        as a deterministic final tie-breaker.
        """
        ...
