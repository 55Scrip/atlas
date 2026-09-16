"""Valuation Evidence Metadata: it describes the evidence, and decides nothing.

Two obligations are under test. The first is that every figure and every
category is a true statement about the evidence handed in -- depth and
span kept apart, a boundary distance that is mathematically the same
quantity in all three classifications, a cash-flow comparison that reports
an unusual year without normalising it away, and capital intensity only
where the statements carry capital expenditure at all.

The second is the firewall: nothing the metadata says may change what
Atlas concludes. The tests at the bottom hold the valuation status,
`ValuationRisk`, the recommendation direction, conviction and Valuation
Support constant across metadata that says wildly different things, and
prove structurally -- by reading the import graph -- that no module in
`atlas.analysis_engine` or `atlas.decision_engine` can read it at all.

No test here names a real company: every fixture is a shape.
"""
from __future__ import annotations

import ast
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from atlas.alpha.investment_case.financial_statement_intelligence import (
    CashFlowStatementPeriod,
    FinancialStatementHistory,
    IncomeStatementPeriod,
    SegmentInformation,
)
from atlas.alpha.investment_case.valuation_evidence_metadata import (
    RangePosition,
    describe_valuation_evidence,
)
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.valuation.contracts import (
    ValuationDataGapKind,
    ValuationDecisionEligibility,
    ValuationMethodKind,
    ValuationStatus,
)
from atlas.analysis_engine.valuation.models import (
    FcfYieldEpochObservation,
    FcfYieldEvidence,
    ShareCountMethod,
    ValuationFinding,
    position_of,
)
from atlas.decision_engine.contracts import EvidenceCoverageLevel

MINIMUM = 3
AS_OF = datetime(2026, 1, 1, tzinfo=timezone.utc)
PROVENANCE = Provenance(
    source_kind=SourceKind.ANALYSIS_ENGINE_STAGE, source_references=(), dependencies=(),
    update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED, consumers=(), computed_at=AS_OF,
)


def epoch(year: int, *, fcf: float, market_cap: float, quality: str | None = None) -> FcfYieldEpochObservation:
    """One fiscal year priced by one observation, at the yield asked for.

    Built on the provider-proxy shape because the arithmetic under test is
    the same either way: `fcf_yield` is free cash flow over market
    capitalisation, and these tests care about the yields, not about how
    the denominator was proven. `quality` carries the denominator
    treatment the issuer basis would have recorded.
    """
    period = f"{year}-12-31"
    return FcfYieldEpochObservation(
        fiscal_period=period,
        available_from=date(year + 1, 2, 1),
        observed_on=f"{year + 1}-03-01",
        free_cash_flow=fcf,
        share_price=market_cap / 1_000.0,
        shares_outstanding=1_000.0,
        currency="USD",
        free_cash_flow_fact_id=f"fcf:{period}",
        share_price_fact_id=f"price:{period}",
        shares_outstanding_fact_id=f"shares:{period}",
        denominator_quality=quality,
    )


def finding(evidence: FcfYieldEvidence) -> ValuationFinding:
    """The real finding for this evidence. Its own invariants decide the
    status and the historical yields -- the test may not choose them, which
    is precisely why the classification assertions below mean something."""
    not_applicable = evidence.eligibility is ValuationDecisionEligibility.NOT_APPLICABLE
    return ValuationFinding(
        id="finding:fcf",
        kind=ValuationMethodKind.FCF_YIELD_RELATIVE,
        status=evidence.decision_status,
        severity=FindingSeverity.INFO,
        supporting_facts=(),
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=(ValuationDataGapKind.VALUATION_METHOD_NOT_APPLICABLE,) if not_applicable else (),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=PROVENANCE,
        evaluated_at=AS_OF,
        current_yield=evidence.current.fcf_yield if evidence.current else None,
        historical_yields=(tuple(sorted(evidence.prior_yields))
                           if evidence.eligibility is ValuationDecisionEligibility.ELIGIBLE else ()),
        fcf_yield_evidence=evidence,
    )


