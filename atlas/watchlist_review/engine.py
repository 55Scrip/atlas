import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from atlas.analysis.watchlist import Watchlist, WatchlistItem
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
from atlas.themes import ThemeAnalysis, ThemeEngine, ThemeInput


class WatchlistReviewRating(str, Enum):
    HIGH_QUALITY = "High Quality Watchlist"
    FOCUSED = "Focused Watchlist"
    BALANCED = "Balanced Watchlist"
    NOISY = "Noisy Watchlist"
    UNCLEAR = "Unclear Watchlist"


@dataclass(frozen=True)
class WatchlistReviewItem:
    name: str
    item_type: str
    relevance_score: int
    summary: str
    evidence_assessment: EvidenceAssessment
    appears_relevant: bool
    requires_better_evidence: bool
    potential_noise: bool


@dataclass(frozen=True)
class WatchlistReviewObservation:
    title: str
    summary: str
    importance: str = "Context"


@dataclass(frozen=True)
class WatchlistReviewSection:
    title: str
    narrative: str
    observations: tuple[WatchlistReviewObservation, ...]


@dataclass(frozen=True)
class WatchlistReviewInput:
    watchlist: Watchlist
    provider: CompanyDataProvider | None = None
    investor_profile: InvestorProfile | None = None
    idea_labels: tuple[str, ...] = ()
    evidence_inputs: dict[str, EvidenceInput] | None = None
    theme_names: tuple[str, ...] = (
        "AI infrastructure",
        "Semiconductors",
        "Energy transition",
    )
    market_snapshot: MarketSnapshot | None = None


@dataclass(frozen=True)
class WatchlistReviewReport:
    title: str
    watchlist_name: str
    bottom_line: str
    atlas_rating: WatchlistReviewRating
    items: tuple[WatchlistReviewItem, ...]
    sections: tuple[WatchlistReviewSection, ...]
    confidence: int
    language_report: AtlasLanguageReport
    principles_check: PrinciplesCheck


class WatchlistReviewEngine:
    def __init__(
        self,
        language_engine: AtlasLanguageEngine | None = None,
        evidence_engine: EvidenceQualityEngine | None = None,
        theme_engine: ThemeEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
        economic_signals_engine: EconomicSignalsEngine | None = None,
        monitoring_engine: MonitoringEngine | None = None,
        suitability_engine: SuitabilityEngine | None = None,
        profile_engine: InvestorProfileEngine | None = None,
        principles_engine: PrinciplesEngine | None = None,
    ) -> None:
        self.language_engine = language_engine or AtlasLanguageEngine()
        self.evidence_engine = evidence_engine or EvidenceQualityEngine(self.language_engine)
        self.theme_engine = theme_engine or ThemeEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()
        self.economic_signals_engine = economic_signals_engine or EconomicSignalsEngine()
        self.monitoring_engine = monitoring_engine or MonitoringEngine()
        self.suitability_engine = suitability_engine or SuitabilityEngine()
        self.profile_engine = profile_engine or InvestorProfileEngine()
        self.principles_engine = principles_engine or PrinciplesEngine()

    def review(self, review_input: WatchlistReviewInput) -> WatchlistReviewReport:
        provider = review_input.provider or MockCompanyAnalysisProvider()
        profile = review_input.investor_profile or self.profile_engine.create_default_profile()
        supported_watchlist, unsupported_items = _split_supported_items(
            review_input.watchlist,
            provider,
        )
        monitoring_snapshot = (
            self.monitoring_engine.snapshot_watchlist(supported_watchlist)
            if supported_watchlist.items
            else None
        )
        themes = _theme_analyses(self.theme_engine, review_input.theme_names)
        market_regime = self.market_regime_engine.analyze(
            review_input.market_snapshot or _default_market_snapshot()
        )
        market_health = self.market_health_engine.analyze()
        economics = self.economic_signals_engine.analyze()
        suitability = self.suitability_engine.assess(SuitabilityInput(profile))
        items = _review_items(
            watchlist=review_input.watchlist,
            idea_labels=review_input.idea_labels,
            unsupported_items=unsupported_items,
            watchlist_analysis=None,
            evidence_inputs=review_input.evidence_inputs or {},
            evidence_engine=self.evidence_engine,
        )
        rating = _watchlist_rating(items, profile, market_health.overall_score)
        confidence = _confidence(items, monitoring_snapshot)
        bottom_line = _bottom_line(review_input.watchlist.name, rating, items, confidence)
        sections = _sections(
            bottom_line=bottom_line,
            rating=rating,
            items=items,
            profile=profile,
            themes=themes,
            market_regime=market_regime,
            market_health=market_health,
            economics=economics,
            monitoring_snapshot=monitoring_snapshot,
            suitability_summary=suitability.overall_suitability.value,
        )
        language_report = _language_report(
            self.language_engine,
            rating,
            bottom_line,
            sections,
            confidence,
        )
        draft = _render_watchlist_review_without_principles(
            title="Atlas Watchlist Review",
            watchlist_name=review_input.watchlist.name,
            bottom_line=bottom_line,
            rating=rating,
            sections=sections,
            confidence=confidence,
        )
        return WatchlistReviewReport(
            title="Atlas Watchlist Review",
            watchlist_name=review_input.watchlist.name,
            bottom_line=bottom_line,
            atlas_rating=rating,
            items=items,
            sections=sections,
            confidence=confidence,
            language_report=language_report,
            principles_check=self.principles_engine.check(draft),
        )


