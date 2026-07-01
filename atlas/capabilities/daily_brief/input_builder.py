"""Daily Brief input builder.

Transforms typed Atlas domain and capability structures into a DailyBriefInput.
The builder is deterministic, side-effect free, and makes no network calls.

Usage::

    from atlas.capabilities.daily_brief.input_builder import build_daily_brief_input

    brief_input = build_daily_brief_input(
        portfolio_summary=my_portfolio_summary,
        research_notes=my_notes,
        watchlist_report=my_watchlist_report,
    )
    report = DailyBriefCapability().generate(brief_input)
"""

from __future__ import annotations

from atlas.capabilities.daily_brief.models import DailyBriefInput
from atlas.domains.research.models import ResearchProject, ResearchQuestionStatus


def build_daily_brief_input(
    *,
    portfolio_summary: object | None = None,
    research_notes: tuple = (),
    research_projects: tuple[ResearchProject, ...] = (),
    company_reports: tuple = (),
    watchlist_report: object | None = None,
    discovery_report: object | None = None,
    knowledge_node_count: int = 0,
    open_research_questions: tuple[str, ...] = (),
    date_label: str = "",
) -> DailyBriefInput:
    """Build a DailyBriefInput from typed Atlas structures.

    All parameters are optional. Passing nothing produces a valid no-developments input.

    research_projects: open questions are extracted and merged with
    open_research_questions so callers do not need to do this manually.
    """
    merged_questions = tuple(open_research_questions) + _extract_open_questions(research_projects)

    return DailyBriefInput(
        portfolio_summary=portfolio_summary,
        research_notes=research_notes,
        company_reports=company_reports,
        watchlist_report=watchlist_report,
        discovery_report=discovery_report,
        knowledge_node_count=knowledge_node_count,
        open_research_questions=merged_questions,
        date_label=date_label,
    )


def _extract_open_questions(projects: tuple[ResearchProject, ...]) -> tuple[str, ...]:
    questions: list[str] = []
    for project in projects:
        for q in project.questions:
            if q.status in (
                ResearchQuestionStatus.OPEN,
                ResearchQuestionStatus.RESEARCHING,
            ):
                questions.append(q.question)
    return tuple(questions)
