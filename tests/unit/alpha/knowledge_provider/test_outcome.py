"""Tests for `atlas.alpha.knowledge_provider.outcome.summarize_acquisition`
-- a pure classifier over hand-built `RefreshSummary` fixtures, mirroring
`atlas.alpha.ingestion.engine.classify_refresh`'s own test convention.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.business_data_refresh.models import ProviderFailure, RefreshSummary
from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_provider.outcome import (
    AcquisitionValidationStatus,
    ExtractionStatus,
    summarize_acquisition,
)

_NOW = datetime(2026, 8, 22, tzinfo=timezone.utc)


class _FakeProvider:
    provider_id = "fake_provider"
    supported_domains = (KnowledgeDomain.REGULATORY_FILINGS,)
    supported_source_kinds = ()


def _summary(**overrides) -> RefreshSummary:
    base = dict(
        ticker="AAPL",
        providers_attempted=("fake_provider",),
        fetched_documents=0,
        new_records=0,
        new_versions=0,
        duplicates_skipped=0,
        rejected_documents=0,
        provider_errors=(),
        evaluated_at=_NOW,
    )
    base.update(overrides)
    return RefreshSummary(**base)


class TestExtractionStatus:
    def test_new_records_with_no_errors_is_complete(self):
        outcome = summarize_acquisition(_FakeProvider(), _summary(fetched_documents=3, new_records=3), evaluated_at=_NOW)
        assert outcome.extraction_status is ExtractionStatus.COMPLETE

    def test_new_records_with_errors_is_partial(self):
        summary = _summary(
            fetched_documents=3, new_records=2, provider_errors=(ProviderFailure(provider_id="x", error="boom"),)
        )
        outcome = summarize_acquisition(_FakeProvider(), summary, evaluated_at=_NOW)
        assert outcome.extraction_status is ExtractionStatus.PARTIAL

    def test_no_new_records_with_errors_is_failed(self):
        summary = _summary(provider_errors=(ProviderFailure(provider_id="x", error="boom"),))
        outcome = summarize_acquisition(_FakeProvider(), summary, evaluated_at=_NOW)
        assert outcome.extraction_status is ExtractionStatus.FAILED

    def test_no_new_records_no_errors_is_no_data(self):
        outcome = summarize_acquisition(_FakeProvider(), _summary(), evaluated_at=_NOW)
        assert outcome.extraction_status is ExtractionStatus.NO_DATA


class TestValidationStatus:
    def test_nothing_fetched_is_not_applicable(self):
        outcome = summarize_acquisition(_FakeProvider(), _summary(fetched_documents=0), evaluated_at=_NOW)
        assert outcome.validation_status is AcquisitionValidationStatus.NOT_APPLICABLE

    def test_zero_rejected_is_all_valid(self):
        outcome = summarize_acquisition(
            _FakeProvider(), _summary(fetched_documents=3, rejected_documents=0), evaluated_at=_NOW
        )
        assert outcome.validation_status is AcquisitionValidationStatus.ALL_VALID

    def test_all_rejected_is_all_rejected(self):
        outcome = summarize_acquisition(
            _FakeProvider(), _summary(fetched_documents=3, rejected_documents=3), evaluated_at=_NOW
        )
        assert outcome.validation_status is AcquisitionValidationStatus.ALL_REJECTED

    def test_some_rejected_is_partially_valid(self):
        outcome = summarize_acquisition(
            _FakeProvider(), _summary(fetched_documents=3, rejected_documents=1), evaluated_at=_NOW
        )
        assert outcome.validation_status is AcquisitionValidationStatus.PARTIALLY_VALID


class TestFieldsReusedVerbatim:
    def test_collected_at_reuses_summary_evaluated_at(self):
        summary = _summary(evaluated_at=_NOW)
        outcome = summarize_acquisition(_FakeProvider(), summary, evaluated_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
        assert outcome.collected_at == _NOW

    def test_provider_id_and_domains_come_from_the_provider_not_the_summary(self):
        outcome = summarize_acquisition(_FakeProvider(), _summary(), evaluated_at=_NOW)
        assert outcome.provider_id == "fake_provider"
        assert outcome.supported_domains == (KnowledgeDomain.REGULATORY_FILINGS,)

    def test_confidence_is_none_for_every_provider_today(self):
        outcome = summarize_acquisition(_FakeProvider(), _summary(), evaluated_at=_NOW)
        assert outcome.confidence is None

    def test_errors_reuse_provider_failures_verbatim(self):
        summary = _summary(provider_errors=(ProviderFailure(provider_id="sec_edgar", error="timeout"),))
        outcome = summarize_acquisition(_FakeProvider(), summary, evaluated_at=_NOW)
        assert outcome.errors == ("sec_edgar: timeout",)

    def test_warnings_name_real_duplicate_and_rejected_counts(self):
        summary = _summary(fetched_documents=5, duplicates_skipped=2, rejected_documents=1)
        outcome = summarize_acquisition(_FakeProvider(), summary, evaluated_at=_NOW)
        assert "2 duplicate document(s) skipped" in outcome.warnings
        assert "1 document(s) rejected by validation" in outcome.warnings

    def test_no_warnings_when_nothing_skipped_or_rejected(self):
        outcome = summarize_acquisition(_FakeProvider(), _summary(fetched_documents=3), evaluated_at=_NOW)
        assert outcome.warnings == ()
