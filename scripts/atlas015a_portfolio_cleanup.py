"""ATLAS-015A — one-time historical cleanup of corrupted portfolio identity.

Root cause (see the sprint's own commit/report for the full trace):
`reconcileRows()` in `frontend/src/portfolio-import/resolution.ts`
applied a manually-typed ticker override on every keystroke with no
minimum-length check, so a person who began typing a ticker (e.g. "A"
on the way to "AAPL") and confirmed the import before finishing was
silently treated as fully resolved. That produced a handful of
single-letter holdings with no recoverable original identity -- the
company name the investor actually typed was never persisted anywhere,
only the truncated ticker. `resolution.ts` now requires >= 2 characters
for a manual entry to resolve (see the same commit), so this cannot
recur; this script is the one-time repair for holdings that already
reached persistence before that fix existed.

A holding is removed by this script only if empirical inspection (not
guessing) confirms all of the following, run once against the live
`atlas.db` before this script was written:
  - it has no linked Investment Case (`case_id is None`)
  - no Decision anywhere in Core references it by subject
  - no Alpha trade-log entry anywhere references it as `security`
i.e. it is completely inert data with zero corroborating portfolio
activity. Every other holding in the portfolio -- including genuine
single-letter tickers like "V" (Visa) or "F" (Ford), had one existed --
is left untouched; letter-count is never used as the removal criterion,
only the absence of any real activity plus the fixed identifier list
below (verified against this specific portfolio, not inferred).

Usage:
    python scripts/atlas015a_portfolio_cleanup.py            # dry run
    python scripts/atlas015a_portfolio_cleanup.py --apply     # writes

Only ever removes holdings; never renormalizes the remaining weights or
invents a replacement value -- the same "never invent" rule Portfolio
Import and Execution already follow elsewhere in this codebase.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine  # noqa: E402

from atlas.alpha.portfolio.store import AlphaPortfolioStore  # noqa: E402
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table  # noqa: E402
from atlas.config import DATABASE_PATH  # noqa: E402

# Verified empirically (see module docstring) against the live database
# before this script was written -- not a general "single letter is bad"
# rule. Do not extend this list speculatively; a future corrupted
# holding needs its own verification pass, not an addition here.
CONFIRMED_CORRUPTED_TICKERS = frozenset({"A", "B", "C", "D", "E", "F"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Write the change. Without this flag, only reports what would happen."
    )
    args = parser.parse_args()

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DATABASE_PATH}", future=True)
    create_alpha_portfolio_state_table(engine)
    store = AlphaPortfolioStore(engine)

    state = store.get()
    if state is None:
        print("No Alpha portfolio state exists. Nothing to clean up.")
        return

    to_remove = [h for h in state.holdings if h.ticker in CONFIRMED_CORRUPTED_TICKERS]
    if not to_remove:
        print("No confirmed-corrupted holdings found. Nothing to do.")
        return

    print(f"Found {len(to_remove)} confirmed-corrupted holding(s):")
    for holding in to_remove:
        print(
            f"  {holding.ticker}  weight={holding.weight_percent}%  "
            f"caseId={holding.case_id}  reconciliationStatus={holding.reconciliation_status.value}"
        )

    remaining = tuple(h for h in state.holdings if h.ticker not in CONFIRMED_CORRUPTED_TICKERS)
    print(f"\n{len(remaining)} holding(s) will remain, untouched (no reweighting).")

    if not args.apply:
        print("\nDry run only -- no changes written. Re-run with --apply to write this change.")
        return

    new_state = replace(state, holdings=remaining, updated_at=datetime.now(timezone.utc))
    store.replace(new_state)
    print(f"\nWrote updated state: {len(new_state.holdings)} holding(s) remain.")


if __name__ == "__main__":
    main()
