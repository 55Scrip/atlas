"""SQLAlchemy-backed read-model cache for `DecisionPath`. One row per
`case_id`, upserted -- mirrors `atlas.alpha.recommendation_conviction
.repository.SqlAlchemyRecommendationConvictionResultRepository` exactly.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionStep,
    DependencyReference,
    DependencySource,
    FinalReachableState,
    ReachabilityStatus,
    RequiredProgressKind,
)
from atlas.alpha.decision_path.table import decision_path_result_table
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionStrength

__all__ = ["SqlAlchemyDecisionPathResultRepository"]


def _step_payload(step: DecisionStep) -> dict:
    return {
        "source": step.dependency.source.value,
        "code": step.dependency.code,
        "progressKind": step.progress_kind.value,
        "reachability": step.reachability.value,
    }


def _to_step(payload: dict) -> DecisionStep:
    return DecisionStep(
        dependency=DependencyReference(DependencySource(payload["source"]), payload["code"]),
        progress_kind=RequiredProgressKind(payload["progressKind"]),
        reachability=ReachabilityStatus(payload["reachability"]),
    )


def _result_payload(path: DecisionPath) -> dict:
    return {
        "caseId": path.case_id,
        "currentAction": path.current_action.value,
        "currentStrength": path.current_strength.value,
        "steps": [_step_payload(s) for s in path.steps],
        "immediateBlocker": _step_payload(path.immediate_blocker) if path.immediate_blocker is not None else None,
        "nextAchievableImprovement": _step_payload(path.next_achievable_improvement)
        if path.next_achievable_improvement is not None
        else None,
        "finalReachableState": path.final_reachable_state.value,
        "generatedAt": path.generated_at.isoformat(),
    }


def _to_path(payload: dict) -> DecisionPath:
    return DecisionPath(
        case_id=payload["caseId"],
        current_action=DecisionAction(payload["currentAction"]),
        current_strength=ConvictionStrength(payload["currentStrength"]),
        steps=tuple(_to_step(s) for s in payload["steps"]),
        immediate_blocker=_to_step(payload["immediateBlocker"]) if payload["immediateBlocker"] is not None else None,
        next_achievable_improvement=_to_step(payload["nextAchievableImprovement"])
        if payload["nextAchievableImprovement"] is not None
        else None,
        final_reachable_state=FinalReachableState(payload["finalReachableState"]),
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyDecisionPathResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, path: DecisionPath, *, ticker: str | None) -> None:
        payload = json.dumps(_result_payload(path))
        with self._engine.begin() as connection:
            connection.execute(delete(decision_path_result_table).where(decision_path_result_table.c.case_id == path.case_id))
            connection.execute(
                insert(decision_path_result_table).values(
                    case_id=path.case_id,
                    ticker=ticker,
                    generated_at=path.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> DecisionPath | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(decision_path_result_table).where(decision_path_result_table.c.case_id == case_id))
                .mappings()
                .first()
            )
        return _to_path(json.loads(row["result_json"])) if row is not None else None

    def list_all(self) -> tuple[DecisionPath, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(decision_path_result_table)).mappings().all()
        return tuple(_to_path(json.loads(row["result_json"])) for row in rows)
