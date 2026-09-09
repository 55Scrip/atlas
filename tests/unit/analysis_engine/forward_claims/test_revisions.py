"""Forward-Looking Evidence, Stage 2 -- guidance revision semantics.

Two questions run through every test here: did the number move, and did
Atlas resist saying anything about whether that is good news.
"""
from datetime import datetime, timezone

import pytest

from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims import (
    REVISION_ENGINE_VERSION,
    ClaimBound,
    ClaimSubject,
    ClaimType,
    ClaimantRole,
    ForwardClaim,
    NonRevisionReason,
    RevisionBasis,
    RevisionType,
    compare_claims,
    detect_revisions,
    group_claims,
)

Q1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
Q2 = datetime(2026, 5, 1, tzinfo=timezone.utc)
Q3 = datetime(2026, 8, 1, tzinfo=timezone.utc)
Q4 = datetime(2026, 11, 1, tzinfo=timezone.utc)


def claim(
    *,
    company: str = "ACME",
    subject: ClaimSubject = ClaimSubject.REVENUE,
    bound: ClaimBound = ClaimBound.POINT,
    low: float = 100.0,
    high: float | None = None,
    unit: str = "USD_BILLION",
    horizon: str = "2027",
    reported_at: datetime = Q1,
    source_text: str = "We expect revenue of $100 billion in 2027.",
    claim_id: str | None = None,
) -> ForwardClaim:
    high = low if high is None else high
    return ForwardClaim(
        id=claim_id or f"{company}:{subject.value}:{horizon}:{reported_at.date()}",
        company=company,
        claim_type=ClaimType.GUIDANCE,
        subject=subject,
        bound=bound,
        value_low=low,
        value_high=high,
        unit=unit,
        value_text=f"${low}",
        horizon_period=horizon,
        horizon_text=horizon,
        claimant_role=ClaimantRole.EXECUTIVE,
        stated_by="A. Executive",
        stated_by_title="Chief Financial Officer",
        source_record_id=f"rec-{reported_at.date()}",
        source_kind=SourceKind.TRANSCRIPT,
        source_text=source_text,
        reported_at=reported_at,
        extracted_at=Q4,
        extractor_version="transcript-guidance-v1",
    )


class TestPointSemantics:
    def test_a_higher_figure_is_raised(self):
        assert compare_claims(claim(low=100), claim(low=110, reported_at=Q2)).revision_type is RevisionType.RAISED

    def test_a_lower_figure_is_lowered(self):
        assert compare_claims(claim(low=100), claim(low=90, reported_at=Q2)).revision_type is RevisionType.LOWERED

    def test_the_same_figure_is_reaffirmed(self):
        assert compare_claims(claim(low=100), claim(low=100, reported_at=Q2)).revision_type is RevisionType.REAFFIRMED


class TestRangeSemantics:
    def test_both_ends_up_is_raised(self):
        old = claim(bound=ClaimBound.RANGE, low=180, high=190)
        new = claim(bound=ClaimBound.RANGE, low=195, high=205, reported_at=Q2)
        assert compare_claims(old, new).revision_type is RevisionType.RAISED

    def test_both_ends_down_is_lowered(self):
        old = claim(bound=ClaimBound.RANGE, low=195, high=205)
        new = claim(bound=ClaimBound.RANGE, low=180, high=190, reported_at=Q2)
        assert compare_claims(old, new).revision_type is RevisionType.LOWERED

    def test_an_identical_range_is_reaffirmed(self):
        old = claim(bound=ClaimBound.RANGE, low=6.8, high=7.6)
        new = claim(bound=ClaimBound.RANGE, low=6.8, high=7.6, reported_at=Q2)
        assert compare_claims(old, new).revision_type is RevisionType.REAFFIRMED

    def test_ranges_may_overlap_and_still_be_raised_when_both_ends_moved_up(self):
        """Overlap alone is not disqualifying: 180-190 becoming 185-195
        raised both the floor and the ceiling, which management did
        state. What is refused is reading a direction out of midpoints
        the company never gave -- see the narrowing case below."""
        old = claim(bound=ClaimBound.RANGE, low=180, high=190)
        new = claim(bound=ClaimBound.RANGE, low=185, high=195, reported_at=Q2)
        assert compare_claims(old, new).revision_type is RevisionType.RAISED

    def test_a_range_whose_ends_moved_in_opposite_directions_is_not_a_direction(self):
        old = claim(bound=ClaimBound.RANGE, low=180, high=200)
        new = claim(bound=ClaimBound.RANGE, low=190, high=195, reported_at=Q2)
        result = compare_claims(old, new)
        assert not result.is_revision
        assert result.reason is NonRevisionReason.MIXED_RANGE_CHANGE

    def test_a_narrowing_range_is_not_a_direction(self):
        old = claim(bound=ClaimBound.RANGE, low=180, high=200)
        new = claim(bound=ClaimBound.RANGE, low=185, high=195, reported_at=Q2)
        assert compare_claims(old, new).reason is NonRevisionReason.MIXED_RANGE_CHANGE


