from dataclasses import dataclass
from pathlib import Path

from atlas.analysis.portfolio import Portfolio
from atlas.analysis.watchlist import Watchlist
from atlas.decision_journal import DecisionJournalEngine, DecisionJournalEntry
from atlas.economics import EconomicSignalsEngine
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
from atlas.portfolio_review import PortfolioReviewEngine, PortfolioReviewInput
from atlas.profile import InvestorProfile, InvestorProfileEngine
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider
from atlas.watchlist_review import (
    WatchlistReviewEngine,
    WatchlistReviewInput,
    demo_watchlist_review_input,
)


@dataclass(frozen=True)
class AtlasHomePriority:
    title: str
    why_it_matters: str
    confidence: int
    evidence_quality: str


@dataclass(frozen=True)
class AtlasHomeMonitoring:
    item: str
    reason: str


@dataclass(frozen=True)
class AtlasHomeSummary:
    bottom_line: str
    atlas_rating: str
    portfolio_alignment: str
    largest_strength: str
    largest_risk: str
    market_context: str


@dataclass(frozen=True)
class AtlasHomeInput:
    investor_profile: InvestorProfile | None = None
    portfolio: Portfolio | None = None
    watchlist: Watchlist | None = None
    provider: CompanyDataProvider | None = None
    journal_path: Path = Path(".atlas/decision_journal.json")
    previous_review_notes: tuple[str, ...] = ()
    market_snapshot: MarketSnapshot | None = None


@dataclass(frozen=True)
class AtlasHomeOutput:
    title: str
    summary: AtlasHomeSummary
    priorities: tuple[AtlasHomePriority, ...]
    watchlist_highlights: tuple[str, ...]
    decision_journal_reminders: tuple[str, ...]
    monitoring: tuple[AtlasHomeMonitoring, ...]
    changes_since_last_review: tuple[str, ...]
    language_report: AtlasLanguageReport
    engines_used: tuple[str, ...]


class AtlasHomeEngine:
    def __init__(
        self,
        profile_engine: InvestorProfileEngine | None = None,
        portfolio_review_engine: PortfolioReviewEngine | None = None,
        watchlist_review_engine: WatchlistReviewEngine | None = None,
        market_health_engine: MarketHealthEngine | None = None,
        market_regime_engine: MarketRegimeEngine | None = None,
        economic_signals_engine: EconomicSignalsEngine | None = None,
        decision_journal_engine: DecisionJournalEngine | None = None,
        language_engine: AtlasLanguageEngine | None = None,
    ) -> None:
        self.profile_engine = profile_engine or InvestorProfileEngine()
        self.portfolio_review_engine = portfolio_review_engine or PortfolioReviewEngine()
        self.watchlist_review_engine = watchlist_review_engine or WatchlistReviewEngine()
        self.market_health_engine = market_health_engine or MarketHealthEngine()
        self.market_regime_engine = market_regime_engine or MarketRegimeEngine()
        self.economic_signals_engine = economic_signals_engine or EconomicSignalsEngine()
        self.decision_journal_engine = decision_journal_engine or DecisionJournalEngine()
        self.language_engine = language_engine or AtlasLanguageEngine()

    def build(self, home_input: AtlasHomeInput | None = None) -> AtlasHomeOutput:
        input_data = home_input or AtlasHomeInput()
        profile = input_data.investor_profile or self.profile_engine.create_default_profile()
        provider = input_data.provider or MockCompanyAnalysisProvider()
        market_snapshot = input_data.market_snapshot or _default_market_snapshot()
        market_regime = self.market_regime_engine.analyze(market_snapshot)
        market_health = self.market_health_engine.analyze()
        economics = self.economic_signals_engine.analyze()
        portfolio_review = (
            self.portfolio_review_engine.review(
                PortfolioReviewInput(
                    portfolio=input_data.portfolio,
                    investor_profile=profile,
                    market_snapshot=market_snapshot,
                )
            )
            if input_data.portfolio is not None
            else None
        )
        watchlist_review = self.watchlist_review_engine.review(
            WatchlistReviewInput(
                watchlist=input_data.watchlist,
                provider=provider,
                investor_profile=profile,
                market_snapshot=market_snapshot,
            )
            if input_data.watchlist is not None
            else demo_watchlist_review_input(provider=provider, investor_profile=profile)
        )
        journal_entries = self.decision_journal_engine.load_entries(input_data.journal_path)
        summary = _summary(
            profile=profile,
            portfolio_review=portfolio_review,
            market_regime=market_regime,
            market_health=market_health,
            economics=economics,
        )
        priorities = _priorities(
            portfolio_review=portfolio_review,
            watchlist_review=watchlist_review,
            market_health=market_health,
            economics=economics,
        )
        watchlist_highlights = _watchlist_highlights(watchlist_review)
        journal_reminders = _journal_reminders(journal_entries)
        monitoring = _monitoring_items(
            summary=summary,
            watchlist_review=watchlist_review,
            market_health=market_health,
            economics=economics,
            journal_entries=journal_entries,
        )
        changes = _meaningful_changes(input_data.previous_review_notes)
        quiet_day = _is_quiet_day(
            input_data=input_data,
            portfolio_review=portfolio_review,
            journal_entries=journal_entries,
            market_regime=market_regime,
            market_health=market_health,
            economics=economics,
        )
        if quiet_day:
            summary = _quiet_day_summary(summary)
            priorities = _quiet_day_priorities()
            watchlist_highlights = ("No meaningful watchlist developments today.",)
            journal_reminders = ("No decision journal reviews require attention today.",)
            monitoring = _quiet_day_monitoring()
            changes = ("No meaningful changes since your last review.",)
        draft_output = AtlasHomeOutput(
            title="Atlas Home",
            summary=summary,
            priorities=priorities,
            watchlist_highlights=watchlist_highlights,
            decision_journal_reminders=journal_reminders,
            monitoring=monitoring,
            changes_since_last_review=changes,
            language_report=_language_report(
                self.language_engine,
                summary,
                priorities,
                monitoring,
            ),
            engines_used=(
                "Investor Profile Engine",
                "Portfolio Review Engine",
                "Watchlist Review Engine",
                "Market Health Engine",
                "Market Regime Engine",
                "Economic Signals Engine",
                "Decision Journal Engine",
                "Atlas Language Engine",
            ),
        )
        return draft_output


