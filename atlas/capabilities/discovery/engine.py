from collections import defaultdict

from atlas.capabilities.company_analysis import CompanyAnalysisReport
from atlas.capabilities.discovery.models import (
    DiscoveryCandidate,
    DiscoveryContext,
    DiscoveryEvidenceLink,
    DiscoveryInput,
    DiscoveryPriority,
    DiscoveryQuestion,
    DiscoveryReason,
    DiscoveryReport,
    DiscoverySignal,
    DiscoveryUnknown,
)
from atlas.capabilities.watchlist_intelligence import WatchlistIntelligenceReport
from atlas.domains.knowledge import KnowledgeFact
from atlas.domains.research import ResearchProject, ResearchQuestionStatus, summarize_research


class DiscoveryEngine:
    """Generate deterministic non-advisory discovery candidates."""

    def discover(self, discovery_input: DiscoveryInput) -> DiscoveryReport:
        candidates = _merge_candidates(
            _candidates_from_knowledge(discovery_input.knowledge_facts)
            + _candidates_from_research(discovery_input.research_projects)
            + _candidates_from_company_analysis(discovery_input.company_analysis_reports)
            + _candidates_from_watchlist(discovery_input.watchlist_intelligence_reports)
            + _candidates_from_themes(discovery_input.themes)
        )
        evidence_links = tuple(
            link
            for candidate in candidates
            for link in candidate.supporting_evidence_links
        )
        unknowns = tuple(unknown for candidate in candidates for unknown in candidate.unknowns)
        return DiscoveryReport(
            summary=f"Discovery found {len(candidates)} candidate(s) for further research.",
            candidates=candidates,
            evidence_links=evidence_links,
            unknowns=unknowns,
        )


def _candidates_from_knowledge(
    facts: tuple[KnowledgeFact, ...],
) -> tuple[DiscoveryCandidate, ...]:
    candidates: list[DiscoveryCandidate] = []
    grouped: dict[str, list[KnowledgeFact]] = defaultdict(list)
    for fact in facts:
        grouped[fact.subject_node_id].append(fact)
    for subject_id in sorted(grouped):
        subject_facts = tuple(sorted(grouped[subject_id], key=lambda fact: fact.id))
        links = tuple(_knowledge_link(fact) for fact in subject_facts)
        reasons = (
            DiscoveryReason(
                "Knowledge Fact",
                f"{len(subject_facts)} attributed knowledge fact(s) are available.",
                links,
            ),
        )
        signals = (
            DiscoverySignal(
                "Knowledge Coverage",
                f"{len(subject_facts)} supporting fact(s).",
                min(len(subject_facts) * 12, 36),
                links,
            ),
        )
        candidates.append(
            _candidate(
                identifier=subject_id,
                title=_title_from_identifier(subject_id),
                reasons=reasons,
                evidence_links=links,
                related_knowledge_facts=subject_facts,
                questions=(),
                unknowns=(),
                signals=signals,
                context=DiscoveryContext(
                    related_knowledge_fact_ids=tuple(fact.id for fact in subject_facts)
                ),
            )
        )
    return tuple(candidates)


