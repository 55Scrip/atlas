"""Tests for `atlas.alpha.ingestion.engine` -- `BusinessRecord`s are
real, built through the actual `atlas.analysis_engine.business_data
.pipeline.ingest` pipeline (never hand-faked), since this module's own
job is reclassifying that pipeline's already-real output, mirroring
`tests/unit/alpha/evidence_timeline/test_engine.py`'s own module
docstring convention.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.business_data_refresh.models import ProviderFailure, RefreshSummary
from atlas.alpha.ingestion.engine import DataFreshnessStatus, classify_refresh, derive_data_freshness_status
from atlas.alpha.ingestion.models import DataChangeKind, IngestionResult
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 8, 21, 13, 0, tzinfo=timezone.utc)
PREVIOUS = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _document(identifier: str, *, content: str, period_end: date) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=identifier,
        company="NVDA",
        source_kind="annual_report",
        published_at=NOW,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=content,
        language="en",
        period_end=period_end,
        metadata={"revenue": 1000.0},
    )


def _new_record(identifier: str = "doc-1"):
    result = ingest(_document(identifier, content="v1", period_end=date(2025, 12, 31)), evaluated_at=NOW)
    assert isinstance(result, IngestedRecord)
    return result.record


def _replaced_record(existing_record):
    result = ingest(
        _document("doc-1", content="v2", period_end=date(2025, 12, 31)),
        existing_records=(existing_record,),
        evaluated_at=LATER,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def _summary(*, changed_records=(), fetched_documents=0, duplicates_skipped=0, rejected_documents=0, evaluated_at=NOW) -> RefreshSummary:
    return RefreshSummary(
        ticker="NVDA",
        providers_attempted=("TestProvider",),
        fetched_documents=fetched_documents,
        new_records=sum(1 for r in changed_records if r.version.version_number == 1),
        new_versions=sum(1 for r in changed_records if r.version.version_number > 1),
        duplicates_skipped=duplicates_skipped,
        rejected_documents=rejected_documents,
        provider_errors=(),
        changed_records=changed_records,
        evaluated_at=evaluated_at,
    )


class TestClassifyRefresh:
    def test_a_brand_new_lineage_is_classified_as_new_dataset(self):
        record = _new_record()
        summary = _summary(changed_records=(record,), fetched_documents=1)
        result = classify_refresh(summary, ticker="NVDA", case_id="case-1", ran_at=NOW)
        assert len(result.changes) == 1
        assert result.changes[0].kind is DataChangeKind.NEW_DATASET
        assert result.changes[0].source_kind == "annual_report"
        assert result.has_new_data is True

    def test_a_second_version_of_a_known_lineage_is_classified_as_dataset_replaced(self):
        first = _new_record()
        second = _replaced_record(first)
        summary = _summary(changed_records=(second,), fetched_documents=1)
        result = classify_refresh(summary, ticker="NVDA", case_id="case-1", ran_at=LATER)
        assert result.changes[0].kind is DataChangeKind.DATASET_REPLACED

    def test_a_run_with_no_changed_records_reports_no_new_data(self):
        """Critical requirement: an unchanged/duplicate-only refresh
        must never fabricate a DataChange."""
        summary = _summary(changed_records=(), fetched_documents=1, duplicates_skipped=1)
        result = classify_refresh(summary, ticker="NVDA", case_id="case-1", ran_at=NOW)
        assert result.changes == ()
        assert result.has_new_data is False

    def test_a_run_that_fetched_nothing_at_all_is_distinguishable_from_an_unchanged_run(self):
        summary = _summary(changed_records=(), fetched_documents=0)
        result = classify_refresh(summary, ticker="NVDA", case_id="case-1", ran_at=NOW)
        assert result.fetched_documents == 0
        assert result.has_new_data is False

    def test_a_company_filing_record_from_the_foundation_provider_needs_no_new_handling(self):
        """Automatic Knowledge Ingestion Framework, Phase 2 ("Determine
        Impact") -- `classify_refresh` is provider-agnostic: a brand
        new `SourceKind.COMPANY_FILING` record classifies exactly like
        any other new lineage, zero new branches required."""
        document = RawBusinessDocument(
            identifier="AAPL:FILING:0001",
            company="AAPL",
            source_kind="company_filing",
            published_at=NOW,
            provider_id="sec_edgar_filings",
            raw_reference="ref://filing-0001",
            content_hash="filing-v1",
            language="en",
            metadata={"form_type": "10-K", "accession_number": "0001"},
        )
        result_record = ingest(document, evaluated_at=NOW)
        assert isinstance(result_record, IngestedRecord)
        summary = _summary(changed_records=(result_record.record,), fetched_documents=1)
        result = classify_refresh(summary, ticker="AAPL", case_id="case-1", ran_at=NOW)
        assert len(result.changes) == 1
        assert result.changes[0].kind is DataChangeKind.NEW_DATASET
        assert result.changes[0].source_kind == "company_filing"
        assert result.has_new_data is True

    def test_provider_errors_are_carried_through_as_readable_strings(self):
        summary = RefreshSummary(
            ticker="NVDA",
            providers_attempted=("TestProvider",),
            fetched_documents=0,
            new_records=0,
            new_versions=0,
            duplicates_skipped=0,
            rejected_documents=0,
            provider_errors=(ProviderFailure(provider_id="TestProvider", error="timeout"),),
            evaluated_at=NOW,
        )
        result = classify_refresh(summary, ticker="NVDA", case_id="case-1", ran_at=NOW)
        assert result.provider_errors == ("TestProvider: timeout",)

    def test_case_id_and_ran_at_are_carried_through_verbatim(self):
        summary = _summary()
        result = classify_refresh(summary, ticker="NVDA", case_id="case-42", ran_at=NOW)
        assert result.case_id == "case-42"
        assert result.ran_at == NOW
        assert result.ticker == "NVDA"


def _ingestion_result(*, has_new_data: bool, ran_at: datetime, fetched_documents: int = 1) -> IngestionResult:
    return IngestionResult(
        ticker="NVDA",
        case_id="case-1",
        ran_at=ran_at,
        changes=(),
        has_new_data=has_new_data,
        fetched_documents=fetched_documents,
        duplicates_skipped=0,
        rejected_documents=0,
        provider_errors=(),
        identity_gate_outcome="AUTO_ACCEPT",
    )


class TestDeriveDataFreshnessStatus:
    def test_a_monitoring_failure_always_wins(self):
        result = _ingestion_result(has_new_data=True, ran_at=LATER)
        status = derive_data_freshness_status(result, PREVIOUS, last_run_failed_for_case=True)
        assert status is DataFreshnessStatus.MONITORING_FAILED

    def test_nothing_known_at_all_is_unknown(self):
        status = derive_data_freshness_status(None, None, last_run_failed_for_case=False)
        assert status is DataFreshnessStatus.UNKNOWN

    def test_monitored_before_but_no_ingestion_record_falls_back_to_waiting_for_new_data(self):
        """Pre-Sprint-9 Case: Monitoring has a checkpoint, but Ingestion
        never ran for it -- an honest fallback, never "up to date."""
        status = derive_data_freshness_status(None, PREVIOUS, last_run_failed_for_case=False)
        assert status is DataFreshnessStatus.WAITING_FOR_NEW_DATA

    def test_ingestion_ran_and_found_zero_documents_is_no_data_source(self):
        result = _ingestion_result(has_new_data=False, ran_at=NOW, fetched_documents=0)
        status = derive_data_freshness_status(result, None, last_run_failed_for_case=False)
        assert status is DataFreshnessStatus.NO_DATA_SOURCE

    def test_ingestion_found_real_data_but_never_monitored_is_waiting_for_analysis(self):
        result = _ingestion_result(has_new_data=True, ran_at=NOW, fetched_documents=1)
        status = derive_data_freshness_status(result, None, last_run_failed_for_case=False)
        assert status is DataFreshnessStatus.WAITING_FOR_ANALYSIS

    def test_new_data_arrived_after_the_last_monitoring_checkpoint_is_waiting_for_analysis(self):
        result = _ingestion_result(has_new_data=True, ran_at=LATER)
        status = derive_data_freshness_status(result, PREVIOUS, last_run_failed_for_case=False)
        assert status is DataFreshnessStatus.WAITING_FOR_ANALYSIS

    def test_new_data_arrived_before_the_last_monitoring_checkpoint_is_waiting_for_new_data(self):
        """The monitoring checkpoint already covers this data -- Atlas
        is caught up, just honestly not calling itself "up to date." """
        result = _ingestion_result(has_new_data=True, ran_at=PREVIOUS)
        status = derive_data_freshness_status(result, LATER, last_run_failed_for_case=False)
        assert status is DataFreshnessStatus.WAITING_FOR_NEW_DATA

    def test_no_new_data_and_monitored_is_waiting_for_new_data(self):
        result = _ingestion_result(has_new_data=False, ran_at=PREVIOUS)
        status = derive_data_freshness_status(result, LATER, last_run_failed_for_case=False)
        assert status is DataFreshnessStatus.WAITING_FOR_NEW_DATA
