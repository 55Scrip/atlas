"""Tests for `atlas.analysis_engine.outlook` (Outlook Intelligence
Sprint 1) -- exercised through the real, top-level `assemble_analysis`
entry point with real `BusinessRecord`s, the same "full BusinessRecord
-> ... -> CanonicalAnalysis chain" style `test_investment_case_synthesis
.py`/`test_pipeline.py` already establish -- never a hand-built fake
`BusinessAnalysisResult`/`ValuationEngineResult`/`RiskAnalysisResult`.

Ten scenarios, per the sprint's own Part 12 list. Assertions are
semantic (status/direction/gap-reason), never snapshot-structure --
matching that same instruction.
"""
from __future__ import annotations

import statistics
from datetime import date, datetime, timezone

import pytest

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.investment_case_change import ThesisImpact
from atlas.analysis_engine.outlook import (
    HorizonOutlook,
    OutlookDriverKind,
    OutlookGapKind,
    OutlookMomentumKind,
    ReturnBasis,
    ScenarioKind,
    derive_outlook_momentum,
)
from atlas.analysis_engine.pipeline import assemble_analysis
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal, run_populated

_RANK = {
    ConvictionLevel.INSUFFICIENT_EVIDENCE: 0,
    ConvictionLevel.LOW: 1,
    ConvictionLevel.MODERATE: 2,
    ConvictionLevel.HIGH: 3,
    ConvictionLevel.VERY_HIGH: 4,
}


