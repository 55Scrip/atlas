from datetime import UTC, datetime

from typer.testing import CliRunner

from atlas.analysis.company_analysis import MockCompanyAnalysisProvider
from atlas.analysis.engine import AtlasInvestmentEngine
from atlas.analysis.memory import (
    MemoryEngine,
    MemoryEntry,
    MemoryStore,
    render_memory_comparison,
    render_memory_entries,
)
from atlas.analysis.report import build_investment_report
from atlas.cli.main import app


def test_memory_store_saves_and_loads_entries(tmp_path):
    path = tmp_path / "memory.json"
    store = MemoryStore(path)
    report = build_investment_report(MockCompanyAnalysisProvider().get_company_analysis("NVDA"))
    entry = MemoryEntry.from_report(
        ticker="NVDA",
        report=report,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )

    store.save(entry)
    loaded_entries = store.load()

    assert loaded_entries == (entry,)
    assert path.exists()


def test_memory_engine_compares_two_latest_entries(tmp_path):
    path = tmp_path / "memory.json"
    store = MemoryStore(path)
    previous = MemoryEntry(
        ticker="NVDA",
        timestamp="2026-01-01T00:00:00+00:00",
        atlas_score=80,
        recommendation="Buy",
        confidence=70,
        category_scores={
            "quality": 90,
            "growth": 80,
            "valuation": 60,
            "financial_strength": 85,
            "risk": 70,
        },
        explanation_summary="Previous explanation.",
    )
    current = MemoryEntry(
        ticker="NVDA",
        timestamp="2026-02-01T00:00:00+00:00",
        atlas_score=86,
        recommendation="Buy",
        confidence=80,
        category_scores={
            "quality": 92,
            "growth": 95,
            "valuation": 72,
            "financial_strength": 91,
            "risk": 77,
        },
        explanation_summary="Current explanation.",
    )
    store.save(previous)
    store.save(current)

    comparison = MemoryEngine().compare(store, "NVDA")

    assert comparison.score_change == 6
    assert comparison.recommendation_change == "unchanged (Buy)"
    assert comparison.confidence_change == 10
    assert comparison.strongest_improving_category == "growth"
    assert comparison.weakest_category == "valuation"
    assert "+6" in comparison.explanation


def test_memory_engine_requires_two_entries_for_comparison(tmp_path):
    path = tmp_path / "memory.json"
    store = MemoryStore(path)
    report = build_investment_report(MockCompanyAnalysisProvider().get_company_analysis("NVDA"))
    MemoryEngine().save(
        store=store,
        ticker="NVDA",
        report=report,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )

    try:
        MemoryEngine().compare(store, "NVDA")
    except ValueError as exc:
        assert "At least two memory entries" in str(exc)
    else:
        raise AssertionError("MemoryEngine should require two entries to compare")


def test_memory_renderers_include_required_fields(tmp_path):
    path = tmp_path / "memory.json"
    store = MemoryStore(path)
    report = build_investment_report(MockCompanyAnalysisProvider().get_company_analysis("NVDA"))
    engine = MemoryEngine()
    engine.save(
        store=store,
        ticker="NVDA",
        report=report,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )
    engine.save(
        store=store,
        ticker="NVDA",
        report=report,
        timestamp=datetime(2026, 2, 1, tzinfo=UTC),
    )

    entries_rendered = render_memory_entries(store.load())
    comparison_rendered = render_memory_comparison(engine.compare(store, "NVDA"))

    assert "Memory Entries" in entries_rendered
    assert "NVDA" in entries_rendered
    assert "Memory Comparison" in comparison_rendered
    assert "Score Change" in comparison_rendered
    assert "Recommendation Change" in comparison_rendered
    assert "Strongest Improving Category" in comparison_rendered
    assert "Weakest Category" in comparison_rendered


def test_memory_save_uses_current_report_fields(tmp_path):
    path = tmp_path / "memory.json"
    store = MemoryStore(path)
    report = AtlasInvestmentEngine().analyze(
        MockCompanyAnalysisProvider().get_company_analysis("NVDA")
    )

    entry = MemoryEngine().save(
        store=store,
        ticker="NVDA",
        report=report,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert entry.atlas_score == report.atlas_score
    assert entry.recommendation == report.overall_recommendation
    assert entry.confidence == report.confidence
    assert entry.category_scores["quality"] == report.quality.score
    assert "bull case" in entry.explanation_summary.lower()


def test_memory_cli_save_show_and_compare(tmp_path):
    path = tmp_path / "memory.json"
    runner = CliRunner()

    first = runner.invoke(app, ["memory", "save", "NVDA", str(path)])
    second = runner.invoke(app, ["memory", "save", "NVDA", str(path)])
    show = runner.invoke(app, ["memory", "show", str(path)])
    compare = runner.invoke(app, ["memory", "compare", str(path), "NVDA"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "Memory saved" in first.output
    assert show.exit_code == 0
    assert "Memory Entries" in show.output
    assert compare.exit_code == 0
    assert "Memory Comparison" in compare.output
