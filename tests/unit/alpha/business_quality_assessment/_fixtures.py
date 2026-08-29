"""Shared fixture helpers for `atlas.alpha.business_quality_assessment`
tests -- builds real `BusinessQualityKnowledge`/`ManagementCredibility
Knowledge` objects through the actual, already-tested extraction
pipeline (`test_business_quality_intelligence.py`/`test_management
_credibility_intelligence.py`'s own established pattern), rather than
hand-constructing these large nested dataclasses field-by-field, which
would risk silently drifting from what the real pipeline actually
produces.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.business_quality_intelligence import BusinessQualityKnowledge, extract_business_quality
from atlas.alpha.investment_case.capital_allocation_intelligence import extract_capital_allocation_history
from atlas.alpha.investment_case.earnings_call import EarningsCallKnowledge, extract_earnings_call_knowledge
from atlas.alpha.investment_case.financial_quality_intelligence import extract_financial_quality
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.growth_intelligence import extract_growth_knowledge
from atlas.alpha.investment_case.management_credibility_intelligence import (
    ManagementCredibilityKnowledge,
    extract_management_credibility,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)


def period(year: int, **metadata):
    document = RawBusinessDocument(
        identifier=f"AAPL:FY:{year}-12-31",
        company="AAPL",
        source_kind="financial_statement",
        published_at=datetime(year + 1, 2, 15, tzinfo=timezone.utc),
        provider_id="sec_edgar",
        raw_reference="https://example.test/10k",
        content_hash=f"hash-{year}",
        language="en",
        period_start=date(year, 1, 1),
        period_end=date(year, 12, 31),
        metadata={**metadata, "currency": "USD"},
    )
    result = ingest(document, evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def steady_growing_records(n: int = 6, **overrides) -> tuple:
    """Mirrors `test_business_quality_intelligence.py`'s own
    `_steady_records` -- a company with rising revenue/income/cash flow,
    stable margins, consistent buybacks, and disciplined debt repayment.
    Real extraction from this shape reaches: `profitability_stability
    STABLE`, `revenue_stability CONSISTENT_GROWTH`,
    `cash_generation_stability CONSISTENT`, `capital_allocation
    _stability CONSISTENT`, growth durability across every tracked
    metric, and a rising `return_on_assets_trend` (income/cash flow grow
    faster than assets each period)."""
    defaults = dict(
        net_income=100.0, operating_cash_flow=150.0, free_cash_flow=120.0, equity=500.0, total_assets=1200.0,
        total_debt=200.0, current_assets=400.0, current_liabilities=200.0, share_buybacks=50.0, dividends=20.0,
        debt_issuance=10.0, debt_repayment=15.0, shares_outstanding=100.0,
    )
    defaults.update(overrides)
    return tuple(
        period(
            2018 + i, revenue=1000.0 + i * 150, net_income=defaults["net_income"] + i * 15,
            operating_cash_flow=defaults["operating_cash_flow"] + i * 20,
            free_cash_flow=defaults["free_cash_flow"] + i * 18, equity=defaults["equity"] + i * 40,
            total_assets=defaults["total_assets"] + i * 10, total_debt=defaults["total_debt"],
            current_assets=defaults["current_assets"], current_liabilities=defaults["current_liabilities"],
            share_buybacks=defaults["share_buybacks"], dividends=defaults["dividends"],
            debt_issuance=defaults["debt_issuance"], debt_repayment=defaults["debt_repayment"],
            shares_outstanding=defaults["shares_outstanding"] - i * 2,
        )
        for i in range(n)
    )


def declining_volatile_records(n: int = 6) -> tuple:
    """A company with volatile, deteriorating margins, inconsistent
    cash generation, no buybacks, and rising debt with no repayment --
    designed to reach `VOLATILE` profitability, `FALLING` returns on
    capital, and no durable-growth metrics."""
    records = []
    for i in range(n):
        revenue = 1000.0 - (i % 2) * 300.0
        records.append(
            period(
                2018 + i,
                revenue=revenue,
                net_income=(revenue * 0.2) if i % 2 == 0 else -(revenue * 0.05),
                operating_cash_flow=50.0 if i % 2 == 0 else -20.0,
                free_cash_flow=30.0 if i % 2 == 0 else -40.0,
                equity=500.0 - i * 20,
                total_assets=1200.0 + i * 80,
                total_debt=200.0 + i * 60,
                current_assets=300.0,
                current_liabilities=350.0,
                share_issuance=40.0,
                debt_issuance=60.0,
                debt_repayment=5.0,
                shares_outstanding=100.0 + i * 3,
            )
        )
    return tuple(records)


def business_quality_from(records: tuple) -> BusinessQualityKnowledge:
    fsh = extract_financial_statement_history(records)
    cah = extract_capital_allocation_history(records)
    fq = extract_financial_quality(fsh)
    growth = extract_growth_knowledge(fsh)
    return extract_business_quality(fsh, cah, fq, growth)


def management_credibility_from(records: tuple, transcripts: tuple = ()) -> ManagementCredibilityKnowledge:
    fsh = extract_financial_statement_history(records)
    cah = extract_capital_allocation_history(records)
    growth = extract_growth_knowledge(fsh)
    earnings_call: EarningsCallKnowledge = extract_earnings_call_knowledge(transcripts)
    return extract_management_credibility(earnings_call, fsh, growth, cah)
