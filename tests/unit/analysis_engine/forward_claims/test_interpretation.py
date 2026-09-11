"""Forward-Looking Evidence, Stage 4.1 -- economic interpretation.

The question every test asks: does Atlas say what a guidance revision
means for the business, taken at face value, without turning a
direction into a verdict? RAISED is not good news, REAFFIRMED is not
reassurance, and more capital spending is neither.
"""
from __future__ import annotations

import ast
import dataclasses
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.forward_claims import (
    ClaimBound,
    ClaimSubject,
    EconomicDimension,
    ExpectedMovement,
    GuidanceEconomicInterpretation,
    HorizonKind,
    OutlookEffect,
    RevisionBasis,
    RevisionType,
    detect_revisions,
    extract_forward_claims,
    interpret_revision,
    interpret_revisions,
)
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document
from tests.unit.analysis_engine.forward_claims.test_revisions import claim

B = 1e9


def interpreted(old, new):
    claims = (old, new)
    revisions, _ = detect_revisions(claims)
    return interpret_revisions(revisions, claims)


def one(old, new) -> GuidanceEconomicInterpretation:
    (interpretation,) = interpreted(old, new)
    return interpretation


def pair(subject, old_low, new_low, *, old_high=None, new_high=None, bound=ClaimBound.POINT):
    return (
        claim(subject=subject, bound=bound, low=old_low, high=old_high, period="2026Q1", claim_id="old"),
        claim(subject=subject, bound=bound, low=new_low, high=new_high, period="2026Q2", claim_id="new"),
    )


# -- every subject, every direction -------------------------------------------

EXPECTED = [
    # subject, old, new, dimension, movement, effect
    (ClaimSubject.REVENUE, 100, 110, EconomicDimension.REVENUE, ExpectedMovement.INCREASED, OutlookEffect.STRENGTHENING),
    (ClaimSubject.REVENUE, 100, 90, EconomicDimension.REVENUE, ExpectedMovement.DECREASED, OutlookEffect.WEAKENING),
    (ClaimSubject.REVENUE, 100, 100, EconomicDimension.REVENUE, ExpectedMovement.UNCHANGED, OutlookEffect.UNCHANGED),
    (ClaimSubject.ADJUSTED_EBITDA, 100, 110, EconomicDimension.EARNINGS, ExpectedMovement.INCREASED, OutlookEffect.STRENGTHENING),
    (ClaimSubject.ADJUSTED_EBITDA, 100, 90, EconomicDimension.EARNINGS, ExpectedMovement.DECREASED, OutlookEffect.WEAKENING),
    (ClaimSubject.ADJUSTED_EBITDA, 100, 100, EconomicDimension.EARNINGS, ExpectedMovement.UNCHANGED, OutlookEffect.UNCHANGED),
    (ClaimSubject.FREE_CASH_FLOW, 100, 110, EconomicDimension.CASH_GENERATION, ExpectedMovement.INCREASED, OutlookEffect.STRENGTHENING),
    (ClaimSubject.FREE_CASH_FLOW, 100, 90, EconomicDimension.CASH_GENERATION, ExpectedMovement.DECREASED, OutlookEffect.WEAKENING),
    (ClaimSubject.FREE_CASH_FLOW, 100, 100, EconomicDimension.CASH_GENERATION, ExpectedMovement.UNCHANGED, OutlookEffect.UNCHANGED),
    (ClaimSubject.CAPITAL_EXPENDITURE, 100, 110, EconomicDimension.INVESTMENT_SPENDING, ExpectedMovement.INCREASED, OutlookEffect.AMBIGUOUS),
    (ClaimSubject.CAPITAL_EXPENDITURE, 100, 90, EconomicDimension.INVESTMENT_SPENDING, ExpectedMovement.DECREASED, OutlookEffect.AMBIGUOUS),
    (ClaimSubject.CAPITAL_EXPENDITURE, 100, 100, EconomicDimension.INVESTMENT_SPENDING, ExpectedMovement.UNCHANGED, OutlookEffect.UNCHANGED),
]


