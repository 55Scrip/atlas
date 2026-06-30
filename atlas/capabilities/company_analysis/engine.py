from atlas.capabilities.company_analysis.models import (
    CompanyAnalysisConfidence,
    CompanyAnalysisEvidenceLink,
    CompanyAnalysisInput,
    CompanyAnalysisObservation,
    CompanyAnalysisReport,
    CompanyAnalysisRisk,
    CompanyAnalysisSection,
    CompanyAnalysisUnknown,
)
from atlas.domains.research import ResearchQuestionStatus, summarize_research


class CompanyAnalysisEngine:
    """Generate deterministic non-advisory company analysis reports."""

    def analyze(self, analysis_input: CompanyAnalysisInput) -> CompanyAnalysisReport:
        evidence_links = _evidence_links(analysis_input)
        unknowns = _unknowns(analysis_input)
        risks = _risks(analysis_input, evidence_links)
        confidence = _confidence(analysis_input, evidence_links, unknowns)
        sections = _sections(
            analysis_input=analysis_input,
            evidence_links=evidence_links,
            risks=risks,
            unknowns=unknowns,
            confidence=confidence,
        )
        return CompanyAnalysisReport(
            company=analysis_input.company,
            sections=sections,
            evidence_links=evidence_links,
            risks=risks,
            unknowns=unknowns,
            confidence=confidence,
            what_could_change_the_view=_what_could_change_the_view(unknowns, risks),
        )


def _evidence_links(
    analysis_input: CompanyAnalysisInput,
) -> tuple[CompanyAnalysisEvidenceLink, ...]:
    links: list[CompanyAnalysisEvidenceLink] = []
    for fact in sorted(analysis_input.knowledge_facts, key=lambda item: item.id):
        links.append(
            CompanyAnalysisEvidenceLink(
                id=f"knowledge:{fact.id}",
                source=fact.source.name,
                description=fact.statement,
                reference_id=fact.evidence_reference.id,
            )
        )
    if analysis_input.research_project is not None:
        for reference in sorted(
            analysis_input.research_project.evidence_references,
            key=lambda item: item.id,
        ):
            links.append(
                CompanyAnalysisEvidenceLink(
                    id=f"research:{reference.id}",
                    source=reference.source_id,
                    description=reference.description,
                    reference_id=reference.knowledge_fact_id,
                )
            )
    for evidence in sorted(analysis_input.decision_evidence, key=lambda item: item.id):
        links.append(
            CompanyAnalysisEvidenceLink(
                id=f"decision:{evidence.id}",
                source=evidence.source,
                description=evidence.statement,
            )
        )
    return tuple(links)


def _unknowns(analysis_input: CompanyAnalysisInput) -> tuple[CompanyAnalysisUnknown, ...]:
    unknowns: list[CompanyAnalysisUnknown] = []
    company = analysis_input.company
    if not company.sector:
        unknowns.append(
            CompanyAnalysisUnknown("Missing Sector", "Company sector is not available.")
        )
    if not company.country:
        unknowns.append(
            CompanyAnalysisUnknown("Missing Country", "Company country is not available.")
        )
    if not analysis_input.business_description.strip():
        unknowns.append(
            CompanyAnalysisUnknown(
                "Missing Business Description",
                "Business description is not available.",
            )
        )
    if not analysis_input.knowledge_facts and not analysis_input.decision_evidence:
        unknowns.append(
            CompanyAnalysisUnknown(
                "Missing Evidence",
                "No knowledge facts or decision evidence were supplied.",
            )
        )
    if analysis_input.research_project is not None:
        for question in sorted(analysis_input.research_project.questions, key=lambda item: item.id):
            if question.status in {
                ResearchQuestionStatus.OPEN,
                ResearchQuestionStatus.RESEARCHING,
            }:
                unknowns.append(
                    CompanyAnalysisUnknown(
                        title="Open Research Question",
                        detail=question.question,
                        evidence_links=tuple(
                            CompanyAnalysisEvidenceLink(
                                id=f"research-question:{question.id}:{reference_id}",
                                source="Research",
                                description=f"Question evidence reference {reference_id}",
                                reference_id=reference_id,
                            )
                            for reference_id in question.evidence_reference_ids
                        ),
                    )
                )
        for fragment in sorted(
            analysis_input.research_project.thesis_fragments,
            key=lambda item: item.id,
        ):
            if not fragment.supporting_evidence_reference_ids:
                unknowns.append(
                    CompanyAnalysisUnknown(
                        "Unsupported Thesis Fragment",
                        f"Thesis fragment {fragment.id} has no supporting evidence reference.",
                    )
                )
    return tuple(unknowns)


