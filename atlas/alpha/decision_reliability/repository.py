"""SQLAlchemy-backed read-model cache for `DecisionReliability`. One
row per `case_id`, upserted -- mirrors `atlas.alpha.decision_explanation
.repository.SqlAlchemyDecisionExplanationResultRepository` exactly.
Every nested reference is serialized in full, the same "no lossy
cache" discipline every sibling repository in the Decision Layer
already follows.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.decision_explanation.models import ExplanationReference, ExplanationReferenceKind
from atlas.alpha.decision_reliability.models import (
    DecisionReliability,
    ReliabilityLevel,
    ReliabilityReason,
    ReliabilitySource,
)
from atlas.alpha.decision_reliability.table import decision_reliability_result_table

__all__ = ["SqlAlchemyDecisionReliabilityResultRepository"]


def _reference_payload(reference: ExplanationReference) -> dict:
    return {"kind": reference.kind.value, "id": reference.id}


def _to_reference(payload: dict) -> ExplanationReference:
    return ExplanationReference(kind=ExplanationReferenceKind(payload["kind"]), id=payload["id"])


def _reason_payload(reason: ReliabilityReason) -> dict:
    return {
        "source": reason.source.value,
        "reference": _reference_payload(reason.reference),
        "count": reason.count,
        "total": reason.total,
    }


def _to_reason(payload: dict) -> ReliabilityReason:
    return ReliabilityReason(
        source=ReliabilitySource(payload["source"]),
        reference=_to_reference(payload["reference"]),
        count=payload.get("count"),
        total=payload.get("total"),
    )


def _result_payload(reliability: DecisionReliability) -> dict:
    return {
        "caseId": reliability.case_id,
        "level": reliability.level.value,
        "supportingReasons": [_reason_payload(r) for r in reliability.supporting_reasons],
        "limitingReasons": [_reason_payload(r) for r in reliability.limiting_reasons],
        "primaryLimitingReason": _reason_payload(reliability.primary_limiting_reason)
        if reliability.primary_limiting_reason is not None
        else None,
        "generatedAt": reliability.generated_at.isoformat(),
    }


def _to_reliability(payload: dict) -> DecisionReliability:
    return DecisionReliability(
        case_id=payload["caseId"],
        level=ReliabilityLevel(payload["level"]),
        supporting_reasons=tuple(_to_reason(r) for r in payload["supportingReasons"]),
        limiting_reasons=tuple(_to_reason(r) for r in payload["limitingReasons"]),
        primary_limiting_reason=_to_reason(payload["primaryLimitingReason"])
        if payload["primaryLimitingReason"] is not None
        else None,
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyDecisionReliabilityResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, reliability: DecisionReliability, *, ticker: str | None) -> None:
        payload = json.dumps(_result_payload(reliability))
        with self._engine.begin() as connection:
            connection.execute(
                delete(decision_reliability_result_table).where(
                    decision_reliability_result_table.c.case_id == reliability.case_id
                )
            )
            connection.execute(
                insert(decision_reliability_result_table).values(
                    case_id=reliability.case_id,
                    ticker=ticker,
                    generated_at=reliability.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> DecisionReliability | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(decision_reliability_result_table).where(decision_reliability_result_table.c.case_id == case_id)
                )
                .mappings()
                .first()
            )
        return _to_reliability(json.loads(row["result_json"])) if row is not None else None
