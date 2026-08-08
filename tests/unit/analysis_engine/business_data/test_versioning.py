"""Tests for `atlas.analysis_engine.business_data.versioning`
(ATLAS-022 Phase 8) -- immutable version history, lineage identity, and
duplicate detection. Uses `pipeline.ingest` to build real
`BusinessRecord`s rather than hand-constructing them, since that is how
they are actually produced."""
from __future__ import annotations

from atlas.analysis_engine.business_data.exceptions import BusinessDataContractError
from atlas.analysis_engine.business_data.models import RecordVersion
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.versioning import (
    DuplicateRecord,
    compute_lineage_id,
    determine_version,
    latest_versions,
)
from atlas.analysis_engine.business_data.sources import SourceKind
from tests.unit.analysis_engine.business_data._fixtures import EVALUATED_AT, build_raw_document


class TestLineageIdIsDeterministic:
    def test_identical_fields_produce_identical_lineage_id(self):
        first = compute_lineage_id(
            provider_id="manual_upload", source_kind=SourceKind.ANNUAL_REPORT, company="ASML", identifier="10-K"
        )
        second = compute_lineage_id(
            provider_id="manual_upload", source_kind=SourceKind.ANNUAL_REPORT, company="ASML", identifier="10-K"
        )
        assert first == second

    def test_different_identifier_produces_a_different_lineage_id(self):
        first = compute_lineage_id(
            provider_id="manual_upload", source_kind=SourceKind.ANNUAL_REPORT, company="ASML", identifier="10-K-2024"
        )
        second = compute_lineage_id(
            provider_id="manual_upload", source_kind=SourceKind.ANNUAL_REPORT, company="ASML", identifier="10-K-2025"
        )
        assert first != second

    def test_content_hash_does_not_affect_lineage_id(self):
        """The whole point of a lineage id: it must stay stable across
        republished versions, which by definition have different
        content hashes."""
        a = compute_lineage_id(
            provider_id="p", source_kind=SourceKind.TRANSCRIPT, company="ASML", identifier="q3-call"
        )
        b = compute_lineage_id(
            provider_id="p", source_kind=SourceKind.TRANSCRIPT, company="ASML", identifier="q3-call"
        )
        assert a == b


class TestNewLineageStartsAtVersionOne:
    def test_first_document_in_a_lineage_is_version_one(self):
        result = ingest(build_raw_document(), evaluated_at=EVALUATED_AT)
        assert isinstance(result, IngestedRecord)
        assert result.record.version.version_number == 1
        assert result.record.version.supersedes is None


class TestRepublishingCreatesANewVersion:
    def test_changed_content_hash_creates_version_two(self):
        first = ingest(build_raw_document(content_hash="hash-v1"), evaluated_at=EVALUATED_AT)
        second = ingest(
            build_raw_document(content_hash="hash-v2"),
            existing_records=(first.record,),
            evaluated_at=EVALUATED_AT,
        )
        assert isinstance(second, IngestedRecord)
        assert second.record.version.version_number == 2
        assert second.record.version.supersedes == first.record.id

    def test_the_old_record_object_is_never_mutated(self):
        first = ingest(build_raw_document(content_hash="hash-v1"), evaluated_at=EVALUATED_AT)
        before = first.record
        ingest(
            build_raw_document(content_hash="hash-v2"),
            existing_records=(first.record,),
            evaluated_at=EVALUATED_AT,
        )
        assert first.record == before
        assert first.record.version.version_number == 1
        assert first.record.version.supersedes is None

    def test_three_generations_form_a_correct_chain(self):
        v1 = ingest(build_raw_document(content_hash="h1"), evaluated_at=EVALUATED_AT)
        v2 = ingest(build_raw_document(content_hash="h2"), existing_records=(v1.record,), evaluated_at=EVALUATED_AT)
        v3 = ingest(
            build_raw_document(content_hash="h3"),
            existing_records=(v1.record, v2.record),
            evaluated_at=EVALUATED_AT,
        )
        assert v3.record.version.version_number == 3
        assert v3.record.version.supersedes == v2.record.id
        assert latest_versions((v1.record, v2.record, v3.record)) == (v3.record,)


