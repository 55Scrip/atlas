from dataclasses import dataclass
from enum import Enum

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


class EvidenceSource(str, Enum):
    AUDITED_ANNUAL_REPORT = "Audited annual report"
    QUARTERLY_REPORT = "Quarterly report"
    COMPANY_PRESS_RELEASE = "Company press release"
    REGULATORY_FILING = "Regulatory filing"
    EXCHANGE_DATA = "Exchange data"
    GOVERNMENT_CENTRAL_BANK_DATA = "Government / central bank data"
    REPUTABLE_FINANCIAL_NEWS = "Reputable financial news"
    ANALYST_REPORT = "Analyst report"
    INVESTOR_PRESENTATION = "Investor presentation"
    SOCIAL_MEDIA_POST = "Social media post"
    FORUM_POST = "Forum post"
    SHORT_FORM_VIDEO = "TikTok / short-form video"
    SCREENSHOT_WITHOUT_SOURCE = "Screenshot without source"
    USER_STATEMENT = "User statement"
    UNKNOWN_SOURCE = "Unknown source"


class EvidenceStrength(str, Enum):
    VERY_STRONG = "Very Strong"
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"
    VERY_WEAK = "Very Weak"
    UNVERIFIED = "Unverified"
    INSUFFICIENT = "Insufficient"


class EvidenceAction(str, Enum):
    UPDATE_ASSESSMENT = "Update assessment"
    REDUCE_CONFIDENCE = "Reduce confidence"
    ADD_RESERVATION = "Add reservation"
    MONITOR_FOR_CONFIRMATION = "Monitor for confirmation"
    REQUEST_SOURCE = "Request source"
    IGNORE_FOR_NOW = "Ignore for now"
    INSUFFICIENT_FOR_ASSESSMENT = "Insufficient for assessment"


@dataclass(frozen=True)
class EvidenceClaim:
    statement: str
    materially_contradicts_current_view: bool = False
    extraordinary: bool = False


@dataclass(frozen=True)
class EvidenceInput:
    claim: EvidenceClaim
    source: EvidenceSource
    source_detail: str = ""
    is_recent: bool = True
    is_verifiable: bool = True
    current_view: str = "Balanced"


@dataclass(frozen=True)
class EvidenceRationale:
    why_strength: str
    primary_or_secondary: str
    recency: str
    verifiability: str
    contradiction: str
    additional_data_needed: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceAssessment:
    claim: EvidenceClaim
    source: EvidenceSource
    strength: EvidenceStrength
    action: EvidenceAction
    rationale: EvidenceRationale
    confidence_impact: int
    should_change_view: bool
    atlas_response: str
    language_report: AtlasLanguageReport


