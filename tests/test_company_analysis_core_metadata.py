"""Sprint 57: Company Analysis --sector and --country flag tests."""

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

_ALL_METADATA = [
    "--ticker", "AMD",
    "--company-name", "AMD Corporation",
    "--sector", "Semiconductors",
    "--country", "USA",
    "--business-description", "AMD designs high-performance CPUs and GPUs.",
]


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _export(tmp_path: Path, *extra_args: str) -> list:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export"] + list(extra_args) + ["--output", str(out)])
    return json.loads(out.read_text())


# ── --sector flag ──────────────────────────────────────────────────────────────


def test_sector_flag_accepted() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--sector", "Semiconductors"])
    assert result.exit_code == 0


def test_sector_appears_in_exported_json(tmp_path: Path) -> None:
    data = _export(tmp_path, "--ticker", "AMD", "--sector", "Semiconductors")
    assert data[0]["company"]["sector"] == "Semiconductors"


def test_sector_eliminates_missing_sector_unknown(tmp_path: Path) -> None:
    with_sector = _export(tmp_path, "--ticker", "AMD", "--sector", "Semiconductors")
    unknowns = [u["title"] for u in with_sector[0]["unknowns"]]
    assert "Missing Sector" not in unknowns


def test_without_sector_missing_sector_unknown_present(tmp_path: Path) -> None:
    without = _export(tmp_path, "--ticker", "AMD")
    unknowns = [u["title"] for u in without[0]["unknowns"]]
    assert "Missing Sector" in unknowns


# ── --country flag ─────────────────────────────────────────────────────────────


def test_country_flag_accepted() -> None:
    result = runner.invoke(app, ["company-analysis", "export", "--ticker", "AMD", "--country", "USA"])
    assert result.exit_code == 0


def test_country_appears_in_exported_json(tmp_path: Path) -> None:
    data = _export(tmp_path, "--ticker", "AMD", "--country", "USA")
    assert data[0]["company"]["country"] == "USA"


def test_country_eliminates_missing_country_unknown(tmp_path: Path) -> None:
    with_country = _export(tmp_path, "--ticker", "AMD", "--country", "USA")
    unknowns = [u["title"] for u in with_country[0]["unknowns"]]
    assert "Missing Country" not in unknowns


def test_without_country_missing_country_unknown_present(tmp_path: Path) -> None:
    without = _export(tmp_path, "--ticker", "AMD")
    unknowns = [u["title"] for u in without[0]["unknowns"]]
    assert "Missing Country" in unknowns


# ── all four metadata flags together ──────────────────────────────────────────


def test_all_metadata_flags_no_core_field_unknowns(tmp_path: Path) -> None:
    data = _export(tmp_path, *_ALL_METADATA)
    unknown_titles = {u["title"] for u in data[0]["unknowns"]}
    core_missing = {"Missing Sector", "Missing Country", "Missing Business Description", "Missing Evidence"}
    # All four core fields supplied except knowledge → only Missing Evidence remains
    assert "Missing Sector" not in unknown_titles
    assert "Missing Country" not in unknown_titles
    assert "Missing Business Description" not in unknown_titles


def test_all_metadata_flags_confidence_elevated(tmp_path: Path) -> None:
    data = _export(tmp_path, *_ALL_METADATA)
    # With all four fields populated confidence should be moderate or high
    assert data[0]["confidence"]["level"] in {"moderate", "high"}


def test_all_metadata_flags_round_trip_to_daily_summary(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export"] + _ALL_METADATA + ["--output", str(out)])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily.exit_code == 0
    assert "Company Analysis Context" in daily.stdout


def test_all_metadata_flags_no_forbidden_language(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    runner.invoke(app, ["company-analysis", "export"] + _ALL_METADATA + ["--output", str(out)])
    daily = runner.invoke(app, ["daily", "summary", "--company-analysis", str(out)])
    assert daily.exit_code == 0
    for term in FORBIDDEN_LANGUAGE:
        assert term not in daily.stdout.lower(), f"Forbidden: {term!r}"


def test_all_metadata_flags_is_deterministic(tmp_path: Path) -> None:
    out1 = tmp_path / "c1.json"
    out2 = tmp_path / "c2.json"
    runner.invoke(app, ["company-analysis", "export"] + _ALL_METADATA + ["--output", str(out1)])
    runner.invoke(app, ["company-analysis", "export"] + _ALL_METADATA + ["--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


def test_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module
    monkeypatch.setattr(yahoo_module, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no network")))
    out = tmp_path / "ca.json"
    result = runner.invoke(app, ["company-analysis", "export"] + _ALL_METADATA + ["--output", str(out)])
    assert result.exit_code == 0


# ── existing behavior preserved ───────────────────────────────────────────────


def test_sprint56_all_previous_flags_still_work(tmp_path: Path) -> None:
    data = _export(tmp_path,
        "--ticker", "AMD",
        "--company-name", "AMD Corporation",
        "--business-description", "AMD designs high-performance CPUs and GPUs.",
    )
    assert data[0]["company"]["name"] == "AMD Corporation"
    assert "Missing Business Description" not in {u["title"] for u in data[0]["unknowns"]}


def test_sprint54_no_input_still_works(tmp_path: Path) -> None:
    out = tmp_path / "ca.json"
    result = runner.invoke(app, ["company-analysis", "export", "--output", str(out)])
    assert result.exit_code == 0
    assert json.loads(out.read_text()) == []
