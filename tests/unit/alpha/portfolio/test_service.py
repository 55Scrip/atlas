"""Tests for `atlas.alpha.portfolio.service.AlphaPortfolioService`.

Includes the Alpha Sprint 1A Foundation Patch regressions: holding-to-
Investment-Case reuse (Defect 1), cash-consistency rejection (Defect 2),
and duplicate-ticker rejection (Defect 3); and Alpha Sprint 1B: external
trade application (Mode A/B) and portfolio reconciliation.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio.exceptions import (
    AlphaHoldingNotFoundError,
    AlphaPortfolioNotEstablishedError,
    AlphaPortfolioValidationError,
    DecisionMismatchError,
    OutcomeNotFoundForTradeError,
    TradeAlreadyAppliedError,
)
from atlas.alpha.portfolio.models import EntryMode, ReconciliationStatus, TransactionType
from atlas.alpha.portfolio.service import (
    AlphaPortfolioService,
    ApplyTradeRequest,
    FromScratchRequest,
    ImportHoldingInput,
    ImportPortfolioRequest,
    ReplaceAllocationRequest,
    UpdateHoldingWeightRequest,
)
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import OutcomeId, Statement

_NOW = datetime.now(timezone.utc)


def _make_outcome(decision_id: DecisionId | None = None) -> Outcome:
    return Outcome.capture(
        case_id=CaseId(),
        decision_id=decision_id or DecisionId(),
        statement=Statement("Bought shares."),
        occurred_at=_NOW,
    )


class _FakeOutcomeRepository:
    """A minimal, in-memory stand-in for the real SQLAlchemy-backed
    OutcomeRepository -- fine for these tests, since `service.py` only
    ever depends on the `OutcomeRepository` Protocol, never a concrete
    class."""

    def __init__(self, outcomes: list[Outcome] | None = None) -> None:
        self._outcomes = {outcome.id: outcome for outcome in (outcomes or [])}
        self.add_was_called = False

    def add(self, outcome: Outcome) -> None:
        self.add_was_called = True
        self._outcomes[outcome.id] = outcome

    def get(self, outcome_id: OutcomeId) -> Outcome | None:
        return self._outcomes.get(outcome_id)

    def list_all(self) -> list[Outcome]:
        return list(self._outcomes.values())

    def list_by_decision_id(self, decision_id: DecisionId) -> list[Outcome]:
        return [o for o in self._outcomes.values() if o.decision_id == decision_id]


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_alpha_portfolio_state_table(engine)
    create_alpha_trade_log_table(engine)
    return engine


@pytest.fixture
def service() -> AlphaPortfolioService:
    return AlphaPortfolioService(AlphaPortfolioStore(_new_engine()))


@pytest.fixture
def trade_service_factory():
    """Returns a factory building a fully-wired AlphaPortfolioService
    (store + trade log store, both on one shared in-memory engine) with
    the given fake OutcomeRepository."""

    def _factory(outcome_repository):
        engine = _new_engine()
        return AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            AlphaTradeLogStore(engine),
            outcome_repository,
        )

    return _factory


class TestImportPortfolio:
    def test_establishes_state_with_imported_entry_mode(self, service):
        state = service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),),
                cash_weight_percent=None,
            )
        )
        assert state.entry_mode == EntryMode.IMPORTED
        assert service.get_state() is not None

    def test_rejects_an_empty_holdings_list(self, service):
        with pytest.raises(AlphaPortfolioValidationError):
            service.import_portfolio(ImportPortfolioRequest(holdings=(), cash_weight_percent=None))

    def test_percentages_alone_are_sufficient_no_absolute_value_required(self, service):
        # Alpha Sprint 1 First-Time Experience requirement.
        state = service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),),
                cash_weight_percent=None,
            )
        )
        assert state.holdings[0].value_absolute is None

    def test_preferences_are_optional(self, service):
        state = service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),),
                cash_weight_percent=None,
                preferences_notes=None,
            )
        )
        assert state.preferences.notes is None


class TestFromScratch:
    def test_establishes_empty_state_with_objective_and_horizon(self, service):
        state = service.start_from_scratch(FromScratchRequest(objective="Grow", horizon="Long"))
        assert state.entry_mode == EntryMode.FROM_SCRATCH
        assert state.holdings == ()
        assert state.objective == "Grow"
        assert state.horizon == "Long"

    def test_requires_objective(self, service):
        with pytest.raises(AlphaPortfolioValidationError):
            service.start_from_scratch(FromScratchRequest(objective="", horizon="Long"))

    def test_requires_horizon(self, service):
        with pytest.raises(AlphaPortfolioValidationError):
            service.start_from_scratch(FromScratchRequest(objective="Grow", horizon=""))

    def test_preferences_are_optional(self, service):
        state = service.start_from_scratch(
            FromScratchRequest(objective="Grow", horizon="Long", preferences_notes=None)
        )
        assert state.preferences.notes is None


class TestCashConsistencyValidation:
    def test_rejects_cash_value_without_cash_weight(self, service):
        with pytest.raises(AlphaPortfolioValidationError):
            service.import_portfolio(
                ImportPortfolioRequest(
                    holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),),
                    cash_weight_percent=None,
                    cash_value_absolute=1000,
                )
            )

    def test_rejects_cash_weight_without_cash_value(self, service):
        with pytest.raises(AlphaPortfolioValidationError):
            service.import_portfolio(
                ImportPortfolioRequest(
                    holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),),
                    cash_weight_percent=40,
                    cash_value_absolute=None,
                )
            )

    def test_accepts_both_cash_fields_together(self, service):
        state = service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),),
                cash_weight_percent=40,
                cash_value_absolute=400,
            )
        )
        assert state.cash_weight_percent == 40
        assert state.cash_value_absolute == 400

    def test_rejected_import_does_not_overwrite_previously_established_cash(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),),
                cash_weight_percent=40,
                cash_value_absolute=400,
            )
        )
        with pytest.raises(AlphaPortfolioValidationError):
            service.import_portfolio(
                ImportPortfolioRequest(
                    holdings=(ImportHoldingInput(ticker="AMD", weight_percent=50),),
                    cash_value_absolute=999,
                )
            )
        assert service.get_state().cash_weight_percent == 40
        assert service.get_state().cash_value_absolute == 400


class TestDuplicateTickerValidation:
    def test_rejects_the_same_ticker_twice(self, service):
        with pytest.raises(AlphaPortfolioValidationError):
            service.import_portfolio(
                ImportPortfolioRequest(
                    holdings=(
                        ImportHoldingInput(ticker="NVDA", weight_percent=50),
                        ImportHoldingInput(ticker="NVDA", weight_percent=50),
                    ),
                )
            )

    def test_rejects_a_ticker_differing_only_by_case_and_whitespace(self, service):
        with pytest.raises(AlphaPortfolioValidationError):
            service.import_portfolio(
                ImportPortfolioRequest(
                    holdings=(
                        ImportHoldingInput(ticker="NVDA", weight_percent=50),
                        ImportHoldingInput(ticker="nvda ", weight_percent=50),
                    ),
                )
            )

    def test_accepts_distinct_tickers(self, service):
        state = service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(
                    ImportHoldingInput(ticker="NVDA", weight_percent=50),
                    ImportHoldingInput(ticker="AMD", weight_percent=50),
                ),
            )
        )
        assert len(state.holdings) == 2


class TestAllocationBoundsValidation:
    def test_rejects_total_allocation_above_100(self, service):
        with pytest.raises(AlphaPortfolioValidationError):
            service.import_portfolio(
                ImportPortfolioRequest(
                    holdings=(
                        ImportHoldingInput(ticker="NVDA", weight_percent=70),
                        ImportHoldingInput(ticker="AMD", weight_percent=40),
                    ),
                )
            )

    def test_accepts_total_allocation_below_100_without_fabricating_the_remainder(self, service):
        state = service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),),
            )
        )
        assert state.holdings[0].weight_percent == 60
        assert state.cash_weight_percent is None


class TestLinkCaseToHolding:
    """Alpha Sprint 1A Foundation Patch, Defect 1."""

    def test_raises_when_no_portfolio_established(self, service):
        with pytest.raises(AlphaPortfolioNotEstablishedError):
            service.link_case_to_holding("NVDA", "case-1")

    def test_raises_for_an_unknown_ticker(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        with pytest.raises(AlphaHoldingNotFoundError):
            service.link_case_to_holding("AMD", "case-1")

    def test_first_call_creates_one_case(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        case_id = service.link_case_to_holding("NVDA", "case-1")
        assert case_id == "case-1"
        assert service.get_state().holdings[0].case_id == "case-1"

    def test_repeated_clicks_reuse_the_same_case(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        first = service.link_case_to_holding("NVDA", "case-1")
        second = service.link_case_to_holding("NVDA", "case-2")
        third = service.link_case_to_holding("NVDA", "case-3")

        assert first == second == third == "case-1"

    def test_lookup_is_normalization_insensitive(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        service.link_case_to_holding("NVDA", "case-1")
        assert service.link_case_to_holding("nvda ", "case-2") == "case-1"


class TestGetView:
    def test_returns_none_when_no_state_established(self, service):
        assert service.get_view() is None

    def test_returns_a_derived_summary_after_import(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),),
                cash_weight_percent=None,
            )
        )
        view = service.get_view()
        assert view is not None
        assert view.number_of_holdings == 1


class TestApplyConfirmedTradeValidation:
    """Alpha Sprint 1B: the three required verification steps."""

    def test_raises_when_no_portfolio_established(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        with pytest.raises(AlphaPortfolioNotEstablishedError):
            trade_service.apply_confirmed_trade(
                ApplyTradeRequest(
                    outcome_id=str(outcome.id.value),
                    decision_id=str(outcome.decision_id.value),
                    security="NVDA",
                    transaction_type=TransactionType.BUY,
                    quantity=1,
                    execution_price=100,
                    executed_at=_NOW,
                )
            )

    def test_raises_when_outcome_does_not_exist(self, trade_service_factory):
        trade_service = trade_service_factory(_FakeOutcomeRepository([]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        with pytest.raises(OutcomeNotFoundForTradeError):
            trade_service.apply_confirmed_trade(
                ApplyTradeRequest(
                    outcome_id=str(OutcomeId().value),
                    decision_id=str(DecisionId().value),
                    security="NVDA",
                    transaction_type=TransactionType.BUY,
                    quantity=1,
                    execution_price=100,
                    executed_at=_NOW,
                )
            )

    def test_raises_when_outcome_belongs_to_a_different_decision(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        with pytest.raises(DecisionMismatchError):
            trade_service.apply_confirmed_trade(
                ApplyTradeRequest(
                    outcome_id=str(outcome.id.value),
                    decision_id=str(DecisionId().value),  # a different Decision
                    security="NVDA",
                    transaction_type=TransactionType.BUY,
                    quantity=1,
                    execution_price=100,
                    executed_at=_NOW,
                )
            )

    def test_raises_on_a_second_apply_for_the_same_outcome(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        request = ApplyTradeRequest(
            outcome_id=str(outcome.id.value),
            decision_id=str(outcome.decision_id.value),
            security="NVDA",
            transaction_type=TransactionType.BUY,
            quantity=1,
            execution_price=100,
            executed_at=_NOW,
        )
        trade_service.apply_confirmed_trade(request)
        with pytest.raises(TradeAlreadyAppliedError):
            trade_service.apply_confirmed_trade(request)

    def test_raises_for_a_sell_of_an_unknown_security(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        with pytest.raises(AlphaPortfolioValidationError):
            trade_service.apply_confirmed_trade(
                ApplyTradeRequest(
                    outcome_id=str(outcome.id.value),
                    decision_id=str(outcome.decision_id.value),
                    security="AMD",
                    transaction_type=TransactionType.SELL,
                    quantity=1,
                    execution_price=100,
                    executed_at=_NOW,
                )
            )

    def test_raises_for_a_buy_that_costs_more_than_available_cash(self, trade_service_factory):
        # Independent verification regression: absolute mode previously
        # floored the deficit at zero and let the holding absorb the
        # full trade cost anyway, fabricating portfolio value.
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=67, value_absolute=200),),
                cash_weight_percent=33,
                cash_value_absolute=100,
            )
        )
        with pytest.raises(AlphaPortfolioValidationError):
            trade_service.apply_confirmed_trade(
                ApplyTradeRequest(
                    outcome_id=str(outcome.id.value),
                    decision_id=str(outcome.decision_id.value),
                    security="NVDA",
                    transaction_type=TransactionType.BUY,
                    quantity=10,
                    execution_price=100,  # costs 1000, only 100 cash available
                    executed_at=_NOW,
                )
            )
        # The rejected trade must not have been logged.
        assert trade_service.list_trade_log() == []

    def test_accepts_a_buy_that_exactly_matches_available_cash(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=50, value_absolute=500),),
                cash_weight_percent=50,
                cash_value_absolute=500,
            )
        )
        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=5,
                execution_price=100,  # costs exactly 500
                executed_at=_NOW,
            )
        )
        assert state.cash_value_absolute == 0
        assert state.holdings[0].value_absolute == 1000

    def test_raises_for_a_sell_that_exceeds_the_holdings_current_value(self, trade_service_factory):
        # Independent verification regression: absolute mode previously
        # floored the holding at zero and credited cash with the full
        # proceeds anyway, fabricating portfolio value.
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=33, value_absolute=50),),
                cash_weight_percent=67,
                cash_value_absolute=100,
            )
        )
        with pytest.raises(AlphaPortfolioValidationError):
            trade_service.apply_confirmed_trade(
                ApplyTradeRequest(
                    outcome_id=str(outcome.id.value),
                    decision_id=str(outcome.decision_id.value),
                    security="NVDA",
                    transaction_type=TransactionType.SELL,
                    quantity=10,
                    execution_price=100,  # proceeds 1000, holding only worth 50
                    executed_at=_NOW,
                )
            )
        assert trade_service.list_trade_log() == []

    def test_accepts_a_sell_that_exactly_matches_the_holdings_current_value(
        self, trade_service_factory
    ):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=50, value_absolute=500),),
                cash_weight_percent=50,
                cash_value_absolute=500,
            )
        )
        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.SELL,
                quantity=5,
                execution_price=100,  # proceeds exactly 500
                executed_at=_NOW,
            )
        )
        assert state.holdings[0].value_absolute == 0
        assert state.cash_value_absolute == 1000

    def test_percentage_only_mode_has_no_cash_sufficiency_check(self, trade_service_factory):
        # No real dollar figures exist to validate against in Mode B, so
        # a BUY that would be "unaffordable" in absolute terms is simply
        # recorded as awaiting reconciliation, not rejected.
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),))
        )
        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1000,
                execution_price=1000,
                executed_at=_NOW,
            )
        )
        assert state.holdings[0].reconciliation_status == ReconciliationStatus.AWAITING_RECONCILIATION

    def test_never_calls_add_on_the_outcome_repository(self, trade_service_factory):
        outcome = _make_outcome()
        fake_outcome_repository = _FakeOutcomeRepository([outcome])
        trade_service = trade_service_factory(fake_outcome_repository)
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        assert fake_outcome_repository.add_was_called is False


class TestApplyConfirmedTradeAbsoluteMode:
    """Alpha Sprint 1B, Mode A: real portfolio value known."""

    def _service_with_portfolio(self, trade_service_factory, outcome):
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60, value_absolute=600),),
                cash_weight_percent=40,
                cash_value_absolute=400,
            )
        )
        return trade_service

    def test_buy_increases_holding_value_and_decreases_cash(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = self._service_with_portfolio(trade_service_factory, outcome)

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
                fees=1,
            )
        )
        holding = state.holdings[0]
        assert holding.value_absolute == 700  # 600 + 1*100
        assert state.cash_value_absolute == 299  # 400 - 100 - 1 fee
        assert holding.reconciliation_status == ReconciliationStatus.UPDATED

    def test_sell_decreases_holding_value_and_increases_cash(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = self._service_with_portfolio(trade_service_factory, outcome)

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.SELL,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        holding = state.holdings[0]
        assert holding.value_absolute == 500  # 600 - 1*100
        assert state.cash_value_absolute == 500  # 400 + 100

    def test_weights_are_recomputed_via_the_shared_calculation_engine(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = self._service_with_portfolio(trade_service_factory, outcome)

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=4,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        # NVDA: 600 + 400 = 1000; cash: 400 - 400 = 0; total 1000.
        holding = state.holdings[0]
        assert round(holding.weight_percent, 2) == 100.0
        assert round(state.cash_weight_percent, 2) == 0.0

    def test_buy_of_a_new_security_adds_a_holding(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = self._service_with_portfolio(trade_service_factory, outcome)

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.BUY,
                quantity=2,
                execution_price=50,
                executed_at=_NOW,
            )
        )
        tickers = {h.ticker for h in state.holdings}
        assert tickers == {"NVDA", "AMD"}
        amd = next(h for h in state.holdings if h.ticker == "AMD")
        assert amd.value_absolute == 100
        assert amd.reconciliation_status == ReconciliationStatus.UPDATED


class TestApplyConfirmedTradePercentageMode:
    """Alpha Sprint 1B, Mode B: percentages only -- Atlas does not invent."""

    def _service_with_portfolio(self, trade_service_factory, outcome):
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        # Mode B is driven by the *holding* lacking an absolute value --
        # cash may still be given consistently (both fields together)
        # without turning this into Mode A, since has_absolute_values
        # requires every holding to carry a value too.
        trade_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),),
                cash_weight_percent=40,
                cash_value_absolute=400,
            )
        )
        return trade_service

    def test_buy_does_not_change_the_weight_percent(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = self._service_with_portfolio(trade_service_factory, outcome)

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        holding = state.holdings[0]
        assert holding.weight_percent == 60
        assert state.cash_weight_percent == 40

    def test_holding_is_marked_awaiting_reconciliation(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = self._service_with_portfolio(trade_service_factory, outcome)

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        assert state.holdings[0].reconciliation_status == ReconciliationStatus.AWAITING_RECONCILIATION

    def test_buy_of_a_new_security_adds_a_pending_holding(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = self._service_with_portfolio(trade_service_factory, outcome)

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=50,
                executed_at=_NOW,
            )
        )
        amd = next(h for h in state.holdings if h.ticker == "AMD")
        assert amd.weight_percent == 0
        assert amd.reconciliation_status == ReconciliationStatus.AWAITING_RECONCILIATION


class TestReconcileUpdateHolding:
    def _awaiting_reconciliation_service(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),))
        )
        trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        return trade_service

    def test_updates_the_weight_and_clears_the_status(self, trade_service_factory):
        trade_service = self._awaiting_reconciliation_service(trade_service_factory)
        state = trade_service.reconcile_update_holding(
            UpdateHoldingWeightRequest(ticker="NVDA", weight_percent=65)
        )
        holding = state.holdings[0]
        assert holding.weight_percent == 65
        assert holding.reconciliation_status == ReconciliationStatus.NONE

    def test_raises_for_an_unknown_ticker(self, trade_service_factory):
        trade_service = self._awaiting_reconciliation_service(trade_service_factory)
        with pytest.raises(AlphaHoldingNotFoundError):
            trade_service.reconcile_update_holding(
                UpdateHoldingWeightRequest(ticker="AMD", weight_percent=10)
            )

    def test_rejects_a_weight_that_would_push_total_above_100(self, trade_service_factory):
        trade_service = self._awaiting_reconciliation_service(trade_service_factory)
        with pytest.raises(AlphaPortfolioValidationError):
            trade_service.reconcile_update_holding(
                UpdateHoldingWeightRequest(ticker="NVDA", weight_percent=200)
            )

    def test_raises_when_no_portfolio_established(self, service):
        with pytest.raises(AlphaPortfolioNotEstablishedError):
            service.reconcile_update_holding(
                UpdateHoldingWeightRequest(ticker="NVDA", weight_percent=50)
            )


class TestTradeAppliedAfterPortfolioReplacement:
    """Edge case: a trade recorded for a ticker that a subsequent
    'replace entire allocation' removed."""

    def test_buy_for_a_ticker_removed_by_replace_creates_a_fresh_holding(
        self, trade_service_factory
    ):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(
                    ImportHoldingInput(ticker="NVDA", weight_percent=50),
                    ImportHoldingInput(ticker="AMD", weight_percent=50),
                ),
            )
        )
        # Replace drops AMD entirely.
        trade_service.reconcile_replace_allocation(
            ReplaceAllocationRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=50,
                executed_at=_NOW,
            )
        )
        tickers = {h.ticker for h in state.holdings}
        assert tickers == {"NVDA", "AMD"}

    def test_sell_for_a_ticker_removed_by_replace_is_rejected(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(
                    ImportHoldingInput(ticker="NVDA", weight_percent=50),
                    ImportHoldingInput(ticker="AMD", weight_percent=50),
                ),
            )
        )
        trade_service.reconcile_replace_allocation(
            ReplaceAllocationRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )

        with pytest.raises(AlphaPortfolioValidationError):
            trade_service.apply_confirmed_trade(
                ApplyTradeRequest(
                    outcome_id=str(outcome.id.value),
                    decision_id=str(outcome.decision_id.value),
                    security="AMD",
                    transaction_type=TransactionType.SELL,
                    quantity=1,
                    execution_price=50,
                    executed_at=_NOW,
                )
            )

    def test_replace_preserves_case_link_and_trade_still_applies_to_it(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        trade_service.link_case_to_holding("NVDA", "case-1")
        trade_service.reconcile_replace_allocation(
            ReplaceAllocationRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=80),))
        )

        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=50,
                executed_at=_NOW,
            )
        )
        assert state.holdings[0].case_id == "case-1"


class TestReconcileReplaceAllocation:
    def test_replaces_holdings_and_cash(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),))
        )
        state = service.reconcile_replace_allocation(
            ReplaceAllocationRequest(
                holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=50),),
                cash_weight_percent=50,
                cash_value_absolute=500,
            )
        )
        assert state.holdings[0].weight_percent == 50
        assert state.cash_weight_percent == 50

    def test_preserves_an_existing_case_id_for_a_still_present_ticker(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        service.link_case_to_holding("NVDA", "case-1")

        state = service.reconcile_replace_allocation(
            ReplaceAllocationRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=80),))
        )
        assert state.holdings[0].case_id == "case-1"

    def test_clears_reconciliation_status(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=60),))
        )
        trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        state = trade_service.reconcile_replace_allocation(
            ReplaceAllocationRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=70),))
        )
        assert state.holdings[0].reconciliation_status == ReconciliationStatus.NONE

    def test_rejects_an_empty_holdings_list(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        with pytest.raises(AlphaPortfolioValidationError):
            service.reconcile_replace_allocation(ReplaceAllocationRequest(holdings=()))

    def test_rejects_duplicate_tickers(self, service):
        service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        with pytest.raises(AlphaPortfolioValidationError):
            service.reconcile_replace_allocation(
                ReplaceAllocationRequest(
                    holdings=(
                        ImportHoldingInput(ticker="NVDA", weight_percent=50),
                        ImportHoldingInput(ticker="nvda", weight_percent=50),
                    )
                )
            )

    def test_raises_when_no_portfolio_established(self, service):
        with pytest.raises(AlphaPortfolioNotEstablishedError):
            service.reconcile_replace_allocation(
                ReplaceAllocationRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
            )


class TestListTradeLog:
    def test_empty_when_no_trades_recorded(self, trade_service_factory):
        trade_service = trade_service_factory(_FakeOutcomeRepository([]))
        assert trade_service.list_trade_log() == []

    def test_empty_when_service_has_no_trade_log_store_configured(self, service):
        assert service.list_trade_log() == []

    def test_includes_an_applied_trade(self, trade_service_factory):
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="NVDA", weight_percent=100),))
        )
        trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        log = trade_service.list_trade_log()
        assert len(log) == 1
        assert log[0].security == "NVDA"


class TestServiceOriginatesNoCoreObject:
    def test_service_module_does_not_import_outcomes_write_path(self):
        # Alpha Sprint 1B: the service is now authorized to *read*
        # Outcome (OutcomeRepository.get, OutcomeId) for
        # apply_confirmed_trade, but must never import Outcome's own
        # write path -- its entity constructor or its application-layer
        # capture service. See also
        # tests/test_architecture_boundaries.py::test_alpha_does_not_write_to_outcome
        # for the same rule enforced across the whole atlas/alpha tree.
        import atlas.alpha.portfolio.service as service_module

        source = service_module.__file__
        with open(source, encoding="utf-8") as handle:
            text = handle.read()
        assert "atlas.core.application.outcome" not in text
        assert "atlas.core.domain.outcome.entity" not in text


class TestAutomaticCaseGeneration:
    """ATLAS-027 Phase 4/5/20: `case_generation_service`, when wired,
    ensures every recognized holding has a real, auto-created
    Investment Case at the exact points a full holdings list is
    persisted (import, reconcile-replace, a confirmed trade) --
    idempotent, one Case per holding, never a second one on repeated
    generation."""

    @staticmethod
    def _case_generation_service(engine):
        from atlas.alpha.case_generation.service import CaseGenerationService
        from atlas.core.application.case.create_case import CaseService
        from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
            SqlAlchemyCaseRepository,
        )
        from atlas.core.infrastructure.persistence.case.table import create_case_table

        create_case_table(engine)
        return CaseGenerationService(CaseService(SqlAlchemyCaseRepository(engine)))

    @pytest.fixture
    def service_with_case_generation(self):
        engine = _new_engine()
        return AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            AlphaTradeLogStore(engine),
            None,
            self._case_generation_service(engine),
        )

    def test_import_gives_every_holding_a_real_case_id(self, service_with_case_generation):
        state = service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(
                holdings=(
                    ImportHoldingInput(ticker="AMD", weight_percent=30),
                    ImportHoldingInput(ticker="NVDA", weight_percent=20),
                )
            )
        )
        assert all(h.case_id is not None for h in state.holdings)

    def test_each_holding_gets_a_distinct_case(self, service_with_case_generation):
        state = service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(
                holdings=(
                    ImportHoldingInput(ticker="AMD", weight_percent=30),
                    ImportHoldingInput(ticker="NVDA", weight_percent=20),
                )
            )
        )
        case_ids = {h.case_id for h in state.holdings}
        assert len(case_ids) == 2

    def test_re_import_of_the_same_holding_does_not_create_a_new_case(self, service_with_case_generation):
        first = service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
        )
        first_case_id = first.holdings[0].case_id

        second = service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=45),))
        )
        assert second.holdings[0].case_id == first_case_id

    def test_repeated_import_of_an_unchanged_portfolio_is_fully_idempotent(self, service_with_case_generation):
        request = ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
        first = service_with_case_generation.import_portfolio(request)
        second = service_with_case_generation.import_portfolio(request)
        third = service_with_case_generation.import_portfolio(request)
        assert first.holdings[0].case_id == second.holdings[0].case_id == third.holdings[0].case_id

    def test_new_holding_added_via_reimport_gets_its_own_new_case(self, service_with_case_generation):
        first = service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
        )
        amd_case_id = first.holdings[0].case_id

        second = service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(
                holdings=(
                    ImportHoldingInput(ticker="AMD", weight_percent=30),
                    ImportHoldingInput(ticker="NVDA", weight_percent=20),
                )
            )
        )
        amd = next(h for h in second.holdings if h.ticker == "AMD")
        nvda = next(h for h in second.holdings if h.ticker == "NVDA")
        assert amd.case_id == amd_case_id
        assert nvda.case_id is not None
        assert nvda.case_id != amd_case_id

    def test_holding_removed_via_reimport_does_not_touch_its_case(self, service_with_case_generation):
        """A removed holding's Case is never deleted -- Alpha only ever
        held a reference on the holding row, and that row is simply
        gone; the Case itself (and everything recorded against it) is
        untouched, entirely in Core (Phase 7)."""
        first = service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(
                holdings=(
                    ImportHoldingInput(ticker="AMD", weight_percent=30),
                    ImportHoldingInput(ticker="NVDA", weight_percent=20),
                )
            )
        )
        nvda_case_id = next(h for h in first.holdings if h.ticker == "NVDA").case_id

        second = service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
        )
        assert {h.ticker for h in second.holdings} == {"AMD"}
        # NVDA's Case still exists in Core, unaffected by leaving the
        # active portfolio -- proven directly against the same
        # CaseService this service used to create it.
        from atlas.core.domain.case.value_objects import CaseId
        import uuid

        case_service = self._case_generation_service(service_with_case_generation._store._engine)._case_service
        assert case_service.get(CaseId(value=uuid.UUID(nvda_case_id))) is not None

    def test_reconcile_replace_allocation_ensures_a_case_for_a_new_holding(self, service_with_case_generation):
        service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
        )
        replaced = service_with_case_generation.reconcile_replace_allocation(
            ReplaceAllocationRequest(
                holdings=(
                    ImportHoldingInput(ticker="AMD", weight_percent=30),
                    ImportHoldingInput(ticker="META", weight_percent=20),
                )
            )
        )
        meta = next(h for h in replaced.holdings if h.ticker == "META")
        assert meta.case_id is not None

    def test_new_holding_from_a_confirmed_trade_gets_a_case(self, service_with_case_generation):
        service_with_case_generation.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="AMD", weight_percent=40, value_absolute=400),),
                cash_weight_percent=60,
                cash_value_absolute=600,
            )
        )
        outcome_repository = _FakeOutcomeRepository([_make_outcome()])
        outcome_id = next(iter(outcome_repository._outcomes))
        engine = service_with_case_generation._store._engine
        service = AlphaPortfolioService(
            service_with_case_generation._store,
            service_with_case_generation._trade_log_store,
            outcome_repository,
            service_with_case_generation._case_generation_service,
        )
        outcome = outcome_repository._outcomes[outcome_id]
        state = service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        nvda = next(h for h in state.holdings if h.ticker == "NVDA")
        assert nvda.case_id is not None

    def test_no_case_generation_service_leaves_case_id_none_exactly_as_before(self, service):
        """Backward compatibility: a caller that constructs
        `AlphaPortfolioService` without `case_generation_service` (the
        `service` fixture, used by every pre-ATLAS-027 test in this
        file) sees import behave exactly as it always did."""
        state = service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
        )
        assert state.holdings[0].case_id is None

    def test_case_creation_failure_propagates_rather_than_silently_leaving_no_case(self):
        """Phase 22: an unresolved/failed Case generation must surface
        as a real error, never a silently case-less holding pretending
        nothing went wrong."""
        from atlas.alpha.case_generation.service import CaseGenerationService

        class _FailingCaseService:
            def create(self):
                raise RuntimeError("simulated Case creation failure")

        engine = _new_engine()
        service = AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            AlphaTradeLogStore(engine),
            None,
            CaseGenerationService(_FailingCaseService()),
        )
        with pytest.raises(RuntimeError, match="simulated Case creation failure"):
            service.import_portfolio(
                ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
            )



class TestCrossContextCaseReuseAndAutomaticEnrichment:
    """(Investment Case Engine v1 slice) Portfolio's own half of
    "Watchlist and Portfolio are membership contexts around the same
    company knowledge": a ticker already linked to a Case via Watchlist
    is reused, never duplicated, when added to Portfolio; and a
    genuinely new position triggers automatic enrichment exactly once."""

    @staticmethod
    def _case_generation_service(engine):
        from atlas.alpha.case_generation.service import CaseGenerationService
        from atlas.core.application.case.create_case import CaseService
        from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
            SqlAlchemyCaseRepository,
        )
        from atlas.core.infrastructure.persistence.case.table import create_case_table

        create_case_table(engine)
        return CaseGenerationService(CaseService(SqlAlchemyCaseRepository(engine)))

    def test_a_ticker_already_in_watchlist_reuses_that_case_on_import(self):
        from atlas.alpha.watchlist.models import AlphaWatchlistEntry
        from atlas.alpha.watchlist.store import AlphaWatchlistStore
        from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table

        engine = _new_engine()
        create_alpha_watchlist_entry_table(engine)
        watchlist_store = AlphaWatchlistStore(engine)
        watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="watchlist-case-id", added_at=_NOW))

        service = AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            AlphaTradeLogStore(engine),
            None,
            self._case_generation_service(engine),
            watchlist_store=watchlist_store,
        )
        state = service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
        )
        assert state.holdings[0].case_id == "watchlist-case-id"

    def test_without_a_watchlist_store_wired_a_brand_new_case_is_still_created(self):
        engine = _new_engine()
        service = AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            AlphaTradeLogStore(engine),
            None,
            self._case_generation_service(engine),
        )
        state = service.import_portfolio(
            ImportPortfolioRequest(holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30),))
        )
        assert state.holdings[0].case_id is not None

    @staticmethod
    def _fake_provider():
        from dataclasses import dataclass, field
        from atlas.analysis_engine.business_data.models import RawBusinessDocument

        @dataclass(frozen=True)
        class _FakeProvider:
            call_count: list = field(default_factory=list)

            def fetch(self, *, company_identifier, evaluated_at):
                self.call_count.append(company_identifier)
                return (
                    RawBusinessDocument(
                        identifier=f"{company_identifier}:FY:2023",
                        company=company_identifier,
                        source_kind="financial_statement",
                        published_at=evaluated_at,
                        provider_id="fake",
                        raw_reference="https://example.test/doc",
                        content_hash="hash-1",
                        language="en",
                        metadata={"revenue": 100.0},
                    ),
                )

        return _FakeProvider()

    def _enrichment_wired_service(self, engine, provider):
        from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
        from atlas.alpha.business_data_refresh.table import create_business_record_table

        create_business_record_table(engine)
        repository = SqlAlchemyBusinessRecordRepository(engine)
        outcome = _make_outcome()
        service = AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            AlphaTradeLogStore(engine),
            _FakeOutcomeRepository([outcome]),
            self._case_generation_service(engine),
            business_record_repository=repository,
            business_data_providers=(provider,),
        )
        return service, repository, outcome

    def test_a_buy_opening_a_brand_new_position_triggers_enrichment(self):
        engine = _new_engine()
        provider = self._fake_provider()
        service, repository, outcome = self._enrichment_wired_service(engine, provider)
        service.start_from_scratch(FromScratchRequest(objective="Grow capital", horizon="Long-term"))

        service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        assert provider.call_count == ["AMD"]
        assert len(repository.get_by_company("AMD")) == 1

    def test_adding_to_an_already_held_position_does_not_re_trigger_enrichment(self):
        engine = _new_engine()
        provider = self._fake_provider()
        service, repository, outcome = self._enrichment_wired_service(engine, provider)
        service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30, value_absolute=300),),
                cash_weight_percent=70,
                cash_value_absolute=700,
            )
        )
        service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.ADD,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        assert provider.call_count == []

    def test_a_sell_never_triggers_enrichment(self):
        engine = _new_engine()
        provider = self._fake_provider()
        service, repository, outcome = self._enrichment_wired_service(engine, provider)
        service.import_portfolio(
            ImportPortfolioRequest(
                holdings=(ImportHoldingInput(ticker="AMD", weight_percent=30, value_absolute=300),),
                cash_weight_percent=70,
                cash_value_absolute=700,
            )
        )
        service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.SELL,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        assert provider.call_count == []

    def test_repeated_buys_of_the_same_new_ticker_only_enrich_once(self):
        """A BUY on a ticker with no existing holding always passes
        through `_ensure_cases`/enrichment -- `ensure_company_enriched`
        itself is what guarantees the second call is a no-op, proven
        here end to end."""
        engine = _new_engine()
        provider = self._fake_provider()
        service, repository, outcome = self._enrichment_wired_service(engine, provider)
        service.start_from_scratch(FromScratchRequest(objective="Grow capital", horizon="Long-term"))
        service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        assert provider.call_count == ["AMD"]
        assert len(repository.get_by_company("AMD")) == 1

    def test_without_enrichment_dependencies_wired_the_trade_still_succeeds(self, trade_service_factory):
        """Omitting `business_record_repository`/`business_data_
        providers` (the opt-in default) is a deliberate no-op -- trade
        application is fully independent of enrichment."""
        outcome = _make_outcome()
        trade_service = trade_service_factory(_FakeOutcomeRepository([outcome]))
        trade_service.start_from_scratch(FromScratchRequest(objective="Grow capital", horizon="Long-term"))
        state = trade_service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        assert state.holdings[0].ticker == "AMD"

    def test_a_provider_failure_does_not_prevent_the_trade_from_succeeding(self):
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class _FailingProvider:
            def fetch(self, *, company_identifier, evaluated_at):
                raise RuntimeError("network unavailable")

        engine = _new_engine()
        service, repository, outcome = self._enrichment_wired_service(engine, _FailingProvider())
        service.start_from_scratch(FromScratchRequest(objective="Grow capital", horizon="Long-term"))

        state = service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=str(outcome.id.value),
                decision_id=str(outcome.decision_id.value),
                security="AMD",
                transaction_type=TransactionType.BUY,
                quantity=1,
                execution_price=100,
                executed_at=_NOW,
            )
        )
        assert state.holdings[0].ticker == "AMD"
        assert state.holdings[0].case_id is not None
        assert repository.get_by_company("AMD") == ()
