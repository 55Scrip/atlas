"""Orchestration for the Evidence Quality Engine -- the only part of
this package that performs I/O. Composes `atlas.alpha.investment_case
.InvestmentCaseCompositionService` (unmodified) and independently
fetches the *raw*, pre-conflict-drop `BusinessRecord`s from the same
`SqlAlchemyBusinessRecordRepository` the composition service itself
uses -- the one piece of data `InvestmentCaseComposition` does not
expose (only its post-drop `business_facts`/`market_facts` survive
onto that object). Mirrors `atlas.alpha.stance.service.StanceService`'s
own shape and its documented "each Alpha service independently
composes for its own purpose" cost tradeoff, one extra repository call
deep.
"""
from __future__ import annotations

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.case_membership import known_cases, resolve_case_id_for_ticker
from atlas.alpha.evidence_quality.engine import assess_evidence_quality
from atlas.alpha.evidence_quality.models import EvidenceQualityReport
from atlas.alpha.investment_case.models import InvestmentCaseComposition
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.business_data.versioning import latest_versions

__all__ = ["EvidenceQualityService"]


def _ticker_for_composition(composition: InvestmentCaseComposition) -> str | None:
    if composition.holding_context is not None:
        return composition.holding_context.ticker
    if composition.company_profile is not None:
        return composition.company_profile.ticker
    return None


class EvidenceQualityService:
    def __init__(
        self,
        composition_service: InvestmentCaseCompositionService,
        business_record_repository: SqlAlchemyBusinessRecordRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
    ) -> None:
        self._composition_service = composition_service
        self._business_record_repository = business_record_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store

    def _assess(self, case_id: str) -> EvidenceQualityReport | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            return None
        ticker = _ticker_for_composition(composition)
        records = latest_versions(self._business_record_repository.get_by_company(ticker)) if ticker is not None else ()
        return assess_evidence_quality(
            records,
            composition.business_facts,
            composition.market_facts,
            composition.canonical_analysis,
            evaluated_at=composition.generated_at,
        )

    def assess_for_case(self, case_id: str) -> EvidenceQualityReport | None:
        return self._assess(case_id)

    def assess_for_ticker(self, ticker: str) -> EvidenceQualityReport | None:
        case_id = resolve_case_id_for_ticker(ticker, self._portfolio_store, self._watchlist_store)
        if case_id is None:
            return None
        return self._assess(case_id)

    def assess_all_holdings(self) -> tuple[tuple[str, EvidenceQualityReport], ...]:
        """Deliverable 6 -- Portfolio's own "which holdings depend on
        weak/stale/conflicting evidence" surface."""
        portfolio_state = self._portfolio_store.get()
        if portfolio_state is None:
            return ()
        results = []
        for holding in portfolio_state.holdings:
            if holding.case_id is None:
                continue
            report = self._assess(holding.case_id)
            if report is not None:
                results.append((holding.ticker, report))
        return tuple(results)

    def assess_for_candidates(self) -> tuple[tuple[str, EvidenceQualityReport], ...]:
        """Deliverable 7 -- Discovery's own evidence-aware candidate
        cards. Same "Watchlist Cases not already held" scope
        `StanceService.assess_for_candidates` already established."""
        portfolio_state = self._portfolio_store.get()
        held_tickers = {h.ticker for h in portfolio_state.holdings} if portfolio_state is not None else set()
        results = []
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            if ticker is not None and ticker in held_tickers:
                continue
            report = self._assess(case_id)
            if report is not None and ticker is not None:
                results.append((ticker, report))
        return tuple(results)
