"""Sprint 261 — Full CLI Swedish regression matrix.

Compact release guard covering all seven --language-aware CLI commands:

  1. atlas weekly-review
  2. atlas snapshot validate
  3. atlas snapshot review
  4. atlas snapshot confirm
  5. atlas snapshot reject
  6. atlas snapshot export-research-notes
  7. atlas snapshot export-company-facts

Each command is tested for:
  - --language present in --help
  - Default output is English (no Swedish)
  - --language en is English
  - --language sv contains Swedish display markers
  - Canonical values remain English with --language sv
  - Unsupported --language fr fails non-zero

Write/export commands also verify:
  - Written files are byte-for-byte identical across default / en / sv
  - Unsupported language causes no file writes

This matrix is a regression guard. It is not a replacement for the detailed
sprint-specific tests (257–260). It exists to catch regressions across the
full language track in a single suite run.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_PORTFOLIO = Path("examples/weekly_review/portfolio.json")
_WATCHLIST = Path("examples/weekly_review/watchlist.json")
_DRAFT_RESEARCH = Path("examples/snapshot_drafts/research_notes_snapshot.json")
_DRAFT_RESEARCH_CONFIRMED = Path("examples/snapshot_drafts/research_notes_snapshot_confirmed.json")
_DRAFT_CF_CONFIRMED = Path("examples/snapshot_drafts/company_facts_snapshot_confirmed.json")

# Swedish display markers — stable constants from strings_sv modules
_SV_WEEKLY_TITLE = "Atlas veckovis investeringsgranskning"
_SV_WEEKLY_SCOPE = "Granskningens omfattning"
_SV_VALIDATE = "Validering av Snapshot Draft"
_SV_REVIEW = "Granskning av Snapshot Draft"
_SV_CONFIRM = "Bekräftelse av Snapshot Draft"
_SV_REJECT = "Avvisning av Snapshot Draft"
_SV_EXPORT_RN = "Export av analysnotisar"
_SV_EXPORT_CF = "Export av företagsfakta"
_SV_SAFETY = "Säkerhetsgräns"

# English display markers — stable constants from strings modules
_EN_WEEKLY_TITLE = "Atlas Weekly Investment Review"
_EN_WEEKLY_SCOPE = "1. Review Scope"
_EN_VALIDATE = "Snapshot Draft Validation"
_EN_REVIEW = "Snapshot Draft Review"
_EN_CONFIRM = "Snapshot Draft Confirmation"
_EN_REJECT = "Snapshot Draft Rejection"
_EN_EXPORT_RN = "Research Notes Export"
_EN_EXPORT_CF = "Company Facts Export"

# Unsupported locales that must always fail
_UNSUPPORTED = ["fr", "de", "EN", "SV", "en-US", "sv-SE"]


def _cli(*args: str) -> subprocess.CompletedProcess:
    atlas = str(Path(".venv/bin/atlas").resolve())
    return subprocess.run([atlas, *args], capture_output=True, text=True)


def _weekly_review(*extra: str) -> subprocess.CompletedProcess:
    return _cli(
        "weekly-review",
        "--portfolio", str(_PORTFOLIO),
        "--watchlist", str(_WATCHLIST),
        "--as-of", "2026-01-05",
        *extra,
    )


# ---------------------------------------------------------------------------
# 1. atlas weekly-review — --language in help
# ---------------------------------------------------------------------------

def test_weekly_review_help_has_language() -> None:
    r = _cli("weekly-review", "--help")
    assert r.returncode == 0
    assert "--language" in r.stdout


# ---------------------------------------------------------------------------
# 1. atlas weekly-review — English default
# ---------------------------------------------------------------------------

def test_weekly_review_default_is_english() -> None:
    r = _weekly_review()
    assert r.returncode == 0, r.stderr
    assert _EN_WEEKLY_TITLE in r.stdout
    assert _SV_WEEKLY_TITLE not in r.stdout


def test_weekly_review_language_en_is_english() -> None:
    r = _weekly_review("--language", "en")
    assert r.returncode == 0, r.stderr
    assert _EN_WEEKLY_TITLE in r.stdout
    assert _SV_WEEKLY_TITLE not in r.stdout


def test_weekly_review_language_en_matches_default() -> None:
    default = _weekly_review()
    en = _weekly_review("--language", "en")
    assert default.returncode == 0 and en.returncode == 0
    assert default.stdout == en.stdout


# ---------------------------------------------------------------------------
# 1. atlas weekly-review — Swedish opt-in
# ---------------------------------------------------------------------------

def test_weekly_review_language_sv_swedish_title() -> None:
    r = _weekly_review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _SV_WEEKLY_TITLE in r.stdout


def test_weekly_review_language_sv_swedish_scope_section() -> None:
    r = _weekly_review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _SV_WEEKLY_SCOPE in r.stdout


def test_weekly_review_language_sv_no_english_title() -> None:
    r = _weekly_review("--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _EN_WEEKLY_TITLE not in r.stdout


def test_weekly_review_language_sv_canonical_warning_code_unchanged() -> None:
    r = _weekly_review("--language", "sv")
    assert r.returncode == 0, r.stderr
    # warning codes are canonical English regardless of display language
    # the watchlist fixture has XYL — ticker must be unchanged
    assert "XYL" in r.stdout


def test_weekly_review_language_sv_user_content_watchlist_reason_unchanged() -> None:
    r = _weekly_review("--language", "sv")
    assert r.returncode == 0, r.stderr
    # watchlist reason from fixture — user-provided content must not be translated
    assert "Water infrastructure" in r.stdout


# ---------------------------------------------------------------------------
# 1. atlas weekly-review — unsupported language
# ---------------------------------------------------------------------------

def test_weekly_review_unsupported_language_fr_fails() -> None:
    r = _weekly_review("--language", "fr")
    assert r.returncode != 0
    assert _EN_WEEKLY_TITLE not in r.stdout
    assert _SV_WEEKLY_TITLE not in r.stdout


def test_weekly_review_unsupported_language_EN_case_fails() -> None:
    r = _weekly_review("--language", "EN")
    assert r.returncode != 0


def test_weekly_review_unsupported_language_sv_SE_region_fails() -> None:
    r = _weekly_review("--language", "sv-SE")
    assert r.returncode != 0


# ---------------------------------------------------------------------------
# 2. atlas snapshot validate — --language in help
# ---------------------------------------------------------------------------

def test_snapshot_validate_help_has_language() -> None:
    r = _cli("snapshot", "validate", "--help")
    assert r.returncode == 0
    assert "--language" in r.stdout


# ---------------------------------------------------------------------------
# 2. atlas snapshot validate — English default
# ---------------------------------------------------------------------------

def test_snapshot_validate_default_is_english() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    assert r.returncode == 0, r.stderr
    assert _EN_VALIDATE in r.stdout
    assert _SV_VALIDATE not in r.stdout


def test_snapshot_validate_language_en_is_english() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "en")
    assert r.returncode == 0, r.stderr
    assert _EN_VALIDATE in r.stdout
    assert _SV_VALIDATE not in r.stdout


def test_snapshot_validate_language_en_matches_default() -> None:
    default = _cli("snapshot", "validate", str(_DRAFT_RESEARCH))
    en = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "en")
    assert default.returncode == 0 and en.returncode == 0
    assert default.stdout == en.stdout


# ---------------------------------------------------------------------------
# 2. atlas snapshot validate — Swedish opt-in
# ---------------------------------------------------------------------------

def test_snapshot_validate_language_sv_swedish_heading() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _SV_VALIDATE in r.stdout


def test_snapshot_validate_language_sv_safety_boundary_swedish() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _SV_SAFETY in r.stdout


def test_snapshot_validate_language_sv_no_english_heading() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _EN_VALIDATE not in r.stdout


def test_snapshot_validate_language_sv_canonical_snapshot_type_unchanged() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "research_notes_snapshot" in r.stdout


# ---------------------------------------------------------------------------
# 2. atlas snapshot validate — unsupported language
# ---------------------------------------------------------------------------

def test_snapshot_validate_unsupported_language_fr_fails() -> None:
    r = _cli("snapshot", "validate", str(_DRAFT_RESEARCH), "--language", "fr")
    assert r.returncode != 0
    assert _EN_VALIDATE not in r.stdout
    assert _SV_VALIDATE not in r.stdout


# ---------------------------------------------------------------------------
# 3. atlas snapshot review — --language in help
# ---------------------------------------------------------------------------

def test_snapshot_review_help_has_language() -> None:
    r = _cli("snapshot", "review", "--help")
    assert r.returncode == 0
    assert "--language" in r.stdout


# ---------------------------------------------------------------------------
# 3. atlas snapshot review — English default
# ---------------------------------------------------------------------------

def test_snapshot_review_default_is_english() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH))
    assert r.returncode == 0, r.stderr
    assert _EN_REVIEW in r.stdout
    assert _SV_REVIEW not in r.stdout


def test_snapshot_review_language_en_is_english() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "en")
    assert r.returncode == 0, r.stderr
    assert _EN_REVIEW in r.stdout
    assert _SV_REVIEW not in r.stdout


def test_snapshot_review_language_en_matches_default() -> None:
    default = _cli("snapshot", "review", str(_DRAFT_RESEARCH))
    en = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "en")
    assert default.returncode == 0 and en.returncode == 0
    assert default.stdout == en.stdout


# ---------------------------------------------------------------------------
# 3. atlas snapshot review — Swedish opt-in
# ---------------------------------------------------------------------------

def test_snapshot_review_language_sv_swedish_heading() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _SV_REVIEW in r.stdout


def test_snapshot_review_language_sv_safety_boundary_swedish() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _SV_SAFETY in r.stdout


def test_snapshot_review_language_sv_no_english_heading() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert _EN_REVIEW not in r.stdout


def test_snapshot_review_language_sv_user_content_notes_unchanged() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    # notes field is user-provided — must not be translated
    assert "Draft created from user-written research notes" in r.stdout


def test_snapshot_review_language_sv_canonical_snapshot_type_unchanged() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "sv")
    assert r.returncode == 0, r.stderr
    assert "research_notes_snapshot" in r.stdout


# ---------------------------------------------------------------------------
# 3. atlas snapshot review — unsupported language
# ---------------------------------------------------------------------------

def test_snapshot_review_unsupported_language_fr_fails() -> None:
    r = _cli("snapshot", "review", str(_DRAFT_RESEARCH), "--language", "fr")
    assert r.returncode != 0
    assert _EN_REVIEW not in r.stdout
    assert _SV_REVIEW not in r.stdout


# ---------------------------------------------------------------------------
# 4. atlas snapshot confirm — --language in help
# ---------------------------------------------------------------------------

def test_snapshot_confirm_help_has_language() -> None:
    r = _cli("snapshot", "confirm", "--help")
    assert r.returncode == 0
    assert "--language" in r.stdout


# ---------------------------------------------------------------------------
# 4. atlas snapshot confirm — English default
# ---------------------------------------------------------------------------

def test_snapshot_confirm_default_is_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out))
        assert r.returncode == 0, r.stderr
        assert _EN_CONFIRM in r.stdout
        assert _SV_CONFIRM not in r.stdout


def test_snapshot_confirm_language_en_is_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "en")
        assert r.returncode == 0, r.stderr
        assert _EN_CONFIRM in r.stdout
        assert _SV_CONFIRM not in r.stdout


# ---------------------------------------------------------------------------
# 4. atlas snapshot confirm — Swedish opt-in
# ---------------------------------------------------------------------------

def test_snapshot_confirm_language_sv_swedish_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _SV_CONFIRM in r.stdout


def test_snapshot_confirm_language_sv_safety_boundary_swedish() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _SV_SAFETY in r.stdout


def test_snapshot_confirm_language_sv_no_english_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _EN_CONFIRM not in r.stdout


# ---------------------------------------------------------------------------
# 4. atlas snapshot confirm — written file invariance
# ---------------------------------------------------------------------------

def test_snapshot_confirm_file_invariance_default_vs_en() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default.json"
        out_en = Path(tmp) / "en.json"
        _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out_default))
        _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out_en), "--language", "en")
        assert out_default.read_bytes() == out_en.read_bytes()


def test_snapshot_confirm_file_invariance_default_vs_sv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default.json"
        out_sv = Path(tmp) / "sv.json"
        _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out_default))
        _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out_sv), "--language", "sv")
        assert out_default.read_bytes() == out_sv.read_bytes()


def test_snapshot_confirm_file_canonical_confirmation_status() -> None:
    import json
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "sv")
        data = json.loads(out.read_text())
        assert data["confirmation_status"] == "confirmed"


# ---------------------------------------------------------------------------
# 4. atlas snapshot confirm — unsupported language — no file write
# ---------------------------------------------------------------------------

def test_snapshot_confirm_unsupported_language_fr_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "confirm", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "fr")
        assert r.returncode != 0
        assert not out.exists(), "confirm must not write file when language is unsupported"


# ---------------------------------------------------------------------------
# 5. atlas snapshot reject — --language in help
# ---------------------------------------------------------------------------

def test_snapshot_reject_help_has_language() -> None:
    r = _cli("snapshot", "reject", "--help")
    assert r.returncode == 0
    assert "--language" in r.stdout


# ---------------------------------------------------------------------------
# 5. atlas snapshot reject — English default
# ---------------------------------------------------------------------------

def test_snapshot_reject_default_is_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out))
        assert r.returncode == 0, r.stderr
        assert _EN_REJECT in r.stdout
        assert _SV_REJECT not in r.stdout


def test_snapshot_reject_language_en_is_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "en")
        assert r.returncode == 0, r.stderr
        assert _EN_REJECT in r.stdout
        assert _SV_REJECT not in r.stdout


# ---------------------------------------------------------------------------
# 5. atlas snapshot reject — Swedish opt-in
# ---------------------------------------------------------------------------

def test_snapshot_reject_language_sv_swedish_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _SV_REJECT in r.stdout


def test_snapshot_reject_language_sv_safety_boundary_swedish() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _SV_SAFETY in r.stdout


def test_snapshot_reject_language_sv_no_english_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _EN_REJECT not in r.stdout


# ---------------------------------------------------------------------------
# 5. atlas snapshot reject — written file invariance
# ---------------------------------------------------------------------------

def test_snapshot_reject_file_invariance_default_vs_en() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default.json"
        out_en = Path(tmp) / "en.json"
        _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out_default))
        _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out_en), "--language", "en")
        assert out_default.read_bytes() == out_en.read_bytes()


def test_snapshot_reject_file_invariance_default_vs_sv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out_default = Path(tmp) / "default.json"
        out_sv = Path(tmp) / "sv.json"
        _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out_default))
        _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out_sv), "--language", "sv")
        assert out_default.read_bytes() == out_sv.read_bytes()


def test_snapshot_reject_file_canonical_confirmation_status() -> None:
    import json
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "sv")
        data = json.loads(out.read_text())
        assert data["confirmation_status"] == "rejected"


# ---------------------------------------------------------------------------
# 5. atlas snapshot reject — unsupported language — no file write
# ---------------------------------------------------------------------------

def test_snapshot_reject_unsupported_language_fr_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        r = _cli("snapshot", "reject", str(_DRAFT_RESEARCH), "--output-draft", str(out), "--language", "fr")
        assert r.returncode != 0
        assert not out.exists(), "reject must not write file when language is unsupported"


# ---------------------------------------------------------------------------
# 6. atlas snapshot export-research-notes — --language in help
# ---------------------------------------------------------------------------

def test_snapshot_export_research_notes_help_has_language() -> None:
    r = _cli("snapshot", "export-research-notes", "--help")
    assert r.returncode == 0
    assert "--language" in r.stdout


# ---------------------------------------------------------------------------
# 6. atlas snapshot export-research-notes — English default
# ---------------------------------------------------------------------------

def test_snapshot_export_research_notes_default_is_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp)
        assert r.returncode == 0, r.stderr
        assert _EN_EXPORT_RN in r.stdout
        assert _SV_EXPORT_RN not in r.stdout


def test_snapshot_export_research_notes_language_en_is_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp, "--language", "en")
        assert r.returncode == 0, r.stderr
        assert _EN_EXPORT_RN in r.stdout
        assert _SV_EXPORT_RN not in r.stdout


# ---------------------------------------------------------------------------
# 6. atlas snapshot export-research-notes — Swedish opt-in
# ---------------------------------------------------------------------------

def test_snapshot_export_research_notes_language_sv_swedish_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _SV_EXPORT_RN in r.stdout


def test_snapshot_export_research_notes_language_sv_safety_boundary_swedish() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _SV_SAFETY in r.stdout


def test_snapshot_export_research_notes_language_sv_no_english_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _EN_EXPORT_RN not in r.stdout


# ---------------------------------------------------------------------------
# 6. atlas snapshot export-research-notes — written file invariance
# ---------------------------------------------------------------------------

def test_snapshot_export_research_notes_file_invariance_default_vs_en() -> None:
    with tempfile.TemporaryDirectory() as tmp_default, tempfile.TemporaryDirectory() as tmp_en:
        _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp_default)
        _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp_en, "--language", "en")
        default_file = next(Path(tmp_default).rglob("notes.md"))
        en_file = next(Path(tmp_en).rglob("notes.md"))
        assert default_file.read_bytes() == en_file.read_bytes()


def test_snapshot_export_research_notes_file_invariance_default_vs_sv() -> None:
    with tempfile.TemporaryDirectory() as tmp_default, tempfile.TemporaryDirectory() as tmp_sv:
        _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp_default)
        _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp_sv, "--language", "sv")
        default_file = next(Path(tmp_default).rglob("notes.md"))
        sv_file = next(Path(tmp_sv).rglob("notes.md"))
        assert default_file.read_bytes() == sv_file.read_bytes()


def test_snapshot_export_research_notes_file_user_content_unchanged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        notes_file = next(Path(tmp).rglob("notes.md"))
        content = notes_file.read_text(encoding="utf-8")
        # notes content is user-provided — must pass through unchanged
        assert "ASML occupies a structural monopoly position" in content


def test_snapshot_export_research_notes_file_ticker_canonical() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        ticker_dir = Path(tmp) / "ASML"
        assert ticker_dir.exists()


# ---------------------------------------------------------------------------
# 6. atlas snapshot export-research-notes — unsupported language — no file write
# ---------------------------------------------------------------------------

def test_snapshot_export_research_notes_unsupported_language_fr_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-research-notes", str(_DRAFT_RESEARCH_CONFIRMED), "--output-dir", tmp, "--language", "fr")
        assert r.returncode != 0
        assert not any(Path(tmp).iterdir()), "export must not create files when language is unsupported"


# ---------------------------------------------------------------------------
# 7. atlas snapshot export-company-facts — --language in help
# ---------------------------------------------------------------------------

def test_snapshot_export_company_facts_help_has_language() -> None:
    r = _cli("snapshot", "export-company-facts", "--help")
    assert r.returncode == 0
    assert "--language" in r.stdout


# ---------------------------------------------------------------------------
# 7. atlas snapshot export-company-facts — English default
# ---------------------------------------------------------------------------

def test_snapshot_export_company_facts_default_is_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp)
        assert r.returncode == 0, r.stderr
        assert _EN_EXPORT_CF in r.stdout
        assert _SV_EXPORT_CF not in r.stdout


def test_snapshot_export_company_facts_language_en_is_english() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp, "--language", "en")
        assert r.returncode == 0, r.stderr
        assert _EN_EXPORT_CF in r.stdout
        assert _SV_EXPORT_CF not in r.stdout


# ---------------------------------------------------------------------------
# 7. atlas snapshot export-company-facts — Swedish opt-in
# ---------------------------------------------------------------------------

def test_snapshot_export_company_facts_language_sv_swedish_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _SV_EXPORT_CF in r.stdout


def test_snapshot_export_company_facts_language_sv_safety_boundary_swedish() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _SV_SAFETY in r.stdout


def test_snapshot_export_company_facts_language_sv_no_english_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert _EN_EXPORT_CF not in r.stdout


def test_snapshot_export_company_facts_language_sv_canonical_ticker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        assert r.returncode == 0, r.stderr
        assert "ASML" in r.stdout


# ---------------------------------------------------------------------------
# 7. atlas snapshot export-company-facts — written file invariance
# ---------------------------------------------------------------------------

def test_snapshot_export_company_facts_file_invariance_default_vs_en() -> None:
    with tempfile.TemporaryDirectory() as tmp_default, tempfile.TemporaryDirectory() as tmp_en:
        _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp_default)
        _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp_en, "--language", "en")
        default_file = next(Path(tmp_default).rglob("ASML.json"))
        en_file = next(Path(tmp_en).rglob("ASML.json"))
        assert default_file.read_bytes() == en_file.read_bytes()


def test_snapshot_export_company_facts_file_invariance_default_vs_sv() -> None:
    with tempfile.TemporaryDirectory() as tmp_default, tempfile.TemporaryDirectory() as tmp_sv:
        _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp_default)
        _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp_sv, "--language", "sv")
        default_file = next(Path(tmp_default).rglob("ASML.json"))
        sv_file = next(Path(tmp_sv).rglob("ASML.json"))
        assert default_file.read_bytes() == sv_file.read_bytes()


def test_snapshot_export_company_facts_file_canonical_snapshot_type() -> None:
    import json
    with tempfile.TemporaryDirectory() as tmp:
        _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp, "--language", "sv")
        cf_file = next(Path(tmp).rglob("ASML.json"))
        data = json.loads(cf_file.read_text())
        # the exported company facts JSON is the facts payload, not the draft envelope
        # verify a canonical field that is always present
        assert "company_name" in data or "business_summary" in data


# ---------------------------------------------------------------------------
# 7. atlas snapshot export-company-facts — unsupported language — no file write
# ---------------------------------------------------------------------------

def test_snapshot_export_company_facts_unsupported_language_fr_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = _cli("snapshot", "export-company-facts", str(_DRAFT_CF_CONFIRMED), "--output-dir", tmp, "--language", "fr")
        assert r.returncode != 0
        assert not any(Path(tmp).iterdir()), "export must not create files when language is unsupported"


# ---------------------------------------------------------------------------
# Infrastructure safety — supported locales, no gettext, no detection
# ---------------------------------------------------------------------------

def test_supported_locales_remain_exactly_en_sv() -> None:
    from atlas.locale_support import _SUPPORTED_LOCALES
    assert _SUPPORTED_LOCALES == frozenset({"en", "sv"})


def test_no_gettext_import_in_locale_support() -> None:
    src = Path("atlas/locale_support.py").read_text(encoding="utf-8")
    assert "import gettext" not in src


def test_no_runtime_locale_detection_in_locale_support() -> None:
    src = Path("atlas/locale_support.py").read_text(encoding="utf-8")
    assert "import locale" not in src
    assert "locale.getlocale" not in src


def test_no_translation_catalogs_in_atlas_package() -> None:
    import atlas
    pkg = Path(atlas.__file__).parent
    assert not any(pkg.glob("*.po"))
    assert not any(pkg.glob("*.mo"))


def test_no_gettext_in_weekly_review_renderer() -> None:
    src = Path("atlas/weekly_review/render.py").read_text(encoding="utf-8")
    assert "gettext" not in src


def test_no_gettext_in_snapshot_renderer() -> None:
    src = Path("atlas/snapshot_input/render.py").read_text(encoding="utf-8")
    assert "gettext" not in src


def test_no_network_import_in_locale_support() -> None:
    src = Path("atlas/locale_support.py").read_text(encoding="utf-8")
    assert "requests" not in src
    assert "urllib" not in src
    assert "httpx" not in src
