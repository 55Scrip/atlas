"""Watchlist Intelligence JSON exporter.

Serializes WatchlistIntelligenceReport to a dict that matches the Daily Brief
Sprint 50 watchlist JSON input format consumed by
atlas.capabilities.daily_brief.json_loader.parse_watchlist_json.

All functions are pure, deterministic, and side-effect free.
"""

from __future__ import annotations

from atlas.capabilities.watchlist_intelligence.models import WatchlistIntelligenceReport


def watchlist_report_to_dict(report: WatchlistIntelligenceReport) -> dict:
    """Convert a WatchlistIntelligenceReport to a JSON-serializable dict.

    The output format is compatible with ``atlas daily summary --watchlist``.
    """
    return {
        "name": report.name,
        "overview": report.overview,
        "open_questions": [
            {
                "id": q.id,
                "question": q.question,
                "status": str(q.status),
            }
            for q in report.open_questions
        ],
        "suggested_next_research_steps": list(report.suggested_next_research_steps),
        "companies_needing_attention": [
            {
                "ticker": obs.ticker,
                "title": obs.title,
                "detail": obs.detail,
                "priority": obs.priority.value,
            }
            for obs in report.companies_needing_attention
        ],
        "unknowns": [
            {
                "ticker": u.ticker,
                "title": u.title,
                "detail": u.detail,
            }
            for u in report.unknowns
        ],
        "evidence_gaps": [
            {
                "ticker": u.ticker,
                "title": u.title,
                "detail": u.detail,
            }
            for u in report.evidence_gaps
        ],
    }