def evidence_for(priors, current, *, minimum: int = MINIMUM) -> FcfYieldEvidence:
    return FcfYieldEvidence(
        eligibility=ValuationDecisionEligibility.ELIGIBLE,
        minimum_prior_epochs=minimum,
        share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY,
        current=current,
        prior_epochs=tuple(priors),
        position=position_of(current.fcf_yield, tuple(p.fcf_yield for p in priors)) if priors and current else None,
    )


def described(priors, current, *, statements=None, minimum: int = MINIMUM):
    """The metadata for one comparison, on the engine's own classification."""
    return describe_valuation_evidence(finding(evidence_for(priors, current, minimum=minimum)), statements)


def statements(rows: dict[int, tuple[float | None, float | None, float | None]]) -> FinancialStatementHistory:
    """`{year: (revenue, capital_expenditure, operating_cash_flow)}`. A
    `None` revenue or capex is a statement that does not carry the figure."""
    income = tuple(
        IncomeStatementPeriod(
            period_end=date(year, 12, 31), revenue=revenue, gross_profit=None, operating_income=None,
            ebitda=None, net_income=None, eps=None, gross_margin=None, operating_margin=None,
            net_margin=None, currency="USD", accounting_basis=None, source_reference=None,
        )
        for year, (revenue, _, _) in sorted(rows.items())
    )
    cash = tuple(
        CashFlowStatementPeriod(
            period_end=date(year, 12, 31), operating_cash_flow=ocf, investing_cash_flow=None,
            financing_cash_flow=None, free_cash_flow=None, capital_expenditure=capex, currency="USD",
            accounting_basis=None, source_reference=None,
        )
        for year, (_, capex, ocf) in sorted(rows.items())
    )
    return FinancialStatementHistory(income, (), cash, SegmentInformation())


# -- history: depth and span are different facts, and both survive -------------------------------------------


class TestHistory:
    def test_depth_and_span_are_reported_separately(self):
        """A short, dense history and a long, sparse one must not be told
        apart only by a count: three consecutive years and seven years
        scattered over sixteen are both real, and differently trustworthy.
        Depth, span and the years actually missing are three separate
        fields, and none of them collapses into another."""
        dense = described([epoch(y, fcf=100, market_cap=2_000) for y in (2022, 2023, 2024)],
                          epoch(2025, fcf=100, market_cap=2_000))
        sparse_years = (2009, 2012, 2015, 2018, 2021, 2023, 2024)
        sparse = described([epoch(y, fcf=100, market_cap=2_000) for y in sparse_years],
                           epoch(2025, fcf=100, market_cap=2_000))
        # `span_years` runs from the earliest prior epoch to the current one.
        assert (dense.history.valid_prior_count, dense.history.span_years) == (3, 3.0)
        assert sparse.history.valid_prior_count == 7
        assert sparse.history.span_years == pytest.approx(16.0, abs=0.05)
        assert sparse.history.missing_fiscal_years == (2010, 2011, 2013, 2014, 2016, 2017, 2019, 2020, 2022)
        assert dense.history.missing_fiscal_years == ()

    def test_minimum_depth_reuses_the_methods_own_minimum_and_invents_no_threshold(self):
        at_minimum = described([epoch(y, fcf=100, market_cap=2_000) for y in (2022, 2023, 2024)],
                               epoch(2025, fcf=100, market_cap=2_000))
        deeper = described([epoch(y, fcf=100, market_cap=2_000) for y in (2021, 2022, 2023, 2024)],
                           epoch(2025, fcf=100, market_cap=2_000))
        assert at_minimum.history.minimum_prior_count == MINIMUM
        assert at_minimum.history.at_minimum_depth is True
        assert deeper.history.at_minimum_depth is False

    def test_a_different_minimum_moves_the_label_with_it(self):
        """Proof the label follows the method, not a constant written here."""
        four = described([epoch(y, fcf=100, market_cap=2_000) for y in (2021, 2022, 2023, 2024)],
                         epoch(2025, fcf=100, market_cap=2_000), minimum=4)
        assert (four.history.minimum_prior_count, four.history.at_minimum_depth) == (4, True)

    def test_dispersion_and_the_typical_move_describe_the_prior_yields(self):
        metadata = described(
            [epoch(2022, fcf=100, market_cap=1_000), epoch(2023, fcf=100, market_cap=2_000),
             epoch(2024, fcf=100, market_cap=4_000)],
            epoch(2025, fcf=100, market_cap=4_000))
        assert metadata.history.yield_minimum == pytest.approx(0.025)
        assert metadata.history.yield_median == pytest.approx(0.05)
        assert metadata.history.yield_maximum == pytest.approx(0.10)
        assert metadata.history.yield_dispersion > 0
        # Each year halves the yield: a 50% move, twice.
        assert metadata.history.typical_year_over_year_move == pytest.approx(0.5)

    def test_no_evidence_is_described_as_nothing_rather_than_as_zero(self):
        evidence = FcfYieldEvidence(
            eligibility=ValuationDecisionEligibility.NOT_APPLICABLE,
            minimum_prior_epochs=MINIMUM,
            share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY,
        )
        metadata = describe_valuation_evidence(finding(evidence))
        assert metadata is not None
        assert metadata.history.valid_prior_count == 0
        assert metadata.history.at_minimum_depth is False
        assert metadata.boundary.distance is None


