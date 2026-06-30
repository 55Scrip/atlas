from atlas.capabilities.company_analysis import (
    CompanyAnalysisEngine,
    CompanyAnalysisInput,
    CompanyAnalysisReport,
)
from atlas.domains.decision import Evidence, EvidenceCategory, EvidenceStrength
from atlas.domains.knowledge import KnowledgeFact, KnowledgeReference, KnowledgeSource
from atlas.domains.research import (
    ResearchAssumption,
    ResearchEvidenceReference,
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
    ThesisFragment,
)
from atlas.shared import Company, ResearchNote


def _company() -> Company:
    return Company(
        id="company-nvda",
        name="NVIDIA",
        ticker="NVDA",
        sector="Semiconductors",
        industry="Accelerated Computing",
        country="United States",
    )


def _knowledge_fact(fact_id: str = "fact-1", statement: str | None = None) -> KnowledgeFact:
    return KnowledgeFact(
        id=fact_id,
        subject_node_id="company-nvda",
        statement=statement or "NVIDIA reports data center revenue as a major business line.",
        source=KnowledgeSource(id="source-1", name="Company filing", source_type="Filing"),
        timestamp="2026-06-30T00:00:00Z",
        confidence=92,
        evidence_reference=KnowledgeReference(
            id="reference-1",
            source_id="source-1",
            citation="Annual report",
        ),
    )


def _research_project() -> ResearchProject:
    return ResearchProject(
        id="research-nvda",
        title="NVIDIA data center durability",
        topic="NVDA",
        status=ResearchStatus.THESIS_FORMING,
        notes=(
            ResearchNote(
                id="note-1",
                title="Initial note",
                body="Data center revenue deserves continued study.",
                created_at="2026-06-30T00:00:00Z",
                related_tickers=("NVDA",),
            ),
        ),
        questions=(
            ResearchQuestion(
                id="question-1",
                question="How durable is data center demand?",
                related_topic="NVDA",
                status=ResearchQuestionStatus.RESEARCHING,
                evidence_reference_ids=("research-evidence-1",),
            ),
        ),
        assumptions=(
            ResearchAssumption(
                id="assumption-1",
                statement="Hyperscaler spending remains important.",
                explanation="Customer capital spending can affect demand durability.",
                evidence_reference_ids=("research-evidence-1",),
            ),
        ),
        thesis_fragments=(
            ThesisFragment(
                id="thesis-1",
                claim="Data center demand is central to the current research thesis.",
                supporting_evidence_reference_ids=("research-evidence-1",),
                assumption_ids=("assumption-1",),
                confidence=70,
            ),
        ),
        evidence_references=(
            ResearchEvidenceReference(
                id="research-evidence-1",
                source_id="research-source",
                description="Research note linked to data center revenue.",
                knowledge_fact_id="fact-1",
            ),
        ),
    )


def _decision_evidence() -> tuple[Evidence, ...]:
    return (
        Evidence(
            id="decision-risk-1",
            category=EvidenceCategory.RISK,
            statement="Customer concentration risk remains worth understanding.",
            source="Decision domain",
            strength=EvidenceStrength.MODERATE,
        ),
    )


def test_company_analysis_generates_structured_report() -> None:
    report = CompanyAnalysisEngine().analyze(
        CompanyAnalysisInput(
            company=_company(),
            business_description="NVIDIA designs accelerated computing platforms.",
            knowledge_facts=(_knowledge_fact(),),
            research_project=_research_project(),
            decision_evidence=_decision_evidence(),
        )
    )

    section_titles = [section.title for section in report.sections]

    assert isinstance(report, CompanyAnalysisReport)
    assert report.company.ticker == "NVDA"
    assert section_titles == [
        "Business Overview",
        "What Matters",
        "Supporting Evidence",
        "Key Risks",
        "Open Questions",
        "Research Context",
        "Knowledge Context",
        "Decision Context",
        "Confidence",
        "What Could Change the View",
    ]
    assert report.evidence_links[0].id == "knowledge:fact-1"
    assert report.evidence_links[1].id == "research:research-evidence-1"
    assert report.evidence_links[2].id == "decision:decision-risk-1"


