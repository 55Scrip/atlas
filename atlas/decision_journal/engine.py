import json
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from atlas.evidence import (
    EvidenceAssessment,
    EvidenceClaim,
    EvidenceInput,
    EvidenceQualityEngine,
    EvidenceSource,
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
from atlas.principles import PrinciplesCheck, PrinciplesEngine
from atlas.profile import InvestorProfile, InvestorProfileEngine


class DecisionJournalStatus(str, Enum):
    OPEN = "Open"
    REVIEW_DUE = "Review Due"
    REVIEWED = "Reviewed"
    LESSON_CAPTURED = "Lesson Captured"


class DecisionType(str, Enum):
    CONSIDERING = "considering"
    ENTERED = "entered"
    EXITED = "exited"
    REVIEWED = "reviewed"
    PASSED = "passed"


@dataclass(frozen=True)
class DecisionJournalTrigger:
    name: str
    description: str
    severity: str = "Context"


@dataclass(frozen=True)
class DecisionJournalLesson:
    summary: str
    decision_quality: str
    outcome_quality: str
    behavior_to_repeat: str
    behavior_to_improve: str


@dataclass(frozen=True)
class DecisionJournalInput:
    decision_title: str
    asset_or_idea: str
    decision_type: DecisionType = DecisionType.CONSIDERING
    decision_date: str | None = None
    investor_profile: InvestorProfile | None = None
    portfolio_context_summary: str = "No portfolio context supplied."
    atlas_rating: str = "Balanced"
    atlas_view: str = "Balanced"
    atlas_fit: str = "Moderate Fit"
    atlas_confidence: int = 68
    investment_thesis: str = (
        "Current evidence suggests the idea is worth monitoring, but the thesis "
        "depends on evidence quality and portfolio role."
    )
    key_reasons: tuple[str, ...] = (
        "The idea has a plausible long-term rationale.",
        "The intended portfolio role is still being clarified.",
    )
    main_risks: tuple[str, ...] = (
        "Evidence may be incomplete.",
        "The thesis could weaken if assumptions change.",
    )
    evidence_input: EvidenceInput | None = None
    assumptions: tuple[str, ...] = (
        "The investor has a long-term horizon.",
        "Short-term liquidity is separate from investment capital.",
    )
    what_could_change_view: tuple[str, ...] = (
        "Better source quality changes the evidence base.",
        "Investor profile or portfolio purpose changes materially.",
    )
    monitoring_plan: tuple[str, ...] = (
        "Evidence quality",
        "Investor fit",
        "Thesis assumptions",
    )
    planned_review_date: str | None = None
    user_notes: str = ""
    lessons_learned: tuple[DecisionJournalLesson, ...] = ()


@dataclass(frozen=True)
class DecisionJournalEntry:
    entry_id: str
    decision_title: str
    asset_or_idea: str
    decision_type: DecisionType
    decision_date: str
    investor_profile_context: str
    portfolio_context_summary: str
    atlas_rating: str
    atlas_view: str
    atlas_fit: str
    atlas_confidence: int
    investment_thesis: str
    key_reasons: tuple[str, ...]
    main_risks: tuple[str, ...]
    evidence_quality: str
    evidence_summary: str
    assumptions: tuple[str, ...]
    what_could_change_view: tuple[str, ...]
    monitoring_plan: tuple[str, ...]
    planned_review_date: str
    user_notes: str = ""
    lessons_learned: tuple[DecisionJournalLesson, ...] = ()
    language_report: AtlasLanguageReport | None = None


@dataclass(frozen=True)
class DecisionJournalReview:
    entry: DecisionJournalEntry
    status: DecisionJournalStatus
    review_summary: str
    triggers: tuple[DecisionJournalTrigger, ...]
    lessons_learned: tuple[DecisionJournalLesson, ...]
    decision_quality_view: str
    outcome_quality_view: str
    principles_check: PrinciplesCheck


class DecisionJournalEngine:
    def __init__(
        self,
        profile_engine: InvestorProfileEngine | None = None,
        evidence_engine: EvidenceQualityEngine | None = None,
        language_engine: AtlasLanguageEngine | None = None,
        principles_engine: PrinciplesEngine | None = None,
    ) -> None:
        self.profile_engine = profile_engine or InvestorProfileEngine()
        self.language_engine = language_engine or AtlasLanguageEngine()
        self.evidence_engine = evidence_engine or EvidenceQualityEngine(self.language_engine)
        self.principles_engine = principles_engine or PrinciplesEngine()

    def create_entry(self, journal_input: DecisionJournalInput) -> DecisionJournalEntry:
        profile = journal_input.investor_profile or self.profile_engine.create_default_profile()
        evidence = self.evidence_engine.assess(
            journal_input.evidence_input
            or EvidenceInput(
                claim=EvidenceClaim(
                    f"{journal_input.asset_or_idea} thesis needs periodic review."
                ),
                source=EvidenceSource.ANALYST_REPORT,
            )
        )
        confidence = _confidence_with_evidence(
            journal_input.atlas_confidence,
            evidence,
        )
        entry = DecisionJournalEntry(
            entry_id=_entry_id(journal_input),
            decision_title=journal_input.decision_title,
            asset_or_idea=journal_input.asset_or_idea,
            decision_type=journal_input.decision_type,
            decision_date=journal_input.decision_date or date.today().isoformat(),
            investor_profile_context=_profile_context(profile),
            portfolio_context_summary=journal_input.portfolio_context_summary,
            atlas_rating=journal_input.atlas_rating,
            atlas_view=journal_input.atlas_view,
            atlas_fit=journal_input.atlas_fit,
            atlas_confidence=confidence,
            investment_thesis=journal_input.investment_thesis,
            key_reasons=journal_input.key_reasons,
            main_risks=journal_input.main_risks,
            evidence_quality=evidence.strength.value,
            evidence_summary=(
                f"{evidence.atlas_response} This evidence should be reviewed "
                "against the original thesis over time."
            ),
            assumptions=journal_input.assumptions,
            what_could_change_view=journal_input.what_could_change_view,
            monitoring_plan=journal_input.monitoring_plan,
            planned_review_date=journal_input.planned_review_date or _default_review_date(),
            user_notes=journal_input.user_notes,
            lessons_learned=journal_input.lessons_learned,
        )
        return _entry_with_language(entry, self.language_engine)

    def review_entry(
        self,
        entry: DecisionJournalEntry,
        lessons: tuple[DecisionJournalLesson, ...] = (),
    ) -> DecisionJournalReview:
        captured_lessons = lessons or entry.lessons_learned
        status = _review_status(entry, captured_lessons)
        review = DecisionJournalReview(
            entry=entry,
            status=status,
            review_summary=(
                "This review preserves the reasoning at the time of consideration. "
                "Decision quality is evaluated separately from outcome quality."
            ),
            triggers=tuple(
                DecisionJournalTrigger("Review Trigger", item, "Worth monitoring")
                for item in entry.what_could_change_view
            ),
            lessons_learned=captured_lessons,
            decision_quality_view=(
                "Decision quality depends on process, evidence quality, risk awareness, "
                "and fit with investor context."
            ),
            outcome_quality_view=(
                "A good decision can have an unfavorable outcome, and a poor decision "
                "can have a favorable outcome."
            ),
            principles_check=self.principles_engine.check(render_decision_journal_entry(entry)),
        )
        return review

    def save_entry(self, entry: DecisionJournalEntry, path: Path) -> DecisionJournalEntry:
        entries = self.load_entries(path) if path.exists() else ()
        updated = tuple(item for item in entries if item.entry_id != entry.entry_id) + (entry,)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps([_entry_to_mapping(item) for item in updated], indent=2),
            encoding="utf-8",
        )
        return entry

    def load_entries(self, path: Path) -> tuple[DecisionJournalEntry, ...]:
        if not path.exists():
            return ()
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("Decision journal JSON must contain a list.")
        return tuple(_entry_from_mapping(item, self.language_engine) for item in payload)

    def demo_entry(self) -> DecisionJournalEntry:
        return self.create_entry(
            DecisionJournalInput(
                decision_title="Review AI infrastructure exposure",
                asset_or_idea="AI infrastructure",
                portfolio_context_summary=(
                    "Potential thematic exposure for a long-term core portfolio."
                ),
                atlas_rating="Balanced",
                atlas_view="Constructive",
                atlas_fit="Moderate Fit",
                atlas_confidence=72,
                investment_thesis=(
                    "AI infrastructure appears worth monitoring because power, grid, "
                    "data center, and semiconductor bottlenecks may shape long-term returns."
                ),
                key_reasons=(
                    "The theme has clear bottlenecks to monitor.",
                    "Evidence quality is sufficient for a structured journal entry.",
                    "The thesis depends on portfolio role and risk tolerance.",
                ),
                main_risks=(
                    "Valuation sensitivity may rise if expectations become crowded.",
                    "Infrastructure constraints could delay business outcomes.",
                ),
                what_could_change_view=(
                    "Evidence quality weakens.",
                    "Power or grid constraints become more severe.",
                    "Investor profile changes materially.",
                ),
                monitoring_plan=(
                    "Evidence quality",
                    "Power infrastructure",
                    "Semiconductor supply chain",
                ),
            )
        )


