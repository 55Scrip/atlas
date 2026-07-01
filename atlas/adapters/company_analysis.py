"""Adapter from a local company analysis JSON shape to CompanyAnalysisReport tuples.

Accepted JSON format (single report or list of reports)::

    {
      "company": {
        "id": "amd",
        "name": "AMD Corporation",
        "ticker": "AMD",
        "sector": "Semiconductors",
        "country": "USA"
      },
      "unknowns": [
        {"title": "Competitive moat durability", "detail": "Evidence is limited."}
      ],
      "evidence_links": [
        {"id": "ev1", "source": "10-K 2024", "description": "Revenue breakdown by segment."}
      ],
      "confidence": {
        "level": "low",
        "explanation": "Limited evidence available.",
        "drivers": ["Name and ticker known"],
        "limitations": ["No knowledge facts supplied"]
      },
      "what_could_change_the_view": [
        "More evidence on durable competitive advantages."
      ]
    }

Only ``company.name`` and ``company.ticker`` are required. All other fields are
optional with safe defaults. ``confidence.level`` must be one of:
``low``, ``moderate``, ``high``.

A list of such objects is also accepted.

This adapter is deterministic, side-effect free, and makes no network calls.
"""

from __future__ import annotations

from atlas.capabilities.company_analysis.models import (
    CompanyAnalysisConfidence,
    CompanyAnalysisEvidenceLink,
    CompanyAnalysisReport,
    CompanyAnalysisSection,
    CompanyAnalysisUnknown,
)
from atlas.shared import Company

_CONFIDENCE_LEVELS = frozenset({"low", "moderate", "high"})


def company_reports_from_dict(
    data: object, source: str = "<input>"
) -> tuple[CompanyAnalysisReport, ...]:
    """Build a tuple of CompanyAnalysisReport from a parsed JSON value.

    Accepts either a single report object or a list of report objects.
    Raises ValueError with a clear message on invalid input.
    """
    if isinstance(data, list):
        return tuple(_parse_report(item, i, source) for i, item in enumerate(data))
    if isinstance(data, dict):
        return (_parse_report(data, 0, source),)
    raise ValueError(
        f"Company analysis JSON in {source} must be a JSON object or list of objects, "
        f"got {type(data).__name__}"
    )


def _parse_report(data: object, idx: int, source: str) -> CompanyAnalysisReport:
    if not isinstance(data, dict):
        raise ValueError(
            f"Company analysis report at index {idx} in {source} must be a JSON object"
        )

    company = _parse_company(data.get("company", {}), idx, source)
    unknowns = _parse_unknowns(data.get("unknowns", []), idx, source)
    evidence_links = _parse_evidence_links(data.get("evidence_links", []), idx, source)
    confidence = _parse_confidence(data.get("confidence", {}), idx, source, unknowns)
    what_could_change = _parse_string_list(
        data.get("what_could_change_the_view", []), "what_could_change_the_view", idx, source
    )

    return CompanyAnalysisReport(
        company=company,
        sections=(),
        evidence_links=evidence_links,
        risks=(),
        unknowns=unknowns,
        confidence=confidence,
        what_could_change_the_view=what_could_change,
    )


def _parse_company(data: object, idx: int, source: str) -> Company:
    if not isinstance(data, dict):
        raise ValueError(
            f"'company' at report index {idx} in {source} must be a JSON object"
        )
    name = str(data.get("name", "")).strip()
    ticker = str(data.get("ticker", "")).strip().upper()
    if not name and not ticker:
        raise ValueError(
            f"Company at report index {idx} in {source} must have at least 'name' or 'ticker'"
        )
    return Company(
        id=str(data.get("id", ticker.lower() or "company")),
        name=name or ticker,
        ticker=ticker or name.upper()[:5],
        sector=str(data.get("sector", "")),
        industry=str(data.get("industry", "")),
        country=str(data.get("country", "")),
    )


def _parse_unknowns(
    raw: object, idx: int, source: str
) -> tuple[CompanyAnalysisUnknown, ...]:
    if not isinstance(raw, list):
        raise ValueError(
            f"'unknowns' at report index {idx} in {source} must be a list"
        )
    result = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(
                f"Unknown at index {i} in report {idx} in {source} must be a JSON object"
            )
        title = str(item.get("title", "Unknown")).strip()
        detail = str(item.get("detail", "")).strip()
        if not title:
            raise ValueError(
                f"Unknown at index {i} in report {idx} in {source} must have a non-empty 'title'"
            )
        result.append(CompanyAnalysisUnknown(title=title, detail=detail))
    return tuple(result)


def _parse_evidence_links(
    raw: object, idx: int, source: str
) -> tuple[CompanyAnalysisEvidenceLink, ...]:
    if not isinstance(raw, list):
        raise ValueError(
            f"'evidence_links' at report index {idx} in {source} must be a list"
        )
    result = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(
                f"Evidence link at index {i} in report {idx} in {source} must be a JSON object"
            )
        result.append(
            CompanyAnalysisEvidenceLink(
                id=str(item.get("id", f"ev-{i}")),
                source=str(item.get("source", "")),
                description=str(item.get("description", "")),
                reference_id=item.get("reference_id") or None,
            )
        )
    return tuple(result)


def _parse_confidence(
    raw: object,
    idx: int,
    source: str,
    unknowns: tuple[CompanyAnalysisUnknown, ...],
) -> CompanyAnalysisConfidence:
    if isinstance(raw, str):
        level = raw.strip().lower()
        if level not in _CONFIDENCE_LEVELS:
            raise ValueError(
                f"'confidence' at report index {idx} in {source} must be one of: "
                f"{', '.join(sorted(_CONFIDENCE_LEVELS))}"
            )
        return CompanyAnalysisConfidence(
            level=level,
            explanation=f"Confidence is {level}.",
            drivers=(),
            limitations=tuple(u.detail for u in unknowns if u.detail),
        )
    if not isinstance(raw, dict):
        raise ValueError(
            f"'confidence' at report index {idx} in {source} must be a string or object"
        )
    level = str(raw.get("level", "low")).strip().lower()
    if level not in _CONFIDENCE_LEVELS:
        raise ValueError(
            f"Invalid confidence level {level!r} at report index {idx} in {source}. "
            f"Valid values: {', '.join(sorted(_CONFIDENCE_LEVELS))}"
        )
    return CompanyAnalysisConfidence(
        level=level,
        explanation=str(raw.get("explanation", f"Confidence is {level}.")),
        drivers=tuple(str(d) for d in raw.get("drivers", []) if str(d).strip()),
        limitations=tuple(str(l) for l in raw.get("limitations", []) if str(l).strip()),
    )


def _parse_string_list(
    raw: object, field: str, idx: int, source: str
) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise ValueError(
            f"'{field}' at report index {idx} in {source} must be a list"
        )
    return tuple(str(item).strip() for item in raw if str(item).strip())
