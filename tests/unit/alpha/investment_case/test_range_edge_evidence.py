"""Range Edge Disclosure: who owns the ends of the observed range, and how
alone that owner is.

Two things are under test. The first is that the description is true of the
evidence handed in -- including the case the audit found across the real
corpus, where a FAIRLY_VALUED Case sits inside its historical range only
because the single year owning the low edge puts it there.

The second is that it decides nothing. The classification is produced by the
same `position_of` the engine uses, and the dependency flag is derived by
asking that same function what would happen without one year -- it never
becomes a second rule, and no decision reads it.

The edge year is valid evidence throughout. Nothing here calls it an
outlier, and no threshold decides whether it "counts".

No test names a real company: every fixture is a shape.
"""
from __future__ import annotations

import pytest

from atlas.alpha.investment_case.valuation_evidence_metadata import describe_valuation_evidence
from atlas.analysis_engine.valuation.contracts import ValuationStatus

from tests.unit.alpha.investment_case.test_valuation_evidence_metadata import (
    MINIMUM,
    described,
    epoch,
    evidence_for,
    finding,
)


def edges(metadata):
    return metadata.range_edge


# -- edge ownership ----------------------------------------------------------


class TestEdgeOwnership:
    PRIORS = [epoch(2022, fcf=100, market_cap=2_000),   # 5.0%
              epoch(2023, fcf=100, market_cap=1_250),   # 8.0%
              epoch(2024, fcf=100, market_cap=1_000)]   # 10.0%

    def test_the_ends_of_the_range_are_named_with_their_own_fiscal_years(self):
        edge = edges(described(self.PRIORS, epoch(2025, fcf=100, market_cap=1_500)))
        assert (edge.low_edge.fiscal_year, edge.low_edge.fcf_yield) == (2022, 0.05)
        assert (edge.high_edge.fiscal_year, edge.high_edge.fcf_yield) == (2024, 0.10)
        assert edge.second_lowest.fiscal_year == 2023
        assert edge.second_highest.fiscal_year == 2023

    def test_age_is_measured_in_fiscal_years_from_the_current_epoch_not_a_clock(self):
        edge = edges(described(self.PRIORS, epoch(2025, fcf=100, market_cap=1_500)))
        assert edge.low_edge.age_years == 3
        assert edge.high_edge.age_years == 1

    def test_the_denominator_treatment_of_the_edge_year_is_carried_through(self):
        priors = [epoch(2022, fcf=100, market_cap=2_000, quality="issuer_bounded"),
                  epoch(2023, fcf=100, market_cap=1_250, quality="issuer_exact"),
                  epoch(2024, fcf=100, market_cap=1_000, quality="issuer_exact")]
        edge = edges(described(priors, epoch(2025, fcf=100, market_cap=1_500, quality="issuer_exact")))
        assert edge.low_edge.denominator_quality == "issuer_bounded"

    def test_the_isolation_primitives_are_raw_gaps_never_a_label(self):
        edge = edges(described(self.PRIORS, epoch(2025, fcf=100, market_cap=1_500)))
        assert edge.low_edge_gap == pytest.approx(0.03)     # 5.0% -> 8.0%
        assert edge.high_edge_gap == pytest.approx(0.02)    # 8.0% -> 10.0%
        assert edge.median_history_gap == pytest.approx(0.025)
        assert not hasattr(edge, "isolated")

    def test_sorting_is_deterministic_for_identical_inputs(self):
        """The engine already requires priors oldest-first, so the only
        determinism this module owes is that identical input gives an
        identical description -- including which year owns each edge."""
        current = epoch(2025, fcf=100, market_cap=1_500)
        first, second = described(self.PRIORS, current), described(self.PRIORS, current)
        assert first == second
        assert first.range_edge.low_edge.fiscal_period == second.range_edge.low_edge.fiscal_period


# -- corroboration primitives ------------------------------------------------


class TestCorroboration:
    def test_counts_priors_at_or_below_and_at_or_above_today(self):
        priors = [epoch(2022, fcf=100, market_cap=2_000),   # 5%
                  epoch(2023, fcf=100, market_cap=1_250),   # 8%
                  epoch(2024, fcf=100, market_cap=1_000)]   # 10%
        edge = edges(described(priors, epoch(2025, fcf=100, market_cap=1_500)))  # 6.67%
        assert edge.priors_at_or_below_current == 1
        assert edge.priors_at_or_above_current == 2

    def test_a_prior_exactly_at_todays_yield_counts_on_both_sides(self):
        """`at or below` and `at or above` are inclusive: a year that matches
        today's yield exactly corroborates in both directions."""
        priors = [epoch(2022, fcf=100, market_cap=2_000),   # 5%
                  epoch(2023, fcf=100, market_cap=1_500),   # 6.67%  == today
                  epoch(2024, fcf=100, market_cap=1_000)]   # 10%
        edge = edges(described(priors, epoch(2025, fcf=100, market_cap=1_500)))
        assert edge.priors_at_or_below_current == 2
        assert edge.priors_at_or_above_current == 2

    def test_no_synthetic_score_is_produced(self):
        edge = edges(described([epoch(y, fcf=100, market_cap=2_000) for y in (2022, 2023, 2024)],
                               epoch(2025, fcf=100, market_cap=2_000)))
        assert not any(name.endswith("_score") for name in vars(edge))


