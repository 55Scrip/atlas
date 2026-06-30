from atlas.capabilities.company_analysis import (
    CompanyAnalysisConfidence,
    CompanyAnalysisReport,
    CompanyAnalysisUnknown,
)
from atlas.capabilities.discovery import DiscoveryEngine, DiscoveryInput, DiscoveryPriority
from atlas.capabilities.watchlist_intelligence import (
    WatchlistIntelligenceReport,
    WatchlistObservation,
    WatchlistPriority,
    WatchlistSignal,
    WatchlistUnknown,
)
from atlas.domains.knowledge import KnowledgeFact, KnowledgeReference, KnowledgeSource
from atlas.domains.research import (
    ResearchEvidenceReference,
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
)
from atlas.shared import Company


def _company() -> Company:
    return Company(
        id="company-nvda",
        name="NVIDIA",
        ticker="NVDA",
        sector="Semiconductors",
        country="United States",
    )


def _knowledge_fact(fact_id: str = "fact-nvda") -> KnowledgeFact:
    return KnowledgeFact(
        id=fact_id,
        subject_node_id="company-nvda",
        statement="NVIDIA has data center exposure.",
        source=KnowledgeSource(id="source-1", name="Company filing", source_type="Filing"),
        timestamp="2026-06-30T00:00:00Z",
        confidence=90,
        evidence_reference=KnowledgeReference(
            id=f"reference-{fact_id}",
            source_id="source-1",
            citation="Annual report",
        ),
    )


def _research_project() -> ResearchProject:
    return ResearchProject(
        id="research-nvda",
        title="NVIDIA research",
        topic="NVDA",
        questions=(
            ResearchQuestion(
                id="question-1",
                question="What evidence supports the durability thesis?",
                related_topic="NVDA",
                status=ResearchQuestionStatus.RESEARCHING,
                evidence_reference_ids=("research-evidence-1",),
            ),
        ),
        evidence_references=(
            ResearchEvidenceReference(
                id="research-evidence-1",
                source_id="research-source",
                description="Research source on data center demand.",
                knowledge_fact_id="fact-nvda",
            ),
        ),
    )


def _company_analysis(confidence: str = "moderate") -> CompanyAnalysisReport:
    return CompanyAnalysisReport(
        company=_company(),
        sections=(),
        evidence_links=(),
        risks=(),
        unknowns=(
            CompanyAnalysisUnknown(
                title="Missing Evidence",
                detail="More evidence is needed.",
            ),
        ),
        confidence=CompanyAnalysisConfidence(
            level=confidence,
            explanation=f"Confidence is {confidence}.",
            drivers=("driver",),
            limitations=("limitation",),
        ),
        what_could_change_the_view=(),
    )


def _watchlist_report() -> WatchlistIntelligenceReport:
    observation = WatchlistObservation(
        ticker="NVDA",
        title="NVIDIA",
        detail="NVDA has unresolved questions.",
        priority=WatchlistPriority.HAS_QUESTIONS,
        signals=(
            WatchlistSignal(
                title="Unresolved Questions",
                detail="1 unresolved research question.",
                score=30,
            ),
        ),
        unknowns=(
            WatchlistUnknown(
                title="Unresolved Research Question",
                detail="What evidence supports the durability thesis?",
                ticker="NVDA",
            ),
        ),
    )
    return WatchlistIntelligenceReport(
        name="AI Watchlist",
        overview="AI Watchlist contains 1 item.",
        observations=(observation,),
        companies_needing_attention=(observation,),
        open_questions=(),
        evidence_gaps=(),
        unknowns=observation.unknowns,
        suggested_next_research_steps=("NVDA: resolve open research questions.",),
    )


def test_discovery_report_generation() -> None:
    report = DiscoveryEngine().discover(
        DiscoveryInput(
            knowledge_facts=(_knowledge_fact(),),
            research_projects=(_research_project(),),
            company_analysis_reports=(_company_analysis(),),
            watchlist_intelligence_reports=(_watchlist_report(),),
        )
    )

    assert report.summary == "Discovery found 2 candidate(s) for further research."
    assert [candidate.identifier for candidate in report.candidates] == ["NVDA", "company-nvda"]
    assert report.candidates[0].title == "NVIDIA"
    assert report.evidence_links
    assert report.unknowns


