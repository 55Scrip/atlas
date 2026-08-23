"""SQLAlchemy-backed read-model cache for `PortfolioDecision`. One row
per `case_id`, upserted -- mirrors `atlas.alpha.decision_reliability
.repository.SqlAlchemyDecisionReliabilityResultRepository` exactly.
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
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import AlternativeKind, AlternativeReason, AlternativeReasonSource, DecisionAlternative
from atlas.alpha.portfolio_decision.models import (
    CapitalCompetition,
    PortfolioDecision,
    PortfolioDecisionCategory,
    PortfolioDecisionImpact,
    PortfolioDecisionReason,
    PortfolioDecisionReasonSource,
)
from atlas.alpha.portfolio_decision.table import portfolio_decision_result_table
from atlas.alpha.recommendation_conviction.models import ConvictionStrength
from atlas.domains.portfolio.models import ConcentrationLevel

__all__ = ["SqlAlchemyPortfolioDecisionResultRepository"]


def _reference_payload(reference: ExplanationReference) -> dict:
    return {"kind": reference.kind.value, "id": reference.id}


def _to_reference(payload: dict) -> ExplanationReference:
    return ExplanationReference(kind=ExplanationReferenceKind(payload["kind"]), id=payload["id"])


def _reason_payload(reason: PortfolioDecisionReason) -> dict:
    return {"source": reason.source.value, "reference": _reference_payload(reason.reference)}


def _to_reason(payload: dict) -> PortfolioDecisionReason:
    return PortfolioDecisionReason(source=PortfolioDecisionReasonSource(payload["source"]), reference=_to_reference(payload["reference"]))


def _alt_reason_payload(reason: AlternativeReason) -> dict:
    return {"source": reason.source.value, "code": reason.code}


def _to_alt_reason(payload: dict) -> AlternativeReason:
    return AlternativeReason(source=AlternativeReasonSource(payload["source"]), code=payload["code"])


def _alternative_payload(alternative: DecisionAlternative) -> dict:
    return {
        "kind": alternative.kind.value,
        "caseId": alternative.case_id,
        "ticker": alternative.ticker,
        "action": alternative.action.value if alternative.action is not None else None,
        "strength": alternative.strength.value if alternative.strength is not None else None,
        "reason": _alt_reason_payload(alternative.reason),
    }


def _to_alternative(payload: dict) -> DecisionAlternative:
    return DecisionAlternative(
        kind=AlternativeKind(payload["kind"]),
        case_id=payload["caseId"],
        ticker=payload["ticker"],
        action=DecisionAction(payload["action"]) if payload["action"] is not None else None,
        strength=ConvictionStrength(payload["strength"]) if payload["strength"] is not None else None,
        reason=_to_alt_reason(payload["reason"]),
    )


def _competition_payload(competition: CapitalCompetition) -> dict:
    return {
        "caseId": competition.case_id,
        "competing": [_alternative_payload(a) for a in competition.competing_alternatives],
        "nonCompeting": [_alternative_payload(a) for a in competition.non_competing_alternatives],
    }


def _to_competition(payload: dict) -> CapitalCompetition:
    return CapitalCompetition(
        case_id=payload["caseId"],
        competing_alternatives=tuple(_to_alternative(a) for a in payload["competing"]),
        non_competing_alternatives=tuple(_to_alternative(a) for a in payload["nonCompeting"]),
    )


def _impact_payload(impact: PortfolioDecisionImpact) -> dict:
    return {
        "isExistingHolding": impact.is_existing_holding,
        "currentWeightPercent": impact.current_weight_percent,
        "isLargestPosition": impact.is_largest_position,
        "allocationRating": impact.allocation_rating,
        "portfolioConcentrationLevel": impact.portfolio_concentration_level.value,
    }


def _to_impact(payload: dict) -> PortfolioDecisionImpact:
    return PortfolioDecisionImpact(
        is_existing_holding=payload["isExistingHolding"],
        current_weight_percent=payload["currentWeightPercent"],
        is_largest_position=payload["isLargestPosition"],
        allocation_rating=payload["allocationRating"],
        portfolio_concentration_level=ConcentrationLevel(payload["portfolioConcentrationLevel"]),
    )


def _result_payload(decision: PortfolioDecision) -> dict:
    return {
        "caseId": decision.case_id,
        "action": decision.action.value,
        "category": decision.category.value,
        "impact": _impact_payload(decision.impact),
        "capitalCompetition": _competition_payload(decision.capital_competition),
        "supportingReasons": [_reason_payload(r) for r in decision.supporting_reasons],
        "limitingReasons": [_reason_payload(r) for r in decision.limiting_reasons],
        "primaryLimitingReason": _reason_payload(decision.primary_limiting_reason) if decision.primary_limiting_reason is not None else None,
        "generatedAt": decision.generated_at.isoformat(),
    }


def _to_decision(payload: dict) -> PortfolioDecision:
    return PortfolioDecision(
        case_id=payload["caseId"],
        action=DecisionAction(payload["action"]),
        category=PortfolioDecisionCategory(payload["category"]),
        impact=_to_impact(payload["impact"]),
        capital_competition=_to_competition(payload["capitalCompetition"]),
        supporting_reasons=tuple(_to_reason(r) for r in payload["supportingReasons"]),
        limiting_reasons=tuple(_to_reason(r) for r in payload["limitingReasons"]),
        primary_limiting_reason=_to_reason(payload["primaryLimitingReason"]) if payload["primaryLimitingReason"] is not None else None,
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyPortfolioDecisionResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, decision: PortfolioDecision, *, ticker: str | None) -> None:
        payload = json.dumps(_result_payload(decision))
        with self._engine.begin() as connection:
            connection.execute(
                delete(portfolio_decision_result_table).where(portfolio_decision_result_table.c.case_id == decision.case_id)
            )
            connection.execute(
                insert(portfolio_decision_result_table).values(
                    case_id=decision.case_id,
                    ticker=ticker,
                    generated_at=decision.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> PortfolioDecision | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(portfolio_decision_result_table).where(portfolio_decision_result_table.c.case_id == case_id)
                )
                .mappings()
                .first()
            )
        return _to_decision(json.loads(row["result_json"])) if row is not None else None
