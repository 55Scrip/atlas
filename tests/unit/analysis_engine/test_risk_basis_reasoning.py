"""The financial-risk basis in Recommendation Reasoning: carried beside the
`financial_risk` driver it explains, never read by anything that decides.

Three layers, as with forward context: the pipeline builds it from the
same risk findings the dampening flag reads; the gate places it into the
reasoning after the direction is chosen; the serializer persists it.
"""
from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path

import pytest

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.reasoning import (
    ELEVATING_RISK_CATEGORIES,
    InvestmentReasonKind,
    RiskDriverBasis,
    deserialize_reasoning,
    serialize_reasoning,
)
from atlas.analysis_engine.recommendation import RecommendationDirection, RecommendationReasoning
from atlas.analysis_engine.risk.contracts import FinancialRiskSignal, RiskStatus
from tests.unit.analysis_engine.risk.test_financial_risk_basis import evaluate, fcf, vst
from tests.unit.analysis_engine.test_real_data_scenarios import (
    _assemble,
    _dt,
    _fundamentals_doc,
    _ingest_all,
    _market_doc,
)

FIN, VAL = RiskCategory.FINANCIAL_RISK, RiskCategory.VALUATION_RISK


def vst_basis() -> RiskDriverBasis:
    return RiskDriverBasis(elevated_categories=(FIN,), financial_risk=vst().financial_risk_basis)


def _elevated_driver():
    from atlas.analysis_engine.reasoning import CanonicalEngine, InvestmentReason, ReasoningPolarity
    return InvestmentReason(kind=InvestmentReasonKind.FINANCIAL_RISK_ELEVATED, polarity=ReasoningPolarity.ADVERSE,
                            engine=CanonicalEngine.FINANCIAL_RISK, source_status="high")


def low_basis():
    return evaluate(BusinessCategoryStatus.STRONG, fcf(5.0)).financial_risk_basis


class TestRiskDriverBasis:
    def test_valuation_alone_can_raise_the_driver_while_financial_risk_is_low(self):
        basis = RiskDriverBasis(elevated_categories=(VAL,), financial_risk=low_basis())
        assert basis.financial_risk.level is RiskStatus.LOW

    def test_financial_risk_is_elevated_exactly_when_its_own_basis_is_high(self):
        with pytest.raises(ValueError):
            RiskDriverBasis(elevated_categories=(FIN,), financial_risk=low_basis())
        with pytest.raises(ValueError):
            RiskDriverBasis(elevated_categories=(), financial_risk=vst().financial_risk_basis)
        with pytest.raises(ValueError):
            RiskDriverBasis(elevated_categories=(VAL,), financial_risk=vst().financial_risk_basis)

    def test_categories_are_the_two_elevating_ones_once_each_in_order(self):
        assert ELEVATING_RISK_CATEGORIES == (FIN, VAL)
        for bad in ((VAL, FIN), (FIN, FIN), (RiskCategory.BUSINESS_RISK,)):
            with pytest.raises(ValueError):
                RiskDriverBasis(elevated_categories=bad, financial_risk=vst().financial_risk_basis)


class TestTheBasisExplainsTheDriverPresent:
    def _reasoning(self, *, elevated_driver: bool, basis):
        counter = (_elevated_driver(),) if elevated_driver else ()
        return RecommendationReasoning(counter_drivers=counter, risk_basis=basis)

    def test_an_elevated_basis_without_the_elevated_driver_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            self._reasoning(elevated_driver=False, basis=vst_basis())

    def test_the_elevated_driver_with_a_not_elevated_basis_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            self._reasoning(elevated_driver=True, basis=RiskDriverBasis((), low_basis()))

    def test_no_basis_is_always_allowed(self):
        assert self._reasoning(elevated_driver=True, basis=None).risk_basis is None


