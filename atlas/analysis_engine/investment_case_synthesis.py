"""Investment Case Intelligence v1 (Investment Case Engine v2 slice).

Turns the analysis this package has already, genuinely computed --
`BusinessAnalysisResult` (`business.py`), `ValuationEngineResult`
(`valuation/pipeline.py`), `RiskAnalysisResult` (`risk/pipeline.py`),
and the `BusinessFact`s those evaluators themselves read
(`business_facts/extraction.py`) -- into the small set of additional,
user-facing conclusions an Investment Case needs: Strengths, Risks (as
a curated, prioritized short list, distinct from the four-category
`RiskAnalysisResult`), a Growth narrative, Valuation Context, Open
Questions, and a concise Atlas Thesis.

**This is not a second reasoning engine.** Every conclusion below is a
direct, deterministic projection of a `BusinessCategoryStatus`/
`ValuationStatus`/`RiskStatus` an evaluator upstream of this module
already reached -- this module never re-derives WEAK/MODERATE/STRONG,
never reads a `BusinessRecord` or raw provider data, and never
introduces a numeric score, weight, or threshold anywhere. Where it
does perform new computation (`_recent_revenue_trend`), it reuses
`atlas.analysis_engine.growth.classify_metric_trend` verbatim -- the
identical, already-documented sign-comparison rule `evaluate_growth`
itself applies to the full history, applied here to a shorter, "most
recent periods" window only, for narrative specificity `evaluate_growth`
alone cannot express (its own `status` is invariant to *where* in the
history a mixed signal occurs).

**Deterministic, no LLM.** `synthesize_investment_case` is a pure
function: identical inputs always produce an identical
`InvestmentCaseSynthesis`, matching every other stage in this package.
`AtlasThesis.narrative` is assembled from fixed sentence templates keyed
by which structured signals are present for *this* company -- never a
generated-text call, and never hand-written per company. If a future
sprint wants real language-model synthesis, it should read the
structured fields this module already produces (`strengths`, `risks`,
`growth`, `valuation_context`, `open_questions`) as its prompt input,
never raw company data directly -- the same "structured first, language
second" rule this module itself follows.

**Grounding.** Every `CaseHighlight`/`GrowthAnalysis`/`ValuationContext`/
`CaseOpenQuestion` carries the real, already-computed Finding/Fact ids
it was derived from (`evidence_references`) -- never an opaque
conclusion with no traceable origin.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_contracts import BusinessAnalysisResult, BusinessCategory
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as BizStatus
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.growth import MetricTrend, classify_metric_trend
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import RiskAnalysisResult
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind
from atlas.analysis_engine.valuation.contracts import ValuationStatus as ValStatus
from atlas.analysis_engine.valuation.models import ValuationEngineResult

__all__ = [
    "HighlightKind",
    "CaseHighlight",
    "RecentRevenueTrend",
    "GrowthAnalysis",
    "ValuationContext",
    "OpenQuestionOrigin",
    "CaseOpenQuestion",
    "AtlasThesis",
    "InvestmentCaseSynthesis",
    "synthesize_investment_case",
    "derive_case_open_questions",
]

#: The most recent N distinct REVENUE periods considered for the
#: "recent trend" narrative -- a window, not a threshold: it bounds how
#: much history the narrative reads, it does not classify anything by
#: comparison against an invented cutoff. 4 points -> 3 consecutive
#: deltas, enough for `classify_metric_trend` to distinguish "every
#: recent delta positive" from "mixed" without reading the company's
#: entire history for a *recent* statement.
_RECENT_WINDOW_SIZE = 4

_RISK_CATEGORIES_FOR_SYNTHESIS = (RiskCategory.BUSINESS_RISK, RiskCategory.FINANCIAL_RISK, RiskCategory.VALUATION_RISK)
#: THESIS_RISK is deliberately excluded: it is a reinterpretation of the
#: investor's own recorded Evidence/Observations contradicting each
#: other, not a fact about the business or valuation Atlas can gather on
#: its own -- exactly the "primarily improves the COMPANY side, keep
#: investor judgment distinct" boundary this sprint sets.


class HighlightKind(str, Enum):
    """Which already-evaluated category a Strength or Risk highlight
    projects -- always traceable back to one real `BusinessFinding`/
    `ValuationFinding`/`RiskFinding`, never invented."""

    GROWTH = "growth"
    CAPITAL_ALLOCATION = "capital_allocation"
    VALUATION = "valuation"
    BUSINESS_RISK = "business_risk"
    FINANCIAL_RISK = "financial_risk"
    VALUATION_RISK = "valuation_risk"


@dataclass(frozen=True)
class CaseHighlight:
    """One Strength or one Risk -- a direct projection of a single
    already-evaluated category's `STRONG`/`WEAK` (Business categories),
    `UNDERVALUED`/`EXPENSIVE` (Valuation), or `LOW`/`HIGH` (Risk)
    conclusion. Never constructed from `MODERATE`/`FAIRLY_VALUED`/
    `INSUFFICIENT_INPUT` -- those are not strong enough, or not real
    enough, conclusions to present as a highlight (see
    `_business_highlights`/`_valuation_highlights`/`_risk_highlights`
    for the exact, documented threshold each dimension uses)."""

    kind: HighlightKind
    supporting_finding_id: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class RecentRevenueTrend:
    """The most recent revenue trajectory, computed the identical way
    `growth.classify_metric_trend` already classifies the full history
    -- applied here to only the most recent `_RECENT_WINDOW_SIZE`
    periods, so a company whose *overall* Growth status is `MODERATE`
    (mixed across its whole history) can still honestly report "the
    most recent periods have all been positive," or vice versa.
    `None` (via `GrowthAnalysis.recent_trend`) when fewer than two
    recent Revenue facts exist -- never fabricated from too little
    data."""

    trend: MetricTrend
    periods_considered: tuple[str, ...]
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class GrowthAnalysis:
    """The Growth section: `status` is `BusinessAnalysisResult`'s own
    Growth `BusinessFinding.status`, reused verbatim, never recomputed.
    `recent_trend` adds the one genuinely new, narrative-specific fact
    this module computes (see `RecentRevenueTrend`)."""

    status: BizStatus
    recent_trend: RecentRevenueTrend | None
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class ValuationContext:
    """The Valuation section: `fcf_yield_status`/`current_yield` are
    `ValuationEngineResult`'s own `FCF_YIELD_RELATIVE` finding, reused
    verbatim. `scenario_available` names, honestly, whether Atlas has
    scenario-based valuation support for capital deployment -- always
    `False` in v1 (see `atlas.analysis_engine.valuation.scenarios`'s own
    module docstring for why fabricating forward assumptions is
    refused); this field exists so a caller never needs to re-derive
    that fact from `ValuationMethodKind.SCENARIO_BASE`'s own status."""

    fcf_yield_status: ValStatus
    current_yield: float | None
    scenario_available: bool
    evidence_references: tuple[str, ...]