def _risks(
    analysis_input: CompanyAnalysisInput,
    evidence_links: tuple[CompanyAnalysisEvidenceLink, ...],
) -> tuple[CompanyAnalysisRisk, ...]:
    risks: list[CompanyAnalysisRisk] = []
    for fact in sorted(analysis_input.knowledge_facts, key=lambda item: item.id):
        if _contains_risk_language(fact.statement):
            risks.append(
                CompanyAnalysisRisk(
                    title="Knowledge Risk",
                    detail=fact.statement,
                    evidence_links=tuple(
                        link for link in evidence_links if link.id == f"knowledge:{fact.id}"
                    ),
                )
            )
    for evidence in sorted(analysis_input.decision_evidence, key=lambda item: item.id):
        if _contains_risk_language(evidence.statement):
            risks.append(
                CompanyAnalysisRisk(
                    title="Decision Context Risk",
                    detail=evidence.statement,
                    evidence_links=tuple(
                        link for link in evidence_links if link.id == f"decision:{evidence.id}"
                    ),
                )
            )
    return tuple(risks)


def _confidence(
    analysis_input: CompanyAnalysisInput,
    evidence_links: tuple[CompanyAnalysisEvidenceLink, ...],
    unknowns: tuple[CompanyAnalysisUnknown, ...],
) -> CompanyAnalysisConfidence:
    information_points = sum(
        1
        for value in (
            analysis_input.company.name,
            analysis_input.company.ticker,
            analysis_input.company.sector,
            analysis_input.company.country,
            analysis_input.business_description,
        )
        if value.strip()
    )
    evidence_points = min(len(evidence_links), 5)
    unresolved_questions = sum(
        1
        for unknown in unknowns
        if unknown.title in {"Open Research Question", "Unsupported Thesis Fragment"}
    )
    missing_core = sum(
        1
        for unknown in unknowns
        if unknown.title
        in {"Missing Sector", "Missing Country", "Missing Business Description", "Missing Evidence"}
    )
    raw_score = information_points * 10 + evidence_points * 8 - unresolved_questions * 8 - missing_core * 10
    if raw_score >= 70:
        level = "high"
    elif raw_score >= 40:
        level = "moderate"
    else:
        level = "low"
    drivers = (
        f"{information_points} core company field(s) available",
        f"{len(evidence_links)} evidence link(s) available",
    )
    limitations = tuple(unknown.detail for unknown in unknowns)
    return CompanyAnalysisConfidence(
        level=level,
        explanation=(
            f"Confidence is {level} because Atlas has {information_points} core "
            f"company field(s), {len(evidence_links)} evidence link(s), and "
            f"{len(unknowns)} unknown(s)."
        ),
        drivers=drivers,
        limitations=limitations,
    )