def render_watchlist_review(report: WatchlistReviewReport) -> str:
    return _render_watchlist_review_without_principles(
        title=report.title,
        watchlist_name=report.watchlist_name,
        bottom_line=report.bottom_line,
        rating=report.atlas_rating,
        sections=report.sections,
        confidence=report.confidence,
    )


def demo_watchlist_review_input(
    provider: CompanyDataProvider | None = None,
    investor_profile: InvestorProfile | None = None,
) -> WatchlistReviewInput:
    watchlist = Watchlist.from_mapping(
        {
            "name": "Atlas Demo Watchlist",
            "tickers": ["NVDA", "AMD", "MSFT"],
        }
    )
    evidence_inputs = {
        "AI POWER BOTTLENECK": EvidenceInput(
            claim=EvidenceClaim("Social posts claim AI power constraints are worsening."),
            source=EvidenceSource.SOCIAL_MEDIA_POST,
        )
    }
    return WatchlistReviewInput(
        watchlist=watchlist,
        provider=provider or MockCompanyAnalysisProvider(),
        investor_profile=investor_profile,
        idea_labels=("AI power bottleneck",),
        evidence_inputs=evidence_inputs,
    )


def watchlist_review_input_from_json_file(
    path: Path,
    provider: CompanyDataProvider | None = None,
    investor_profile: InvestorProfile | None = None,
) -> WatchlistReviewInput:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError("Watchlist review JSON must contain an object.")
    return watchlist_review_input_from_mapping(
        payload,
        provider=provider,
        investor_profile=investor_profile,
    )


def watchlist_review_input_from_mapping(
    payload: dict[str, Any],
    provider: CompanyDataProvider | None = None,
    investor_profile: InvestorProfile | None = None,
) -> WatchlistReviewInput:
    watchlist = Watchlist.from_mapping(payload)
    idea_labels = tuple(
        str(item).strip()
        for key in ("ideas", "themes", "etfs")
        for item in payload.get(key, [])
        if str(item).strip()
    )
    return WatchlistReviewInput(
        watchlist=watchlist,
        provider=provider or MockCompanyAnalysisProvider(),
        investor_profile=investor_profile,
        idea_labels=idea_labels,
        evidence_inputs=_evidence_inputs_from_mapping(payload),
        theme_names=_theme_names_from_mapping(payload),
    )


