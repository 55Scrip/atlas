"""Calibration Phase 8B -- Minimal Enrichment Architecture.

Covers the two new, independent gates on `refresh_company_data`
(`depth` -- is this stage wanted; `budget_available` -- is there
provider budget left *right now*), the coverage classification derived
from them, and the properties the sprint's own success criteria name:
no unnecessary provider calls, graceful stop, resumability, and never
recording a fabricated identity outcome.

Every provider here is a fake with an injected fetcher -- no network,
by construction as well as by `tests/conftest.py`'s socket guard.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.completion import (
    CoverageClassification,
    ProviderCompletionStatus,
    assess_enrichment_completion,
    classify_coverage,
)
from atlas.alpha.business_data_refresh.models import EnrichmentDepth, ProviderFailure, stage_allowed
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.canonical_security_gate.factory import build_identity_gate
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind

_NOW = datetime(2026, 8, 31, tzinfo=timezone.utc)
_TICKER = "BENCH"


def _doc(
    kind: SourceKind,
    *,
    identifier: str,
    provider_id: str,
    period_end: date | None = None,
    **metadata,
) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company=_TICKER,
        source_kind=kind.value,
        published_at=_NOW,
        provider_id=provider_id,
        raw_reference=f"stub://{identifier}",
        content_hash=f"hash-{identifier}",
        period_end=period_end,
        language="en",
        metadata=metadata,
    )


class RecordingProvider:
    """Implements every optional provider Protocol `refresh_company_data`
    probes, and records which of them were actually called -- the direct
    way to assert "no unnecessary provider calls" rather than inferring
    it from record counts."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch_company_profile(self, *, company_identifier: str, evaluated_at: datetime):
        self.calls.append("profile")
        return (
            _doc(
                SourceKind.COMPANY_PROFILE,
                identifier="profile-1",
                provider_id="alpha_vantage",
                name="Example Corporation",
                country="USA",
                exchange="NASDAQ",
                currency="USD",
                asset_type="Common Stock",
            ),
        )

    def fetch(self, *, company_identifier: str, evaluated_at: datetime):
        self.calls.append("fetch")
        return (
            _doc(
                SourceKind.FINANCIAL_STATEMENT,
                identifier="fin-2025",
                provider_id="sec_edgar",
                period_end=date(2026, 1, 25),
                metric="Revenues",
                value="1000",
            ),
        )

    def fetch_historical_snapshots(self, *, company_identifier: str, filing_dates, evaluated_at: datetime):
        self.calls.append("historical")
        return (_doc(SourceKind.MARKET_DATA_SNAPSHOT, identifier="snap-1", provider_id="alpha_vantage"),)

    def fetch_earnings_call_transcripts(self, *, company_identifier: str, evaluated_at: datetime):
        self.calls.append("transcripts")
        return (_doc(SourceKind.TRANSCRIPT, identifier="tr-1", provider_id="alpha_vantage"),)


@pytest.fixture
def harness():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    gate = build_identity_gate(engine)
    return repository, gate


def _run(harness, *, depth=EnrichmentDepth.FULL, budget=None, provider=None):
    repository, gate = harness
    provider = provider or RecordingProvider()
    summary = refresh_company_data(
        _TICKER, (provider,), repository, identity_gate=gate, depth=depth, budget_available=budget
    )
    return summary, provider, repository


class TestStageTable:
    def test_unknown_stage_is_never_allowed(self):
        assert stage_allowed(EnrichmentDepth.FULL, "not-a-stage") is False

    def test_minimal_allows_only_profile(self):
        assert stage_allowed(EnrichmentDepth.MINIMAL, "profile") is True
        for stage in ("fundamentals", "historical", "transcripts"):
            assert stage_allowed(EnrichmentDepth.MINIMAL, stage) is False

    def test_full_allows_every_stage(self):
        for stage in ("profile", "fundamentals", "historical", "transcripts"):
            assert stage_allowed(EnrichmentDepth.FULL, stage) is True


class TestDepthGating:
    def test_full_is_the_default_and_runs_every_stage(self, harness):
        summary, provider, _ = _run(harness)
        assert provider.calls == ["profile", "fetch", "historical", "transcripts"]
        assert summary.depth is EnrichmentDepth.FULL
        assert summary.stopped_for_budget is False

    def test_minimal_calls_the_profile_leg_and_nothing_else(self, harness):
        summary, provider, _ = _run(harness, depth=EnrichmentDepth.MINIMAL)
        assert provider.calls == ["profile"]
        assert summary.completed_stages == ("profile",)
        assert summary.stopped_for_budget is False

    def test_minimal_still_establishes_identity(self, harness):
        summary, _, repository = _run(harness, depth=EnrichmentDepth.MINIMAL)
        assert summary.identity_gate_outcome == "AUTO_ACCEPT"
        assert summary.new_records == 1
        assert [r.document_type for r in repository.get_by_company(_TICKER)] == [SourceKind.COMPANY_PROFILE]

    def test_standard_stops_before_the_historical_stages(self, harness):
        _, provider, _ = _run(harness, depth=EnrichmentDepth.STANDARD)
        assert provider.calls == ["profile", "fetch"]


