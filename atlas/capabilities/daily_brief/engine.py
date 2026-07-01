"""Daily Brief capability engine.

Deterministic, no external calls, no AI, no network access.
Consumes optional domain/capability structures and organises them into a
calm structured daily overview.
"""

from __future__ import annotations

from atlas.capabilities.daily_brief.models import (
    DailyBriefEvidenceLink,
    DailyBriefInput,
    DailyBriefItem,
    DailyBriefPriority,
    DailyBriefReport,
    DailyBriefSection,
    DailyBriefSummary,
    DailyBriefUnknown,
)

_NO_DEVELOPMENTS_MESSAGE = (
    "No meaningful developments were identified from the available inputs."
)


class DailyBriefCapability:
    """Generates a deterministic Daily Brief report from provided inputs."""

    def generate(self, brief_input: DailyBriefInput | None = None) -> DailyBriefReport:
        data = brief_input or DailyBriefInput()
        sections = _build_sections(data)
        unknowns = _build_unknowns(data)
        evidence_gaps = _build_evidence_gaps(data)
        next_steps = _build_next_steps(data)
        all_items = [item for section in sections for item in section.items]
        high_priority_count = sum(
            1 for item in all_items if item.priority == DailyBriefPriority.HIGH
        )
        moderate_priority_count = sum(
            1 for item in all_items if item.priority == DailyBriefPriority.MODERATE
        )
        has_developments = _has_meaningful_input(data)
        overall_priority = _overall_priority(high_priority_count, moderate_priority_count)
        bottom_line = _bottom_line(has_developments, high_priority_count, data)
        summary = DailyBriefSummary(
            bottom_line=bottom_line,
            overall_priority=overall_priority,
            item_count=len(all_items),
            has_meaningful_developments=has_developments,
        )
        return DailyBriefReport(
            title="Atlas Daily Brief",
            summary=summary,
            sections=tuple(sections),
            unknowns=tuple(unknowns),
            evidence_gaps=tuple(evidence_gaps),
            next_research_steps=tuple(next_steps),
        )


_SEP = "─" * 45


def render_daily_brief_report(report: DailyBriefReport) -> str:
    lines: list[str] = [report.title, _SEP]

    # Opening Summary
    lines += [
        "",
        "Opening Summary",
        report.summary.bottom_line,
        f"Overall priority: {report.summary.overall_priority.value}",
    ]
    date_label = getattr(report.summary, "date_label", "")
    if date_label:
        lines.append(f"Date: {date_label}")

    # Included Context — summarise what inputs are present
    ctx_lines = _render_included_context(report)
    if ctx_lines:
        lines += ["", _SEP, "Included Context", ""] + ctx_lines

    # Detail sections
    for section in report.sections:
        lines += ["", _SEP, section.title]
        if not section.items:
            lines.append("  No items.")
        elif section.title == "Company Analysis Context":
            lines.append("")
            for item in section.items:
                lines.append(f"  {item.title}")
                lines.append(f"    {item.detail}")
        else:
            lines.append("")
            for item in section.items:
                marker = _priority_marker(item.priority)
                lines.append(f"  {marker}{item.title}: {item.detail}")

    # Evidence Gaps (before Unknowns)
    if report.evidence_gaps:
        lines += ["", _SEP, "Evidence Gaps", ""]
        for gap in report.evidence_gaps:
            lines.append(f"  {gap.ticker}: {gap.description}")

    # Unresolved Questions grouped by company
    if report.unknowns:
        lines += ["", _SEP, "Unresolved Questions"]
        standalone = [u for u in report.unknowns if not u.context]
        by_company: dict[str, list[str]] = {}
        for u in report.unknowns:
            if u.context:
                by_company.setdefault(u.context, []).append(u.question)
        if standalone:
            lines.append("")
            for u in standalone:
                lines.append(f"  - {u.question}")
        for company, questions in by_company.items():
            lines += ["", f"  {company}"]
            for q in questions:
                lines.append(f"    - {q}")

    # Suggested Next Research Steps
    if report.next_research_steps:
        lines += ["", _SEP, "Suggested Next Research Steps", ""]
        for step in report.next_research_steps:
            lines.append(f"  - {step}")

    # Research Framing
    lines += [
        "",
        _SEP,
        "Research Framing",
        (
            "This is a deterministic daily brief for context and education. "
            "It is not a news feed, market prediction, investment recommendation, "
            "or personal financial advice."
        ),
    ]
    return "\n".join(lines)


def _priority_marker(priority: DailyBriefPriority) -> str:
    if priority == DailyBriefPriority.HIGH:
        return "[!] "
    if priority == DailyBriefPriority.MODERATE:
        return "[·] "
    return ""