class OpenQuestionOrigin(str, Enum):
    """A closed, growing set -- every member names the exact analytical
    condition that produced it, the same discipline
    `atlas.decision_engine.contracts.OpenQuestionKind` already
    established. Distinct from that enum: these questions are
    Investment-Case-Intelligence-level (company-analysis gaps this
    module curates for the user-facing case), not decision_engine's own
    case-wide gaps (`reasoning.finding.open_questions`, still surfaced
    separately, unmodified, on `CanonicalAnalysis.open_questions`)."""

    GROWTH_INCONCLUSIVE = "growth_inconclusive"
    """Growth's own status is `INSUFFICIENT_INPUT` -- not enough
    revenue/free-cash-flow history to say anything about growth at all."""

    GROWTH_MIXED = "growth_mixed"
    """Growth's own status is `MODERATE` -- revenue and free cash flow
    disagree, or growth itself has been inconsistent across periods:
    "is recent growth durable, or was it one-off."""

    CAPITAL_ALLOCATION_INCONCLUSIVE = "capital_allocation_inconclusive"
    """Capital Allocation's own status is `INSUFFICIENT_INPUT`."""

    CAPITAL_ALLOCATION_WEAK = "capital_allocation_weak"
    """Capital Allocation's own status is `WEAK` -- net dilution or
    rising leverage: "is this temporary or persistent."""

    VALUATION_INCONCLUSIVE = "valuation_inconclusive"
    """`FCF_YIELD_RELATIVE`'s own status is `INSUFFICIENT_INPUT` --
    Atlas cannot yet say whether the current price is cheap or
    expensive relative to this company's own history."""

    VALUATION_EXPENSIVE_VERSUS_GROWTH = "valuation_expensive_versus_growth"
    """Valuation is `EXPENSIVE` while Growth is `STRONG` or `MODERATE`
    (not itself inconclusive) -- "is the current price already
    discounting the growth Atlas is seeing." Never constructed when
    Growth is `INSUFFICIENT_INPUT`: that gap already has its own,
    distinct question (`GROWTH_INCONCLUSIVE`)."""

    SCENARIO_VALUATION_UNAVAILABLE = "scenario_valuation_unavailable"
    """Atlas has no scenario-based (forward-assumption) valuation
    support yet -- always true in v1; see `ValuationContext
    .scenario_available`. Included only when at least one other
    Valuation signal is real (current-yield status is not itself
    `INSUFFICIENT_INPUT`), so this never appears as the sole Valuation
    question when Atlas has no valuation signal at all."""


