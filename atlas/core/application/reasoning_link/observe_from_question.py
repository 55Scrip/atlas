"""Composite application service: Observation answering a Question
(ATLAS-001 Core Loop, step 2 of 10).

Verifies the referenced Question exists, then reuses the existing,
unmodified CaptureObservationService to construct the Observation, and
records the QuestionObservationLink atomically. Never writes to
QuestionRepository or modifies Observation's own construction path.

PROVISIONAL STATUS: the Link half of this operation belongs to the
reasoning_link module — see its module docstring for why.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.application.observation.capture_observation import (
    CaptureObservationRequest,
    CaptureObservationService,
)
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.question.exceptions import QuestionNotFoundError
from atlas.core.domain.question.repository import QuestionRepository
from atlas.core.domain.question.value_objects import QuestionId
from atlas.core.domain.reasoning_link.entity import QuestionObservationLink
from atlas.core.domain.reasoning_link.repository import QuestionObservationLinkRepository


@dataclass(frozen=True)
class ObserveFromQuestionRequest:
    case_id: uuid.UUID
    question_id: uuid.UUID
    subject: str
    statement: str
    observed_at: datetime
    source: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class ObserveFromQuestionResult:
    observation: Observation
    link: QuestionObservationLink


class ObserveFromQuestionService:
    def __init__(
        self,
        question_repository: QuestionRepository,
        observation_service: CaptureObservationService,
        link_repository: QuestionObservationLinkRepository,
    ) -> None:
        self._questions = question_repository
        self._observation_service = observation_service
        self._links = link_repository

    def observe(self, request: ObserveFromQuestionRequest) -> ObserveFromQuestionResult:
        question_id = QuestionId(request.question_id)

        if self._questions.get(question_id) is None:
            raise QuestionNotFoundError(f"No Question found with id {question_id}")

        observation = self._observation_service.capture(
            CaptureObservationRequest(
                case_id=request.case_id,
                subject=request.subject,
                statement=request.statement,
                observed_at=request.observed_at,
                source=request.source,
                note=request.note,
            )
        )
        link = QuestionObservationLink.capture(
            question_id=question_id, observation_id=observation.id
        )
        self._links.add(link)
        return ObserveFromQuestionResult(observation=observation, link=link)
