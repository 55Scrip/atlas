"""Forward-Looking Evidence, Stage 5.2 -- source-local links between
commitment statements.

Real sequences are verbatim consecutive sentences of one speaker's turn in
a persisted transcript (company, fiscal quarter, statement, first sentence
index). Every link must be explainable by words the source itself uses.
"""
from __future__ import annotations

import dataclasses
import time
from datetime import date, datetime, timezone

import pytest

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.forward_claims.commitment_links import find_commitment_links, link_commitment_sentences
from atlas.analysis_engine.forward_claims.commitments import (
    LINK_WINDOW,
    CommitmentKind,
    CommitmentStatus,
    CommitmentSupport,
    CommitmentTerm,
    CommitmentWindow,
    CommittedQuantity,
    CustomerCommitmentClaim,
    SourceEvidenceLink,
    SourceLinkKind,
    read_commitment_status,
)
from atlas.analysis_engine.forward_claims.contracts import ClaimBound, ClaimantRole, HorizonKind
from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

BACK, COMPONENT, ACRONYM = (
    SourceLinkKind.EXPLICIT_BACK_REFERENCE, SourceLinkKind.COMPONENT_REFERENCE, SourceLinkKind.ACRONYM_DEFINITION,
)

# VST 2025Q3, statement 2, sentences 17-19.
VST_AWS_2025Q3 = (
    "While multiple drivers of gross margin variability remain, including the 2027, 2028 PJM capacity auction, our hedge "
    "percentage, which currently sits at approximately 70% of expected generation, provides line of sight to our adjusted "
    "EBITDA midpoint opportunity.",
    "Finally, the recently announced power purchase agreement at Comanche Peak marks a major milestone for our company, "
    "for our site and for Texas.",
    "We believe this 20-year agreement, which enables our customer to energize up to 1,200 megawatts of new load ensures "
    "the Comanche Peak nuclear plant will continue to deliver power to Texans at least through the middle of this century.",
)
# VST 2025Q4, statement 1, sentences 70-82.
VST_NUCLEAR_2025Q4 = (
    "Our nuclear power purchase agreements represent a significant milestone, not just for Vistra, but for the industry.",
    "We have now signed approximately 3.8 gigawatts of nuclear capacity, including uprates under long-term contracts, "
    "more than any other power company in the country.",
    "These agreements executed with 2 of the world's leading technology companies represent meaningful long-term "
    "commitments to the safe and reliable operation of nuclear power generation in the United States.",
    "The first agreement, which we announced in September last year, is a 20-year contract with Amazon at our Comanche "
    "Peak nuclear plant in Texas.",
    "Under this agreement, Amazon will site a facility on our property to utilize the 1,200 megawatts of capacity.",
    "Importantly, Amazon also plans to bring one-for-one backup generation, a structure we believe supports future "
    "expansion at the site while maintaining reliability across the system.",
    "Progress on the site continues to be made, with initial energization still expected in the fourth quarter of 2027 "
    "and full ramp expected by the fourth quarter of 2032.",
    "The agreement also includes options to explore new nuclear development with a specific focus on possible uprates "
    "and small modular reactors.",
    "We are excited about this partnership and the long-term potential at the Comanche Peak site.",
    "Building on that momentum, in January of this year, we announced long-term power purchase agreements with Meta.",
    "The agreements, which are also for 20 years, cover 2,176 megawatts of operating capacity from our Perry and "
    "Davis-Besse nuclear power plants and an additional 433 megawatts of upgrade capacity from our Perry, Davis-Besse "
    "and Beaver Valley power plants.",
    "We expect delivery of the operating capacity at Perry to commence in December of 2026 and Davis-Besse in December 2027.",
    "Uprate capacity remains longer dated, with Perry upgrades expected to be online in the fourth quarter of 2031, with "
    "each subsequent year seeing an additional upgrade online until all 4 upgrades are completed by the fourth quarter "
    "of 2034.",
)
# VST 2025Q4, statement 1, sentences 90-91 -- the opportunity, right after the agreements.
VST_OPPORTUNITY = (
    "While these agreements are important for our company, we have more we can do.",
    "We still see an opportunity to contract up to an additional 3.2 gigawatts of nuclear capacity across our Beaver "
    "Valley and Comanche Peak sites, including potential upgrades of approximately 200 megawatts at Comanche Peak.",
)
# AMD 2025Q3, statement 2, sentences 47-51.
AMD_OPENAI = (
    "On the customer front, we announced a comprehensive multiyear agreement with OpenAI to deploy 6 gigawatts of "
    "Instinct GPUs with the first gigawatt of MI450 Series accelerators scheduled to start coming online in the second "
    "half of 2026.",
    "The partnership establishes AMD as a core compute provider for OpenAI and underscores the strength of our hardware, "
    "software and full stack solution strategy.",
    "Moving forward, AMD and OpenAI will work even more closely on future hardware, software, networking and "
    "system-level road maps and technologies.",
    "OpenAI's decision to use AMD Instinct platforms for its most sophisticated and complex AI workloads sends a clear "
    "signal that our Instinct GPUs and ROCm open software stack deliver the performance and TCO required for the most "
    "demanding deployments.",
    "We expect this partnership will significantly accelerate our data center AI business with the potential to generate "
    "well over $100 billion in revenue over the next few years.",
)
# AMD 2026Q2, statement 2, sentences 28-30.
AMD_ANTHROPIC = (
    "In addition to our multi-generation gigawatt scale deployments with OpenAI and Meta, we announced a new strategic "
    "partnership with Anthropic.",
    "Anthropic will deploy up to 2 gigawatts of MI450 series GPUs in Helios with deployment of the first gigawatt "
    "beginning in the first half of 2027.",
    "The partnership includes a multiyear joint engineering collaboration using Claude to optimize workloads for "
    "Instinct GPUs and accelerate ROCm software development.",
)
# MU 2026Q2, statement 2, sentences 13-15.
MU_SCA = (
    "We continue to work with customers on strategic customer agreements, or SCAs, that are different from prior LTAs "
    "and have specific commitments over a multiyear time horizon for improved visibility and stability in our business "
    "model.",
    "These SCAs also provide customers greater certainty to plan their businesses while reinforcing long-term engagement "
    "across our broad product portfolio.",
    "We are excited to have signed our first five-year SCA.",
)
# GOOGL 2026Q2, statement 4, sentences 49-51.
GOOGL_TPU = (
    "As I mentioned earlier, we started delivering TPU systems to customer data centers in the second quarter.",
    "We continue to expect to recognize a relatively small portion of the revenues from our existing TPU system sales "
    "agreements this year, ramping as we exit 2026.",
    "We anticipate the vast majority of the revenues from these agreements will be realized in 2027.",
)


