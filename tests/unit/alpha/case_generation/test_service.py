"""Direct unit tests for `atlas.alpha.case_generation.service
.CaseGenerationService.ensure_cases` (ATLAS-027 Phase 4/5/20) --
isolated from `AlphaPortfolioService`'s own integration (covered
separately in `tests/unit/alpha/portfolio/test_service.py
::TestAutomaticCaseGeneration`)."""
from __future__ import annotations

from dataclasses import replace

import pytest

from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.portfolio.models import AlphaHolding


class _FakeCase:
    def __init__(self, case_id: str) -> None:
        self.id = _FakeCaseId(case_id)


class _FakeCaseId:
    def __init__(self, value: str) -> None:
        self._value = value

    def __str__(self) -> str:
        return self._value


class _FakeCaseService:
    """A minimal stand-in for `CaseService` -- `ensure_cases` only ever
    calls `.create()`, so that is the only method faked here."""

    def __init__(self) -> None:
        self.create_call_count = 0

    def create(self) -> _FakeCase:
        self.create_call_count += 1
        return _FakeCase(f"generated-case-{self.create_call_count}")


class _FailingCaseService:
    def create(self):
        raise RuntimeError("simulated Case creation failure")


def _holding(ticker: str, case_id: str | None = None) -> AlphaHolding:
    return AlphaHolding(ticker=ticker, weight_percent=10.0, case_id=case_id)


class TestEnsureCasesForCaseLessHoldings:
    def test_a_holding_without_a_case_gets_one(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_cases((_holding("AMD"),))
        assert result[0].case_id is not None
        assert case_service.create_call_count == 1

    def test_multiple_case_less_holdings_each_get_their_own_case(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_cases((_holding("AMD"), _holding("NVDA"), _holding("META")))
        case_ids = {h.case_id for h in result}
        assert len(case_ids) == 3
        assert case_service.create_call_count == 3

    def test_ticker_and_weight_are_otherwise_unchanged(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        original = _holding("AMD")
        result = service.ensure_cases((original,))[0]
        assert result.ticker == original.ticker
        assert result.weight_percent == original.weight_percent


class TestIdempotency:
    def test_a_holding_that_already_has_a_case_is_returned_unchanged(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        already_cased = _holding("AMD", case_id="existing-case-id")
        result = service.ensure_cases((already_cased,))
        assert result[0] is already_cased
        assert result[0].case_id == "existing-case-id"
        assert case_service.create_call_count == 0

    def test_running_ensure_cases_twice_on_its_own_output_creates_nothing_new(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        first_pass = service.ensure_cases((_holding("AMD"),))
        assert case_service.create_call_count == 1
        second_pass = service.ensure_cases(first_pass)
        assert case_service.create_call_count == 1
        assert second_pass[0].case_id == first_pass[0].case_id

    def test_mixed_list_only_creates_cases_for_the_case_less_ones(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        holdings = (_holding("AMD", case_id="pre-existing"), _holding("NVDA"))
        result = service.ensure_cases(holdings)
        amd = next(h for h in result if h.ticker == "AMD")
        nvda = next(h for h in result if h.ticker == "NVDA")
        assert amd.case_id == "pre-existing"
        assert nvda.case_id is not None
        assert case_service.create_call_count == 1


class TestEmptyInput:
    def test_empty_holdings_tuple_is_a_no_op(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_cases(())
        assert result == ()
        assert case_service.create_call_count == 0


class TestOrderPreserved:
    def test_holdings_order_is_preserved(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_cases((_holding("AMD"), _holding("NVDA"), _holding("META")))
        assert [h.ticker for h in result] == ["AMD", "NVDA", "META"]


class TestFailurePropagation:
    def test_a_creation_failure_propagates_rather_than_being_swallowed(self):
        service = CaseGenerationService(_FailingCaseService())
        with pytest.raises(RuntimeError, match="simulated Case creation failure"):
            service.ensure_cases((_holding("AMD"),))

    def test_a_failure_never_produces_a_partially_cased_or_guessed_result(self):
        """No holding is ever returned with a fabricated or partial
        `case_id` when creation fails -- the exception propagates
        before any such value could be constructed."""
        service = CaseGenerationService(_FailingCaseService())
        try:
            service.ensure_cases((_holding("AMD"),))
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass


class TestDeterminismOfAlreadyLinkedHoldings:
    def test_identical_already_cased_input_produces_identical_output(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        holdings = (_holding("AMD", case_id="case-1"), _holding("NVDA", case_id="case-2"))
        first = service.ensure_cases(holdings)
        second = service.ensure_cases(holdings)
        assert first == second
        assert case_service.create_call_count == 0


class TestEnsureCaseId:
    """(Investment Case Engine v1 slice) The single-ticker primitive
    `ensure_cases` itself now delegates to, and `AlphaWatchlistService
    .add_ticker` calls directly -- covers the cross-context reuse
    `ensure_cases` alone never needed before this slice."""

    def test_an_existing_case_id_is_returned_unchanged(self):
        service = CaseGenerationService(_FakeCaseService())
        result = service.ensure_case_id(current_case_id="existing", ticker="AMD")
        assert result == "existing"

    def test_no_current_case_id_and_no_known_map_creates_a_new_one(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_case_id(current_case_id=None, ticker="AMD")
        assert result is not None
        assert case_service.create_call_count == 1

    def test_a_ticker_present_in_the_known_map_reuses_it_without_creating(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_case_id(
            current_case_id=None, ticker="AMD", known_case_ids_by_ticker={"AMD": "cross-context-case"}
        )
        assert result == "cross-context-case"
        assert case_service.create_call_count == 0

    def test_a_ticker_absent_from_the_known_map_still_creates_a_new_one(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_case_id(
            current_case_id=None, ticker="NVDA", known_case_ids_by_ticker={"AMD": "some-other-case"}
        )
        assert result is not None
        assert result != "some-other-case"
        assert case_service.create_call_count == 1

    def test_current_case_id_wins_even_if_the_known_map_disagrees(self):
        """Priority order is current -> cross-context -> new; an
        already-linked Case is never silently replaced."""
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_case_id(
            current_case_id="already-linked", ticker="AMD", known_case_ids_by_ticker={"AMD": "different-case"}
        )
        assert result == "already-linked"
        assert case_service.create_call_count == 0


class TestEnsureCasesCrossContextReuse:
    def test_a_holding_reuses_a_cross_context_case_for_its_ticker(self):
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_cases(
            (_holding("AMD"),), known_case_ids_by_ticker={"AMD": "watchlist-case-id"}
        )
        assert result[0].case_id == "watchlist-case-id"
        assert case_service.create_call_count == 0

    def test_omitting_the_known_map_preserves_prior_ensure_cases_behavior(self):
        """`known_case_ids_by_ticker=None` (the default, every call
        site before this slice) must behave identically to before this
        slice existed -- always create a new Case for a case-less
        holding."""
        case_service = _FakeCaseService()
        service = CaseGenerationService(case_service)
        result = service.ensure_cases((_holding("AMD"),))
        assert result[0].case_id is not None
        assert case_service.create_call_count == 1
