"""Give every security Atlas has actually analysed a bound Case.

Atlas persists company data for securities that have no Case, because
enrichment and canonical-security work reached them without anyone
adding them to a Portfolio or a Watchlist. Those are precisely the
independent ideas Discovery should be able to surface -- but Discovery
reads bound Cases, and a security with no Case has nothing to read.

This adopts them: for each ticker with persisted `BusinessRecord`s and
no Case, it ensures one through the canonical `CaseGenerationService`,
which writes the instrument binding at the same time.

Deliberately an operator command, not something Discovery does while
rendering. Creating rows as a side effect of opening a page is how
"list composition" and "explicit case creation" get confused, and this
codebase keeps them apart.

Creates only Case identity: no membership, no Decision Memory, no
analysis, no provider call. Idempotent -- a second run adopts nothing.
Refuses to run outside a development environment, before it reads or
writes anything.

    python -m atlas.dev.adopt_analysed_securities [--database PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine, select

from atlas.alpha.business_data_refresh.table import business_record_table
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.case_instrument.table import create_case_instrument_binding_table
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import SqlAlchemyCaseRepository
from atlas.core.infrastructure.persistence.case.table import create_case_table
from atlas.dev.guard import ensure_development_environment


def main() -> int:
    ensure_development_environment()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=None, help="Path to the Atlas database (default: the resolved one).")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be adopted, write nothing.")
    arguments = parser.parse_args()

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    create_case_instrument_binding_table(engine)
    create_case_table(engine)

    bindings = CaseInstrumentBindingRepository(engine)
    generation = CaseGenerationService(CaseService(SqlAlchemyCaseRepository(engine)), bindings)

    with engine.connect() as connection:
        known = sorted(
            {row[0] for row in connection.execute(select(business_record_table.c.company).distinct())}
        )
    already = {binding.instrument_key for binding in bindings.list_all()}
    missing = [ticker for ticker in known if ticker not in already]

    print(f"database              : {path}")
    print(f"securities with data  : {len(known)}")
    print(f"already have a Case   : {len(already & set(known))}")
    print(f"to adopt              : {len(missing)}")
    if missing:
        print(f"                        {', '.join(missing)}")

    if arguments.dry_run:
        print("dry run -- nothing written")
        return 0

    for ticker in missing:
        generation.ensure_case_id(current_case_id=None, ticker=ticker)

    print(f"adopted               : {len(missing)}")
    print(f"bindings in table     : {len(bindings.list_all())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