def links(sentences, record="rec") -> tuple[SourceEvidenceLink, ...]:
    return link_commitment_sentences(record, sentences)


def pairs(sentences) -> set[tuple[SourceLinkKind, int, int, int]]:
    return {(l.link_kind, l.anchor_index, l.antecedent_index, l.referring_index) for l in links(sentences)}


def record(sentences, title="President and Chief Executive Officer", speaker="James Burke") -> BusinessRecord:
    evaluated_at = datetime(2026, 9, 9, tzinfo=timezone.utc)
    result = ingest(
        build_raw_document(
            identifier="VST:transcript:2025Q4:1", company="VST", source_kind="transcript", published_at=evaluated_at,
            period_start=date(2025, 12, 31), period_end=date(2025, 12, 31),
            metadata={"quarter": "2025Q4", "statement_index": 1, "speaker": speaker, "title": title,
                      "content": " ".join(sentences)},
        ),
        evaluated_at=evaluated_at,
    )
    assert isinstance(result, IngestedRecord)
    return result.record


def Q(value, unit, text, measure=None, bound=ClaimBound.POINT):
    return CommittedQuantity(bound, value, value, unit, text, measure)


def claim(sentences, anchor, *, supports=(), **fields) -> CustomerCommitmentClaim:
    base = dict(
        company="VST", commitment_kind=CommitmentKind.POWER_PURCHASE, counterparty_text=None,
        agreement_text="agreement", quantities=(), term=None, window=None,
        claimant_role=ClaimantRole.EXECUTIVE, stated_by="James Burke", stated_by_title="President and Chief Executive Officer",
        source_record_id="rec", source_kind=SourceKind.TRANSCRIPT, source_text=sentences[anchor],
        commitment_text=sentences[anchor], source_period="2025Q4", statement_at=None, extractor_version="stage-5.2-audit",
        sentence_index=anchor, supports=supports,
    )
    base["execution_text"] = read_commitment_status(
        sentences[anchor], frozenset(s.link.reference_text for s in supports if s.link.link_kind is ACRONYM)
    ).marker_text
    base.update(fields)
    return CustomerCommitmentClaim(**base)