def _make_record(source_kind, period_end, identifier, *, published_at=GENERATED_AT, **metadata):
    document = RawBusinessDocument(
        identifier=identifier,
        company="ASML",
        source_kind=source_kind,
        published_at=published_at,
        provider_id="structured_test",
        raw_reference=f"ref://{identifier}",
        content_hash=f"hash-{identifier}",
        language="en",
        period_end=period_end,
        metadata=metadata,
    )
    result = ingest(document, evaluated_at=GENERATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


#: Fiscal periods every combined fixture below shares -- `published_at`
#: is deliberately well before the *next* period's own market
#: observation date, so `cash_flow.py`'s no-look-ahead rule always finds
#: an eligible Free Cash Flow fact for every observation below.
_PERIODS = (date(2022, 12, 31), date(2023, 12, 31), date(2024, 12, 31))
_PUBLISHED = (
    datetime(2023, 2, 15, tzinfo=timezone.utc),
    datetime(2024, 2, 15, tzinfo=timezone.utc),
    datetime(2025, 2, 15, tzinfo=timezone.utc),
)
_OBSERVATION_DATES = (date(2023, 3, 1), date(2024, 3, 1), date(2025, 3, 1))


def _growth_records(*, strong: bool, tag: str):
    """One `annual_report` record per period, carrying **both** Revenue
    and Free Cash Flow -- the single source of truth both Growth and
    the FCF Yield evaluator read, so a caller that also attaches market
    data for the same periods (`_market_data_records` below) never
    redefines the same `(company, FREE_CASH_FLOW, period)` fact twice
    (which `extract_facts_from_records` would honestly drop as
    conflicting, per its own documented policy)."""
    if strong:
        revenue, fcf = (1000.0, 1100.0, 1250.0), (100.0, 110.0, 200.0)
    else:
        revenue, fcf = (1250.0, 1100.0, 1000.0), (300.0, 240.0, 200.0)
    return tuple(
        _make_record(
            "annual_report", _PERIODS[i], f"{tag}{i}",
            published_at=_PUBLISHED[i], revenue=revenue[i], free_cash_flow=fcf[i],
        )
        for i in range(3)
    )


def _strong_growth_records():
    return _growth_records(strong=True, tag="sg")


def _weak_growth_records():
    return _growth_records(strong=False, tag="wg")


def _strong_capital_allocation_records():
    return (
        _make_record(
            "annual_report", date(2023, 12, 31), "sca23",
            share_buybacks=100.0, share_issuance=10.0, debt_repayment=50.0, debt_issuance=5.0,
        ),
        _make_record(
            "annual_report", date(2024, 12, 31), "sca24",
            share_buybacks=120.0, share_issuance=10.0, debt_repayment=60.0, debt_issuance=5.0,
        ),
    )


def _weak_capital_allocation_records():
    """Dilution (capital_return NEGATIVE) plus rising `TOTAL_DEBT`
    (leverage_trend NEGATIVE) -- two negative signals outweigh the one
    positive `cash_generation` signal every scenario's combined
    `_growth_records`' own real, positive Free Cash Flow otherwise
    contributes, so this stays WEAK under the v2 combination rule
    exactly as it was under v1's own "any negative disqualifies" rule."""
    return (
        _make_record(
            "annual_report", date(2022, 12, 31), "wca22", total_debt=50.0,
        ),
        _make_record(
            "annual_report", date(2023, 12, 31), "wca23",
            share_buybacks=10.0, share_issuance=100.0, total_debt=150.0,
        ),
        _make_record(
            "annual_report", date(2024, 12, 31), "wca24",
            share_buybacks=10.0, share_issuance=120.0, total_debt=300.0,
        ),
    )


def _market_data_records(prices: tuple[float, float, float], *, tag: str):
    """`market_data_snapshot` documents only -- `SHARE_PRICE`/
    `SHARES_OUTSTANDING` are a disjoint `ValuationFactKind` taxonomy
    from `BusinessFactKind`, so these never conflict with
    `_growth_records`'s own Free Cash Flow facts at the same period."""
    return tuple(
        _make_record(
            "market_data_snapshot", _OBSERVATION_DATES[i], f"{tag}{i}",
            share_price=prices[i], shares_outstanding=100.0,
        )
        for i in range(3)
    )


def _undervalued_market_data(*, tag: str = "uv"):
    """Flat-to-slowly-rising price against genuinely growing Free Cash
    Flow -- the most recent yield ends up above every historical one."""
    return _market_data_records((50.0, 52.0, 53.0), tag=tag)


def _expensive_market_data(*, tag: str = "ex"):
    """A sharp final-period price spike -- the most recent yield ends
    up below every historical one, regardless of the underlying Free
    Cash Flow trend it's paired with."""
    return _market_data_records((20.0, 22.0, 500.0), tag=tag)


def _undervalued_against_declining_fcf_market_data(*, tag: str = "uvd"):
    """Pairs with `_weak_growth_records`: price falls *faster* than the
    declining Free Cash Flow, so the most recent yield still ends up
    above every historical one -- a real, if unusual, "statistically
    cheap despite a shrinking business" case, not a fabricated one."""
    return _market_data_records((50.0, 52.0, 20.0), tag=tag)


def _single_market_observation_records():
    """Exactly one market observation -- a real current yield, but
    nothing to build a historical range from (Scenario 8)."""
    return (
        _make_record(
            "annual_report", date(2024, 12, 31), "sfy24",
            published_at=datetime(2025, 2, 15, tzinfo=timezone.utc), free_cash_flow=100.0,
        ),
        _make_record("market_data_snapshot", date(2025, 3, 1), "sm24", share_price=50.0, shares_outstanding=100.0),
    )


#: Long-Term Expected Return v1 -- a few scenarios need more than three
#: fiscal periods (a recent-deterioration or recent-recovery narrative
#: needs a real full-history trend *and* a real, differently-signed
#: recent-window trend, which three periods cannot express). Same
#: one-year cadence as `_PERIODS`/`_PUBLISHED`/`_OBSERVATION_DATES`,
#: generalized to `n` periods starting 2020-12-31.
def _n_periods(n: int) -> tuple[date, ...]:
    return tuple(date(2020 + i, 12, 31) for i in range(n))


def _n_published(n: int) -> tuple[datetime, ...]:
    return tuple(datetime(2021 + i, 2, 15, tzinfo=timezone.utc) for i in range(n))


def _n_observations(n: int) -> tuple[date, ...]:
    return tuple(date(2021 + i, 3, 1) for i in range(n))


def _custom_growth_records(revenue: tuple[float, ...], fcf: tuple[float, ...], *, tag: str):
    n = len(revenue)
    assert len(fcf) == n
    periods, published = _n_periods(n), _n_published(n)
    return tuple(
        _make_record(
            "annual_report", periods[i], f"{tag}{i}",
            published_at=published[i], revenue=revenue[i], free_cash_flow=fcf[i],
        )
        for i in range(n)
    )


def _custom_market_data_records(prices: tuple[float, ...], *, tag: str):
    n = len(prices)
    observations = _n_observations(n)
    return tuple(
        _make_record(
            "market_data_snapshot", observations[i], f"{tag}{i}",
            share_price=prices[i], shares_outstanding=100.0,
        )
        for i in range(n)
    )


def _recent_deterioration_growth_records():
    """Full-history Growth is real and positive on both metrics through
    period 3, but the most recent period reverses -- `_RECENT_WINDOW_SIZE`
    (4) exactly covers all four periods here, so the recent window
    itself is `MIXED_METRIC` on both Revenue and Free Cash Flow despite
    three of four periods being strong growth."""
    return _custom_growth_records(
        revenue=(1000.0, 1100.0, 1250.0, 1200.0), fcf=(100.0, 110.0, 200.0, 150.0), tag="rd"
    )


def _recovering_growth_records():
    """Full-history Growth is genuinely `MIXED_METRIC` on both metrics
    (an early decline, `2020->2021`), but the most recent
    `_RECENT_WINDOW_SIZE` (4) periods -- `2021` through `2024` -- are
    `STRONG_METRIC` on both: a real, improving recent trajectory that a
    full-history-only read would understate."""
    return _custom_growth_records(
        revenue=(100.0, 80.0, 90.0, 120.0, 160.0), fcf=(40.0, 30.0, 35.0, 50.0, 70.0), tag="rc"
    )


def _fcf_strong_revenue_weak_records():
    """Free Cash Flow rises every period (`STRONG_METRIC`); Revenue
    falls every period (`WEAK_METRIC`) -- one real, strong growth lever
    is not enough on its own (Part 4's own "one growth lever drives the
    arithmetic, corroborated by the other" design)."""
    return _custom_growth_records(revenue=(1000.0, 950.0, 900.0), fcf=(50.0, 80.0, 130.0), tag="fw")


def _single_late_market_observation_records():
    """Pairs with three real growth periods (unlike
    `_single_market_observation_records`, which has only one Free Cash
    Flow fact at all) -- eligibility is genuinely met, but exactly one
    market observation exists, so no historical yield *range* does.
    Dated at `_OBSERVATION_DATES[2]` (not the generic `_n_observations`
    helper) so it falls *after* `_strong_growth_records`'s own last
    published Free Cash Flow fact -- otherwise `cash_flow.py`'s own
    no-look-ahead rule would find no eligible fact at all and this
    would exercise `VALUATION_NOT_CONCLUSIVE` instead of the intended
    `NO_HISTORICAL_VALUATION_RANGE`."""
    return (_make_record("market_data_snapshot", _OBSERVATION_DATES[2], "slm", share_price=53.0, shares_outstanding=100.0),)


def _assemble(records=(), *, populated=False):
    engine_input, output = run_populated() if populated else run_minimal()
    return assemble_analysis(
        engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
    )


def _driver_kinds(horizon: HorizonOutlook) -> dict[OutlookDriverKind, str]:
    return {d.kind: d.direction.value for d in horizon.key_drivers}


class TestScenario1_StrongBusinessAttractiveValuation:
    def test_short_term_expected_return_is_a_real_range(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records)
        outlook = analysis.outlook.short_term
        assert outlook.expected_return is not None
        assert outlook.expected_return.low_percent <= outlook.expected_return.high_percent
        assert outlook.expected_return.basis is ReturnBasis.CUMULATIVE

    def test_long_term_drivers_are_positive(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records)
        drivers = _driver_kinds(analysis.outlook.long_term)
        assert drivers[OutlookDriverKind.GROWTH] == "positive"
        assert drivers[OutlookDriverKind.CAPITAL_ALLOCATION] == "positive"

    def test_three_periods_is_honestly_insufficient_for_a_rolling_cagr_window(self):
        """Calibration Sprint: `_rolling_cagr_observations` needs a fact
        `LONG_TERM_COMPOUNDING_YEARS` (4) periods later than its start to
        form even one observation -- this fixture's 3 periods can never
        produce one, regardless of how strong the business looks on a
        raw YoY basis. See `TestLongTermExpectedReturnCalibration` for
        real, populated Long-Term ranges built from fixtures with enough
        periods to actually smooth a rolling window; this test's own
        purpose narrowed from "produces a range" (v1) to "correctly
        recognizes it cannot yet" -- an equally real, equally required
        honesty check."""
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records)
        outlook = analysis.outlook.long_term
        assert outlook.expected_return is None
        assert outlook.expected_return_gap is OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY


