"""Tests for SqlAlchemyReflectionResponseRepository.list_all_for_owner (ATLAS-010).

Proves the owner-scoped join is genuinely owner-scoped — not accidentally
correct because today's single-investor-local mode only ever produces one
owner. `add`/`get` themselves are untouched by ATLAS-010 and remain
covered, unchanged, by test_sqlalchemy_repository.py (ATLAS-009).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import (
    PatternMembershipSnapshot,
    ProvenanceSnapshot,
    ResponseText,
)
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.reflection_response.sqlalchemy_repository import (
    SqlAlchemyReflectionResponseRepository,
)
from atlas.core.infrastructure.persistence.reflection_response.table import (
    create_reflection_response_table,
)

_RECORDED_AT = datetime(2026, 7, 21, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(eng)
    create_reflection_response_table(eng)
    return eng


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def repository(engine):
    return SqlAlchemyReflectionResponseRepository(engine)


def _make_decision(user_id: UserId) -> Decision:
    return Decision.register(
        user_id=user_id,
        decision_type=DecisionType.BUY,
        subject=Subject("NVIDIA"),
        investment_case=InvestmentCase("Demand accelerating."),
        confidence=Confidence(80),
        decided_at=_RECORDED_AT,
        clock=lambda: _RECORDED_AT,
    )


def _make_response(decision_id, response_text_value="Keeping this.", recorded_at=_RECORDED_AT):
    return ReflectionResponse.register(
        decision_id=decision_id,
        response_text=ResponseText(response_text_value),
        provenance=ProvenanceSnapshot(
            reflection_description="You have made 2 BUY decisions on NVIDIA.",
            coaching_question_text="What's similar or different this time?",
            grounding_pattern=PatternMembershipSnapshot(
                strategy_name="same_subject_and_type",
                member_decision_ids=(decision_id,),
            ),
            strategy_signature_patterns=(),
            reasoning_context_subject="NVIDIA",
            reasoning_context_decision_type="BUY",
            reasoning_context_confidence=None,
        ),
        clock=lambda: recorded_at,
    )


class TestOwnerScoping:
    def test_returns_only_responses_owned_by_the_given_investor(
        self, decision_repository, repository
    ):
        owner = UserId(uuid.uuid4())
        other_owner = UserId(uuid.uuid4())

        owner_decision = _make_decision(owner)
        other_decision = _make_decision(other_owner)
        decision_repository.add(owner_decision)
        decision_repository.add(other_decision)

        owner_response = _make_response(owner_decision.id)
        other_response = _make_response(other_decision.id)
        repository.add(owner_response)
        repository.add(other_response)

        results = repository.list_all_for_owner(owner)

        assert [r.id for r in results] == [owner_response.id]

    def test_returns_empty_list_for_an_owner_with_no_responses(
        self, decision_repository, repository
    ):
        owner = UserId(uuid.uuid4())
        decision_repository.add(_make_decision(owner))
        # No ReflectionResponse ever added.

        assert repository.list_all_for_owner(owner) == []

    def test_each_owned_response_appears_exactly_once_no_duplicates(
        self, decision_repository, repository
    ):
        owner = UserId(uuid.uuid4())
        decision = _make_decision(owner)
        decision_repository.add(decision)
        response = _make_response(decision.id)
        repository.add(response)

        results = repository.list_all_for_owner(owner)

        assert len(results) == 1
        assert results[0].id == response.id

    def test_multiple_responses_for_one_decision_remain_separate(
        self, decision_repository, repository
    ):
        owner = UserId(uuid.uuid4())
        decision = _make_decision(owner)
        decision_repository.add(decision)
        first = _make_response(decision.id, "First reflection kept.")
        second = _make_response(decision.id, "Second, separate reflection kept.")
        repository.add(first)
        repository.add(second)

        results = repository.list_all_for_owner(owner)

        assert {r.id for r in results} == {first.id, second.id}
        assert len(results) == 2

    def test_response_text_round_trips_byte_for_byte_through_the_join(
        self, decision_repository, repository
    ):
        owner = UserId(uuid.uuid4())
        decision = _make_decision(owner)
        decision_repository.add(decision)
        weird_text = "  Multiple   spaces, Mixed CASE, punctuation?! ...yes.  "
        response = _make_response(decision.id, weird_text)
        repository.add(response)

        results = repository.list_all_for_owner(owner)

        assert results[0].response_text.value == weird_text

    def test_provenance_round_trips_exactly_as_persisted(self, decision_repository, repository):
        owner = UserId(uuid.uuid4())
        decision = _make_decision(owner)
        decision_repository.add(decision)
        response = _make_response(decision.id)
        repository.add(response)

        results = repository.list_all_for_owner(owner)

        assert results[0].provenance == response.provenance
