from collections import Counter

from atlas.domains.research.models import (
    ResearchIssueSeverity,
    ResearchProject,
    ResearchQuestionStatus,
    ResearchStatus,
    ResearchValidationIssue,
    ResearchValidationResult,
)


ALLOWED_STATUS_TRANSITIONS: dict[ResearchStatus, frozenset[ResearchStatus]] = {
    ResearchStatus.NOT_STARTED: frozenset(
        {ResearchStatus.RESEARCHING, ResearchStatus.ARCHIVED}
    ),
    ResearchStatus.RESEARCHING: frozenset(
        {
            ResearchStatus.NEEDS_MORE_EVIDENCE,
            ResearchStatus.THESIS_FORMING,
            ResearchStatus.READY_FOR_REVIEW,
            ResearchStatus.ARCHIVED,
        }
    ),
    ResearchStatus.NEEDS_MORE_EVIDENCE: frozenset(
        {ResearchStatus.RESEARCHING, ResearchStatus.THESIS_FORMING, ResearchStatus.ARCHIVED}
    ),
    ResearchStatus.THESIS_FORMING: frozenset(
        {
            ResearchStatus.NEEDS_MORE_EVIDENCE,
            ResearchStatus.READY_FOR_REVIEW,
            ResearchStatus.ARCHIVED,
        }
    ),
    ResearchStatus.READY_FOR_REVIEW: frozenset(
        {ResearchStatus.THESIS_FORMING, ResearchStatus.ARCHIVED}
    ),
    ResearchStatus.ARCHIVED: frozenset(),
}


def validate_research_project(project: ResearchProject) -> ResearchValidationResult:
    """Validate research artifacts and return structured issues."""

    issues: list[ResearchValidationIssue] = []
    if not project.title.strip():
        issues.append(
            ResearchValidationIssue(
                code="missing_title",
                message="Research project is missing a title.",
                severity=ResearchIssueSeverity.ERROR,
                item_id=project.id,
            )
        )
    if not project.notes and not project.questions and not project.thesis_fragments:
        issues.append(
            ResearchValidationIssue(
                code="empty_research_project",
                message="Research project has no notes, questions, or thesis fragments.",
                severity=ResearchIssueSeverity.WARNING,
                item_id=project.id,
            )
        )

    question_counts = Counter(question.id for question in project.questions)
    for question_id, count in sorted(question_counts.items()):
        if count > 1:
            issues.append(
                ResearchValidationIssue(
                    code="duplicate_question_id",
                    message=f"Research question {question_id} appears more than once.",
                    severity=ResearchIssueSeverity.ERROR,
                    item_id=question_id,
                )
            )

    for question in sorted(project.questions, key=lambda item: item.id):
        if (
            question.status == ResearchQuestionStatus.RESOLVED
            and not question.resolution_notes.strip()
        ):
            issues.append(
                ResearchValidationIssue(
                    code="resolved_question_missing_resolution_notes",
                    message=f"Resolved question {question.id} has no resolution notes.",
                    severity=ResearchIssueSeverity.WARNING,
                    item_id=question.id,
                )
            )
        if question.resolved_at and question.status != ResearchQuestionStatus.RESOLVED:
            issues.append(
                ResearchValidationIssue(
                    code="resolved_timestamp_without_resolved_status",
                    message=f"Question {question.id} has a resolved timestamp but is not resolved.",
                    severity=ResearchIssueSeverity.WARNING,
                    item_id=question.id,
                )
            )

    for assumption in sorted(project.assumptions, key=lambda item: item.id):
        if not assumption.explanation.strip():
            issues.append(
                ResearchValidationIssue(
                    code="assumption_missing_explanation",
                    message=f"Assumption {assumption.id} is missing an explanation.",
                    severity=ResearchIssueSeverity.WARNING,
                    item_id=assumption.id,
                )
            )

    for fragment in sorted(project.thesis_fragments, key=lambda item: item.id):
        if not fragment.supporting_evidence_reference_ids:
            issues.append(
                ResearchValidationIssue(
                    code="thesis_fragment_missing_evidence",
                    message=f"Thesis fragment {fragment.id} has no supporting evidence reference.",
                    severity=ResearchIssueSeverity.WARNING,
                    item_id=fragment.id,
                )
            )

    return ResearchValidationResult(
        is_valid=not any(issue.severity == ResearchIssueSeverity.ERROR for issue in issues),
        issues=tuple(issues),
    )


def is_valid_status_transition(current: ResearchStatus, next_status: ResearchStatus) -> bool:
    """Return whether a research status transition is allowed."""

    if current == next_status:
        return True
    return next_status in ALLOWED_STATUS_TRANSITIONS[current]
