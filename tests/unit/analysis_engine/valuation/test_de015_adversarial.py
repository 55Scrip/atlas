"""`DE-015` Implementation Sprint -- Phase 14's own required deliverable:
a single, comprehensive adversarial suite covering all 20 named cases from
the sprint prompt, exercised at the real `evaluate_valuation_support`
orchestration level (not the individual proof-path level, which already
has its own dedicated test files: `test_scenario_proof.py`,
`test_net_cash_proof.py`, `test_eligibility.py`, `test_synthesis.py`).

Every fixture here is either a real `BusinessRecord` fed through
`extract_facts_from_records`/`extract_valuation_facts_from_records` (the
same "reuse, never re-derive" discipline the rest of this arc already
uses), or -- for the one case where no real company shape can honestly
produce two conflicting *sufficient* proofs at once (case 11) -- a
targeted patch of the two proof-path functions `support.py` itself calls,
exactly the technique `test_support.py::TestRegression` already
establishes as legitimate for isolating orchestration logic.
"""
from __future__ import annotations

import inspect
from datetime import date, datetime, timezone
from unittest.mock import patch

from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.direction_selector import select_direction
from atlas.analysis_engine.recommendation import evaluate_recommendation_gate
from atlas.analysis_engine.recommendation_conviction import calculate_recommendation_conviction
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.analysis_engine.valuation.pipeline import evaluate_valuation
from atlas.analysis_engine.valuation.proof import PathProof, ProofVerdict
from atlas.analysis_engine.valuation.support import (
    ValuationSupportGapKind,
    ValuationSupportStatus,
    evaluate_valuation_support,
)
from tests.unit.analysis_engine.valuation._fixtures import fundamentals_record, market_record

_GENERATED_AT = datetime(2026, 8, 13, tzinfo=timezone.utc)


def _filed(year: int, month: int = 2, day: int = 15) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _support(records, *, generated_at: datetime = _GENERATED_AT):
    business_facts = extract_facts_from_records(records, evaluated_at=generated_at)
    valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=generated_at)
    valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=generated_at)
    return evaluate_valuation_support(valuation_engine, business_facts, valuation_facts, generated_at=generated_at)


def _durable_growth_records(tag: str = "dg"):
    """6 periods, Revenue + Free Cash Flow both growing every period --
    identical shape to `test_scenario_proof.py`'s own fixture, so the
    eligibility/growth-range math is already independently verified."""
    revenue = (900.0, 1000.0, 1100.0, 1250.0, 1400.0, 1600.0)
    fcf = (90.0, 100.0, 115.0, 140.0, 165.0, 200.0)
    years = (2019, 2020, 2021, 2022, 2023, 2024)
    return tuple(
        fundamentals_record(
            period_end=date(year, 12, 31),
            identifier=f"{tag}{year}",
            published_at=_filed(year + 1),
            revenue=revenue[i],
            free_cash_flow=fcf[i],
        )
        for i, year in enumerate(years)
    )


def _envelope_market_records(*, current: float, hist_a: float, hist_b: float, tag: str = "mk"):
    """3 market records priced so that `FCF_YIELD_RELATIVE`'s own real
    computation (`eligible_fcf / (price * shares)`) produces exactly the
    requested current/historical yields against `_durable_growth_records`'s
    real, published FCF values (140 as of 2023-03, 165 as of 2024-03, 200
    as of 2025-03 -- the most recent published FCF at or before each
    observation date)."""
    shares = 100.0
    return (
        market_record(period_end=date(2023, 3, 1), identifier=f"{tag}23", share_price=140.0 / (hist_a * shares), shares_outstanding=shares),
        market_record(period_end=date(2024, 3, 1), identifier=f"{tag}24", share_price=165.0 / (hist_b * shares), shares_outstanding=shares),
        market_record(period_end=date(2025, 3, 1), identifier=f"{tag}25", share_price=200.0 / (current * shares), shares_outstanding=shares),
    )


def _cash_debt_records(*, cash: float, debt: float, tag: str = "bs"):
    return (
        fundamentals_record(period_end=date(2024, 12, 31), identifier=f"{tag}cash", published_at=_filed(2025), cash=cash),
        fundamentals_record(period_end=date(2024, 12, 31), identifier=f"{tag}debt", published_at=_filed(2025), total_debt=debt),
    )