class TestQuotaEnforcement:
    def test_no_budget_at_all_makes_no_provider_call(self, harness):
        _, provider, _ = _run(harness, budget=lambda: False)
        assert provider.calls == []

    def test_no_budget_never_records_a_fabricated_no_match(self, harness):
        """The gate persists every attempt it is given. Recording
        `NO_MATCH` for a company Atlas never asked about would claim a
        provider fact that was never established."""
        summary, _, _ = _run(harness, budget=lambda: False)
        assert summary.identity_gate_outcome == "NOT_ATTEMPTED"
        assert summary.identity_gate_outcome != "NO_MATCH"
        assert "budget" in (summary.identity_gate_reason or "").lower()
        assert summary.stopped_for_budget is True

    def test_budget_exhausted_mid_company_stops_after_the_completed_stage(self, harness):
        budget = iter([True, False, False, False, False])
        summary, provider, _ = _run(harness, budget=lambda: next(budget, False))
        assert provider.calls == ["profile"]
        assert summary.stopped_for_budget is True
        assert summary.completed_stages == ("profile",)

    def test_stopping_persists_everything_already_fetched(self, harness):
        """Never partially corrupt enrichment: the stage that did run is
        fully ingested."""
        budget = iter([True, False, False, False, False])
        summary, _, repository = _run(harness, budget=lambda: next(budget, False))
        assert summary.new_records == 1
        assert len(repository.get_by_company(_TICKER)) == 1

    def test_an_unstarted_stage_stays_retryable_so_a_later_run_resumes_it(self, harness):
        budget = iter([True, False, False, False, False])
        _, _, repository = _run(harness, budget=lambda: next(budget, False))
        completion = assess_enrichment_completion(_TICKER, tuple(repository.get_by_company(_TICKER)), ())
        assert completion.status_for(SourceKind.FINANCIAL_STATEMENT) is ProviderCompletionStatus.NOT_YET_ATTEMPTED
        assert completion.has_retryable_work is True

    def test_resuming_after_budget_returns_completes_the_remaining_stages(self, harness):
        repository, gate = harness
        provider = RecordingProvider()
        budget = iter([True, False, False, False, False])
        refresh_company_data(
            _TICKER, (provider,), repository, identity_gate=gate, budget_available=lambda: next(budget, False)
        )
        provider.calls.clear()
        refresh_company_data(_TICKER, (provider,), repository, identity_gate=gate, budget_available=lambda: True)
        assert provider.calls == ["profile", "fetch", "historical", "transcripts"]

    def test_budget_is_rechecked_between_stages_not_once_per_company(self, harness):
        """Phase 8B's own finding: checking once per company lets a
        single company overshoot by every call after its first."""
        checks = {"n": 0}

        def budget() -> bool:
            checks["n"] += 1
            return True

        _run(harness, budget=budget)
        assert checks["n"] >= 4


class TestCoverageClassification:
    def _completion(self, records=(), failures=()):
        return assess_enrichment_completion(_TICKER, tuple(records), tuple(failures))

    def test_never_attempted_is_temporarily_incomplete_not_unsupported(self):
        state = classify_coverage(self._completion())
        assert state.classification is CoverageClassification.TEMPORARILY_INCOMPLETE
        assert state.can_analyse is False

    def test_permanent_identity_failure_is_unsupported(self):
        failure = ProviderFailure(
            provider_id="AlphaVantageMarketDataProvider.fetch_company_profile",
            error="unknown symbol",
            kind="CompanyNotFound",
        )
        state = classify_coverage(self._completion(failures=(failure,)))
        assert state.classification is CoverageClassification.UNSUPPORTED
        assert state.can_analyse is False

    def test_missing_api_key_is_retryable_never_unsupported(self):
        """A deployment-configuration gap must never be reported as a
        fact about the company -- the Phase 8 root cause."""
        failure = ProviderFailure(
            provider_id="AlphaVantageMarketDataProvider.fetch_company_profile",
            error="ALPHA_VANTAGE_API_KEY is not set.",
            kind="MissingRequiredField",
        )
        state = classify_coverage(self._completion(failures=(failure,)))
        assert state.classification is CoverageClassification.TEMPORARILY_INCOMPLETE

    def test_profile_only_is_analysable_with_depth_still_pending(self, harness):
        _, _, repository = _run(harness, depth=EnrichmentDepth.MINIMAL)
        state = classify_coverage(self._completion(records=repository.get_by_company(_TICKER)))
        assert state.classification is CoverageClassification.DEEP_ANALYSIS_PENDING
        assert state.can_analyse is True

    def test_profile_and_statements_is_supported(self, harness):
        _, _, repository = _run(harness, depth=EnrichmentDepth.STANDARD)
        state = classify_coverage(self._completion(records=repository.get_by_company(_TICKER)))
        assert state.classification is CoverageClassification.SUPPORTED
        assert state.can_analyse is True

    def test_every_classification_carries_a_named_cause(self):
        state = classify_coverage(self._completion())
        assert state.reason
        assert "missing" != state.reason.strip().lower()

    def test_classification_is_deterministic(self, harness):
        _, _, repository = _run(harness, depth=EnrichmentDepth.MINIMAL)
        records = repository.get_by_company(_TICKER)
        first = classify_coverage(self._completion(records=records))
        second = classify_coverage(self._completion(records=records))
        assert first.classification is second.classification
        assert first.reason == second.reason


class TestRegressionSafety:
    def test_omitting_the_new_arguments_reproduces_pre_8b_behaviour(self, harness):
        repository, gate = harness
        provider = RecordingProvider()
        summary = refresh_company_data(_TICKER, (provider,), repository, identity_gate=gate)
        assert provider.calls == ["profile", "fetch", "historical", "transcripts"]
        assert summary.depth is EnrichmentDepth.FULL
        assert summary.stopped_for_budget is False

    def test_no_duplicate_enrichment_within_one_run(self, harness):
        _, provider, _ = _run(harness)
        assert len(provider.calls) == len(set(provider.calls))
