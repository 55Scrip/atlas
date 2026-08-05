"""Tests for `atlas.alpha.portfolio.service.AlphaPortfolioService`."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio.exceptions import AlphaPortfolioValidationError
from atlas.alpha.portfolio.models import EntryMode
from atlas.alpha.portfolio.service import (
    AlphaPortfolioService,
    FromScratchRequest,
    ImportHoldingInput,
    ImportPortfolioRequest,
)
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table


@pytest.fixture
def service() -> AlphaPortfolioService:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_alpha_portfolio_state_table(engine)
    return AlphaPortfolioService(AlphaPortfolioStore(engine))


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


class TestServiceOriginatesNoCoreObject:
    def test_service_module_imports_nothing_from_atlas_core_domain(self):
        # Alpha Sprint 1, Phase 4, Decision A: this module must never
        # originate a Core Domain Object.
        import atlas.alpha.portfolio.service as service_module

        source = service_module.__file__
        with open(source, encoding="utf-8") as handle:
            text = handle.read()
        assert "atlas.core.domain" not in text
