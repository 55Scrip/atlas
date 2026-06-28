from dataclasses import dataclass
from pathlib import Path

from atlas.analysis.portfolio import Portfolio
from atlas.analysis.watchlist import Watchlist
from atlas.evidence import EvidenceClaim, EvidenceInput, EvidenceQualityEngine, EvidenceSource
from atlas.home import AtlasHomeEngine, AtlasHomeInput, AtlasHomeOutput
from atlas.language import AtlasLanguageEngine
from atlas.market import MarketSnapshot
from atlas.profile import InvestorProfile
from atlas.providers import CompanyDataProvider, MockCompanyAnalysisProvider


DAILY_BRIEF_ENGINES_USED = (
    "Atlas Home Engine",
    "Portfolio Review Engine",
    "Watchlist Review Engine",
    "Market Health Engine",
    "Market Regime Engine",
    "Economic Signals Engine",
    "Evidence Quality Engine",
    "Atlas Language Engine",
    "Decision Journal Engine",
    "Monitoring Engine",
    "Investor Profile Engine",
)

DAILY_BRIEF_ASSUMPTIONS = (
    "The brief uses deterministic Atlas engine outputs.",
    "No live news feed or live market API is used.",
    "Only supplied previous review notes are treated as changed context.",
)

DAILY_BRIEF_MISSING_INFORMATION = (
    "Exact liquidity needs may be missing.",
    "Tax context is not included.",
    "External real-time news is not included.",
)


@dataclass(frozen=True)
class DailyBriefInput:
    investor_profile: InvestorProfile | None = None
    portfolio: Portfolio | None = None
    watchlist: Watchlist | None = None
    provider: CompanyDataProvider | None = None
    target_ticker: str | None = None
    journal_path: Path = Path(".atlas/decision_journal.json")
    previous_review_notes: tuple[str, ...] = ()
    market_snapshot: MarketSnapshot | None = None


@dataclass(frozen=True)
class DailyBriefItem:
    title: str
    summary: str
    confidence: int | None = None
    evidence_quality: str = "Context"


@dataclass(frozen=True)
class DailyBriefSection:
    title: str
    narrative: str
    items: tuple[DailyBriefItem, ...]


@dataclass(frozen=True)
class DailyBriefOutput:
    title: str
    bottom_line: str
    sections: tuple[DailyBriefSection, ...]
    confidence: int
    engines_used: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    confidence_drivers: tuple[str, ...]


class DailyBriefEngine:
    def __init__(
        self,
        home_engine: AtlasHomeEngine | None = None,
        evidence_engine: EvidenceQualityEngine | None = None,
        language_engine: AtlasLanguageEngine | None = None,
    ) -> None:
        self.home_engine = home_engine or AtlasHomeEngine()
        self.evidence_engine = evidence_engine or EvidenceQualityEngine(
            language_engine or AtlasLanguageEngine()
        )

    def build(self, daily_input: DailyBriefInput | None = None) -> DailyBriefOutput:
        input_data = daily_input or DailyBriefInput()
        provider = input_data.provider or MockCompanyAnalysisProvider()
        home = self.home_engine.build(
            AtlasHomeInput(
                investor_profile=input_data.investor_profile,
                portfolio=input_data.portfolio,
                watchlist=input_data.watchlist,
                provider=provider,
                journal_path=input_data.journal_path,
                previous_review_notes=input_data.previous_review_notes,
                market_snapshot=input_data.market_snapshot,
            )
        )
        evidence = self.evidence_engine.assess(
            EvidenceInput(
                claim=EvidenceClaim(
                    "Daily Brief synthesizes structured Atlas engine outputs."
                ),
                source=EvidenceSource.ANALYST_REPORT,
                is_recent=True,
                is_verifiable=True,
            )
        )
        confidence_drivers = _confidence_drivers(home)
        sections = (
            _what_changed_section(home),
            _why_it_matters_section(home),
            _portfolio_context_section(home),
            _watchlist_context_section(home),
            _market_context_section(home),
            _priorities_section(home),
            _monitoring_section(home),
            _change_view_section(home),
            _full_reasoning_section(
                home=home,
                evidence_quality=evidence.strength.value,
                confidence_drivers=confidence_drivers,
            ),
        )
        return DailyBriefOutput(
            title="Atlas Daily Brief",
            bottom_line=home.summary.bottom_line,
            sections=sections,
            confidence=_confidence(home),
            engines_used=DAILY_BRIEF_ENGINES_USED,
            assumptions=DAILY_BRIEF_ASSUMPTIONS,
            missing_information=DAILY_BRIEF_MISSING_INFORMATION,
            confidence_drivers=confidence_drivers,
        )


def render_daily_brief(output: DailyBriefOutput) -> str:
    lines = [
        output.title,
        "",
        "Bottom Line",
        output.bottom_line,
    ]
    for section in output.sections:
        lines.extend(["", section.title, section.narrative])
        lines.extend(_render_items(section.items))
    lines.extend(
        [
            "",
            "Confidence",
            f"{output.confidence}/100",
            "",
            "Research Framing",
            (
                "This is a deterministic briefing for context and education. It is "
                "not a news feed, market prediction, investment recommendation, or "
                "personal financial advice."
            ),
        ]
    )
    return "\n".join(lines)


