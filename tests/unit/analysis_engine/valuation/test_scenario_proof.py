"""Tests for `atlas.analysis_engine.valuation.scenario_proof` (`DE-015`
§11/§12's Scenario proof path).

`current_yield`/`historical_yields` are supplied directly (real,
hand-computed numbers, matching the exact shape `FCF_YIELD_RELATIVE`
already exposes on `ValuationFinding`) so the envelope math can be tested
precisely and predictably, independent of `cash_flow.py`'s own separate
mechanics (already covered by that module's own test suite). Growth
eligibility uses real records through `extract_facts_from_records`,
matching this arc's own established fixture discipline.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.valuation.proof import ProofVerdict
from atlas.analysis_engine.valuation.scenario_proof import evaluate_scenario_proof
from tests.unit.analysis_engine.valuation._fixtures import fundamentals_record

_GENERATED_AT = datetime(2026, 8, 13, tzinfo=timezone.utc)


def _filed(year: int, month: int = 2, day: int = 15) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _durable_growth_records(tag: str = "dg"):
    """6 periods, Revenue + Free Cash Flow both growing every period --
    real growth observations roughly 16-19% (see test module's own
    docstring-adjacent computation notes below each test)."""
    revenue = (900.0, 1000.0, 1100.0, 1250.0, 1400.0, 1600.0)
    fcf = (90.0, 100.0, 115.0, 140.0, 165.0, 200.0)
    years = (2019, 2020, 2021, 2022, 2023, 2024)
    return tuple(
        fundamentals_record(
            period_end=date(year, 12, 31),
            identifier=f"{tag}{year}",
            published_at=_filed(year + 1),
            revenue=revenue[i],
            free_cash_flow=fcf[i],
        )
        for i, year in enumerate(years)
    )


def _durable_growth_facts(tag: str = "dg"):
    return extract_facts_from_records(_durable_growth_records(tag), evaluated_at=_GENERATED_AT)


class TestFullyPositiveEnvelope:
    def test_establishes_support(self):
        """Real growth range ~16.4%-18.9%; current yield 0.05 vs
        historical (0.04, 0.06) -- even the bear case (min growth,
        cheapest/highest terminal yield) stays positive."""
        proof = evaluate_scenario_proof(
            _durable_growth_facts(),
            current_yield=0.05,
            historical_yields=(0.04, 0.06),
            generated_at=_GENERATED_AT,
        )
        assert proof.verdict is ProofVerdict.ESTABLISHES_SUPPORT


class TestFullyNegativeEnvelope:
    def test_establishes_non_support(self):
        """Current yield far below even the most favorable historical
        yield -- even the bull case (max growth, richest terminal yield)
        remains a loss."""
        proof = evaluate_scenario_proof(
            _durable_growth_facts(),
            current_yield=0.01,
            historical_yields=(0.05, 0.08),
            generated_at=_GENERATED_AT,
        )
        assert proof.verdict is ProofVerdict.ESTABLISHES_NON_SUPPORT


class TestStraddlingEnvelope:
    def test_does_not_establish(self):
        proof = evaluate_scenario_proof(
            _durable_growth_facts(),
            current_yield=0.02,
            historical_yields=(0.018, 0.05),
            generated_at=_GENERATED_AT,
        )
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert "envelope_low" in proof.evidence_summary


class TestInsufficientGrowthHistory:
    def test_thin_history_does_not_establish(self):
        records = (
            fundamentals_record(period_end=date(2023, 12, 31), identifier="th23", published_at=_filed(2024), revenue=1000.0, free_cash_flow=100.0),
            fundamentals_record(period_end=date(2024, 12, 31), identifier="th24", published_at=_filed(2025), revenue=1100.0, free_cash_flow=115.0),
        )
        facts = extract_facts_from_records(records, evaluated_at=_GENERATED_AT)
        proof = evaluate_scenario_proof(facts, current_yield=0.05, historical_yields=(0.04, 0.06), generated_at=_GENERATED_AT)
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert "ineligible" in proof.evidence_summary


class TestInsufficientYieldHistory:
    def test_empty_historical_yields_does_not_establish(self):
        proof = evaluate_scenario_proof(
            _durable_growth_facts(), current_yield=0.05, historical_yields=(), generated_at=_GENERATED_AT
        )
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert proof.evidence_summary == "no_historical_yield_range"

    def test_missing_current_yield_does_not_establish(self):
        proof = evaluate_scenario_proof(
            _durable_growth_facts(), current_yield=None, historical_yields=(0.04, 0.06), generated_at=_GENERATED_AT
        )
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert proof.evidence_summary == "no_current_yield"


class TestFutureDatedFacts:
    def test_future_dated_facts_do_not_change_the_verdict(self):
        with_future = _durable_growth_records() + (
            fundamentals_record(period_end=date(2029, 12, 31), identifier="future", published_at=_filed(2030), revenue=99999.0, free_cash_flow=99999.0),
        )
        facts_with_future = extract_facts_from_records(with_future, evaluated_at=_GENERATED_AT)
        facts_without = _durable_growth_facts()
        proof_with = evaluate_scenario_proof(facts_with_future, current_yield=0.05, historical_yields=(0.04, 0.06), generated_at=_GENERATED_AT)
        proof_without = evaluate_scenario_proof(facts_without, current_yield=0.05, historical_yields=(0.04, 0.06), generated_at=_GENERATED_AT)
        assert proof_with == proof_without


class TestNegativeFcfPeriods:
    def test_negative_fcf_periods_excluded_not_crashing(self):
        revenue = (900.0, 1000.0, 1100.0, 1250.0, 1400.0, 1600.0)
        fcf = (-10.0, 100.0, 115.0, 140.0, 165.0, 200.0)
        years = (2019, 2020, 2021, 2022, 2023, 2024)
        records = tuple(
            fundamentals_record(
                period_end=date(year, 12, 31), identifier=f"neg{year}", published_at=_filed(year + 1), revenue=revenue[i], free_cash_flow=fcf[i]
            )
            for i, year in enumerate(years)
        )
        facts = extract_facts_from_records(records, evaluated_at=_GENERATED_AT)
        proof = evaluate_scenario_proof(facts, current_yield=0.05, historical_yields=(0.04, 0.06), generated_at=_GENERATED_AT)
        # Only one real window (2020->2024) survives the negative-endpoint
        # exclusion -- fewer than 2 corroborated observations -> ineligible.
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert "ineligible" in proof.evidence_summary


class TestWideDispersion:
    def test_wide_growth_dispersion_handled_honestly(self):
        """A company with wildly inconsistent historical growth still
        produces a real, deterministic verdict -- no crash, no invented
        dispersion gate (the width itself is the disclosure)."""
        revenue = (500.0, 1500.0, 600.0, 1800.0, 700.0, 2200.0)
        fcf = (50.0, 150.0, 60.0, 180.0, 70.0, 220.0)
        years = (2019, 2020, 2021, 2022, 2023, 2024)
        records = tuple(
            fundamentals_record(
                period_end=date(year, 12, 31), identifier=f"wide{year}", published_at=_filed(year + 1), revenue=revenue[i], free_cash_flow=fcf[i]
            )
            for i, year in enumerate(years)
        )
        facts = extract_facts_from_records(records, evaluated_at=_GENERATED_AT)
        proof = evaluate_scenario_proof(facts, current_yield=0.05, historical_yields=(0.03, 0.07), generated_at=_GENERATED_AT)
        assert proof.verdict in (ProofVerdict.ESTABLISHES_SUPPORT, ProofVerdict.ESTABLISHES_NON_SUPPORT, ProofVerdict.DOES_NOT_ESTABLISH)


class TestOutlookIndependence:
    def test_module_never_imports_outlook(self):
        import atlas.analysis_engine.valuation.scenario_proof as module

        for forbidden in ("Outlook", "ExpectedReturnRange", "OutlookScenario", "HorizonOutlook", "build_outlook"):
            assert not hasattr(module, forbidden)


class TestDeterminism:
    def test_identical_inputs_produce_identical_proof(self):
        first = evaluate_scenario_proof(_durable_growth_facts(), current_yield=0.05, historical_yields=(0.04, 0.06), generated_at=_GENERATED_AT)
        second = evaluate_scenario_proof(_durable_growth_facts(), current_yield=0.05, historical_yields=(0.04, 0.06), generated_at=_GENERATED_AT)
        assert first == second
