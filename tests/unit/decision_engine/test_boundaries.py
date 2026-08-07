"""Boundary tests scoped to `atlas.decision_engine` itself (Sprint Phase
8). Complements the repository-wide static guardrails in
`tests/test_architecture_boundaries.py`
(`test_core_does_not_import_atlas_decision_engine` and
`test_decision_engine_only_reads_core_domain_entities`), which already
enforce the one-way-read-from-Core boundary via import scanning. This
file checks the specific forbidden dependencies the Sprint names by
category, so a reviewer can see them enumerated in one place.
"""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "atlas" / "decision_engine"

_FORBIDDEN_SUBSTRINGS = (
    # No network calls.
    "import requests",
    "import httpx",
    "import aiohttp",
    "import urllib.request",
    "fetch(",
    # No AI / LLM dependencies.
    "import openai",
    "import anthropic",
    # No persistence.
    "import sqlalchemy",
    "import sqlite3",
    "import psycopg",
    # No browser / UI dependencies.
    "import react",
    "from react",
    "document.",
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
        """Phase 7: "contain no current-time calls inside the stage."
        `datetime.now()` / `datetime.utcnow()` must not appear anywhere
        in this package — every timestamp is supplied by the caller."""
        violations: list[str] = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            if "datetime.now(" in text or "datetime.utcnow(" in text or "time.time(" in text:
                violations.append(path.name)
        assert not violations, "Wall-clock call found in:\n" + "\n".join(violations)

    def test_package_contains_at_least_the_expected_modules(self):
        """A basic sanity check that this scan is actually looking at
        real content, not an empty or misconfigured directory."""
        names = {p.name for p in _source_files()}
        assert "contracts.py" in names
        assert "pipeline.py" in names
