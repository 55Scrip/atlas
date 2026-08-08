"""Tests for `atlas.analysis_engine.business_facts.models.BusinessFact`
(ATLAS-023 Phase 2) -- immutability and the deliberate absence of a
`confidence` field."""
from __future__ import annotations

import dataclasses

from atlas.analysis_engine.business_facts.extraction import extract_facts
from tests.unit.analysis_engine.business_facts._fixtures import EVALUATED_AT, build_record


class TestImmutability:
    def test_business_fact_is_frozen(self):
        record = build_record(metadata={"revenue": 1000})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts
        try:
            facts[0].value = 999.0
            assert False, "expected FrozenInstanceError"
        except dataclasses.FrozenInstanceError:
            pass


class TestNoConfidenceField:
    def test_business_fact_has_no_confidence_field(self):
        """Phase 9's own audit point: EvidenceCoverageLevel's
        collection-coverage semantics do not fit one atomic fact --
        confidence lives on BusinessFinding instead (see growth.py/
        capital_allocation.py)."""
        record = build_record(metadata={"revenue": 1000})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        field_names = {f.name for f in dataclasses.fields(facts[0])}
        assert "confidence" not in field_names


class TestDeterministicId:
    def test_id_is_derived_from_source_record_kind_and_period(self):
        record = build_record(identifier="fy2024", metadata={"revenue": 1000})
        facts = extract_facts(record, evaluated_at=EVALUATED_AT)
        assert facts[0].id == f"{record.id}:revenue:2024-12-31"
