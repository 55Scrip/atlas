"""Sprint 49: Daily Brief input builder and integration tests.

Tests that build_daily_brief_input correctly transforms typed Atlas structures
and that DailyBriefCapability produces correct output for each integration target.
All tests are deterministic, make no network calls, and use no AI.
"""

from __future__ import annotations

from atlas.capabilities.company_analysis.models import (
    CompanyAnalysisConfidence,
    CompanyAnalysisObservation,
    CompanyAnalysisReport,
    CompanyAnalysisUnknown,
)
from atlas.capabilities.daily_brief import (
    DailyBriefCapability,
    DailyBriefInput,
    DailyBriefPriority,
    build_daily_brief_input,
)
from atlas.capabilities.daily_brief.engine import render_daily_brief_report
from atlas.capabilities.daily_brief.input_builder import _extract_open_questions
from atlas.capabilities.discovery.models import (
    DiscoveryCandidate,
    DiscoveryContext,
    DiscoveryPriority,
    DiscoveryReason,
    DiscoveryReport,
)
from atlas.capabilities.watchlist_intelligence.models import (
    WatchlistIntelligenceReport,
    WatchlistObservation,
    WatchlistPriority,
    WatchlistQuestion,
    WatchlistUnknown,
)
from atlas.domains.research.models import (
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
)
from atlas.shared import Company, ResearchNote

FORBIDDEN_LANGUAGE = (
    "buy",
    "sell",
    "strong buy",
    "strong sell",
    "urgent",
    "must act",
    "guaranteed",
    "risk-free",
    "price target",
    "outperform",
    "entry",
    "exit",
)


# ── fixtures ──────────────────────────────────────────────────────────────────


def _make_research_note(title: str = "NVDA research", body: str = "Initial notes.") -> ResearchNote:
    return ResearchNote(
        id="note-1",
        title=title,
        body=body,
        created_at="2026-07-01",
        related_tickers=("NVDA",),
    )


def _make_research_project(open_question_count: int = 2) -> ResearchProject:
    questions = tuple(
        ResearchQuestion(
            id=f"q-{i}",
            question=f"Research question {i}",
            related_topic="NVDA",
            status=ResearchQuestionStatus.OPEN,
        )
        for i in range(open_question_count)
    )
    return ResearchProject(
        id="proj-1",
        title="NVDA Research",
        topic="NVDA",
        status=ResearchStatus.RESEARCHING,
        questions=questions,
    )


def _make_watchlist_report(open_question_count: int = 1) -> WatchlistIntelligenceReport:
    questions = tuple(
        WatchlistQuestion(id=f"wq-{i}", question=f"Watchlist question {i}", status="open")
        for i in range(open_question_count)
    )
    return WatchlistIntelligenceReport(
        name="My Watchlist",
        overview="Watchlist overview.",
        observations=(),
        companies_needing_attention=(),
        open_questions=questions,
        evidence_gaps=(),
        unknowns=(),
        suggested_next_research_steps=("Research NVDA moat further.",),
    )


def _make_discovery_report(candidate_count: int = 1) -> DiscoveryReport:
    candidates = tuple(
        DiscoveryCandidate(
            identifier=f"TICK{i}",
            title=f"Company {i}",
            reasons=(DiscoveryReason(title="Knowledge Fact", detail="Multiple facts available."),),
            supporting_evidence_links=(),
            related_knowledge_facts=(),
            related_research_questions=(),
            related_watchlist_status=None,
            unknowns=(),
            suggested_next_research_questions=(),
            priority=DiscoveryPriority.MODERATE,
            confidence="medium",
            context=DiscoveryContext(),
        )
        for i in range(candidate_count)
    )
    return DiscoveryReport(
        summary=f"Found {candidate_count} candidate(s).",
        candidates=candidates,
        evidence_links=(),
        unknowns=(),
    )


def _make_company_report(ticker: str = "NVDA", unknown_count: int = 1) -> CompanyAnalysisReport:
    company = Company(id="nvda", name="NVIDIA", ticker=ticker, sector="Semiconductors")
    unknowns = tuple(
        CompanyAnalysisUnknown(title=f"Unknown {i}", detail="Missing evidence.")
        for i in range(unknown_count)
    )
    return CompanyAnalysisReport(
        company=company,
        sections=(),
        evidence_links=(),
        risks=(),
        unknowns=unknowns,
        confidence=CompanyAnalysisConfidence(
            level="medium",
            explanation="Moderate evidence available.",
            drivers=("Known revenue",),
            limitations=("Limited competitive data",),
        ),
        what_could_change_the_view=("New competitive entrant",),
    )


# ── builder unit tests ────────────────────────────────────────────────────────


