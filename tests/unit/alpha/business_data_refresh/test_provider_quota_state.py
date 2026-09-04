"""Provider & Quota Intelligence -- daily-vs-pacing discrimination,
persisted provider availability, and the two honesty rules that follow
from them.

The governing incident: on 2026-09-01 Atlas read a fresh 0/25 local
budget at 00:05 UTC, Alpha Vantage rejected the first call with an
explicit daily-limit payload, and the run then spent 16 consecutive
rejected calls -- persisting 16 `NO_MATCH` resolution records for
companies whose identity was never evaluated.

Every provider here is a fake. No network, by construction and by
`tests/conftest.py`'s socket guard.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.bulk import enrich_holdings
from atlas.alpha.business_data_refresh.completion import (
    CoverageClassification,
    ProviderCompletionStatus,
    ProviderFailureClassification,
    assess_enrichment_completion,
    classify_coverage,
    classify_provider_failure,
)
from atlas.alpha.business_data_refresh.models import EnrichmentOutcome, ProviderFailure
from atlas.alpha.business_data_refresh.provider_state import (
    ALPHA_VANTAGE_PROVIDER_NAME,
    DEFAULT_DAILY_COOLDOWN,
    ProviderAvailability,
    ProviderAvailabilityStore,
    ProviderBudgetGate,
)
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.business_data_providers.alpha_vantage import _check_for_provider_error, _is_daily_quota_message
from atlas.business_data_providers.errors import (
    DailyQuotaExhausted,
    NoIdentityDataForSymbol,
    RateLimited,
)
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider

_NOW = datetime(2026, 9, 1, 0, 5, tzinfo=timezone.utc)

#: Both strings were captured live on 2026-09-01 from the real API.
DAILY_PAYLOAD = {
    "Information": (
        "We have detected your API key as NCYQMW1SCW5OBXXX and our standard API rate limit is 25 "
        "requests per day. Please subscribe to any of the premium plans at "
        "https://www.alphavantage.co/premium/ to instantly remove all daily rate limits."
    )
}
PACING_PAYLOAD = {
    "Information": (
        "Thank you for using Alpha Vantage! Please consider spreading out your free API requests "
        "more sparingly (1 request per second). You may subscribe to any of the premium plans at "
        "https://www.alphavantage.co/premium/ to lift the free key rate limit (25 requests per day), "
        "raise the per-second limit"
    )
}


class TestDailyVersusShortTermClassification:
    def test_real_daily_payload_raises_daily_quota_exhausted(self):
        with pytest.raises(DailyQuotaExhausted):
            _check_for_provider_error(DAILY_PAYLOAD, context="OVERVIEW(MSFT)")

    def test_real_pacing_payload_raises_plain_rate_limited(self):
        with pytest.raises(RateLimited) as caught:
            _check_for_provider_error(PACING_PAYLOAD, context="OVERVIEW(AVGO)")
        assert not isinstance(caught.value, DailyQuotaExhausted)

    def test_pacing_payload_is_not_misread_despite_naming_the_daily_cap(self):
        """The real pacing message also contains the words '25 requests
        per day'. Matching that phrase alone would block Atlas for a
        whole reset cycle over a one-second problem."""
        assert "requests per day" in PACING_PAYLOAD["Information"]
        assert _is_daily_quota_message(PACING_PAYLOAD["Information"]) is False

    def test_daily_remains_catchable_as_rate_limited(self):
        """Every pre-existing `except RateLimited` must keep working."""
        assert issubclass(DailyQuotaExhausted, RateLimited)

    def test_unknown_wording_degrades_to_short_term_not_daily(self):
        assert _is_daily_quota_message("Some wording Atlas has never seen before") is False

    def test_classification_is_deterministic(self):
        for _ in range(3):
            assert _is_daily_quota_message(DAILY_PAYLOAD["Information"]) is True
            assert _is_daily_quota_message(PACING_PAYLOAD["Information"]) is False


@pytest.fixture
def engine():
    return create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )


class _FullBudget:
    """A local counter that always claims budget -- the exact optimism
    that caused the incident."""

    def has_budget(self) -> bool:
        return True


class _NoBudget:
    def has_budget(self) -> bool:
        return False


class TestPersistenceAndOverride:
    def test_local_counter_says_available_but_provider_state_blocks(self, engine):
        store = ProviderAvailabilityStore(engine)
        gate = ProviderBudgetGate(
            _FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: _NOW
        )
        assert gate.has_budget() is True
        gate.record_daily_exhausted("provider said 25/day spent")
        assert gate.has_budget() is False
        assert gate.current_state() is ProviderAvailability.PROVIDER_DAILY_EXHAUSTED

    def test_provider_block_survives_process_restart(self, engine):
        first = ProviderBudgetGate(
            _FullBudget(), ProviderAvailabilityStore(engine),
            provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: _NOW,
        )
        first.record_daily_exhausted("provider said 25/day spent")

        # A brand-new store and gate stand in for a restarted process.
        restarted = ProviderBudgetGate(
            _FullBudget(), ProviderAvailabilityStore(engine),
            provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: _NOW,
        )
        assert restarted.has_budget() is False

    def test_a_fresh_utc_date_does_not_clear_a_provider_block(self, engine):
        """The precise failure of 2026-09-01: the local counter resets at
        UTC midnight, the provider's allowance evidently does not."""
        store = ProviderAvailabilityStore(engine)
        ProviderBudgetGate(
            _FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: _NOW
        ).record_daily_exhausted("provider said 25/day spent")

        just_after_midnight = _NOW + timedelta(minutes=30)
        gate = ProviderBudgetGate(
            _FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: just_after_midnight
        )
        assert gate.has_budget() is False

    def test_block_lifts_once_the_cooldown_has_elapsed(self, engine):
        store = ProviderAvailabilityStore(engine)
        ProviderBudgetGate(
            _FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: _NOW
        ).record_daily_exhausted("provider said 25/day spent")
        later = _NOW + DEFAULT_DAILY_COOLDOWN + timedelta(minutes=1)
        gate = ProviderBudgetGate(
            _FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: later
        )
        assert gate.has_budget() is True

    def test_short_term_throttle_lifts_far_sooner_than_daily(self, engine):
        store = ProviderAvailabilityStore(engine)
        gate_at = lambda t: ProviderBudgetGate(  # noqa: E731
            _FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: t
        )
        gate_at(_NOW).record_short_term_throttle("slow down")
        assert gate_at(_NOW + timedelta(seconds=5)).has_budget() is False
        assert gate_at(_NOW + timedelta(minutes=5)).has_budget() is True

    def test_local_exhaustion_still_blocks_without_any_provider_state(self, engine):
        gate = ProviderBudgetGate(
            _NoBudget(), ProviderAvailabilityStore(engine),
            provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: _NOW,
        )
        assert gate.has_budget() is False
        assert gate.current_state() is ProviderAvailability.LOCALLY_EXHAUSTED

    def test_unknown_is_distinct_from_available(self, engine):
        gate = ProviderBudgetGate(
            _FullBudget(), ProviderAvailabilityStore(engine),
            provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: _NOW,
        )
        assert gate.current_state() is ProviderAvailability.UNKNOWN
        gate.record_available()
        assert gate.current_state() is ProviderAvailability.AVAILABLE

    def test_state_is_provider_keyed_not_global(self, engine):
        store = ProviderAvailabilityStore(engine)
        ProviderBudgetGate(
            _FullBudget(), store, provider_name="ALPHA_VANTAGE", clock=lambda: _NOW
        ).record_daily_exhausted("spent")
        other = ProviderBudgetGate(
            _FullBudget(), store, provider_name="SOME_OTHER_PROVIDER", clock=lambda: _NOW
        )
        assert other.has_budget() is True

    def test_recording_is_deterministic(self, engine):
        store = ProviderAvailabilityStore(engine)
        a = store.record(
            "P", ProviderAvailability.PROVIDER_DAILY_EXHAUSTED, reason="r", observed_at=_NOW
        )
        b = store.record(
            "P", ProviderAvailability.PROVIDER_DAILY_EXHAUSTED, reason="r", observed_at=_NOW
        )
        assert a == b
        assert store.get("P") == a