class EvidenceQualityEngine:
    def __init__(self, language_engine: AtlasLanguageEngine | None = None) -> None:
        self.language_engine = language_engine or AtlasLanguageEngine()

    def assess(self, evidence: EvidenceInput) -> EvidenceAssessment:
        base_strength = SOURCE_PROFILES[evidence.source].strength
        strength = _adjust_strength(
            base_strength=base_strength,
            is_recent=evidence.is_recent,
            is_verifiable=evidence.is_verifiable,
            extraordinary=evidence.claim.extraordinary,
        )
        action = _action_for_evidence(evidence, strength)
        confidence_impact = _confidence_impact(strength, action, evidence)
        should_change_view = (
            evidence.claim.materially_contradicts_current_view
            and action == EvidenceAction.UPDATE_ASSESSMENT
        )
        rationale = _rationale(evidence, strength)
        response = _atlas_response(evidence, strength, action, should_change_view)
        return EvidenceAssessment(
            claim=evidence.claim,
            source=evidence.source,
            strength=strength,
            action=action,
            rationale=rationale,
            confidence_impact=confidence_impact,
            should_change_view=should_change_view,
            atlas_response=response,
            language_report=self._language_report(
                evidence=evidence,
                strength=strength,
                action=action,
                rationale=rationale,
                confidence_impact=confidence_impact,
                should_change_view=should_change_view,
            ),
        )

    def example_assessment(self) -> EvidenceAssessment:
        return self.assess(
            EvidenceInput(
                claim=EvidenceClaim(
                    statement=(
                        "A sourced regulatory filing shows a material change in "
                        "customer concentration."
                    ),
                    materially_contradicts_current_view=True,
                ),
                source=EvidenceSource.REGULATORY_FILING,
                source_detail="Deterministic example filing input",
                is_recent=True,
                is_verifiable=True,
                current_view="Constructive",
            )
        )

    def _language_report(
        self,
        evidence: EvidenceInput,
        strength: EvidenceStrength,
        action: EvidenceAction,
        rationale: EvidenceRationale,
        confidence_impact: int,
        should_change_view: bool,
    ) -> AtlasLanguageReport:
        confidence_score = max(10, min(95, 72 + confidence_impact))
        return self.language_engine.build_report(
            rating=AtlasRating(
                value=_rating_label(strength),
                explanation=(
                    "The evidence rating reflects source quality, recency, "
                    "verifiability, and relevance to the current view."
                ),
            ),
            view=AtlasView(
                value="Improving" if should_change_view else "Unclear",
                explanation=(
                    "The current view can change only when evidence is strong, "
                    "verifiable, and materially relevant."
                ),
            ),
            fit=AtlasFit(
                value="Moderate Fit",
                explanation="Evidence fit depends on whether the claim is decision-relevant.",
            ),
            confidence=AtlasConfidence(
                overall_confidence=confidence_score,
                confidence_level=_confidence_level(confidence_score),
                key_confidence_drivers=(
                    rationale.primary_or_secondary,
                    rationale.verifiability,
                ),
                uncertainty_drivers=(
                    rationale.recency,
                    rationale.contradiction,
                ),
                missing_information=rationale.additional_data_needed,
            ),
            thesis=AtlasThesis(
                current_thesis=evidence.claim.statement,
                supporting_evidence=(rationale.why_strength,),
                counter_arguments=(rationale.verifiability, rationale.recency),
                what_could_change_view=(
                    "A stronger original source confirms the claim.",
                    "Comparable evidence contradicts the claim.",
                ),
                what_atlas_is_monitoring=rationale.additional_data_needed,
            ),
            rationale=AtlasRationale(
                bottom_line=_atlas_response(
                    evidence,
                    strength,
                    action,
                    should_change_view,
                ),
                key_reasons=(
                    rationale.why_strength,
                    rationale.primary_or_secondary,
                    rationale.verifiability,
                ),
                main_risk="The main risk is overweighting weak or unverifiable evidence.",
                optional_follow_up_questions=(
                    "Can you provide the original source document or dataset?",
                    "Has this evidence materially changed the current thesis?",
                ),
            ),
            engines_used=("Evidence Quality Engine", "Atlas Language Engine"),
        )


def render_evidence_assessment(assessment: EvidenceAssessment) -> str:
    lines = [
        "Atlas Evidence Quality Assessment",
        "",
        f"Claim: {assessment.claim.statement}",
        f"Source Type: {assessment.source.value}",
        f"Evidence Strength: {assessment.strength.value}",
        f"Evidence Action: {assessment.action.value}",
        f"Confidence Impact: {assessment.confidence_impact:+d}",
        f"Should Atlas' View Change: {'Yes' if assessment.should_change_view else 'No'}",
        "",
        "Rationale",
        f"- Strength: {assessment.rationale.why_strength}",
        f"- Evidence Type: {assessment.rationale.primary_or_secondary}",
        f"- Recency: {assessment.rationale.recency}",
        f"- Verifiability: {assessment.rationale.verifiability}",
        f"- Contradiction: {assessment.rationale.contradiction}",
        "",
        "Additional Data Needed",
        *_render_list(assessment.rationale.additional_data_needed),
        "",
        "Atlas Response",
        assessment.atlas_response,
        "",
        "Research Framing",
        (
            "This engine classifies evidence quality from structured inputs. "
            "It does not browse, independently verify external facts, or provide "
            "investment instructions."
        ),
    ]
    return "\n".join(lines)


def _adjust_strength(
    base_strength: EvidenceStrength,
    is_recent: bool,
    is_verifiable: bool,
    extraordinary: bool,
) -> EvidenceStrength:
    rank = STRENGTH_ORDER.index(base_strength)
    if not is_verifiable:
        rank = max(rank, STRENGTH_ORDER.index(EvidenceStrength.UNVERIFIED))
    if not is_recent and rank < STRENGTH_ORDER.index(EvidenceStrength.WEAK):
        rank += 1
    if extraordinary and rank < STRENGTH_ORDER.index(EvidenceStrength.STRONG):
        rank = STRENGTH_ORDER.index(EvidenceStrength.INSUFFICIENT)
    return STRENGTH_ORDER[rank]


