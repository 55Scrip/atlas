"""Tests for FormHypothesisFromInterpretationService (ATLAS-001 Core Loop, step 4 of 10)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.hypothesis.capture_hypothesis import HypothesisService
from atlas.core.application.reasoning_link.form_hypothesis_from_interpretation import (
    FormHypothesisFromInterpretationRequest,
    FormHypothesisFromInterpretationService,
)
from atlas.core.domain.interpretation.entity import Interpretation
from atlas.core.domain.interpretation.exceptions import InterpretationNotFoundError
from atlas.core.domain.interpretation.value_objects import InterpretationId
from atlas.core.domain.interpretation.value_objects import Statement as InterpretationStatement
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.persistence.hypothesis.sqlalchemy_repository import (
    SqlAlchemyHypothesisRepository,
)
from atlas.core.infrastructure.persistence.hypothesis.table import create_hypothesis_table
from atlas.core.infrastructure.persistence.interpretation.sqlalchemy_repository import (
    SqlAlchemyInterpretationRepository,
)
from atlas.core.infrastructure.persistence.interpretation.table import (
    create_interpretation_table,
)
from atlas.core.infrastructure.persistence.reasoning_link.sqlalchemy_repository import (
    SqlAlchemyInterpretationHypothesisLinkRepository,
)
from atlas.core.infrastructure.persistence.reasoning_link.table import (
    create_reasoning_link_tables,
)

_INTERPRETED_AT = datetime(2026, 7, 13, 9, 0, 0, tzinfo=timezone.utc)
_FORMULATED_AT = datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_interpretation_table(eng)
    create_hypothesis_table(eng)
    create_reasoning_link_tables(eng)
    return eng


@pytest.fixture
def interpretation_repository(engine):
    return SqlAlchemyInterpretationRepository(engine)


@pytest.fixture
def link_repository(engine):
    return SqlAlchemyInterpretationHypothesisLinkRepository(engine)


@pytest.fixture
def service(engine, interpretation_repository, link_repository):
    hypothesis_service = HypothesisService(SqlAlchemyHypothesisRepository(engine))
    return FormHypothesisFromInterpretationService(
        interpretation_repository, hypothesis_service, link_repository
    )


@pytest.fixture
def existing_interpretation(interpretation_repository):
    interpretation = Interpretation.capture(
        observation_id=ObservationId(),
        statement=InterpretationStatement("This suggests demand may be accelerating."),
        interpreted_at=_INTERPRETED_AT,
    )
    interpretation_repository.add(interpretation)
    return interpretation


def _request(interpretation_id, **overrides) -> FormHypothesisFromInterpretationRequest:
    defaults = dict(
        interpretation_id=interpretation_id.value,
        statement="Demand for AI infrastructure may be accelerating.",
        formulated_at=_FORMULATED_AT,
    )
    defaults.update(overrides)
    return FormHypothesisFromInterpretationRequest(**defaults)


class TestFormHypothesisFromInterpretation:
    def test_creates_a_hypothesis_and_a_link(self, service, existing_interpretation):
        result = service.form(_request(existing_interpretation.id))
        assert result.hypothesis.statement.value == (
            "Demand for AI infrastructure may be accelerating."
        )
        assert result.link.interpretation_id == existing_interpretation.id
        assert result.link.hypothesis_id == result.hypothesis.id

    def test_rejects_unknown_interpretation(self, service):
        with pytest.raises(InterpretationNotFoundError):
            service.form(_request(InterpretationId()))

    def test_does_not_write_to_interpretation_repository(
        self, service, interpretation_repository, existing_interpretation
    ):
        before = interpretation_repository.list_all()
        service.form(_request(existing_interpretation.id))
        after = interpretation_repository.list_all()
        assert before == after

    def test_link_is_persisted_and_queryable(
        self, service, link_repository, existing_interpretation
    ):
        result = service.form(_request(existing_interpretation.id))
        links = link_repository.list_by_interpretation_id(existing_interpretation.id)
        assert [link.link_id for link in links] == [result.link.link_id]
