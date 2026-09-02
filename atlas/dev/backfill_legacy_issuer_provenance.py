"""Repair issuer provenance on legacy BusinessRecords. Zero provider calls.

Attaches `canonical_issuer_id` to records that predate the Identity Gate,
using only SEC CIK evidence that an *already-linked* record has
independently established for an issuer.

Never reads a ticker or a company name. `plan_legacy_repair` is not even
given them, so no future edit can quietly start matching on one.

Never sets `canonical_security_id`: a CIK proves which filer produced a
filing, not which listing generated the record.

Dry run by default; `--apply` to write. Idempotent -- an already-repaired
record reports `ALREADY_LINKED`/`ISSUER_PROVEN` and is skipped because it
is already at its target value. Back up the database before applying.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from sqlalchemy import create_engine, select, update

from atlas.alpha.business_data_refresh.table import (
    business_record_table,
    create_business_record_table,
)
from atlas.alpha.canonical_security.legacy_provenance import (
    LegacyRepairOutcome,
    build_cik_to_issuer_index,
    plan_legacy_repair,
)
from atlas.alpha.canonical_security.table import (
    canonical_securities_table,
    create_canonical_security_tables,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="database/atlas.db")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    engine = create_engine(f"sqlite:///{args.database}", future=True)
    # Both table sets are synced first: `sync_table_schema` is what
    # adds the new nullable `canonical_issuer_id` column to an existing
    # development database, with no manual migration step.
    create_business_record_table(engine)
    create_canonical_security_tables(engine)

    with engine.connect() as connection:
        issuer_by_security = {
            row["id"]: row["issuer_id"]
            for row in connection.execute(
                select(canonical_securities_table.c.id, canonical_securities_table.c.issuer_id)
            ).mappings()
        }
        rows = (
            connection.execute(
                select(
                    business_record_table.c.id,
                    business_record_table.c.canonical_security_id,
                    business_record_table.c.canonical_issuer_id,
                    business_record_table.c.document_type,
                    business_record_table.c.metadata_json,
                )
            )
            .mappings()
            .all()
        )

    parsed = []
    for row in rows:
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except json.JSONDecodeError:
            metadata = {}
        parsed.append((row["id"], row["canonical_security_id"], row["document_type"], metadata, row["canonical_issuer_id"]))

    index = build_cik_to_issuer_index(
        tuple((r[0], r[1], r[3]) for r in parsed), issuer_by_security
    )
    print(f"  business records                 : {len(parsed)}")
    print(f"  CIKs proven for an issuer        : {len(index)}")
    for cik, issuers in sorted(index.items()):
        marker = "  <-- ambiguous" if len(issuers) > 1 else ""
        print(f"    {cik} -> {len(issuers)} issuer(s){marker}")

    repairs = plan_legacy_repair(tuple((r[0], r[1], r[2], r[3]) for r in parsed), index)
    counts = Counter(repair.outcome.value for repair in repairs)
    print("\n  outcome breakdown:")
    for outcome in LegacyRepairOutcome:
        if counts.get(outcome.value):
            print(f"    {outcome.value:28s} {counts[outcome.value]:5d}")

    current_issuer = {r[0]: r[4] for r in parsed}
    pending = [
        repair
        for repair in repairs
        if repair.is_repairable and current_issuer.get(repair.record_id) != repair.canonical_issuer_id
    ]
    print(f"\n  records to repair now            : {len(pending)}")
    by_issuer = Counter(repair.canonical_issuer_id for repair in pending)
    for issuer_id, count in sorted(by_issuer.items()):
        print(f"    issuer {issuer_id}: {count} record(s)")

    if not pending:
        print("\n  Nothing to repair (idempotent -- already at target state).")
        return 0
    if not args.apply:
        print("\n  DRY RUN -- nothing written. Re-run with --apply.")
        return 0

    with engine.begin() as connection:
        for repair in pending:
            connection.execute(
                update(business_record_table)
                .where(business_record_table.c.id == repair.record_id)
                .values(canonical_issuer_id=repair.canonical_issuer_id)
            )

    with engine.connect() as connection:
        total = connection.execute(select(business_record_table.c.id)).all()
        with_issuer = connection.execute(
            select(business_record_table.c.id).where(
                business_record_table.c.canonical_issuer_id.isnot(None)
            )
        ).all()
        wrongly_given_security = connection.execute(
            select(business_record_table.c.id)
            .where(business_record_table.c.canonical_issuer_id.isnot(None))
            .where(business_record_table.c.canonical_security_id.isnot(None))
            .where(business_record_table.c.document_type == "market_data_snapshot")
        ).all()
    print(f"\n  records repaired                 : {len(pending)}")
    print(f"  total records (must be unchanged): {len(total)}")
    print(f"  records with issuer provenance   : {len(with_issuer)}")
    print(f"  price records given issuer prov. : {len(wrongly_given_security)}   (must be 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