@dataclass(frozen=True)
class CaseOpenQuestion:
    origin: OpenQuestionOrigin
    reference: str | None
    """The underlying Finding id this question traces back to, when one
    specific Finding caused it (e.g. `business_finding:growth`);
    `None` for a question that spans more than one section (e.g.
    `VALUATION_EXPENSIVE_VERSUS_GROWTH`, which names both in its own
    `origin` instead)."""


class ThesisPosture(str, Enum):
    """Which fixed sentence template `AtlasThesis.narrative` was
    assembled from -- exposed so a test (or a future reader) can assert
    on *which* structured conclusion produced a given narrative without
    parsing prose. Never itself a score: an ordered, documented
    classification of "how much real signal exists," the same
    discipline `conviction.py` already applies to `ConvictionLevel`."""

    INSUFFICIENT_DATA = "insufficient_data"
    """No Strengths and no Risks were identified -- Atlas does not yet
    have enough evaluated signal to describe a case at all."""

    STRENGTHS_AND_RISKS = "strengths_and_risks"
    """At least one Strength and at least one Risk were identified --
    the normal, most-informative case."""

    STRENGTHS_ONLY = "strengths_only"
    RISKS_ONLY = "risks_only"


@dataclass(frozen=True)
class AtlasThesis:
    """A concise, provisional, Atlas-generated synthesis -- never the
    investor's own thesis (`InvestmentCaseComposition.current_thesis`,
    an entirely separate, user-authored field this module never reads
    or writes), never a Decision, never a directional recommendation by
    itself (`CanonicalAnalysis.recommendation` remains the one place a
    direction is ever selected, via `direction_selector.select_direction`,
    untouched by this module)."""

    posture: ThesisPosture
    narrative: str
    supporting_highlight_ids: tuple[str, ...]
    key_uncertainty_origins: tuple[OpenQuestionOrigin, ...]


@dataclass(frozen=True)
class InvestmentCaseSynthesis:
    strengths: tuple[CaseHighlight, ...]
    risks: tuple[CaseHighlight, ...]
    growth: GrowthAnalysis
    valuation_context: ValuationContext
    open_questions: tuple[CaseOpenQuestion, ...]
    atlas_thesis: AtlasThesis
    generated_at: datetime


