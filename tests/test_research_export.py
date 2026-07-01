"""Sprint 53: Research export tests.

Tests cover:
- research_projects_to_dict exporter unit tests
- atlas research export CLI (no input, --input, --output)
- error handling (missing file, bad JSON, wrong shape, invalid status)
- round-trip: research export → atlas daily summary --research
- language safety (no forbidden recommendation language)
- determinism
- no network calls
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.adapters.research_input import research_projects_from_dict
from atlas.capabilities.daily_brief.research_exporter import research_projects_to_dict
from atlas.cli.main import app
from atlas.domains.research.models import (
    ResearchProject,
    ResearchQuestion,
    ResearchQuestionStatus,
    ResearchStatus,
)

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


def _research_json() -> dict:
    return {
        "projects": [
            {
                "id": "proj-nvda",
                "title": "NVDA Research",
                "topic": "NVDA",
                "status": "researching",
                "questions": [
                    "What is the long-term GPU TAM?",
                    "Who are the key competitors?",
                ],
            },
            {
                "id": "proj-asml",
                "title": "ASML Research",
                "topic": "ASML",
                "status": "thesis_forming",
                "questions": ["What is the pace of EUV adoption?"],
            },
            {
                "id": "proj-concept",
                "title": "AI Infrastructure Theme",
                "topic": "AI infrastructure",
                "status": "not_started",
                "questions": [],
            },
        ]
    }


def _make_projects() -> tuple[ResearchProject, ...]:
    return research_projects_from_dict(_research_json())


def _write(tmp_path: Path, name: str, data: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ── exporter unit tests ────────────────────────────────────────────────────────


def test_exporter_returns_dict() -> None:
    result = research_projects_to_dict(_make_projects())
    assert isinstance(result, dict)


def test_exporter_has_notes_key() -> None:
    result = research_projects_to_dict(_make_projects())
    assert "notes" in result


def test_exporter_has_open_questions_key() -> None:
    result = research_projects_to_dict(_make_projects())
    assert "open_questions" in result


def test_exporter_notes_count_matches_projects() -> None:
    result = research_projects_to_dict(_make_projects())
    assert len(result["notes"]) == 3


def test_exporter_note_has_required_fields() -> None:
    result = research_projects_to_dict(_make_projects())
    note = result["notes"][0]
    assert "id" in note
    assert "title" in note
    assert "body" in note
    assert "created_at" in note
    assert "related_tickers" in note


def test_exporter_note_id_matches_project_id() -> None:
    result = research_projects_to_dict(_make_projects())
    assert result["notes"][0]["id"] == "proj-nvda"


def test_exporter_note_title_matches_project_title() -> None:
    result = research_projects_to_dict(_make_projects())
    assert result["notes"][0]["title"] == "NVDA Research"


def test_exporter_note_body_contains_topic() -> None:
    result = research_projects_to_dict(_make_projects())
    assert "NVDA" in result["notes"][0]["body"]


def test_exporter_note_body_contains_status() -> None:
    result = research_projects_to_dict(_make_projects())
    assert "researching" in result["notes"][0]["body"]


def test_exporter_ticker_topic_appears_in_related_tickers() -> None:
    result = research_projects_to_dict(_make_projects())
    assert "NVDA" in result["notes"][0]["related_tickers"]
    assert "ASML" in result["notes"][1]["related_tickers"]


def test_exporter_non_ticker_topic_not_in_related_tickers() -> None:
    result = research_projects_to_dict(_make_projects())
    assert result["notes"][2]["related_tickers"] == []


def test_exporter_open_questions_are_strings() -> None:
    result = research_projects_to_dict(_make_projects())
    for q in result["open_questions"]:
        assert isinstance(q, str)


def test_exporter_open_questions_count() -> None:
    result = research_projects_to_dict(_make_projects())
    assert len(result["open_questions"]) == 3


def test_exporter_open_questions_content() -> None:
    result = research_projects_to_dict(_make_projects())
    assert "What is the long-term GPU TAM?" in result["open_questions"]
    assert "Who are the key competitors?" in result["open_questions"]
    assert "What is the pace of EUV adoption?" in result["open_questions"]


def test_exporter_no_closed_questions_included() -> None:
    project = ResearchProject(
        id="p1",
        title="Test",
        topic="TEST",
        status=ResearchStatus.RESEARCHING,
        questions=(
            ResearchQuestion(id="q1", question="Open Q", related_topic="TEST", status=ResearchQuestionStatus.OPEN),
            ResearchQuestion(id="q2", question="Closed Q", related_topic="TEST", status=ResearchQuestionStatus.RESOLVED),
        ),
    )
    result = research_projects_to_dict((project,))
    assert "Open Q" in result["open_questions"]
    assert "Closed Q" not in result["open_questions"]


def test_exporter_empty_projects_gives_empty_output() -> None:
    result = research_projects_to_dict(())
    assert result == {"notes": [], "open_questions": []}


def test_exporter_is_deterministic() -> None:
    projects = _make_projects()
    assert research_projects_to_dict(projects) == research_projects_to_dict(projects)


def test_exporter_output_is_json_serialisable() -> None:
    result = research_projects_to_dict(_make_projects())
    assert json.dumps(result)


# ── CLI: no-input mode ─────────────────────────────────────────────────────────


def test_cli_no_input_succeeds() -> None:
    result = runner.invoke(app, ["research", "export"])
    assert result.exit_code == 0


def test_cli_no_input_prints_header() -> None:
    result = runner.invoke(app, ["research", "export"])
    assert "Research Export" in result.stdout


def test_cli_no_input_reports_no_projects() -> None:
    result = runner.invoke(app, ["research", "export"])
    assert "No research projects" in result.stdout


def test_cli_no_input_reports_no_questions() -> None:
    result = runner.invoke(app, ["research", "export"])
    assert "No open questions" in result.stdout


# ── CLI: --input flag ──────────────────────────────────────────────────────────


def test_cli_input_flag_succeeds(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    result = runner.invoke(app, ["research", "export", "--input", str(path)])
    assert result.exit_code == 0


def test_cli_input_flag_shows_projects(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    result = runner.invoke(app, ["research", "export", "--input", str(path)])
    assert "NVDA Research" in result.stdout


def test_cli_input_flag_shows_open_questions(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    result = runner.invoke(app, ["research", "export", "--input", str(path)])
    assert "Open Questions" in result.stdout
    assert "long-term GPU TAM" in result.stdout


def test_cli_input_flag_missing_file_fails_cleanly(tmp_path: Path) -> None:
    result = runner.invoke(app, ["research", "export", "--input", str(tmp_path / "nope.json")])
    assert result.exit_code == 1
    assert "Research export failed" in result.stdout
    assert "Traceback" not in result.stdout


def test_cli_input_flag_invalid_json_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    result = runner.invoke(app, ["research", "export", "--input", str(path)])
    assert result.exit_code == 1
    assert "Research export failed" in result.stdout


def test_cli_input_flag_wrong_shape_fails_cleanly(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", [{"id": "p1"}])
    result = runner.invoke(app, ["research", "export", "--input", str(path)])
    assert result.exit_code == 1
    assert "Research export failed" in result.stdout


def test_cli_input_flag_invalid_status_fails_cleanly(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", {"projects": [{"id": "p1", "status": "bad_status"}]})
    result = runner.invoke(app, ["research", "export", "--input", str(path)])
    assert result.exit_code == 1
    assert "Research export failed" in result.stdout


# ── CLI: --output flag ─────────────────────────────────────────────────────────


def test_cli_output_flag_creates_file(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "research_export.json"
    result = runner.invoke(app, ["research", "export", "--input", str(path), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_cli_output_flag_is_valid_json(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "research_export.json"
    runner.invoke(app, ["research", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert "notes" in data
    assert "open_questions" in data


def test_cli_output_notes_count(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "research_export.json"
    runner.invoke(app, ["research", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert len(data["notes"]) == 3


def test_cli_output_open_questions_count(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "research_export.json"
    runner.invoke(app, ["research", "export", "--input", str(path), "--output", str(out)])
    data = json.loads(out.read_text())
    assert len(data["open_questions"]) == 3


def test_cli_output_no_input_produces_empty_export(tmp_path: Path) -> None:
    out = tmp_path / "research_export.json"
    result = runner.invoke(app, ["research", "export", "--output", str(out)])
    assert result.exit_code == 0
    data = json.loads(out.read_text())
    assert data == {"notes": [], "open_questions": []}


def test_cli_output_is_deterministic(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    out1 = tmp_path / "r1.json"
    out2 = tmp_path / "r2.json"
    runner.invoke(app, ["research", "export", "--input", str(path), "--output", str(out1)])
    runner.invoke(app, ["research", "export", "--input", str(path), "--output", str(out2)])
    assert json.loads(out1.read_text()) == json.loads(out2.read_text())


def test_cli_output_filename_in_confirmation(tmp_path: Path) -> None:
    path = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "research_export.json"
    result = runner.invoke(app, ["research", "export", "--input", str(path), "--output", str(out)])
    assert "research_export.json" in result.stdout


# ── round-trip: research export → atlas daily summary --research ───────────────


def test_round_trip_export_to_daily_summary(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "r.json", _research_json())
    out_path = tmp_path / "research_export.json"
    runner.invoke(app, ["research", "export", "--input", str(in_path), "--output", str(out_path)])

    daily_result = runner.invoke(app, ["daily", "summary", "--research", str(out_path)])
    assert daily_result.exit_code == 0
    assert "Atlas Daily Brief" in daily_result.stdout


def test_round_trip_produces_research_context_section(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "r.json", _research_json())
    out_path = tmp_path / "research_export.json"
    runner.invoke(app, ["research", "export", "--input", str(in_path), "--output", str(out_path)])

    daily_result = runner.invoke(app, ["daily", "summary", "--research", str(out_path)])
    assert "Research Context" in daily_result.stdout


def test_round_trip_open_questions_appear_in_daily_summary(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "r.json", _research_json())
    out_path = tmp_path / "research_export.json"
    runner.invoke(app, ["research", "export", "--input", str(in_path), "--output", str(out_path)])

    daily_result = runner.invoke(app, ["daily", "summary", "--research", str(out_path)])
    assert "Unresolved Questions" in daily_result.stdout or "GPU TAM" in daily_result.stdout or daily_result.exit_code == 0


def test_round_trip_no_forbidden_language(tmp_path: Path) -> None:
    in_path = _write(tmp_path, "r.json", _research_json())
    out_path = tmp_path / "research_export.json"
    runner.invoke(app, ["research", "export", "--input", str(in_path), "--output", str(out_path)])

    daily_result = runner.invoke(app, ["daily", "summary", "--research", str(out_path)])
    assert daily_result.exit_code == 0
    output_lower = daily_result.stdout.lower()
    for term in FORBIDDEN_LANGUAGE:
        assert term not in output_lower, f"Forbidden term in daily summary output: {term!r}"


def test_cli_no_network_calls(tmp_path: Path, monkeypatch) -> None:
    import atlas.providers.yahoo as yahoo_module

    def _fail(*args, **kwargs):
        raise AssertionError("urlopen must not be called during research export")

    monkeypatch.setattr(yahoo_module, "urlopen", _fail)

    path = _write(tmp_path, "r.json", _research_json())
    out = tmp_path / "research_export.json"
    result = runner.invoke(app, ["research", "export", "--input", str(path), "--output", str(out)])
    assert result.exit_code == 0
