"""Forward-Looking Evidence, Stage 5.1 -- executed customer commitments.

The sentences are verbatim from persisted earnings-call transcripts
(company, fiscal quarter of the call). The boundary under test is the one
between a commitment that exists and every way of talking about one that
does not.
"""
from __future__ import annotations

import dataclasses

import pytest

from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims import ForwardEconomicSignal
from atlas.analysis_engine.forward_claims.commitments import (
    CommitmentKind,
    CommitmentStatus,
    CommitmentStatusReading,
    CommitmentTerm,
    CommitmentWindow,
    CommittedQuantity,
    CustomerCommitmentClaim,
    read_commitment_status,
)
from atlas.analysis_engine.forward_claims.contracts import ClaimBound, ClaimantRole, HorizonKind

# VST 2025Q4 -- AWS and Meta in one sentence, with the 3.8 GW total they add up to.
VST_CONTRACTED = (
    "We have now contracted approximately 3.8 gigawatts of nuclear capacity through multiple power purchase "
    "agreements, including a 20-year agreement with Amazon Web Services for 1,200 megawatts at our Comanche Peak "
    "nuclear power plant in Texas and 20-year agreements with Meta covering 2,176 megawatts of operating capacity "
    "and an additional 433 megawatts of upgrades at our PJM nuclear plants, the largest nuclear operation supported "
    "by a corporate customer in the United States."
)
# VST 2025Q4 -- the same AWS agreement, restated.
VST_AMAZON_CONTRACT = (
    "The first agreement, which we announced in September last year, is a 20-year contract with Amazon at our "
    "Comanche Peak nuclear plant in Texas."
)
# VST 2025Q4 and 2026Q1 -- the negative control: megawatts, sites, "contracted", and no commitment.
VST_OPPORTUNITY = (
    "We still see an opportunity to contract up to an additional 3.2 gigawatts of nuclear capacity across our "
    "Beaver Valley and Comanche Peak sites, including potential upgrades of approximately 200 megawatts at "
    "Comanche Peak."
)
VST_OPPORTUNITY_RESTATED = (
    "As I already mentioned, we still see an approximately 3.2 gigawatts of opportunities at Beaver Valley and "
    "Comanche Peak that can be contracted on a long-term basis."
)
VST_PRIORITIES = (
    "Our near-term priorities include approximately 3.2 gigawatts of nuclear capacity at Beaver Valley and "
    "Comanche Peak that can be contracted on a long-term basis and ongoing opportunities with customers with "
    "respect to our existing gas plants as well as potential new construction."
)
# VST 2025Q4 -- the Meta terms, stated by reference to the previous sentence.
VST_META_BY_REFERENCE = (
    "The agreements, which are also for 20 years, cover 2,176 megawatts of operating capacity from our Perry and "
    "Davis-Besse nuclear power plants and an additional 433 megawatts of upgrade capacity from our Perry, "
    "Davis-Besse and Beaver Valley power plants."
)
VST_META_ANNOUNCED = (
    "Building on that momentum, in January of this year, we announced long-term power purchase agreements with Meta."
)
# VST 2025Q3 -- the AWS agreement on the call after it was signed: no customer named, terms by reference.
VST_AWS_2025Q3 = (
    "We believe this 20-year agreement, which enables our customer to energize up to 1,200 megawatts of new load "
    "ensures the Comanche Peak nuclear plant will continue to deliver power to Texans at least through the middle "
    "of this century."
)
# VST 2026Q1 -- Meta PPAs and an acquisition under one verb.
VST_ACQUISITION_AND_PPA = (
    "As outlined on our year-end call, within the first week of the year, we announced the acquisition of the "
    "5,500-megawatt Cogentrix natural gas generation portfolio as well as long-term power purchase agreements with "
    "Meta for approximately 2,600 megawatts of energy and capacity at our PJM nuclear sites."
)
VST_ACQUISITION = (
    "Building on the Lotus transaction, we recently announced our agreement to acquire Cogentrix Energy, which "
    "includes 10 modern natural gas generation facilities totaling approximately 5,500 megawatts of capacity, "
    "including 2 plants, Patriot and Hamilton-Liberty that were completed in 2016 with heat rates well below 7,000."
)
VST_DEBT = (
    "With this milestone, the fallaway provisions in our senior secured debt agreements were triggered, releasing "
    "the liens on our assets under those documents."
)
VST_AGGREGATE = (
    "We have now signed approximately 3.8 gigawatts of nuclear capacity, including uprates under long-term "
    "contracts, more than any other power company in the country."
)
VST_EXISTENCE_ONLY = (
    "We successfully executed the Oak Hill solar PPA with Amazon and the Pulaski project with Microsoft, which "
    "establishes strong existing relationships."
)
VST_PARTNER = (
    "Second, Vistra will serve as the preferred power partner, allowing us to participate in Helix development "
    "projects either through contracted new build projects or through new contracts with existing assets."
)
VST_DISCUSSIONS = (
    "Yes, they are willing to and are engaging in discussions about bilateral contracts even ahead of the rules "
    "for the backstop procurement being clarified."
)
VST_WHEN_READY = "And when they're ready to sign PPAs, projects can move forward."
# AMD 2025Q3 and 2026Q2.
AMD_OPENAI = (
    "On the customer front, we announced a comprehensive multiyear agreement with OpenAI to deploy 6 gigawatts of "
    "Instinct GPUs with the first gigawatt of MI450 Series accelerators scheduled to start coming online in the "
    "second half of 2026."
)
AMD_ANTHROPIC_PARTNERSHIP = (
    "In addition to our multi-generation gigawatt scale deployments with OpenAI and Meta, we announced a new "
    "strategic partnership with Anthropic."
)
AMD_ANTHROPIC_QUANTITY = (
    "Anthropic will deploy up to 2 gigawatts of MI450 series GPUs in Helios with deployment of the first gigawatt "
    "beginning in the first half of 2027."
)
# MU 2025Q4, 2026Q1, 2026Q2.
MU_SCA = "We are excited to have signed our first five-year SCA."
MU_HBM_2026 = (
    "We have completed agreements on price and volume for our entire calendar 2026 HBM supply, including Micron's "
    "industry-leading HBM4."
)
MU_EXPECT_TO_CONCLUDE = (
    "We are in active discussions with customers on the specifications and volumes for HBM four, and we expect to "
    "conclude agreements to sell out the remainder of our total HPM calendar 2026 supply in the coming months."
)
MU_IF_AND_WHEN = "If and when we complete these agreements and as appropriate, we will, of course, share further details with you."
# GOOGL 2026Q2 -- agreements that exist, with nothing committed stated.
GOOGL_TPU = (
    "We continue to expect to recognize a relatively small portion of the revenues from our existing TPU system "
    "sales agreements this year, ramping as we exit 2026."
)
# SU 2026Q2, CRM 2026Q1, TSLA 2026Q2.
SU_MOU = (
    "For those that aren't as familiar: about a month ago five oilsands companies signed a non-binding MoU with the "
    "federal and provincial governments."
)
CRM_ACQUISITION = "I'm excited that we have signed a definitive agreement to acquire Informatica for $8 billion."
TSLA_FRAMEWORK = "Earlier this year, we deepened our relationship through an investment and a framework agreement."