def _render_included_context(report: DailyBriefReport) -> list[str]:
    items: list[str] = []
    company_section = next(
        (s for s in report.sections if s.title == "Company Analysis Context"), None
    )
    if company_section and company_section.items:
        tickers = ", ".join(item.title for item in company_section.items)
        items.append(f"  Companies:  {tickers}")
    research_section = next(
        (s for s in report.sections if s.title == "Research Context"), None
    )
    if research_section and research_section.items:
        items.append(f"  Research:   {len(research_section.items)} project(s)")
    if any(s.title == "Watchlist Context" for s in report.sections):
        items.append("  Watchlist:  available")
    discovery_section = next(
        (s for s in report.sections if s.title == "Discovery Context"), None
    )
    if discovery_section and discovery_section.items:
        items.append(f"  Discovery:  {len(discovery_section.items)} candidate(s)")
    if any(s.title == "Portfolio Context" for s in report.sections):
        items.append("  Portfolio:  available")
    return items


def _build_sections(data: DailyBriefInput) -> list[DailyBriefSection]:
    sections: list[DailyBriefSection] = []
    sections.append(_opening_section(data))
    portfolio_section = _portfolio_section(data)
    if portfolio_section.items:
        sections.append(portfolio_section)
    company_section = _company_section(data)
    if company_section.items:
        sections.append(company_section)
    research_section = _research_section(data)
    if research_section.items:
        sections.append(research_section)
    watchlist_section = _watchlist_section(data)
    if watchlist_section.items:
        sections.append(watchlist_section)
    discovery_section = _discovery_section(data)
    if discovery_section.items:
        sections.append(discovery_section)
    return sections


def _opening_section(data: DailyBriefInput) -> DailyBriefSection:
    items: list[DailyBriefItem] = []
    if data.open_research_questions:
        items.append(
            DailyBriefItem(
                title="Open research questions",
                detail=f"{len(data.open_research_questions)} question(s) remain unresolved.",
                priority=DailyBriefPriority.MODERATE,
            )
        )
    if data.knowledge_node_count > 0:
        items.append(
            DailyBriefItem(
                title="Knowledge context",
                detail=f"{data.knowledge_node_count} knowledge node(s) available for review.",
                priority=DailyBriefPriority.LOW,
            )
        )
    if data.portfolio_summary is not None:
        concentration = getattr(data.portfolio_summary, "concentration", None)
        if concentration is not None:
            level = getattr(concentration, "level", None)
            if level is not None and level.value in {"High", "Elevated"}:
                items.append(
                    DailyBriefItem(
                        title="Portfolio concentration",
                        detail=f"Concentration appears {level.value.lower()}. This deserves review.",
                        priority=DailyBriefPriority.HIGH,
                    )
                )
    if data.company_reports:
        items.append(_company_analysis_opening_item(data.company_reports))
    if data.discovery_report is not None:
        candidates = getattr(data.discovery_report, "candidates", ())
        if candidates:
            items.append(
                DailyBriefItem(
                    title="Discovery candidates",
                    detail=f"{len(candidates)} candidate(s) identified for further research.",
                    priority=DailyBriefPriority.MODERATE,
                )
            )
    if not items:
        items.append(
            DailyBriefItem(
                title="Status",
                detail=_NO_DEVELOPMENTS_MESSAGE,
                priority=DailyBriefPriority.LOW,
            )
        )
    return DailyBriefSection(
        title="What Deserves Attention",
        items=tuple(items),
        narrative="Atlas organises available inputs into a calm daily overview.",
    )


def _company_analysis_opening_item(company_reports: tuple) -> DailyBriefItem:
    n = len(company_reports)
    companies_with_unknowns = sum(
        1 for r in company_reports if getattr(r, "unknowns", ())
    )
    if companies_with_unknowns > 0:
        if n == 1:
            detail = "Company analysis includes observations that deserve review."
        else:
            detail = (
                f"{companies_with_unknowns} of {n} company analysis report(s) "
                "include observations that deserve review."
            )
        return DailyBriefItem(
            title="Company analysis",
            detail=detail,
            priority=DailyBriefPriority.MODERATE,
        )
    if n == 1:
        detail = "Company analysis context is available for review."
    else:
        detail = f"{n} company analysis report(s) are available for review."
    return DailyBriefItem(
        title="Company analysis",
        detail=detail,
        priority=DailyBriefPriority.LOW,
    )


