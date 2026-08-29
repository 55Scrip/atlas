"""Analysis Engine pipeline orchestration (ATLAS-020, Phase 2/3 assembly).

Single public entry point: `assemble_analysis`. A **pure function** over
an already-computed `atlas.decision_engine.contracts.DecisionEngineOutput`
-- it never calls `atlas.decision_engine.pipeline.run_pipeline` itself,
so a caller that already has a `DecisionEngineOutput` (as
`atlas.alpha.portfolio_intelligence.pipeline_bridge` and
`atlas.alpha.case_intelligence` already do, per ATLAS-016/017) never
pays for a second pipeline run, and this package never duplicates what
`run_pipeline` already computed.

`engine_input` is accepted only because
`atlas.analysis_engine.recommendation.evaluate_recommendation_gate`
delegates to `atlas.decision_engine.stages.recommendation
.determine_recommendation`, whose signature requires it (that stage
does not currently read it -- see its own `del engine_input`). Every
caller of `run_pipeline` already holds the `DecisionEngineInput` it
built, so this is never an extra lookup.

`is_thesis_stale` is the one fact this function cannot derive from
`DecisionEngineOutput` alone: it depends on the 90-day-since-last-Decision
threshold `atlas.alpha.portfolio_intelligence.thresholds` already applies
-- Alpha-scoped data this package's own architectural boundary does not
read (see `__init__.py`). The caller (a future Alpha-side composition
layer) supplies it, exactly as `conviction.calculate_conviction` already
documents.

Findings are assembled once, in `_build_findings`, then partitioned: the
full tuple becomes `CanonicalAnalysis.findings`; the subset tagged with a
`risk_category` in `details` becomes `RiskSection.findings`. Both refer
to the same `Finding` objects -- filtering, not duplicating.

Every `Finding`'s `confidence` field reuses one case-wide value --
Business Evaluation's own `EvidenceCoverageLevel` (`confidence.py`).
This sprint's evaluators produce no finer-grained, per-Finding
confidence signal than that one case-wide fact, and inventing one would
be exactly the kind of fabricated precision `Doctrine`'s "avoid false
precision" principle forbids; a future stage with a real per-Finding
signal can override this without a shape change (`confidence` stays on
every `Finding` regardless of which value populates it).
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.analysis_coverage import calculate_analysis_coverage
from atlas.analysis_engine.business import (
    BusinessAnalysisResult,
    BusinessCategory,
    BusinessCategoryStatus,
    evaluate_business_analysis,
)
from atlas.analysis_engine.business_data.completeness import assess_data_completeness
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.confidence import Confidence
from atlas.analysis_engine.contracts import RiskCategory, CapabilityStatus
from atlas.analysis_engine.conviction import calculate_conviction
from atlas.analysis_engine.findings import Finding, FindingKind, FindingProducer, FindingSeverity
from atlas.analysis_engine.investment_case_synthesis import derive_case_open_questions, synthesize_investment_case
from atlas.analysis_engine.models import CanonicalAnalysis, Identity, RiskSection, UnavailableCapability
from atlas.analysis_engine.outlook import build_outlook
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.recommendation import evaluate_recommendation_gate
from atlas.analysis_engine.recommendation_outlook_context import derive_recommendation_outlook_context
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import RiskAnalysisResult
from atlas.analysis_engine.risk.pipeline import evaluate_risk
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.analysis_engine.valuation.pipeline import evaluate_valuation
from atlas.analysis_engine.valuation.support import evaluate_valuation_support
from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    DecisionEngineOutput,
    OpenQuestion,
    OpenQuestionKind,
    RecommendationWithheld,
)

__all__ = ["assemble_analysis"]

#: Every Finding this sprint's pipeline produces is read the same way by
#: every surface ATLAS-019's audit identified as a future
#: `CanonicalAnalysis` consumer. No Finding kind is scoped to fewer
#: consumers than this today -- a future sprint that wires a specific
#: surface to a specific Finding kind can narrow this per-Finding, not
#: before there is a real reader to narrow it for.
_ALL_INTENDED_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


def _provenance(
    *,
    source_kind: SourceKind,
    source_references: tuple[str, ...],
    dependencies: tuple[str, ...],
    update_trigger: UpdateTrigger,
    generated_at: datetime,
) -> Provenance:
    return Provenance(
        source_kind=source_kind,
        source_references=source_references,
        dependencies=dependencies,
        update_trigger=update_trigger,
        consumers=_ALL_INTENDED_CONSUMERS,
        computed_at=generated_at,
    )


def _build_findings(
    decision_output: DecisionEngineOutput,
    *,
    confidence: Confidence,
    conviction_finding_id: str,
    generated_at: datetime,
) -> tuple[Finding, ...]:
    """Every `Finding` this sprint's pipeline can honestly produce, from
    signals `atlas.decision_engine` already computed -- one Finding per
    already-real fact, never a Finding invented to fill out the shape.
    Order is fixed (business, valuation, portfolio, reasoning-derived,
    then conviction/recommendation) so two assemblies of the same
    `DecisionEngineOutput` are trivially diffable.
    """
    business = decision_output.business_evaluation
    valuation = decision_output.valuation
    portfolio = decision_output.portfolio_intelligence
    reasoning = decision_output.reasoning.finding

    findings: list[Finding] = []

    # -- Business Evaluation ------------------------------------------------
    findings.append(
        Finding(
            id=FindingKind.EVIDENCE_COVERAGE.value,
            kind=FindingKind.EVIDENCE_COVERAGE,
            severity=FindingSeverity.INFO,
            details={"coverage": business.evidence_quality.coverage.value},
            evidence_references=(),
            confidence=confidence,
            producer=FindingProducer.BUSINESS_EVALUATION,
            provenance=_provenance(
                source_kind=SourceKind.DECISION_ENGINE_STAGE,
                source_references=(),
                dependencies=(),
                update_trigger=UpdateTrigger.NEW_EVIDENCE_RECORDED,
                generated_at=generated_at,
            ),
        )
    )
    findings.append(
        Finding(
            id=FindingKind.BUSINESS_ANALYSIS_UNAVAILABLE.value,
            kind=FindingKind.BUSINESS_ANALYSIS_UNAVAILABLE,
            severity=FindingSeverity.ATTENTION,
            details={"reason": business.durability.reason.value},
            evidence_references=(),
            confidence=confidence,
            producer=FindingProducer.BUSINESS_EVALUATION,
            provenance=_provenance(
                source_kind=SourceKind.DECISION_ENGINE_STAGE,
                source_references=(),
                dependencies=(),
                update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
                generated_at=generated_at,
            ),
        )
    )
    for gap in business.evidence_quality.evidence_gaps:
        reference = gap.reference
        findings.append(
            Finding(
                id=f"{FindingKind.MISSING_EVIDENCE.value}:{gap.kind.value}:{reference or 'case'}",
                kind=FindingKind.MISSING_EVIDENCE,
                severity=FindingSeverity.ATTENTION,
                details={"gap_kind": gap.kind.value},
                evidence_references=(reference,) if reference is not None else (),
                confidence=confidence,
                producer=FindingProducer.BUSINESS_EVALUATION,
                provenance=_provenance(
                    source_kind=SourceKind.DECISION_ENGINE_STAGE,
                    source_references=(reference,) if reference is not None else (),
                    dependencies=(),
                    update_trigger=UpdateTrigger.NEW_EVIDENCE_RECORDED,
                    generated_at=generated_at,
                ),
            )
        )

    # -- Contradicting evidence (also Risk: THESIS_RISK) ---------------------
    for classification in reasoning.contradicting_evidence.observation_classifications:
        reference = str(classification.observation_id)
        findings.append(
            Finding(
                id=f"{FindingKind.CONTRADICTING_EVIDENCE.value}:{reference}",
                kind=FindingKind.CONTRADICTING_EVIDENCE,
                severity=FindingSeverity.MATERIAL,
                details={
                    "risk_category": RiskCategory.THESIS_RISK.value,
                    "challenging_evidence_count": classification.challenging_evidence_count,
                },
                evidence_references=(reference,),
                confidence=confidence,
                producer=FindingProducer.REASONING,
                provenance=_provenance(
                    source_kind=SourceKind.DECISION_ENGINE_STAGE,
                    source_references=(reference,),
                    dependencies=(),
                    update_trigger=UpdateTrigger.NEW_EVIDENCE_RECORDED,
                    generated_at=generated_at,
                ),
            )
        )

    # -- Valuation ------------------------------------------------------
    findings.append(
        Finding(
            id=FindingKind.VALUATION_UNAVAILABLE.value,
            kind=FindingKind.VALUATION_UNAVAILABLE,
            severity=FindingSeverity.ATTENTION,
            details={"reason": valuation.substantive_valuation.reason.value},
            evidence_references=(),
            confidence=confidence,
            producer=FindingProducer.VALUATION,
            provenance=_provenance(
                source_kind=SourceKind.DECISION_ENGINE_STAGE,
                source_references=(),
                dependencies=(),
                update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
                generated_at=generated_at,
            ),
        )
    )
    findings.append(
        Finding(
            id=FindingKind.EXECUTION_PRICE_HISTORY.value,
            kind=FindingKind.EXECUTION_PRICE_HISTORY,
            severity=FindingSeverity.INFO,
            details={
                "coverage": valuation.execution_price_history.coverage.value,
                "entry_count": valuation.execution_price_history.entry_count,
            },
            evidence_references=(),
            confidence=confidence,
            producer=FindingProducer.VALUATION,
            provenance=_provenance(
                source_kind=SourceKind.DECISION_ENGINE_STAGE,
                source_references=(),
                dependencies=(),
                update_trigger=UpdateTrigger.NEW_TRADE_RECORDED,
                generated_at=generated_at,
            ),
        )
    )

    # -- Portfolio Intelligence ------------------------------------------
    holding = portfolio.holding_context
    findings.append(
        Finding(
            id=FindingKind.HOLDING_CONTEXT.value,
            kind=FindingKind.HOLDING_CONTEXT,
            severity=FindingSeverity.INFO,
            details={
                "linkage": holding.linkage.value,
                "ticker": holding.ticker,
                "weight_percent": holding.weight_percent,
                "reconciliation_status": (
                    holding.reconciliation_status.value if holding.reconciliation_status else None
                ),
            },
            evidence_references=(),
            confidence=confidence,
            producer=FindingProducer.PORTFOLIO_INTELLIGENCE,
            provenance=_provenance(
                source_kind=SourceKind.DECISION_ENGINE_STAGE,
                source_references=(),
                dependencies=(),
                update_trigger=UpdateTrigger.HOLDING_STATE_CHANGED,
                generated_at=generated_at,
            ),
        )
    )
    for factor in portfolio.portfolio_factors.factors:
        findings.append(
            Finding(
                id=f"{FindingKind.PORTFOLIO_FACTOR_UNAVAILABLE.value}:{factor.value}",
                kind=FindingKind.PORTFOLIO_FACTOR_UNAVAILABLE,
                severity=FindingSeverity.INFO,
                details={
                    "factor": factor.value,
                    "reason": portfolio.portfolio_factors.reason.value,
                },
                evidence_references=(),
                confidence=confidence,
                producer=FindingProducer.PORTFOLIO_INTELLIGENCE,
                provenance=_provenance(
                    source_kind=SourceKind.DECISION_ENGINE_STAGE,
                    source_references=(),
                    dependencies=(),
                    update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
                    generated_at=generated_at,
                ),
            )
        )

    # -- Reasoning: open questions ----------------------------------------
    for question in reasoning.open_questions:
        reference = question.reference
        findings.append(
            Finding(
                id=f"{FindingKind.OPEN_QUESTION.value}:{question.kind.value}:{reference or 'case'}",
                kind=FindingKind.OPEN_QUESTION,
                severity=FindingSeverity.ATTENTION,
                details={"question_kind": question.kind.value},
                evidence_references=(reference,) if reference is not None else (),
                confidence=confidence,
                producer=FindingProducer.REASONING,
                provenance=_provenance(
                    source_kind=SourceKind.DECISION_ENGINE_STAGE,
                    source_references=(reference,) if reference is not None else (),
                    dependencies=(),
                    update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
                    generated_at=generated_at,
                ),
            )
        )

    # -- Conviction (Analysis Engine's own stage) --------------------------
    findings.append(
        Finding(
            id=conviction_finding_id,
            kind=FindingKind.CONVICTION_ASSESSED,
            severity=FindingSeverity.INFO,
            details={"level": None},  # placeholder overwritten by caller below
            evidence_references=(),
            confidence=confidence,
            producer=FindingProducer.CONVICTION,
            provenance=_provenance(
                source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
                source_references=(),
                dependencies=(FindingKind.EVIDENCE_COVERAGE.value,),
                update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
                generated_at=generated_at,
            ),
        )
    )

    return tuple(findings)


def _business_category_findings(business_analysis: BusinessAnalysisResult) -> tuple[Finding, ...]:
    """Project each rich `BusinessFinding` (ATLAS-021) onto the generic,
    flat `Finding` shape -- for consumers of `CanonicalAnalysis.findings`
    that want "every Finding this run produced" without caring about
    category-specific structure. The richer type, with its own
    evidence/missing-evidence detail, stays on
    `CanonicalAnalysis.business_analysis.findings`; this is a view, not
    a second computation -- `provenance` is reused verbatim from the
    `BusinessFinding` it projects, never rebuilt.
    """
    return tuple(
        Finding(
            id=f"{FindingKind.BUSINESS_CATEGORY_ASSESSED.value}:{business_finding.kind.value}",
            kind=FindingKind.BUSINESS_CATEGORY_ASSESSED,
            severity=business_finding.severity,
            details={"category": business_finding.kind.value, "status": business_finding.status.value},
            evidence_references=business_finding.supporting_evidence + business_finding.contradicting_evidence,
            confidence=business_finding.confidence,
            producer=FindingProducer.BUSINESS_ANALYSIS,
            provenance=business_finding.provenance,
        )
        for business_finding in business_analysis.findings
    )


def _valuation_method_findings(valuation_engine: ValuationEngineResult) -> tuple[Finding, ...]:
    """Project each rich `ValuationFinding` (ATLAS-024) onto the
    generic, flat `Finding` shape -- mirrors
    `_business_category_findings` exactly. The richer type stays on
    `CanonicalAnalysis.valuation_engine.findings`."""
    return tuple(
        Finding(
            id=f"{FindingKind.VALUATION_METHOD_ASSESSED.value}:{valuation_finding.kind.value}",
            kind=FindingKind.VALUATION_METHOD_ASSESSED,
            severity=valuation_finding.severity,
            details={"method": valuation_finding.kind.value, "status": valuation_finding.status.value},
            evidence_references=valuation_finding.supporting_facts + valuation_finding.contradicting_facts,
            confidence=valuation_finding.confidence,
            producer=FindingProducer.VALUATION_ENGINE,
            provenance=valuation_finding.provenance,
        )
        for valuation_finding in valuation_engine.findings
    )


def _risk_category_findings(risk_analysis: RiskAnalysisResult) -> tuple[Finding, ...]:
    """Project each rich `RiskFinding` (ATLAS-025) onto the generic,
    flat `Finding` shape -- mirrors `_business_category_findings`/
    `_valuation_method_findings` exactly. `details["risk_category"]`
    reuses the exact key `RiskSection`'s pre-existing filter already
    checks (`risk_findings = tuple(f for f in findings if
    "risk_category" in f.details)`, below), so these new Findings are
    picked up into `RiskSection` automatically -- zero changes to that
    filter or to `RiskSection` itself. The richer type stays on
    `CanonicalAnalysis.risk_analysis.findings`."""
    return tuple(
        Finding(
            id=f"{FindingKind.RISK_CATEGORY_ASSESSED.value}:{risk_finding.category.value}",
            kind=FindingKind.RISK_CATEGORY_ASSESSED,
            severity=risk_finding.severity,
            details={"risk_category": risk_finding.category.value, "status": risk_finding.status.value},
            evidence_references=risk_finding.supporting_facts + risk_finding.contradicting_facts,
            confidence=risk_finding.confidence,
            producer=FindingProducer.RISK_ANALYSIS,
            provenance=risk_finding.provenance,
        )
        for risk_finding in risk_analysis.findings
    )


def _effective_open_questions(
    open_questions: tuple[OpenQuestion, ...], *, valuation_conclusive: bool
) -> tuple[OpenQuestion, ...]:
    """ATLAS-027 Phase 2: `reasoning.finding.open_questions`, corrected
    for exactly one proven-stale case -- never a wholesale filter, never
    touched to artificially raise Conviction.

    `OpenQuestionKind.VALUATION_THESIS_NOT_DOCUMENTED` is built by
    `atlas.decision_engine.stages.reasoning` from decision_engine's own
    `ValuationResult.substantive_valuation` -- a hardcoded constant,
    always `INSUFFICIENT_INPUT`, structurally blind to this package's
    own real `valuation_engine.cash_flow.evaluate_fcf_yield_relative`.
    When that real method reaches a genuine conclusion
    (`valuation_conclusive`), the decision_engine-level question no
    longer describes `CanonicalAnalysis`'s true state and is omitted.
    Every other question -- `BUSINESS_DURABILITY_NOT_ASSESSABLE`,
    every `PORTFOLIO_FACTOR_NOT_ASSESSABLE` -- is untouched: both were
    individually audited and confirmed genuinely, permanently
    unresolved (see this function's own module docstring reference in
    `models.py::CanonicalAnalysis.open_questions`), not merely
    inconvenient for reaching a higher Conviction level.
    """
    if not valuation_conclusive:
        return open_questions
    return tuple(
        question
        for question in open_questions
        if question.kind is not OpenQuestionKind.VALUATION_THESIS_NOT_DOCUMENTED
    )


def assemble_analysis(
    engine_input: DecisionEngineInput,
    decision_output: DecisionEngineOutput,
    *,
    is_thesis_stale: bool,
    business_records: tuple[BusinessRecord, ...] = (),
    generated_at: datetime,
) -> CanonicalAnalysis:
    """Assemble one `CanonicalAnalysis` from an already-computed
    `DecisionEngineOutput`. Deterministic: identical inputs always
    produce a deeply equal `CanonicalAnalysis` -- no wall-clock read, no
    randomness, matching every stage in `atlas.decision_engine` and
    every stage in this package.

    `business_records` (ATLAS-022) is a passthrough both to
    `business.evaluate_business_analysis` and, new in ATLAS-024, to
    `valuation.pipeline.evaluate_valuation` -- always `()` at every
    real call site today, same as `is_thesis_stale`'s own
    Alpha-supplied default; a future composition layer that has run
    `business_data.pipeline.ingest` supplies the resulting
    `BusinessRecord`s here. A market-data snapshot is a `BusinessRecord`
    tagged `SourceKind.MARKET_DATA_SNAPSHOT` like any other -- there is
    no separate `valuation_records` parameter, since
    `business_facts.extraction`/`valuation.facts.extraction` each
    already filter the same tuple down to what they respectively need.

    **ATLAS-024 Conviction wiring**: `valuation_conclusive` is no longer
    hardcoded `False`. It is `True` exactly when
    `ValuationMethodKind.FCF_YIELD_RELATIVE`'s own finding reaches a
    real categorical conclusion (not `NOT_EVALUATED`/`INSUFFICIENT_INPUT`)
    -- the smallest correct integration change: real valuation is
    allowed to count as conclusive, but by itself it does not raise
    Conviction (`conviction.py`'s own thresholds/logic are untouched;
    only this call site's argument changed).

    **ATLAS-026 Conviction wiring**: `business_conclusive` is no longer
    hardcoded `False`. It is `True` exactly when both of `business`'s
    currently real evaluators -- Growth and Capital Allocation -- reach
    a genuine categorical conclusion, per explicit confirmation (see
    `conviction.py`'s own module docstring for the full reasoning).
    `has_high_financial_or_valuation_risk` is new: `True` when
    `risk_analysis` names `FINANCIAL_RISK` or `VALUATION_RISK` as
    `RiskStatus.HIGH` -- `BUSINESS_RISK`/`THESIS_RISK` are deliberately
    excluded to avoid double-counting signals `business_conclusive`/
    `has_contradicting_evidence` already carry.
    """
    reasoning = decision_output.reasoning.finding
    confidence: Confidence = decision_output.business_evaluation.evidence_quality.coverage

    business_analysis = evaluate_business_analysis(
        decision_output.business_evaluation, business_records=business_records, evaluated_at=generated_at
    )

    business_facts = extract_facts_from_records(business_records, evaluated_at=generated_at)
    market_facts = extract_valuation_facts_from_records(business_records, evaluated_at=generated_at)
    valuation_engine = evaluate_valuation(business_facts, market_facts, evaluated_at=generated_at)
    # Valuation Support for Capital Deployment (`DE-015`): an independent
    # conclusion derived from valuation_engine plus raw business/valuation
    # facts (never Business Analysis/Outlook/Portfolio Intelligence
    # conclusions -- see valuation/support.py's own module docstring).
    # `DE-016` forwards only its public `.status` into
    # evaluate_recommendation_gate below (`DE-015` §18) -- Outlook and
    # Portfolio Intelligence still never read it.
    valuation_support = evaluate_valuation_support(
        valuation_engine, business_facts, market_facts, generated_at=generated_at
    )
    fcf_yield_finding = next(
        f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
    )
    valuation_conclusive = fcf_yield_finding.status not in (
        ValuationStatus.NOT_EVALUATED,
        ValuationStatus.INSUFFICIENT_INPUT,
    )

    risk_analysis = evaluate_risk(
        business_analysis,
        business_facts,
        valuation_engine,
        reasoning.contradicting_evidence,
        evidence_coverage=confidence,
        evaluated_at=generated_at,
    )

    growth_finding = next(f for f in business_analysis.findings if f.kind is BusinessCategory.GROWTH)
    capital_allocation_finding = next(
        f for f in business_analysis.findings if f.kind is BusinessCategory.CAPITAL_ALLOCATION
    )
    _inconclusive_business_statuses = (
        BusinessCategoryStatus.NOT_EVALUATED,
        BusinessCategoryStatus.INSUFFICIENT_INPUT,
    )
    business_conclusive = (
        growth_finding.status not in _inconclusive_business_statuses
        and capital_allocation_finding.status not in _inconclusive_business_statuses
    )

    has_high_financial_or_valuation_risk = any(
        risk_finding.status is RiskStatus.HIGH
        for risk_finding in risk_analysis.findings
        if risk_finding.category in (RiskCategory.FINANCIAL_RISK, RiskCategory.VALUATION_RISK)
    )
    # Recommendation Evidence Sufficiency Alignment: any real (not
    # NOT_EVALUATED/INSUFFICIENT_INPUT) risk category is provenance-
    # backed company evidence -- one of the three real evidence sources
    # `select_direction`'s Stage-1 gate now recognizes, alongside Growth/
    # Capital Allocation and Valuation (already its own parameters).
    # Deliberately broader than `has_high_financial_or_valuation_risk`
    # above (HIGH-only, two categories, used for matrix dampening): this
    # is an existence check across all four real risk categories, not a
    # severity check.
    has_real_risk_evidence = any(
        risk_finding.status in (RiskStatus.LOW, RiskStatus.MODERATE, RiskStatus.HIGH)
        for risk_finding in risk_analysis.findings
    )

    # Internal Alpha Fix Sprint 1, Part 2 (IA-003): a separate, purely
    # company-data-driven signal -- deliberately never reads
    # `confidence`/`evidence_coverage` (investor evidence), unlike
    # `conviction` below. Reuses `business_conclusive`/
    # `valuation_conclusive`, computed once, just above.
    analysis_coverage = calculate_analysis_coverage(
        has_company_data=assess_data_completeness(business_records).is_minimally_complete,
        business_conclusive=business_conclusive,
        valuation_conclusive=valuation_conclusive,
    )

    open_questions = _effective_open_questions(reasoning.open_questions, valuation_conclusive=valuation_conclusive)

    # Calibration Phase 4 (Conviction & Capital Allocation Repair):
    # Conviction's own inputs below are Atlas's own analytical
    # knowledge, never investor history -- see `conviction.py`'s own
    # module docstring for the full investigation. `has_analytical
    # _contradiction` is a finding that carries BOTH real supporting
    # AND real contradicting evidence at once (e.g. Capital
    # Allocation's own two independent signals disagreeing) -- a
    # genuine internal tension in Atlas's own analysis, never an
    # investor's Observation classification. `THESIS_RISK` is excluded:
    # its own `contradicting_facts` are investor Observation ids reused
    # verbatim from `ContradictionSummary` (`thesis_risk.py`'s own
    # docstring) -- exactly the investor-history signal this redesign
    # removes; its `supporting_facts` is always `()` by construction so
    # it could never trigger this check anyway, but the exclusion is
    # explicit rather than relying on that incidental fact.
    has_analytical_contradiction = (
        any(finding.supporting_evidence and finding.contradicting_evidence for finding in business_analysis.findings)
        or any(
            finding.supporting_facts and finding.contradicting_facts
            for finding in risk_analysis.findings
            if finding.category is not RiskCategory.THESIS_RISK
        )
        or bool(fcf_yield_finding.supporting_facts and fcf_yield_finding.contradicting_facts)
    )
    # `derive_case_open_questions` (Atlas's own business-analysis-driven
    # open questions) replaces `reasoning.open_questions`
    # (`decision_engine`'s own investor evidence-*linkage* gap list,
    # still real and still used above/below for `open_questions`'s own,
    # unrelated consumers -- Calibration Phase 2's own ownership map
    # already named `key_open_questions`/`derive_case_open_questions`
    # as the correct owner for a user-facing "open question," never
    # this evidence-linkage list).
    analysis_open_questions = derive_case_open_questions(business_analysis, valuation_engine)

    conviction_finding_id = FindingKind.CONVICTION_ASSESSED.value
    conviction = calculate_conviction(
        business_state=decision_output.business_evaluation.state,
        valuation_state=decision_output.valuation.state,
        analysis_coverage=analysis_coverage.level,
        has_contradicting_evidence=has_analytical_contradiction,
        has_open_questions=bool(analysis_open_questions),
        is_thesis_stale=is_thesis_stale,
        business_conclusive=business_conclusive,
        valuation_conclusive=valuation_conclusive,
        has_high_financial_or_valuation_risk=has_high_financial_or_valuation_risk,
    )

    findings = _build_findings(
        decision_output,
        confidence=confidence,
        conviction_finding_id=conviction_finding_id,
        generated_at=generated_at,
    )
    # `_build_findings` cannot know `conviction.level` before `calculate_conviction`
    # runs (it needs `has_contradicting_evidence`/`has_open_questions`, computed
    # from the same findings it assembles) -- so the Conviction Finding's
    # `details` is populated here, once, by replacing its placeholder entry
    # rather than threading `conviction` into `_build_findings` and computing
    # it twice.
    findings = tuple(
        Finding(
            id=finding.id,
            kind=finding.kind,
            severity=finding.severity,
            details={"level": conviction.level.value},
            evidence_references=finding.evidence_references,
            confidence=finding.confidence,
            producer=finding.producer,
            provenance=finding.provenance,
        )
        if finding.id == conviction_finding_id
        else finding
        for finding in findings
    )

    recommendation = evaluate_recommendation_gate(
        engine_input,
        business_evaluation=decision_output.business_evaluation,
        valuation=decision_output.valuation,
        portfolio_intelligence=decision_output.portfolio_intelligence,
        reasoning=decision_output.reasoning,
        conviction=conviction,
        business_analysis=business_analysis,
        valuation_engine=valuation_engine,
        valuation_support=valuation_support,
        has_high_financial_or_valuation_risk=has_high_financial_or_valuation_risk,
        has_open_questions=bool(open_questions),
        generated_at=generated_at,
        has_real_risk_evidence=has_real_risk_evidence,
    )
    # "Recommendation Backend Step 3": `recommendation.recommendation` is
    # now a real union -- `RecommendationWithheld` (no `direction` field,
    # carries `.reason`) or `ComputedDirectionalRecommendation` (carries
    # `.direction`/`.conviction_level`, no `.reason`). The two produce
    # different Finding kinds; never the same kind with a field read that
    # would only be valid for the other branch.
    if isinstance(recommendation.recommendation, RecommendationWithheld):
        recommendation_finding = Finding(
            id=FindingKind.RECOMMENDATION_WITHHELD.value,
            kind=FindingKind.RECOMMENDATION_WITHHELD,
            severity=FindingSeverity.INFO,
            details={
                "reason": recommendation.recommendation.reason.value,
                "conviction_gate_met": recommendation.conviction_gate_met,
            },
            evidence_references=(),
            confidence=confidence,
            producer=FindingProducer.RECOMMENDATION_GATE,
            provenance=_provenance(
                source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
                source_references=(),
                dependencies=(conviction_finding_id,),
                update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
                generated_at=generated_at,
            ),
        )
    else:
        recommendation_finding = Finding(
            id=FindingKind.RECOMMENDATION_DIRECTION_SELECTED.value,
            kind=FindingKind.RECOMMENDATION_DIRECTION_SELECTED,
            severity=FindingSeverity.INFO,
            details={
                "direction": recommendation.recommendation.direction.value,
                "conviction_level": recommendation.recommendation.conviction_level.value,
            },
            evidence_references=(),
            confidence=confidence,
            producer=FindingProducer.RECOMMENDATION_GATE,
            provenance=_provenance(
                source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
                source_references=(),
                dependencies=(conviction_finding_id,),
                update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
                generated_at=generated_at,
            ),
        )
    findings = (
        findings
        + (recommendation_finding,)
        + _business_category_findings(business_analysis)
        + _valuation_method_findings(valuation_engine)
        + _risk_category_findings(risk_analysis)
    )

    risk_findings = tuple(finding for finding in findings if "risk_category" in finding.details)

    # Investment Case Engine v2 slice: synthesized from the exact same
    # already-computed `business_analysis`/`valuation_engine`/
    # `risk_analysis`/`conviction` this function just assembled -- one
    # source of analytical truth, never a second, independent read of
    # `business_records` or raw provider data.
    synthesis = synthesize_investment_case(
        business_analysis,
        valuation_engine,
        risk_analysis,
        business_facts,
        conviction,
        generated_at=generated_at,
    )

    # Outlook Intelligence Sprint 1 / Long-Term Expected Return v1: from
    # the exact same already-computed business_analysis/valuation_engine
    # /risk_analysis/conviction/synthesis/business_facts this function
    # just assembled -- see outlook.py's own module docstring for why
    # momentum is left UNAVAILABLE at this layer.
    outlook = build_outlook(
        business_analysis=business_analysis,
        valuation_engine=valuation_engine,
        risk_analysis=risk_analysis,
        conviction=conviction,
        synthesis=synthesis,
        business_facts=business_facts,
        generated_at=generated_at,
    )

    # Recommendation / Decision Intelligence Sprint 1: a disclosure-only
    # fact about the two already-computed objects immediately above --
    # never fed back into either. See recommendation_outlook_context.py's
    # own module docstring for the DE-012/DE-014 boundary this respects.
    recommendation_outlook_context = derive_recommendation_outlook_context(
        recommendation.recommendation,
        outlook,
    )

    return CanonicalAnalysis(
        identity=Identity(case_id=str(decision_output.case_id)),
        business=decision_output.business_evaluation,
        valuation=decision_output.valuation,
        portfolio_intelligence=decision_output.portfolio_intelligence,
        reasoning=decision_output.reasoning,
        confidence=confidence,
        risk=RiskSection(findings=risk_findings),
        conviction=conviction,
        analysis_coverage=analysis_coverage,
        recommendation=recommendation,
        findings=findings,
        business_analysis=business_analysis,
        valuation_engine=valuation_engine,
        risk_analysis=risk_analysis,
        open_questions=open_questions,
        synthesis=synthesis,
        outlook=outlook,
        recommendation_outlook_context=recommendation_outlook_context,
        valuation_support=valuation_support,
        catalysts=UnavailableCapability(reason=CapabilityStatus.NOT_YET_IMPLEMENTED),
        scenario_analysis=UnavailableCapability(reason=CapabilityStatus.NOT_YET_IMPLEMENTED),
        generated_at=generated_at,
    )