class TestSubjectSemantics:
    @pytest.mark.parametrize("subject,old,new,dimension,movement,effect", EXPECTED,
                             ids=[f"{s.value}-{o}->{n}" for s, o, n, *_ in EXPECTED])
    def test_each_subject_and_direction(self, subject, old, new, dimension, movement, effect):
        interpretation = one(*pair(subject, old, new))
        assert (interpretation.dimension, interpretation.movement, interpretation.outlook_effect) == (
            dimension, movement, effect,
        )

    def test_raised_capex_is_more_spending_not_good_news(self):
        interpretation = one(*pair(ClaimSubject.CAPITAL_EXPENDITURE, 100, 120))
        assert interpretation.movement is ExpectedMovement.INCREASED
        assert interpretation.outlook_effect is OutlookEffect.AMBIGUOUS
        assert interpretation.outlook_effect is not OutlookEffect.STRENGTHENING

    def test_lowered_capex_is_less_spending_not_bad_news(self):
        assert one(*pair(ClaimSubject.CAPITAL_EXPENDITURE, 100, 80)).outlook_effect is OutlookEffect.AMBIGUOUS

    @pytest.mark.parametrize("subject", list(ClaimSubject))
    def test_a_reaffirmation_is_never_encoded_as_strengthening(self, subject):
        interpretation = one(*pair(subject, 100, 100))
        assert interpretation.outlook_effect is OutlookEffect.UNCHANGED

    def test_the_model_carries_no_polarity_score_or_confidence(self):
        names = {f.name for f in dataclasses.fields(GuidanceEconomicInterpretation)}
        for forbidden in ("polarity", "sentiment", "score", "confidence", "is_positive", "bullish", "bearish",
                          "materiality", "is_material", "recommendation", "impact"):
            assert not any(forbidden in name for name in names), forbidden
        for enum in (EconomicDimension, ExpectedMovement, OutlookEffect):
            for member in enum:
                assert member.value not in ("positive", "negative", "bullish", "bearish", "good", "bad")


class TestShapesAndMagnitude:
    def test_a_partial_range_raise_moves_only_the_low_end(self):
        interpretation = one(*pair(ClaimSubject.REVENUE, 41.0 * B, 41.1 * B, old_high=41.3 * B, new_high=41.3 * B,
                                   bound=ClaimBound.RANGE))
        assert interpretation.revision_type is RevisionType.RAISED
        assert interpretation.low_end_change == pytest.approx(0.1 * B)
        assert interpretation.high_end_change == 0
        assert "the low end rose and the high end was unchanged" in interpretation.explanation

    def test_a_partial_range_lower_moves_only_the_high_end(self):
        interpretation = one(*pair(ClaimSubject.REVENUE, 41.0 * B, 41.0 * B, old_high=41.3 * B, new_high=41.2 * B,
                                   bound=ClaimBound.RANGE))
        assert interpretation.movement is ExpectedMovement.DECREASED
        assert interpretation.low_end_change == 0
        assert interpretation.high_end_change == pytest.approx(-0.1 * B)
        assert "the low end was unchanged and the high end fell" in interpretation.explanation

    def test_identical_ranges_have_no_change_at_either_end(self):
        interpretation = one(*pair(ClaimSubject.ADJUSTED_EBITDA, 6.8 * B, 6.8 * B, old_high=7.6 * B, new_high=7.6 * B,
                                   bound=ClaimBound.RANGE))
        assert (interpretation.low_end_change, interpretation.high_end_change) == (0, 0)
        assert (interpretation.low_end_relative_change, interpretation.high_end_relative_change) == (0, 0)

    def test_a_point_revision_changes_both_ends_equally(self):
        interpretation = one(*pair(ClaimSubject.REVENUE, 100.0, 110.0))
        assert interpretation.low_end_change == interpretation.high_end_change == 10.0
        assert interpretation.low_end_relative_change == pytest.approx(0.1)
        assert "both ends" not in interpretation.explanation  # a point has no ends to describe

    @pytest.mark.parametrize("bound", [ClaimBound.LOWER_BOUND, ClaimBound.UPPER_BOUND])
    def test_a_one_sided_bound_moves_its_single_figure(self, bound):
        interpretation = one(*pair(ClaimSubject.CAPITAL_EXPENDITURE, 20 * B, 25 * B, bound=bound))
        assert interpretation.movement is ExpectedMovement.INCREASED
        assert interpretation.low_end_change == interpretation.high_end_change == 5 * B

    def test_there_is_no_midpoint_anywhere(self):
        names = {f.name for f in dataclasses.fields(GuidanceEconomicInterpretation)}
        assert not any("mid" in name for name in names)

    def test_a_prior_of_zero_has_no_relative_change(self):
        interpretation = one(*pair(ClaimSubject.FREE_CASH_FLOW, 0.0, 1.0))
        assert interpretation.low_end_relative_change is None


