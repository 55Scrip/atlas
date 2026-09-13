"""Financial Risk v2 in Recommendation Reasoning: the basis travels beside the
`financial_risk` driver it explains and is never read by anything that
decides; and "financial risk is not elevated" is said only when Financial
Risk itself reached a level.

Three layers, as with forward context: the pipeline builds the basis from
the same risk findings the dampening flag reads; the gate places it into the
reasoning after the direction is chosen; the serializer persists it.
"""
from __future__ import annotations

import ast
import dataclasses
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.reasoning import (
    ELEVATING_RISK_CATEGORIES,
    RISK_BASIS_VERSION,
    CanonicalEngine,
    InvestmentReason,
    InvestmentReasonKind,
    KeyUnknownKind,
    ReasoningPolarity,
    RiskDriverBasis,
    build_drivers,
    build_key_unknowns,
    build_signal_summary,
    deserialize_reasoning,
    serialize_reasoning,
)
from atlas.analysis_engine.recommendation import (
    ChangeTriggerKind,
    RecommendationDirection,
    RecommendationReasoning,
    _derive_what_would_change,
)
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupportStatus
from tests.unit.analysis_engine.risk.test_financial_risk import company, evaluate
from tests.unit.analysis_engine.test_real_data_scenarios import _assemble, _fundamentals_doc, _ingest_all, _valuation_history

FIN, VAL = RiskCategory.FINANCIAL_RISK, RiskCategory.VALUATION_RISK
_EVALUATED_AT = datetime(2026, 8, 9, tzinfo=timezone.utc)


def vst_basis() -> RiskDriverBasis:
    return RiskDriverBasis(elevated_categories=(FIN,), financial_risk=company("VST").financial_risk_basis)


def low_basis():
    return company("META").financial_risk_basis


def not_applicable_basis():
    return evaluate((), "BANKS - DIVERSIFIED").financial_risk_basis


def elevated_driver():
    return InvestmentReason(kind=InvestmentReasonKind.FINANCIAL_RISK_ELEVATED, polarity=ReasoningPolarity.ADVERSE,
                            engine=CanonicalEngine.FINANCIAL_RISK, source_status="high")


def statement(period_end: str, *, debt: float, fcf: float, capex: float, revenue: float = 100.0) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier=f"TEST:FY:{period_end}", company="TEST", source_kind="financial_statement",
        published_at=_EVALUATED_AT, provider_id="sec_edgar", raw_reference="https://example.test/filing",
        content_hash=f"hash-{period_end}-{debt}-{fcf}-{capex}", language="en",
        period_start=date(int(period_end[:4]), 1, 1), period_end=date.fromisoformat(period_end),
        metadata={"revenue": revenue, "free_cash_flow": fcf, "capital_expenditure": capex, "total_debt": debt,
                  "currency": "USD"},
    )


def profile(industry: str) -> RawBusinessDocument:
    return RawBusinessDocument(
        identifier="TEST:profile", company="TEST", source_kind="company_profile", published_at=_EVALUATED_AT,
        provider_id="alpha_vantage", raw_reference="https://example.test/profile", content_hash=f"profile-{industry}",
        language="en", period_start=None, period_end=None,
        metadata={"name": "Test Co", "sector": "TEST", "industry": industry},
    )


