"""Forward-Looking Evidence, Stage 3 -- the operator command that turns
a single-quarter transcript corpus into a longitudinal one.

The two things worth pinning here are the ones a reviewer cannot check
by reading: that an earlier quarter is selected without the provider
being changed, and that re-running never duplicates a call Atlas
already has.
"""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.versioning import DuplicateRecord
from atlas.business_data_providers.alpha_vantage import _most_recent_completed_quarter
from atlas.dev.backfill_transcript_quarters import (
    companies_with_transcripts,
    evaluation_dates,
    plan_backfill,
    stored_transcript_quarters,
)

NOW = datetime(2026, 9, 9, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", future=True)
    create_business_record_table(engine)
    return engine


def statement(*, ticker: str, quarter: str, index: int, published_at: datetime, content: str = "We expect revenue."):
    end = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}[quarter[4:]]
    period_end = date(int(quarter[:4]), *end)
    return RawBusinessDocument(
        identifier=f"{ticker}:transcript:{quarter}:{index}",
        company=ticker,
        source_kind="transcript",
        published_at=published_at,
        provider_id="alpha_vantage",
        raw_reference=f"https://example.test/{ticker}/{quarter}",
        content_hash=f"hash-{ticker}-{quarter}-{index}",
        language="en",
        period_start=period_end,
        period_end=period_end,
        metadata={"quarter": quarter, "statement_index": index, "speaker": "A. Exec",
                  "title": "Chief Financial Officer", "content": content},
    )


class TestQuarterSelection:
    """The provider has no quarter argument -- it derives one from
    `evaluated_at`. Backfilling earlier quarters therefore means
    evaluating as of earlier dates, using the provider as written."""

    def test_each_step_back_selects_the_preceding_quarter(self):
        quarters = [_most_recent_completed_quarter(d) for d in evaluation_dates(latest=NOW, quarters=3)]
        assert quarters == ["2026Q1", "2025Q4", "2025Q3"]

    def test_the_quarter_atlas_already_has_is_never_requested_again(self):
        already_have = _most_recent_completed_quarter(NOW)
        assert already_have == "2026Q2"
        assert already_have not in [_most_recent_completed_quarter(d) for d in evaluation_dates(latest=NOW, quarters=4)]

    def test_selection_is_deterministic_for_a_given_run_date(self):
        assert evaluation_dates(latest=NOW, quarters=2) == evaluation_dates(latest=NOW, quarters=2)

    @pytest.mark.parametrize(
        "run_date,expected",
        [
            (datetime(2026, 1, 15, tzinfo=timezone.utc), ["2025Q3", "2025Q2"]),
            (datetime(2026, 5, 2, tzinfo=timezone.utc), ["2025Q4", "2025Q3"]),
            (datetime(2026, 11, 30, tzinfo=timezone.utc), ["2026Q2", "2026Q1"]),
        ],
    )
    def test_it_works_from_any_point_in_the_year_including_across_a_year_boundary(self, run_date, expected):
        assert [_most_recent_completed_quarter(d) for d in evaluation_dates(latest=run_date, quarters=2)] == expected


class TestCompanySelection:
    def test_the_target_set_is_read_from_the_corpus_never_hardcoded(self, engine):
        repository = SqlAlchemyBusinessRecordRepository(engine)
        for ticker in ("VST", "GOOGL"):
            result = ingest(statement(ticker=ticker, quarter="2026Q2", index=0, published_at=NOW), evaluated_at=NOW)
            assert isinstance(result, IngestedRecord)
            repository.add(result.record)
        assert companies_with_transcripts(engine) == ["GOOGL", "VST"]

    def test_a_company_with_no_call_is_not_a_backfill_target(self, engine):
        assert companies_with_transcripts(engine) == []


