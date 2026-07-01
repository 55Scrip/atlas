"""Sprint 58/59/66: Daily Brief demo dataset validation, pipeline, and asset tests."""

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


def test_knowledge_includes_amd_facts() -> None:
    data = json.loads(KNOWLEDGE.read_text())
    ids = {f["id"] for f in data["facts"]}
    assert any(fid.startswith("amd-") for fid in ids), "No AMD facts found in knowledge.json"


def test_knowledge_includes_nvda_facts() -> None:
    data = json.loads(KNOWLEDGE.read_text())
    ids = {f["id"] for f in data["facts"]}
    assert any(fid.startswith("nvda-") for fid in ids), "No NVDA facts found in knowledge.json"


def test_research_input_is_valid_json() -> None:
    data = json.loads(RESEARCH_INPUT.read_text())
    assert isinstance(data, dict)


def test_research_input_has_projects() -> None:
    data = json.loads(RESEARCH_INPUT.read_text())
    assert "projects" in data
    assert len(data["projects"]) >= 2


def test_research_projects_have_required_fields() -> None:
    data = json.loads(RESEARCH_INPUT.read_text())
    for proj in data["projects"]:
        assert "id" in proj, f"project missing 'id': {proj}"
        assert "topic" in proj, f"project missing 'topic': {proj}"


def test_research_includes_amd_project() -> None:
    data = json.loads(RESEARCH_INPUT.read_text())
    topics = {p["topic"].upper() for p in data["projects"]}
    assert "AMD" in topics


def test_research_includes_nvda_project() -> None:
    data = json.loads(RESEARCH_INPUT.read_text())
    topics = {p["topic"].upper() for p in data["projects"]}
    assert "NVDA" in topics


def test_watchlist_input_is_valid_json() -> None:
    data = json.loads(WATCHLIST_INPUT.read_text())
    assert isinstance(data, dict)


def test_watchlist_input_has_items() -> None:
    data = json.loads(WATCHLIST_INPUT.read_text())
    assert "items" in data
    assert len(data["items"]) >= 2


def test_watchlist_items_have_ticker() -> None:
    data = json.loads(WATCHLIST_INPUT.read_text())
    for item in data["items"]:
        assert "ticker" in item, f"watchlist item missing 'ticker': {item}"


def test_watchlist_includes_amd_item() -> None:
    data = json.loads(WATCHLIST_INPUT.read_text())
    tickers = {item["ticker"].upper() for item in data["items"]}
    assert "AMD" in tickers


def test_watchlist_includes_nvda_item() -> None:
    data = json.loads(WATCHLIST_INPUT.read_text())
    tickers = {item["ticker"].upper() for item in data["items"]}
    assert "NVDA" in tickers


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


def test_amd_company_analysis_accepts_demo_inputs(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca_out = tmp_path / "ca_amd.json"
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
    assert data[0]["company"]["ticker"] == "AMD"


def test_nvda_company_analysis_accepts_demo_inputs(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca_out = tmp_path / "ca_nvda.json"
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "NVDA",
        "--company-name", "NVIDIA Corporation",
        "--sector", "Semiconductors",
        "--country", "USA",
        "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.",
        "--knowledge", str(KNOWLEDGE),
        "--research", str(research_out),
        "--output", str(ca_out),
    ])
    assert result.exit_code == 0
    data = json.loads(ca_out.read_text())
    assert data[0]["company"]["ticker"] == "NVDA"


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


def test_combined_company_analysis_is_daily_brief_compatible(tmp_path: Path) -> None:
    """Merged AMD+NVDA list is accepted by daily summary --company-analysis."""
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--company-name", "AMD Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "AMD designs high-performance CPUs and GPUs.", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--output", str(ca_amd)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--company-name", "NVIDIA Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--output", str(ca_nvda)])
    combined = json.loads(ca_amd.read_text()) + json.loads(ca_nvda.read_text())
    assert len(combined) == 2
    combined_path = tmp_path / "ca_combined.json"
    combined_path.write_text(json.dumps(combined))
    result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined_path)])
    assert result.exit_code == 0
    assert "Company Analysis Context" in result.stdout


