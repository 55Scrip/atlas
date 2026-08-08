"""`InvestmentCaseCompositionService` (ATLAS-027, Phase 9/10). See this
package's own `__init__.py` for the full ownership rationale.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.investment_case.models import CurrentThesis, InvestmentCaseComposition
from atlas.alpha.portfolio_intelligence.pipeline_bridge import build_decision_engine_input
from atlas.alpha.portfolio_status.service import VERY_OLD_CASE_THRESHOLD_DAYS
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.decision_engine.pipeline import run_pipeline

__all__ = ["InvestmentCaseCompositionService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _current_thesis(
    decisions: tuple[Decision, ...], observations: tuple[Observation, ...]
) -> CurrentThesis:
    latest_decision = max(decisions, key=lambda d: d.decided_at, default=None)
    latest_observation = max(observations, key=lambda o: o.observed_at, default=None)
    return CurrentThesis(
        latest_decision_reason=latest_decision.investment_case.reason if latest_decision else None,
        latest_decision_type=latest_decision.decision_type.value if latest_decision else None,
        latest_observation_statement=str(latest_observation.statement) if latest_observation else None,
    )


def _is_thesis_stale(
    decisions: tuple[Decision, ...], observations: tuple[Observation, ...], evaluated_at: datetime
) -> bool:
    """Reuses `PortfolioStatusService`'s own `VERY_OLD_CASE_THRESHOLD_DAYS`
    and earliest-activity-timestamp rule verbatim -- the only existing,
    real staleness threshold in this codebase -- rather than inventing a
    second one for Conviction's own `is_thesis_stale` input. `decided_at`/
    `observed_at`, not `recorded_at`: both are client-settable, so this
    reflects when the thinking actually happened."""
    activity_timestamps = [d.decided_at for d in decisions] + [o.observed_at for o in observations]
    if not activity_timestamps:
        return False
    earliest = min(activity_timestamps)
    return (evaluated_at - earliest).days >= VERY_OLD_CASE_THRESHOLD_DAYS


class InvestmentCaseCompositionService:
    def __init__(
        self,
        case_repository: CaseRepository,
        decision_repository: DecisionRepository,
        observation_repository: ObservationRepository,
        evidence_repository: EvidenceRepository,
        outcome_repository: OutcomeRepository,
        portfolio_store: AlphaPortfolioStore,
        trade_log_store: AlphaTradeLogStore,
    ) -> None:
        self._case_repository = case_repository
        self._decision_repository = decision_repository
        self._observation_repository = observation_repository
        self._evidence_repository = evidence_repository
        self._outcome_repository = outcome_repository
        self._portfolio_store = portfolio_store
        self._trade_log_store = trade_log_store

    def build(self, case_id_str: str) -> InvestmentCaseComposition | None:
        """Returns `None` only when `case_id_str` does not resolve to a
        real Case -- an honest, explicit absence (Phase 22), never a
        best-effort guess. Every other gap (no holding, no Observations,
        no BusinessRecords) still produces a real, complete
        `InvestmentCaseComposition` with an honest, mostly
        `INSUFFICIENT_INPUT` `canonical_analysis` (Phase 10/11) -- a
        Case never needs a Decision, Observation, or Outcome recorded
        against it before this method can run.
        """
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
        # Untyped (not `tuple[Outcome, ...]`): see
        # `pipeline_bridge.build_decision_engine_input`'s own note --
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
        engine_input = build_decision_engine_input(
            case_id_str,
            holding=holding,
            decisions=case_decisions,
            observations=case_observations,
            evidence=case_evidence,
            outcomes=case_outcomes,
            trade_log_entries=trades_for_ticker,
            evaluated_at=evaluated_at,
        )
        decision_output = run_pipeline(engine_input, generated_at=evaluated_at)

        canonical_analysis = assemble_analysis(
            engine_input,
            decision_output,
            is_thesis_stale=_is_thesis_stale(case_decisions, case_observations, evaluated_at),
            business_records=(),
            generated_at=evaluated_at,
        )

        return InvestmentCaseComposition(
            case_id=case_id_str,
            holding_context=holding,
            canonical_analysis=canonical_analysis,
            current_thesis=_current_thesis(case_decisions, case_observations),
            decision_history=case_decisions,
            observation_history=case_observations,
            outcome_history=case_outcomes,
            trade_log=trades_for_ticker,
            generated_at=evaluated_at,
        )