def _profile_doc(ticker: str) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"{ticker}:profile",
        company=ticker,
        source_kind=SourceKind.COMPANY_PROFILE.value,
        published_at=_NOW,
        provider_id="alpha_vantage",
        raw_reference="stub://overview",
        content_hash=f"hash-{ticker}",
        language="en",
        metadata={
            "name": "Example Corporation", "country": "USA", "exchange": "NASDAQ",
            "currency": "USD", "asset_type": "Common Stock",
        },
    )


class _ThrottledProvider:
    """Raises the real daily-quota error from the profile leg, exactly as
    the live provider did on 2026-09-01."""

    def __init__(self, error=None):
        self.error = error or DailyQuotaExhausted("OVERVIEW: 25 requests per day")
        self.profile_calls = 0

    def fetch_company_profile(self, *, company_identifier, evaluated_at):
        self.profile_calls += 1
        raise self.error

    def fetch(self, *, company_identifier, evaluated_at):
        return ()


class _SilentProvider:
    """Returns no identity documents without raising -- a *genuine*
    no-match, which must keep behaving exactly as before."""

    def fetch_company_profile(self, *, company_identifier, evaluated_at):
        return ()

    def fetch(self, *, company_identifier, evaluated_at):
        return ()


class _WorkingProvider:
    def fetch_company_profile(self, *, company_identifier, evaluated_at):
        return (_profile_doc(company_identifier),)

    def fetch(self, *, company_identifier, evaluated_at):
        return ()


