"""Daily Brief JSON loader.

Parses local JSON files into lightweight structures the Daily Brief engine
can consume. All parsing is local-only, side-effect free, and makes no
network calls.

Each loader function accepts a raw dict (already JSON-parsed) and returns
the corresponding structured object. The CLI reads the file and hands the
dict to the appropriate loader; this module does not open files itself.

Supported formats
-----------------
Research JSON::

    {
      "notes": [
        {"id": "n1", "title": "NVDA research", "body": "Notes here.",
         "created_at": "2026-07-01", "related_tickers": ["NVDA"]}
      ],
      "open_questions": ["What is the TAM?", "Who owns the supply chain?"]
    }

Watchlist JSON::

    {
      "name": "My Watchlist",
      "open_questions": [
        {"id": "wq1", "question": "What is the competitive moat?", "status": "open"}
      ],
      "suggested_next_research_steps": ["Research NVDA moat further."]
    }

Discovery JSON::

    {
      "candidates": [
        {
          "identifier": "NVDA",
          "title": "NVIDIA Corporation",
          "reasons": [{"title": "Knowledge Fact", "detail": "Multiple facts available."}],
          "priority": "moderate"
        }
      ]
    }

Company Analysis JSON::

    {
      "company": {"id": "nvda", "name": "NVIDIA", "ticker": "NVDA",
                  "sector": "Semiconductors", "country": "USA"},
      "unknowns": [{"title": "Competitive moat", "detail": "Evidence incomplete."}],
      "evidence_links": [{"id": "ev1", "source": "10-K", "description": "Revenue table."}],
      "confidence": {"level": "medium", "explanation": "Moderate evidence.",
                     "drivers": ["Known revenue"], "limitations": ["Limited competitive data"]}
    }

Multiple company analysis reports may appear in a single file as a list::

    [
      { "company": {...}, "unknowns": [...], ... },
      { "company": {...}, "unknowns": [...], ... }
    ]
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


# ── lightweight value types ────────────────────────────────────────────────────
# These match the attribute names the engine reads via getattr.


@dataclass(frozen=True)
class _ReasonFromJSON:
    title: str
    detail: str


@dataclass(frozen=True)
class _ResearchNoteFromJSON:
    id: str
    title: str
    body: str
    created_at: str = ""
    related_tickers: tuple[str, ...] = ()


@dataclass(frozen=True)
class _WatchlistQuestionFromJSON:
    id: str
    question: str
    status: str = "open"


@dataclass(frozen=True)
class _WatchlistReportFromJSON:
    name: str
    open_questions: tuple[_WatchlistQuestionFromJSON, ...]
    suggested_next_research_steps: tuple[str, ...]


@dataclass(frozen=True)
class _DiscoveryCandidateFromJSON:
    identifier: str
    title: str
    reasons: tuple[_ReasonFromJSON, ...]
    priority: str = "moderate"


@dataclass(frozen=True)
class _DiscoveryReportFromJSON:
    candidates: tuple[_DiscoveryCandidateFromJSON, ...]


@dataclass(frozen=True)
class _CompanyFromJSON:
    id: str
    name: str
    ticker: str
    sector: str = ""
    country: str = ""


@dataclass(frozen=True)
class _CompanyUnknownFromJSON:
    title: str
    detail: str = ""


@dataclass(frozen=True)
class _EvidenceLinkFromJSON:
    id: str
    source: str
    description: str


@dataclass(frozen=True)
class _CompanyReportFromJSON:
    company: _CompanyFromJSON
    unknowns: tuple[_CompanyUnknownFromJSON, ...]
    evidence_links: tuple[_EvidenceLinkFromJSON, ...]


# ── file reader ────────────────────────────────────────────────────────────────


def load_json_file(path: Path) -> object:
    """Read and parse a local JSON file. Raises ValueError on bad input."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {path}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


# ── per-format loaders ─────────────────────────────────────────────────────────


def parse_research_json(data: object, path: Path) -> tuple[tuple, tuple[str, ...]]:
    """Parse research JSON into (notes, open_questions).

    Returns a tuple of (_ResearchNoteFromJSON, ...) and open question strings.
    """
    if not isinstance(data, dict):
        raise ValueError(f"Research JSON in {path} must be a JSON object, got {type(data).__name__}")

    raw_notes = data.get("notes", [])
    if not isinstance(raw_notes, list):
        raise ValueError(f"'notes' in {path} must be a list")
    notes = tuple(
        _parse_research_note(item, i, path) for i, item in enumerate(raw_notes)
    )

    raw_questions = data.get("open_questions", [])
    if not isinstance(raw_questions, list):
        raise ValueError(f"'open_questions' in {path} must be a list")
    questions = tuple(str(q) for q in raw_questions if str(q).strip())

    return notes, questions


def parse_watchlist_json(data: object, path: Path) -> _WatchlistReportFromJSON:
    """Parse watchlist JSON into a _WatchlistReportFromJSON."""
    if not isinstance(data, dict):
        raise ValueError(f"Watchlist JSON in {path} must be a JSON object")

    name = str(data.get("name", "Watchlist"))

    raw_questions = data.get("open_questions", [])
    if not isinstance(raw_questions, list):
        raise ValueError(f"'open_questions' in {path} must be a list")
    questions = tuple(
        _parse_watchlist_question(item, i, path) for i, item in enumerate(raw_questions)
    )

    raw_steps = data.get("suggested_next_research_steps", [])
    if not isinstance(raw_steps, list):
        raise ValueError(f"'suggested_next_research_steps' in {path} must be a list")
    steps = tuple(str(s) for s in raw_steps if str(s).strip())

    return _WatchlistReportFromJSON(
        name=name,
        open_questions=questions,
        suggested_next_research_steps=steps,
    )