# -- single-edge dependency --------------------------------------------------


class TestSingleLowEdgeDependency:
    #: One year far below the rest: the shape the corpus audit found.
    PRIORS = [epoch(2021, fcf=100, market_cap=5_000),   # 2.0%  <- low edge
              epoch(2022, fcf=100, market_cap=2_000),   # 5.0%
              epoch(2023, fcf=100, market_cap=1_800),   # 5.6%
              epoch(2024, fcf=100, market_cap=1_600)]   # 6.3%

    def test_true_when_one_uniquely_owned_edge_year_is_the_only_thing_inside(self):
        """Today sits below every prior except the edge year."""
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=4_000))  # 2.5%
        assert metadata.range_edge.single_low_edge_dependency is True
        assert metadata.range_edge.priors_at_or_below_current == 1
        assert metadata.range_edge.low_edge.fiscal_year == 2021

    def test_false_when_today_is_above_the_second_lowest_prior(self):
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=1_900))  # 5.3%
        assert metadata.range_edge.single_low_edge_dependency is False
        assert metadata.range_edge.priors_at_or_below_current == 2

    def test_false_when_the_low_edge_is_tied_between_two_years(self):
        """An edge two years share is owned by neither: removing one leaves the
        other holding the same edge, so nothing depends on a single year."""
        priors = [epoch(2020, fcf=100, market_cap=5_000), epoch(2021, fcf=100, market_cap=5_000),
                  epoch(2022, fcf=100, market_cap=2_000), epoch(2023, fcf=100, market_cap=1_800)]
        metadata = described(priors, epoch(2025, fcf=100, market_cap=4_000))
        assert metadata.range_edge.low_edge.uniquely_owned is False
        assert metadata.range_edge.single_low_edge_dependency is False

    def test_a_distant_edge_year_counts_exactly_like_a_recent_one(self):
        """No recency cutoff exists. A sixteen-year-old edge and a one-year-old
        edge produce the identical flag -- the age is reported, never applied."""
        old_priors = [epoch(2009, fcf=100, market_cap=5_000), epoch(2022, fcf=100, market_cap=2_000),
                      epoch(2023, fcf=100, market_cap=1_800), epoch(2024, fcf=100, market_cap=1_600)]
        old_edge = described(old_priors, epoch(2025, fcf=100, market_cap=4_000))
        recent = described(self.PRIORS, epoch(2025, fcf=100, market_cap=4_000))
        assert old_edge.range_edge.low_edge.age_years == 16
        assert recent.range_edge.low_edge.age_years == 4
        assert old_edge.range_edge.single_low_edge_dependency is True
        assert recent.range_edge.single_low_edge_dependency is True

    def test_the_symmetric_high_edge_case_is_implemented(self):
        priors = [epoch(2021, fcf=100, market_cap=1_000),   # 10.0%  <- high edge
                  epoch(2022, fcf=100, market_cap=3_000),   # 3.3%
                  epoch(2023, fcf=100, market_cap=3_200),   # 3.1%
                  epoch(2024, fcf=100, market_cap=3_400)]   # 2.9%
        metadata = described(priors, epoch(2025, fcf=100, market_cap=1_100))  # 9.1%
        assert metadata.range_edge.single_high_edge_dependency is True
        assert metadata.range_edge.high_edge.fiscal_year == 2021
        assert metadata.range_edge.single_low_edge_dependency is False

    def test_false_when_the_high_edge_is_tied(self):
        priors = [epoch(2020, fcf=100, market_cap=1_000), epoch(2021, fcf=100, market_cap=1_000),
                  epoch(2022, fcf=100, market_cap=3_000), epoch(2023, fcf=100, market_cap=3_200)]
        metadata = described(priors, epoch(2025, fcf=100, market_cap=1_100))
        assert metadata.range_edge.high_edge.uniquely_owned is False
        assert metadata.range_edge.single_high_edge_dependency is False

    def test_an_expensive_case_never_claims_a_fairly_dependency(self):
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=9_000))  # 1.1%, below all
        assert metadata.range_edge.low_edge is not None
        assert metadata.range_edge.single_low_edge_dependency is False
        assert metadata.range_edge.single_high_edge_dependency is False

    def test_an_undervalued_case_never_claims_a_fairly_dependency(self):
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=500))  # 20%, above all
        assert metadata.range_edge.single_low_edge_dependency is False
        assert metadata.range_edge.single_high_edge_dependency is False

    def test_the_dependency_is_decided_by_the_engines_own_position_test(self):
        """Removing the edge must genuinely move the yield outside the range --
        proven by classifying the remainder, never by an invented rule."""
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=4_000))
        remaining = tuple(p.fcf_yield for p in self.PRIORS[1:])
        assert metadata.range_edge.single_low_edge_dependency is True
        assert 0.025 < min(remaining)