def _render_watchlist_review_without_principles(
    title: str,
    watchlist_name: str,
    bottom_line: str,
    rating: WatchlistReviewRating,
    sections: tuple[WatchlistReviewSection, ...],
    confidence: int,
) -> str:
    lines = [
        title,
        "",
        f"Watchlist: {watchlist_name}",
        "",
        "Bottom Line",
        bottom_line,
        "",
        f"Atlas Watchlist Rating: {rating.value}",
        "Rating Type: Contextual watchlist assessment, not an investment instruction.",
        f"Confidence: {confidence}/100",
    ]
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
                "This is deterministic watchlist context for research and education. "
                "It is not personalized financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _split_supported_items(
    watchlist: Watchlist,
    provider: CompanyDataProvider,
) -> tuple[Watchlist, tuple[WatchlistItem, ...]]:
    supported = []
    unsupported = []
    for item in watchlist.items:
        try:
            provider.get_company_analysis(item.ticker)
            supported.append(item)
        except LookupError:
            unsupported.append(item)
    return (
        Watchlist(name=watchlist.name, items=tuple(supported)),
        tuple(unsupported),
    )


def _theme_analyses(
    theme_engine: ThemeEngine,
    theme_names: tuple[str, ...],
) -> tuple[ThemeAnalysis, ...]:
    analyses = []
    for name in theme_names[:4]:
        try:
            analyses.append(theme_engine.analyze(ThemeInput(theme=name)))
        except ValueError:
            continue
    return tuple(analyses)


def _review_items(
    watchlist: Watchlist,
    idea_labels: tuple[str, ...],
    unsupported_items: tuple[WatchlistItem, ...],
    watchlist_analysis,
    evidence_inputs: dict[str, EvidenceInput],
    evidence_engine: EvidenceQualityEngine,
) -> tuple[WatchlistReviewItem, ...]:
    items: list[WatchlistReviewItem] = []
    unsupported = {item.ticker for item in unsupported_items}
    for watchlist_item in watchlist.items:
        report = (
            watchlist_analysis.reports.get(watchlist_item.ticker)
            if watchlist_analysis
            else None
        )
        evidence = _evidence_for_item(
            watchlist_item.ticker,
            evidence_inputs,
            report is not None,
        )
        assessment = evidence_engine.assess(evidence)
        items.append(
            _review_item_from_assessment(
                name=watchlist_item.ticker,
                item_type="Company" if watchlist_item.ticker not in unsupported else "Idea",
                assessment=assessment,
                atlas_score=report.atlas_score if report is not None else None,
                confidence=report.confidence if report is not None else None,
            )
        )
    for idea in idea_labels:
        evidence = _evidence_for_item(idea, evidence_inputs, supported=False)
        assessment = evidence_engine.assess(evidence)
        items.append(
            _review_item_from_assessment(
                name=idea,
                item_type=_idea_type(idea),
                assessment=assessment,
                atlas_score=None,
                confidence=None,
            )
        )
    return tuple(sorted(items, key=lambda item: (-item.relevance_score, item.name.lower())))


def _review_item_from_assessment(
    name: str,
    item_type: str,
    assessment: EvidenceAssessment,
    atlas_score: int | None,
    confidence: int | None,
) -> WatchlistReviewItem:
    evidence_bonus = _evidence_score(assessment.strength)
    base_score = atlas_score if atlas_score is not None else 45
    relevance = round((base_score * 0.65) + (evidence_bonus * 0.25) + ((confidence or 50) * 0.10))
    requires_better = assessment.action in {
        EvidenceAction.REQUEST_SOURCE,
        EvidenceAction.INSUFFICIENT_FOR_ASSESSMENT,
    }
    potential_noise = assessment.strength in {
        EvidenceStrength.VERY_WEAK,
        EvidenceStrength.UNVERIFIED,
        EvidenceStrength.INSUFFICIENT,
    }
    return WatchlistReviewItem(
        name=name,
        item_type=item_type,
        relevance_score=relevance,
        summary=_item_summary(name, item_type, relevance, assessment),
        evidence_assessment=assessment,
        appears_relevant=relevance >= 70 and not requires_better,
        requires_better_evidence=requires_better,
        potential_noise=potential_noise,
    )


