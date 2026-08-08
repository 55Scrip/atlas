"""Tests for `atlas.analysis_engine.business_data.models` (ATLAS-022
Phase 3/8) -- immutability, contract guards, and structural-only
content."""
from __future__ import annotations

import dataclasses

from atlas.analysis_engine.business_data.exceptions import BusinessDataContractError
from atlas.analysis_engine.business_data.contracts import ValidationStatus
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.models import BusinessRecord
from tests.unit.analysis_engine.business_data._fixtures import EVALUATED_AT, build_raw_document


def _ingested_record():
    result = ingest(build_raw_document(), evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestImmutability:
    def test_business_record_is_frozen(self):
        record = _ingested_record()
        try:
            record.company = "Someone Else"
            assert False, "expected FrozenInstanceError"
        except dataclasses.FrozenInstanceError:
            pass

    def test_raw_business_document_is_frozen(self):
        document = build_raw_document()
        try:
            document.identifier = "changed"
            assert False, "expected FrozenInstanceError"
        except dataclasses.FrozenInstanceError:
            pass

    def test_record_version_is_frozen(self):
        record = _ingested_record()
        try:
            record.version.version_number = 99
            assert False, "expected FrozenInstanceError"
        except dataclasses.FrozenInstanceError:
            pass

    def test_metadata_mapping_cannot_be_mutated(self):
        document = build_raw_document(metadata={"fiscal_year": 2025})
        try:
            document.metadata["fiscal_year"] = 2026
            assert False, "expected TypeError from an immutable mapping"
        except TypeError:
            pass


class TestBusinessRecordContract:
    def test_rejects_construction_with_a_non_valid_validation_status(self):
        record = _ingested_record()
        try:
            BusinessRecord(**{**record.__dict__, "validation_status": ValidationStatus.REJECTED})
            assert False, "expected BusinessDataContractError"
        except BusinessDataContractError:
            pass


class TestNoParsedFinancialFieldsExist:
    def test_no_metric_style_fields_on_business_record(self):
        """Phase 3's own hard constraint: never a parsed financial
        metric, never a conclusion. Enumerate the real field set and
        confirm none of the forbidden names crept in."""
        field_names = {f.name for f in dataclasses.fields(BusinessRecord)}
        forbidden = {
            "revenue",
            "eps",
            "margin",
            "valuation",
            "recommendation",
            "conclusion",
            "summary",
            "score",
        }
        assert field_names.isdisjoint(forbidden)


class TestDeterminism:
    def test_same_normalized_inputs_produce_deeply_equal_records(self):
        document = build_raw_document()
        first = ingest(document, evaluated_at=EVALUATED_AT)
        second = ingest(document, evaluated_at=EVALUATED_AT)
        assert first.record == second.record
