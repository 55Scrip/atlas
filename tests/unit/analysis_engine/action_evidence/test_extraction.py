"""Action Evidence v1 -- the frozen Sprint 23 benchmark, sentence by sentence.

Every POSITIVE and NEGATIVE below is verbatim 10-K text from the cached
Sprint 18 corpus. Cases marked SYNTHETIC exist only to exercise a guard
the real corpus never triggers with an in-scope predicate; they say so.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.action_evidence import (
    ActionStatus,
    ActionType,
    ActorKind,
    DateKind,
    QuantityKind,
    SourceParagraph,
    extract_actions,
    read_sentence,
    split_sentences,
)


def one(sentence: str, **loc):
    base = dict(issuer="X", accession="A", section="MDA", paragraph_ordinal=0, sentence_ordinal=0)
    base.update(loc)
    records = [r for r, _ in read_sentence(sentence, base) if r is not None]
    assert len(records) == 1, [r.predicate for r in records]
    return records[0]


def none(sentence: str) -> list[str]:
    out = read_sentence(sentence)
    assert all(r is None for r, _ in out), [r.predicate for r, _ in out if r]
    return [why for _, why in out]


def q(record):
    return {(x.value_text, x.unit) for x in record.quantities}


# ------------------------------------------------------------------ positives
AWS = ("In September 2025, we announced that we had entered into a 20-year power purchase agreement "
       "(PPA) (with options to extend for up to an additional 20 years) with Amazon Web Services (AWS) "
       "to supply 1,200 MW of carbon-free power from our Comanche Peak Nuclear Power Plant.")
META = ("In January 2026, we announced that we had entered into 20-year PPAs with Meta Platforms, Inc. "
        "(Meta) to supply 2,609 MW of carbon-free power and capacity from our PJM nuclear power plants, "
        "including 2,176 MW of operating energy and capacity and 433 of uprate energy and capacity to be "
        "constructed.")
META_2 = ("In January 2026, Vistra announced it had entered into 20-year PPAs with Meta, pursuant to which "
          "the Company has agreed to supply Meta with a total of 2,609 MW of carbon-free power and capacity "
          "from the Company's PJM nuclear power plants as follows:")
WEST_TEXAS = ("Executed disciplined capital allocation through targeted natural gas expansion, including the "
              "development of an 860 MW facility in West Texas and the acquisition of 2,600 MW of natural gas "
              "generation capacity from Lotus.")
LOTUS = ("On October 22, 2025, pursuant to a purchase and sale agreement dated May 15, 2025, Vistra "
         "Operations acquired 100% of the membership interests of certain subsidiaries of Lotus "
         "(Lotus Acquisition).")
CHIPS = ("On December 9, 2024, we entered into direct funding agreements with the U.S. Department of "
         "Commerce for up to $6.1 billion in direct funding pursuant to the CHIPS Act for a planned fab in "
         "Boise, Idaho, and two planned fabs in Clay, New York.")
CHIPS_AMEND = ("On June 11, 2025, we entered into amendments to the direct funding agreements to add a second "
               "planned fab in Boise, Idaho, and allocate certain award funding from the $6.1 billion grants "
               "previously awarded to the second planned Idaho fab.")
VIRGINIA = ("On June 11, 2025, we also entered into a direct funding agreement with the U.S. Department of "
            "Commerce for up to $275 million in direct funding to expand and modernize our fab in Manassas, "
            "Virginia.")
CHIPS_RISK = ("For example, in December 2024, we entered into direct funding agreements, providing funds for "
              "the construction of fab facilities in Idaho and New York, with the United States Department of "
              "Commerce (the “Department”) under the Department’s CHIPS Incentives Program "
              "established pursuant to the CHIPS Act.")
WAYMO = ("In Other Bets, our fully autonomous driving technology company, Waymo, is now providing fully "
         "autonomous, paid ride-hailing services to customers in multiple cities.")
MODEL_Y = ("In 2025, we completed the refresh of our vehicle lineup with the launch of the new Model Y and "
           "additional variants for Model 3 and Model Y.")


def test_aws_ppa_is_an_entered_contract_dated_by_its_announcement():
    r = one(AWS)
    assert (r.actor_text, r.actor_kind, r.actor_is_filer) == ("we", ActorKind.FILER_PRONOUN, True)
    assert r.predicate == "had entered into" and r.reported_via == "announced"
    assert (r.action_type, r.status) == (ActionType.CONTRACT_ENTERED, ActionStatus.ENTERED)
    assert r.object_text == "a 20-year power purchase agreement (PPA)"
    assert r.counterparty_text == "Amazon Web Services (AWS)"
    assert {("1,200", "MW"), ("20", "year")} <= q(r)
    assert r.date.raw_text == "In September 2025" and r.date.kind is DateKind.ANNOUNCEMENT
    assert (r.date.year, r.date.month, r.date.day) == (2025, 9, None)


def test_the_option_duration_keeps_its_full_qualifier():
    r = one(AWS)
    assert any(x.qualifier == "up to an additional" for x in r.quantities if x.unit == "year")


def test_meta_ppa_keeps_every_quantity_and_invents_no_unit():
    r = one(META)
    assert r.counterparty_text == "Meta Platforms, Inc. (Meta)"
    assert {("2,609", "MW"), ("2,176", "MW"), ("20", "year"), ("433", None)} <= q(r)
    bare = next(x for x in r.quantities if x.value_text == "433")
    assert bare.unit is None and bare.kind is QuantityKind.UNSPECIFIED
    assert "uprate" in bare.qualifier


def test_mw_qualifier_is_preserved():
    r = one(META)
    op = next(x for x in r.quantities if x.value_text == "2,176")
    assert op.qualifier == "of operating energy and capacity"


def test_named_reporter_binds_the_pronoun_but_is_not_asserted_to_be_the_filer():
    r = one(META_2)
    assert (r.actor_text, r.actor_kind, r.actor_is_filer) == ("Vistra", ActorKind.NAMED, None)
    assert r.counterparty_text == "Meta" and r.reported_via == "announced"


def test_subjectless_highlight_is_implicit_and_keeps_both_capacities():
    r = one(WEST_TEXAS)
    assert (r.actor_text, r.actor_kind, r.actor_is_filer) == (None, ActorKind.IMPLICIT, None)
    assert r.predicate == "Executed"
    assert r.object_text == "disciplined capital allocation through targeted natural gas expansion"
    assert {("860", "MW"), ("2,600", "MW")} <= q(r)


def test_lotus_is_dated_by_the_event_not_by_the_agreement_it_cites():
    r = one(LOTUS)
    assert r.actor_text == "Vistra Operations" and r.actor_kind is ActorKind.NAMED
    assert r.predicate == "acquired" and r.action_type is ActionType.ACQUISITION
    assert r.object_text.startswith("100% of the membership interests of certain subsidiaries of Lotus")
    assert r.date.raw_text == "On October 22, 2025" and r.date.kind is DateKind.EVENT
    assert (r.date.year, r.date.month, r.date.day) == (2025, 10, 22)


def test_a_month_name_is_not_a_modal_verb():
    # "dated May 15" once read as the hedge "may" and dropped the Lotus acquisition.
    assert one(LOTUS).predicate == "acquired"


@pytest.mark.parametrize("sentence,obj,party,qty,day", [
    (CHIPS, "direct funding agreements", "the U.S. Department of Commerce", ("6.1 billion", "$"), 9),
    (CHIPS_AMEND, "amendments to the direct funding agreements", None, ("6.1 billion", "$"), 11),
    (VIRGINIA, "a direct funding agreement", "the U.S. Department of Commerce", ("275 million", "$"), 11),
])
def test_chips_funding_agreements(sentence, obj, party, qty, day):
    r = one(sentence)
    assert r.object_text == obj and r.counterparty_text == party and qty in q(r)
    assert r.date.day == day and r.date.kind is DateKind.EVENT


def test_up_to_is_kept_on_the_funding_amount():
    r = one(CHIPS)
    assert next(x for x in r.quantities if x.unit == "$").qualifier.startswith("up to")


def test_the_currency_is_the_symbol_the_source_wrote_not_an_asserted_iso_code():
    assert next(x for x in one(CHIPS).quantities if x.kind is QuantityKind.MONETARY).unit == "$"


def test_a_filer_action_cited_in_a_risk_factor_still_counts():
    r = one(CHIPS_RISK, section="RISK_FACTORS")
    assert r.object_text == "direct funding agreements"
    assert r.counterparty_text.startswith("the United States Department of Commerce")
    assert r.date.raw_text == "in December 2024" and r.date.day is None
    assert r.locator.section == "RISK_FACTORS"


def test_waymo_is_an_ongoing_activity_of_a_named_actor():
    r = one(WAYMO)
    assert (r.actor_text, r.actor_is_filer) == ("Waymo", None)
    assert (r.action_type, r.status) == (ActionType.ONGOING_ACTIVITY, ActionStatus.ONGOING)
    assert r.object_text == "fully autonomous, paid ride-hailing services"
    assert r.date is None


def test_model_y_refresh_is_a_completion_in_a_period():
    r = one(MODEL_Y)
    assert r.object_text == "the refresh of our vehicle lineup" and r.counterparty_text is None
    assert r.date.kind is DateKind.PERIOD and (r.date.month, r.date.day) == (None, None)


# ------------------------------------------------------------------ negatives (real corpus)
NEGATIVES = {
    "accounting": "As of December 31, 2025 and 2024, the carrying value of our ARO related to our Comanche Peak "
                  "nuclear generation facility decommissioning totaled $1.838 billion and $1.797 billion, "
                  "respectively, which is lower than the fair value of the assets contained in the Comanche Peak "
                  "NDT of $2.589 billion and $2.249 billion, respectively.",
    "country_list": "In addition to our U.S. operations, a substantial portion of our operations are conducted "
                    "in Taiwan, Singapore, Japan, Malaysia, China, and India, and many of our customers, "
                    "suppliers, and vendors also operate internationally.",
    "external_actor": "Over the past several years, the U.S. government announced additional export regulations "
                      "for U.S. semiconductor technology sold in China, including wafer fabrication equipment "
                      "and related parts and services.",
    "optimus": "We are also capitalizing on our strengths in real-world AI data to advance the development of "
               "Optimus, a general purpose, autonomous humanoid robot.",
    "bots": "We are focused on bringing artificial intelligence (“AI”) into the real world, through "
            "products and services like Full Self-Driving (“FSD”) (Supervised) and Robotaxi, as well "
            "as working to develop and commercialize AI robots (“Bots”) (including Optimus).",
    "gemini": "Over the last decade, our research teams have pushed the boundaries of AI forward, which is "
              "displayed through Gemini 3, our most intelligent AI model yet.",
    "ai_mode": "AI Mode allows users to ask more nuanced questions that might have previously taken multiple "
               "searches, using Gemini’s advanced reasoning, thinking, and multimodal capabilities.",
    "tpus": "Our technical infrastructure allows us to use and offer our customers a range of AI accelerator "
            "options, including specialized Graphics Processing Units (GPUs) and our own custom-built Tensor "
            "Processing Units (TPUs), such as Ironwood, our seventh-generation TPU.",
    "anticipate": "We anticipate power delivery to begin in the fourth quarter of 2027 and ramp to full "
                  "capacity by 2032.",
    "announced_plans": "In addition, we announced plans to bring advanced HBM packaging capabilities to the U.S.",
    "announced_plan": "Our announced plan for New York includes construction of a leading-edge DRAM memory "
                      "manufacturing site, consisting of up to four fabs to be built over the next 20-plus "
                      "years, in Clay, New York.",
    "conditional": "The awards under the direct funding agreements are subject to various conditions and we may "
                   "not receive the funding expected on the same terms or at all.",
    "did_not": "In 2025, the Company did not complete any business acquisitions.",
    "not_yet_entered": "Internationally, there may be laws in jurisdictions we have not yet entered or laws we "
                       "are unaware of in jurisdictions we have entered that may restrict our sales or other "
                       "business practices.",
    "lease_position": "As of December 31, 2024, we have entered into leases that have not yet commenced with "
                      "future short-term and long-term lease payments of $773 million and $6.5 billion, "
                      "respectively, that are not yet recorded on our Consolidated Balance Sheets.",
    "unchanged": "The direct funding for up to $6.1 billion remains unchanged.",
    "commencing": "We anticipate commencing delivery on a portion of the operating energy and capacity in late "
                  "2026 and full delivery by year end 2027.",
}


@pytest.mark.parametrize("name", sorted(NEGATIVES))
def test_negative_controls_emit_nothing(name):
    none(NEGATIVES[name])


def test_a_balance_sheet_position_is_refused_by_name():
    assert none(NEGATIVES["lease_position"]) == ["position_as_of"]


# ------------------------------------------------------------------ corpus failure modes found in Sprint 23
def test_a_leading_participle_used_as_an_adjective_is_not_an_action():
    assert "adjectival_participle" in none(
        "Completed assets are transferred to their respective asset classes and depreciation begins when an "
        "asset is ready for its intended use.")
    assert "adjectival_participle" in none(
        "Acquired technology is amortized over a one to six year period, acquired customer relationships are "
        "amortized over a one- to two-year period.")


def test_a_title_case_heading_is_not_an_action():
    assert none("Long-Lived Assets Including Acquired Intangible Assets") == ["heading"]


def test_a_determiner_is_never_an_actor():
    assert "no_actor" in none("The acquired technology was valued at $255 million using a relief-from-royalty "
                              "methodology.")


def test_an_intransitive_performance_idiom_is_not_an_action():
    assert "not_active_object" in none(
        "We executed well on pricing and improved our financial performance significantly from the start of "
        "the year.")


def test_an_adverb_inside_the_object_phrase_is_kept():
    assert one("During the year ended December 31, 2024, the Company completed individually immaterial "
               "acquisitions that resulted in goodwill being recognized.").object_text == (
        "individually immaterial acquisitions")


def test_entering_a_market_is_not_entering_a_contract():
    r = one("Upon launching our Robotaxi service in June 2025, we also entered into the autonomous "
            "ride-hailing service market, and have plans to mass produce Cybercab.")
    assert r.action_type is ActionType.ENTRY


# ------------------------------------------------------------------ counterparty discipline
@pytest.mark.parametrize("sentence", [
    "In June 2025, we entered into a 364-day Credit Agreement that provided us with the ability to borrow up "
    "to $4.0 billion.",
    "For example, we entered into certain credit agreements in connection with our acquisition of "
    "Informatica.",
    "In 2021, we entered into fixed-to-floating interest rate swaps on the 2027 Notes with an aggregate $900 "
    "million notional amount equal to the principal amount of the 2027 Notes.",
])
def test_a_with_that_is_not_a_party_is_not_a_counterparty(sentence):
    assert one(sentence).counterparty_text is None


def test_a_real_party_is_kept_and_stops_at_its_relative_clause():
    r = one("On the Effective Date, we entered into the Tax Matters Agreement with EFH Corp. whereby the "
            "parties have agreed to take certain actions.")
    assert r.counterparty_text == "EFH Corp."


# ------------------------------------------------------------------ SYNTHETIC guard fixtures
@pytest.mark.parametrize("sentence,reason", [
    ("In 2025, we have not entered into any new power purchase agreements.", "negated"),       # SYNTHETIC
    ("By year end, we will have completed the acquisition of the facility.", "forward"),        # SYNTHETIC
    ("Upon closing, we acquired all outstanding stock of the target company.", "conditional"),   # SYNTHETIC
])
def test_synthetic_guards_refuse_with_the_right_reason(sentence, reason):
    assert reason in none(sentence)


def test_synthetic_external_actor_is_recorded_as_named_and_never_as_the_filer():
    # SYNTHETIC: an agency acting, reported in a filer's document.
    r = one("In 2024, the Department executed a funding agreement.".replace("the Department", "Commerce"))
    assert r.actor_kind is ActorKind.NAMED and r.actor_is_filer is None


# ------------------------------------------------------------------ provenance, co-occurrence, determinism
OPTIMUS_PARAGRAPH = (
    "We are focused on growing and optimizing our manufacturing capacity. In 2025, we completed the refresh "
    "of our vehicle lineup with the launch of the new Model Y and additional variants for Model 3 and Model Y. "
    "We are also capitalizing on our strengths in real-world AI data to advance the development of Optimus, a "
    "general purpose, autonomous humanoid robot.")


def para(text, ordinal=0, issuer="TSLA", accession="0001628280-26-003952", section="MDA"):
    return SourceParagraph(issuer=issuer, accession=accession, section=section, ordinal=ordinal, text=text)


def test_a_co_occurring_object_never_steals_the_predicate():
    records = extract_actions([para(OPTIMUS_PARAGRAPH, 330)])
    assert len(records) == 1
    r = records[0]
    assert "Optimus" not in r.sentence and "Optimus" not in r.object_text


def test_provenance_is_complete_and_rereadable():
    r = extract_actions([para(OPTIMUS_PARAGRAPH, 330)])[0]
    loc = r.locator
    assert (loc.issuer, loc.accession, loc.section, loc.paragraph_ordinal, loc.sentence_ordinal) == (
        "TSLA", "0001628280-26-003952", "MDA", 330, 1)
    assert split_sentences(OPTIMUS_PARAGRAPH)[loc.sentence_ordinal] == r.sentence
    assert r.sentence[loc.predicate_offset:].startswith(r.predicate)


def test_sentence_splitting_keeps_initialisms_and_corporate_abbreviations_whole():
    assert len(split_sentences(CHIPS)) == 1
    assert len(split_sentences(META)) == 1


def test_extraction_is_deterministic_idempotent_and_order_independent():
    ps = [para(OPTIMUS_PARAGRAPH, 330), para(AWS, 531, "VST", "0001692819-26-000006"),
          para(CHIPS, 486, "MU", "0000723125-25-000028", "PROPERTIES")]
    a = extract_actions(ps)
    assert a == extract_actions(ps)
    assert a == extract_actions(list(reversed(ps)))
    assert a == extract_actions(ps + ps)            # the same paragraph twice is one observation
    assert len({r.key for r in a}) == len(a) == 3


def test_the_same_sentence_in_two_places_is_two_observations():
    rs = extract_actions([para(LOTUS, 570, "VST", "V", "MDA"), para(LOTUS, 949, "VST", "V", "FINANCIAL_STATEMENTS")])
    assert len(rs) == 2 and {r.locator.section for r in rs} == {"MDA", "FINANCIAL_STATEMENTS"}


# ------------------------------------------------------------------ which date governs the action
def test_a_date_after_the_predicate_never_dates_the_action():
    # SYNTHETIC: the later date belongs to the original agreement, not to this amendment.
    r = one("On March 3, 2025, we entered into an amendment to the agreement originally signed on May 1, 2019.")
    assert (r.date.year, r.date.month, r.date.day) == (2025, 3, 3)


def test_only_the_sentence_opening_date_governs_the_action():
    # SYNTHETIC: "in March 2020" dates the review; the sale happened in 2024.
    r = one("In 2024, following a review begun in March 2020, we completed the sale of the business.")
    assert (r.date.year, r.date.month, r.date.kind) == (2024, None, DateKind.PERIOD)


def test_contract_duration_is_never_read_as_capacity():
    kinds = {(x.value_text, x.unit): x.kind for x in one(AWS).quantities}
    assert kinds[("20", "year")] is QuantityKind.DURATION
    assert kinds[("1,200", "MW")] is QuantityKind.CAPACITY


# ------------------------------------------------------------------ share repurchase
class TestSharesActuallyBoughtBack:
    """Sprint 26. Claims about returning capital had no action vocabulary at
    all, so every one of them was refused on event. The family is narrow on
    purpose: only the past-tense verb counts, because the nouns around it --
    "repurchase programme", "authorized repurchases", "remaining
    authorization" -- describe permission to spend, not spending."""

    def test_a_completed_repurchase_is_read_with_its_amount(self):
        r = one("We repurchased 3.2 million shares of our common stock for $300 million in 2024.")
        assert r.action_type is ActionType.SHARE_REPURCHASE
        assert r.status is ActionStatus.COMPLETED
        assert r.actor_is_filer is True
        assert r.object_text == "3.2 million shares of our common stock"
        assert [(q.value_text, q.unit) for q in r.quantities] == [("300 million", "$")]

    def test_a_cumulative_repurchase_is_still_an_observed_one(self):
        r = one("Through August 28, 2025, we had repurchased an aggregate of $7.19 billion "
                "under the authorization.")
        assert r.action_type is ActionType.SHARE_REPURCHASE
        assert r.predicate.lower().endswith("repurchased")
        # the figure is what was spent, not what was permitted
        assert [q.value_text for q in r.quantities] == ["7.19 billion"]

    def test_the_company_as_actor_reads_the_same_as_we(self):
        r = one("The Company repurchased an additional $959 million dollar-value of shares in 2025.")
        assert r.action_type is ActionType.SHARE_REPURCHASE and r.actor_is_filer is True

    # ---------------------------------------------------------- hard negatives
    @pytest.mark.parametrize("sentence", [
        # a board permitting a ceiling is not a purchase -- the single most
        # dangerous false positive in this family
        "In February 2026, our Board of Directors authorized the repurchase of up to $2 billion "
        "of our Class A subordinate voting shares.",
        "In March 2025, our Board of Directors approved a common stock repurchase program "
        "authorizing $10.0 billion in repurchases.",
        "As of January 31, 2026, we were authorized to purchase a remaining $17.9 billion of the "
        "Company's common stock under the Share Repurchase Program.",
        # the same permission without the "As of" opener, so the sentence has
        # to be refused on what it says rather than on how it begins
        "We were authorized to purchase a remaining $17.9 billion of the Company's common stock.",
        "The Board authorized an additional $20.0 billion in repurchases under the programme.",
        # explicitly denied
        "No shares were repurchased in 2025.",
        # permitted, not done
        "Under the Share Repurchase Program, shares of common stock may be repurchased using a "
        "variety of methods.",
        # future
        "The timing, number, and value of shares repurchased will be determined at our discretion.",
        # accounting description, not an act
        "Repurchased shares of our common stock are considered treasury stock.",
        "Amounts repurchased are included in treasury stock.",
        # somebody else's act
        "The US has imposed a 1% excise tax on the fair market value of shares repurchased.",
    ])
    def test_permission_denial_and_description_never_become_a_repurchase(self, sentence):
        assert [r for r, _ in read_sentence(sentence) if r] == []

    def test_a_table_lead_in_names_nothing_and_is_refused(self):
        # "the following" points at rows this layer never read
        out = read_sentence("We repurchased the following under the Share Repurchase Program "
                            "(in millions, except average price per share):")
        assert [r for r, _ in out if r] == []
        assert "not_active_object" in [why for _, why in out if why]

    def test_no_date_is_invented_when_the_source_states_none_this_layer_reads(self):
        r = one("We repurchased 3.2 million shares of our common stock for $300 million in 2024.")
        assert r.date is None


