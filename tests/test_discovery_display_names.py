"""Sprint 72: Discovery Context display name resolver tests.

Verifies that _resolve_node_display_name follows the deterministic resolution
order and that the Daily Brief Discovery Context uses readable names rather
than raw node IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from atlas.capabilities.daily_brief.engine import _resolve_node_display_name


# ── unit tests for _resolve_node_display_name ──────────────────────────────────

@dataclass
class _Candidate:
    identifier: str = ""
    title: str = ""
    ticker: str = ""


def test_explicit_title_preferred_over_identifier() -> None:
    c = _Candidate(identifier="company-amd", title="AMD Corporation")
    assert _resolve_node_display_name(c) == "AMD Corporation"


def test_explicit_title_preferred_over_ticker() -> None:
    c = _Candidate(identifier="company-amd", title="AMD Corporation", ticker="AMD")
    assert _resolve_node_display_name(c) == "AMD Corporation"


def test_ticker_used_when_title_empty() -> None:
    c = _Candidate(identifier="company-amd", title="", ticker="AMD")
    assert _resolve_node_display_name(c) == "AMD"


def test_company_node_pattern_amd() -> None:
    c = _Candidate(identifier="company-amd", title="", ticker="")
    assert _resolve_node_display_name(c) == "AMD"


def test_company_node_pattern_nvda() -> None:
    c = _Candidate(identifier="company-nvda", title="", ticker="")
    assert _resolve_node_display_name(c) == "NVDA"


def test_company_node_pattern_uppercases() -> None:
    c = _Candidate(identifier="company-tsla", title="", ticker="")
    assert _resolve_node_display_name(c) == "TSLA"


def test_unknown_node_id_falls_back_to_identifier() -> None:
    c = _Candidate(identifier="theme:semiconductors", title="", ticker="")
    assert _resolve_node_display_name(c) == "theme:semiconductors"


def test_ambiguous_compound_company_node_falls_back_to_identifier() -> None:
    # company-some-thing has a hyphen in suffix — ambiguous, fall back
    c = _Candidate(identifier="company-some-thing", title="", ticker="")
    assert _resolve_node_display_name(c) == "company-some-thing"


def test_empty_title_treated_as_missing() -> None:
    c = _Candidate(identifier="company-amd", title="   ", ticker="")
    assert _resolve_node_display_name(c) == "AMD"


def test_empty_ticker_treated_as_missing() -> None:
    c = _Candidate(identifier="company-nvda", title="", ticker="   ")
    assert _resolve_node_display_name(c) == "NVDA"


def test_no_identifier_returns_unknown() -> None:
    c = _Candidate(identifier="", title="", ticker="")
    result = _resolve_node_display_name(c)
    assert result == "Unknown" or result == ""


# ── integration: demo output ───────────────────────────────────────────────────

DEMO_DIR = Path(__file__).parent.parent / "examples" / "daily_brief_demo"
KNOWLEDGE = DEMO_DIR / "knowledge.json"
WATCHLIST_INPUT = DEMO_DIR / "watchlist_input.json"
RESEARCH_INPUT = DEMO_DIR / "research_input.json"
PORTFOLIO_JSON = DEMO_DIR / "portfolio.json"

from typer.testing import CliRunner
from atlas.cli.main import app
import json

runner = CliRunner()


def _run_full_pipeline(tmp_path: Path) -> str:
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
    return result.stdout


def test_discovery_context_no_raw_company_amd(tmp_path: Path) -> None:
    output = _run_full_pipeline(tmp_path)
    assert "company-amd" not in output


def test_discovery_context_no_raw_company_nvda(tmp_path: Path) -> None:
    output = _run_full_pipeline(tmp_path)
    assert "company-nvda" not in output


def test_discovery_context_shows_amd(tmp_path: Path) -> None:
    output = _run_full_pipeline(tmp_path)
    assert "AMD" in output


def test_discovery_context_shows_nvda(tmp_path: Path) -> None:
    output = _run_full_pipeline(tmp_path)
    assert "NVDA" in output


def test_discovery_context_deterministic(tmp_path: Path) -> None:
    out1 = _run_full_pipeline(tmp_path)
    out2 = _run_full_pipeline(tmp_path)
    assert out1 == out2


def test_no_recommendation_language(tmp_path: Path) -> None:
    output = _run_full_pipeline(tmp_path).lower()
    for term in ("strong buy", "price target", "outperform", "must act", "guaranteed", "risk-free"):
        assert term not in output, f"Forbidden term {term!r} in output"