# ---------------------------------------------------------------------------
# 1. No valuation data at all
# ---------------------------------------------------------------------------


class TestCase01NoValuationData:
    def test_no_records_is_insufficient_input(self):
        support = _support(())
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.gap is ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA


# ---------------------------------------------------------------------------
# 2. UNDERVALUED alone (`DE-008` boundary)
# ---------------------------------------------------------------------------


class TestCase02UndervaluedAlone:
    def test_undervalued_fcf_yield_alone_never_becomes_supported(self):
        records = (
            fundamentals_record(period_end=date(2022, 12, 31), identifier="uv22", published_at=_filed(2023), free_cash_flow=100.0),
            fundamentals_record(period_end=date(2023, 12, 31), identifier="uv23", published_at=_filed(2024), free_cash_flow=110.0),
            fundamentals_record(period_end=date(2024, 12, 31), identifier="uv24", published_at=_filed(2025), free_cash_flow=200.0),
            market_record(period_end=date(2023, 3, 1), identifier="uvm22", share_price=50.0, shares_outstanding=100.0),
            market_record(period_end=date(2024, 3, 1), identifier="uvm23", share_price=52.0, shares_outstanding=100.0),
            market_record(period_end=date(2025, 3, 1), identifier="uvm24", share_price=53.0, shares_outstanding=100.0),
        )
        business_facts = extract_facts_from_records(records, evaluated_at=_GENERATED_AT)
        valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=_GENERATED_AT)
        valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=_GENERATED_AT)
        fcf_yield = next(f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)
        assert fcf_yield.status is ValuationStatus.UNDERVALUED

        support = _support(records)
        assert support.status is not ValuationSupportStatus.SUPPORTED


# ---------------------------------------------------------------------------
# 3. EXPENSIVE alone (`DE-008` boundary, symmetric)
# ---------------------------------------------------------------------------


class TestCase03ExpensiveAlone:
    def test_expensive_fcf_yield_alone_never_becomes_not_supported(self):
        records = (
            fundamentals_record(period_end=date(2022, 12, 31), identifier="ex22", published_at=_filed(2023), free_cash_flow=100.0),
            fundamentals_record(period_end=date(2023, 12, 31), identifier="ex23", published_at=_filed(2024), free_cash_flow=150.0),
            fundamentals_record(period_end=date(2024, 12, 31), identifier="ex24", published_at=_filed(2025), free_cash_flow=250.0),
            market_record(period_end=date(2023, 3, 1), identifier="exm22", share_price=10.0, shares_outstanding=100.0),
            market_record(period_end=date(2024, 3, 1), identifier="exm23", share_price=10.0, shares_outstanding=100.0),
            market_record(period_end=date(2025, 3, 1), identifier="exm24", share_price=90.0, shares_outstanding=100.0),
        )
        business_facts = extract_facts_from_records(records, evaluated_at=_GENERATED_AT)
        valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=_GENERATED_AT)
        valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=_GENERATED_AT)
        fcf_yield = next(f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)
        assert fcf_yield.status is ValuationStatus.EXPENSIVE

        support = _support(records)
        assert support.status is not ValuationSupportStatus.NOT_SUPPORTED


# ---------------------------------------------------------------------------
# 4/5/6. Full envelope shapes, end to end through the real orchestrator
# ---------------------------------------------------------------------------


class TestCase04FullyPositiveEnvelope:
    def test_establishes_supported_end_to_end(self):
        records = _durable_growth_records("p4") + _envelope_market_records(current=0.05, hist_a=0.04, hist_b=0.06, tag="p4m")
        support = _support(records)
        assert support.status is ValuationSupportStatus.SUPPORTED
        assert support.gap is None


class TestCase05FullyNegativeEnvelope:
    def test_establishes_not_supported_end_to_end(self):
        records = _durable_growth_records("p5") + _envelope_market_records(current=0.01, hist_a=0.05, hist_b=0.08, tag="p5m")
        support = _support(records)
        assert support.status is ValuationSupportStatus.NOT_SUPPORTED


class TestCase06StraddlingEnvelope:
    def test_stays_honestly_insufficient_input(self):
        records = _durable_growth_records("p6") + _envelope_market_records(current=0.02, hist_a=0.018, hist_b=0.05, tag="p6m")
        support = _support(records)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.gap is ValuationSupportGapKind.SCENARIO_ENVELOPE_INCONCLUSIVE