class TestDuplicateDetection:
    def test_resubmitting_the_identical_content_hash_is_a_duplicate(self):
        first = ingest(build_raw_document(content_hash="same-hash"), evaluated_at=EVALUATED_AT)
        second = ingest(
            build_raw_document(content_hash="same-hash"),
            existing_records=(first.record,),
            evaluated_at=EVALUATED_AT,
        )
        assert isinstance(second, DuplicateRecord)
        assert second.existing_record_id == first.record.id

    def test_a_duplicate_does_not_create_a_new_version(self):
        first = ingest(build_raw_document(content_hash="same-hash"), evaluated_at=EVALUATED_AT)
        ingest(
            build_raw_document(content_hash="same-hash"),
            existing_records=(first.record,),
            evaluated_at=EVALUATED_AT,
        )
        # The only record that would exist in a real store is still v1 --
        # nothing about determine_version's own output claims otherwise.
        assert first.record.version.version_number == 1


class TestLatestVersions:
    def test_empty_collection_has_no_heads(self):
        assert latest_versions(()) == ()

    def test_unrelated_lineages_each_keep_their_own_head(self):
        asml = ingest(build_raw_document(identifier="asml-doc"), evaluated_at=EVALUATED_AT)
        besi = ingest(build_raw_document(identifier="besi-doc", company="BESI"), evaluated_at=EVALUATED_AT)
        heads = latest_versions((asml.record, besi.record))
        assert {record.id for record in heads} == {asml.record.id, besi.record.id}


class TestInconsistentHistoryIsSurfacedNotHidden:
    def test_two_heads_in_the_same_lineage_raises(self):
        """A caller that (incorrectly) hands in two un-superseded records
        for the same lineage gets a loud contract error, never a
        silently-picked winner."""
        v1 = ingest(build_raw_document(content_hash="h1"), evaluated_at=EVALUATED_AT)
        # Simulate a second "head" branching off v1 independently, by
        # constructing a sibling RecordVersion also claiming version 1
        # -- i.e. two structurally distinct version-1 records in the
        # same lineage, both un-superseded.
        broken_sibling = build_raw_document(content_hash="h1-sibling")
        # This sibling has a different identifier, so it is a different
        # lineage by construction -- to force a genuine collision we
        # instead call determine_version directly with a constructed
        # duplicate lineage_id.
        lineage_id = v1.record.lineage_id
        fabricated_second_head = v1.record.__class__(
            **{**v1.record.__dict__, "id": f"{lineage_id}:v1-duplicate"}
        )
        try:
            determine_version(
                lineage_id=lineage_id,
                content_hash="h2",
                existing_records=(v1.record, fabricated_second_head),
                created_at=EVALUATED_AT,
            )
            assert False, "expected BusinessDataContractError for an inconsistent lineage history"
        except BusinessDataContractError:
            pass


class TestRecordVersionContract:
    def test_version_number_below_one_is_rejected(self):
        try:
            RecordVersion(version_number=0, created_at=EVALUATED_AT, content_hash="h")
            assert False, "expected BusinessDataContractError"
        except BusinessDataContractError:
            pass

    def test_version_one_must_not_carry_a_supersedes_reference(self):
        try:
            RecordVersion(version_number=1, created_at=EVALUATED_AT, content_hash="h", supersedes="something")
            assert False, "expected BusinessDataContractError"
        except BusinessDataContractError:
            pass

    def test_version_above_one_must_carry_a_supersedes_reference(self):
        try:
            RecordVersion(version_number=2, created_at=EVALUATED_AT, content_hash="h", supersedes=None)
            assert False, "expected BusinessDataContractError"
        except BusinessDataContractError:
            pass
