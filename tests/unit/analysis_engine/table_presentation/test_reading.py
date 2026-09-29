"""When a table's shape shows it presents no data -- and when it says nothing.

The shapes here are the ones the held filings actually set in table markup: a
cover-page checkbox, a signature block, a page header, a heading, a panel of
bulleted prose. The negatives are the shapes that must stay untouched, including
a real data table whose lone currency symbol takes it past the threshold.
"""
from __future__ import annotations

from atlas.analysis_engine.table_presentation import (
    MAX_NON_EMPTY_CELLS_WITHOUT_DATA,
    LicensingFeature,
    SourceTable,
    TABLE_PRESENTATION_VERSION,
    TablePresentationEvidence,
    TablePresentationKind,
    non_empty_cell_count,
    read_table_presentation,
)

_ISSUER, _ACC, _SECTION, _PERIOD = "AAA", "0000000-25-000001", "FINANCIAL_STATEMENTS", "2025-01"


def _t(index: int, *cells: str, accession: str = _ACC, section: str = _SECTION) -> SourceTable:
    return SourceTable(issuer=_ISSUER, accession=accession, section=section,
                       source_event_index=index, cell_texts=cells, period=_PERIOD)


class TestWhatItSays:
    def test_a_page_header_of_two_cells(self):
        records = read_table_presentation([_t(10, "", "Table of Contents", "", "Alphabet Inc.", "")])
        assert len(records) == 1
        record = records[0]
        assert record.kind is TablePresentationKind.NOT_A_DATA_PRESENTATION
        assert record.licensing_feature is LicensingFeature.NON_EMPTY_CELL_COUNT
        assert record.observed_value == 2
        assert record.threshold == MAX_NON_EMPTY_CELLS_WITHOUT_DATA
        assert record.table.source_event_index == 10
        assert record.source_period == _PERIOD
        assert record.version == TABLE_PRESENTATION_VERSION

    def test_a_heading_set_in_a_table(self):
        assert len(read_table_presentation([_t(10, "", "Note 10. Stock-Based Compensation", "")])) == 1

    def test_a_table_with_nothing_in_it_at_all(self):
        """45 of the held tables are pure spacers. They fall inside the same rule
        rather than getting a kind of their own."""
        records = read_table_presentation([_t(10, "", "", "", "", "", "")])
        assert len(records) == 1
        assert records[0].observed_value == 0

    def test_a_cover_page_checkbox_block(self):
        assert len(read_table_presentation([_t(10, "(Mark One)", "", "☒",
                                               "ANNUAL REPORT PURSUANT TO SECTION 13")])) == 1

    def test_a_panel_of_bulleted_prose(self):
        """The three tables Sprint 40 could only call ambiguous. Reached here by
        counting cells, not by noticing the bullets."""
        records = read_table_presentation([
            _t(10, "", "", "•Security solutions•Consumer acquisition",
               "•Processing and gateway•Other solutions", "", "")])
        assert records[0].observed_value == 2

    def test_exactly_three_non_empty_cells_is_inside_the_rule(self):
        records = read_table_presentation([_t(10, "*By:", "/s/Jean Hu", "Jean Hu, Attorney-in-Fact")])
        assert len(records) == 1
        assert records[0].observed_value == 3


class TestWhatItStaysSilentAbout:
    def test_four_non_empty_cells_licenses_nothing(self):
        """The boundary. A signature block with four cells gets no evidence, even
        though a reader would call it layout: the measured residue holds both
        classes, so there is nothing safe to say."""
        assert read_table_presentation([_t(10, "Delaware", "94-1655526",
                                           "(State of incorporation)", "(I.R.S. Employer No.)")]) == ()

    def test_a_small_data_table_is_left_alone(self):
        """Salesforce prints "Total revenues | $ | 399" and "Pretax income | 24".
        Five non-empty cells, because the lone currency symbol counts."""
        assert read_table_presentation(
            [_t(10, "Total revenues", "$", "399", "Pretax income", "24")]) == ()

    def test_a_full_data_matrix_is_left_alone(self):
        cells = tuple(str(n) for n in range(40))
        assert read_table_presentation([_t(10, *cells)]) == ()

    def test_no_data_presentation_kind_exists(self):
        """Four or more non-empty cells is not evidence of anything. There is no
        second kind to emit, and the enum has no second member."""
        assert [k.value for k in TablePresentationKind] == ["not_a_data_presentation"]

    def test_silence_is_not_a_record_with_a_different_kind(self):
        records = read_table_presentation([_t(10, "a", "b", "c", "d"), _t(20, "a", "b")])
        assert [r.table.source_event_index for r in records] == [20]