@pytest.fixture
def harness(engine):
    create_business_record_table(engine)
    # Deliberately does NOT construct a resolution repository: this
    # package's own integration-safety guard forbids anything outside
    # `canonical_security_resolution` and the Identity Gate from
    # importing it. Row counts go through raw SQL in `_count_resolutions`
    # instead, which needs no such import.
    return (
        SqlAlchemyBusinessRecordRepository(engine),
        build_identity_gate(engine),
        None,
        engine,
    )


class TestNoIdentityOutcomePersistedWhileThrottled:
    def test_throttled_attempt_writes_no_resolution_record(self, harness):
        repository, gate, resolutions, engine = harness
        before = _count_resolutions(engine)
        summary = refresh_company_data(
            "VOLV-B", (_ThrottledProvider(),), repository, identity_gate=gate
        )
        assert _count_resolutions(engine) == before
        assert summary.identity_gate_outcome == "NOT_EVALUATED_PROVIDER_THROTTLED"
        assert summary.identity_gate_outcome != "NO_MATCH"

    def test_throttled_attempt_reports_the_real_cause(self, harness):
        repository, gate, _resolutions, _engine = harness
        summary = refresh_company_data(
            "VOLV-B", (_ThrottledProvider(),), repository, identity_gate=gate
        )
        assert "never evaluated" in (summary.identity_gate_reason or "")
        assert summary.daily_quota_exhausted is True
        assert summary.provider_errors[0].kind == "DailyQuotaExhausted"

    def test_short_term_throttle_also_suppresses_the_identity_outcome(self, harness):
        repository, gate, _resolutions, engine = harness
        before = _count_resolutions(engine)
        summary = refresh_company_data(
            "VOLV-B", (_ThrottledProvider(RateLimited("slow down")),), repository, identity_gate=gate
        )
        assert _count_resolutions(engine) == before
        assert summary.daily_quota_exhausted is False

    def test_genuine_no_match_is_unchanged(self, harness):
        """A provider that answers and simply has nothing must still
        produce a real, persisted `NO_MATCH` -- the throttle fix must not
        suppress honest evidence."""
        repository, gate, _resolutions, engine = harness
        before = _count_resolutions(engine)
        summary = refresh_company_data(
            "NOSUCHCO", (_SilentProvider(),), repository, identity_gate=gate
        )
        assert summary.identity_gate_outcome == "NO_MATCH"
        assert _count_resolutions(engine) == before + 1

    def test_successful_identity_is_unchanged(self, harness):
        repository, gate, _resolutions, _engine = harness
        summary = refresh_company_data(
            "MSFT", (_WorkingProvider(),), repository, identity_gate=gate
        )
        assert summary.identity_gate_outcome == "AUTO_ACCEPT"
        assert summary.new_records == 1