# ------------------------------------------------------------------ guard repairs
class TestANounThatLooksLikeAnIntention:
    """The forward guard reads "plan" as a modal. After a determiner it is a
    thing, and a sentence can describe something already done as part of one."""

    def test_an_action_taken_under_a_plan_is_still_an_action(self):
        r = one("As part of this plan, in September 2022, we entered into an agreement with a supplier.")
        assert r.action_type is ActionType.CONTRACT_ENTERED and r.actor_is_filer is True

    def test_the_determiner_is_what_makes_it_a_noun(self):
        assert one("Under the plan, we acquired 4,048 MW of nuclear generation facilities.")

    @pytest.mark.parametrize("sentence", [
        # the verb, which really is intent, is untouched
        "We plan to enter into an agreement with a supplier.",
        "The Company plans to enter into an agreement with a supplier.",
        # so is the adjective
        "In addition to our planned solar investments, we may enter into further agreements.",
        # and a modal still governs whatever noun sits beside it
        "The trading arrangement will terminate one year from the date the plan is entered into.",
    ])
    def test_intent_is_still_refused(self, sentence):
        assert [r for r, _ in read_sentence(sentence) if r] == []

    def test_a_plan_completing_itself_is_not_the_company_acting(self):
        assert [r for r, _ in read_sentence("The plan was substantially completed in 2023.") if r] == []


