"""Sprint 259 — Phase 2 CLI language option tests.

Verifies that --language {en,sv} is available on snapshot confirm, reject,
export-research-notes, and export-company-facts. Tests that Swedish display
output is produced when requested, that written files are invariant across
language settings, that unsupported values fail before any file writes, that
canonical values remain English, and that user-provided content passes through
unchanged.

No renderers were changed. No schemas were changed. Only CLI command signatures
and renderer call sites were updated.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

_DRAFT_RESEARCH = Path("examples/snapshot_drafts/research_notes_snapshot.json")
_DRAFT_RESEARCH_CONFIRMED = Path("examples/snapshot_drafts/research_notes_snapshot_confirmed.json")
_DRAFT_CF_CONFIRMED = Path("examples/snapshot_drafts/company_facts_snapshot_confirmed.json")

_UNSUPPORTED = ["fr", "de", "EN", "SV", "en-US", "sv-SE", "xx"]


def _atlas_cli(*args: str) -> subprocess.CompletedProcess:
    atlas_bin = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas_bin, *args], capture_output=True, text=True)


# ---------------------------------------------------------------------------
# Help surface
# ---------------------------------------------------------------------------

def test_snapshot_confirm_help_has_language() -> None:
    result = _atlas_cli("snapshot", "confirm", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" in result.stdout


def test_snapshot_reject_help_has_language() -> None:
    result = _atlas_cli("snapshot", "reject", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" in result.stdout


def test_snapshot_export_research_notes_help_has_language() -> None:
    result = _atlas_cli("snapshot", "export-research-notes", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" in result.stdout


def test_snapshot_export_company_facts_help_has_language() -> None:
    result = _atlas_cli("snapshot", "export-company-facts", "--help")
    assert result.returncode == 0, result.stderr
    assert "--language" in result.stdout


def test_phase1_weekly_review_help_still_has_language() -> None:
    result = _atlas_cli("weekly-review", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


def test_phase1_snapshot_validate_help_still_has_language() -> None:
    result = _atlas_cli("snapshot", "validate", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


def test_phase1_snapshot_review_help_still_has_language() -> None:
    result = _atlas_cli("snapshot", "review", "--help")
    assert result.returncode == 0
    assert "--language" in result.stdout


# ---------------------------------------------------------------------------
# snapshot confirm: default / en / sv display
# ---------------------------------------------------------------------------

def test_confirm_default_output_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "confirmed.json"
        result = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
        )
        assert result.returncode == 0, result.stderr
        assert "Snapshot Draft Confirmation" in result.stdout
        assert "Bekräftelse av Snapshot Draft" not in result.stdout


def test_confirm_language_en_equals_default() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "confirmed_default.json"
        out_en = Path(tmp) / "confirmed_en.json"
        r_default = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out_default),
        )
        r_en = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out_en),
            "--language", "en",
        )
        assert r_default.returncode == 0
        assert r_en.returncode == 0
        assert "Snapshot Draft Confirmation" in r_default.stdout
        assert "Snapshot Draft Confirmation" in r_en.stdout


def test_confirm_language_sv_swedish_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "confirmed_sv.json"
        result = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        assert "Bekräftelse av Snapshot Draft" in result.stdout


def test_confirm_language_sv_safety_boundary_swedish() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "confirmed_sv.json"
        result = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        assert "Säkerhetsgräns" in result.stdout


# ---------------------------------------------------------------------------
# snapshot reject: default / en / sv display
# ---------------------------------------------------------------------------

def test_reject_default_output_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "rejected.json"
        result = _atlas_cli(
            "snapshot", "reject", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
        )
        assert result.returncode == 0, result.stderr
        assert "Snapshot Draft Rejection" in result.stdout
        assert "Avvisning av Snapshot Draft" not in result.stdout


def test_reject_language_sv_swedish_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "rejected_sv.json"
        result = _atlas_cli(
            "snapshot", "reject", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        assert "Avvisning av Snapshot Draft" in result.stdout


def test_reject_language_sv_safety_boundary_swedish() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "rejected_sv.json"
        result = _atlas_cli(
            "snapshot", "reject", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        assert "Säkerhetsgräns" in result.stdout


# ---------------------------------------------------------------------------
# snapshot export-research-notes: default / en / sv display
# ---------------------------------------------------------------------------

def test_export_research_notes_default_output_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _atlas_cli(
            "snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED),
            "--output-dir", tmp,
        )
        assert result.returncode == 0, result.stderr
        assert "Research Notes Export" in result.stdout
        assert "Export av analysnotisar" not in result.stdout


def test_export_research_notes_language_sv_swedish_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _atlas_cli(
            "snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED),
            "--output-dir", tmp,
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        assert "Export av analysnotisar" in result.stdout


def test_export_research_notes_language_sv_safety_boundary_swedish() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _atlas_cli(
            "snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED),
            "--output-dir", tmp,
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        assert "Säkerhetsgräns" in result.stdout


# ---------------------------------------------------------------------------
# snapshot export-company-facts: default / en / sv display
# ---------------------------------------------------------------------------

def test_export_company_facts_default_output_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _atlas_cli(
            "snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED),
            "--output-dir", tmp,
        )
        assert result.returncode == 0, result.stderr
        assert "Company Facts Export" in result.stdout
        assert "Export av företagsfakta" not in result.stdout


def test_export_company_facts_language_sv_swedish_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _atlas_cli(
            "snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED),
            "--output-dir", tmp,
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        assert "Export av företagsfakta" in result.stdout


def test_export_company_facts_language_sv_safety_boundary_swedish() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = _atlas_cli(
            "snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED),
            "--output-dir", tmp,
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        assert "Säkerhetsgräns" in result.stdout


# ---------------------------------------------------------------------------
# File-write invariance: confirm
# ---------------------------------------------------------------------------

def test_confirm_file_invariance_default_vs_en() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default.json"
        out_en = Path(tmp) / "en.json"
        _atlas_cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out_default))
        _atlas_cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out_en), "--language", "en")
        assert out_default.read_bytes() == out_en.read_bytes()


def test_confirm_file_invariance_default_vs_sv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default.json"
        out_sv = Path(tmp) / "sv.json"
        _atlas_cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out_default))
        _atlas_cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out_sv), "--language", "sv")
        assert out_default.read_bytes() == out_sv.read_bytes()


# ---------------------------------------------------------------------------
# File-write invariance: reject
# ---------------------------------------------------------------------------

def test_reject_file_invariance_default_vs_en() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default.json"
        out_en = Path(tmp) / "en.json"
        _atlas_cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out_default))
        _atlas_cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out_en), "--language", "en")
        assert out_default.read_bytes() == out_en.read_bytes()


def test_reject_file_invariance_default_vs_sv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default.json"
        out_sv = Path(tmp) / "sv.json"
        _atlas_cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out_default))
        _atlas_cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out_sv), "--language", "sv")
        assert out_default.read_bytes() == out_sv.read_bytes()


# ---------------------------------------------------------------------------
# File-write invariance: export-research-notes
# ---------------------------------------------------------------------------

def test_export_research_notes_file_invariance_default_vs_en() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default"
        out_en = Path(tmp) / "en"
        _atlas_cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", str(out_default))
        _atlas_cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", str(out_en), "--language", "en")
        notes_default = (out_default / "ASML" / "notes.md").read_bytes()
        notes_en = (out_en / "ASML" / "notes.md").read_bytes()
        assert notes_default == notes_en


def test_export_research_notes_file_invariance_default_vs_sv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default"
        out_sv = Path(tmp) / "sv"
        _atlas_cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", str(out_default))
        _atlas_cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", str(out_sv), "--language", "sv")
        notes_default = (out_default / "ASML" / "notes.md").read_bytes()
        notes_sv = (out_sv / "ASML" / "notes.md").read_bytes()
        assert notes_default == notes_sv


# ---------------------------------------------------------------------------
# File-write invariance: export-company-facts
# ---------------------------------------------------------------------------

def test_export_company_facts_file_invariance_default_vs_en() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default"
        out_en = Path(tmp) / "en"
        _atlas_cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", str(out_default))
        _atlas_cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", str(out_en), "--language", "en")
        assert (out_default / "ASML.json").read_bytes() == (out_en / "ASML.json").read_bytes()


def test_export_company_facts_file_invariance_default_vs_sv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default"
        out_sv = Path(tmp) / "sv"
        _atlas_cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", str(out_default))
        _atlas_cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", str(out_sv), "--language", "sv")
        assert (out_default / "ASML.json").read_bytes() == (out_sv / "ASML.json").read_bytes()


# ---------------------------------------------------------------------------
# Unsupported language fails before side effects
# ---------------------------------------------------------------------------

import pytest

@pytest.mark.parametrize("lang", _UNSUPPORTED)
def test_confirm_unsupported_language_fails(lang: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "should_not_exist.json"
        result = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", lang,
        )
        assert result.returncode != 0
        assert not out.exists(), f"Output file was created despite unsupported language {lang!r}"


@pytest.mark.parametrize("lang", _UNSUPPORTED)
def test_reject_unsupported_language_fails(lang: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "should_not_exist.json"
        result = _atlas_cli(
            "snapshot", "reject", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", lang,
        )
        assert result.returncode != 0
        assert not out.exists(), f"Output file was created despite unsupported language {lang!r}"


@pytest.mark.parametrize("lang", _UNSUPPORTED)
def test_export_research_notes_unsupported_language_fails(lang: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "output"
        result = _atlas_cli(
            "snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED),
            "--output-dir", str(out_dir),
            "--language", lang,
        )
        assert result.returncode != 0
        assert not (out_dir / "ASML" / "notes.md").exists(), \
            f"notes.md was written despite unsupported language {lang!r}"


@pytest.mark.parametrize("lang", _UNSUPPORTED)
def test_export_company_facts_unsupported_language_fails(lang: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "output"
        result = _atlas_cli(
            "snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED),
            "--output-dir", str(out_dir),
            "--language", lang,
        )
        assert result.returncode != 0
        assert not (out_dir / "ASML.json").exists(), \
            f"ASML.json was written despite unsupported language {lang!r}"


def test_unsupported_language_error_names_value() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "x.json"
        result = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "fr",
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "fr" in combined


def test_unsupported_language_error_lists_supported_values() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "x.json"
        result = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "de",
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "en" in combined
        assert "sv" in combined


# ---------------------------------------------------------------------------
# Canonical values in written files remain English
# ---------------------------------------------------------------------------

def test_confirmed_draft_confirmation_status_is_confirmed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "confirmed_sv.json"
        result = _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["confirmation_status"] == "confirmed"


def test_rejected_draft_confirmation_status_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "rejected_sv.json"
        result = _atlas_cli(
            "snapshot", "reject", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["confirmation_status"] == "rejected"


def test_confirmed_draft_snapshot_type_canonical() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "confirmed_sv.json"
        _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["snapshot_type"] == "research_notes_snapshot"


def test_rejected_draft_snapshot_type_canonical() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "rejected_sv.json"
        _atlas_cli(
            "snapshot", "reject", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["snapshot_type"] == "research_notes_snapshot"


def test_company_facts_json_schema_keys_canonical() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp) / "out"
        _atlas_cli(
            "snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED),
            "--output-dir", str(out_dir),
            "--language", "sv",
        )
        data = json.loads((out_dir / "ASML.json").read_text(encoding="utf-8"))
        assert "ticker" in data
        assert "source" in data


# ---------------------------------------------------------------------------
# User-provided content passes through unchanged
# ---------------------------------------------------------------------------

def test_confirmed_draft_notes_field_unchanged() -> None:
    original = json.loads(_DRAFT_RESEARCH.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "confirmed_sv.json"
        _atlas_cli(
            "snapshot", "confirm", str(_DRAFT_RESEARCH),
            "--output-draft", str(out),
            "--language", "sv",
        )
        result_data = json.loads(out.read_text(encoding="utf-8"))
        if original.get("notes"):
            assert result_data.get("notes") == original.get("notes")


def test_export_research_notes_user_content_preserved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        _atlas_cli(
            "snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED),
            "--output-dir", tmp,
            "--language", "sv",
        )
        notes_sv = (Path(tmp) / "ASML" / "notes.md").read_text(encoding="utf-8")
        draft_data = json.loads(_DRAFT_RESEARCH_CONFIRMED.read_text(encoding="utf-8"))
        ef = draft_data.get("extracted_fields", {})
        title = ef.get("title", "")
        if title:
            assert title in notes_sv


def test_company_facts_values_preserved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_dir_en = Path(tmp) / "en"
        out_dir_sv = Path(tmp) / "sv"
        _atlas_cli(
            "snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED),
            "--output-dir", str(out_dir_en), "--language", "en",
        )
        _atlas_cli(
            "snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED),
            "--output-dir", str(out_dir_sv), "--language", "sv",
        )
        en_data = json.loads((out_dir_en / "ASML.json").read_text(encoding="utf-8"))
        sv_data = json.loads((out_dir_sv / "ASML.json").read_text(encoding="utf-8"))
        assert en_data == sv_data


# ---------------------------------------------------------------------------
# Phase 1 behavior unchanged
# ---------------------------------------------------------------------------

def test_phase1_weekly_review_default_still_english() -> None:
    result = _atlas_cli(
        "weekly-review",
        "--portfolio", "examples/weekly_review/portfolio.json",
        "--watchlist", "examples/weekly_review/watchlist.json",
        "--as-of", "2026-01-05",
    )
    assert result.returncode == 0
    assert "Atlas Weekly Investment Review" in result.stdout
    assert "Atlas veckovis investeringsgranskning" not in result.stdout


def test_phase1_snapshot_validate_default_still_english() -> None:
    result = _atlas_cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    assert result.returncode == 0
    assert "Snapshot Draft Validation" in result.stdout


# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

def test_no_gettext_import_in_cli() -> None:
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "import gettext" not in source


def test_no_locale_detection_in_cli() -> None:
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert "locale.getlocale" not in source


def test_no_translation_catalogs() -> None:
    import atlas
    assert not any(Path(atlas.__file__).parent.glob("*.po"))
    assert not any(Path(atlas.__file__).parent.glob("*.mo"))


def test_supported_locales_remain_en_sv() -> None:
    from atlas.locale_support import _SUPPORTED_LOCALES
    assert _SUPPORTED_LOCALES == frozenset({"en", "sv"})


def test_no_provider_imports_in_locale_support() -> None:
    source = Path("atlas/locale_support.py").read_text(encoding="utf-8")
    for term in ("requests", "urllib", "httpx", "aiohttp"):
        assert term not in source


def test_cli_phase2_commands_have_language_param() -> None:
    source = Path("atlas/cli/main.py").read_text(encoding="utf-8")
    assert source.count('def snapshot_confirm_command') == 1
    assert source.count('def snapshot_reject_command') == 1
    assert "ensure_supported_locale" in source
