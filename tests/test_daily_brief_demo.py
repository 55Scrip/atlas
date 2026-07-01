"""Sprint 58: Daily Brief demo dataset validation and end-to-end pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.main import app

runner = CliRunner()

DEMO_DIR = Path(__file__).parent.parent / "examples" / "daily_brief_demo"
KNOWLEDGE = DEMO_DIR / "knowledge.json"
RESEARCH_INPUT = DEMO_DIR / "research_input.json"
WATCHLIST_INPUT = DEMO_DIR / "watchlist_input.json"

FORBIDDEN = (
    "buy", "sell", "strong buy", "strong sell", "urgent", "must act",
    "guaranteed", "risk-free", "price target", "outperform", "market-beating",
)


# ── demo data validity ─────────────────────────────────────────────────────────


def test_knowledge_json_exists() -> None:
    assert KNOWLEDGE.exists()


def test_research_input_json_exists() -> None:
    assert RESEARCH_INPUT.exists()


def test_watchlist_input_json_exists() -> None:
    assert WATCHLIST_INPUT.exists()


def test_knowledge_json_is_valid_json() -> None:
    data = json.loads(KNOWLEDGE.read_text())
    assert isinstance(data, dict)


def test_knowledge_json_has_facts() -> None:
    data = json.loads(KNOWLEDGE.read_text())
    assert "facts" in data
    assert len(data["facts"]) > 0


def test_knowledge_facts_have_required_fields() -> None:
    data = json.loads(KNOWLEDGE.read_text())
    for fact in data["facts"]:
        assert "id" in fact, f"fact missing 'id': {fact}"
        assert "subject_node_id" in fact, f"fact missing 'subject_node_id': {fact}"
        assert "statement" in fact, f"fact missing 'statement': {fact}"


def test_research_input_is_valid_json() -> None:
    data = json.loads(RESEARCH_INPUT.read_text())
    assert isinstance(data, dict)


def test_research_input_has_projects() -> None:
    data = json.loads(RESEARCH_INPUT.read_text())
    assert "projects" in data
    assert len(data["projects"]) > 0


def test_research_projects_have_required_fields() -> None:
    data = json.loads(RESEARCH_INPUT.read_text())
    for proj in data["projects"]:
        assert "id" in proj, f"project missing 'id': {proj}"
        assert "topic" in proj, f"project missing 'topic': {proj}"


def test_watchlist_input_is_valid_json() -> None:
    data = json.loads(WATCHLIST_INPUT.read_text())
    assert isinstance(data, dict)


def test_watchlist_input_has_items() -> None:
    data = json.loads(WATCHLIST_INPUT.read_text())
    assert "items" in data
    assert len(data["items"]) > 0


def test_watchlist_items_have_ticker() -> None:
    data = json.loads(WATCHLIST_INPUT.read_text())
    for item in data["items"]:
        assert "ticker" in item, f"watchlist item missing 'ticker': {item}"


# ── individual export steps ────────────────────────────────────────────────────


def test_research_export_accepts_demo_input(tmp_path: Path) -> None:
    out = tmp_path / "research.json"
    result = runner.invoke(app, [
        "research", "export",
        "--input", str(RESEARCH_INPUT),
        "--output", str(out),
    ])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert "notes" in data
    assert "open_questions" in data


def test_watchlist_export_accepts_demo_input(tmp_path: Path) -> None:
    out = tmp_path / "watchlist.json"
    result = runner.invoke(app, [
        "watchlist", "intelligence",
        "--input", str(WATCHLIST_INPUT),
        "--output", str(out),
    ])
    assert result.exit_code == 0


def test_company_analysis_accepts_demo_inputs(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, [
        "research", "export",
        "--input", str(RESEARCH_INPUT),
        "--output", str(research_out),
    ])
    ca_out = tmp_path / "ca.json"
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--sector", "Semiconductors",
        "--country", "USA",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--knowledge", str(KNOWLEDGE),
        "--research", str(research_out),
        "--output", str(ca_out),
    ])
    assert result.exit_code == 0
    data = json.loads(ca_out.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["company"]["ticker"] == "AMD"


def test_discovery_export_accepts_demo_inputs(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    watchlist_out = tmp_path / "watchlist.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(watchlist_out)])
    disc_out = tmp_path / "discovery.json"
    result = runner.invoke(app, [
        "discovery", "export",
        "--knowledge", str(KNOWLEDGE),
        "--research", str(research_out),
        "--watchlist", str(watchlist_out),
        "--output", str(disc_out),
    ])
    assert result.exit_code == 0


# ── end-to-end pipeline ────────────────────────────────────────────────────────


def _run_full_pipeline(tmp_path: Path) -> tuple:
    """Run the complete demo pipeline and return (daily_result, all_outputs_ok)."""
    research_out = tmp_path / "research.json"
    watchlist_out = tmp_path / "watchlist.json"
    disc_out = tmp_path / "discovery.json"
    ca_out = tmp_path / "ca.json"

    r1 = runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    r2 = runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(watchlist_out)])
    r3 = runner.invoke(app, [
        "discovery", "export",
        "--knowledge", str(KNOWLEDGE),
        "--research", str(research_out),
        "--watchlist", str(watchlist_out),
        "--output", str(disc_out),
    ])
    r4 = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--sector", "Semiconductors",
        "--country", "USA",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--knowledge", str(KNOWLEDGE),
        "--research", str(research_out),
        "--output", str(ca_out),
    ])
    daily = runner.invoke(app, [
        "daily", "summary",
        "--research", str(research_out),
        "--watchlist", str(watchlist_out),
        "--discovery", str(disc_out),
        "--company-analysis", str(ca_out),
    ])
    all_ok = all(r.exit_code == 0 for r in [r1, r2, r3, r4, daily])
    return daily, all_ok


def test_end_to_end_pipeline_succeeds(tmp_path: Path) -> None:
    _, all_ok = _run_full_pipeline(tmp_path)
    assert all_ok


def test_daily_brief_contains_research_context(tmp_path: Path) -> None:
    daily, _ = _run_full_pipeline(tmp_path)
    assert "Research Context" in daily.stdout


def test_daily_brief_contains_watchlist_context(tmp_path: Path) -> None:
    daily, _ = _run_full_pipeline(tmp_path)
    assert "Watchlist Context" in daily.stdout


def test_daily_brief_contains_company_analysis_context(tmp_path: Path) -> None:
    daily, _ = _run_full_pipeline(tmp_path)
    assert "Company Analysis Context" in daily.stdout


def test_daily_brief_no_forbidden_language(tmp_path: Path) -> None:
    daily, _ = _run_full_pipeline(tmp_path)
    output_lower = daily.stdout.lower()
    for term in FORBIDDEN:
        assert term not in output_lower, f"Forbidden term found: {term!r}"


def test_end_to_end_pipeline_is_deterministic(tmp_path: Path) -> None:
    tmp1 = tmp_path / "run1"
    tmp2 = tmp_path / "run2"
    tmp1.mkdir()
    tmp2.mkdir()

    def outputs(d: Path) -> dict:
        r_out = d / "research.json"
        w_out = d / "watchlist.json"
        di_out = d / "discovery.json"
        ca_out = d / "ca.json"
        runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(r_out)])
        runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(w_out)])
        runner.invoke(app, ["discovery", "export", "--knowledge", str(KNOWLEDGE), "--research", str(r_out), "--watchlist", str(w_out), "--output", str(di_out)])
        runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--company-name", "AMD Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "AMD designs high-performance CPUs and GPUs.", "--knowledge", str(KNOWLEDGE), "--research", str(r_out), "--output", str(ca_out)])
        return {
            "research": json.loads(r_out.read_text()),
            "discovery": json.loads(di_out.read_text()),
            "ca": json.loads(ca_out.read_text()),
        }

    assert outputs(tmp1) == outputs(tmp2)


def test_end_to_end_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(yahoo_module, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network call")))
    _, all_ok = _run_full_pipeline(tmp_path)
    assert all_ok
