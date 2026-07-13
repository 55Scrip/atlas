"""Repository interfaces for the reasoning_link module (ATLAS-001 Core Loop).

PROVISIONAL STATUS: see entity.py's module docstring. Insert-only: no
update, no delete. No SQL foreign keys anywhere in this module, matching
the rest of this codebase's convention.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.conclusion.value_objects import ConclusionId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.domain.hypothesis.value_objects import HypothesisId
from atlas.core.domain.interpretation.value_objects import InterpretationId
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.domain.question.value_objects import QuestionId
from atlas.core.domain.reasoning_link.entity import (
    ConclusionDecisionLink,
    HypothesisEvidenceLink,
    InterpretationHypothesisLink,
    QuestionObservationLink,
)


class QuestionObservationLinkRepository(Protocol):
    def add(self, link: QuestionObservationLink) -> None: ...

    def list_by_question_id(self, question_id: QuestionId) -> list[QuestionObservationLink]: ...

    def list_by_observation_id(
        self, observation_id: ObservationId
    ) -> list[QuestionObservationLink]: ...


class InterpretationHypothesisLinkRepository(Protocol):
    def add(self, link: InterpretationHypothesisLink) -> None: ...

    def list_by_interpretation_id(
        self, interpretation_id: InterpretationId
    ) -> list[InterpretationHypothesisLink]: ...

    def list_by_hypothesis_id(
        self, hypothesis_id: HypothesisId
    ) -> list[InterpretationHypothesisLink]: ...


class HypothesisEvidenceLinkRepository(Protocol):
    def add(self, link: HypothesisEvidenceLink) -> None: ...

    def list_by_hypothesis_id(
        self, hypothesis_id: HypothesisId
    ) -> list[HypothesisEvidenceLink]: ...

    def list_by_evidence_id(self, evidence_id: EvidenceId) -> list[HypothesisEvidenceLink]: ...


class ConclusionDecisionLinkRepository(Protocol):
    def add(self, link: ConclusionDecisionLink) -> None: ...

    def list_by_conclusion_id(
        self, conclusion_id: ConclusionId
    ) -> list[ConclusionDecisionLink]: ...

    def list_by_decision_id(self, decision_id: DecisionId) -> list[ConclusionDecisionLink]: ...
