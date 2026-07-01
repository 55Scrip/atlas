"""Serialise ResearchProject tuples to the Daily Brief research JSON format.

The output dict is compatible with ``atlas daily summary --research``.

Output format::

    {
      "notes": [
        {
          "id": "proj-nvda",
          "title": "NVDA Research",
          "body": "NVDA — researching",
          "created_at": "",
          "related_tickers": ["NVDA"]
        }
      ],
      "open_questions": [
        "What is the long-term GPU TAM?",
        "Who are the key competitors?"
      ]
    }

This module is deterministic and makes no network calls.
"""

from __future__ import annotations

from atlas.domains.research.models import (
    ResearchProject,
    ResearchQuestionStatus,
)

_OPEN_STATUSES = frozenset({ResearchQuestionStatus.OPEN, ResearchQuestionStatus.RESEARCHING})


def research_projects_to_dict(projects: tuple[ResearchProject, ...]) -> dict:
    """Convert a tuple of ResearchProject to a Daily Brief research JSON dict."""
    notes = [_project_to_note(p) for p in projects]
    open_questions = [
        q.question
        for p in projects
        for q in p.questions
        if q.status in _OPEN_STATUSES and q.question.strip()
    ]
    return {"notes": notes, "open_questions": open_questions}


def _project_to_note(project: ResearchProject) -> dict:
    return {
        "id": project.id,
        "title": project.title,
        "body": f"{project.topic} — {project.status.value}",
        "created_at": "",
        "related_tickers": [project.topic] if project.topic.isupper() and len(project.topic) <= 5 else [],
    }
