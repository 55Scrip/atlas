"""Tests for `atlas.alpha.portfolio_cockpit.service.PortfolioCockpitService`
(ATLAS-028 Phase 22) -- built through the real, unmodified Case/Decision
/Observation/Evidence/Outcome persistence and the real
`atlas.alpha.portfolio`/`case_generation`/`investment_case`/
`portfolio_status` services, exactly mirroring
`atlas.alpha.investment_case`'s own test style: nothing mocked below the
Cockpit service itself."""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.service import AlphaPortfolioService, ImportHoldingInput, ImportPortfolioRequest
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.portfolio_cockpit.contracts import AttentionReasonKind, ReviewPriority
from atlas.alpha.portfolio_cockpit.service import PortfolioCockpitService
from atlas.alpha.portfolio_intelligence.thresholds import ELEVATED_CONCENTRATION_WEIGHT_PERCENT
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_NOW = datetime.now(timezone.utc)
_LARGE = ELEVATED_CONCENTRATION_WEIGHT_PERCENT
_SMALL = ELEVATED_CONCENTRATION_WEIGHT_PERCENT - 5.0


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
    create_business_record_table(engine)
    return engine


class _Harness:
    def __init__(self, engine, *, with_case_generation: bool = True):
        self.engine = engine
        self.case_repository = get_case_repository(engine)
        self.case_service = CaseService(self.case_repository)
        self.decision_repository = get_decision_repository(engine)
        self.observation_repository = get_observation_repository(engine)
        self.evidence_repository = get_evidence_repository(engine)
        self.outcome_repository = get_outcome_repository(engine)
        self.portfolio_store = AlphaPortfolioStore(engine)
        self.trade_log_store = AlphaTradeLogStore(engine)
        self.business_record_repository = SqlAlchemyBusinessRecordRepository(engine)
        self.case_generation_service = CaseGenerationService(self.case_service) if with_case_generation else None
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
            self.business_record_repository,
        )
        self.portfolio_status_service = PortfolioStatusService(
            portfolio_store=self.portfolio_store,
            trade_log_store=self.trade_log_store,
            decision_repository=self.decision_repository,
            outcome_repository=self.outcome_repository,
            observation_repository=self.observation_repository,
        )
        self.cockpit_service = PortfolioCockpitService(
            portfolio_store=self.portfolio_store,
            investment_case_composition_service=self.composition_service,
            portfolio_status_service=self.portfolio_status_service,
        )

    def import_holdings_with_weights(self, weights: dict[str, float]) -> None:
        self.portfolio_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=tuple(
                    ImportHoldingInput(ticker=ticker, weight_percent=weight)
                    for ticker, weight in weights.items()
                )
            )
        )

    def dangle_case_id(self, ticker: str) -> None:
        """Overwrites one holding's `case_id` with a well-formed UUID
        that resolves to no real Case -- simulates the "case_id set but
        Case genuinely failed to resolve" branch, distinct from
        `case_id is None`."""
        state = self.portfolio_store.get()
        new_holdings = tuple(
            dataclasses.replace(h, case_id=str(uuid.uuid4())) if h.ticker == ticker else h
            for h in state.holdings
        )
        self.portfolio_store.replace(dataclasses.replace(state, holdings=new_holdings))

    def count_calls(self, repository_name: str) -> "_CallCounter":
        repository = getattr(self, repository_name)
        return _CallCounter(repository)


class _CallCounter:
    """Wraps a repository's `list_all` to count invocations, without
    changing its return value -- mirrors
    `tests.unit.alpha.investment_case.test_service`'s own helper."""

    def __init__(self, repository) -> None:
        self._repository = repository
        self._original = repository.list_all
        self.call_count = 0
        repository.list_all = self._counted

    def _counted(self):
        self.call_count += 1
        return self._original()


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


@pytest.fixture
def harness_no_case_generation() -> _Harness:
    return _Harness(_new_engine(), with_case_generation=False)


class TestEmptyPortfolio:
    def test_no_portfolio_established_returns_exists_false(self, harness):
        report = harness.cockpit_service.build_report()
        assert report.exists is False
        assert report.holdings == ()
        assert report.unresolved_holdings == ()
        assert report.summary is None
        assert report.conviction_distribution == ()
        assert report.valuation_distribution == ()
        assert report.priority_review_count == 0

    def test_does_not_crash_and_generated_at_is_still_set(self, harness):
        report = harness.cockpit_service.build_report()
        assert report.generated_at is not None