def _count_resolutions(engine) -> int:
    from sqlalchemy import text

    with engine.connect() as connection:
        return connection.execute(
            text("select count(*) from canonical_security_resolution_records")
        ).scalar_one()


class TestBatchAbortOnFirstDailyRejection:
    def test_batch_stops_after_the_first_confirmed_daily_rejection(self, harness):
        repository, gate, _resolutions, _engine = harness
        provider = _ThrottledProvider()
        summary = enrich_holdings(
            ("AAA", "BBB", "CCC", "DDD"), (provider,), repository, identity_gate=gate
        )
        assert provider.profile_calls == 1, "only the first company may spend a call"
        outcomes = [r.outcome for r in summary.results]
        assert outcomes[1:] == [EnrichmentOutcome.QUOTA_DEFERRED] * 3

    def test_every_untouched_ticker_is_reported_not_silently_dropped(self, harness):
        repository, gate, _resolutions, _engine = harness
        summary = enrich_holdings(
            ("AAA", "BBB", "CCC"), (_ThrottledProvider(),), repository, identity_gate=gate
        )
        assert [r.ticker for r in summary.results] == ["AAA", "BBB", "CCC"]

    def test_short_term_throttle_does_not_abort_the_batch(self, harness):
        """A pacing rejection is recoverable in seconds; aborting a whole
        batch for it would be an over-reaction."""
        repository, gate, _resolutions, _engine = harness
        provider = _ThrottledProvider(RateLimited("slow down"))
        enrich_holdings(("AAA", "BBB", "CCC"), (provider,), repository, identity_gate=gate)
        assert provider.profile_calls == 3

    def test_abort_records_the_block_on_the_availability_gate(self, harness):
        repository, gate, _resolutions, engine = harness
        store = ProviderAvailabilityStore(engine)
        availability = ProviderBudgetGate(
            _FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME, clock=lambda: _NOW
        )
        enrich_holdings(
            ("AAA", "BBB"), (_ThrottledProvider(),), repository,
            identity_gate=gate, availability_gate=availability,
        )
        assert availability.current_state() is ProviderAvailability.PROVIDER_DAILY_EXHAUSTED
        assert availability.has_budget() is False


class TestArchitectureBoundaries:
    def test_provider_state_imports_no_provider_adapter(self):
        """The state model must stay provider-agnostic -- it may never
        import Alpha Vantage or any other adapter."""
        from pathlib import Path

        source = Path("atlas/alpha/business_data_refresh/provider_state.py").read_text()
        for forbidden in (
            "from atlas.business_data_providers.alpha_vantage",
            "from atlas.business_data_providers.sec_edgar",
            "import alpha_vantage",
        ):
            assert forbidden not in source

    def test_services_do_not_import_quota_or_provider_concepts(self):
        from pathlib import Path

        for module in ("atlas/alpha/portfolio/service.py", "atlas/alpha/watchlist/service.py"):
            source = Path(module).read_text()
            assert "AlphaVantageQuotaTracker" not in source
            assert "ProviderBudgetGate" not in source