def _evidence_for_item(
    name: str,
    evidence_inputs: dict[str, EvidenceInput],
    supported: bool,
) -> EvidenceInput:
    key = name.upper()
    if key in evidence_inputs:
        return evidence_inputs[key]
    if supported:
        return EvidenceInput(
            claim=EvidenceClaim(f"{name} has structured company data in Atlas."),
            source=EvidenceSource.EXCHANGE_DATA,
        )
    return EvidenceInput(
        claim=EvidenceClaim(f"{name} requires a more verifiable source."),
        source=EvidenceSource.UNKNOWN_SOURCE,
    )


def _evidence_inputs_from_mapping(payload: dict[str, Any]) -> dict[str, EvidenceInput]:
    raw_evidence = payload.get("evidence", {})
    if not isinstance(raw_evidence, dict):
        return {}
    parsed: dict[str, EvidenceInput] = {}
    for raw_name, raw_value in raw_evidence.items():
        if not isinstance(raw_value, dict):
            continue
        name = str(raw_name).upper()
        source = _parse_evidence_source(str(raw_value.get("source", "unknown source")))
        claim = EvidenceClaim(
            statement=str(raw_value.get("claim", f"{raw_name} evidence claim.")),
            materially_contradicts_current_view=bool(raw_value.get("contradicts", False)),
            extraordinary=bool(raw_value.get("extraordinary", False)),
        )
        parsed[name] = EvidenceInput(
            claim=claim,
            source=source,
            is_recent=bool(raw_value.get("recent", True)),
            is_verifiable=bool(
                raw_value.get("verifiable", source != EvidenceSource.UNKNOWN_SOURCE)
            ),
        )
    return parsed


def _parse_evidence_source(raw_source: str) -> EvidenceSource:
    normalized = raw_source.strip().lower().replace("-", " ")
    for source in EvidenceSource:
        if normalized in {source.name.lower().replace("_", " "), source.value.lower()}:
            return source
    aliases = {
        "tiktok": EvidenceSource.SHORT_FORM_VIDEO,
        "short form video": EvidenceSource.SHORT_FORM_VIDEO,
        "screenshot": EvidenceSource.SCREENSHOT_WITHOUT_SOURCE,
        "filing": EvidenceSource.REGULATORY_FILING,
        "annual report": EvidenceSource.AUDITED_ANNUAL_REPORT,
    }
    return aliases.get(normalized, EvidenceSource.UNKNOWN_SOURCE)


def _theme_names_from_mapping(payload: dict[str, Any]) -> tuple[str, ...]:
    raw_themes = payload.get("themes")
    if isinstance(raw_themes, list) and raw_themes:
        return tuple(str(theme) for theme in raw_themes)
    return ("AI infrastructure", "Semiconductors", "Energy transition")


def _watchlist_rating(
    items: tuple[WatchlistReviewItem, ...],
    profile: InvestorProfile,
    market_health_score: int,
) -> WatchlistReviewRating:
    if not items:
        return WatchlistReviewRating.UNCLEAR
    average_relevance = sum(item.relevance_score for item in items) / len(items)
    evidence_penalty = sum(1 for item in items if item.requires_better_evidence) * 8
    noise_penalty = sum(1 for item in items if item.potential_noise) * 6
    profile_bonus = 5 if profile.time_horizon.value == "10+ years" else 0
    score = average_relevance + profile_bonus + (market_health_score - 60) * 0.10
    score -= evidence_penalty + noise_penalty
    if score >= 82:
        return WatchlistReviewRating.HIGH_QUALITY
    if score >= 72:
        return WatchlistReviewRating.FOCUSED
    if score >= 58:
        return WatchlistReviewRating.BALANCED
    if score >= 42:
        return WatchlistReviewRating.NOISY
    return WatchlistReviewRating.UNCLEAR