def parse_discovery_json(data: object, path: Path) -> _DiscoveryReportFromJSON:
    """Parse discovery JSON into a _DiscoveryReportFromJSON."""
    if not isinstance(data, dict):
        raise ValueError(f"Discovery JSON in {path} must be a JSON object")

    raw_candidates = data.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raise ValueError(f"'candidates' in {path} must be a list")
    candidates = tuple(
        _parse_discovery_candidate(item, i, path) for i, item in enumerate(raw_candidates)
    )

    return _DiscoveryReportFromJSON(candidates=candidates)


def parse_company_analysis_json(data: object, path: Path) -> tuple[_CompanyReportFromJSON, ...]:
    """Parse company analysis JSON into a tuple of _CompanyReportFromJSON.

    Accepts either a single report object or a list of report objects.
    """
    if isinstance(data, list):
        return tuple(
            _parse_single_company_report(item, i, path) for i, item in enumerate(data)
        )
    if isinstance(data, dict):
        return (_parse_single_company_report(data, 0, path),)
    raise ValueError(f"Company analysis JSON in {path} must be an object or list of objects")


# ── internal parsers ───────────────────────────────────────────────────────────


def _parse_research_note(item: object, idx: int, path: Path) -> _ResearchNoteFromJSON:
    if not isinstance(item, dict):
        raise ValueError(f"Research note at index {idx} in {path} must be an object")
    try:
        return _ResearchNoteFromJSON(
            id=str(item.get("id", f"note-{idx}")),
            title=str(item["title"]),
            body=str(item.get("body", "")),
            created_at=str(item.get("created_at", "")),
            related_tickers=tuple(str(t) for t in item.get("related_tickers", [])),
        )
    except KeyError as exc:
        raise ValueError(f"Research note at index {idx} in {path} missing required field {exc}") from exc


def _parse_watchlist_question(item: object, idx: int, path: Path) -> _WatchlistQuestionFromJSON:
    if isinstance(item, str):
        return _WatchlistQuestionFromJSON(id=f"wq-{idx}", question=item)
    if not isinstance(item, dict):
        raise ValueError(f"Watchlist question at index {idx} in {path} must be a string or object")
    try:
        return _WatchlistQuestionFromJSON(
            id=str(item.get("id", f"wq-{idx}")),
            question=str(item["question"]),
            status=str(item.get("status", "open")),
        )
    except KeyError as exc:
        raise ValueError(f"Watchlist question at index {idx} in {path} missing required field {exc}") from exc


def _parse_discovery_candidate(item: object, idx: int, path: Path) -> _DiscoveryCandidateFromJSON:
    if not isinstance(item, dict):
        raise ValueError(f"Discovery candidate at index {idx} in {path} must be an object")
    try:
        raw_reasons = item.get("reasons", [])
        reasons = tuple(
            _ReasonFromJSON(
                title=str(r.get("title", "Discovery")),
                detail=str(r.get("detail", "Candidate identified.")),
            )
            for r in (raw_reasons if isinstance(raw_reasons, list) else [])
        )
        if not reasons:
            identifier = str(item.get("identifier", item.get("ticker", f"candidate-{idx}")))
            reasons = (_ReasonFromJSON(title="Discovery", detail=f"{identifier} identified as a research candidate."),)
        return _DiscoveryCandidateFromJSON(
            identifier=str(item.get("identifier", item.get("ticker", f"candidate-{idx}"))),
            title=str(item.get("title", "")),
            reasons=reasons,
            priority=str(item.get("priority", "moderate")),
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Discovery candidate at index {idx} in {path} is malformed: {exc}") from exc


def _parse_single_company_report(item: object, idx: int, path: Path) -> _CompanyReportFromJSON:
    if not isinstance(item, dict):
        raise ValueError(f"Company analysis report at index {idx} in {path} must be an object")
    try:
        raw_company = item.get("company", {})
        if not isinstance(raw_company, dict):
            raise ValueError(f"'company' field at index {idx} in {path} must be an object")
        company = _CompanyFromJSON(
            id=str(raw_company.get("id", f"company-{idx}")),
            name=str(raw_company.get("name", "Unknown")),
            ticker=str(raw_company.get("ticker", "UNKN")),
            sector=str(raw_company.get("sector", "")),
            country=str(raw_company.get("country", "")),
        )
        unknowns = tuple(
            _CompanyUnknownFromJSON(
                title=str(u.get("title", "Unknown")),
                detail=str(u.get("detail", "")),
            )
            for u in (item.get("unknowns", []) or [])
            if isinstance(u, dict)
        )
        evidence_links = tuple(
            _EvidenceLinkFromJSON(
                id=str(e.get("id", f"ev-{i}")),
                source=str(e.get("source", "")),
                description=str(e.get("description", "")),
            )
            for i, e in enumerate(item.get("evidence_links", []) or [])
            if isinstance(e, dict)
        )
        return _CompanyReportFromJSON(
            company=company,
            unknowns=unknowns,
            evidence_links=evidence_links,
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Company analysis report at index {idx} in {path} is malformed: {exc}") from exc
