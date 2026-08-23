"""SQLAlchemy-backed read-model cache for `DecisionExplanation`. One
row per `case_id`, upserted -- mirrors `atlas.alpha.opportunity_cost
.repository.SqlAlchemyOpportunityCostResultRepository` exactly. Every
nested reference is serialized in full, the same "no lossy cache"
discipline every sibling repository in the Decision Layer already
follows.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.decision_explanation.models import (
    BlockingFinding,
    DecisionExplanation,
    ExplanationChain,
    ExplanationLayer,
    ExplanationReference,
    ExplanationReferenceKind,
    ExplanationSection,
    ExplanationSectionKind,
    SupportingFinding,
)
from atlas.alpha.decision_explanation.table import decision_explanation_result_table
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionStrength

__all__ = ["SqlAlchemyDecisionExplanationResultRepository"]


def _reference_payload(reference: ExplanationReference) -> dict:
    return {"kind": reference.kind.value, "id": reference.id}


def _to_reference(payload: dict) -> ExplanationReference:
    return ExplanationReference(kind=ExplanationReferenceKind(payload["kind"]), id=payload["id"])


def _supporting_payload(finding: SupportingFinding) -> dict:
    return {"reference": _reference_payload(finding.reference), "namedBy": [layer.value for layer in finding.named_by]}


def _to_supporting(payload: dict) -> SupportingFinding:
    return SupportingFinding(
        reference=_to_reference(payload["reference"]),
        named_by=tuple(ExplanationLayer(layer) for layer in payload["namedBy"]),
    )


def _blocking_payload(finding: BlockingFinding) -> dict:
    return {
        "reference": _reference_payload(finding.reference),
        "namedBy": [layer.value for layer in finding.named_by],
        "isChangeTrigger": finding.is_change_trigger,
    }


def _to_blocking(payload: dict) -> BlockingFinding:
    return BlockingFinding(
        reference=_to_reference(payload["reference"]),
        named_by=tuple(ExplanationLayer(layer) for layer in payload["namedBy"]),
        is_change_trigger=payload["isChangeTrigger"],
    )


def _section_payload(section: ExplanationSection) -> dict:
    return {"kind": section.kind.value, "itemCount": section.item_count}


def _to_section(payload: dict) -> ExplanationSection:
    return ExplanationSection(kind=ExplanationSectionKind(payload["kind"]), item_count=payload["itemCount"])


def _chain_payload(chain: ExplanationChain) -> dict:
    return {
        "caseId": chain.case_id,
        "order": [_section_payload(s) for s in chain.order],
        "supporting": [_supporting_payload(s) for s in chain.supporting],
        "blocking": [_blocking_payload(b) for b in chain.blocking],
        "dependencySteps": [_reference_payload(r) for r in chain.dependency_steps],
        "historicalReference": _reference_payload(chain.historical_reference)
        if chain.historical_reference is not None
        else None,
    }


def _to_chain(payload: dict) -> ExplanationChain:
    return ExplanationChain(
        case_id=payload["caseId"],
        order=tuple(_to_section(s) for s in payload["order"]),
        supporting=tuple(_to_supporting(s) for s in payload["supporting"]),
        blocking=tuple(_to_blocking(b) for b in payload["blocking"]),
        dependency_steps=tuple(_to_reference(r) for r in payload["dependencySteps"]),
        historical_reference=_to_reference(payload["historicalReference"])
        if payload["historicalReference"] is not None
        else None,
    )


def _result_payload(explanation: DecisionExplanation) -> dict:
    return {
        "caseId": explanation.case_id,
        "action": explanation.action.value,
        "convictionStrength": explanation.conviction_strength.value,
        "chain": _chain_payload(explanation.chain),
        "primarySupporting": _supporting_payload(explanation.primary_supporting)
        if explanation.primary_supporting is not None
        else None,
        "primaryBlocking": _blocking_payload(explanation.primary_blocking)
        if explanation.primary_blocking is not None
        else None,
        "generatedAt": explanation.generated_at.isoformat(),
    }


def _to_explanation(payload: dict) -> DecisionExplanation:
    return DecisionExplanation(
        case_id=payload["caseId"],
        action=DecisionAction(payload["action"]),
        conviction_strength=ConvictionStrength(payload["convictionStrength"]),
        chain=_to_chain(payload["chain"]),
        primary_supporting=_to_supporting(payload["primarySupporting"]) if payload["primarySupporting"] is not None else None,
        primary_blocking=_to_blocking(payload["primaryBlocking"]) if payload["primaryBlocking"] is not None else None,
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyDecisionExplanationResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, explanation: DecisionExplanation, *, ticker: str | None) -> None:
        payload = json.dumps(_result_payload(explanation))
        with self._engine.begin() as connection:
            connection.execute(
                delete(decision_explanation_result_table).where(
                    decision_explanation_result_table.c.case_id == explanation.case_id
                )
            )
            connection.execute(
                insert(decision_explanation_result_table).values(
                    case_id=explanation.case_id,
                    ticker=ticker,
                    generated_at=explanation.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> DecisionExplanation | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(decision_explanation_result_table).where(decision_explanation_result_table.c.case_id == case_id)
                )
                .mappings()
                .first()
            )
        return _to_explanation(json.loads(row["result_json"])) if row is not None else None
