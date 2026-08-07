"""Builds the Case Intelligence report (ATLAS-017).

Runs the canonical Decision Engine pipeline for exactly one Case (via
`atlas.alpha.portfolio_intelligence.pipeline_bridge.run_decision_engine_for_case`
-- the same shared function `atlas.alpha.portfolio_intelligence.PortfolioIntelligenceService`
uses in its own per-holding loop), then assembles the result with
already-captured Core records and `atlas.alpha.portfolio_status.PortfolioStatusService`
(ATLAS-015) into one `CaseIntelligenceReport`.

Works whether or not the Case has a linked Alpha holding: a brand-new
Case (opened before any ticker is assigned) still gets an honest report
-- `CurrentView.held=False`, `PortfolioContextSummary.held=False`,
`portfolio_holding=None` on the pipeline input (a real, valid state,
`HoldingLinkage.ABSENT`).

Deliberately bounded scope, documented rather than silently accepted:

- **Consider items require a linked holding.** `ConsiderItem.ticker`
  (`atlas.alpha.portfolio_intelligence.models`, ATLAS-016) is a required
  `str` -- widening it to `str | None` mid-sprint to support unheld
  Cases would touch already-tested ATLAS-016 code for a narrow benefit
  (the underlying facts -- Missing Evidence, Review Status -- are still
  shown directly for an unheld Case, just not wrapped in a Consider
  object). `consider_items` is `()` for an unheld Case.
- **Pending-workflow detection (`ConsiderKind.UPDATE_CASE`) is computed
  independently here**, not via a shared function with
  `PortfolioStatusService`, because that service's own detection is
  entangled with iterating the whole portfolio's holdings and
  cross-referencing whole-system id sets. The three checks themselves
  (Decision without Outcome, Outcome without a matching trade,
  Observation without a Decision) are the same three
  `AttentionCategory` concepts (`atlas.alpha.portfolio_status.models`,
  ATLAS-015) and the same `outcome.id`/`trade.outcome_id`
  /`decision.observation_id` cross-referencing technique
  `PortfolioStatusService.build_report` already uses -- not a new kind
  of check, just re-expressed as a single count here rather than
  extracted into a shared function this sprint.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry, ReconciliationStatus, TransactionType
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio_intelligence.models import ConsiderItem, ConsiderKind, PortfolioFitStatus, PortfolioFitUnavailableReason
from atlas.alpha.portfolio_intelligence.pipeline_bridge import (
    coverage_for,
    evidence_gap_count,
    run_decision_engine_for_case,
)
from atlas.alpha.portfolio_intelligence.thresholds import (
    ELEVATED_CONCENTRATION_WEIGHT_PERCENT,
    HIGH_CONCENTRATION_WEIGHT_PERCENT,
)
from atlas.alpha.portfolio_status.service import PortfolioStatusService, VERY_OLD_CASE_THRESHOLD_DAYS
from atlas.alpha.case_intelligence.models import (
    CaseIntelligenceReport,
    ConvictionStatus,
    ConvictionUnavailableReason,
    CurrentThesis,
    CurrentView,
    DecisionHistoryEntry,
    KeyRiskItem,
    KeyRiskKind,
    ObservationTimelineEntry,
    PortfolioContextFact,
    PortfolioContextSummary,
    ReviewStatus,
)
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository

_INCREASE_TRANSACTION_TYPES = frozenset({TransactionType.BUY, TransactionType.ADD})
_DECREASE_TRANSACTION_TYPES = frozenset({TransactionType.SELL, TransactionType.EXIT})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CaseIntelligenceService:
    def __init__(
        self,
        case_repository: CaseRepository,
        decision_repository: DecisionRepository,
        observation_repository: ObservationRepository,
        evidence_repository: EvidenceRepository,
        outcome_repository: OutcomeRepository,
        portfolio_store: AlphaPortfolioStore,
        trade_log_store: AlphaTradeLogStore,
        portfolio_status_service: PortfolioStatusService,
    ) -> None:
        self._case_repository = case_repository
        self._decision_repository = decision_repository
        self._observation_repository = observation_repository
        self._evidence_repository = evidence_repository
        self._outcome_repository = outcome_repository
        self._portfolio_store = portfolio_store
        self._trade_log_store = trade_log_store
        self._portfolio_status_service = portfolio_status_service

    def build_report(self, case_id_str: str) -> CaseIntelligenceReport | None:
        case = self._case_repository.get(CaseId(value=uuid.UUID(case_id_str)))
        if case is None:
            return None

        case_decisions = tuple(
            d for d in self._decision_repository.list_all() if str(d.case_id) == case_id_str
        )
        case_observations = tuple(
            o for o in self._observation_repository.list_all() if str(o.case_id) == case_id_str
        )
        case_observation_ids = {o.id for o in case_observations}
        case_evidence = tuple(
            e for e in self._evidence_repository.list_all() if e.observation_id in case_observation_ids
        )
        # Untyped list (not `tuple[Outcome, ...]`): see
        # `atlas.alpha.portfolio_intelligence.service`'s own note --
        # `atlas.alpha` may never import `atlas.core.domain.outcome.entity`.
        all_outcomes = self._outcome_repository.list_all()
        case_outcomes = tuple(o for o in all_outcomes if str(o.case_id) == case_id_str)

        state = self._portfolio_store.get()
        holding: AlphaHolding | None = None
        if state is not None:
            holding = next((h for h in state.holdings if h.case_id == case_id_str), None)

        all_trades = self._trade_log_store.list_all()
        trades_for_ticker: tuple[AlphaTradeLogEntry, ...] = ()
        if holding is not None:
            trades_for_ticker = tuple(t for t in all_trades if t.security == holding.ticker)

        evaluated_at = _utc_now()
        output = run_decision_engine_for_case(
            case_id_str,
            holding=holding,
            decisions=case_decisions,
            observations=case_observations,
            evidence=case_evidence,
            outcomes=case_outcomes,
            trade_log_entries=trades_for_ticker,
            evaluated_at=evaluated_at,
        )

        evidence_quality = output.business_evaluation.evidence_quality
        reasoning = output.reasoning.finding

        review_status = self._build_review_status(case_decisions, case_observations, evaluated_at)
        pending_workflow_count = self._pending_workflow_count(case_decisions, case_observations, case_outcomes, all_outcomes, all_trades)

        status_report = self._portfolio_status_service.build_report()

        return CaseIntelligenceReport(
            case_id=case_id_str,
            current_view=self._build_current_view(holding),
            current_thesis=self._build_current_thesis(case_decisions, case_observations),
            evidence_quality=evidence_quality,
            supporting_evidence=reasoning.supporting_evidence if reasoning else None,
            contradicting_evidence=reasoning.contradicting_evidence if reasoning else None,
            missing_evidence=evidence_quality.evidence_gaps if evidence_quality else (),
            open_questions=reasoning.open_questions if reasoning else (),
            key_risks=self._build_key_risks(reasoning, holding),
            decision_history=self._build_decision_history(case_decisions, case_outcomes),
            observation_timeline=self._build_observation_timeline(case_observations, evidence_quality),
            portfolio_context=self._build_portfolio_context(
                holding, status_report, evidence_quality, trades_for_ticker, pending_workflow_count
            ),
            portfolio_fit=PortfolioFitStatus(
                available=False, reason=PortfolioFitUnavailableReason.NOT_YET_IMPLEMENTED
            ),
            conviction=ConvictionStatus(
                available=False,
                reason=ConvictionUnavailableReason.NO_ATLAS_COMPUTED_CONVICTION_EXISTS,
            ),
            confidence=coverage_for(output),
            review_status=review_status,
            consider_items=self._build_consider_items(
                case_id_str, holding, output, review_status, pending_workflow_count
            ),
        )

    # -- Section builders -----------------------------------------------

    def _build_current_view(self, holding: AlphaHolding | None) -> CurrentView:
        if holding is None:
            return CurrentView(
                ticker=None, held=False, weight_percent=None, value_absolute=None, reconciliation_status=None
            )
        return CurrentView(
            ticker=holding.ticker,
            held=True,
            weight_percent=holding.weight_percent,
            value_absolute=holding.value_absolute,
            reconciliation_status=holding.reconciliation_status.value,
        )

    def _build_current_thesis(
        self, case_decisions: tuple[Decision, ...], case_observations: tuple[Observation, ...]
    ) -> CurrentThesis:
        latest_decision = max(case_decisions, key=lambda d: d.decided_at, default=None)
        latest_observation = max(case_observations, key=lambda o: o.observed_at, default=None)
        return CurrentThesis(
            latest_decision_reason=latest_decision.investment_case.reason if latest_decision else None,
            latest_decision_type=latest_decision.decision_type.value if latest_decision else None,
            latest_observation_statement=str(latest_observation.statement) if latest_observation else None,
        )

    def _build_key_risks(self, reasoning, holding: AlphaHolding | None) -> tuple[KeyRiskItem, ...]:
        risks: list[KeyRiskItem] = []
        if reasoning is not None:
            for classification in reasoning.contradicting_evidence.observation_classifications:
                risks.append(
                    KeyRiskItem(
                        kind=KeyRiskKind.CONTRADICTING_EVIDENCE,
                        reference=str(classification.observation_id),
                    )
                )
        if holding is not None:
            if holding.weight_percent >= HIGH_CONCENTRATION_WEIGHT_PERCENT:
                risks.append(KeyRiskItem(kind=KeyRiskKind.HIGH_CONCENTRATION))
            if holding.reconciliation_status is ReconciliationStatus.AWAITING_RECONCILIATION:
                risks.append(KeyRiskItem(kind=KeyRiskKind.AWAITING_RECONCILIATION))
        return tuple(risks)

    def _build_decision_history(
        self, case_decisions: tuple[Decision, ...], case_outcomes: tuple
    ) -> tuple[DecisionHistoryEntry, ...]:
        outcomes_by_decision: dict[str, list] = {}
        for outcome in case_outcomes:
            outcomes_by_decision.setdefault(str(outcome.decision_id), []).append(outcome)

        entries = []
        for decision in sorted(case_decisions, key=lambda d: d.decided_at):
            matched = sorted(
                outcomes_by_decision.get(str(decision.id), []), key=lambda o: o.occurred_at
            )
            outcome = matched[-1] if matched else None
            entries.append(
                DecisionHistoryEntry(
                    decision_id=str(decision.id),
                    decision_type=decision.decision_type.value,
                    reason=decision.investment_case.reason,
                    investor_confidence=decision.confidence.value,
                    decided_at=decision.decided_at,
                    outcome_id=str(outcome.id) if outcome else None,
                    outcome_statement=str(outcome.statement) if outcome else None,
                    outcome_occurred_at=outcome.occurred_at if outcome else None,
                )
            )
        return tuple(entries)

    def _build_observation_timeline(
        self, case_observations: tuple[Observation, ...], evidence_quality
    ) -> tuple[ObservationTimelineEntry, ...]:
        classification_by_id = {}
        if evidence_quality is not None:
            for classification in evidence_quality.observation_classifications:
                classification_by_id[classification.observation_id] = classification

        entries = []
        for observation in sorted(case_observations, key=lambda o: o.observed_at):
            classification = classification_by_id.get(observation.id)
            evidence_count = (
                classification.supporting_evidence_count + classification.challenging_evidence_count
                if classification is not None
                else 0
            )
            entries.append(
                ObservationTimelineEntry(
                    observation_id=str(observation.id),
                    subject=str(observation.subject),
                    statement=str(observation.statement),
                    observed_at=observation.observed_at,
                    evidence_count=evidence_count,
                    epistemic_status=classification.status.value if classification is not None else None,
                )
            )
        return tuple(entries)

    def _build_review_status(
        self,
        case_decisions: tuple[Decision, ...],
        case_observations: tuple[Observation, ...],
        evaluated_at: datetime,
    ) -> ReviewStatus:
        timestamps = [d.decided_at for d in case_decisions] + [
            o.observed_at for o in case_observations
        ]
        if not timestamps:
            return ReviewStatus(is_stale=False, age_days=None)
        age_days = (evaluated_at - min(timestamps)).days
        return ReviewStatus(is_stale=age_days >= VERY_OLD_CASE_THRESHOLD_DAYS, age_days=age_days)

    def _pending_workflow_count(
        self,
        case_decisions: tuple[Decision, ...],
        case_observations: tuple[Observation, ...],
        case_outcomes: tuple,
        all_outcomes,
        all_trades: list[AlphaTradeLogEntry],
    ) -> int:
        """Reuses `AttentionCategory`'s own three "unfinished chain"
        categories (`PENDING_WORKFLOW_CATEGORIES`) -- see module
        docstring for why this cross-referencing is computed here rather
        than via a shared function with `PortfolioStatusService`."""
        del all_outcomes  # only case_outcomes matters once scoped to this Case
        outcomes_by_decision_id: dict[str, int] = {}
        for outcome in case_outcomes:
            outcomes_by_decision_id[str(outcome.decision_id)] = (
                outcomes_by_decision_id.get(str(outcome.decision_id), 0) + 1
            )
        outcome_ids_with_trade = {trade.outcome_id for trade in all_trades}
        observation_ids_referenced = {
            str(d.observation_id) for d in case_decisions if d.observation_id is not None
        }

        count = 0
        for decision in case_decisions:
            if outcomes_by_decision_id.get(str(decision.id), 0) == 0:
                count += 1
        for outcome in case_outcomes:
            if str(outcome.id) not in outcome_ids_with_trade:
                count += 1
        for observation in case_observations:
            if str(observation.id) not in observation_ids_referenced:
                count += 1
        return count

    def _build_portfolio_context(
        self,
        holding: AlphaHolding | None,
        status_report,
        evidence_quality,
        trades_for_ticker: tuple[AlphaTradeLogEntry, ...],
        pending_workflow_count: int,
    ) -> PortfolioContextSummary:
        if holding is None:
            return PortfolioContextSummary(
                held=False,
                facts=(),
                weight_percent=None,
                concentration_level=None,
                most_recent_trade_transaction_type=None,
                most_recent_trade_at=None,
            )

        facts: list[PortfolioContextFact] = []
        summary = status_report.summary if status_report is not None else None
        if summary is not None and summary.largest_position_ticker == holding.ticker:
            facts.append(PortfolioContextFact.LARGEST_HOLDING)
        if holding.weight_percent >= HIGH_CONCENTRATION_WEIGHT_PERCENT:
            facts.append(PortfolioContextFact.HIGH_CONCENTRATION)
        if pending_workflow_count > 0:
            facts.append(PortfolioContextFact.PENDING_WORKFLOW)
        if evidence_quality is not None and evidence_quality.coverage.value not in ("full", "not_applicable"):
            facts.append(PortfolioContextFact.EVIDENCE_INCOMPLETE)

        most_recent_trade = max(trades_for_ticker, key=lambda t: t.executed_at, default=None)
        if most_recent_trade is not None:
            if most_recent_trade.transaction_type in _INCREASE_TRANSACTION_TYPES:
                facts.append(PortfolioContextFact.RECENTLY_INCREASED)
            elif most_recent_trade.transaction_type in _DECREASE_TRANSACTION_TYPES:
                facts.append(PortfolioContextFact.RECENTLY_TRIMMED)

        return PortfolioContextSummary(
            held=True,
            facts=tuple(facts),
            weight_percent=holding.weight_percent,
            concentration_level=summary.concentration_level if summary is not None else None,
            most_recent_trade_transaction_type=(
                most_recent_trade.transaction_type.value if most_recent_trade is not None else None
            ),
            most_recent_trade_at=most_recent_trade.executed_at if most_recent_trade is not None else None,
        )

    def _build_consider_items(
        self,
        case_id_str: str,
        holding: AlphaHolding | None,
        output,
        review_status: ReviewStatus,
        pending_workflow_count: int,
    ) -> tuple[ConsiderItem, ...]:
        """`ConsiderKind.OPEN_INVESTMENT_CASE` never fires here -- this
        Case already exists. See module docstring for why this is `()`
        for an unheld Case."""
        if holding is None:
            return ()

        items: list[ConsiderItem] = []
        confidence = coverage_for(output)
        gap_count = evidence_gap_count(output)

        if gap_count > 0:
            items.append(
                ConsiderItem(
                    kind=ConsiderKind.GATHER_EVIDENCE,
                    ticker=holding.ticker,
                    case_id=case_id_str,
                    confidence=confidence,
                    related_holdings=(holding.ticker,),
                    evidence_gap_count=gap_count,
                )
            )
        if review_status.is_stale:
            items.append(
                ConsiderItem(
                    kind=ConsiderKind.REVIEW_THESIS,
                    ticker=holding.ticker,
                    case_id=case_id_str,
                    confidence=confidence,
                    related_holdings=(holding.ticker,),
                    age_days=review_status.age_days,
                )
            )
        if pending_workflow_count > 0:
            items.append(
                ConsiderItem(
                    kind=ConsiderKind.UPDATE_CASE,
                    ticker=holding.ticker,
                    case_id=case_id_str,
                    confidence=confidence,
                    related_holdings=(holding.ticker,),
                    pending_item_count=pending_workflow_count,
                )
            )
        if holding.weight_percent >= ELEVATED_CONCENTRATION_WEIGHT_PERCENT:
            items.append(
                ConsiderItem(
                    kind=ConsiderKind.REVIEW_CONCENTRATION,
                    ticker=holding.ticker,
                    case_id=case_id_str,
                    confidence=confidence,
                    related_holdings=(holding.ticker,),
                    weight_percent=holding.weight_percent,
                )
            )
        return tuple(items)