def render_decision_journal_entry(entry: DecisionJournalEntry) -> str:
    lines = [
        "Decision Journal Entry",
        "",
        "Journal Entry Summary",
        (
            f"{entry.decision_title} for {entry.asset_or_idea} is a "
            f"{entry.decision_type.value} decision under review."
        ),
        "",
        "Atlas Rating Snapshot",
        f"Atlas Rating: {entry.atlas_rating}",
        f"Atlas View: {entry.atlas_view}",
        f"Atlas Fit: {entry.atlas_fit}",
        f"Atlas Confidence: {entry.atlas_confidence}/100",
        "",
        "Thesis",
        entry.investment_thesis,
        "",
        "Supporting Reasons",
        *_render_list(entry.key_reasons),
        "",
        "Main Risks",
        *_render_list(entry.main_risks),
        "",
        "Evidence Quality",
        f"{entry.evidence_quality}: {entry.evidence_summary}",
        "",
        "What Could Change Atlas' View",
        *_render_list(entry.what_could_change_view),
        "",
        "Monitoring Plan",
        *_render_list(entry.monitoring_plan),
        "",
        "Review Schedule",
        f"Planned Review Date: {entry.planned_review_date}",
        "",
        "Lessons Learned",
        *_render_lessons(entry.lessons_learned),
        "",
        "Full Reasoning",
        *_render_list(entry.assumptions),
        f"Investor Context: {entry.investor_profile_context}",
        f"Portfolio Context: {entry.portfolio_context_summary}",
        "",
        "Research Framing",
        "This preserves decision reasoning only. It is not personal financial advice.",
    ]
    return "\n".join(lines)


