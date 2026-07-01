"""Sprint 54: Company Analysis export tests.

Covers:
- company_reports_from_dict adapter unit tests
- company_report_to_dict / company_reports_to_list exporter unit tests
- atlas company-analysis export CLI (no input, --input, --output)
- error handling (missing file, bad JSON, wrong shape, bad confidence)
- round-trip: company analysis export → atlas daily summary --company-analysis
- language safety (no forbidden recommendation language)
- determinism and no-network constraints
- architecture boundary: no provider calls
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.adapters.company_analysis import company_reports_from_dict
from atlas.capabilities.company_analysis.exporter import (
    company_report_to_dict,
    company_reports_to_list,
)
from atlas.capabilities.company_analysis.models import (
    CompanyAnalysisConfidence,
    CompanyAnalysisEvidenceLink,
    CompanyAnalysisReport,
    CompanyAnalysisSection,
    CompanyAnalysisUnknown,
)
from atlas.cli.main import app
from atlas.shared import Company

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


def _single_report_json() -> dict:
    return {
        "company": {
            "id": "amd",
            "name": "AMD Corporation",
            "ticker": "AMD",
            "sector": "Semiconductors",
            "country": "USA",
        },
        "unknowns": [
            {
                "title": "Competitive moat durability",
                "detail": "Evidence on long-term moat durability is limited.",
            },
            {
                "title": "Margin trajectory",
                "detail": "Gross margin trajectory under competitive pressure is unresolved.",
            },
        ],
        "evidence_links": [
            {
                "id": "ev-1",
                "source": "10-K 2024",
                "description": "Revenue breakdown by segment shows data centre growth.",
            },
        ],
        "confidence": {
            "level": "low",
            "explanation": "Confidence is low because evidence is limited.",
            "drivers": ["Company name and ticker known"],
            "limitations": ["No knowledge facts supplied", "Competitive position unresolved"],
        },
        "what_could_change_the_view": [
            "Evidence on durable competitive advantages.",
            "Margin trajectory data over multiple cycles.",
        ],
    }


def _multi_report_json() -> list:
    amd = _single_report_json()
    asml = {
        "company": {"id": "asml", "name": "ASML Holding", "ticker": "ASML", "sector": "Semiconductors"},
        "unknowns": [{"title": "EUV adoption pace", "detail": "Adoption rate remains uncertain."}],
        "evidence_links": [],
        "confidence": "moderate",
        "what_could_change_the_view": ["EUV shipment data from annual reports."],
    }
    return [amd, asml]


def _make_report() -> CompanyAnalysisReport:
    return company_reports_from_dict(_single_report_json())[0]


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ── adapter unit tests ─────────────────────────────────────────────────────────


def test_adapter_single_dict_produces_one_report() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert len(reports) == 1


def test_adapter_list_produces_multiple_reports() -> None:
    reports = company_reports_from_dict(_multi_report_json())
    assert len(reports) == 2


def test_adapter_company_name_preserved() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert reports[0].company.name == "AMD Corporation"


def test_adapter_company_ticker_uppercased() -> None:
    reports = company_reports_from_dict({"company": {"name": "AMD", "ticker": "amd"}})
    assert reports[0].company.ticker == "AMD"


def test_adapter_company_sector_preserved() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert reports[0].company.sector == "Semiconductors"


def test_adapter_unknowns_parsed() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert len(reports[0].unknowns) == 2


def test_adapter_unknown_title_preserved() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert reports[0].unknowns[0].title == "Competitive moat durability"


def test_adapter_evidence_links_parsed() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert len(reports[0].evidence_links) == 1


def test_adapter_evidence_link_source_preserved() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert reports[0].evidence_links[0].source == "10-K 2024"


def test_adapter_confidence_dict_level_preserved() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert reports[0].confidence.level == "low"


def test_adapter_confidence_string_form_accepted() -> None:
    data = {"company": {"name": "ASML", "ticker": "ASML"}, "confidence": "moderate"}
    reports = company_reports_from_dict(data)
    assert reports[0].confidence.level == "moderate"


def test_adapter_what_could_change_preserved() -> None:
    reports = company_reports_from_dict(_single_report_json())
    assert "Evidence on durable competitive advantages." in reports[0].what_could_change_the_view


def test_adapter_missing_name_and_ticker_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must have at least"):
        company_reports_from_dict({"company": {"id": "x"}})


def test_adapter_invalid_confidence_level_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="Invalid confidence level"):
        company_reports_from_dict({"company": {"ticker": "AMD"}, "confidence": {"level": "extreme"}})


def test_adapter_invalid_confidence_string_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be one of"):
        company_reports_from_dict({"company": {"ticker": "AMD"}, "confidence": "very high"})


def test_adapter_non_dict_non_list_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be a JSON object or list"):
        company_reports_from_dict("not a dict")


def test_adapter_report_not_dict_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be a JSON object"):
        company_reports_from_dict(["not a dict"])


def test_adapter_company_not_dict_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be a JSON object"):
        company_reports_from_dict({"company": "AMD"})


def test_adapter_empty_list_produces_empty_tuple() -> None:
    assert company_reports_from_dict([]) == ()


def test_adapter_unknowns_not_list_fails_cleanly() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        company_reports_from_dict({"company": {"ticker": "AMD"}, "unknowns": "not a list"})


# ── exporter unit tests ────────────────────────────────────────────────────────


def test_exporter_returns_dict() -> None:
    assert isinstance(company_report_to_dict(_make_report()), dict)


def test_exporter_company_key_present() -> None:
    result = company_report_to_dict(_make_report())
    assert "company" in result


def test_exporter_unknowns_key_present() -> None:
    result = company_report_to_dict(_make_report())
    assert "unknowns" in result


def test_exporter_evidence_links_key_present() -> None:
    result = company_report_to_dict(_make_report())
    assert "evidence_links" in result


def test_exporter_confidence_key_present() -> None:
    result = company_report_to_dict(_make_report())
    assert "confidence" in result


def test_exporter_what_could_change_key_present() -> None:
    result = company_report_to_dict(_make_report())
    assert "what_could_change_the_view" in result


def test_exporter_company_ticker_preserved() -> None:
    result = company_report_to_dict(_make_report())
    assert result["company"]["ticker"] == "AMD"


def test_exporter_unknowns_count_matches() -> None:
    result = company_report_to_dict(_make_report())
    assert len(result["unknowns"]) == 2


def test_exporter_evidence_links_count_matches() -> None:
    result = company_report_to_dict(_make_report())
    assert len(result["evidence_links"]) == 1


def test_exporter_confidence_level_preserved() -> None:
    result = company_report_to_dict(_make_report())
    assert result["confidence"]["level"] == "low"


def test_exporter_is_json_serialisable() -> None:
    result = company_report_to_dict(_make_report())
    assert json.dumps(result)


def test_exporter_list_returns_list() -> None:
    reports = company_reports_from_dict(_multi_report_json())
    result = company_reports_to_list(reports)
    assert isinstance(result, list)
    assert len(result) == 2


def test_exporter_empty_tuple_returns_empty_list() -> None:
    assert company_reports_to_list(()) == []


def test_exporter_is_deterministic() -> None:
    report = _make_report()
    assert company_report_to_dict(report) == company_report_to_dict(report)


# ── CLI: no-input mode ─────────────────────────────────────────────────────────


def test_cli_no_input_succeeds() -> None:
    result = runner.invoke(app, ["company-analysis", "export"])
    assert result.exit_code == 0


def test_cli_no_input_prints_header() -> None:
    result = runner.invoke(app, ["company-analysis", "export"])
    assert "Company Analysis Export" in result.stdout


def test_cli_no_input_reports_no_data() -> None:
    result = runner.invoke(app, ["company-analysis", "export"])
    assert "No company analysis inputs provided" in result.stdout


# ── CLI: --input flag ──────────────────────────────────────────────────────────


def test_cli_input_flag_single_report_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert result.exit_code == 0


def test_cli_input_flag_shows_company(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert "AMD" in result.stdout


def test_cli_input_flag_shows_confidence(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert "low" in result.stdout


def test_cli_input_flag_multi_report_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _multi_report_json())
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert result.exit_code == 0


def test_cli_input_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(tmp_path / "nope.json")])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_cli_input_invalid_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout


def test_cli_input_wrong_shape_fails_cleanly(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", "not a dict")
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout


def test_cli_input_invalid_confidence_fails_cleanly(tmp_path: Path) -> None:
    data = {"company": {"ticker": "AMD"}, "confidence": {"level": "very_high"}}
    path = _write(tmp_path, "ca.json", data)
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert result.exit_code == 1
    assert "Company analysis export failed" in result.stdout


# ── CLI: --output flag ─────────────────────────────────────────────────────────


def test_cli_output_flag_creates_file(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_cli_output_flag_is_valid_json(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 1


def test_cli_output_report_has_company_field(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert "company" in data[0]
    assert data[0]["company"]["ticker"] == "AMD"


def test_cli_output_report_has_unknowns_field(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert "unknowns" in data[0]
    assert len(data[0]["unknowns"]) == 2


def test_cli_output_report_has_evidence_links_field(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert "evidence_links" in data[0]


def test_cli_output_no_input_produces_empty_list(tmp_path: Path) -> None:
    out = tmp_path / "ca_export.json"
    result = runner.invoke(app, ["company-analysis", "export", "--output", str(out)])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data == []


def test_cli_output_multi_report_produces_list(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _multi_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 2


def test_cli_output_is_deterministic(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    out1 = tmp_path / "c1.json"
    out2 = tmp_path / "c2.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out1)])
    runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


def test_cli_output_filename_in_confirmation(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    assert "ca_export.json" in result.stdout


# ── round-trip: company analysis export → atlas daily summary ──────────────────


def test_round_trip_empty_export_to_daily_summary(tmp_path: Path) -> None:
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--output", str(out)])
    daily_result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily_result.exit_code == 0
    assert "Atlas Daily Brief" in daily_result.stdout


def test_round_trip_single_report_to_daily_summary(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(in_path), "--output", str(out)])
    daily_result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily_result.exit_code == 0
    assert "Atlas Daily Brief" in daily_result.stdout


def test_round_trip_produces_company_analysis_section(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(in_path), "--output", str(out)])
    daily_result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert "Company Analysis Context" in daily_result.stdout


def test_round_trip_multi_report_to_daily_summary(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "ca.json", _multi_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(in_path), "--output", str(out)])
    daily_result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily_result.exit_code == 0


def test_round_trip_no_forbidden_language(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    runner.invoke(app, ["company-analysis", "export", "--input", str(in_path), "--output", str(out)])
    daily_result = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily_result.exit_code == 0
    output_lower = daily_result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term in daily summary: {term!r}"


def test_cli_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail(*args, **kwargs):
        raise AssertionError("urlopen must not be called during company analysis export")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail)

    path = _write(tmp_path, "ca.json", _single_report_json())
    out = tmp_path / "ca_export.json"
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path), "--output", str(out)])
    assert result.exit_code == 0


def test_cli_output_no_forbidden_language_stdout(tmp_path: Path) -> None:
    path = _write(tmp_path, "ca.json", _single_report_json())
    result = runner.invoke(app, ["company-analysis", "export", "--input", str(path)])
    assert result.exit_code == 0
    output_lower = result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term in export stdout: {term!r}"