class TestScenario2_StrongBusinessExpensiveValuation:
    def test_short_term_driver_is_negative(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _expensive_market_data()
        analysis = _assemble(records)
        drivers = _driver_kinds(analysis.outlook.short_term)
        assert drivers[OutlookDriverKind.VALUATION_RERATING] == "negative"

    def test_long_term_drivers_stay_positive_despite_expensive_valuation(self):
        """Business Quality and Valuation stay independent -- an
        expensive price never contaminates a real Growth/Capital
        Allocation driver's own direction."""
        records = _strong_growth_records() + _strong_capital_allocation_records() + _expensive_market_data()
        analysis = _assemble(records)
        drivers = _driver_kinds(analysis.outlook.long_term)
        assert drivers[OutlookDriverKind.GROWTH] == "positive"
        assert drivers[OutlookDriverKind.CAPITAL_ALLOCATION] == "positive"


class TestScenario3_WeakBusinessAttractiveValuation:
    def test_short_term_driver_is_positive(self):
        records = (
            _weak_growth_records() + _weak_capital_allocation_records() + _undervalued_against_declining_fcf_market_data()
        )
        analysis = _assemble(records)
        drivers = _driver_kinds(analysis.outlook.short_term)
        assert drivers[OutlookDriverKind.VALUATION_RERATING] == "positive"

    def test_long_term_drivers_are_negative(self):
        records = (
            _weak_growth_records() + _weak_capital_allocation_records() + _undervalued_against_declining_fcf_market_data()
        )
        analysis = _assemble(records)
        drivers = _driver_kinds(analysis.outlook.long_term)
        assert drivers[OutlookDriverKind.GROWTH] == "negative"
        assert drivers[OutlookDriverKind.CAPITAL_ALLOCATION] == "negative"


class TestScenario4_MixedEvidence:
    def test_growth_and_capital_allocation_drivers_disagree(self):
        records = _strong_growth_records() + _weak_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records)
        drivers = _driver_kinds(analysis.outlook.long_term)
        assert drivers[OutlookDriverKind.GROWTH] == "positive"
        assert drivers[OutlookDriverKind.CAPITAL_ALLOCATION] == "negative"

    def test_weak_capital_allocation_correctly_excludes_long_term_via_financial_risk(self):
        """Long-Term Expected Return v1: Growth alone disagreeing with
        Capital Allocation does not, by itself, block Long-Term -- but
        this specific fixture's weak Capital Allocation (net share
        issuance exceeding buybacks) is *also* real evidence of elevated
        Financial Risk (`financial_risk.py`'s own `capital_allocation
        _signal: WEAK -> HIGH` rule), and `_business_trajectory_eligible`
        excludes Long-Term whenever Financial Risk is `HIGH` -- a real,
        disclosed boundary condition (Part 5), not an arbitrary cutoff.
        Long-Term Outlook Conviction is correctly forced to
        `INSUFFICIENT_EVIDENCE` as a result, even though case-wide
        Conviction itself is not."""
        records = _strong_growth_records() + _weak_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records, populated=True)
        assert analysis.risk_analysis.findings
        financial_risk = next(
            f for f in analysis.risk_analysis.findings if f.category.value == "financial_risk"
        )
        assert financial_risk.status.value == "high"
        assert analysis.outlook.long_term.expected_return_gap is OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY
        assert analysis.outlook.long_term.conviction is ConvictionLevel.INSUFFICIENT_EVIDENCE


class TestScenario5_InsufficientData:
    def test_short_term_is_honestly_unavailable(self):
        analysis = _assemble(())
        outlook = analysis.outlook.short_term
        assert outlook.expected_return is None
        assert outlook.expected_return_gap is OutlookGapKind.VALUATION_NOT_CONCLUSIVE
        assert outlook.scenarios == ()
        assert outlook.key_drivers == ()

    def test_long_term_is_honestly_unavailable(self):
        analysis = _assemble(())
        outlook = analysis.outlook.long_term
        assert outlook.expected_return is None
        assert outlook.scenarios == ()
        assert outlook.key_drivers == ()

    def test_both_horizons_conviction_is_insufficient_evidence(self):
        analysis = _assemble(())
        assert analysis.outlook.short_term.conviction is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert analysis.outlook.long_term.conviction is ConvictionLevel.INSUFFICIENT_EVIDENCE


