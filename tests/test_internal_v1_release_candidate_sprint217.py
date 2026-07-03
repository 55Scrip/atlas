"""Sprint 217 — Internal v1 release candidate doc guardrail tests.

Checks:
- docs/InternalV1ReleaseCandidate.md exists
- references atlas weekly-review
- references all 10 section headings
- references usage guide
- avoids forbidden language (outside guardrail-definition context)
- README pointer remains present
- __version__ and __release_stage__ metadata present in atlas package
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
RC_DOC = REPO_ROOT / "docs" / "InternalV1ReleaseCandidate.md"
README = REPO_ROOT / "README.md"

FORBIDDEN_TERMS = [
    "buy", "sell", "strong buy", "strong sell", "price target", "target price",
    "urgent", "act now", "must buy", "must sell", "guaranteed", "will outperform",
    "financial advice",
]

REQUIRED_SECTION_HEADINGS = [
    "Review Scope",
    "Portfolio Context",
    "Watchlist Review",
    "Company Reviews Needing Attention",
    "Portfolio Fit and Suitability Notes",
    "Risk and Principle Guardrails",
    "Open Decisions",
    "Missing Evidence",
    "Follow-Up Questions",
    "Non-Actions / Reasons to Wait",
]


@pytest.fixture(scope="module")
def rc_text() -> str:
    return RC_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rc_lower(rc_text) -> str:
    return rc_text.lower()


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------


def test_rc_doc_exists():
    assert RC_DOC.exists(), f"RC doc not found at {RC_DOC}"


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------


def test_rc_doc_references_weekly_review_command(rc_text):
    assert "atlas weekly-review" in rc_text


def test_rc_doc_references_all_10_sections(rc_text):
    for heading in REQUIRED_SECTION_HEADINGS:
        assert heading in rc_text, f"RC doc missing section reference: {heading!r}"


def test_rc_doc_references_usage_guide(rc_text):
    assert "AtlasWeeklyReviewUsageGuide" in rc_text or "usage guide" in rc_text.lower()


def test_rc_doc_references_acceptance_criteria(rc_text):
    assert "Acceptance Criteria" in rc_text or "acceptance criteria" in rc_text.lower()


def test_rc_doc_references_all_criteria_met(rc_text):
    assert "All 24 acceptance criteria met" in rc_text or "criteria met" in rc_text.lower()


def test_rc_doc_references_known_limitations(rc_text):
    assert "limitation" in rc_text.lower()


def test_rc_doc_no_broker_claims(rc_lower):
    assert "avanza" not in rc_lower or "not part" in rc_lower or "excluded" in rc_lower


def test_rc_doc_references_no_recommendations(rc_lower):
    assert "recommendation" in rc_lower


def test_rc_doc_references_human_judgment(rc_text):
    assert "judgment" in rc_text.lower() or "human" in rc_text.lower()


# ---------------------------------------------------------------------------
# Forbidden language
# ---------------------------------------------------------------------------


def test_rc_doc_no_forbidden_language(rc_lower):
    for term in FORBIDDEN_TERMS:
        assert term not in rc_lower, f"Forbidden term {term!r} found in RC doc"


# ---------------------------------------------------------------------------
# README pointer still present
# ---------------------------------------------------------------------------


def test_readme_still_references_usage_guide():
    readme = README.read_text(encoding="utf-8")
    assert "AtlasWeeklyReviewUsageGuide" in readme


def test_readme_still_references_weekly_review():
    readme = README.read_text(encoding="utf-8")
    assert "weekly-review" in readme or "Weekly Review" in readme


# ---------------------------------------------------------------------------
# Version / release metadata
# ---------------------------------------------------------------------------


def test_atlas_version_string_present():
    import atlas
    assert hasattr(atlas, "__version__")
    assert atlas.__version__


def test_atlas_release_stage_present():
    import atlas
    assert hasattr(atlas, "__release_stage__")
    assert "v1" in atlas.__release_stage__.lower() or "rc" in atlas.__release_stage__.lower()


def test_atlas_version_is_string():
    import atlas
    assert isinstance(atlas.__version__, str)
