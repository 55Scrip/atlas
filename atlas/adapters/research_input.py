"""Adapter from a local research JSON shape to ResearchProject tuples.

Accepted JSON format::

    {
      "projects": [
        {
          "id": "proj-nvda",
          "title": "NVDA Research",
          "topic": "NVDA",
          "status": "researching",
          "questions": [
            "What is the long-term GPU TAM?",
            "Who are the key competitors?"
          ]
        }
      ]
    }

Only ``id`` and ``topic`` are required. ``title`` defaults to the topic.
``status`` must be one of: not_started, researching, needs_more_evidence,
thesis_forming, ready_for_review, archived.
``questions`` may be plain strings or omitted.

This adapter is deterministic, side-effect free, and makes no network calls.
"""

from __future__ import annotations

from atlas.domains.research.models import (
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
)

_STATUS_MAP: dict[str, ResearchStatus] = {
    "not_started": ResearchStatus.NOT_STARTED,
    "researching": ResearchStatus.RESEARCHING,
    "needs_more_evidence": ResearchStatus.NEEDS_MORE_EVIDENCE,
    "thesis_forming": ResearchStatus.THESIS_FORMING,
    "ready_for_review": ResearchStatus.READY_FOR_REVIEW,
    "archived": ResearchStatus.ARCHIVED,
}


def research_projects_from_dict(data: object, source: str = "<input>") -> tuple[ResearchProject, ...]:
    """Build a tuple of ResearchProject from a parsed JSON dict.

    Raises ValueError with a clear message on invalid input.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"Research JSON in {source} must be a JSON object, got {type(data).__name__}"
        )

    raw_projects = data.get("projects", [])
    if not isinstance(raw_projects, list):
        raise ValueError(f"'projects' in {source} must be a list")

    return tuple(_parse_project(item, i, source) for i, item in enumerate(raw_projects))


def _parse_project(data: object, idx: int, source: str) -> ResearchProject:
    if not isinstance(data, dict):
        raise ValueError(f"Research project at index {idx} in {source} must be a JSON object")

    try:
        project_id = str(data["id"])
    except KeyError as exc:
        raise ValueError(
            f"Research project at index {idx} in {source} missing required field {exc}"
        ) from exc

    topic = str(data.get("topic", project_id))
    title = str(data.get("title", topic))
    status = _parse_status(data.get("status", "researching"), idx, source)

    raw_questions = data.get("questions", [])
    if not isinstance(raw_questions, list):
        raise ValueError(f"'questions' at project {idx} in {source} must be a list")

    questions = tuple(
        ResearchQuestion(
            id=f"q-{project_id}-{i}",
            question=str(q).strip(),
            related_topic=topic,
            status=ResearchQuestionStatus.OPEN,
        )
        for i, q in enumerate(raw_questions)
        if str(q).strip()
    )

    return ResearchProject(
        id=project_id,
        title=title,
        topic=topic,
        status=status,
        questions=questions,
    )


def _parse_status(raw: object, idx: int, source: str) -> ResearchStatus:
    normalized = str(raw).strip().lower() if raw is not None else "researching"
    if normalized not in _STATUS_MAP:
        valid = ", ".join(_STATUS_MAP)
        raise ValueError(
            f"Invalid status {raw!r} at research project {idx} in {source}. "
            f"Valid values: {valid}"
        )
    return _STATUS_MAP[normalized]
