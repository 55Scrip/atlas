"""Persistence tests for the four reasoning_link repositories (ATLAS-001 Core Loop)."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

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
from atlas.core.infrastructure.persistence.reasoning_link.sqlalchemy_repository import (
    SqlAlchemyConclusionDecisionLinkRepository,
    SqlAlchemyHypothesisEvidenceLinkRepository,
    SqlAlchemyInterpretationHypothesisLinkRepository,
    SqlAlchemyQuestionObservationLinkRepository,
)
from atlas.core.infrastructure.persistence.reasoning_link.table import (
    conclusion_decision_links_table,
    create_reasoning_link_tables,
    hypothesis_evidence_links_table,
    interpretation_hypothesis_links_table,
    question_observation_links_table,
)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_reasoning_link_tables(eng)
    return eng


class TestQuestionObservationLinkRepository:
    def test_round_trips_by_question_id_and_observation_id(self, engine):
        repo = SqlAlchemyQuestionObservationLinkRepository(engine)
        question_id, observation_id = QuestionId(), ObservationId()
        link = QuestionObservationLink.capture(
            question_id=question_id, observation_id=observation_id
        )
        repo.add(link)

        by_question = repo.list_by_question_id(question_id)
        by_observation = repo.list_by_observation_id(observation_id)

        assert [link.link_id for link in by_question] == [link.link_id]
        assert [link.link_id for link in by_observation] == [link.link_id]
        assert by_question[0].question_id == question_id
        assert by_question[0].observation_id == observation_id
        assert by_question[0].linked_at == link.linked_at

    def test_multiple_links_for_the_same_question_are_all_returned(self, engine):
        repo = SqlAlchemyQuestionObservationLinkRepository(engine)
        question_id = QuestionId()
        first = QuestionObservationLink.capture(
            question_id=question_id, observation_id=ObservationId()
        )
        second = QuestionObservationLink.capture(
            question_id=question_id, observation_id=ObservationId()
        )
        repo.add(first)
        repo.add(second)

        result = repo.list_by_question_id(question_id)
        assert {link.link_id for link in result} == {first.link_id, second.link_id}


class TestInterpretationHypothesisLinkRepository:
    def test_round_trips_by_interpretation_id_and_hypothesis_id(self, engine):
        repo = SqlAlchemyInterpretationHypothesisLinkRepository(engine)
        interpretation_id, hypothesis_id = InterpretationId(), HypothesisId()
        link = InterpretationHypothesisLink.capture(
            interpretation_id=interpretation_id, hypothesis_id=hypothesis_id
        )
        repo.add(link)

        by_interpretation = repo.list_by_interpretation_id(interpretation_id)
        by_hypothesis = repo.list_by_hypothesis_id(hypothesis_id)

        assert [link.link_id for link in by_interpretation] == [link.link_id]
        assert [link.link_id for link in by_hypothesis] == [link.link_id]


class TestHypothesisEvidenceLinkRepository:
    def test_round_trips_by_hypothesis_id_and_evidence_id(self, engine):
        repo = SqlAlchemyHypothesisEvidenceLinkRepository(engine)
        hypothesis_id, evidence_id = HypothesisId(), EvidenceId()
        link = HypothesisEvidenceLink.capture(hypothesis_id=hypothesis_id, evidence_id=evidence_id)
        repo.add(link)

        by_hypothesis = repo.list_by_hypothesis_id(hypothesis_id)
        by_evidence = repo.list_by_evidence_id(evidence_id)

        assert [link.link_id for link in by_hypothesis] == [link.link_id]
        assert [link.link_id for link in by_evidence] == [link.link_id]

    def test_multiple_evidence_links_for_the_same_hypothesis_are_all_returned(self, engine):
        repo = SqlAlchemyHypothesisEvidenceLinkRepository(engine)
        hypothesis_id = HypothesisId()
        first = HypothesisEvidenceLink.capture(
            hypothesis_id=hypothesis_id, evidence_id=EvidenceId()
        )
        second = HypothesisEvidenceLink.capture(
            hypothesis_id=hypothesis_id, evidence_id=EvidenceId()
        )
        repo.add(first)
        repo.add(second)

        result = repo.list_by_hypothesis_id(hypothesis_id)
        assert {link.link_id for link in result} == {first.link_id, second.link_id}


class TestConclusionDecisionLinkRepository:
    def test_round_trips_by_conclusion_id_and_decision_id(self, engine):
        repo = SqlAlchemyConclusionDecisionLinkRepository(engine)
        conclusion_id, decision_id = ConclusionId(), DecisionId()
        link = ConclusionDecisionLink.capture(
            conclusion_id=conclusion_id, decision_id=decision_id
        )
        repo.add(link)

        by_conclusion = repo.list_by_conclusion_id(conclusion_id)
        by_decision = repo.list_by_decision_id(decision_id)

        assert [link.link_id for link in by_conclusion] == [link.link_id]
        assert [link.link_id for link in by_decision] == [link.link_id]


class TestNoForeignKeysOrUniqueness:
    def test_all_four_tables_have_no_sql_foreign_key(self):
        for table in (
            question_observation_links_table,
            interpretation_hypothesis_links_table,
            hypothesis_evidence_links_table,
            conclusion_decision_links_table,
        ):
            assert table.foreign_keys == set()

    def test_all_four_tables_have_no_unique_constraint(self):
        for table in (
            question_observation_links_table,
            interpretation_hypothesis_links_table,
            hypothesis_evidence_links_table,
            conclusion_decision_links_table,
        ):
            for column in table.columns:
                assert column.unique is not True

    def test_expected_columns(self):
        assert set(question_observation_links_table.columns.keys()) == {
            "link_id",
            "question_id",
            "observation_id",
            "linked_at",
        }
        assert set(interpretation_hypothesis_links_table.columns.keys()) == {
            "link_id",
            "interpretation_id",
            "hypothesis_id",
            "linked_at",
        }
        assert set(hypothesis_evidence_links_table.columns.keys()) == {
            "link_id",
            "hypothesis_id",
            "evidence_id",
            "linked_at",
        }
        assert set(conclusion_decision_links_table.columns.keys()) == {
            "link_id",
            "conclusion_id",
            "decision_id",
            "linked_at",
        }
