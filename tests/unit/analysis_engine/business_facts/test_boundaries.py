"""Boundary tests scoped to `atlas.analysis_engine.business_facts`
(ATLAS-023). Complements the repository-wide
`test_analysis_engine_only_reads_core_and_decision_engine`, which
already covers this subpackage."""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "atlas" / "analysis_engine" / "business_facts"
)

_FORBIDDEN_ANYWHERE = (
    "import requests",
    "import httpx",
    "import openai",
    "import anthropic",
    "import sqlalchemy",
    "import sqlite3",
)

_FORBIDDEN_IN_IMPORTS = ("atlas.alpha", "atlas.providers")


def _source_files() -> list[Path]:
    return [p for p in _PACKAGE_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def _import_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip().startswith(("import ", "from "))]


class TestNoForbiddenDependencies:
    def test_no_forbidden_substrings_anywhere(self):
        violations = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            for needle in _FORBIDDEN_ANYWHERE:
                if needle in text:
                    violations.append(f"{path.name} contains {needle!r}")
        assert not violations, "\n".join(violations)

    def test_no_forbidden_imports(self):
        violations = []
        for path in _source_files():
            for line in _import_lines(path.read_text(encoding="utf-8")):
                for needle in _FORBIDDEN_IN_IMPORTS:
                    if needle in line:
                        violations.append(f"{path.name}: {line.strip()!r}")
        assert not violations, "\n".join(violations)

    def test_no_wall_clock_calls(self):
        violations = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            if "datetime.now(" in text or "datetime.utcnow(" in text:
                violations.append(path.name)
        assert not violations, "\n".join(violations)

    def test_expected_modules_exist(self):
        names = {p.name for p in _source_files()}
        for expected in ("__init__.py", "contracts.py", "models.py", "extraction.py", "exceptions.py"):
            assert expected in names


class TestNoSemanticInterpretation:
    def test_no_llm_or_nlp_libraries_imported(self):
        violations = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8").lower()
            for needle in ("import spacy", "import nltk", "import transformers", "openai", "anthropic"):
                if needle in text:
                    violations.append(f"{path.name} contains {needle!r}")
        assert not violations, "\n".join(violations)
