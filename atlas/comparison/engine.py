from dataclasses import dataclass
from enum import Enum

from atlas.analysis.report import build_investment_report
from atlas.analysis.scores import clamp_score
from atlas.economics import EconomicSignalsEngine
from atlas.evidence import (
    EvidenceAction,
    EvidenceAssessment,
    EvidenceClaim,
    EvidenceInput,
    EvidenceQualityEngine,
    EvidenceSource,
    EvidenceStrength,
)
from atlas.language import (
    AtlasConfidence,
    AtlasFit,
    AtlasLanguageEngine,
    AtlasLanguageReport,
    AtlasRating,
    AtlasRationale,
    AtlasThesis,
    AtlasView,
    ConfidenceLevel,
)
from atlas.market import (
    MarketHealthEngine,
    MarketIndicators,
    MarketRegimeEngine,
    MarketSnapshot,
)
from atlas.monitoring import MonitoringEngine
from atlas.principles import PrinciplesCheck, PrinciplesEngine
from atlas.profile import InvestorProfile, InvestorProfileEngine
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider
from atlas.suitability import SuitabilityEngine, SuitabilityInput
from atlas.themes import ThemeEngine, ThemeInput


class ComparisonRating(str, Enum):
    CLEARER_FIT = "Clearer Fit"
    SIMILAR_QUALITY = "Similar Quality"
    HIGHER_UNCERTAINTY = "Higher Uncertainty"
    DIFFERENT_ROLES = "Different Roles"
    EVIDENCE_GAP = "Evidence Gap"
    UNCLEAR = "Unclear"


@dataclass(frozen=True)
class InvestmentComparisonCandidate:
    name: str
    candidate_type: str
    atlas_rating: str
    atlas_view: str
    atlas_fit: str
    confidence: int
    key_reasons: tuple[str, ...]
    main_risk: str
    evidence_strength: EvidenceStrength
    evidence_assessment: EvidenceAssessment
    monitoring_items: tuple[str, ...]
    portfolio_role: str
    quality_score: int
    risk_score: int
    valuation_sensitivity: str
    cyclicality: str
    theme_exposure: tuple[str, ...]
    macro_sensitivity: str
    language_report: AtlasLanguageReport


@dataclass(frozen=True)
class InvestmentComparisonObservation:
    title: str
    summary: str
    importance: str = "Context"


@dataclass(frozen=True)
class InvestmentComparisonSection:
    title: str
    narrative: str
    observations: tuple[InvestmentComparisonObservation, ...]


@dataclass(frozen=True)
class InvestmentComparisonInput:
    ideas: tuple[str, ...]
    provider: CompanyDataProvider | None = None
    investor_profile: InvestorProfile | None = None
    evidence_inputs: dict[str, EvidenceInput] | None = None
    market_snapshot: MarketSnapshot | None = None


@dataclass(frozen=True)
class InvestmentComparisonReport:
    title: str
    bottom_line: str
    comparison_rating: ComparisonRating
    candidates: tuple[InvestmentComparisonCandidate, ...]
    sections: tuple[InvestmentComparisonSection, ...]
    confidence: int
    language_report: AtlasLanguageReport
    principles_check: PrinciplesCheck