def _business_finding(business_analysis: BusinessAnalysisResult, category: BusinessCategory):
    return next(f for f in business_analysis.findings if f.kind is category)


def _valuation_finding(valuation_engine: ValuationEngineResult, kind: ValuationMethodKind):
    return next(f for f in valuation_engine.findings if f.kind is kind)


def _risk_finding(risk_analysis: RiskAnalysisResult, category: RiskCategory):
    return next((f for f in risk_analysis.findings if f.category is category), None)


def _business_highlights(business_analysis: BusinessAnalysisResult) -> tuple[list[CaseHighlight], list[CaseHighlight]]:
    """`STRONG` -> a Strength, `WEAK` -> a Risk, for Growth and Capital
    Allocation only -- the two `BusinessCategory` members with a real
    evaluator today (see `business.py`'s own module docstring for why
    the other four stay `INSUFFICIENT_INPUT` on every run and therefore
    never produce a highlight here). `MODERATE` produces neither: a
    mixed signal is real uncertainty, surfaced instead as an Open
    Question (`GROWTH_MIXED`), never forced into a Strength or a Risk."""
    strengths: list[CaseHighlight] = []
    risks: list[CaseHighlight] = []
    for category, kind in (
        (BusinessCategory.GROWTH, HighlightKind.GROWTH),
        (BusinessCategory.CAPITAL_ALLOCATION, HighlightKind.CAPITAL_ALLOCATION),
    ):
        finding = _business_finding(business_analysis, category)
        highlight = CaseHighlight(
            kind=kind,
            supporting_finding_id=finding.id,
            evidence_references=finding.supporting_evidence + finding.contradicting_evidence,
        )
        if finding.status is BizStatus.STRONG:
            strengths.append(highlight)
        elif finding.status is BizStatus.WEAK:
            risks.append(highlight)
    return strengths, risks


def _valuation_highlights(valuation_engine: ValuationEngineResult) -> tuple[list[CaseHighlight], list[CaseHighlight]]:
    """`UNDERVALUED` -> a Strength, `EXPENSIVE` -> a Risk. `FAIRLY_VALUED`
    and `INSUFFICIENT_INPUT` produce neither -- "fairly valued" is a
    real, neutral conclusion, not a strength or a weakness, and an
    inconclusive read is uncertainty, not a finding."""
    strengths: list[CaseHighlight] = []
    risks: list[CaseHighlight] = []
    finding = _valuation_finding(valuation_engine, ValuationMethodKind.FCF_YIELD_RELATIVE)
    highlight = CaseHighlight(
        kind=HighlightKind.VALUATION,
        supporting_finding_id=finding.id,
        evidence_references=finding.supporting_facts + finding.contradicting_facts,
    )
    if finding.status is ValStatus.UNDERVALUED:
        strengths.append(highlight)
    elif finding.status is ValStatus.EXPENSIVE:
        risks.append(highlight)
    return strengths, risks


def _risk_highlights(risk_analysis: RiskAnalysisResult) -> tuple[list[CaseHighlight], list[CaseHighlight]]:
    """`LOW` -> a Strength (resilient economics), `HIGH` -> a Risk.
    `MODERATE`/`INSUFFICIENT_INPUT` produce neither. `THESIS_RISK` is
    excluded (see `_RISK_CATEGORIES_FOR_SYNTHESIS`'s own docstring)."""
    strengths: list[CaseHighlight] = []
    risks: list[CaseHighlight] = []
    kind_by_category = {
        RiskCategory.BUSINESS_RISK: HighlightKind.BUSINESS_RISK,
        RiskCategory.FINANCIAL_RISK: HighlightKind.FINANCIAL_RISK,
        RiskCategory.VALUATION_RISK: HighlightKind.VALUATION_RISK,
    }
    for category in _RISK_CATEGORIES_FOR_SYNTHESIS:
        finding = _risk_finding(risk_analysis, category)
        if finding is None:
            continue
        highlight = CaseHighlight(
            kind=kind_by_category[category],
            supporting_finding_id=finding.id,
            evidence_references=finding.supporting_facts + finding.contradicting_facts,
        )
        if finding.status is RiskStatus.LOW:
            strengths.append(highlight)
        elif finding.status is RiskStatus.HIGH:
            risks.append(highlight)
    return strengths, risks


