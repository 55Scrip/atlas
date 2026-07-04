"""Sprint 235 — Internal v1 Demo Package tests.

Checks that the demo package document and script are present, complete,
and free of forbidden language. No brittle prose matching.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DEMO_DOC = Path("docs/InternalV1DemoPackage.md")
DEMO_SCRIPT = Path("scripts/run_internal_v1_demo.sh")

REQUIRED_COMMANDS = [
    "atlas snapshot validate",
    "atlas snapshot review",
    "atlas snapshot confirm",
    "atlas snapshot reject",
    "atlas snapshot export-research-notes",
    "atlas snapshot export-company-facts",
    "atlas weekly-review",
]

REQUIRED_TMP_PATHS = [
    "/tmp/",
]

REQUIRED_SAFETY_TERMS = [
    "no network",
    "no broker",
    "no external api",
    "no ai",
    "no ocr",
]

FORBIDDEN_LANGUAGE = [
    "Strong Buy",
    "Strong Sell",
    "Price Target",
    "Target Price",
    "Act Now",
    "Must Buy",
    "Must Sell",
    "Guaranteed",
    "Will Outperform",
    "Financial Advice",
]

OUT_OF_SCOPE_ITEMS = [
    "portfolio",
    "watchlist",
    "journal",
    "OCR",
    "AI",
    "broker",
]


# ---------------------------------------------------------------------------
# Demo package document
# ---------------------------------------------------------------------------

def test_demo_doc_exists():
    assert DEMO_DOC.exists(), f"{DEMO_DOC} not found"


def test_demo_doc_is_nonempty():
    assert len(DEMO_DOC.read_text(encoding="utf-8").strip()) > 0


def test_demo_doc_includes_all_commands():
    content = DEMO_DOC.read_text(encoding="utf-8")
    for cmd in REQUIRED_COMMANDS:
        assert cmd in content, f"Missing command in demo doc: {cmd}"


def test_demo_doc_includes_tmp_output_path():
    content = DEMO_DOC.read_text(encoding="utf-8")
    for path in REQUIRED_TMP_PATHS:
        assert path in content, f"Missing tmp path in demo doc: {path}"


def test_demo_doc_includes_safety_boundary_section():
    content = DEMO_DOC.read_text(encoding="utf-8").lower()
    for term in REQUIRED_SAFETY_TERMS:
        assert term in content, f"Missing safety term in demo doc: {term!r}"


def test_demo_doc_includes_out_of_scope_section():
    content = DEMO_DOC.read_text(encoding="utf-8")
    for item in OUT_OF_SCOPE_ITEMS:
        assert item in content, f"Missing out-of-scope item in demo doc: {item!r}"


def test_demo_doc_includes_cleanup_instructions():
    content = DEMO_DOC.read_text(encoding="utf-8")
    assert "rm -rf" in content or "clean" in content.lower()


def test_demo_doc_no_forbidden_language():
    content = DEMO_DOC.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in demo doc: {term!r}"


def test_demo_doc_includes_user_journey_narrative():
    content = DEMO_DOC.read_text(encoding="utf-8").lower()
    assert "snapshot draft" in content
    assert "confirmed" in content
    assert "weekly review" in content or "weekly investment review" in content


def test_demo_doc_includes_expected_checkpoints():
    content = DEMO_DOC.read_text(encoding="utf-8")
    assert "Status: valid" in content
    assert "Status: confirmed" in content
    assert "Status: rejected" in content
    assert "Status: written" in content


def test_demo_doc_mentions_related_documents():
    content = DEMO_DOC.read_text(encoding="utf-8")
    assert "AtlasWeeklyReviewUsageGuide" in content
    assert "AtlasSnapshotInputWorkflow" in content
    assert "InternalV1ReleaseCandidate" in content


# ---------------------------------------------------------------------------
# Demo script
# ---------------------------------------------------------------------------

def test_demo_script_exists():
    assert DEMO_SCRIPT.exists(), f"{DEMO_SCRIPT} not found"


def test_demo_script_is_bash():
    first_line = DEMO_SCRIPT.read_text(encoding="utf-8").splitlines()[0]
    assert "bash" in first_line or "sh" in first_line


def test_demo_script_has_strict_mode():
    content = DEMO_SCRIPT.read_text(encoding="utf-8")
    assert "set -e" in content


def test_demo_script_writes_only_to_tmp():
    content = DEMO_SCRIPT.read_text(encoding="utf-8")
    assert "/tmp/" in content
    # Script must not write to examples/ directly
    assert "examples/weekly_review/portfolio.json" in content  # reads only
    assert "> examples/" not in content


def test_demo_script_includes_all_commands():
    content = DEMO_SCRIPT.read_text(encoding="utf-8")
    # Script uses $ATLAS variable instead of the literal "atlas" prefix.
    script_commands = [cmd.replace("atlas ", "") for cmd in REQUIRED_COMMANDS]
    for cmd in script_commands:
        assert cmd in content, f"Missing command in demo script: {cmd}"


def test_demo_script_no_network_calls():
    content = DEMO_SCRIPT.read_text(encoding="utf-8")
    for net_term in ("curl", "wget", "http://", "https://"):
        assert net_term not in content, f"Network call found in demo script: {net_term!r}"


def test_demo_script_no_forbidden_language():
    content = DEMO_SCRIPT.read_text(encoding="utf-8")
    for term in FORBIDDEN_LANGUAGE:
        assert term not in content, f"Forbidden language in demo script: {term!r}"


def test_demo_script_includes_cleanup_reference():
    content = DEMO_SCRIPT.read_text(encoding="utf-8")
    assert "rm -rf" in content


def test_demo_script_verifies_file_presence():
    content = DEMO_SCRIPT.read_text(encoding="utf-8")
    # Script should check output files exist
    assert "-f " in content or "[ -f" in content


def test_demo_script_verifies_reject_blocks_export():
    content = DEMO_SCRIPT.read_text(encoding="utf-8")
    # Script should verify that export from rejected draft is blocked
    assert "rejected" in content
    assert "blocked" in content or "export-research-notes" in content


# ---------------------------------------------------------------------------
# Demo output files are not committed (ephemeral)
# ---------------------------------------------------------------------------

def test_no_tmp_demo_files_in_repository():
    """Demo writes to /tmp — no output files should be committed to the repo."""
    for path in Path(".").rglob("atlas_internal_v1_demo"):
        assert not path.exists(), f"Demo output found in repository: {path}"


# ---------------------------------------------------------------------------
# Regression — core commands still reachable
# ---------------------------------------------------------------------------

def test_all_snapshot_commands_exist_in_main():
    import atlas.cli.main as main_mod
    source = Path(main_mod.__file__).read_text(encoding="utf-8")
    for cmd in ("validate", "review", "confirm", "reject", "export-research-notes", "export-company-facts"):
        assert cmd in source, f"Command missing from CLI: {cmd}"
