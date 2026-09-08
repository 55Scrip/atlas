"""Backfill the Alpha Case -> instrument binding from existing membership.

Reads Portfolio holdings, Watchlist entries and *removed* Watchlist
entries, and records which instrument each existing Case is about. The
removed rows matter: `AlphaWatchlistStore.get_by_case_id` was left
unfiltered on purpose so a de-listed prospect's Case kept resolving,
and that history is exactly as authoritative here.

Makes no provider call, resolves no canonical security, normalizes no
ticker, and creates no Case. It writes down what the data already says.

Idempotent -- running it twice binds nothing the second time.

A Case whose memberships name two different securities is an integrity
defect, not a tie to break. Those are reported and left unbound;
preferring Portfolio over Watchlist would be the same backwards guess
this binding exists to remove. The run still binds every healthy Case,
so one bad row cannot block the rest, and it exits non-zero so the
conflicts cannot go unnoticed.

    python -m atlas.dev.backfill_case_instrument_bindings [--database PATH]
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine

from atlas.alpha.case_instrument.backfill import backfill_case_instrument_bindings
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.case_instrument.table import create_case_instrument_binding_table
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.core.infrastructure.config.database import resolve_database_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default=None, help="Path to the Atlas database (default: the resolved one).")
    arguments = parser.parse_args()

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)

    create_case_instrument_binding_table(engine)
    create_alpha_portfolio_state_table(engine)
    create_alpha_watchlist_entry_table(engine)

    repository = CaseInstrumentBindingRepository(engine)
    report = backfill_case_instrument_bindings(
        repository, AlphaPortfolioStore(engine), AlphaWatchlistStore(engine)
    )

    print(f"database          : {path}")
    print(f"newly bound       : {len(report.bound)}")
    print(f"already bound     : {len(report.already_bound)}")
    print(f"conflicts         : {len(report.conflicts)}")
    for case_id, tickers in report.conflicts:
        print(f"    CONFLICT {case_id}: {', '.join(tickers)}", file=sys.stderr)

    total = len(repository.list_all())
    print(f"bindings in table : {total}")
    if report.conflicts:
        print("  CONFLICTS PRESENT -- those Cases are unbound and need a decision", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
