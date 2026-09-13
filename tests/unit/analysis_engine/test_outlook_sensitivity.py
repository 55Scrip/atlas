"""Outlook -> Sensitivity: Outlook's two horizons are conditional
sensitivity arithmetic, never a forecast, and an endpoint anchored on a
non-comparable (near-zero free cash flow) fiscal year is withheld rather
than shown with absurd precision.

Pure fixtures through the real `assemble_analysis` chain (the
`test_outlook.py` calibration helpers), plus direct checks on the anchor
policy's arithmetic. No issuer-specific data: the troughs are synthetic.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import statistics
from pathlib import Path

import pytest

from atlas.analysis_engine import outlook as outlook_module
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.outlook import (
    LONG_TERM_COMPOUNDING_YEARS,
    LONG_TERM_HORIZON_MONTHS,
    NEAR_ZERO_FCF_ANCHOR_RATIO,
    OUTLOOK_METHODOLOGY,
    OUTLOOK_ROLE,
    OutlookAssumption,
    OutlookAssumptionKind,
    OutlookDriverKind,
    OutlookGapKind,
    OutlookScenario,
    ReturnBasis,
    ScenarioKind,
    _comparable_anchor_cut,
    _long_term_valuation,
)
from tests.unit.analysis_engine._fixtures import GENERATED_AT
from tests.unit.analysis_engine.test_outlook import (
    _assemble,
    _cal_growth_records,
    _cal_market_records,
    _make_record,
    _single_market_observation_records,
)

_REVENUE = (100, 108, 117, 126, 136, 147, 159, 172, 186, 201)
_PRICES = (50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0)
_CLEAN_FCF = (40, 43, 47, 50, 54, 59, 63, 68, 74, 80)
#: FY2007 collapses to a near-zero trough, far below 10% of the median.
_TROUGH_FCF = (40, 43, 1, 50, 54, 59, 63, 68, 74, 80)
#: Today's own free cash flow is the near-zero year.
_CURRENT_TROUGH_FCF = (40, 43, 47, 50, 54, 59, 63, 68, 74, 2)
#: Four consecutive troughs: every 4-year window but the last touches one.
_MANY_TROUGHS_FCF = (40, 1, 1, 1, 1, 59, 63, 68, 74, 80)


def _analysis(fcf: tuple[float, ...], tag: str):
    records = _cal_growth_records(_REVENUE, fcf, tag=tag) + _cal_market_records(_PRICES, tag=f"m{tag}")
    return _assemble(records)


def _fcf_finding(analysis):
    return next(f for f in analysis.valuation_engine.findings if f.kind.value == "fcf_yield_relative")


def _by_kind(horizon):
    return {s.kind: s for s in horizon.scenarios}


class TestRoleIsSensitivity:
    def test_role_constant_names_a_sensitivity(self):
        assert OUTLOOK_ROLE == "sensitivity"
        assert OUTLOOK_METHODOLOGY == "sensitivity_v2"

    def test_api_view_carries_the_role(self):
        from atlas.alpha.investment_case.api.schemas import OutlookView

        view = OutlookView.from_domain(_analysis(_CLEAN_FCF, "role").outlook, change_intelligence=None)
        assert view.role == "sensitivity"

    def test_methodology_identity_names_the_outlook_component(self):
        from atlas.analysis_engine.methodology import ANALYSIS_METHODOLOGY

        assert f"outlook={OUTLOOK_METHODOLOGY}" in ANALYSIS_METHODOLOGY.split(";")


class TestHorizonsAreTruthful:
    def test_short_term_rerating_has_no_horizon(self):
        short = _analysis(_CLEAN_FCF, "sth").outlook.short_term
        assert short.expected_return.basis is ReturnBasis.CUMULATIVE
        assert short.expected_return.horizon_months_low is None
        assert short.expected_return.horizon_months_high is None

    def test_long_term_horizon_is_exactly_the_compounding_duration(self):
        long = _analysis(_CLEAN_FCF, "lth").outlook.long_term
        assert long.expected_return.basis is ReturnBasis.ANNUALIZED
        assert (long.expected_return.horizon_months_low, long.expected_return.horizon_months_high) == LONG_TERM_HORIZON_MONTHS
        assert LONG_TERM_HORIZON_MONTHS == (48, 48)
        for scenario in long.scenarios:
            assert scenario.assumption.horizon_years == LONG_TERM_COMPOUNDING_YEARS == 4

    def test_api_short_term_horizon_serializes_as_null(self):
        from atlas.alpha.investment_case.api.schemas import OutlookView

        payload = OutlookView.from_domain(_analysis(_CLEAN_FCF, "sapi").outlook, change_intelligence=None).model_dump(by_alias=True)
        assert payload["shortTerm"]["expectedReturn"]["horizonMonthsLow"] is None
        assert payload["longTerm"]["expectedReturn"]["horizonMonthsLow"] == 48


class TestBaseIsTheMedianAssumptionNotMostLikely:
    def test_short_term_endpoints_are_anchored_on_named_fiscal_years(self):
        analysis = _analysis(_CLEAN_FCF, "anc")
        epochs = sorted(_fcf_finding(analysis).fcf_yield_evidence.prior_epochs, key=lambda e: (e.fcf_yield, e.fiscal_period))
        scenarios = _by_kind(analysis.outlook.short_term)
        assert scenarios[ScenarioKind.BULL].anchor_periods == (epochs[0].fiscal_period,)
        assert scenarios[ScenarioKind.BEAR].anchor_periods == (epochs[-1].fiscal_period,)
        assert scenarios[ScenarioKind.BASE].anchor_periods == (epochs[len(epochs) // 2].fiscal_period,)

    def test_base_is_the_median_yield_with_no_probability_attached(self):
        analysis = _analysis(_CLEAN_FCF, "med")
        base = _by_kind(analysis.outlook.short_term)[ScenarioKind.BASE]
        assert base.assumption.target_fcf_yield == pytest.approx(statistics.median(_fcf_finding(analysis).historical_yields))
        field_names = {f.name for f in dataclasses.fields(OutlookScenario)}
        assert not any("probab" in name or "likel" in name or "weight" in name for name in field_names)

    def test_long_term_endpoints_name_their_growth_windows(self):
        long = _analysis(_CLEAN_FCF, "lwin").outlook.long_term
        for scenario in long.scenarios:
            assert scenario.anchor_periods and len(scenario.anchor_periods) % 2 == 0


class TestNearZeroAnchorWithholdsTheEndpoint:
    def test_a_trough_anchored_bull_is_withheld_never_shown(self):
        short = _analysis(_TROUGH_FCF, "tr").outlook.short_term
        bull = _by_kind(short)[ScenarioKind.BULL]
        assert bull.return_percent is None
        assert bull.withheld_reason is OutlookGapKind.NEAR_ZERO_FCF_ANCHOR
        assert bull.anchor_periods == ("2007-12-31",)

    def test_the_other_endpoints_stay_and_define_the_range(self):
        short = _analysis(_TROUGH_FCF, "trr").outlook.short_term
        scenarios = _by_kind(short)
        shown = [scenarios[ScenarioKind.BASE].return_percent, scenarios[ScenarioKind.BEAR].return_percent]
        assert None not in shown
        assert short.expected_return.low_percent == pytest.approx(min(shown))
        assert short.expected_return.high_percent == pytest.approx(max(shown))
        assert short.expected_return_gap is None

    def test_a_withheld_endpoint_still_discloses_its_assumption(self):
        """The yield it would have re-rated to stays visible: withholding
        hides the number, not the provenance."""
        bull = _by_kind(_analysis(_TROUGH_FCF, "tra").outlook.short_term)[ScenarioKind.BULL]
        assert bull.assumption.kind is OutlookAssumptionKind.HISTORICAL_FCF_YIELD_REVERSION
        assert bull.assumption.target_fcf_yield > 0

    def test_long_term_leaves_out_every_window_touching_the_trough(self):
        clean = _analysis(_CLEAN_FCF, "lcl").outlook.long_term
        trough = _analysis(_TROUGH_FCF, "ltr").outlook.long_term
        assert trough.expected_return is not None
        counts = {s.assumption.growth_observation_count for s in trough.scenarios}
        assert counts == {clean.scenarios[0].assumption.growth_observation_count - 1}
        assert all("2007-12-31" not in s.anchor_periods for s in trough.scenarios)

    def test_fewer_than_two_comparable_windows_withholds_long_term_only(self):
        analysis = _analysis(_MANY_TROUGHS_FCF, "many")
        assert analysis.outlook.long_term.expected_return_gap is OutlookGapKind.NEAR_ZERO_FCF_ANCHOR
        assert analysis.outlook.long_term.scenarios == ()
        assert analysis.outlook.short_term.expected_return is not None

    def test_a_near_zero_current_year_withholds_both_horizons(self):
        outlook = _analysis(_CURRENT_TROUGH_FCF, "cur").outlook
        assert outlook.short_term.expected_return_gap is OutlookGapKind.NEAR_ZERO_FCF_ANCHOR
        assert outlook.long_term.expected_return_gap is OutlookGapKind.NEAR_ZERO_FCF_ANCHOR

    def test_a_clean_history_withholds_nothing(self):
        outlook = _analysis(_CLEAN_FCF, "none").outlook
        for horizon in (outlook.short_term, outlook.long_term):
            assert all(s.withheld_reason is None and s.return_percent is not None for s in horizon.scenarios)

    def test_a_near_zero_median_year_withholds_long_term(self):
        """Every Long-Term scenario shares the terminal (median) yield, so a
        non-comparable median year withholds the horizon, not one
        endpoint. Built by lowering prior-epoch FCF on the real clean
        evidence: with an even prior-epoch count the median straddles two
        years, and one of them is now a trough."""
        analysis = _analysis(_CLEAN_FCF, "mdz")
        finding = _fcf_finding(analysis)
        evidence = finding.fcf_yield_evidence
        priors = list(evidence.prior_epochs)[1:]  # an even count: 8
        lowered = [dataclasses.replace(e, free_cash_flow=0.5) if i < 4 else e for i, e in enumerate(priors)]
        evidence = dataclasses.replace(evidence, prior_epochs=tuple(lowered))
        facts = extract_facts_from_records(_cal_growth_records(_REVENUE, _CLEAN_FCF, tag="mdzf"), evaluated_at=GENERATED_AT)
        result = _long_term_valuation(
            growth_status=BusinessCategoryStatus.STRONG,
            business_facts=facts,
            debt_trend=None,
            fcf_finding_current_yield=finding.current_yield,
            historical_yields=tuple(sorted(e.fcf_yield for e in lowered)),
            generated_at=GENERATED_AT,
            evidence=evidence,
        )
        assert result[1] is OutlookGapKind.NEAR_ZERO_FCF_ANCHOR


class TestFixtureMatrix:
    """The sprint's pure-fixture matrix: each shape lands on its own named
    outcome, never a collapsed "insufficient data"."""

    def test_stable_deep_history_keeps_every_number_visible(self):
        outlook = _analysis(_CLEAN_FCF, "deep").outlook
        assert len(outlook.short_term.scenarios) == 3 and len(outlook.long_term.scenarios) == 3
        assert all(s.return_percent is not None for s in outlook.short_term.scenarios + outlook.long_term.scenarios)
        for scenario in outlook.short_term.scenarios:
            assumption = scenario.assumption
            assert scenario.return_percent == pytest.approx(assumption.current_fcf_yield / assumption.target_fcf_yield - 1)

    def test_limited_history_is_no_historical_valuation_range(self):
        outlook = _assemble(_single_market_observation_records()).outlook
        assert outlook.short_term.expected_return_gap is OutlookGapKind.NO_HISTORICAL_VALUATION_RANGE

    def test_no_history_is_valuation_not_conclusive(self):
        outlook = _assemble(()).outlook
        assert outlook.short_term.expected_return_gap is OutlookGapKind.VALUATION_NOT_CONCLUSIVE
        assert outlook.long_term.expected_return_gap is OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY

    def test_no_long_term_growth_keeps_the_rerating(self):
        records = _cal_growth_records(tuple(reversed(_REVENUE)), tuple(reversed(_CLEAN_FCF)), tag="dec") + _cal_market_records(
            _PRICES, tag="mdec"
        )
        outlook = _assemble(records).outlook
        assert outlook.long_term.expected_return_gap is OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY
        assert outlook.short_term.expected_return is not None

    def test_not_applicable_industry_computes_no_sensitivity(self):
        """A capital-markets business: the FCF-yield method does not apply,
        so there is no current yield to re-rate from."""
        records = (
            _cal_growth_records(_REVENUE, _CLEAN_FCF, tag="bank")
            + _cal_market_records(_PRICES, tag="mbank")
            + (_make_record("company_profile", None, "profile", industry="CAPITAL MARKETS"),)
        )
        outlook = _assemble(records, profile=False).outlook
        assert outlook.short_term.expected_return_gap is OutlookGapKind.VALUATION_NOT_CONCLUSIVE
        assert outlook.long_term.expected_return_gap is OutlookGapKind.VALUATION_NOT_CONCLUSIVE


class TestAnchorCutArithmetic:
    def test_cut_is_the_ratio_of_the_median_epoch_fcf_including_today(self):
        evidence = _fcf_finding(_analysis(_TROUGH_FCF, "cut")).fcf_yield_evidence
        fcf = [e.free_cash_flow for e in evidence.prior_epochs] + [evidence.current.free_cash_flow]
        assert _comparable_anchor_cut(evidence) == pytest.approx(NEAR_ZERO_FCF_ANCHOR_RATIO * statistics.median(fcf))

    def test_no_evidence_judges_nothing(self):
        assert _comparable_anchor_cut(None) is None

    def test_a_scenario_carries_exactly_one_of_a_number_or_a_reason(self):
        assumption = OutlookAssumption(
            kind=OutlookAssumptionKind.HISTORICAL_FCF_YIELD_REVERSION,
            current_fcf_yield=0.05, target_fcf_yield=0.04, observation_count=3,
        )
        driver = OutlookDriverKind.VALUATION_RERATING
        with pytest.raises(ValueError):
            OutlookScenario(kind=ScenarioKind.BULL, return_percent=None, assumption=assumption, driver=driver)
        with pytest.raises(ValueError):
            OutlookScenario(
                kind=ScenarioKind.BULL, return_percent=0.1, assumption=assumption, driver=driver,
                withheld_reason=OutlookGapKind.NEAR_ZERO_FCF_ANCHOR,
            )

    def test_the_policy_is_generic_no_issuer_names_in_logic(self):
        source = inspect.getsource(outlook_module)
        tree = ast.parse(source)
        literals = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        code_literals = {v for v in literals if len(v) <= 6 and v.isupper()}
        assert not code_literals & {"AMD", "NVDA", "VST", "GOOGL", "AAPL", "MCO", "META", "CRWD", "AMZN", "MU", "V", "AMAT"}


class TestOutlookIsFirewalledFromDecisions:
    """Outlook is a sensitivity: nothing decision-facing imports it."""

    _ROOT = Path(__file__).resolve().parents[3] / "atlas"

    @pytest.mark.parametrize(
        "relative",
        [
            "analysis_engine/recommendation.py",
            "analysis_engine/direction_selector.py",
            "analysis_engine/conviction.py",
            "analysis_engine/recommendation_conviction.py",
            "analysis_engine/valuation/support.py",
            "analysis_engine/valuation/scenario_proof.py",
            "alpha/portfolio_fit/engine.py",
            "alpha/stance/engine.py",
        ],
    )
    def test_module_never_imports_outlook(self, relative):
        path = self._ROOT / relative
        tree = ast.parse(path.read_text())
        imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        imported |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert not any(name.endswith("outlook") for name in imported), relative
