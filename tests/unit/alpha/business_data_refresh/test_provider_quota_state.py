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
from atlas.alpha.business_data_refresh.models import EnrichmentOutcome
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
from atlas.business_data_providers.errors import DailyQuotaExhausted, RateLimited

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