class InvestmentComparisonEngine:
    def __init__(
        self,
        language_engine: AtlasLanguageEngine | None = None,
        evidence_engine: EvidenceQualityEngine | None = None,
        profile_engine: InvestorProfileEngine | None = None,
        suitability_engine: SuitabilityEngine | None = None,
        theme_engine: ThemeEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
        economic_signals_engine: EconomicSignalsEngine | None = None,
        monitoring_engine: MonitoringEngine | None = None,
        principles_engine: PrinciplesEngine | None = None,
    ) -> None:
        self.language_engine = language_engine or AtlasLanguageEngine()
        self.evidence_engine = evidence_engine or EvidenceQualityEngine(self.language_engine)
        self.profile_engine = profile_engine or InvestorProfileEngine()
        self.suitability_engine = suitability_engine or SuitabilityEngine()
        self.theme_engine = theme_engine or ThemeEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()
        self.economic_signals_engine = economic_signals_engine or EconomicSignalsEngine()
        self.monitoring_engine = monitoring_engine or MonitoringEngine()
        self.principles_engine = principles_engine or PrinciplesEngine()

    def compare(
        self,
        comparison_input: InvestmentComparisonInput,
    ) -> InvestmentComparisonReport:
        if len(comparison_input.ideas) < 2:
            raise ValueError("Investment comparison requires at least two ideas.")
        provider = comparison_input.provider or MockCompanyAnalysisProvider()
        profile = (
            comparison_input.investor_profile
            or self.profile_engine.create_default_profile()
        )
        market_regime = self.market_regime_engine.analyze(
            comparison_input.market_snapshot or _default_market_snapshot()
        )
        market_health = self.market_health_engine.analyze()
        economics = self.economic_signals_engine.analyze()
        candidates = tuple(
            self._candidate(
                idea=idea,
                provider=provider,
                profile=profile,
                evidence_inputs=comparison_input.evidence_inputs or {},
            )
            for idea in comparison_input.ideas
        )
        rating = _comparison_rating(candidates)
        confidence = _comparison_confidence(candidates)
        bottom_line = _bottom_line(candidates, rating, profile)
        sections = _sections(
            bottom_line=bottom_line,
            rating=rating,
            candidates=candidates,
            profile=profile,
            market_regime=market_regime,
            market_health=market_health,
            economics=economics,
        )
        language_report = _language_report(
            self.language_engine,
            bottom_line,
            rating,
            sections,
            confidence,
        )
        draft = _render_investment_comparison_without_principles(
            title="Investment Comparison",
            bottom_line=bottom_line,
            rating=rating,
            candidates=candidates,
            sections=sections,
            confidence=confidence,
        )
        return InvestmentComparisonReport(
            title="Investment Comparison",
            bottom_line=bottom_line,
            comparison_rating=rating,
            candidates=candidates,
            sections=sections,
            confidence=confidence,
            language_report=language_report,
            principles_check=self.principles_engine.check(draft),
        )

    def _candidate(
        self,
        idea: str,
        provider: CompanyDataProvider,
        profile: InvestorProfile,
        evidence_inputs: dict[str, EvidenceInput],
    ) -> InvestmentComparisonCandidate:
        normalized = idea.strip()
        evidence = _evidence_for_idea(normalized, evidence_inputs)
        try:
            company_analysis = provider.get_company_analysis(normalized.upper())
        except LookupError:
            try:
                theme = self.theme_engine.analyze(ThemeInput(theme=normalized))
            except ValueError:
                return self._idea_candidate(normalized, profile, evidence)
            return self._theme_candidate(normalized, profile, evidence, theme)

        report = build_investment_report(company_analysis)
        assessment = self.evidence_engine.assess(
            evidence
            or EvidenceInput(
                claim=EvidenceClaim(
                    f"{normalized.upper()} has structured company analysis in Atlas."
                ),
                source=EvidenceSource.EXCHANGE_DATA,
            )
        )
        suitability = self.suitability_engine.assess(
            SuitabilityInput(
                investor_profile=profile,
                ticker=normalized.upper(),
                investment_report=report,
            )
        )
        monitoring = self.monitoring_engine.snapshot_company(normalized.upper(), provider)
        confidence = _candidate_confidence(report.confidence, assessment)
        reasons = (
            f"Quality is {report.quality.score}/100.",
            f"Valuation sensitivity is {_valuation_sensitivity(report.valuation.score)}.",
            f"Profile fit appears {suitability.overall_suitability.value.lower()}.",
        )
        main_risk = f"Risk profile is {report.risk.score}/100 and should be monitored."
        return _candidate(
            language_engine=self.language_engine,
            name=normalized.upper(),
            candidate_type="Company",
            atlas_rating=_rating_from_score(report.atlas_score),
            atlas_view=_view_from_confidence(confidence),
            atlas_fit=suitability.overall_suitability.value,
            confidence=confidence,
            key_reasons=reasons,
            main_risk=main_risk,
            evidence_assessment=assessment,
            monitoring_items=monitoring.monitoring_items,
            portfolio_role=_portfolio_role_for_company(report.quality.score, report.risk.score),
            quality_score=report.quality.score,
            risk_score=report.risk.score,
            valuation_sensitivity=_valuation_sensitivity(report.valuation.score),
            cyclicality="Moderate",
            theme_exposure=_theme_exposure_for_company(normalized.upper()),
            macro_sensitivity="Depends on earnings durability and market conditions.",
        )

    def _theme_candidate(
        self,
        idea: str,
        profile: InvestorProfile,
        evidence: EvidenceInput | None,
        theme,
    ) -> InvestmentComparisonCandidate:
        assessment = self.evidence_engine.assess(
            evidence
            or EvidenceInput(
                claim=EvidenceClaim(f"{theme.theme.value} is a supported Atlas theme."),
                source=EvidenceSource.ANALYST_REPORT,
            )
        )
        suitability = self.suitability_engine.assess(
            SuitabilityInput(investor_profile=profile, theme_analysis=theme)
        )
        confidence = _candidate_confidence(theme.confidence, assessment)
        reasons = (
            theme.summary,
            f"Theme confidence is {theme.confidence}/100.",
            f"Profile fit appears {suitability.overall_suitability.value.lower()}.",
        )
        main_risk = theme.key_risks[0].why_it_matters if theme.key_risks else (
            "Theme evidence can change as source quality improves."
        )
        return _candidate(
            language_engine=self.language_engine,
            name=theme.theme.value,
            candidate_type="Theme",
            atlas_rating=_rating_from_score(theme.confidence),
            atlas_view=_view_from_confidence(confidence),
            atlas_fit=suitability.overall_suitability.value,
            confidence=confidence,
            key_reasons=reasons,
            main_risk=main_risk,
            evidence_assessment=assessment,
            monitoring_items=theme.monitoring_items,
            portfolio_role="Thematic satellite",
            quality_score=theme.confidence,
            risk_score=max(30, 100 - theme.confidence),
            valuation_sensitivity="Indirect",
            cyclicality="Theme-dependent",
            theme_exposure=(theme.theme.value,),
            macro_sensitivity="Depends on capital spending and market conditions.",
        )

    def _idea_candidate(
        self,
        idea: str,
        profile: InvestorProfile,
        evidence: EvidenceInput | None,
    ) -> InvestmentComparisonCandidate:
        assessment = self.evidence_engine.assess(
            evidence
            or EvidenceInput(
                claim=EvidenceClaim(f"{idea} needs stronger structured evidence."),
                source=EvidenceSource.UNKNOWN_SOURCE,
            )
        )
        suitability = self.suitability_engine.assess(SuitabilityInput(profile))
        confidence = _candidate_confidence(45, assessment)
        reasons = (
            "Atlas can frame the idea, but structured company or theme data is limited.",
            f"Evidence strength is {assessment.strength.value.lower()}.",
            f"Profile fit appears {suitability.overall_suitability.value.lower()}.",
        )
        return _candidate(
            language_engine=self.language_engine,
            name=idea,
            candidate_type="Idea",
            atlas_rating="Unclear",
            atlas_view="Unclear",
            atlas_fit=suitability.overall_suitability.value,
            confidence=confidence,
            key_reasons=reasons,
            main_risk="Not enough reliable information for a high-confidence assessment.",
            evidence_assessment=assessment,
            monitoring_items=assessment.rationale.additional_data_needed,
            portfolio_role="Exploration idea",
            quality_score=45,
            risk_score=65,
            valuation_sensitivity="Unknown",
            cyclicality="Unknown",
            theme_exposure=("Unclear",),
            macro_sensitivity="Not enough information for a high-confidence assessment.",
        )


