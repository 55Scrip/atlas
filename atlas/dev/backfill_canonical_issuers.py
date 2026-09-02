"""One-time backfill: give every existing `CanonicalSecurity` an issuer,
strictly 1:1 (Issuer Identity Foundation, Phase 4).

**Why 1:1 and not smarter.** It is tempting to notice that two rows share
a company name and give them one issuer. That is precisely the merge this
sprint forbids. The identity investigation showed name comparison failing
in both directions at once -- too strict to see `AB Volvo` and `Volvo AB`
as one company, too weak to keep `Volvo AB` and `Volvo Car AB` apart if
loosened -- and Alpha Vantage returned those two Volvos tied at the same
match score. So this script never compares names, tickers, exchanges or
industries. One security in, one issuer out.

The result is deliberately conservative: if a future sprint proves via a
strong identifier that two of these issuers are the same company, merging
two rows is easy. Un-attaching the wrong company's financial statements
from a holding, after a recommendation has been made on them, is not.

**Safe to run repeatedly.** A security that already has an `issuer_id` is
skipped, so this is idempotent. It creates no issuer for a security that
already has one, and never rewrites an existing link.

Run with `--apply` to write; the default is a dry run.
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine, select, update

from atlas.alpha.canonical_security.issuer import CanonicalIssuer
from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalIssuerRepository
from atlas.alpha.canonical_security.table import (
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
        rows = (
            connection.execute(
                select(
                    canonical_securities_table.c.id,
                    canonical_securities_table.c.canonical_company_name,
                    canonical_securities_table.c.country,
                    canonical_securities_table.c.native_ticker,
                    canonical_securities_table.c.issuer_id,
                )
            )
            .mappings()
            .all()
        )

    pending = [row for row in rows if not row["issuer_id"]]
    linked = [row for row in rows if row["issuer_id"]]

    print(f"  canonical securities      : {len(rows)}")
    print(f"  already linked to an issuer: {len(linked)}")
    print(f"  to backfill (1 issuer each): {len(pending)}\n")
    for row in pending:
        print(f"    {row['native_ticker']:10s} {row['canonical_company_name']}")

    if not args.apply:
        print("\n  DRY RUN -- nothing written. Re-run with --apply.")
        return 0
    if not pending:
        print("\n  Nothing to do (idempotent).")
        return 0

    created = 0
    for row in pending:
        issuer = CanonicalIssuer.create(
            legal_name=row["canonical_company_name"],
            jurisdiction=row["country"],
        )
        issuers.save(issuer)
        with engine.begin() as connection:
            connection.execute(
                update(canonical_securities_table)
                .where(canonical_securities_table.c.id == row["id"])
                .where(canonical_securities_table.c.issuer_id.is_(None))
                .values(issuer_id=str(issuer.id))
            )
        created += 1

    with engine.connect() as connection:
        still_null = connection.execute(
            select(canonical_securities_table.c.id).where(
                canonical_securities_table.c.issuer_id.is_(None)
            )
        ).all()
        distinct_issuers = connection.execute(
            select(canonical_securities_table.c.issuer_id).distinct()
        ).all()

    print(f"\n  issuers created           : {created}")
    print(f"  securities still unlinked : {len(still_null)}   (must be 0)")
    print(f"  distinct issuer ids       : {len(distinct_issuers)}   (must equal security count for 1:1)")
    if still_null or len(distinct_issuers) != len(rows):
        print("  POST-CONDITION FAILED", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
