"""SQLAlchemy-backed read-model cache for `InvestmentDecision`. One row
per `case_id`, upserted -- mirrors `atlas.alpha.decision_readiness
.repository.SqlAlchemyDecisionReadinessResultRepository` exactly.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.investment_decision.models import (
    DecisionAction,
    DecisionQualifier,
    DecisionQualifierKind,
    DecisionReason,
    DecisionReasonSource,
    InvestmentDecision,
)
from atlas.alpha.investment_decision.table import investment_decision_result_table

__all__ = ["SqlAlchemyInvestmentDecisionResultRepository"]


def _reason_payload(reason: DecisionReason) -> dict:
    return {"source": reason.source.value, "code": reason.code}


def _to_reason(payload: dict) -> DecisionReason:
    return DecisionReason(source=DecisionReasonSource(payload["source"]), code=payload["code"])


def _result_payload(decision: InvestmentDecision) -> dict:
    return {
        "caseId": decision.case_id,
        "action": decision.action.value,
        "qualifiers": [q.kind.value for q in decision.qualifiers],
        "supportingReasons": [_reason_payload(r) for r in decision.supporting_reasons],
        "blockers": [_reason_payload(r) for r in decision.blockers],
        "changeTrigger": _reason_payload(decision.change_trigger) if decision.change_trigger is not None else None,
        "generatedAt": decision.generated_at.isoformat(),
        # Canonical analytical rationale, serialized by the Core
        # reasoning module. Absent on rows written before this existed.
        "reasoning": decision.reasoning_payload,
    }


def _to_decision(payload: dict) -> InvestmentDecision:
    return InvestmentDecision(
        case_id=payload["caseId"],
        action=DecisionAction(payload["action"]),
        qualifiers=tuple(DecisionQualifier(DecisionQualifierKind(k)) for k in payload["qualifiers"]),
        supporting_reasons=tuple(_to_reason(r) for r in payload["supportingReasons"]),
        blockers=tuple(_to_reason(r) for r in payload["blockers"]),
        change_trigger=_to_reason(payload["changeTrigger"]) if payload["changeTrigger"] is not None else None,
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
        # `.get`, not `[]`: a legacy row simply has no key. Defaulting
        # to None is what keeps "written before reasoning existed"
        # distinguishable from "reasoning was computed and empty".
        reasoning_payload=payload.get("reasoning"),
    )


class SqlAlchemyInvestmentDecisionResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, decision: InvestmentDecision, *, ticker: str | None) -> None:
        payload = json.dumps(_result_payload(decision))
        with self._engine.begin() as connection:
            connection.execute(
                delete(investment_decision_result_table).where(investment_decision_result_table.c.case_id == decision.case_id)
            )
            connection.execute(
                insert(investment_decision_result_table).values(
                    case_id=decision.case_id,
                    ticker=ticker,
                    generated_at=decision.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> InvestmentDecision | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(investment_decision_result_table).where(investment_decision_result_table.c.case_id == case_id)
                )
                .mappings()
                .first()
            )
        return _to_decision(json.loads(row["result_json"])) if row is not None else None

    def list_all(self) -> tuple[InvestmentDecision, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(investment_decision_result_table)).mappings().all()
        return tuple(_to_decision(json.loads(row["result_json"])) for row in rows)
