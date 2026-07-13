"""Tests for reasoning_link identity value objects (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid

from atlas.core.domain.reasoning_link.value_objects import (
    ConclusionDecisionLinkId,
    HypothesisEvidenceLinkId,
    InterpretationHypothesisLinkId,
    QuestionObservationLinkId,
)


class TestLinkIds:
    def test_question_observation_link_id_generates_a_uuid_by_default(self):
        assert isinstance(QuestionObservationLinkId().value, uuid.UUID)

    def test_interpretation_hypothesis_link_id_generates_a_uuid_by_default(self):
        assert isinstance(InterpretationHypothesisLinkId().value, uuid.UUID)

    def test_hypothesis_evidence_link_id_generates_a_uuid_by_default(self):
        assert isinstance(HypothesisEvidenceLinkId().value, uuid.UUID)

    def test_conclusion_decision_link_id_generates_a_uuid_by_default(self):
        assert isinstance(ConclusionDecisionLinkId().value, uuid.UUID)

    def test_two_default_ids_are_different(self):
        assert QuestionObservationLinkId() != QuestionObservationLinkId()

    def test_equal_by_value(self):
        value = uuid.uuid4()
        assert QuestionObservationLinkId(value) == QuestionObservationLinkId(value)
