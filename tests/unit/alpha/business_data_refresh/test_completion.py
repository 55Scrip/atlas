"""Tests for `atlas.alpha.business_data_refresh.completion` (Automatic
Enrichment Coverage, Implementation Phase 1) -- the provider-aware
completion model replacing `ensure_company_enriched`'s own prior,
coarser `is_minimally_complete` gate.

Real, ingested `BusinessRecord`s throughout (via `build_raw_document`/
`ingest`, the same fixture `tests.unit.analysis_engine.business_data
.test_completeness` already uses) -- never hand-built dataclass
instances standing in for what the real pipeline actually produces.
"""
from __future__ import annotations

from atlas.alpha.business_data_refresh.completion import (
    ProviderCompletionStatus,
    ProviderFailureClassification,
    assess_enrichment_completion,
    classify_provider_failure,
)
from atlas.alpha.business_data_refresh.models import ProviderFailure
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.sources import SourceKind
from tests.unit.analysis_engine.business_data._fixtures import EVALUATED_AT, build_raw_document

_ALPHA_VANTAGE_PROFILE_ID = "AlphaVantageMarketDataProvider.fetch_company_profile"
_SEC_FUNDAMENTALS_ID = "SecEdgarFundamentalsProvider"


def _record(**kwargs) -> BusinessRecord:
    result = ingest(build_raw_document(**kwargs), evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def _profile_record() -> BusinessRecord:
    return _record(identifier="profile", source_kind="company_profile", metadata={"name": "Test Co"})


def _statement_record() -> BusinessRecord:
    from datetime import date

    return _record(
        identifier="fy2024",
        source_kind="financial_statement",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        metadata={"revenue": 1000.0},
    )


class TestClassifyProviderFailure:
    def test_alpha_vantage_profile_missing_required_field_is_transient(self):
        """`fetch_company_profile`'s own only exception source is a
        missing/unset API key -- a deployment config gap, not a
        per-ticker fact."""
        result = classify_provider_failure(provider_id=_ALPHA_VANTAGE_PROFILE_ID, kind="MissingRequiredField")
        assert result is ProviderFailureClassification.TRANSIENT

    def test_sec_missing_required_field_is_unsupported(self):
        """SEC's own `MissingRequiredField` (no CIK match, no us-gaap
        facts for a foreign-private-issuer 20-F filer) is a genuine,
        per-ticker structural absence."""
        result = classify_provider_failure(provider_id=_SEC_FUNDAMENTALS_ID, kind="MissingRequiredField")
        assert result is ProviderFailureClassification.UNSUPPORTED

    def test_company_not_found_is_unsupported(self):
        result = classify_provider_failure(provider_id=_SEC_FUNDAMENTALS_ID, kind="CompanyNotFound")
        assert result is ProviderFailureClassification.UNSUPPORTED

    def test_ambiguous_symbol_is_unsupported(self):
        result = classify_provider_failure(provider_id=_SEC_FUNDAMENTALS_ID, kind="AmbiguousSymbol")
        assert result is ProviderFailureClassification.UNSUPPORTED

    def test_unsupported_unit_is_unsupported(self):
        result = classify_provider_failure(provider_id=_ALPHA_VANTAGE_PROFILE_ID, kind="UnsupportedUnit")
        assert result is ProviderFailureClassification.UNSUPPORTED

    def test_provider_unavailable_is_transient(self):
        result = classify_provider_failure(provider_id=_SEC_FUNDAMENTALS_ID, kind="ProviderUnavailable")
        assert result is ProviderFailureClassification.TRANSIENT

    def test_provider_timeout_is_transient(self):
        result = classify_provider_failure(provider_id=_SEC_FUNDAMENTALS_ID, kind="ProviderTimeout")
        assert result is ProviderFailureClassification.TRANSIENT

    def test_rate_limited_is_transient(self):
        result = classify_provider_failure(provider_id=_ALPHA_VANTAGE_PROFILE_ID, kind="RateLimited")
        assert result is ProviderFailureClassification.TRANSIENT

    def test_malformed_provider_response_is_transient(self):
        result = classify_provider_failure(provider_id=_SEC_FUNDAMENTALS_ID, kind="MalformedProviderResponse")
        assert result is ProviderFailureClassification.TRANSIENT

    def test_empty_kind_defaults_to_transient(self):
        """A `ProviderFailure` built before `kind` existed (`""`) --
        the safe default: retry rather than silently give up on old
        data."""
        result = classify_provider_failure(provider_id=_SEC_FUNDAMENTALS_ID, kind="")
        assert result is ProviderFailureClassification.TRANSIENT


class TestAssessEnrichmentCompletion:
    def test_no_records_no_failures_is_not_yet_attempted_for_both(self):
        completion = assess_enrichment_completion("XYZ", ())
        assert completion.status_for(SourceKind.COMPANY_PROFILE) is ProviderCompletionStatus.NOT_YET_ATTEMPTED
        assert completion.status_for(SourceKind.FINANCIAL_STATEMENT) is ProviderCompletionStatus.NOT_YET_ATTEMPTED
        assert completion.is_fully_complete is False
        assert completion.has_retryable_work is True

    def test_both_records_present_is_fully_complete(self):
        completion = assess_enrichment_completion("XYZ", (_profile_record(), _statement_record()))
        assert completion.status_for(SourceKind.COMPANY_PROFILE) is ProviderCompletionStatus.SUCCEEDED
        assert completion.status_for(SourceKind.FINANCIAL_STATEMENT) is ProviderCompletionStatus.SUCCEEDED
        assert completion.is_fully_complete is True
        assert completion.has_retryable_work is False

    def test_sec_only_remains_eligible_for_alpha_vantage(self):
        """A ticker with only SEC data must remain eligible for the
        missing Alpha Vantage work -- Requirement 5."""
        completion = assess_enrichment_completion("XYZ", (_statement_record(),))
        assert completion.status_for(SourceKind.FINANCIAL_STATEMENT) is ProviderCompletionStatus.SUCCEEDED
        assert completion.status_for(SourceKind.COMPANY_PROFILE) is ProviderCompletionStatus.NOT_YET_ATTEMPTED
        assert completion.is_fully_complete is False
        assert completion.has_retryable_work is True

    def test_alpha_vantage_only_remains_eligible_for_sec(self):
        """A ticker with only Alpha Vantage data must remain eligible
        for the missing fundamentals work -- Requirement 6."""
        completion = assess_enrichment_completion("XYZ", (_profile_record(),))
        assert completion.status_for(SourceKind.COMPANY_PROFILE) is ProviderCompletionStatus.SUCCEEDED
        assert completion.status_for(SourceKind.FINANCIAL_STATEMENT) is ProviderCompletionStatus.NOT_YET_ATTEMPTED
        assert completion.is_fully_complete is False
        assert completion.has_retryable_work is True

    def test_known_transient_sec_failure_remains_retryable(self):
        failures = (ProviderFailure(provider_id=_SEC_FUNDAMENTALS_ID, error="SEC EDGAR unavailable", kind="ProviderUnavailable"),)
        completion = assess_enrichment_completion("XYZ", (_profile_record(),), failures)
        assert completion.status_for(SourceKind.FINANCIAL_STATEMENT) is ProviderCompletionStatus.FAILED_TRANSIENT
        assert completion.has_retryable_work is True

    def test_known_unsupported_sec_failure_is_not_retryable(self):
        """Requirement 8: a provider genuinely unsupported/not-
        applicable is not retried as though it were a transient
        failure."""
        failures = (ProviderFailure(provider_id=_SEC_FUNDAMENTALS_ID, error="not an SEC filer", kind="CompanyNotFound"),)
        completion = assess_enrichment_completion("XYZ", (_profile_record(),), failures)
        assert completion.status_for(SourceKind.FINANCIAL_STATEMENT) is ProviderCompletionStatus.FAILED_UNSUPPORTED
        assert completion.is_fully_complete is False  # honestly incomplete, not silently treated as done
        assert completion.has_retryable_work is False  # but nothing left worth retrying

    def test_known_transient_alpha_vantage_failure_remains_retryable(self):
        failures = (
            ProviderFailure(
                provider_id=_ALPHA_VANTAGE_PROFILE_ID,
                error="ALPHA_VANTAGE_API_KEY is not set.",
                kind="MissingRequiredField",
            ),
        )
        completion = assess_enrichment_completion("XYZ", (), failures)
        assert completion.status_for(SourceKind.COMPANY_PROFILE) is ProviderCompletionStatus.FAILED_TRANSIENT
        assert completion.has_retryable_work is True

    def test_a_real_record_outranks_a_stale_recorded_failure(self):
        """A later, out-of-band success (e.g. a manual CLI run) must
        never be shadowed by a stale prior failure for the same
        provider."""
        failures = (ProviderFailure(provider_id=_SEC_FUNDAMENTALS_ID, error="stale", kind="CompanyNotFound"),)
        completion = assess_enrichment_completion("XYZ", (_statement_record(),), failures)
        assert completion.status_for(SourceKind.FINANCIAL_STATEMENT) is ProviderCompletionStatus.SUCCEEDED

    def test_every_required_provider_is_always_named(self):
        completion = assess_enrichment_completion("XYZ", ())
        document_kinds = {p.document_kind for p in completion.providers}
        assert document_kinds == {SourceKind.COMPANY_PROFILE, SourceKind.FINANCIAL_STATEMENT}