# -- boundary: one quantity, consistent across all three classifications -------------------------------------


class TestBoundary:
    PRIORS = [epoch(2022, fcf=100, market_cap=2_000),   # 5.0%
              epoch(2023, fcf=100, market_cap=1_250),   # 8.0%
              epoch(2024, fcf=100, market_cap=1_000)]   # 10.0%

    def test_expensive_measures_the_gap_up_to_the_lowest_prior_year(self):
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=4_000))  # 2.5%
        assert metadata.boundary.nearest_classification == ValuationStatus.FAIRLY_VALUED.value
        assert metadata.boundary.boundary_yield == pytest.approx(0.05)
        assert metadata.boundary.distance == pytest.approx(0.025)
        assert metadata.boundary.distance_percent == pytest.approx(0.5)

    def test_undervalued_measures_the_gap_down_to_the_highest_prior_year(self):
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=800))  # 12.5%
        assert metadata.boundary.nearest_classification == ValuationStatus.FAIRLY_VALUED.value
        assert metadata.boundary.boundary_yield == pytest.approx(0.10)
        assert metadata.boundary.distance == pytest.approx(0.025)
        assert metadata.boundary.distance_percent == pytest.approx(0.25)

    def test_fairly_valued_reports_whichever_end_is_nearer(self):
        near_low = described(self.PRIORS, epoch(2025, fcf=100, market_cap=1_800))  # 5.6%
        near_high = described(self.PRIORS, epoch(2025, fcf=100, market_cap=1_050))  # 9.5%
        assert near_low.boundary.nearest_classification == ValuationStatus.EXPENSIVE.value
        assert near_low.boundary.boundary_yield == pytest.approx(0.05)
        assert near_high.boundary.nearest_classification == ValuationStatus.UNDERVALUED.value
        assert near_high.boundary.boundary_yield == pytest.approx(0.10)

    def test_the_distance_is_the_same_quantity_in_every_classification(self):
        """`|current - boundary|`, and its share of the boundary, computed
        identically whichever side of the range today's yield falls on."""
        for current_cap, expected_boundary in ((4_000, 0.05), (800, 0.10), (1_800, 0.05), (1_050, 0.10)):
            metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=current_cap))
            current = metadata.boundary.current_yield
            assert metadata.boundary.boundary_yield == pytest.approx(expected_boundary)
            assert metadata.boundary.distance == pytest.approx(abs(current - expected_boundary))
            assert metadata.boundary.distance_percent == pytest.approx(
                abs(current - expected_boundary) / expected_boundary)

    def test_nearness_is_judged_against_this_historys_own_typical_move(self):
        """Never against a number chosen here: the same distance is 'close'
        beside a placid history and ordinary beside a volatile one."""
        placid = [epoch(2022, fcf=100, market_cap=2_000), epoch(2023, fcf=100, market_cap=2_020),
                  epoch(2024, fcf=100, market_cap=2_040)]
        volatile = [epoch(2022, fcf=100, market_cap=2_000), epoch(2023, fcf=100, market_cap=1_000),
                    epoch(2024, fcf=100, market_cap=4_000)]
        current = epoch(2025, fcf=100, market_cap=2_400)  # ~17% below the placid range
        assert described(placid, current).boundary.closer_than_typical_move is False
        assert described(volatile, current).boundary.closer_than_typical_move is True