class TestRiskDriverBasis:
    def test_valuation_alone_is_recorded_as_the_dampening_fact_while_financial_risk_is_low(self):
        assert RiskDriverBasis(elevated_categories=(VAL,), financial_risk=low_basis()).financial_risk.level is RiskStatus.LOW

    def test_financial_risk_is_elevated_exactly_when_its_own_basis_is_high(self):
        for bad in ((FIN,), ()):
            basis = low_basis() if bad == (FIN,) else company("VST").financial_risk_basis
            with pytest.raises(ValueError):
                RiskDriverBasis(elevated_categories=bad, financial_risk=basis)

    def test_categories_are_the_two_elevating_ones_once_each_in_order(self):
        assert ELEVATING_RISK_CATEGORIES == (FIN, VAL)
        for bad in ((VAL, FIN), (FIN, FIN), (RiskCategory.BUSINESS_RISK,)):
            with pytest.raises(ValueError):
                RiskDriverBasis(elevated_categories=bad, financial_risk=company("VST").financial_risk_basis)

    def test_a_basis_must_explain_the_driver_actually_present(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationReasoning(counter_drivers=(), risk_basis=vst_basis())
        with pytest.raises(AnalysisEngineContractError):
            RecommendationReasoning(counter_drivers=(elevated_driver(),), risk_basis=RiskDriverBasis((), low_basis()))


def _builders(**overrides):
    kwargs = dict(
        growth_status=BusinessCategoryStatus.MODERATE, capital_allocation_status=BusinessCategoryStatus.STRONG,
        valuation_status=ValuationStatus.FAIRLY_VALUED, valuation_support_status=ValuationSupportStatus.SUPPORTED,
        financial_risk_high=False, financial_risk_assessed=False,
    )
    kwargs.update(overrides)
    return kwargs


class TestNotElevatedOnlyWhenAssessed:
    """The audit's blocker: "no elevated financial risk" appeared whenever any
    risk category was real, even when Financial Risk itself was insufficient
    or not applicable (AVGO, CRWD, DE, GS, JPM, BRK.B, MC, NEE, VZ)."""

    def test_the_driver_needs_an_assessed_financial_risk(self):
        primary, _ = build_drivers(**_builders(financial_risk_assessed=False))
        assert InvestmentReasonKind.FINANCIAL_RISK_NOT_ELEVATED not in [r.kind for r in primary]
        primary, _ = build_drivers(**_builders(financial_risk_assessed=True))
        assert InvestmentReasonKind.FINANCIAL_RISK_NOT_ELEVATED in [r.kind for r in primary]

    def test_the_change_trigger_needs_an_assessed_financial_risk(self):
        kwargs = dict(financial_risk_high=False, valuation_support_status=ValuationSupportStatus.SUPPORTED,
                      growth_status=BusinessCategoryStatus.MODERATE, capital_allocation_status=BusinessCategoryStatus.STRONG,
                      valuation_status=ValuationStatus.FAIRLY_VALUED)
        assert ChangeTriggerKind.FINANCIAL_RISK_BECOMES_ELEVATED not in _derive_what_would_change(**kwargs)
        assert ChangeTriggerKind.FINANCIAL_RISK_BECOMES_ELEVATED in _derive_what_would_change(
            **kwargs, financial_risk_assessed=True)

    def test_insufficient_is_an_input_missing_unknown(self):
        summary = build_signal_summary(**_builders())
        fr = next(c for c in summary if c.engine is CanonicalEngine.FINANCIAL_RISK)
        assert fr.source_status == "not_evaluated"
        assert any(u.engine is CanonicalEngine.FINANCIAL_RISK and u.kind is KeyUnknownKind.ANALYSIS_INPUT_MISSING
                   for u in build_key_unknowns(summary))

    def test_not_applicable_is_neither_reassurance_nor_a_missing_input(self):
        summary = build_signal_summary(**_builders(financial_risk_not_applicable=True))
        fr = next(c for c in summary if c.engine is CanonicalEngine.FINANCIAL_RISK)
        assert fr.source_status == "not_applicable"
        assert not any(u.engine is CanonicalEngine.FINANCIAL_RISK for u in build_key_unknowns(summary))
        primary, counter = build_drivers(**_builders())
        assert not [r for r in primary + counter if r.engine is CanonicalEngine.FINANCIAL_RISK]


class TestTheGateCarriesTheBasisWithoutReadingIt:
    """Behavioural twin of the structural firewall below: identical gate
    inputs with and without the basis give identical decisions."""

    def _gates(self, risk_basis, **extra):
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
            financial_risk_status=RiskStatus.HIGH, **extra,
        )
        return (evaluate_recommendation_gate(engine_input, **fields),
                evaluate_recommendation_gate(engine_input, **fields, risk_basis=risk_basis))

    def test_direction_conviction_drivers_triggers_and_unknowns_are_identical(self):
        basis = vst_basis()
        without, with_basis = self._gates(basis)
        a, b = without.recommendation, with_basis.recommendation
        assert a.direction is b.direction is RecommendationDirection.TRIM
        assert (a.conviction_level, a.conviction_reason) == (b.conviction_level, b.conviction_reason)
        assert dataclasses.replace(b.reasoning, risk_basis=None) == a.reasoning
        assert b.reasoning.risk_basis is basis

    def test_the_basis_adds_no_driver(self):
        without, with_basis = (g.recommendation.reasoning for g in self._gates(vst_basis()))
        assert (with_basis.primary_drivers, with_basis.counter_drivers) == (without.primary_drivers, without.counter_drivers)
        assert not any("debt" in r.kind.value for r in with_basis.primary_drivers + with_basis.counter_drivers)

    def test_a_basis_that_contradicts_the_driver_cannot_be_carried(self):
        with pytest.raises(AnalysisEngineContractError):
            self._gates(RiskDriverBasis((), low_basis()))


