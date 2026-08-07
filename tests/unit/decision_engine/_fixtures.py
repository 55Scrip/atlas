"""Shared test fixtures for the Decision Engine test suite.

Builds real Core Domain Objects (Decision, Outcome, Observation,
Evidence) rather than fabricating loose dicts, so these tests exercise
the actual read-only contract `atlas.decision_engine` has with
`atlas.core.domain` — mirroring the established pattern in
`tests/unit/domain/decision/test_entity.py`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.value_objects import Direction
from atlas.core.domain.evidence.value_objects import Statement as EvidenceStatement
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement as ObservationStatement
from atlas.core.domain.observation.value_objects import Subject as ObservationSubject
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import Statement as OutcomeStatement
from atlas.decision_engine.contracts import DecisionEngineInput

CASE_ID = CaseId()
USER_ID = UserId(uuid.uuid4())
GENERATED_AT = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
EVALUATED_AT = datetime(2026, 8, 7, 11, 0, tzinfo=timezone.utc)


def _fixed_clock(dt: datetime):
    return lambda: dt


def build_decision(*, case_id: CaseId = CASE_ID, decided_at: datetime = EVALUATED_AT) -> Decision:
    return Decision.register(
        case_id=case_id,
        user_id=USER_ID,
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat, undervalued relative to peers"),
        confidence=Confidence(70),
        decided_at=decided_at,
        clock=_fixed_clock(decided_at),
    )


def build_outcome(*, decision: Decision, occurred_at: datetime = EVALUATED_AT) -> Outcome:
    return Outcome.capture(
        case_id=decision.case_id,
        decision_id=decision.id,
        statement=OutcomeStatement("Position held; thesis unchanged so far."),
        occurred_at=occurred_at,
        clock=_fixed_clock(occurred_at),
    )


def build_observation(
    *,
    case_id: CaseId = CASE_ID,
    subject: str = "ASML",
    statement: str = "Q2 revenue grew 12% year over year.",
    observed_at: datetime = EVALUATED_AT,
) -> Observation:
    return Observation.capture(
        case_id=case_id,
        subject=ObservationSubject(subject),
        statement=ObservationStatement(statement),
        observed_at=observed_at,
        clock=_fixed_clock(observed_at),
    )


def build_evidence(
    *,
    observation: Observation,
    direction: Direction = Direction.SUPPORTS,
    statement: str = "Reported revenue growth exceeded guidance.",
    observed_at: datetime = EVALUATED_AT,
) -> Evidence:
    return Evidence.capture(
        observation_id=observation.id,
        statement=EvidenceStatement(statement),
        direction=direction,
        observed_at=observed_at,
        clock=_fixed_clock(observed_at),
    )


def build_minimal_input(*, case_id: CaseId = CASE_ID) -> DecisionEngineInput:
    """The smallest valid input: a Case with no recorded history yet."""
    return DecisionEngineInput(case_id=case_id, evaluated_at=EVALUATED_AT)


def build_populated_input(*, case_id: CaseId = CASE_ID) -> DecisionEngineInput:
    """A Case with a real Decision, Outcome, Observation, and Evidence
    attached — exercises the read side of the input contract without
    ever writing back to Core."""
    decision = build_decision(case_id=case_id)
    outcome = build_outcome(decision=decision)
    observation = build_observation(case_id=case_id)
    evidence = build_evidence(observation=observation)
    return DecisionEngineInput(
        case_id=case_id,
        evaluated_at=EVALUATED_AT,
        decisions=(decision,),
        outcomes=(outcome,),
        observations=(observation,),
        evidence=(evidence,),
    )