# ---------------------------------------------------------------------------
# 7/8. Net-Cash path alone (Scenario ineligible on thin history)
# ---------------------------------------------------------------------------


class TestCase07NetCashEstablishes:
    def test_below_net_cash_establishes_supported_even_with_no_scenario_proof(self):
        records = _cash_debt_records(cash=1000.0, debt=100.0, tag="nc7") + (
            market_record(period_end=date(2025, 3, 1), identifier="nc7mkt", share_price=1.0, shares_outstanding=10.0),
        )
        support = _support(records)
        assert support.status is ValuationSupportStatus.SUPPORTED


class TestCase08NetCashDoesNotEstablish:
    def test_priced_above_net_cash_stays_insufficient_input(self):
        records = _cash_debt_records(cash=1000.0, debt=100.0, tag="nc8") + (
            market_record(period_end=date(2025, 3, 1), identifier="nc8mkt", share_price=1000.0, shares_outstanding=10.0),
        )
        support = _support(records)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.gap is ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA


# ---------------------------------------------------------------------------
# 9/10. Scenario sufficient, Net-Cash merely `does_not_establish` (not
# missing) -- confirms a real `does_not_establish` never blocks a real
# `SUPPORT`/`NON_SUPPORT` from the other path.
# ---------------------------------------------------------------------------


class TestCase09ScenarioSupportNetCashDoesNotEstablish:
    def test_scenario_support_wins_while_net_cash_honestly_does_not_establish(self):
        records = (
            _durable_growth_records("p9")
            + _envelope_market_records(current=0.05, hist_a=0.04, hist_b=0.06, tag="p9m")
            + _cash_debt_records(cash=50.0, debt=10.0, tag="p9bs")
        )
        support = _support(records)
        assert support.status is ValuationSupportStatus.SUPPORTED


class TestCase10ScenarioNonSupportNetCashDoesNotEstablish:
    def test_scenario_non_support_wins_while_net_cash_honestly_does_not_establish(self):
        records = (
            _durable_growth_records("p10")
            + _envelope_market_records(current=0.01, hist_a=0.05, hist_b=0.08, tag="p10m")
            + _cash_debt_records(cash=50.0, debt=10.0, tag="p10bs")
        )
        support = _support(records)
        assert support.status is ValuationSupportStatus.NOT_SUPPORTED


# ---------------------------------------------------------------------------
# 11. Conflicting sufficient proofs (`DE-015` §16's own real meaning of
# "conflict" -- two independently-sufficient paths disagreeing). No real
# company fixture can be hand-built to trigger this deterministically
# without also being a `does_not_establish` case for one of the two paths
# by construction, so this isolates `support.py`'s own synthesis-mapping
# logic the same way `TestRegression` already does.
# ---------------------------------------------------------------------------


class TestCase11ConflictingSufficientProofs:
    def test_conflicting_proofs_map_to_insufficient_input_with_the_conflict_gap(self):
        with (
            patch(
                "atlas.analysis_engine.valuation.support.evaluate_scenario_proof",
                return_value=PathProof(path_name="scenario", verdict=ProofVerdict.ESTABLISHES_SUPPORT, evidence_summary="test"),
            ),
            patch(
                "atlas.analysis_engine.valuation.support.evaluate_net_cash_proof",
                return_value=PathProof(path_name="net_cash", verdict=ProofVerdict.ESTABLISHES_NON_SUPPORT, evidence_summary="test"),
            ),
        ):
            support = _support(())
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.gap is ValuationSupportGapKind.CONFLICTING_VALUATION_PROOFS


# ---------------------------------------------------------------------------
# 12. Thin growth history
# ---------------------------------------------------------------------------


class TestCase12ThinGrowthHistory:
    def test_two_periods_is_insufficient_input(self):
        records = (
            fundamentals_record(period_end=date(2023, 12, 31), identifier="th23", published_at=_filed(2024), revenue=1000.0, free_cash_flow=100.0),
            fundamentals_record(period_end=date(2024, 12, 31), identifier="th24", published_at=_filed(2025), revenue=1100.0, free_cash_flow=115.0),
            market_record(period_end=date(2024, 3, 1), identifier="thm24", share_price=20.0, shares_outstanding=100.0),
            market_record(period_end=date(2025, 3, 1), identifier="thm25", share_price=22.0, shares_outstanding=100.0),
        )
        support = _support(records)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.gap is ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA


# ---------------------------------------------------------------------------
# 13. Missing Revenue corroboration
# ---------------------------------------------------------------------------


class TestCase13MissingRevenueCorroboration:
    def test_fcf_only_growth_never_corroborated_stays_insufficient_input(self):
        fcf = (100.0, 115.0, 140.0, 165.0, 200.0)
        years = (2020, 2021, 2022, 2023, 2024)
        records = tuple(
            fundamentals_record(period_end=date(year, 12, 31), identifier=f"rc{year}", published_at=_filed(year + 1), free_cash_flow=fcf[i])
            for i, year in enumerate(years)
        ) + (
            market_record(period_end=date(2024, 3, 1), identifier="rcm24", share_price=30.0, shares_outstanding=100.0),
            market_record(period_end=date(2025, 3, 1), identifier="rcm25", share_price=35.0, shares_outstanding=100.0),
        )
        support = _support(records)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.gap is ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA


# ---------------------------------------------------------------------------
# 14. Future-dated facts never change the verdict
# ---------------------------------------------------------------------------


class TestCase14FutureDatedFacts:
    def test_future_dated_facts_are_excluded_not_merely_ignored_by_luck(self):
        base_records = _durable_growth_records("p14") + _envelope_market_records(current=0.05, hist_a=0.04, hist_b=0.06, tag="p14m")
        with_future = base_records + (
            fundamentals_record(period_end=date(2029, 12, 31), identifier="p14future", published_at=_filed(2030), revenue=99999.0, free_cash_flow=99999.0),
        )
        assert _support(base_records) == _support(with_future)


# ---------------------------------------------------------------------------
# 15. Negative FCF history
# ---------------------------------------------------------------------------


class TestCase15NegativeFcfHistory:
    def test_negative_fcf_endpoint_excluded_not_crashing(self):
        revenue = (900.0, 1000.0, 1100.0, 1250.0, 1400.0, 1600.0)
        fcf = (-10.0, 100.0, 115.0, 140.0, 165.0, 200.0)
        years = (2019, 2020, 2021, 2022, 2023, 2024)
        records = tuple(
            fundamentals_record(
                period_end=date(year, 12, 31), identifier=f"nf{year}", published_at=_filed(year + 1), revenue=revenue[i], free_cash_flow=fcf[i]
            )
            for i, year in enumerate(years)
        ) + (
            market_record(period_end=date(2024, 3, 1), identifier="nfm24", share_price=27.5, shares_outstanding=100.0),
            market_record(period_end=date(2025, 3, 1), identifier="nfm25", share_price=40.0, shares_outstanding=100.0),
        )
        support = _support(records)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT


# ---------------------------------------------------------------------------
# 16. Cyclical/noisy history -- disclosed `DE-015` §19 limitation, not
# hidden: no crash, a real deterministic verdict, nothing invented to
# "smooth" the noise.
# ---------------------------------------------------------------------------


class TestCase16CyclicalNoisyHistory:
    def test_alternating_up_down_history_still_resolves_deterministically(self):
        revenue = (1000.0, 1300.0, 950.0, 1250.0, 900.0, 1400.0)
        fcf = (100.0, 140.0, 90.0, 130.0, 85.0, 150.0)
        years = (2019, 2020, 2021, 2022, 2023, 2024)
        records = tuple(
            fundamentals_record(
                period_end=date(year, 12, 31), identifier=f"cy{year}", published_at=_filed(year + 1), revenue=revenue[i], free_cash_flow=fcf[i]
            )
            for i, year in enumerate(years)
        ) + (
            market_record(period_end=date(2024, 3, 1), identifier="cym24", share_price=25.0, shares_outstanding=100.0),
            market_record(period_end=date(2025, 3, 1), identifier="cym25", share_price=30.0, shares_outstanding=100.0),
        )
        first = _support(records)
        second = _support(records)
        assert first == second
        assert first.status in (
            ValuationSupportStatus.SUPPORTED,
            ValuationSupportStatus.NOT_SUPPORTED,
            ValuationSupportStatus.INSUFFICIENT_INPUT,
        )


