from atlas.domains.research.models import (
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
    ResearchSummary,
)


def summarize_research(project: ResearchProject) -> ResearchSummary:
    """Return a deterministic summary of research maturity."""

    open_questions = tuple(
        question
        for question in project.questions
        if question.status in {ResearchQuestionStatus.OPEN, ResearchQuestionStatus.RESEARCHING}
    )
    resolved_questions = tuple(
        question for question in project.questions if question.status == ResearchQuestionStatus.RESOLVED
    )
    missing_evidence_warnings = tuple(
        f"Thesis fragment {fragment.id} has no supporting evidence reference."
        for fragment in sorted(project.thesis_fragments, key=lambda item: item.id)
        if not fragment.supporting_evidence_reference_ids
    )
    return ResearchSummary(
        project_id=project.id,
        project_title=project.title,
        number_of_notes=len(project.notes),
        number_of_open_questions=len(open_questions),
        number_of_resolved_questions=len(resolved_questions),
        number_of_assumptions=len(project.assumptions),
        thesis_maturity=_thesis_maturity(project),
        missing_evidence_warnings=missing_evidence_warnings,
        overall_research_status=_overall_status(project, open_questions, missing_evidence_warnings),
    )


def _thesis_maturity(project: ResearchProject) -> str:
    if not project.thesis_fragments:
        return "No thesis formed"
    if any(not fragment.supporting_evidence_reference_ids for fragment in project.thesis_fragments):
        return "Needs more evidence"
    if all(fragment.status == ResearchStatus.READY_FOR_REVIEW for fragment in project.thesis_fragments):
        return "Ready for review"
    if any(fragment.status == ResearchStatus.THESIS_FORMING for fragment in project.thesis_fragments):
        return "Thesis forming"
    return "Exploratory"


def _overall_status(
    project: ResearchProject,
    open_questions: tuple[ResearchQuestion, ...],
    missing_evidence_warnings: tuple[str, ...],
) -> ResearchStatus:
    if project.status == ResearchStatus.ARCHIVED:
        return ResearchStatus.ARCHIVED
    if not project.notes and not project.questions and not project.thesis_fragments:
        return ResearchStatus.NOT_STARTED
    if missing_evidence_warnings:
        return ResearchStatus.NEEDS_MORE_EVIDENCE
    if project.thesis_fragments and not open_questions:
        return ResearchStatus.READY_FOR_REVIEW
    if project.thesis_fragments:
        return ResearchStatus.THESIS_FORMING
    return ResearchStatus.RESEARCHING