class TestALabelInFrontOfTheClause:
    """Filings label a clause with its subject -- "Singapore: we broke
    ground". The label hid the actor behind it, and where an actor was found
    anyway the label was pasted onto the front of its name."""

    def test_the_actor_behind_a_label_is_found(self):
        r = one("Singapore: we entered into an agreement with a supplier.")
        assert r.actor_text == "we" and r.actor_is_filer is True

    def test_the_label_is_not_part_of_the_actors_name(self):
        r = one("Idaho: the Company acquired 4,048 MW of nuclear generation facilities.")
        assert r.actor_text == "the Company"
        assert ":" not in r.actor_text

    def test_a_bare_heading_never_becomes_the_actor(self):
        # nothing follows the colon, so the label names the topic and the
        # filing does not say who acted
        assert [r for r, _ in read_sentence(
            "Amazon Web Services: entered into an agreement with a third party.") if r] == []

    def test_a_label_cannot_manufacture_a_predicate_or_an_actor(self):
        assert [r for r, _ in read_sentence("Note 5: the fair value of the trust was $450 million.") if r] == []

    def test_forward_language_still_governs_after_a_label(self):
        assert [r for r, _ in read_sentence(
            "Risk Factors: we may be unable to complete the transaction.") if r] == []


class TestAReportingPeriodIsNotADay:
    """"During the year ended December 31, 2024" says the act happened
    somewhere inside 2024. It does not say it happened on the 31st."""

    def test_a_year_ended_opener_yields_a_period_with_no_day(self):
        r = one("During the year ended December 31, 2024, we repurchased 16.6 million shares "
                "for $1.2 billion under the program.")
        assert r.date is not None
        assert r.date.kind is DateKind.PERIOD
        assert (r.date.year, r.date.month, r.date.day) == (2024, None, None)

    def test_a_fiscal_year_is_read_the_same_way(self):
        r = one("During the fiscal year ended January 31, 2025, we repurchased approximately "
                "30 million shares.")
        assert r.date.kind is DateKind.PERIOD
        assert (r.date.year, r.date.month, r.date.day) == (2025, None, None)

    def test_a_cumulative_boundary_is_not_a_period_of_occurrence(self):
        # "through" says how much had been done by a date, not when it was done
        r = one("Through August 28, 2025, we had repurchased an aggregate of $7.19 billion "
                "under the authorization.")
        assert r.date is None

    def test_two_years_in_one_opener_are_left_unread_rather_than_collapsed(self):
        out = [r for r, _ in read_sentence(
            "During the years ended December 31, 2024 and 2025, we entered into agreements "
            "with several suppliers.") if r]
        assert out and out[0].date is None

    def test_an_explicit_day_keeps_its_day_and_stays_an_event(self):
        r = one("On December 9, 2024, we entered into direct funding agreements with a department.")
        assert r.date.kind is DateKind.EVENT and r.date.day == 9

    def test_the_filing_date_is_never_used_as_the_action_date(self):
        r = one("We repurchased 3.2 million shares of our common stock for $300 million in 2024.")
        assert r.date is None


