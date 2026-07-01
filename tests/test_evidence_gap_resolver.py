"""Sprint 61: Daily Brief Evidence Gap resolver tests.

Verifies that evidence gaps are:
- scoped per company (AMD gaps do not appear as NVDA gaps and vice versa)
- derived from company analysis unknowns, not from evidence_links
- empty when all evidence is linked (full metadata + knowledge facts)
- present only when evidence is genuinely missing
- deterministic
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from atlas.capabilities.daily_brief.engine import DailyBriefCapability, _build_evidence_gaps
from atlas.capabilities.daily_brief.models import DailyBriefInput
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


# ── helpers ────────────────────────────────────────────────────────────────────


def _make_company(ticker: str) -> object:
    return SimpleNamespace(ticker=ticker, name=ticker, id=ticker.lower())


def _make_unknown(title: str, detail: str = "") -> object:
    return SimpleNamespace(title=title, detail=detail)


def _make_evidence_link(id: str, description: str) -> object:
    return SimpleNamespace(id=id, description=description, source="test")


def _make_report(
    ticker: str,
    unknowns: list = (),
    evidence_links: list = (),
) -> object:
    return SimpleNamespace(
        company=_make_company(ticker),
        unknowns=list(unknowns),
        evidence_links=list(evidence_links),
    )


def _brief_with_reports(*reports) -> DailyBriefInput:
    return DailyBriefInput(company_reports=tuple(reports))


# ── evidence_links are NOT gaps ────────────────────────────────────────────────


def test_evidence_links_do_not_appear_as_gaps() -> None:
    """A confirmed evidence link should never surface as an evidence gap."""
    report = _make_report(
        "AMD",
        unknowns=[],
        evidence_links=[_make_evidence_link("knowledge:amd-k1", "AMD designs CPUs.")],
    )
    data = _brief_with_reports(report)
    gaps = _build_evidence_gaps(data)
    assert gaps == []


def test_evidence_links_from_multiple_companies_do_not_appear_as_gaps() -> None:
    amd = _make_report("AMD", evidence_links=[_make_evidence_link("knowledge:amd-k1", "AMD fact.")])
    nvda = _make_report("NVDA", evidence_links=[_make_evidence_link("knowledge:nvda-k1", "NVDA fact.")])
    gaps = _build_evidence_gaps(_brief_with_reports(amd, nvda))
    assert gaps == []


# ── missing evidence unknowns ARE gaps ────────────────────────────────────────


def test_missing_evidence_unknown_surfaces_as_gap() -> None:
    report = _make_report(
        "AMD",
        unknowns=[_make_unknown("Missing Evidence", "No knowledge facts were supplied.")],
    )
    gaps = _build_evidence_gaps(_brief_with_reports(report))
    assert len(gaps) == 1
    assert gaps[0].ticker == "AMD"
    assert "knowledge facts" in gaps[0].description.lower() or "evidence" in gaps[0].description.lower()


def test_gap_uses_unknown_detail_as_description() -> None:
    detail = "No knowledge facts were supplied."
    report = _make_report("AMD", unknowns=[_make_unknown("Missing Evidence", detail)])
    gaps = _build_evidence_gaps(_brief_with_reports(report))
    assert gaps[0].description == detail


def test_gap_falls_back_to_title_when_no_detail() -> None:
    report = _make_report("AMD", unknowns=[_make_unknown("Missing Evidence")])
    gaps = _build_evidence_gaps(_brief_with_reports(report))
    assert "Missing Evidence" in gaps[0].description or gaps[0].description


# ── company scoping ────────────────────────────────────────────────────────────


def test_amd_gaps_scoped_to_amd() -> None:
    amd = _make_report("AMD", unknowns=[_make_unknown("Missing Evidence", "No AMD facts.")])
    nvda = _make_report("NVDA", unknowns=[])
    gaps = _build_evidence_gaps(_brief_with_reports(amd, nvda))
    assert all(g.ticker == "AMD" for g in gaps)


def test_nvda_gaps_scoped_to_nvda() -> None:
    amd = _make_report("AMD", unknowns=[])
    nvda = _make_report("NVDA", unknowns=[_make_unknown("Missing Evidence", "No NVDA facts.")])
    gaps = _build_evidence_gaps(_brief_with_reports(amd, nvda))
    assert all(g.ticker == "NVDA" for g in gaps)


def test_amd_evidence_links_do_not_become_nvda_gaps() -> None:
    """Core company-scoping test: AMD's evidence facts must not appear as NVDA gaps."""
    amd = _make_report("AMD", evidence_links=[
        _make_evidence_link("knowledge:amd-k1", "AMD designs CPUs."),
        _make_evidence_link("knowledge:nvda-k1", "NVDA designs GPUs."),  # shared knowledge
    ])
    nvda = _make_report("NVDA", evidence_links=[
        _make_evidence_link("knowledge:nvda-k1", "NVDA designs GPUs."),
    ])
    gaps = _build_evidence_gaps(_brief_with_reports(amd, nvda))
    descriptions = [g.description for g in gaps]
    assert "AMD designs CPUs." not in descriptions
    assert "NVDA designs GPUs." not in descriptions
    assert gaps == []