def _recent_revenue_trend(business_facts: tuple[BusinessFact, ...]) -> RecentRevenueTrend | None:
    """Applies `growth.classify_metric_trend` -- the exact rule
    `evaluate_growth` itself uses -- to only the most recent
    `_RECENT_WINDOW_SIZE` distinct-period Revenue facts. Returns `None`
    when fewer than two recent Revenue facts exist: there is nothing to
    compute a trend from, and this function never falls back to a
    longer window silently (that would just be restating Growth's own
    full-history `status`, not a "recent" fact)."""
    revenue_facts = sorted(
        (fact for fact in business_facts if fact.kind is BusinessFactKind.REVENUE),
        key=lambda f: f.period,
    )
    recent = revenue_facts[-_RECENT_WINDOW_SIZE:]
    if len(recent) < 2:
        return None
    trend, supporting, contradicting = classify_metric_trend(recent)
    return RecentRevenueTrend(
        trend=trend,
        periods_considered=tuple(fact.period for fact in recent),
        evidence_references=tuple(sorted({*supporting, *contradicting})) or tuple(fact.id for fact in recent),
    )


def _growth_analysis(
    business_analysis: BusinessAnalysisResult, business_facts: tuple[BusinessFact, ...]
) -> GrowthAnalysis:
    finding = _business_finding(business_analysis, BusinessCategory.GROWTH)
    return GrowthAnalysis(
        status=finding.status,
        recent_trend=_recent_revenue_trend(business_facts),
        evidence_references=finding.supporting_evidence + finding.contradicting_evidence,
    )


def _valuation_context(valuation_engine: ValuationEngineResult) -> ValuationContext:
    finding = _valuation_finding(valuation_engine, ValuationMethodKind.FCF_YIELD_RELATIVE)
    return ValuationContext(
        fcf_yield_status=finding.status,
        current_yield=finding.current_yield,
        scenario_available=False,
        evidence_references=finding.supporting_facts + finding.contradicting_facts,
    )