def _action_for_evidence(
    evidence: EvidenceInput,
    strength: EvidenceStrength,
) -> EvidenceAction:
    if evidence.source in REQUEST_SOURCE_SOURCES:
        return EvidenceAction.REQUEST_SOURCE
    if strength in {EvidenceStrength.INSUFFICIENT, EvidenceStrength.UNVERIFIED}:
        return EvidenceAction.INSUFFICIENT_FOR_ASSESSMENT
    if (
        evidence.claim.materially_contradicts_current_view
        and strength in STRONG_ENOUGH_TO_UPDATE
    ):
        return EvidenceAction.UPDATE_ASSESSMENT
    if strength in {EvidenceStrength.VERY_STRONG, EvidenceStrength.STRONG}:
        return EvidenceAction.ADD_RESERVATION
    if strength == EvidenceStrength.MODERATE:
        return EvidenceAction.MONITOR_FOR_CONFIRMATION
    if strength == EvidenceStrength.WEAK:
        return EvidenceAction.REDUCE_CONFIDENCE
    return EvidenceAction.IGNORE_FOR_NOW


def _confidence_impact(
    strength: EvidenceStrength,
    action: EvidenceAction,
    evidence: EvidenceInput,
) -> int:
    if action == EvidenceAction.UPDATE_ASSESSMENT:
        return -12 if evidence.claim.materially_contradicts_current_view else 8
    if action == EvidenceAction.REDUCE_CONFIDENCE:
        return -10
    if action == EvidenceAction.ADD_RESERVATION:
        return -4 if evidence.claim.materially_contradicts_current_view else 4
    if action == EvidenceAction.MONITOR_FOR_CONFIRMATION:
        return -6
    if action in {
        EvidenceAction.REQUEST_SOURCE,
        EvidenceAction.INSUFFICIENT_FOR_ASSESSMENT,
    }:
        return -18
    if strength in {EvidenceStrength.VERY_WEAK, EvidenceStrength.WEAK}:
        return -8
    return 0


def _rationale(evidence: EvidenceInput, strength: EvidenceStrength) -> EvidenceRationale:
    profile = SOURCE_PROFILES[evidence.source]
    return EvidenceRationale(
        why_strength=(
            f"{evidence.source.value} is classified as {strength.value.lower()} "
            f"because {profile.reason}."
        ),
        primary_or_secondary=(
            "Primary evidence." if profile.primary else "Secondary or indirect evidence."
        ),
        recency=(
            "The evidence is recent enough to influence confidence."
            if evidence.is_recent
            else "The evidence may be stale and should be refreshed before relying on it."
        ),
        verifiability=(
            "The source is verifiable from the provided structured input."
            if evidence.is_verifiable
            else "The source is not verifiable from the provided structured input."
        ),
        contradiction=(
            "The claim materially contradicts Atlas' current view."
            if evidence.claim.materially_contradicts_current_view
            else "The claim does not materially contradict Atlas' current view."
        ),
        additional_data_needed=_additional_data_needed(evidence, strength),
    )


def _additional_data_needed(
    evidence: EvidenceInput,
    strength: EvidenceStrength,
) -> tuple[str, ...]:
    needs = []
    if evidence.source in REQUEST_SOURCE_SOURCES or not evidence.is_verifiable:
        needs.append("Original source document, dataset, filing, or report.")
    if not evidence.is_recent:
        needs.append("A more recent version of the evidence.")
    if evidence.claim.extraordinary:
        needs.append("Independent confirmation from a primary or official source.")
    if strength in {EvidenceStrength.WEAK, EvidenceStrength.VERY_WEAK, EvidenceStrength.UNVERIFIED}:
        needs.append("Confirmation from a reputable or primary source.")
    if not needs:
        needs.append("No major additional source is required for initial assessment.")
    return tuple(needs)


def _atlas_response(
    evidence: EvidenceInput,
    strength: EvidenceStrength,
    action: EvidenceAction,
    should_change_view: bool,
) -> str:
    if should_change_view:
        return (
            "That evidence is materially relevant. If accurate, it would reduce "
            "Atlas' confidence and may change the current view."
        )
    if evidence.source in SOCIAL_OR_SCREENSHOT_SOURCES:
        return (
            "This claim may be worth investigating, but this source is not enough "
            "to change Atlas' view. Please provide the original source, dataset, "
            "filing, or report behind the claim."
        )
    if action == EvidenceAction.REQUEST_SOURCE:
        return (
            "Not enough information for a high-confidence assessment. Atlas would "
            "need a verifiable source before changing the current view."
        )
    if strength in {EvidenceStrength.WEAK, EvidenceStrength.VERY_WEAK}:
        return (
            "That is a potentially relevant claim, but the source quality is not "
            "strong enough to change the assessment yet."
        )
    return (
        "This evidence is relevant to the assessment. Atlas would incorporate it "
        "as context while tracking whether additional evidence confirms it."
    )


