"""Boundary tests scoped to `atlas.analysis_engine` itself (ATLAS-020
Phase 2). Complements the repository-wide static guardrails in
`tests/test_architecture_boundaries.py`
(`test_core_does_not_import_atlas_analysis_engine` and
`test_analysis_engine_only_reads_core_and_decision_engine`), mirroring
`tests/unit/decision_engine/test_boundaries.py`'s own per-package
substring scan so a reviewer can see the forbidden dependencies
enumerated in one place, scoped to this package.
"""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "atlas" / "analysis_engine"

_FORBIDDEN_SUBSTRINGS = (
    "import requests",
    "import httpx",
    "import aiohttp",
    "import urllib.request",
    "window.fetch(",
    "await fetch(",
    "import openai",
    "import anthropic",
    "import sqlalchemy",
    "import sqlite3",
    "import psycopg",
    "import react",
    "from react",
    "document.getElementById",
    "document.querySelector",
    "window.",
    "localStorage",
)


def _source_files() -> list[Path]:
    return [p for p in _PACKAGE_DIR.rglob("*.py") if "__pycache__" not in p.parts]


class TestNoForbiddenDependencies:
    def test_no_forbidden_substrings_anywhere_in_the_package(self):
        violations: list[str] = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            for needle in _FORBIDDEN_SUBSTRINGS:
                if needle in text:
                    violations.append(f"{path.name} contains {needle!r}")
        assert not violations, "Forbidden dependency found:\n" + "\n".join(violations)

    def test_no_wall_clock_calls_inside_the_package(self):
        """Every timestamp (`generated_at`, `Provenance.computed_at`) is
        caller-supplied -- the same determinism rule
        `atlas.decision_engine` already enforces for itself."""
        violations: list[str] = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            if "datetime.now(" in text or "datetime.utcnow(" in text or "time.time(" in text:
                violations.append(path.name)
        assert not violations, "Wall-clock call found in:\n" + "\n".join(violations)

    def test_package_contains_at_least_the_expected_modules(self):
        names = {p.name for p in _source_files()}
        for expected in (
            "__init__.py",
            "contracts.py",
            "provenance.py",
            "findings.py",
            "confidence.py",
            "conviction.py",
            "recommendation.py",
            "models.py",
            "pipeline.py",
            "lifecycle.py",
            "business.py",
            "exceptions.py",
        ):
            assert expected in names, f"{expected} missing from atlas/analysis_engine/"
