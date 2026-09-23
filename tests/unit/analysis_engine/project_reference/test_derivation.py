"""Project Reference v1 -- the frozen Sprint 31 benchmark.

Every object below is verbatim from a committed StrategyClaim or
ActionEvidence at 25e5f90, reached through the real upstream extractors. The
negatives carry the weight: the word "facility" names a building in one
sentence and a line of credit in the next, and a rule that cannot tell them
apart is worse than no rule.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.action_evidence import SourceParagraph, extract_actions
from atlas.analysis_engine.project_reference import (
    ProjectKind, SourceRole, references_from_action, references_from_claim,
)
from atlas.analysis_engine.strategy_claim import ClaimProvenance, read_claim

# ------------------------------------------------------------------ claims
SINGAPORE = ("In NAND, the combination of a higher demand outlook and our decision to colocate R&D "
             "cleanroom in our manufacturing fab underpins our decision to break ground for a new "
             "NAND fab at our Singapore site.")
NEW_YORK = ("We plan to break ground on our first New York fab in early calendar 2026, which we "
            "expect will provide supply in 2030 and beyond.")
CLEANROOM = ("Adding to the existing fab, we plan to begin construction of a similar-sized second "
             "cleanroom at this site by 2026.")
WEST_TEXAS = ("In addition to our planned solar and energy storage investments, we will be allocating "
              "capital to our new gas-fired units in West Texas, which we estimate will require "
              "approximately $900 million before any offsets from project financing.")
CLEAN_ROOM_SPACE = ("Simultaneously, we are focused on maximizing our production output from our "
                    "current footprint, ramping our industry-leading technology nodes, and investing "
                    "in new clean room space to add to our supply capability.")
JAPAN = ("We are investing not only in technology transitions but also in greenfield capacity and "
         "enabling greater technology production capability in our existing clean rooms in Japan.")
DATA_CENTERS = ("We've been working hard to ensure we're running a productive and efficient "
                "organization, and it's not just how we operate the business, but even in areas such "
                "as our technical infrastructure where we are investing significant CapEx in data "
                "centers and servers, ensuring we get the most out of every dollar.")
ARIZONA = ("As part of this endeavor, we plan to invest more than $200 million in Arizona to "
           "establish a state-of-the-art facility for manufacturing specialized components for our "
           "equipment.")
TURBINES = ("Having an existing site there, our Permian gas site, which we are expanding by adding "
            "turbines, makes this opportunity even more compelling.")
PPAS = ("This is just the beginning, as we aim to secure customer PPAs for both new generation and "
        "our existing assets, continuing on this growth path.")
COMANCHE = ("However, our immediate priority is to ensure that everything necessary for the data "
            "center at Comanche Peak is completed on schedule.")

# ----------------------------------------------------------------- actions
BOISE = "As part of this plan, in September 2022, we broke ground on a leading-edge memory manufacturing fab in Boise, Idaho."
HBM = ("Singapore: we broke ground on an HBM advanced packaging facility to meaningfully expand our "
       "total advanced packaging capacity beginning in calendar 2027; and")
ENERGY_HARBOR = ("Acquisition of Nuclear Generation Facilities — In 2024, we acquired 4,048 MW of "
                 "nuclear generation facilities in PJM from Energy Harbor.")
GAS_FLEET = ("Acquisition of Natural Gas Generation Facilities — In 2025, we acquired 2,557 MW of "
             "natural gas generation facilities in Delaware and Pennsylvania (PJM), Rhode Island "
             "(ISO-NE), New York (NYISO).")
RCF = ("In 2023, we entered into a 5-year senior unsecured revolving credit facility (the “RCF "
       "Credit Agreement”) with a syndicate of banks.")
LOC = "We entered into uncommitted standby letter of credit facilities with a number of banks."
BALDWIN = "We have completed closure activities at those ponds at our Baldwin facility."
CHIPS_FUNDING = ("For example, in December 2024, we entered into direct funding agreements, providing "
                 "funds for the construction of fab facilities in Idaho and New York, with the United "
                 "States Department of Commerce (the “Department”) under the Department’s CHIPS "
                 "Incentives Program established pursuant to the CHIPS Act.")
SG_PPA = ("In 2023, we entered into an 18-year power purchase agreement in Singapore to purchase up "
          "to 450 megawatts of power at predominantly variable prices.")
DELIVERR = ("The Company acquired 100% of the outstanding shares of Deliverr in exchange for cash "
            "consideration of $1,962 million and $10 million in Shopify Class A subordinate voting shares.")
MU_BUYBACK = "During 2024, we repurchased 3.2 million shares of our common stock for $425 million."


def _claim(passage, issuer="ZZ"):
    return read_claim(passage, ClaimProvenance(issuer=issuer, node_id="n", node_kind="objective",
                                               source_record_id="r", source_period="2026Q1",
                                               speaker_title="CEO"))


def claim_refs(passage, issuer="ZZ"):
    claim = _claim(passage, issuer)
    assert claim is not None, "the upstream claim reader must still read this passage"
    return references_from_claim(claim)


def action_refs(sentence, issuer="ZZ"):
    actions = list(extract_actions([SourceParagraph(issuer=issuer, accession="a", section="MDA",
                                                    ordinal=0, text=sentence)]))
    assert actions, "the upstream action reader must still read this sentence"
    return [r for a in actions for r in references_from_action(a)]


class TestTheObjectsHeadNamesTheProject:
    def test_a_named_fab_carries_its_own_words(self):
        (ref,) = claim_refs(SINGAPORE)
        assert ref.surface == "a new NAND fab"
        assert ref.kind is ProjectKind.FAB
        assert ref.location_surface == "our Singapore site"
        assert ref.modifiers == ("new", "NAND")
        assert ref.ordinal is None
        assert ref.source_role is SourceRole.OBJECT_OF_CLAIM

    def test_a_groundbreaking_object_carries_its_own_words(self):
        (ref,) = action_refs(BOISE)
        assert ref.surface == "a leading-edge memory manufacturing fab"
        assert ref.kind is ProjectKind.FAB
        assert ref.location_surface == "Boise, Idaho"
        assert ref.modifiers == ("leading-edge", "memory", "manufacturing")
        assert ref.source_role is SourceRole.OBJECT_OF_ACTION

    def test_a_plural_portfolio_is_one_reference_and_keeps_every_place(self):
        (ref,) = action_refs(GAS_FLEET)
        assert ref.surface == "natural gas generation facilities"
        assert ref.location_surface == "Delaware and Pennsylvania (PJM), Rhode Island (ISO-NE), New York (NYISO)"

    def test_capacity_describes_a_project_and_is_not_part_of_its_identity(self):
        (ref,) = action_refs(ENERGY_HARBOR)
        assert ref.surface == "nuclear generation facilities"
        assert "4,048" not in ref.surface and "MW" not in ref.surface
        assert ref.location_surface == "PJM"

    def test_a_thing_at_a_place_whose_class_the_source_never_states(self):
        (ref,) = claim_refs(WEST_TEXAS)
        assert ref.surface == "our new gas-fired units"
        assert ref.kind is ProjectKind.UNKNOWN, "the source calls them units, not a class of plant"
        assert ref.location_surface == "West Texas"

    def test_provenance_points_back_at_the_owning_record(self):
        (ref,) = claim_refs(SINGAPORE, issuer="ZZ")
        assert ref.provenance.issuer == "ZZ"
        assert ref.provenance.owner_kind == "strategy_claim"
        assert ref.provenance.owner_key == "n"
        assert ref.provenance.source_period == "2026Q1"
        assert ref.provenance.source_passage == SINGAPORE
        assert ref.surface in ref.provenance.source_object_text


class TestASourceOrdinalSurvives:
    def test_first_is_preserved_because_the_source_says_it(self):
        (ref,) = claim_refs(NEW_YORK)
        assert ref.ordinal == "first"
        assert ref.surface == "our first New York fab"

    def test_second_is_preserved_because_the_source_says_it(self):
        (ref,) = claim_refs(CLEANROOM)
        assert ref.ordinal == "second"
        assert ref.surface == "a similar-sized second cleanroom"
        assert ref.kind is ProjectKind.CLEANROOM

    def test_an_unresolved_deictic_stays_unresolved(self):
        (ref,) = claim_refs(CLEANROOM)
        assert ref.location_surface == "this site", "the claim never says which site"

    def test_no_ordinal_is_invented_where_the_source_states_none(self):
        assert claim_refs(SINGAPORE)[0].ordinal is None
        assert action_refs(BOISE)[0].ordinal is None


class TestAPlaceIsNotAProject:
    def test_a_place_inside_the_project_phrase_stays_inside_it(self):
        (ref,) = claim_refs(NEW_YORK)
        assert ref.surface == "our first New York fab"
        assert ref.location_surface is None, "the source attaches no separate place here"

    def test_a_trailing_date_is_not_read_as_a_place(self):
        (ref,) = claim_refs(NEW_YORK)
        assert ref.location_surface is None
        assert "2026" not in (ref.location_surface or "")

    def test_an_object_that_names_no_place_gets_none(self):
        (ref,) = action_refs(HBM)
        assert ref.location_surface is None, (
            "the only place word sits outside the object, in a bulleted label")
        assert ref.surface == "an HBM advanced packaging facility"


class TestAFacilityWordIsNotAlwaysAFacility:
    @pytest.mark.parametrize("sentence", [RCF, LOC])
    def test_a_facility_that_is_a_line_of_credit_is_not_a_project(self, sentence):
        assert action_refs(sentence) == []

    def test_a_facility_agreement_is_an_agreement(self):
        assert action_refs("In 2023, we entered into a facility agreement (Facility Agreement).") == []

    def test_a_facility_that_is_merely_where_the_work_happened(self):
        assert action_refs(BALDWIN) == [], "the object is closure activities, not the Baldwin facility"

    def test_a_facility_named_only_in_the_purpose_clause_is_not_the_object(self):
        assert action_refs(CHIPS_FUNDING) == [], (
            "the object is funding agreements; 'fab facilities in Idaho and New York' is what the "
            "money is for")

    def test_a_facility_named_only_in_a_purpose_clause_of_a_claim_is_not_the_object(self):
        assert claim_refs(ARIZONA) == ()


class TestNoProjectWhereTheSourceNamesNone:
    @pytest.mark.parametrize("passage", [DATA_CENTERS, CLEAN_ROOM_SPACE, JAPAN, TURBINES, PPAS, COMANCHE])
    def test_claims_that_name_no_particular_project(self, passage):
        assert claim_refs(passage) == ()

    @pytest.mark.parametrize("sentence", [SG_PPA, DELIVERR, MU_BUYBACK])
    def test_actions_that_name_no_project(self, sentence):
        assert action_refs(sentence) == []

    def test_a_company_with_a_home_town_is_not_a_project_in_that_town(self):
        assert action_refs(DELIVERR) == []


class TestSingaporeStaysDistinct:
    """The Sprint 30 stop gate, now visible in the representation."""

    def test_the_claim_and_the_action_keep_different_words(self):
        (claim_ref,) = claim_refs(SINGAPORE)
        (action_ref,) = action_refs(HBM)
        assert claim_ref.surface != action_ref.surface
        assert claim_ref.modifiers != action_ref.modifiers
        assert "NAND" in claim_ref.modifiers and "NAND" not in action_ref.modifiers
        assert "HBM" in action_ref.modifiers and "HBM" not in claim_ref.modifiers

    def test_neither_reference_offers_a_verdict_about_the_other(self):
        import atlas.analysis_engine.project_reference as pkg
        offered = [n for n in dir(pkg) if not n.startswith("_")]
        assert not [n for n in offered
                    if any(w in n.lower() for w in ("same", "match", "identi", "equal", "compare",
                                                    "resolve", "link"))], offered


class TestOneRecordYieldsAtMostOneReference:
    def test_the_corpus_earns_no_multi_reference_machinery(self):
        for passage in (SINGAPORE, NEW_YORK, CLEANROOM, WEST_TEXAS):
            assert len(claim_refs(passage)) <= 1
        for sentence in (BOISE, HBM, ENERGY_HARBOR, GAS_FLEET):
            assert len(action_refs(sentence)) <= 1


class TestTheSameAnswerEveryTime:
    def test_deterministic(self):
        assert claim_refs(SINGAPORE) == claim_refs(SINGAPORE)
        assert action_refs(BOISE) == action_refs(BOISE)

    def test_idempotent(self):
        claim = _claim(SINGAPORE)
        assert references_from_claim(claim) == references_from_claim(claim)

    def test_order_independent(self):
        passages = [SINGAPORE, NEW_YORK, CLEANROOM, WEST_TEXAS, DATA_CENTERS]
        forward = [claim_refs(p) for p in passages]
        backward = [claim_refs(p) for p in reversed(passages)]
        assert forward == list(reversed(backward))


class TestTheSourceSuppliesTheKnowledge:
    """Whether two process words name different things is the filer's business.
    We keep the words; we do not know what they mean."""

    @pytest.mark.parametrize("word", ["NAND", "HBM", "quixotic"])
    def test_every_modifier_is_handled_the_same_way(self, word):
        (ref,) = claim_refs(f"We plan to break ground for a new {word} fab at our Singapore site.")
        assert ref.modifiers == ("new", word)
        assert ref.kind is ProjectKind.FAB

    @pytest.mark.parametrize("place", ["Boise, Idaho", "Nowhere, Erewhon"])
    def test_every_place_is_kept_verbatim_and_unresolved(self, place):
        (ref,) = action_refs(f"In 2022, we broke ground on a leading-edge fab in {place}.")
        assert ref.location_surface == place


class TestBoundariesTheCorpusOnlyAlmostReaches:
    """Two shapes the held filings do not quite contain. Marked synthetic, kept
    small, and here because the rules have a boundary whether or not Micron and
    Vistra happen to have written the sentence that finds it."""

    def test_a_project_at_a_place_that_is_itself_a_facility(self):
        """SYNTHETIC. The corpus has a facility as a place ("at our Baldwin
        facility") and facilities as objects, but never both in one object."""
        (ref,) = action_refs("In 2022, we broke ground on a new fab at our packaging facility.")
        assert ref.surface == "a new fab", "the place must not become the project"
        assert ref.location_surface == "our packaging facility"

    def test_the_four_kinds_stay_four_distinct_kinds(self):
        """A kind whose stored word collides with another's stops being its own
        answer the moment anything reads the value rather than the member."""
        assert len(list(ProjectKind)) == 4
        assert len({k.value for k in ProjectKind}) == 4
        assert ProjectKind.UNKNOWN is not ProjectKind.FAB


class TestEqualityIsRecordEqualityNotProjectIdentity:
    """Two records can use the very same words for what may or may not be the
    same project. Nothing here answers that question -- not the surface, not
    the place, not the class."""

    def test_the_same_words_in_two_records_are_two_references(self):
        (a,) = claim_refs(SINGAPORE, issuer="AA")
        (b,) = claim_refs(SINGAPORE, issuer="BB")
        assert a.surface == b.surface and a.location_surface == b.location_surface
        assert a != b, "they differ by provenance, which is all we actually know"

    def test_sharing_a_place_says_nothing(self):
        (claim_ref,) = claim_refs(SINGAPORE)
        (action_ref,) = action_refs(BOISE)
        assert claim_ref.location_surface != action_ref.location_surface
        assert claim_ref.kind is action_ref.kind, "same class, and still nothing follows"
