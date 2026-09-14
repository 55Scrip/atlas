"""Backfill security-level share-class evidence from annual SEC filings
(Security-Level Share-Class Evidence v1).

For each named ticker, the annual filings Atlas's own stored SEC statements
come from (`sec_cik`, `sec_accession`, `sec_form`, filing date) -- filed on
or after `--since`, 2019 by default: the cover-page tagging that can prove a
class link starts there -- are read at filing level: the XBRL instance
itself, not companyfacts. Each filing's class share facts are recorded with
what that filing alone proves about them (`PROVEN_BY_SHARED_DIMENSION`,
`AMBIGUOUS`, `NO_LINK`); nothing is carried from one filing to another.

**Explicit tickers only.** There is no "every company" default: the command
touches only the filers the operator names. Tickers of one SEC filer share
its filings, which are fetched once.

**Two keyless SEC requests per pending filing** (the filing index, then the
instance), counted as they are made -- a failed request still counts. A
filing already processed at the current parser version costs nothing, so a
re-run resumes where the last one stopped and a finished run is a no-op.
Each filing is written in one transaction, completion row and
observations together. `--max-requests` caps the run.

Writes only its own two tables (created on first write): no business
record, no Case, no decision, no methodology change.

    python -m atlas.dev.backfill_security_share_evidence --tickers GOOG,GOOGL
        [--database PATH] [--since 2019-01-01] [--max-requests N] [--dry-run]
        [--save-fetched DIR | --from-fetched DIR]

`--save-fetched`/`--from-fetched` split requests from writes: fetch once
(rehearsing on a database copy), then apply the same saved instances to the
live database with no further request.
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.security_share_evidence import (
    PARSER_VERSION,
    FilingRefused,
    ShareClassFilingSource,
    evidence_from_instance,
    get_default_share_class_provider,
)
from atlas.alpha.canonical_security_gate.factory import build_listing_mic_reader
from atlas.alpha.security_share_evidence.models import ShareClassLinkKind
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.alpha.security_share_evidence.table import create_security_share_evidence_tables
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

__all__ = ["IssuerPlan", "plan_issuers", "main"]

_ANNUAL_FORMS = frozenset({"10-K", "20-F", "40-F"})
_REQUESTS_PER_FILING = 2


@dataclass
class IssuerPlan:
    issuer_cik: str
    tickers: list[str]
    filings: list[ShareClassFilingSource]
    done: list[str] = field(default_factory=list)

    @property
    def pending(self) -> list[ShareClassFilingSource]:
        return [f for f in self.filings if f.accession not in self.done]


def _day(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _filings_of(records: Iterable[BusinessRecord], since: date) -> tuple[set[str], dict[str, ShareClassFilingSource], list[str]]:
    """(CIKs, annual filings by accession, refusals) from one company's
    stored SEC statements -- every version, since a later version need not
    repeat an earlier filing."""
    ciks: set[str] = set()
    seen: dict[str, set[tuple]] = {}
    for r in records:
        if r.document_type is not SourceKind.FINANCIAL_STATEMENT:
            continue
        m = r.metadata
        if m.get("sec_cik"):
            ciks.add(str(m["sec_cik"]))
        accession, form, filed = m.get("sec_accession"), m.get("sec_form"), _day(r.published_at)
        if accession and form in _ANNUAL_FORMS and filed is not None and filed >= since and m.get("sec_cik"):
            seen.setdefault(accession, set()).add((str(m["sec_cik"]), form, filed))
    filings, refusals = {}, []
    for accession, variants in seen.items():
        if len(variants) != 1:
            refusals.append(f"{accession}: statements disagree on its filer, form or date")
            continue
        cik, form, filed = variants.pop()
        filings[accession] = ShareClassFilingSource(cik, accession, form, filed)
    return ciks, filings, refusals


def plan_issuers(records_by_ticker: dict[str, tuple[BusinessRecord, ...]], since: date) -> tuple[list[IssuerPlan], list[str]]:
    by_cik: dict[str, IssuerPlan] = {}
    refusals: list[str] = []
    for ticker, records in records_by_ticker.items():
        ciks, filings, refused = _filings_of(records, since)
        refusals += [f"{ticker}: {r}" for r in refused]
        if len(ciks) != 1:
            refusals.append(f"{ticker}: {'no' if not ciks else 'more than one'} SEC filer in its stored statements")
            continue
        cik = ciks.pop()
        plan = by_cik.setdefault(cik, IssuerPlan(cik, [], []))
        plan.tickers.append(ticker)
        known = {f.accession for f in plan.filings}
        plan.filings += [f for a, f in filings.items() if a not in known and f.issuer_cik == cik]
    for plan in by_cik.values():
        plan.filings.sort(key=lambda f: (f.filing_date, f.accession))
    return sorted(by_cik.values(), key=lambda p: p.issuer_cik), refusals


# -- fetch-once ---------------------------------------------------------------------------------------------


def _save(directory: Path, source: ShareClassFilingSource, fetched) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{source.accession}.xml").write_text(fetched.instance_xml)
    manifest = directory / "manifest.json"
    entries = json.loads(manifest.read_text()) if manifest.exists() else {}
    entries[source.accession] = {
        "cik": fetched.cik, "instance_name": fetched.instance_name, "instance_url": fetched.instance_url,
        "requests": fetched.requests, "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest.write_text(json.dumps(entries, indent=1, sort_keys=True))


def _load(directory: Path, source: ShareClassFilingSource):
    from types import SimpleNamespace

    entries = json.loads((directory / "manifest.json").read_text())
    entry = entries.get(source.accession)
    path = directory / f"{source.accession}.xml"
    if entry is None or not path.exists():
        return None
    return SimpleNamespace(cik=entry["cik"], accession=source.accession, instance_name=entry["instance_name"],
                           instance_url=entry["instance_url"], instance_xml=path.read_text(), requests=0)


def main() -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None, help="Path to the Atlas database (default: the resolved one).")
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers (required; no default set).")
    parser.add_argument("--since", default="2019-01-01", help="Earliest filing date (default 2019-01-01).")
    parser.add_argument("--max-requests", type=int, default=100, help="SEC requests this run may make.")
    parser.add_argument("--dry-run", action="store_true", help="Report the plan and its request count; fetch nothing.")
    parser.add_argument("--save-fetched", default=None, help="Also save each fetched instance under this directory.")
    parser.add_argument("--from-fetched", default=None, help="Apply instances saved by --save-fetched; no request.")
    arguments = parser.parse_args()
    if arguments.save_fetched and arguments.from_fetched:
        parser.error("choose one of --save-fetched and --from-fetched")

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    records = SqlAlchemyBusinessRecordRepository(engine)
    evidence = SqlAlchemySecurityShareEvidenceRepository(engine, listing_mics=build_listing_mic_reader(engine))
    tickers = [t.strip().upper() for t in arguments.tickers.split(",") if t.strip()]
    plans, refusals = plan_issuers({t: records.get_by_company(t) for t in tickers}, date.fromisoformat(arguments.since))
    for plan in plans:
        versions = evidence.processed_parser_versions(tuple(f.accession for f in plan.filings))
        plan.done = [a for a, v in versions.items() if v == PARSER_VERSION]

    print(f"database        : {path}")
    print(f"parser          : {PARSER_VERSION}; filings filed on or after {arguments.since}")
    for plan in plans:
        print(f"  CIK {plan.issuer_cik}  {','.join(plan.tickers):12} annual filings {len(plan.filings):3}  "
              f"done {len(plan.done):3}  pending {len(plan.pending):3}  requests {len(plan.pending) * _REQUESTS_PER_FILING}")
    for refusal in refusals:
        print(f"  REFUSED {refusal}")
    planned = sum(len(p.pending) for p in plans) * _REQUESTS_PER_FILING
    source = "saved instances, no request" if arguments.from_fetched else "keyless, uncounted by Alpha Vantage"
    print(f"SEC EDGAR       : {planned if not arguments.from_fetched else 0} requests planned ({source}; cap {arguments.max_requests})")
    if arguments.dry_run:
        print("\n[dry run] no request made, nothing written.")
        return 0

    create_security_share_evidence_tables(engine)
    provider = None if arguments.from_fetched else get_default_share_class_provider()
    saved = Path(arguments.save_fetched) if arguments.save_fetched else None
    counts = {"attempted": 0, "succeeded": 0, "failed": 0, "recorded": 0, "refused": 0, "missing": 0}
    stopped = None

    def count_request():
        counts["attempted"] += 1

    for plan in plans:
        print(f"\nCIK {plan.issuer_cik} ({', '.join(plan.tickers)})")
        for filing in plan.pending:
            if arguments.from_fetched:
                fetched = _load(Path(arguments.from_fetched), filing)
                if fetched is None:
                    counts["missing"] += 1
                    print(f"  {filing.accession}  not in {arguments.from_fetched} -- skipped")
                    continue
            else:
                if counts["attempted"] + _REQUESTS_PER_FILING > arguments.max_requests:
                    stopped = "max-requests reached"
                    break
                before = counts["attempted"]
                try:
                    fetched = provider.fetch_instance(cik=filing.issuer_cik, accession=filing.accession,
                                                      on_request=count_request)
                except Exception as exc:  # noqa: BLE001 -- reported, never swallowed
                    counts["succeeded"] += max(0, counts["attempted"] - before - 1)
                    counts["failed"] += 1
                    print(f"  {filing.accession}  {type(exc).__name__}: {str(exc)[:140]}")
                    continue
                counts["succeeded"] += fetched.requests
                if saved is not None:
                    _save(saved, filing, fetched)
            try:
                record, observations = evidence_from_instance(filing, fetched, recorded_at=datetime.now(timezone.utc))
            except FilingRefused as exc:
                counts["refused"] += 1
                print(f"  {filing.accession}  REFUSED: {exc}")
                continue
            evidence.record_filing(record, observations)
            counts["recorded"] += 1
            proven = sorted({f"{o.class_member}->{o.cover_symbol}@{o.cover_mic}" for o in observations
                             if o.link_kind is ShareClassLinkKind.PROVEN_BY_SHARED_DIMENSION})
            print(f"  {filing.accession}  {filing.filing_date}  {record.fiscal_period or '?':7} cover rows "
                  f"{record.cover_rows} ({record.dimensioned_cover_rows} dimensioned)  facts {record.observations:2}  "
                  f"proven {record.proven:2}  ambiguous {record.ambiguous:2}  no link {record.no_link:2}  "
                  f"conflicts {record.conflicts}  {' '.join(proven)}")
        if stopped:
            break

    joined = evidence.proven_for_securities({t: p.issuer_cik for p in plans for t in p.tickers})
    print("\nsecurity join (CIK + symbol + MIC):")
    for ticker in tickers:
        observations = joined.get(ticker, ())
        periods = sorted({o.period_end.isoformat() for o in observations if o.usable})
        print(f"  {ticker:6} proven observations {len(observations):3}  usable period ends {len(periods):2}  "
              f"{periods[0] + '..' + periods[-1] if periods else ''}")
    print(f"\nSEC requests: attempted {counts['attempted']}  succeeded {counts['succeeded']}  failed {counts['failed']}"
          + (f" -- stopped: {stopped}" if stopped else ""))
    print(f"filings: recorded {counts['recorded']}  refused {counts['refused']}  missing from saved {counts['missing']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