def render_decision_journal_entries(entries: tuple[DecisionJournalEntry, ...]) -> str:
    lines = ["Decision Journal", ""]
    if not entries:
        lines.append("No decision journal entries found.")
        return "\n".join(lines)
    for entry in entries:
        lines.append(
            (
                f"- {entry.entry_id}: {entry.decision_title} | {entry.asset_or_idea} | "
                f"{entry.decision_type.value} | review {entry.planned_review_date}"
            )
        )
    return "\n".join(lines)


def render_decision_journal_review(review: DecisionJournalReview) -> str:
    lines = [
        "Decision Journal Review",
        "",
        f"Status: {review.status.value}",
        "",
        "Journal Entry Summary",
        review.review_summary,
        "",
        "Decision Quality",
        review.decision_quality_view,
        "",
        "Outcome Quality",
        review.outcome_quality_view,
        "",
        "Review Triggers",
    ]
    lines.extend(f"- {trigger.description} ({trigger.severity})" for trigger in review.triggers)
    lines.extend(
        [
            "",
            "Lessons Learned",
            *_render_lessons(review.lessons_learned),
            "",
            "Research Framing",
            "This review supports learning and does not judge the investor.",
        ]
    )
    return "\n".join(lines)


def _entry_with_language(
    entry: DecisionJournalEntry,
    language_engine: AtlasLanguageEngine,
) -> DecisionJournalEntry:
    language_report = language_engine.build_report(
        rating=AtlasRating(
            value=entry.atlas_rating,
            explanation="Journal snapshot rating captures context at the time.",
        ),
        view=AtlasView(value=entry.atlas_view, explanation=entry.investment_thesis),
        fit=AtlasFit(value=entry.atlas_fit, explanation=entry.investor_profile_context),
        confidence=AtlasConfidence(
            overall_confidence=entry.atlas_confidence,
            confidence_level=_confidence_level(entry.atlas_confidence),
            key_confidence_drivers=entry.key_reasons,
            uncertainty_drivers=entry.main_risks,
            missing_information=entry.what_could_change_view,
        ),
        thesis=AtlasThesis(
            current_thesis=entry.investment_thesis,
            supporting_evidence=entry.key_reasons,
            counter_arguments=entry.main_risks,
            what_could_change_view=entry.what_could_change_view,
            what_atlas_is_monitoring=entry.monitoring_plan,
        ),
        rationale=AtlasRationale(
            bottom_line=entry.investment_thesis,
            key_reasons=entry.key_reasons,
            main_risk=entry.main_risks[0] if entry.main_risks else "Evidence may be incomplete.",
            optional_follow_up_questions=(
                "Has the thesis changed materially?",
                "Has the intended portfolio role changed?",
            ),
        ),
        engines_used=("Decision Journal Engine", "Atlas Language Engine"),
    )
    return DecisionJournalEntry(
        **{
            **_entry_to_mapping(entry),
            "decision_type": entry.decision_type,
            "key_reasons": entry.key_reasons,
            "main_risks": entry.main_risks,
            "assumptions": entry.assumptions,
            "what_could_change_view": entry.what_could_change_view,
            "monitoring_plan": entry.monitoring_plan,
            "lessons_learned": entry.lessons_learned,
            "language_report": language_report,
        }
    )