class TestBoundSemantics:
    def test_a_raised_floor_is_raised(self):
        old = claim(bound=ClaimBound.LOWER_BOUND, low=100)
        new = claim(bound=ClaimBound.LOWER_BOUND, low=110, reported_at=Q2)
        assert compare_claims(old, new).revision_type is RevisionType.RAISED

    def test_a_reduced_ceiling_is_lowered_numerically_and_says_nothing_more(self):
        """"up to 90" from "up to 100" moved down. Whether a lower
        ceiling is welcome is not this module's question."""
        old = claim(bound=ClaimBound.UPPER_BOUND, low=100)
        new = claim(bound=ClaimBound.UPPER_BOUND, low=90, reported_at=Q2)
        assert compare_claims(old, new).revision_type is RevisionType.LOWERED

    def test_a_point_and_a_range_are_not_the_same_shape_of_statement(self):
        old = claim(bound=ClaimBound.POINT, low=7)
        new = claim(bound=ClaimBound.RANGE, low=6.8, high=7.6, reported_at=Q2)
        assert compare_claims(old, new).reason is NonRevisionReason.INCOMPATIBLE_BOUND


class TestComparability:
    @pytest.mark.parametrize(
        "kwargs,expected",
        [
            ({"company": "OTHER"}, NonRevisionReason.DIFFERENT_COMPANY),
            ({"subject": ClaimSubject.CAPITAL_EXPENDITURE}, NonRevisionReason.DIFFERENT_SUBJECT),
            ({"horizon": "2028"}, NonRevisionReason.DIFFERENT_HORIZON),
            ({"unit": "EUR_BILLION"}, NonRevisionReason.INCOMPATIBLE_UNIT),
        ],
    )
    def test_claims_that_mean_different_things_are_never_compared(self, kwargs, expected):
        result = compare_claims(claim(), claim(reported_at=Q2, **kwargs))
        assert not result.is_revision
        assert result.reason is expected


class TestEconomicNeutrality:
    """The firewall this stage exists behind. A revision is a number
    moving, never an opinion about the investment."""

    def test_the_enum_carries_no_notion_of_good_or_bad(self):
        names = {member.name for member in RevisionType}
        assert names == {"RAISED", "LOWERED", "REAFFIRMED"}
        for word in ("POSITIVE", "NEGATIVE", "IMPROVED", "DETERIORATED", "GOOD", "BAD", "BULLISH", "BEARISH"):
            assert word not in names

    def test_raising_capex_and_raising_revenue_are_the_same_fact(self):
        """Raising capex may be a company investing into demand or one
        losing control of its costs. Stage 2 must not choose."""
        revenue = compare_claims(
            claim(subject=ClaimSubject.REVENUE, low=100),
            claim(subject=ClaimSubject.REVENUE, low=110, reported_at=Q2),
        )
        capex = compare_claims(
            claim(subject=ClaimSubject.CAPITAL_EXPENDITURE, low=100),
            claim(subject=ClaimSubject.CAPITAL_EXPENDITURE, low=110, reported_at=Q2),
        )
        assert revenue.revision_type is capex.revision_type is RevisionType.RAISED

    def test_a_revision_has_no_field_that_could_hold_a_verdict(self):
        from dataclasses import fields

        from atlas.analysis_engine.forward_claims.revisions import GuidanceRevision

        names = {f.name for f in fields(GuidanceRevision)}
        for forbidden in ("polarity", "sentiment", "impact", "materiality", "score", "is_positive", "significance"):
            assert forbidden not in names


class TestOrdering:
    def test_the_older_claim_must_have_been_reported_first(self):
        newer, older = claim(low=110, reported_at=Q2), claim(low=100, reported_at=Q1)
        assert compare_claims(newer, older).reason is NonRevisionReason.AMBIGUOUS_ORDER

    def test_equal_timestamps_are_ambiguous_rather_than_broken_by_a_record_id(self):
        a = claim(low=100, reported_at=Q1, claim_id="aaa")
        b = claim(low=110, reported_at=Q1, claim_id="zzz")
        assert compare_claims(a, b).reason is NonRevisionReason.AMBIGUOUS_ORDER

    def test_the_horizon_never_decides_which_claim_came_first(self):
        old = claim(low=100, horizon="2027", reported_at=Q1)
        new = claim(low=110, horizon="2027", reported_at=Q2)
        assert compare_claims(old, new).revision_type is RevisionType.RAISED