class TestIdempotency:
    """Re-running must not duplicate a call, and a different quarter
    must not be mistaken for a new version of the one Atlas has."""

    def test_refetching_the_same_quarter_ingests_nothing_new(self, engine):
        repository = SqlAlchemyBusinessRecordRepository(engine)
        document = statement(ticker="VST", quarter="2026Q1", index=0, published_at=NOW)
        first = ingest(document, evaluated_at=NOW)
        assert isinstance(first, IngestedRecord)
        repository.add(first.record)

        second = ingest(document, existing_records=tuple(repository.get_by_company("VST")), evaluated_at=NOW)
        assert isinstance(second, DuplicateRecord)
        assert len(repository.get_by_company("VST")) == 1

    def test_a_different_quarter_is_a_distinct_record_not_a_new_version(self, engine):
        repository = SqlAlchemyBusinessRecordRepository(engine)
        for quarter, when in (("2026Q2", NOW), ("2026Q1", datetime(2026, 6, 10, tzinfo=timezone.utc))):
            result = ingest(
                statement(ticker="VST", quarter=quarter, index=0, published_at=when),
                existing_records=tuple(repository.get_by_company("VST")),
                evaluated_at=when,
            )
            assert isinstance(result, IngestedRecord), quarter
            repository.add(result.record)

        records = repository.get_by_company("VST")
        assert len(records) == 2
        assert {r.version.version_number for r in records} == {1}
        assert len({r.identifier for r in records}) == 2

    def test_backfilled_quarters_carry_distinct_reported_at_timestamps(self, engine):
        """Stage 2 orders claims by `reported_at`, which the provider
        stamps from `evaluated_at`. Fetching every quarter "now" would
        make them all simultaneous and Stage 2 would correctly refuse to
        order them -- back-dating is what makes revision detection
        possible at all."""
        repository = SqlAlchemyBusinessRecordRepository(engine)
        for quarter, when in (("2026Q2", NOW), ("2026Q1", datetime(2026, 6, 10, tzinfo=timezone.utc))):
            result = ingest(statement(ticker="VST", quarter=quarter, index=0, published_at=when), evaluated_at=when)
            assert isinstance(result, IngestedRecord)
            repository.add(result.record)

        timestamps = sorted(r.published_at for r in repository.get_by_company("VST"))
        assert timestamps[0] < timestamps[1]


class TestProviderBoundary:
    def test_the_command_never_reaches_the_provider_package_directly(self):
        """`atlas.business_data_providers` is meant to have exactly one
        caller in the application. A dev script importing it would be a
        second, undisclosed route to a real network call -- so the
        provider arrives through `business_data_refresh`'s own
        composition, and provider errors are read by exception class
        name, the discipline `completion.classify_provider_failure`
        already follows."""
        import ast
        import pathlib

        source = pathlib.Path("atlas/dev/backfill_transcript_quarters.py").read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
        assert not [m for m in imported if m.startswith("atlas.business_data_providers")]


class TestNoMembershipEffects:
    def test_the_command_touches_no_case_membership_or_decision_table(self):
        """Backfilling evidence must not create Cases, holdings,
        Watchlist entries or Decision Memory events."""
        source = __import__("pathlib").Path("atlas/dev/backfill_transcript_quarters.py").read_text(encoding="utf-8")
        for forbidden in ("CaseService", "CaseGenerationService", "AlphaPortfolioStore",
                          "AlphaWatchlistStore", "DecisionRepository", "case_instrument"):
            assert forbidden not in source, f"backfill must not reach {forbidden}"


class _CountingTranscriptProvider:
    """Stands in for the configured transcript provider. Implements the
    `EarningsCallTranscriptProvider` protocol plus `transcript_quarter_for`,
    answering with the real provider's own quarter rule, and records every
    fetch -- a fetch here is a provider call that would cost quota."""

    def __init__(self):
        self.fetched: list[tuple[str, str]] = []

    def transcript_quarter_for(self, evaluated_at):
        return _most_recent_completed_quarter(evaluated_at)

    def fetch_earnings_call_transcripts(self, *, company_identifier, evaluated_at):
        quarter = self.transcript_quarter_for(evaluated_at)
        self.fetched.append((company_identifier, quarter))
        return [statement(ticker=company_identifier, quarter=quarter, index=0, published_at=evaluated_at)]


class _ProviderWithoutQuarterAnswer:
    def __init__(self):
        self.fetched = 0

    def fetch_earnings_call_transcripts(self, *, company_identifier, evaluated_at):
        self.fetched += 1
        return []


def _seed(database_path, rows):
    engine = create_engine(f"sqlite:///{database_path}", future=True)
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    for ticker, quarter in rows:
        result = ingest(statement(ticker=ticker, quarter=quarter, index=0, published_at=NOW), evaluated_at=NOW)
        assert isinstance(result, IngestedRecord)
        repository.add(result.record)
    return engine


def _run(monkeypatch, provider, database_path, *arguments):
    import atlas.dev.backfill_transcript_quarters as command

    monkeypatch.setenv("ATLAS_ENV", "development")
    monkeypatch.setattr(command, "get_default_business_data_providers", lambda: (provider,))
    monkeypatch.setattr(command, "_utc_now", lambda: NOW)
    monkeypatch.setattr("sys.argv", ["backfill", "--database", str(database_path), *arguments])
    return command.main()


