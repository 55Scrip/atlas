"""Tests for `atlas.analysis_engine.valuation.net_cash_proof` (`DE-015`
§15's Net-Cash proof path)."""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.analysis_engine.valuation.net_cash_proof import evaluate_net_cash_proof
from atlas.analysis_engine.valuation.proof import ProofVerdict
from tests.unit.analysis_engine.valuation._fixtures import fundamentals_record, market_record

_GENERATED_AT = datetime(2026, 8, 13, tzinfo=timezone.utc)


def _filed(year: int, month: int = 2, day: int = 15) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _records(*, cash: float | None, debt: float | None, price: float | None, shares: float | None, tag: str = "nc"):
    records = []
    if cash is not None:
        records.append(
            fundamentals_record(period_end=date(2024, 12, 31), identifier=f"{tag}cash", published_at=_filed(2025), cash=cash)
        )
    if debt is not None:
        records.append(
            fundamentals_record(period_end=date(2024, 12, 31), identifier=f"{tag}debt", published_at=_filed(2025), total_debt=debt)
        )
    if price is not None and shares is not None:
        records.append(
            market_record(period_end=date(2025, 3, 1), identifier=f"{tag}mkt", share_price=price, shares_outstanding=shares)
        )
    return tuple(records)


def _proof(*, cash, debt, price, shares, generated_at=_GENERATED_AT, tag="nc"):
    records = _records(cash=cash, debt=debt, price=price, shares=shares, tag=tag)
    business_facts = extract_facts_from_records(records, evaluated_at=generated_at)
    valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=generated_at)
    return evaluate_net_cash_proof(business_facts, valuation_facts, generated_at=generated_at)


class TestBelowNetCash:
    def test_establishes_support(self):
        # net_cash = 100 - 20 = 80; market_cap = 5 * 10 = 50 < 80
        proof = _proof(cash=100.0, debt=20.0, price=5.0, shares=10.0)
        assert proof.verdict is ProofVerdict.ESTABLISHES_SUPPORT
        assert "market_cap=50.00" in proof.evidence_summary
        assert "net_cash=80.00" in proof.evidence_summary


class TestEqualToNetCash:
    def test_does_not_establish(self):
        # net_cash = 100 - 20 = 80; market_cap = 8 * 10 = 80 == 80 -> not strictly below
        proof = _proof(cash=100.0, debt=20.0, price=8.0, shares=10.0)
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH


class TestAboveNetCash:
    def test_does_not_establish_never_non_support(self):
        # net_cash = 100 - 20 = 80; market_cap = 50 * 10 = 500 > 80
        proof = _proof(cash=100.0, debt=20.0, price=50.0, shares=10.0)
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert proof.verdict is not ProofVerdict.ESTABLISHES_NON_SUPPORT


class TestMissingCash:
    def test_missing_cash_does_not_establish(self):
        proof = _proof(cash=None, debt=20.0, price=5.0, shares=10.0)
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert proof.evidence_summary == "missing_cash"


class TestMissingDebt:
    def test_missing_debt_does_not_establish(self):
        proof = _proof(cash=100.0, debt=None, price=5.0, shares=10.0)
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert proof.evidence_summary == "missing_debt"


class TestMissingMarketCap:
    def test_missing_price_and_shares_does_not_establish(self):
        proof = _proof(cash=100.0, debt=20.0, price=None, shares=None)
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert proof.evidence_summary == "missing_current_market_cap"

    def test_missing_shares_only_does_not_establish(self):
        """Cash/debt real; a market record carries only `share_price`,
        never `shares_outstanding` -- no market observation is complete
        enough to compute a market cap from."""
        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import ingest

        records = _records(cash=100.0, debt=20.0, price=None, shares=None, tag="ms")
        doc = RawBusinessDocument(
            identifier="ms_price_only",
            company="ASML",
            source_kind="market_data_snapshot",
            published_at=_filed(2025),
            provider_id="structured_test_provider",
            raw_reference="ref://ms_price_only",
            content_hash="hash-ms-price-only",
            language="en",
            period_end=date(2025, 3, 1),
            metadata={"share_price": 5.0},
        )
        result = ingest(doc, evaluated_at=_GENERATED_AT)
        records = records + (result.record,)
        business_facts = extract_facts_from_records(records, evaluated_at=_GENERATED_AT)
        valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=_GENERATED_AT)
        proof = evaluate_net_cash_proof(business_facts, valuation_facts, generated_at=_GENERATED_AT)
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert proof.evidence_summary == "missing_current_market_cap"


class TestFutureDatedBalanceSheetFacts:
    def test_future_published_cash_is_excluded(self):
        records = _records(cash=100.0, debt=20.0, price=5.0, shares=10.0, tag="fd")
        # A future-published, misleadingly-large cash fact must not be
        # used for a claim about today's state.
        records = records + (
            fundamentals_record(
                period_end=date(2030, 12, 31), identifier="fd_future_cash", published_at=_filed(2031), cash=999999.0
            ),
        )
        business_facts = extract_facts_from_records(records, evaluated_at=_GENERATED_AT)
        valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=_GENERATED_AT)
        proof = evaluate_net_cash_proof(business_facts, valuation_facts, generated_at=_GENERATED_AT)
        assert "net_cash=80.00" in proof.evidence_summary


class TestNoAdditionalBalanceSheetCapabilityInvented:
    def test_module_reads_only_cash_and_total_debt_and_market_facts(self):
        import atlas.analysis_engine.valuation.net_cash_proof as module

        for forbidden in ("INVENTORY", "RECEIVABLES", "PP_E", "liquidation", "sum_of_the_parts"):
            assert forbidden not in dir(module)


class TestDeterminism:
    def test_identical_inputs_produce_identical_proof(self):
        first = _proof(cash=100.0, debt=20.0, price=5.0, shares=10.0, tag="det")
        second = _proof(cash=100.0, debt=20.0, price=5.0, shares=10.0, tag="det")
        assert first == second