def _confidence_with_evidence(base_confidence: int, evidence: EvidenceAssessment) -> int:
    return max(10, min(95, base_confidence + evidence.confidence_impact))


def _entry_id(journal_input: DecisionJournalInput) -> str:
    raw_date = journal_input.decision_date or date.today().isoformat()
    slug = journal_input.decision_title.lower().replace(" ", "-")
    slug = "".join(character for character in slug if character.isalnum() or character == "-")
    return f"{raw_date}-{slug[:40]}"


def _default_review_date() -> str:
    return (date.today() + timedelta(days=90)).isoformat()


def _profile_context(profile: InvestorProfile) -> str:
    return (
        f"{profile.name}: {profile.portfolio_purpose.value}, "
        f"{profile.risk_tolerance.value} risk tolerance, "
        f"{profile.time_horizon.value} horizon."
    )


def _review_status(
    entry: DecisionJournalEntry,
    lessons: tuple[DecisionJournalLesson, ...],
) -> DecisionJournalStatus:
    if lessons:
        return DecisionJournalStatus.LESSON_CAPTURED
    if entry.planned_review_date <= date.today().isoformat():
        return DecisionJournalStatus.REVIEW_DUE
    return DecisionJournalStatus.OPEN


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


def _entry_to_mapping(entry: DecisionJournalEntry) -> dict[str, Any]:
    return {
        "entry_id": entry.entry_id,
        "decision_title": entry.decision_title,
        "asset_or_idea": entry.asset_or_idea,
        "decision_type": entry.decision_type.value,
        "decision_date": entry.decision_date,
        "investor_profile_context": entry.investor_profile_context,
        "portfolio_context_summary": entry.portfolio_context_summary,
        "atlas_rating": entry.atlas_rating,
        "atlas_view": entry.atlas_view,
        "atlas_fit": entry.atlas_fit,
        "atlas_confidence": entry.atlas_confidence,
        "investment_thesis": entry.investment_thesis,
        "key_reasons": list(entry.key_reasons),
        "main_risks": list(entry.main_risks),
        "evidence_quality": entry.evidence_quality,
        "evidence_summary": entry.evidence_summary,
        "assumptions": list(entry.assumptions),
        "what_could_change_view": list(entry.what_could_change_view),
        "monitoring_plan": list(entry.monitoring_plan),
        "planned_review_date": entry.planned_review_date,
        "user_notes": entry.user_notes,
        "lessons_learned": [_lesson_to_mapping(lesson) for lesson in entry.lessons_learned],
    }


