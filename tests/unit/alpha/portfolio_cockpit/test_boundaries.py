"""Static validation for `atlas.alpha.portfolio_cockpit` (ATLAS-028): no
independent analysis recomputation, no fabricated recommendation, no
numeric scoring/weighting, no forbidden Core/infrastructure imports.
Mirrors `tests/unit/alpha/investment_case/test_boundaries.py`'s own
pattern."""
from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "atlas" / "alpha" / "portfolio_cockpit"

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
    "score -=",
    "weighted_score",
    "weighted score",
    "portfolio_score",
    "risk_score",
    "conviction_score",
    "np.mean",
    "statistics.mean",
)

_FORBIDDEN_RECOMMENDATION_LANGUAGE = ("\"buy\"", "\"sell\"", "\"trim\"", "\"add\"", "'buy'", "'sell'", "'trim'")

_FORBIDDEN_IN_IMPORTS = (
    "atlas.core.infrastructure",
    "atlas.analysis_engine.growth",
    "atlas.analysis_engine.capital_allocation",
    "atlas.analysis_engine.valuation.cash_flow",
    "atlas.analysis_engine.risk.business_risk",
    "atlas.analysis_engine.risk.financial_risk",
    "atlas.analysis_engine.risk.valuation_risk",
    "atlas.analysis_engine.risk.thesis_risk",
    "atlas.analysis_engine.conviction.calculate_conviction",
    "atlas.analysis_engine.pipeline",
)


def _source_files() -> list[Path]:
    return [p for p in _PACKAGE_DIR.rglob("*.py") if "__pycache__" not in p.parts and "/api/" not in str(p)]


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
        """This package composes many Cases via
        `InvestmentCaseCompositionService.build_many` (ATLAS-027/028)
        only -- it never imports an individual evaluator or the
        analysis-engine pipeline directly, and never touches
        `atlas.core.infrastructure` outside its own `api/` layer."""
        violations = []
        for path in _source_files():
            for line in _import_lines(path.read_text(encoding="utf-8")):
                for needle in _FORBIDDEN_IN_IMPORTS:
                    if needle in line:
                        violations.append(f"{path.name}: {line.strip()!r}")
        assert not violations, "\n".join(violations)

    def test_uses_investment_case_composition_service(self):
        service_path = _PACKAGE_DIR / "service.py"
        text = service_path.read_text(encoding="utf-8")
        assert "from atlas.alpha.investment_case.service import InvestmentCaseCompositionService" in text
        assert "build_many" in text

    def test_expected_modules_exist(self):
        names = {p.name for p in _source_files()}
        for expected in ("__init__.py", "models.py", "contracts.py", "projection.py", "attention.py", "service.py"):
            assert expected in names, f"{expected} missing from atlas/alpha/portfolio_cockpit/"


class TestNoRecommendationLeakage:
    """Important Rule: Attention is prioritization, never recommendation
    -- no BUY/SELL/TRIM/ADD vocabulary anywhere in this package's own
    contracts or logic."""

    def test_contracts_and_attention_never_spell_a_directional_action(self):
        for filename in ("contracts.py", "attention.py", "models.py"):
            text = (_PACKAGE_DIR / filename).read_text(encoding="utf-8").lower()
            for needle in _FORBIDDEN_RECOMMENDATION_LANGUAGE:
                assert needle not in text, f"{filename} contains {needle!r}"


class TestPortfolioStatusReuse:
    def test_service_reuses_portfolio_status_service_rather_than_recomputing(self):
        text = (_PACKAGE_DIR / "service.py").read_text(encoding="utf-8")
        assert "PortfolioStatusService" in text
        assert "build_report" in text
