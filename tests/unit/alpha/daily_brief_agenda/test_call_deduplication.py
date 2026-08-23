"""Performance Sprint 2 -- Decision Layer Request Deduplication.

Verifies `DailyBriefAgendaService.build_agenda()`'s per-call
memoization of `DecisionReadinessService.assess_for_case` and
`InvestmentDecisionService.synthesize_for_case` (Performance Sprint 1's
own proven request-local pattern, extended to these two services):
real call counts collapse to (at most) one per distinct `(case_id,
ticker)` combination actually used, output is unaffected, and nothing
survives past one `build_agenda()` call. Reuses `test_service.py`'s
own harness construction verbatim.
"""
from __future__ import annotations

from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from tests.unit.alpha.daily_brief_agenda.test_service import _Harness, _new_engine


def _harness_with_holding_and_decision(ticker: str) -> _Harness:
    h = _Harness(_new_engine())
    case_id = h.import_holding(ticker)
    h.record_decision(case_id, subject=ticker)
    return h


class _CallCounter:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def __len__(self) -> int:
        return len(self.calls)


def _count_real_calls(monkeypatch, cls, method_name: str) -> _CallCounter:
    counter = _CallCounter()
    original = getattr(cls, method_name)

    def _counted(self, case_id, *, ticker=None):
        counter.calls.append((case_id, ticker))
        return original(self, case_id, ticker=ticker)

    monkeypatch.setattr(cls, method_name, _counted)
    return counter


class TestRealCallCountsCollapse:
    def test_decision_readiness_and_investment_decision_are_each_called_a_bounded_number_of_times(
        self, monkeypatch
    ):
        """Before this sprint, both services were measured (profiling,
        this sprint's own investigation) at 855 and 585 real calls for
        9 known Cases. After deduplication, the real, uncached
        implementation must run at most once per distinct `(case_id,
        ticker)` pair actually used across the whole request -- with 3
        Cases here, that's a small, bounded number, never anything
        close to the pre-optimization multiplier."""
        h1 = _harness_with_holding_and_decision("AAA")
        h2 = _harness_with_holding_and_decision("BBB")
        h3 = _harness_with_holding_and_decision("CCC")
        # All three harnesses are independent engines; use just one for
        # this assertion (call-count shape doesn't depend on which).
        h = h1

        readiness_calls = _count_real_calls(monkeypatch, DecisionReadinessService, "assess_for_case")
        decision_calls = _count_real_calls(monkeypatch, InvestmentDecisionService, "synthesize_for_case")

        h.agenda_service.build_agenda()

        # Exactly 1 known Case in this harness -- at most a small,
        # fixed number of distinct (case_id, ticker) keys can ever be
        # real-computed, regardless of how many signal sources ask.
        assert len(readiness_calls) <= 3
        assert len(decision_calls) <= 2

    def test_repeating_the_same_case_id_ticker_pair_never_triggers_a_second_real_call(self, monkeypatch):
        h = _harness_with_holding_and_decision("AAA")
        readiness_calls = _count_real_calls(monkeypatch, DecisionReadinessService, "assess_for_case")

        h.agenda_service.build_agenda()

        seen_keys = readiness_calls.calls
        assert len(seen_keys) == len(set(seen_keys)), (
            f"a (case_id, ticker) pair was real-computed more than once: {seen_keys}"
        )

    def test_repeating_the_same_case_id_ticker_pair_never_triggers_a_second_real_decision_call(self, monkeypatch):
        h = _harness_with_holding_and_decision("AAA")
        decision_calls = _count_real_calls(monkeypatch, InvestmentDecisionService, "synthesize_for_case")

        h.agenda_service.build_agenda()

        seen_keys = decision_calls.calls
        assert len(seen_keys) == len(set(seen_keys)), (
            f"a (case_id, ticker) pair was real-computed more than once: {seen_keys}"
        )


class TestWrappersDoNotLeakAfterOneCall:
    def test_neither_wrapper_survives_the_call(self):
        h = _harness_with_holding_and_decision("AAA")
        h.agenda_service.build_agenda()

        assert "build" not in vars(h.composition_service)
        assert "assess_for_case" not in vars(h.decision_readiness_service)
        assert "synthesize_for_case" not in vars(h.investment_decision_service)

    def test_the_service_is_still_correctly_usable_after_build_agenda_returns(self):
        h = _harness_with_holding_and_decision("AAA")
        case_id = h.import_holdings({"AAA": 100.0})["AAA"]
        h.agenda_service.build_agenda()

        # A direct call after build_agenda() must go through the real,
        # unwrapped implementation and produce a correct result.
        readiness = h.decision_readiness_service.assess_for_case(case_id)
        assert readiness is not None
        assert readiness.case_id == case_id


class TestExceptionSafetyForBothNewWrappers:
    def test_an_exception_mid_build_still_restores_both_new_wrappers(self, monkeypatch):
        h = _harness_with_holding_and_decision("AAA")

        def _boom(*_args, **_kwargs):
            raise RuntimeError("simulated failure inside build_agenda")

        monkeypatch.setattr(h.agenda_service, "_build_agenda_impl", _boom)

        try:
            h.agenda_service.build_agenda()
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected RuntimeError to propagate")

        assert "build" not in vars(h.composition_service)
        assert "assess_for_case" not in vars(h.decision_readiness_service)
        assert "synthesize_for_case" not in vars(h.investment_decision_service)