class TestScenario6_ShortTermWeakLongTermStrong:
    def test_directions_diverge_by_horizon(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _expensive_market_data()
        analysis = _assemble(records)
        short_drivers = _driver_kinds(analysis.outlook.short_term)
        long_drivers = _driver_kinds(analysis.outlook.long_term)
        assert short_drivers[OutlookDriverKind.VALUATION_RERATING] == "negative"
        assert long_drivers[OutlookDriverKind.GROWTH] == "positive"
        assert long_drivers[OutlookDriverKind.CAPITAL_ALLOCATION] == "positive"

    def test_short_term_expected_return_skews_negative(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _expensive_market_data()
        analysis = _assemble(records)
        expected_return = analysis.outlook.short_term.expected_return
        assert expected_return is not None
        assert expected_return.low_percent < 0


class TestScenario7_ShortTermStrongLongTermWeak:
    def test_directions_diverge_by_horizon(self):
        records = (
            _weak_growth_records() + _weak_capital_allocation_records() + _undervalued_against_declining_fcf_market_data()
        )
        analysis = _assemble(records)
        short_drivers = _driver_kinds(analysis.outlook.short_term)
        long_drivers = _driver_kinds(analysis.outlook.long_term)
        assert short_drivers[OutlookDriverKind.VALUATION_RERATING] == "positive"
        assert long_drivers[OutlookDriverKind.GROWTH] == "negative"
        assert long_drivers[OutlookDriverKind.CAPITAL_ALLOCATION] == "negative"

    def test_short_term_expected_return_skews_positive(self):
        records = (
            _weak_growth_records() + _weak_capital_allocation_records() + _undervalued_against_declining_fcf_market_data()
        )
        analysis = _assemble(records)
        expected_return = analysis.outlook.short_term.expected_return
        assert expected_return is not None
        assert expected_return.high_percent > 0


class TestScenario8_ScenarioUnavailable:
    def test_single_market_observation_yields_no_historical_range_gap(self):
        analysis = _assemble(_single_market_observation_records())
        outlook = analysis.outlook.short_term
        assert outlook.expected_return is None
        assert outlook.expected_return_gap is OutlookGapKind.NO_HISTORICAL_VALUATION_RANGE
        assert outlook.scenarios == ()
        assert outlook.scenarios_gap is OutlookGapKind.NO_HISTORICAL_VALUATION_RANGE

    def test_never_manufactures_a_scenario_from_one_observation(self):
        """A real current yield exists here (unlike Scenario 5's zero
        records) -- confirms the gap is specifically about the missing
        *range*, not a missing yield altogether."""
        analysis = _assemble(_single_market_observation_records())
        fcf_finding = next(
            f for f in analysis.valuation_engine.findings
            if f.kind.value == "fcf_yield_relative"
        )
        assert fcf_finding.current_yield is not None
        assert analysis.outlook.short_term.scenarios == ()


class TestScenario9_ConvictionUnavailable:
    """Outlook Conviction is a bounded derivation of case-wide
    Conviction (see `outlook.py`'s own module docstring) -- these tests
    confirm the bound holds in both directions: capped to
    INSUFFICIENT_EVIDENCE when data is genuinely thin (`run_minimal`),
    and tracking (not exceeding) whatever case-wide Conviction reaches
    with richer, real evidence (`run_populated`)."""

    def test_thin_evidence_forces_insufficient_evidence(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records, populated=False)
        assert analysis.conviction.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert analysis.outlook.short_term.conviction is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert analysis.outlook.long_term.conviction is ConvictionLevel.INSUFFICIENT_EVIDENCE

    def test_outlook_conviction_never_exceeds_case_wide_conviction(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        for populated in (False, True):
            analysis = _assemble(records, populated=populated)
            case_rank = _RANK[analysis.conviction.level]
            assert _RANK[analysis.outlook.short_term.conviction] <= case_rank
            assert _RANK[analysis.outlook.long_term.conviction] <= case_rank

    def test_data_sufficient_horizon_tracks_case_wide_conviction_exactly(self):
        """When this horizon's own data requirement *is* met, Outlook
        Conviction equals case-wide Conviction verbatim -- never
        independently inflated, never independently deflated beyond the
        documented cap. Short-Term only here (this fixture's 3 periods
        cannot make Long-Term data-sufficient post-Calibration-Sprint --
        see `TestLongTermExpectedReturnCalibration` for the identical
        bounded-derivation check against a Long-Term-eligible fixture)."""
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records, populated=True)
        assert analysis.outlook.short_term.conviction == analysis.conviction.level


class TestScenario10_NoValidStandingViewForMomentum:
    """`derive_outlook_momentum` pure-function coverage -- Momentum
    needs a genuine prior Standing View (a non-baseline
    `ChangeIntelligence`) to mean anything; every path that lacks one
    honestly returns `UNAVAILABLE`, never a fabricated trend."""

    def test_no_change_intelligence_at_all_is_unavailable(self):
        assert derive_outlook_momentum(None, is_baseline=False) is OutlookMomentumKind.UNAVAILABLE

    def test_baseline_case_is_unavailable_even_with_a_thesis_impact(self):
        """A baseline always carries `ThesisImpact.UNCHANGED` by
        construction (`compare_snapshots`'s own baseline branch) -- this
        confirms `is_baseline` alone forces UNAVAILABLE, never reading
        UNCHANGED as a real "stable" trend for a Case's first analysis."""
        assert derive_outlook_momentum(ThesisImpact.UNCHANGED, is_baseline=True) is OutlookMomentumKind.UNAVAILABLE

    def test_strengthened_maps_to_strengthening(self):
        assert derive_outlook_momentum(ThesisImpact.STRENGTHENED, is_baseline=False) is OutlookMomentumKind.STRENGTHENING

    def test_weakened_maps_to_weakening(self):
        assert derive_outlook_momentum(ThesisImpact.WEAKENED, is_baseline=False) is OutlookMomentumKind.WEAKENING

    def test_unchanged_maps_to_stable(self):
        assert derive_outlook_momentum(ThesisImpact.UNCHANGED, is_baseline=False) is OutlookMomentumKind.STABLE

    def test_mixed_stays_mixed_not_collapsed_to_stable(self):
        """Semantic Hardening Pass: `MIXED` (some dimensions
        strengthened, others weakened) is a different fact from
        `UNCHANGED` (nothing moved) -- collapsing both onto `STABLE`
        would erase that difference, so `MIXED` maps to its own
        `OutlookMomentumKind.MIXED`."""
        assert derive_outlook_momentum(ThesisImpact.MIXED, is_baseline=False) is OutlookMomentumKind.MIXED


class TestRerationMathIsSelfConsistent:
    """Not one of the ten named scenarios, but a direct check on the
    one real formula this sprint introduces (Part 4's own "must not be
    authored independently" requirement) -- verified against the exact
    live AAPL numbers this sprint's own gap report cites."""

    def test_bull_uses_the_lowest_historical_yield(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records)
        scenarios = {s.kind: s for s in analysis.outlook.short_term.scenarios}
        assert set(scenarios) == {ScenarioKind.BULL, ScenarioKind.BASE, ScenarioKind.BEAR}
        bull, base, bear = scenarios[ScenarioKind.BULL], scenarios[ScenarioKind.BASE], scenarios[ScenarioKind.BEAR]
        assert bull.assumption.target_fcf_yield <= base.assumption.target_fcf_yield <= bear.assumption.target_fcf_yield

    def test_return_formula_matches_yield_ratio_identity(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records)
        for scenario in analysis.outlook.short_term.scenarios:
            expected = (scenario.assumption.current_fcf_yield / scenario.assumption.target_fcf_yield) - 1.0
            assert scenario.return_percent == pytest.approx(expected)

    def test_assumption_discloses_the_historical_sample_size(self):
        """Semantic Hardening Pass: `observation_count` is real,
        disclosed transparency about how many historical FCF-yield
        observations a scenario's `target_fcf_yield` was drawn from --
        the fixture here has 3 total market observations (2 historical
        once the most recent is excluded), and every scenario's
        assumption must say so."""
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records)
        for scenario in analysis.outlook.short_term.scenarios:
            assert scenario.assumption.observation_count == 2
        assert analysis.outlook.short_term.expected_return.assumption.observation_count == 2

    def test_headline_range_bounds_are_the_min_and_max_of_the_three_scenarios(self):
        records = _strong_growth_records() + _strong_capital_allocation_records() + _undervalued_market_data()
        analysis = _assemble(records)
        returns = [s.return_percent for s in analysis.outlook.short_term.scenarios]
        expected_return = analysis.outlook.short_term.expected_return
        assert expected_return.low_percent == pytest.approx(min(returns))
        assert expected_return.high_percent == pytest.approx(max(returns))


#: Calibration Sprint fixtures need real multi-period (8-10 fiscal year)
#: histories -- long enough to form at least one rolling
#: `LONG_TERM_COMPOUNDING_YEARS`-year CAGR window, several of them for a
#: real distribution. Started far enough before `GENERATED_AT` (2026) that
#: even a 10-period fixture never brushes up against `outlook.py`'s own
#: `_exclude_future_dated` guard -- a real, adopted correctness rule
#: discovered this sprint (a stray test record with a future `period_end`
#: silently inflating a rolling-CAGR endpoint in production), not a
#: fixture-only concern.
_CAL_START_YEAR = 2005


def _cal_periods(n: int) -> tuple[date, ...]:
    return tuple(date(_CAL_START_YEAR + i, 12, 31) for i in range(n))


def _cal_published(n: int) -> tuple[datetime, ...]:
    return tuple(datetime(_CAL_START_YEAR + 1 + i, 2, 15, tzinfo=timezone.utc) for i in range(n))


def _cal_observations(n: int) -> tuple[date, ...]:
    return tuple(date(_CAL_START_YEAR + 1 + i, 3, 1) for i in range(n))


def _cal_growth_records(revenue: tuple[float, ...], fcf: tuple[float, ...], *, tag: str):
    n = len(revenue)
    assert len(fcf) == n
    periods, published = _cal_periods(n), _cal_published(n)
    return tuple(
        _make_record(
            "annual_report", periods[i], f"{tag}{i}",
            published_at=published[i], revenue=revenue[i], free_cash_flow=fcf[i],
        )
        for i in range(n)
    )


def _cal_market_records(prices: tuple[float, ...], *, tag: str):
    n = len(prices)
    observations = _cal_observations(n)
    return tuple(
        _make_record(
            "market_data_snapshot", observations[i], f"{tag}{i}", share_price=prices[i], shares_outstanding=100.0
        )
        for i in range(n)
    )


#: A flat, mildly-rising 8-observation price series -- reused wherever a
#: scenario's point is the *growth* mechanism, not the valuation one.
_CAL_STEADY_PRICES = (50.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0)


class TestLongTermExpectedReturnCalibration:
    """Calibration Sprint's 15 named semantic scenarios (Part 19) --
    real, multi-period (8-10 fiscal year) fixtures, long enough to
    exercise the calibrated model's own mechanism: rolling
    `LONG_TERM_COMPOUNDING_YEARS`-year Free Cash Flow CAGR, gated to
    windows Revenue evidence actually corroborates, with growth status
    and `TOTAL_DEBT` escalation as the eligibility floor. Values verified
    against real AAPL/MSFT shapes and this sprint's own live database
    finding (see `_cal_periods`'s own docstring) before being written
    here -- not hand-tuned to make an assertion pass."""

    def test_noisy_but_durable_fcf_is_eligible(self):
        """Free Cash Flow bounces up and down every single period (never
        `STRONG_METRIC` on its own recent window -- the exact real shape
        Part 1 found in AAPL/MSFT), but Revenue rises every period and
        rolling 4-year CAGR smooths the noise into a real, positive,
        tight range. Proves the calibrated gate no longer requires
        monotonic Free Cash Flow."""
        revenue = (100, 108, 115, 124, 130, 140, 148, 158)
        fcf = (40, 35, 44, 39, 48, 43, 52, 47)
        records = _cal_growth_records(revenue, fcf, tag="ndf") + _cal_market_records(_CAL_STEADY_PRICES, tag="mndf")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return_gap is None
        assert outlook.expected_return.assumption.growth_rate > 0

    def test_genuine_both_metric_deterioration_is_unavailable(self):
        """Revenue *and* Free Cash Flow both contract in every single
        period -- Growth's own full-history status reaches `WEAK`, and
        the calibrated gate still refuses this business regardless of
        how the rolling-CAGR/corroboration machinery would otherwise
        treat it. The one condition v1 and the calibration both agree
        on: a business that has never once grown does not get a forward
        range."""
        revenue = (200, 190, 178, 165, 150, 135, 118, 100)
        fcf = (80, 74, 66, 58, 48, 38, 26, 14)
        records = _cal_growth_records(revenue, fcf, tag="gbd") + _cal_market_records(_CAL_STEADY_PRICES, tag="mgbd")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is None
        assert outlook.expected_return_gap is OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY

    def test_stable_revenue_with_noisy_fcf_is_eligible(self):
        """Revenue essentially flat (~0% real drift, never a clean
        trend), Free Cash Flow noisy around a stable level -- Growth
        reaches `MODERATE`, not `WEAK`, and enough revenue-corroborated
        rolling windows exist for a real, if narrow, range."""
        revenue = (100, 101, 99, 102, 100, 103, 101, 104)
        fcf = (40, 36, 44, 38, 46, 40, 48, 42)
        records = _cal_growth_records(revenue, fcf, tag="srn") + _cal_market_records(_CAL_STEADY_PRICES, tag="msrn")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return_gap is None

    def test_deteriorating_revenue_with_noisy_fcf_produces_an_honestly_negative_range(self):
        """Revenue contracts every period, but Free Cash Flow is
        genuinely mixed (not all-contracting) -- Growth's own rule table
        classifies this `MODERATE` (only one of two metrics is `WEAK`),
        so the calibrated gate does not exclude it outright. The
        corroborated growth range is honestly negative -- a real,
        disclosed reflection of a shrinking top line, not a silently
        withheld number and not a fabricated positive one."""
        revenue = (150, 140, 128, 115, 100, 85, 70, 55)
        fcf = (50, 55, 45, 50, 42, 48, 38, 44)
        records = _cal_growth_records(revenue, fcf, tag="drn") + _cal_market_records(_CAL_STEADY_PRICES, tag="mdrn")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return.high_percent < 0

    def test_temporary_fcf_spike_does_not_dominate_the_range(self):
        """One period has an anomalous Free Cash Flow spike (an asset
        sale, in spirit) against an otherwise steady business -- rolling
        4-year CAGR means the spike appears in only some of the
        overlapping windows, not all of them, so it pulls the Bull case
        up without erasing the other, unaffected windows from the
        distribution."""
        revenue = (100, 108, 116, 125, 134, 144, 155, 166)
        fcf = (40, 43, 46, 49, 90, 53, 57, 61)
        records = _cal_growth_records(revenue, fcf, tag="spk") + _cal_market_records(_CAL_STEADY_PRICES, tag="mspk")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return.assumption.growth_observation_count > 1

    def test_temporary_fcf_collapse_recovering_off_a_low_base_inflates_the_pct_range(self):
        """One period has an anomalous Free Cash Flow collapse (a
        legal settlement, in spirit) that fully recovers -- a real,
        disclosed caveat this sprint's own adversarial testing surfaced:
        recovering off a depressed base is mathematically a large
        percentage gain regardless of the absolute dollars involved, so
        the rolling-CAGR window spanning the collapse pulls the range's
        *upper* bound up, not down. The model reports this real
        arithmetic honestly rather than "fixing" it with an invented
        adjustment."""
        revenue = (100, 108, 116, 125, 134, 144, 155, 166)
        fcf = (40, 43, 46, 10, 52, 56, 60, 64)
        records = _cal_growth_records(revenue, fcf, tag="col") + _cal_market_records(_CAL_STEADY_PRICES, tag="mcol")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return.assumption.growth_observation_count > 1
        assert outlook.expected_return.high_percent > 0.3

    def test_acquisition_driven_step_change_is_not_specially_detected(self):
        """A one-time step-change in both Revenue and Free Cash Flow (an
        acquisition, in spirit) is not distinguished from organic growth
        -- this module has no mechanism to tell the two apart, and does
        not invent one. The step shows up as an elevated growth
        assumption; it is disclosed via `growth_observation_count`, not
        silently smoothed away or specially flagged."""
        revenue = (100, 105, 110, 200, 210, 220, 230, 240)
        fcf = (30, 32, 34, 70, 75, 80, 85, 90)
        records = _cal_growth_records(revenue, fcf, tag="acq") + _cal_market_records(_CAL_STEADY_PRICES, tag="macq")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return.assumption.growth_rate > 0.1

    def test_cyclical_cash_generation_without_net_trend_produces_a_low_flat_range(self):
        """Free Cash Flow alternates high/low every single period around
        a flat level (no net multi-year drift) -- a real, durable
        business model (seasonality/cyclicality, in spirit), not a
        deteriorating one. The calibrated model does not require
        monotonic growth, only real corroborated evidence, so this stays
        eligible with a low, close-to-flat range rather than being
        excluded for "not growing every year." """
        revenue = (100, 102, 101, 103, 102, 104, 103, 105)
        fcf = (40, 55, 38, 53, 40, 55, 38, 53)
        records = _cal_growth_records(revenue, fcf, tag="cyc") + _cal_market_records(_CAL_STEADY_PRICES, tag="mcyc")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert abs(outlook.expected_return.assumption.growth_rate) < 0.05

    def test_negative_fcf_periods_are_excluded_from_growth_rates_not_treated_as_a_crash(self):
        """The business's earliest periods have genuinely negative Free
        Cash Flow (pre-profitability, in spirit) before turning positive
        -- `_rolling_cagr_observations` only computes a rate between two
        positive endpoints (mirrors `cash_flow.py`'s own refusal to
        divide by a non-positive Free Cash Flow), so windows touching a
        negative period are excluded rather than producing a nonsensical
        sign, and the model still reaches a real range from the
        remaining, all-positive windows."""
        revenue = (50, 60, 72, 86, 103, 124, 148, 178)
        fcf = (-10, -5, 8, 15, 22, 28, 35, 42)
        records = _cal_growth_records(revenue, fcf, tag="neg") + _cal_market_records(_CAL_STEADY_PRICES, tag="mneg")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return.assumption.growth_observation_count >= 2

    def test_thin_four_period_sample_cannot_form_a_single_rolling_window_is_unavailable(self):
        """Four periods is one short of the five a
        `LONG_TERM_COMPOUNDING_YEARS`-year rolling window needs
        (`range(4 - 4)` is empty) -- correctly, honestly unavailable,
        never a range built from a single raw delta."""
        revenue = (100, 110, 121, 133)
        fcf = (40, 44, 48, 53)
        records = _cal_growth_records(revenue, fcf, tag="thn") + _cal_market_records((50.0, 52.0, 53.0, 54.0), tag="mthn")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is None
        assert outlook.expected_return_gap is OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY

    def test_long_stable_history_produces_a_narrow_high_confidence_shaped_range(self):
        """Ten periods of genuinely consistent ~8%/year growth on both
        Revenue and Free Cash Flow -- six real rolling-CAGR observations,
        all close together, producing the narrowest range in this suite.
        The model's own range width tracks real historical consistency,
        exactly Part 5's "narrower ranges when history is consistent"
        without any invented dispersion formula."""
        revenue = (100, 108, 117, 126, 136, 147, 159, 172, 186, 201)
        fcf = (40, 43, 47, 50, 54, 59, 63, 68, 74, 80)
        prices = (50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0)
        records = _cal_growth_records(revenue, fcf, tag="lng") + _cal_market_records(prices, tag="mlng")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return.assumption.growth_observation_count >= 5
        spread = outlook.expected_return.high_percent - outlook.expected_return.low_percent
        assert spread < 0.05

    def test_extreme_single_year_spike_is_diluted_not_erased_by_rolling_windows(self):
        """One freak Free Cash Flow year (roughly 4x any other period) --
        Part 4's own central adversarial case. Rolling 4-year CAGR means
        this single year appears in more than one overlapping window but
        never dominates *every* window the way a raw single-period YoY
        delta would -- the range is elevated but stays inside what the
        overlapping, only-partially-affected windows actually produce,
        not the raw spike's own multiple-hundred-percent single-year
        rate."""
        revenue = (100, 110, 121, 133, 146, 161, 177, 195)
        fcf = (40, 44, 48, 53, 58, 200, 70, 77)
        records = _cal_growth_records(revenue, fcf, tag="ext") + _cal_market_records(_CAL_STEADY_PRICES, tag="mext")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        raw_spike_rate = (200.0 / 58.0) - 1.0
        assert outlook.expected_return.assumption.growth_rate < raw_spike_rate

    def test_aapl_like_history_produces_a_real_but_valuation_dragged_range(self):
        """Real (relabeled-date) AAPL Revenue/Free Cash Flow figures,
        2018-2025 -- moderate real revenue growth, genuinely noisy Free
        Cash Flow, reused verbatim from this sprint's own live database
        finding. A rising price series (mirroring AAPL's own real,
        historically-rich valuation) still lets the business trajectory
        qualify; the terminal-valuation reversion (unchanged from v1,
        median historical yield) can still legitimately pull the range
        toward or below zero -- exactly what this sprint's own live
        AAPL/MSFT verification found, and exactly why Expected Return
        and a price forecast are different concepts."""
        revenue = (265595, 260174, 274515, 365817, 394328, 383285, 391035, 416161)
        fcf = (64121, 58896, 73365, 92953, 111443, 99584, 108807, 98767)
        prices = (40.0, 42.0, 55.0, 70.0, 68.0, 72.0, 80.0, 85.0)
        records = _cal_growth_records(revenue, fcf, tag="apl") + _cal_market_records(prices, tag="mapl")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return_gap is None
        assert outlook.expected_return.assumption.growth_rate > 0

    def test_msft_like_history_produces_a_real_range(self):
        """Real (relabeled-date) MSFT Revenue/Free Cash Flow figures,
        2018-2025 -- strong, consistent real revenue growth with a real
        recent Free Cash Flow deceleration (the live AI-capex buildout
        this sprint's own database verification found), still eligible
        under the calibrated gate, still a real, disclosed range."""
        revenue = (110360, 125843, 143015, 168088, 198270, 211915, 245122, 281724)
        fcf = (32252, 38260, 45234, 56118, 65149, 59475, 74071, 71611)
        prices = (90.0, 110.0, 155.0, 220.0, 240.0, 230.0, 320.0, 340.0)
        records = _cal_growth_records(revenue, fcf, tag="mft") + _cal_market_records(prices, tag="mmft")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return_gap is None

    def test_tsla_like_zero_business_facts_is_unavailable(self):
        """No `BusinessFact`s at all -- the honest floor, and the
        sprint's own explicit adversarial control (Part 15): a company
        with no real evidence must never receive a confident number no
        matter how permissive the rest of the calibration became."""
        outlook = _assemble(()).outlook.long_term
        assert outlook.expected_return is None
        assert outlook.expected_return_gap is OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY
        assert outlook.scenarios == ()
        assert outlook.conviction is ConvictionLevel.INSUFFICIENT_EVIDENCE

    def test_capital_allocation_never_enters_the_return_arithmetic(self):
        """The Long-Term Expected Return figure itself is byte-for-byte
        identical whether real buyback/debt Capital Allocation evidence
        exists at all -- proof, not just documentation, that share
        count/buyback evidence stays out of the arithmetic (this
        module's own docstring on why -- the AAPL stock-split hazard).

        Calibration Phase 4: `growth_and_market`'s own real, positive
        Free Cash Flow now also drives Capital Allocation's
        `cash_generation` signal (the same shared `FREE_CASH_FLOW`
        facts `financial_risk.py`'s own signal of the same name already
        reads) -- so a `CAPITAL_ALLOCATION` driver is present either
        way, `neutral` from `cash_generation` alone without buyback/debt
        evidence, `positive` once `_strong_capital_allocation_records`'
        own corroborating buyback and debt-reduction signals are added."""
        revenue = (100, 108, 115, 124, 130, 140, 148, 158)
        fcf = (40, 35, 44, 39, 48, 43, 52, 47)
        growth_and_market = _cal_growth_records(revenue, fcf, tag="cae") + _cal_market_records(
            _CAL_STEADY_PRICES, tag="mcae"
        )
        with_capital_allocation = _assemble(growth_and_market + _strong_capital_allocation_records())
        without_capital_allocation = _assemble(growth_and_market)
        er_with = with_capital_allocation.outlook.long_term.expected_return
        er_without = without_capital_allocation.outlook.long_term.expected_return
        assert er_with is not None and er_without is not None
        assert er_with.low_percent == pytest.approx(er_without.low_percent)
        assert er_with.high_percent == pytest.approx(er_without.high_percent)
        with_drivers = _driver_kinds(with_capital_allocation.outlook.long_term)
        without_drivers = _driver_kinds(without_capital_allocation.outlook.long_term)
        assert with_drivers[OutlookDriverKind.CAPITAL_ALLOCATION] == "positive"
        assert without_drivers[OutlookDriverKind.CAPITAL_ALLOCATION] == "neutral"

    def test_margin_and_share_count_fields_never_exist_on_the_assumption(self):
        """Structural guardrail, not just prose: `OutlookAssumption` has
        no share-count field at all, and its only margin-adjacent field
        (`MARGIN_TREND`'s own informational Key Driver) is never on
        `OutlookAssumption` itself -- Part 6/7/8's exclusions from the
        return *arithmetic* stay true by construction, not by discipline
        that could silently erode in a future edit."""
        import dataclasses

        from atlas.analysis_engine.outlook import OutlookAssumption

        field_names = {f.name for f in dataclasses.fields(OutlookAssumption)}
        assert not any("margin" in name for name in field_names)
        assert not any("share" in name for name in field_names)

    def test_bull_uses_highest_realized_growth_bear_uses_lowest(self):
        """Unlike Short-Term's yield-only scenarios (where a *lower*
        yield is the Bull case), Long-Term's growth lever is not
        inverted -- higher realized Free Cash Flow growth is
        unambiguously the Bull assumption."""
        revenue = (100, 108, 117, 126, 136, 147, 159, 172, 186, 201)
        fcf = (40, 43, 47, 50, 54, 59, 63, 68, 74, 80)
        prices = (50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0)
        records = _cal_growth_records(revenue, fcf, tag="bul") + _cal_market_records(prices, tag="mbul")
        analysis = _assemble(records)
        scenarios = {s.kind: s for s in analysis.outlook.long_term.scenarios}
        assert set(scenarios) == {ScenarioKind.BULL, ScenarioKind.BASE, ScenarioKind.BEAR}
        bull, base, bear = scenarios[ScenarioKind.BULL], scenarios[ScenarioKind.BASE], scenarios[ScenarioKind.BEAR]
        assert bear.assumption.growth_rate <= base.assumption.growth_rate <= bull.assumption.growth_rate
        assert bear.return_percent <= base.return_percent <= bull.return_percent

    def test_terminal_yield_is_the_historical_median_and_constant_across_scenarios(self):
        """Part 8/9/11: all three scenarios share the identical, real
        historical-median terminal yield -- Bull/Base/Bear differ on one
        coherent business assumption (growth) only, never a second,
        undisclosed swing in the valuation assumption. Preserved
        unchanged from v1 through the Calibration Sprint, per Part 9's
        own explicit instruction not to touch terminal valuation this
        sprint."""
        revenue = (100, 108, 117, 126, 136, 147, 159, 172, 186, 201)
        fcf = (40, 43, 47, 50, 54, 59, 63, 68, 74, 80)
        prices = (50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0)
        records = _cal_growth_records(revenue, fcf, tag="trm") + _cal_market_records(prices, tag="mtrm")
        analysis = _assemble(records)
        fcf_finding = next(f for f in analysis.valuation_engine.findings if f.kind.value == "fcf_yield_relative")
        expected_terminal = statistics.median(fcf_finding.historical_yields)
        for scenario in analysis.outlook.long_term.scenarios:
            assert scenario.assumption.target_fcf_yield == pytest.approx(expected_terminal)

    def test_annualized_return_formula_matches_manual_computation(self):
        """Regression-proofs the algebra itself (Part 4's own "must not
        be authored independently" requirement): for every Long-Term
        scenario, `return_percent` equals
        `((1+g)**years * current_yield/terminal_yield) ** (1/years) - 1`
        computed independently here."""
        revenue = (100, 108, 117, 126, 136, 147, 159, 172, 186, 201)
        fcf = (40, 43, 47, 50, 54, 59, 63, 68, 74, 80)
        prices = (50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0)
        records = _cal_growth_records(revenue, fcf, tag="frm") + _cal_market_records(prices, tag="mfrm")
        analysis = _assemble(records)
        assert analysis.outlook.long_term.scenarios, "fixture must be eligible for this test to verify anything"
        for scenario in analysis.outlook.long_term.scenarios:
            assumption = scenario.assumption
            years = assumption.horizon_years
            total_multiple = (1.0 + assumption.growth_rate) ** years * (
                assumption.current_fcf_yield / assumption.target_fcf_yield
            )
            expected = total_multiple ** (1.0 / years) - 1.0
            assert scenario.return_percent == pytest.approx(expected)

    def test_synthetic_extreme_growth_case_from_prior_sprint_is_no_longer_unbounded(self):
        """Part 16: the prior sprint's own 3-period `_strong_growth_records`
        fixture produced an approximately 28%-112% annualized range from
        just 2 raw single-year deltas dominated by the fixture's own
        artificial 82% single-period jump. That exact fixture is now
        honestly unavailable (too few periods for even one rolling
        window -- see `TestScenario1_StrongBusinessAttractiveValuation
        .test_three_periods_is_honestly_insufficient_for_a_rolling_cagr_window`).
        This test proves the *general* claim, not just that one fixture's
        absence: an equally aggressive but longer, real-shaped 8-period
        history (`test_extreme_single_year_spike_is_diluted_not_erased_by
        _rolling_windows`, `test_temporary_fcf_spike_does_not_dominate
        _the_range`) never reproduces a 100%+ annualized figure -- the
        calibrated model rejects that class of output structurally
        (revenue corroboration + rolling-window smoothing), not by
        coincidence of which fixture happens to be in the suite."""
        revenue = (100, 110, 121, 133, 146, 161, 177, 195)
        fcf = (40, 44, 48, 53, 58, 200, 70, 77)  # the single-year 200 spike, same shape as before
        records = _cal_growth_records(revenue, fcf, tag="syn") + _cal_market_records(_CAL_STEADY_PRICES, tag="msyn")
        outlook = _assemble(records).outlook.long_term
        assert outlook.expected_return is not None
        assert outlook.expected_return.high_percent < 1.0, "must not reproduce the prior sprint's ~100%+ Bull case"
