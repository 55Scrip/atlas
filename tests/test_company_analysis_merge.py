"""Sprint 60: Company Analysis merge command tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.main import app

runner = CliRunner()

FORBIDDEN = (
    "buy", "sell", "strong buy", "strong sell", "urgent", "must act",
    "guaranteed", "risk-free", "price target", "outperform", "market-beating",
)

_AMD_REPORT = {
    "company": {"id": "amd", "name": "AMD Corporation", "ticker": "AMD", "sector": "Semiconductors", "country": "USA"},
    "unknowns": [{"title": "Missing Evidence", "detail": "No knowledge facts supplied."}],
    "evidence_links": [],
    "confidence": {"level": "low", "explanation": "Minimal context.", "drivers": [], "limitations": []},
    "what_could_change_the_view": [],
}

_NVDA_REPORT = {
    "company": {"id": "nvda", "name": "NVIDIA Corporation", "ticker": "NVDA", "sector": "Semiconductors", "country": "USA"},
    "unknowns": [{"title": "Missing Evidence", "detail": "No knowledge facts supplied."}],
    "evidence_links": [],
    "confidence": {"level": "low", "explanation": "Minimal context.", "drivers": [], "limitations": []},
    "what_could_change_the_view": [],
}


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data if isinstance(data, list) else [data]), encoding="utf-8")
    return path


def _amd_file(tmp_path: Path) -> Path:
    return _write(tmp_path, "amd.json", _AMD_REPORT)


def _nvda_file(tmp_path: Path) -> Path:
    return _write(tmp_path, "nvda.json", _NVDA_REPORT)


# ── command existence ──────────────────────────────────────────────────────────


def test_merge_command_exists() -> None:
    result = runner.invoke(app, ["company-analysis", "merge", "--help"])
    assert result.exit_code == 0
    assert "merge" in result.stdout.lower()


# ── merge two valid files ──────────────────────────────────────────────────────


def test_merge_two_files_succeeds(tmp_path: Path) -> None:
    out = tmp_path / "combined.json"
    result = runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--inputs", str(_nvda_file(tmp_path)),
        "--output", str(out),
    ])
    assert result.exit_code == 0


def test_merged_output_contains_both_companies(tmp_path: Path) -> None:
    out = tmp_path / "combined.json"
    runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--inputs", str(_nvda_file(tmp_path)),
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    tickers = {r["company"]["ticker"] for r in data}
    assert "AMD" in tickers
    assert "NVDA" in tickers


def test_merged_output_is_list(tmp_path: Path) -> None:
    out = tmp_path / "combined.json"
    runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--inputs", str(_nvda_file(tmp_path)),
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 2


def test_merge_preserves_input_order(tmp_path: Path) -> None:
    out = tmp_path / "combined.json"
    runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--inputs", str(_nvda_file(tmp_path)),
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    assert data[0]["company"]["ticker"] == "AMD"
    assert data[1]["company"]["ticker"] == "NVDA"


def test_merge_is_deterministic(tmp_path: Path) -> None:
    amd = _amd_file(tmp_path)
    nvda = _nvda_file(tmp_path)
    out1 = tmp_path / "c1.json"
    out2 = tmp_path / "c2.json"
    args = ["company-analysis", "merge", "--inputs", str(amd), "--inputs", str(nvda)]
    runner.invoke(app, args + ["--output", str(out1)])
    runner.invoke(app, args + ["--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


def test_merge_single_file_succeeds(tmp_path: Path) -> None:
    out = tmp_path / "single.json"
    result = runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--output", str(out),
    ])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert len(data) == 1
    assert data[0]["company"]["ticker"] == "AMD"


# ── Daily Brief compatibility ──────────────────────────────────────────────────


def test_merged_output_consumed_by_daily_summary(tmp_path: Path) -> None:
    out = tmp_path / "combined.json"
    runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--inputs", str(_nvda_file(tmp_path)),
        "--output", str(out),
    ])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily.exit_code == 0
    assert "Company Analysis Context" in daily.stdout


def test_merged_daily_brief_contains_both_tickers(tmp_path: Path) -> None:
    out = tmp_path / "combined.json"
    runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--inputs", str(_nvda_file(tmp_path)),
        "--output", str(out),
    ])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert "AMD" in daily.stdout
    assert "NVDA" in daily.stdout


def test_merged_daily_brief_no_forbidden_language(tmp_path: Path) -> None:
    out = tmp_path / "combined.json"
    runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--inputs", str(_nvda_file(tmp_path)),
        "--output", str(out),
    ])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    output_lower = daily.stdout.lower()
    for term in FORBIDDEN:
        assert term not in output_lower, f"Forbidden term: {term!r}"


# ── error handling ─────────────────────────────────────────────────────────────


def test_missing_input_file_fails(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    result = runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(tmp_path / "nonexistent.json"),
        "--output", str(out),
    ])
    assert result.exit_code != 0


def test_invalid_json_input_fails(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    out = tmp_path / "out.json"
    result = runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(bad),
        "--output", str(out),
    ])
    assert result.exit_code != 0


def test_malformed_company_analysis_json_fails(tmp_path: Path) -> None:
    # A JSON number is neither a dict nor a list — parse_company_analysis_json raises ValueError.
    bad = tmp_path / "bad.json"
    bad.write_text("42", encoding="utf-8")
    out = tmp_path / "out.json"
    result = runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(bad),
        "--output", str(out),
    ])
    assert result.exit_code != 0


# ── no network / no provider ───────────────────────────────────────────────────


def test_merge_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(yahoo_module, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network call")))
    out = tmp_path / "combined.json"
    result = runner.invoke(app, [
        "company-analysis", "merge",
        "--inputs", str(_amd_file(tmp_path)),
        "--inputs", str(_nvda_file(tmp_path)),
        "--output", str(out),
    ])
    assert result.exit_code == 0


# ── demo script check ──────────────────────────────────────────────────────────


def test_demo_script_uses_atlas_merge_not_python() -> None:
    script = (
        Path(__file__).parent.parent / "scripts" / "run_daily_brief_demo.sh"
    ).read_text()
    assert "company-analysis merge" in script
    assert "python3 -c" not in script
    assert "python -c" not in script