EXEC = dict(claimant_role=ClaimantRole.EXECUTIVE, stated_by="James Burke", stated_by_title="President and Chief Executive Officer")


def quantity(value, unit, value_text, measure_text, bound=ClaimBound.POINT):
    return CommittedQuantity(bound, value, value, unit, value_text, measure_text)


def claim(source_text=VST_CONTRACTED, **overrides) -> CustomerCommitmentClaim:
    fields = dict(
        company="VST",
        commitment_kind=CommitmentKind.POWER_PURCHASE,
        counterparty_text="Amazon Web Services",
        agreement_text="20-year agreement",
        execution_text="have now contracted",
        commitment_text=source_text,
        quantities=(quantity(1200, "MW", "1,200 megawatts", None),),
        term=CommitmentTerm(20, "20-year"),
        window=None,
        source_record_id="rec-vst-2025Q4-1",
        source_kind=SourceKind.TRANSCRIPT,
        source_text=source_text,
        source_period="2025Q4",
        statement_at=None,
        extractor_version="stage-5.1-audit",
        **EXEC,
    )
    fields.update(overrides)
    return CustomerCommitmentClaim(**fields)


def meta() -> CustomerCommitmentClaim:
    return claim(
        counterparty_text="Meta",
        agreement_text="20-year agreements",
        quantities=(
            quantity(2176, "MW", "2,176 megawatts", "of operating capacity"),
            quantity(433, "MW", "433 megawatts", "of upgrades"),
        ),
    )


