"""Forward-Looking Evidence, Stage 1.2 -- measure scope and claim status.

Local grounding (Stage 1.1) proves subject, figure and year belong to
one proposition. It does not prove the proposition is the company's
current guidance for that measure. Two real VST sentences show the gap:
a previously communicated figure and an asset-level contribution, both
perfectly grounded, neither company-level guidance.

Normal extraction hid both: claims are unique per (subject, horizon)
within one statement, and in the real 2025Q3 statement the genuine
guidance sentence happens to come first. These tests therefore extract
each hazard with no competing claim at all -- alone, and ahead of the
genuine guidance -- so order and de-duplication cannot mask anything.
"""
from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.forward_claims import (
    ClaimBound,
    ClaimSubject,
    HorizonKind,
    extract_forward_claims,
)
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

EVALUATED_AT = datetime(2026, 9, 9, tzinfo=timezone.utc)
EXTRACTED_AT = datetime(2026, 9, 10, tzinfo=timezone.utc)
B = 1e9


def claims_for(content: str, *, period_end: date = date(2025, 9, 30), title: str = "President and CEO"):
    result = ingest(
        build_raw_document(
            identifier="TEST:transcript:x:0",
            company="TEST",
            source_kind="transcript",
            published_at=EVALUATED_AT,
            period_start=period_end,
            period_end=period_end,
            metadata={"quarter": "x", "statement_index": 0, "speaker": "A. Exec", "title": title,
                      "content": content},
        ),
        evaluated_at=EVALUATED_AT,
    )
    assert isinstance(result, IngestedRecord)
    return extract_forward_claims(result.record, extracted_at=EXTRACTED_AT)


def as_facts(claims):
    return {(c.subject, c.horizon_period, c.horizon_kind, c.bound, c.value_low, c.value_high) for c in claims}


# Verbatim, VST 2025Q3 call, statement 2 (James Burke, President and CEO).

#: The company's own previously communicated figure, cited as a
#: comparison baseline -- not guidance being issued in this proposition.
VST_PREVIOUSLY_COMMUNICATED = (
    "It's worth noting that excluding the benefits from the Lotus assets, the midpoint of our 2026 adjusted "
    "EBITDA guidance range is above our previously communicated 2026 adjusted EBITDA midpoint opportunity of "
    "$6.8 billion plus, another clear sign of sustainable momentum across our business."
)

#: EBITDA from a subset of assets -- not company-level adjusted EBITDA.
VST_ASSET_CONTRIBUTION = (
    "We continue to target approximately $270 million of adjusted EBITDA from these assets in 2026, with "
    "potential upside in the out years driven by synergies and higher capacity revenue."
)

#: The genuine company-level guidance issued on the same call.
VST_GUIDANCE = (
    "We are introducing guidance ranges for 2026 adjusted EBITDA of $6.8 billion to $7.6 billion and adjusted "
    "free cash flow before growth of $3.925 billion to $4.725 billion, including the expected contribution "
    "from the assets acquired from Lotus Infrastructure Partners."
)
VST_GUIDANCE_FACTS = {
    (ClaimSubject.ADJUSTED_EBITDA, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 6.8 * B, 7.6 * B),
    (ClaimSubject.FREE_CASH_FLOW, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 3.925 * B, 4.725 * B),
}


class TestTheTwoLatentClaimsWithNoDedupeToHideThem:
    def test_a_previously_communicated_figure_on_its_own_is_not_a_current_claim(self):
        claims, _ = claims_for(VST_PREVIOUSLY_COMMUNICATED)
        assert claims == ()

    def test_an_asset_level_contribution_on_its_own_is_not_company_level_ebitda(self):
        claims, _ = claims_for(VST_ASSET_CONTRIBUTION)
        assert claims == ()

    def test_placed_before_the_real_guidance_the_reference_figure_does_not_displace_it(self):
        """In the real statement the guidance sentence comes first, so
        the first-claim-wins rule kept it. Reverse the order and the
        reference figure used to take the (subject, horizon) slot and
        silently drop the genuine range."""
        claims, _ = claims_for(f"{VST_PREVIOUSLY_COMMUNICATED} {VST_GUIDANCE}")
        assert as_facts(claims) == VST_GUIDANCE_FACTS

    def test_placed_before_the_real_guidance_the_asset_figure_does_not_displace_it(self):
        claims, _ = claims_for(f"{VST_ASSET_CONTRIBUTION} {VST_GUIDANCE}")
        assert as_facts(claims) == VST_GUIDANCE_FACTS

    def test_the_real_order_still_yields_exactly_the_real_guidance(self):
        claims, _ = claims_for(f"{VST_GUIDANCE} {VST_PREVIOUSLY_COMMUNICATED} {VST_ASSET_CONTRIBUTION}")
        assert as_facts(claims) == VST_GUIDANCE_FACTS


from atlas.analysis_engine.forward_claims import (  # noqa: E402
    ClaimRejectionReason,
    RevisionBasis,
    RevisionType,
    detect_revisions,
)


class TestWhyTheLatentClaimsAreRejected:
    def test_the_previously_communicated_figure_is_a_reference_value(self):
        _, rejected = claims_for(VST_PREVIOUSLY_COMMUNICATED)
        assert [r.reason for r in rejected] == [ClaimRejectionReason.REFERENCE_VALUE]

    def test_the_asset_contribution_is_below_company_level(self):
        _, rejected = claims_for(VST_ASSET_CONTRIBUTION)
        assert [r.reason for r in rejected] == [ClaimRejectionReason.MEASURE_BELOW_COMPANY_LEVEL]


def point(subject, value, year="2027"):
    return (subject, year, HorizonKind.UNSPECIFIED_YEAR, ClaimBound.POINT, value, value)


