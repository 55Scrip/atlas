"""Shared Decision Engine pipeline assembly (ATLAS-016, generalized ATLAS-017).

`run_decision_engine_for_case` is the one place in `atlas.alpha` that
constructs `DecisionEngineInput` and calls
`atlas.decision_engine.pipeline.run_pipeline` -- extracted from
`atlas.alpha.portfolio_intelligence.service.PortfolioIntelligenceService`
(ATLAS-016's own per-holding loop body) so `atlas.alpha.case_intelligence`
(ATLAS-017) can run the identical, canonical pipeline for a single Case
without a second, independent assembly of `DecisionEngineInput` --
directly the "no duplicated reasoning" principle both sprints require.

Generalized beyond ATLAS-016's original assumption (`holding` always
present): `holding` is `None` when the Case has no linked Alpha holding
at all -- a real, honest state (`HoldingLinkage.ABSENT`), not an error.
`PortfolioIntelligenceService` never passes `None` (it only ever iterates
Case-linked holdings); `CaseIntelligenceService` may, since an Investment
Case can exist before any holding links to it.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.observation.entity import Observation
from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    DecisionEngineOutput,
    EvidenceCoverageLevel,
    PortfolioHoldingContext,
    ReconciliationState,
    TradeLogEntry,
)
from atlas.decision_engine.pipeline import run_pipeline


def build_decision_engine_input(
    case_id: str,
    *,
    holding: AlphaHolding | None,
    decisions: tuple[Decision, ...],
    observations: tuple[Observation, ...],
    evidence: tuple[Evidence, ...],
    outcomes: tuple,
    trade_log_entries: tuple[AlphaTradeLogEntry, ...],
    evaluated_at: datetime,
) -> DecisionEngineInput:
    """Assemble one `DecisionEngineInput` for one Case -- the pure
    construction half of `run_decision_engine_for_case`, split out
    (ATLAS-027) so a caller that needs the `DecisionEngineInput` itself
    (`atlas.analysis_engine.pipeline.assemble_analysis` requires one,
    per its own docstring) does not have to re-derive this assembly a
    second time. `run_decision_engine_for_case` below is unchanged in
    behavior and signature -- it simply calls this function, then
    `run_pipeline`, exactly as it always did.

    `outcomes` is deliberately untyped (not `tuple[Outcome, ...]`):
    `atlas.alpha` is forbidden from importing
    `atlas.core.domain.outcome.entity` at all, even for a type
    annotation, so Alpha can never originate or construct an Outcome
    (see `tests/test_architecture_boundaries.py
    ::test_alpha_does_not_write_to_outcome`). Every element's real type
    is `atlas.core.domain.outcome.entity.Outcome`, inferred from
    `OutcomeRepository.list_all()`'s own return type at the call site.

    `trade_log_entries` must already be scoped to this Case's ticker by
    the caller (matched on `AlphaTradeLogEntry.security ==
    holding.ticker`) -- this function does no matching of its own, only
    assembly.
    """
    trade_log = tuple(
        TradeLogEntry(
            security=trade.security,
            transaction_type=trade.transaction_type.value,
            quantity=trade.quantity,
            execution_price=trade.execution_price,
            executed_at=trade.executed_at,
        )
        for trade in trade_log_entries
    )
    portfolio_holding = (
        PortfolioHoldingContext(
            ticker=holding.ticker,
            weight_percent=holding.weight_percent,
            value_absolute=holding.value_absolute,
            reconciliation_status=ReconciliationState(holding.reconciliation_status.value),
        )
        if holding is not None
        else None
    )
    return DecisionEngineInput(
        case_id=CaseId(value=uuid.UUID(case_id)),
        evaluated_at=evaluated_at,
        decisions=decisions,
        outcomes=outcomes,
        observations=observations,
        evidence=evidence,
        portfolio_holding=portfolio_holding,
        trade_log=trade_log,
    )


def run_decision_engine_for_case(
    case_id: str,
    *,
    holding: AlphaHolding | None,
    decisions: tuple[Decision, ...],
    observations: tuple[Observation, ...],
    evidence: tuple[Evidence, ...],
    outcomes: tuple,
    trade_log_entries: tuple[AlphaTradeLogEntry, ...],
    evaluated_at: datetime,
) -> DecisionEngineOutput:
    """Run one Decision Engine pipeline pass for one Case. See
    `build_decision_engine_input`'s own docstring for the assembly
    rules this delegates to; unchanged in behavior since ATLAS-016."""
    engine_input = build_decision_engine_input(
        case_id,
        holding=holding,
        decisions=decisions,
        observations=observations,
        evidence=evidence,
        outcomes=outcomes,
        trade_log_entries=trade_log_entries,
        evaluated_at=evaluated_at,
    )
    return run_pipeline(engine_input, generated_at=evaluated_at)


def coverage_for(output: DecisionEngineOutput) -> EvidenceCoverageLevel:
    """`output.business_evaluation.evidence_quality.coverage`, or
    `NOT_APPLICABLE` when the finding itself is absent -- the same
    fallback `PortfolioIntelligenceService._coverage_for` already used
    before this extraction."""
    if output.business_evaluation.evidence_quality is None:
        return EvidenceCoverageLevel.NOT_APPLICABLE
    return output.business_evaluation.evidence_quality.coverage


def evidence_gap_count(output: DecisionEngineOutput) -> int:
    """Count of real `EvidenceGap`s on this output -- used (rather than
    `coverage`) to detect a genuine gap, because a Case with zero
    recorded Observations reports `coverage=NOT_APPLICABLE` yet still
    legitimately carries a case-wide `NO_EVIDENCE_RECORDED` gap; see
    `atlas.alpha.portfolio_intelligence.service`'s own note on this."""
    if output.business_evaluation.evidence_quality is None:
        return 0
    return len(output.business_evaluation.evidence_quality.evidence_gaps)
