"""Discovery JSON exporter.

Serializes DiscoveryReport to a dict that matches the Daily Brief Sprint 50
discovery JSON input format consumed by
atlas.capabilities.daily_brief.json_loader.parse_discovery_json.

All functions are pure, deterministic, and side-effect free.
"""

from __future__ import annotations

from atlas.capabilities.discovery.models import DiscoveryReport


def discovery_report_to_dict(report: DiscoveryReport) -> dict:
    """Convert a DiscoveryReport to a JSON-serializable dict.

    The output format is compatible with ``atlas daily summary --discovery``.
    """
    return {
        "summary": report.summary,
        "candidates": [
            {
                "identifier": c.identifier,
                "title": c.title,
                "reasons": [
                    {"title": r.title, "detail": r.detail}
                    for r in c.reasons
                ],
                "priority": c.priority.value,
                "confidence": c.confidence,
                "unknowns": [
                    {"title": u.title, "detail": u.detail}
                    for u in c.unknowns
                ],
                "suggested_next_research_questions": [
                    {"question": q.question, "source": q.source}
                    for q in c.suggested_next_research_questions
                ],
            }
            for c in report.candidates
        ],
        "unknowns": [
            {"title": u.title, "detail": u.detail}
            for u in report.unknowns
        ],
    }