# -- today's cash flow: described, never normalised ----------------------------------------------------------


class TestCurrentCashFlow:
    PRIORS = [epoch(2022, fcf=100, market_cap=2_000), epoch(2023, fcf=110, market_cap=2_000),
              epoch(2024, fcf=120, market_cap=2_000)]

    def test_an_ordinary_year_sits_inside_its_own_recent_range(self):
        metadata = described(self.PRIORS, epoch(2025, fcf=115, market_cap=2_000))
        assert metadata.current_cash_flow.position_versus_recent is RangePosition.WITHIN
        assert metadata.current_cash_flow.recent_range == (100, 120)
        assert metadata.current_cash_flow.recent_years_compared == MINIMUM

    def test_a_year_below_every_recent_one_is_reported_as_such(self):
        """The generic shape behind a heavy-investment year: a real,
        unusually low current free cash flow, named -- not replaced."""
        metadata = described(self.PRIORS, epoch(2025, fcf=20, market_cap=2_000))
        assert metadata.current_cash_flow.position_versus_recent is RangePosition.BELOW
        assert metadata.current_cash_flow.versus_prior_year == pytest.approx(20 / 120)
        assert metadata.current_cash_flow.versus_recent_median == pytest.approx(20 / 110)

    def test_a_year_above_every_recent_one_is_reported_the_same_way(self):
        metadata = described(self.PRIORS, epoch(2025, fcf=400, market_cap=2_000))
        assert metadata.current_cash_flow.position_versus_recent is RangePosition.ABOVE

    def test_the_valuation_still_uses_the_reported_cash_flow_unchanged(self):
        """No normalisation: the current free cash flow the metadata
        describes is exactly the one the finding was classified on."""
        current = epoch(2025, fcf=20, market_cap=2_000)
        metadata = described(self.PRIORS, current)
        assert metadata.current_cash_flow.current_free_cash_flow == current.free_cash_flow == 20
        assert metadata.boundary.current_yield == pytest.approx(current.fcf_yield)

    def test_the_recent_window_is_the_methods_own_minimum(self):
        priors = [epoch(y, fcf=100 + y - 2020, market_cap=2_000) for y in range(2018, 2025)]
        assert described(priors, epoch(2025, fcf=100, market_cap=2_000)).current_cash_flow.recent_years_compared == 3
        wider = described(priors, epoch(2025, fcf=100, market_cap=2_000), minimum=5)
        assert wider.current_cash_flow.recent_years_compared == 5


# -- capital intensity: only where the statements carry it ---------------------------------------------------


