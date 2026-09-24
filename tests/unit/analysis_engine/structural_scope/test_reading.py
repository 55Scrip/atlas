"""Structural Scope v1 -- the frozen Sprint 36 benchmark.

Micron's Properties section is the falsification set, and it is a good one
because it contains both cases: a colon that introduces a list, and a colon
that introduces a table the parser holds elsewhere. Every paragraph below is
verbatim from the held filing at b18066a.

What the layer may use is narrow by necessity. A parsed section carries an item
heading, paragraphs and tables, and no subsections -- 0 of 357 across the 22
held filings -- so a heading governing a region of prose cannot be represented
at all. These tests hold the layer to what remains.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.structural_scope import (
    BoundaryKind, GovernedUnitKind, GovernorKind, SourceParagraph, read_scopes,
)

US_PROSE = [
    "Our corporate headquarters are located in Boise, Idaho. In addition to our principal "
    "facilities described below, we own or lease numerous other facilities in locations "
    "throughout the world used for design, R&D, and sales and marketing activities. The "
    "following is a summary of our principal facilities as of August 28, 2025:",
    "We believe that our existing facilities are suitable and adequate for our present purposes.",
    "As part of this plan, in September 2022, we broke ground on a leading-edge memory "
    "manufacturing fab in Boise, Idaho.",
    "47 | 2025 10-K",
    "Table of Contents",
    "Our announced plan for New York includes construction of a leading-edge DRAM memory "
    "manufacturing site, consisting of up to four fabs to be built over the next 20-plus "
    "years, in Clay, New York.",
]
GOVERNOR = ("Outside the U.S., we are investing in manufacturing technologies, facilities and "
            "equipment, and R&D, and advancing our global back-end assembly and test network. "
            "Planned investments and those underway include the following:")
BULLETS = [
    "•India: our construction is progressing for the assembly and test facility in Gujarat;",
    "•Japan: we are modernizing our Hiroshima manufacturing facility;",
    "•Singapore: we broke ground on an HBM advanced packaging facility; and",
    "•Taiwan: we are modernizing our production capacity for DRAM and HBM products.",
]
AFTER = ("We do not identify or allocate assets by operating segment, other than goodwill.")


def paras(texts, issuer="ZZ", accession="ZZ-1", section="PROPERTIES", period="2025-10"):
    return [SourceParagraph(issuer=issuer, accession=accession, section=section, ordinal=i,
                            text=t, period=period) for i, t in enumerate(texts)]


MICRON = US_PROSE + [GOVERNOR] + BULLETS + [AFTER]


class TestTheSourceShowsWhereAListBeginsAndEnds:
    def test_the_lead_in_governs_exactly_its_own_bullets(self):
        (scope,) = read_scopes(paras(MICRON))
        assert scope.governor_surface == GOVERNOR
        assert scope.governor_kind is GovernorKind.LEAD_IN
        assert scope.governor_span.paragraph_ordinal == 6
        assert [u.span.paragraph_ordinal for u in scope.governed_units] == [7, 8, 9, 10]
        assert [u.position for u in scope.governed_units] == [1, 2, 3, 4]
        assert all(u.kind is GovernedUnitKind.BULLET for u in scope.governed_units)

    def test_the_prose_above_is_outside_the_scope(self):
        (scope,) = read_scopes(paras(MICRON))
        inside = {u.span.paragraph_ordinal for u in scope.governed_units}
        assert inside.isdisjoint(range(0, 6)), "the Boise and New York prose is not governed"

    def test_the_scope_ends_at_the_first_unmarked_paragraph(self):
        (scope,) = read_scopes(paras(MICRON))
        assert scope.boundary_kind is BoundaryKind.FIRST_UNMARKED_PARAGRAPH
        assert scope.boundary_span.paragraph_ordinal == 11
        assert scope.boundary_span.paragraph_ordinal not in {
            u.span.paragraph_ordinal for u in scope.governed_units}

    def test_the_singapore_unit_is_recorded_as_a_unit_and_nothing_more(self):
        (scope,) = read_scopes(paras(MICRON))
        singapore = [u for u in scope.governed_units if u.surface.startswith("•Singapore")]
        assert len(singapore) == 1
        assert not hasattr(singapore[0], "meaning")
        assert not hasattr(scope, "interpretation")

    def test_surfaces_and_period_are_the_sources_own(self):
        (scope,) = read_scopes(paras(MICRON, period="2025-10"))
        assert scope.source_period == "2025-10"
        for unit, raw in zip(scope.governed_units, BULLETS):
            assert unit.surface == raw


class TestAColonOnItsOwnLicensesNothing:
    def test_a_colon_followed_by_prose_governs_nothing(self):
        """Verbatim: Micron's Properties opens with a colon introducing the
        principal-facilities table, which the parser holds apart from the
        paragraph stream. Of 944 colon-terminated paragraphs in the held
        filings, 691 are followed by prose."""
        assert read_scopes(paras(US_PROSE)) == ()

    def test_only_the_list_governor_is_read_when_both_colons_are_present(self):
        (scope,) = read_scopes(paras(MICRON))
        assert scope.governor_surface == GOVERNOR
        assert not scope.governor_surface.startswith("Our corporate headquarters")

    def test_a_list_with_no_paragraph_after_it_is_not_a_scope(self):
        """Without a following paragraph the source never shows where the scope
        stops, and an unbounded scope is the one thing worse than none."""
        assert read_scopes(paras([GOVERNOR] + BULLETS)) == ()


class TestStructureIsTheBasisAndNotWording:
    def test_the_governor_wording_can_change_freely(self):
        (a,) = read_scopes(paras([GOVERNOR] + BULLETS + [AFTER]))
        (b,) = read_scopes(paras(["Region Foo comprises the following:"] + BULLETS + [AFTER]))
        assert [u.span.paragraph_ordinal for u in a.governed_units] == \
               [u.span.paragraph_ordinal for u in b.governed_units]

    def test_project_words_are_not_required(self):
        nonsense = ["•Quux: the frobnicator is being widgeted;",
                    "•Blorb: the thingummy is nearly quoxed."]
        (scope,) = read_scopes(paras(["Some grouping of items includes the following:"]
                                     + nonsense + ["An ordinary closing paragraph."]))
        assert len(scope.governed_units) == 2

    def test_removing_the_colon_removes_the_scope(self):
        assert read_scopes(paras([GOVERNOR.rstrip(":") + "."] + BULLETS + [AFTER])) == ()

    def test_removing_the_bullet_markers_removes_the_scope(self):
        plain = [b.lstrip("•") for b in BULLETS]
        assert read_scopes(paras([GOVERNOR] + plain + [AFTER])) == ()

    def test_adjacency_alone_is_not_scope(self):
        assert read_scopes(paras([GOVERNOR.rstrip(":") + "."] + [b.lstrip("•") for b in BULLETS]
                                 + [AFTER])) == ()

    def test_page_furniture_interrupts_a_list_without_ending_it(self):
        """Every interruption found inside a run in the held filings is a page
        number, a running header or a contents line -- never a heading."""
        split = [GOVERNOR, BULLETS[0], "9", "VISTRA CORP.", BULLETS[1], AFTER]
        (scope,) = read_scopes(paras(split))
        assert [u.span.paragraph_ordinal for u in scope.governed_units] == [1, 4]
        assert scope.boundary_span.paragraph_ordinal == 5


class TestNothingReachesAcrossADocumentOrASection:
    def test_a_list_cannot_span_two_filings(self):
        governor = [SourceParagraph("ZZ", "ZZ-2024", "PROPERTIES", 0, GOVERNOR, "2024-10")]
        rest = [SourceParagraph("ZZ", "ZZ-2025", "PROPERTIES", i, t, "2025-10")
                for i, t in enumerate(BULLETS + [AFTER], start=1)]
        assert read_scopes(governor + rest) == ()

    def test_a_list_cannot_span_two_sections(self):
        governor = [SourceParagraph("ZZ", "ZZ-1", "PROPERTIES", 0, GOVERNOR, "2025-10")]
        rest = [SourceParagraph("ZZ", "ZZ-1", "MDA", i, t, "2025-10")
                for i, t in enumerate(BULLETS + [AFTER], start=1)]
        assert read_scopes(governor + rest) == ()

    def test_same_issuer_is_not_enough(self):
        governor = [SourceParagraph("ZZ", "ZZ-A", "BUSINESS", 0, GOVERNOR, "2025-10")]
        rest = [SourceParagraph("ZZ", "ZZ-B", "BUSINESS", i, t, "2025-10")
                for i, t in enumerate(BULLETS + [AFTER], start=1)]
        assert read_scopes(governor + rest) == ()


class TestScopeIsLayoutAndNotMeaning:
    def test_the_package_answers_no_question_about_meaning(self):
        import atlas.analysis_engine.structural_scope as pkg
        banned = ("same", "not_same", "identi", "equal", "match", "resolve", "alias", "canonical",
                  "project", "geograph", "country", "outside", "region", "semantic", "topic")
        offered = [n for n in dir(pkg) if not n.startswith("_")]
        assert not [n for n in offered if any(w in n.lower() for w in banned)], offered

    def test_a_non_project_list_is_read_the_same_way(self):
        """A risk list. 128 of the 273 scopes in the held filings are in risk or
        forward-looking sections, and the layer must not care."""
        risk = ["The ownership and operation of nuclear generation facilities involves certain "
                "risks. These risks include:",
                "•the costs of storing and maintaining spent nuclear fuel;",
                "•uncertainties with respect to decommissioning.",
                "We maintain insurance against these risks."]
        (scope,) = read_scopes(paras(risk, section="RISK_FACTORS"))
        assert len(scope.governed_units) == 2
        assert scope.boundary_span.paragraph_ordinal == 3


class TestTheSameAnswerEveryTime:
    def test_deterministic(self):
        assert read_scopes(paras(MICRON)) == read_scopes(paras(MICRON))

    def test_idempotent(self):
        given = paras(MICRON)
        assert read_scopes(given) == read_scopes(given)

    def test_document_order_does_not_change_the_result(self):
        given = paras(MICRON)
        assert read_scopes(given) == read_scopes(list(reversed(given)))

    def test_governed_units_keep_source_order(self):
        (scope,) = read_scopes(paras(MICRON))
        ordinals = [u.span.paragraph_ordinal for u in scope.governed_units]
        assert ordinals == sorted(ordinals)

    def test_one_paragraph_is_one_unit(self):
        (scope,) = read_scopes(paras(MICRON))
        assert len({u.span.paragraph_ordinal for u in scope.governed_units}) == \
               len(scope.governed_units)
