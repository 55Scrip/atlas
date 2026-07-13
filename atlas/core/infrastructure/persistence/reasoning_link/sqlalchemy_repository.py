"""SQLAlchemy-backed repositories for the reasoning_link module.

PROVISIONAL STATUS: see atlas.core.domain.reasoning_link.entity's module
docstring. `add` is the only write operation and is always an INSERT.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

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
from atlas.core.domain.reasoning_link.value_objects import (
    ConclusionDecisionLinkId,
    HypothesisEvidenceLinkId,
    InterpretationHypothesisLinkId,
    QuestionObservationLinkId,
)
from atlas.core.infrastructure.persistence.reasoning_link.table import (
    conclusion_decision_links_table,
    hypothesis_evidence_links_table,
    interpretation_hypothesis_links_table,
    question_observation_links_table,
)


class SqlAlchemyQuestionObservationLinkRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, link: QuestionObservationLink) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                insert(question_observation_links_table).values(
                    link_id=str(link.link_id),
                    question_id=str(link.question_id),
                    observation_id=str(link.observation_id),
                    linked_at=link.linked_at.isoformat(),
                )
            )

    def list_by_question_id(self, question_id: QuestionId) -> list[QuestionObservationLink]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(question_observation_links_table)
                .where(question_observation_links_table.c.question_id == str(question_id))
                .order_by(question_observation_links_table.c.linked_at)
            ).mappings().all()
        return [_to_question_observation_link(row) for row in rows]

    def list_by_observation_id(
        self, observation_id: ObservationId
    ) -> list[QuestionObservationLink]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(question_observation_links_table)
                .where(question_observation_links_table.c.observation_id == str(observation_id))
                .order_by(question_observation_links_table.c.linked_at)
            ).mappings().all()
        return [_to_question_observation_link(row) for row in rows]


class SqlAlchemyInterpretationHypothesisLinkRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, link: InterpretationHypothesisLink) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                insert(interpretation_hypothesis_links_table).values(
                    link_id=str(link.link_id),
                    interpretation_id=str(link.interpretation_id),
                    hypothesis_id=str(link.hypothesis_id),
                    linked_at=link.linked_at.isoformat(),
                )
            )

    def list_by_interpretation_id(
        self, interpretation_id: InterpretationId
    ) -> list[InterpretationHypothesisLink]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(interpretation_hypothesis_links_table)
                .where(
                    interpretation_hypothesis_links_table.c.interpretation_id
                    == str(interpretation_id)
                )
                .order_by(interpretation_hypothesis_links_table.c.linked_at)
            ).mappings().all()
        return [_to_interpretation_hypothesis_link(row) for row in rows]

    def list_by_hypothesis_id(
        self, hypothesis_id: HypothesisId
    ) -> list[InterpretationHypothesisLink]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(interpretation_hypothesis_links_table)
                .where(interpretation_hypothesis_links_table.c.hypothesis_id == str(hypothesis_id))
                .order_by(interpretation_hypothesis_links_table.c.linked_at)
            ).mappings().all()
        return [_to_interpretation_hypothesis_link(row) for row in rows]


class SqlAlchemyHypothesisEvidenceLinkRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, link: HypothesisEvidenceLink) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                insert(hypothesis_evidence_links_table).values(
                    link_id=str(link.link_id),
                    hypothesis_id=str(link.hypothesis_id),
                    evidence_id=str(link.evidence_id),
                    linked_at=link.linked_at.isoformat(),
                )
            )

    def list_by_hypothesis_id(self, hypothesis_id: HypothesisId) -> list[HypothesisEvidenceLink]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(hypothesis_evidence_links_table)
                .where(hypothesis_evidence_links_table.c.hypothesis_id == str(hypothesis_id))
                .order_by(hypothesis_evidence_links_table.c.linked_at)
            ).mappings().all()
        return [_to_hypothesis_evidence_link(row) for row in rows]

    def list_by_evidence_id(self, evidence_id: EvidenceId) -> list[HypothesisEvidenceLink]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(hypothesis_evidence_links_table)
                .where(hypothesis_evidence_links_table.c.evidence_id == str(evidence_id))
                .order_by(hypothesis_evidence_links_table.c.linked_at)
            ).mappings().all()
        return [_to_hypothesis_evidence_link(row) for row in rows]


class SqlAlchemyConclusionDecisionLinkRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, link: ConclusionDecisionLink) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                insert(conclusion_decision_links_table).values(
                    link_id=str(link.link_id),
                    conclusion_id=str(link.conclusion_id),
                    decision_id=str(link.decision_id),
                    linked_at=link.linked_at.isoformat(),
                )
            )

    def list_by_conclusion_id(self, conclusion_id: ConclusionId) -> list[ConclusionDecisionLink]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(conclusion_decision_links_table)
                .where(conclusion_decision_links_table.c.conclusion_id == str(conclusion_id))
                .order_by(conclusion_decision_links_table.c.linked_at)
            ).mappings().all()
        return [_to_conclusion_decision_link(row) for row in rows]

    def list_by_decision_id(self, decision_id: DecisionId) -> list[ConclusionDecisionLink]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(conclusion_decision_links_table)
                .where(conclusion_decision_links_table.c.decision_id == str(decision_id))
                .order_by(conclusion_decision_links_table.c.linked_at)
            ).mappings().all()
        return [_to_conclusion_decision_link(row) for row in rows]


def _to_question_observation_link(row: Mapping[str, Any]) -> QuestionObservationLink:
    return QuestionObservationLink(
        link_id=QuestionObservationLinkId(uuid.UUID(row["link_id"])),
        question_id=QuestionId(uuid.UUID(row["question_id"])),
        observation_id=ObservationId(uuid.UUID(row["observation_id"])),
        linked_at=datetime.fromisoformat(row["linked_at"]),
    )


def _to_interpretation_hypothesis_link(row: Mapping[str, Any]) -> InterpretationHypothesisLink:
    return InterpretationHypothesisLink(
        link_id=InterpretationHypothesisLinkId(uuid.UUID(row["link_id"])),
        interpretation_id=InterpretationId(uuid.UUID(row["interpretation_id"])),
        hypothesis_id=HypothesisId(uuid.UUID(row["hypothesis_id"])),
        linked_at=datetime.fromisoformat(row["linked_at"]),
    )


def _to_hypothesis_evidence_link(row: Mapping[str, Any]) -> HypothesisEvidenceLink:
    return HypothesisEvidenceLink(
        link_id=HypothesisEvidenceLinkId(uuid.UUID(row["link_id"])),
        hypothesis_id=HypothesisId(uuid.UUID(row["hypothesis_id"])),
        evidence_id=EvidenceId(uuid.UUID(row["evidence_id"])),
        linked_at=datetime.fromisoformat(row["linked_at"]),
    )


def _to_conclusion_decision_link(row: Mapping[str, Any]) -> ConclusionDecisionLink:
    return ConclusionDecisionLink(
        link_id=ConclusionDecisionLinkId(uuid.UUID(row["link_id"])),
        conclusion_id=ConclusionId(uuid.UUID(row["conclusion_id"])),
        decision_id=DecisionId(uuid.UUID(row["decision_id"])),
        linked_at=datetime.fromisoformat(row["linked_at"]),
    )
