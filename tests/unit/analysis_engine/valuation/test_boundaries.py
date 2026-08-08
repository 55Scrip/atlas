"""Boundary tests scoped to `atlas.analysis_engine.valuation`
(ATLAS-024). Complements the repository-wide
`test_analysis_engine_only_reads_core_and_decision_engine` (already
covers this subpackage) and
`test_analysis_engine_never_imports_the_legacy_company_analysis_tree`.
"""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "atlas" / "analysis_engine" / "valuation"
)

_FORBIDDEN_ANYWHERE = (
    "import requests",
    "import httpx",
    "import openai",
    "import anthropic",
    "import sqlalchemy",
    "import sqlite3",
)

_FORBIDDEN_IN_IMPORTS = ("atlas.alpha", "atlas.providers", "atlas.value_scenario")

_FORBIDDEN_SCORING_PATTERNS = (
    "score +=",
    "score -=",
    "weighted_score",
    "weighted score",
)


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
        """Confirms the legacy `atlas.value_scenario` tree (studied only
        as prior art per the Phase 1 audit) is never actually imported."""
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

    def test_no_scoring_patterns(self):
        violations = []
        for path in _source_files():
            text = path.read_text(encoding="utf-8")
            for needle in _FORBIDDEN_SCORING_PATTERNS:
                if needle in text:
                    violations.append(f"{path.name} contains {needle!r}")
        assert not violations, "\n".join(violations)

    def test_expected_modules_exist(self):
        names = {p.name for p in _source_files()}
        for expected in (
            "__init__.py",
            "contracts.py",
            "facts.py",
            "models.py",
            "cash_flow.py",
            "scenarios.py",
            "pipeline.py",
            "exceptions.py",
        ):
            assert expected in names, f"{expected} missing from atlas/analysis_engine/valuation/"


class TestProviderIndependence:
    def test_no_evaluator_imports_business_data_providers(self):
        """Phase 22 Q9: a future market-data provider must never require
        an evaluator change."""
        violations = []
        for module_name in ("cash_flow.py", "scenarios.py", "pipeline.py"):
            path = _PACKAGE_DIR / module_name
            text = path.read_text(encoding="utf-8")
            if "business_data.providers" in text or "BusinessDataProvider" in text:
                violations.append(module_name)
        assert not violations, f"Provider coupling found in: {violations}"
