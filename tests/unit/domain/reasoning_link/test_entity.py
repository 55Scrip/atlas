"""Tests for the four reasoning_link entities (ATLAS-001 Core Loop)."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

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


def _fixed_clock(dt: datetime):
    return lambda: dt


class TestQuestionObservationLink:
    def test_captures_both_ids(self):
        question_id, observation_id = QuestionId(), ObservationId()
        link = QuestionObservationLink.capture(
            question_id=question_id, observation_id=observation_id
        )
        assert link.question_id == question_id
        assert link.observation_id == observation_id

    def test_linked_at_is_always_now(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        link = QuestionObservationLink.capture(
            question_id=QuestionId(), observation_id=ObservationId(), clock=_fixed_clock(now)
        )
        assert link.linked_at == now

    def test_assigns_a_fresh_link_id(self):
        first = QuestionObservationLink.capture(
            question_id=QuestionId(), observation_id=ObservationId()
        )
        second = QuestionObservationLink.capture(
            question_id=QuestionId(), observation_id=ObservationId()
        )
        assert first.link_id != second.link_id

    def test_is_frozen(self):
        link = QuestionObservationLink.capture(
            question_id=QuestionId(), observation_id=ObservationId()
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            link.question_id = QuestionId()


class TestInterpretationHypothesisLink:
    def test_captures_both_ids(self):
        interpretation_id, hypothesis_id = InterpretationId(), HypothesisId()
        link = InterpretationHypothesisLink.capture(
            interpretation_id=interpretation_id, hypothesis_id=hypothesis_id
        )
        assert link.interpretation_id == interpretation_id
        assert link.hypothesis_id == hypothesis_id

    def test_is_frozen(self):
        link = InterpretationHypothesisLink.capture(
            interpretation_id=InterpretationId(), hypothesis_id=HypothesisId()
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            link.hypothesis_id = HypothesisId()


class TestHypothesisEvidenceLink:
    def test_captures_both_ids(self):
        hypothesis_id, evidence_id = HypothesisId(), EvidenceId()
        link = HypothesisEvidenceLink.capture(hypothesis_id=hypothesis_id, evidence_id=evidence_id)
        assert link.hypothesis_id == hypothesis_id
        assert link.evidence_id == evidence_id

    def test_is_frozen(self):
        link = HypothesisEvidenceLink.capture(
            hypothesis_id=HypothesisId(), evidence_id=EvidenceId()
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            link.evidence_id = EvidenceId()


class TestConclusionDecisionLink:
    def test_captures_both_ids(self):
        conclusion_id, decision_id = ConclusionId(), DecisionId()
        link = ConclusionDecisionLink.capture(
            conclusion_id=conclusion_id, decision_id=decision_id
        )
        assert link.conclusion_id == conclusion_id
        assert link.decision_id == decision_id

    def test_is_frozen(self):
        link = ConclusionDecisionLink.capture(
            conclusion_id=ConclusionId(), decision_id=DecisionId()
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            link.decision_id = DecisionId()