def render_atlas_home(output: AtlasHomeOutput) -> str:
    lines = [
        output.title,
        "",
        "Bottom Line",
        output.summary.bottom_line,
        "",
        f"Atlas Rating: {output.summary.atlas_rating}",
        "",
        "Today's Priorities",
    ]
    lines.extend(_render_priorities(output.priorities))
    lines.extend(
        [
            "",
            "Portfolio Health",
            f"- Alignment: {output.summary.portfolio_alignment}",
            f"- Largest Strength: {output.summary.largest_strength}",
            f"- Largest Risk: {output.summary.largest_risk}",
            "",
            "Market Context",
            output.summary.market_context,
            "",
            "Watchlist Highlights",
            *_render_list(output.watchlist_highlights),
            "",
            "Decision Journal",
            *_render_list(output.decision_journal_reminders),
            "",
            "What Atlas Is Monitoring",
            *_render_monitoring(output.monitoring),
            "",
            "What Changed Since Last Review",
            *_render_list(output.changes_since_last_review),
            "",
            "Supporting Reasoning",
            output.language_report.rationale.bottom_line,
            "",
            "Research Framing",
            (
                "Atlas Home follows the Atlas Constitution: evidence before opinion, "
                "context before conclusion, and calm before clever. This briefing is "
                "for context and education, not personal financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _summary(
    profile: InvestorProfile,
    portfolio_review,
    market_regime,
    market_health,
    economics,
) -> AtlasHomeSummary:
    if portfolio_review is None:
        rating = "Unclear"
        alignment = "Portfolio context not loaded"
        largest_strength = "Investor profile context is available."
        largest_risk = "Atlas needs portfolio holdings for a higher-confidence view."
        bottom_line = (
            f"Good day, {profile.name}. Atlas has market and watchlist context, but "
            "portfolio context is not loaded, so no immediate action appears necessary "
            "from this briefing alone."
        )
    else:
        rating = portfolio_review.atlas_rating.value
        alignment = portfolio_review.atlas_rating.value
        largest_strength = _section_observation(portfolio_review, "Portfolio Strengths")
        largest_risk = _section_observation(portfolio_review, "Main Risks")
        bottom_line = (
            f"Good day, {profile.name}. Current evidence suggests the portfolio is "
            f"{rating.lower()} relative to the stated strategy, with "
            f"{largest_risk.lower()} worth monitoring."
        )
    market_context = (
        f"The market regime is {market_regime.regime.value.lower()}, market health is "
        f"{market_health.overall_market_health.lower()}, and economic signals are "
        f"{economics.overall_economic_health.lower()} with risk score "
        f"{economics.overall_risk_score}/100."
    )
    return AtlasHomeSummary(
        bottom_line=bottom_line,
        atlas_rating=rating,
        portfolio_alignment=alignment,
        largest_strength=largest_strength,
        largest_risk=largest_risk,
        market_context=market_context,
    )


def _priorities(
    portfolio_review,
    watchlist_review,
    market_health,
    economics,
) -> tuple[AtlasHomePriority, ...]:
    priorities: list[AtlasHomePriority] = []
    if portfolio_review is not None:
        priorities.append(
            AtlasHomePriority(
                title="Portfolio alignment",
                why_it_matters=portfolio_review.bottom_line,
                confidence=portfolio_review.confidence,
                evidence_quality="Structured portfolio review",
            )
        )
    priorities.append(
        AtlasHomePriority(
            title="Watchlist quality",
            why_it_matters=watchlist_review.bottom_line,
            confidence=watchlist_review.confidence,
            evidence_quality=watchlist_review.atlas_rating.value,
        )
    )
    priorities.append(
        AtlasHomePriority(
            title="Market context",
            why_it_matters=market_health.atlas_view,
            confidence=_bounded_confidence(market_health.overall_score),
            evidence_quality=f"Economic risk score {economics.overall_risk_score}/100",
        )
    )
    return tuple(priorities[:3])


def _watchlist_highlights(watchlist_review) -> tuple[str, ...]:
    highlights = []
    for item in watchlist_review.items:
        if item.appears_relevant:
            highlights.append(f"{item.name} appears relevant: {item.summary}")
        elif item.requires_better_evidence:
            highlights.append(f"{item.name} needs better evidence: {item.summary}")
        if len(highlights) == 3:
            break
    if not highlights:
        highlights.append("No meaningful watchlist developments stand out today.")
    return tuple(highlights[:3])


def _journal_reminders(entries: tuple[DecisionJournalEntry, ...]) -> tuple[str, ...]:
    if not entries:
        return ("No decision journal reviews are due in the current local journal.",)
    reminders = [
        f"{entry.decision_title}: review planned for {entry.planned_review_date}."
        for entry in sorted(entries, key=lambda item: item.planned_review_date)
    ]
    return tuple(reminders[:3])


def _monitoring_items(
    summary: AtlasHomeSummary,
    watchlist_review,
    market_health,
    economics,
    journal_entries: tuple[DecisionJournalEntry, ...],
) -> tuple[AtlasHomeMonitoring, ...]:
    raw_items = [
        AtlasHomeMonitoring(summary.largest_risk, "Largest portfolio risk or missing context."),
        AtlasHomeMonitoring("Credit conditions", market_health.signal_groups[0].interpretation),
        AtlasHomeMonitoring("Economic risk", economics.conclusion),
        AtlasHomeMonitoring("Watchlist evidence quality", watchlist_review.bottom_line),
    ]
    if journal_entries:
        raw_items.append(
            AtlasHomeMonitoring(
                "Decision journal reviews",
                "Review reminders preserve thesis quality over time.",
            )
        )
    else:
        raw_items.append(
            AtlasHomeMonitoring(
                "Decision journal coverage",
                "No local review reminders are currently available.",
            )
        )
    return tuple(_dedupe_monitoring(raw_items)[:5])


def _meaningful_changes(previous_review_notes: tuple[str, ...]) -> tuple[str, ...]:
    changes = tuple(note for note in previous_review_notes if note.strip())
    if not changes:
        return ("No meaningful changes supplied since the last review.",)
    return changes[:3]


def _is_quiet_day(
    input_data: AtlasHomeInput,
    portfolio_review,
    journal_entries: tuple[DecisionJournalEntry, ...],
    market_regime,
    market_health,
    economics,
) -> bool:
    return (
        input_data.portfolio is not None
        and input_data.watchlist is None
        and not journal_entries
        and not any(note.strip() for note in input_data.previous_review_notes)
        and portfolio_review is not None
        and portfolio_review.atlas_rating.value
        in {"Excellent Alignment", "Strong Alignment", "Balanced"}
        and market_regime.regime.value in {"Bull", "Neutral"}
        and market_health.overall_score >= 60
        and economics.overall_risk_score <= 60
    )


def _quiet_day_summary(summary: AtlasHomeSummary) -> AtlasHomeSummary:
    return AtlasHomeSummary(
        bottom_line=(
            "No meaningful changes since your last review. Your portfolio remains "
            "broadly aligned with your strategy."
        ),
        atlas_rating=summary.atlas_rating,
        portfolio_alignment=summary.portfolio_alignment,
        largest_strength=summary.largest_strength,
        largest_risk=summary.largest_risk,
        market_context=(
            "No significant market update requires attention in this briefing. "
            f"{summary.market_context}"
        ),
    )


def _quiet_day_priorities() -> tuple[AtlasHomePriority, ...]:
    return (
        AtlasHomePriority(
            title="No immediate action appears necessary.",
            why_it_matters=(
                "Atlas found no meaningful portfolio change, watchlist development, "
                "journal reminder, or market update requiring attention today."
            ),
            confidence=74,
            evidence_quality="Stable deterministic context",
        ),
    )


def _quiet_day_monitoring() -> tuple[AtlasHomeMonitoring, ...]:
    return (
        AtlasHomeMonitoring(
            "Portfolio alignment",
            "Current evidence suggests the strategy remains broadly aligned.",
        ),
        AtlasHomeMonitoring(
            "Market context",
            "No significant market update requires attention today.",
        ),
        AtlasHomeMonitoring(
            "Decision journal",
            "No local review reminders require attention today.",
        ),
    )


def _language_report(
    language_engine: AtlasLanguageEngine,
    summary: AtlasHomeSummary,
    priorities: tuple[AtlasHomePriority, ...],
    monitoring: tuple[AtlasHomeMonitoring, ...],
) -> AtlasLanguageReport:
    confidence = round(sum(priority.confidence for priority in priorities) / len(priorities))
    return language_engine.build_report(
        rating=AtlasRating(
            value=summary.atlas_rating,
            explanation=(
                "Home rating reflects overall alignment and context, not an investment "
                "instruction."
            ),
        ),
        view=AtlasView(
            value="Balanced",
            explanation=summary.bottom_line,
        ),
        fit=AtlasFit(
            value=_fit_from_rating(summary.atlas_rating),
            explanation="Fit is inferred from investor, portfolio, and market context.",
        ),
        confidence=AtlasConfidence(
            overall_confidence=confidence,
            confidence_level=_confidence_level(confidence),
            key_confidence_drivers=tuple(priority.title for priority in priorities),
            uncertainty_drivers=(
                "Live external data is not used in this deterministic briefing.",
                "Changes since last review depend on supplied prior context.",
            ),
            missing_information=(
                "Exact liquidity needs may be missing.",
                "Tax context is not included.",
            ),
        ),
        thesis=AtlasThesis(
            current_thesis=summary.bottom_line,
            supporting_evidence=tuple(priority.why_it_matters for priority in priorities),
            counter_arguments=(summary.largest_risk,),
            what_could_change_view=(
                "Portfolio alignment changes materially.",
                "Market health or economic risk deteriorates.",
                "Watchlist evidence quality changes.",
            ),
            what_atlas_is_monitoring=tuple(item.item for item in monitoring),
        ),
        rationale=AtlasRationale(
            bottom_line=(
                "Atlas Home prioritizes the few items most likely to improve the "
                "investor's understanding today."
            ),
            key_reasons=(
                "The briefing starts with investor and portfolio context.",
                "Priorities are capped to reduce noise.",
                "Monitoring items are linked to evidence and context.",
            ),
            main_risk=summary.largest_risk,
        ),
        engines_used=(
            "Atlas Home Engine",
            "Atlas Language Engine",
            "Portfolio Review Engine",
            "Watchlist Review Engine",
            "Market Health Engine",
        ),
    )


def _section_observation(report, section_title: str) -> str:
    for section in report.sections:
        if section.title == section_title and section.observations:
            return section.observations[0].summary
    return "Not enough information for a high-confidence assessment."


def _fit_from_rating(rating: str) -> str:
    if rating in {"Excellent Alignment", "Strong Alignment"}:
        return "Strong Fit"
    if rating in {"Balanced", "Good Fit"}:
        return "Moderate Fit"
    if rating in {"Limited Alignment", "Limited Fit"}:
        return "Limited Fit"
    if rating == "Misaligned":
        return "Poor Fit"
    return "Moderate Fit"


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


def _bounded_confidence(score: int) -> int:
    return max(35, min(90, score))


def _dedupe_monitoring(items: list[AtlasHomeMonitoring]) -> list[AtlasHomeMonitoring]:
    seen: set[str] = set()
    deduped: list[AtlasHomeMonitoring] = []
    for item in items:
        key = item.item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def _default_market_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        indicators=MarketIndicators(
            sp500_drawdown=-0.04,
            nasdaq_drawdown=-0.07,
            vix=19,
            interest_rate_trend="stable",
            inflation_trend="stable",
        ),
        source="deterministic-home-placeholder",
    )


def _render_priorities(priorities: tuple[AtlasHomePriority, ...]) -> list[str]:
    if not priorities:
        return ["- No priorities require attention today."]
    lines = []
    for priority in priorities:
        lines.append(f"- {priority.title}")
        lines.append(f"  Why it matters: {priority.why_it_matters}")
        lines.append(f"  Confidence: {priority.confidence}/100")
        lines.append(f"  Evidence Quality: {priority.evidence_quality}")
    return lines


def _render_monitoring(items: tuple[AtlasHomeMonitoring, ...]) -> list[str]:
    if not items:
        return ["- No monitoring items today."]
    return [f"- {item.item}: {item.reason}" for item in items]


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]
