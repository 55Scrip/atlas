"""HTTP request/response schemas for Assumption (ADR-AS-001).

CamelCase via the shared `CamelModel` (ADR-004), mirroring
`case_condition/schemas.py` (Sprint 10) exactly.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from atlas.core.domain.assumption.entity import AssumptionView
from atlas.core.infrastructure.api.serialization import CamelModel


class CreateAssumptionRequest(CamelModel):
    statement: str | None = None
    authorship: Literal["atlas", "user", "mixed"] | None = None


class ReviseAssumptionRequest(CamelModel):
    statement: str | None = None
    authorship: Literal["atlas", "user", "mixed"] | None = None


class ChallengeAssumptionRequest(CamelModel):
    evidence_id: str | None = None
    note: str | None = None
    severity: Literal["challenged", "invalidated"] = "challenged"


class SupersedeAssumptionRequest(CamelModel):
    superseded_by_assumption_id: uuid.UUID | None = None


class AssumptionResponse(CamelModel):
    assumption_id: uuid.UUID
    decision_id: uuid.UUID
    case_id: uuid.UUID
    status: Literal["supported", "challenged", "invalidated", "superseded", "retired"]
    is_active: bool
    statement: str | None
    authorship: Literal["atlas", "user", "mixed"] | None
    linked_case_condition_ids: list[uuid.UUID]
    last_challenge_evidence_id: str | None
    last_challenge_note: str | None
    superseded_by_assumption_id: uuid.UUID | None
    latest_event_id: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, view: AssumptionView) -> AssumptionResponse:
        return cls(
            assumption_id=view.assumption_id.value,
            decision_id=view.decision_id.value,
            case_id=view.case_id.value,
            status=view.status,
            is_active=view.is_active,
            statement=view.statement,
            authorship=view.authorship,
            linked_case_condition_ids=[
                uuid.UUID(linked_id) for linked_id in view.linked_case_condition_ids
            ],
            last_challenge_evidence_id=view.last_challenge_evidence_id,
            last_challenge_note=view.last_challenge_note,
            superseded_by_assumption_id=(
                uuid.UUID(view.superseded_by_assumption_id)
                if view.superseded_by_assumption_id is not None
                else None
            ),
            latest_event_id=view.latest_event_id,
            created_at=view.created_at,
            updated_at=view.updated_at,
        )
