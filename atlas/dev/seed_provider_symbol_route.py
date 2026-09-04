"""Record the one provider symbol route proven by live verification.

Berkshire Hathaway Class B: Atlas knows it as `BRK.B`; Alpha Vantage
answers only to `BRK-B`. Verified 2026-09-04T09:38:53Z with a single
OVERVIEW request, which returned name "Berkshire Hathaway Inc",
exchange NYSE, country USA, currency USD, asset type Common Stock --
where the same request for `BRK.B` had returned no identity fields at
all.

This writes a stored fact. It is not a rule, and adding a second route
means proving a second one the same way. Idempotent; dry run by default.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from atlas.alpha.canonical_security.table import create_canonical_security_tables

ROUTE = {
    "provider_name": "ALPHA_VANTAGE",
    "canonical_ticker": "BRK.B",
    "provider_symbol": "BRK-B",
    "evidence": (
        "Live OVERVIEW 2026-09-04T09:38:53Z: BRK-B returned name/exchange/country/"
        "currency/asset_type; BRK.B returned no identity fields (NoIdentityDataForSymbol)."
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--database", default="database/atlas.db")
    args = parser.parse_args()

    engine = create_engine(f"sqlite:///{args.database}", future=True)
    create_canonical_security_tables(engine)

    with engine.connect() as connection:
        existing = connection.execute(text(
            "select provider_symbol from provider_symbol_routes "
            "where provider_name = :provider_name and canonical_ticker = :canonical_ticker"
        ), ROUTE).scalar()

    print(f"{'MODE':20s} {'APPLY' if args.apply else 'DRY RUN'}")
    for key in ("provider_name", "canonical_ticker", "provider_symbol"):
        print(f"{key:20s} {ROUTE[key]!r}")
    print(f"{'already stored':20s} {existing!r}")

    if existing == ROUTE["provider_symbol"]:
        print("\n  already present and identical -- nothing to do.")
        return 0
    if existing is not None:
        print(f"\n  REFUSED: a different symbol {existing!r} is already stored.")
        return 1
    if not args.apply:
        print("\n  DRY RUN -- nothing written.")
        return 0

    with engine.begin() as connection:
        connection.execute(text(
            "insert into provider_symbol_routes "
            "(provider_name, canonical_ticker, provider_symbol, evidence, recorded_at) "
            "values (:provider_name, :canonical_ticker, :provider_symbol, :evidence, :recorded_at)"
        ), {**ROUTE, "recorded_at": datetime.now(timezone.utc).isoformat()})
    print("\n  route recorded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