class TestCapitalIntensity:
    PRIORS = [epoch(2022, fcf=100, market_cap=2_000), epoch(2023, fcf=100, market_cap=2_000),
              epoch(2024, fcf=100, market_cap=2_000)]

    def test_intensity_is_capital_expenditure_over_revenue_in_each_year(self):
        metadata = described(
            self.PRIORS, epoch(2025, fcf=100, market_cap=2_000),
            statements=statements({2022: (1_000, 100, 300), 2023: (1_000, 120, 300),
                                   2024: (1_000, 140, 300), 2025: (1_000, 300, 330)}))
        capital = metadata.capital_intensity
        assert capital.current_intensity == pytest.approx(0.30)
        assert (capital.prior_intensity_minimum, capital.prior_intensity_maximum) == (
            pytest.approx(0.10), pytest.approx(0.14))
        assert capital.prior_intensity_median == pytest.approx(0.12)
        assert capital.prior_years_compared == 3
        assert capital.position_versus_prior_range is RangePosition.ABOVE
        assert capital.versus_prior_median == pytest.approx(2.5)
        assert capital.capital_expenditure_versus_prior_year == pytest.approx(300 / 140)
        assert capital.operating_cash_flow_versus_prior_year == pytest.approx(330 / 300)

    def test_an_ordinary_capital_year_is_not_flagged_above_the_range(self):
        metadata = described(
            self.PRIORS, epoch(2025, fcf=100, market_cap=2_000),
            statements=statements({2022: (1_000, 100, 300), 2023: (1_000, 120, 300),
                                   2024: (1_000, 140, 300), 2025: (1_000, 130, 300)}))
        assert metadata.capital_intensity.position_versus_prior_range is RangePosition.WITHIN

    def test_missing_capital_expenditure_fabricates_nothing(self):
        metadata = described(
            self.PRIORS, epoch(2025, fcf=100, market_cap=2_000),
            statements=statements({2022: (1_000, None, None), 2023: (1_000, None, None),
                                   2024: (1_000, None, None), 2025: (1_000, None, None)}))
        capital = metadata.capital_intensity
        assert capital.current_intensity is None
        assert capital.prior_intensity_median is None
        assert capital.prior_years_compared == 0
        assert capital.position_versus_prior_range is None

    def test_no_statements_at_all_leaves_every_capital_field_empty(self):
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=2_000))
        assert metadata.capital_intensity.current_intensity is None
        assert metadata.capital_intensity.position_versus_prior_range is None

    def test_missing_revenue_yields_no_intensity_for_that_year_only(self):
        metadata = described(
            self.PRIORS, epoch(2025, fcf=100, market_cap=2_000),
            statements=statements({2022: (None, 100, 300), 2023: (1_000, 120, 300),
                                   2024: (1_000, 140, 300), 2025: (1_000, 130, 300)}))
        assert metadata.capital_intensity.prior_years_compared == 2


# -- the denominator each epoch was priced on ----------------------------------------------------------------


class TestDenominator:
    PRIORS_EXACT = [epoch(y, fcf=100, market_cap=2_000, quality="issuer_exact") for y in (2022, 2023, 2024)]

    def test_an_all_exact_history_says_so(self):
        metadata = described(self.PRIORS_EXACT, epoch(2025, fcf=100, market_cap=2_000, quality="issuer_exact"))
        assert metadata.denominator.all_exact is True
        assert metadata.denominator.current_treatment == "issuer_exact"
        assert metadata.denominator.prior_treatments == ("issuer_exact",)

    def test_one_equivalent_prior_makes_the_history_not_exact(self):
        priors = [*self.PRIORS_EXACT[:2], epoch(2024, fcf=100, market_cap=2_000, quality="issuer_equivalent")]
        metadata = described(priors, epoch(2025, fcf=100, market_cap=2_000, quality="issuer_exact"))
        assert metadata.denominator.all_exact is False
        assert metadata.denominator.prior_treatments == ("issuer_equivalent", "issuer_exact")

    def test_a_bounded_epoch_is_reported_by_name(self):
        priors = [*self.PRIORS_EXACT[:2], epoch(2024, fcf=100, market_cap=2_000, quality="issuer_bounded")]
        metadata = described(priors, epoch(2025, fcf=100, market_cap=2_000, quality="issuer_exact"))
        assert "issuer_bounded" in metadata.denominator.prior_treatments
        assert metadata.denominator.all_exact is False

    def test_an_unrecorded_treatment_is_absence_not_exactness(self):
        metadata = described([epoch(y, fcf=100, market_cap=2_000) for y in (2022, 2023, 2024)],
                             epoch(2025, fcf=100, market_cap=2_000))
        assert metadata.denominator.all_exact is False
        assert metadata.denominator.current_treatment is None
        assert metadata.denominator.prior_treatments == ()


# -- the firewall --------------------------------------------------------------------------------------------


ENGINE_ROOTS = ("atlas/analysis_engine", "atlas/decision_engine")
MODULE = "atlas.alpha.investment_case.valuation_evidence_metadata"
REPOSITORY = Path(__file__).resolve().parents[4]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