class TestSingleHoldingNoEvidence:
    """No Observation/Decision/Evidence exists yet -- every analytical
    axis is honestly INSUFFICIENT_EVIDENCE / INSUFFICIENT_INPUT, never a
    fabricated value, and this must not crash anything downstream."""

    def test_holding_composes_with_honest_insufficient_values(self, harness):
        harness.import_holdings_with_weights({"AMD": _LARGE})
        report = harness.cockpit_service.build_report()
        assert report.exists is True
        assert len(report.holdings) == 1
        holding = report.holdings[0]
        assert holding.ticker == "AMD"
        assert holding.conviction.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert holding.valuation.status is ValuationStatus.INSUFFICIENT_INPUT
        assert holding.confidence.value in ("not_applicable", "none")

    def test_only_insufficient_evidence_reason_fires(self, harness):
        harness.import_holdings_with_weights({"AMD": _LARGE})
        report = harness.cockpit_service.build_report()
        holding = report.holdings[0]
        assert holding.attention.reasons == (AttentionReasonKind.INSUFFICIENT_EVIDENCE,)

    def test_large_holding_with_only_evidence_signal_is_evidence_review(self, harness):
        harness.import_holdings_with_weights({"AMD": _LARGE})
        report = harness.cockpit_service.build_report()
        assert report.holdings[0].attention.priority is ReviewPriority.EVIDENCE_REVIEW
        assert report.priority_review_count == 0

    def test_small_holding_with_only_evidence_signal_is_standard_review(self, harness):
        harness.import_holdings_with_weights({"AMD": _SMALL})
        report = harness.cockpit_service.build_report()
        assert report.holdings[0].attention.priority is ReviewPriority.STANDARD_REVIEW


class TestMultipleHoldings:
    def test_large_and_small_holdings_get_different_review_priorities(self, harness):
        harness.import_holdings_with_weights({"NVDA": 30.0, "AMD": 20.0})
        report = harness.cockpit_service.build_report()
        by_ticker = {h.ticker: h for h in report.holdings}
        assert by_ticker["NVDA"].attention.priority is ReviewPriority.EVIDENCE_REVIEW
        assert by_ticker["AMD"].attention.priority is ReviewPriority.STANDARD_REVIEW
        assert report.unresolved_holdings == ()

    def test_summary_is_the_real_portfolio_status_summary_reused_by_reference(self, harness):
        harness.import_holdings_with_weights({"NVDA": 30.0, "AMD": 20.0})
        report = harness.cockpit_service.build_report()
        status_report = harness.portfolio_status_service.build_report()
        assert report.summary == status_report.summary
        assert report.summary.holdings_count == 2

    def test_distributions_name_every_enum_member_including_zero_counts(self, harness):
        harness.import_holdings_with_weights({"NVDA": 30.0, "AMD": 20.0})
        report = harness.cockpit_service.build_report()
        assert {c.level for c in report.conviction_distribution} == set(ConvictionLevel)
        assert {c.status for c in report.valuation_distribution} == set(ValuationStatus)
        insufficient = next(
            c for c in report.conviction_distribution if c.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        )
        assert insufficient.count == 2
        very_high = next(c for c in report.conviction_distribution if c.level is ConvictionLevel.VERY_HIGH)
        assert very_high.count == 0

    def test_holdings_cover_every_import_and_no_duplicates(self, harness):
        harness.import_holdings_with_weights({"NVDA": 20.0, "AMD": 20.0, "META": 20.0})
        report = harness.cockpit_service.build_report()
        tickers = [h.ticker for h in report.holdings]
        assert sorted(tickers) == ["AMD", "META", "NVDA"]
        assert len(tickers) == len(set(tickers))


class TestLargePortfolio:
    """Phase 36's own explicit scenario: a realistic-sized portfolio
    (>=25 holdings), composed and projected without error, with correct
    coverage and no duplication -- the same shape as the real Atlas Alpha
    dev database this sprint was also manually verified against."""

    _TICKERS = tuple(f"T{i:02d}" for i in range(30))

    def test_thirty_holdings_compose_without_error_and_are_all_covered(self, harness):
        weight = round(100.0 / len(self._TICKERS), 4)
        harness.import_holdings_with_weights({ticker: weight for ticker in self._TICKERS})
        report = harness.cockpit_service.build_report()
        assert report.exists is True
        assert report.unresolved_holdings == ()
        tickers = [h.ticker for h in report.holdings]
        assert sorted(tickers) == sorted(self._TICKERS)
        assert len(tickers) == len(set(tickers))
        assert report.summary.holdings_count == 30

    def test_thirty_holdings_repository_scans_stay_batched_not_per_case(self, harness):
        """`InvestmentCaseCompositionService.build_many`'s own batching
        invariant (proven per-repository already in
        `tests.unit.alpha.investment_case.test_service`) holds at this
        scale too: the scan count never grows with the number of Cases.
        `PortfolioStatusService.build_report()` -- reused, not
        recomputed, by `PortfolioCockpitService` -- legitimately makes
        its own single additional scan of the same shared repository, so
        the ceiling here is a small constant, never anywhere close to 30."""
        weight = round(100.0 / len(self._TICKERS), 4)
        harness.import_holdings_with_weights({ticker: weight for ticker in self._TICKERS})
        decision_counter = harness.count_calls("decision_repository")
        harness.cockpit_service.build_report()
        assert decision_counter.call_count <= 2