class TestThePipeline:
    def test_high_burden_elevates_financial_risk_and_the_basis_names_the_ratio(self):
        records = _ingest_all(
            profile("UTILITIES - INDEPENDENT POWER PRODUCERS"),
            statement("2023-12-31", debt=14.402, fcf=3.777, capex=1.676),
            statement("2024-12-31", debt=16.298, fcf=2.485, capex=2.078),
            statement("2025-12-31", debt=17.043, fcf=1.318, capex=2.752),
        )
        analysis = _assemble(records)
        reasoning = analysis.recommendation.recommendation.reasoning
        financial = next(f for f in analysis.risk_analysis.findings if f.category is FIN)
        assert financial.status is RiskStatus.HIGH
        assert reasoning.risk_basis.elevated_categories == (FIN,)
        assert reasoning.risk_basis.financial_risk is financial.financial_risk_basis
        assert round(financial.financial_risk_basis.latest.ratio, 2) == 4.19
        assert [r.kind for r in reasoning.counter_drivers] == [InvestmentReasonKind.FINANCIAL_RISK_ELEVATED]

    def test_rising_but_small_debt_is_not_elevated(self):
        records = _ingest_all(
            profile("INTERNET CONTENT & INFORMATION"),
            statement("2023-12-31", debt=18.385, fcf=44.068, capex=27.045),
            statement("2024-12-31", debt=28.826, fcf=54.072, capex=37.256),
            statement("2025-12-31", debt=58.744, fcf=46.109, capex=69.691),
        )
        reasoning = _assemble(records).recommendation.recommendation.reasoning
        assert reasoning.risk_basis.elevated_categories == ()
        assert InvestmentReasonKind.FINANCIAL_RISK_NOT_ELEVATED in [r.kind for r in reasoning.primary_drivers]

    def test_a_bank_is_not_applicable_and_never_reassured(self):
        records = _ingest_all(profile("BANKS - DIVERSIFIED"), statement("2025-12-31", debt=250.0, fcf=-47.0, capex=2.0))
        analysis = _assemble(records)
        financial = next(f for f in analysis.risk_analysis.findings if f.category is FIN)
        reasoning = analysis.recommendation.recommendation.reasoning
        assert financial.status is RiskStatus.NOT_APPLICABLE
        kinds = [r.kind for r in reasoning.primary_drivers + reasoning.counter_drivers]
        assert InvestmentReasonKind.FINANCIAL_RISK_NOT_ELEVATED not in kinds
        assert InvestmentReasonKind.FINANCIAL_RISK_ELEVATED not in kinds
        assert ChangeTriggerKind.FINANCIAL_RISK_BECOMES_ELEVATED not in reasoning.what_would_change

    def test_missing_debt_is_insufficient_and_never_reassured(self):
        records = _ingest_all(profile("SEMICONDUCTORS"), _fundamentals_doc(period_end="2025-12-31", revenue=100, fcf=20))
        reasoning = _assemble(records).recommendation.recommendation.reasoning
        kinds = [r.kind for r in reasoning.primary_drivers]
        assert InvestmentReasonKind.FINANCIAL_RISK_NOT_ELEVATED not in kinds
        assert any(u.engine is CanonicalEngine.FINANCIAL_RISK and u.kind is KeyUnknownKind.ANALYSIS_INPUT_MISSING
                   for u in reasoning.key_unknowns)

    def test_an_expensive_valuation_alone_is_disclosed_as_valuation_not_as_finances(self):
        records = _ingest_all(*_valuation_history(50, 50, 50, 200))
        basis = _assemble(records).recommendation.recommendation.reasoning.risk_basis
        assert basis.elevated_categories == (VAL,)
        assert basis.financial_risk.level is not RiskStatus.HIGH