def test_builder_produces_daily_brief_input() -> None:
    result = build_daily_brief_input()
    assert isinstance(result, DailyBriefInput)


def test_builder_empty_is_no_developments() -> None:
    brief_input = build_daily_brief_input()
    report = DailyBriefCapability().generate(brief_input)
    assert not report.summary.has_meaningful_developments


def test_builder_passes_through_portfolio_summary() -> None:
    sentinel = object()
    result = build_daily_brief_input(portfolio_summary=sentinel)
    assert result.portfolio_summary is sentinel


def test_builder_passes_through_research_notes() -> None:
    notes = (_make_research_note(),)
    result = build_daily_brief_input(research_notes=notes)
    assert result.research_notes == notes


def test_builder_passes_through_watchlist_report() -> None:
    report = _make_watchlist_report()
    result = build_daily_brief_input(watchlist_report=report)
    assert result.watchlist_report is report


def test_builder_passes_through_discovery_report() -> None:
    report = _make_discovery_report()
    result = build_daily_brief_input(discovery_report=report)
    assert result.discovery_report is report


def test_builder_passes_through_company_reports() -> None:
    reports = (_make_company_report(),)
    result = build_daily_brief_input(company_reports=reports)
    assert result.company_reports == reports


def test_builder_passes_through_knowledge_node_count() -> None:
    result = build_daily_brief_input(knowledge_node_count=12)
    assert result.knowledge_node_count == 12


def test_builder_passes_through_date_label() -> None:
    result = build_daily_brief_input(date_label="2026-07-01")
    assert result.date_label == "2026-07-01"


def test_builder_merges_explicit_questions_with_project_questions() -> None:
    project = _make_research_project(open_question_count=2)
    result = build_daily_brief_input(
        research_projects=(project,),
        open_research_questions=("Extra question",),
    )
    assert len(result.open_research_questions) == 3
    assert "Extra question" in result.open_research_questions
    assert "Research question 0" in result.open_research_questions


def test_builder_only_extracts_open_and_researching_questions() -> None:
    archived = ResearchQuestion(
        id="q-arch",
        question="Archived question",
        related_topic="X",
        status=ResearchQuestionStatus.ARCHIVED,
    )
    resolved = ResearchQuestion(
        id="q-res",
        question="Resolved question",
        related_topic="X",
        status=ResearchQuestionStatus.RESOLVED,
    )
    open_q = ResearchQuestion(
        id="q-open",
        question="Open question",
        related_topic="X",
        status=ResearchQuestionStatus.OPEN,
    )
    project = ResearchProject(
        id="p1",
        title="Test",
        topic="X",
        questions=(archived, resolved, open_q),
    )
    extracted = _extract_open_questions((project,))
    assert extracted == ("Open question",)


def test_extract_open_questions_empty_project() -> None:
    project = ResearchProject(id="p1", title="Test", topic="X")
    assert _extract_open_questions((project,)) == ()


def test_extract_open_questions_multiple_projects() -> None:
    p1 = _make_research_project(open_question_count=1)
    p2 = _make_research_project(open_question_count=2)
    result = _extract_open_questions((p1, p2))
    assert len(result) == 3


# ── research note integration ─────────────────────────────────────────────────


def test_research_notes_produce_research_context_section() -> None:
    brief_input = build_daily_brief_input(research_notes=(_make_research_note(),))
    report = DailyBriefCapability().generate(brief_input)
    assert any(s.title == "Research Context" for s in report.sections)


def test_research_note_title_used_as_item_title() -> None:
    note = _make_research_note(title="NVDA deep dive")
    brief_input = build_daily_brief_input(research_notes=(note,))
    report = DailyBriefCapability().generate(brief_input)
    research_section = next(s for s in report.sections if s.title == "Research Context")
    item_titles = [i.title for i in research_section.items]
    assert "NVDA deep dive" in item_titles


def test_research_note_body_used_as_item_detail() -> None:
    note = _make_research_note(body="Core thesis forming.")
    brief_input = build_daily_brief_input(research_notes=(note,))
    report = DailyBriefCapability().generate(brief_input)
    research_section = next(s for s in report.sections if s.title == "Research Context")
    detail_text = " ".join(i.detail for i in research_section.items)
    assert "Core thesis forming." in detail_text


def test_research_note_body_truncated_to_200_chars() -> None:
    note = _make_research_note(body="x" * 300)
    brief_input = build_daily_brief_input(research_notes=(note,))
    report = DailyBriefCapability().generate(brief_input)
    research_section = next(s for s in report.sections if s.title == "Research Context")
    for item in research_section.items:
        assert len(item.detail) <= 200


# ── watchlist integration ──────────────────────────────────────────────────────