class TestFirewall:
    def test_no_decision_module_can_import_the_metadata(self):
        """Structural, not behavioural: if no engine module imports it, no
        engine module can read it, whatever a future edit does inside one."""
        offenders = [
            str(path.relative_to(REPOSITORY))
            for root in ENGINE_ROOTS
            for path in (REPOSITORY / root).rglob("*.py")
            if any(name == MODULE or name.startswith(MODULE + ".") for name in imported_modules(path))
        ]
        assert offenders == []

    def test_no_engine_module_even_mentions_the_module_by_name(self):
        mentions = [
            str(path.relative_to(REPOSITORY))
            for root in ENGINE_ROOTS
            for path in (REPOSITORY / root).rglob("*.py")
            if "valuation_evidence_metadata" in path.read_text(encoding="utf-8")
        ]
        assert mentions == []

    def test_the_metadata_itself_imports_nothing_from_the_decision_engine(self):
        """It reads the engine's *models*, and nothing that decides."""
        names = imported_modules(REPOSITORY / (MODULE.replace(".", "/") + ".py"))
        assert not any(name.startswith("atlas.decision_engine") for name in names)
        assert all(name.startswith(("atlas.analysis_engine.valuation.contracts",
                                    "atlas.analysis_engine.valuation.models"))
                   for name in names if name.startswith("atlas.analysis_engine"))

    def test_describing_the_evidence_leaves_the_finding_untouched(self):
        """It is a projection: the finding it read is not mutated, and the
        status, current yield and evidence it carried are unchanged."""
        priors = [epoch(y, fcf=100, market_cap=2_000) for y in (2022, 2023, 2024)]
        evidence = evidence_for(priors, epoch(2025, fcf=20, market_cap=2_000))
        original = finding(evidence)
        assert original.status is ValuationStatus.EXPENSIVE
        before = (original.status, original.current_yield, original.fcf_yield_evidence)
        describe_valuation_evidence(original, statements({2025: (1_000, 900, 200)}))
        assert (original.status, original.current_yield, original.fcf_yield_evidence) == before

    def test_the_description_is_pure(self):
        """Same evidence in, deeply equal description out -- no clock, no
        randomness, nothing read from outside the arguments."""
        priors = [epoch(y, fcf=100, market_cap=2_000) for y in (2022, 2023, 2024)]
        current = epoch(2025, fcf=20, market_cap=2_000)
        rows = statements({2024: (1_000, 140, 300), 2025: (1_000, 900, 200)})
        assert described(priors, current, statements=rows) == described(priors, current, statements=rows)

    @pytest.mark.parametrize(
        "current, expected",
        [(epoch(2025, fcf=100, market_cap=4_000), ValuationStatus.EXPENSIVE),
         (epoch(2025, fcf=100, market_cap=1_500), ValuationStatus.FAIRLY_VALUED),
         (epoch(2025, fcf=100, market_cap=500), ValuationStatus.UNDERVALUED)],
    )
    def test_the_classification_is_the_strict_min_max_test_the_metadata_never_touches(self, current, expected):
        """The metadata may say the history is thin, the cash flow abnormal
        and the denominator inexact; the class is still decided by position
        alone."""
        priors = [epoch(2022, fcf=100, market_cap=2_000), epoch(2023, fcf=100, market_cap=1_250),
                  epoch(2024, fcf=100, market_cap=1_000)]
        alarming = described(priors, current, statements=statements(
            {2022: (1_000, 100, 300), 2023: (1_000, 120, 300), 2024: (1_000, 140, 300), 2025: (1_000, 900, 200)}))
        assert alarming.history.at_minimum_depth is True
        assert alarming.capital_intensity.position_versus_prior_range is RangePosition.ABOVE
        assert alarming.denominator.all_exact is False
        position = position_of(current.fcf_yield, tuple(p.fcf_yield for p in priors))
        classified = {"below_all_prior": ValuationStatus.EXPENSIVE,
                      "within_prior_range": ValuationStatus.FAIRLY_VALUED,
                      "above_all_prior": ValuationStatus.UNDERVALUED}[position.value]
        assert classified is expected