def derive_case_open_questions(
    business_analysis: BusinessAnalysisResult, valuation_engine: ValuationEngineResult
) -> tuple[CaseOpenQuestion, ...]:
    """Fixed, documented rule order -- every question named here traces
    to one real analytical condition (Phase requirement: "traceable to
    the underlying analysis condition that caused it"). Never padded to
    reach a target count, and never suppressed to reach one either:
    however many of these conditions are genuinely true for this
    company is exactly how many questions are produced.

    Calibration Phase 4 (Conviction & Capital Allocation Repair):
    promoted from a private function to this package's public surface
    so `atlas.analysis_engine.pipeline.assemble_analysis` can call it
    directly, from the identical `business_analysis`/`valuation_engine`
    values it already holds, to feed Conviction's own
    `has_open_questions` input from Atlas's own analysis-derived open
    questions rather than `decision_engine`'s evidence-*linkage* gap
    list (an investor-history signal -- see this module's own callers
    for the distinction). No behavior changed for this function's
    original caller below; only its visibility widened."""
    growth = _business_finding(business_analysis, BusinessCategory.GROWTH)
    capital_allocation = _business_finding(business_analysis, BusinessCategory.CAPITAL_ALLOCATION)
    valuation = _valuation_finding(valuation_engine, ValuationMethodKind.FCF_YIELD_RELATIVE)

    questions: list[CaseOpenQuestion] = []

    if growth.status is BizStatus.INSUFFICIENT_INPUT:
        questions.append(CaseOpenQuestion(origin=OpenQuestionOrigin.GROWTH_INCONCLUSIVE, reference=growth.id))
    elif growth.status is BizStatus.MODERATE:
        questions.append(CaseOpenQuestion(origin=OpenQuestionOrigin.GROWTH_MIXED, reference=growth.id))

    if capital_allocation.status is BizStatus.INSUFFICIENT_INPUT:
        questions.append(
            CaseOpenQuestion(origin=OpenQuestionOrigin.CAPITAL_ALLOCATION_INCONCLUSIVE, reference=capital_allocation.id)
        )
    elif capital_allocation.status is BizStatus.WEAK:
        questions.append(
            CaseOpenQuestion(origin=OpenQuestionOrigin.CAPITAL_ALLOCATION_WEAK, reference=capital_allocation.id)
        )

    if valuation.status is ValStatus.INSUFFICIENT_INPUT:
        questions.append(CaseOpenQuestion(origin=OpenQuestionOrigin.VALUATION_INCONCLUSIVE, reference=valuation.id))
    else:
        if valuation.status is ValStatus.EXPENSIVE and growth.status in (BizStatus.STRONG, BizStatus.MODERATE):
            questions.append(
                CaseOpenQuestion(origin=OpenQuestionOrigin.VALUATION_EXPENSIVE_VERSUS_GROWTH, reference=None)
            )
        questions.append(CaseOpenQuestion(origin=OpenQuestionOrigin.SCENARIO_VALUATION_UNAVAILABLE, reference=valuation.id))

    return tuple(questions)


