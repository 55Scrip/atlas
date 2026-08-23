"""SQLAlchemy-backed read-model cache for `RecommendationConviction`.
One row per `case_id`, upserted -- mirrors `atlas.alpha.investment_decision
.repository.SqlAlchemyInvestmentDecisionResultRepository` exactly.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import (
    ConvictionReason,
    ConvictionReasonSource,
    ConvictionStrength,
    RecommendationConviction,
    RecommendationStability,
)
from atlas.alpha.recommendation_conviction.table import recommendation_conviction_result_table

__all__ = ["SqlAlchemyRecommendationConvictionResultRepository"]


def _reason_payload(reason: ConvictionReason) -> dict:
    return {"source": reason.source.value, "code": reason.code}


def _to_reason(payload: dict) -> ConvictionReason:
    return ConvictionReason(source=ConvictionReasonSource(payload["source"]), code=payload["code"])


def _result_payload(conviction: RecommendationConviction) -> dict:
    return {
        "caseId": conviction.case_id,
        "action": conviction.action.value,
        "strength": conviction.strength.value,
        "stability": conviction.stability.value,
        "supportingReasons": [_reason_payload(r) for r in conviction.supporting_reasons],
        "limitingReasons": [_reason_payload(r) for r in conviction.limiting_reasons],
        "strengtheningTrigger": _reason_payload(conviction.strengthening_trigger)
        if conviction.strengthening_trigger is not None
        else None,
        "generatedAt": conviction.generated_at.isoformat(),
    }


def _to_conviction(payload: dict) -> RecommendationConviction:
    return RecommendationConviction(
        case_id=payload["caseId"],
        action=DecisionAction(payload["action"]),
        strength=ConvictionStrength(payload["strength"]),
        stability=RecommendationStability(payload["stability"]),
        supporting_reasons=tuple(_to_reason(r) for r in payload["supportingReasons"]),
        limiting_reasons=tuple(_to_reason(r) for r in payload["limitingReasons"]),
        strengthening_trigger=_to_reason(payload["strengtheningTrigger"])
        if payload["strengtheningTrigger"] is not None
        else None,
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyRecommendationConvictionResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, conviction: RecommendationConviction, *, ticker: str | None) -> None:
        payload = json.dumps(_result_payload(conviction))
        with self._engine.begin() as connection:
            connection.execute(
                delete(recommendation_conviction_result_table).where(
                    recommendation_conviction_result_table.c.case_id == conviction.case_id
                )
            )
            connection.execute(
                insert(recommendation_conviction_result_table).values(
                    case_id=conviction.case_id,
                    ticker=ticker,
                    generated_at=conviction.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> RecommendationConviction | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(recommendation_conviction_result_table).where(
                        recommendation_conviction_result_table.c.case_id == case_id
                    )
                )
                .mappings()
                .first()
            )
        return _to_conviction(json.loads(row["result_json"])) if row is not None else None

    def list_all(self) -> tuple[RecommendationConviction, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(recommendation_conviction_result_table)).mappings().all()
        return tuple(_to_conviction(json.loads(row["result_json"])) for row in rows)