class TestPersistence:
    def test_the_basis_round_trips_through_json(self):
        for basis in (RiskDriverBasis((VAL,), low_basis()), vst_basis(), RiskDriverBasis((VAL,), not_applicable_basis())):
            # The financial driver goes with a basis in which Financial Risk is elevated, and only then.
            drivers = (elevated_driver(),) if FIN in basis.elevated_categories else ()
            reasoning = RecommendationReasoning(counter_drivers=drivers, risk_basis=basis)
            payload = json.loads(json.dumps(serialize_reasoning(reasoning)))
            assert deserialize_reasoning(payload).risk_basis == basis

    def test_the_payload_carries_the_ratio_its_figures_and_their_provenance(self):
        payload = serialize_reasoning(RecommendationReasoning(counter_drivers=(elevated_driver(),), risk_basis=vst_basis()))
        basis = payload["riskBasis"]
        assert basis["version"] == RISK_BASIS_VERSION == 2
        fr = basis["financialRisk"]
        assert (fr["level"], fr["condition"], fr["measure"]) == ("high", "debt_burden_high", "gross_debt_to_operating_cash_flow")
        assert fr["bands"] == {"lowBelow": 1.25, "highFrom": 3.0}
        latest = fr["latest"]
        assert round(latest["ratio"], 2) == 4.19
        assert latest["operatingCashFlow"] == pytest.approx(latest["freeCashFlow"] + latest["capitalExpenditure"])
        assert latest["freeCashFlowFactId"] and latest["capitalExpenditureFactId"] and latest["totalDebtFactId"]
        assert [round(o["ratio"], 2) for o in fr["history"]] == [2.64, 3.57, 4.19]

    def test_a_v1_or_legacy_payload_is_never_read_as_v2(self):
        payload = serialize_reasoning(RecommendationReasoning())
        assert payload["riskBasis"] is None
        v1 = dict(payload, riskBasis={"elevatedCategories": ["financial_risk"],
                                      "financialRisk": {"level": "high", "rule": "any_signal_high"}})
        assert deserialize_reasoning(v1).risk_basis is None
        legacy = {k: v for k, v in payload.items() if k != "riskBasis"}
        assert deserialize_reasoning(legacy).risk_basis is None


class TestFirewall:
    """Structural: the basis reaches the reasoning and nothing that decides;
    Financial Risk's own status reaches only the reasoning builders."""

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
        loads = [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "risk_basis" and isinstance(n.ctx, ast.Load)]
        assert len(loads) == 2, [n.lineno for n in loads]

    def test_financial_risk_status_never_reaches_direction_selection(self):
        tree = self._tree("atlas/analysis_engine/recommendation.py")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "select_direction":
                inner = {n.id for k in node.keywords for n in ast.walk(k.value) if isinstance(n, ast.Name)}
                assert not {"financial_risk_status", "financial_risk_assessed"} & inner

    def test_the_pipeline_hands_basis_and_status_only_to_the_gate(self):
        tree = self._tree("atlas/analysis_engine/pipeline.py")
        for arg in ("risk_basis", "financial_risk_status"):
            uses = [getattr(node.func, "id", None) for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and any(k.arg == arg for k in node.keywords)]
            assert uses == ["evaluate_recommendation_gate"], (arg, uses)

    def test_only_the_pipeline_reads_a_findings_financial_risk_basis(self):
        readers = set()
        for path in Path("atlas").rglob("*.py"):
            for node in ast.walk(self._tree(path)):
                if isinstance(node, ast.Attribute) and node.attr == "financial_risk_basis" and isinstance(node.ctx, ast.Load):
                    readers.add(str(path))
        assert readers <= {"atlas/analysis_engine/pipeline.py", "atlas/analysis_engine/risk/models.py"}, readers

    def test_the_dampening_flag_and_the_disclosed_categories_are_one_fact(self):
        source = Path("atlas/analysis_engine/pipeline.py").read_text(encoding="utf-8")
        assert "has_high_financial_or_valuation_risk = bool(elevated_risk_categories)" in source
        assert "elevated_categories=elevated_risk_categories" in source