def _rating_label(strength: EvidenceStrength) -> str:
    if strength in {EvidenceStrength.VERY_STRONG, EvidenceStrength.STRONG}:
        return "Constructive"
    if strength == EvidenceStrength.MODERATE:
        return "Balanced"
    if strength in {EvidenceStrength.WEAK, EvidenceStrength.VERY_WEAK}:
        return "Cautious"
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


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


@dataclass(frozen=True)
class SourceProfile:
    strength: EvidenceStrength
    primary: bool
    reason: str


SOURCE_PROFILES = {
    EvidenceSource.AUDITED_ANNUAL_REPORT: SourceProfile(
        EvidenceStrength.VERY_STRONG,
        True,
        "it is audited, primary, and company-level evidence",
    ),
    EvidenceSource.QUARTERLY_REPORT: SourceProfile(
        EvidenceStrength.STRONG,
        True,
        "it is primary company reporting with recurring disclosure standards",
    ),
    EvidenceSource.COMPANY_PRESS_RELEASE: SourceProfile(
        EvidenceStrength.MODERATE,
        True,
        "it is primary but may be selective or promotional",
    ),
    EvidenceSource.REGULATORY_FILING: SourceProfile(
        EvidenceStrength.VERY_STRONG,
        True,
        "it is official, structured, and subject to regulatory standards",
    ),
    EvidenceSource.EXCHANGE_DATA: SourceProfile(
        EvidenceStrength.VERY_STRONG,
        True,
        "it comes from market infrastructure or official exchange records",
    ),
    EvidenceSource.GOVERNMENT_CENTRAL_BANK_DATA: SourceProfile(
        EvidenceStrength.VERY_STRONG,
        True,
        "it is official macro or financial data from an authoritative institution",
    ),
    EvidenceSource.REPUTABLE_FINANCIAL_NEWS: SourceProfile(
        EvidenceStrength.MODERATE,
        False,
        "it is secondary reporting that may summarize primary evidence",
    ),
    EvidenceSource.ANALYST_REPORT: SourceProfile(
        EvidenceStrength.MODERATE,
        False,
        "it is expert interpretation rather than original evidence",
    ),
    EvidenceSource.INVESTOR_PRESENTATION: SourceProfile(
        EvidenceStrength.MODERATE,
        True,
        "it is company-provided but selectively framed",
    ),
    EvidenceSource.SOCIAL_MEDIA_POST: SourceProfile(
        EvidenceStrength.WEAK,
        False,
        "it is indirect and usually lacks source traceability",
    ),
    EvidenceSource.FORUM_POST: SourceProfile(
        EvidenceStrength.VERY_WEAK,
        False,
        "it is informal and usually not independently sourced",
    ),
    EvidenceSource.SHORT_FORM_VIDEO: SourceProfile(
        EvidenceStrength.VERY_WEAK,
        False,
        "short-form video often lacks original data and source traceability",
    ),
    EvidenceSource.SCREENSHOT_WITHOUT_SOURCE: SourceProfile(
        EvidenceStrength.UNVERIFIED,
        False,
        "the original source cannot be inspected from the screenshot alone",
    ),
    EvidenceSource.USER_STATEMENT: SourceProfile(
        EvidenceStrength.UNVERIFIED,
        False,
        "it is not independently supported by source material",
    ),
    EvidenceSource.UNKNOWN_SOURCE: SourceProfile(
        EvidenceStrength.INSUFFICIENT,
        False,
        "the source category is unknown",
    ),
}

STRENGTH_ORDER = (
    EvidenceStrength.VERY_STRONG,
    EvidenceStrength.STRONG,
    EvidenceStrength.MODERATE,
    EvidenceStrength.WEAK,
    EvidenceStrength.VERY_WEAK,
    EvidenceStrength.UNVERIFIED,
    EvidenceStrength.INSUFFICIENT,
)

STRONG_ENOUGH_TO_UPDATE = {
    EvidenceStrength.VERY_STRONG,
    EvidenceStrength.STRONG,
}

REQUEST_SOURCE_SOURCES = {
    EvidenceSource.SCREENSHOT_WITHOUT_SOURCE,
    EvidenceSource.USER_STATEMENT,
    EvidenceSource.UNKNOWN_SOURCE,
}

SOCIAL_OR_SCREENSHOT_SOURCES = {
    EvidenceSource.SOCIAL_MEDIA_POST,
    EvidenceSource.FORUM_POST,
    EvidenceSource.SHORT_FORM_VIDEO,
    EvidenceSource.SCREENSHOT_WITHOUT_SOURCE,
}