def link_of(sentences, kind, referring) -> SourceEvidenceLink:
    return next(l for l in links(sentences) if l.link_kind is kind and l.referring_index == referring)


class TestExplicitBackReference:
    def test_1_this_agreement_links_to_the_one_commitment_just_stated(self):
        s = ("We signed a 15-year power purchase agreement with Acme.", "This agreement covers 500 megawatts of capacity.")
        (l,) = links(s)
        assert (l.link_kind, l.antecedent_index, l.referring_index) == (BACK, 0, 1)
        assert (l.reference_text, l.antecedent_text) == ("This agreement", "We signed a 15-year power purchase agreement")

    def test_2_the_agreement_links_the_same_way(self):
        s = ("We have signed a supply agreement with Acme.", "The agreement runs for five years.")
        assert pairs(s) == {(BACK, 0, 0, 1)}

    def test_3_a_plural_reference_links_only_to_one_named_group_of_agreements(self):
        assert (BACK, 9, 9, 10) in pairs(VST_NUCLEAR_2025Q4)
        singular_anchor = ("We signed a 15-year agreement with Acme.", "The agreements cover 500 megawatts.")
        plural_anchor = ("We signed 15-year agreements with Acme.", "The agreement covers 500 megawatts.")
        assert links(singular_anchor) == () and links(plural_anchor) == ()

    def test_4_two_candidate_commitments_mean_no_link(self):
        s = ("We signed a 10-year agreement with Acme.", "We also signed a 5-year agreement with Beta.",
             "The agreement covers 500 megawatts.")
        assert not [l for l in links(s) if l.referring_index == 2]

    def test_a_sentence_naming_two_customers_cannot_be_referred_to(self):
        s = ("We have now contracted 3 gigawatts through agreements with Acme and a 20-year agreement with Beta.",
             "The agreement covers 500 megawatts.")
        assert links(s) == ()


class TestAcronyms:
    def test_5_an_acronym_defined_in_the_same_turn_makes_the_signing_readable(self):
        assert read_commitment_status(MU_SCA[2]).status is CommitmentStatus.UNKNOWN
        (l,) = links(MU_SCA)
        assert (l.link_kind, l.anchor_index, l.antecedent_index, l.referring_index) == (ACRONYM, 2, 0, 2)
        assert (l.reference_text, l.antecedent_text) == ("SCA", "strategic customer agreements, or SCAs")

    def test_6_an_acronym_defined_two_ways_binds_nothing(self):
        redefined = (MU_SCA[0], "We also sign strategic capacity agreements (SCAs) with utilities.", MU_SCA[2])
        assert links(redefined) == ()

    def test_6b_an_acronym_whose_initials_do_not_match_binds_nothing(self):
        assert links(("We work with customers on long-term supply agreements, or SCAs.", "Filler.", MU_SCA[2])) == ()

    def test_6c_an_acronym_defined_beyond_the_window_binds_nothing(self):
        assert links((MU_SCA[0], "Filler one.", "Filler two.", MU_SCA[2])) == ()

    def test_16_mu_first_five_year_sca_becomes_a_claim_only_through_its_definition(self):
        support = CommitmentSupport(link_of(MU_SCA, ACRONYM, 2))
        c = claim(MU_SCA, 2, supports=(support,), company="MU", commitment_kind=CommitmentKind.PRODUCT_SUPPLY,
                  agreement_text="five-year SCA", term=CommitmentTerm(5, "five-year"))
        assert c.term.years == 5 and c.counterparty_text is None and c.execution_text == "have signed"
        with pytest.raises(ValueError, match="unknown"):
            claim(MU_SCA, 2, supports=(), company="MU", agreement_text="five-year SCA", term=CommitmentTerm(5, "five-year"),
                  execution_text="have signed")


