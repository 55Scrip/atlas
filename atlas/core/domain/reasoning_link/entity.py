"""reasoning_link: the four bridge entities that connect the Core Loop's
protected, unmodifiable aggregates (ATLAS-001 Core Loop).

PROVISIONAL STATUS — READ BEFORE EXTENDING THIS MODULE: this module is a
temporary orchestration mechanism, not a permanent addition to the
ubiquitous language. It exists for one narrow structural reason: four
edges in the Core Loop (Question -> Observation, Interpretation ->
Hypothesis, Hypothesis -> Evidence, Conclusion -> Decision) point INTO an
aggregate that must not be modified (Observation, Hypothesis, Evidence,
Decision each carry a hard "no relationships to other aggregates"
invariant from their own prior increments). The established pattern for
one aggregate referencing another (`DecisionContext.decision_id`) always
puts the foreign id on the new/later side — but here the later side is
exactly what can't be touched. These four Link records exist solely to
bridge that gap without violating either the protected aggregates'
invariants or their own immutability (no UPDATE, ever, means a
"preceding" concept can never be retrofitted with a forward-pointing
field once the "following" concept is created).

A later iteration will evaluate whether this bridging responsibility
should live inside the domain model, move up into the application layer
as pure in-memory orchestration (no persisted link records at all), or
take some other shape entirely. This module deliberately does not
prejudge that outcome — see docs/CoreLoopATLAS001.md.

Each Link is thinner than the six step aggregates: no investor-supplied
timestamp field (the meaningful moment already lives on the downstream
entity's own timestamp), just `linked_at` (always UTC, via clock). No
uniqueness constraint on any of the four — none of these edges is 1:1
the way DecisionContext:Decision is.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.conclusion.value_objects import ConclusionId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.domain.hypothesis.value_objects import HypothesisId
from atlas.core.domain.interpretation.value_objects import InterpretationId
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.domain.question.value_objects import QuestionId
from atlas.core.domain.reasoning_link.exceptions import ReasoningLinkValidationError
from atlas.core.domain.reasoning_link.value_objects import (
    ConclusionDecisionLinkId,
    HypothesisEvidenceLinkId,
    InterpretationHypothesisLinkId,
    QuestionObservationLinkId,
)

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _require(value: object, message: str) -> None:
    if value is None:
        raise ReasoningLinkValidationError(message)


@dataclass(frozen=True)
class QuestionObservationLink:
    """Records that a given Observation was made in answer to a given
    Question. Bridges the edge whose target (Observation) may not carry
    a question_id field of its own.
    """

    link_id: QuestionObservationLinkId
    question_id: QuestionId
    observation_id: ObservationId
    linked_at: datetime

    def __post_init__(self) -> None:
        _require(self.question_id, "QuestionObservationLink.question_id must not be missing")
        _require(
            self.observation_id, "QuestionObservationLink.observation_id must not be missing"
        )

    @classmethod
    def capture(
        cls,
        *,
        question_id: QuestionId,
        observation_id: ObservationId,
        clock: _Clock = _utc_now,
    ) -> QuestionObservationLink:
        return cls(
            link_id=QuestionObservationLinkId(),
            question_id=question_id,
            observation_id=observation_id,
            linked_at=clock(),
        )


@dataclass(frozen=True)
class InterpretationHypothesisLink:
    """Records that a given Hypothesis was formed from a given
    Interpretation. Bridges the edge whose target (Hypothesis) may not
    carry an interpretation_id field of its own.
    """

    link_id: InterpretationHypothesisLinkId
    interpretation_id: InterpretationId
    hypothesis_id: HypothesisId
    linked_at: datetime

    def __post_init__(self) -> None:
        _require(
            self.interpretation_id,
            "InterpretationHypothesisLink.interpretation_id must not be missing",
        )
        _require(
            self.hypothesis_id, "InterpretationHypothesisLink.hypothesis_id must not be missing"
        )

    @classmethod
    def capture(
        cls,
        *,
        interpretation_id: InterpretationId,
        hypothesis_id: HypothesisId,
        clock: _Clock = _utc_now,
    ) -> InterpretationHypothesisLink:
        return cls(
            link_id=InterpretationHypothesisLinkId(),
            interpretation_id=interpretation_id,
            hypothesis_id=hypothesis_id,
            linked_at=clock(),
        )


@dataclass(frozen=True)
class HypothesisEvidenceLink:
    """Records that a given Evidence record was captured against a given
    Hypothesis. Bridges the edge whose target (Evidence) may not carry a
    hypothesis_id field of its own.
    """

    link_id: HypothesisEvidenceLinkId
    hypothesis_id: HypothesisId
    evidence_id: EvidenceId
    linked_at: datetime

    def __post_init__(self) -> None:
        _require(self.hypothesis_id, "HypothesisEvidenceLink.hypothesis_id must not be missing")
        _require(self.evidence_id, "HypothesisEvidenceLink.evidence_id must not be missing")

    @classmethod
    def capture(
        cls,
        *,
        hypothesis_id: HypothesisId,
        evidence_id: EvidenceId,
        clock: _Clock = _utc_now,
    ) -> HypothesisEvidenceLink:
        return cls(
            link_id=HypothesisEvidenceLinkId(),
            hypothesis_id=hypothesis_id,
            evidence_id=evidence_id,
            linked_at=clock(),
        )


@dataclass(frozen=True)
class ConclusionDecisionLink:
    """Records that a given Decision was committed from a given
    Conclusion. Bridges the edge whose target (Decision) may not carry a
    conclusion_id field of its own.
    """

    link_id: ConclusionDecisionLinkId
    conclusion_id: ConclusionId
    decision_id: DecisionId
    linked_at: datetime

    def __post_init__(self) -> None:
        _require(self.conclusion_id, "ConclusionDecisionLink.conclusion_id must not be missing")
        _require(self.decision_id, "ConclusionDecisionLink.decision_id must not be missing")

    @classmethod
    def capture(
        cls,
        *,
        conclusion_id: ConclusionId,
        decision_id: DecisionId,
        clock: _Clock = _utc_now,
    ) -> ConclusionDecisionLink:
        return cls(
            link_id=ConclusionDecisionLinkId(),
            conclusion_id=conclusion_id,
            decision_id=decision_id,
            linked_at=clock(),
        )
