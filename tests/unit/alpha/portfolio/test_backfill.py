"""Tests for `atlas.alpha.portfolio.backfill.backfill_missing_portfolio_cases`
(ATLAS-029, Phase 45) -- the one explicit, idempotent legacy Case repair
path, exercised through the real, unmocked Case/CaseGenerationService
stack, mirroring every other Alpha service test's style in this repo."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.portfolio.backfill import BackfillResult, backfill_missing_portfolio_cases
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, EntryMode
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.core.application.case.create_case import CaseService
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from datetime import datetime, timezone
import uuid

_NOW = datetime.now(timezone.utc)


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    create_alpha_portfolio_state_table(engine)
    return engine


class _Harness:
    def __init__(self, engine):
        self.engine = engine
        self.case_repository = get_case_repository(engine)
        self.case_service = CaseService(self.case_repository)
        self.case_generation_service = CaseGenerationService(self.case_service)
        self.portfolio_store = AlphaPortfolioStore(engine)

    def set_holdings(self, holdings: tuple[AlphaHolding, ...]) -> None:
        self.portfolio_store.replace(
            AlphaPortfolioState(
                established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.IMPORTED, holdings=holdings
            )
        )

    def run(self) -> BackfillResult:
        return backfill_missing_portfolio_cases(self.portfolio_store, self.case_generation_service)


@pytest.fixture
def harness() -> _Harness:
    return _Harness(_new_engine())


class _FailingCaseGenerationService:
    """Stands in for `CaseGenerationService` to simulate `CaseService
    .create()` raising for one specific ticker -- proves per-holding
    isolation without needing to actually break Core's Case creation."""

    def __init__(self, real: CaseGenerationService, fail_for_ticker: str) -> None:
        self._real = real
        self._fail_for_ticker = fail_for_ticker

    def ensure_cases(self, holdings):
        if len(holdings) == 1 and holdings[0].ticker == self._fail_for_ticker:
            raise RuntimeError(f"simulated Case creation failure for {self._fail_for_ticker}")
        return self._real.ensure_cases(holdings)


class TestNoPortfolioEstablished:
    def test_returns_a_zeroed_result_without_error(self, harness):
        result = harness.run()
        assert result == BackfillResult(holdings_scanned=0, cases_preserved=0, cases_created=0, failures=())


class TestEmptyHoldings:
    def test_returns_a_zeroed_result(self, harness):
        harness.set_holdings(())
        result = harness.run()
        assert result.holdings_scanned == 0
        assert result.cases_created == 0


class TestAllHoldingsAlreadyHaveCases:
    def test_nothing_is_created_and_case_ids_are_preserved(self, harness):
        case_a = str(harness.case_service.create().id)
        case_b = str(harness.case_service.create().id)
        harness.set_holdings(
            (
                AlphaHolding(ticker="AMD", weight_percent=50.0, case_id=case_a),
                AlphaHolding(ticker="NVDA", weight_percent=50.0, case_id=case_b),
            )
        )
        result = harness.run()
        assert result == BackfillResult(holdings_scanned=2, cases_preserved=2, cases_created=0, failures=())
        state = harness.portfolio_store.get()
        assert {h.ticker: h.case_id for h in state.holdings} == {"AMD": case_a, "NVDA": case_b}


class TestMixedResolvedAndMissing:
    def test_only_the_missing_holding_gets_a_new_case(self, harness):
        existing_case = str(harness.case_service.create().id)
        harness.set_holdings(
            (
                AlphaHolding(ticker="AMD", weight_percent=50.0, case_id=existing_case),
                AlphaHolding(ticker="NVDA", weight_percent=50.0, case_id=None),
            )
        )
        result = harness.run()
        assert result.holdings_scanned == 2
        assert result.cases_preserved == 1
        assert result.cases_created == 1
        assert result.failures == ()

        state = harness.portfolio_store.get()
        by_ticker = {h.ticker: h.case_id for h in state.holdings}
        assert by_ticker["AMD"] == existing_case
        assert by_ticker["NVDA"] is not None
        assert by_ticker["NVDA"] != existing_case

    def test_the_new_case_is_a_real_resolvable_case(self, harness):
        harness.set_holdings((AlphaHolding(ticker="NVDA", weight_percent=100.0, case_id=None),))
        harness.run()
        new_case_id = harness.portfolio_store.get().holdings[0].case_id
        assert harness.case_repository.get(CaseId(value=uuid.UUID(new_case_id))) is not None


