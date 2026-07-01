"""Sprint 56: Company Analysis --company-name and --business-description flag tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from atlas.cli.main import app

runner = CliRunner()

FORBIDDEN_LANGUAGE = (
    "buy", "sell", "strong buy", "strong sell", "urgent", "must act",
    "guaranteed", "risk-free", "price target", "outperform", "entry", "exit",
)


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _knowledge_json() -> dict:
    return {
        "facts": [
            {
                "id": "f1",
                "subject_node_id": "company-amd",
                "statement": "AMD reported strong data centre GPU growth.",
                "source": {"id": "s1", "name": "10-K 2024", "source_type": "Filing"},
                "confidence": 85,
            }
        ]
    }


# ── --company-name flag ────────────────────────────────────────────────────────


def test_company_name_flag_accepted() -> None:
    result = runner.invoke(app, [
        "company-analysis", "export", "--ticker", "AMD", "--company-name", "AMD Corporation",
    ])
    assert result.exit_code == 0


def test_company_name_appears_in_stdout() -> None:
    result = runner.invoke(app, [
        "company-analysis", "export", "--ticker", "AMD", "--company-name", "AMD Corporation",
    ])
    assert "AMD Corporation" in result.stdout


def test_company_name_appears_in_exported_json(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    assert data[0]["company"]["name"] == "AMD Corporation"


def test_ticker_still_preserved_with_company_name(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    assert data[0]["company"]["ticker"] == "AMD"


def test_without_company_name_ticker_used_as_name(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--output", str(out)])
    data = json.loads(out.read_text())
    assert data[0]["company"]["name"] == "AMD"


# ── --business-description flag ────────────────────────────────────────────────


def test_business_description_flag_accepted() -> None:
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
    ])
    assert result.exit_code == 0


def test_business_description_eliminates_missing_description_unknown(tmp_path: Path) -> None:
    out_with = tmp_path / "with_desc.json"
    out_without = tmp_path / "without_desc.json"

    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--output", str(out_with),
    ])
    runner.invoke(app, [
        "company-analysis", "export", "--ticker", "AMD", "--output", str(out_without),
    ])

    unknowns_with = [u["title"] for u in json.loads(out_with.read_text())[0]["unknowns"]]
    unknowns_without = [u["title"] for u in json.loads(out_without.read_text())[0]["unknowns"]]

    assert "Missing Business Description" not in unknowns_with
    assert "Missing Business Description" in unknowns_without


def test_business_description_does_not_remove_other_unknowns(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    # Missing Evidence and Missing Sector/Country are still present (no knowledge/company details)
    unknowns = [u["title"] for u in data[0]["unknowns"]]
    assert "Missing Evidence" in unknowns


# ── both flags together ────────────────────────────────────────────────────────


def test_both_flags_together_succeed() -> None:
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
    ])
    assert result.exit_code == 0


def test_both_flags_in_exported_json(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--output", str(out),
    ])
    data = json.loads(out.read_text())
    assert data[0]["company"]["name"] == "AMD Corporation"
    assert data[0]["company"]["ticker"] == "AMD"
    missing_desc = [u for u in data[0]["unknowns"] if u["title"] == "Missing Business Description"]
    assert missing_desc == []


def test_both_flags_with_knowledge_round_trip_to_daily_summary(tmp_path: Path) -> None:
    k = _write(tmp_path, "k.json", _knowledge_json())
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--knowledge", str(k),
        "--output", str(out),
    ])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily.exit_code == 0
    assert "Company Analysis Context" in daily.stdout


def test_both_flags_no_forbidden_language(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--output", str(out),
    ])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily.exit_code == 0
    for term in FORBIDDEN_LANGUAGE:
        assert term not in daily.stdout.lower(), f"Forbidden: {term!r}"


def test_export_is_deterministic_with_both_flags(tmp_path: Path) -> None:
    args = [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
    ]
    out1 = tmp_path / "c1.json"
    out2 = tmp_path / "c2.json"
    runner.invoke(app, args + ["--output", str(out1)])
    runner.invoke(app, args + ["--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


def test_no_network_calls_with_metadata_flags(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(yahoo_module, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no network")))
    out = tmp_path / "ca.json"
    result = runner.invoke(app, [
        "company-analysis", "export",
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
        "--output", str(out),
    ])
    assert result.exit_code == 0


# ── existing behavior preserved ───────────────────────────────────────────────


def test_sprint55_ticker_only_still_works() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD"])
    assert result.exit_code == 0
    assert "AMD" in result.stdout


def test_sprint54_no_input_still_works(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    result = runner.invoke(app, ["company-analysis", "export", "--output", str(out)])
    assert result.exit_code == 0
    assert json.loads(out.read_text()) == []
