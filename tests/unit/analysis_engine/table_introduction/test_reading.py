"""What licenses "this paragraph presents the table below it", and what does not.

The negatives here are not invented: each is a shape the held corpus actually
puts in front of the rule -- headings, page numbers, units labels, backward
references, and colon paragraphs whose colon introduces something else.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.table_introduction import (
    LicensingBasis,
    SourceParagraph,
    SourceTable,
    TABLE_INTRODUCTION_VERSION,
    read_table_introductions,
)

_ISSUER, _ACC, _SECTION, _PERIOD = "AAA", "0000000-25-000001", "FINANCIAL_STATEMENTS", "2025-01"


def _p(index: int, text: str, *, accession: str = _ACC, section: str = _SECTION) -> SourceParagraph:
    return SourceParagraph(issuer=_ISSUER, accession=accession, section=section,
                           source_event_index=index, text=text, period=_PERIOD)


def _t(index: int, *, accession: str = _ACC, section: str = _SECTION, rows: int = 8) -> SourceTable:
    return SourceTable(issuer=_ISSUER, accession=accession, section=section,
                       source_event_index=index, row_count=rows, column_count=6, period=_PERIOD)


class TestWhatLicensesARecord:
    def test_a_colon_paragraph_immediately_before_a_table(self):
        records = read_table_introductions([_p(10, "Debt consisted of the following:")], [_t(11)])
        assert len(records) == 1
        record = records[0]
        assert record.licensing_bases == (LicensingBasis.COLON_ADJACENCY,)
        assert record.introducer.source_event_index == 10
        assert record.table.source_event_index == 11
        assert record.licensing_surface == "Debt consisted of the following:"
        assert record.source_period == _PERIOD
        assert record.version == TABLE_INTRODUCTION_VERSION

    def test_a_forward_table_reference_without_any_colon(self):
        records = read_table_introductions(
            [_p(4, "The following table presents segment operating income (in millions).")], [_t(5)])
        assert [r.licensing_bases for r in records] == [
            (LicensingBasis.EXPLICIT_DEICTIC_TABLE_REFERENCE,)]

    def test_the_table_below_is_the_same_forward_reference(self):
        records = read_table_introductions(
            [_p(4, "The table below displays the reconciliation.")], [_t(5)])
        assert len(records) == 1

    def test_one_word_may_sit_inside_the_reference(self):
        """The corpus says "the following maturity table" once, and it introduces
        the table as plainly as the other 273 do."""
        records = read_table_introductions(
            [_p(4, "The following maturity table presents the net liability.")], [_t(5)])
        assert len(records) == 1

    def test_both_bases_are_kept_when_both_hold(self):
        records = read_table_introductions(
            [_p(4, "The following table summarizes Goodwill:")], [_t(5)])
        assert records[0].licensing_bases == (
            LicensingBasis.COLON_ADJACENCY, LicensingBasis.EXPLICIT_DEICTIC_TABLE_REFERENCE)


class TestWhatDoesNot:
    def test_a_colon_with_no_table_after_it(self):
        """Colon paragraphs in the corpus introduce a bullet run 276 times and
        prose 75 times."""
        assert read_table_introductions(
            [_p(10, "Management believes the following is a critical estimate:"),
             _p(11, "Our estimate of useful life is reviewed annually.")], []) == ()

    def test_a_paragraph_before_a_table_that_introduces_nothing(self):
        assert read_table_introductions(
            [_p(10, "Depreciation expense for 2025 and 2024 was $521 million and $454 million.")],
            [_t(11)]) == ()

    def test_a_heading_before_a_table(self):
        assert read_table_introductions([_p(10, "Consolidated Balance Sheets")], [_t(11)]) == ()

    def test_a_page_number_before_a_table(self):
        assert read_table_introductions([_p(10, "66.")], [_t(11)]) == ()

    def test_a_units_label_before_a_table(self):
        assert read_table_introductions([_p(10, "(in millions)")], [_t(11)]) == ()

    def test_a_backward_reference_is_not_a_forward_one(self):
        for backward in ("The table above excludes executed leases.",
                         "The notes in the table above rank equally.",
                         "See the preceding table for maturities."):
            assert read_table_introductions([_p(10, backward)], [_t(11)]) == (), backward

    def test_the_bare_noun_table_is_not_enough(self):
        assert read_table_introductions(
            [_p(10, "We maintain a table of authorised signatories.")], [_t(11)]) == ()

    def test_following_on_its_own_is_not_enough(self):
        assert read_table_introductions(
            [_p(10, "The following year we completed the acquisition.")], [_t(11)]) == ()

    def test_a_presenting_verb_on_its_own_is_not_enough(self):
        assert read_table_introductions(
            [_p(10, "Management presents its analysis of liquidity annually.")], [_t(11)]) == ()

    def test_a_colon_inside_the_prose_is_not_a_colon_at_the_end(self):
        """An auditor's report sits immediately above a table in four filings and
        carries an internal colon before an enumeration. It introduces nothing:
        only a colon that CLOSES the paragraph points at what comes next."""
        audit_report = (
            "The critical audit matter communicated below is a matter arising from the current "
            "period audit of the financial statements that was communicated or required to be "
            "communicated to the audit committee and that: (1) relates to accounts or disclosures "
            "that are material to the financial statements and (2) involved our especially "
            "challenging, subjective or complex judgments. The communication of the critical audit "
            "matter does not alter in any way our opinion on the consolidated financial statements."
        )
        assert read_table_introductions([_p(10, audit_report)], [_t(11)]) == ()

    def test_a_defined_term_colon_mid_sentence_introduces_nothing(self):
        text = ('Until such time as there are no shares that are not earned (the "Unearned Shares"): '
                "the award remains outstanding and is remeasured each period.")
        assert read_table_introductions([_p(10, text)], [_t(11)]) == ()

    def test_a_bullet_never_introduces_the_table_under_it(self):
        assert read_table_introductions([_p(10, "•India: construction is progressing:")],
                                        [_t(11)]) == ()

    def test_a_paragraph_separated_from_the_table_by_anything_at_all(self):
        """A page break between the two is the corpus's own shape, four times. The
        rule refuses rather than guess which paragraphs are page furniture."""
        assert read_table_introductions(
            [_p(10, "Accrued warranty activity consisted of the following:"), _p(11, "66")],
            [_t(12)]) == ()

    def test_a_table_following_another_table_is_not_introduced_by_it(self):
        records = read_table_introductions([_p(10, "Debt consisted of the following:")],
                                          [_t(11), _t(12)])
        assert [r.table.source_event_index for r in records] == [11]

    def test_a_paragraph_after_its_table_introduces_nothing(self):
        assert read_table_introductions([_p(12, "Debt consisted of the following:")], [_t(11)]) == ()


class TestTheLicensingSurface:
    _MICRON_SHAPED = ("Our corporate headquarters are located in Boise, Idaho. In addition to our "
                      "principal facilities, we lease sites used for design and marketing. The "
                      "following is a summary of our principal facilities as of August 28, 2025:")

    def test_it_is_the_introducing_sentence_and_not_the_whole_paragraph(self):
        records = read_table_introductions([_p(10, self._MICRON_SHAPED)], [_t(11)])
        assert records[0].licensing_surface == (
            "The following is a summary of our principal facilities as of August 28, 2025:")

    def test_the_opening_sentence_of_a_paragraph_licenses_nothing(self):
        surface = read_table_introductions([_p(10, self._MICRON_SHAPED)], [_t(11)])[0].licensing_surface
        assert "Boise" not in surface
        assert "headquarters" not in surface

    def test_an_abbreviation_does_not_end_a_sentence(self):
        text = "Outside the U.S. we invest through ASU No. 2023-08. Debt consisted of the following:"
        records = read_table_introductions([_p(10, text)], [_t(11)])
        assert records[0].licensing_surface == "Debt consisted of the following:"

    def test_a_reference_earlier_in_the_paragraph_is_still_quoted(self):
        text = ("Our chief operating decision maker reviews no asset information by segment. The "
                "table below presents long-lived assets by country.")
        records = read_table_introductions([_p(10, text)], [_t(11)])
        assert records[0].licensing_surface == (
            "The table below presents long-lived assets by country.")


class TestIdentityAndStability:
    _CORPUS = ([_p(10, "Debt consisted of the following:"), _p(12, "Other information:"),
                _p(20, "Debt consisted of the following:", accession="0000000-24-000001")],
               [_t(11), _t(13), _t(21, accession="0000000-24-000001")])

    def test_one_record_per_table_at_most(self):
        records = read_table_introductions(*self._CORPUS)
        assert len({(r.table.accession, r.table.source_event_index) for r in records}) == len(records)

    def test_identical_text_in_two_filings_stays_two_observations(self):
        records = read_table_introductions(*self._CORPUS)
        same = [r for r in records if r.licensing_surface == "Debt consisted of the following:"]
        assert len(same) == 2
        assert {r.introducer.accession for r in same} == {"0000000-25-000001", "0000000-24-000001"}

    def test_repeated_text_inside_one_filing_stays_distinct(self):
        paragraphs = [_p(10, "Debt consisted of the following:"),
                      _p(12, "Debt consisted of the following:")]
        records = read_table_introductions(paragraphs, [_t(11), _t(13)])
        assert {r.introducer.source_event_index for r in records} == {10, 12}

    def test_reading_twice_gives_the_same_records(self):
        assert read_table_introductions(*self._CORPUS) == read_table_introductions(*self._CORPUS)

    def test_the_order_the_objects_arrive_in_does_not_matter(self):
        paragraphs, tables = self._CORPUS
        forward = read_table_introductions(paragraphs, tables)
        backward = read_table_introductions(list(reversed(paragraphs)), list(reversed(tables)))
        assert set(forward) == set(backward)
        assert forward == backward

    def test_a_section_boundary_separates_two_documents_worth_of_objects(self):
        records = read_table_introductions(
            [_p(10, "Debt consisted of the following:", section="MDA")],
            [_t(11, section="FINANCIAL_STATEMENTS")])
        assert records == ()


class TestItSaysNothingMore:
    def test_the_record_carries_no_judgement_of_any_kind(self):
        import dataclasses

        from atlas.analysis_engine.table_introduction import TableIntroductionEvidence

        names = {f.name for f in dataclasses.fields(TableIntroductionEvidence)}
        assert names == {"introducer", "table", "licensing_surface", "licensing_bases",
                         "source_period", "version"}
        for banned in ("confidence", "probability", "score", "topic", "project", "identity",
                       "same", "scope", "governs", "supports", "materiality", "recommendation"):
            assert not any(banned in n for n in names), banned

    def test_there_are_exactly_two_licensing_bases(self):
        assert [b.value for b in LicensingBasis] == [
            "colon_adjacency", "explicit_deictic_table_reference"]