class TestEvidenceHandling:
    def test_evidence_that_disagrees_on_direction_is_not_interpreted(self):
        """A stated prior above the new figure and an observed prior below
        it: no single movement exists, so none is interpreted."""
        old = claim(low=100 * B, period="2026Q1", claim_id="old")
        new = claim(low=110 * B, period="2026Q2", claim_id="new",
                    source_text="We now expect revenue of $110 billion in 2027, down from our previous estimate of $120 billion.")
        revisions, _ = detect_revisions((old, new))
        assert revisions and revisions[0].revision_type is None
        assert interpret_revisions(revisions, (old, new)) == ()

    def test_agreed_direction_with_different_priors_keeps_no_magnitude(self):
        old = claim(low=100 * B, period="2026Q1", claim_id="old")
        new = claim(low=130 * B, period="2026Q2", claim_id="new",
                    source_text="We now expect revenue of $130 billion in 2027, up from our previous estimate of $120 billion.")
        (interpretation,) = interpreted(old, new)
        assert interpretation.movement is ExpectedMovement.INCREASED
        assert (interpretation.prior_value_low, interpretation.low_end_change, interpretation.prior_value_text) == (None, None, None)
        assert "sources state different prior figures" in interpretation.explanation

    def test_the_wrong_claim_is_refused_rather_than_misread(self):
        old, new = pair(ClaimSubject.REVENUE, 100, 110)
        (revision,), _ = detect_revisions((old, new))
        with pytest.raises(ValueError):
            interpret_revision(revision, old)


class TestNoAggregationAndNoRevisionControl:
    def test_two_dimensions_for_one_company_stay_two_interpretations(self):
        claims = (
            claim(subject=ClaimSubject.REVENUE, low=100, period="2026Q1", claim_id="r1"),
            claim(subject=ClaimSubject.REVENUE, low=110, period="2026Q2", claim_id="r2"),
            claim(subject=ClaimSubject.FREE_CASH_FLOW, low=50, period="2026Q1", claim_id="f1"),
            claim(subject=ClaimSubject.FREE_CASH_FLOW, low=40, period="2026Q2", claim_id="f2"),
        )
        revisions, _ = detect_revisions(claims)
        effects = {i.dimension: i.outlook_effect for i in interpret_revisions(revisions, claims)}
        assert effects == {EconomicDimension.REVENUE: OutlookEffect.STRENGTHENING,
                           EconomicDimension.CASH_GENERATION: OutlookEffect.WEAKENING}

    def test_a_claim_with_no_prior_gets_no_interpretation(self):
        lone = claim(low=100, period="2026Q2", claim_id="lone")
        revisions, _ = detect_revisions((lone,))
        assert interpret_revisions(revisions, (lone,)) == ()


class TestFirewalls:
    _SOURCE = Path(__file__).resolve().parents[4] / "atlas" / "analysis_engine" / "forward_claims" / "interpretation.py"

    def test_no_time_other_than_the_fiscal_period_is_read(self):
        """Stage 3.1/3.2: none of these is when management spoke."""
        tree = ast.parse(self._SOURCE.read_text(encoding="utf-8"))
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        for forbidden in ("published_at", "period_end", "period_start", "statement_at", "extracted_at",
                          "created_at", "computed_at", "reported_at", "now", "today", "utcnow"):
            assert forbidden not in attributes, forbidden

    def test_it_depends_on_nothing_that_could_make_it_a_recommendation(self):
        tree = ast.parse(self._SOURCE.read_text(encoding="utf-8"))
        imported = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        assert all(m.startswith("atlas.analysis_engine.forward_claims") or m in ("__future__", "dataclasses", "enum")
                   for m in imported), imported

    def test_the_explanation_states_what_changed_never_why(self):
        claims = pair(ClaimSubject.CAPITAL_EXPENDITURE, 175 * B, 180 * B, old_high=185 * B, new_high=190 * B,
                      bound=ClaimBound.RANGE)
        text = one(*claims).explanation.lower()
        for causal in ("because", "due to", "driven by", "demand", "expects", "bullish", "bearish", "strong",
                       "aggressive", "confident", "recent", "positive", "negative"):
            assert causal not in text, causal


# -- the five real events, from verbatim transcript sentences ------------------

