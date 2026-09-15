"""Re-version stored SEC financial statements from a saved companyfacts
payload -- SEC only (SEC-Only Content Refresh v1).

A statement ingested before the SEC adapter captured some concept, or the
filing behind its share count, cannot gain that through
`backfill_market_data_provenance --sec`: its content differs, and an
enrichment may add provenance, never content. This command compares every
stored statement of the named tickers with what the production adapter
reads from the filer's companyfacts today
(`business_data_refresh.sec_statement_content`) and writes only:

- the missing provenance of a statement whose content is identical, and
- a new version of a statement whose new content only adds to it -- every
  stored value, period, publication and source repeated exactly.

A statement with any stored value changed, and any period Atlas holds no
statement for, is held and reported: bringing that in is a decision this
command never makes.

**Explicit tickers only**; each one's SEC filer is the CIK its own stored
statements carry (exactly one, or the ticker is refused). **One keyless
request per filer**, and only with `--save-fetched DIR` (the payload is
saved with its URL, retrieval time and checksum); `--from-fetched DIR`
replays that saved payload with no request -- rehearse on a database copy,
then apply the same payload live. No Alpha Vantage request, no quote, no
profile, no filing history; no Case, decision or methodology is touched.
Append-only: every stored version stays; a re-run writes nothing.

    python -m atlas.dev.refresh_sec_statement_content --tickers TICKER[,TICKER]
        (--save-fetched DIR | --from-fetched DIR) [--database PATH] [--dry-run] [--max-requests N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.sec_statement_content import (
    ContentKind,
    companyfacts_url,
    content_refresh_records,
    fetch_companyfacts,
    statement_documents,
)
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.core.infrastructure.config.database import resolve_database_path

_SAVED_MANIFEST = "manifest.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _filer(records) -> str | None:
    ciks = {f"{int(r.metadata['sec_cik']):010d}" for r in records
            if r.document_type is SourceKind.FINANCIAL_STATEMENT and str(r.metadata.get("sec_cik") or "").isdigit()}
    return ciks.pop() if len(ciks) == 1 else None


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_saved(saved: Path, cik10: str) -> tuple[object, datetime] | None:
    manifest_path = saved / _SAVED_MANIFEST
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    entry = manifest.get(cik10)
    if entry is None:
        return None
    payload_path = saved / entry["file"]
    if _checksum(payload_path) != entry["sha256"]:
        raise SystemExit(f"STOPPED: {payload_path} does not match its saved checksum")
    return json.loads(payload_path.read_text()), datetime.fromisoformat(entry["retrieved_at"])


def _save(saved: Path, cik10: str, tickers: list[str], payload: object, retrieved_at: datetime) -> None:
    saved.mkdir(parents=True, exist_ok=True)
    name = f"companyfacts_CIK{cik10}.json"
    (saved / name).write_text(json.dumps(payload))
    manifest_path = saved / _SAVED_MANIFEST
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest[cik10] = {"file": name, "url": companyfacts_url(cik10), "tickers": tickers,
                       "retrieved_at": retrieved_at.isoformat(), "sha256": _checksum(saved / name)}
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True))


def _fmt(value) -> str:
    return "-" if value is None else f"{value:,.0f}" if isinstance(value, float) else str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m atlas.dev.refresh_sec_statement_content",
                                     description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers (required).")
    parser.add_argument("--save-fetched", default=None, help="Fetch each filer's companyfacts once and save it here.")
    parser.add_argument("--from-fetched", default=None, help="Replay payloads saved by --save-fetched; no request.")
    parser.add_argument("--max-requests", type=int, default=0, help="SEC requests this run may make.")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args(argv)
    if bool(arguments.save_fetched) == bool(arguments.from_fetched):
        parser.error("choose exactly one of --save-fetched and --from-fetched")

    path = arguments.database or resolve_database_path()
    repository = SqlAlchemyBusinessRecordRepository(create_engine(f"sqlite:///{path}", future=True))
    tickers = sorted({t.strip().upper() for t in arguments.tickers.split(",") if t.strip()})
    records = {t: tuple(repository.get_by_company(t)) for t in tickers}
    filers: dict[str, list[str]] = {}
    refused = []
    for ticker in tickers:
        cik = _filer(records[ticker])
        if cik is None:
            refused.append(f"{ticker}: its stored statements name no single SEC filer")
        else:
            filers.setdefault(cik, []).append(ticker)
    saved = Path(arguments.from_fetched or arguments.save_fetched)
    replay = bool(arguments.from_fetched)
    planned = 0 if replay else len(filers)
    print(f"database        : {path}")
    for cik, owners in sorted(filers.items()):
        print(f"  CIK {cik}  {','.join(owners)}  {companyfacts_url(cik)}")
    for r in refused:
        print(f"  REFUSED {r}")
    print(f"SEC EDGAR       : {planned} keyless requests (cap {arguments.max_requests}); Alpha Vantage: 0")
    if arguments.dry_run and not replay:
        print("\n[dry run] no request made, nothing written.")
        return 0
    if planned > arguments.max_requests:
        print(f"STOPPED: {planned} requests planned, cap {arguments.max_requests}")
        return 1

    requests = 0
    totals = {k: 0 for k in ContentKind}
    changed_values = {"free_cash_flow": 0, "shares_outstanding": 0, "other": 0}
    written = 0
    for cik, owners in sorted(filers.items()):
        loaded = _load_saved(saved, cik) if replay else None
        if replay and loaded is None:
            print(f"  CIK {cik}: not in {saved} -- skipped")
            continue
        if loaded is None:
            retrieved_at = _now()
            payload = fetch_companyfacts(cik)
            requests += 1
            _save(saved, cik, owners, payload, retrieved_at)
        else:
            payload, retrieved_at = loaded
        for ticker in owners:
            documents = statement_documents(ticker, cik, payload)
            planned_records = content_refresh_records(documents, records[ticker], evaluated_at=retrieved_at)
            print(f"\n{ticker} (evidence retrieved {retrieved_at.isoformat()}):")
            for comparison, record in planned_records:
                totals[comparison.kind] += 1
                line = f"  {comparison.period_end}  {comparison.kind.value:15}"
                if comparison.added:
                    line += f"  +{len(comparison.added)} fields"
                if comparison.provenance_added:
                    line += f"  +provenance({len(comparison.provenance_added)})"
                if record is not None:
                    line += f"  -> {record.id}"
                print(line)
                for name, stored, now in comparison.changed:
                    changed_values[name if name in changed_values else "other"] += 1
                    print(f"      HELD {name}: stored {_fmt(stored)} -> now {_fmt(now)}")
            if not arguments.dry_run:
                for _, record in planned_records:
                    if record is not None:
                        repository.add(record)
                        written += 1
            else:
                written += sum(1 for _, record in planned_records if record is not None)

    print("\nstatements: " + "  ".join(f"{k.value} {v}" for k, v in totals.items()))
    print("stored values changed (held): " + "  ".join(f"{k} {v}" for k, v in changed_values.items()))
    print(f"versions {'that would be written' if arguments.dry_run else 'written'}: {written}")
    print(f"SEC requests made: {requests}  Alpha Vantage requests made: 0")
    if arguments.dry_run:
        print("[dry run] nothing written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