def test_watchlist_report_produces_watchlist_context_section() -> None:
    brief_input = build_daily_brief_input(watchlist_report=_make_watchlist_report())
    report = DailyBriefCapability().generate(brief_input)
    assert any(s.title == "Watchlist Context" for s in report.sections)


def test_watchlist_open_questions_surface_in_section() -> None:
    brief_input = build_daily_brief_input(watchlist_report=_make_watchlist_report(open_question_count=3))
    report = DailyBriefCapability().generate(brief_input)
    section = next(s for s in report.sections if s.title == "Watchlist Context")
    detail_text = " ".join(i.detail for i in section.items)
    assert "3" in detail_text


def test_watchlist_suggested_steps_surface_in_next_steps() -> None:
    brief_input = build_daily_brief_input(watchlist_report=_make_watchlist_report())
    report = DailyBriefCapability().generate(brief_input)
    steps_text = " ".join(report.next_research_steps)
    assert "NVDA" in steps_text or "Research" in steps_text


def test_watchlist_empty_when_no_report() -> None:
    brief_input = build_daily_brief_input()
    report = DailyBriefCapability().generate(brief_input)
    assert not any(s.title == "Watchlist Context" for s in report.sections)


# ── discovery integration ──────────────────────────────────────────────────────


def test_discovery_report_produces_discovery_context_section() -> None:
    brief_input = build_daily_brief_input(discovery_report=_make_discovery_report())
    report = DailyBriefCapability().generate(brief_input)
    assert any(s.title == "Discovery Context" for s in report.sections)


def test_discovery_candidate_identifier_used_as_item_title() -> None:
    brief_input = build_daily_brief_input(discovery_report=_make_discovery_report(candidate_count=1))
    report = DailyBriefCapability().generate(brief_input)
    section = next(s for s in report.sections if s.title == "Discovery Context")
    assert "TICK0" in [i.title for i in section.items]


def test_discovery_candidate_reason_detail_used_as_item_detail() -> None:
    brief_input = build_daily_brief_input(discovery_report=_make_discovery_report())
    report = DailyBriefCapability().generate(brief_input)
    section = next(s for s in report.sections if s.title == "Discovery Context")
    detail_text = " ".join(i.detail for i in section.items)
    assert "Multiple facts available." in detail_text


def test_discovery_empty_when_no_report() -> None:
    brief_input = build_daily_brief_input()
    report = DailyBriefCapability().generate(brief_input)
    assert not any(s.title == "Discovery Context" for s in report.sections)


def test_discovery_candidate_count_in_opening_section() -> None:
    brief_input = build_daily_brief_input(discovery_report=_make_discovery_report(candidate_count=2))
    report = DailyBriefCapability().generate(brief_input)
    opening = next(s for s in report.sections if s.title == "What Deserves Attention")
    detail_text = " ".join(i.detail for i in opening.items)
    assert "2" in detail_text


# ── company analysis integration ──────────────────────────────────────────────


def test_company_report_produces_company_analysis_context_section() -> None:
    brief_input = build_daily_brief_input(company_reports=(_make_company_report(),))
    report = DailyBriefCapability().generate(brief_input)
    assert any(s.title == "Company Analysis Context" for s in report.sections)


def test_company_ticker_resolved_via_company_attribute() -> None:
    brief_input = build_daily_brief_input(company_reports=(_make_company_report(ticker="MSFT"),))
    report = DailyBriefCapability().generate(brief_input)
    section = next(s for s in report.sections if s.title == "Company Analysis Context")
    titles = [i.title for i in section.items]
    assert "MSFT" in titles


def test_company_unknowns_surface_in_section() -> None:
    brief_input = build_daily_brief_input(company_reports=(_make_company_report(unknown_count=2),))
    report = DailyBriefCapability().generate(brief_input)
    section = next(s for s in report.sections if s.title == "Company Analysis Context")
    detail_text = " ".join(i.detail for i in section.items)
    assert "2" in detail_text


def test_company_unknowns_surface_in_report_unknowns() -> None:
    brief_input = build_daily_brief_input(company_reports=(_make_company_report(unknown_count=1),))
    report = DailyBriefCapability().generate(brief_input)
    assert report.unknowns
    assert any(u.context == "NVDA" for u in report.unknowns)


