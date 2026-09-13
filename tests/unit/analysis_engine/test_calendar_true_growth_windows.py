"""Calendar-true rolling FCF growth windows, through every consumer.

Outlook's Long-Term range, Valuation Support's Scenario proof and Growth's
full-span CAGR all read `growth_primitives.rolling_growth_observations`.
These tests pin that they read the same fiscal-year windows, and that the
two real defects the windows had -- NVDA's missing fiscal years and DE's
duplicated period labels -- can no longer reach a decision.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import statistics
from datetime import datetime, timezone

import pytest

from atlas.analysis_engine import outlook
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.growth_primitives import (
    corroborated_by,
    fiscal_years_apart,
    real_periods,
    rolling_growth_observations,
)
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.growth import evaluate_growth
from atlas.analysis_engine.outlook import OutlookGapKind
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.valuation.eligibility import (
    SCENARIO_HORIZON_YEARS,
    IneligibilityReason,
    evaluate_scenario_eligibility,
)
from atlas.analysis_engine.valuation.proof import ProofVerdict
from atlas.analysis_engine.valuation.scenario_proof import evaluate_scenario_proof
from tests.unit.analysis_engine.business_facts.test_growth_primitives import DE_FCF, NVDA_FCF

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
_PROVENANCE = Provenance(
    source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
    source_references=(),
    dependencies=(),
    update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
    consumers=(),
    computed_at=NOW,
)

#: NVDA's persisted Revenue: every fiscal year FY2008-FY2026.
NVDA_REVENUE = {
    "2008-01-27": 4097860000.0, "2009-01-25": 3424859000.0, "2010-01-31": 3326445000.0,
    "2011-01-30": 3543309000.0, "2012-01-29": 3997930000.0, "2013-01-27": 4280159000.0,
    "2014-01-26": 4130000000.0, "2015-01-25": 4682000000.0, "2016-01-31": 5010000000.0,
    "2017-01-29": 6910000000.0, "2018-01-28": 9714000000.0, "2019-01-27": 11716000000.0,
    "2020-01-26": 10918000000.0, "2021-01-31": 16675000000.0, "2022-01-30": 26914000000.0,
    "2023-01-29": 26974000000.0, "2024-01-28": 60922000000.0, "2025-01-26": 130497000000.0,
    "2026-01-25": 215938000000.0,
}
#: NVDA's FCF-yield inputs as the FCF-yield finding reports them today.
NVDA_CURRENT_YIELD = 0.017379945932684562
NVDA_HISTORICAL_YIELDS = (
    0.006807686976335808, 0.012378541988043345, 0.014169486114380276, 0.020203307409336575,
    0.04264022587222206, 0.05661904307451925, 0.09051192650688294,
)


def _fact(kind: BusinessFactKind, period: str, value: float) -> BusinessFact:
    return BusinessFact(
        id=f"rec-{period}:{kind.value}:{period}",
        company="TEST",
        kind=kind,
        value=value,
        unit="USD",
        period=period,
        source_record_id=f"rec-{period}",
        provenance=_PROVENANCE,
        extracted_at=NOW,
        published_at=NOW,
    )


def _facts(fcf: dict[str, float], revenue: dict[str, float] | None = None) -> tuple[BusinessFact, ...]:
    revenue = revenue if revenue is not None else {period: 10 * value for period, value in fcf.items()}
    return tuple(
        [_fact(BusinessFactKind.FREE_CASH_FLOW, p, v) for p, v in fcf.items()]
        + [_fact(BusinessFactKind.REVENUE, p, v) for p, v in revenue.items()]
    )


def _nvda() -> tuple[BusinessFact, ...]:
    return _facts(NVDA_FCF, NVDA_REVENUE)


def _list_index_rates(facts: tuple[BusinessFact, ...], years: int = 4) -> list[float]:
    """The retired construction, kept here only as the defect's
    reference: list item `i` paired with item `i + years`."""
    fcf = sorted((f for f in facts if f.kind is BusinessFactKind.FREE_CASH_FLOW), key=lambda f: f.period)
    return [
        (fcf[i + years].value / fcf[i].value) ** (1 / years) - 1
        for i in range(len(fcf) - years)
        if fcf[i].value > 0 and fcf[i + years].value > 0
    ]


def _long_term(facts, *, current_yield=0.05, historical_yields=(0.04, 0.05, 0.06)):
    return outlook._long_term_valuation(
        growth_status=BusinessCategoryStatus.MODERATE,
        business_facts=facts,
        debt_trend=None,
        fcf_finding_current_yield=current_yield,
        historical_yields=historical_yields,
        generated_at=NOW,
    )


def _contiguous(start=2014, end=2025, growth=0.1):
    return _facts({f"{y}-12-31": 100.0 * (1 + growth) ** (y - start) for y in range(start, end + 1)})


class TestOneWindowSemanticsForEveryConsumer:
    def test_outlook_and_valuation_support_read_the_same_windows(self):
        for facts in (_nvda(), _facts(DE_FCF), _contiguous()):
            fcf = [f for f in facts if f.kind is BusinessFactKind.FREE_CASH_FLOW]
            revenue = [f for f in facts if f.kind is BusinessFactKind.REVENUE]
            expected = corroborated_by(rolling_growth_observations(fcf, years=4), real_periods(revenue))
            eligibility = evaluate_scenario_eligibility(facts, generated_at=NOW)
            assert eligibility.corroborated_growth_observations == expected
            scenarios = _long_term(facts)[2]
            if scenarios:
                rates = [o.rate for o in expected]
                by_kind = {s.kind.value: s.assumption.growth_rate for s in scenarios}
                assert (by_kind["bear"], by_kind["base"], by_kind["bull"]) == (
                    min(rates), statistics.median(rates), max(rates),
                )
                assert scenarios[0].assumption.growth_observation_count == len(expected)

    def test_outlook_keeps_no_second_rolling_window_implementation(self):
        assert not hasattr(outlook, "_rolling_cagr_observations")
        assert outlook.rolling_growth_observations is rolling_growth_observations

    def test_no_production_module_pairs_list_positions_as_years(self):
        """Structural: nothing indexes a fact list at `i + years`."""
        offenders = []
        for path in pathlib.Path("atlas").rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.BinOp):
                    names = {n.id for n in ast.walk(node.slice) if isinstance(n, ast.Name)}
                    if "years" in names:
                        offenders.append(f"{path}:{node.lineno}")
        assert offenders == []

    def test_every_4_year_growth_input_is_four_fiscal_years(self):
        for facts in (_nvda(), _facts(DE_FCF), _contiguous()):
            for obs in evaluate_scenario_eligibility(facts, generated_at=NOW).corroborated_growth_observations:
                assert obs.years == SCENARIO_HORIZON_YEARS == outlook.LONG_TERM_COMPOUNDING_YEARS
                assert fiscal_years_apart(obs.start_period, obs.end_period) == 4


class TestFutureFacts:
    def test_a_future_fiscal_year_is_never_a_window_endpoint(self):
        facts = _contiguous(2019, 2025) + _facts({"2026-12-31": 999.0})
        eligibility = evaluate_scenario_eligibility(facts, generated_at=NOW)
        assert all(o.end_period <= "2025-12-31" for o in eligibility.corroborated_growth_observations)
        assert [o.end_period for o in eligibility.corroborated_growth_observations] == [
            "2023-12-31", "2024-12-31", "2025-12-31",
        ]


class TestOutlookLongTerm:
    def test_contiguous_history_gives_a_range_from_fiscal_windows(self):
        expected, gap, scenarios, _, _ = _long_term(_contiguous())
        assert gap is None and expected is not None
        assert {round(s.assumption.growth_rate, 12) for s in scenarios} == {0.1}

    def test_missing_years_leave_too_few_windows_for_a_range(self):
        expected, gap, scenarios, _, _ = _long_term(
            _nvda(), current_yield=NVDA_CURRENT_YIELD, historical_yields=NVDA_HISTORICAL_YIELDS
        )
        assert expected is None and scenarios == ()
        assert gap is OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY


class TestOutlookShortTerm:
    def test_short_term_reads_yields_only_and_is_unchanged_for_nvda(self):
        """Short-Term holds today's FCF and re-rates it to the prior yields;
        no growth window reaches it (+155 / -14 / -81% for NVDA)."""
        assert "business_facts" not in inspect.signature(outlook._short_term_valuation).parameters
        _, _, scenarios, _ = outlook._short_term_valuation(NVDA_CURRENT_YIELD, NVDA_HISTORICAL_YIELDS)
        returns = {s.kind.value: s.return_percent for s in scenarios}
        assert returns == {
            "bull": NVDA_CURRENT_YIELD / min(NVDA_HISTORICAL_YIELDS) - 1,
            "base": NVDA_CURRENT_YIELD / statistics.median(NVDA_HISTORICAL_YIELDS) - 1,
            "bear": NVDA_CURRENT_YIELD / max(NVDA_HISTORICAL_YIELDS) - 1,
        }
        assert [round(returns[k], 4) for k in ("bull", "base", "bear")] == [1.553, -0.1397, -0.808]


class TestValuationSupportScenario:
    def test_nvda_scenario_proof_no_longer_rests_on_13_year_spans(self):
        """Before: FY2010->FY2023, FY2011->FY2024 and FY2012->FY2025 were
        read as 4-year growth (74.6/161.5/198.1%/yr), and the envelope's
        low end (+15.5%) established support."""
        assert [round(r, 3) for r in _list_index_rates(_nvda())] == [0.746, 1.615, 1.981, 0.857]
        eligibility = evaluate_scenario_eligibility(_nvda(), generated_at=NOW)
        assert [(o.start_period, o.end_period) for o in eligibility.corroborated_growth_observations] == [
            ("2022-01-30", "2026-01-25"),
        ]
        assert eligibility.ineligibility_reason is IneligibilityReason.INSUFFICIENT_CORROBORATED_OBSERVATIONS
        proof = evaluate_scenario_proof(
            _nvda(), current_yield=NVDA_CURRENT_YIELD, historical_yields=NVDA_HISTORICAL_YIELDS, generated_at=NOW
        )
        assert proof.verdict is ProofVerdict.DOES_NOT_ESTABLISH
        assert proof.evidence_summary == "ineligible:insufficient_corroborated_observations"

    def test_de_scenario_windows_are_four_fiscal_years_without_duplicates(self):
        eligibility = evaluate_scenario_eligibility(_facts(DE_FCF), generated_at=NOW)
        windows = [(o.start_period, o.end_period) for o in eligibility.corroborated_growth_observations]
        assert windows == [("2013-10-31", "2017-10-29"), ("2014-10-31", "2018-10-28")]
        assert not any(p in ("2015-10-31", "2015-11-01", "2016-10-30", "2016-10-31") for w in windows for p in w)

    def test_contiguous_history_still_establishes_from_its_envelope(self):
        proof = evaluate_scenario_proof(
            _contiguous(), current_yield=0.06, historical_yields=(0.04, 0.05, 0.055), generated_at=NOW
        )
        assert proof.verdict is ProofVerdict.ESTABLISHES_SUPPORT


class TestGrowthFullSpanCagr:
    def test_a_gapped_series_is_annualised_over_its_fiscal_years_not_its_facts(self):
        """NVDA: FY2010 -> FY2026 is sixteen fiscal years; the eight facts
        used to annualise it over seven (118%/yr)."""
        finding = evaluate_growth(_facts(NVDA_FCF, NVDA_REVENUE), evaluated_at=NOW)
        assert finding.free_cash_flow_cagr == pytest.approx((96676000000.0 / 410206000.0) ** (1 / 16) - 1)

    def test_duplicate_labels_do_not_lengthen_or_shorten_the_span(self):
        facts = _facts({"2013-10-31": 100.0, "2015-10-31": 150.0, "2015-11-01": 150.0, "2017-10-29": 200.0})
        finding = evaluate_growth(facts, evaluated_at=NOW)
        assert finding.free_cash_flow_cagr == pytest.approx(2.0 ** 0.25 - 1)

    def test_a_contiguous_series_is_unchanged(self):
        finding = evaluate_growth(_facts({"2020-12-31": 100.0, "2021-12-31": 200.0, "2022-12-31": 400.0}), evaluated_at=NOW)
        assert finding.free_cash_flow_cagr == pytest.approx(1.0)
