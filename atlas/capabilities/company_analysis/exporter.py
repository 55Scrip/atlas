"""Serialise CompanyAnalysisReport to the Daily Brief company analysis JSON format.

The output dict (or list of dicts) is compatible with
``atlas daily summary --company-analysis`` and ``parse_company_analysis_json``.

Single-report output format::

    {
      "company": {
        "id": "amd",
        "name": "AMD Corporation",
        "ticker": "AMD",
        "sector": "Semiconductors",
        "country": "USA"
      },
      "unknowns": [
        {"title": "Missing Evidence", "detail": "No knowledge facts were supplied."}
      ],
      "evidence_links": [
        {"id": "knowledge:fact-1", "source": "10-K 2025", "description": "Revenue breakdown."}
      ],
      "confidence": {
        "level": "low",
        "explanation": "Confidence is low because ...",
        "drivers": ["2 core company field(s) available"],
        "limitations": ["No knowledge facts or decision evidence were supplied."]
      },
      "what_could_change_the_view": [
        "Resolve: No knowledge facts or decision evidence were supplied."
      ]
    }

This module is deterministic and makes no network calls.
"""

from __future__ import annotations

from atlas.capabilities.company_analysis.models import CompanyAnalysisReport


def company_report_to_dict(report: CompanyAnalysisReport) -> dict:
    """Convert a CompanyAnalysisReport to a Daily Brief–compatible dict."""
    return {
        "company": {
            "id": report.company.id,
            "name": report.company.name,
            "ticker": report.company.ticker,
            "sector": report.company.sector,
            "country": report.company.country,
        },
        "unknowns": [
            {"title": u.title, "detail": u.detail}
            for u in report.unknowns
        ],
        "evidence_links": [
            {"id": e.id, "source": e.source, "description": e.description}
            for e in report.evidence_links
        ],
        "confidence": {
            "level": report.confidence.level,
            "explanation": report.confidence.explanation,
            "drivers": list(report.confidence.drivers),
            "limitations": list(report.confidence.limitations),
        },
        "what_could_change_the_view": list(report.what_could_change_the_view),
    }


def company_reports_to_list(reports: tuple[CompanyAnalysisReport, ...]) -> list:
    """Convert a tuple of CompanyAnalysisReport to a JSON-serialisable list."""
    return [company_report_to_dict(r) for r in reports]
