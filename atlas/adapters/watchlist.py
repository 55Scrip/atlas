"""Adapter from a local watchlist JSON shape to WatchlistIntelligenceInput.

Accepted JSON format::

    {
      "name": "My Watchlist",
      "items": [
        {
          "id": "amd",
          "ticker": "AMD",
          "company": "AMD Corporation",
          "status": "researching",
          "open_questions": [
            "What evidence supports long-term margin expansion?"
          ],
          "manual_observations": [
            "Entered data centre market aggressively."
          ]
        }
      ]
    }

All fields except ``ticker`` are optional. ``status`` must be one of:
observing, researching, needs_more_evidence, thesis_forming,
ready_for_review, paused, archived.

``open_questions`` are converted to ResearchProject questions so the
WatchlistIntelligenceEngine can surface them as unresolved questions in
the generated report.

This adapter is deterministic, side-effect free, and makes no network calls.
"""

from __future__ import annotations

from atlas.capabilities.watchlist_intelligence.models import (
    WatchlistIntelligenceInput,
    WatchlistItem,
    WatchlistStatus,
)
from atlas.domains.research.models import (
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
)

_STATUS_MAP: dict[str, WatchlistStatus] = {
    "observing": WatchlistStatus.OBSERVING,
    "researching": WatchlistStatus.RESEARCHING,
    "needs_more_evidence": WatchlistStatus.NEEDS_MORE_EVIDENCE,
    "thesis_forming": WatchlistStatus.THESIS_FORMING,
    "ready_for_review": WatchlistStatus.READY_FOR_REVIEW,
    "paused": WatchlistStatus.PAUSED,
    "archived": WatchlistStatus.ARCHIVED,
}


def watchlist_input_from_dict(data: object, source: str = "<input>") -> WatchlistIntelligenceInput:
    """Build a WatchlistIntelligenceInput from a parsed JSON dict.

    Raises ValueError with a clear message on invalid input.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"Watchlist input in {source} must be a JSON object, got {type(data).__name__}"
        )

    name = str(data.get("name", "My Watchlist"))
    raw_items = data.get("items", [])
    if not isinstance(raw_items, list):
        raise ValueError(f"'items' in {source} must be a list")

    items = tuple(_parse_item(item, i, source) for i, item in enumerate(raw_items))
    return WatchlistIntelligenceInput(name=name, items=items)


def _parse_item(data: object, idx: int, source: str) -> WatchlistItem:
    if not isinstance(data, dict):
        raise ValueError(
            f"Watchlist item at index {idx} in {source} must be a JSON object"
        )

    ticker = data.get("ticker")
    if not ticker or not isinstance(ticker, str) or not ticker.strip():
        raise ValueError(
            f"Watchlist item at index {idx} in {source} must have a non-empty 'ticker'"
        )
    ticker = ticker.strip().upper()

    item_id = str(data.get("id", ticker.lower()))
    company_name = str(data.get("company", data.get("name", ticker)))
    status = _parse_status(data.get("status", "observing"), idx, source)

    raw_questions = data.get("open_questions", [])
    if not isinstance(raw_questions, list):
        raise ValueError(f"'open_questions' at item {idx} in {source} must be a list")
    questions = [str(q).strip() for q in raw_questions if str(q).strip()]

    raw_observations = data.get("manual_observations", [])
    if not isinstance(raw_observations, list):
        raise ValueError(f"'manual_observations' at item {idx} in {source} must be a list")
    observations = tuple(str(o).strip() for o in raw_observations if str(o).strip())

    research_project: ResearchProject | None = None
    if questions:
        research_project = ResearchProject(
            id=f"research-{item_id}",
            title=f"{ticker} Research",
            topic=ticker,
            status=ResearchStatus.RESEARCHING,
            questions=tuple(
                ResearchQuestion(
                    id=f"q-{item_id}-{i}",
                    question=q,
                    related_topic=ticker,
                    status=ResearchQuestionStatus.OPEN,
                )
                for i, q in enumerate(questions)
            ),
        )

    return WatchlistItem(
        id=item_id,
        ticker=ticker,
        name=company_name,
        status=status,
        research_project=research_project,
        manual_observations=observations,
    )


def _parse_status(raw: object, idx: int, source: str) -> WatchlistStatus:
    normalized = str(raw).strip().lower() if raw is not None else "observing"
    if normalized not in _STATUS_MAP:
        valid = ", ".join(_STATUS_MAP)
        raise ValueError(
            f"Invalid status {raw!r} at watchlist item {idx} in {source}. "
            f"Valid values: {valid}"
        )
    return _STATUS_MAP[normalized]