class TestHistory:
    def _series(self):
        return (
            claim(low=100, reported_at=Q1, claim_id="c1"),
            claim(low=110, reported_at=Q2, claim_id="c2"),
            claim(low=105, reported_at=Q3, claim_id="c3"),
            claim(low=105, reported_at=Q4, claim_id="c4"),
        )

    def test_a_series_keeps_every_step_rather_than_collapsing_to_the_latest(self):
        revisions, _ = detect_revisions(self._series())
        assert [r.revision_type for r in revisions] == [
            RevisionType.RAISED,
            RevisionType.LOWERED,
            RevisionType.REAFFIRMED,
        ]

    def test_nothing_is_overwritten_when_a_claim_is_superseded(self):
        claims = self._series()
        revisions, _ = detect_revisions(claims)
        # Every original claim is untouched and still reachable.
        assert claims == self._series()
        assert {r.prior_claim_id for r in revisions} == {"c1", "c2", "c3"}

    def test_a_first_claim_is_not_a_revision(self):
        revisions, unrevised = detect_revisions((claim(low=100),))
        assert revisions == ()
        assert set(unrevised.values()) == {NonRevisionReason.NO_PRIOR_CLAIM}

    def test_the_result_does_not_depend_on_the_order_claims_arrive_in(self):
        forward = detect_revisions(self._series())[0]
        shuffled = detect_revisions(tuple(reversed(self._series())))[0]
        assert forward == shuffled

    def test_grouping_keys_on_everything_that_must_match(self):
        groups = group_claims(
            (claim(subject=ClaimSubject.REVENUE), claim(subject=ClaimSubject.CAPITAL_EXPENDITURE, reported_at=Q2))
        )
        assert len(groups) == 2


class TestPriorValueStatedInTheSameSentence:
    GOOGL = (
        "We are updating our full year 2026 CapEx guidance range to $195 billion to $205 billion, "
        "up from our previous estimate of $180 billion to $190 billion."
    )

    def _claim(self, text: str = GOOGL) -> ForwardClaim:
        return claim(
            company="GOOGL",
            subject=ClaimSubject.CAPITAL_EXPENDITURE,
            bound=ClaimBound.RANGE,
            low=195e9,
            high=205e9,
            horizon="2026",
            source_text=text,
        )

    def test_management_restating_its_own_previous_range_is_a_revision(self):
        revisions, _ = detect_revisions((self._claim(),))
        assert len(revisions) == 1
        assert revisions[0].revision_type is RevisionType.RAISED
        assert (revisions[0].prior_value_low, revisions[0].prior_value_high) == (180e9, 190e9)

    def test_it_is_never_presented_as_guidance_atlas_observed(self):
        """Atlas never saw the earlier guidance issued. Claiming an
        earlier observation would fabricate a source event."""
        revision = detect_revisions((self._claim(),))[0][0]
        assert revision.basis is RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE
        assert revision.prior_claim_id is None
        assert revision.prior_source_record_id == revision.new_source_record_id

    def test_both_values_are_retrievable_from_the_one_sentence_that_carries_them(self):
        revision = detect_revisions((self._claim(),))[0][0]
        assert revision.prior_value_text in revision.prior_source_text
        assert revision.new_value_text in revision.new_source_text or revision.new_value_text.startswith("$")
        assert revision.prior_source_text == self.GOOGL

    def test_a_historical_comparison_is_not_a_guidance_revision(self):
        """"up from 42% a year ago" describes what happened, and the
        corpus is full of it. Only an explicit prior-guidance phrase
        counts."""
        revisions, _ = detect_revisions(
            (self._claim("Data center revenue more than doubled year-over-year, up from 42 billion a year ago."),)
        )
        assert revisions == ()

    def test_a_statement_with_no_prior_reference_produces_no_revision(self):
        revisions, unrevised = detect_revisions(
            (self._claim("We expect full year 2026 CapEx of $195 billion to $205 billion."),)
        )
        assert revisions == ()
        assert set(unrevised.values()) == {NonRevisionReason.NO_PRIOR_CLAIM}


class TestProvenanceAndVersioning:
    def test_a_revision_can_be_traced_to_both_of_its_operands(self):
        revisions, _ = detect_revisions((claim(low=100, reported_at=Q1, claim_id="c1"),
                                         claim(low=110, reported_at=Q2, claim_id="c2")))
        revision = revisions[0]
        assert revision.prior_claim_id == "c1" and revision.new_claim_id == "c2"
        assert revision.prior_source_text and revision.new_source_text
        assert revision.prior_reported_at < revision.new_reported_at
        assert revision.stated_by_title == "Chief Financial Officer"

    def test_every_revision_records_which_rules_produced_it(self):
        revisions, _ = detect_revisions((claim(low=100, reported_at=Q1), claim(low=110, reported_at=Q2)))
        assert revisions[0].revision_engine_version == REVISION_ENGINE_VERSION

    def test_withdrawal_is_not_inferred_from_a_claim_simply_not_recurring(self):
        """Absence is absence. The corpus's only "withdraw" sentences
        are the Operator explaining how to withdraw a question."""
        assert "WITHDRAWN" not in {m.name for m in RevisionType}
        revisions, unrevised = detect_revisions((claim(low=100, reported_at=Q1),))
        assert revisions == ()
        assert set(unrevised.values()) == {NonRevisionReason.NO_PRIOR_CLAIM}
