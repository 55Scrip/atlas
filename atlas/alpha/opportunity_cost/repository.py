"""SQLAlchemy-backed read-model cache for `OpportunityCost`. One row
per `case_id`, upserted -- mirrors `atlas.alpha.decision_path
.repository.SqlAlchemyDecisionPathResultRepository` exactly. Every
nested object (`RecommendationConviction`, `DecisionPath`, and their
own comparisons) is serialized in full, the same "no lossy cache"
discipline every sibling repository in the Decision Layer already
follows.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionPathComparison,
    DecisionStep,
    DependencyReference,
    DependencySource,
    FinalReachableState,
    ReachabilityStatus,
    RequiredProgressKind,
)
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import (
    AlternativeComparison,
    AlternativeKind,
    AlternativeReason,
    AlternativeReasonSource,
    DecisionAlternative,
    DecisionTradeoff,
    OpportunityCost,
)
from atlas.alpha.opportunity_cost.table import opportunity_cost_result_table
from atlas.alpha.recommendation_conviction.models import (
    ConvictionComparison,
    ConvictionReason,
    ConvictionReasonSource,
    ConvictionStrength,
    RecommendationConviction,
    RecommendationStability,
)

__all__ = ["SqlAlchemyOpportunityCostResultRepository"]


def _conviction_reason_payload(reason: ConvictionReason) -> dict:
    return {"source": reason.source.value, "code": reason.code}


def _to_conviction_reason(payload: dict) -> ConvictionReason:
    return ConvictionReason(source=ConvictionReasonSource(payload["source"]), code=payload["code"])


def _conviction_payload(conviction: RecommendationConviction) -> dict:
    return {
        "caseId": conviction.case_id,
        "action": conviction.action.value,
        "strength": conviction.strength.value,
        "stability": conviction.stability.value,
        "supportingReasons": [_conviction_reason_payload(r) for r in conviction.supporting_reasons],
        "limitingReasons": [_conviction_reason_payload(r) for r in conviction.limiting_reasons],
        "strengtheningTrigger": _conviction_reason_payload(conviction.strengthening_trigger)
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
        supporting_reasons=tuple(_to_conviction_reason(r) for r in payload["supportingReasons"]),
        limiting_reasons=tuple(_to_conviction_reason(r) for r in payload["limitingReasons"]),
        strengthening_trigger=_to_conviction_reason(payload["strengtheningTrigger"])
        if payload["strengtheningTrigger"] is not None
        else None,
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


def _conviction_comparison_payload(comparison: ConvictionComparison) -> dict:
    return {
        "a": _conviction_payload(comparison.a),
        "b": _conviction_payload(comparison.b),
        "strongerCaseId": comparison.stronger_case_id,
        "moreEvidenceLimitedCaseId": comparison.more_evidence_limited_case_id,
        "moreOperationallyBlockedCaseId": comparison.more_operationally_blocked_case_id,
        "moreStableCaseId": comparison.more_stable_case_id,
    }


def _to_conviction_comparison(payload: dict) -> ConvictionComparison:
    return ConvictionComparison(
        a=_to_conviction(payload["a"]),
        b=_to_conviction(payload["b"]),
        stronger_case_id=payload["strongerCaseId"],
        more_evidence_limited_case_id=payload["moreEvidenceLimitedCaseId"],
        more_operationally_blocked_case_id=payload["moreOperationallyBlockedCaseId"],
        more_stable_case_id=payload["moreStableCaseId"],
    )


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


def _path_payload(path: DecisionPath) -> dict:
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


def _path_comparison_payload(comparison: DecisionPathComparison) -> dict:
    return {
        "a": _path_payload(comparison.a),
        "b": _path_payload(comparison.b),
        "shorterPathCaseId": comparison.shorter_path_case_id,
        "fewerRemainingBlockersCaseId": comparison.fewer_remaining_blockers_case_id,
        "moreOperationallyDependentCaseId": comparison.more_operationally_dependent_case_id,
        "moreEvidenceDependentCaseId": comparison.more_evidence_dependent_case_id,
    }


def _to_path_comparison(payload: dict) -> DecisionPathComparison:
    return DecisionPathComparison(
        a=_to_path(payload["a"]),
        b=_to_path(payload["b"]),
        shorter_path_case_id=payload["shorterPathCaseId"],
        fewer_remaining_blockers_case_id=payload["fewerRemainingBlockersCaseId"],
        more_operationally_dependent_case_id=payload["moreOperationallyDependentCaseId"],
        more_evidence_dependent_case_id=payload["moreEvidenceDependentCaseId"],
    )


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


def _alternative_comparison_payload(comparison: AlternativeComparison) -> dict:
    return {
        "conviction": _conviction_comparison_payload(comparison.conviction),
        "path": _path_comparison_payload(comparison.path),
        "moreDependencyBlockedCaseId": comparison.more_dependency_blocked_case_id,
    }


def _to_alternative_comparison(payload: dict) -> AlternativeComparison:
    return AlternativeComparison(
        conviction=_to_conviction_comparison(payload["conviction"]),
        path=_to_path_comparison(payload["path"]),
        more_dependency_blocked_case_id=payload["moreDependencyBlockedCaseId"],
    )


def _tradeoff_payload(tradeoff: DecisionTradeoff) -> dict:
    return {
        "alternative": _alternative_payload(tradeoff.alternative),
        "comparison": _alternative_comparison_payload(tradeoff.comparison) if tradeoff.comparison is not None else None,
    }


def _to_tradeoff(payload: dict) -> DecisionTradeoff:
    return DecisionTradeoff(
        alternative=_to_alternative(payload["alternative"]),
        comparison=_to_alternative_comparison(payload["comparison"]) if payload["comparison"] is not None else None,
    )


def _result_payload(opportunity_cost: OpportunityCost) -> dict:
    return {
        "caseId": opportunity_cost.case_id,
        "currentAction": opportunity_cost.current_action.value,
        "tradeoffs": [_tradeoff_payload(t) for t in opportunity_cost.tradeoffs],
        "generatedAt": opportunity_cost.generated_at.isoformat(),
    }


def _to_opportunity_cost(payload: dict) -> OpportunityCost:
    return OpportunityCost(
        case_id=payload["caseId"],
        current_action=DecisionAction(payload["currentAction"]),
        tradeoffs=tuple(_to_tradeoff(t) for t in payload["tradeoffs"]),
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyOpportunityCostResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, opportunity_cost: OpportunityCost, *, ticker: str | None) -> None:
        payload = json.dumps(_result_payload(opportunity_cost))
        with self._engine.begin() as connection:
            connection.execute(
                delete(opportunity_cost_result_table).where(opportunity_cost_result_table.c.case_id == opportunity_cost.case_id)
            )
            connection.execute(
                insert(opportunity_cost_result_table).values(
                    case_id=opportunity_cost.case_id,
                    ticker=ticker,
                    generated_at=opportunity_cost.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> OpportunityCost | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(opportunity_cost_result_table).where(opportunity_cost_result_table.c.case_id == case_id)
                )
                .mappings()
                .first()
            )
        return _to_opportunity_cost(json.loads(row["result_json"])) if row is not None else None

    def list_all(self) -> tuple[OpportunityCost, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(opportunity_cost_result_table)).mappings().all()
        return tuple(_to_opportunity_cost(json.loads(row["result_json"])) for row in rows)