def _confidence(items: tuple[WatchlistReviewItem, ...], monitoring_snapshot) -> int:
    if not items:
        return 35
    evidence_average = sum(
        _evidence_score(item.evidence_assessment.strength) for item in items
    )
    evidence_average = round(evidence_average / len(items))
    monitoring_score = monitoring_snapshot.confidence if monitoring_snapshot else 55
    missing_penalty = sum(1 for item in items if item.requires_better_evidence) * 5
    return max(
        20,
        min(
            90,
            round(evidence_average * 0.45 + monitoring_score * 0.55) - missing_penalty,
        ),
    )


def _bottom_line(
    name: str,
    rating: WatchlistReviewRating,
    items: tuple[WatchlistReviewItem, ...],
    confidence: int,
) -> str:
    relevant_count = sum(1 for item in items if item.appears_relevant)
    evidence_gaps = sum(1 for item in items if item.requires_better_evidence)
    return (
        f"Current evidence suggests {name} is a {rating.value.lower()} with "
        f"{relevant_count} idea(s) appearing most relevant and {evidence_gaps} "
        f"idea(s) needing better evidence. Atlas confidence is {confidence}/100, "
        "so the watchlist is useful for monitoring but still evidence-dependent."
    )


def _sections(
    bottom_line: str,
    rating: WatchlistReviewRating,
    items: tuple[WatchlistReviewItem, ...],
    profile: InvestorProfile,
    themes: tuple[ThemeAnalysis, ...],
    market_regime,
    market_health,
    economics,
    monitoring_snapshot,
    suitability_summary: str,
) -> tuple[WatchlistReviewSection, ...]:
    return (
        _section("Bottom Line", bottom_line, (("Summary", bottom_line, "High"),)),
        _section(
            "Atlas Watchlist Rating",
            "The rating reflects usefulness, focus, evidence quality, and profile fit.",
            (("Rating", rating.value, "High"),),
        ),
        _items_section("Most Relevant Ideas", items, lambda item: item.appears_relevant),
        _items_section(
            "Ideas Worth Monitoring",
            items,
            lambda item: not item.appears_relevant and not item.potential_noise,
        ),
        _items_section(
            "Ideas Requiring Better Evidence",
            items,
            lambda item: item.requires_better_evidence,
        ),
        _items_section("Potential Noise", items, lambda item: item.potential_noise),
        _theme_section(themes),
        _fit_section(profile, suitability_summary),
        _market_section(market_regime, market_health, economics),
        _monitoring_section(items, themes, monitoring_snapshot),
        _change_view_section(items, market_health, economics),
        _suggested_questions_section(items),
    )


def _section(
    title: str,
    narrative: str,
    observations: tuple[tuple[str, str, str], ...],
) -> WatchlistReviewSection:
    return WatchlistReviewSection(
        title=title,
        narrative=narrative,
        observations=tuple(
            WatchlistReviewObservation(item_title, summary, importance)
            for item_title, summary, importance in observations
        ),
    )


def _items_section(
    title: str,
    items: tuple[WatchlistReviewItem, ...],
    predicate,
) -> WatchlistReviewSection:
    selected = tuple(item for item in items if predicate(item))
    observations = tuple(
        (item.name, item.summary, "Worth monitoring" if not item.potential_noise else "Context")
        for item in selected[:5]
    ) or (("None", "No items currently fit this category.", "Context"),)
    narrative = _items_narrative(title)
    return _section(title, narrative, observations)


def _items_narrative(title: str) -> str:
    narratives = {
        "Most Relevant Ideas": "These ideas currently look most useful for continued study.",
        "Ideas Worth Monitoring": "These ideas are not urgent but deserve continued tracking.",
        "Ideas Requiring Better Evidence": (
            "These ideas may be worth investigating, but current evidence is not strong "
            "enough for a high-confidence assessment."
        ),
        "Potential Noise": (
            "These ideas appear less supported, unclear, duplicated, or mainly hype-driven."
        ),
    }
    return narratives.get(title, "Atlas is organizing watchlist ideas by usefulness.")