def test_duplicate_candidate_handling_merges_reasons() -> None:
    report = DiscoveryEngine().discover(
        DiscoveryInput(
            research_projects=(_research_project(),),
            company_analysis_reports=(_company_analysis("low"),),
            watchlist_intelligence_reports=(_watchlist_report(),),
        )
    )

    candidate = report.candidates[0]

    assert candidate.identifier == "NVDA"
    assert [reason.title for reason in candidate.reasons] == [
        "Company Analysis Context",
        "Research Project",
        "Watchlist Signal",
    ]
    assert candidate.context.related_research_project_ids == ("research-nvda",)
    assert candidate.context.related_company_analysis_ticker == "NVDA"
    assert candidate.related_watchlist_status == "has unresolved questions"


def test_evidence_links_are_preserved() -> None:
    report = DiscoveryEngine().discover(DiscoveryInput(knowledge_facts=(_knowledge_fact(),)))
    candidate = report.candidates[0]

    assert candidate.supporting_evidence_links[0].id == "knowledge:fact-nvda"
    assert candidate.supporting_evidence_links[0].source == "Company filing"
    assert candidate.supporting_evidence_links[0].reference_id == "reference-fact-nvda"


def test_unknown_detection_and_suggested_questions() -> None:
    report = DiscoveryEngine().discover(
        DiscoveryInput(company_analysis_reports=(_company_analysis("low"),))
    )
    candidate = report.candidates[0]

    assert candidate.unknowns[0].title == "Missing Evidence"
    assert candidate.suggested_next_research_questions[0].question == (
        "What evidence supports the business quality thesis?"
    )


def test_priority_and_confidence_are_explainable_categories() -> None:
    report = DiscoveryEngine().discover(
        DiscoveryInput(
            research_projects=(_research_project(),),
            company_analysis_reports=(_company_analysis("high"),),
            watchlist_intelligence_reports=(_watchlist_report(),),
        )
    )
    candidate = report.candidates[0]

    assert candidate.priority in set(DiscoveryPriority)
    assert candidate.priority == DiscoveryPriority.HIGH
    assert candidate.confidence in {"low", "moderate", "high"}


def test_empty_input_behavior() -> None:
    report = DiscoveryEngine().discover(DiscoveryInput())

    assert report.summary == "Discovery found 0 candidate(s) for further research."
    assert report.candidates == ()
    assert report.evidence_links == ()
    assert report.unknowns == ()


def test_theme_candidates_generate_research_questions() -> None:
    report = DiscoveryEngine().discover(DiscoveryInput(themes=("AI infrastructure",)))
    candidate = report.candidates[0]

    assert candidate.identifier == "theme:ai-infrastructure"
    assert candidate.priority == DiscoveryPriority.LOW
    assert candidate.suggested_next_research_questions[0].question == (
        "How does AI infrastructure relate to existing Atlas knowledge?"
    )


def test_discovery_avoids_trade_and_urgency_language() -> None:
    report = DiscoveryEngine().discover(
        DiscoveryInput(
            knowledge_facts=(_knowledge_fact(),),
            research_projects=(_research_project(),),
            watchlist_intelligence_reports=(_watchlist_report(),),
            themes=("AI infrastructure",),
        )
    )
    text = " ".join(
        [
            report.summary,
            " ".join(candidate.title for candidate in report.candidates),
            " ".join(reason.detail for candidate in report.candidates for reason in candidate.reasons),
            " ".join(question.question for candidate in report.candidates for question in candidate.suggested_next_research_questions),
        ]
    ).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "strong buy" not in text
    assert "guaranteed" not in text
    assert "risk-free" not in text
    assert "prediction" not in text
    assert "price target" not in text
    assert "urgent" not in text
    assert "must act" not in text


def test_discovery_does_not_require_ai_or_api_usage() -> None:
    engine = DiscoveryEngine()

    assert not hasattr(engine, "client")
    assert not hasattr(engine, "provider")
