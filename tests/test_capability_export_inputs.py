"""Sprint 52: Meaningful capability export input tests.

Tests cover adapters (watchlist, knowledge, research), extended CLI flags,
error handling, round-trip export → Daily Brief, and language safety.
All tests are local-only, deterministic, and make no network calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.adapters.knowledge import knowledge_facts_from_dict
from atlas.adapters.research_input import research_projects_from_dict
from atlas.adapters.watchlist import watchlist_input_from_dict
from atlas.capabilities.discovery import DiscoveryEngine, DiscoveryInput
from atlas.capabilities.watchlist_intelligence import (
    WatchlistIntelligenceEngine,
    WatchlistIntelligenceInput,
    WatchlistStatus,
)
from atlas.cli.main import app
from atlas.domains.knowledge.models import KnowledgeFact
from atlas.domains.research.models import ResearchProject, ResearchQuestionStatus

runner = CliRunner()

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


# ── JSON fixture helpers ───────────────────────────────────────────────────────


def _watchlist_json(name: str = "My Watchlist", items: list | None = None) -> dict:
    if items is None:
        items = [
            {
                "id": "amd",
                "ticker": "AMD",
                "company": "AMD Corporation",
                "status": "researching",
                "open_questions": [
                    "What evidence supports long-term margin expansion?",
                    "How durable is the data centre GPU demand cycle?",
                ],
                "manual_observations": [
                    "Entered data centre market aggressively.",
                ],
            },
            {
                "id": "asml",
                "ticker": "ASML",
                "company": "ASML Holding",
                "status": "observing",
                "open_questions": ["What is the pace of EUV adoption?"],
            },
        ]
    return {"name": name, "items": items}


def _knowledge_json() -> dict:
    return {
        "facts": [
            {
                "id": "fact-1",
                "subject_node_id": "company-nvda",
                "statement": "NVDA is a leading GPU supplier for data centres.",
                "source": {
                    "id": "src-1",
                    "name": "10-K 2025",
                    "source_type": "Filing",
                    "url": "",
                },
                "timestamp": "2026-07-01T00:00:00Z",
                "confidence": 85,
            },
            {
                "id": "fact-2",
                "subject_node_id": "company-nvda",
                "statement": "NVDA reported $44bn data centre revenue in FY2025.",
                "source": {
                    "id": "src-1",
                    "name": "10-K 2025",
                    "source_type": "Filing",
                },
                "timestamp": "2026-07-01T00:00:00Z",
                "confidence": 90,
            },
        ]
    }


def _research_json() -> dict:
    return {
        "projects": [
            {
                "id": "proj-nvda",
                "title": "NVDA Research",
                "topic": "NVDA",
                "status": "researching",
                "questions": [
                    "What is the long-term GPU TAM?",
                    "Who are the key competitors?",
                ],
            },
            {
                "id": "proj-asml",
                "title": "ASML Research",
                "topic": "ASML",
                "status": "thesis_forming",
                "questions": ["What is the pace of EUV adoption?"],
            },
        ]
    }


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ── watchlist adapter unit tests ───────────────────────────────────────────────


def test_watchlist_adapter_produces_input() -> None:
    data = _watchlist_json()
    result = watchlist_input_from_dict(data)
    assert isinstance(result, WatchlistIntelligenceInput)


def test_watchlist_adapter_name_preserved() -> None:
    result = watchlist_input_from_dict({"name": "Portfolio Watch", "items": []})
    assert result.name == "Portfolio Watch"


def test_watchlist_adapter_items_parsed() -> None:
    result = watchlist_input_from_dict(_watchlist_json())
    assert len(result.items) == 2


def test_watchlist_adapter_ticker_uppercased() -> None:
    result = watchlist_input_from_dict({"items": [{"ticker": "amd", "status": "researching"}]})
    assert result.items[0].ticker == "AMD"


def test_watchlist_adapter_status_parsed() -> None:
    result = watchlist_input_from_dict({"items": [{"ticker": "AMD", "status": "paused"}]})
    assert result.items[0].status == WatchlistStatus.PAUSED


def test_watchlist_adapter_open_questions_become_research_project() -> None:
    result = watchlist_input_from_dict({
        "items": [{"ticker": "AMD", "open_questions": ["What is the moat?"]}]
    })
    item = result.items[0]
    assert item.research_project is not None
    assert len(item.research_project.questions) == 1
    assert item.research_project.questions[0].status == ResearchQuestionStatus.OPEN


def test_watchlist_adapter_no_questions_no_research_project() -> None:
    result = watchlist_input_from_dict({"items": [{"ticker": "AMD"}]})
    assert result.items[0].research_project is None


def test_watchlist_adapter_manual_observations_preserved() -> None:
    result = watchlist_input_from_dict({
        "items": [{"ticker": "AMD", "manual_observations": ["Entered GPU market."]}]
    })
    assert "Entered GPU market." in result.items[0].manual_observations


def test_watchlist_adapter_missing_ticker_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="ticker"):
        watchlist_input_from_dict({"items": [{"id": "amd", "status": "observing"}]})


def test_watchlist_adapter_invalid_status_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="Invalid status"):
        watchlist_input_from_dict({"items": [{"ticker": "AMD", "status": "unknown_status"}]})


def test_watchlist_adapter_non_dict_input_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be a JSON object"):
        watchlist_input_from_dict([{"ticker": "AMD"}])


def test_watchlist_adapter_items_not_list_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        watchlist_input_from_dict({"items": "not a list"})


def test_watchlist_adapter_empty_items_produces_empty_input() -> None:
    result = watchlist_input_from_dict({"items": []})
    assert result.items == ()


def test_watchlist_adapter_feeds_engine_successfully() -> None:
    wi_input = watchlist_input_from_dict(_watchlist_json())
    report = WatchlistIntelligenceEngine().analyze(wi_input)
    assert report.name == "My Watchlist"
    assert report.open_questions  # AMD has open research questions


def test_watchlist_adapter_open_questions_surface_in_report() -> None:
    wi_input = watchlist_input_from_dict(_watchlist_json())
    report = WatchlistIntelligenceEngine().analyze(wi_input)
    question_texts = [q.question for q in report.open_questions]
    assert any("margin expansion" in q.lower() for q in question_texts)


# ── knowledge adapter unit tests ───────────────────────────────────────────────


def test_knowledge_adapter_produces_facts() -> None:
    facts = knowledge_facts_from_dict(_knowledge_json())
    assert isinstance(facts, tuple)
    assert len(facts) == 2


def test_knowledge_adapter_all_are_knowledge_facts() -> None:
    facts = knowledge_facts_from_dict(_knowledge_json())
    assert all(isinstance(f, KnowledgeFact) for f in facts)


def test_knowledge_adapter_statement_preserved() -> None:
    facts = knowledge_facts_from_dict(_knowledge_json())
    assert facts[0].statement == "NVDA is a leading GPU supplier for data centres."


def test_knowledge_adapter_confidence_preserved() -> None:
    facts = knowledge_facts_from_dict(_knowledge_json())
    assert facts[0].confidence == 85


def test_knowledge_adapter_source_name_preserved() -> None:
    facts = knowledge_facts_from_dict(_knowledge_json())
    assert facts[0].source.name == "10-K 2025"


def test_knowledge_adapter_missing_id_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="missing required field"):
        knowledge_facts_from_dict({"facts": [{"statement": "x", "subject_node_id": "y"}]})


def test_knowledge_adapter_empty_facts_returns_empty_tuple() -> None:
    assert knowledge_facts_from_dict({"facts": []}) == ()


def test_knowledge_adapter_non_dict_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be a JSON object"):
        knowledge_facts_from_dict([])


def test_knowledge_adapter_feeds_discovery_engine() -> None:
    facts = knowledge_facts_from_dict(_knowledge_json())
    report = DiscoveryEngine().discover(DiscoveryInput(knowledge_facts=facts))
    assert report.candidates  # NVDA has 2 facts → should produce a candidate


def test_knowledge_adapter_subject_node_id_produces_candidate_identifier() -> None:
    facts = knowledge_facts_from_dict(_knowledge_json())
    report = DiscoveryEngine().discover(DiscoveryInput(knowledge_facts=facts))
    identifiers = {c.identifier for c in report.candidates}
    assert "company-nvda" in identifiers


# ── research adapter unit tests ────────────────────────────────────────────────


def test_research_adapter_produces_projects() -> None:
    projects = research_projects_from_dict(_research_json())
    assert isinstance(projects, tuple)
    assert len(projects) == 2


def test_research_adapter_all_are_research_projects() -> None:
    projects = research_projects_from_dict(_research_json())
    assert all(isinstance(p, ResearchProject) for p in projects)


def test_research_adapter_title_preserved() -> None:
    projects = research_projects_from_dict(_research_json())
    assert projects[0].title == "NVDA Research"


def test_research_adapter_questions_parsed() -> None:
    projects = research_projects_from_dict(_research_json())
    assert len(projects[0].questions) == 2


def test_research_adapter_questions_are_open() -> None:
    projects = research_projects_from_dict(_research_json())
    for q in projects[0].questions:
        assert q.status == ResearchQuestionStatus.OPEN


def test_research_adapter_missing_id_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="missing required field"):
        research_projects_from_dict({"projects": [{"title": "x"}]})


def test_research_adapter_invalid_status_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="Invalid status"):
        research_projects_from_dict({"projects": [{"id": "p1", "status": "bad_status"}]})


def test_research_adapter_empty_projects_returns_empty_tuple() -> None:
    assert research_projects_from_dict({"projects": []}) == ()


def test_research_adapter_non_dict_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be a JSON object"):
        research_projects_from_dict([])


def test_research_adapter_feeds_discovery_engine() -> None:
    projects = research_projects_from_dict(_research_json())
    report = DiscoveryEngine().discover(DiscoveryInput(research_projects=projects))
    assert report.candidates


# ── watchlist intelligence CLI --input flag ────────────────────────────────────


def test_watchlist_intelligence_input_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "wl.json", _watchlist_json())
    result = runner.invoke(app, ["watchlist", "intelligence", "--input", str(path)])
    assert result.exit_code == 0


def test_watchlist_intelligence_input_surfaces_questions(tmp_path: Path) -> None:
    path = _write(tmp_path, "wl.json", _watchlist_json())
    result = runner.invoke(app, ["watchlist", "intelligence", "--input", str(path)])
    assert result.exit_code == 0
    assert "Open Questions" in result.stdout


def test_watchlist_intelligence_input_and_output(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "wl.json", _watchlist_json())
    out_path = tmp_path / "wl_export.json"
    result = runner.invoke(app, [
        "watchlist", "intelligence",
        "--input", str(in_path),
        "--output", str(out_path),
    ])
    assert result.exit_code == 0
    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data["name"] == "My Watchlist"
    assert data["suggested_next_research_steps"]


def test_watchlist_intelligence_export_has_open_questions_when_input_provided(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "wl.json", _watchlist_json())
    out_path = tmp_path / "wl_export.json"
    runner.invoke(app, [
        "watchlist", "intelligence",
        "--input", str(in_path),
        "--output", str(out_path),
    ])
    data = json.loads(out_path.read_text())
    assert data["open_questions"]


def test_watchlist_intelligence_missing_input_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["watchlist", "intelligence", "--input", str(tmp_path / "nope.json")])
    assert result.exit_code == 1
    assert "Watchlist intelligence failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_watchlist_intelligence_invalid_json_input_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    result = runner.invoke(app, ["watchlist", "intelligence", "--input", str(path)])
    assert result.exit_code == 1
    assert "Watchlist intelligence failed" in result.stdout


def test_watchlist_intelligence_no_input_still_works() -> None:
    result = runner.invoke(app, ["watchlist", "intelligence"])
    assert result.exit_code == 0


def test_watchlist_intelligence_input_no_forbidden_language(tmp_path: Path) -> None:
    path = _write(tmp_path, "wl.json", _watchlist_json())
    result = runner.invoke(app, ["watchlist", "intelligence", "--input", str(path)])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term: {term!r}"


def test_watchlist_intelligence_input_is_deterministic(tmp_path: Path) -> None:
    path = _write(tmp_path, "wl.json", _watchlist_json())
    out1 = tmp_path / "w1.json"
    out2 = tmp_path / "w2.json"
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(path), "--output", str(out1)])
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(path), "--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


# ── discovery export CLI new flags ─────────────────────────────────────────────


def test_discovery_export_with_knowledge_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "knowledge.json", _knowledge_json())
    result = runner.invoke(app, ["discovery", "export", "--knowledge", str(path)])
    assert result.exit_code == 0


def test_discovery_export_knowledge_produces_candidates(tmp_path: Path) -> None:
    path = _write(tmp_path, "knowledge.json", _knowledge_json())
    out = tmp_path / "discovery.json"
    runner.invoke(app, ["discovery", "export", "--knowledge", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert data["candidates"]


def test_discovery_export_with_research_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "research.json", _research_json())
    result = runner.invoke(app, ["discovery", "export", "--research", str(path)])
    assert result.exit_code == 0


def test_discovery_export_research_produces_candidates(tmp_path: Path) -> None:
    path = _write(tmp_path, "research.json", _research_json())
    out = tmp_path / "discovery.json"
    runner.invoke(app, ["discovery", "export", "--research", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert data["candidates"]


def test_discovery_export_with_watchlist_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "wl.json", _watchlist_json())
    result = runner.invoke(app, ["discovery", "export", "--watchlist", str(path)])
    assert result.exit_code == 0


def test_discovery_export_watchlist_produces_candidates(tmp_path: Path) -> None:
    path = _write(tmp_path, "wl.json", _watchlist_json())
    out = tmp_path / "discovery.json"
    runner.invoke(app, ["discovery", "export", "--watchlist", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert data["candidates"]


def test_discovery_export_all_flags_together(tmp_path: Path) -> None:
    k_path = _write(tmp_path, "knowledge.json", _knowledge_json())
    r_path = _write(tmp_path, "research.json", _research_json())
    w_path = _write(tmp_path, "wl.json", _watchlist_json())
    out = tmp_path / "discovery.json"
    result = runner.invoke(app, [
        "discovery", "export",
        "--knowledge", str(k_path),
        "--research", str(r_path),
        "--watchlist", str(w_path),
        "--output", str(out),
    ])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["candidates"]


def test_discovery_export_missing_knowledge_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["discovery", "export", "--knowledge", str(tmp_path / "nope.json")])
    assert result.exit_code == 1
    assert "Discovery export failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_discovery_export_invalid_research_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[bad", encoding="utf-8")
    result = runner.invoke(app, ["discovery", "export", "--research", str(path)])
    assert result.exit_code == 1
    assert "Discovery export failed" in result.stdout


def test_discovery_export_no_flags_still_works() -> None:
    result = runner.invoke(app, ["discovery", "export"])
    assert result.exit_code == 0


def test_discovery_export_no_forbidden_language_with_inputs(tmp_path: Path) -> None:
    k_path = _write(tmp_path, "knowledge.json", _knowledge_json())
    r_path = _write(tmp_path, "research.json", _research_json())
    result = runner.invoke(app, [
        "discovery", "export",
        "--knowledge", str(k_path),
        "--research", str(r_path),
    ])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term: {term!r}"


def test_discovery_export_is_deterministic_with_inputs(tmp_path: Path) -> None:
    k_path = _write(tmp_path, "knowledge.json", _knowledge_json())
    out1 = tmp_path / "d1.json"
    out2 = tmp_path / "d2.json"
    runner.invoke(app, ["discovery", "export", "--knowledge", str(k_path), "--output", str(out1)])
    runner.invoke(app, ["discovery", "export", "--knowledge", str(k_path), "--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


# ── end-to-end round-trip tests ────────────────────────────────────────────────


def test_watchlist_export_with_input_to_daily_summary(tmp_path: Path) -> None:
    wl_path = _write(tmp_path, "wl.json", _watchlist_json())
    export_path = tmp_path / "wl_export.json"
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(wl_path), "--output", str(export_path)])
    daily_result = runner.invoke(app, ["daily", "summary", "--watchlist", str(export_path)])
    assert daily_result.exit_code == 0
    assert "Atlas Daily Brief" in daily_result.stdout
    assert "Watchlist Context" in daily_result.stdout


def test_discovery_export_with_knowledge_to_daily_summary(tmp_path: Path) -> None:
    k_path = _write(tmp_path, "knowledge.json", _knowledge_json())
    export_path = tmp_path / "discovery.json"
    runner.invoke(app, ["discovery", "export", "--knowledge", str(k_path), "--output", str(export_path)])
    daily_result = runner.invoke(app, ["daily", "summary", "--discovery", str(export_path)])
    assert daily_result.exit_code == 0
    assert "Discovery Context" in daily_result.stdout


def test_full_pipeline_watchlist_then_discovery_then_daily(tmp_path: Path) -> None:
    wl_path = _write(tmp_path, "wl.json", _watchlist_json())
    wl_export = tmp_path / "wl_export.json"
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(wl_path), "--output", str(wl_export)])

    k_path = _write(tmp_path, "knowledge.json", _knowledge_json())
    disc_export = tmp_path / "disc_export.json"
    runner.invoke(app, [
        "discovery", "export",
        "--knowledge", str(k_path),
        "--watchlist", str(wl_path),
        "--output", str(disc_export),
    ])

    daily_result = runner.invoke(app, [
        "daily", "summary",
        "--watchlist", str(wl_export),
        "--discovery", str(disc_export),
    ])
    assert daily_result.exit_code == 0
    assert "Watchlist Context" in daily_result.stdout
    assert "Discovery Context" in daily_result.stdout


def test_full_pipeline_no_forbidden_language(tmp_path: Path) -> None:
    wl_path = _write(tmp_path, "wl.json", _watchlist_json())
    k_path = _write(tmp_path, "knowledge.json", _knowledge_json())
    wl_export = tmp_path / "wl_export.json"
    disc_export = tmp_path / "disc_export.json"

    runner.invoke(app, ["watchlist", "intelligence", "--input", str(wl_path), "--output", str(wl_export)])
    runner.invoke(app, ["discovery", "export", "--knowledge", str(k_path), "--output", str(disc_export)])

    daily_result = runner.invoke(app, [
        "daily", "summary",
        "--watchlist", str(wl_export),
        "--discovery", str(disc_export),
    ])
    assert daily_result.exit_code == 0
    output_lower = daily_result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term in pipeline output: {term!r}"


def test_full_pipeline_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail(*args, **kwargs):
        raise AssertionError("urlopen must not be called during export pipeline")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail)

    wl_path = _write(tmp_path, "wl.json", _watchlist_json())
    export_path = tmp_path / "wl_export.json"
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(wl_path), "--output", str(export_path)])
    daily_result = runner.invoke(app, ["daily", "summary", "--watchlist", str(export_path)])
    assert daily_result.exit_code == 0