def _candidates_from_research(
    projects: tuple[ResearchProject, ...],
) -> tuple[DiscoveryCandidate, ...]:
    candidates: list[DiscoveryCandidate] = []
    for project in sorted(projects, key=lambda item: item.id):
        links = tuple(
            DiscoveryEvidenceLink(
                id=f"research:{project.id}:{reference.id}",
                source=reference.source_id,
                description=reference.description,
                reference_id=reference.knowledge_fact_id,
            )
            for reference in sorted(project.evidence_references, key=lambda item: item.id)
        )
        unresolved_questions = tuple(
            question
            for question in sorted(project.questions, key=lambda item: item.id)
            if question.status in {ResearchQuestionStatus.OPEN, ResearchQuestionStatus.RESEARCHING}
        )
        discovery_questions = tuple(
            DiscoveryQuestion(question.question, "Research Project", links)
            for question in unresolved_questions
        )
        summary = summarize_research(project)
        unknowns = tuple(
            DiscoveryUnknown("Unresolved Research Question", question.question, links)
            for question in unresolved_questions
        ) + tuple(
            DiscoveryUnknown("Missing Thesis Evidence", warning, links)
            for warning in summary.missing_evidence_warnings
        )
        signals = (
            DiscoverySignal(
                "Research Link",
                f"Research project {project.id} is linked.",
                16,
                links,
            ),
            DiscoverySignal(
                "Open Questions",
                f"{len(unresolved_questions)} unresolved question(s).",
                len(unresolved_questions) * 10,
                links,
            ),
        )
        candidates.append(
            _candidate(
                identifier=project.topic or project.id,
                title=project.title,
                reasons=(
                    DiscoveryReason(
                        "Research Project",
                        f"Research status is {summary.overall_research_status.value}.",
                        links,
                    ),
                ),
                evidence_links=links,
                related_knowledge_facts=(),
                questions=discovery_questions,
                unknowns=unknowns,
                signals=signals,
                context=DiscoveryContext(related_research_project_ids=(project.id,)),
            )
        )
    return tuple(candidates)


def _candidates_from_company_analysis(
    reports: tuple[CompanyAnalysisReport, ...],
) -> tuple[DiscoveryCandidate, ...]:
    candidates: list[DiscoveryCandidate] = []
    for report in sorted(reports, key=lambda item: item.company.ticker):
        links = tuple(
            DiscoveryEvidenceLink(
                id=f"company-analysis:{report.company.ticker}:{link.id}",
                source=link.source,
                description=link.description,
                reference_id=link.reference_id,
            )
            for link in sorted(report.evidence_links, key=lambda item: item.id)
        )
        unknowns = tuple(
            DiscoveryUnknown(unknown.title, unknown.detail, links)
            for unknown in sorted(report.unknowns, key=lambda item: (item.title, item.detail))
        )
        questions = _questions_from_unknowns(unknowns)
        signals = (
            DiscoverySignal(
                "Company Analysis",
                f"Company analysis confidence is {report.confidence.level}.",
                _confidence_signal(report.confidence.level),
                links,
            ),
        )
        candidates.append(
            _candidate(
                identifier=report.company.ticker or report.company.id,
                title=report.company.name or report.company.ticker,
                reasons=(
                    DiscoveryReason(
                        "Company Analysis Context",
                        report.confidence.explanation,
                        links,
                    ),
                ),
                evidence_links=links,
                related_knowledge_facts=(),
                questions=questions,
                unknowns=unknowns,
                signals=signals,
                context=DiscoveryContext(related_company_analysis_ticker=report.company.ticker),
            )
        )
    return tuple(candidates)


def _candidates_from_watchlist(
    reports: tuple[WatchlistIntelligenceReport, ...],
) -> tuple[DiscoveryCandidate, ...]:
    candidates: list[DiscoveryCandidate] = []
    for report in reports:
        for observation in sorted(report.observations, key=lambda item: item.ticker):
            links = tuple(
                DiscoveryEvidenceLink(
                    id=f"watchlist:{observation.ticker}:{signal.title}",
                    source="Watchlist Intelligence",
                    description=signal.detail,
                )
                for signal in observation.signals
            )
            unknowns = tuple(
                DiscoveryUnknown(unknown.title, unknown.detail, tuple(_from_watchlist_links(unknown.evidence_links)))
                for unknown in observation.unknowns
            )
            questions = tuple(
                DiscoveryQuestion(question.question, "Watchlist Intelligence", tuple(_from_watchlist_links(question.evidence_links)))
                for question in report.open_questions
                if question.id.startswith(f"{observation.ticker}:")
            ) + _questions_from_unknowns(unknowns)
            candidates.append(
                _candidate(
                    identifier=observation.ticker,
                    title=observation.title,
                    reasons=(
                        DiscoveryReason(
                            "Watchlist Signal",
                            observation.detail,
                            links,
                        ),
                    ),
                    evidence_links=links,
                    related_knowledge_facts=(),
                    questions=questions,
                    unknowns=unknowns,
                    signals=tuple(
                        DiscoverySignal(signal.title, signal.detail, signal.score, links)
                        for signal in observation.signals
                    ),
                    context=DiscoveryContext(related_watchlist_status=observation.priority.value),
                )
            )
    return tuple(candidates)


