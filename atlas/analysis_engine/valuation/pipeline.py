"""Valuation Engine orchestration (ATLAS-024, Phase 2/9) -- single
public entry point: `evaluate_valuation`.

A pure function over already-extracted facts, mirroring
`atlas.analysis_engine.business.evaluate_business_analysis`'s own
shape: assembles `ValuationMethodKind.FCF_YIELD_RELATIVE`
(`cash_flow.evaluate_fcf_yield_relative`) and the three scenario
findings (`scenarios.build_scenario_findings`) into one
`ValuationEngineResult`, always naming all four methods.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.valuation.cash_flow import evaluate_fcf_yield_relative
from atlas.analysis_engine.valuation.facts import ValuationFact
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.analysis_engine.valuation.scenarios import build_scenario_findings
from atlas.decision_engine.contracts import EvaluationState

__all__ = ["evaluate_valuation"]


def evaluate_valuation(
    business_facts: tuple[BusinessFact, ...],
    valuation_facts: tuple[ValuationFact, ...],
    *,
    statement_record_ids: frozenset[str],
    industry: str | None,
    evaluated_at: datetime,
) -> ValuationEngineResult:
    """Deterministic: identical inputs always produce a deeply equal
    `ValuationEngineResult`. `statement_record_ids` names the records that
    are annual financial statements and `industry` is the company-profile
    industry -- the FCF-yield method's eligibility inputs (`cash_flow.py`).
    """
    fcf_yield_finding = evaluate_fcf_yield_relative(
        business_facts,
        valuation_facts,
        statement_record_ids=statement_record_ids,
        industry=industry,
        evaluated_at=evaluated_at,
    )
    scenario_findings = build_scenario_findings(evaluated_at=evaluated_at)

    return ValuationEngineResult(
        state=EvaluationState.EVALUATED,
        findings=(fcf_yield_finding, *scenario_findings),
    )
