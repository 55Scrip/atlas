"""Tests for reflection_history's composition root (ATLAS-010).

Proves, end-to-end against a real engine: genuine owner-scoping, reuse
of the exact ATLAS-009B resolve_investor_identity boundary, the
bootstrap/read-only separation Correction 1 requires, and that later
Decision activity never retroactively changes a previously-built entry's
stored provenance.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.core.application.investor_identity.composition import resolve_investor_identity
from atlas.core.application.reflection_history.composition import (
    build_reflection_history_query,
    create_reflection_history_tables,
)
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
from atlas.core.infrastructure.persistence.decision.table import decisions_table
from atlas.core.infrastructure.persistence.investor_identity.table import (
    investor_identity_table,
)
from atlas.core.infrastructure.persistence.reflection_response.sqlalchemy_repository import (
    SqlAlchemyReflectionResponseRepository,
)
from atlas.core.infrastructure.persistence.reflection_response.table import (
    reflection_responses_table,
)

_T0 = datetime(2026, 7, 21, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    return create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )


def _make_decision(user_id: UserId) -> Decision:
    return Decision.register(
        user_id=user_id,
        decision_type=DecisionType.BUY,
        subject=Subject("NVIDIA"),
        investment_case=InvestmentCase("Demand accelerating."),
        confidence=Confidence(80),
        decided_at=_T0,
        clock=lambda: _T0,
    )


def _make_response(decision_id, recorded_at=_T0, text="Keeping this.") -> ReflectionResponse:
    return ReflectionResponse.register(
        decision_id=decision_id,
        response_text=ResponseText(text),
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


def _snapshot_all_tables(engine):
    with engine.connect() as connection:
        return {
            "investor_identity": sorted(
                map(tuple, connection.execute(select(investor_identity_table)).all())
            ),
            "decisions": sorted(map(tuple, connection.execute(select(decisions_table)).all())),
            "reflection_responses": sorted(
                map(tuple, connection.execute(select(reflection_responses_table)).all())
            ),
        }


class TestEndToEndOwnerScoping:
    def test_only_the_current_investors_own_entries_appear(self, engine):
        create_reflection_history_tables(engine)
        owner_user_id = resolve_investor_identity(engine)  # explicit prerequisite step

        decision_repo = SqlAlchemyDecisionRepository(engine)
        response_repo = SqlAlchemyReflectionResponseRepository(engine)

        own_decision = _make_decision(owner_user_id)
        decision_repo.add(own_decision)
        own_response = _make_response(own_decision.id)
        response_repo.add(own_response)

        # Simulate what a future multi-investor store might contain: a
        # Decision + Reflection Response belonging to a different owner,
        # inserted directly since today's single-investor-local mode
        # never produces this on its own.
        other_owner = UserId(uuid.uuid4())
        other_decision = _make_decision(other_owner)
        decision_repo.add(other_decision)
        other_response = _make_response(other_decision.id, text="Not this investor's.")
        response_repo.add(other_response)

        history = build_reflection_history_query(engine, owner_user_id).build()

        assert [entry.id for entry in history.entries] == [own_response.id]

    def test_resolved_owner_matches_resolve_investor_identity_independently(self, engine):
        create_reflection_history_tables(engine)
        owner_user_id = resolve_investor_identity(engine)

        # Calling the shared ATLAS-009B boundary again, independently,
        # returns the exact same value — proving reuse, not a parallel
        # identity mechanism.
        independently_resolved = resolve_investor_identity(engine)

        assert owner_user_id == independently_resolved


class TestBootstrapReadOnlySeparation:
    def test_building_reflection_history_after_bootstrap_performs_no_writes(self, engine):
        create_reflection_history_tables(engine)
        owner_user_id = resolve_investor_identity(engine)  # bootstrap step — may write

        decision_repo = SqlAlchemyDecisionRepository(engine)
        response_repo = SqlAlchemyReflectionResponseRepository(engine)
        decision = _make_decision(owner_user_id)
        decision_repo.add(decision)
        response_repo.add(_make_response(decision.id))

        before = _snapshot_all_tables(engine)
        build_reflection_history_query(engine, owner_user_id).build()
        after = _snapshot_all_tables(engine)

        assert before == after

    def test_build_reflection_history_query_never_invokes_resolve_investor_identity(
        self, engine, monkeypatch
    ):
        create_reflection_history_tables(engine)
        owner_user_id = resolve_investor_identity(engine)  # explicit prerequisite, done once

        from atlas.core.infrastructure.persistence.investor_identity import (
            sqlalchemy_repository as investor_identity_repository_module,
        )

        def _fail_if_called(self, clock=None):
            raise AssertionError(
                "build_reflection_history_query/.build() must never resolve "
                "Investor Identity themselves"
            )

        monkeypatch.setattr(
            investor_identity_repository_module.SqlAlchemyInvestorIdentityRepository,
            "resolve",
            _fail_if_called,
        )

        # Must not raise: the read-only path never touches
        # InvestorIdentityRepository.resolve at all.
        build_reflection_history_query(engine, owner_user_id).build()


class TestLaterRecomputationHasNoEffect:
    def test_previously_built_entries_provenance_is_unaffected_by_later_decisions(self, engine):
        create_reflection_history_tables(engine)
        owner_user_id = resolve_investor_identity(engine)
        decision_repo = SqlAlchemyDecisionRepository(engine)
        response_repo = SqlAlchemyReflectionResponseRepository(engine)

        decision = _make_decision(owner_user_id)
        decision_repo.add(decision)
        response = _make_response(decision.id)
        response_repo.add(response)

        first_build = build_reflection_history_query(engine, owner_user_id).build()
        original_provenance = first_build.entries[0].provenance

        # Record more Decisions on the same subject/type — exactly the
        # kind of activity that would change what pattern_recognition or
        # strategy_signature would freshly compute today.
        for _ in range(3):
            decision_repo.add(_make_decision(owner_user_id))

        second_build = build_reflection_history_query(engine, owner_user_id).build()
        rebuilt_entry = next(e for e in second_build.entries if e.id == response.id)

        assert rebuilt_entry.provenance == original_provenance