# ── end-to-end two-company pipeline ───────────────────────────────────────────


def _run_full_pipeline(tmp_path: Path) -> tuple:
    research_out = tmp_path / "research.json"
    watchlist_out = tmp_path / "watchlist.json"
    disc_out = tmp_path / "discovery.json"
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    ca_combined = tmp_path / "ca.json"

    r1 = runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    r2 = runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(watchlist_out)])
    r3 = runner.invoke(app, ["discovery", "export", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--watchlist", str(watchlist_out), "--output", str(disc_out)])
    r4 = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--company-name", "AMD Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "AMD designs high-performance CPUs and GPUs.", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--output", str(ca_amd)])
    r5 = runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--company-name", "NVIDIA Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--output", str(ca_nvda)])

    combined = json.loads(ca_amd.read_text()) + json.loads(ca_nvda.read_text())
    ca_combined.write_text(json.dumps(combined))

    daily = runner.invoke(app, [
        "daily", "summary",
        "--research", str(research_out),
        "--watchlist", str(watchlist_out),
        "--discovery", str(disc_out),
        "--company-analysis", str(ca_combined),
    ])
    all_ok = all(r.exit_code == 0 for r in [r1, r2, r3, r4, r5, daily])
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


def test_daily_brief_contains_amd(tmp_path: Path) -> None:
    daily, _ = _run_full_pipeline(tmp_path)
    assert "AMD" in daily.stdout


def test_daily_brief_contains_nvda(tmp_path: Path) -> None:
    daily, _ = _run_full_pipeline(tmp_path)
    assert "NVDA" in daily.stdout


def test_daily_brief_contains_two_company_reports(tmp_path: Path) -> None:
    daily, _ = _run_full_pipeline(tmp_path)
    assert "2 company analysis report(s)" in daily.stdout


def test_daily_brief_no_forbidden_language(tmp_path: Path) -> None:
    daily, _ = _run_full_pipeline(tmp_path)
    output_lower = daily.stdout.lower()
    for term in FORBIDDEN:
        assert term not in output_lower, f"Forbidden term found: {term!r}"


def test_end_to_end_pipeline_is_deterministic(tmp_path: Path) -> None:
    def outputs(d: Path) -> dict:
        r_out = d / "research.json"
        w_out = d / "watchlist.json"
        di_out = d / "discovery.json"
        ca_amd = d / "ca_amd.json"
        ca_nvda = d / "ca_nvda.json"
        runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(r_out)])
        runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(w_out)])
        runner.invoke(app, ["discovery", "export", "--knowledge", str(KNOWLEDGE), "--research", str(r_out), "--watchlist", str(w_out), "--output", str(di_out)])
        runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--company-name", "AMD Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "AMD designs high-performance CPUs and GPUs.", "--knowledge", str(KNOWLEDGE), "--research", str(r_out), "--output", str(ca_amd)])
        runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--company-name", "NVIDIA Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.", "--knowledge", str(KNOWLEDGE), "--research", str(r_out), "--output", str(ca_nvda)])
        return {
            "research": json.loads(r_out.read_text()),
            "discovery": json.loads(di_out.read_text()),
            "ca_amd": json.loads(ca_amd.read_text()),
            "ca_nvda": json.loads(ca_nvda.read_text()),
        }

    tmp1 = tmp_path / "run1"
    tmp2 = tmp_path / "run2"
    tmp1.mkdir()
    tmp2.mkdir()
    assert outputs(tmp1) == outputs(tmp2)


