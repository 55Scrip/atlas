"""Tests for `atlas.analysis_engine.business_data.validation`
(ATLAS-022 Phase 7) -- every required field, collected failures (not
first-match), and the "never silently repair" guarantee."""
from __future__ import annotations

from atlas.analysis_engine.business_data.validation import (
    ValidationFailureReason,
    validate_raw_document,
)
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document


class TestValidDocumentPasses:
    def test_a_fully_populated_document_has_no_failures(self):
        assert validate_raw_document(build_raw_document()) == ()


class TestEachRequiredFieldIsChecked:
    def test_missing_identifier(self):
        reasons = validate_raw_document(build_raw_document(identifier=None))
        assert ValidationFailureReason.MISSING_IDENTIFIER in reasons

    def test_blank_identifier_is_also_missing(self):
        reasons = validate_raw_document(build_raw_document(identifier="   "))
        assert ValidationFailureReason.MISSING_IDENTIFIER in reasons

    def test_missing_company(self):
        reasons = validate_raw_document(build_raw_document(company=None))
        assert ValidationFailureReason.MISSING_COMPANY in reasons

    def test_missing_provider(self):
        reasons = validate_raw_document(build_raw_document(provider_id=None))
        assert ValidationFailureReason.MISSING_PROVIDER in reasons

    def test_missing_source_kind(self):
        reasons = validate_raw_document(build_raw_document(source_kind=None))
        assert ValidationFailureReason.MISSING_SOURCE_KIND in reasons

    def test_unrecognized_source_kind_is_rejected_not_coerced_to_unknown(self):
        reasons = validate_raw_document(build_raw_document(source_kind="blog_post"))
        assert reasons == (ValidationFailureReason.UNRECOGNIZED_SOURCE_KIND,)

    def test_explicit_unknown_source_kind_is_valid(self):
        assert validate_raw_document(build_raw_document(source_kind="unknown")) == ()

    def test_missing_publication_date(self):
        reasons = validate_raw_document(build_raw_document(published_at=None))
        assert ValidationFailureReason.MISSING_PUBLICATION_DATE in reasons

    def test_missing_raw_reference(self):
        reasons = validate_raw_document(build_raw_document(raw_reference=None))
        assert ValidationFailureReason.MISSING_RAW_REFERENCE in reasons

    def test_missing_content_hash(self):
        reasons = validate_raw_document(build_raw_document(content_hash=None))
        assert ValidationFailureReason.MISSING_CONTENT_HASH in reasons

    def test_missing_language(self):
        reasons = validate_raw_document(build_raw_document(language=None))
        assert ValidationFailureReason.MISSING_LANGUAGE in reasons


class TestAllFailuresAreCollectedNotJustTheFirst:
    def test_completely_empty_document_reports_every_reason(self):
        empty = build_raw_document(
            identifier=None,
            company=None,
            source_kind=None,
            published_at=None,
            provider_id=None,
            raw_reference=None,
            content_hash=None,
            language=None,
        )
        reasons = validate_raw_document(empty)
        assert set(reasons) == {
            ValidationFailureReason.MISSING_IDENTIFIER,
            ValidationFailureReason.MISSING_COMPANY,
            ValidationFailureReason.MISSING_PROVIDER,
            ValidationFailureReason.MISSING_SOURCE_KIND,
            ValidationFailureReason.MISSING_PUBLICATION_DATE,
            ValidationFailureReason.MISSING_RAW_REFERENCE,
            ValidationFailureReason.MISSING_CONTENT_HASH,
            ValidationFailureReason.MISSING_LANGUAGE,
        }


class TestNeverSilentlyRepairs:
    def test_missing_language_is_rejected_not_defaulted(self):
        """Validation must never invent 'en' for a missing language --
        confirmed by checking the reason is reported, not silently
        absorbed."""
        reasons = validate_raw_document(build_raw_document(language=None))
        assert ValidationFailureReason.MISSING_LANGUAGE in reasons


class TestDeterminism:
    def test_identical_input_produces_identical_output(self):
        document = build_raw_document(identifier=None)
        assert validate_raw_document(document) == validate_raw_document(document)
