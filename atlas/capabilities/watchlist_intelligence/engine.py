from atlas.capabilities.watchlist_intelligence.models import (
    WatchlistEvidenceLink,
    WatchlistIntelligenceInput,
    WatchlistIntelligenceReport,
    WatchlistItem,
    WatchlistObservation,
    WatchlistPriority,
    WatchlistQuestion,
    WatchlistSignal,
    WatchlistStatus,
    WatchlistUnknown,
)
from atlas.domains.research import ResearchQuestionStatus, summarize_research


class WatchlistIntelligenceEngine:
    """Generate deterministic non-advisory watchlist intelligence."""

    def analyze(self, watchlist_input: WatchlistIntelligenceInput) -> WatchlistIntelligenceReport:
        observations = tuple(
            _observation_for_item(item)
            for item in sorted(watchlist_input.items, key=lambda item: (item.ticker, item.id))
        )
        open_questions = tuple(
            question
            for observation in observations
            for question in _questions_from_observation(observation)
        )
        unknowns = tuple(unknown for observation in observations for unknown in observation.unknowns)
        evidence_gaps = tuple(
            unknown for unknown in unknowns if unknown.title in _EVIDENCE_GAP_TITLES
        )
        companies_needing_attention = tuple(
            observation
            for observation in observations
            if observation.priority
            in {
                WatchlistPriority.REVIEW,
                WatchlistPriority.NEEDS_EVIDENCE,
                WatchlistPriority.HAS_QUESTIONS,
                WatchlistPriority.INCOMPLETE,
            }
        )
        return WatchlistIntelligenceReport(
            name=watchlist_input.name,
            overview=_overview(watchlist_input, companies_needing_attention),
            observations=observations,
            companies_needing_attention=companies_needing_attention,
            open_questions=open_questions,
            evidence_gaps=evidence_gaps,
            unknowns=unknowns,
            suggested_next_research_steps=_research_steps(observations, evidence_gaps),
        )


_EVIDENCE_GAP_TITLES = {
    "No Linked Research Project",
    "No Supporting Knowledge Facts",
    "Thesis Fragment Needs Evidence",
    "Low Company Analysis Confidence",
}


def _observation_for_item(item: WatchlistItem) -> WatchlistObservation:
    evidence_links = _evidence_links(item)
    signals = _signals(item, evidence_links)
    unknowns = _unknowns(item, evidence_links)
    priority = _priority(item, signals, unknowns)
    return WatchlistObservation(
        ticker=item.ticker,
        title=item.name or item.ticker,
        detail=_detail(item, priority, signals),
        priority=priority,
        signals=signals,
        unknowns=unknowns,
    )


def _evidence_links(item: WatchlistItem) -> tuple[WatchlistEvidenceLink, ...]:
    links: list[WatchlistEvidenceLink] = []
    for fact in sorted(item.knowledge_facts, key=lambda fact: fact.id):
        links.append(
            WatchlistEvidenceLink(
                id=f"knowledge:{item.ticker}:{fact.id}",
                source=fact.source.name,
                description=fact.statement,
                reference_id=fact.evidence_reference.id,
            )
        )
    if item.research_project is not None:
        for reference in sorted(item.research_project.evidence_references, key=lambda ref: ref.id):
            links.append(
                WatchlistEvidenceLink(
                    id=f"research:{item.ticker}:{reference.id}",
                    source=reference.source_id,
                    description=reference.description,
                    reference_id=reference.knowledge_fact_id,
                )
            )
    if item.company_analysis is not None:
        for link in sorted(item.company_analysis.evidence_links, key=lambda link: link.id):
            links.append(
                WatchlistEvidenceLink(
                    id=f"company-analysis:{item.ticker}:{link.id}",
                    source=link.source,
                    description=link.description,
                    reference_id=link.reference_id,
                )
            )
    return tuple(links)


def _signals(
    item: WatchlistItem,
    evidence_links: tuple[WatchlistEvidenceLink, ...],
) -> tuple[WatchlistSignal, ...]:
    signals: list[WatchlistSignal] = []
    if item.research_project is not None:
        summary = summarize_research(item.research_project)
        if summary.number_of_open_questions:
            signals.append(
                WatchlistSignal(
                    "Unresolved Questions",
                    f"{summary.number_of_open_questions} unresolved research question(s).",
                    30,
                    evidence_links,
                )
            )
        if summary.missing_evidence_warnings:
            signals.append(
                WatchlistSignal(
                    "Missing Research Evidence",
                    f"{len(summary.missing_evidence_warnings)} thesis evidence gap(s).",
                    28,
                    evidence_links,
                )
            )
    if item.company_analysis is not None and item.company_analysis.confidence.level == "low":
        signals.append(
            WatchlistSignal(
                "Low Company Analysis Confidence",
                item.company_analysis.confidence.explanation,
                24,
                tuple(
                    link
                    for link in evidence_links
                    if link.id.startswith(f"company-analysis:{item.ticker}:")
                ),
            )
        )
    if item.manual_observations:
        signals.append(
            WatchlistSignal(
                "Manual Observation",
                item.manual_observations[-1],
                12,
            )
        )
    if item.status in {WatchlistStatus.PAUSED, WatchlistStatus.ARCHIVED}:
        signals.append(
            WatchlistSignal(
                "Inactive Status",
                f"Item status is {item.status.value}.",
                -20,
            )
        )
    return tuple(sorted(signals, key=lambda signal: (-signal.score, signal.title)))


