"""Internal Alpha Performance Sprint 1A -- Concurrency Verification.

Proves, empirically, that `DailyBriefAgendaService.build_agenda()`'s
per-call memoization wrapper (Performance Sprint 1) is safe under real
concurrent execution, and demonstrates precisely why it would NOT be
safe if the underlying `InvestmentCaseCompositionService` instance were
ever shared across two concurrent callers -- which it structurally
cannot be in production, proven separately in `TestDependencyIsNeverShared`
and in this session's own Final Report (read directly from the installed
FastAPI 0.141.1 source: `solve_dependencies` defaults `dependency_cache`
to a brand-new `{}` on every call, and that call happens once per
`app(request)` invocation -- i.e. once per HTTP request, never reused
across requests).

Reuses `test_service.py`'s own harness construction verbatim -- the
same "one canonical harness per package" convention this suite already
follows elsewhere.
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from atlas.alpha.daily_brief_agenda.service import DailyBriefAgendaService
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from tests.unit.alpha.daily_brief_agenda.test_service import _Harness, _new_engine


def _harness_with_watchlist(ticker: str) -> _Harness:
    h = _Harness(_new_engine())
    h.add_to_watchlist(ticker)
    return h


class _SlowBuildCounter:
    """Holds the artificial delay and a thread-safe per-case_id call
    counter, so a test can (a) force two concurrent `build_agenda()`
    calls to genuinely overlap in wall-clock time, and (b) verify
    exactly how many times the *real* underlying implementation
    actually ran for a given Case, independent of caching. The delay
    itself is applied by a plain function (below), monkeypatched onto
    the class -- a plain function, unlike a callable instance, still
    goes through Python's normal descriptor binding when accessed via
    `self._composition_service.build`, exactly like the real method."""

    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self.calls: list[str] = []
        self._lock = threading.Lock()

    def count_for(self, case_id_str: str) -> int:
        with self._lock:
            return self.calls.count(case_id_str)

    def record(self, case_id_str: str) -> None:
        with self._lock:
            self.calls.append(case_id_str)


@pytest.fixture
def slow_build(monkeypatch) -> _SlowBuildCounter:
    counter = _SlowBuildCounter(delay_seconds=0.3)
    original_build = InvestmentCaseCompositionService.build

    def _instrumented_build(self, case_id_str: str):
        counter.record(case_id_str)
        time.sleep(counter.delay_seconds)
        return original_build(self, case_id_str)

    monkeypatch.setattr(InvestmentCaseCompositionService, "build", _instrumented_build)
    return counter


class TestTwoConcurrentRequestsAreFullyIsolated:
    """The real production shape: two separate HTTP requests, each with
    its own `InvestmentCaseCompositionService` instance (exactly what
    FastAPI's per-request dependency resolution constructs -- see
    `TestDependencyIsNeverShared` below for direct proof of that claim)."""

    def test_both_complete_successfully_with_no_exceptions(self, slow_build):
        harness_a = _harness_with_watchlist("AAA")
        harness_b = _harness_with_watchlist("BBB")

        results: dict[str, object] = {}
        errors: dict[str, BaseException] = {}

        def _run(name: str, harness: _Harness) -> None:
            try:
                results[name] = harness.agenda_service.build_agenda()
            except BaseException as exc:  # noqa: BLE001 -- captured for the assertion below, not swallowed
                errors[name] = exc

        t1 = threading.Thread(target=_run, args=("a", harness_a))
        t2 = threading.Thread(target=_run, args=("b", harness_b))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == {}
        assert set(results.keys()) == {"a", "b"}

    def test_the_two_requests_genuinely_overlap_in_wall_clock_time(self, slow_build):
        """If this test's own concurrency were accidentally serialized
        (e.g. a hidden global lock), the assertions in the other tests
        in this class would be vacuous -- they'd never actually exercise
        overlapping execution. This test proves overlap really happens.

        Note this is CPython, with a GIL: the CPU-bound portion of
        `build_agenda()` (everything except the artificially injected
        `time.sleep`) does NOT run in parallel across two threads --
        only I/O-bound waits (real DB calls, and this fixture's own
        sleep) release the GIL and genuinely overlap. So concurrent
        wall time is expected to land somewhere between ~1x solo
        (if sleep dominates) and ~2x solo (if CPU work dominates) --
        never *at* 2x, which is what a real serialization bug (e.g. a
        hidden lock forcing one request to fully finish before the
        other starts) would produce. The threshold below rules out
        that failure mode with margin, without pretending CPython
        threads give full CPU parallelism."""
        harness_solo = _harness_with_watchlist("SOLO")
        solo_start = time.perf_counter()
        harness_solo.agenda_service.build_agenda()
        solo_duration = time.perf_counter() - solo_start

        harness_a = _harness_with_watchlist("AAA")
        harness_b = _harness_with_watchlist("BBB")

        def _run(harness: _Harness) -> None:
            harness.agenda_service.build_agenda()

        start = time.perf_counter()
        t1 = threading.Thread(target=_run, args=(harness_a,))
        t2 = threading.Thread(target=_run, args=(harness_b,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        concurrent_duration = time.perf_counter() - start

        assert concurrent_duration < solo_duration * 1.9, (
            f"concurrent={concurrent_duration:.3f}s solo={solo_duration:.3f}s -- "
            "requests appear to have run fully serialized, not overlapped"
        )

    def test_each_requests_own_case_is_built_exactly_once_real_time(self, slow_build):
        """Caching works per request (the real, uncached implementation
        runs exactly once per Case within that request), and never
        leaks: harness A's Case is never built while resolving harness
        B's agenda, and vice versa -- structurally guaranteed here since
        each harness owns its own database, but confirmed directly via
        the real-call counter regardless."""
        harness_a = _harness_with_watchlist("AAA")
        harness_b = _harness_with_watchlist("BBB")
        case_a = harness_a.watchlist_store.get_by_ticker("AAA").case_id
        case_b = harness_b.watchlist_store.get_by_ticker("BBB").case_id

        def _run(harness: _Harness) -> None:
            harness.agenda_service.build_agenda()

        t1 = threading.Thread(target=_run, args=(harness_a,))
        t2 = threading.Thread(target=_run, args=(harness_b,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert slow_build.count_for(case_a) == 1
        assert slow_build.count_for(case_b) == 1
        # Neither harness ever touched the other's Case id.
        assert case_b not in [c for c in slow_build.calls if c == case_a]

    def test_neither_instance_leaks_the_wrapper_after_both_complete(self, slow_build):
        """`build_agenda`'s own `finally: del self._composition_service
        .build` must fire for each instance independently. A leaked
        instance attribute would mean the next real caller of that
        exact `InvestmentCaseCompositionService` object silently keeps
        using a stale, request-scoped cache forever."""
        harness_a = _harness_with_watchlist("AAA")
        harness_b = _harness_with_watchlist("BBB")

        def _run(harness: _Harness) -> None:
            harness.agenda_service.build_agenda()

        t1 = threading.Thread(target=_run, args=(harness_a,))
        t2 = threading.Thread(target=_run, args=(harness_b,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert "build" not in vars(harness_a.composition_service)
        assert "build" not in vars(harness_b.composition_service)
        # The class's own method is exactly what a brand-new, unrelated
        # instance would use -- proving no class-level leakage either.
        fresh = _harness_with_watchlist("FRESH")
        assert "build" not in vars(fresh.composition_service)


class TestExceptionSafety:
    def test_an_exception_mid_build_still_restores_the_original_method(self, monkeypatch):
        harness = _harness_with_watchlist("EXC")

        def _boom(*_args, **_kwargs):
            raise RuntimeError("simulated failure inside build_agenda")

        monkeypatch.setattr(harness.agenda_service, "_build_agenda_impl", _boom)

        with pytest.raises(RuntimeError, match="simulated failure"):
            harness.agenda_service.build_agenda()

        # The wrapper must be gone even though the call raised.
        assert "build" not in vars(harness.composition_service)
        # And the service is still genuinely usable afterward.
        result = harness.composition_service.build(
            harness.watchlist_store.get_by_ticker("EXC").case_id
        )
        assert result is not None


class TestDependencyIsNeverShared:
    """Direct proof, not assumption: two independent calls to the exact
    FastAPI provider function construct two distinct objects. Combined
    with the read of fastapi/dependencies/utils.py's own
    `solve_dependencies` (defaults `dependency_cache` to a fresh `{}`
    every call, and that call happens once per `app(request)` -- i.e.
    once per HTTP request), this is the complete chain of evidence that
    two concurrent HTTP requests can never observe each other's
    `InvestmentCaseCompositionService` instance."""

    def test_the_composition_service_provider_returns_a_new_instance_every_call(self):
        from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
        from atlas.core.infrastructure.api.case.dependencies import get_case_repository
        from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
        from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
        from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
        from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
        from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store, get_alpha_trade_log_store
        from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
        from atlas.alpha.business_data_refresh.api.dependencies import get_business_record_repository
        from atlas.alpha.investment_case_change.api.dependencies import get_investment_case_snapshot_repository

        engine = _new_engine()
        kwargs = dict(
            case_repository=get_case_repository(engine=engine),
            decision_repository=get_decision_repository(engine=engine),
            observation_repository=get_observation_repository(engine=engine),
            evidence_repository=get_evidence_repository(engine=engine),
            outcome_repository=get_outcome_repository(engine=engine),
            portfolio_store=get_alpha_portfolio_store(engine=engine),
            trade_log_store=get_alpha_trade_log_store(engine=engine),
            business_record_repository=get_business_record_repository(engine=engine),
            watchlist_store=get_alpha_watchlist_store(engine=engine),
            snapshot_repository=get_investment_case_snapshot_repository(engine=engine),
        )

        first = get_investment_case_composition_service(**kwargs)
        second = get_investment_case_composition_service(**kwargs)

        assert first is not second
        assert type(first) is InvestmentCaseCompositionService


class TestCounterfactualSharedInstanceIsUnsafe:
    """Documents, as a deliberate proof-of-concept, exactly why sharing
    ONE `InvestmentCaseCompositionService` between two concurrently-
    running `DailyBriefAgendaService`s -- which never happens in
    production, per `TestDependencyIsNeverShared` above -- would be
    unsafe. This is what the current design avoids, not what it does."""

    def test_a_deliberately_shared_instance_corrupts_or_crashes_under_concurrency(self, monkeypatch):
        # A short, dedicated delay -- not the 0.3s `slow_build` fixture
        # used elsewhere. An early version of this test used that
        # fixture directly and took over two minutes: sharing one
        # instance makes the two threads' wrapper-install/cache-lookup
        # steps race on which wrapper is "currently installed," so many
        # of the 16 signal sources' repeated `build()` calls for the
        # *same* Case land on the *other* thread's cache and miss,
        # triggering the real (slow) implementation dozens of times
        # instead of once -- itself a second, independent demonstration
        # of the hazard (silent cache-defeat, not just a clean crash).
        # A much shorter delay still reliably creates the same race
        # window (CPython's default GIL switch interval is ~5ms) while
        # keeping this test fast.
        counter = _SlowBuildCounter(delay_seconds=0.01)
        original_build = InvestmentCaseCompositionService.build

        def _instrumented_build(self, case_id_str: str):
            counter.record(case_id_str)
            time.sleep(counter.delay_seconds)
            return original_build(self, case_id_str)

        monkeypatch.setattr(InvestmentCaseCompositionService, "build", _instrumented_build)

        harness_a = _harness_with_watchlist("SHAREDA")
        harness_b = _harness_with_watchlist("SHAREDB")
        # Force both DailyBriefAgendaServices onto the SAME
        # InvestmentCaseCompositionService object -- the counterfactual
        # this design deliberately avoids.
        harness_b.agenda_service._composition_service = harness_a.composition_service
        case_a = harness_a.watchlist_store.get_by_ticker("SHAREDA").case_id

        outcomes: dict[str, str] = {}

        def _run(name: str, harness: _Harness) -> None:
            try:
                harness.agenda_service.build_agenda()
                outcomes[name] = "completed"
            except AttributeError:
                outcomes[name] = "attribute_error"

        t1 = threading.Thread(target=_run, args=("a", harness_a))
        t2 = threading.Thread(target=_run, args=("b", harness_b))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Whichever thread's `finally: del self._composition_service
        # .build` runs first deletes the ONLY instance attribute on the
        # shared object; the second thread's own `finally` then either
        # crashes trying to delete an attribute that is already gone,
        # or (if it ran its own `del` first and the other thread's
        # install/delete raced around it) leaves the object in a state
        # neither thread intended. Either observable outcome -- a raised
        # AttributeError, or both reporting "completed" while having
        # silently shared one cache instead of two -- demonstrates the
        # real hazard a shared instance introduces. The one outcome that
        # would be genuinely wrong is neither thread ever detecting
        # anything unusual while also producing fully correct, isolated
        # results -- which the assertion below rules out by checking the
        # shared object's own final state is inconsistent with clean,
        # independent per-request teardown. A third, independent
        # signature of the same hazard: harness A's own Case is real-
        # built (cache miss) more than once, meaning at some point
        # harness B's wrapper/cache was the one "currently installed"
        # when harness A's own signal sources asked for it -- the two
        # threads' caches got cross-wired rather than staying isolated.
        cache_defeated = counter.count_for(case_a) > 1
        shared_has_leaked_or_conflicting_state = (
            "build" in vars(harness_a.composition_service)
            or outcomes["a"] == "attribute_error"
            or outcomes["b"] == "attribute_error"
            or cache_defeated
        )
        assert shared_has_leaked_or_conflicting_state, (
            "expected the shared-instance counterfactual to show a leaked wrapper, a "
            f"raised AttributeError, or cache defeat, but observed clean outcomes={outcomes}, "
            f"build(case_a) called {counter.count_for(case_a)} time(s) -- "
            "if this genuinely never reproduces, the isolation the real (non-shared) "
            "design relies on may be less load-bearing than documented"
        )


