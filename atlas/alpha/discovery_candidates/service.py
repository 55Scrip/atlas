"""Builds the Discovery candidate universe from persisted state.

Provider-free by construction: the four collaborators are the binding
repository, the two membership stores and the composition service, and
none of them can reach a provider, a quota tracker or a refresh
coordinator. Nothing here creates a Case -- rendering Discovery must
not mutate anything. Cases are adopted deliberately, by an operator,
through `atlas.dev.adopt_analysed_securities`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.decision_support import describe_recommendation
from atlas.alpha.discovery_candidates.models import CandidateExclusionReason, DiscoveryCandidate
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel

__all__ = ["DiscoveryCandidateService", "DiscoveryCandidateUniverse"]


@dataclass(frozen=True)
class DiscoveryCandidateUniverse:
    candidates: tuple[DiscoveryCandidate, ...] = ()
    excluded: tuple[tuple[str, CandidateExclusionReason], ...] = ()
    """`(ticker, reason)` for every bound Case that did not qualify --
    the universe is auditable, not a black box."""


class DiscoveryCandidateService:
    def __init__(
        self,
        binding_repository: CaseInstrumentBindingRepository,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
        composition_service: InvestmentCaseCompositionService,
        portfolio_fit_service: PortfolioFitService,
        stance_service: StanceService,
    ) -> None:
        self._bindings = binding_repository
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        self._composition_service = composition_service
        self._portfolio_fit_service = portfolio_fit_service
        self._stance_service = stance_service

    def build(self) -> DiscoveryCandidateUniverse:
        """Eligibility, stated once and kept separate from ranking.

        A bound Case qualifies when the investor is not already
        following it -- not held, not actively watched -- and Atlas has
        actually looked at the company. That last condition is
        `analysis_coverage`, not a recommendation: an
        `insufficient_evidence` company Atlas has genuinely studied is a
        legitimate thing to investigate, while one it has never seen is
        not an idea, it is a blank.

        A *previously removed* Watchlist entry is eligible again. Removal
        ended the monitoring relationship; Atlas independently finding
        the company attractive later is exactly what Discovery is for.
        Atlas has no "dismissed" concept today -- if one is ever added,
        it belongs here, and this comment is the reason to look.

        Ordering of eligible candidates is left entirely to the caller;
        this method decides *what may be considered*, never *in what
        order*.
        """
        state = self._portfolio_store.get()
        held = {holding.ticker for holding in state.holdings} if state is not None else set()
        watched = {entry.ticker for entry in self._watchlist_store.list_all()}

        candidates: list[DiscoveryCandidate] = []
        excluded: list[tuple[str, CandidateExclusionReason]] = []

        for binding in self._bindings.list_all():
            ticker = binding.instrument_key
            if ticker in held:
                excluded.append((ticker, CandidateExclusionReason.HELD_IN_PORTFOLIO))
                continue
            if ticker in watched:
                excluded.append((ticker, CandidateExclusionReason.ON_WATCHLIST))
                continue

            composition = self._composition_service.build(binding.case_id)
            if composition is None:
                excluded.append((ticker, CandidateExclusionReason.NO_COMPOSITION))
                continue

            analysis = composition.canonical_analysis
            if analysis.analysis_coverage.level is AnalysisCoverageLevel.NO_COVERAGE:
                excluded.append((ticker, CandidateExclusionReason.NO_ANALYSIS))
                continue

            fit = self._portfolio_fit_service.assess_for_case(binding.case_id)
            stance = self._stance_service.assess_for_case(binding.case_id)
            candidates.append(
                DiscoveryCandidate(
                    ticker=ticker,
                    case_id=binding.case_id,
                    company_name=composition.company_profile.name if composition.company_profile else None,
                    decision_support_level=describe_recommendation(analysis.recommendation).level.value,
                    analysis_coverage_level=analysis.analysis_coverage.level.value,
                    # `None`, never a neutral-looking substitute: an
                    # unavailable Fit or Stance is a real state.
                    fit_rating=fit.overall.value if fit is not None else None,
                    stance_level=stance.level.value if stance is not None else None,
                )
            )

        candidates.sort(key=lambda candidate: candidate.ticker)
        return DiscoveryCandidateUniverse(candidates=tuple(candidates), excluded=tuple(excluded))