class TestBoundaries:
    def test_7_links_stay_inside_one_executive_turn(self):
        s = ("We signed a 15-year power purchase agreement with Acme.", "This agreement covers 500 megawatts of capacity.")
        assert [l.link_kind for l in find_commitment_links(record(s))] == [BACK]

    def test_8_an_analyst_turn_never_links(self):
        s = ("We signed a 15-year power purchase agreement with Acme.", "This agreement covers 500 megawatts of capacity.")
        assert find_commitment_links(record(s, title="Analyst", speaker="Jane Doe")) == ()

    def test_9_the_window_is_two_sentences(self):
        anchor, ref = "We signed a 15-year power purchase agreement with Acme.", "This agreement covers 500 megawatts."
        assert LINK_WINDOW == 2
        assert pairs((anchor, "Filler.", ref)) == {(BACK, 0, 0, 2)}
        assert links((anchor, "Filler.", "More filler.", ref)) == ()

    def test_22_links_point_backward_only_and_never_across_shuffled_order(self):
        s = ("We signed a 15-year power purchase agreement with Acme.", "This agreement covers 500 megawatts of capacity.")
        assert links(tuple(reversed(s))) == ()
        assert links(("This agreement covers 500 megawatts.", "Filler.")) == ()

    def test_a_link_object_cannot_point_forward_or_reach_too_far(self):
        l = links(("We signed a 15-year power purchase agreement with Acme.", "This agreement covers 500 megawatts."))[0]
        with pytest.raises(ValueError, match="backward"):
            dataclasses.replace(l, antecedent_index=1, referring_index=0)
        with pytest.raises(ValueError, match="at most"):
            dataclasses.replace(l, referring_index=3)


class TestFalseLinks:
    def test_18_a_partnership_followed_by_a_quantity_is_not_a_commitment(self):
        assert links(AMD_ANTHROPIC) == ()
        assert links(("We announced a strategic partnership with Acme.",
                      "Acme will deploy 2 gigawatts of GPUs under the agreement.")) == ()

    def test_19_an_opportunity_followed_by_a_duration_is_not_a_commitment(self):
        assert links(("We see an opportunity to contract 3.2 gigawatts.", "The contracts run for 20 years.")) == ()

    def test_19b_the_real_3_2_gw_opportunity_never_links(self):
        assert links(VST_NUCLEAR_2025Q4 + VST_OPPORTUNITY) == links(VST_NUCLEAR_2025Q4)

    @pytest.mark.parametrize("interloper", [
        "We also announced our agreement to acquire Beta.",
        "We also amended our credit agreement.",
    ])
    def test_20_an_acquisition_or_debt_agreement_in_between_blocks_the_link(self, interloper):
        s = ("We signed a 20-year power purchase agreement with Acme.", interloper, "The agreement covers 500 megawatts.")
        assert links(s) == ()

    def test_a_referring_sentence_with_its_own_status_language_never_links(self):
        s = ("We signed a 20-year power purchase agreement with Acme.", "Under this agreement, we may add 2 gigawatts.")
        assert links(s) == ()

    def test_a_new_signing_is_a_new_commitment_not_a_support(self):
        s = ("We signed a 20-year power purchase agreement with Acme.",
             "We have also signed the agreement with Beta for 300 megawatts.")
        assert links(s) == ()

    def test_a_quantity_after_a_market_demand_sentence_does_not_link(self):
        s = ("We signed a 20-year power purchase agreement with Acme.", "We expect 2 gigawatts of demand growth in ERCOT.")
        assert links(s) == ()

    def test_a_delivery_date_after_an_unrelated_project_does_not_link(self):
        s = ("We signed a 20-year power purchase agreement with Acme for 500 megawatts of operating capacity.",
             "The Permian project will be online in 2028.")
        assert links(s) == ()


