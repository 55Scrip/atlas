"""Fetch earlier earnings-call quarters for companies Atlas already has
one call for.

Stage 2's guidance-revision engine can only compare claims Atlas
observed at different times. This gets the history.

**A quarter Atlas already holds costs nothing.** Before any request is
planned, the quarter it would resolve to is checked against the
transcripts already stored for that company, and a quarter that is
present is skipped outright -- no provider call, no quota. Ingestion's
own duplicate detection would also have refused to store it twice, but
only *after* the request had been paid for; with a 25-request daily
allowance that is the difference between a backfill finishing in one
day and in two. The dry run shows exactly which quarters are skipped
and which calls remain.

**Which quarter a request means is the provider's answer, not a copy
of it.** `EarningsCallTranscriptProvider.fetch_earnings_call_transcripts`
takes no quarter argument: it derives one from `evaluated_at`, and the
protocol makes the provider the owner of that rule. So this asks the
provider (`transcript_quarter_for`) rather than restating the rule, and
the provider's own fetch uses that same method -- the quarter checked
here and the quarter requested can never disagree. A provider that
cannot answer the question is refused rather than called blind.

**No new fetch mechanism, and no new path to the network.** An earlier
quarter is requested by evaluating as of an earlier date, using the
provider exactly as written. The provider is obtained from
`business_data_refresh`'s own composition rather than imported here --
`atlas.business_data_providers` has exactly one sanctioned caller, and a
dev script reaching past it would be a second, undisclosed route to a
real network call.

**The back-dated instant selects a quarter; it is not a date of
anything** (Stage 3.1). The provider stamps it onto each statement's
`published_at`, so those values are only the as-of instants this
command chose -- never when the call took place, which Alpha Vantage
does not report. Nothing orders calls by them: Stage 2.1 orders one
company's calls by their fiscal reporting period. The records' ingestion
time is the real time this command ran, so the operational record of
when Atlas received the data stays true.

**Bounded by the provider's own budget.** `DailyQuotaExhausted` stops
the run immediately; whatever was ingested stays, and the next run
skips it.

Ingests through the same `business_data.pipeline.ingest` every provider
path uses. Creates no Case, no membership, no Decision Memory event,
and touches no recommendation.

    python -m atlas.dev.backfill_transcript_quarters [--database PATH]
        [--quarters N] [--tickers VST,GOOGL] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select

from atlas.alpha.business_data_refresh.api.dependencies import get_default_business_data_providers
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import business_record_table, create_business_record_table
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, IngestionRejected, ingest
from atlas.analysis_engine.business_data.providers import EarningsCallTranscriptProvider
from atlas.analysis_engine.business_data.versioning import DuplicateRecord
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

#: How far back each successive request evaluates. One quarter is 3
#: months; the middle of the following quarter is comfortably after any
#: quarter end, so the provider resolves to exactly the intended quarter
#: without depending on the day this is run.
_QUARTER_DAYS = 91


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def evaluation_dates(*, latest: datetime, quarters: int) -> list[datetime]:
    """The `evaluated_at` values that select the `quarters` calls before
    the one Atlas already has. Deterministic given `latest`."""
    return [latest - timedelta(days=_QUARTER_DAYS * step) for step in range(1, quarters + 1)]


def companies_with_transcripts(engine) -> list[str]:
    """Derived from the corpus, never a hardcoded list."""
    with engine.connect() as connection:
        rows = connection.execute(
            select(business_record_table.c.company)
            .where(business_record_table.c.document_type == "transcript")
            .distinct()
        ).all()
    return sorted(row[0] for row in rows)


def stored_transcript_quarters(engine) -> dict[str, set[str]]:
    """Every quarter Atlas already holds a transcript statement for, per
    company -- read from the quarter each stored statement records about
    itself. One query, no provider."""
    stored: dict[str, set[str]] = {}
    with engine.connect() as connection:
        rows = connection.execute(
            select(business_record_table.c.company, business_record_table.c.metadata_json).where(
                business_record_table.c.document_type == "transcript"
            )
        ).all()
    for company, metadata_json in rows:
        try:
            quarter = json.loads(metadata_json or "{}").get("quarter")
        except ValueError:
            continue
        if isinstance(quarter, str) and quarter:
            stored.setdefault(company, set()).add(quarter)
    return stored


@dataclass(frozen=True)
class PlannedRequest:
    ticker: str
    evaluated_at: datetime
    quarter: str


@dataclass(frozen=True)
class BackfillPlan:
    requests: tuple[PlannedRequest, ...]
    """Calls that will actually be made -- the quarter is not stored."""
    already_present: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    """(ticker, quarter) pairs skipped because Atlas already holds them.
    Each one is a provider call that is not made."""


def plan_backfill(
    *,
    tickers: list[str],
    dates: list[datetime],
    stored: dict[str, set[str]],
    quarter_for: Callable[[datetime], str],
) -> BackfillPlan:
    """Pure. A (ticker, quarter) already stored is skipped; a quarter two
    dates happen to resolve to is requested once."""
    requests: list[PlannedRequest] = []
    skipped: list[tuple[str, str]] = []
    for ticker in tickers:
        seen: set[str] = set()
        for when in dates:
            quarter = quarter_for(when)
            if quarter in seen:
                continue
            seen.add(quarter)
            if quarter in stored.get(ticker, set()):
                skipped.append((ticker, quarter))
            else:
                requests.append(PlannedRequest(ticker=ticker, evaluated_at=when, quarter=quarter))
    return BackfillPlan(requests=tuple(requests), already_present=tuple(skipped))


def _transcript_provider() -> EarningsCallTranscriptProvider | None:
    for provider in get_default_business_data_providers():
        if isinstance(provider, EarningsCallTranscriptProvider):
            return provider
    return None


def main() -> int:
    ensure_development_environment()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=None, help="Path to the Atlas database (default: the resolved one).")
    parser.add_argument("--quarters", type=int, default=2, help="How many earlier quarters to consider per company.")
    parser.add_argument("--tickers", default=None, help="Comma-separated subset; default is every company with a call.")
    parser.add_argument("--dry-run", action="store_true", help="Report the plan and the request cost, fetch nothing.")
    arguments = parser.parse_args()

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)

    tickers = (
        [t.strip().upper() for t in arguments.tickers.split(",") if t.strip()]
        if arguments.tickers
        else companies_with_transcripts(engine)
    )
    if not tickers:
        print("No company has a transcript yet; nothing to backfill from.")
        return 0

    provider = _transcript_provider()
    if provider is None:
        print("No configured provider offers earnings-call transcripts; nothing to do.")
        return 0
    quarter_for = getattr(provider, "transcript_quarter_for", None)
    if not callable(quarter_for):
        # Without the provider's own answer, "already present" cannot be
        # checked -- and guessing the quarter would be the duplicated rule
        # this command exists not to have.
        print("The transcript provider cannot say which quarter it would request; refusing to fetch blind.")
        return 1

    run_at = _utc_now()
    dates = evaluation_dates(latest=run_at, quarters=arguments.quarters)
    stored = stored_transcript_quarters(engine)
    plan = plan_backfill(tickers=tickers, dates=dates, stored=stored, quarter_for=quarter_for)

    print(f"database        : {path}")
    print(f"companies       : {len(tickers)} ({', '.join(tickers)})")
    print(f"quarters        : {', '.join(quarter_for(d) for d in dates)}")
    print()
    for ticker in tickers:
        present = [q for t, q in plan.already_present if t == ticker]
        planned = [r.quarter for r in plan.requests if r.ticker == ticker]
        print(
            f"  {ticker:6} already present / skipped: {', '.join(present) or '-':16}"
            f" to request: {', '.join(planned) or '-'}"
        )
    print()
    print(f"skipped         : {len(plan.already_present)} (already stored -- 0 provider calls)")
    print(f"provider calls  : {len(plan.requests)}")
    if arguments.dry_run:
        print("\n[dry run] no provider call made, nothing written.")
        return 0

    ingested = duplicates = rejected = 0
    failures: list[str] = []
    for request in plan.requests:
        ticker, when, quarter = request.ticker, request.evaluated_at, request.quarter
        if quarter in stored.get(ticker, set()):
            continue  # stored by an earlier request in this same run
        try:
            documents = provider.fetch_earnings_call_transcripts(company_identifier=ticker, evaluated_at=when)
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed
            # Read by exception class name, never by importing the provider
            # package's own error types -- the discipline
            # `business_data_refresh.completion.classify_provider_failure`
            # already follows, for the same boundary reason.
            kind = type(exc).__name__
            if kind == "DailyQuotaExhausted":
                print(f"  {ticker:6} {quarter}  QUOTA EXHAUSTED -- stopping: {str(exc)[:70]}")
                failures.append(f"{ticker}/{quarter}: daily quota exhausted")
                break
            print(f"  {ticker:6} {quarter}  {kind}: {str(exc)[:70]}")
            failures.append(f"{ticker}/{quarter}: {kind}")
            continue

        if not documents:
            print(f"  {ticker:6} {quarter}  no transcript published for that quarter")
            continue

        returned = str(documents[0].metadata.get("quarter") or "unknown")
        if returned != quarter:
            # The provider answered for a different quarter than it said it
            # would request -- report it rather than file it under the wrong one.
            print(f"  {ticker:6} {quarter}  provider returned {returned} instead; ingesting as returned")

        known = list(repository.get_by_company(ticker))
        added = same = 0
        for document in documents:
            # Ingested at the real run time; `when` only chose the quarter.
            result = ingest(document, existing_records=tuple(known), evaluated_at=run_at)
            if isinstance(result, IngestionRejected):
                rejected += 1
                continue
            if isinstance(result, DuplicateRecord):
                duplicates += 1
                same += 1
                continue
            if isinstance(result, IngestedRecord):
                repository.add(result.record)
                known.append(result.record)
                ingested += 1
                added += 1
        stored.setdefault(ticker, set()).add(returned)
        print(f"  {ticker:6} {returned}  statements={len(documents):3} new={added:3} already had={same:3}")

    print(f"\ningested {ingested} statements, {duplicates} already present, {rejected} rejected")
    if failures:
        print("incomplete:", "; ".join(failures))
        print("Re-run once the provider's daily allowance resets; stored quarters are skipped without a call.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
