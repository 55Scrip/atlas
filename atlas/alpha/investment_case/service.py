"""`InvestmentCaseCompositionService` (ATLAS-027, Phase 9/10; batch path
ATLAS-028, Phase 3/22). See this package's own `__init__.py` for the
full ownership rationale.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.investment_case.company_profile import extract_company_profile
from atlas.alpha.investment_case.financial_history import extract_financial_history, extract_market_snapshot
from atlas.alpha.investment_case.models import CurrentThesis, InvestmentCaseComposition
from atlas.alpha.investment_case.business_quality_intelligence import extract_business_quality
from atlas.alpha.investment_case.capital_allocation_intelligence import extract_capital_allocation_history
from atlas.alpha.investment_case.earnings_call import extract_earnings_call_knowledge
from atlas.alpha.investment_case.executive_change_intelligence import extract_executive_change_intelligence
from atlas.alpha.investment_case.executive_track_record_intelligence import extract_executive_track_record
from atlas.alpha.investment_case.financial_quality_intelligence import extract_financial_quality
from atlas.alpha.investment_case.incentive_intelligence import extract_incentive_intelligence
from atlas.alpha.investment_case.insider_alignment_intelligence import extract_insider_alignment_knowledge
from atlas.alpha.investment_case.ownership_intelligence import extract_ownership_knowledge
from atlas.alpha.investment_case.executive_compensation_intelligence import extract_executive_compensation_knowledge
from atlas.alpha.investment_case.governance_intelligence import extract_governance_knowledge
from atlas.alpha.investment_case.risk_factor_intelligence import extract_risk_factor_knowledge
from atlas.alpha.investment_case.legal_proceedings_intelligence import extract_legal_proceedings_knowledge
from atlas.alpha.investment_case.growth_intelligence import extract_growth_knowledge
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.historical_valuation import extract_historical_valuation
from atlas.alpha.investment_case.management_credibility_intelligence import extract_management_credibility
from atlas.alpha.investment_case.management_guidance_intelligence import extract_management_guidance
from atlas.alpha.investment_case.regulatory_filings import extract_regulatory_filings
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio_intelligence.pipeline_bridge import build_decision_engine_input
from atlas.alpha.portfolio_status.service import VERY_OLD_CASE_THRESHOLD_DAYS
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.investment_case_change import ChangeIntelligence, capture_snapshot, compare_snapshots
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.core.domain.case.entity import Case
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
        business_record_repository: SqlAlchemyBusinessRecordRepository,
        watchlist_store: AlphaWatchlistStore | None = None,
        snapshot_repository: SqlAlchemyInvestmentCaseSnapshotRepository | None = None,
    ) -> None:
        self._case_repository = case_repository
        self._decision_repository = decision_repository
        self._observation_repository = observation_repository
        self._evidence_repository = evidence_repository
        self._outcome_repository = outcome_repository
        self._portfolio_store = portfolio_store
        self._trade_log_store = trade_log_store
        self._business_record_repository = business_record_repository
        # (Investment Case Engine v1 slice) Optional, `build`-only: when
        # a Case has no Portfolio holding, `build` falls back to
        # Watchlist to resolve this Case's own ticker, so a
        # Watchlist-only company still gets its persisted
        # `BusinessRecord`s (Company Profile, Financial History, Market
        # Snapshot) surfaced -- "Watchlist should be almost as
        # analytically complete as a Portfolio company." `None` (the
        # default) preserves `build`'s exact prior, Portfolio-only
        # ticker resolution. Deliberately not threaded into
        # `build_many`: its only real consumer, Portfolio Cockpit, is a
        # Portfolio-only surface with no Watchlist entries to resolve.
        self._watchlist_store = watchlist_store
        # (Investment Case Monitoring & Change Intelligence v1) Optional,
        # trailing, same backward-compatible-extension shape as
        # `watchlist_store` above: every call site built before this
        # sprint keeps constructing a valid service unchanged. `None`
        # means Change Intelligence is honestly unavailable (never a
        # silently-empty "no changes" result) -- see `_assemble`'s own
        # comment for exactly how `None` is distinguished from a real,
        # populated `ChangeIntelligence` at the composition layer.
        self._snapshot_repository = snapshot_repository

    def _assemble(
        self,
        case_id_str: str,
        *,
        holding: AlphaHolding | None,
        ticker: str | None,
        decisions: tuple[Decision, ...],
        observations: tuple[Observation, ...],
        evidence: tuple,
        outcomes: tuple,
        trades_for_ticker: tuple[AlphaTradeLogEntry, ...],
        business_records: tuple[BusinessRecord, ...],
        evaluated_at: datetime,
    ) -> InvestmentCaseComposition:
        """The one per-Case assembly implementation -- both `build` and
        `build_many` call only this. Never duplicated, never
        re-derived: this is the sole place `build_decision_engine_input`
        /`run_pipeline`/`assemble_analysis` are invoked for a Case
        (ATLAS-028 Phase 3's own explicit requirement).

        `business_records` (ATLAS-031) must already be filtered to
        `versioning.latest_versions` by the caller -- passing a
        superseded and its replacement together would make
        `extract_facts_from_records` see two different values for the
        same `(company, kind, period)` and silently drop both as
        "conflicting" (see that function's own docstring), which would
        wrongly erase a real, current fact rather than correctly
        preferring its latest version."""
        engine_input = build_decision_engine_input(
            case_id_str,
            holding=holding,
            decisions=decisions,
            observations=observations,
            evidence=evidence,
            outcomes=outcomes,
            trade_log_entries=trades_for_ticker,
            evaluated_at=evaluated_at,
        )
        decision_output = run_pipeline(engine_input, generated_at=evaluated_at)

        is_thesis_stale = _is_thesis_stale(decisions, observations, evaluated_at)
        canonical_analysis = assemble_analysis(
            engine_input,
            decision_output,
            is_thesis_stale=is_thesis_stale,
            business_records=business_records,
            generated_at=evaluated_at,
        )

        # Product Sprint 14 (Evidence & Explanation Quality): the exact
        # same pure extraction `assemble_analysis` already ran
        # internally to produce the findings above -- re-derived once
        # more here (cheap, deterministic, no side effects) so the API
        # schema layer can resolve a finding's own evidence-reference
        # ids back into the real fact they name. See
        # `InvestmentCaseComposition.business_facts`'s own docstring.
        business_facts = extract_facts_from_records(business_records, evaluated_at=evaluated_at)
        market_facts = extract_valuation_facts_from_records(business_records, evaluated_at=evaluated_at)

        # Investment Case Engine v1 slice: a direct, unevaluated read of
        # the same already-ingested `business_records` -- "what does
        # Atlas actually know," alongside `canonical_analysis`'s own
        # "what has Atlas concluded from it." `ticker` may come from a
        # Portfolio holding or (in `build`, never `build_many`) a
        # Watchlist entry; `extract_company_profile` only needs it to
        # label an otherwise-empty result, since `business_records` is
        # already scoped to this one ticker by the caller.
        company_profile = extract_company_profile(ticker, business_records) if ticker is not None else None
        financial_history = extract_financial_history(business_records)
        market_snapshot = extract_market_snapshot(business_records)
        regulatory_filings = extract_regulatory_filings(business_records)
        incentive_intelligence = extract_incentive_intelligence(regulatory_filings)
        historical_valuation = extract_historical_valuation(business_facts, market_facts)
        earnings_call = extract_earnings_call_knowledge(business_records)
        financial_statement_intelligence = extract_financial_statement_history(business_records)
        financial_quality_intelligence = extract_financial_quality(financial_statement_intelligence)
        growth_intelligence = extract_growth_knowledge(financial_statement_intelligence)
        capital_allocation_intelligence = extract_capital_allocation_history(business_records)
        business_quality_intelligence = extract_business_quality(
            financial_statement_intelligence, capital_allocation_intelligence, financial_quality_intelligence,
            growth_intelligence,
        )
        management_credibility_intelligence = extract_management_credibility(
            earnings_call, financial_statement_intelligence, growth_intelligence, capital_allocation_intelligence,
        )
        management_guidance_intelligence = extract_management_guidance(
            earnings_call, financial_statement_intelligence, growth_intelligence, capital_allocation_intelligence,
        )
        executive_change_intelligence = extract_executive_change_intelligence(ticker, earnings_call)
        executive_track_record_intelligence = extract_executive_track_record(
            executive_change_intelligence, financial_statement_intelligence, earnings_call,
            capital_allocation_intelligence, growth_intelligence, management_credibility_intelligence,
            management_guidance_intelligence,
        )
        # (Integration Sprint 1: Knowledge Activation) The entire Filing
        # Content Intelligence family (Sprints 13-20) -- Governance, Risk
        # Factor, Legal Proceedings, Ownership, Executive Compensation --
        # is wired into production composition here for the first time,
        # each called with the real, empty `()` filing-content tuple this
        # service actually has today. No production code path fetches
        # real DEF 14A/10-K/10-Q content into a `FilingContent` anywhere
        # in Atlas: `filing_content_intelligence.extract_filing_content`'s
        # own real fetcher dependencies (`atlas.business_data_providers.
        # http.fetch_text`, `sec_edgar_identity.sec_user_agent`) already
        # exist, production-ready, purpose-built for exactly this by
        # Sprint 13 -- but wiring them into this synchronous path was a
        # deliberate, documented decision NOT to make this sprint: `build_
        # many` (ATLAS-028) was engineered specifically to cost a fixed
        # number of reads regardless of Case count, and a per-Case network
        # fetch here, through the shared `_assemble` both `build` and
        # `build_many` call, would reintroduce exactly the N-times-per-
        # Case cost that sprint eliminated. See `models.py`'s own
        # `governance_intelligence` field docstring for the same reasoning
        # in full, and the Integration Sprint 1 Final Report for the
        # complete tradeoff. Every module below remains entirely
        # unmodified; only this call site is new.
        governance_intelligence = extract_governance_knowledge(())
        risk_factor_intelligence = extract_risk_factor_knowledge(())
        legal_proceedings_intelligence = extract_legal_proceedings_knowledge(())
        ownership_intelligence = extract_ownership_knowledge(())
        executive_compensation_intelligence = extract_executive_compensation_knowledge(())
        insider_alignment_intelligence = extract_insider_alignment_knowledge(
            executive_change_intelligence.executives, ownership_intelligence, executive_compensation_intelligence,
        )

        # Investment Case Monitoring & Change Intelligence v1: the
        # smallest correct integration point is exactly here -- the one
        # place a fresh `CanonicalAnalysis` already exists, for both
        # `build` and `build_many`. `capture_snapshot` is pure (no
        # persistence); `self._snapshot_repository.get_latest` reads the
        # previous structured state (if any) *before* this run's own
        # snapshot is written, so `compare_snapshots` always sees a
        # genuinely prior state, never the one just captured.
        # `.add` is itself idempotent by `content_hash` (see that
        # repository method's own docstring): calling it on every build,
        # including a user simply reloading the page with no new source
        # data, never creates a duplicate row or a fabricated change --
        # "recomputed" and "changed" stay distinct. `None` (no
        # repository wired -- every real call site wires one; only bare
        # test construction omits it) means this capability is honestly
        # unavailable, never a silently-empty "nothing changed" result.
        change_intelligence: ChangeIntelligence | None = None
        if self._snapshot_repository is not None:
            snapshot = capture_snapshot(canonical_analysis)
            previous_snapshot = self._snapshot_repository.get_latest(case_id_str)
            change_intelligence = compare_snapshots(previous_snapshot, snapshot)
            self._snapshot_repository.add(case_id_str, snapshot, change_intelligence)

        return InvestmentCaseComposition(
            case_id=case_id_str,
            holding_context=holding,
            canonical_analysis=canonical_analysis,
            current_thesis=_current_thesis(decisions, observations),
            decision_history=decisions,
            observation_history=observations,
            outcome_history=outcomes,
            trade_log=trades_for_ticker,
            is_thesis_stale=is_thesis_stale,
            company_profile=company_profile,
            financial_history=financial_history,
            market_snapshot=market_snapshot,
            change_intelligence=change_intelligence,
            generated_at=evaluated_at,
            business_facts=business_facts,
            market_facts=market_facts,
            regulatory_filings=regulatory_filings,
            historical_valuation=historical_valuation,
            earnings_call=earnings_call,
            financial_statement_intelligence=financial_statement_intelligence,
            financial_quality_intelligence=financial_quality_intelligence,
            growth_intelligence=growth_intelligence,
            capital_allocation_intelligence=capital_allocation_intelligence,
            business_quality_intelligence=business_quality_intelligence,
            management_credibility_intelligence=management_credibility_intelligence,
            management_guidance_intelligence=management_guidance_intelligence,
            executive_change_intelligence=executive_change_intelligence,
            executive_track_record_intelligence=executive_track_record_intelligence,
            incentive_intelligence=incentive_intelligence,
            governance_intelligence=governance_intelligence,
            risk_factor_intelligence=risk_factor_intelligence,
            legal_proceedings_intelligence=legal_proceedings_intelligence,
            ownership_intelligence=ownership_intelligence,
            executive_compensation_intelligence=executive_compensation_intelligence,
            insider_alignment_intelligence=insider_alignment_intelligence,
        )

    def build(self, case_id_str: str) -> InvestmentCaseComposition | None:
        """Returns `None` only when `case_id_str` does not resolve to a
        real Case -- an honest, explicit absence (Phase 22), never a
        best-effort guess. Every other gap (no holding, no Observations,
        no BusinessRecords) still produces a real, complete
        `InvestmentCaseComposition` with an honest, mostly
        `INSUFFICIENT_INPUT` `canonical_analysis` (Phase 10/11) -- a
        Case never needs a Decision, Observation, or Outcome recorded
        against it before this method can run.

        Unbatched by design: reads each repository's own `list_all()`
        exactly once, scoped to this single Case, then filters in
        Python -- the same shape this method has had since ATLAS-027.
        A caller building this for many Cases in a loop should use
        `build_many` instead (ATLAS-028) -- see that method's own
        docstring for why.
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
        all_outcomes = self._outcome_repository.list_all()
        case_outcomes = tuple(o for o in all_outcomes if str(o.case_id) == case_id_str)

        state = self._portfolio_store.get()
        holding: AlphaHolding | None = None
        if state is not None:
            holding = next((h for h in state.holdings if h.case_id == case_id_str), None)

        # Investment Case Engine v1 slice: a Case with no Portfolio
        # holding may still be a Watchlist company -- fall back to
        # Watchlist to resolve this Case's own ticker so its persisted
        # `BusinessRecord`s (Company Profile, Financial History, Market
        # Snapshot) are still surfaced. `holding_context` itself is
        # deliberately NOT set from this fallback: it specifically means
        # "held as a Portfolio position," and a Watchlist-only company
        # is honestly not one.
        ticker: str | None = holding.ticker if holding is not None else None
        if ticker is None and self._watchlist_store is not None:
            watchlist_entry = self._watchlist_store.get_by_case_id(case_id_str)
            ticker = watchlist_entry.ticker if watchlist_entry is not None else None

        all_trades = self._trade_log_store.list_all()
        trades_for_ticker: tuple[AlphaTradeLogEntry, ...] = ()
        business_records: tuple[BusinessRecord, ...] = ()
        if ticker is not None:
            trades_for_ticker = tuple(t for t in all_trades if t.security == ticker)
            business_records = latest_versions(self._business_record_repository.get_by_company(ticker))

        return self._assemble(
            case_id_str,
            holding=holding,
            ticker=ticker,
            decisions=case_decisions,
            observations=case_observations,
            evidence=case_evidence,
            outcomes=case_outcomes,
            trades_for_ticker=trades_for_ticker,
            business_records=business_records,
            evaluated_at=_utc_now(),
        )

    def build_many(self, case_ids: tuple[str, ...]) -> dict[str, InvestmentCaseComposition]:
        """Batch counterpart to `build` (ATLAS-028, Phase 3/22/23).

        Reads each of Decision/Observation/Evidence/Outcome/trade-log
        exactly **once in total**, regardless of `len(case_ids)` --
        never once per Case -- then groups by `case_id` in Python and
        assembles each Case via the exact same `_assemble` `build`
        itself uses. This is the fix for a real, measured problem: a
        naive `[build(cid) for cid in case_ids]` loop issues four full,
        unfiltered table scans *per Case* (confirmed by reading every
        `list_all()` implementation directly -- none is case-scoped at
        the SQL level), so a 25-holding portfolio would cost 100 full
        table scans through `build`'s own unbatched path. `build_many`
        costs exactly four scans total, no matter how many Cases are
        requested.

        Returns a dict keyed by the input `case_id` strings that
        actually resolved to a real Case -- a `case_id` with no
        matching Case is simply absent from the result (the same
        honest-absence contract `build` expresses via returning `None`),
        never a fabricated entry. Every Case is assembled from only its
        own records -- one Case's Decisions never leak into another's
        (`decisions_by_case`/`observations_by_case`/etc. are grouped by
        exact `case_id` string equality, the same comparison `build`
        itself already used).
        """
        if not case_ids:
            return {}

        wanted = set(case_ids)
        cases: dict[str, Case] = {}
        for case_id_str in case_ids:
            case = self._case_repository.get(CaseId(value=uuid.UUID(case_id_str)))
            if case is not None:
                cases[case_id_str] = case

        decisions_by_case: dict[str, list[Decision]] = {cid: [] for cid in cases}
        for decision in self._decision_repository.list_all():
            cid = str(decision.case_id)
            if cid in decisions_by_case:
                decisions_by_case[cid].append(decision)

        observations_by_case: dict[str, list[Observation]] = {cid: [] for cid in cases}
        observation_id_to_case: dict = {}
        for observation in self._observation_repository.list_all():
            cid = str(observation.case_id)
            if cid in observations_by_case:
                observations_by_case[cid].append(observation)
                observation_id_to_case[observation.id] = cid

        evidence_by_case: dict[str, list] = {cid: [] for cid in cases}
        for evidence_item in self._evidence_repository.list_all():
            cid = observation_id_to_case.get(evidence_item.observation_id)
            if cid is not None:
                evidence_by_case[cid].append(evidence_item)

        outcomes_by_case: dict[str, list] = {cid: [] for cid in cases}
        for outcome in self._outcome_repository.list_all():
            cid = str(outcome.case_id)
            if cid in outcomes_by_case:
                outcomes_by_case[cid].append(outcome)

        state = self._portfolio_store.get()
        holdings_by_case: dict[str, AlphaHolding] = {}
        if state is not None:
            for holding in state.holdings:
                if holding.case_id in wanted:
                    holdings_by_case[holding.case_id] = holding

        all_trades = self._trade_log_store.list_all()
        trades_by_ticker: dict[str, list[AlphaTradeLogEntry]] = {}
        for trade in all_trades:
            trades_by_ticker.setdefault(trade.security, []).append(trade)

        #: one batched read, not one per Case (ATLAS-031, Phase 19 --
        #: the exact discipline `build_many` already established for
        #: Decision/Observation/Evidence/Outcome/trade-log). Cases with
        #: no holding (research-only) are simply absent from
        #: `wanted_tickers` and get `()`, honestly, below.
        wanted_tickers = tuple({h.ticker for h in holdings_by_case.values()})
        business_records_by_ticker = self._business_record_repository.get_by_companies(wanted_tickers)

        evaluated_at = _utc_now()
        results: dict[str, InvestmentCaseComposition] = {}
        for case_id_str in cases:
            holding = holdings_by_case.get(case_id_str)
            trades_for_ticker = tuple(trades_by_ticker.get(holding.ticker, ())) if holding is not None else ()
            business_records: tuple[BusinessRecord, ...] = ()
            if holding is not None:
                business_records = latest_versions(business_records_by_ticker.get(holding.ticker, ()))
            results[case_id_str] = self._assemble(
                case_id_str,
                holding=holding,
                ticker=holding.ticker if holding is not None else None,
                decisions=tuple(decisions_by_case[case_id_str]),
                observations=tuple(observations_by_case[case_id_str]),
                evidence=tuple(evidence_by_case[case_id_str]),
                outcomes=tuple(outcomes_by_case[case_id_str]),
                trades_for_ticker=trades_for_ticker,
                business_records=business_records,
                evaluated_at=evaluated_at,
            )
        return results
