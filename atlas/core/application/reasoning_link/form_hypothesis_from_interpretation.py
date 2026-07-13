"""Composite application service: Hypothesis formed from an Interpretation
(ATLAS-001 Core Loop, step 4 of 10).

Verifies the referenced Interpretation exists, then reuses the existing,
unmodified HypothesisService to construct the Hypothesis, and records
the InterpretationHypothesisLink atomically. Never writes to
InterpretationRepository or modifies Hypothesis's own construction path.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.application.hypothesis.capture_hypothesis import (
    CaptureHypothesisRequest,
    HypothesisService,
)
from atlas.core.domain.hypothesis.entity import Hypothesis
from atlas.core.domain.interpretation.exceptions import InterpretationNotFoundError
from atlas.core.domain.interpretation.repository import InterpretationRepository
from atlas.core.domain.interpretation.value_objects import InterpretationId
from atlas.core.domain.reasoning_link.entity import InterpretationHypothesisLink
from atlas.core.domain.reasoning_link.repository import InterpretationHypothesisLinkRepository


@dataclass(frozen=True)
class FormHypothesisFromInterpretationRequest:
    interpretation_id: uuid.UUID
    statement: str
    formulated_at: datetime
    note: str | None = None


@dataclass(frozen=True)
class FormHypothesisFromInterpretationResult:
    hypothesis: Hypothesis
    link: InterpretationHypothesisLink


class FormHypothesisFromInterpretationService:
    def __init__(
        self,
        interpretation_repository: InterpretationRepository,
        hypothesis_service: HypothesisService,
        link_repository: InterpretationHypothesisLinkRepository,
    ) -> None:
        self._interpretations = interpretation_repository
        self._hypothesis_service = hypothesis_service
        self._links = link_repository

    def form(
        self, request: FormHypothesisFromInterpretationRequest
    ) -> FormHypothesisFromInterpretationResult:
        interpretation_id = InterpretationId(request.interpretation_id)

        if self._interpretations.get(interpretation_id) is None:
            raise InterpretationNotFoundError(
                f"No Interpretation found with id {interpretation_id}"
            )

        hypothesis = self._hypothesis_service.capture(
            CaptureHypothesisRequest(
                statement=request.statement,
                formulated_at=request.formulated_at,
                note=request.note,
            )
        )
        link = InterpretationHypothesisLink.capture(
            interpretation_id=interpretation_id, hypothesis_id=hypothesis.id
        )
        self._links.add(link)
        return FormHypothesisFromInterpretationResult(hypothesis=hypothesis, link=link)