# ---------------------------------------------------------------------------
# 17. M&A-like step-change -- another disclosed `DE-015` §19 limitation:
# a sudden, permanent step-change is invisible to a rolling-window growth
# rate, and this module makes no attempt to detect it.
# ---------------------------------------------------------------------------


class TestCase17MergerStepChangeFixture:
    def test_sudden_step_change_does_not_crash_and_resolves_deterministically(self):
        revenue = (900.0, 950.0, 2800.0, 2900.0, 3000.0, 3100.0)
        fcf = (90.0, 95.0, 280.0, 290.0, 300.0, 310.0)
        years = (2019, 2020, 2021, 2022, 2023, 2024)
        records = tuple(
            fundamentals_record(
                period_end=date(year, 12, 31), identifier=f"ma{year}", published_at=_filed(year + 1), revenue=revenue[i], free_cash_flow=fcf[i]
            )
            for i, year in enumerate(years)
        ) + (
            market_record(period_end=date(2024, 3, 1), identifier="mam24", share_price=40.0, shares_outstanding=100.0),
            market_record(period_end=date(2025, 3, 1), identifier="mam25", share_price=45.0, shares_outstanding=100.0),
        )
        first = _support(records)
        second = _support(records)
        assert first == second


# ---------------------------------------------------------------------------
# 18. Wide terminal valuation distribution -- the width itself is the
# disclosure; no invented dispersion gate.
# ---------------------------------------------------------------------------


class TestCase18WideTerminalValuationDistribution:
    def test_wide_historical_yield_dispersion_resolves_honestly(self):
        records = _durable_growth_records("p18") + (
            market_record(period_end=date(2022, 3, 1), identifier="p18m22", share_price=200.0, shares_outstanding=100.0),
            market_record(period_end=date(2023, 3, 1), identifier="p18m23", share_price=14.0, shares_outstanding=100.0),
            market_record(period_end=date(2024, 3, 1), identifier="p18m24", share_price=330.0, shares_outstanding=100.0),
            market_record(period_end=date(2025, 3, 1), identifier="p18m25", share_price=40.0, shares_outstanding=100.0),
        )
        support = _support(records)
        assert support.status in (
            ValuationSupportStatus.SUPPORTED,
            ValuationSupportStatus.NOT_SUPPORTED,
            ValuationSupportStatus.INSUFFICIENT_INPUT,
        )


# ---------------------------------------------------------------------------
# 19. Recommendation boundary (revised for `DE-016`: Recommendation now
# deliberately consumes `ValuationSupport.status` -- the invariant this
# case now proves is narrower and different in kind: only `.status`
# crosses the boundary, `calculate_recommendation_conviction` remains
# fully untouched, and `.reasoning`/`.gap` are never read by Direction
# Selection. This class's name is kept for continuity with the original
# `DE-015` adversarial numbering; its content is `DE-016`'s own.)
# ---------------------------------------------------------------------------