class TestNoIdentityDataForSymbolIsItsOwnOutcome:
    """2026-09-02. Alpha Vantage answered successfully for eleven
    companies at once and returned no identity fields; Atlas recorded no
    failure at all, so coverage told the investor identity had "failed
    for a retryable reason (provider or budget)". The provider had
    answered. Re-sending the identical symbol could never succeed.

    These assert the outcome is distinct from every neighbouring one --
    the whole point being that five different realities must not share a
    single reason string.
    """

    def _completion(self, kind: str, ticker: str = "VOLV-B"):
        failure = ProviderFailure(
            provider_id="AlphaVantageMarketDataProvider.fetch_company_profile",
            error="OVERVIEW returned no identity fields for this symbol form",
            kind=kind,
        )
        return assess_enrichment_completion(ticker, (), (failure,))

    def test_provider_raises_instead_of_returning_empty(self):
        from datetime import datetime as _dt

        provider = AlphaVantageMarketDataProvider(
            lambda url, headers=None: {}, api_key="k", sleeper=lambda s: None
        )
        with pytest.raises(NoIdentityDataForSymbol):
            provider.fetch_company_profile(
                company_identifier="VOLV-B", evaluated_at=_dt(2026, 9, 2, tzinfo=timezone.utc)
            )

    def test_classified_as_its_own_kind_not_transient_not_unsupported(self):
        result = classify_provider_failure(provider_id="p", kind="NoIdentityDataForSymbol")
        assert result is ProviderFailureClassification.NO_IDENTITY_FOR_SYMBOL
        assert result is not ProviderFailureClassification.TRANSIENT
        assert result is not ProviderFailureClassification.UNSUPPORTED

    def test_completion_status_is_its_own_member(self):
        completion = self._completion("NoIdentityDataForSymbol")
        status = completion.status_for(SourceKind.COMPANY_PROFILE)
        assert status is ProviderCompletionStatus.FAILED_NO_IDENTITY_FOR_SYMBOL
        assert status is not ProviderCompletionStatus.NOT_YET_ATTEMPTED
        assert status is not ProviderCompletionStatus.FAILED_TRANSIENT
        assert status is not ProviderCompletionStatus.FAILED_UNSUPPORTED

    def test_the_false_retryable_reason_is_gone(self):
        state = classify_coverage(self._completion("NoIdentityDataForSymbol"))
        assert "retryable reason" not in state.reason
        assert "no identity data for this exact symbol" in state.reason.lower()

    def test_reason_does_not_claim_structural_unsupportedness(self):
        """Only one symbol form has been tried."""
        state = classify_coverage(self._completion("NoIdentityDataForSymbol"))
        assert state.classification is not CoverageClassification.UNSUPPORTED
        assert "one symbol form" in state.reason

    def test_the_profile_leg_itself_is_no_longer_treated_as_retryable(self):
        """Leg-level, not whole-ticker. `has_retryable_work` stays True
        here because SEC's statements leg is genuinely NOT_YET_ATTEMPTED
        -- it was never reached, since the identity gate blocks without
        a profile. What this asserts is narrower and is the part the
        fix owns: the *profile* leg is no longer one of the statuses
        that mean "worth asking again"."""
        completion = self._completion("NoIdentityDataForSymbol")
        profile = completion.status_for(SourceKind.COMPANY_PROFILE)
        assert profile not in (
            ProviderCompletionStatus.NOT_YET_ATTEMPTED,
            ProviderCompletionStatus.FAILED_TRANSIENT,
        )

    def test_all_five_realities_have_distinct_reasons(self):
        """NOT_ATTEMPTED / throttled / daily-exhausted / transient /
        answered-with-nothing must never share a reason string."""
        never = classify_coverage(assess_enrichment_completion("X", (), ()))
        answered = classify_coverage(self._completion("NoIdentityDataForSymbol"))
        throttled = classify_coverage(self._completion("RateLimited"))
        daily = classify_coverage(self._completion("DailyQuotaExhausted"))
        network = classify_coverage(self._completion("ProviderTimeout"))
        unsupported = classify_coverage(self._completion("CompanyNotFound"))

        assert never.reason != answered.reason
        assert throttled.reason != answered.reason
        assert daily.reason != answered.reason
        assert network.reason != answered.reason
        assert unsupported.reason != answered.reason
        assert unsupported.classification is CoverageClassification.UNSUPPORTED
        assert answered.classification is not CoverageClassification.UNSUPPORTED

    def test_transient_and_throttled_remain_retryable(self):
        """The new status must not accidentally make real transient
        failures un-retryable."""
        for kind in ("RateLimited", "DailyQuotaExhausted", "ProviderTimeout", "ProviderUnavailable"):
            completion = self._completion(kind)
            assert completion.status_for(SourceKind.COMPANY_PROFILE) is (
                ProviderCompletionStatus.FAILED_TRANSIENT
            ), kind
            assert completion.has_retryable_work is True, kind

    def test_genuine_company_not_found_still_unsupported(self):
        completion = self._completion("CompanyNotFound")
        assert completion.status_for(SourceKind.COMPANY_PROFILE) is (
            ProviderCompletionStatus.FAILED_UNSUPPORTED
        )

    def test_deterministic(self):
        first = classify_coverage(self._completion("NoIdentityDataForSymbol"))
        second = classify_coverage(self._completion("NoIdentityDataForSymbol"))
        assert first.classification is second.classification and first.reason == second.reason