def test_company_analysis_is_deterministic() -> None:
    analysis_input = CompanyAnalysisInput(
        company=_company(),
        business_description="NVIDIA designs accelerated computing platforms.",
        knowledge_facts=(_knowledge_fact("fact-b"), _knowledge_fact("fact-a")),
        research_project=_research_project(),
    )
    engine = CompanyAnalysisEngine()

    first = engine.analyze(analysis_input)
    second = engine.analyze(analysis_input)

    assert first == second
    assert [link.id for link in first.evidence_links[:2]] == [
        "knowledge:fact-a",
        "knowledge:fact-b",
    ]


def test_empty_input_surfaces_unknowns_and_low_confidence() -> None:
    report = CompanyAnalysisEngine().analyze(
        CompanyAnalysisInput(company=Company(id="company-unknown", name="", ticker="UNK"))
    )

    unknown_titles = [unknown.title for unknown in report.unknowns]

    assert report.confidence.level == "low"
    assert "Missing Sector" in unknown_titles
    assert "Missing Country" in unknown_titles
    assert "Missing Business Description" in unknown_titles
    assert "Missing Evidence" in unknown_titles


def test_open_questions_and_unsupported_fragments_are_surfaced() -> None:
    research = ResearchProject(
        id="research-1",
        title="Research",
        topic="NVDA",
        questions=(
            ResearchQuestion(
                id="question-1",
                question="What is still unknown?",
                related_topic="NVDA",
                status=ResearchQuestionStatus.OPEN,
            ),
        ),
        thesis_fragments=(ThesisFragment(id="thesis-1", claim="Incomplete thesis"),),
    )

    report = CompanyAnalysisEngine().analyze(
        CompanyAnalysisInput(
            company=_company(),
            business_description="NVIDIA designs accelerated computing platforms.",
            research_project=research,
        )
    )

    assert [unknown.title for unknown in report.unknowns] == [
        "Missing Evidence",
        "Open Research Question",
        "Unsupported Thesis Fragment",
    ]
    assert any("What is still unknown?" in item for item in report.what_could_change_the_view)


def test_confidence_calculation_is_explainable() -> None:
    high_report = CompanyAnalysisEngine().analyze(
        CompanyAnalysisInput(
            company=_company(),
            business_description="NVIDIA designs accelerated computing platforms.",
            knowledge_facts=(
                _knowledge_fact("fact-1"),
                _knowledge_fact("fact-2"),
                _knowledge_fact("fact-3"),
            ),
            research_project=_research_project(),
            decision_evidence=_decision_evidence(),
        )
    )

    assert high_report.confidence.level == "high"
    assert "core company field" in high_report.confidence.explanation
    assert high_report.confidence.drivers == (
        "5 core company field(s) available",
        "5 evidence link(s) available",
    )
    assert high_report.confidence.limitations


def test_risks_are_detected_only_from_supplied_evidence() -> None:
    report = CompanyAnalysisEngine().analyze(
        CompanyAnalysisInput(
            company=_company(),
            business_description="NVIDIA designs accelerated computing platforms.",
            knowledge_facts=(
                _knowledge_fact("fact-risk", "Supplier dependency risk is material."),
            ),
            decision_evidence=_decision_evidence(),
        )
    )

    assert [risk.title for risk in report.risks] == [
        "Knowledge Risk",
        "Decision Context Risk",
    ]


def test_company_analysis_avoids_trade_recommendation_language() -> None:
    report = CompanyAnalysisEngine().analyze(
        CompanyAnalysisInput(
            company=_company(),
            business_description="NVIDIA designs accelerated computing platforms.",
            knowledge_facts=(_knowledge_fact(),),
            research_project=_research_project(),
        )
    )
    text = " ".join(
        [
            report.confidence.explanation,
            " ".join(section.narrative for section in report.sections),
            " ".join(observation.detail for section in report.sections for observation in section.observations),
            " ".join(unknown.detail for unknown in report.unknowns),
        ]
    ).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "strong buy" not in text
    assert "guaranteed" not in text
    assert "risk-free" not in text
    assert "prediction" not in text


def test_company_analysis_does_not_require_ai_or_external_api_usage() -> None:
    engine = CompanyAnalysisEngine()

    assert not hasattr(engine, "client")
    assert not hasattr(engine, "provider")