def openai() -> CustomerCommitmentClaim:
    return claim(
        AMD_OPENAI,
        company="AMD",
        commitment_kind=CommitmentKind.PRODUCT_SUPPLY,
        counterparty_text="OpenAI",
        agreement_text="comprehensive multiyear agreement",
        execution_text="we announced",
        quantities=(quantity(6, "GW", "6 gigawatts", "of Instinct GPUs"),),
        term=None,
        window=CommitmentWindow(2026, None, HorizonKind.UNSPECIFIED_YEAR, "start coming online in the second half of 2026"),
        source_period="2025Q3",
    )


class TestPositiveControls:
    def test_1_vst_aws_is_an_executed_1200_mw_20_year_commitment(self):
        c = claim()
        assert (c.company, c.commitment_kind, c.counterparty_text) == ("VST", CommitmentKind.POWER_PURCHASE, "Amazon Web Services")
        assert [(q.value_low, q.unit, q.measure_text) for q in c.quantities] == [(1200, "MW", None)]
        assert c.term == CommitmentTerm(20, "20-year")
        assert c.source_period == "2025Q4"
        assert c.execution_text == "have now contracted"

    def test_1b_the_restated_aws_contract_carries_only_what_it_states(self):
        c = claim(VST_AMAZON_CONTRACT, counterparty_text="Amazon", agreement_text="20-year contract",
                  execution_text="we announced", quantities=())
        assert c.quantities == () and c.term.years == 20 and c.window is None

    def test_2_vst_meta_is_one_group_of_agreements_with_two_unsummed_components(self):
        c = meta()
        assert c.agreement_text == "20-year agreements"
        assert [(q.value_low, q.measure_text) for q in c.quantities] == [
            (2176, "of operating capacity"), (433, "of upgrades"),
        ]
        assert not any(q.value_low in (2609, 3800) for q in c.quantities)

    def test_9_amd_openai_is_a_product_supply_commitment_counted_in_gpus_not_capacity(self):
        c = openai()
        assert c.commitment_kind is CommitmentKind.PRODUCT_SUPPLY
        assert c.quantities[0].measure_text == "of Instinct GPUs"
        assert c.term is None, "'multiyear' states no number of years"
        assert (c.window.start_year, c.window.end_year) == (2026, None)

    def test_a_gigawatt_of_gpus_and_a_gigawatt_of_capacity_never_share_a_comparison(self):
        assert openai().comparison_key[1] is not claim().comparison_key[1]


