"""Record class economic-rights evidence from named SEC filings (Issuer
Common-Equity Market Cap v1).

Explicit tickers and explicit accessions only: every accession must be a
filing Atlas's share evidence already read for one of the named tickers'
own SEC filers, so its instance URL is known -- exactly one keyless request
per filing, each logged as it is made. A filing already recorded under the
current parser version is never fetched again. Append-only, one transaction
per filing. No Alpha Vantage request; no Case, decision or business record
is touched. After applying, prints each ticker's descriptive issuer
common-equity market cap -- composed from the evidence, never stored.

    python -m atlas.dev.backfill_class_rights_evidence --tickers GOOG,V --accessions A1,A2
        [--database PATH] [--as-of YYYY-MM-DD] [--max-requests N] [--dry-run]
        [--save-fetched DIR | --from-fetched DIR]
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.class_rights_evidence import (
    RIGHTS_PARSER_VERSION,
    RightsFilingRefused,
    RightsFilingSource,
    get_default_class_rights_provider,
    rights_evidence_from_instance,
)
from atlas.alpha.canonical_security_gate.factory import build_listing_mic_reader
from atlas.alpha.class_rights_evidence.repository import SqlAlchemyClassRightsEvidenceRepository
from atlas.alpha.class_rights_evidence.table import create_class_rights_evidence_tables
from atlas.alpha.issuer_equity.reader import IssuerEquityReader
from atlas.alpha.security_share_evidence.repository import SqlAlchemySecurityShareEvidenceRepository
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

__all__ = ["main"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def main() -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers (required).")
    parser.add_argument("--accessions", required=True, help="Comma-separated accessions (required).")
    parser.add_argument("--as-of", default=None, help="Evaluation date for the composed report (default: today, UTC).")
    parser.add_argument("--max-requests", type=int, default=10, help="SEC requests this run may make.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--save-fetched", default=None)
    parser.add_argument("--from-fetched", default=None)
    arguments = parser.parse_args()
    if arguments.save_fetched and arguments.from_fetched:
        parser.error("choose one of --save-fetched and --from-fetched")
    as_of = date.fromisoformat(arguments.as_of) if arguments.as_of else _now().date()
    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    listing_mics = build_listing_mic_reader(engine)
    shares = SqlAlchemySecurityShareEvidenceRepository(engine, listing_mics=listing_mics)
    rights = SqlAlchemyClassRightsEvidenceRepository(engine)
    reader = IssuerEquityReader(engine, listing_mics=listing_mics)
    tickers = [t.strip().upper() for t in arguments.tickers.split(",") if t.strip()]
    accessions = [a.strip() for a in arguments.accessions.split(",") if a.strip()]
    ciks = {t: reader.issuer_cik(t) for t in tickers}
    located = shares.filing_locations(tuple(accessions))
    processed = rights.processed(tuple(accessions))
    saved = Path(arguments.from_fetched or arguments.save_fetched) if (arguments.from_fetched or arguments.save_fetched) else None

    plan, refused = [], []
    for accession in accessions:
        if accession not in located:
            refused.append(f"{accession}: not a filing Atlas's share evidence has read")
            continue
        cik, form, filed, url = located[accession]
        owners = [t for t, c in ciks.items() if c == cik]
        if not owners:
            refused.append(f"{accession}: filer {cik} is none of the named tickers' filers")
            continue
        if RIGHTS_PARSER_VERSION in processed.get(accession, frozenset()):
            print(f"  {accession}  already recorded ({RIGHTS_PARSER_VERSION}) -- no request")
            continue
        plan.append((accession, cik, form, filed, url, owners))
    print(f"database        : {path}")
    print(f"parser          : {RIGHTS_PARSER_VERSION}")
    for accession, cik, form, filed, url, owners in plan:
        print(f"  CIK {cik}  {','.join(owners):10} {form:5} {accession} filed {filed}  instance: {url.rsplit('/', 1)[-1]}")
    for r in refused:
        print(f"  REFUSED {r}")
    planned = 0 if arguments.from_fetched else len(plan)
    print(f"SEC EDGAR       : {planned} keyless requests (one instance per filing; cap {arguments.max_requests}); Alpha Vantage: 0")
    if arguments.dry_run:
        print("\n[dry run] no request made, nothing written.")
        return 0
    if planned > arguments.max_requests:
        print(f"STOPPED: {planned} requests planned, cap {arguments.max_requests}")
        return 1

    create_class_rights_evidence_tables(engine)
    provider = None if arguments.from_fetched else get_default_class_rights_provider()
    log: list[dict] = []
    counts = {"recorded": 0, "already": 0, "refused": 0, "failed": 0, "missing": 0}
    manifest_path = saved / "manifest.json" if saved else None
    manifest = json.loads(manifest_path.read_text()) if manifest_path and manifest_path.exists() else {}
    for accession, cik, form, filed, url, owners in plan:
        inst_path = saved / "instances" / f"{accession}.xml" if saved else None
        if arguments.from_fetched:
            if accession not in manifest or not inst_path.exists():
                counts["missing"] += 1
                print(f"  {accession}: not saved -- skipped")
                continue
            xml, retrieved_at = inst_path.read_text(), datetime.fromisoformat(manifest[accession]["retrieved_at"])
        else:
            entry = {"timestamp": _now().isoformat(), "cik": cik, "accession": accession, "form": form,
                     "resource": "instance", "purpose": "class economic rights", "status": "ok"}
            try:
                xml = provider.fetch_instance_at(instance_url=url, on_request=lambda: log.append(entry))
            except Exception as exc:  # noqa: BLE001 -- reported, never swallowed
                entry["status"] = type(exc).__name__
                if entry not in log:
                    log.append(entry)
                counts["failed"] += 1
                print(f"  {accession}: {type(exc).__name__}: {str(exc)[:120]}")
                continue
            retrieved_at = _now()
            if saved is not None:
                inst_path.parent.mkdir(parents=True, exist_ok=True)
                inst_path.write_text(xml)
                manifest[accession] = {"cik": cik, "form": form, "filing_date": filed.isoformat(), "instance_url": url,
                                       "retrieved_at": retrieved_at.isoformat()}
                manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        source = RightsFilingSource(cik, accession, form, filed, url)
        try:
            filing, observations = rights_evidence_from_instance(source, xml, retrieved_at=retrieved_at, recorded_at=_now())
        except RightsFilingRefused as exc:
            counts["refused"] += 1
            print(f"  REFUSED {exc}")
            continue
        wrote = rights.record_filing(filing, observations)
        counts["recorded" if wrote else "already"] += 1
        print(f"  {accession}: {form} filed {filed}  observations {len(observations)}")
    if saved is not None and not arguments.from_fetched:
        (saved / "requests.json").write_text(json.dumps(log, indent=1))

    print(f"\nissuer common-equity market cap (descriptive; evaluated {as_of}):")
    for ticker in tickers:
        cap = reader.current(ticker, as_of)
        if cap is None:
            print(f"  {ticker:6} -")
            continue
        low = f"{cap.market_cap_low / 1e9:,.2f}" if cap.market_cap_low else "-"
        high = f"{cap.market_cap_high / 1e9:,.2f}" if cap.market_cap_high else "-"
        print(f"  {ticker:6} {cap.quality.value:22} {low}..{high}B on {cap.economic_date} (counts {cap.count_instant})"
              + (f"  gaps: {', '.join(cap.gaps)}" if cap.gaps else ""))
    print(f"\nSEC requests: attempted {len(log)}  failed {sum(1 for x in log if x['status'] != 'ok')}")
    print(f"filings: recorded {counts['recorded']}  already recorded {counts['already']}  refused {counts['refused']}  "
          f"failed {counts['failed']}  missing from saved {counts['missing']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
