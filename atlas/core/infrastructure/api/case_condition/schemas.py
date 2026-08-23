"""HTTP request/response schemas for CaseCondition (ADR-CC-001).

CamelCase via the shared `CamelModel` (ADR-004), mirroring
`decision_draft/schemas.py` (Sprint 9) exactly.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from atlas.core.application.case_condition.case_condition_service import (
    CaseConditionEvaluationResult,
)
from atlas.core.domain.case_condition.entity import CaseConditionView
from atlas.core.infrastructure.api.serialization import CamelModel


class CreateCaseConditionRequest(CamelModel):
    decision_id: uuid.UUID | None = None
    predicate_text: str | None = None
    role: Literal["monitoring", "invalidation"] | None = None
    authorship: Literal["atlas", "user", "mixed"] | None = None
    structured_kind: Literal["date", "threshold"] | None = None
    threshold_date: datetime | None = None
    threshold_metric: str | None = None
    threshold_operator: Literal["<", "<=", ">", ">=", "==", "!="] | None = None
    threshold_value: float | None = None


class ReviseCaseConditionRequest(CamelModel):
    predicate_text: str | None = None
    role: Literal["monitoring", "invalidation"] | None = None
    authorship: Literal["atlas", "user", "mixed"] | None = None
    structured_kind: Literal["date", "threshold"] | None = None
    threshold_date: datetime | None = None
    threshold_metric: str | None = None
    threshold_operator: Literal["<", "<=", ">", ">=", "==", "!="] | None = None
    threshold_value: float | None = None


class EvaluateCaseConditionRequest(CamelModel):
    evaluated_at: datetime | None = None
    observed_value: float | None = None
    human_asserted_satisfied: bool | None = None


class SupersedeCaseConditionRequest(CamelModel):
    superseded_by_condition_id: uuid.UUID | None = None


class CaseConditionResponse(CamelModel):
    condition_id: uuid.UUID
    case_id: uuid.UUID
    decision_id: uuid.UUID | None
    status: Literal["active", "satisfied", "superseded", "retired"]
    is_active: bool
    predicate_text: str | None
    role: Literal["monitoring", "invalidation"] | None
    authorship: Literal["atlas", "user", "mixed"] | None
    structured_kind: Literal["date", "threshold"] | None
    threshold_date: datetime | None
    threshold_metric: str | None
    threshold_operator: Literal["<", "<=", ">", ">=", "==", "!="] | None
    threshold_value: float | None
    last_observed_value: float | None
    superseded_by_condition_id: uuid.UUID | None
    latest_event_id: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, view: CaseConditionView) -> CaseConditionResponse:
        return cls(
            condition_id=view.condition_id.value,
            case_id=view.case_id.value,
            decision_id=view.decision_id.value if view.decision_id is not None else None,
            status=view.status,
            is_active=view.is_active,
            predicate_text=view.predicate_text,
            role=view.role,
            authorship=view.authorship,
            structured_kind=view.structured_kind,
            threshold_date=view.threshold_date,
            threshold_metric=view.threshold_metric,
            threshold_operator=view.threshold_operator,
            threshold_value=view.threshold_value,
            last_observed_value=view.last_observed_value,
            superseded_by_condition_id=(
                uuid.UUID(view.superseded_by_condition_id)
                if view.superseded_by_condition_id is not None
                else None
            ),
            latest_event_id=view.latest_event_id,
            created_at=view.created_at,
            updated_at=view.updated_at,
        )


class CaseConditionEvaluationResponse(CamelModel):
    satisfied: bool
    transitioned: bool
    condition: CaseConditionResponse

    @classmethod
    def from_domain(cls, result: CaseConditionEvaluationResult) -> CaseConditionEvaluationResponse:
        return cls(
            satisfied=result.satisfied,
            transitioned=result.transitioned,
            condition=CaseConditionResponse.from_domain(result.view),
        )