class TestNegativeControls:
    @pytest.mark.parametrize("sentence", [VST_OPPORTUNITY, VST_OPPORTUNITY_RESTATED, VST_PRIORITIES])
    def test_3_the_vst_3_2_gw_opportunity_is_never_a_commitment(self, sentence):
        assert read_commitment_status(sentence).status is CommitmentStatus.OPPORTUNITY
        with pytest.raises(ValueError, match="opportunity"):
            claim(sentence, counterparty_text=None, agreement_text="contracted",
                  quantities=(quantity(3.2, "GW", "3.2 gigawatts", "of nuclear capacity"),), term=None)

    def test_4_pipeline_is_not_a_commitment(self):
        reading = read_commitment_status("We have signed a strong pipeline of contracts for 2 gigawatts of capacity.")
        assert reading.status is CommitmentStatus.OPPORTUNITY

    @pytest.mark.parametrize("sentence", [VST_DISCUSSIONS, MU_EXPECT_TO_CONCLUDE])
    def test_5_discussions_are_not_a_commitment(self, sentence):
        assert read_commitment_status(sentence).status is CommitmentStatus.IN_DISCUSSION

    @pytest.mark.parametrize("sentence", [VST_WHEN_READY, MU_IF_AND_WHEN])
    def test_future_and_conditional_agreements_are_expected_not_executed(self, sentence):
        assert read_commitment_status(sentence).status is CommitmentStatus.EXPECTED

    def test_6_a_signed_mou_is_non_definitive_whatever_the_verb(self):
        assert read_commitment_status(SU_MOU) == CommitmentStatusReading(CommitmentStatus.NON_DEFINITIVE, "non-binding")

    def test_a_framework_agreement_is_non_definitive(self):
        assert read_commitment_status(TSLA_FRAMEWORK).status is CommitmentStatus.NON_DEFINITIVE

    @pytest.mark.parametrize("sentence", [VST_PARTNER, AMD_ANTHROPIC_PARTNERSHIP])
    def test_8_a_partnership_is_not_a_commitment(self, sentence):
        assert read_commitment_status(sentence).status is CommitmentStatus.PARTNERSHIP_ONLY

    def test_8b_the_anthropic_quantity_cannot_borrow_a_status_from_its_neighbour(self):
        assert read_commitment_status(AMD_ANTHROPIC_QUANTITY).status is CommitmentStatus.UNKNOWN
        with pytest.raises(ValueError):
            claim(AMD_ANTHROPIC_QUANTITY, company="AMD", commitment_kind=CommitmentKind.PRODUCT_SUPPLY,
                  counterparty_text="Anthropic", agreement_text="strategic partnership", execution_text="we announced",
                  quantities=(quantity(2, "GW", "2 gigawatts", "of MI450 series GPUs", ClaimBound.UPPER_BOUND),), term=None)

    @pytest.mark.parametrize("sentence", [VST_ACQUISITION, CRM_ACQUISITION, VST_DEBT])
    def test_acquisition_and_debt_agreements_are_not_customer_commitments(self, sentence):
        """Signed, definitive, with megawatts or dollars -- and the wrong concept."""
        assert read_commitment_status(sentence).status is CommitmentStatus.NOT_A_CUSTOMER_COMMITMENT

    def test_a_ppa_sharing_a_verb_with_an_acquisition_is_not_read_at_all(self):
        assert read_commitment_status(VST_ACQUISITION_AND_PPA).status is CommitmentStatus.NOT_A_CUSTOMER_COMMITMENT

    @pytest.mark.parametrize("sentence", [VST_META_BY_REFERENCE, VST_AWS_2025Q3])
    def test_terms_stated_by_reference_are_not_a_claim(self, sentence):
        assert read_commitment_status(sentence).status is CommitmentStatus.UNKNOWN
        with pytest.raises(ValueError, match="unknown"):
            claim(sentence, counterparty_text=None, agreement_text="agreement", execution_text="", term=None, quantities=())

    def test_negation_blocks_execution(self):
        assert read_commitment_status("We have not signed a power purchase agreement for the site.").status is not CommitmentStatus.EXECUTED

    def test_an_analyst_cannot_state_the_companys_commitment(self):
        with pytest.raises(ValueError, match="insider"):
            claim(claimant_role=ClaimantRole.ANALYST)