def test_two_companies_both_with_missing_evidence() -> None:
    amd = _make_report("AMD", unknowns=[_make_unknown("Missing Evidence", "No AMD facts.")])
    nvda = _make_report("NVDA", unknowns=[_make_unknown("Missing Evidence", "No NVDA facts.")])
    gaps = _build_evidence_gaps(_brief_with_reports(amd, nvda))
    tickers = {g.ticker for g in gaps}
    assert "AMD" in tickers
    assert "NVDA" in tickers


# ── metadata unknowns are NOT evidence gaps ───────────────────────────────────


def test_missing_sector_unknown_is_not_an_evidence_gap() -> None:
    report = _make_report("AMD", unknowns=[_make_unknown("Missing Sector", "Sector is not available.")])
    gaps = _build_evidence_gaps(_brief_with_reports(report))
    assert gaps == []


def test_missing_country_unknown_is_not_an_evidence_gap() -> None:
    report = _make_report("AMD", unknowns=[_make_unknown("Missing Country", "Country is not available.")])
    gaps = _build_evidence_gaps(_brief_with_reports(report))
    assert gaps == []


def test_missing_business_description_unknown_is_not_an_evidence_gap() -> None:
    report = _make_report("AMD", unknowns=[_make_unknown("Missing Business Description", "No description.")])
    gaps = _build_evidence_gaps(_brief_with_reports(report))
    assert gaps == []


# ── full metadata + knowledge → no evidence gaps ──────────────────────────────


def test_full_metadata_and_knowledge_produce_no_evidence_gaps(tmp_path: Path) -> None:
    """When all metadata and knowledge facts are supplied, no evidence gaps should appear."""
    research_out = tmp_path / "research.json"
    runner.invoke(app, ["research", "export", "--input", str(RESEARCH_INPUT), "--output", str(research_out)])
    ca_amd = tmp_path / "ca_amd.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD", "--company-name", "AMD Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_amd),
    ])
    ca_nvda = tmp_path / "ca_nvda.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "NVDA", "--company-name", "NVIDIA Corporation",
        "--sector", "Semiconductors", "--country", "USA",
        "--business-description", "NVIDIA designs GPUs and accelerated computing platforms.",
        "--knowledge", str(KNOWLEDGE), "--research", str(research_out),
        "--output", str(ca_nvda),
    ])
    combined = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(ca_amd), "--inputs", str(ca_nvda),
        "--output", str(combined),
    ])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(combined)])
    assert daily.exit_code == 0
    assert "Evidence Gaps" not in daily.stdout


def test_ticker_only_produces_missing_evidence_gap(tmp_path: Path) -> None:
    """Without knowledge facts the engine emits Missing Evidence — should appear as gap."""
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert daily.exit_code == 0
    assert "Evidence Gaps" in daily.stdout
    assert "AMD" in daily.stdout


# ── determinism ────────────────────────────────────────────────────────────────


def test_evidence_gap_resolution_is_deterministic(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    d1 = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    d2 = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert d1.stdout == d2.stdout


# ── no network / no recommendation ────────────────────────────────────────────


def test_evidence_gap_resolution_no_network(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(yahoo_module, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    assert daily.exit_code == 0


def test_evidence_gap_output_no_forbidden_language(tmp_path: Path) -> None:
    ca = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(ca)])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(ca)])
    output_lower = daily.stdout.lower()
    for term in FORBIDDEN:
        assert term not in output_lower, f"Forbidden term: {term!r}"