def render_investment_comparison(report: InvestmentComparisonReport) -> str:
    return _render_investment_comparison_without_principles(
        title=report.title,
        bottom_line=report.bottom_line,
        rating=report.comparison_rating,
        candidates=report.candidates,
        sections=report.sections,
        confidence=report.confidence,
    )


def demo_investment_comparison_input(
    provider: CompanyDataProvider | None = None,
) -> InvestmentComparisonInput:
    return InvestmentComparisonInput(
        ideas=("NVDA", "MSFT", "AI infrastructure"),
        provider=provider or MockCompanyAnalysisProvider(),
        evidence_inputs={
            "AI INFRASTRUCTURE": EvidenceInput(
                claim=EvidenceClaim("AI infrastructure remains a supported Atlas theme."),
                source=EvidenceSource.ANALYST_REPORT,
            )
        },
    )


def _render_investment_comparison_without_principles(
    title: str,
    bottom_line: str,
    rating: ComparisonRating,
    candidates: tuple[InvestmentComparisonCandidate, ...],
    sections: tuple[InvestmentComparisonSection, ...],
    confidence: int,
) -> str:
    lines = [
        title,
        "",
        "Bottom Line",
        bottom_line,
        "",
        f"Comparison Rating: {rating.value}",
        "Rating Type: Contextual comparison, not an investment instruction.",
        f"Confidence: {confidence}/100",
        "",
        "Candidate Summaries",
    ]
    for candidate in candidates:
        lines.extend(
            [
                f"- {candidate.name} ({candidate.candidate_type})",
                f"  Atlas Rating: {candidate.atlas_rating}",
                f"  Atlas View: {candidate.atlas_view}",
                f"  Atlas Fit: {candidate.atlas_fit}",
                f"  Confidence: {candidate.confidence}/100",
                f"  Evidence Strength: {candidate.evidence_strength.value}",
                f"  Main Risk: {candidate.main_risk}",
                "  Key Reasons:",
                *[f"  - {reason}" for reason in candidate.key_reasons[:3]],
                "  What Atlas Is Monitoring:",
                *[f"  - {item}" for item in candidate.monitoring_items[:3]],
            ]
        )
    for section in sections:
        lines.extend(["", section.title, section.narrative])
        lines.extend(
            f"- {item.title}: {item.summary} ({item.importance})"
            for item in section.observations
        )
    lines.extend(
        [
            "",
            "Research Framing",
            (
                "This is deterministic comparison context for research and education. "
                "It is not personalized financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _candidate(
    language_engine: AtlasLanguageEngine,
    name: str,
    candidate_type: str,
    atlas_rating: str,
    atlas_view: str,
    atlas_fit: str,
    confidence: int,
    key_reasons: tuple[str, ...],
    main_risk: str,
    evidence_assessment: EvidenceAssessment,
    monitoring_items: tuple[str, ...],
    portfolio_role: str,
    quality_score: int,
    risk_score: int,
    valuation_sensitivity: str,
    cyclicality: str,
    theme_exposure: tuple[str, ...],
    macro_sensitivity: str,
) -> InvestmentComparisonCandidate:
    language_report = language_engine.build_report(
        rating=AtlasRating(
            value=atlas_rating,
            explanation="Candidate rating reflects context, fit, and evidence quality.",
        ),
        view=AtlasView(value=atlas_view, explanation="View depends on role and evidence."),
        fit=AtlasFit(value=atlas_fit, explanation="Fit depends on investor context."),
        confidence=AtlasConfidence(
            overall_confidence=confidence,
            confidence_level=_confidence_level(confidence),
            key_confidence_drivers=key_reasons,
            uncertainty_drivers=(main_risk, evidence_assessment.rationale.verifiability),
            missing_information=evidence_assessment.rationale.additional_data_needed,
        ),
        thesis=AtlasThesis(
            current_thesis=f"{name} serves a {portfolio_role.lower()} role.",
            supporting_evidence=key_reasons,
            counter_arguments=(main_risk,),
            what_could_change_view=_candidate_change_view(evidence_assessment),
            what_atlas_is_monitoring=monitoring_items,
        ),
        rationale=AtlasRationale(
            bottom_line=f"{name} appears context-dependent and evidence-sensitive.",
            key_reasons=key_reasons,
            main_risk=main_risk,
            optional_follow_up_questions=(
                "Is the intended portfolio role core, satellite, income, or exploration?",
                "Would stronger evidence change the comparison?",
            ),
        ),
        engines_used=("Investment Comparison Engine", "Atlas Language Engine"),
    )
    return InvestmentComparisonCandidate(
        name=name,
        candidate_type=candidate_type,
        atlas_rating=atlas_rating,
        atlas_view=atlas_view,
        atlas_fit=atlas_fit,
        confidence=confidence,
        key_reasons=key_reasons,
        main_risk=main_risk,
        evidence_strength=evidence_assessment.strength,
        evidence_assessment=evidence_assessment,
        monitoring_items=monitoring_items,
        portfolio_role=portfolio_role,
        quality_score=quality_score,
        risk_score=risk_score,
        valuation_sensitivity=valuation_sensitivity,
        cyclicality=cyclicality,
        theme_exposure=theme_exposure,
        macro_sensitivity=macro_sensitivity,
        language_report=language_report,
    )


def _sections(
    bottom_line: str,
    rating: ComparisonRating,
    candidates: tuple[InvestmentComparisonCandidate, ...],
    profile: InvestorProfile,
    market_regime,
    market_health,
    economics,
) -> tuple[InvestmentComparisonSection, ...]:
    return (
        _section("Bottom Line", bottom_line, (("Summary", bottom_line, "High"),)),
        _section(
            "Comparison Rating",
            "The rating is traceable to fit, evidence quality, and candidate spread.",
            (("Rating", rating.value, "High"),),
        ),
        _key_differences_section(candidates),
        _investor_fit_section(candidates, profile),
        _evidence_quality_section(candidates),
        _theme_market_section(candidates, market_regime, market_health, economics),
        _portfolio_role_section(candidates),
        _change_view_section(candidates),
        _suggested_questions_section(candidates),
        _full_reasoning_section(candidates),
    )


def _section(
    title: str,
    narrative: str,
    observations: tuple[tuple[str, str, str], ...],
) -> InvestmentComparisonSection:
    return InvestmentComparisonSection(
        title=title,
        narrative=narrative,
        observations=tuple(
            InvestmentComparisonObservation(item_title, summary, importance)
            for item_title, summary, importance in observations
        ),
    )


def _key_differences_section(
    candidates: tuple[InvestmentComparisonCandidate, ...],
) -> InvestmentComparisonSection:
    quality_leader = max(candidates, key=lambda candidate: candidate.quality_score)
    risk_leader = min(candidates, key=lambda candidate: candidate.risk_score)
    evidence_leader = max(
        candidates,
        key=lambda candidate: _evidence_score(candidate.evidence_strength),
    )
    observations = (
        (
            "Business Quality",
            f"{quality_leader.name} has the clearest quality signal.",
            "High",
        ),
        (
            "Risk Profile",
            f"{risk_leader.name} appears less risk-sensitive in this comparison.",
            "High",
        ),
        (
            "Evidence Quality",
            f"{evidence_leader.name} has the strongest current evidence signal.",
            "High",
        ),
        (
            "Valuation Sensitivity",
            "; ".join(f"{c.name}: {c.valuation_sensitivity}" for c in candidates),
            "Worth monitoring",
        ),
        (
            "Cyclicality",
            "; ".join(f"{c.name}: {c.cyclicality}" for c in candidates),
            "Context",
        ),
    )
    return _section(
        "Key Differences",
        "Atlas compares role, evidence, quality, risk, and market sensitivity.",
        observations,
    )


def _investor_fit_section(
    candidates: tuple[InvestmentComparisonCandidate, ...],
    profile: InvestorProfile,
) -> InvestmentComparisonSection:
    fit_candidate = max(candidates, key=lambda candidate: candidate.confidence)
    exploration = max(candidates, key=lambda candidate: candidate.risk_score)
    observations = (
        (
            "Conservative Long-Term Investor",
            f"{fit_candidate.name} appears better aligned if stability matters most.",
            "Context",
        ),
        (
            "Balanced Long-Term Investor",
            f"{fit_candidate.name} may fit better if the role is durable compounding.",
            "Context",
        ),
        (
            "Growth-Oriented Investor",
            f"{_highest_quality(candidates).name} appears more quality-oriented.",
            "Context",
        ),
        (
            "High-Risk Exploration Allocation",
            f"{exploration.name} may fit better only if volatility is intentional.",
            "Worth monitoring",
        ),
        (
            "Current Profile",
            (
                f"Current profile is {profile.risk_tolerance.value} risk tolerance "
                f"with {profile.time_horizon.value} horizon."
            ),
            "High",
        ),
    )
    return _section(
        "Investor Fit",
        "The best investment depends on investor context and intended portfolio role.",
        observations,
    )


def _evidence_quality_section(
    candidates: tuple[InvestmentComparisonCandidate, ...],
) -> InvestmentComparisonSection:
    observations = tuple(
        (
            candidate.name,
            _evidence_summary(candidate),
            "High" if candidate.evidence_strength in STRONG_EVIDENCE else "May deserve attention",
        )
        for candidate in candidates
    )
    return _section(
        "Evidence Quality",
        "Atlas weighs stronger, more verifiable evidence above information volume.",
        observations,
    )


def _theme_market_section(
    candidates: tuple[InvestmentComparisonCandidate, ...],
    market_regime,
    market_health,
    economics,
) -> InvestmentComparisonSection:
    observations = tuple(
        (
            candidate.name,
            (
                f"Themes: {', '.join(candidate.theme_exposure)}. "
                f"Macro sensitivity: {candidate.macro_sensitivity}"
            ),
            "Context",
        )
        for candidate in candidates
    )
    return _section(
        "Theme and Market Context",
        (
            f"Current regime is {market_regime.regime.value}; market health is "
            f"{market_health.overall_market_health}; economic signals are "
            f"{economics.overall_economic_health}."
        ),
        observations,
    )


def _portfolio_role_section(
    candidates: tuple[InvestmentComparisonCandidate, ...],
) -> InvestmentComparisonSection:
    return _section(
        "Portfolio Role",
        "Atlas compares what each idea could do inside a portfolio.",
        tuple((candidate.name, candidate.portfolio_role, "Context") for candidate in candidates),
    )


def _change_view_section(
    candidates: tuple[InvestmentComparisonCandidate, ...],
) -> InvestmentComparisonSection:
    observations = tuple(
        (
            candidate.name,
            "; ".join(_candidate_change_view(candidate.evidence_assessment)[:3]),
            "Worth monitoring",
        )
        for candidate in candidates
    )
    return _section(
        "What Could Change Atlas' View",
        "Atlas changes its mind when evidence, profile, or market context changes.",
        observations,
    )


def _suggested_questions_section(
    candidates: tuple[InvestmentComparisonCandidate, ...],
) -> InvestmentComparisonSection:
    questions = [
        "Is this comparison for a core portfolio role or a satellite portfolio role?",
        "Is the goal stability, growth, income or theme exposure?",
    ]
    if any(candidate.risk_score >= 65 for candidate in candidates):
        questions.append("Is the higher-risk idea meant to be a small exploration allocation?")
    if any(candidate.evidence_strength not in STRONG_EVIDENCE for candidate in candidates):
        questions.append("Would stronger source quality materially change the comparison?")
    return _section(
        "Suggested Questions",
        "Atlas only asks questions when answers could materially change the comparison.",
        tuple(("Question", question, "Could improve confidence") for question in questions),
    )


def _full_reasoning_section(
    candidates: tuple[InvestmentComparisonCandidate, ...],
) -> InvestmentComparisonSection:
    observations = (
        ("Assumptions", "Inputs are deterministic and structured.", "Context"),
        (
            "Engines Used",
            (
                "Atlas Language, Evidence Quality, Investor Profile, Suitability, "
                "Theme, Market, Economic Signals, Monitoring, and Principles engines."
            ),
            "Context",
        ),
        (
            "Signals Considered",
            "Quality, risk profile, valuation sensitivity, cyclicality, fit, and evidence.",
            "High",
        ),
        (
            "Missing Information",
            _missing_information(candidates),
            "May deserve attention",
        ),
        (
            "Counterarguments",
            "; ".join(candidate.main_risk for candidate in candidates[:3]),
            "Worth monitoring",
        ),
    )
    return _section(
        "Full Reasoning",
        "Full reasoning exposes assumptions, evidence limits, and confidence drivers.",
        observations,
    )


def _language_report(
    language_engine: AtlasLanguageEngine,
    bottom_line: str,
    rating: ComparisonRating,
    sections: tuple[InvestmentComparisonSection, ...],
    confidence: int,
) -> AtlasLanguageReport:
    return language_engine.build_report(
        rating=AtlasRating(
            value=rating.value,
            explanation="Comparison rating reflects fit, evidence quality, and role clarity.",
        ),
        view=AtlasView(value="Balanced", explanation=bottom_line),
        fit=AtlasFit(
            value="Moderate Fit",
            explanation="Fit depends on investor profile and intended portfolio role.",
        ),
        confidence=AtlasConfidence(
            overall_confidence=confidence,
            confidence_level=_confidence_level(confidence),
            key_confidence_drivers=_section_summaries(sections, "Key Differences"),
            uncertainty_drivers=_section_summaries(sections, "Evidence Quality"),
            missing_information=_section_summaries(sections, "Suggested Questions"),
        ),
        thesis=AtlasThesis(
            current_thesis=bottom_line,
            supporting_evidence=_section_summaries(sections, "Key Differences"),
            counter_arguments=_section_summaries(sections, "Full Reasoning"),
            what_could_change_view=_section_summaries(
                sections,
                "What Could Change Atlas' View",
            ),
            what_atlas_is_monitoring=_section_summaries(sections, "Theme and Market Context"),
        ),
        rationale=AtlasRationale(
            bottom_line=bottom_line,
            key_reasons=(
                "The comparison separates fit, role, and evidence quality.",
                "The comparison avoids universal winner language.",
                "The comparison explains uncertainty and missing information.",
            ),
            main_risk="The main risk is comparing ideas without enough source quality.",
            optional_follow_up_questions=_section_summaries(sections, "Suggested Questions"),
        ),
        engines_used=("Investment Comparison Engine", "Atlas Language Engine"),
    )


def _bottom_line(
    candidates: tuple[InvestmentComparisonCandidate, ...],
    rating: ComparisonRating,
    profile: InvestorProfile,
) -> str:
    leader = max(candidates, key=lambda candidate: (candidate.confidence, candidate.quality_score))
    alternate = min(candidates, key=lambda candidate: candidate.confidence)
    return (
        f"Current evidence suggests {leader.name} appears better aligned for a "
        f"{profile.risk_tolerance.value.lower()} investor with a "
        f"{profile.time_horizon.value} horizon, while {alternate.name} appears more "
        "evidence-sensitive. The difference is not that one is universally better; "
        "they may serve a different purpose depending on portfolio role."
    )


def _comparison_rating(
    candidates: tuple[InvestmentComparisonCandidate, ...],
) -> ComparisonRating:
    confidence_spread = max(c.confidence for c in candidates) - min(
        c.confidence for c in candidates
    )
    evidence_gaps = sum(c.evidence_strength not in STRONG_EVIDENCE for c in candidates)
    roles = {candidate.portfolio_role for candidate in candidates}
    quality_spread = max(c.quality_score for c in candidates) - min(
        c.quality_score for c in candidates
    )
    if evidence_gaps >= len(candidates):
        return ComparisonRating.EVIDENCE_GAP
    if confidence_spread >= 20:
        return ComparisonRating.CLEARER_FIT
    if evidence_gaps:
        return ComparisonRating.HIGHER_UNCERTAINTY
    if len(roles) > 1 and quality_spread < 15:
        return ComparisonRating.DIFFERENT_ROLES
    if quality_spread <= 8:
        return ComparisonRating.SIMILAR_QUALITY
    return ComparisonRating.UNCLEAR


def _comparison_confidence(candidates: tuple[InvestmentComparisonCandidate, ...]) -> int:
    average = round(sum(candidate.confidence for candidate in candidates) / len(candidates))
    evidence_penalty = sum(
        1 for candidate in candidates if candidate.evidence_strength not in STRONG_EVIDENCE
    ) * 4
    return clamp_score(average - evidence_penalty)


def _candidate_confidence(base_confidence: int, assessment: EvidenceAssessment) -> int:
    return clamp_score(base_confidence + assessment.confidence_impact)


def _evidence_for_idea(
    idea: str,
    evidence_inputs: dict[str, EvidenceInput],
) -> EvidenceInput | None:
    return evidence_inputs.get(idea.upper())


def _candidate_change_view(assessment: EvidenceAssessment) -> tuple[str, ...]:
    changes = [
        "Stronger financial evidence.",
        "Change in investor profile.",
        "Market regime shift.",
    ]
    if assessment.strength not in STRONG_EVIDENCE:
        changes.insert(0, "Better source quality.")
    if assessment.should_change_view:
        changes.insert(0, "Thesis invalidation from stronger evidence.")
    return tuple(changes)


def _evidence_summary(candidate: InvestmentComparisonCandidate) -> str:
    if candidate.evidence_strength not in STRONG_EVIDENCE:
        return (
            "The current evidence is not strong enough to support a "
            "high-confidence assessment."
        )
    return (
        f"Evidence is {candidate.evidence_strength.value.lower()} and supports "
        "a more structured comparison."
    )


def _missing_information(candidates: tuple[InvestmentComparisonCandidate, ...]) -> str:
    missing = [
        item
        for candidate in candidates
        for item in candidate.evidence_assessment.rationale.additional_data_needed
        if "No major" not in item
    ]
    if missing:
        return missing[0]
    return "No major missing information was detected for this deterministic comparison."


def _rating_from_score(score: int) -> str:
    if score >= 82:
        return "Constructive"
    if score >= 65:
        return "Balanced"
    if score >= 50:
        return "Cautious"
    return "Unclear"


def _view_from_confidence(confidence: int) -> str:
    if confidence >= 78:
        return "Constructive"
    if confidence >= 58:
        return "Balanced"
    return "Unclear"


def _confidence_level(score: int) -> ConfidenceLevel:
    if score >= 90:
        return ConfidenceLevel.VERY_HIGH
    if score >= 75:
        return ConfidenceLevel.HIGH
    if score >= 55:
        return ConfidenceLevel.MODERATE
    if score >= 35:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.VERY_LOW


def _valuation_sensitivity(valuation_score: int) -> str:
    if valuation_score >= 80:
        return "Lower valuation sensitivity"
    if valuation_score >= 65:
        return "Moderate valuation sensitivity"
    return "Higher valuation sensitivity"


def _portfolio_role_for_company(quality_score: int, risk_score: int) -> str:
    if quality_score >= 85 and risk_score <= 45:
        return "Core compounder"
    if quality_score >= 80:
        return "Quality growth exposure"
    if risk_score >= 65:
        return "High-risk exploration idea"
    return "Thematic satellite"


def _theme_exposure_for_company(ticker: str) -> tuple[str, ...]:
    exposures = {
        "NVDA": ("AI infrastructure", "Semiconductors"),
        "AMD": ("AI infrastructure", "Semiconductors"),
        "MSFT": ("AI infrastructure", "Cloud infrastructure"),
        "AAPL": ("Consumer technology",),
        "EVO": ("Digital entertainment",),
    }
    return exposures.get(ticker.upper(), ("Unclear",))


def _highest_quality(
    candidates: tuple[InvestmentComparisonCandidate, ...],
) -> InvestmentComparisonCandidate:
    return max(candidates, key=lambda candidate: candidate.quality_score)


def _evidence_score(strength: EvidenceStrength) -> int:
    scores = {
        EvidenceStrength.VERY_STRONG: 92,
        EvidenceStrength.STRONG: 84,
        EvidenceStrength.MODERATE: 68,
        EvidenceStrength.WEAK: 42,
        EvidenceStrength.VERY_WEAK: 28,
        EvidenceStrength.UNVERIFIED: 20,
        EvidenceStrength.INSUFFICIENT: 12,
    }
    return scores[strength]


def _section_summaries(
    sections: tuple[InvestmentComparisonSection, ...],
    title: str,
) -> tuple[str, ...]:
    for section in sections:
        if section.title == title:
            return tuple(item.summary for item in section.observations[:4])
    return ("Not enough information for a high-confidence assessment.",)


def _default_market_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        indicators=MarketIndicators(
            sp500_drawdown=-0.04,
            nasdaq_drawdown=-0.07,
            vix=19,
            interest_rate_trend="stable",
            inflation_trend="stable",
        ),
        source="deterministic-investment-comparison-placeholder",
    )


STRONG_EVIDENCE = {
    EvidenceStrength.VERY_STRONG,
    EvidenceStrength.STRONG,
}