def _portfolio_section(data: DailyBriefInput) -> DailyBriefSection:
    if data.portfolio_summary is None:
        return DailyBriefSection(title="Portfolio Context", items=())

    summary = data.portfolio_summary
    items: list[DailyBriefItem] = []

    total_value = getattr(summary, "total_value", None)
    number_of_holdings = getattr(summary, "number_of_holdings", None)
    if number_of_holdings is not None:
        items.append(
            DailyBriefItem(
                title="Holdings",
                detail=f"{number_of_holdings} holding(s) in portfolio.",
                priority=DailyBriefPriority.LOW,
            )
        )

    concentration = getattr(summary, "concentration", None)
    if concentration is not None:
        level = getattr(concentration, "level", None)
        largest_weight = getattr(summary, "largest_weight", None)
        priority = DailyBriefPriority.HIGH if (
            level is not None and level.value in {"High", "Elevated"}
        ) else DailyBriefPriority.LOW
        detail = f"Concentration appears {level.value.lower()}." if level else "Concentration data available."
        if largest_weight is not None:
            detail += f" Largest position is {largest_weight:.1%} of portfolio."
        items.append(
            DailyBriefItem(
                title="Concentration",
                detail=detail,
                priority=priority,
            )
        )

    cash_weight = getattr(summary, "cash_weight", None)
    if cash_weight is not None and cash_weight > 0:
        items.append(
            DailyBriefItem(
                title="Cash weight",
                detail=f"Cash represents {cash_weight:.1%} of portfolio.",
                priority=DailyBriefPriority.LOW,
            )
        )

    return DailyBriefSection(
        title="Portfolio Context",
        items=tuple(items),
        narrative="Portfolio context is available for review.",
    )


def _research_section(data: DailyBriefInput) -> DailyBriefSection:
    notes = data.research_notes
    if not notes:
        return DailyBriefSection(title="Research Context", items=())

    items = tuple(
        DailyBriefItem(
            title=getattr(note, "title", getattr(note, "id", "Unknown")),
            detail=getattr(note, "body", getattr(note, "content", str(note)))[:200],
            priority=DailyBriefPriority.MODERATE,
        )
        for note in notes[:5]
    )
    return DailyBriefSection(
        title="Research Context",
        items=items,
        narrative="Research notes are available for review.",
    )


def _watchlist_section(data: DailyBriefInput) -> DailyBriefSection:
    report = data.watchlist_report
    if report is None:
        return DailyBriefSection(title="Watchlist Context", items=())

    items: list[DailyBriefItem] = []
    open_questions = getattr(report, "open_questions", ())
    if open_questions:
        items.append(
            DailyBriefItem(
                title="Open watchlist questions",
                detail=f"{len(open_questions)} open question(s) across watchlist.",
                priority=DailyBriefPriority.MODERATE,
            )
        )
    next_steps = getattr(
        report, "suggested_next_research_steps",
        getattr(report, "suggested_next_steps", ()),
    )
    if next_steps:
        items.append(
            DailyBriefItem(
                title="Suggested research steps",
                detail=f"{len(next_steps)} suggested next step(s) from watchlist review.",
                priority=DailyBriefPriority.LOW,
            )
        )
    return DailyBriefSection(
        title="Watchlist Context",
        items=tuple(items),
        narrative="Watchlist context is available for review.",
    )


def _discovery_candidate_detail(candidate: object) -> str:
    reasons = getattr(candidate, "reasons", ())
    if reasons:
        first = reasons[0]
        return getattr(first, "detail", getattr(first, "title", "Discovery candidate deserves research."))
    return getattr(candidate, "reason", "Discovery candidate deserves research.")


def _discovery_section(data: DailyBriefInput) -> DailyBriefSection:
    report = data.discovery_report
    if report is None:
        return DailyBriefSection(title="Discovery Context", items=())

    candidates = getattr(report, "candidates", ())
    if not candidates:
        return DailyBriefSection(title="Discovery Context", items=())

    items = tuple(
        DailyBriefItem(
            title=getattr(c, "identifier", getattr(c, "ticker", "Unknown")),
            detail=_discovery_candidate_detail(c),
            priority=DailyBriefPriority.MODERATE,
        )
        for c in candidates[:3]
    )
    return DailyBriefSection(
        title="Discovery Context",
        items=items,
        narrative="Discovery candidates are available for further research.",
    )


def _company_section(data: DailyBriefInput) -> DailyBriefSection:
    reports = data.company_reports
    if not reports:
        return DailyBriefSection(title="Company Analysis Context", items=())

    items: list[DailyBriefItem] = []
    for report in reports[:3]:
        unknowns = getattr(report, "unknowns", ())
        company = getattr(report, "company", None)
        ticker = getattr(company, "ticker", None) or getattr(report, "ticker", "Unknown")
        if unknowns:
            items.append(
                DailyBriefItem(
                    title=ticker,
                    detail=f"{len(unknowns)} open question(s) in company analysis.",
                    priority=DailyBriefPriority.MODERATE,
                )
            )
        else:
            items.append(
                DailyBriefItem(
                    title=ticker,
                    detail="Company analysis context is available for review.",
                    priority=DailyBriefPriority.LOW,
                )
            )
    return DailyBriefSection(
        title="Company Analysis Context",
        items=tuple(items),
        narrative="Company analysis context is available for review.",
    )