def _atlas_thesis(
    strengths: tuple[CaseHighlight, ...],
    risks: tuple[CaseHighlight, ...],
    open_questions: tuple[CaseOpenQuestion, ...],
    conviction: ConvictionAssessment,
) -> AtlasThesis:
    """Assembles a 2-4 sentence narrative from fixed templates, keyed
    only by which structured signals are real for this Case -- no
    per-company hand-written text, no language-model call. Every
    sentence names the same `HighlightKind`/`OpenQuestionOrigin`
    vocabulary already defined above, so the narrative can never claim
    something the structured fields do not also carry."""
    highlight_labels = {
        HighlightKind.GROWTH: "sustained growth across revenue and free cash flow",
        HighlightKind.CAPITAL_ALLOCATION: "disciplined capital allocation",
        HighlightKind.VALUATION: "an undervalued current price relative to this company's own history",
        HighlightKind.BUSINESS_RISK: "resilient underlying business economics",
        HighlightKind.FINANCIAL_RISK: "a low-risk financial position",
        HighlightKind.VALUATION_RISK: "valuation that is not currently stretched",
    }
    risk_labels = {
        HighlightKind.GROWTH: "weakening growth",
        HighlightKind.CAPITAL_ALLOCATION: "capital allocation that is currently working against shareholders",
        HighlightKind.VALUATION: "a current price that looks expensive relative to this company's own history",
        HighlightKind.BUSINESS_RISK: "elevated business risk",
        HighlightKind.FINANCIAL_RISK: "elevated financial risk",
        HighlightKind.VALUATION_RISK: "elevated valuation risk",
    }
    question_labels = {
        OpenQuestionOrigin.GROWTH_INCONCLUSIVE: "whether this business is actually growing",
        OpenQuestionOrigin.GROWTH_MIXED: "whether recent growth is durable",
        OpenQuestionOrigin.CAPITAL_ALLOCATION_INCONCLUSIVE: "how capital is being allocated",
        OpenQuestionOrigin.CAPITAL_ALLOCATION_WEAK: "whether current capital allocation is temporary or persistent",
        OpenQuestionOrigin.VALUATION_INCONCLUSIVE: "whether the current price is cheap or expensive",
        OpenQuestionOrigin.VALUATION_EXPENSIVE_VERSUS_GROWTH: (
            "whether the current price already discounts the growth Atlas is seeing"
        ),
        OpenQuestionOrigin.SCENARIO_VALUATION_UNAVAILABLE: (
            "whether the current price offers attractive expected return under explicit forward assumptions"
        ),
    }

    strength_ids = tuple(h.supporting_finding_id for h in strengths)
    risk_ids = tuple(h.supporting_finding_id for h in risks)
    question_origins = tuple(q.origin for q in open_questions)

    if not strengths and not risks:
        return AtlasThesis(
            posture=ThesisPosture.INSUFFICIENT_DATA,
            narrative=(
                "Atlas does not yet have enough evaluated business, valuation, or risk signal to describe a "
                "case for this company. Available real company data has been gathered, but no dimension has "
                "reached a strong or weak conclusion yet."
            ),
            supporting_highlight_ids=(),
            key_uncertainty_origins=question_origins,
        )

    sentences: list[str] = []
    if strengths:
        sentences.append(
            "The current case is supported primarily by "
            + _join_labels([highlight_labels[h.kind] for h in strengths])
            + "."
        )
    if risks:
        if strengths:
            lede = "The main counterweight is"
        elif len(risks) > 1:
            lede = "The main risks are"
        else:
            lede = "The main risk is"
        sentences.append(lede + " " + _join_labels([risk_labels[h.kind] for h in risks]) + ".")
    if open_questions:
        sentences.append(
            "The most important open question"
            + ("s are" if len(open_questions) > 1 else " is")
            + " "
            + _join_labels([question_labels[origin] for origin in question_origins])
            + "."
        )
    if conviction.level is ConvictionLevel.INSUFFICIENT_EVIDENCE:
        sentences.append(
            "Atlas does not yet have enough recorded investor evidence on this Case to assess conviction; "
            "this thesis reflects the company data alone."
        )

    if strengths and risks:
        posture = ThesisPosture.STRENGTHS_AND_RISKS
    elif strengths:
        posture = ThesisPosture.STRENGTHS_ONLY
    else:
        posture = ThesisPosture.RISKS_ONLY

    return AtlasThesis(
        posture=posture,
        narrative=" ".join(sentences),
        supporting_highlight_ids=strength_ids + risk_ids,
        key_uncertainty_origins=question_origins,
    )


def _join_labels(labels: list[str]) -> str:
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def synthesize_investment_case(
    business_analysis: BusinessAnalysisResult,
    valuation_engine: ValuationEngineResult,
    risk_analysis: RiskAnalysisResult,
    business_facts: tuple[BusinessFact, ...],
    conviction: ConvictionAssessment,
    *,
    generated_at: datetime,
) -> InvestmentCaseSynthesis:
    """Deterministic: identical inputs always produce a deeply equal
    `InvestmentCaseSynthesis`. Reads only already-computed results and
    already-extracted facts -- no `BusinessRecord`, no provider object,
    no wall-clock read, no randomness.
    """
    business_strengths, business_risks = _business_highlights(business_analysis)
    valuation_strengths, valuation_risks = _valuation_highlights(valuation_engine)
    risk_strengths, risk_risks = _risk_highlights(risk_analysis)

    strengths = tuple(business_strengths + valuation_strengths + risk_strengths)
    risks = tuple(business_risks + valuation_risks + risk_risks)

    growth = _growth_analysis(business_analysis, business_facts)
    valuation_context = _valuation_context(valuation_engine)
    open_questions = derive_case_open_questions(business_analysis, valuation_engine)
    atlas_thesis = _atlas_thesis(strengths, risks, open_questions, conviction)

    return InvestmentCaseSynthesis(
        strengths=strengths,
        risks=risks,
        growth=growth,
        valuation_context=valuation_context,
        open_questions=open_questions,
        atlas_thesis=atlas_thesis,
        generated_at=generated_at,
    )
