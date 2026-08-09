"""Direct unit tests for `DiscoveryContextService` (ATLAS-018; migrated
to the canonical Investment Case composition path in ATLAS-030).

Built through the real, unmocked Case/Decision/Observation/Alpha-
portfolio stack -- mirroring `tests.unit.alpha.investment_case
.test_service`'s own harness style -- since `DiscoveryContextService`
now composes `InvestmentCaseCompositionService` and
`PortfolioStatusService` directly rather than a fake report sentinel.
Whether `InvestmentCaseCompositionService.build()` itself produces the
right composition for real data is already covered by that package's
own test suite; the behavior under test here is purely the identity-
resolution branching (Phase 3) and that `DiscoveryContextService` wires
the real canonical composition through untouched.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.discovery_context.models import IdentityResolutionStatus
from atlas.alpha.discovery_context.service import DiscoveryContextService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.service import AlphaPortfolioService, ImportHoldingInput, ImportPortfolioRequest
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.portfolio_intelligence.models import PortfolioIntelligenceReport
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_SENTINEL_PORTFOLIO = PortfolioIntelligenceReport.empty()


class _FakePortfolioIntelligenceService:
    def build_report(self) -> PortfolioIntelligenceReport:
        return _SENTINEL_PORTFOLIO


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    create_alpha_portfolio_state_table(engine)
    create_alpha_trade_log_table(engine)
    return engine


class _Harness:
    def __init__(self, engine):
        self.case_repository = get_case_repository(engine)
        self.case_service = CaseService(self.case_repository)
        self.decision_repository = get_decision_repository(engine)
        self.observation_repository = get_observation_repository(engine)
        self.evidence_repository = get_evidence_repository(engine)
        self.outcome_repository = get_outcome_repository(engine)
        self.portfolio_store = AlphaPortfolioStore(engine)
        self.trade_log_store = AlphaTradeLogStore(engine)
        self.case_generation_service = CaseGenerationService(self.case_service)
        self.portfolio_service = AlphaPortfolioService(
            self.portfolio_store, self.trade_log_store, None, self.case_generation_service
        )
        self.composition_service = InvestmentCaseCompositionService(
            self.case_repository,
            self.decision_repository,
            self.observation_repository,
            self.evidence_repository,
            self.outcome_repository,
            self.portfolio_store,
            self.trade_log_store,
        )
        self.portfolio_status_service = PortfolioStatusService(
            portfolio_store=self.portfolio_store,
            trade_log_store=self.trade_log_store,
            decision_repository=self.decision_repository,
            outcome_repository=self.outcome_repository,
            observation_repository=self.observation_repository,
        )
        self.discovery_context_service = DiscoveryContextService(
            portfolio_intelligence_service=_FakePortfolioIntelligenceService(),
            investment_case_composition_service=self.composition_service,
            portfolio_status_service=self.portfolio_status_service,
        )

    def import_holding(self, ticker: str, weight_percent: float = 20.0) -> str:
        state = self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker=ticker, weight_percent=weight_percent),))
        )
        case_id = next(h for h in state.holdings if h.ticker == ticker).case_id
        assert case_id is not None
        return case_id


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class TestNoCaseIdRequested:
    def test_status_is_not_requested(self, harness):
        context = harness.discovery_context_service.build(None)
        assert context.identity.status is IdentityResolutionStatus.NOT_REQUESTED
        assert context.identity.case_id is None
        assert context.identity.ticker is None
        assert context.case is None

    def test_portfolio_is_still_the_real_report(self, harness):
        context = harness.discovery_context_service.build(None)
        assert context.portfolio is _SENTINEL_PORTFOLIO


class TestMalformedCaseId:
    def test_status_is_unresolved(self, harness):
        context = harness.discovery_context_service.build("not-a-real-uuid")
        assert context.identity.status is IdentityResolutionStatus.UNRESOLVED
        assert context.identity.case_id == "not-a-real-uuid"
        assert context.identity.ticker is None
        assert context.case is None

    def test_never_raises(self, harness):
        context = harness.discovery_context_service.build("")
        assert context.identity.status is IdentityResolutionStatus.UNRESOLVED


class TestWellFormedButNonexistentCaseId:
    def test_status_is_unresolved(self, harness):
        case_id = str(uuid.uuid4())
        context = harness.discovery_context_service.build(case_id)
        assert context.identity.status is IdentityResolutionStatus.UNRESOLVED
        assert context.identity.case_id == case_id
        assert context.identity.ticker is None
        assert context.case is None


class TestResolvedCaseId:
    def test_status_is_resolved_and_ticker_comes_from_the_real_holding(self, harness):
        case_id = harness.import_holding("AMD")
        context = harness.discovery_context_service.build(case_id)

        assert context.identity.status is IdentityResolutionStatus.RESOLVED
        assert context.identity.case_id == case_id
        assert context.identity.ticker == "AMD"
        assert context.case is not None
        assert context.case.ticker == "AMD"
        assert context.case.held is True

    def test_unheld_research_case_resolves_with_no_ticker(self, harness):
        case = harness.case_service.create()
        case_id = str(case.id.value)
        context = harness.discovery_context_service.build(case_id)

        assert context.identity.status is IdentityResolutionStatus.RESOLVED
        assert context.identity.ticker is None
        assert context.case is not None
        assert context.case.held is False
        assert context.case.ticker is None

    def test_case_is_built_from_the_real_canonical_composition_not_a_second_reconstruction(self, harness):
        case_id = harness.import_holding("AMD")
        context = harness.discovery_context_service.build(case_id)
        composition = harness.composition_service.build(case_id)

        assert context.case.confidence is composition.canonical_analysis.confidence
        assert context.case.conviction_level is composition.canonical_analysis.conviction.level
        assert context.case.is_stale == composition.is_thesis_stale
