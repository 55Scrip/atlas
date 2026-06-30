from dataclasses import FrozenInstanceError

import pytest

from atlas.domains.research import (
    ResearchAssumption,
    ResearchEvidenceReference,
    ResearchIssueSeverity,
    ResearchNote,
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
    ThesisFragment,
    is_valid_status_transition,
    summarize_research,
    validate_research_project,
)


def _evidence(reference_id: str = "evidence-1") -> ResearchEvidenceReference:
    return ResearchEvidenceReference(
        id=reference_id,
        source_id="source-1",
        description="Annual report data center revenue disclosure.",
        knowledge_fact_id="fact-1",
    )


def _project() -> ResearchProject:
    return ResearchProject(
        id="research-nvda",
        title="NVIDIA data center durability",
        topic="NVDA",
        status=ResearchStatus.THESIS_FORMING,
        notes=(
            ResearchNote(
                id="note-1",
                title="Initial note",
                body="Revenue mix deserves study.",
                created_at="2026-06-30T00:00:00Z",
                related_tickers=("NVDA",),
            ),
        ),
        questions=(
            ResearchQuestion(
                id="question-1",
                question="How durable is data center demand?",
                related_topic="NVDA",
                status=ResearchQuestionStatus.RESEARCHING,
                evidence_reference_ids=("evidence-1",),
                created_at="2026-06-30T00:00:00Z",
            ),
            ResearchQuestion(
                id="question-2",
                question="What changed in gross margin?",
                related_topic="NVDA",
                status=ResearchQuestionStatus.RESOLVED,
                evidence_reference_ids=("evidence-1",),
                created_at="2026-06-30T00:00:00Z",
                resolved_at="2026-06-30T01:00:00Z",
                resolution_notes="Margin change was explained by product mix.",
            ),
        ),
        assumptions=(
            ResearchAssumption(
                id="assumption-1",
                statement="Hyperscaler capital spending remains important.",
                explanation="Customer concentration can affect data center revenue durability.",
                evidence_reference_ids=("evidence-1",),
                confidence=80,
            ),
        ),
        thesis_fragments=(
            ThesisFragment(
                id="thesis-1",
                claim="Data center demand appears central to the research thesis.",
                supporting_evidence_reference_ids=("evidence-1",),
                assumption_ids=("assumption-1",),
                confidence=72,
                open_question_ids=("question-1",),
            ),
        ),
        evidence_references=(_evidence(),),
        created_at="2026-06-30T00:00:00Z",
    )


def test_research_project_creation_and_immutability() -> None:
    project = _project()

    assert project.title == "NVIDIA data center durability"
    assert project.questions[0].question == "How durable is data center demand?"
    assert project.evidence_references[0].knowledge_fact_id == "fact-1"

    with pytest.raises(FrozenInstanceError):
        project.title = "Changed"  # type: ignore[misc]


def test_research_question_lifecycle_and_status_transitions() -> None:
    question = _project().questions[1]

    assert question.status == ResearchQuestionStatus.RESOLVED
    assert question.resolved_at == "2026-06-30T01:00:00Z"
    assert is_valid_status_transition(ResearchStatus.NOT_STARTED, ResearchStatus.RESEARCHING)
    assert not is_valid_status_transition(
        ResearchStatus.NOT_STARTED,
        ResearchStatus.READY_FOR_REVIEW,
    )


def test_thesis_fragment_represents_reasoning_under_development() -> None:
    fragment = _project().thesis_fragments[0]

    assert fragment.claim.startswith("Data center demand")
    assert fragment.supporting_evidence_reference_ids == ("evidence-1",)
    assert fragment.assumption_ids == ("assumption-1",)
    assert fragment.confidence == 72
    assert fragment.status == ResearchStatus.THESIS_FORMING


def test_research_summary_is_deterministic() -> None:
    summary = summarize_research(_project())

    assert summary.number_of_notes == 1
    assert summary.number_of_open_questions == 1
    assert summary.number_of_resolved_questions == 1
    assert summary.number_of_assumptions == 1
    assert summary.thesis_maturity == "Thesis forming"
    assert summary.missing_evidence_warnings == ()
    assert summary.overall_research_status == ResearchStatus.THESIS_FORMING


def test_validation_reports_structured_issues() -> None:
    project = ResearchProject(
        id="research-empty",
        title="",
        topic="",
        questions=(
            ResearchQuestion(
                id="question-1",
                question="What matters?",
                related_topic="Topic",
                status=ResearchQuestionStatus.RESOLVED,
                resolved_at="2026-06-30T00:00:00Z",
            ),
            ResearchQuestion(
                id="question-1",
                question="Duplicate question?",
                related_topic="Topic",
            ),
        ),
        assumptions=(
            ResearchAssumption(
                id="assumption-1",
                statement="Assumption",
                explanation="",
            ),
        ),
        thesis_fragments=(ThesisFragment(id="thesis-1", claim="Incomplete claim"),),
    )

    result = validate_research_project(project)
    issue_codes = [issue.code for issue in result.issues]

    assert result.is_valid is False
    assert "missing_title" in issue_codes
    assert "duplicate_question_id" in issue_codes
    assert "resolved_question_missing_resolution_notes" in issue_codes
    assert "assumption_missing_explanation" in issue_codes
    assert "thesis_fragment_missing_evidence" in issue_codes


def test_empty_project_behavior_is_safe() -> None:
    project = ResearchProject(id="empty", title="Empty project", topic="Learning")

    validation = validate_research_project(project)
    summary = summarize_research(project)

    assert validation.is_valid is True
    assert validation.issues[0].code == "empty_research_project"
    assert validation.issues[0].severity == ResearchIssueSeverity.WARNING
    assert summary.overall_research_status == ResearchStatus.NOT_STARTED
    assert summary.thesis_maturity == "No thesis formed"


def test_missing_evidence_warning_is_deterministic() -> None:
    project = ResearchProject(
        id="research-1",
        title="Research",
        topic="Topic",
        thesis_fragments=(
            ThesisFragment(id="thesis-b", claim="Second"),
            ThesisFragment(id="thesis-a", claim="First"),
        ),
    )

    summary = summarize_research(project)

    assert summary.missing_evidence_warnings == (
        "Thesis fragment thesis-a has no supporting evidence reference.",
        "Thesis fragment thesis-b has no supporting evidence reference.",
    )
    assert summary.overall_research_status == ResearchStatus.NEEDS_MORE_EVIDENCE


def test_research_domain_avoids_trade_recommendation_language() -> None:
    project = _project()
    summary = summarize_research(project)
    text = " ".join(
        [
            project.title,
            project.thesis_fragments[0].claim,
            summary.thesis_maturity,
            summary.overall_research_status.value,
        ]
    ).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "strong buy" not in text
    assert "guaranteed" not in text
    assert "risk-free" not in text
    assert "prediction" not in text