def test_company_evidence_links_are_not_evidence_gaps() -> None:
    from atlas.capabilities.company_analysis.models import (
        CompanyAnalysisEvidenceLink,
        CompanyAnalysisReport,
        CompanyAnalysisConfidence,
    )
    company = Company(id="nvda", name="NVIDIA", ticker="NVDA")
    link = CompanyAnalysisEvidenceLink(
        id="ev-1", source="10-K", description="Revenue breakdown table."
    )
    report_obj = CompanyAnalysisReport(
        company=company,
        sections=(),
        evidence_links=(link,),
        risks=(),
        unknowns=(),
        confidence=CompanyAnalysisConfidence(
            level="medium", explanation="ok", drivers=(), limitations=()
        ),
        what_could_change_the_view=(),
    )
    brief_input = build_daily_brief_input(company_reports=(report_obj,))
    report = DailyBriefCapability().generate(brief_input)
    assert report.evidence_gaps == ()


def test_company_empty_when_no_reports() -> None:
    brief_input = build_daily_brief_input()
    report = DailyBriefCapability().generate(brief_input)
    assert not any(s.title == "Company Analysis Context" for s in report.sections)


# ── mixed-input integration ────────────────────────────────────────────────────


def test_all_inputs_together_produce_all_sections() -> None:
    from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio
    from atlas.analysis.portfolio import Portfolio as LegacyPortfolio
    from atlas.domains.portfolio import portfolio_summary

    legacy = LegacyPortfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "NVDA", "company": "NVIDIA", "sector": "Semiconductors",
                    "country": "USA", "market_cap": 1_000_000, "weight": 0.4,
                    "quality_score": 90, "risk_score": 50,
                },
                {
                    "ticker": "MSFT", "company": "Microsoft", "sector": "Software",
                    "country": "USA", "market_cap": 2_500_000, "weight": 0.6,
                    "quality_score": 88, "risk_score": 30,
                },
            ]
        }
    )
    ps = portfolio_summary(legacy_portfolio_to_domain_portfolio(legacy))

    brief_input = build_daily_brief_input(
        portfolio_summary=ps,
        research_notes=(_make_research_note(),),
        watchlist_report=_make_watchlist_report(),
        discovery_report=_make_discovery_report(),
        company_reports=(_make_company_report(),),
        knowledge_node_count=3,
    )
    report = DailyBriefCapability().generate(brief_input)
    section_titles = {s.title for s in report.sections}
    assert "What Deserves Attention" in section_titles
    assert "Portfolio Context" in section_titles
    assert "Research Context" in section_titles
    assert "Watchlist Context" in section_titles
    assert "Discovery Context" in section_titles
    assert "Company Analysis Context" in section_titles


def test_mixed_input_is_deterministic() -> None:
    note = _make_research_note()
    watchlist = _make_watchlist_report()
    discovery = _make_discovery_report()
    company = _make_company_report()
    brief_input = build_daily_brief_input(
        research_notes=(note,),
        watchlist_report=watchlist,
        discovery_report=discovery,
        company_reports=(company,),
        open_research_questions=("Q1", "Q2"),
    )
    first = render_daily_brief_report(DailyBriefCapability().generate(brief_input))
    second = render_daily_brief_report(DailyBriefCapability().generate(brief_input))
    assert first == second


# ── preserved behaviors ────────────────────────────────────────────────────────


def test_empty_builder_input_still_produces_no_developments() -> None:
    brief_input = build_daily_brief_input()
    report = DailyBriefCapability().generate(brief_input)
    assert not report.summary.has_meaningful_developments
    rendered = render_daily_brief_report(report)
    assert "No meaningful developments were identified" in rendered


def test_section_order_preserved_with_all_inputs() -> None:
    note = _make_research_note()
    brief_input = build_daily_brief_input(
        research_notes=(note,),
        watchlist_report=_make_watchlist_report(),
        discovery_report=_make_discovery_report(),
    )
    report = DailyBriefCapability().generate(brief_input)
    titles = [s.title for s in report.sections]
    assert titles[0] == "What Deserves Attention"


def test_no_forbidden_language_in_mixed_input_output() -> None:
    brief_input = build_daily_brief_input(
        research_notes=(_make_research_note(),),
        watchlist_report=_make_watchlist_report(),
        discovery_report=_make_discovery_report(),
        company_reports=(_make_company_report(),),
        open_research_questions=("What is the TAM?",),
    )
    rendered = render_daily_brief_report(DailyBriefCapability().generate(brief_input)).lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in rendered, f"Forbidden term found: {term!r}"


def test_builder_does_not_mutate_input_tuples() -> None:
    notes = (_make_research_note(),)
    original_id = id(notes)
    build_daily_brief_input(research_notes=notes)
    assert id(notes) == original_id


def test_input_builder_makes_no_network_calls(monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail(*args, **kwargs):
        raise AssertionError("urlopen must not be called by build_daily_brief_input")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail)
    build_daily_brief_input(
        research_notes=(_make_research_note(),),
        watchlist_report=_make_watchlist_report(),
        discovery_report=_make_discovery_report(),
        company_reports=(_make_company_report(),),
    )