class TestSupplyAndThinEvidence:
    def test_7_a_locally_stated_signed_supply_agreement_is_representable(self):
        sentence = "We have signed a five-year supply agreement with a large customer."
        c = claim(sentence, company="MU", commitment_kind=CommitmentKind.PRODUCT_SUPPLY, counterparty_text=None,
                  agreement_text="five-year supply agreement", execution_text="have signed", quantities=(),
                  term=CommitmentTerm(5, "five-year"))
        assert c.term.years == 5 and c.quantities == () and c.comparison_key is None

    def test_10_mu_five_year_sca_needs_the_acronym_defined_two_sentences_earlier(self):
        """"SCA" is an agreement only because an earlier sentence says
        so. Pinned as the limitation it is, not worked around with an
        issuer's own vocabulary."""
        assert read_commitment_status(MU_SCA).status is CommitmentStatus.UNKNOWN

    def test_10b_mu_2026_hbm_agreements_are_a_position_across_customers_not_one_commitment(self):
        assert read_commitment_status(MU_HBM_2026).status is CommitmentStatus.EXECUTED
        with pytest.raises(ValueError, match="contracted position"):
            claim(MU_HBM_2026, company="MU", commitment_kind=CommitmentKind.PRODUCT_SUPPLY, counterparty_text=None,
                  agreement_text="agreements on price and volume", execution_text="have completed", quantities=(),
                  term=None, window=CommitmentWindow(2026, 2026, HorizonKind.CALENDAR_YEAR, "calendar 2026"))

    def test_the_vst_3_8_gw_total_is_a_position_not_a_commitment(self):
        with pytest.raises(ValueError, match="contracted position"):
            claim(VST_AGGREGATE, counterparty_text=None, agreement_text="long-term contracts", execution_text="have now signed",
                  quantities=(quantity(3.8, "GW", "3.8 gigawatts", "of nuclear capacity"),), term=None)

    def test_googl_tpu_agreements_state_nothing_committed(self):
        assert read_commitment_status(GOOGL_TPU).status is CommitmentStatus.UNKNOWN

    def test_an_agreement_that_only_exists_is_not_enough(self):
        with pytest.raises(ValueError, match="at least"):
            claim(VST_EXISTENCE_ONLY, counterparty_text="Amazon", agreement_text="Oak Hill solar PPA",
                  execution_text="We successfully executed", quantities=(), term=None)
        with pytest.raises(ValueError, match="at least"):
            claim(VST_META_ANNOUNCED, counterparty_text="Meta", agreement_text="long-term power purchase agreements",
                  execution_text="we announced", quantities=(), term=None)


class TestShape:
    def test_11_a_named_customer_is_optional_but_must_be_stated_in_the_proposition(self):
        with pytest.raises(ValueError, match="not stated"):
            claim(counterparty_text="Google")
        assert claim(VST_AMAZON_CONTRACT, counterparty_text="Amazon", agreement_text="20-year contract",
                     execution_text="we announced", quantities=()).counterparty_text == "Amazon"

    def test_12_capacity_and_duration_are_separate_and_years_are_not_a_quantity_unit(self):
        c = claim()
        assert "years" not in {f.name for f in dataclasses.fields(CommittedQuantity)}
        assert c.term.years == 20 and c.quantities[0].unit == "MW"
        with pytest.raises(ValueError, match="unit"):
            claim(quantities=(quantity(20, "YEARS", "20-year", "20-year"),))

    def test_13_a_multi_year_window_keeps_both_ends(self):
        sentence = "We have signed a 20-year agreement with Meta for 433 megawatts delivered from 2031 to 2034."
        def uprate(window):
            return claim(sentence, counterparty_text="Meta", execution_text="have signed", window=window,
                         quantities=(quantity(433, "MW", "433 megawatts", None),))
        c = uprate(CommitmentWindow(2031, 2034, HorizonKind.UNSPECIFIED_YEAR, "from 2031 to 2034"))
        assert (c.window.start_year, c.window.end_year) == (2031, 2034)
        with pytest.raises(ValueError, match="before it starts"):
            uprate(CommitmentWindow(2034, 2031, HorizonKind.UNSPECIFIED_YEAR, "from 2031 to 2034"))
        with pytest.raises(ValueError, match="at least one year"):
            uprate(CommitmentWindow(None, None, HorizonKind.UNSPECIFIED_YEAR, "from 2031 to 2034"))
        with pytest.raises(ValueError, match="not stated"):
            uprate(CommitmentWindow(2031, 2034, HorizonKind.UNSPECIFIED_YEAR, "2031-2034"))

    def test_14_an_unknown_start_is_left_unknown_not_derived_from_the_term(self):
        c = claim()
        assert c.window is None and c.term.years == 20

    def test_15_every_field_leads_back_to_the_verbatim_passage(self):
        c = meta()
        assert c.commitment_text in c.source_text
        for text in (c.counterparty_text, c.agreement_text, c.execution_text, *[q.value_text for q in c.quantities]):
            assert text in c.commitment_text
        assert c.id == meta().id and c.id.startswith("rec-vst-2025Q4-1:commitment:")
        assert claim().id != c.id, "two commitments in one sentence are two claims"
        with pytest.raises(ValueError, match="verbatim span"):
            claim(commitment_text="We have now contracted 5 gigawatts with Meta.")

    def test_execution_text_must_be_what_the_reading_found(self):
        with pytest.raises(ValueError, match="execution_text"):
            claim(execution_text="signed")