def _candidates_from_themes(themes: tuple[str, ...]) -> tuple[DiscoveryCandidate, ...]:
    return tuple(
        _candidate(
            identifier=f"theme:{theme.lower().replace(' ', '-')}",
            title=theme,
            reasons=(
                DiscoveryReason(
                    "Theme",
                    f"{theme} was supplied as a theme for further research.",
                ),
            ),
            evidence_links=(),
            related_knowledge_facts=(),
            questions=(
                DiscoveryQuestion(
                    f"How does {theme} relate to existing Atlas knowledge?",
                    "Theme",
                ),
            ),
            unknowns=(
                DiscoveryUnknown(
                    "Theme Evidence Needed",
                    f"{theme} needs supporting knowledge facts before deeper analysis.",
                ),
            ),
            signals=(DiscoverySignal("Theme Input", "Theme supplied for research.", 8),),
            context=DiscoveryContext(),
        )
        for theme in sorted(dict.fromkeys(themes))
    )


def _merge_candidates(
    candidates: tuple[DiscoveryCandidate, ...],
) -> tuple[DiscoveryCandidate, ...]:
    grouped: dict[str, list[DiscoveryCandidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.identifier].append(candidate)

    merged: list[DiscoveryCandidate] = []
    for identifier in sorted(grouped):
        group = grouped[identifier]
        reasons = tuple(
            sorted(
                _unique_tuple(reason for candidate in group for reason in candidate.reasons),
                key=lambda reason: (reason.title, reason.detail),
            )
        )
        evidence_links = _unique_tuple(
            link for candidate in group for link in candidate.supporting_evidence_links
        )
        knowledge_facts = _unique_by_id(
            fact for candidate in group for fact in candidate.related_knowledge_facts
        )
        questions = _unique_tuple(
            question
            for candidate in group
            for question in candidate.related_research_questions
        )
        unknowns = _unique_tuple(
            unknown for candidate in group for unknown in candidate.unknowns
        )
        signals = tuple(
            DiscoverySignal(reason.title, reason.detail, 8, reason.evidence_links)
            for reason in reasons
        )
        priority = _priority(evidence_links, questions, unknowns, signals)
        confidence = _confidence(evidence_links, unknowns)
        first = sorted(group, key=lambda candidate: candidate.title)[0]
        merged.append(
            DiscoveryCandidate(
                identifier=identifier,
                title=first.title,
                reasons=reasons,
                supporting_evidence_links=evidence_links,
                related_knowledge_facts=knowledge_facts,
                related_research_questions=questions,
                related_watchlist_status=next(
                    (
                        candidate.related_watchlist_status
                        for candidate in group
                        if candidate.related_watchlist_status is not None
                    ),
                    None,
                ),
                unknowns=unknowns,
                suggested_next_research_questions=questions or _questions_from_unknowns(unknowns),
                priority=priority,
                confidence=confidence,
                context=_merge_context(group),
            )
        )
    return tuple(merged)


def _candidate(
    identifier: str,
    title: str,
    reasons: tuple[DiscoveryReason, ...],
    evidence_links: tuple[DiscoveryEvidenceLink, ...],
    related_knowledge_facts: tuple[KnowledgeFact, ...],
    questions: tuple[DiscoveryQuestion, ...],
    unknowns: tuple[DiscoveryUnknown, ...],
    signals: tuple[DiscoverySignal, ...],
    context: DiscoveryContext,
) -> DiscoveryCandidate:
    return DiscoveryCandidate(
        identifier=identifier,
        title=title,
        reasons=reasons,
        supporting_evidence_links=evidence_links,
        related_knowledge_facts=related_knowledge_facts,
        related_research_questions=questions,
        related_watchlist_status=context.related_watchlist_status,
        unknowns=unknowns,
        suggested_next_research_questions=questions or _questions_from_unknowns(unknowns),
        priority=_priority(evidence_links, questions, unknowns, signals),
        confidence=_confidence(evidence_links, unknowns),
        context=context,
    )


def _priority(
    evidence_links: tuple[DiscoveryEvidenceLink, ...],
    questions: tuple[DiscoveryQuestion, ...],
    unknowns: tuple[DiscoveryUnknown, ...],
    signals: tuple[DiscoverySignal, ...],
) -> DiscoveryPriority:
    score = min(len(evidence_links) * 8, 32) + min(len(questions) * 10, 30)
    score += sum(signal.score for signal in signals)
    score -= min(len(unknowns) * 4, 24)
    if score >= 52:
        return DiscoveryPriority.HIGH
    if score >= 24:
        return DiscoveryPriority.MODERATE
    return DiscoveryPriority.LOW


def _confidence(
    evidence_links: tuple[DiscoveryEvidenceLink, ...],
    unknowns: tuple[DiscoveryUnknown, ...],
) -> str:
    if len(evidence_links) >= 3 and len(unknowns) <= 2:
        return "high"
    if evidence_links:
        return "moderate"
    return "low"


def _questions_from_unknowns(
    unknowns: tuple[DiscoveryUnknown, ...],
) -> tuple[DiscoveryQuestion, ...]:
    questions: list[DiscoveryQuestion] = []
    for unknown in unknowns:
        if unknown.title in {"Missing Company Context", "No Linked Research Project"}:
            question = "How does this company relate to existing watchlist themes?"
        elif "evidence" in unknown.title.lower():
            question = "What evidence supports the business quality thesis?"
        elif "confidence" in unknown.title.lower():
            question = "What risks remain insufficiently researched?"
        else:
            question = f"What would resolve: {unknown.detail}"
        questions.append(
            DiscoveryQuestion(
                question=question,
                source=unknown.title,
                evidence_links=unknown.evidence_links,
            )
        )
    return tuple(_unique_tuple(questions))


def _knowledge_link(fact: KnowledgeFact) -> DiscoveryEvidenceLink:
    return DiscoveryEvidenceLink(
        id=f"knowledge:{fact.id}",
        source=fact.source.name,
        description=fact.statement,
        reference_id=fact.evidence_reference.id,
    )


def _from_watchlist_links(links) -> tuple[DiscoveryEvidenceLink, ...]:
    return tuple(
        DiscoveryEvidenceLink(
            id=f"watchlist-link:{link.id}",
            source=link.source,
            description=link.description,
            reference_id=link.reference_id,
        )
        for link in links
    )


def _merge_context(candidates: list[DiscoveryCandidate]) -> DiscoveryContext:
    return DiscoveryContext(
        related_knowledge_fact_ids=tuple(
            sorted(
                {
                    fact_id
                    for candidate in candidates
                    for fact_id in candidate.context.related_knowledge_fact_ids
                }
            )
        ),
        related_research_project_ids=tuple(
            sorted(
                {
                    project_id
                    for candidate in candidates
                    for project_id in candidate.context.related_research_project_ids
                }
            )
        ),
        related_watchlist_status=next(
            (
                candidate.context.related_watchlist_status
                for candidate in candidates
                if candidate.context.related_watchlist_status is not None
            ),
            None,
        ),
        related_company_analysis_ticker=next(
            (
                candidate.context.related_company_analysis_ticker
                for candidate in candidates
                if candidate.context.related_company_analysis_ticker is not None
            ),
            None,
        ),
    )


def _confidence_signal(level: str) -> int:
    return {"high": 24, "moderate": 14, "low": 4}.get(level, 0)


def _title_from_identifier(identifier: str) -> str:
    return identifier.removeprefix("company-").replace("-", " ").upper()


def _unique_tuple(items) -> tuple:
    return tuple(dict.fromkeys(items))


def _unique_by_id(items) -> tuple:
    by_id = {item.id: item for item in items}
    return tuple(by_id[key] for key in sorted(by_id))
