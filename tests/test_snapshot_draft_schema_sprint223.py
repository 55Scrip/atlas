"""Sprint 223 — Snapshot Draft schema tests.

Tests cover: enum completeness, SnapshotDraft construction, field defaults,
validation rules, round-trip serialization, file helpers, example drafts,
language guardrails, and provider/network boundary.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

import pytest

from atlas.snapshot_input.schema import (
    SnapshotConfidence,
    SnapshotConfirmationStatus,
    SnapshotDraft,
    SnapshotType,
    load_snapshot_draft,
    save_snapshot_draft,
    validate_snapshot_draft,
)

EXAMPLES_DIR = Path("examples/snapshot_drafts")

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


def _minimal_draft(**kwargs) -> SnapshotDraft:
    defaults = dict(
        draft_id="draft-test-001",
        snapshot_type=SnapshotType.PORTFOLIO_SNAPSHOT,
        source_description="Test source",
        extracted_fields={"account_name": "Test"},
        uncertainties=[],
        missing_required_fields=[],
        confirmation_status=SnapshotConfirmationStatus.DRAFT,
        target_local_file="portfolio.json",
        created_at="2026-01-05",
    )
    defaults.update(kwargs)
    return SnapshotDraft(**defaults)


# ---------------------------------------------------------------------------
# SnapshotType enum
# ---------------------------------------------------------------------------

def test_snapshot_type_portfolio():
    assert SnapshotType.PORTFOLIO_SNAPSHOT.value == "portfolio_snapshot"

def test_snapshot_type_watchlist():
    assert SnapshotType.WATCHLIST_SNAPSHOT.value == "watchlist_snapshot"

def test_snapshot_type_open_orders():
    assert SnapshotType.OPEN_ORDERS_SNAPSHOT.value == "open_orders_snapshot"

def test_snapshot_type_news():
    assert SnapshotType.NEWS_SNAPSHOT.value == "news_snapshot"

def test_snapshot_type_external_analysis():
    assert SnapshotType.EXTERNAL_ANALYSIS_SNAPSHOT.value == "external_analysis_snapshot"

def test_snapshot_type_research_notes():
    assert SnapshotType.RESEARCH_NOTES_SNAPSHOT.value == "research_notes_snapshot"

def test_snapshot_type_company_facts():
    assert SnapshotType.COMPANY_FACTS_SNAPSHOT.value == "company_facts_snapshot"

def test_snapshot_type_unknown():
    assert SnapshotType.UNKNOWN_SNAPSHOT.value == "unknown_snapshot"

def test_snapshot_type_has_eight_members():
    assert len(SnapshotType) == 8

def test_snapshot_type_all_sprint221_types_present():
    expected = {
        "portfolio_snapshot", "watchlist_snapshot", "open_orders_snapshot",
        "news_snapshot", "external_analysis_snapshot", "research_notes_snapshot",
        "company_facts_snapshot", "unknown_snapshot",
    }
    assert {t.value for t in SnapshotType} == expected


# ---------------------------------------------------------------------------
# SnapshotConfirmationStatus enum
# ---------------------------------------------------------------------------

def test_confirmation_status_draft():
    assert SnapshotConfirmationStatus.DRAFT.value == "draft"

def test_confirmation_status_needs_user_review():
    assert SnapshotConfirmationStatus.NEEDS_USER_REVIEW.value == "needs_user_review"

def test_confirmation_status_confirmed():
    assert SnapshotConfirmationStatus.CONFIRMED.value == "confirmed"

def test_confirmation_status_rejected():
    assert SnapshotConfirmationStatus.REJECTED.value == "rejected"

def test_confirmation_status_superseded():
    assert SnapshotConfirmationStatus.SUPERSEDED.value == "superseded"

def test_confirmation_status_has_five_members():
    assert len(SnapshotConfirmationStatus) == 5


# ---------------------------------------------------------------------------
# SnapshotConfidence enum
# ---------------------------------------------------------------------------

def test_confidence_low():
    assert SnapshotConfidence.LOW.value == "low"

def test_confidence_medium():
    assert SnapshotConfidence.MEDIUM.value == "medium"

def test_confidence_high():
    assert SnapshotConfidence.HIGH.value == "high"

def test_confidence_unknown():
    assert SnapshotConfidence.UNKNOWN.value == "unknown"

def test_confidence_has_four_members():
    assert len(SnapshotConfidence) == 4


# ---------------------------------------------------------------------------
# SnapshotDraft construction
# ---------------------------------------------------------------------------

def test_minimal_draft_constructs():
    draft = _minimal_draft()
    assert draft.draft_id == "draft-test-001"
    assert draft.snapshot_type == SnapshotType.PORTFOLIO_SNAPSHOT
    assert draft.source_description == "Test source"
    assert draft.confirmation_status == SnapshotConfirmationStatus.DRAFT
    assert draft.target_local_file == "portfolio.json"
    assert draft.created_at == "2026-01-05"


def test_draft_optional_defaults():
    draft = _minimal_draft()
    assert draft.confidence == SnapshotConfidence.UNKNOWN
    assert draft.related_tickers == []
    assert draft.raw_source_reference == ""
    assert draft.notes == ""


def test_draft_with_all_fields():
    draft = _minimal_draft(
        confidence=SnapshotConfidence.MEDIUM,
        related_tickers=["ASML", "msft"],
        raw_source_reference="my_notes.txt",
        notes="Some notes.",
        uncertainties=["Currency unclear"],
        missing_required_fields=["cost_basis"],
    )
    assert draft.confidence == SnapshotConfidence.MEDIUM
    assert "ASML" in draft.related_tickers
    assert draft.raw_source_reference == "my_notes.txt"


def test_related_tickers_normalized_to_uppercase():
    draft = _minimal_draft(related_tickers=["asml", "Msft", "xyl"])
    assert draft.related_tickers == ["ASML", "MSFT", "XYL"]


def test_related_tickers_strips_whitespace():
    draft = _minimal_draft(related_tickers=["  ASML  ", " msft"])
    assert "ASML" in draft.related_tickers
    assert "MSFT" in draft.related_tickers


def test_draft_accepts_empty_uncertainties():
    draft = _minimal_draft(uncertainties=[])
    assert draft.uncertainties == []


def test_draft_accepts_populated_uncertainties():
    draft = _minimal_draft(uncertainties=["Currency unclear", "Sector inferred"])
    assert len(draft.uncertainties) == 2


def test_draft_all_snapshot_types_constructible():
    for stype in SnapshotType:
        draft = _minimal_draft(snapshot_type=stype)
        assert draft.snapshot_type == stype


# ---------------------------------------------------------------------------
# Validation — required fields
# ---------------------------------------------------------------------------

def test_validation_rejects_empty_draft_id():
    with pytest.raises(ValueError, match="draft_id"):
        _minimal_draft(draft_id="")


def test_validation_rejects_whitespace_draft_id():
    with pytest.raises(ValueError, match="draft_id"):
        _minimal_draft(draft_id="   ")


def test_validation_rejects_empty_source_description():
    with pytest.raises(ValueError, match="source_description"):
        _minimal_draft(source_description="")


def test_validation_rejects_non_dict_extracted_fields():
    with pytest.raises(ValueError, match="extracted_fields"):
        _minimal_draft(extracted_fields=["not", "a", "dict"])  # type: ignore


def test_validation_rejects_empty_target_local_file():
    with pytest.raises(ValueError, match="target_local_file"):
        _minimal_draft(target_local_file="")


def test_validation_rejects_empty_created_at():
    with pytest.raises(ValueError, match="created_at"):
        _minimal_draft(created_at="")


def test_validation_rejects_invalid_snapshot_type():
    with pytest.raises((ValueError, Exception)):
        _minimal_draft(snapshot_type="not_a_type")  # type: ignore


def test_validation_rejects_invalid_confirmation_status():
    with pytest.raises((ValueError, Exception)):
        _minimal_draft(confirmation_status="not_a_status")  # type: ignore


def test_validate_snapshot_draft_callable_explicitly():
    draft = _minimal_draft()
    validate_snapshot_draft(draft)  # Should not raise


# ---------------------------------------------------------------------------
# Serialization — to_dict / from_dict
# ---------------------------------------------------------------------------

def test_to_dict_contains_required_keys():
    draft = _minimal_draft()
    d = draft.to_dict()
    for key in ("draft_id", "snapshot_type", "source_description", "extracted_fields",
                "uncertainties", "missing_required_fields", "confirmation_status",
                "target_local_file", "created_at"):
        assert key in d, f"Missing key in to_dict: {key}"


def test_to_dict_snapshot_type_is_string():
    draft = _minimal_draft()
    d = draft.to_dict()
    assert isinstance(d["snapshot_type"], str)
    assert d["snapshot_type"] == "portfolio_snapshot"


def test_to_dict_confirmation_status_is_string():
    draft = _minimal_draft()
    d = draft.to_dict()
    assert isinstance(d["confirmation_status"], str)
    assert d["confirmation_status"] == "draft"


def test_from_dict_round_trip():
    original = _minimal_draft(
        uncertainties=["Currency unclear"],
        missing_required_fields=["cost_basis"],
        related_tickers=["ASML"],
        confidence=SnapshotConfidence.MEDIUM,
    )
    restored = SnapshotDraft.from_dict(original.to_dict())
    assert restored.draft_id == original.draft_id
    assert restored.snapshot_type == original.snapshot_type
    assert restored.uncertainties == original.uncertainties
    assert restored.missing_required_fields == original.missing_required_fields
    assert restored.related_tickers == original.related_tickers
    assert restored.confidence == original.confidence


def test_from_dict_rejects_missing_snapshot_type():
    d = _minimal_draft().to_dict()
    del d["snapshot_type"]
    with pytest.raises(ValueError, match="snapshot_type"):
        SnapshotDraft.from_dict(d)


def test_from_dict_rejects_invalid_snapshot_type():
    d = _minimal_draft().to_dict()
    d["snapshot_type"] = "not_a_type"
    with pytest.raises(ValueError, match="snapshot_type"):
        SnapshotDraft.from_dict(d)


def test_from_dict_rejects_invalid_confirmation_status():
    d = _minimal_draft().to_dict()
    d["confirmation_status"] = "not_a_status"
    with pytest.raises(ValueError, match="confirmation_status"):
        SnapshotDraft.from_dict(d)


def test_from_dict_defaults_confidence_to_unknown_on_invalid():
    d = _minimal_draft().to_dict()
    d["confidence"] = "not_a_confidence"
    restored = SnapshotDraft.from_dict(d)
    assert restored.confidence == SnapshotConfidence.UNKNOWN


# ---------------------------------------------------------------------------
# Serialization — to_json / from_json
# ---------------------------------------------------------------------------

def test_to_json_produces_valid_json():
    draft = _minimal_draft()
    text = draft.to_json()
    parsed = json.loads(text)
    assert isinstance(parsed, dict)


def test_to_json_snapshot_type_is_string():
    text = _minimal_draft().to_json()
    parsed = json.loads(text)
    assert parsed["snapshot_type"] == "portfolio_snapshot"


def test_from_json_round_trip():
    original = _minimal_draft(uncertainties=["Sector unclear"])
    restored = SnapshotDraft.from_json(original.to_json())
    assert restored.draft_id == original.draft_id
    assert restored.uncertainties == original.uncertainties


def test_to_json_is_deterministic():
    draft = _minimal_draft(related_tickers=["MSFT", "ASML"], uncertainties=["u1", "u2"])
    assert draft.to_json() == draft.to_json()


def test_from_json_rejects_non_object():
    with pytest.raises(ValueError):
        SnapshotDraft.from_json('["not", "an", "object"]')


def test_from_json_rejects_invalid_json():
    with pytest.raises(ValueError):
        SnapshotDraft.from_json("not json at all {{{")


# ---------------------------------------------------------------------------
# File helpers — load / save
# ---------------------------------------------------------------------------

def test_save_and_load_round_trip(tmp_path):
    draft = _minimal_draft(
        uncertainties=["Currency unclear"],
        related_tickers=["ASML"],
    )
    path = tmp_path / "test_draft.json"
    save_snapshot_draft(path, draft)
    assert path.exists()
    loaded = load_snapshot_draft(path)
    assert loaded.draft_id == draft.draft_id
    assert loaded.uncertainties == draft.uncertainties
    assert loaded.related_tickers == draft.related_tickers


def test_save_creates_parent_directories(tmp_path):
    draft = _minimal_draft()
    path = tmp_path / "subdir" / "nested" / "draft.json"
    save_snapshot_draft(path, draft)
    assert path.exists()


def test_load_raises_on_missing_file(tmp_path):
    with pytest.raises(OSError):
        load_snapshot_draft(tmp_path / "nonexistent.json")


def test_save_writes_valid_json(tmp_path):
    draft = _minimal_draft()
    path = tmp_path / "draft.json"
    save_snapshot_draft(path, draft)
    text = path.read_text(encoding="utf-8")
    parsed = json.loads(text)
    assert isinstance(parsed, dict)
    assert parsed["draft_id"] == "draft-test-001"


# ---------------------------------------------------------------------------
# Example draft files
# ---------------------------------------------------------------------------

def _load_example(filename: str) -> SnapshotDraft:
    return load_snapshot_draft(EXAMPLES_DIR / filename)


def test_example_portfolio_snapshot_loads():
    if not (EXAMPLES_DIR / "portfolio_snapshot.json").exists():
        pytest.skip("portfolio_snapshot.json not found")
    draft = _load_example("portfolio_snapshot.json")
    assert draft.snapshot_type == SnapshotType.PORTFOLIO_SNAPSHOT


def test_example_research_notes_snapshot_loads():
    if not (EXAMPLES_DIR / "research_notes_snapshot.json").exists():
        pytest.skip("research_notes_snapshot.json not found")
    draft = _load_example("research_notes_snapshot.json")
    assert draft.snapshot_type == SnapshotType.RESEARCH_NOTES_SNAPSHOT


def test_example_news_snapshot_loads():
    if not (EXAMPLES_DIR / "news_snapshot.json").exists():
        pytest.skip("news_snapshot.json not found")
    draft = _load_example("news_snapshot.json")
    assert draft.snapshot_type == SnapshotType.NEWS_SNAPSHOT


def test_example_drafts_have_non_empty_draft_id():
    for f in EXAMPLES_DIR.glob("*.json"):
        draft = load_snapshot_draft(f)
        assert draft.draft_id, f"Empty draft_id in {f.name}"


def test_example_drafts_have_valid_target_local_file():
    for f in EXAMPLES_DIR.glob("*.json"):
        draft = load_snapshot_draft(f)
        assert draft.target_local_file, f"Empty target_local_file in {f.name}"


def test_example_drafts_are_valid():
    for f in EXAMPLES_DIR.glob("*.json"):
        draft = load_snapshot_draft(f)
        validate_snapshot_draft(draft)  # Should not raise


def test_example_drafts_have_related_tickers_uppercased():
    for f in EXAMPLES_DIR.glob("*.json"):
        draft = load_snapshot_draft(f)
        for t in draft.related_tickers:
            assert t == t.upper(), f"Ticker not uppercased in {f.name}: {t!r}"


# ---------------------------------------------------------------------------
# Language guardrails
# ---------------------------------------------------------------------------

def test_no_forbidden_language_in_example_drafts():
    for f in EXAMPLES_DIR.glob("*.json"):
        content = f.read_text(encoding="utf-8")
        for term in FORBIDDEN_LANGUAGE:
            assert term not in content, f"Forbidden language '{term}' in {f.name}"


def test_no_forbidden_language_in_schema_module():
    import atlas.snapshot_input.schema as mod
    source = inspect.getsource(mod)
    # Docstrings and comments may reference forbidden terms as documentation of what
    # NOT to do — but field names and literal output strings must not use them.
    # We check that no forbidden term appears outside of quoted strings in docstrings.
    for term in FORBIDDEN_LANGUAGE:
        # We skip "Entry" and "Exit" as they're common in non-financial contexts,
        # but check the rest are absent
        if term in ("Entry", "Exit"):
            continue
        assert term not in source, f"Forbidden language '{term}' in schema.py"


# ---------------------------------------------------------------------------
# Provider / network boundary
# ---------------------------------------------------------------------------

def test_no_provider_imports_in_schema():
    import atlas.snapshot_input.schema as mod
    source = inspect.getsource(mod)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for alias in node.names:
                names.append(alias.name)
            for name in names:
                assert "providers" not in name, f"Provider import in schema.py: {name}"
                assert "requests" not in name, f"Network import: {name}"
                assert "urllib" not in name, f"Network import: {name}"
                assert "httpx" not in name, f"Network import: {name}"


def test_no_provider_imports_in_init():
    import atlas.snapshot_input as pkg
    source = inspect.getsource(pkg)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            for alias in node.names:
                names.append(alias.name)
            for name in names:
                assert "providers" not in name, f"Provider import in __init__.py: {name}"


# ---------------------------------------------------------------------------
# Package exports
# ---------------------------------------------------------------------------

def test_package_exports_snapshot_type():
    from atlas.snapshot_input import SnapshotType as ST
    assert ST is SnapshotType


def test_package_exports_confirmation_status():
    from atlas.snapshot_input import SnapshotConfirmationStatus as SCS
    assert SCS is SnapshotConfirmationStatus


def test_package_exports_snapshot_draft():
    from atlas.snapshot_input import SnapshotDraft as SD
    assert SD is SnapshotDraft


def test_package_exports_confidence():
    from atlas.snapshot_input import SnapshotConfidence as SC
    assert SC is SnapshotConfidence


def test_package_exports_file_helpers():
    from atlas.snapshot_input import load_snapshot_draft as lsd, save_snapshot_draft as ssd
    assert callable(lsd)
    assert callable(ssd)