class TestMultipleMissingHoldings:
    def test_each_gets_exactly_one_new_case_no_duplicates(self, harness):
        harness.set_holdings(
            tuple(
                AlphaHolding(ticker=t, weight_percent=100.0 / 5, case_id=None)
                for t in ("A", "B", "C", "D", "E")
            )
        )
        result = harness.run()
        assert result.cases_created == 5
        state = harness.portfolio_store.get()
        case_ids = [h.case_id for h in state.holdings]
        assert all(cid is not None for cid in case_ids)
        assert len(case_ids) == len(set(case_ids))


class TestIdempotency:
    def test_rerunning_is_a_true_no_op(self, harness):
        harness.set_holdings(
            tuple(AlphaHolding(ticker=t, weight_percent=100.0 / 3, case_id=None) for t in ("A", "B", "C"))
        )
        first = harness.run()
        state_after_first = harness.portfolio_store.get()

        second = harness.run()
        state_after_second = harness.portfolio_store.get()

        assert first.cases_created == 3
        assert second == BackfillResult(holdings_scanned=3, cases_preserved=3, cases_created=0, failures=())
        assert state_after_first.holdings == state_after_second.holdings

    def test_rerunning_after_a_partial_run_only_repairs_what_remains(self, harness):
        harness.set_holdings(
            tuple(AlphaHolding(ticker=t, weight_percent=50.0, case_id=None) for t in ("A", "B"))
        )
        failing_service = _FailingCaseGenerationService(harness.case_generation_service, fail_for_ticker="B")
        first = backfill_missing_portfolio_cases(harness.portfolio_store, failing_service)
        assert first.cases_created == 1
        assert len(first.failures) == 1
        assert first.failures[0].ticker == "B"

        state = harness.portfolio_store.get()
        by_ticker = {h.ticker: h.case_id for h in state.holdings}
        assert by_ticker["A"] is not None
        assert by_ticker["B"] is None

        second = harness.run()
        assert second.cases_created == 1
        assert second.failures == ()
        state2 = harness.portfolio_store.get()
        assert all(h.case_id is not None for h in state2.holdings)


class TestFailureIsolation:
    def test_one_holdings_failure_does_not_block_another(self, harness):
        harness.set_holdings(
            tuple(AlphaHolding(ticker=t, weight_percent=100.0 / 3, case_id=None) for t in ("A", "B", "C"))
        )
        failing_service = _FailingCaseGenerationService(harness.case_generation_service, fail_for_ticker="B")
        result = backfill_missing_portfolio_cases(harness.portfolio_store, failing_service)
        assert result.cases_created == 2
        assert len(result.failures) == 1
        assert result.failures[0].ticker == "B"

        state = harness.portfolio_store.get()
        by_ticker = {h.ticker: h.case_id for h in state.holdings}
        assert by_ticker["A"] is not None
        assert by_ticker["B"] is None
        assert by_ticker["C"] is not None

    def test_failure_never_fabricates_a_case_id(self, harness):
        harness.set_holdings((AlphaHolding(ticker="B", weight_percent=100.0, case_id=None),))
        failing_service = _FailingCaseGenerationService(harness.case_generation_service, fail_for_ticker="B")
        backfill_missing_portfolio_cases(harness.portfolio_store, failing_service)
        state = harness.portfolio_store.get()
        assert state.holdings[0].case_id is None


class TestNoUnrelatedMutation:
    def test_does_not_modify_decisions_observations_evidence_outcomes(self, harness):
        """Structural guarantee: the function's only dependencies are a
        portfolio store and a CaseGenerationService -- it has no access
        to Decision/Observation/Evidence/Outcome repositories at all, so
        it cannot touch them by construction."""
        import inspect

        from atlas.alpha.portfolio import backfill as backfill_module

        signature = inspect.signature(backfill_missing_portfolio_cases)
        assert set(signature.parameters) == {"portfolio_store", "case_generation_service"}

    def test_does_not_change_a_holdings_weight_or_value(self, harness):
        harness.set_holdings((AlphaHolding(ticker="NVDA", weight_percent=42.5, value_absolute=1000.0, case_id=None),))
        harness.run()
        holding = harness.portfolio_store.get().holdings[0]
        assert holding.weight_percent == pytest.approx(42.5)
        assert holding.value_absolute == pytest.approx(1000.0)


class TestReadOnlyWhenNothingToRepair:
    def test_store_is_not_written_to_when_every_holding_already_has_a_case(self, harness):
        """Proves the 'no read-time mutation, safe to rerun' guarantee
        goes further than just producing the same result -- a no-op run
        performs no write at all."""
        case_id = str(harness.case_service.create().id)
        harness.set_holdings((AlphaHolding(ticker="NVDA", weight_percent=100.0, case_id=case_id),))

        original_replace = harness.portfolio_store.replace
        calls = []
        harness.portfolio_store.replace = lambda state: (calls.append(state), original_replace(state))[1]

        harness.run()
        assert calls == []