def _theme_section(themes: tuple[ThemeAnalysis, ...]) -> WatchlistReviewSection:
    observations = tuple(
        (
            theme.theme.value,
            f"{theme.summary} Monitoring: {theme.monitoring_items[0]}.",
            "Worth understanding",
        )
        for theme in themes[:5]
    )
    return _section(
        "Theme Exposure",
        "Atlas maps watchlist ideas to long-term themes where evidence supports it.",
        observations or (("Themes", "No supported theme exposure was detected.", "Context"),),
    )


def _fit_section(profile: InvestorProfile, suitability_summary: str) -> WatchlistReviewSection:
    return _section(
        "Fit With Investor Profile",
        "Atlas checks whether the watchlist appears aligned with stated context.",
        (
            ("Goals", ", ".join(goal.value for goal in profile.investment_goals), "Context"),
            ("Risk Tolerance", profile.risk_tolerance.value, "Context"),
            ("Time Horizon", profile.time_horizon.value, "Context"),
            ("Portfolio Purpose", profile.portfolio_purpose.value, "Context"),
            ("Suitability Context", suitability_summary, "Worth monitoring"),
        ),
    )


def _market_section(market_regime, market_health, economics) -> WatchlistReviewSection:
    return _section(
        "Market Context",
        "Market context shapes how aggressively Atlas interprets watchlist signals.",
        (
            ("Market Regime", market_regime.regime.value, "Context"),
            ("Market Health", market_health.overall_market_health, "Worth monitoring"),
            ("Economic Signals", economics.overall_economic_health, "Worth monitoring"),
        ),
    )


def _monitoring_section(
    items: tuple[WatchlistReviewItem, ...],
    themes: tuple[ThemeAnalysis, ...],
    monitoring_snapshot,
) -> WatchlistReviewSection:
    item_signals = tuple(
        (item.name, item.evidence_assessment.rationale.verifiability, "Worth monitoring")
        for item in items[:3]
    )
    theme_signals = tuple(
        (theme.theme.value, theme.monitoring_items[0], "Worth understanding")
        for theme in themes[:2]
    )
    monitor_signal = (
        ("Watchlist Signal", monitoring_snapshot.summary, "Context")
        if monitoring_snapshot
        else ("Watchlist Signal", "No supported company snapshot is available yet.", "Context")
    )
    return _section(
        "What Atlas Is Monitoring",
        "Atlas tracks evidence quality, theme signals, market context, and idea relevance.",
        (*item_signals, *theme_signals, monitor_signal),
    )


def _change_view_section(
    items: tuple[WatchlistReviewItem, ...],
    market_health,
    economics,
) -> WatchlistReviewSection:
    evidence_gaps = tuple(item for item in items if item.requires_better_evidence)
    observations = [
        (
            "Evidence Quality",
            "Original sources or verified datasets would improve confidence.",
            "High",
        ),
        ("Market Health", market_health.what_could_change_view[0], "Context"),
        ("Economic Signals", economics.what_would_worsen_outlook[0], "Context"),
    ]
    if evidence_gaps:
        observations.append(
            (
                "Evidence Gaps",
                f"{evidence_gaps[0].name} needs a more verifiable source.",
                "High",
            )
        )
    return _section(
        "What Could Change Atlas' View",
        "Atlas changes its mind when evidence quality or context changes materially.",
        tuple(observations),
    )


def _suggested_questions_section(items: tuple[WatchlistReviewItem, ...]) -> WatchlistReviewSection:
    questions = [
        "Is this a long-term watchlist or a short-term idea list?",
        "Are these ideas meant to complement the existing portfolio?",
    ]
    if any(item.requires_better_evidence for item in items):
        questions.append("Which of these ideas are based on verified sources?")
    if len(items) <= 3:
        questions.append("Is the narrow focus intentional?")
    return _section(
        "Suggested Questions",
        "Atlas only asks questions when answers could materially change the assessment.",
        tuple(("Question", question, "Could improve confidence") for question in questions),
    )