class TestRealControls:
    def test_10_vst_aws_2025q3_term_and_quantity_attach_but_the_customer_stays_unnamed(self):
        assert read_commitment_status(VST_AWS_2025Q3[1]).status is CommitmentStatus.EXECUTED
        l = link_of(VST_AWS_2025Q3, BACK, 2)
        support = CommitmentSupport(l, term=CommitmentTerm(20, "20-year"),
                                    quantities=(Q(1200, "MW", "1,200 megawatts", "of new load", ClaimBound.UPPER_BOUND),))
        c = claim(VST_AWS_2025Q3, 1, supports=(support,), agreement_text="power purchase agreement", source_period="2025Q3")
        assert c.counterparty_text is None and c.comparison_key is None
        assert (c.term, c.quantities) == (None, ()), "the anchor's own terms stay empty; the neighbour's are its own"
        assert c.supports[0].term.years == 20 and c.supports[0].quantities[0].bound is ClaimBound.UPPER_BOUND
        with pytest.raises(ValueError, match="not stated in the commitment's own proposition"):
            claim(VST_AWS_2025Q3, 1, supports=(support,), agreement_text="power purchase agreement", counterparty_text="Amazon")

    def test_11_13_vst_meta_terms_and_delivery_attach_by_explicit_reference(self):
        assert pairs(VST_NUCLEAR_2025Q4) == {(BACK, 3, 3, 4), (BACK, 9, 9, 10), (COMPONENT, 9, 10, 11)}
        terms = CommitmentSupport(
            link_of(VST_NUCLEAR_2025Q4, BACK, 10), term=CommitmentTerm(20, "20 years"),
            quantities=(Q(2176, "MW", "2,176 megawatts", "of operating capacity"),
                        Q(433, "MW", "433 megawatts", "of upgrade capacity")),
        )
        delivery = link_of(VST_NUCLEAR_2025Q4, COMPONENT, 11)
        assert (delivery.reference_text, delivery.antecedent_text) == ("the operating capacity", "2,176 megawatts of operating capacity")
        perry = CommitmentSupport(delivery, component_text="the operating capacity at Perry",
                                  window=CommitmentWindow(2026, None, HorizonKind.UNSPECIFIED_YEAR, "commence in December of 2026"))
        davis = CommitmentSupport(delivery, component_text="Davis-Besse",
                                  window=CommitmentWindow(2027, None, HorizonKind.UNSPECIFIED_YEAR, "in December 2027"))
        c = claim(VST_NUCLEAR_2025Q4, 9, supports=(terms, perry, davis), counterparty_text="Meta",
                  agreement_text="long-term power purchase agreements")
        assert [s.window.start_year for s in c.supports if s.window] == [2026, 2027]
        assert sorted(q.value_low for s in c.supports for q in s.quantities) == [433, 2176]

    def test_13b_uprate_dates_do_not_attach_upgrade_is_not_uprate(self):
        assert not [l for l in links(VST_NUCLEAR_2025Q4) if l.referring_index == 12]

    def test_13c_aws_energization_dates_about_the_site_do_not_attach(self):
        assert not [l for l in links(VST_NUCLEAR_2025Q4) if l.referring_index == 6]

    def test_12_the_3_8_gw_total_never_becomes_anyones_quantity(self):
        refused = [l for l in links(VST_NUCLEAR_2025Q4) if l.referring_index == 2]
        assert refused == [], "'These agreements' after a plural, unnamed total is a position, not a commitment"
        quantities = {q.value_text for s in claim_supports_everywhere() for q in s.quantities}
        assert not any("3.8" in q for q in quantities)

    def test_14_amd_openai_gains_nothing_and_the_revenue_potential_never_attaches(self):
        assert links(AMD_OPENAI) == ()
        with pytest.raises(ValueError):
            CommitmentSupport(
                SourceEvidenceLink("rec", BACK, 0, 4, 0, "this partnership", "we announced a comprehensive multiyear agreement",
                                   AMD_OPENAI[4], AMD_OPENAI[0], "test"),
                quantities=(Q(100, "USD_BILLION", "$100 billion"),),
            )

    def test_15_amd_anthropic_stays_withheld(self):
        assert links(AMD_ANTHROPIC) == ()
        assert read_commitment_status(AMD_ANTHROPIC[0]).status is CommitmentStatus.PARTNERSHIP_ONLY

    def test_17_googl_tpu_agreements_state_nothing_to_link(self):
        assert links(GOOGL_TPU) == ()


def claim_supports_everywhere() -> list[CommitmentSupport]:
    """Every support the real VST 2025Q4 links can carry."""
    return [
        CommitmentSupport(link_of(VST_NUCLEAR_2025Q4, BACK, 4), quantities=(Q(1200, "MW", "1,200 megawatts", "of capacity"),)),
        CommitmentSupport(link_of(VST_NUCLEAR_2025Q4, BACK, 10),
                          quantities=(Q(2176, "MW", "2,176 megawatts", "of operating capacity"),)),
    ]


