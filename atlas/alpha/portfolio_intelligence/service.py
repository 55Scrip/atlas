"""Builds the Portfolio Intelligence report (ATLAS-016).

For every held Alpha holding that already has a linked Investment Case,
runs the canonical `atlas.decision_engine.pipeline.run_pipeline` once,
using only real, already-captured Core data (Decision/Observation/
Evidence, scoped to that Case) and the holding's own Alpha state --
exactly the composition boundary `atlas/decision_engine/contracts.py`'s
`PortfolioHoldingContext`/`TradeLogEntry` mirror types were built for.
This is the first caller to actually assemble `DecisionEngineInput` from
live data; before this sprint the pipeline was built but never invoked
outside its own tests.

Reuses `atlas.alpha.portfolio_status.PortfolioStatusService` (ATLAS-015)
directly for the Portfolio Overview numbers and the underlying
attention-gap facts (`AttentionItem`) that Key Findings/Consider/Risk
Signals are derived from -- never recomputed here.

Deliberately excluded, and why (the sprint's own "nothing may be
hallucinated" rule):

- "Consider Increase Conviction" / "Consider Wait" -- no field in this
  codebase's canonical domain model represents an Atlas-computed
  conviction or a "wait" signal; only `Decision.confidence` exists, and
  it is investor-entered (see `atlas/core/domain/decision/value_objects.py`),
  never Atlas's own. Inventing either would fabricate a conclusion.
- Sector/country balance, correlation, opportunity cost -- `AlphaHolding`
  carries no sector/country field, and `PortfolioDoctrineFactor` (the
  canonical pipeline's own name for these) is structurally locked to
  `INSUFFICIENT_INPUT` (see `atlas/decision_engine/stages
  /portfolio_intelligence.py`). Surfaced as `PortfolioFitStatus
  (available=False)`, never fabricated.

Concentration thresholds (25% "elevated", 35% "high") are not new
numbers invented for this sprint -- they are read directly from
`atlas.domains.portfolio.calculations.concentration_level`, the same
thresholds `PortfolioStatusService`'s own `concentration_level` field
already reflects.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from atlas.alpha.portfolio.models import AlphaPortfolioState
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio_intelligence.models import (
    ConsiderItem,
    ConsiderKind,
    KeyFinding,
    KeyFindingKind,
    MissingEvidenceItem,
    PortfolioFitStatus,
    PortfolioFitUnavailableReason,
    PortfolioIntelligenceReport,
    RiskSignal,
    RiskSignalKind,
)
from atlas.alpha.portfolio_status.models import AttentionCategory, PortfolioStatusReport
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    DecisionEngineOutput,
    EvidenceCoverageLevel,
    PortfolioHoldingContext,
    ReconciliationState,
    TradeLogEntry,
)
from atlas.decision_engine.pipeline import run_pipeline

# Reused directly from `atlas.domains.portfolio.calculations.concentration_level`
# -- not new numbers. `_HIGH` mirrors that function's `>= 0.35` branch,
# `_ELEVATED` its `>= 0.25` branch, both expressed on the 0-100 scale
# `AlphaHolding.weight_percent` already uses.
_HIGH_CONCENTRATION_WEIGHT_PERCENT = 35.0
_ELEVATED_CONCENTRATION_WEIGHT_PERCENT = 25.0

# Matches `frontend/src/routes/PortfolioPage.tsx`'s own
# `UNALLOCATED_TOLERANCE` -- the same threshold already used to decide
# whether to show an "Unallocated: X%" line, not a new number.
_UNALLOCATED_TOLERANCE_PERCENT = 0.01

_PENDING_WORKFLOW_CATEGORIES = frozenset(
    {
        AttentionCategory.DECISION_WITHOUT_OUTCOME,
        AttentionCategory.OUTCOME_WITHOUT_EXECUTION,
        AttentionCategory.OBSERVATION_WITHOUT_DECISION,
    }
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PortfolioIntelligenceService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        trade_log_store: AlphaTradeLogStore,
        decision_repository: DecisionRepository,
        observation_repository: ObservationRepository,
        evidence_repository: EvidenceRepository,
        outcome_repository: OutcomeRepository,
        portfolio_status_service: PortfolioStatusService,
    ) -> None:
        self._portfolio_store = portfolio_store
        self._trade_log_store = trade_log_store
        self._decision_repository = decision_repository
        self._observation_repository = observation_repository
        self._evidence_repository = evidence_repository
        self._outcome_repository = outcome_repository
        self._portfolio_status_service = portfolio_status_service

    def build_report(self) -> PortfolioIntelligenceReport:
        state = self._portfolio_store.get()
        if state is None or not state.holdings:
            return PortfolioIntelligenceReport.empty()

        status_report = self._portfolio_status_service.build_report()

        pipeline_outputs = self._run_pipeline_per_case(state)

        key_findings = self._build_key_findings(status_report, pipeline_outputs)
        consider_items = self._build_consider_items(state, status_report, pipeline_outputs)
        risk_signals = self._build_risk_signals(state, status_report, pipeline_outputs)
        missing_evidence = self._build_missing_evidence(pipeline_outputs)

        return PortfolioIntelligenceReport(
            exists=True,
            overview=status_report.summary,
            cash_weight_percent=state.cash_weight_percent,
            cash_value_absolute=state.cash_value_absolute,
            key_findings=key_findings,
            consider_items=consider_items,
            risk_signals=risk_signals,
            missing_evidence=missing_evidence,
            portfolio_fit=PortfolioFitStatus(
                available=False, reason=PortfolioFitUnavailableReason.NOT_YET_IMPLEMENTED
            ),
        )

    # -- Decision Engine pipeline composition -----------------------------

    def _run_pipeline_per_case(
        self, state: AlphaPortfolioState
    ) -> dict[str, DecisionEngineOutput]:
        """One `run_pipeline` call per held, Case-linked holding. All
        source data is fetched once, then sliced in memory per Case --
        the same N+1-avoidance pattern `PortfolioStatusService.build_report`
        already uses."""
        all_decisions = self._decision_repository.list_all()
        all_observations = self._observation_repository.list_all()
        all_evidence = self._evidence_repository.list_all()
        all_outcomes = self._outcome_repository.list_all()
        all_trades = self._trade_log_store.list_all()

        decisions_by_case: dict[str, list[Decision]] = defaultdict(list)
        for decision in all_decisions:
            decisions_by_case[str(decision.case_id)].append(decision)

        observations_by_case: dict[str, list[Observation]] = defaultdict(list)
        for observation in all_observations:
            observations_by_case[str(observation.case_id)].append(observation)

        # Untyped (rather than `dict[str, list[Outcome]]`): `atlas.alpha`
        # is forbidden from importing `atlas.core.domain.outcome.entity`
        # at all -- even for a type annotation -- so Alpha can never
        # originate or construct an Outcome (see
        # `tests/test_architecture_boundaries.py::test_alpha_does_not_write_to_outcome`).
        # `all_outcomes`'s own element type is inferred from
        # `OutcomeRepository.list_all()`'s return type instead.
        outcomes_by_case = defaultdict(list)
        for outcome in all_outcomes:
            outcomes_by_case[str(outcome.case_id)].append(outcome)

        evidence_by_observation_id: dict[object, list[Evidence]] = defaultdict(list)
        for item in all_evidence:
            evidence_by_observation_id[item.observation_id].append(item)

        trades_by_security: dict[str, list] = defaultdict(list)
        for trade in all_trades:
            trades_by_security[trade.security].append(trade)

        evaluated_at = _utc_now()
        outputs: dict[str, DecisionEngineOutput] = {}

        for holding in state.holdings:
            if holding.case_id is None:
                continue

            case_observations = tuple(observations_by_case.get(holding.case_id, ()))
            case_evidence = tuple(
                item
                for observation in case_observations
                for item in evidence_by_observation_id.get(observation.id, ())
            )
            trade_log = tuple(
                TradeLogEntry(
                    security=trade.security,
                    transaction_type=trade.transaction_type.value,
                    quantity=trade.quantity,
                    execution_price=trade.execution_price,
                    executed_at=trade.executed_at,
                )
                for trade in trades_by_security.get(holding.ticker, ())
            )

            engine_input = DecisionEngineInput(
                case_id=CaseId(value=uuid.UUID(holding.case_id)),
                evaluated_at=evaluated_at,
                decisions=tuple(decisions_by_case.get(holding.case_id, ())),
                outcomes=tuple(outcomes_by_case.get(holding.case_id, ())),
                observations=case_observations,
                evidence=case_evidence,
                portfolio_holding=PortfolioHoldingContext(
                    ticker=holding.ticker,
                    weight_percent=holding.weight_percent,
                    value_absolute=holding.value_absolute,
                    reconciliation_status=ReconciliationState(holding.reconciliation_status.value),
                ),
                trade_log=trade_log,
            )
            outputs[holding.ticker] = run_pipeline(engine_input, generated_at=evaluated_at)

        return outputs

    # -- Derivation ---------------------------------------------------------

    def _coverage_for(
        self, ticker: str, pipeline_outputs: dict[str, DecisionEngineOutput]
    ) -> EvidenceCoverageLevel:
        output = pipeline_outputs.get(ticker)
        if output is None or output.business_evaluation.evidence_quality is None:
            return EvidenceCoverageLevel.NOT_APPLICABLE
        return output.business_evaluation.evidence_quality.coverage

    def _evidence_gap_count(
        self, ticker: str, pipeline_outputs: dict[str, DecisionEngineOutput]
    ) -> int:
        """Whether this Case has any real `EvidenceGap` at all -- the
        same list `_build_missing_evidence` surfaces verbatim. Used
        (rather than `coverage`) to trigger Gather Evidence/Missing
        Evidence, because a Case with zero recorded Observations reports
        `coverage=NOT_APPLICABLE` yet still legitimately carries a
        case-wide `NO_EVIDENCE_RECORDED` gap -- `coverage` alone would
        silently miss that real finding."""
        output = pipeline_outputs.get(ticker)
        if output is None or output.business_evaluation.evidence_quality is None:
            return 0
        return len(output.business_evaluation.evidence_quality.evidence_gaps)

    def _build_key_findings(
        self,
        status_report: PortfolioStatusReport,
        pipeline_outputs: dict[str, DecisionEngineOutput],
    ) -> tuple[KeyFinding, ...]:
        findings: list[KeyFinding] = []
        summary = status_report.summary

        if summary is not None and summary.concentration_level == "High" and summary.largest_position_ticker:
            findings.append(
                KeyFinding(
                    kind=KeyFindingKind.HIGH_CONCENTRATION,
                    count=1,
                    tickers=(summary.largest_position_ticker,),
                )
            )
        elif (
            summary is not None
            and summary.concentration_level == "Elevated"
            and summary.largest_position_ticker
        ):
            findings.append(
                KeyFinding(
                    kind=KeyFindingKind.ELEVATED_CONCENTRATION,
                    count=1,
                    tickers=(summary.largest_position_ticker,),
                )
            )

        if (
            summary is not None
            and summary.unallocated_percent is not None
            and summary.unallocated_percent > _UNALLOCATED_TOLERANCE_PERCENT
        ):
            findings.append(KeyFinding(kind=KeyFindingKind.LARGE_UNALLOCATED, count=0, tickers=()))

        missing_case_tickers = tuple(
            sorted(
                {
                    item.ticker
                    for item in status_report.attention_items
                    if item.category is AttentionCategory.MISSING_CASE
                }
            )
        )
        if missing_case_tickers:
            findings.append(
                KeyFinding(
                    kind=KeyFindingKind.MULTIPLE_MISSING_CASES,
                    count=len(missing_case_tickers),
                    tickers=missing_case_tickers,
                )
            )

        stale_case_tickers = tuple(
            sorted(
                {
                    item.ticker
                    for item in status_report.attention_items
                    if item.category is AttentionCategory.VERY_OLD_CASE
                }
            )
        )
        if stale_case_tickers:
            findings.append(
                KeyFinding(
                    kind=KeyFindingKind.MULTIPLE_STALE_CASES,
                    count=len(stale_case_tickers),
                    tickers=stale_case_tickers,
                )
            )

        evidence_gap_tickers = tuple(
            sorted(
                ticker
                for ticker in pipeline_outputs
                if self._evidence_gap_count(ticker, pipeline_outputs) > 0
            )
        )
        if evidence_gap_tickers:
            findings.append(
                KeyFinding(
                    kind=KeyFindingKind.MULTIPLE_EVIDENCE_GAPS,
                    count=len(evidence_gap_tickers),
                    tickers=evidence_gap_tickers,
                )
            )

        return tuple(findings)

    def _build_consider_items(
        self,
        state: AlphaPortfolioState,
        status_report: PortfolioStatusReport,
        pipeline_outputs: dict[str, DecisionEngineOutput],
    ) -> tuple[ConsiderItem, ...]:
        items: list[ConsiderItem] = []

        for item in status_report.attention_items:
            if item.category is AttentionCategory.MISSING_CASE:
                items.append(
                    ConsiderItem(
                        kind=ConsiderKind.OPEN_INVESTMENT_CASE,
                        ticker=item.ticker,
                        case_id=None,
                        confidence=EvidenceCoverageLevel.NOT_APPLICABLE,
                        related_holdings=(item.ticker,),
                    )
                )
            elif item.category is AttentionCategory.VERY_OLD_CASE:
                items.append(
                    ConsiderItem(
                        kind=ConsiderKind.REVIEW_THESIS,
                        ticker=item.ticker,
                        case_id=item.case_id,
                        confidence=self._coverage_for(item.ticker, pipeline_outputs),
                        related_holdings=(item.ticker,),
                        age_days=item.age_days,
                    )
                )

        pending_counts: dict[str, int] = defaultdict(int)
        pending_case_ids: dict[str, str | None] = {}
        for item in status_report.attention_items:
            if item.category in _PENDING_WORKFLOW_CATEGORIES:
                pending_counts[item.ticker] += 1
                pending_case_ids[item.ticker] = item.case_id
        for ticker, count in pending_counts.items():
            items.append(
                ConsiderItem(
                    kind=ConsiderKind.UPDATE_CASE,
                    ticker=ticker,
                    case_id=pending_case_ids[ticker],
                    confidence=self._coverage_for(ticker, pipeline_outputs),
                    related_holdings=(ticker,),
                    pending_item_count=count,
                )
            )

        for ticker, output in pipeline_outputs.items():
            gap_count = self._evidence_gap_count(ticker, pipeline_outputs)
            if gap_count > 0:
                items.append(
                    ConsiderItem(
                        kind=ConsiderKind.GATHER_EVIDENCE,
                        ticker=ticker,
                        case_id=str(output.case_id),
                        confidence=self._coverage_for(ticker, pipeline_outputs),
                        related_holdings=(ticker,),
                        evidence_gap_count=gap_count,
                    )
                )

        for holding in state.holdings:
            if holding.weight_percent >= _ELEVATED_CONCENTRATION_WEIGHT_PERCENT:
                items.append(
                    ConsiderItem(
                        kind=ConsiderKind.REVIEW_CONCENTRATION,
                        ticker=holding.ticker,
                        case_id=holding.case_id,
                        confidence=self._coverage_for(holding.ticker, pipeline_outputs),
                        related_holdings=(holding.ticker,),
                        weight_percent=holding.weight_percent,
                    )
                )

        return tuple(items)

    def _build_risk_signals(
        self,
        state: AlphaPortfolioState,
        status_report: PortfolioStatusReport,
        pipeline_outputs: dict[str, DecisionEngineOutput],
    ) -> tuple[RiskSignal, ...]:
        signals: list[RiskSignal] = []

        for item in status_report.attention_items:
            if item.category is AttentionCategory.MISSING_CASE:
                signals.append(
                    RiskSignal(kind=RiskSignalKind.MISSING_CASE, ticker=item.ticker, case_id=None)
                )
            elif item.category is AttentionCategory.VERY_OLD_CASE:
                signals.append(
                    RiskSignal(
                        kind=RiskSignalKind.STALE_REVIEW,
                        ticker=item.ticker,
                        case_id=item.case_id,
                        age_days=item.age_days,
                    )
                )
            elif item.category is AttentionCategory.AWAITING_RECONCILIATION:
                signals.append(
                    RiskSignal(
                        kind=RiskSignalKind.AWAITING_RECONCILIATION,
                        ticker=item.ticker,
                        case_id=item.case_id,
                    )
                )

        for ticker, output in pipeline_outputs.items():
            if self._evidence_gap_count(ticker, pipeline_outputs) > 0:
                signals.append(
                    RiskSignal(
                        kind=RiskSignalKind.MISSING_EVIDENCE,
                        ticker=ticker,
                        case_id=str(output.case_id),
                    )
                )

        for holding in state.holdings:
            if holding.weight_percent >= _HIGH_CONCENTRATION_WEIGHT_PERCENT:
                signals.append(
                    RiskSignal(
                        kind=RiskSignalKind.HIGH_CONCENTRATION,
                        ticker=holding.ticker,
                        case_id=holding.case_id,
                    )
                )

        return tuple(signals)

    def _build_missing_evidence(
        self, pipeline_outputs: dict[str, DecisionEngineOutput]
    ) -> tuple[MissingEvidenceItem, ...]:
        items: list[MissingEvidenceItem] = []
        for ticker, output in pipeline_outputs.items():
            evidence_quality = output.business_evaluation.evidence_quality
            if evidence_quality is None:
                continue
            for gap in evidence_quality.evidence_gaps:
                items.append(
                    MissingEvidenceItem(
                        ticker=ticker,
                        case_id=str(output.case_id),
                        gap_kind=gap.kind,
                        reference=gap.reference,
                    )
                )
        return tuple(items)