class TestTheRepairsStayInsideTheirOwnBoundaries:
    """Each repair removes one specific false refusal. These pin the edge it
    must not cross -- the forward negatives above cannot do it, because a
    sentence stating intent uses an infinitive and is refused for having no
    predicate at all, whichever way the guard behaves."""

    @pytest.mark.parametrize("phrase", ["this plan", "the plan", "our plans", "a plan", "such plans"])
    def test_a_determiner_before_it_makes_it_a_noun(self, phrase):
        from atlas.analysis_engine.action_evidence.extraction import _NOUN_PLAN
        assert _NOUN_PLAN.search(f"As part of {phrase}, we acted")

    @pytest.mark.parametrize("phrase", [
        "we plan to build", "the Company plans to build", "planning to build",
        "planned to build", "our planned investments", "we are planning",
    ])
    def test_the_verb_and_the_adjective_are_left_for_the_forward_guard(self, phrase):
        from atlas.analysis_engine.action_evidence.extraction import _NOUN_PLAN
        assert not _NOUN_PLAN.search(phrase), f"{phrase!r} must still read as intent"

    def test_a_long_clause_before_a_colon_is_not_a_label(self):
        from atlas.analysis_engine.action_evidence.extraction import _classify_actor

        # four words or fewer is a heading; beyond that it is running prose,
        # and the text after a colon inside it is not the actor
        assert _classify_actor("Singapore: we")[0] == "we"
        assert _classify_actor("Following a detailed review of our capital structure: we")[0] != "we"

    def test_through_a_date_is_not_a_year_ended_period(self):
        from atlas.analysis_engine.action_evidence.extraction import _PERIOD_YEAR

        assert _PERIOD_YEAR.match("During the year ended December 31, 2024,")
        assert not _PERIOD_YEAR.match("Through August 28, 2025,")
        assert not _PERIOD_YEAR.match("As of December 31, 2024,")