def _what_changed_section(home: AtlasHomeOutput) -> DailyBriefSection:
    return DailyBriefSection(
        title="What Changed",
        narrative="Atlas reports only meaningful supplied or detected changes.",
        items=tuple(
            DailyBriefItem("Change", change, evidence_quality="Structured context")
            for change in home.changes_since_last_review[:3]
        ),
    )


def _why_it_matters_section(home: AtlasHomeOutput) -> DailyBriefSection:
    quiet = _is_quiet_home(home)
    summary = (
        "No immediate action appears necessary because Atlas did not detect a "
        "meaningful portfolio, watchlist, journal, or market change."
        if quiet
        else (
            "Current evidence suggests attention should stay focused on the "
            "highest-signal priorities, not every available data point."
        )
    )
    return DailyBriefSection(
        title="Why It Matters",
        narrative="Atlas connects changed context to the investor's current briefing.",
        items=(
            DailyBriefItem(
                "Relevance",
                summary,
                confidence=home.language_report.confidence.overall_confidence,
            ),
        ),
    )


def _portfolio_context_section(home: AtlasHomeOutput) -> DailyBriefSection:
    return DailyBriefSection(
        title="Portfolio Context",
        narrative="Portfolio context is summarized from Atlas Home and portfolio review data.",
        items=(
            DailyBriefItem("Alignment", home.summary.portfolio_alignment),
            DailyBriefItem("Largest Strength", home.summary.largest_strength),
            DailyBriefItem("Largest Risk", home.summary.largest_risk),
        ),
    )


def _watchlist_context_section(home: AtlasHomeOutput) -> DailyBriefSection:
    return DailyBriefSection(
        title="Watchlist Context",
        narrative="Watchlist context is limited to meaningful developments.",
        items=tuple(
            DailyBriefItem("Watchlist", highlight, evidence_quality="Watchlist review")
            for highlight in home.watchlist_highlights[:3]
        ),
    )


def _market_context_section(home: AtlasHomeOutput) -> DailyBriefSection:
    return DailyBriefSection(
        title="Market Context",
        narrative="Market context is summarized calmly without forecasting.",
        items=(DailyBriefItem("Market", home.summary.market_context),),
    )


def _priorities_section(home: AtlasHomeOutput) -> DailyBriefSection:
    return DailyBriefSection(
        title="Today's Priorities",
        narrative="Atlas limits priorities to the few items that deserve attention.",
        items=tuple(
            DailyBriefItem(
                priority.title,
                priority.why_it_matters,
                confidence=priority.confidence,
                evidence_quality=priority.evidence_quality,
            )
            for priority in home.priorities[:3]
        ),
    )


def _monitoring_section(home: AtlasHomeOutput) -> DailyBriefSection:
    return DailyBriefSection(
        title="What Atlas Is Monitoring",
        narrative="Monitoring items are capped so the brief stays usable.",
        items=tuple(
            DailyBriefItem(item.item, item.reason)
            for item in home.monitoring[:5]
        ),
    )


def _change_view_section(home: AtlasHomeOutput) -> DailyBriefSection:
    return DailyBriefSection(
        title="What Could Change This View",
        narrative="Only material factors are included.",
        items=tuple(
            DailyBriefItem("Material Factor", factor)
            for factor in home.language_report.thesis.what_could_change_view[:3]
        ),
    )


def _full_reasoning_section(
    home: AtlasHomeOutput,
    evidence_quality: str,
    confidence_drivers: tuple[str, ...],
) -> DailyBriefSection:
    confidence = home.language_report.confidence
    items = [
        DailyBriefItem(
            "Assumptions",
            "; ".join(DAILY_BRIEF_ASSUMPTIONS),
            evidence_quality=evidence_quality,
        ),
        DailyBriefItem(
            "Engines Used",
            ", ".join(DAILY_BRIEF_ENGINES_USED),
        ),
        DailyBriefItem(
            "Missing Information",
            ", ".join((*confidence.missing_information, *DAILY_BRIEF_MISSING_INFORMATION)),
        ),
        DailyBriefItem(
            "Confidence Drivers",
            ", ".join(confidence_drivers),
            confidence=confidence.overall_confidence,
        ),
    ]
    return DailyBriefSection(
        title="Full Reasoning",
        narrative="Progressive transparency for users who want to inspect the brief.",
        items=tuple(items),
    )


def _confidence(home: AtlasHomeOutput) -> int:
    return home.language_report.confidence.overall_confidence


def _confidence_drivers(home: AtlasHomeOutput) -> tuple[str, ...]:
    return (
        "Atlas Home synthesized profile, portfolio, watchlist, market, and journal context.",
        f"Daily priorities are capped at {len(home.priorities)} item(s).",
        f"Monitoring is capped at {len(home.monitoring)} item(s).",
    )


def _is_quiet_home(home: AtlasHomeOutput) -> bool:
    return home.changes_since_last_review == ("No meaningful changes since your last review.",)


def _render_items(items: tuple[DailyBriefItem, ...]) -> list[str]:
    if not items:
        return ["- None"]
    lines = []
    for item in items:
        suffix = []
        if item.confidence is not None:
            suffix.append(f"confidence {item.confidence}/100")
        if item.evidence_quality != "Context":
            suffix.append(f"evidence {item.evidence_quality}")
        detail = f" ({'; '.join(suffix)})" if suffix else ""
        lines.append(f"- {item.title}: {item.summary}{detail}")
    return lines
