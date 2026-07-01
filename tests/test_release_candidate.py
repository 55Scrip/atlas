"""Sprint 67: Release candidate documentation and constraint verification tests.

Lightweight static checks that the RC1 deliverables exist and contain required
content. These tests do not run the demo or import Atlas modules — they scan
text files, keeping the suite fast and stable.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DOCS = REPO_ROOT / "docs"
RC_DOC = DOCS / "ReleaseCandidate.md"
README = REPO_ROOT / "README.md"
ARCH_DOC = DOCS / "ArchitectureConsolidation.md"
DECISION_LOG = DOCS / "DecisionLog.md"

FORBIDDEN_TERMS = (
    "strong buy",
    "strong sell",
    "price target",
    "outperform",
    "market-beating",
    "must act",
    "guaranteed",
    "risk-free",
)


# ── release candidate document ─────────────────────────────────────────────────


def test_release_candidate_doc_exists() -> None:
    assert RC_DOC.exists(), f"docs/ReleaseCandidate.md not found"


def test_release_candidate_has_version() -> None:
    content = RC_DOC.read_text()
    assert "v0.1.0" in content or "RC1" in content or "Release Candidate" in content


def test_release_candidate_documents_test_command() -> None:
    content = RC_DOC.read_text()
    assert "pytest" in content


def test_release_candidate_documents_demo_command() -> None:
    content = RC_DOC.read_text()
    assert "run_daily_brief_demo.sh" in content


def test_release_candidate_has_release_checklist() -> None:
    content = RC_DOC.read_text()
    assert "checklist" in content.lower() or "- [x]" in content or "- [ ]" in content


def test_release_candidate_documents_known_limitations() -> None:
    content = RC_DOC.read_text()
    assert "limitation" in content.lower() or "Known Limitation" in content


def test_release_candidate_documents_technical_debt() -> None:
    content = RC_DOC.read_text()
    assert "technical debt" in content.lower() or "Technical Debt" in content


def test_release_candidate_has_no_recommendation_language() -> None:
    content = RC_DOC.read_text().lower()
    for term in FORBIDDEN_TERMS:
        assert term not in content, f"Forbidden term {term!r} in ReleaseCandidate.md"


def test_release_candidate_references_architecture_doc() -> None:
    content = RC_DOC.read_text()
    assert "ArchitectureConsolidation" in content or "architecture" in content.lower()


def test_release_candidate_has_next_phase_recommendation() -> None:
    content = RC_DOC.read_text()
    assert "next" in content.lower() and ("phase" in content.lower() or "sprint" in content.lower())


# ── README ─────────────────────────────────────────────────────────────────────


def test_readme_has_what_atlas_is_section() -> None:
    content = README.read_text()
    assert "What Atlas Is" in content


def test_readme_has_what_atlas_is_not_section() -> None:
    content = README.read_text()
    assert "What Atlas Is Not" in content


def test_readme_references_no_ai_constraint() -> None:
    content = README.read_text()
    assert "No AI" in content or "no AI" in content or "Does not use AI" in content


def test_readme_references_no_external_apis() -> None:
    content = README.read_text()
    assert "external API" in content or "no external" in content.lower()


def test_readme_references_demo_readme() -> None:
    content = README.read_text()
    assert "daily_brief_demo/README.md" in content or "examples/daily_brief_demo" in content


def test_readme_references_architecture_docs() -> None:
    content = README.read_text()
    assert "ArchitectureConsolidation" in content or "docs/Architecture" in content


def test_readme_references_decision_log() -> None:
    content = README.read_text()
    assert "DecisionLog" in content


def test_readme_has_install_section() -> None:
    content = README.read_text()
    assert "pip install" in content


def test_readme_has_test_command() -> None:
    content = README.read_text()
    assert "pytest" in content


def test_readme_has_demo_command() -> None:
    content = README.read_text()
    assert "run_daily_brief_demo.sh" in content


def test_readme_has_no_recommendation_language() -> None:
    # Check the developer-facing top section only (first 120 lines)
    lines = README.read_text().splitlines()[:120]
    top = "\n".join(lines).lower()
    for term in FORBIDDEN_TERMS:
        assert term not in top, f"Forbidden term {term!r} in README top section"


def test_readme_has_capability_map() -> None:
    content = README.read_text()
    assert "Company Analysis" in content
    assert "Daily Brief" in content
    assert "Watchlist Intelligence" in content


def test_readme_has_historical_separator() -> None:
    content = README.read_text()
    assert "Historical Sprint Notes" in content or "historical" in content.lower()


# ── architecture consolidation doc ────────────────────────────────────────────


def test_architecture_consolidation_doc_exists() -> None:
    assert ARCH_DOC.exists()


def test_architecture_consolidation_updated_for_rc1() -> None:
    content = ARCH_DOC.read_text()
    assert "Sprint 67" in content or "RC1" in content or "67" in content


# ── decision log ──────────────────────────────────────────────────────────────


def test_decision_log_exists() -> None:
    assert DECISION_LOG.exists()


def test_decision_log_has_sprint_67_entry() -> None:
    content = DECISION_LOG.read_text()
    assert "Sprint 67" in content


def test_decision_log_has_sprint_68_entry() -> None:
    content = DECISION_LOG.read_text()
    assert "Sprint 68" in content


# ── Sprint 68: verification script ────────────────────────────────────────────

VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_release_candidate.sh"


def test_verify_script_exists() -> None:
    assert VERIFY_SCRIPT.exists(), "scripts/verify_release_candidate.sh not found"


def test_verify_script_does_not_call_network_tools() -> None:
    content = VERIFY_SCRIPT.read_text()
    assert "curl" not in content
    assert "wget" not in content


def test_verify_script_does_not_use_python_one_liners() -> None:
    content = VERIFY_SCRIPT.read_text()
    assert "python3 -c" not in content
    assert "python -c" not in content


def test_verify_script_has_set_euo_pipefail() -> None:
    content = VERIFY_SCRIPT.read_text()
    assert "set -euo pipefail" in content


def test_verify_script_runs_pytest() -> None:
    content = VERIFY_SCRIPT.read_text()
    assert "pytest" in content


def test_verify_script_runs_demo() -> None:
    content = VERIFY_SCRIPT.read_text()
    assert "run_daily_brief_demo.sh" in content


def test_verify_script_checks_forbidden_language() -> None:
    content = VERIFY_SCRIPT.read_text()
    assert "forbidden" in content.lower() or "FORBIDDEN" in content


def test_verify_script_cleans_up_after_itself() -> None:
    content = VERIFY_SCRIPT.read_text()
    assert "rm -rf" in content


def test_release_candidate_doc_references_verify_script() -> None:
    content = RC_DOC.read_text()
    assert "verify_release_candidate.sh" in content


# ── Sprint 71: RC2 verification tests ─────────────────────────────────────────

DEMO_README = REPO_ROOT / "examples" / "daily_brief_demo" / "README.md"
DAILY_BRIEF_DOC = DOCS / "DailyBrief.md"
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_release_candidate.sh"


def test_rc_doc_contains_rc2_section() -> None:
    content = RC_DOC.read_text()
    assert "Release Candidate 2" in content or "rc2" in content.lower()


def test_rc_doc_mentions_all_five_input_surfaces() -> None:
    content = RC_DOC.read_text()
    for surface in ("portfolio", "research", "watchlist", "discovery", "company analysis"):
        assert surface.lower() in content.lower(), f"RC doc missing input surface: {surface}"


def test_rc_doc_mentions_evidence_link_resolution() -> None:
    content = RC_DOC.read_text()
    assert "evidence link" in content.lower() or "company-amd" in content


def test_rc_doc_mentions_947_tests() -> None:
    content = RC_DOC.read_text()
    assert "947" in content


def test_rc_doc_no_stale_false_negative_limitation() -> None:
    content = RC_DOC.read_text()
    assert "No knowledge facts are linked" not in content or "Resolved since RC1" in content


def test_demo_readme_mentions_knowledge_flag_for_watchlist() -> None:
    content = DEMO_README.read_text()
    assert "--knowledge" in content


def test_demo_readme_no_stale_false_negative_output() -> None:
    content = DEMO_README.read_text()
    assert "No knowledge facts are linked" not in content


def test_readme_mentions_rc2() -> None:
    content = README.read_text()
    assert "RC2" in content or "Release Candidate 2" in content


def test_readme_mentions_947_tests() -> None:
    content = README.read_text()
    assert "947" in content


def test_verify_script_says_rc2() -> None:
    content = VERIFY_SCRIPT.read_text()
    assert "RC2" in content


def test_rc_doc_no_recommendation_language() -> None:
    content = RC_DOC.read_text().lower()
    for term in ("strong buy", "price target", "outperform", "must act", "guaranteed", "risk-free"):
        assert term not in content, f"Forbidden term {term!r} found in RC doc"


def test_daily_brief_doc_mentions_evidence_link_resolution() -> None:
    content = DAILY_BRIEF_DOC.read_text()
    assert "Evidence Link Resolution" in content or "company-amd" in content
