from atlas.capabilities.company_analysis import (
    CompanyAnalysisConfidence,
    CompanyAnalysisReport,
)
from atlas.capabilities.watchlist_intelligence import (
    WatchlistIntelligenceEngine,
    WatchlistIntelligenceInput,
    WatchlistItem,
    WatchlistPriority,
    WatchlistStatus,
)
from atlas.domains.knowledge import KnowledgeFact, KnowledgeReference, KnowledgeSource
from atlas.domains.research import (
    ResearchEvidenceReference,
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
    ThesisFragment,
)
from atlas.shared import Company


def _company(ticker: str = "NVDA") -> Company:
    return Company(
        id=f"company-{ticker.lower()}",
        name="NVIDIA" if ticker == "NVDA" else ticker,
        ticker=ticker,
        sector="Semiconductors",
        country="United States",
    )


def _knowledge_fact(ticker: str = "NVDA") -> KnowledgeFact:
    return KnowledgeFact(
        id=f"fact-{ticker.lower()}",
        subject_node_id=f"company-{ticker.lower()}",
        statement=f"{ticker} has supplied knowledge context.",
        source=KnowledgeSource(id="source-1", name="Company filing", source_type="Filing"),
        timestamp="2026-06-30T00:00:00Z",
        confidence=90,
        evidence_reference=KnowledgeReference(
            id=f"reference-{ticker.lower()}",
            source_id="source-1",
            citation="Annual report",
        ),
    )


def _research_project(with_open_question: bool = True, unsupported_fragment: bool = False) -> ResearchProject:
    questions = (
        ResearchQuestion(
            id="question-1",
            question="What evidence would improve understanding?",
            related_topic="NVDA",
            status=ResearchQuestionStatus.RESEARCHING
            if with_open_question
            else ResearchQuestionStatus.RESOLVED,
            evidence_reference_ids=("research-evidence-1",),
            resolution_notes="" if with_open_question else "Question resolved from supplied evidence.",
        ),
    )
    fragments = (
        ThesisFragment(
            id="thesis-1",
            claim="Research thesis is still forming.",
            supporting_evidence_reference_ids=()
            if unsupported_fragment
            else ("research-evidence-1",),
            status=ResearchStatus.THESIS_FORMING,
        ),
    )
    return ResearchProject(
        id="research-nvda",
        title="NVIDIA research",
        topic="NVDA",
        status=ResearchStatus.THESIS_FORMING,
        questions=questions,
        thesis_fragments=fragments,
        evidence_references=(
            ResearchEvidenceReference(
                id="research-evidence-1",
                source_id="research-source",
                description="Linked research evidence.",
                knowledge_fact_id="fact-nvda",
            ),
        ),
    )


def _company_analysis(level: str = "moderate") -> CompanyAnalysisReport:
    return CompanyAnalysisReport(
        company=_company(),
        sections=(),
        evidence_links=(),
        risks=(),
        unknowns=(),
        confidence=CompanyAnalysisConfidence(
            level=level,
            explanation=f"Confidence is {level} because evidence is incomplete.",
            drivers=("driver",),
            limitations=("limitation",),
        ),
        what_could_change_the_view=(),
    )


def test_watchlist_report_generation() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="AI Infrastructure",
            items=(
                WatchlistItem(
                    id="item-nvda",
                    ticker="NVDA",
                    name="NVIDIA",
                    status=WatchlistStatus.RESEARCHING,
                    company=_company(),
                    research_project=_research_project(),
                    knowledge_facts=(_knowledge_fact(),),
                    company_analysis=_company_analysis(),
                ),
            ),
        )
    )

    assert report.name == "AI Infrastructure"
    assert report.overview == "AI Infrastructure contains 1 item(s). 1 item(s) deserve review or more evidence."
    assert report.observations[0].ticker == "NVDA"
    assert report.observations[0].priority == WatchlistPriority.HAS_QUESTIONS
    assert report.open_questions[0].question == "What evidence would improve understanding?"