def statement(content, *, company, quarter, title="Chief Financial Officer"):
    end = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}[quarter[4:]]
    result = ingest(
        build_raw_document(
            identifier=f"{company}:transcript:{quarter}:0", company=company, source_kind="transcript",
            published_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
            period_start=date(int(quarter[:4]), *end), period_end=date(int(quarter[:4]), *end),
            content_hash=f"{company}-{quarter}",
            metadata={"quarter": quarter, "statement_index": 0, "speaker": "A. Exec", "title": title, "content": content},
        ),
        evaluated_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def real(*records):
    claims = tuple(c for r in records for c in extract_forward_claims(r, extracted_at=datetime(2026, 9, 11, tzinfo=timezone.utc))[0])
    revisions, _ = detect_revisions(claims)
    return interpret_revisions(revisions, claims)


GOOGL = {
    "2025Q4": "For the full year 2026, we expect CapEx to be in the range of $175 billion to $185 billion with investments ramping over the course of the year.",
    "2026Q1": "We are updating our full year 2026 CapEx guidance range to $180 billion to $190 billion, up from our previous estimate of $175 billion to $185 billion to now include investment related to the acquisition of Intersect, which closed in March.",
    "2026Q2": "We are updating our full year 2026 CapEx guidance range to $195 billion to $205 billion, up from our previous estimate of $180 billion to $190 billion.",
}
CRM = {
    "2026Q1": "Guidance: we raised fiscal year 2026 revenue guidance to $41.0 billion to $41.3 billion, increasing the high end by $400 million driven by foreign exchange tailwinds.",
    "2026Q2": "We are pleased to raise the low end of our fiscal year 2026 revenue guidance to $41.1 billion to $41.3 billion, resulting in growth of approximately 8.5% to 9% year over year in nominal and 8% in constant currency.",
}
VST = {
    "2025Q3": "We are introducing guidance ranges for 2026 adjusted EBITDA of $6.8 billion to $7.6 billion and adjusted free cash flow before growth of $3.925 billion to $4.725 billion, including the expected contribution from the assets acquired from Lotus Infrastructure Partners.",
    "2026Q2": "Turning to slide nine, we are reaffirming our 2026 Adjusted EBITDA guidance range of $6.8 billion-$7.6 billion and our adjusted free cash flow before growth guidance range of $3.925 billion-$4.725 billion.",
}


class TestTheFiveRealEvents:
    def test_googl_capex_raises_are_more_investment_spending_and_nothing_more(self):
        first, second = real(*(statement(text, company="GOOGL", quarter=q) for q, text in GOOGL.items()))
        for interpretation in (first, second):
            assert interpretation.dimension is EconomicDimension.INVESTMENT_SPENDING
            assert interpretation.movement is ExpectedMovement.INCREASED
            assert interpretation.outlook_effect is OutlookEffect.AMBIGUOUS
            assert set(interpretation.evidence_bases) == {RevisionBasis.OBSERVED_PRIOR_CLAIM,
                                                          RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE}
        assert (first.low_end_change, first.high_end_change) == (5 * B, 5 * B)
        assert (second.low_end_change, second.high_end_change) == (15 * B, 15 * B)
        assert (first.new_source_period, second.new_source_period) == ("2026Q1", "2026Q2")
        assert first.explanation == ("GOOGL management raised its 2026 guidance for capital expenditure: "
                                     "$175 billion to $185 billion → $180 billion to $190 billion; both ends rose.")

    def test_crm_revenue_raise_is_narrow_and_says_so(self):
        (interpretation,) = real(*(statement(text, company="CRM", quarter=q, title="Chief Operating & Financial Officer")
                                   for q, text in CRM.items()))
        assert (interpretation.dimension, interpretation.movement, interpretation.outlook_effect) == (
            EconomicDimension.REVENUE, ExpectedMovement.INCREASED, OutlookEffect.STRENGTHENING,
        )
        assert interpretation.horizon_kind is HorizonKind.FISCAL_YEAR
        assert interpretation.low_end_change == pytest.approx(0.1 * B)
        assert interpretation.high_end_change == 0
        assert interpretation.explanation.endswith("the low end rose and the high end was unchanged.")

    def test_vst_reaffirmations_are_unchanged_not_positive(self):
        interpretations = real(*(statement(text, company="VST", quarter=q) for q, text in VST.items()))
        by_dimension = {i.dimension: i for i in interpretations}
        assert set(by_dimension) == {EconomicDimension.EARNINGS, EconomicDimension.CASH_GENERATION}
        for interpretation in interpretations:
            assert interpretation.movement is ExpectedMovement.UNCHANGED
            assert interpretation.outlook_effect is OutlookEffect.UNCHANGED
            assert (interpretation.low_end_change, interpretation.high_end_change) == (0, 0)

    def test_vst_cash_measure_keeps_its_before_growth_qualification(self):
        """The canonical subject is generic free cash flow; the source says
        "adjusted free cash flow before growth". The explanation does not
        present it as plain free cash flow, and the verbatim wording
        travels with the interpretation."""
        cash = next(i for i in real(*(statement(t, company="VST", quarter=q) for q, t in VST.items()))
                    if i.dimension is EconomicDimension.CASH_GENERATION)
        assert "a free-cash-flow measure" in cash.explanation
        assert "guidance for free cash flow" not in cash.explanation
        assert "free cash flow before growth" in cash.new_source_text

    def test_reinterpreting_is_deterministic(self):
        records = tuple(statement(text, company="GOOGL", quarter=q) for q, text in GOOGL.items())
        assert real(*records) == real(*records)
