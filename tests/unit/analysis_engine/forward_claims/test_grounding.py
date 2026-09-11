"""Forward-Looking Evidence, Stage 1.1 -- claim grounding.

A claim is three operands -- what is guided (subject), how much
(value) and for when (horizon) -- and it is only a claim if all three
belong to the same local proposition. Four quarters of real transcripts
showed the extractor finding each operand somewhere in a sentence and
combining them regardless of which clause each one came from.

Every sentence in the first two classes is verbatim from the persisted
corpus, so the tests pin the real grammar Atlas has to handle rather
than a paraphrase of it.
"""
from datetime import date, datetime, timezone

import pytest

from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.forward_claims import (
    ClaimBound,
    ClaimRejectionReason,
    ClaimSubject,
    HorizonKind,
    extract_forward_claims,
)
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

EVALUATED_AT = datetime(2026, 9, 9, tzinfo=timezone.utc)
EXTRACTED_AT = datetime(2026, 9, 10, tzinfo=timezone.utc)
CFO = "Chief Financial Officer"


def claims_for(content: str, *, company: str = "TEST", period_end: date = date(2025, 9, 30), title: str = CFO):
    result = ingest(
        build_raw_document(
            identifier=f"{company}:transcript:{period_end.year}Q{(period_end.month - 1) // 3 + 1}:0",
            company=company,
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
    return {
        (c.subject, c.horizon_period, c.horizon_kind, c.bound, c.value_low, c.value_high)
        for c in claims
    }


# --- the three false claims deep history exposed -----------------------------

#: VST, 2025Q4 call. The $3 billion is capital returned to shareholders;
#: "adjusted EBITDA" appears only in the closing clause, and only as half
#: of a leverage ratio.
VST_CAPITAL_RETURN = (
    "Even after allocating approximately $3 billion to our equity holders through share repurchases and "
    "common and preferred dividends in 2026 and 2027 and approximately $4 billion towards accretive growth "
    "investments, including the Cogentrix acquisition, the development of the Permian gas units and the PJM "
    "nuclear uprates supported by PPAs with Meta, we still expect to have more than $3 billion of additional "
    "capital available to allocate through year-end 2027, all while achieving an attractive net debt to "
    "adjusted EBITDA ratio of approximately 2.3x by year-end 2027."
)

#: TSLA, 2025Q3 call. The $9 billion is "for the current year"; 2026 sits
#: in a different clause with no figure at all.
TSLA_CURRENT_YEAR = (
    "On the CapEx front, while we are expecting to be around $9 billion for the current year, we're "
    "projecting the numbers to increase substantially in 2026 as we prepare the company for the next phase "
    "of growth in terms of not just our existing businesses, but our bets around AI initiatives, including "
    "Optimus."
)

#: AMD, 2025Q3 call. Guidance for one quarter, not the year.
AMD_FOURTH_QUARTER = (
    "For the fourth quarter of 2025, we expect revenue to be approximately $9.6 billion, plus or minus "
    "$300 million."
)


class TestTheThreeRealFalseClaims:
    """Each of these produced a claim before Stage 1.1. None of them
    contains a claim at all."""

    def test_capital_returned_to_shareholders_is_not_adjusted_ebitda_guidance(self):
        claims, _ = claims_for(VST_CAPITAL_RETURN, company="VST", period_end=date(2025, 12, 31))
        assert claims == ()

    def test_a_current_year_figure_does_not_inherit_a_year_from_another_clause(self):
        claims, _ = claims_for(TSLA_CURRENT_YEAR, company="TSLA")
        assert claims == ()

    def test_a_quarter_qualified_year_is_not_a_full_year_horizon(self):
        claims, _ = claims_for(AMD_FOURTH_QUARTER, company="AMD")
        assert claims == ()


# --- the true claims that must survive ---------------------------------------

B = 1e9
TRUE_POSITIVES = [
    pytest.param(
        "Turning to slide nine, we are reaffirming our 2026 Adjusted EBITDA guidance range of $6.8 billion-$7.6 "
        "billion and our adjusted free cash flow before growth guidance range of $3.925 billion-$4.725 billion.",
        date(2026, 6, 30),
        {(ClaimSubject.ADJUSTED_EBITDA, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 6.8 * B, 7.6 * B),
         (ClaimSubject.FREE_CASH_FLOW, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 3.925 * B, 4.725 * B)},
        id="VST-2026Q2-two-measures-one-year",
    ),
    pytest.param(
        "We are introducing guidance ranges for 2026 adjusted EBITDA of $6.8 billion to $7.6 billion and adjusted "
        "free cash flow before growth of $3.925 billion to $4.725 billion, including the expected contribution "
        "from the assets acquired from Lotus Infrastructure Partners.",
        date(2025, 9, 30),
        {(ClaimSubject.ADJUSTED_EBITDA, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 6.8 * B, 7.6 * B),
         (ClaimSubject.FREE_CASH_FLOW, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 3.925 * B, 4.725 * B)},
        id="VST-2025Q3-original-2026-guidance",
    ),
    pytest.param(
        "Combined with our results year-to-date, we are narrowing our guidance range for 2025 adjusted EBITDA to "
        "$5.7 billion to $5.9 billion, and our 2025 adjusted free cash flow before growth to $3.3 billion to "
        "$3.5 billion.",
        date(2025, 9, 30),
        {(ClaimSubject.ADJUSTED_EBITDA, "2025", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 5.7 * B, 5.9 * B),
         (ClaimSubject.FREE_CASH_FLOW, "2025", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 3.3 * B, 3.5 * B)},
        id="VST-2025Q3-two-clauses-each-grounded",
    ),
    pytest.param(
        "For the full year 2026, we expect CapEx to be in the range of $175 billion to $185 billion with "
        "investments ramping over the course of the year.",
        date(2025, 12, 31),
        {(ClaimSubject.CAPITAL_EXPENDITURE, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 175 * B, 185 * B)},
        id="GOOGL-2025Q4-fronted-year",
    ),
    pytest.param(
        "We are updating our full year 2026 CapEx guidance range to $180 billion to $190 billion, up from our "
        "previous estimate of $175 billion to $185 billion to now include investment related to the acquisition "
        "of Intersect, which closed in March.",
        date(2026, 3, 31),
        {(ClaimSubject.CAPITAL_EXPENDITURE, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 180 * B, 190 * B)},
        id="GOOGL-2026Q1",
    ),
    pytest.param(
        "We are updating our full year 2026 CapEx guidance range to $195 billion to $205 billion, up from our "
        "previous estimate of $180 billion to $190 billion.",
        date(2026, 6, 30),
        {(ClaimSubject.CAPITAL_EXPENDITURE, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 195 * B, 205 * B)},
        id="GOOGL-2026Q2",
    ),
    pytest.param(
        "Guidance: we raised fiscal year 2026 revenue guidance to $41.0 billion to $41.3 billion, increasing the "
        "high end by $400 million driven by foreign exchange tailwinds.",
        date(2026, 3, 31),
        {(ClaimSubject.REVENUE, "2026", HorizonKind.FISCAL_YEAR, ClaimBound.RANGE, 41.0 * B, 41.3 * B)},
        id="CRM-2026Q1",
    ),
    pytest.param(
        "We are pleased to raise the low end of our fiscal year 2026 revenue guidance to $41.1 billion to $41.3 "
        "billion, resulting in growth of approximately 8.5% to 9% year over year in nominal and 8% in constant "
        "currency.",
        date(2026, 6, 30),
        {(ClaimSubject.REVENUE, "2026", HorizonKind.FISCAL_YEAR, ClaimBound.RANGE, 41.1 * B, 41.3 * B)},
        id="CRM-2026Q2",
    ),
    pytest.param(
        "Finally, to close on the numbers: as mentioned at Capital Market Day, we expect 2030 to see an "
        "opportunity for revenue between €44 billion and €60 billion and a gross margin between 56-60%.",
        date(2025, 9, 30),
        {(ClaimSubject.REVENUE, "2030", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.RANGE, 44 * B, 60 * B)},
        id="ASML-2025Q3",
    ),
]


class TestEveryValidatedTrueClaimSurvives:
    """The nine real sentences behind the twelve manually validated true
    claims. Precision bought by rejecting these would be no repair."""

    @pytest.mark.parametrize("sentence,period_end,expected", TRUE_POSITIVES)
    def test_the_real_sentence_still_yields_exactly_its_claims(self, sentence, period_end, expected):
        claims, _ = claims_for(sentence, period_end=period_end)
        assert as_facts(claims) == expected

    def test_the_twelve_true_claims_are_all_accounted_for(self):
        assert sum(len(p.values[2]) for p in TRUE_POSITIVES) == 12


class TestWhyTheThreeAreRejected:
    """The reason is diagnostic output, but it should say what actually
    went wrong rather than a generic miss."""

    def test_the_capital_return_sentence_names_adjusted_ebitda_only_inside_a_ratio(self):
        _, rejected = claims_for(VST_CAPITAL_RETURN, company="VST", period_end=date(2025, 12, 31))
        assert [r.reason for r in rejected] == [ClaimRejectionReason.NO_KNOWN_SUBJECT]

    def test_the_current_year_figure_has_no_year_of_its_own(self):
        _, rejected = claims_for(TSLA_CURRENT_YEAR, company="TSLA")
        assert [r.reason for r in rejected] == [ClaimRejectionReason.UNGROUNDED_OPERANDS]

    def test_the_fourth_quarter_figure_is_sub_annual(self):
        _, rejected = claims_for(AMD_FOURTH_QUARTER, company="AMD")
        assert [r.reason for r in rejected] == [ClaimRejectionReason.SUB_ANNUAL_HORIZON]


class TestOperandsNeverCrossAClause:
    """Generic sentences, one hazard each. The invariant: a number cannot
    borrow a subject or a year from an unrelated clause merely because
    they share a sentence."""

    def test_a_figure_does_not_borrow_a_year_from_a_qualitative_clause(self):
        claims, _ = claims_for("We expect capex of around $9 billion this year, and a substantial increase in 2027.")
        assert claims == ()

    def test_a_figure_does_not_borrow_a_subject_from_a_fronted_topic(self):
        claims, _ = claims_for("On revenue, we expect $10 billion to $10.5 billion in 2027.")
        assert claims == ()

    def test_a_figure_does_not_borrow_a_year_from_a_later_clause(self):
        claims, _ = claims_for("We expect revenue of about $10 billion, and we will set 2027 guidance in March.")
        assert claims == ()

    def test_a_year_in_a_subordinate_clause_is_not_the_figures_year(self):
        claims, _ = claims_for("We expect capex of about $4 billion while the 2027 program ramps.")
        assert claims == ()

    def test_multiple_figures_in_one_clause_take_the_first_as_before(self):
        claims, _ = claims_for("We expect revenue of $10 billion in 2027, up from $9 billion.")
        assert as_facts(claims) == {(ClaimSubject.REVENUE, "2027", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.POINT, 10 * B, 10 * B)}

    def test_multiple_years_in_one_clause_keep_the_earliest_as_before(self):
        claims, _ = claims_for("We expect capex of $5 billion in 2027 and 2028.")
        assert [c.horizon_period for c in claims] == ["2027"]

    def test_a_figure_that_precedes_two_measures_is_not_paired_by_guesswork(self):
        claims, rejected = claims_for("We expect $10 billion of revenue and $2 billion of capex in 2027.")
        assert claims == ()
        assert [r.reason for r in rejected] == [ClaimRejectionReason.UNGROUNDED_OPERANDS]

    def test_a_historical_result_beside_guidance_never_becomes_the_guidance(self):
        claims, _ = claims_for("Revenue was $9 billion this quarter, and we expect revenue of $10 billion in 2027.")
        assert all(c.value_low != 9 * B for c in claims)

    def test_a_comma_inside_a_number_is_not_a_clause_boundary(self):
        claims, _ = claims_for("We expect capex of $1,500 million in 2027.")
        assert [(c.value_low, c.horizon_period) for c in claims] == [(1.5e9, "2027")]


class TestDerivedMeasures:
    def test_capital_return_beside_a_leverage_ratio_in_the_same_clause_is_not_ebitda(self):
        """Clause grounding alone would not catch this: the figure, the
        year and "adjusted EBITDA" share one clause. The ratio is a
        different measure."""
        claims, _ = claims_for(
            "We expect to return $3 billion to shareholders in 2027 at a net debt to adjusted EBITDA ratio of 2.5x."
        )
        assert claims == ()

    def test_a_margin_is_not_the_measure_it_is_a_margin_of(self):
        claims, _ = claims_for("We expect free cash flow margin of about 20% on revenue of $10 billion in 2027.")
        assert as_facts(claims) == {(ClaimSubject.REVENUE, "2027", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.POINT, 10 * B, 10 * B)}

    def test_a_per_unit_figure_is_not_the_measure(self):
        claims, _ = claims_for("We expect revenue per gigawatt of about $10 billion in 2027.")
        assert claims == ()


class TestSubAnnualPeriods:
    @pytest.mark.parametrize(
        "sentence",
        [
            "We expect Q4 2026 revenue of approximately $3 billion.",
            "We expect fourth-quarter 2026 revenue of approximately $3 billion.",
            "We expect revenue of approximately $3 billion in the second half of 2026.",
            "We expect fiscal 2026 third quarter revenue of approximately $3 billion.",
        ],
    )
    def test_a_quarter_or_half_is_never_filed_as_a_year(self, sentence):
        claims, rejected = claims_for(sentence)
        assert claims == ()
        assert [r.reason for r in rejected] == [ClaimRejectionReason.SUB_ANNUAL_HORIZON]

    def test_a_quarterly_figure_does_not_bind_to_annual_language_in_another_clause(self):
        claims, _ = claims_for(
            "For the fourth quarter of 2026, we expect revenue of approximately $3 billion, and for the full year "
            "2026 we expect revenue of approximately $11 billion."
        )
        assert as_facts(claims) == {(ClaimSubject.REVENUE, "2026", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.POINT, 11 * B, 11 * B)}


class TestGenuineMultiClaimSentencesSurvive:
    """Precision is not bought with a one-claim-per-sentence rule."""

    def test_two_measures_coordinated_under_one_year_both_survive(self):
        claims, _ = claims_for("We expect 2027 revenue of $10 billion and capex of $2 billion.")
        assert as_facts(claims) == {
            (ClaimSubject.REVENUE, "2027", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.POINT, 10 * B, 10 * B),
            (ClaimSubject.CAPITAL_EXPENDITURE, "2027", HorizonKind.UNSPECIFIED_YEAR, ClaimBound.POINT, 2 * B, 2 * B),
        }

    def test_two_claims_in_separate_clauses_each_with_their_own_operands_survive(self):
        claims, _ = claims_for("We expect 2027 revenue of $10 billion, and 2027 capex of $2 billion.")
        assert {c.subject for c in claims} == {ClaimSubject.REVENUE, ClaimSubject.CAPITAL_EXPENDITURE}

    def test_a_fronted_year_frames_only_the_clause_it_introduces(self):
        claims, _ = claims_for("For 2027, we expect revenue growth to accelerate, and capex of $5 billion.")
        assert claims == ()

    def test_a_fronted_phrase_that_names_a_measure_is_not_a_year_frame(self):
        claims, _ = claims_for("On the CapEx front for 2027, we expect around $9 billion.")
        assert claims == ()
