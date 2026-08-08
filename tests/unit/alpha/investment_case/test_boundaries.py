"""Static validation for `atlas.alpha.investment_case` (ATLAS-027 Phase
31): no independent analysis recomputation, no automatic Decision or
Recommendation fabrication, no forbidden Core/infrastructure imports."""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "atlas" / "alpha" / "investment_case"

_FORBIDDEN_ANYWHERE = (
    "import requests",
    "import httpx",
    "import openai",
    "import anthropic",
    "import sqlalchemy",
    "DirectionalRecommendation",
    "capture_decision",
    "DecisionService",
    "score +=",
    "weighted_score",
)

_FORBIDDEN_IN_IMPORTS = (
    "atlas.core.infrastructure",
    "atlas.analysis_engine.growth",
    "atlas.analysis_engine.capital_allocation",
    "atlas.analysis_engine.valuation.cash_flow",
    "atlas.analysis_engine.risk.business_risk",
    "atlas.analysis_engine.risk.financial_risk",
    "atlas.analysis_engine.risk.valuation_risk",
    "atlas.analysis_engine.risk.thesis_risk",
    "atlas.analysis_engine.conviction",
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
        """Confirms this composition layer never imports an individual
        analytical evaluator directly -- only the canonical
        `assemble_analysis` entry point (Phase 9/14's own "never
        duplicate Business/Valuation/Risk/Conviction" rule, checked
        structurally)."""
        violations = []
        for path in _source_files():
            for line in _import_lines(path.read_text(encoding="utf-8")):
                for needle in _FORBIDDEN_IN_IMPORTS:
                    if needle in line:
                        violations.append(f"{path.name}: {line.strip()!r}")
        assert not violations, "\n".join(violations)

    def test_uses_assemble_analysis(self):
        service_path = _PACKAGE_DIR / "service.py"
        text = service_path.read_text(encoding="utf-8")
        assert "from atlas.analysis_engine.pipeline import assemble_analysis" in text

    def test_expected_modules_exist(self):
        names = {p.name for p in _source_files()}
        for expected in ("__init__.py", "models.py", "service.py"):
            assert expected in names, f"{expected} missing from atlas/alpha/investment_case/"
