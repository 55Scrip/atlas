"""Fetch earlier earnings-call quarters for companies Atlas already has
one call for.

Stage 2's guidance-revision engine can only compare claims Atlas
observed at different times, and the corpus holds exactly one call per
company -- so every group reports `no_prior_claim` and the engine is
proven against fixtures rather than history. This gets the history.

**No new fetch mechanism, and no new path to the network.**
`EarningsCallTranscriptProvider.fetch_earnings_call_transcripts` takes
no quarter argument: it derives one from `evaluated_at`. So an earlier
quarter is requested by evaluating as of an earlier date, using the
provider exactly as written. The provider itself is obtained from
`business_data_refresh`'s own composition rather than imported here --
`atlas.business_data_providers` is meant to have exactly one caller in
the application, and a dev script reaching past that would be precisely
the second, undisclosed route to a real network call the boundary
exists to prevent. For the same reason the provider's own quarter rule
is never duplicated here: which quarter a request resolved to is read
back from the documents it returned. That also fixes the timestamps: the
provider stamps `published_at` from `evaluated_at`, so fetching every
quarter "now" would give them all the same instant and Stage 2 would
correctly refuse to order them (`AMBIGUOUS_ORDER`). Back-dating gives
each quarter a distinct, and far more truthful, reported-at than the
moment the operator happened to run this.

**Bounded by the provider's own budget, and honest about it.** Alpha
Vantage's free tier is 25 requests per day and one call is one quarter
for one company, so a two-quarter backfill of a twelve-company corpus
is 24 requests -- essentially the whole day. `DailyQuotaExhausted`
stops the run immediately rather than burning the remainder against a
wall; whatever was already ingested stays, and the next run resumes.

Ingests through the same `business_data.pipeline.ingest` every provider
path uses, so versioning and duplicate detection are the existing ones:
re-running a quarter Atlas already has ingests nothing. Creates no
Case, no membership, no Decision Memory event, and touches no
recommendation.

    python -m atlas.dev.backfill_transcript_quarters [--database PATH]
        [--quarters N] [--tickers VST,GOOGL] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
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
#: quarter end, so `_most_recent_completed_quarter` resolves to exactly
#: the intended quarter without depending on the day this is run.
_QUARTER_DAYS = 91


def evaluation_dates(*, latest: datetime, quarters: int) -> list[datetime]:
    """The `evaluated_at` values that select the `quarters` calls before
    the one Atlas already has. Deterministic given `latest`."""
    return [latest - timedelta(days=_QUARTER_DAYS * step) for step in range(1, quarters + 1)]


def companies_with_transcripts(engine) -> list[str]:
    """Derived from the corpus, never a hardcoded list -- the set of
    companies worth backfilling is whichever ones Atlas already has a
    call for."""
    with engine.connect() as connection:
        rows = connection.execute(
            select(business_record_table.c.company)
            .where(business_record_table.c.document_type == "transcript")
            .distinct()
        ).all()
    return sorted(row[0] for row in rows)


def main() -> int:
    ensure_development_environment()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=None, help="Path to the Atlas database (default: the resolved one).")
    parser.add_argument("--quarters", type=int, default=2, help="How many earlier quarters to request per company.")
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

    now = datetime.now(timezone.utc)
    dates = evaluation_dates(latest=now, quarters=arguments.quarters)
    plan = [(ticker, when) for ticker in tickers for when in dates]

    print(f"database        : {path}")
    print(f"companies       : {len(tickers)} ({', '.join(tickers)})")
    print(f"evaluating as of: {', '.join(d.date().isoformat() for d in dates)}")
    print("                  (each resolves to that date's most recently completed quarter, the provider's own rule)")
    print(f"provider calls  : {len(plan)}")
    if arguments.dry_run:
        print("\n[dry run] no provider call made, nothing written.")
        return 0

    transcript_providers = [
        provider for provider in get_default_business_data_providers()
        if isinstance(provider, EarningsCallTranscriptProvider)
    ]
    if not transcript_providers:
        print("No configured provider offers earnings-call transcripts; nothing to do.")
        return 0
    provider = transcript_providers[0]
    ingested = duplicates = rejected = 0
    fetched_by_quarter: dict[str, int] = {}
    failures: list[str] = []

    for ticker, when in plan:
        as_of = when.date().isoformat()
        try:
            documents = provider.fetch_earnings_call_transcripts(company_identifier=ticker, evaluated_at=when)
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed
            # Read by exception class name, never by importing the
            # provider package's own error types -- the same discipline
            # `business_data_refresh.completion.classify_provider_failure`
            # already follows, and for the same boundary reason.
            kind = type(exc).__name__
            if kind == "DailyQuotaExhausted":
                # The provider's own word that the day is spent. Stopping
                # is the honest response; everything already ingested
                # stays and the next run continues from here.
                print(f"  {ticker:6} @{as_of}  QUOTA EXHAUSTED -- stopping: {str(exc)[:70]}")
                failures.append(f"{ticker}@{as_of}: daily quota exhausted")
                break
            print(f"  {ticker:6} @{as_of}  {kind}: {str(exc)[:70]}")
            failures.append(f"{ticker}@{as_of}: {kind}")
            continue

        if not documents:
            print(f"  {ticker:6} @{as_of}  no transcript published for that quarter")
            continue

        # Which quarter this actually was, according to the provider.
        quarter = str(documents[0].metadata.get("quarter") or "unknown")

        known = list(repository.get_by_company(ticker))
        added = same = 0
        for document in documents:
            result = ingest(document, existing_records=tuple(known), evaluated_at=when)
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
        fetched_by_quarter[quarter] = fetched_by_quarter.get(quarter, 0) + len(documents)
        print(f"  {ticker:6} @{as_of} -> {quarter}  statements={len(documents):3} new={added:3} already had={same:3}")

    print(f"\ningested {ingested} statements, {duplicates} already present, {rejected} rejected")
    if fetched_by_quarter:
        print("by quarter:", ", ".join(f"{q}={n}" for q, n in sorted(fetched_by_quarter.items())))
    if failures:
        print("incomplete:", "; ".join(failures))
        print("Re-run once the provider's daily allowance resets; already-ingested quarters are skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
