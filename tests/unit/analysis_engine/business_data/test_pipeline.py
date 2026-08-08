"""Tests for `atlas.analysis_engine.business_data.pipeline.ingest`
(ATLAS-022 Phase 6) -- the full orchestration: validation, then
normalization, then versioning, end to end."""
from __future__ import annotations

from atlas.analysis_engine.business_data.contracts import ValidationStatus
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, IngestionRejected, ingest
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_data.validation import ValidationFailureReason
from atlas.analysis_engine.business_data.versioning import DuplicateRecord
from atlas.analysis_engine.provenance import SourceKind as ProvenanceSourceKind
from atlas.analysis_engine.provenance import UpdateTrigger
from tests.unit.analysis_engine.business_data._fixtures import EVALUATED_AT, build_raw_document


class TestSuccessfulIngestion:
    def test_valid_document_produces_an_ingested_record(self):
        result = ingest(build_raw_document(), evaluated_at=EVALUATED_AT)
        assert isinstance(result, IngestedRecord)

    def test_record_carries_the_normalized_fields(self):
        result = ingest(build_raw_document(identifier="  10-K  ", company="  ASML  "), evaluated_at=EVALUATED_AT)
        assert result.record.identifier == "10-K"
        assert result.record.company == "ASML"

    def test_record_document_type_is_a_real_source_kind(self):
        result = ingest(build_raw_document(source_kind="transcript"), evaluated_at=EVALUATED_AT)
        assert result.record.document_type is SourceKind.TRANSCRIPT

    def test_record_validation_status_is_always_valid(self):
        result = ingest(build_raw_document(), evaluated_at=EVALUATED_AT)
        assert result.record.validation_status is ValidationStatus.VALID

    def test_record_provenance_uses_external_data_source(self):
        """The first real construction anywhere in the repository of
        `SourceKind.EXTERNAL_DATA_SOURCE` -- reserved since ATLAS-020,
        unconstructed until this sprint."""
        result = ingest(build_raw_document(), evaluated_at=EVALUATED_AT)
        assert result.record.provenance.source_kind is ProvenanceSourceKind.EXTERNAL_DATA_SOURCE
        assert result.record.provenance.update_trigger is UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED

    def test_record_id_is_deterministic(self):
        first = ingest(build_raw_document(), evaluated_at=EVALUATED_AT)
        second_doc = build_raw_document()
        second = ingest(second_doc, evaluated_at=EVALUATED_AT)
        assert first.record.id == second.record.id


class TestRejection:
    def test_invalid_document_produces_a_rejection_not_a_record(self):
        result = ingest(build_raw_document(identifier=None), evaluated_at=EVALUATED_AT)
        assert isinstance(result, IngestionRejected)
        assert ValidationFailureReason.MISSING_IDENTIFIER in result.reasons

    def test_rejected_document_never_reaches_normalization_or_versioning(self):
        """No BusinessRecord is constructed at all for a rejected
        document -- proven by the result simply not being an
        IngestedRecord, which is the only way a BusinessRecord could
        have been returned."""
        result = ingest(build_raw_document(content_hash=None), evaluated_at=EVALUATED_AT)
        assert not hasattr(result, "record")


class TestDuplicateDetectionThroughThePipeline:
    def test_resubmitting_unchanged_content_is_a_duplicate_not_a_new_version(self):
        first = ingest(build_raw_document(content_hash="stable-hash"), evaluated_at=EVALUATED_AT)
        second = ingest(
            build_raw_document(content_hash="stable-hash"),
            existing_records=(first.record,),
            evaluated_at=EVALUATED_AT,
        )
        assert isinstance(second, DuplicateRecord)


class TestUnsupportedSourceTypes:
    def test_unrecognized_source_kind_is_rejected(self):
        result = ingest(build_raw_document(source_kind="press_conference"), evaluated_at=EVALUATED_AT)
        assert isinstance(result, IngestionRejected)
        assert ValidationFailureReason.UNRECOGNIZED_SOURCE_KIND in result.reasons

    def test_explicit_unknown_source_kind_flows_through_successfully(self):
        """UNKNOWN is a real, honest classification a provider may
        choose -- never itself a rejection reason."""
        result = ingest(build_raw_document(source_kind="unknown"), evaluated_at=EVALUATED_AT)
        assert isinstance(result, IngestedRecord)
        assert result.record.document_type is SourceKind.UNKNOWN


class TestNoWallClock:
    def test_evaluated_at_is_the_only_timestamp_source(self):
        result = ingest(build_raw_document(), evaluated_at=EVALUATED_AT)
        assert result.record.version.created_at == EVALUATED_AT
        assert result.record.provenance.computed_at == EVALUATED_AT


class TestDeterminism:
    def test_identical_document_and_history_produce_a_deeply_equal_result(self):
        document = build_raw_document()
        first = ingest(document, evaluated_at=EVALUATED_AT)
        second = ingest(document, evaluated_at=EVALUATED_AT)
        assert first == second
