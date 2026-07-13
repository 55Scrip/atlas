"""Application service for the Question use case (ATLAS-001 Core Loop).

Question is the root of the cycle: no cross-aggregate checks, no
collaborators. This service owns all three use cases needed downstream:
capture, retrieve by id (the existence check consumed by
ObserveFromQuestionService), and retrieve all.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.question.entity import Question
from atlas.core.domain.question.exceptions import QuestionNotFoundError
from atlas.core.domain.question.repository import QuestionRepository
from atlas.core.domain.question.value_objects import QuestionId, Statement


@dataclass(frozen=True)
class CaptureQuestionRequest:
    statement: str
    raised_at: datetime
    note: str | None = None


class QuestionService:
    def __init__(self, repository: QuestionRepository) -> None:
        self._repository = repository

    def capture(self, request: CaptureQuestionRequest) -> Question:
        question = Question.capture(
            statement=Statement(request.statement),
            raised_at=request.raised_at,
            note=request.note,
        )
        self._repository.add(question)
        return question

    def get(self, question_id: QuestionId) -> Question:
        question = self._repository.get(question_id)
        if question is None:
            raise QuestionNotFoundError(f"No Question found with id {question_id}")
        return question

    def list_all(self) -> list[Question]:
        return self._repository.list_all()
