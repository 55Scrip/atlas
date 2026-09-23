"""Project Relationship v1 -- the frozen Sprint 33 benchmark.

Every paragraph below is verbatim from a held 10-K at 4120dab. The layer
records what a filing says about how the things it names relate. It never
says whether two of them are the same project, and the tests hold it to that
as firmly as they hold it to finding the relationships at all.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.project_relationship import (
    Direction, EndpointRole, RelationshipKind, SourceParagraph, read_relationships,
)

BOISE_AND_CLAY = (
    "To support projected memory demand in the second half of the decade, we will need to add new "
    "DRAM wafer capacity. Following the enactment of the U.S. CHIPS and Science Act of 2022 "
    "(“CHIPS Act”), we announced plans to invest in two leading-edge memory manufacturing fab "
    "facilities in the United States, based on CHIPS Act support through grants and investment tax "
    "credits. As part of this plan, in September 2022, we broke ground on a leading-edge memory "
    "manufacturing fab in Boise, Idaho. Construction of the fab began in October 2023, with "
    "meaningful DRAM output projected in 2027. In addition, in October 2022, we announced plans to "
    "build a second leading-edge DRAM manufacturing facility, consisting of up to four fabs to be "
    "built over the next 20-plus years, in Clay, New York.")
PJM_DEFINED = (
    "AROs for nuclear generation decommissioning relate to the Comanche Peak plant in ERCOT and the "
    "facilities acquired from Energy Harbor which include the Beaver Valley, Perry and Davis-Besse "
    "plants in PJM (the PJM nuclear facilities).")
WEST_TEXAS_SECOND = (
    "In August 2024, the PUCT notified Vistra that an application for one of its west Texas advanced "
    "simple-cycle peaking plants was selected for due diligence as part of the Texas Energy Fund "
    "loan program, which is ongoing. Vistra's other application for a second west Texas gas plant "
    "remains active.")
MARTIN_LAKE = ("On November 27, 2024, we experienced a fire at Unit 1 of our Martin Lake generation "
               "plant in ERCOT. We wrote-off the plant's net book value in December 2024.")
CREDIT_FACILITY = (
    "In conjunction with the Commercial Paper Program, the Company has a committed five-year "
    "unsecured $8 billion revolving credit facility (the “Credit Facility”). The facility "
    "expires in 2029.")
MARKET_PARENS = (
    "Acquisition of Natural Gas Generation Facilities — In 2025, we acquired 2,557 MW of natural "
    "gas generation facilities in Delaware and Pennsylvania (PJM), Rhode Island (ISO-NE), New York "
    "(NYISO), and California (CAISO).")
BOARD = ("Our Board of Directors was comprised of five men and four women as of August 29, 2024.")
CAPTION = ("In connection with the business combination, the Company recorded $5.6 billion in "
           "property, plant and equipment which includes the value of the three nuclear power plants.")


def paras(*texts, issuer="ZZ", accession="ZZ-1", section="PROPERTIES", period="2025-10"):
    return [SourceParagraph(issuer=issuer, accession=accession, section=section, ordinal=i,
                            text=t, period=period) for i, t in enumerate(texts)]


def of(records, kind):
    return [r for r in records if r.kind is kind]


class TestWhatTheFilingSaysOutright:
    def test_consisting_of_is_a_part_whole_statement(self):
        (r,) = of(read_relationships(paras(BOISE_AND_CLAY)), RelationshipKind.PART_WHOLE)
        assert "a second leading-edge DRAM manufacturing facility" in r.left.surface
        assert "up to four fabs" in r.right.surface
        assert r.direction is Direction.WHOLE_TO_PART
        assert r.left.role is EndpointRole.WHOLE and r.right.role is EndpointRole.PART
        assert r.context.connective == "consisting of"

    def test_which_include_is_a_part_whole_statement(self):
        (r,) = of(read_relationships(paras(PJM_DEFINED)), RelationshipKind.PART_WHOLE)
        assert "the facilities acquired from Energy Harbor" in r.left.surface
        assert "Beaver Valley, Perry and Davis-Besse plants" in r.right.surface
        assert r.direction is Direction.WHOLE_TO_PART

    def test_a_short_name_the_source_gives(self):
        (r,) = of(read_relationships(paras(PJM_DEFINED)), RelationshipKind.DEFINED_TERM)
        assert r.left.surface == "the PJM nuclear facilities"
        assert "the facilities acquired from Energy Harbor" in r.right.surface
        assert r.direction is Direction.TERM_TO_REFERENT

    def test_an_ordinal_names_one_of_a_set_without_naming_the_other(self):
        records = of(read_relationships(paras(WEST_TEXAS_SECOND)),
                     RelationshipKind.ORDINAL_DISTINCTION)
        assert [r.left.surface for r in records] == ["a second west Texas gas plant"]
        assert records[0].right is None, "the source does not say which plant the first one is"
        assert records[0].direction is Direction.NONE

    def test_an_ordinal_keeps_the_place_the_source_attached(self):
        records = of(read_relationships(paras(
            "On June 11, 2025, we entered into amendments to the direct funding agreements to add a "
            "second planned fab in Boise, Idaho, and allocate certain award funding.")),
            RelationshipKind.ORDINAL_DISTINCTION)
        assert [r.left.surface for r in records] == ["a second planned fab in Boise, Idaho"]

    def test_a_bare_definite_phrase_points_back_at_the_one_candidate(self):
        (r,) = of(read_relationships(paras(BOISE_AND_CLAY)),
                  RelationshipKind.ANAPHORIC_COREFERENCE)
        assert r.left.surface == "the fab"
        assert r.right.surface == "a leading-edge memory manufacturing fab"
        assert r.direction is Direction.ANAPHOR_TO_ANTECEDENT

    def test_a_possessive_antecedent_keeps_its_name(self):
        (r,) = of(read_relationships(paras(MARTIN_LAKE)),
                  RelationshipKind.ANAPHORIC_COREFERENCE)
        assert r.right.surface == "our Martin Lake generation plant"


class TestTheWordsAreNotEnough:
    def test_a_facility_that_is_a_line_of_credit_is_not_a_plant(self):
        assert read_relationships(paras(CREDIT_FACILITY)) == ()

    def test_market_abbreviations_are_not_definitions(self):
        assert of(read_relationships(paras(MARKET_PARENS)), RelationshipKind.DEFINED_TERM) == []

    def test_a_balance_sheet_caption_is_not_a_plant(self):
        assert of(read_relationships(paras(CAPTION)), RelationshipKind.PART_WHOLE) == []

    def test_a_part_whole_sentence_about_people_is_not_about_plants(self):
        assert read_relationships(paras(BOARD)) == ()

    @pytest.mark.parametrize("sentence", [
        "Construction of the fab began in October 2023, with first DRAM wafer output projected in "
        "the second half of calendar 2027.",
        "We will need to add new DRAM wafer capacity to support projected memory demand in the "
        "second half of the decade."])
    def test_a_second_half_is_not_a_second_plant(self, sentence):
        assert of(read_relationships(paras(sentence)),
                  RelationshipKind.ORDINAL_DISTINCTION) == []

    def test_an_anaphor_with_two_candidates_is_refused(self):
        """SYNTHETIC: the corpus holds no paragraph of this shape. An ambiguous
        antecedent is not a harder problem -- the source has not said which."""
        assert of(read_relationships(paras(
            "We operate a leading-edge fab in one region and a modernised fab in another region. "
            "Construction of the fab began in October 2023.")),
            RelationshipKind.ANAPHORIC_COREFERENCE) == []

    def test_a_definite_phrase_cannot_be_its_own_antecedent(self):
        assert of(read_relationships(paras(
            "Decommissioning may continue until the end of the life of the facility.")),
            RelationshipKind.ANAPHORIC_COREFERENCE) == []


class TestNothingReachesAcrossDocuments:
    def test_a_pronoun_does_not_reach_into_another_filing(self):
        first = paras("In September 2022, we broke ground on a leading-edge memory manufacturing "
                      "fab in Boise, Idaho.", accession="ZZ-2024")
        second = paras("Construction of the fab began in October 2023.", accession="ZZ-2025")
        assert of(read_relationships(first + second),
                  RelationshipKind.ANAPHORIC_COREFERENCE) == []

    def test_no_record_ever_spans_two_documents(self):
        records = read_relationships(
            paras(BOISE_AND_CLAY, accession="ZZ-2024") + paras(PJM_DEFINED, accession="ZZ-2025"))
        assert records
        for r in records:
            if r.right is not None:
                assert r.left.span.accession == r.right.span.accession

    def test_the_same_words_in_two_filings_are_not_a_relationship(self):
        twice = (paras(BOISE_AND_CLAY, accession="ZZ-2024")
                 + paras(BOISE_AND_CLAY, accession="ZZ-2025"))
        kinds = {r.kind for r in read_relationships(twice)}
        assert kinds == {r.kind for r in read_relationships(paras(BOISE_AND_CLAY))}


class TestNoIdentityIsOffered:
    def test_the_package_answers_no_identity_question(self):
        import atlas.analysis_engine.project_relationship as pkg
        banned = ("same", "not_same", "identi", "equal", "match", "resolve", "alias", "canonical")
        offered = [n for n in dir(pkg) if not n.startswith("_")]
        assert not [n for n in offered if any(w in n.lower() for w in banned)], offered

    def test_a_relationship_is_not_a_verdict(self):
        """Two entries of a part-whole are related and not thereby the same, and
        an ordinal names a counterpart it never identifies."""
        records = read_relationships(paras(BOISE_AND_CLAY))
        for r in records:
            assert not hasattr(r, "same")
            assert not hasattr(r, "identity")
        assert {r.kind for r in records} <= set(RelationshipKind)

    def test_provenance_points_back_at_the_words(self):
        for r in read_relationships(paras(PJM_DEFINED, issuer="ZZ", accession="ZZ-7",
                                          section="FINANCIAL_STATEMENTS", period="2025-02")):
            assert r.left.span.issuer == "ZZ" and r.left.span.accession == "ZZ-7"
            assert r.left.span.section == "FINANCIAL_STATEMENTS"
            assert r.source_period == "2025-02"
            assert r.licensing_surface


class TestTheSameAnswerEveryTime:
    def test_deterministic(self):
        assert read_relationships(paras(BOISE_AND_CLAY)) == read_relationships(paras(BOISE_AND_CLAY))

    def test_idempotent(self):
        given = paras(BOISE_AND_CLAY)
        assert read_relationships(given) == read_relationships(given)

    def test_order_independent(self):
        given = paras(BOISE_AND_CLAY, PJM_DEFINED, WEST_TEXAS_SECOND)
        assert set(read_relationships(given)) == set(read_relationships(list(reversed(given))))


class TestSurfacesAreTheSourcesOwnWords:
    """A surface a later layer cannot find in the filing is a surface it
    cannot check."""

    @pytest.mark.parametrize("text", [BOISE_AND_CLAY, PJM_DEFINED, WEST_TEXAS_SECOND, MARTIN_LAKE])
    def test_every_endpoint_surface_appears_verbatim_in_its_paragraph(self, text):
        records = read_relationships(paras(text))
        assert records
        for r in records:
            assert r.left.surface in text, r.left.surface
            if r.right is not None:
                assert r.right.surface in text, r.right.surface
            assert r.licensing_surface.lower() in text.lower()


class TestAnAntecedentHasToIntroduceSomething:
    def test_a_definite_phrase_between_the_two_takes_the_reference(self):
        """Verbatim from a held filing: the nearest indefinite determiner is
        'a majority', but the head belongs to 'the manufacturing facility',
        which is itself already pointing somewhere."""
        assert of(read_relationships(paras(
            "The Company is responsible for a majority of the construction costs related to the "
            "manufacturing facility. The facility is expected to be completed in 2026.")),
            RelationshipKind.ANAPHORIC_COREFERENCE) == []

    def test_a_defined_term_has_to_look_like_a_definition(self):
        """Verbatim shape from a held filing. '(Facility Agreement)' names an
        agreement; a definition the source writes gives a short name with
        'the'."""
        assert of(read_relationships(paras(
            "In 2023, Vistra Operations entered into a facility agreement (Facility Agreement) "
            "with a syndicate of banks.")), RelationshipKind.DEFINED_TERM) == []
