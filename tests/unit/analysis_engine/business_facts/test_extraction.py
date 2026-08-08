"""Tests for `atlas.analysis_engine.business_facts.extraction`
(ATLAS-023 Phase 4) -- deterministic key lookup only, no LLM, no NLP,
never a fact from document presence alone."""
from __future__ import annotations

from datetime import date

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.extraction import extract_facts, extract_facts_from_records
from tests.unit.analysis_engine.business_facts._fixtures import EVALUATED_AT, build_record


class TestBasicExtraction:
    def test_a_known_key_produces_a_fact(self):
        record = build_record(metadata={"revenue": 1000.0})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert len(facts) == 1
        assert facts[0].kind is BusinessFactKind.REVENUE
        assert facts[0].value == 1000.0

    def test_an_unknown_key_produces_no_fact(self):
        record = build_record(metadata={"employee_count": 5000})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts == ()

    def test_multiple_known_keys_produce_multiple_facts(self):
        record = build_record(metadata={"revenue": 1000.0, "capital_expenditure": 50.0})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert {f.kind for f in facts} == {BusinessFactKind.REVENUE, BusinessFactKind.CAPITAL_EXPENDITURE}

    def test_a_document_with_no_metadata_produces_no_facts(self):
        record = build_record(metadata={})
        assert extract_facts(record, evaluated_at=EVALUATED_AT) == ()

    def test_document_presence_alone_is_never_evidence(self):
        """A report existing is not evidence that anything is strong --
        confirmed directly: an otherwise-empty, validly-ingested record
        produces zero facts."""
        record = build_record(metadata={})
        assert extract_facts(record, evaluated_at=EVALUATED_AT) == ()


class TestTypeSafety:
    def test_string_value_produces_no_fact(self):
        record = build_record(metadata={"revenue": "one thousand"})
        assert extract_facts(record, evaluated_at=EVALUATED_AT) == ()

    def test_none_value_produces_no_fact(self):
        record = build_record(metadata={"revenue": None})
        assert extract_facts(record, evaluated_at=EVALUATED_AT) == ()

    def test_bool_value_is_not_silently_treated_as_zero_or_one(self):
        """Python's int/bool subtyping is a real footgun here --
        confirmed explicitly excluded."""
        record = build_record(metadata={"revenue": True})
        assert extract_facts(record, evaluated_at=EVALUATED_AT) == ()

    def test_integer_value_is_accepted(self):
        record = build_record(metadata={"revenue": 1000})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts[0].value == 1000.0
        assert isinstance(facts[0].value, float)


class TestPeriodRequirement:
    def test_no_period_on_the_record_means_no_facts_at_all(self):
        record = build_record(period_end=None, period_start=None, metadata={"revenue": 1000.0})
        assert extract_facts(record, evaluated_at=EVALUATED_AT) == ()

    def test_period_start_is_used_when_no_period_end(self):
        record = build_record(period_end=None, period_start=date(2024, 1, 1), metadata={"revenue": 1000.0})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts[0].period == "2024-01-01"

    def test_period_end_is_preferred_over_period_start(self):
        record = build_record(
            period_end=date(2024, 12, 31), period_start=date(2024, 1, 1), metadata={"revenue": 1000.0}
        )
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts[0].period == "2024-12-31"


class TestUnit:
    def test_currency_metadata_key_becomes_the_unit(self):
        record = build_record(metadata={"revenue": 1000.0, "currency": "eur"})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts[0].unit == "eur"

    def test_missing_currency_is_an_honest_unspecified_value_not_a_guess(self):
        record = build_record(metadata={"revenue": 1000.0})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts[0].unit == "unspecified"


class TestProvenance:
    def test_fact_provenance_references_the_source_record(self):
        record = build_record(metadata={"revenue": 1000.0})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts[0].source_record_id == record.id
        assert record.id in facts[0].provenance.dependencies
        assert record.source_reference in facts[0].provenance.source_references


class TestExtractFactsFromRecords:
    def test_flat_maps_across_multiple_records(self):
        r1 = build_record(identifier="fy2023", period_end=date(2023, 12, 31), metadata={"revenue": 900.0})
        r2 = build_record(identifier="fy2024", period_end=date(2024, 12, 31), metadata={"revenue": 1000.0})
        facts = extract_facts_from_records((r1, r2), evaluated_at=EVALUATED_AT)
        assert len(facts) == 2
        assert {f.period for f in facts} == {"2023-12-31", "2024-12-31"}

    def test_conflicting_facts_for_the_same_period_are_excluded(self):
        """Two records disagreeing on the same (company, kind, period)
        -- neither is guessed as authoritative; both are dropped."""
        r1 = build_record(identifier="a", period_end=date(2024, 12, 31), metadata={"revenue": 1000.0})
        r2 = build_record(identifier="b", period_end=date(2024, 12, 31), metadata={"revenue": 1100.0})
        facts = extract_facts_from_records((r1, r2), evaluated_at=EVALUATED_AT)
        assert facts == ()

    def test_identical_duplicate_values_are_kept_once(self):
        r1 = build_record(identifier="a", period_end=date(2024, 12, 31), metadata={"revenue": 1000.0})
        r2 = build_record(identifier="b", period_end=date(2024, 12, 31), metadata={"revenue": 1000.0})
        facts = extract_facts_from_records((r1, r2), evaluated_at=EVALUATED_AT)
        assert len(facts) == 1
        assert facts[0].value == 1000.0

    def test_empty_input_produces_no_facts(self):
        assert extract_facts_from_records((), evaluated_at=EVALUATED_AT) == ()


class TestDeterminism:
    def test_identical_record_produces_a_deeply_equal_result(self):
        record = build_record(metadata={"revenue": 1000.0})
        assert extract_facts(record, evaluated_at=EVALUATED_AT) == extract_facts(record, evaluated_at=EVALUATED_AT)