class TestUnresolvedHoldingNoCaseId:
    def test_holding_with_no_case_id_lands_in_unresolved_not_holdings(self, harness_no_case_generation):
        harness_no_case_generation.import_holdings_with_weights({"AMD": _LARGE})
        report = harness_no_case_generation.cockpit_service.build_report()
        assert report.exists is True
        assert report.holdings == ()
        assert len(report.unresolved_holdings) == 1
        assert report.unresolved_holdings[0].ticker == "AMD"
        assert report.unresolved_holdings[0].case_id is None

    def test_never_fabricates_analytical_values_for_an_unresolved_holding(self, harness_no_case_generation):
        harness_no_case_generation.import_holdings_with_weights({"AMD": _LARGE})
        report = harness_no_case_generation.cockpit_service.build_report()
        assert not hasattr(report.unresolved_holdings[0], "conviction")
        assert not hasattr(report.unresolved_holdings[0], "attention")


class TestUnresolvedHoldingDanglingCaseId:
    """A holding may carry a `case_id` that does not resolve to a real
    Case -- distinct from `case_id is None`, and equally honest: still
    named in `unresolved_holdings`, never silently dropped."""

    def test_dangling_case_id_still_lands_in_unresolved(self, harness):
        harness.import_holdings_with_weights({"AMD": _LARGE, "NVDA": _SMALL})
        harness.dangle_case_id("AMD")
        report = harness.cockpit_service.build_report()
        assert {h.ticker for h in report.unresolved_holdings} == {"AMD"}
        assert report.unresolved_holdings[0].case_id is not None
        assert {h.ticker for h in report.holdings} == {"NVDA"}

    def test_other_holdings_compose_normally_despite_one_dangling_case(self, harness):
        harness.import_holdings_with_weights({"AMD": _LARGE, "NVDA": _SMALL})
        harness.dangle_case_id("AMD")
        report = harness.cockpit_service.build_report()
        assert len(report.holdings) == 1
        assert report.holdings[0].ticker == "NVDA"


class TestPriorityReviewCount:
    def test_counts_only_priority_review_never_evidence_or_standard(self, harness):
        harness.import_holdings_with_weights({"AMD": _LARGE, "NVDA": _SMALL})
        report = harness.cockpit_service.build_report()
        assert all(h.attention.priority is not ReviewPriority.PRIORITY_REVIEW for h in report.holdings)
        assert report.priority_review_count == 0


class TestDeterminism:
    def test_two_builds_of_the_same_state_agree_on_every_analytical_field(self, harness):
        harness.import_holdings_with_weights({"AMD": _LARGE, "NVDA": _SMALL})
        first = harness.cockpit_service.build_report()
        second = harness.cockpit_service.build_report()
        first_by_ticker = {h.ticker: h for h in first.holdings}
        second_by_ticker = {h.ticker: h for h in second.holdings}
        for ticker in first_by_ticker:
            assert first_by_ticker[ticker].conviction.level == second_by_ticker[ticker].conviction.level
            assert first_by_ticker[ticker].valuation.status == second_by_ticker[ticker].valuation.status
            assert first_by_ticker[ticker].attention == second_by_ticker[ticker].attention


class TestNoIndependentRecomputation:
    """Phase 22: this service must never independently recompute
    Business/Valuation/Risk/Conviction, or the Portfolio-wide summary --
    verified structurally, not just asserted in prose."""

    def test_service_module_never_imports_an_individual_evaluator_directly(self):
        import atlas.alpha.portfolio_cockpit.service as service_module

        with open(service_module.__file__, encoding="utf-8") as handle:
            text = handle.read()
        for forbidden in (
            "atlas.analysis_engine.growth",
            "atlas.analysis_engine.capital_allocation",
            "atlas.analysis_engine.valuation.cash_flow",
            "atlas.analysis_engine.risk.business_risk",
            "atlas.analysis_engine.risk.financial_risk",
            "atlas.analysis_engine.conviction.calculate_conviction",
        ):
            assert forbidden not in text, f"found forbidden direct import: {forbidden!r}"
        assert "build_many" in text
        assert "PortfolioStatusService" in text