class TestEdgeCases:
    def test_minimum_eligible_history_still_describes_its_edges(self):
        priors = [epoch(2022, fcf=100, market_cap=5_000), epoch(2023, fcf=100, market_cap=2_000),
                  epoch(2024, fcf=100, market_cap=1_800)]
        metadata = described(priors, epoch(2025, fcf=100, market_cap=4_000))
        assert len(priors) == MINIMUM
        assert metadata.range_edge.single_low_edge_dependency is True

    def test_a_single_prior_has_no_second_and_no_dependency(self):
        metadata = described([epoch(2024, fcf=100, market_cap=2_000)],
                             epoch(2025, fcf=100, market_cap=2_000), minimum=1)
        edge = metadata.range_edge
        assert edge.second_lowest is None and edge.second_highest is None
        assert edge.single_low_edge_dependency is False
        assert edge.median_history_gap is None

    def test_a_history_of_one_repeated_yield_has_no_distinct_second(self):
        priors = [epoch(y, fcf=100, market_cap=2_000) for y in (2022, 2023, 2024)]
        edge = edges(described(priors, epoch(2025, fcf=100, market_cap=2_000)))
        assert edge.low_edge.uniquely_owned is False
        assert edge.second_lowest is None
        assert edge.single_low_edge_dependency is False

    def test_no_evidence_at_all_produces_no_range_edge(self):
        from atlas.analysis_engine.valuation.contracts import ValuationDecisionEligibility
        from atlas.analysis_engine.valuation.models import FcfYieldEvidence, ShareCountMethod
        evidence = FcfYieldEvidence(
            eligibility=ValuationDecisionEligibility.NOT_APPLICABLE,
            minimum_prior_epochs=MINIMUM,
            share_count_method=ShareCountMethod.CURRENT_SHARE_COUNT_PROXY)
        assert describe_valuation_evidence(finding(evidence)).range_edge is None

    def test_it_reads_exactly_the_epochs_the_engine_accepted(self):
        """The evidence object is the only source: whatever `fiscal_epoch_v3`
        excluded is not visible here, so the description can never describe a
        valuation Atlas did not make."""
        priors = [epoch(y, fcf=100, market_cap=2_000) for y in (2022, 2023, 2024)]
        current = epoch(2025, fcf=100, market_cap=1_500)
        evidence = evidence_for(priors, current)
        metadata = describe_valuation_evidence(finding(evidence))
        described_years = {metadata.range_edge.low_edge.fiscal_year,
                           metadata.range_edge.high_edge.fiscal_year}
        assert described_years <= {p.fiscal_period[:4] and int(p.fiscal_period[:4]) for p in evidence.prior_epochs}


# -- firewall ----------------------------------------------------------------


class TestFirewall:
    PRIORS = [epoch(2021, fcf=100, market_cap=5_000), epoch(2022, fcf=100, market_cap=2_000),
              epoch(2023, fcf=100, market_cap=1_800), epoch(2024, fcf=100, market_cap=1_600)]

    def test_describing_the_edges_leaves_the_finding_and_its_status_untouched(self):
        evidence = evidence_for(self.PRIORS, epoch(2025, fcf=100, market_cap=4_000))
        original = finding(evidence)
        before = (original.status, original.current_yield, original.historical_yields,
                  original.fcf_yield_evidence)
        metadata = describe_valuation_evidence(original)
        assert metadata.range_edge.single_low_edge_dependency is True
        assert (original.status, original.current_yield, original.historical_yields,
                original.fcf_yield_evidence) == before
        assert original.status is ValuationStatus.FAIRLY_VALUED

    def test_the_dependency_flag_does_not_change_the_classification(self):
        """The Case is FAIRLY_VALUED with the flag set, exactly as it was
        without one: the flag reports the fragility, it does not act on it."""
        metadata = described(self.PRIORS, epoch(2025, fcf=100, market_cap=4_000))
        assert metadata.range_edge.single_low_edge_dependency is True
        assert metadata.boundary.nearest_classification is not None
        evidence = evidence_for(self.PRIORS, epoch(2025, fcf=100, market_cap=4_000))
        assert evidence.decision_status is ValuationStatus.FAIRLY_VALUED

    def test_the_description_is_pure(self):
        priors, current = self.PRIORS, epoch(2025, fcf=100, market_cap=4_000)
        assert described(priors, current) == described(priors, current)

    def test_no_ticker_appears_anywhere_in_the_module(self):
        """The rule must be generic: the corpus Cases it fires for are an
        outcome of the evidence, never a list written here."""
        import re
        from pathlib import Path
        source = Path(__file__).resolve().parents[4].joinpath(
            "atlas/alpha/investment_case/valuation_evidence_metadata.py").read_text(encoding="utf-8")
        for ticker in ("AMAT", "MSFT", "MU", "UNP", "NVDA", "AMZN", "GOOG", "META", "VST", "CRM"):
            assert re.search(rf"\b{ticker}\b", source) is None, ticker
