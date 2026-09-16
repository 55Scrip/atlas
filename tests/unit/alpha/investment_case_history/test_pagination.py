"""A bounded History that still means exactly what the unbounded one meant.

The proof that matters is at the bottom: walking every page of the new
endpoint must reproduce, row for row and in order, the history the old
unbounded read returned. Everything above it protects that equivalence at
the boundaries -- equal timestamps, rows appended or retracted mid-traversal,
the cursor's own row disappearing, and a scope that must be re-applied rather
than carried in the cursor.

No test here names a real company: every fixture is a shape.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from atlas.alpha.investment_case_history.api.schemas import AnalyticalHistoryView
from atlas.alpha.investment_case_history.cursor import (
    VERSION,
    HistoryCursor,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from atlas.alpha.investment_case_history.service import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from atlas.alpha.investment_case_change.table import investment_case_snapshot_table

from tests.unit.alpha.investment_case_change.test_valuation_evidence_snapshot import (
    CURRENT,
    PRIORS,
    baseline,
    frozen,
)
from tests.unit.alpha.investment_case_history.test_service import _snapshot, harness  # noqa: F401
from tests.unit.alpha.investment_case.test_valuation_evidence_metadata import epoch

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def write(harness_, case_id: str, *, index: int, at: datetime | None = None, evidence=None):
    """One snapshot, with a distinct analytical identity so nothing dedups."""
    captured_at = at if at is not None else _T0 + timedelta(days=index)
    snapshot = _snapshot(content_hash=f"h{case_id}:{index}", captured_at=captured_at)
    harness_.snapshot_repository.add(case_id, snapshot, baseline(), valuation_evidence=evidence)
    return snapshot


def page(harness_, *, limit: int = DEFAULT_PAGE_SIZE, cursor: str | None = None):
    return AnalyticalHistoryView.from_domain(
        harness_.history_service.build_analytical_history(limit=limit, cursor=cursor))


def traverse(harness_, *, limit: int = DEFAULT_PAGE_SIZE):
    """Every page, concatenated -- what a client sees over a full traversal."""
    entries, cursor, pages = [], None, 0
    while True:
        view = page(harness_, limit=limit, cursor=cursor)
        entries.extend(view.entries)
        pages += 1
        assert pages < 200, "traversal did not terminate"
        if not view.has_more:
            assert view.next_cursor is None
            return entries, pages
        cursor = view.next_cursor


# -- the cursor --------------------------------------------------------------


class TestCursor:
    def test_it_round_trips_a_position(self):
        position = HistoryCursor(captured_at=_T0.isoformat(), case_id="c1", content_hash="h1")
        assert decode_cursor(encode_cursor(position)) == position

    def test_it_is_url_safe_and_unpadded(self):
        encoded = encode_cursor(HistoryCursor(captured_at=_T0.isoformat(), case_id="c/1+2", content_hash="h"))
        assert "=" not in encoded and "/" not in encoded and "+" not in encoded

    def test_no_cursor_means_the_beginning(self):
        assert decode_cursor(None) is None
        assert decode_cursor("") is None

    @pytest.mark.parametrize("raw", ["not-base64!!", "", "e30", "bm90LWpzb24"])
    def test_a_malformed_cursor_is_refused_rather_than_guessed(self, raw):
        if raw == "":
            pytest.skip("empty means the beginning, tested separately")
        with pytest.raises(InvalidCursorError):
            decode_cursor(raw)

    def test_a_cursor_from_another_ordering_version_is_refused(self):
        import base64
        import json

        payload = json.dumps({"v": VERSION + 1, "at": _T0.isoformat(), "case": "c", "hash": "h"}).encode()
        stale = base64.urlsafe_b64encode(payload).decode().rstrip("=")
        with pytest.raises(InvalidCursorError):
            decode_cursor(stale)

    def test_a_cursor_missing_its_position_is_refused(self):
        import base64
        import json

        payload = json.dumps({"v": VERSION, "at": _T0.isoformat()}).encode()
        broken = base64.urlsafe_b64encode(payload).decode().rstrip("=")
        with pytest.raises(InvalidCursorError):
            decode_cursor(broken)

    def test_it_carries_no_identity_or_scope(self):
        import base64
        import json

        decoded = json.loads(base64.urlsafe_b64decode(
            encode_cursor(HistoryCursor(_T0.isoformat(), "c1", "h1")) + "=="))
        assert set(decoded) == {"v", "at", "case", "hash"}


# -- page mechanics ----------------------------------------------------------


class TestPages:
    def test_an_empty_scope_is_an_empty_page_not_an_error(self, harness):
        view = page(harness)
        assert view.entries == [] and view.has_more is False and view.next_cursor is None

    def test_a_request_without_a_limit_is_bounded_by_the_default(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(DEFAULT_PAGE_SIZE + 7):
            write(harness, case_id, index=index)
        view = page(harness)
        assert len(view.entries) == DEFAULT_PAGE_SIZE
        assert view.has_more is True and view.next_cursor is not None

    def test_the_last_page_says_so(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(3):
            write(harness, case_id, index=index)
        view = page(harness, limit=10)
        assert len(view.entries) == 3 and view.has_more is False and view.next_cursor is None

    def test_a_limit_of_one_walks_the_whole_history(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(5):
            write(harness, case_id, index=index)
        entries, pages = traverse(harness, limit=1)
        assert len(entries) == 5 and pages == 5

    def test_the_maximum_page_size_is_a_ceiling_not_a_suggestion(self, harness):
        """The ceiling is what removes the unbounded response: no caller, by
        accident or intent, may ask for the whole corpus again."""
        case_id = harness.import_holding("AAA")
        for index in range(MAX_PAGE_SIZE + 5):
            write(harness, case_id, index=index)
        wide = harness.history_service.build_analytical_history(limit=MAX_PAGE_SIZE * 1000)
        assert len(wide.entries) == MAX_PAGE_SIZE, "an oversized limit was honoured instead of clamped"
        assert wide.has_more is True

    def test_a_nonsensical_limit_still_yields_a_usable_page(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(3):
            write(harness, case_id, index=index)
        assert len(harness.history_service.build_analytical_history(limit=0).entries) == 1
        assert len(harness.history_service.build_analytical_history(limit=-5).entries) == 1

    def test_pages_are_newest_first_and_never_repeat_a_row(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(9):
            write(harness, case_id, index=index)
        entries, _ = traverse(harness, limit=4)
        identities = [entry.snapshot_id for entry in entries]
        assert len(identities) == len(set(identities)), "a boundary row was repeated"
        assert [e.captured_at for e in entries] == sorted((e.captured_at for e in entries), reverse=True)


# -- boundaries --------------------------------------------------------------


class TestBoundaries:
    def test_rows_sharing_one_timestamp_each_appear_exactly_once(self, harness):
        """The case an offset would survive and a timestamp-only cursor would
        not: three visible rows at the same instant, split across pages."""
        first = harness.import_holding("AAA")
        second = harness.add_to_watchlist("BBB")
        third = harness.add_to_watchlist("CCC")
        for index, case_id in enumerate((first, second, third)):
            write(harness, case_id, index=index, at=_T0)
        entries, _ = traverse(harness, limit=1)
        assert len(entries) == 3
        assert len({e.snapshot_id for e in entries}) == 3

    def test_a_row_appended_between_pages_does_not_shift_the_next_page(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(4):
            write(harness, case_id, index=index)
        first = page(harness, limit=2)
        seen = [e.snapshot_id for e in first.entries]
        write(harness, case_id, index=99, at=_T0 + timedelta(days=50))  # newer than everything
        second = page(harness, limit=2, cursor=first.next_cursor)
        assert all(entry.snapshot_id not in seen for entry in second.entries)
        assert [e.captured_at for e in second.entries] == sorted(
            (e.captured_at for e in second.entries), reverse=True)

    def test_retracting_a_later_row_between_pages_causes_no_gap_or_repeat(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(6):
            write(harness, case_id, index=index)
        first = page(harness, limit=2)
        doomed = page(harness, limit=2, cursor=first.next_cursor).entries[0]
        with harness.engine.begin() as connection:
            connection.execute(investment_case_snapshot_table.update()
                               .where(investment_case_snapshot_table.c.id == doomed.snapshot_id)
                               .values(retracted_by="correction-1"))
        rest, _ = traverse_from(harness, first.next_cursor, limit=2)
        identities = [e.snapshot_id for e in first.entries] + [e.snapshot_id for e in rest]
        assert doomed.snapshot_id not in identities
        assert len(identities) == len(set(identities)) == 5

    def test_retracting_the_cursor_row_itself_does_not_strand_the_traversal(self, harness):
        """The cursor is a position, not a row: it need not still exist."""
        case_id = harness.import_holding("AAA")
        for index in range(5):
            write(harness, case_id, index=index)
        first = page(harness, limit=2)
        boundary = first.entries[-1]
        with harness.engine.begin() as connection:
            connection.execute(investment_case_snapshot_table.update()
                               .where(investment_case_snapshot_table.c.id == boundary.snapshot_id)
                               .values(retracted_by="correction-1"))
        rest, _ = traverse_from(harness, first.next_cursor, limit=2)
        assert [e.snapshot_id for e in rest] and boundary.snapshot_id not in [e.snapshot_id for e in rest]
        assert len(rest) == 3, "the pages after a retracted boundary lost or repeated a row"


def traverse_from(harness_, cursor, *, limit):
    entries, pages = [], 0
    while cursor is not None:
        view = page(harness_, limit=limit, cursor=cursor)
        entries.extend(view.entries)
        pages += 1
        assert pages < 200
        cursor = view.next_cursor if view.has_more else None
    return entries, pages


# -- scope -------------------------------------------------------------------


class TestScope:
    def test_a_snapshot_outside_scope_never_consumes_a_page_slot(self, harness):
        visible = harness.import_holding("AAA")
        invisible = "case-not-in-portfolio-or-watchlist"
        for index in range(3):
            write(harness, visible, index=index)
            write(harness, invisible, index=index)
        view = page(harness, limit=3)
        assert len(view.entries) == 3
        assert all(entry.case_id == visible for entry in view.entries)
        assert view.has_more is False, "out-of-scope rows leaked into has_more"

    def test_a_retracted_row_never_consumes_a_page_slot(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(4):
            write(harness, case_id, index=index)
        with harness.engine.begin() as connection:
            connection.execute(investment_case_snapshot_table.update()
                               .where(investment_case_snapshot_table.c.content_hash == f"h{case_id}:1")
                               .values(retracted_by="correction-1"))
        view = page(harness, limit=3)
        assert len(view.entries) == 3, "a retracted row was filtered after the limit, shortening the page"
        assert view.has_more is False

    def test_a_cursor_cannot_widen_scope(self, harness):
        """The cursor is an ordering boundary and nothing else: scope is
        re-derived from live membership on every request."""
        visible = harness.import_holding("AAA")
        hidden = "case-outside-scope"
        write(harness, visible, index=0)
        write(harness, hidden, index=1)
        forged = encode_cursor(HistoryCursor(
            captured_at=(_T0 + timedelta(days=99)).isoformat(), case_id=hidden, content_hash="anything"))
        view = page(harness, cursor=forged)
        assert all(entry.case_id == visible for entry in view.entries)

    def test_a_case_leaving_scope_mid_traversal_is_gone_from_the_later_page(self, harness):
        """Scope means "now", on every request. A traversal is therefore not a
        transactional snapshot of membership -- documented, not accidental --
        and the important guarantee holds regardless: no row is repeated, and
        nothing a reader may no longer see comes back."""
        first_case = harness.import_holding("AAA")
        second_case = harness.add_to_watchlist("BBB")
        for index in range(2):
            write(harness, first_case, index=index)          # days 0, 1
            write(harness, second_case, index=index + 10)    # days 10, 11
        first = page(harness, limit=2)
        assert {entry.case_id for entry in first.entries} == {second_case}, "newest first"

        harness.watchlist_store.remove("BBB", removed_at=_T0 + timedelta(days=20))

        rest = page(harness, limit=10, cursor=first.next_cursor)
        assert all(entry.case_id == first_case for entry in rest.entries)
        seen = {entry.snapshot_id for entry in first.entries}
        assert all(entry.snapshot_id not in seen for entry in rest.entries), "a row was repeated"

    def test_a_case_leaving_scope_cannot_resurrect_through_a_cursor(self, harness):
        first_case = harness.import_holding("AAA")
        second_case = harness.add_to_watchlist("BBB")
        write(harness, first_case, index=0)
        write(harness, second_case, index=5)
        harness.watchlist_store.remove("BBB", removed_at=_T0 + timedelta(days=20))
        walked, _ = traverse(harness, limit=1)
        assert all(entry.case_id == first_case for entry in walked)


# -- the equivalence proof ---------------------------------------------------


class TestTraversalEquivalence:
    def reference(self, harness_):
        """What the unbounded read returned: every visible row of every Case
        in scope, ordered by Core."""
        from atlas.alpha.case_membership import known_cases
        from atlas.analysis_engine.investment_case_history import (
            HistoricalAnalysisEntry,
            build_analytical_history,
        )

        entries = []
        for case_id, ticker in known_cases(harness_.portfolio_store, harness_.watchlist_store):
            for snapshot, transition in harness_.snapshot_repository.get_history(case_id):
                entries.append(HistoricalAnalysisEntry(
                    case_id=case_id, ticker=ticker, snapshot=snapshot, change_intelligence=transition))
        return build_analytical_history(tuple(entries), generated_at=_T0).entries

    @pytest.mark.parametrize("limit", [1, 2, 3, 7, DEFAULT_PAGE_SIZE])
    def test_every_page_concatenated_reproduces_the_unbounded_history(self, harness, limit):
        first = harness.import_holding("AAA")
        second = harness.add_to_watchlist("BBB")
        third = harness.add_to_watchlist("CCC")
        for index in range(5):
            write(harness, first, index=index, evidence=frozen(PRIORS, CURRENT) if index % 2 else None)
            write(harness, second, index=index + 5)
            write(harness, third, index=index, at=_T0 + timedelta(days=index))  # ties with `first`
        with harness.engine.begin() as connection:
            connection.execute(investment_case_snapshot_table.update()
                               .where(investment_case_snapshot_table.c.content_hash == f"h{second}:7")
                               .values(retracted_by="correction-1"))

        expected = self.reference(harness)
        walked, _ = traverse(harness, limit=limit)

        assert len(walked) == len(expected), "a full traversal did not return every visible row"
        assert [e.snapshot_id for e in walked] == [
            f"{entry.case_id}:{entry.snapshot.captured_at.isoformat()}" for entry in expected]
        assert [e.captured_at for e in walked] == [entry.snapshot.captured_at for entry in expected]
        assert [e.is_baseline for e in walked] == [
            entry.change_intelligence.is_baseline for entry in expected], "baselines moved"

    def test_a_mixed_legacy_and_evidence_history_paginates_unchanged(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(6):
            write(harness, case_id, index=index, evidence=frozen(PRIORS, CURRENT) if index % 2 else None)
        walked, _ = traverse(harness, limit=2)
        assert [entry.valuation_evidence is None for entry in walked] == [False, True, False, True, False, True]

    def test_two_snapshots_of_one_case_keep_their_own_evidence_across_a_page_break(self, harness):
        case_id = harness.import_holding("AAA")
        write(harness, case_id, index=0, evidence=frozen(PRIORS, CURRENT))
        deeper = [epoch(2021, fcf=100, market_cap=2_500), *PRIORS]
        write(harness, case_id, index=1, evidence=frozen(deeper, CURRENT))
        walked, pages = traverse(harness, limit=1)
        assert pages == 2, "the two snapshots must land on different pages"
        assert [entry.valuation_evidence.prior_epoch_count for entry in walked] == [4, 3]

    def test_methodology_identity_survives_a_page_boundary(self, harness):
        from tests.unit.alpha.investment_case_change.test_valuation_evidence_snapshot import (
            METHOD, SUPPORT, frozen_issuer,
        )
        from atlas.alpha.investment_case.valuation_evidence_snapshot import freeze_valuation_evidence
        from atlas.alpha.investment_case.valuation_evidence_metadata import describe_valuation_evidence
        from tests.unit.alpha.investment_case.test_valuation_evidence_metadata import evidence_for, finding

        case_id = harness.import_holding("AAA")
        the_finding = finding(evidence_for(PRIORS, CURRENT))
        write(harness, case_id, index=0, evidence=freeze_valuation_evidence(
            the_finding, SUPPORT, describe_valuation_evidence(the_finding), valuation_methodology="fiscal_epoch_v3"))
        write(harness, case_id, index=1, evidence=freeze_valuation_evidence(
            the_finding, SUPPORT, describe_valuation_evidence(the_finding), valuation_methodology="fiscal_epoch_v4"))
        walked, _ = traverse(harness, limit=1)
        assert [entry.valuation_evidence.valuation_methodology for entry in walked] == [
            "fiscal_epoch_v4", "fiscal_epoch_v3"]


# -- cost --------------------------------------------------------------------


class TestCost:
    def test_a_page_costs_one_snapshot_query_however_many_cases_it_spans(self, harness):
        from sqlalchemy import event

        cases = [harness.import_holding("AAA")] + [harness.add_to_watchlist(f"W{i}") for i in range(5)]
        for case_id in cases:
            for index in range(4):
                write(harness, case_id, index=index, evidence=frozen(PRIORS, CURRENT))
        statements = []

        @event.listens_for(harness.engine, "before_cursor_execute")
        def record(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
            if "investment_case_snapshots" in statement:
                statements.append(statement)

        page(harness, limit=DEFAULT_PAGE_SIZE)
        event.remove(harness.engine, "before_cursor_execute", record)
        assert len(statements) == 1, f"a page took {len(statements)} snapshot queries; evidence or history is N+1"

    def test_a_page_reads_no_more_rows_than_it_returns_plus_one(self, harness):
        case_id = harness.import_holding("AAA")
        for index in range(50):
            write(harness, case_id, index=index)
        rows, has_more = harness.snapshot_repository.get_visible_history_page([case_id], limit=5)
        assert len(rows) == 5 and has_more is True

    def test_the_page_is_cut_by_the_database_not_in_python(self, harness):
        """Slicing a full read in Python would return the same rows and cost
        the whole corpus. The LIMIT must reach storage."""
        from sqlalchemy import event

        case_id = harness.import_holding("AAA")
        for index in range(40):
            write(harness, case_id, index=index)
        statements = []

        @event.listens_for(harness.engine, "before_cursor_execute")
        def record(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
            if "investment_case_snapshots" in statement:
                statements.append((statement, parameters))

        harness.snapshot_repository.get_visible_history_page([case_id], limit=5)
        event.remove(harness.engine, "before_cursor_execute", record)
        assert len(statements) == 1
        statement, parameters = statements[0]
        assert "LIMIT" in statement.upper(), "the page query reads the whole corpus and slices afterwards"
        assert 6 in tuple(parameters or ()), "the query did not ask storage for limit + 1 rows"