class TestProvenanceAndFirewalls:
    def test_21_every_support_chains_back_to_its_own_claim(self):
        terms = CommitmentSupport(link_of(VST_NUCLEAR_2025Q4, BACK, 10), term=CommitmentTerm(20, "20 years"))
        delivery = CommitmentSupport(link_of(VST_NUCLEAR_2025Q4, COMPONENT, 11),
                                     window=CommitmentWindow(2026, None, HorizonKind.UNSPECIFIED_YEAR, "December of 2026"))
        meta = dict(counterparty_text="Meta", agreement_text="long-term power purchase agreements")
        assert claim(VST_NUCLEAR_2025Q4, 9, supports=(terms, delivery), **meta).supports[1].link.antecedent_index == 10
        with pytest.raises(ValueError, match="one of this claim's back-references"):
            claim(VST_NUCLEAR_2025Q4, 9, supports=(delivery,), **meta)
        with pytest.raises(ValueError, match="own source"):
            claim(VST_NUCLEAR_2025Q4, 9, supports=(terms,), source_record_id="another-record", **meta)
        with pytest.raises(ValueError, match="which sentence"):
            claim(VST_NUCLEAR_2025Q4, 9, supports=(terms,), sentence_index=None, **meta)
        aws = CommitmentSupport(link_of(VST_NUCLEAR_2025Q4, BACK, 4), quantities=(Q(1200, "MW", "1,200 megawatts", "of capacity"),))
        with pytest.raises(ValueError, match="own sentence"):
            claim(VST_NUCLEAR_2025Q4, 9, supports=(aws,), **meta)
        assert link_of(VST_NUCLEAR_2025Q4, BACK, 10).id == "rec:link:explicit_back_reference:9:9->10"

    def test_a_support_states_only_what_its_own_sentence_states(self):
        with pytest.raises(ValueError, match="not stated in the supporting sentence"):
            CommitmentSupport(link_of(VST_NUCLEAR_2025Q4, BACK, 10), term=CommitmentTerm(25, "25 years"))
        with pytest.raises(ValueError, match="acronym"):
            CommitmentSupport(link_of(MU_SCA, ACRONYM, 2), term=CommitmentTerm(5, "five-year"))
        with pytest.raises(ValueError, match="must state"):
            CommitmentSupport(link_of(VST_NUCLEAR_2025Q4, BACK, 10))

    _TOKENS = {
        token
        for cls in (SourceEvidenceLink, CommitmentSupport, CustomerCommitmentClaim)
        for field in dataclasses.fields(cls)
        for token in field.name.split("_")
    }

    def test_23_no_economic_field_exists(self):
        for forbidden in ("revenue", "earnings", "ebitda", "price", "margin", "cash", "usd", "probability",
                          "likelihood", "renewal", "score"):
            assert forbidden not in self._TOKENS, forbidden
        for cls in (SourceEvidenceLink, CommitmentSupport, CustomerCommitmentClaim):
            assert "value" not in {f.name for f in dataclasses.fields(cls)}

    def test_24_no_recommendation_vocabulary(self):
        for forbidden in ("recommendation", "conviction", "stance", "rating", "thesis", "buy", "sell", "trim", "verdict",
                          "confidence", "outlook", "sentiment", "polarity"):
            assert forbidden not in self._TOKENS, forbidden
        for member in SourceLinkKind:
            assert not {"positive", "negative", "strong", "weak"} & set(member.value.split("_"))

    def test_25_supports_never_change_which_commitment_a_claim_is(self):
        base = dict(counterparty_text="Amazon", agreement_text="20-year contract", term=CommitmentTerm(20, "20-year"))
        alone = claim(VST_NUCLEAR_2025Q4, 3, **base)
        enriched = claim(VST_NUCLEAR_2025Q4, 3, supports=(claim_supports_everywhere()[0],), **base)
        assert (alone.id, alone.comparison_key) == (enriched.id, enriched.comparison_key)
        assert enriched.supports[0].quantities[0].value_low == 1200 and alone.quantities == ()


class TestPerformance:
    def test_linking_is_linear_in_the_number_of_sentences(self):
        turn = (VST_NUCLEAR_2025Q4 + VST_OPPORTUNITY) * 200
        started = time.perf_counter()
        found = links(turn)
        assert time.perf_counter() - started < 2.0
        assert len(found) >= 3
