"""Sprint 51: Capability JSON export tests.

Tests cover:
- Watchlist Intelligence export (exporter + CLI --output)
- Discovery export (exporter + CLI --output)
- Round-trip: export → Daily Brief --watchlist / --discovery
- Error handling (invalid paths)
- Determinism
- Language safety
- No network calls
- Existing CLI behavior preserved
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.capabilities.daily_brief.json_loader import (
    parse_discovery_json,
    parse_watchlist_json,
)
from atlas.capabilities.discovery import DiscoveryEngine, DiscoveryInput
from atlas.capabilities.discovery.exporter import discovery_report_to_dict
from atlas.capabilities.watchlist_intelligence import (
    WatchlistIntelligenceEngine,
    WatchlistIntelligenceInput,
    WatchlistItem,
    WatchlistStatus,
)
from atlas.capabilities.watchlist_intelligence.exporter import watchlist_report_to_dict
from atlas.cli.main import app

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


# ── watchlist exporter unit tests ──────────────────────────────────────────────


def test_watchlist_exporter_returns_dict() -> None:
    report = WatchlistIntelligenceEngine().analyze(WatchlistIntelligenceInput(name="Test"))
    result = watchlist_report_to_dict(report)
    assert isinstance(result, dict)


def test_watchlist_export_has_required_keys() -> None:
    report = WatchlistIntelligenceEngine().analyze(WatchlistIntelligenceInput(name="Test"))
    result = watchlist_report_to_dict(report)
    assert "name" in result
    assert "open_questions" in result
    assert "suggested_next_research_steps" in result


def test_watchlist_export_name_preserved() -> None:
    report = WatchlistIntelligenceEngine().analyze(WatchlistIntelligenceInput(name="My Portfolio Watch"))
    result = watchlist_report_to_dict(report)
    assert result["name"] == "My Portfolio Watch"


def test_watchlist_export_open_questions_are_list() -> None:
    report = WatchlistIntelligenceEngine().analyze(WatchlistIntelligenceInput(name="Test"))
    result = watchlist_report_to_dict(report)
    assert isinstance(result["open_questions"], list)


def test_watchlist_export_steps_are_list() -> None:
    report = WatchlistIntelligenceEngine().analyze(WatchlistIntelligenceInput(name="Test"))
    result = watchlist_report_to_dict(report)
    assert isinstance(result["suggested_next_research_steps"], list)


def test_watchlist_export_is_json_serializable() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="Test",
            items=(WatchlistItem(id="item-1", ticker="NVDA"),),
        )
    )
    result = watchlist_report_to_dict(report)
    serialized = json.dumps(result)
    assert isinstance(serialized, str)


def test_watchlist_export_is_deterministic() -> None:
    inp = WatchlistIntelligenceInput(
        name="Test",
        items=(WatchlistItem(id="item-1", ticker="NVDA"),),
    )
    first = watchlist_report_to_dict(WatchlistIntelligenceEngine().analyze(inp))
    second = watchlist_report_to_dict(WatchlistIntelligenceEngine().analyze(inp))
    assert first == second


def test_watchlist_export_with_item_produces_steps() -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="Test",
            items=(WatchlistItem(id="item-1", ticker="NVDA"),),
        )
    )
    result = watchlist_report_to_dict(report)
    assert result["suggested_next_research_steps"]


def test_watchlist_export_parseable_by_daily_brief_loader(tmp_path: Path) -> None:
    report = WatchlistIntelligenceEngine().analyze(
        WatchlistIntelligenceInput(
            name="My Watchlist",
            items=(WatchlistItem(id="item-1", ticker="NVDA"),),
        )
    )
    exported = watchlist_report_to_dict(report)
    path = tmp_path / "watchlist.json"
    path.write_text(json.dumps(exported), encoding="utf-8")
    parsed = parse_watchlist_json(json.loads(path.read_text()), path)
    assert parsed.name == "My Watchlist"
    assert isinstance(parsed.suggested_next_research_steps, tuple)


# ── discovery exporter unit tests ─────────────────────────────────────────────


def test_discovery_exporter_returns_dict() -> None:
    report = DiscoveryEngine().discover(DiscoveryInput())
    result = discovery_report_to_dict(report)
    assert isinstance(result, dict)


def test_discovery_export_has_required_keys() -> None:
    report = DiscoveryEngine().discover(DiscoveryInput())
    result = discovery_report_to_dict(report)
    assert "candidates" in result
    assert "summary" in result


def test_discovery_export_candidates_is_list() -> None:
    report = DiscoveryEngine().discover(DiscoveryInput())
    result = discovery_report_to_dict(report)
    assert isinstance(result["candidates"], list)


def test_discovery_export_is_json_serializable() -> None:
    report = DiscoveryEngine().discover(DiscoveryInput())
    result = discovery_report_to_dict(report)
    serialized = json.dumps(result)
    assert isinstance(serialized, str)


def test_discovery_export_is_deterministic() -> None:
    inp = DiscoveryInput()
    first = discovery_report_to_dict(DiscoveryEngine().discover(inp))
    second = discovery_report_to_dict(DiscoveryEngine().discover(inp))
    assert first == second


def test_discovery_export_candidate_has_required_fields() -> None:
    from atlas.domains.knowledge import KnowledgeFact, KnowledgeReference, KnowledgeSource
    fact = KnowledgeFact(
        id="fact-1",
        subject_node_id="company-nvda",
        statement="NVDA supplies GPUs.",
        source=KnowledgeSource(id="src-1", name="Filing", source_type="Filing"),
        timestamp="2026-07-01T00:00:00Z",
        confidence=80,
        evidence_reference=KnowledgeReference(
            id="ref-1", source_id="src-1", citation="Annual report"
        ),
    )
    report = DiscoveryEngine().discover(DiscoveryInput(knowledge_facts=(fact,)))
    result = discovery_report_to_dict(report)
    if result["candidates"]:
        candidate = result["candidates"][0]
        assert "identifier" in candidate
        assert "title" in candidate
        assert "reasons" in candidate
        assert "priority" in candidate


def test_discovery_export_parseable_by_daily_brief_loader(tmp_path: Path) -> None:
    report = DiscoveryEngine().discover(DiscoveryInput())
    exported = discovery_report_to_dict(report)
    path = tmp_path / "discovery.json"
    path.write_text(json.dumps(exported), encoding="utf-8")
    parsed = parse_discovery_json(json.loads(path.read_text()), path)
    assert isinstance(parsed.candidates, tuple)


# ── watchlist intelligence CLI command ─────────────────────────────────────────


def test_watchlist_intelligence_command_succeeds() -> None:
    result = runner.invoke(app, ["watchlist", "intelligence"])
    assert result.exit_code == 0


def test_watchlist_intelligence_command_output_readable() -> None:
    result = runner.invoke(app, ["watchlist", "intelligence"])
    assert result.exit_code == 0
    assert "Watchlist" in result.stdout


def test_watchlist_intelligence_output_flag_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "watchlist.json"
    result = runner.invoke(app, ["watchlist", "intelligence", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "name" in data
    assert "open_questions" in data
    assert "suggested_next_research_steps" in data


def test_watchlist_intelligence_output_flag_confirms_path(tmp_path: Path) -> None:
    out = tmp_path / "watchlist.json"
    result = runner.invoke(app, ["watchlist", "intelligence", "--output", str(out)])
    assert result.exit_code == 0
    assert "watchlist.json" in result.stdout


def test_watchlist_intelligence_output_is_valid_json(tmp_path: Path) -> None:
    out = tmp_path / "watchlist.json"
    runner.invoke(app, ["watchlist", "intelligence", "--output", str(out)])
    data = json.loads(out.read_text())
    assert isinstance(data, dict)


def test_watchlist_intelligence_output_is_deterministic(tmp_path: Path) -> None:
    out1 = tmp_path / "w1.json"
    out2 = tmp_path / "w2.json"
    runner.invoke(app, ["watchlist", "intelligence", "--output", str(out1)])
    runner.invoke(app, ["watchlist", "intelligence", "--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


def test_watchlist_intelligence_invalid_output_path_fails_cleanly() -> None:
    result = runner.invoke(app, ["watchlist", "intelligence", "--output", "/no/such/dir/w.json"])
    assert result.exit_code == 1
    assert "Watchlist intelligence failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_watchlist_intelligence_no_forbidden_language() -> None:
    result = runner.invoke(app, ["watchlist", "intelligence"])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term: {term!r}"


# ── discovery CLI command ──────────────────────────────────────────────────────


def test_discovery_export_command_succeeds() -> None:
    result = runner.invoke(app, ["discovery", "export"])
    assert result.exit_code == 0


def test_discovery_export_command_output_readable() -> None:
    result = runner.invoke(app, ["discovery", "export"])
    assert result.exit_code == 0
    assert "Discovery" in result.stdout


def test_discovery_export_output_flag_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "discovery.json"
    result = runner.invoke(app, ["discovery", "export", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "candidates" in data
    assert "summary" in data


def test_discovery_export_output_flag_confirms_path(tmp_path: Path) -> None:
    out = tmp_path / "discovery.json"
    result = runner.invoke(app, ["discovery", "export", "--output", str(out)])
    assert result.exit_code == 0
    assert "discovery.json" in result.stdout


def test_discovery_export_output_is_valid_json(tmp_path: Path) -> None:
    out = tmp_path / "discovery.json"
    runner.invoke(app, ["discovery", "export", "--output", str(out)])
    data = json.loads(out.read_text())
    assert isinstance(data, dict)


def test_discovery_export_output_is_deterministic(tmp_path: Path) -> None:
    out1 = tmp_path / "d1.json"
    out2 = tmp_path / "d2.json"
    runner.invoke(app, ["discovery", "export", "--output", str(out1)])
    runner.invoke(app, ["discovery", "export", "--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


def test_discovery_export_invalid_output_path_fails_cleanly() -> None:
    result = runner.invoke(app, ["discovery", "export", "--output", "/no/such/dir/d.json"])
    assert result.exit_code == 1
    assert "Discovery export failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_discovery_export_no_forbidden_language() -> None:
    result = runner.invoke(app, ["discovery", "export"])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term: {term!r}"


# ── round-trip: export → Daily Brief ──────────────────────────────────────────


def test_watchlist_export_round_trip_to_daily_summary(tmp_path: Path) -> None:
    watchlist_out = tmp_path / "watchlist.json"
    export_result = runner.invoke(
        app, ["watchlist", "intelligence", "--output", str(watchlist_out)]
    )
    assert export_result.exit_code == 0

    daily_result = runner.invoke(
        app, ["daily", "summary", "--watchlist", str(watchlist_out)]
    )
    assert daily_result.exit_code == 0
    assert "Atlas Daily Brief" in daily_result.stdout


def test_discovery_export_round_trip_to_daily_summary(tmp_path: Path) -> None:
    discovery_out = tmp_path / "discovery.json"
    export_result = runner.invoke(
        app, ["discovery", "export", "--output", str(discovery_out)]
    )
    assert export_result.exit_code == 0

    daily_result = runner.invoke(
        app, ["daily", "summary", "--discovery", str(discovery_out)]
    )
    assert daily_result.exit_code == 0
    assert "Atlas Daily Brief" in daily_result.stdout


def test_watchlist_and_discovery_export_combined_daily_summary(tmp_path: Path) -> None:
    watchlist_out = tmp_path / "watchlist.json"
    discovery_out = tmp_path / "discovery.json"

    runner.invoke(app, ["watchlist", "intelligence", "--output", str(watchlist_out)])
    runner.invoke(app, ["discovery", "export", "--output", str(discovery_out)])

    daily_result = runner.invoke(app, [
        "daily", "summary",
        "--watchlist", str(watchlist_out),
        "--discovery", str(discovery_out),
    ])
    assert daily_result.exit_code == 0
    assert "Atlas Daily Brief" in daily_result.stdout


def test_round_trip_output_is_deterministic(tmp_path: Path) -> None:
    watchlist_out = tmp_path / "watchlist.json"
    runner.invoke(app, ["watchlist", "intelligence", "--output", str(watchlist_out)])

    first = runner.invoke(app, ["daily", "summary", "--watchlist", str(watchlist_out)])
    second = runner.invoke(app, ["daily", "summary", "--watchlist", str(watchlist_out)])
    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout


def test_round_trip_no_forbidden_language(tmp_path: Path) -> None:
    watchlist_out = tmp_path / "watchlist.json"
    discovery_out = tmp_path / "discovery.json"
    runner.invoke(app, ["watchlist", "intelligence", "--output", str(watchlist_out)])
    runner.invoke(app, ["discovery", "export", "--output", str(discovery_out)])

    daily_result = runner.invoke(app, [
        "daily", "summary",
        "--watchlist", str(watchlist_out),
        "--discovery", str(discovery_out),
    ])
    assert daily_result.exit_code == 0
    output_lower = daily_result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term in round-trip output: {term!r}"


def test_round_trip_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail(*args, **kwargs):
        raise AssertionError("urlopen must not be called during export or daily summary")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail)

    watchlist_out = tmp_path / "watchlist.json"
    runner.invoke(app, ["watchlist", "intelligence", "--output", str(watchlist_out)])

    daily_result = runner.invoke(app, ["daily", "summary", "--watchlist", str(watchlist_out)])
    assert daily_result.exit_code == 0


# ── existing CLI behavior preserved ───────────────────────────────────────────


def test_watchlist_analyze_is_retired(tmp_path: Path) -> None:
    # Sprint 91: atlas watchlist analyze command body retired — no longer a valid command
    watchlist_path = tmp_path / "watchlist_legacy.json"
    watchlist_path.write_text(
        '{"tickers": ["NVDA"], "name": "Test Watchlist", "id": "w1", "owner_id": "user1"}',
        encoding="utf-8",
    )
    result = runner.invoke(app, ["watchlist", "analyze", str(watchlist_path)])
    assert result.exit_code != 0


def test_existing_daily_summary_no_flags_still_works() -> None:
    result = runner.invoke(app, ["daily", "summary"])
    assert result.exit_code == 0
    assert "No meaningful developments" in result.stdout


def test_existing_daily_brief_command_is_retired() -> None:
    """Sprint 85: atlas daily brief command body retired — no longer a valid command."""
    result = runner.invoke(app, ["daily", "brief"])
    assert result.exit_code != 0