class TestTheGateCarriesTheBasisWithoutReadingIt:
    """Behavioural twin of the structural firewall below: identical gate
    inputs with and without the basis give identical decisions."""

    def _gates(self, risk_basis):
        from tests.unit.analysis_engine.test_recommendation import (
            TestDirectionSelectorNowWired,
            _assessment,
            _insufficient_valuation_engine,
            _insufficient_valuation_support,
        )
        from atlas.analysis_engine.conviction import ConvictionLevel
        from atlas.analysis_engine.recommendation import evaluate_recommendation_gate
        from tests.unit.analysis_engine._fixtures import GENERATED_AT

        engine_input, output, business_analysis = TestDirectionSelectorNowWired()._held_weak_business_result()
        fields = dict(
            business_evaluation=output.business_evaluation, valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence, reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH), business_analysis=business_analysis,
            valuation_engine=_insufficient_valuation_engine(), valuation_support=_insufficient_valuation_support(),
            has_high_financial_or_valuation_risk=True, has_open_questions=False, generated_at=GENERATED_AT,
        )
        return (evaluate_recommendation_gate(engine_input, **fields),
                evaluate_recommendation_gate(engine_input, **fields, risk_basis=risk_basis))

    def test_direction_conviction_drivers_triggers_and_unknowns_are_identical(self):
        basis = vst_basis()
        without, with_basis = self._gates(basis)
        a, b = without.recommendation, with_basis.recommendation
        assert a.direction is b.direction is RecommendationDirection.TRIM
        assert (a.conviction_level, a.conviction_reason) == (b.conviction_level, b.conviction_reason)
        assert without.conviction == with_basis.conviction
        assert dataclasses.replace(b.reasoning, risk_basis=None) == a.reasoning
        assert b.reasoning.risk_basis is basis

    def test_the_basis_adds_no_driver(self):
        without, with_basis = (g.recommendation.reasoning for g in self._gates(vst_basis()))
        assert with_basis.primary_drivers == without.primary_drivers
        assert with_basis.counter_drivers == without.counter_drivers
        assert InvestmentReasonKind.FINANCIAL_RISK_ELEVATED in [r.kind for r in with_basis.counter_drivers]
        assert not any("debt" in r.kind.value for r in with_basis.primary_drivers + with_basis.counter_drivers)

    def test_a_basis_that_contradicts_the_driver_cannot_be_carried(self):
        with pytest.raises(AnalysisEngineContractError):
            self._gates(RiskDriverBasis((), low_basis()))


class TestThePipelineBuildsItFromTheSameFindings:
    def test_rising_total_debt_elevates_financial_risk_and_the_basis_names_the_debt_trend(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2023-12-31", revenue=100, fcf=10, total_debt=14.402),
            _fundamentals_doc(period_end="2024-12-31", revenue=110, fcf=12, total_debt=16.298),
            _fundamentals_doc(period_end="2025-12-31", revenue=120, fcf=13, total_debt=17.043),
        )
        analysis = _assemble(records)
        reasoning = analysis.recommendation.recommendation.reasoning
        financial = next(f for f in analysis.risk_analysis.findings if f.category is FIN)
        assert reasoning.risk_basis.elevated_categories == (FIN,)
        assert reasoning.risk_basis.financial_risk is financial.financial_risk_basis
        assert reasoning.risk_basis.financial_risk.determining == (FinancialRiskSignal.DEBT_TREND,)
        assert [r.kind for r in reasoning.counter_drivers] == [InvestmentReasonKind.FINANCIAL_RISK_ELEVATED]

    def test_an_expensive_valuation_alone_is_disclosed_as_valuation_not_as_finances(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2021-12-31", revenue=100, fcf=10, published_at=_dt(2022, 2, 15)),
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=10, published_at=_dt(2023, 2, 15)),
            _market_doc(snapshot="2022-06-01", price=50, shares=100),
            _market_doc(snapshot="2023-06-01", price=200, shares=100),
        )
        analysis = _assemble(records)
        basis = analysis.recommendation.recommendation.reasoning.risk_basis
        assert basis.elevated_categories == (VAL,)
        assert basis.financial_risk.level is not RiskStatus.HIGH

    def test_no_elevated_risk_carries_a_basis_but_no_elevated_category(self):
        records = _ingest_all(
            _fundamentals_doc(period_end="2022-12-31", revenue=100, fcf=20),
            _fundamentals_doc(period_end="2023-12-31", revenue=125, fcf=30),
        )
        basis = _assemble(records).recommendation.recommendation.reasoning.risk_basis
        assert basis.elevated_categories == ()