class TestPacingConstantIndependence:
    """2026-09-04. Widening the Alpha Vantage inter-request spacing from
    1.1s to 12.0s must not touch the quota/provider-state layer at all.
    The two mechanisms answer different questions -- pacing asks "how
    long until the next call is safe to make", provider state asks
    "may a call be made at all" -- and they protect against different
    failures. Spacing cannot prevent a daily exhaustion, and provider
    state cannot prevent a short-term throttle.

    These tests pin the separation as a boundary, so a future pacing
    change cannot quietly become a quota change.
    """

    def test_provider_state_module_holds_no_pacing_concept(self):
        """`provider_state.py` must not grow a spacing constant. If
        pacing ever needs to be adaptive it belongs in the provider,
        not smuggled into the availability model."""
        from pathlib import Path

        source = Path("atlas/alpha/business_data_refresh/provider_state.py").read_text()
        for forbidden in (
            "_DEFAULT_INTER_REQUEST_DELAY_SECONDS",
            "inter_request_delay",
            "time.sleep",
        ):
            assert forbidden not in source

    def test_budget_gate_decisions_do_not_consult_any_pacing_value(self, engine):
        """The gate's answer depends only on the local counter and the
        persisted provider state. Same inputs, same answer -- there is
        no timing input that a pacing change could perturb."""
        store = ProviderAvailabilityStore(engine)
        gate = ProviderBudgetGate(_FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME)
        # UNKNOWN, not AVAILABLE: nothing has been recorded yet, and
        # the gate reports absence of state as absence rather than as
        # an optimistic claim. Budget still flows from the counter.
        assert gate.has_budget() is True
        assert gate.current_state() is ProviderAvailability.UNKNOWN

        gate.record_daily_exhausted("provider said daily limit reached")
        assert gate.has_budget() is False
        assert gate.current_state() is ProviderAvailability.PROVIDER_DAILY_EXHAUSTED

    def test_short_term_throttle_still_leaves_the_provider_available(self, engine):
        """The discrimination the pacing change does NOT alter: a
        short-term throttle is a pacing problem, and must never be
        recorded as daily exhaustion. Wider spacing should make these
        rarer -- it does not change what one means when it happens."""
        store = ProviderAvailabilityStore(engine)
        gate = ProviderBudgetGate(_FullBudget(), store, provider_name=ALPHA_VANTAGE_PROVIDER_NAME)
        # TRANSIENT, and specifically not UNSUPPORTED: a throttle says
        # nothing about whether the ticker can ever be served, so it
        # stays retry-worthy. Wider spacing changes how often this
        # happens, never what it means.
        assert (
            classify_provider_failure(provider_id="alpha_vantage", kind="RateLimited")
            is ProviderFailureClassification.TRANSIENT
        )
        assert (
            classify_provider_failure(provider_id="alpha_vantage", kind="DailyQuotaExhausted")
            is ProviderFailureClassification.TRANSIENT
        )
        # No state transition was recorded, so budget is untouched.
        assert gate.has_budget() is True
        assert gate.current_state() is ProviderAvailability.UNKNOWN

    def test_daily_cooldown_is_a_safety_floor_not_a_pacing_interval(self):
        """Guards against the two constants ever being conflated: the
        daily cooldown is measured in hours and gates whole runs; the
        pacing constant is measured in seconds and gates single
        requests."""
        from atlas.business_data_providers.alpha_vantage import _DEFAULT_INTER_REQUEST_DELAY_SECONDS

        assert DEFAULT_DAILY_COOLDOWN.total_seconds() > _DEFAULT_INTER_REQUEST_DELAY_SECONDS * 100