class TestNoEconomics:
    _TOKENS = {
        token
        for cls in (CustomerCommitmentClaim, CommittedQuantity, CommitmentTerm, CommitmentWindow)
        for field in dataclasses.fields(cls)
        for token in field.name.split("_")
    }

    def test_16_no_recommendation_vocabulary(self):
        for forbidden in ("recommendation", "conviction", "stance", "rating", "score", "thesis", "buy", "sell",
                          "trim", "verdict", "confidence"):
            assert forbidden not in self._TOKENS, forbidden
        for member in CommitmentStatus:
            assert member.value not in ("positive", "negative", "bullish", "bearish", "good", "bad")

    def test_17_no_economic_polarity_or_movement(self):
        for forbidden in ("movement", "effect", "outlook", "dimension", "polarity", "sentiment", "strengthening",
                          "raised", "lowered", "reaffirmed", "revision"):
            assert forbidden not in self._TOKENS, forbidden

    def test_18_no_revenue_earnings_price_or_currency(self):
        for forbidden in ("revenue", "earnings", "ebitda", "price", "cash", "usd", "dollars", "premium"):
            assert forbidden not in self._TOKENS, forbidden
        assert "value" not in {f.name for f in dataclasses.fields(CustomerCommitmentClaim)}
        for unit in ("USD_BILLION", "USD", "$"):
            with pytest.raises(ValueError, match="unit"):
                claim(quantities=(quantity(8, unit, "1,200 megawatts", None),))


class TestStateFirst:
    def test_19_a_first_observation_is_complete_without_any_prior_state(self):
        c = claim()
        assert not isinstance(c, ForwardEconomicSignal), "state evidence must not enter the revision-shaped synthesis"
        assert not {"prior", "previous", "old", "new", "revision"} & TestNoEconomics._TOKENS

    def test_20_the_comparison_key_survives_every_change_a_later_stage_would_detect(self):
        base = claim()
        later = claim(
            "We have now contracted 1,500 megawatts of capacity under our 20-year agreement with Amazon Web Services, "
            "with deliveries starting in 2027.",
            execution_text="have now contracted",
            quantities=(quantity(1500, "MW", "1,500 megawatts", "of capacity"),),
            window=CommitmentWindow(2027, None, HorizonKind.UNSPECIFIED_YEAR, "deliveries starting in 2027"),
            source_period="2026Q2", source_record_id="rec-vst-2026Q2-9",
        )
        assert later.comparison_key == base.comparison_key == ("VST", CommitmentKind.POWER_PURCHASE, "amazon web services")
        assert later.id != base.id, "a restatement is a new claim about the same commitment"
        restated = claim(VST_AMAZON_CONTRACT, counterparty_text="Amazon", agreement_text="20-year contract",
                         execution_text="we announced", quantities=())
        assert restated.comparison_key != base.comparison_key, "names match only as stated: a miss, never a false match"
        assert meta().comparison_key != base.comparison_key
        assert claim(company="AMD").comparison_key != base.comparison_key

    def test_no_field_a_historical_evaluator_would_recognise(self):
        """The same firewall as `ForwardClaim`: `BusinessFact` consumers
        read `.kind`, `.value` and `.period`."""
        names = {f.name for f in dataclasses.fields(CustomerCommitmentClaim)}
        assert not {"kind", "value", "period"} & names

    def test_unnamed_commitments_are_never_comparable(self):
        c = claim("We have signed a five-year supply agreement with a large customer.", counterparty_text=None,
                  commitment_kind=CommitmentKind.PRODUCT_SUPPLY, agreement_text="five-year supply agreement",
                  execution_text="have signed", quantities=(), term=CommitmentTerm(5, "five-year"))
        assert c.comparison_key is None
