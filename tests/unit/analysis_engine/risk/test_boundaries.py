"""Boundary tests scoped to `atlas.analysis_engine.risk` (ATLAS-025).
Complements the repository-wide
`test_analysis_engine_only_reads_core_and_decision_engine` (already
covers this subpackage, since it is nested under `atlas.analysis_engine`)
and `test_no_scoring_patterns_anywhere_in_the_package` -- this file
scopes the same checks to `risk/` alone so a reviewer can see them
enumerated in one place, mirroring
`tests/unit/analysis_engine/valuation/test_boundaries.py`'s own pattern.
"""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "atlas" / "analysis_engine" / "risk"
)

_FORBIDDEN_ANYWHERE = (
    "import requests",
    "import httpx",
    "import openai",
    "import anthropic",
    "import sqlalchemy",
    "import sqlite3",
)

#: `atlas.alpha` is the Phase 16 boundary this sprint explicitly refuses
#: to cross -- Portfolio Risk and Execution Risk stay unproduced by this
#: package precisely because their real signal lives behind this import.
_FORBIDDEN_IN_IMPORTS = ("atlas.alpha", "atlas.core.application", "atlas.core.infrastructure")

_FORBIDDEN_SCORING_PATTERNS = (
    "score +=",
    "score -=",
    "weighted_score",
    "weighted score",
    "risk_score",
    "points +=",
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
            if "datetime.now(" in text or "datetime.utcnow(" in text or "time.time(" in text:
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
            "models.py",
            "business_risk.py",
            "financial_risk.py",
            "valuation_risk.py",
            "thesis_risk.py",
            "pipeline.py",
        ):
            assert expected in names, f"{expected} missing from atlas/analysis_engine/risk/"


class TestNoCrossCategoryReasoning:
    """Phase 17's independence-of-dimensions rule, checked structurally:
    no evaluator module may import a sibling evaluator, which would be
    the only way one Risk category's conclusion could leak into
    another's."""

    _EVALUATOR_MODULES = ("business_risk.py", "financial_risk.py", "valuation_risk.py", "thesis_risk.py")

    def test_no_evaluator_imports_another_evaluator(self):
        violations = []
        for module_name in self._EVALUATOR_MODULES:
            path = _PACKAGE_DIR / module_name
            other_modules = [m.removesuffix(".py") for m in self._EVALUATOR_MODULES if m != module_name]
            for line in _import_lines(path.read_text(encoding="utf-8")):
                for other in other_modules:
                    if f".{other}" in line or f" {other} " in line:
                        violations.append(f"{module_name}: {line.strip()!r}")
        assert not violations, "\n".join(violations)