class TestStoredQuartersCostNothing:
    """A quarter Atlas already holds is skipped before the provider is
    asked -- not fetched and then discarded as a duplicate. With a
    25-request daily allowance, the difference is the whole point."""

    def test_the_plan_skips_a_stored_quarter_and_requests_only_the_rest(self):
        tickers = [f"T{i:02}" for i in range(12)]
        stored = {ticker: {"2026Q2", "2026Q1"} for ticker in tickers}
        plan = plan_backfill(
            tickers=tickers,
            dates=evaluation_dates(latest=NOW, quarters=3),
            stored=stored,
            quarter_for=_most_recent_completed_quarter,
        )
        assert {q for _, q in plan.already_present} == {"2026Q1"}
        assert len(plan.already_present) == 12
        assert {r.quarter for r in plan.requests} == {"2025Q4", "2025Q3"}
        assert len(plan.requests) == 24

    def test_a_company_missing_the_quarter_is_still_planned_for_it(self):
        plan = plan_backfill(
            tickers=["VST", "SU"],
            dates=evaluation_dates(latest=NOW, quarters=3),
            stored={"VST": {"2026Q2", "2026Q1"}, "SU": {"2026Q2"}},
            quarter_for=_most_recent_completed_quarter,
        )
        assert [(r.ticker, r.quarter) for r in plan.requests] == [
            ("VST", "2025Q4"), ("VST", "2025Q3"), ("SU", "2026Q1"), ("SU", "2025Q4"), ("SU", "2025Q3"),
        ]
        assert plan.already_present == (("VST", "2026Q1"),)

    def test_two_dates_resolving_to_one_quarter_cost_one_request(self):
        plan = plan_backfill(
            tickers=["VST"],
            dates=[datetime(2026, 5, 1, tzinfo=timezone.utc), datetime(2026, 4, 2, tzinfo=timezone.utc)],
            stored={},
            quarter_for=_most_recent_completed_quarter,
        )
        assert [r.quarter for r in plan.requests] == ["2026Q1"]

    def test_stored_quarters_are_read_per_company_from_the_records(self, engine):
        repository = SqlAlchemyBusinessRecordRepository(engine)
        for ticker, quarter in (("VST", "2026Q2"), ("VST", "2026Q1"), ("SU", "2026Q2")):
            result = ingest(statement(ticker=ticker, quarter=quarter, index=0, published_at=NOW), evaluated_at=NOW)
            repository.add(result.record)
        assert stored_transcript_quarters(engine) == {"VST": {"2026Q2", "2026Q1"}, "SU": {"2026Q2"}}

    def test_a_stored_quarter_causes_zero_provider_invocations(self, monkeypatch, tmp_path):
        database = tmp_path / "atlas.db"
        _seed(database, [("VST", "2026Q2"), ("VST", "2026Q1")])
        provider = _CountingTranscriptProvider()

        assert _run(monkeypatch, provider, database, "--quarters", "3") == 0

        assert ("VST", "2026Q1") not in provider.fetched
        assert provider.fetched == [("VST", "2025Q4"), ("VST", "2025Q3")]

    def test_when_every_quarter_is_stored_the_provider_is_never_called(self, monkeypatch, tmp_path):
        database = tmp_path / "atlas.db"
        _seed(database, [("VST", q) for q in ("2026Q2", "2026Q1", "2025Q4", "2025Q3")])
        provider = _CountingTranscriptProvider()

        assert _run(monkeypatch, provider, database, "--quarters", "3") == 0

        assert provider.fetched == []

    def test_a_second_run_makes_no_calls_for_what_the_first_run_stored(self, monkeypatch, tmp_path):
        database = tmp_path / "atlas.db"
        _seed(database, [("VST", "2026Q2")])
        first = _CountingTranscriptProvider()
        _run(monkeypatch, first, database, "--quarters", "2")
        assert first.fetched == [("VST", "2026Q1"), ("VST", "2025Q4")]

        second = _CountingTranscriptProvider()
        _run(monkeypatch, second, database, "--quarters", "2")
        assert second.fetched == []

    def test_dry_run_reports_skipped_and_planned_and_calls_nothing(self, monkeypatch, tmp_path, capsys):
        database = tmp_path / "atlas.db"
        _seed(database, [("VST", "2026Q2"), ("VST", "2026Q1"), ("SU", "2026Q2")])
        provider = _CountingTranscriptProvider()

        assert _run(monkeypatch, provider, database, "--quarters", "3", "--dry-run") == 0

        out = capsys.readouterr().out
        assert provider.fetched == []
        assert "VST    already present / skipped: 2026Q1" in out
        assert "to request: 2025Q4, 2025Q3" in out
        assert "provider calls  : 5" in out
        assert "skipped         : 1" in out

    def test_a_provider_that_cannot_name_its_quarter_is_refused_not_called(self, monkeypatch, tmp_path):
        database = tmp_path / "atlas.db"
        _seed(database, [("VST", "2026Q2")])
        provider = _ProviderWithoutQuarterAnswer()

        assert _run(monkeypatch, provider, database, "--quarters", "3") == 1
        assert provider.fetched == 0