def _language_report(
    language_engine: AtlasLanguageEngine,
    rating: WatchlistReviewRating,
    bottom_line: str,
    sections: tuple[WatchlistReviewSection, ...],
    confidence: int,
) -> AtlasLanguageReport:
    return language_engine.build_report(
        rating=AtlasRating(
            value=rating.value,
            explanation="The watchlist rating reflects usefulness, focus, and evidence quality.",
        ),
        view=AtlasView(value="Balanced", explanation=bottom_line),
        fit=AtlasFit(
            value="Moderate Fit",
            explanation="Watchlist fit depends on investor profile and intended purpose.",
        ),
        confidence=AtlasConfidence(
            overall_confidence=confidence,
            confidence_level=_confidence_level(confidence),
            key_confidence_drivers=_section_summaries(sections, "Most Relevant Ideas"),
            uncertainty_drivers=_section_summaries(sections, "Ideas Requiring Better Evidence"),
            missing_information=_section_summaries(sections, "Suggested Questions"),
        ),
        thesis=AtlasThesis(
            current_thesis=bottom_line,
            supporting_evidence=_section_summaries(sections, "Most Relevant Ideas"),
            counter_arguments=_section_summaries(sections, "Potential Noise"),
            what_could_change_view=_section_summaries(
                sections,
                "What Could Change Atlas' View",
            ),
            what_atlas_is_monitoring=_section_summaries(sections, "What Atlas Is Monitoring"),
        ),
        rationale=AtlasRationale(
            bottom_line=bottom_line,
            key_reasons=(
                "The review combines watchlist ranking with evidence quality.",
                "The review separates relevant ideas from ideas needing better sources.",
                "The review includes market, theme, and profile context.",
            ),
            main_risk="The main risk is treating weak evidence as stronger than it is.",
            optional_follow_up_questions=_section_summaries(sections, "Suggested Questions"),
        ),
        engines_used=("Watchlist Review Engine", "Atlas Language Engine"),
    )


def _section_summaries(sections: tuple[WatchlistReviewSection, ...], title: str) -> tuple[str, ...]:
    for section in sections:
        if section.title == title:
            return tuple(item.summary for item in section.observations[:4])
    return ("Not enough information for a high-confidence assessment.",)


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


def _item_summary(
    name: str,
    item_type: str,
    relevance: int,
    assessment: EvidenceAssessment,
) -> str:
    if assessment.action in {
        EvidenceAction.REQUEST_SOURCE,
        EvidenceAction.INSUFFICIENT_FOR_ASSESSMENT,
    }:
        return (
            f"{name} is a {item_type.lower()} with relevance {relevance}/100, but "
            "not enough information for a high-confidence assessment."
        )
    if assessment.strength in {EvidenceStrength.WEAK, EvidenceStrength.VERY_WEAK}:
        return (
            f"{name} may deserve attention, but appears less supported by current "
            f"evidence. Relevance is {relevance}/100."
        )
    return (
        f"{name} appears relevant as a {item_type.lower()} with relevance "
        f"{relevance}/100 and {assessment.strength.value.lower()} evidence."
    )


def _idea_type(name: str) -> str:
    lowered = name.lower()
    if "etf" in lowered:
        return "ETF"
    if any(word in lowered for word in ("infrastructure", "transition", "innovation")):
        return "Theme"
    return "Idea"


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


def _default_market_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        indicators=MarketIndicators(
            sp500_drawdown=-0.04,
            nasdaq_drawdown=-0.07,
            vix=19,
            interest_rate_trend="stable",
            inflation_trend="stable",
        ),
        source="deterministic-watchlist-review-placeholder",
    )