def _unknowns(
    item: WatchlistItem,
    evidence_links: tuple[WatchlistEvidenceLink, ...],
) -> tuple[WatchlistUnknown, ...]:
    unknowns: list[WatchlistUnknown] = []
    if item.company is None:
        unknowns.append(
            WatchlistUnknown("Missing Company Context", "Company context is not linked.", item.ticker)
        )
    else:
        if not item.company.sector:
            unknowns.append(WatchlistUnknown("Missing Sector", "Company sector is not available.", item.ticker))
        if not item.company.country:
            unknowns.append(WatchlistUnknown("Missing Country", "Company country is not available.", item.ticker))
    if item.research_project is None:
        unknowns.append(
            WatchlistUnknown("No Linked Research Project", "No research project is linked.", item.ticker)
        )
    if not item.knowledge_facts:
        unknowns.append(
            WatchlistUnknown("No Supporting Knowledge Facts", "No knowledge facts are linked.", item.ticker)
        )
    if item.research_project is not None:
        for question in sorted(item.research_project.questions, key=lambda question: question.id):
            if question.status in {ResearchQuestionStatus.OPEN, ResearchQuestionStatus.RESEARCHING}:
                unknowns.append(
                    WatchlistUnknown(
                        "Unresolved Research Question",
                        question.question,
                        item.ticker,
                        tuple(
                            link
                            for link in evidence_links
                            if link.reference_id in question.evidence_reference_ids
                            or link.id.removeprefix(f"research:{item.ticker}:")
                            in question.evidence_reference_ids
                        ),
                    )
                )
        for fragment in sorted(item.research_project.thesis_fragments, key=lambda fragment: fragment.id):
            if not fragment.supporting_evidence_reference_ids:
                unknowns.append(
                    WatchlistUnknown(
                        "Thesis Fragment Needs Evidence",
                        f"Thesis fragment {fragment.id} has no supporting evidence reference.",
                        item.ticker,
                    )
                )
    if item.company_analysis is not None and item.company_analysis.confidence.level == "low":
        unknowns.append(
            WatchlistUnknown(
                "Low Company Analysis Confidence",
                item.company_analysis.confidence.explanation,
                item.ticker,
            )
        )
    return tuple(unknowns)


def _priority(
    item: WatchlistItem,
    signals: tuple[WatchlistSignal, ...],
    unknowns: tuple[WatchlistUnknown, ...],
) -> WatchlistPriority:
    if item.status == WatchlistStatus.ARCHIVED:
        return WatchlistPriority.ARCHIVED
    if item.status == WatchlistStatus.PAUSED:
        return WatchlistPriority.PAUSED
    unknown_titles = {unknown.title for unknown in unknowns}
    if "No Linked Research Project" in unknown_titles or "No Supporting Knowledge Facts" in unknown_titles:
        return WatchlistPriority.NEEDS_EVIDENCE
    if "Unresolved Research Question" in unknown_titles:
        return WatchlistPriority.HAS_QUESTIONS
    if "Thesis Fragment Needs Evidence" in unknown_titles or "Missing Company Context" in unknown_titles:
        return WatchlistPriority.INCOMPLETE
    score = sum(signal.score for signal in signals)
    if score >= 35 or item.status == WatchlistStatus.READY_FOR_REVIEW:
        return WatchlistPriority.REVIEW
    return WatchlistPriority.MONITOR


def _detail(
    item: WatchlistItem,
    priority: WatchlistPriority,
    signals: tuple[WatchlistSignal, ...],
) -> str:
    if priority in {WatchlistPriority.ARCHIVED, WatchlistPriority.PAUSED}:
        return f"{item.ticker} is {priority.value}."
    if signals:
        return f"{item.ticker} {priority.value} because {signals[0].detail}"
    return f"{item.ticker} can continue being observed."


def _questions_from_observation(
    observation: WatchlistObservation,
) -> tuple[WatchlistQuestion, ...]:
    return tuple(
        WatchlistQuestion(
            id=f"{observation.ticker}:{index}",
            question=unknown.detail,
            status="open",
            evidence_links=unknown.evidence_links,
        )
        for index, unknown in enumerate(observation.unknowns, start=1)
        if unknown.title == "Unresolved Research Question"
    )


def _overview(
    watchlist_input: WatchlistIntelligenceInput,
    companies_needing_attention: tuple[WatchlistObservation, ...],
) -> str:
    return (
        f"{watchlist_input.name} contains {len(watchlist_input.items)} item(s). "
        f"{len(companies_needing_attention)} item(s) deserve review or more evidence."
    )


def _research_steps(
    observations: tuple[WatchlistObservation, ...],
    evidence_gaps: tuple[WatchlistUnknown, ...],
) -> tuple[str, ...]:
    steps: list[str] = []
    for gap in evidence_gaps[:5]:
        steps.append(f"{gap.ticker}: {gap.detail}")
    for observation in observations:
        if observation.priority == WatchlistPriority.HAS_QUESTIONS:
            steps.append(f"{observation.ticker}: resolve open research questions.")
    if not steps:
        steps.append("Continue observing and update evidence when new facts are available.")
    return tuple(dict.fromkeys(steps))