def test_prioritisation_is_deterministic() -> None:
    watchlist_input = WatchlistIntelligenceInput(
        name="Test Watchlist",
        items=(
            WatchlistItem(id="item-b", ticker="MSFT", company=_company("MSFT"), knowledge_facts=(_knowledge_fact("MSFT"),)),
            WatchlistItem(id="item-a", ticker="AAPL"),
        ),
    )
    engine = WatchlistIntelligenceEngine()

    first = engine.analyze(watchlist_input)
    second = engine.analyze(watchlist_input)

    assert first == second
    assert [observation.ticker for observation in first.observations] == ["AAPL", "MSFT"]
    assert first.observations[0].priority == WatchlistPriority.NEEDS_EVIDENCE


def test_missing_evidence_and_unknown_detection() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="Sparse",
            items=(WatchlistItem(id="item-unknown", ticker="UNK"),),
        )
    )

    unknown_titles = [unknown.title for unknown in report.unknowns]

    assert "Missing Company Context" in unknown_titles
    assert "No Linked Research Project" in unknown_titles
    assert "No Supporting Knowledge Facts" in unknown_titles
    assert [gap.title for gap in report.evidence_gaps] == [
        "No Linked Research Project",
        "No Supporting Knowledge Facts",
    ]


def test_archived_and_paused_items_do_not_create_attention() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="Inactive",
            items=(
                WatchlistItem(id="item-paused", ticker="PAUS", status=WatchlistStatus.PAUSED),
                WatchlistItem(id="item-archived", ticker="ARCH", status=WatchlistStatus.ARCHIVED),
            ),
        )
    )

    priorities = {observation.ticker: observation.priority for observation in report.observations}

    assert priorities == {
        "ARCH": WatchlistPriority.ARCHIVED,
        "PAUS": WatchlistPriority.PAUSED,
    }
    assert report.companies_needing_attention == ()


def test_company_analysis_low_confidence_is_surfaced() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="Company Analysis Context",
            items=(
                WatchlistItem(
                    id="item-nvda",
                    ticker="NVDA",
                    company=_company(),
                    research_project=_research_project(with_open_question=False),
                    knowledge_facts=(_knowledge_fact(),),
                    company_analysis=_company_analysis("low"),
                ),
            ),
        )
    )

    assert any(unknown.title == "Low Company Analysis Confidence" for unknown in report.unknowns)
    assert any(signal.title == "Low Company Analysis Confidence" for signal in report.observations[0].signals)


def test_thesis_fragments_without_evidence_are_evidence_gaps() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="Research Gap",
            items=(
                WatchlistItem(
                    id="item-nvda",
                    ticker="NVDA",
                    company=_company(),
                    research_project=_research_project(with_open_question=False, unsupported_fragment=True),
                    knowledge_facts=(_knowledge_fact(),),
                ),
            ),
        )
    )

    assert report.observations[0].priority == WatchlistPriority.INCOMPLETE
    assert [gap.title for gap in report.evidence_gaps] == ["Thesis Fragment Needs Evidence"]


def test_empty_watchlist_behavior() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(name="Empty Watchlist")
    )

    assert report.overview == "Empty Watchlist contains 0 item(s). 0 item(s) deserve review or more evidence."
    assert report.observations == ()
    assert report.suggested_next_research_steps == (
        "Continue observing and update evidence when new facts are available.",
    )


def test_watchlist_intelligence_avoids_trade_and_urgency_language() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="Guardrails",
            items=(
                WatchlistItem(
                    id="item-nvda",
                    ticker="NVDA",
                    company=_company(),
                    research_project=_research_project(),
                    knowledge_facts=(_knowledge_fact(),),
                ),
            ),
        )
    )
    text = " ".join(
        [
            report.overview,
            " ".join(observation.detail for observation in report.observations),
            " ".join(step for step in report.suggested_next_research_steps),
        ]
    ).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "strong buy" not in text
    assert "guaranteed" not in text
    assert "risk-free" not in text
    assert "prediction" not in text
    assert "urgent" not in text
    assert "must act" not in text


def test_watchlist_intelligence_does_not_require_ai_or_api_usage() -> None:
    engine = WatchlistIntelligenceEngine()

    assert not hasattr(engine, "client")
    assert not hasattr(engine, "provider")