def test_end_to_end_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(yahoo_module, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network call")))
    _, all_ok = _run_full_pipeline(tmp_path)
    assert all_ok


# ── Sprint 66: demo script and documentation asset verification ────────────────

REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "scripts" / "run_daily_brief_demo.sh"
DEMO_README = DEMO_DIR / "README.md"
ROOT_README = REPO_ROOT / "README.md"


def test_demo_script_exists() -> None:
    assert SCRIPT.exists(), f"Demo script not found: {SCRIPT}"


def test_demo_script_uses_atlas_cli() -> None:
    content = SCRIPT.read_text()
    assert "atlas" in content


def test_demo_script_does_not_call_network_tools() -> None:
    content = SCRIPT.read_text()
    assert "curl" not in content
    assert "wget" not in content


def test_demo_script_does_not_use_python_one_liners() -> None:
    content = SCRIPT.read_text()
    assert "python3 -c" not in content
    assert "python -c" not in content


def test_demo_script_has_set_euo_pipefail() -> None:
    content = SCRIPT.read_text()
    assert "set -euo pipefail" in content


def test_demo_script_writes_to_tmp_atlas_demo() -> None:
    content = SCRIPT.read_text()
    assert "tmp/atlas_demo" in content


def test_demo_script_saves_daily_brief_to_file() -> None:
    content = SCRIPT.read_text()
    assert "daily_brief.txt" in content


def test_demo_script_prints_cleanup_instructions() -> None:
    content = SCRIPT.read_text()
    assert "rm -rf" in content


def test_demo_script_handles_missing_atlas_command() -> None:
    content = SCRIPT.read_text()
    assert "command not found" in content or "ERROR" in content


def test_demo_readme_exists() -> None:
    assert DEMO_README.exists()


def test_demo_readme_has_no_api_disclaimer() -> None:
    content = DEMO_README.read_text()
    assert "No external APIs" in content or "external API" in content


def test_demo_readme_has_no_ai_disclaimer() -> None:
    content = DEMO_README.read_text()
    assert "No AI" in content or "no AI" in content


def test_demo_readme_has_cleanup_instructions() -> None:
    content = DEMO_README.read_text()
    assert "rm -rf" in content
    assert "tmp/atlas_demo" in content


def test_demo_readme_has_expected_output_section() -> None:
    content = DEMO_README.read_text()
    assert "Expected Output" in content


def test_demo_readme_expected_output_shows_what_deserves_attention() -> None:
    content = DEMO_README.read_text()
    assert "What Deserves Attention" in content


def test_demo_readme_expected_output_shows_what_can_safely_wait() -> None:
    content = DEMO_README.read_text()
    assert "What Can Safely Wait" in content


def test_demo_readme_expected_output_shows_included_context() -> None:
    content = DEMO_README.read_text()
    assert "Included Context" in content


def test_demo_readme_generated_files_section_lists_daily_brief_txt() -> None:
    content = DEMO_README.read_text()
    assert "daily_brief.txt" in content


def test_demo_readme_no_recommendation_language() -> None:
    # Use a tighter set: bare "buy"/"sell" legitimately appear in disclaimers
    # ("Not a recommendation to buy…"), so only check terms that never belong.
    readme_forbidden = (
        "strong buy", "strong sell", "price target", "outperform",
        "market-beating", "must act", "guaranteed", "risk-free",
    )
    content = DEMO_README.read_text().lower()
    for term in readme_forbidden:
        assert term not in content, f"Forbidden term {term!r} found in demo README"


def test_root_readme_has_quickstart_section() -> None:
    content = ROOT_README.read_text()
    assert "Quickstart" in content


def test_root_readme_quickstart_mentions_demo_script() -> None:
    content = ROOT_README.read_text()
    assert "run_daily_brief_demo.sh" in content


def test_root_readme_quickstart_has_cleanup_instructions() -> None:
    content = ROOT_README.read_text()
    assert "rm -rf tmp/atlas_demo" in content


# ── Sprint 69: portfolio demo integration ──────────────────────────────────────

PORTFOLIO_JSON = DEMO_DIR / "portfolio.json"


def test_demo_portfolio_json_exists() -> None:
    assert PORTFOLIO_JSON.exists(), "examples/daily_brief_demo/portfolio.json not found"


def test_demo_portfolio_json_is_valid() -> None:
    data = json.loads(PORTFOLIO_JSON.read_text())
    assert "positions" in data
    assert len(data["positions"]) > 0


def test_demo_portfolio_has_required_fields() -> None:
    data = json.loads(PORTFOLIO_JSON.read_text())
    required = {"ticker", "company", "sector", "country", "market_cap", "weight",
                "quality_score", "risk_score"}
    for pos in data["positions"]:
        missing = required - pos.keys()
        assert not missing, f"Position missing fields {missing}: {pos}"


def test_demo_portfolio_weights_sum_to_one() -> None:
    data = json.loads(PORTFOLIO_JSON.read_text())
    total = sum(p["weight"] for p in data["positions"])
    assert abs(total - 1.0) < 0.01, f"Portfolio weights sum to {total}, expected ~1.0"


def test_demo_portfolio_triggers_high_concentration() -> None:
    from pathlib import Path as _Path
    from atlas.analysis.portfolio import Portfolio
    from atlas.adapters.portfolio import legacy_portfolio_to_domain_portfolio
    from atlas.domains.portfolio import portfolio_summary
    p = Portfolio.from_json_file(PORTFOLIO_JSON)
    dp = legacy_portfolio_to_domain_portfolio(p)
    s = portfolio_summary(dp)
    assert s.concentration.level.value in {"High", "Elevated"}, (
        f"Expected High/Elevated concentration, got {s.concentration.level.value}"
    )


def test_demo_portfolio_is_accepted_by_daily_summary(tmp_path: Path) -> None:
    result = runner.invoke(app, [
        "daily", "summary",
        "--portfolio", str(PORTFOLIO_JSON),
    ])
    assert result.exit_code == 0
    assert "Portfolio Context" in result.stdout


def test_demo_portfolio_raises_priority_to_high(tmp_path: Path) -> None:
    result = runner.invoke(app, [
        "daily", "summary",
        "--portfolio", str(PORTFOLIO_JSON),
    ])
    assert result.exit_code == 0
    assert "high" in result.stdout.lower()


def test_demo_script_passes_portfolio_flag() -> None:
    content = (REPO_ROOT / "scripts" / "run_daily_brief_demo.sh").read_text()
    assert "--portfolio" in content
    assert "portfolio.json" in content


def test_demo_readme_lists_portfolio_json() -> None:
    content = DEMO_README.read_text()
    assert "portfolio.json" in content


def test_demo_readme_notes_portfolio_is_static_data() -> None:
    content = DEMO_README.read_text().lower()
    assert "static" in content and "portfolio" in content


def test_full_pipeline_with_portfolio_includes_portfolio_context(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    watchlist_out = tmp_path / "watchlist.json"
    disc_out = tmp_path / "discovery.json"
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    ca_combined = tmp_path / "ca.json"

    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--output", str(watchlist_out)])
    runner.invoke(app, ["discovery", "export", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--watchlist", str(watchlist_out), "--output", str(disc_out)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--company-name", "AMD Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "AMD designs high-performance CPUs and GPUs.", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--output", str(ca_amd)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--company-name", "NVIDIA Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--output", str(ca_nvda)])
    combined = json.loads(ca_amd.read_text()) + json.loads(ca_nvda.read_text())
    ca_combined.write_text(json.dumps(combined))

    result = runner.invoke(app, [
        "daily", "summary",
        "--portfolio", str(PORTFOLIO_JSON),
        "--research", str(research_out),
        "--watchlist", str(watchlist_out),
        "--discovery", str(disc_out),
        "--company-analysis", str(ca_combined),
    ])
    assert result.exit_code == 0
    assert "Portfolio Context" in result.stdout
    assert "What Deserves Attention" in result.stdout
    assert "overall priority: high" in result.stdout.lower()


def test_full_pipeline_with_portfolio_no_forbidden_language(tmp_path: Path) -> None:
    result = runner.invoke(app, [
        "daily", "summary",
        "--portfolio", str(PORTFOLIO_JSON),
    ])
    output_lower = result.stdout.lower()
    for term in FORBIDDEN:
        assert term not in output_lower, f"Forbidden term {term!r} in portfolio output"


# ── Sprint 70: evidence link resolution ────────────────────────────────────────

from atlas.adapters.watchlist import assign_knowledge_facts, _node_id_matches_ticker, watchlist_input_from_dict  # noqa: E402
from atlas.adapters.knowledge import knowledge_facts_from_dict  # noqa: E402
from atlas.capabilities.watchlist_intelligence.engine import WatchlistIntelligenceEngine  # noqa: E402


def test_node_id_matches_ticker_exact() -> None:
    assert _node_id_matches_ticker("AMD", "AMD")


def test_node_id_matches_ticker_company_pattern_amd() -> None:
    assert _node_id_matches_ticker("company-amd", "AMD")


def test_node_id_matches_ticker_company_pattern_nvda() -> None:
    assert _node_id_matches_ticker("company-nvda", "NVDA")


def test_node_id_does_not_match_wrong_ticker() -> None:
    assert not _node_id_matches_ticker("company-amd", "NVDA")


def test_node_id_does_not_match_unrelated() -> None:
    assert not _node_id_matches_ticker("sector-semiconductors", "AMD")


def test_assign_knowledge_facts_populates_amd() -> None:
    raw = {"name": "W", "items": [{"ticker": "AMD"}]}
    wi_input = watchlist_input_from_dict(raw)
    knowledge = knowledge_facts_from_dict(json.loads(KNOWLEDGE.read_text()), str(KNOWLEDGE))
    result = assign_knowledge_facts(wi_input, knowledge)
    amd_item = result.items[0]
    assert len(amd_item.knowledge_facts) > 0
    assert all(f.subject_node_id == "company-amd" for f in amd_item.knowledge_facts)


def test_assign_knowledge_facts_populates_nvda() -> None:
    raw = {"name": "W", "items": [{"ticker": "NVDA"}]}
    wi_input = watchlist_input_from_dict(raw)
    knowledge = knowledge_facts_from_dict(json.loads(KNOWLEDGE.read_text()), str(KNOWLEDGE))
    result = assign_knowledge_facts(wi_input, knowledge)
    nvda_item = result.items[0]
    assert len(nvda_item.knowledge_facts) > 0
    assert all(f.subject_node_id == "company-nvda" for f in nvda_item.knowledge_facts)


def test_amd_facts_do_not_attach_to_nvda() -> None:
    raw = {"name": "W", "items": [{"ticker": "NVDA"}]}
    wi_input = watchlist_input_from_dict(raw)
    knowledge = knowledge_facts_from_dict(json.loads(KNOWLEDGE.read_text()), str(KNOWLEDGE))
    result = assign_knowledge_facts(wi_input, knowledge)
    nvda_item = result.items[0]
    assert not any(f.subject_node_id == "company-amd" for f in nvda_item.knowledge_facts)


def test_nvda_facts_do_not_attach_to_amd() -> None:
    raw = {"name": "W", "items": [{"ticker": "AMD"}]}
    wi_input = watchlist_input_from_dict(raw)
    knowledge = knowledge_facts_from_dict(json.loads(KNOWLEDGE.read_text()), str(KNOWLEDGE))
    result = assign_knowledge_facts(wi_input, knowledge)
    amd_item = result.items[0]
    assert not any(f.subject_node_id == "company-nvda" for f in amd_item.knowledge_facts)


def test_assign_knowledge_empty_facts_no_change() -> None:
    raw = {"name": "W", "items": [{"ticker": "AMD"}]}
    wi_input = watchlist_input_from_dict(raw)
    result = assign_knowledge_facts(wi_input, [])
    assert result.items[0].knowledge_facts == ()


def test_watchlist_intelligence_with_knowledge_no_false_negative() -> None:
    raw = json.loads(WATCHLIST_INPUT.read_text())
    wi_input = watchlist_input_from_dict(raw)
    knowledge = knowledge_facts_from_dict(json.loads(KNOWLEDGE.read_text()), str(KNOWLEDGE))
    wi_input = assign_knowledge_facts(wi_input, knowledge)
    report = WatchlistIntelligenceEngine().analyze(wi_input)
    for step in report.suggested_next_research_steps:
        assert "No knowledge facts are linked" not in step, (
            f"False-negative step still present: {step!r}"
        )


def test_watchlist_cli_knowledge_flag(tmp_path: Path) -> None:
    out = tmp_path / "watchlist.json"
    result = runner.invoke(app, [
        "watchlist", "intelligence",
        "--input", str(WATCHLIST_INPUT),
        "--knowledge", str(KNOWLEDGE),
        "--output", str(out),
    ])
    assert result.exit_code == 0, result.stdout
    assert out.exists()
    data = json.loads(out.read_text())
    steps = data.get("suggested_next_research_steps", [])
    for step in steps:
        assert "No knowledge facts are linked" not in step, (
            f"False-negative still in CLI output: {step!r}"
        )


def test_full_pipeline_with_knowledge_no_false_negative(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    watchlist_out = tmp_path / "watchlist.json"
    disc_out = tmp_path / "discovery.json"
    ca_amd = tmp_path / "ca_amd.json"
    ca_nvda = tmp_path / "ca_nvda.json"
    ca_combined = tmp_path / "ca_combined.json"

    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--knowledge", str(KNOWLEDGE), "--output", str(watchlist_out)])
    runner.invoke(app, ["discovery", "export", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--watchlist", str(watchlist_out), "--output", str(disc_out)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--company-name", "AMD Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "AMD designs high-performance CPUs and GPUs.", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--output", str(ca_amd)])
    runner.invoke(app, ["company-analysis", "export", "--ticker", "NVDA", "--company-name", "NVIDIA Corporation", "--sector", "Semiconductors", "--country", "USA", "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.", "--knowledge", str(KNOWLEDGE), "--research", str(research_out), "--output", str(ca_nvda)])
    combined = json.loads(ca_amd.read_text()) + json.loads(ca_nvda.read_text())
    ca_combined.write_text(json.dumps(combined))

    result = runner.invoke(app, [
        "daily", "summary",
        "--portfolio", str(PORTFOLIO_JSON),
        "--research", str(research_out),
        "--watchlist", str(watchlist_out),
        "--discovery", str(disc_out),
        "--company-analysis", str(ca_combined),
    ])
    assert result.exit_code == 0
    assert "No knowledge facts are linked" not in result.stdout


def test_full_pipeline_deterministic_with_knowledge(tmp_path: Path) -> None:
    research_out = tmp_path / "research.json"
    watchlist_out = tmp_path / "watchlist.json"

    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    runner.invoke(app, ["watchlist", "intelligence", "--input", str(WATCHLIST_INPUT), "--knowledge", str(KNOWLEDGE), "--output", str(watchlist_out)])

    result1 = runner.invoke(app, ["daily", "summary", "--research", str(research_out), "--watchlist", str(watchlist_out)])
    result2 = runner.invoke(app, ["daily", "summary", "--research", str(research_out), "--watchlist", str(watchlist_out)])
    assert result1.stdout == result2.stdout


def test_demo_script_passes_knowledge_to_watchlist() -> None:
    script = Path("scripts/run_daily_brief_demo.sh").read_text()
    assert "--knowledge" in script
    lines = [l for l in script.splitlines() if "watchlist intelligence" in l or "--knowledge" in l]
    found = False
    in_watchlist_block = False
    for line in script.splitlines():
        if "watchlist intelligence" in line:
            in_watchlist_block = True
        if in_watchlist_block and "--knowledge" in line:
            found = True
            break
        if in_watchlist_block and line.strip() and not line.strip().startswith("#") and "--knowledge" not in line and "watchlist" not in line and "--input" not in line and "--output" not in line and "echo" not in line:
            in_watchlist_block = False
    assert found, "Demo script Step 2 does not pass --knowledge to watchlist intelligence"
