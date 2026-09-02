"""CIK-backed issuer reconciliation over stored data.

Finds every `CanonicalSecurity` whose own `BusinessRecord`s carry one
consistent SEC CIK, groups them by that CIK, and folds duplicate issuers
into one -- but only where an identical filer id proves the securities
belong to one company.

**Requires no provider call.** Every CIK it reads was ingested long ago
and sits in `business_records.metadata_json`.

**Evidence is collected strictly through `canonical_security_id`.**
Matching records by ticker string would reintroduce exactly the
`SU`/`SU.PA` class of collision this whole arc exists to prevent. The
cost is real: most stored CIK records predate the identity gate, carry
no security link, and are therefore invisible here.

**This may reduce duplicate issuers. It must never reduce securities.**
`reassign_security_issuer` touches only `issuer_id`; ticker, exchange,
currency, share class, listings and provider mappings are untouched.

Idempotent: a second run finds every security already on the surviving
issuer and plans nothing. Run with `--apply`; the default is a dry run.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import create_engine, select

from atlas.alpha.business_data_refresh.table import business_record_table
from atlas.alpha.canonical_security.issuer_cik import (
    extract_cik_evidence,
    plan_issuer_reconciliation,
)
from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalIssuerRepository
from atlas.alpha.canonical_security.table import (
    canonical_issuers_table,
    canonical_securities_table,
    create_canonical_security_tables,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="database/atlas.db")
    parser.add_argument("--apply", action="store_true", help="write (default: dry run)")
    args = parser.parse_args()

    engine = create_engine(f"sqlite:///{args.database}", future=True)
    create_canonical_security_tables(engine)
    issuers = SqlAlchemyCanonicalIssuerRepository(engine)

    with engine.connect() as connection:
        securities = (
            connection.execute(
                select(
                    canonical_securities_table.c.id,
                    canonical_securities_table.c.native_ticker,
                    canonical_securities_table.c.issuer_id,
                )
            )
            .mappings()
            .all()
        )
        record_rows = (
            connection.execute(
                select(
                    business_record_table.c.canonical_security_id,
                    business_record_table.c.metadata_json,
                ).where(business_record_table.c.canonical_security_id.isnot(None))
            )
            .mappings()
            .all()
        )
        issuer_rows = (
            connection.execute(
                select(canonical_issuers_table.c.id, canonical_issuers_table.c.created_at)
            )
            .mappings()
            .all()
        )

    metadata_by_security: dict[str, list[dict]] = defaultdict(list)
    for row in record_rows:
        try:
            metadata_by_security[row["canonical_security_id"]].append(
                json.loads(row["metadata_json"] or "{}")
            )
        except json.JSONDecodeError:
            continue

    ticker_of = {row["id"]: row["native_ticker"] for row in securities}
    issuer_of = {row["id"]: row["issuer_id"] for row in securities}
    created_at = {
        row["id"]: datetime.fromisoformat(row["created_at"]) for row in issuer_rows
    }

    evidence = tuple(
        extract_cik_evidence(row["id"], tuple(metadata_by_security.get(row["id"], ())))
        for row in securities
    )

    print(f"  canonical securities            : {len(securities)}")
    print(f"  records linked to a security    : {len(record_rows)}")
    print("\n  CIK evidence per security:")
    for item in sorted(evidence, key=lambda e: ticker_of.get(e.canonical_security_id, "")):
        ticker = ticker_of.get(item.canonical_security_id, "?")
        detail = item.cik or (",".join(item.observed) if item.observed else "-")
        print(f"    {ticker:10s} {item.state.value:20s} {detail}")

    plans = plan_issuer_reconciliation(evidence, issuer_of, created_at)
    mergeable = [plan for plan in plans if not plan.is_noop]

    print(f"\n  CIK groups examined             : {len(plans)}")
    print(f"  groups needing reconciliation   : {len(mergeable)}")
    for plan in mergeable:
        tickers = [ticker_of.get(s, "?") for s in plan.security_ids]
        print(f"    CIK {plan.cik}: {tickers}")
        print(f"      surviving issuer : {plan.surviving_issuer_id}")
        print(f"      issuers merged   : {list(plan.merged_issuer_ids)}")

    if not mergeable:
        print("\n  Nothing to reconcile — no CIK covers more than one issuer.")
        return 0
    if not args.apply:
        print("\n  DRY RUN — nothing written. Re-run with --apply.")
        return 0

    moved = 0
    for plan in mergeable:
        for security_id in plan.security_ids:
            if issuer_of.get(security_id) != plan.surviving_issuer_id:
                issuers.reassign_security_issuer(security_id, plan.surviving_issuer_id)
                moved += 1

    with engine.connect() as connection:
        remaining = connection.execute(
            select(canonical_securities_table.c.id).where(
                canonical_securities_table.c.issuer_id.is_(None)
            )
        ).all()
        security_count = connection.execute(
            select(canonical_securities_table.c.id)
        ).all()
    print(f"\n  securities moved to a surviving issuer : {moved}")
    print(f"  securities total (must be unchanged)   : {len(security_count)}")
    print(f"  securities with no issuer              : {len(remaining)}   (must be 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