def _entry_from_mapping(
    payload: dict[str, Any],
    language_engine: AtlasLanguageEngine,
) -> DecisionJournalEntry:
    lessons = tuple(_lesson_from_mapping(item) for item in payload.get("lessons_learned", []))
    entry = DecisionJournalEntry(
        entry_id=str(payload["entry_id"]),
        decision_title=str(payload["decision_title"]),
        asset_or_idea=str(payload["asset_or_idea"]),
        decision_type=DecisionType(str(payload["decision_type"])),
        decision_date=str(payload["decision_date"]),
        investor_profile_context=str(payload["investor_profile_context"]),
        portfolio_context_summary=str(payload["portfolio_context_summary"]),
        atlas_rating=str(payload["atlas_rating"]),
        atlas_view=str(payload["atlas_view"]),
        atlas_fit=str(payload["atlas_fit"]),
        atlas_confidence=int(payload["atlas_confidence"]),
        investment_thesis=str(payload["investment_thesis"]),
        key_reasons=tuple(str(item) for item in payload.get("key_reasons", [])),
        main_risks=tuple(str(item) for item in payload.get("main_risks", [])),
        evidence_quality=str(payload["evidence_quality"]),
        evidence_summary=str(payload["evidence_summary"]),
        assumptions=tuple(str(item) for item in payload.get("assumptions", [])),
        what_could_change_view=tuple(
            str(item) for item in payload.get("what_could_change_view", [])
        ),
        monitoring_plan=tuple(str(item) for item in payload.get("monitoring_plan", [])),
        planned_review_date=str(payload["planned_review_date"]),
        user_notes=str(payload.get("user_notes", "")),
        lessons_learned=lessons,
    )
    return _entry_with_language(entry, language_engine)


def _lesson_to_mapping(lesson: DecisionJournalLesson) -> dict[str, str]:
    return {
        "summary": lesson.summary,
        "decision_quality": lesson.decision_quality,
        "outcome_quality": lesson.outcome_quality,
        "behavior_to_repeat": lesson.behavior_to_repeat,
        "behavior_to_improve": lesson.behavior_to_improve,
    }


def _lesson_from_mapping(payload: dict[str, Any]) -> DecisionJournalLesson:
    return DecisionJournalLesson(
        summary=str(payload.get("summary", "")),
        decision_quality=str(payload.get("decision_quality", "")),
        outcome_quality=str(payload.get("outcome_quality", "")),
        behavior_to_repeat=str(payload.get("behavior_to_repeat", "")),
        behavior_to_improve=str(payload.get("behavior_to_improve", "")),
    )


def _render_lessons(lessons: tuple[DecisionJournalLesson, ...]) -> list[str]:
    if not lessons:
        return ["- None yet"]
    return [
        (
            f"- {lesson.summary} Decision quality: {lesson.decision_quality}. "
            f"Outcome quality: {lesson.outcome_quality}."
        )
        for lesson in lessons
    ]


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]
