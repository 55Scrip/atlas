"""Tests for `atlas.analysis_engine.valuation.facts` (ATLAS-024 Phase
4/5) -- market-data extraction, and the boundary that keeps it separate
from `business_facts`."""
from __future__ import annotations

from datetime import date

from atlas.analysis_engine.valuation.facts import (
    ValuationFactKind,
    extract_valuation_facts,
    extract_valuation_facts_from_records,
)
from tests.unit.analysis_engine.valuation._fixtures import EVALUATED_AT, fundamentals_record, market_record


class TestBasicExtraction:
    def test_a_market_snapshot_produces_facts(self):
        record = market_record(period_end=date(2024, 12, 31), identifier="m1", share_price=50.0, shares_outstanding=100.0)
        facts = extract_valuation_facts(record, evaluated_at=EVALUATED_AT)
        assert len(facts) == 2
        assert {f.kind for f in facts} == {ValuationFactKind.SHARE_PRICE, ValuationFactKind.SHARES_OUTSTANDING}

    def test_share_price_value_is_correct(self):
        record = market_record(period_end=date(2024, 12, 31), identifier="m1", share_price=53.5, shares_outstanding=100.0)
        facts = extract_valuation_facts(record, evaluated_at=EVALUATED_AT)
        price = next(f for f in facts if f.kind is ValuationFactKind.SHARE_PRICE)
        assert price.value == 53.5


class TestMarketDataBoundary:
    def test_a_fundamentals_record_never_produces_valuation_facts(self):
        """Phase 5's own boundary: even if an annual report's metadata
        happened to contain a 'share_price' key, this module must not
        treat it as authoritative market data."""
        record = fundamentals_record(
            period_end=date(2024, 12, 31), identifier="f1", share_price=999.0, shares_outstanding=100.0
        )
        assert extract_valuation_facts(record, evaluated_at=EVALUATED_AT) == ()

    def test_only_market_data_snapshot_document_type_is_read(self):
        record = market_record(period_end=date(2024, 12, 31), identifier="m1", share_price=50.0)
        facts = extract_valuation_facts(record, evaluated_at=EVALUATED_AT)
        assert len(facts) == 1
        assert facts[0].kind is ValuationFactKind.SHARE_PRICE


class TestTypeSafetyAndPeriod:
    def test_bool_value_is_excluded(self):
        record = market_record(period_end=date(2024, 12, 31), identifier="m1", share_price=True)
        assert extract_valuation_facts(record, evaluated_at=EVALUATED_AT) == ()

    def test_no_period_means_no_facts(self):
        document_kwargs = dict(identifier="m1", company="ASML", metadata={"share_price": 50.0})
        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        document = RawBusinessDocument(
            source_kind="market_data_snapshot",
            published_at=EVALUATED_AT,
            provider_id="p",
            raw_reference="r1",
            content_hash="h1",
            language="en",
            period_end=None,
            period_start=None,
            **document_kwargs,
        )
        result = ingest(document, evaluated_at=EVALUATED_AT)
        assert isinstance(result, IngestedRecord)
        assert extract_valuation_facts(result.record, evaluated_at=EVALUATED_AT) == ()


class TestExtractValuationFactsFromRecords:
    def test_conflicting_facts_are_excluded(self):
        r1 = market_record(period_end=date(2024, 12, 31), identifier="m1", share_price=50.0)
        r2 = market_record(period_end=date(2024, 12, 31), identifier="m2", share_price=60.0)
        facts = extract_valuation_facts_from_records((r1, r2), evaluated_at=EVALUATED_AT)
        assert facts == ()

    def test_multiple_periods_flat_map_correctly(self):
        r1 = market_record(period_end=date(2023, 12, 31), identifier="m1", share_price=40.0)
        r2 = market_record(period_end=date(2024, 12, 31), identifier="m2", share_price=50.0)
        facts = extract_valuation_facts_from_records((r1, r2), evaluated_at=EVALUATED_AT)
        assert {f.period for f in facts} == {"2023-12-31", "2024-12-31"}


class TestNoConfidenceField:
    def test_valuation_fact_has_no_confidence_field(self):
        import dataclasses

        record = market_record(period_end=date(2024, 12, 31), identifier="m1", share_price=50.0)
        facts = extract_valuation_facts(record, evaluated_at=EVALUATED_AT)
        field_names = {f.name for f in dataclasses.fields(facts[0])}
        assert "confidence" not in field_names


class TestDeterminism:
    def test_identical_record_produces_identical_facts(self):
        record = market_record(period_end=date(2024, 12, 31), identifier="m1", share_price=50.0)
        assert extract_valuation_facts(record, evaluated_at=EVALUATED_AT) == extract_valuation_facts(
            record, evaluated_at=EVALUATED_AT
        )
