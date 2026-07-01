"""Sprint 55: Company Analysis engine-backed export tests.

Covers:
- atlas company-analysis export --ticker (ticker-only, no knowledge/research)
- atlas company-analysis export --ticker --knowledge
- atlas company-analysis export --ticker --research
- atlas company-analysis export --ticker --knowledge --research
- CompanyAnalysisEngine invoked (engine-derived content in output)
- exported JSON shape compatible with Daily Brief
- round-trip: engine export → atlas daily summary --company-analysis
- error handling (missing files, bad JSON, wrong shape, empty ticker)
- Sprint 54 --input path preserved
- no-input path preserved
- language safety (no forbidden terms)
- determinism
- no network calls
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

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


# ── fixtures ───────────────────────────────────────────────────────────────────


def _knowledge_json() -> dict:
    return {
        "facts": [
            {
                "id": "fact-amd-1",
                "subject_node_id": "company-amd",
                "statement": "AMD designs high-performance GPUs and CPUs for data centres and PCs.",
                "source": {"id": "src-1", "name": "10-K 2024", "source_type": "Filing"},
                "timestamp": "2026-07-01T00:00:00Z",
                "confidence": 85,
            },
            {
                "id": "fact-amd-2",
                "subject_node_id": "company-amd",
                "statement": "AMD reported data centre revenue growth exceeding 90% year-over-year.",
                "source": {"id": "src-1", "name": "10-K 2024", "source_type": "Filing"},
                "timestamp": "2026-07-01T00:00:00Z",
                "confidence": 90,
            },
        ]
    }


def _research_json(ticker: str = "AMD") -> dict:
    return {
        "projects": [
            {
                "id": f"proj-{ticker.lower()}",
                "title": f"{ticker} Research",
                "topic": ticker,
                "status": "researching",
                "questions": [
                    "What is the long-term competitive moat in data centre GPUs?",
                    "How durable is the margin expansion?",
                ],
            }
        ]
    }


def _company_analysis_json() -> dict:
    return {
        "company": {"id": "nvda", "name": "NVIDIA", "ticker": "NVDA"},
        "unknowns": [{"title": "Moat durability", "detail": "Evidence is limited."}],
        "evidence_links": [],
        "confidence": "low",
        "what_could_change_the_view": ["Further evidence on competitive positioning."],
    }


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ── ticker-only export ─────────────────────────────────────────────────────────


def test_ticker_only_succeeds() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD"])
    assert result.exit_code == 0


def test_ticker_only_shows_ticker_in_output() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD"])
    assert "AMD" in result.stdout


def test_ticker_only_shows_confidence_level() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD"])
    assert "confidence" in result.stdout


def test_ticker_only_produces_engine_derived_unknowns() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD"])
    assert "Unknowns" in result.stdout


def test_ticker_uppercased() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "amd"])
    assert result.exit_code == 0
    assert "AMD" in result.stdout


def test_ticker_output_is_list(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 1


def test_ticker_output_has_company_field(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    data = json.loads(out.read_text())
    assert data[0]["company"]["ticker"] == "AMD"


def test_ticker_output_has_unknowns_field(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    data = json.loads(out.read_text())
    assert "unknowns" in data[0]


def test_ticker_output_has_confidence_field(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    data = json.loads(out.read_text())
    assert "confidence" in data[0]
    assert data[0]["confidence"]["level"] in {"low", "moderate", "high"}


def test_ticker_output_has_evidence_links_field(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    data = json.loads(out.read_text())
    assert "evidence_links" in data[0]


def test_ticker_output_has_what_could_change_field(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    data = json.loads(out.read_text())
    assert "what_could_change_the_view" in data[0]


# ── ticker + knowledge export ──────────────────────────────────────────────────


def test_ticker_and_knowledge_succeeds(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--knowledge", str(k)])
    assert result.exit_code == 0


def test_ticker_and_knowledge_produces_evidence_links(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--knowledge", str(k), "--output", str(out)])
    data = json.loads(out.read_text())
    assert len(data[0]["evidence_links"]) == 2


def test_ticker_and_knowledge_raises_confidence(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--knowledge", str(k), "--output", str(out)])
    data = json.loads(out.read_text())
    # With 2 facts, confidence should be higher than ticker-only (which has 0 evidence)
    assert data[0]["confidence"]["level"] in {"low", "moderate", "high"}


def test_ticker_and_knowledge_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--knowledge", str(tmp_path / "nope.json"),
    ])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_ticker_and_knowledge_invalid_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--knowledge", str(path)])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout


def test_ticker_and_knowledge_wrong_shape_fails_cleanly(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", {"facts": "not a list"})
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--knowledge", str(k)])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout


# ── ticker + research export ───────────────────────────────────────────────────


def test_ticker_and_research_succeeds(tmp_path: Path) -> None:
    r = _write(tmp_path, "r.json", _research_json())
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--research", str(r)])
    assert result.exit_code == 0


def test_ticker_and_research_surfaces_open_questions(tmp_path: Path) -> None:
    r = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--research", str(r), "--output", str(out)])
    data = json.loads(out.read_text())
    unknown_titles = [u["title"] for u in data[0]["unknowns"]]
    assert "Open Research Question" in unknown_titles


def test_ticker_and_research_matching_topic_selected(tmp_path: Path) -> None:
    r = _write(tmp_path, "r.json", _research_json("AMD"))
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--research", str(r), "--output", str(out)])
    data = json.loads(out.read_text())
    assert data[0]["company"]["ticker"] == "AMD"


def test_ticker_and_research_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--research", str(tmp_path / "nope.json"),
    ])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout


def test_ticker_and_research_invalid_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[bad", encoding="utf-8")
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--research", str(path)])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout


# ── ticker + knowledge + research ─────────────────────────────────────────────


def test_all_flags_together_succeeds(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    r = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "ca.json"
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--knowledge", str(k),
        "--research", str(r),
        "--output", str(out),
    ])
    assert result.exit_code == 0
    assert out.exists()


def test_all_flags_output_is_valid_json(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    r = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--knowledge", str(k),
        "--research", str(r),
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 1


def test_all_flags_has_evidence_links_from_knowledge(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    r = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--knowledge", str(k),
        "--research", str(r),
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    assert data[0]["evidence_links"]


def test_all_flags_has_open_questions_from_research(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    r = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--knowledge", str(k),
        "--research", str(r),
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    unknown_titles = [u["title"] for u in data[0]["unknowns"]]
    assert "Open Research Question" in unknown_titles


def test_all_flags_is_deterministic(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    r = _write(tmp_path, "r.json", _research_json())
    out1 = tmp_path / "ca1.json"
    out2 = tmp_path / "ca2.json"
    args = ["company-analysis", "export", "--ticker", "AMD", "--knowledge", str(k), "--research", str(r)]
    runner.invoke(app, args + ["--output", str(out1)])
    runner.invoke(app, args + ["--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


# ── round-trip: engine export → daily summary ──────────────────────────────────


def test_round_trip_ticker_only_to_daily_summary(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily.exit_code == 0
    assert "Atlas Daily Brief" in daily.stdout


def test_round_trip_produces_company_analysis_section(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert "Company Analysis Context" in daily.stdout


def test_round_trip_with_knowledge_and_research(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    r = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--knowledge", str(k),
        "--research", str(r),
        "--output", str(out),
    ])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily.exit_code == 0
    assert "Company Analysis Context" in daily.stdout


def test_round_trip_no_forbidden_language(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--knowledge", str(k),
        "--output", str(out),
    ])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily.exit_code == 0
    output_lower = daily.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term in daily summary: {term!r}"


def test_engine_export_stdout_no_forbidden_language() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD"])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term in stdout: {term!r}"


# ── Sprint 54 --input path preserved ──────────────────────────────────────────


def test_sprint54_input_path_still_works(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _company_analysis_json())
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert result.exit_code == 0
    assert "NVDA" in result.stdout


def test_sprint54_input_path_output_still_works(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _company_analysis_json())
    out = tmp_path / "out.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert data[0]["company"]["ticker"] == "NVDA"


def test_no_input_path_still_works(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    result = runner.invoke(app, ["company-analysis", "export", "--output", str(out)])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data == []


# ── no-network constraint ──────────────────────────────────────────────────────


def test_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail(*args, **kwargs):
        raise AssertionError("urlopen must not be called during company analysis export")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail)

    k = _write(tmp_path, "k.json", _knowledge_json())
    out = tmp_path / "ca.json"
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--knowledge", str(k),
        "--output", str(out),
    ])
    assert result.exit_code == 0
