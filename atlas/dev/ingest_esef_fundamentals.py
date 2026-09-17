"""Give Atlas's European holdings the evidence their own filings already hold.

Eleven of the twenty-six followed holdings produce no conclusion, and for the
European ones the reason has never been that the numbers are unknowable. Volvo,
Assa Abloy, Atlas Copco, Investor and Schneider all publish machine-readable
annual reports under the EU's ESEF mandate. No source Atlas was connected to
could read them, so Atlas said it had no coverage -- of companies that file
their accounts in XBRL every spring.

This ingests those filings. It is deliberately a hand-run script rather than a
scheduled provider: the first European evidence entering a live database should
be looked at by someone, and the normalization it depends on withholds often
enough that the withholdings are worth reading.

    python -m atlas.dev.ingest_esef_fundamentals [--database PATH] [--apply]
        [--holding TICKER=ISIN ...] [--years N] [--cache DIR]

Dry run by default: it prints every fact it would store and writes nothing.

What it does not do: decide anything. It produces `BusinessRecord`s through the
ordinary ingestion pipeline, and Atlas's own evaluators draw whatever
conclusions the evidence supports -- including, for most of these issuers,
withholding a debt figure and therefore a financial-risk verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.esef_fundamentals import (
    EsefSourceError,
    annual_evidence,
    document_for,
    esef_filing_index,
    issuer_lei,
)
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.analysis_engine.business_data.pipeline import ingest
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

#: The European holdings, with the ISIN each was verified against OpenFIGI in
#: Import Strong Identity Resolution v1. The ticker is Atlas's own key for the
#: holding; the ISIN is what finds the filer. Nothing here is a normalization
#: rule -- it is the operator saying which holdings to ingest, the same way
#: `populate_security_identifiers` takes a list of tickers.
DEFAULT_HOLDINGS: dict[str, str] = {
    "VOLV-B": "SE0000115446",
    "ATCO-B": "SE0017486897",
    "INVE-B": "SE0015811963",
    "ASSA-B": "SE0007100581",
    "SU.PA": "FR0000121972",
}


def main(argv: list[str] | None = None) -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(
        prog="python -m atlas.dev.ingest_esef_fundamentals",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--apply", action="store_true", help="Write. Without this, nothing is written.")
    parser.add_argument("--holding", action="append", default=[], metavar="TICKER=ISIN",
                        help="Override the default holdings. Repeatable.")
    parser.add_argument("--years", type=int, default=4,
                        help="Most recent annual filings per issuer (default 4).")
    parser.add_argument("--cache", default=None, help="Where downloaded filings are kept.")
    arguments = parser.parse_args(argv)

    holdings = dict(DEFAULT_HOLDINGS)
    if arguments.holding:
        holdings = {}
        for pair in arguments.holding:
            ticker, _, isin = pair.partition("=")
            if not isin:
                print(f"--holding needs TICKER=ISIN, got {pair!r}", file=sys.stderr)
                return 2
            holdings[ticker.strip().upper()] = isin.strip().upper()

    path = arguments.database or resolve_database_path()
    cache = Path(arguments.cache or (Path(path).parent / "esef_cache"))
    engine = create_engine(f"sqlite:///{path}", future=True)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    evaluated_at = datetime.now(timezone.utc)

    print(f"database : {path}")
    print(f"cache    : {cache}")
    print(f"mode     : {'APPLY' if arguments.apply else 'dry run -- nothing is written'}")
    print(f"holdings : {', '.join(sorted(holdings))}\n")

    # One scan of the filing index for the whole batch, rather than one per
    # issuer. Everything after this is cached downloads.
    print("indexing ESEF filings ...", flush=True)
    filing_index = esef_filing_index()
    print(f"  {sum(len(v) for v in filing_index.values())} filings across {len(filing_index)} issuers\n", flush=True)

    written = skipped = failed = 0
    for ticker, isin in sorted(holdings.items()):
        try:
            lei = issuer_lei(isin)
            if lei is None:
                print(f"{ticker:8} no LEI is mapped to {isin} -- nothing to ingest")
                failed += 1
                continue
            evidence = annual_evidence(lei, cache, years=arguments.years, index=filing_index)
        except EsefSourceError as error:
            # One issuer's failure is that issuer's failure. Everything already
            # ingested stays, and every other issuer still runs.
            print(f"{ticker:8} source unavailable: {error}", file=sys.stderr)
            failed += 1
            continue

        print(f"{ticker:8} {lei}  {len(evidence)} annual filing(s)", flush=True)
        known = list(repository.get_by_company(ticker))
        for item in evidence:
            document = document_for(ticker, item, lei)
            result = ingest(document, existing_records=tuple(known), evaluated_at=evaluated_at)
            record = getattr(result, "record", None)
            rejected = getattr(result, "reasons", None)

            fields = sorted(k for k in document.metadata
                            if not k.startswith("esef_") and k != "currency")
            print(f"           {item.filing.period_end}  published {item.filing.published_at}  "
                  f"{item.period.currency or '?'}  {len(fields)} fields  "
                  f"debt={item.debt.outcome.value}", flush=True)
            if item.period.withheld:
                print(f"                       withheld: {', '.join(item.period.withheld)}")
            if rejected:
                print(f"                       rejected: {[r.value for r in rejected]}", file=sys.stderr)
                failed += 1
                continue
            if record is None:
                skipped += 1        # already held, identical content
                continue
            if arguments.apply:
                repository.add(record)
                known.append(record)
            written += 1

    print(f"\nrecords {'written' if arguments.apply else 'that would be written'}: {written}")
    print(f"unchanged/skipped : {skipped}")
    print(f"failures          : {failed}")
    print("Alpha Vantage: 0   SEC: 0   commercial providers: 0")
    if not arguments.apply:
        print("\n[dry run] nothing written.")
    return 1 if failed and not written else 0


if __name__ == "__main__":
    sys.exit(main())