class TestDriverSplit:
    """Financial and valuation risk share one decision effect -- either HIGH
    dampens the direction -- but never one meaning. Each dimension speaks
    through its own reason: `FINANCIAL_RISK_ELEVATED` for Financial Risk,
    `VALUATION_EXPENSIVE` (from the same FCF-yield finding Valuation Risk
    maps from) for valuation."""

    STATUS = {RiskStatus.HIGH: (True, True), RiskStatus.MODERATE: (False, True), RiskStatus.LOW: (False, True),
              RiskStatus.INSUFFICIENT_INPUT: (False, False), RiskStatus.NOT_APPLICABLE: (False, False)}

    @pytest.mark.parametrize("financial", list(STATUS))
    @pytest.mark.parametrize("valuation", [ValuationStatus.EXPENSIVE, ValuationStatus.FAIRLY_VALUED,
                                           ValuationStatus.UNDERVALUED, ValuationStatus.INSUFFICIENT_INPUT])
    def test_the_truth_table(self, financial, valuation):
        high, assessed = self.STATUS[financial]
        primary, counter = build_drivers(**_builders(financial_risk_high=high, financial_risk_assessed=assessed,
                                                     valuation_status=valuation))
        kinds = [r.kind for r in counter]
        assert (InvestmentReasonKind.FINANCIAL_RISK_ELEVATED in kinds) is (financial is RiskStatus.HIGH)
        assert (InvestmentReasonKind.VALUATION_EXPENSIVE in kinds) is (valuation is ValuationStatus.EXPENSIVE)
        not_elevated = InvestmentReasonKind.FINANCIAL_RISK_NOT_ELEVATED in [r.kind for r in primary]
        assert not_elevated is (financial in (RiskStatus.LOW, RiskStatus.MODERATE))
        assert sum(k is InvestmentReasonKind.FINANCIAL_RISK_ELEVATED for k in kinds) <= 1
        assert all(r.polarity is ReasoningPolarity.ADVERSE for r in counter)

    def test_both_high_gives_two_reasons_financial_first(self):
        _, counter = build_drivers(**_builders(financial_risk_high=True, financial_risk_assessed=True,
                                               valuation_status=ValuationStatus.EXPENSIVE))
        assert [r.kind for r in counter] == [InvestmentReasonKind.FINANCIAL_RISK_ELEVATED,
                                            InvestmentReasonKind.VALUATION_EXPENSIVE]
        assert [r.engine for r in counter] == [CanonicalEngine.FINANCIAL_RISK, CanonicalEngine.VALUATION]

    def test_valuation_only_never_reports_financial_risk_as_high_in_the_signal_summary(self):
        summary = build_signal_summary(**_builders(financial_risk_high=False, financial_risk_assessed=True,
                                                   valuation_status=ValuationStatus.EXPENSIVE))
        entries = {c.engine: c.source_status for c in summary}
        assert entries[CanonicalEngine.FINANCIAL_RISK] == "not_high"
        assert entries[CanonicalEngine.VALUATION] == "expensive"

    def test_the_risk_trigger_speaks_for_financial_risk_only(self):
        base = dict(valuation_support_status=ValuationSupportStatus.SUPPORTED, growth_status=BusinessCategoryStatus.MODERATE,
                    capital_allocation_status=BusinessCategoryStatus.MODERATE, valuation_status=ValuationStatus.EXPENSIVE)
        valuation_only = _derive_what_would_change(financial_risk_high=False, financial_risk_assessed=True, **base)
        assert ChangeTriggerKind.REDUCED_RISK not in valuation_only
        assert ChangeTriggerKind.LOWER_VALUATION in valuation_only
        both = _derive_what_would_change(financial_risk_high=True, financial_risk_assessed=True, **base)
        assert both[:2] == (ChangeTriggerKind.REDUCED_RISK, ChangeTriggerKind.LOWER_VALUATION)

    def test_a_financial_driver_on_a_valuation_only_basis_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationReasoning(counter_drivers=(elevated_driver(),), risk_basis=RiskDriverBasis((VAL,), low_basis()))
        assert RecommendationReasoning(counter_drivers=(), risk_basis=RiskDriverBasis((VAL,), low_basis())).risk_basis

    def test_a_real_valuation_only_case_is_named_as_valuation(self):
        records = _ingest_all(*_valuation_history(50, 50, 50, 200))
        analysis = _assemble(records)
        statuses = {f.category: f.status for f in analysis.risk_analysis.findings}
        assert statuses[VAL] is RiskStatus.HIGH and statuses[FIN] is not RiskStatus.HIGH
        reasoning = analysis.recommendation.recommendation.reasoning
        kinds = [r.kind for r in reasoning.counter_drivers]
        assert InvestmentReasonKind.FINANCIAL_RISK_ELEVATED not in kinds
        assert InvestmentReasonKind.VALUATION_EXPENSIVE in kinds
        assert reasoning.risk_basis.elevated_categories == (VAL,)  # the dampening fact is still recorded

    def test_direction_selection_still_reads_the_shared_flag_and_no_reason_vocabulary(self):
        tree = TestFirewall._tree("atlas/analysis_engine/recommendation.py")
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "select_direction"]
        assert len(calls) == 1
        kw = {k.arg: k.value for k in calls[0].keywords}
        flag = kw["has_high_financial_or_valuation_risk"]
        assert isinstance(flag, ast.Name) and flag.id == "has_high_financial_or_valuation_risk"
        assert "financial_risk_high" not in kw and "financial_risk_status" not in kw
        selector = Path("atlas/analysis_engine/direction_selector.py").read_text(encoding="utf-8")
        for token in ("InvestmentReasonKind", "FINANCIAL_RISK_ELEVATED", "VALUATION_EXPENSIVE", "financial_risk_high"):
            assert token not in selector
        pipeline = Path("atlas/analysis_engine/pipeline.py").read_text(encoding="utf-8")
        assert "has_high_financial_or_valuation_risk = bool(elevated_risk_categories)" in pipeline