class TestPersistence:
    def test_the_basis_round_trips_through_json(self):
        for basis in (RiskDriverBasis((VAL,), low_basis()), vst_basis()):
            reasoning = RecommendationReasoning(counter_drivers=(_elevated_driver(),), risk_basis=basis)
            payload = json.loads(json.dumps(serialize_reasoning(reasoning)))
            assert deserialize_reasoning(payload).risk_basis == basis

    def test_the_payload_is_tokens_facts_and_figures(self):
        payload = serialize_reasoning(RecommendationReasoning(counter_drivers=(_elevated_driver(),),
                                                              risk_basis=vst_basis()))
        basis = payload["riskBasis"]
        assert basis["elevatedCategories"] == ["financial_risk"]
        assert basis["financialRisk"]["determining"] == ["debt_trend"]
        debt = basis["financialRisk"]["signals"][2]
        assert (debt["signal"], debt["level"], debt["condition"]) == (
            "debt_trend", "high", "total_debt_increased_every_period")
        assert [(o["period"], o["value"]) for o in debt["observations"]] == [
            ("2023-12-31", 14.402e9), ("2024-12-31", 16.298e9), ("2025-12-31", 17.043e9)]
        assert set(debt["observations"][0]) == {"metric", "period", "value", "unit", "factId", "sourceRecordId"}

    def test_absent_and_null_both_read_back_as_no_basis(self):
        payload = serialize_reasoning(RecommendationReasoning())
        assert payload["riskBasis"] is None
        legacy = {k: v for k, v in payload.items() if k != "riskBasis"}
        assert deserialize_reasoning(legacy).risk_basis is None
        assert deserialize_reasoning(payload).risk_basis is None


class TestFirewall:
    """Structural: the basis reaches the reasoning and nothing that decides."""

    _DECIDING_CALLS = {
        "select_direction", "build_drivers", "build_signal_summary", "_derive_what_would_change",
        "build_key_unknowns", "calculate_recommendation_conviction", "build_conviction_reasoning",
        "has_company_fundamentals_evidence", "determine_recommendation",
    }

    @staticmethod
    def _tree(path):
        return ast.parse(Path(path).read_text(encoding="utf-8"))

    def test_the_gate_passes_risk_basis_only_into_recommendation_reasoning(self):
        tree = self._tree("atlas/analysis_engine/recommendation.py")
        uses = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", getattr(node.func, "attr", None))
                args = [*node.args, *(k.value for k in node.keywords)]
                if any(isinstance(a, ast.Name) and a.id == "risk_basis" for a in args):
                    uses.append(name)
                if name in self._DECIDING_CALLS:
                    inner = {n.id for a in args for n in ast.walk(a) if isinstance(n, ast.Name)}
                    assert "risk_basis" not in inner, name
        assert uses == ["RecommendationReasoning", "RecommendationReasoning"]
        # And nowhere else: any other read -- a comparison, a derived flag --
        # would let the basis steer the gate.
        loads = [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "risk_basis"
                 and isinstance(n.ctx, ast.Load)]
        assert len(loads) == 2, [n.lineno for n in loads]

    def test_the_pipeline_hands_it_only_to_the_gate(self):
        tree = self._tree("atlas/analysis_engine/pipeline.py")
        uses = [getattr(node.func, "id", None) for node in ast.walk(tree) if isinstance(node, ast.Call)
                and any(k.arg == "risk_basis" or (isinstance(k.value, ast.Name) and k.value.id == "risk_basis")
                        for k in node.keywords)]
        assert uses == ["evaluate_recommendation_gate"]

    def test_only_the_pipeline_reads_a_findings_financial_risk_basis(self):
        readers = set()
        for path in Path("atlas").rglob("*.py"):
            for node in ast.walk(self._tree(path)):
                if isinstance(node, ast.Attribute) and node.attr == "financial_risk_basis" \
                        and isinstance(node.ctx, ast.Load):
                    readers.add(str(path))
        assert readers <= {"atlas/analysis_engine/pipeline.py", "atlas/analysis_engine/risk/models.py"}, readers

    def test_the_dampening_flag_and_the_disclosed_categories_are_one_fact(self):
        source = Path("atlas/analysis_engine/pipeline.py").read_text(encoding="utf-8")
        assert "has_high_financial_or_valuation_risk = bool(elevated_risk_categories)" in source
        assert "elevated_categories=elevated_risk_categories" in source
