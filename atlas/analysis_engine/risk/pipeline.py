"""Risk Analysis orchestration (ATLAS-025, Phase 12/13) -- single public
entry point: `evaluate_risk`.

A pure function over already-computed upstream results, mirroring
`atlas.analysis_engine.valuation.pipeline.evaluate_valuation`'s own
shape: assembles the four v1 evaluators
(`business_risk`/`financial_risk`/`valuation_risk`/`thesis_risk`) into
one `RiskAnalysisResult`. Never reads a `BusinessRecord`, a
`ValuationFact`, or Core Evidence/Observation records directly -- every
input here is itself the output of an earlier stage, matching Phase
8/9's "consume, never recompute" rule uniformly across all four
categories.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business import BusinessAnalysisResult, BusinessCategory
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.risk.business_risk import evaluate_business_risk
from atlas.analysis_engine.risk.financial_risk import evaluate_financial_risk
from atlas.analysis_engine.risk.models import RiskAnalysisResult
from atlas.analysis_engine.risk.thesis_risk import evaluate_thesis_risk
from atlas.analysis_engine.risk.valuation_risk import evaluate_valuation_risk
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.decision_engine.contracts import ContradictionSummary, EvaluationState, EvidenceCoverageLevel

__all__ = ["evaluate_risk"]


def evaluate_risk(
    business_analysis: BusinessAnalysisResult,
    business_facts: tuple[BusinessFact, ...],
    valuation_engine: ValuationEngineResult,
    contradicting_evidence: ContradictionSummary,
    *,
    evidence_coverage: EvidenceCoverageLevel,
    evaluated_at: datetime,
) -> RiskAnalysisResult:
    """Deterministic: identical inputs always produce a deeply equal
    `RiskAnalysisResult`.
    """
    growth_finding = next(f for f in business_analysis.findings if f.kind is BusinessCategory.GROWTH)
    capital_allocation_finding = next(
        f for f in business_analysis.findings if f.kind is BusinessCategory.CAPITAL_ALLOCATION
    )
    fcf_yield_finding = next(
        f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
    )

    findings = (
        evaluate_business_risk(growth_finding, evaluated_at=evaluated_at),
        evaluate_financial_risk(capital_allocation_finding, business_facts, evaluated_at=evaluated_at),
        evaluate_valuation_risk(fcf_yield_finding, evaluated_at=evaluated_at),
        evaluate_thesis_risk(
            contradicting_evidence, evidence_coverage=evidence_coverage, evaluated_at=evaluated_at
        ),
    )

    return RiskAnalysisResult(state=EvaluationState.EVALUATED, findings=findings)
