"""Shared fixtures for the Investment Case Lifecycle test suite. Builds
real `InvestmentCaseComposition`/`CanonicalAnalysis` objects through the
real pipeline (`assemble_analysis`, real `BusinessRecord` ingestion) --
the same convention `tests/unit/alpha/knowledge_coverage/test_engine.py`
already established -- so Mandatory Core evaluation is exercised
against genuine evidence, never a hand-faked status. The one exception
is `real_directional_recommendation`, which mirrors
`tests/unit/alpha/test_decision_support.py`'s own `_directional`
helper: a real, valid `ComputedDirectionalRecommendation` built from a
real `run_populated()` output, swapped in via `dataclasses.replace`
because triggering `select_direction` to return non-`None` through the
full pipeline needs a portfolio/thesis setup this package's own tests
have no reason to duplicate -- `evaluate_recommendation_gate`'s own
suite (`test_recommendation.py`) already owns that responsibility.
"""
from __future__ import annotations

import dataclasses
from datetime import date

from atlas.alpha.investment_case.company_profile import extract_company_profile
from atlas.alpha.investment_case.financial_history import extract_financial_history, extract_market_snapshot
from atlas.alpha.investment_case.models import CurrentThesis, InvestmentCaseComposition
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.analysis_engine.recommendation import (
    ComputedDirectionalRecommendation,
    RecommendationConvictionLevel,
    RecommendationDirection,
    RecommendationGateResult,
    RecommendationReasoning,
)
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal, run_populated

EVALUATED_AT = GENERATED_AT


def make_record(source_kind, period_end, identifier, **metadata):
    document = RawBusinessDocument(
        identifier=identifier,
        company="ASML",
        source_kind=source_kind,
        published_at=GENERATED_AT,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


def profile_record():
    return make_record(
        "company_profile", None, "profile1", name="ASML", sector="Technology", industry="Semiconductors",
        country="Netherlands",
    )


def financial_statement_records():
    return (
        make_record("financial_statement", date(2022, 12, 31), "fy22", revenue=1000.0, free_cash_flow=200.0),
        make_record("financial_statement", date(2023, 12, 31), "fy23", revenue=1100.0, free_cash_flow=240.0),
        make_record("financial_statement", date(2024, 12, 31), "fy24", revenue=1250.0, free_cash_flow=300.0),
    )


def market_snapshot_record():
    return make_record("market_data_snapshot", date(2024, 12, 31), "mkt1", share_price=700.0, shares_outstanding=400.0)


def full_records():
    return (profile_record(), *financial_statement_records(), market_snapshot_record())


def build_composition(
    records: tuple = (), *, case_id: str = "00000000-0000-0000-0000-0000000000aa", populated: bool = True
) -> InvestmentCaseComposition:
    engine_input, output = run_populated(case_id=case_id) if populated else run_minimal(case_id=case_id)
    canonical_analysis = assemble_analysis(
        engine_input, output, is_thesis_stale=False, business_records=records, generated_at=EVALUATED_AT
    )
    return InvestmentCaseComposition(
        case_id=case_id,
        holding_context=None,
        canonical_analysis=canonical_analysis,
        current_thesis=CurrentThesis(
            latest_decision_reason=None, latest_decision_type=None, latest_observation_statement=None
        ),
        decision_history=(),
        observation_history=(),
        outcome_history=(),
        trade_log=(),
        is_thesis_stale=False,
        generated_at=EVALUATED_AT,
        company_profile=extract_company_profile("ASML", records),
        financial_history=extract_financial_history(records),
        market_snapshot=extract_market_snapshot(records),
    )


def real_directional_recommendation(
    direction: RecommendationDirection = RecommendationDirection.ADD, **overrides
) -> ComputedDirectionalRecommendation:
    _, output = run_populated()
    finding = output.reasoning.finding
    assert finding is not None
    portfolio_factors = output.portfolio_intelligence.portfolio_factors
    assert portfolio_factors is not None
    fields = dict(
        recommendation_instance_id="lifecycle-test",
        case_id=output.case_id,
        generated_at=GENERATED_AT,
        direction=direction,
        direction_statement="test fixture -- never read by lifecycle evaluation",
        conviction_level=RecommendationConvictionLevel.MEDIUM,
        conviction_reason="test fixture",
        reasoning=RecommendationReasoning(
            current_situation=finding.current_situation,
            supporting_evidence=finding.supporting_evidence,
            contradicting_evidence=finding.contradicting_evidence,
            portfolio_context=finding.portfolio_context,
            what_would_change=(),
        ),
        portfolio_factors=portfolio_factors,
    )
    fields.update(overrides)
    return ComputedDirectionalRecommendation(**fields)


def with_real_recommendation(
    composition: InvestmentCaseComposition, *, direction: RecommendationDirection = RecommendationDirection.ADD
) -> InvestmentCaseComposition:
    """Swaps in a real `ComputedDirectionalRecommendation` -- see this
    module's own docstring for why `dataclasses.replace` is the correct
    tool here rather than re-deriving one through the full pipeline."""
    recommendation = real_directional_recommendation(direction=direction)
    gate_result = RecommendationGateResult(
        recommendation=recommendation,
        conviction_gate_met=True,
        conviction=ConvictionAssessment(level=ConvictionLevel.HIGH, reasons=()),
    )
    new_canonical = dataclasses.replace(composition.canonical_analysis, recommendation=gate_result)
    return dataclasses.replace(composition, canonical_analysis=new_canonical)