def span(subject, low, high, year="2027"):
    return (subject, year, HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, low, high)


class TestCompanyLevelMeasuresStillClaim:
    def test_company_ebitda_guidance(self):
        claims, _ = claims_for("We expect 2027 adjusted EBITDA of $5 billion to $5.5 billion.")
        assert as_facts(claims) == {span(ClaimSubject.ADJUSTED_EBITDA, 5 * B, 5.5 * B)}

    def test_company_level_qualifiers_do_not_narrow_the_measure(self):
        claims, _ = claims_for("We expect total company revenue of $10 billion in 2027.")
        assert as_facts(claims) == {point(ClaimSubject.REVENUE, 10 * B)}

    def test_current_guidance_reaffirmed_numerically(self):
        claims, _ = claims_for("We are reaffirming our 2027 revenue guidance of $10 billion to $10.5 billion.")
        assert as_facts(claims) == {span(ClaimSubject.REVENUE, 10 * B, 10.5 * B)}


class TestMeasuresBelowCompanyLevel:
    """No segment list: only generic corporate-structure words, a
    capitalised name in front of the measure, or a source restriction
    after it."""

    def test_asset_level_ebitda_contribution(self):
        claims, _ = claims_for("We expect asset-level EBITDA contribution of about $300 million in 2027.")
        assert claims == ()

    def test_assets_contributing_ebitda(self):
        claims, _ = claims_for("We expect the acquired assets to contribute adjusted EBITDA of $300 million in 2027.")
        assert claims == ()

    def test_segment_revenue(self):
        claims, _ = claims_for("We expect Data Center segment revenue of $50 billion in 2027.")
        assert claims == ()

    def test_a_named_segment_in_front_of_the_measure(self):
        claims, _ = claims_for("We expect Semiconductor Systems revenue of around $20 billion in 2027.")
        assert claims == ()

    def test_ai_capex_is_not_company_capex(self):
        claims, _ = claims_for("We expect AI capex of about $40 billion in 2027.")
        assert claims == ()

    def test_acquisition_contribution(self):
        claims, _ = claims_for("We expect revenue from the acquisition of about $2 billion in 2027.")
        assert claims == ()

    def test_incremental_ebitda(self):
        claims, _ = claims_for("We expect incremental EBITDA of $500 million in 2027.")
        assert claims == ()

    def test_a_company_claim_beside_a_subset_one_survives_alone(self):
        claims, _ = claims_for(
            "We expect 2027 adjusted EBITDA of $5 billion, including approximately $270 million of adjusted "
            "EBITDA from these assets."
        )
        assert as_facts(claims) == {point(ClaimSubject.ADJUSTED_EBITDA, 5 * B)}


class TestReferenceValues:
    def test_previously_communicated_guidance_is_not_reissued(self):
        claims, _ = claims_for("We remain above our previously communicated 2027 revenue target of $10 billion.")
        assert claims == ()

    def test_a_prior_estimate_cited_alone_is_not_a_claim(self):
        claims, _ = claims_for("Our prior 2027 capex guidance of $5 billion no longer reflects the plan we expect.")
        assert claims == ()

    def test_new_guidance_with_its_previous_estimate_is_one_claim_and_one_stated_prior(self):
        """The GOOGL shape. The new range is the claim; the previous one
        is evidence Stage 2.1 reads from the same sentence."""
        for sentence in (
            "We are updating our full year 2027 CapEx guidance range to $195 billion to $205 billion, up from "
            "our previous estimate of $180 billion to $190 billion.",
            "We are updating our full year 2027 CapEx guidance range to $195 billion to $205 billion up from "
            "our previous estimate of $180 billion to $190 billion.",
        ):
            claims, _ = claims_for(sentence)
            assert as_facts(claims) == {span(ClaimSubject.CAPITAL_EXPENDITURE, 195 * B, 205 * B)}
            (revision,), _ = detect_revisions(claims)
            assert revision.revision_type is RevisionType.RAISED
            assert [e.basis for e in revision.evidence] == [RevisionBasis.PRIOR_VALUE_STATED_IN_SAME_SOURCE]
            assert (revision.evidence[0].prior_value_low, revision.evidence[0].prior_value_high) == (180 * B, 190 * B)

    def test_a_cited_range_ahead_of_the_new_one_is_skipped_whole(self):
        claims, _ = claims_for(
            "Against our previous estimate of $180 billion to $190 billion we now expect 2027 capex of $195 "
            "billion to $205 billion."
        )
        assert as_facts(claims) == {span(ClaimSubject.CAPITAL_EXPENDITURE, 195 * B, 205 * B)}

    def test_guidance_raised_from_an_old_figure_issues_the_new_one(self):
        claims, _ = claims_for("We are raising our 2027 revenue guidance from $9 billion to $10 billion.")
        assert as_facts(claims) == {point(ClaimSubject.REVENUE, 10 * B)}

    def test_guidance_raised_from_an_old_range_issues_the_new_range(self):
        claims, _ = claims_for(
            "We are raising our 2027 revenue guidance range from $10.0 billion-$10.5 billion to $11.0 "
            "billion-$11.5 billion."
        )
        assert as_facts(claims) == {span(ClaimSubject.REVENUE, 11 * B, 11.5 * B)}

    def test_a_comparison_with_a_historical_value_keeps_the_current_figure_and_year(self):
        claims, _ = claims_for("We expect 2027 revenue of $10 billion compared with $8 billion in 2025.")
        assert as_facts(claims) == {point(ClaimSubject.REVENUE, 10 * B)}

    def test_a_baseline_year_is_never_the_horizon_of_the_new_figure(self):
        claims, _ = claims_for("We expect revenue to grow from 2025 levels to $12 billion in 2027.")
        assert [c.horizon_period for c in claims] == ["2027"]