def _build_unknowns(data: DailyBriefInput) -> list[DailyBriefUnknown]:
    unknowns: list[DailyBriefUnknown] = []
    for question in data.open_research_questions:
        unknowns.append(DailyBriefUnknown(question=question))
    for report in data.company_reports:
        company = getattr(report, "company", None)
        ticker = getattr(company, "ticker", None) or getattr(report, "ticker", "Unknown")
        for unknown in getattr(report, "unknowns", ()):
            question = (
                getattr(unknown, "question", None)
                or getattr(unknown, "title", None)
                or str(unknown)
            )
            unknowns.append(DailyBriefUnknown(question=question, context=ticker))
    return unknowns[:10]


def _build_evidence_gaps(data: DailyBriefInput) -> list[DailyBriefEvidenceLink]:
    """Build Evidence Gaps from company analysis unknowns that signal missing evidence.

    evidence_links on a company report represent facts the engine *confirmed* as
    supporting evidence — they are linked, not gaps. Only unknowns that indicate
    unresolved or absent evidence support are surfaced here, scoped per company
    so that AMD gaps never appear under NVDA and vice versa.
    """
    gaps: list[DailyBriefEvidenceLink] = []
    for report in data.company_reports:
        company = getattr(report, "company", None)
        ticker = getattr(company, "ticker", None) or getattr(report, "ticker", "Unknown")
        for unknown in getattr(report, "unknowns", ()):
            title = getattr(unknown, "title", None) or str(unknown)
            detail = getattr(unknown, "detail", "") or ""
            if _is_evidence_gap_unknown(title):
                desc = detail.strip() or title
                gaps.append(DailyBriefEvidenceLink(ticker=ticker, description=desc))
    return gaps[:10]


def _is_evidence_gap_unknown(title: str) -> bool:
    """True when an unknown title signals missing or unresolved evidence support.

    Matches "Missing Evidence" and similar but excludes metadata gaps such as
    "Missing Sector" or "Missing Country" which are not evidence-support issues.
    """
    t = title.lower()
    return "evidence" in t


def _build_next_steps(data: DailyBriefInput) -> list[str]:
    steps: list[str] = []
    if data.open_research_questions:
        steps.append(
            f"Continue research on {len(data.open_research_questions)} open question(s)."
        )
    if data.discovery_report is not None:
        candidates = getattr(data.discovery_report, "candidates", ())
        if candidates:
            steps.append("Review discovery candidates for further research eligibility.")
    if data.watchlist_report is not None:
        next_watchlist = getattr(
            data.watchlist_report, "suggested_next_research_steps",
            getattr(data.watchlist_report, "suggested_next_steps", ()),
        )
        steps.extend(str(s) for s in next_watchlist[:2])
    if not steps:
        steps.append("No research actions identified from available inputs.")
    return steps[:5]


def _has_meaningful_input(data: DailyBriefInput) -> bool:
    return bool(
        data.portfolio_summary is not None
        or data.research_notes
        or data.company_reports
        or data.watchlist_report is not None
        or data.discovery_report is not None
        or data.knowledge_node_count > 0
        or data.open_research_questions
    )


def _overall_priority(high_count: int, moderate_count: int) -> DailyBriefPriority:
    if high_count > 0:
        return DailyBriefPriority.HIGH
    if moderate_count > 0:
        return DailyBriefPriority.MODERATE
    return DailyBriefPriority.LOW


def _bottom_line(
    has_developments: bool,
    high_priority_count: int,
    data: DailyBriefInput,
) -> str:
    if not has_developments:
        return _NO_DEVELOPMENTS_MESSAGE
    parts: list[str] = []
    if data.open_research_questions:
        parts.append(
            f"{len(data.open_research_questions)} research question(s) remain unresolved."
        )
    if data.portfolio_summary is not None:
        concentration = getattr(data.portfolio_summary, "concentration", None)
        if concentration is not None:
            level = getattr(concentration, "level", None)
            if level is not None and level.value in {"High", "Elevated"}:
                parts.append("Portfolio concentration deserves review.")
    if data.company_reports:
        parts.append(
            f"{len(data.company_reports)} company analysis report(s) available for review."
        )
    if data.watchlist_report is not None:
        parts.append("Watchlist context is available for review.")
    if data.discovery_report is not None:
        candidates = getattr(data.discovery_report, "candidates", ())
        if candidates:
            parts.append(f"{len(candidates)} discovery candidate(s) identified.")
    if not parts:
        return "Available inputs have been organised. No urgent items identified."
    return " ".join(parts)