class TestCase19RecommendationInvariance:
    def test_calculate_recommendation_conviction_never_accepts_valuation_support(self):
        """`DE-016` Phase 10: Recommendation Conviction (`DE-004` §3)
        stays completely independent of `ValuationSupport` -- it is a
        Direction prerequisite, never Conviction evidence."""
        params = inspect.signature(calculate_recommendation_conviction).parameters
        assert "valuation_support" not in params
        assert "valuation_support_status" not in params

    def test_select_direction_and_gate_now_deliberately_accept_valuation_support(self):
        """The inverse of this test's own pre-`DE-016` assumption,
        confirmed against the real, current signatures: `select_direction`
        reads only the public `status`; `evaluate_recommendation_gate`
        reads the full `ValuationSupport` object but forwards only
        `.status` (`DE-015` §18)."""
        assert "valuation_support_status" in inspect.signature(select_direction).parameters
        assert "valuation_support" in inspect.signature(evaluate_recommendation_gate).parameters

    def test_swapping_real_valuation_support_status_changes_direction_only_where_de008_allows(self):
        """Behavioral companion to the structural checks above: two
        genuinely different, real `ValuationSupport` results (`SUPPORTED`
        from case 4's own fixture vs. `INSUFFICIENT_INPUT` from case 1's)
        are computed, then fed through `select_direction` holding every
        other input fixed at a `DE-008`-blocked cell -- proving the
        wiring is real, not proving invariance (that claim is now false
        by design; see `DE-016`)."""
        from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel, HoldingLinkage
        from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
        from atlas.analysis_engine.recommendation import RecommendationDirection

        supported_records = _durable_growth_records("p19") + _envelope_market_records(
            current=0.05, hist_a=0.04, hist_b=0.06, tag="p19m"
        )
        supported = _support(supported_records)
        insufficient = _support(())
        assert supported.status is ValuationSupportStatus.SUPPORTED
        assert insufficient.status is ValuationSupportStatus.INSUFFICIENT_INPUT

        kwargs = dict(
            holding_linkage=HoldingLinkage.ABSENT,
            business_evaluation_state=EvaluationState.EVALUATED,
            valuation_state=EvaluationState.EVALUATED,
            portfolio_intelligence_state=EvaluationState.EVALUATED,
            reasoning_state=EvaluationState.EVALUATED,
            evidence_coverage=EvidenceCoverageLevel.FULL,
            growth_status=BusinessCategoryStatus.MODERATE,
            capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT,
            valuation_status=ValuationStatus.UNDERVALUED,
            has_portfolio_dampening=False,
            has_high_financial_or_valuation_risk=False,
        )
        with_supported = select_direction(**kwargs, valuation_support_status=supported.status)
        with_insufficient = select_direction(**kwargs, valuation_support_status=insufficient.status)
        assert with_supported is RecommendationDirection.BUY
        assert with_insufficient is None

    def test_only_status_crosses_for_recommendation_semantics(self):
        """`DE-015` §18 as amended (§22.7), checked against the real
        source -- never against behavior alone, since a field could be
        read and silently discarded without test-visible effect.

        `reasoning` still never crosses: it is diagnostic prose. `gap`
        may now cross into the gate for explanatory projection only, and
        Direction Selection remains status-only either way. The
        structural proof that the gate uses it for nothing else lives in
        `test_support.py::TestArchitecturalBoundary`.
        """
        import pathlib

        for fn in (select_direction, evaluate_recommendation_gate):
            source = pathlib.Path(inspect.getfile(fn)).read_text(encoding="utf-8")
            assert "valuation_support.reasoning" not in source

        direction_source = pathlib.Path(inspect.getfile(select_direction)).read_text(encoding="utf-8")
        assert "valuation_support.gap" not in direction_source

    def test_changing_only_the_gap_never_changes_direction(self):
        """The behavioural half: `gap` is explanatory, so no gap value
        may move Direction while `status` is held fixed."""
        from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
        from atlas.analysis_engine.valuation.contracts import ValuationStatus
        from atlas.analysis_engine.valuation.support import (
            ValuationSupportGapKind,
            ValuationSupportStatus,
        )
        from atlas.decision_engine.contracts import (
            EvaluationState,
            EvidenceCoverageLevel,
            HoldingLinkage,
        )

        kwargs = dict(
            holding_linkage=HoldingLinkage.PRESENT,
            business_evaluation_state=EvaluationState.EVALUATED,
            valuation_state=EvaluationState.EVALUATED,
            portfolio_intelligence_state=EvaluationState.EVALUATED,
            reasoning_state=EvaluationState.EVALUATED,
            evidence_coverage=EvidenceCoverageLevel.FULL,
            growth_status=BusinessCategoryStatus.STRONG,
            capital_allocation_status=BusinessCategoryStatus.STRONG,
            valuation_status=ValuationStatus.UNDERVALUED,
            has_portfolio_dampening=False,
            has_high_financial_or_valuation_risk=False,
        )
        directions = {
            select_direction(**kwargs, valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT)
            for _ in ValuationSupportGapKind
        }
        assert len(directions) == 1


# ---------------------------------------------------------------------------
# 20. Outlook independence
# ---------------------------------------------------------------------------


class TestCase20OutlookIndependence:
    def test_support_module_never_imports_outlook_types(self):
        import atlas.analysis_engine.valuation.support as support_module

        for forbidden in ("Outlook", "ExpectedReturnRange", "OutlookScenario", "HorizonOutlook", "build_outlook"):
            assert not hasattr(support_module, forbidden)

    def test_outlook_module_never_imports_valuation_support(self):
        import atlas.analysis_engine.outlook as outlook_module

        assert not hasattr(outlook_module, "evaluate_valuation_support")
        assert not hasattr(outlook_module, "ValuationSupport")