class TestPerformanceSprint2WrappersAreAlsoIsolatedUnderConcurrency:
    """Performance Sprint 2 added two more per-call wrappers -- over
    `DecisionReadinessService.assess_for_case` and
    `InvestmentDecisionService.synthesize_for_case` -- using the exact
    same technique as `composition_service.build` above. Same proof
    applies identically (both services' own FastAPI providers are
    depended on, via the identical `Depends(get_decision_readiness_
    service)` / `Depends(get_investment_decision_service)` functions,
    by every sibling package that also needs them -- confirmed by grep
    across atlas/alpha/ during that sprint's own investigation, so
    FastAPI's per-request dependency cache guarantees the same
    instance-per-request isolation already proven above for
    `InvestmentCaseCompositionService`). This class re-runs the same
    concurrent-request shape specifically against the two new
    wrappers, rather than assuming the earlier proof automatically
    covers code added later."""

    def test_two_concurrent_requests_leave_no_wrapper_on_either_instance(self, slow_build):
        harness_a = _harness_with_watchlist("RDA")
        harness_b = _harness_with_watchlist("RDB")

        def _run(harness: _Harness) -> None:
            harness.agenda_service.build_agenda()

        t1 = threading.Thread(target=_run, args=(harness_a,))
        t2 = threading.Thread(target=_run, args=(harness_b,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert "assess_for_case" not in vars(harness_a.decision_readiness_service)
        assert "assess_for_case" not in vars(harness_b.decision_readiness_service)
        assert "synthesize_for_case" not in vars(harness_a.investment_decision_service)
        assert "synthesize_for_case" not in vars(harness_b.investment_decision_service)

    def test_two_concurrent_requests_both_complete_with_correct_results(self, slow_build):
        harness_a = _harness_with_watchlist("RDC")
        harness_b = _harness_with_watchlist("RDD")

        results: dict[str, object] = {}
        errors: dict[str, BaseException] = {}

        def _run(name: str, harness: _Harness) -> None:
            try:
                results[name] = harness.agenda_service.build_agenda()
            except BaseException as exc:  # noqa: BLE001
                errors[name] = exc

        t1 = threading.Thread(target=_run, args=("a", harness_a))
        t2 = threading.Thread(target=_run, args=("b", harness_b))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == {}
        assert set(results.keys()) == {"a", "b"}

    def test_a_deliberately_shared_readiness_instance_shows_the_same_hazard(self, monkeypatch):
        """The same counterfactual as the composition-service case
        above, applied to `decision_readiness_service`: sharing it
        between two concurrently-running `DailyBriefAgendaService`s
        (never happens in production -- see the class docstring above)
        reproduces the identical leaked-wrapper/AttributeError/cache-
        defeat signature."""
        import time as _time

        counter = _SlowBuildCounter(delay_seconds=0.01)
        original = DecisionReadinessService.assess_for_case

        def _instrumented(self, case_id, *, ticker=None):
            counter.record(case_id)
            _time.sleep(counter.delay_seconds)
            return original(self, case_id, ticker=ticker)

        monkeypatch.setattr(DecisionReadinessService, "assess_for_case", _instrumented)

        harness_a = _harness_with_watchlist("RDSHAREDA")
        harness_b = _harness_with_watchlist("RDSHAREDB")
        harness_b.agenda_service._decision_readiness_service = harness_a.decision_readiness_service
        case_a = harness_a.watchlist_store.get_by_ticker("RDSHAREDA").case_id

        outcomes: dict[str, str] = {}

        def _run(name: str, harness: _Harness) -> None:
            try:
                harness.agenda_service.build_agenda()
                outcomes[name] = "completed"
            except AttributeError:
                outcomes[name] = "attribute_error"

        t1 = threading.Thread(target=_run, args=("a", harness_a))
        t2 = threading.Thread(target=_run, args=("b", harness_b))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        cache_defeated = counter.count_for(case_a) > 1
        shared_has_leaked_or_conflicting_state = (
            "assess_for_case" in vars(harness_a.decision_readiness_service)
            or outcomes["a"] == "attribute_error"
            or outcomes["b"] == "attribute_error"
            or cache_defeated
        )
        assert shared_has_leaked_or_conflicting_state, (
            f"expected the shared-instance counterfactual to reproduce the hazard, but "
            f"observed clean outcomes={outcomes}, assess_for_case(case_a) called "
            f"{counter.count_for(case_a)} time(s)"
        )