def _sections(
    analysis_input: CompanyAnalysisInput,
    evidence_links: tuple[CompanyAnalysisEvidenceLink, ...],
    risks: tuple[CompanyAnalysisRisk, ...],
    unknowns: tuple[CompanyAnalysisUnknown, ...],
    confidence: CompanyAnalysisConfidence,
) -> tuple[CompanyAnalysisSection, ...]:
    company = analysis_input.company
    knowledge_observations = tuple(
        CompanyAnalysisObservation(
            title="Knowledge Fact",
            detail=fact.statement,
            evidence_links=tuple(
                link for link in evidence_links if link.id == f"knowledge:{fact.id}"
            ),
        )
        for fact in sorted(analysis_input.knowledge_facts, key=lambda item: item.id)
    )
    research_observations = _research_observations(analysis_input, evidence_links)
    decision_observations = tuple(
        CompanyAnalysisObservation(
            title="Decision Evidence",
            detail=evidence.statement,
            evidence_links=tuple(
                link for link in evidence_links if link.id == f"decision:{evidence.id}"
            ),
        )
        for evidence in sorted(analysis_input.decision_evidence, key=lambda item: item.id)
    )
    return (
        CompanyAnalysisSection(
            title="Business Overview",
            observations=(
                CompanyAnalysisObservation(
                    "Company",
                    f"{company.name or company.ticker} ({company.ticker})",
                ),
                CompanyAnalysisObservation(
                    "Business Description",
                    analysis_input.business_description
                    or "Business description is not available.",
                ),
            ),
            narrative="Atlas starts with what is known about the business.",
        ),
        CompanyAnalysisSection(
            title="What Matters",
            observations=tuple(
                observation
                for observation in (
                    CompanyAnalysisObservation("Sector", company.sector)
                    if company.sector
                    else None,
                    CompanyAnalysisObservation("Industry", company.industry)
                    if company.industry
                    else None,
                    CompanyAnalysisObservation("Country", company.country)
                    if company.country
                    else None,
                )
                if observation is not None
            ),
            narrative="This section highlights basic context that frames further research.",
        ),
        CompanyAnalysisSection(
            title="Supporting Evidence",
            observations=knowledge_observations + decision_observations,
            narrative="Evidence is preserved as structured links rather than generated prose.",
        ),
        CompanyAnalysisSection(
            title="Key Risks",
            risks=risks,
            narrative="Risks are surfaced when supplied evidence explicitly mentions risk-sensitive context.",
        ),
        CompanyAnalysisSection(
            title="Open Questions",
            unknowns=tuple(
                unknown for unknown in unknowns if unknown.title == "Open Research Question"
            ),
            narrative="Open questions show where understanding remains incomplete.",
        ),
        CompanyAnalysisSection(
            title="Research Context",
            observations=research_observations,
            narrative="Research context is included when a research project is supplied.",
        ),
        CompanyAnalysisSection(
            title="Knowledge Context",
            observations=knowledge_observations,
            narrative="Knowledge context comes from attributed facts.",
        ),
        CompanyAnalysisSection(
            title="Decision Context",
            observations=decision_observations,
            narrative="Decision context is included as evidence, not as an action.",
        ),
        CompanyAnalysisSection(
            title="Confidence",
            observations=(
                CompanyAnalysisObservation("Confidence", confidence.explanation),
            ),
            unknowns=unknowns,
            narrative="Confidence is categorical and tied to evidence completeness.",
        ),
        CompanyAnalysisSection(
            title="What Could Change the View",
            observations=tuple(
                CompanyAnalysisObservation("Change Factor", item)
                for item in _what_could_change_the_view(unknowns, risks)
            ),
            narrative="Atlas changes its view when evidence changes.",
        ),
    )


def _research_observations(
    analysis_input: CompanyAnalysisInput,
    evidence_links: tuple[CompanyAnalysisEvidenceLink, ...],
) -> tuple[CompanyAnalysisObservation, ...]:
    if analysis_input.research_project is None:
        return ()
    project = analysis_input.research_project
    summary = summarize_research(project)
    observations: list[CompanyAnalysisObservation] = [
        CompanyAnalysisObservation(
            "Research Status",
            summary.overall_research_status.value,
        ),
        CompanyAnalysisObservation(
            "Thesis Maturity",
            summary.thesis_maturity,
        ),
    ]
    for fragment in sorted(project.thesis_fragments, key=lambda item: item.id):
        observations.append(
            CompanyAnalysisObservation(
                "Thesis Fragment",
                fragment.claim,
                evidence_links=tuple(
                    link
                    for link in evidence_links
                    if link.reference_id in fragment.supporting_evidence_reference_ids
                    or link.id.removeprefix("research:") in fragment.supporting_evidence_reference_ids
                ),
            )
        )
    return tuple(observations)


def _what_could_change_the_view(
    unknowns: tuple[CompanyAnalysisUnknown, ...],
    risks: tuple[CompanyAnalysisRisk, ...],
) -> tuple[str, ...]:
    factors = [
        f"Resolve: {unknown.detail}"
        for unknown in unknowns[:5]
    ]
    factors.extend(f"Reassess risk: {risk.detail}" for risk in risks[:3])
    if not factors:
        factors.append("New evidence that materially changes the business context.")
    return tuple(factors)


def _contains_risk_language(statement: str) -> bool:
    normalized = statement.lower()
    return any(
        token in normalized
        for token in ("risk", "concentration", "uncertain", "dependency", "margin pressure")
    )