class TestWhatCountsAsANonEmptyCell:
    def test_whitespace_of_any_kind_is_empty(self):
        """The filing parser collapses whitespace and strips before this layer
        sees a cell, so a space, a non-breaking space and an em space all arrive
        as the empty string. Counted here anyway, so the rule cannot drift."""
        assert non_empty_cell_count(["", " ", " ", " ", "\t\n "]) == 0

    def test_a_lone_currency_symbol_counts(self):
        assert non_empty_cell_count(["$"]) == 1

    def test_a_lone_percent_counts(self):
        assert non_empty_cell_count(["%"]) == 1

    def test_a_lone_dash_counts(self):
        assert non_empty_cell_count(["—", "-", "–"]) == 3

    def test_a_numeric_zero_counts(self):
        """The filing printed a value. 701 cells in the held corpus are a lone
        zero, and treating them as absent would make a data table look empty."""
        assert non_empty_cell_count(["0"]) == 1

    def test_the_count_is_of_cells_not_rows_or_columns(self):
        records = read_table_presentation([_t(10, "a", "", "", "", "", "", "", "", "", "", "", "")])
        assert records[0].observed_value == 1


class TestItReadsShapeAndNotWords:
    def test_the_words_in_a_cell_never_matter(self):
        """Substituting every word for another of the same shape cannot move the
        verdict, because no rule here looks at a word."""
        a = read_table_presentation([_t(10, "Total revenues", "399", "")])
        b = read_table_presentation([_t(10, "Zzzz qqqqqqqq", "111", "")])
        assert [r.observed_value for r in a] == [r.observed_value for r in b] == [2]

    def test_numeric_density_is_not_consulted(self):
        """Sprint 41 also earned a numeric rule. This layer deliberately refuses
        it: an all-numeric two-cell table is still reached, and a text-only
        five-cell table is still left alone."""
        assert len(read_table_presentation([_t(10, "12", "34")])) == 1
        assert read_table_presentation([_t(20, "a", "b", "c", "d", "e")]) == ()

    def test_bullets_are_not_consulted(self):
        assert read_table_presentation([_t(10, "•a", "•b", "•c", "•d")]) == ()

    def test_section_and_issuer_do_not_decide(self):
        for section in ("BUSINESS", "FINANCIAL_STATEMENTS", "UNATTRIBUTED"):
            assert len(read_table_presentation([_t(10, "a", "b", section=section)])) == 1
            assert read_table_presentation([_t(10, "a", "b", "c", "d", section=section)]) == ()


class TestIdentityAndStability:
    _CORPUS = [_t(10, "a", "b"), _t(12, "a", "b"), _t(20, "a", "b", accession="0000000-24-000001"),
               _t(30, "a", "b", "c", "d")]

    def test_one_record_per_table(self):
        records = read_table_presentation(self._CORPUS)
        assert len({(r.table.accession, r.table.source_event_index) for r in records}) == len(records)

    def test_identical_shapes_in_two_filings_stay_two_observations(self):
        records = read_table_presentation(self._CORPUS)
        same = [r for r in records if r.table.source_event_index in (10, 20)]
        assert {r.table.accession for r in same} == {"0000000-25-000001", "0000000-24-000001"}

    def test_reading_twice_gives_the_same_records(self):
        assert read_table_presentation(self._CORPUS) == read_table_presentation(self._CORPUS)

    def test_the_order_the_tables_arrive_in_does_not_matter(self):
        forward = read_table_presentation(self._CORPUS)
        backward = read_table_presentation(list(reversed(self._CORPUS)))
        assert forward == backward
        assert set(forward) == set(backward)

    def test_the_record_carries_no_judgement(self):
        import dataclasses

        names = {f.name for f in dataclasses.fields(TablePresentationEvidence)}
        assert names == {"table", "kind", "licensing_feature", "observed_value", "threshold",
                         "source_period", "version"}
        for banned in ("confidence", "probability", "score", "topic", "project", "identity",
                       "same", "continuation", "fragment", "materiality", "recommendation"):
            assert not any(banned in n for n in names), banned
