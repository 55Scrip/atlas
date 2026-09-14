"""Record current share-count evidence from SEC cover pages (Current
Share-Count Evidence v1).

For each named ticker's SEC filer: SEC submissions locate the latest
original 10-K or 10-Q filed by `--as-of` (submissions are never share-count
evidence), and that filing's XBRL instance gives its cover-page counts --
`dei:EntityCommonStockSharesOutstanding`, each dated by its own instant and
linked to a listed security only by the same-filing rule. Nothing is
aggregated across classes and nothing is taken from the market-data
provider: its `SharesOutstanding` is printed beside the SEC count as a
cross-check, never written.

**Explicit tickers only; three keyless requests per filer** (submissions,
filing index, instance), each logged as it is made. A filing already
recorded under the current parser version is not fetched again. Evidence is
append-only: one transaction per filing, nothing updated or deleted.
`--save-fetched`/`--from-fetched` split requests from writes, so a rehearsal
and the live apply use the very same documents.

Writes only its own two tables (created on first write). No Case, no
decision, no business record, no Alpha Vantage request.

    python -m atlas.dev.backfill_current_share_evidence --tickers CRM,MA
        [--database PATH] [--as-of YYYY-MM-DD] [--max-requests N] [--dry-run]
        [--save-fetched DIR | --from-fetched DIR]
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.security_share_evidence import (
    COVER_PARSER_VERSION,
    FilingRefused,
    ShareClassFilingSource,
    current_evidence_from_instance,
    get_default_share_class_provider,
    latest_periodic_filing,
)
from atlas.alpha.canonical_security_gate.factory import build_listing_mic_reader
from atlas.alpha.security_share_evidence.current import cross_check, read_current_shares
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.alpha.security_share_evidence.table import create_current_share_evidence_tables
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.backfill_security_share_evidence import plan_issuers
from atlas.dev.guard import ensure_development_environment

__all__ = ["main", "provider_shares"]

_REQUESTS_PER_FILER = 3


def _now() -> datetime:
    return datetime.now(timezone.utc)


def provider_shares(records) -> tuple[float | None, datetime | None]:
    """The provider's current `shares_outstanding` and when that snapshot was
    written -- read from the latest quote snapshot, never interpreted."""
    quotes = [r for r in latest_versions(records) if r.document_type is SourceKind.MARKET_DATA_SNAPSHOT
              and "GLOBAL_QUOTE" in (r.source_reference or "")]
    if not quotes:
        return None, None
    latest = max(quotes, key=lambda r: (r.period_end, r.version.created_at))
    return latest.metadata.get("shares_outstanding"), latest.version.created_at


class _Log:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    def add(self, cik, accession, resource, purpose, status="ok"):
        self.entries.append({"timestamp": _now().isoformat(), "cik": cik, "accession": accession,
                             "resource": resource, "purpose": purpose, "status": status})

    @property
    def attempted(self) -> int:
        return len(self.entries)


def main() -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None, help="Path to the Atlas database (default: the resolved one).")
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers (required; no default set).")
    parser.add_argument("--as-of", default=None, help="Evaluate filings filed by this date (default: today, UTC).")
    parser.add_argument("--max-requests", type=int, default=60, help="SEC requests this run may make.")
    parser.add_argument("--dry-run", action="store_true", help="Report the plan and its request count; fetch nothing.")
    parser.add_argument("--save-fetched", default=None, help="Also save every fetched document under this directory.")
    parser.add_argument("--from-fetched", default=None, help="Apply documents saved by --save-fetched; no request.")
    arguments = parser.parse_args()
    if arguments.save_fetched and arguments.from_fetched:
        parser.error("choose one of --save-fetched and --from-fetched")
    as_of = date.fromisoformat(arguments.as_of) if arguments.as_of else _now().date()

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    records = SqlAlchemyBusinessRecordRepository(engine)
    evidence = SqlAlchemySecurityShareEvidenceRepository(engine, listing_mics=build_listing_mic_reader(engine))
    tickers = [t.strip().upper() for t in arguments.tickers.split(",") if t.strip()]
    by_ticker = {t: records.get_by_company(t) for t in tickers}
    plans, refusals = plan_issuers(by_ticker, date.min)
    saved = Path(arguments.from_fetched or arguments.save_fetched) if (arguments.from_fetched or arguments.save_fetched) else None

    print(f"database        : {path}")
    print(f"parser          : {COVER_PARSER_VERSION}; latest original 10-K/10-Q filed by {as_of}")
    for plan in plans:
        cached = saved is not None and (saved / "submissions" / f"{plan.issuer_cik}.json").exists()
        print(f"  CIK {plan.issuer_cik}  {','.join(plan.tickers):12} submissions {'saved' if cached else 'to fetch'}")
    for refusal in refusals:
        print(f"  REFUSED {refusal}")
    planned = 0 if arguments.from_fetched else _REQUESTS_PER_FILER * len(plans)
    print(f"SEC EDGAR       : up to {planned} keyless requests (submissions + index + instance per filer; "
          f"a filing already recorded is not fetched); Alpha Vantage: 0 (cap {arguments.max_requests})")
    if arguments.dry_run:
        print("\n[dry run] no request made, nothing written.")
        return 0

    create_current_share_evidence_tables(engine)
    provider = None if arguments.from_fetched else get_default_share_class_provider()
    log = _Log()
    stopped = None
    counts = {"recorded": 0, "already": 0, "refused": 0, "failed": 0, "missing": 0}
    for plan in plans:
        cik = plan.issuer_cik
        sub_path = saved / "submissions" / f"{cik}.json" if saved else None
        if arguments.from_fetched:
            if not sub_path.exists():
                counts["missing"] += 1
                print(f"  CIK {cik}: submissions not saved -- skipped")
                continue
            submissions = json.loads(sub_path.read_text())
        else:
            if log.attempted + _REQUESTS_PER_FILER > arguments.max_requests:
                stopped = "max-requests reached"
                break
            try:
                submissions = provider.fetch_submissions(cik=cik)
                log.add(cik, None, "submissions", "locate the latest 10-K/10-Q")
            except Exception as exc:  # noqa: BLE001 -- reported, never swallowed
                log.add(cik, None, "submissions", "locate the latest 10-K/10-Q", f"{type(exc).__name__}")
                counts["failed"] += 1
                print(f"  CIK {cik}: submissions {type(exc).__name__}: {str(exc)[:120]}")
                continue
            if sub_path is not None:
                sub_path.parent.mkdir(parents=True, exist_ok=True)
                sub_path.write_text(json.dumps(submissions))
        filing = latest_periodic_filing(submissions, filed_by=as_of)
        if filing is None:
            print(f"  CIK {cik}: no original 10-K/10-Q filed by {as_of}")
            continue
        if COVER_PARSER_VERSION in evidence.current_processed((filing.accession,)).get(filing.accession, frozenset()):
            counts["already"] += 1
            print(f"  CIK {cik}: {filing.form} {filing.accession} already recorded -- no request")
            continue
        inst_path = saved / "instances" / f"{filing.accession}.xml" if saved else None
        if arguments.from_fetched:
            manifest = json.loads((saved / "manifest.json").read_text())
            if filing.accession not in manifest or not inst_path.exists():
                counts["missing"] += 1
                print(f"  CIK {cik}: {filing.accession} not saved -- skipped")
                continue
            entry = manifest[filing.accession]
            fetched = SimpleNamespace(cik=cik, accession=filing.accession, instance_name=entry["instance_name"],
                                      instance_url=entry["instance_url"], instance_xml=inst_path.read_text(), requests=0)
            retrieved_at = datetime.fromisoformat(entry["retrieved_at"])
        else:
            resources = iter(("filing_index", "instance"))
            try:
                fetched = provider.fetch_instance(
                    cik=cik, accession=filing.accession,
                    on_request=lambda: log.add(cik, filing.accession, next(resources), "read the cover page"))
            except Exception as exc:  # noqa: BLE001 -- reported, never swallowed
                if log.entries:
                    log.entries[-1]["status"] = type(exc).__name__
                counts["failed"] += 1
                print(f"  CIK {cik}: {filing.accession} {type(exc).__name__}: {str(exc)[:120]}")
                continue
            retrieved_at = _now()
            if saved is not None:
                inst_path.parent.mkdir(parents=True, exist_ok=True)
                inst_path.write_text(fetched.instance_xml)
                manifest_path = saved / "manifest.json"
                manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
                manifest[filing.accession] = {"cik": cik, "form": filing.form, "filing_date": filing.filing_date.isoformat(),
                                              "instance_name": fetched.instance_name, "instance_url": fetched.instance_url,
                                              "retrieved_at": retrieved_at.isoformat()}
                manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        source = ShareClassFilingSource(cik, filing.accession, filing.form, filing.filing_date)
        try:
            record, observations = current_evidence_from_instance(source, fetched, retrieved_at=retrieved_at, recorded_at=_now())
        except FilingRefused as exc:
            counts["refused"] += 1
            print(f"  CIK {cik}: REFUSED {exc}")
            continue
        wrote = evidence.record_current_filing(record, observations)
        counts["recorded" if wrote else "already"] += 1
        linked = [f"{o.class_member.split(':')[1] if o.class_member else 'issuer'}->{o.cover_symbol}@{o.cover_mic}" for o in observations
                  if o.link_kind.value == "proven_by_shared_dimension"]
        print(f"  CIK {cik}: {filing.form} {filing.accession} filed {filing.filing_date}  counts {record.counts} "
              f"(proven {record.proven}, ambiguous {record.ambiguous}, no link {record.no_link}, conflicts {record.conflicts})  "
              f"classes reported {record.share_classes_reported}  {' '.join(linked)}")
    if saved is not None and not arguments.from_fetched:
        (saved / "requests.json").write_text(json.dumps(log.entries, indent=1))

    cik_by_ticker = {t: p.issuer_cik for p in plans for t in p.tickers}
    joined = evidence.current_joined(cik_by_ticker)
    issuers = evidence.current_evidence_for_issuers(frozenset(cik_by_ticker.values()))
    print(f"\ncurrent share evidence as of {as_of} (SEC cover page) vs provider SharesOutstanding (cross-check only):")
    for ticker in tickers:
        if ticker not in cik_by_ticker:
            continue
        reading = read_current_shares(ticker, joined[ticker], issuers[cik_by_ticker[ticker]], evaluated_on=as_of)
        shares, written = provider_shares(by_ticker[ticker])
        check = cross_check(reading, shares, written)
        e = reading.evidence
        print(f"  {ticker:6} {reading.status.value:9} "
              + (f"SEC {e.shares / 1e6:10.1f}M as of {e.as_of} ({e.form} filed {e.filing_date}, {e.scope.value}"
                 f"{':' + e.class_member.split(':')[1] if e.class_member else ''}, decimals {e.decimals})  " if e else " " * 60)
              + (f"provider {check.provider_shares / 1e6:10.1f}M" if check.provider_shares else "provider      -")
              + (f"  ratio {check.ratio:.4f}" if check.ratio else ""))
    print(f"\nSEC requests: attempted {log.attempted}  failed {sum(1 for x in log.entries if x['status'] != 'ok')}"
          + (f" -- stopped: {stopped}" if stopped else ""))
    print(f"filings: recorded {counts['recorded']}  already recorded {counts['already']}  refused {counts['refused']}  "
          f"failed {counts['failed']}  missing from saved {counts['missing']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
