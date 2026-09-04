"""Continuous growth magnitude preserved alongside GrowthStatus.

`status` measures monotonicity, so it cannot separate a company
compounding FCF at +118%/yr from one compounding at +6%/yr -- both are
MODERATE the moment either series has a single down-period. These
fields keep that difference, without attaching a threshold to it and
without reaching recommendation logic.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.analysis_engine.business_contracts import BusinessCategory, BusinessCategoryStatus
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.growth import evaluate_growth
# Reuses this package's existing fact builder rather than a second one,
# so these tests cannot drift from the shape `evaluate_growth` really
# receives.
from tests.unit.analysis_engine.test_growth import fact as _fact

_NOW = datetime(2026, 9, 4, tzinfo=timezone.utc)


def _series(values, kind=BusinessFactKind.REVENUE, start=2016):
    return tuple(_fact(kind, v, f"{start + i}-12-31") for i, v in enumerate(values))


def _growth(facts):
    finding = evaluate_growth(facts, evaluated_at=_NOW)
    assert finding.kind is BusinessCategory.GROWTH
    return finding


class TestMagnitudeIsPreserved:
    def test_a_high_growth_series_reports_its_rate(self):
        f = _growth(_series([100.0, 200.0, 400.0, 800.0]))
        assert f.revenue_cagr == pytest.approx(1.0)  # doubling each period

    def test_a_low_growth_series_reports_its_rate(self):
        f = _growth(_series([100.0, 102.0, 104.04, 106.12]))
        assert f.revenue_cagr == pytest.approx(0.02, abs=1e-4)

    def test_materially_different_rates_share_one_status(self):
        """The defect this exists for. Both series dip once, so both are
        MODERATE -- and before these fields they were indistinguishable
        to every downstream consumer."""
        fast = _growth(_series([100.0, 300.0, 250.0, 900.0]))
        slow = _growth(_series([100.0, 103.0, 101.0, 106.0]))
        assert fast.status is BusinessCategoryStatus.MODERATE
        assert slow.status is fast.status
        assert fast.revenue_cagr > slow.revenue_cagr * 5


class TestUndefinedRatesAreAbsentNotZero:
    def test_one_observation_yields_none(self):
        assert _growth(_series([100.0])).revenue_cagr is None

    def test_no_observations_yields_none(self):
        f = _growth(())
        assert f.revenue_cagr is None and f.free_cash_flow_cagr is None

    def test_zero_start_yields_none_not_infinity(self):
        assert _growth(_series([0.0, 50.0, 100.0])).revenue_cagr is None

    def test_negative_endpoint_yields_none(self):
        """Free cash flow legitimately crosses zero. A compound rate
        across a sign change is meaningless, not merely imprecise."""
        facts = _series([-50.0, 20.0, 80.0], kind=BusinessFactKind.FREE_CASH_FLOW)
        assert _growth(facts).free_cash_flow_cagr is None

    def test_negative_terminal_value_yields_none(self):
        facts = _series([80.0, 20.0, -50.0], kind=BusinessFactKind.FREE_CASH_FLOW)
        assert _growth(facts).free_cash_flow_cagr is None

    def test_an_absent_rate_never_changes_the_status(self):
        """A missing magnitude must not make a company look worse."""
        with_zero = _growth(_series([0.0, 50.0, 100.0]))
        assert with_zero.revenue_cagr is None
        assert with_zero.status is BusinessCategoryStatus.STRONG or \
               with_zero.status is BusinessCategoryStatus.MODERATE
        # identical values, positive start -> same monotonic shape
        without_zero = _growth(_series([25.0, 50.0, 100.0]))
        assert without_zero.status is with_zero.status


class TestStatusIsUnaffected:
    @pytest.mark.parametrize("values,expected", [
        # Revenue alone rising cannot reach STRONG -- that needs both
        # metrics -- but revenue alone falling does reach WEAK, since
        # the WEAK rule carries no both-metrics requirement. That
        # asymmetry is the documented rule and must stay unchanged.
        ([100.0, 110.0, 120.0], BusinessCategoryStatus.MODERATE),
        ([120.0, 110.0, 100.0], BusinessCategoryStatus.WEAK),
    ])
    def test_classification_is_unchanged_by_the_new_fields(self, values, expected):
        assert _growth(_series(values)).status is expected

    def test_both_series_monotonic_still_reaches_strong(self):
        facts = _series([100.0, 200.0, 300.0]) + _series(
            [10.0, 20.0, 30.0], kind=BusinessFactKind.FREE_CASH_FLOW)
        f = _growth(facts)
        assert f.status is BusinessCategoryStatus.STRONG
        assert f.revenue_cagr is not None and f.free_cash_flow_cagr is not None


class TestDeterminism:
    def test_repeated_evaluation_is_identical(self):
        facts = _series([100.0, 130.0, 120.0, 190.0])
        assert len({_growth(facts).revenue_cagr for _ in range(50)}) == 1

    def test_input_order_does_not_matter(self):
        """`_facts_by_kind` sorts by period explicitly, so a shuffled
        input must not change the result."""
        ordered = _series([100.0, 130.0, 120.0, 190.0])
        shuffled = tuple(reversed(ordered))
        assert _growth(ordered).revenue_cagr == _growth(shuffled).revenue_cagr


class TestBackwardCompatibility:
    def test_the_fields_default_to_none_for_legacy_construction(self):
        """Every pre-existing construction site omits them; a finding
        built without them must remain valid and report absence."""
        from atlas.analysis_engine.business_contracts import BusinessFinding
        import inspect
        signature = inspect.signature(BusinessFinding)
        assert signature.parameters["revenue_cagr"].default is None
        assert signature.parameters["free_cash_flow_cagr"].default is None

    def test_magnitude_is_not_a_recommendation_input(self):
        """`select_direction` must never see these. Its parameter list
        is the contract."""
        import inspect
        from atlas.analysis_engine.direction_selector import select_direction
        params = set(inspect.signature(select_direction).parameters)
        assert "revenue_cagr" not in params
        assert "free_cash_flow_cagr" not in params
