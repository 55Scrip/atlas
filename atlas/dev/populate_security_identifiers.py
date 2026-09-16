"""Record the identifiers that let a security survive a change of venue.

Atlas's security master holds tickers and MICs and nothing stronger -- zero
ISINs, zero FIGIs. That works only while every security is American and every
provider speaks American tickers. It fails the moment a holding arrives from
Stockholm, and it is unsafe wherever a ticker is reused: Schneider Electric
trades as `SU` in Paris and Suncor Energy as `SU` in Canada.

This asks OpenFIGI what each canonical security *is*, using ticker together
with venue -- never ticker alone, which is the question that cannot tell those
two apart -- and records what comes back as three separate identifier types.
They mean three different things: one listing, one composite, one share class.
Only the share class is stable worldwide, which is what makes it the useful
one.

Identity only. Nothing here reads or writes a Case, a valuation or a
recommendation, and populating an identifier must never change what Atlas
concludes about a company.

    python -m atlas.dev.populate_security_identifiers [--database PATH] [--apply]
        [--ticker TICKER ...] [--pause SECONDS]

Dry run by default: it prints what it would record and writes nothing.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone

from sqlalchemy import create_engine, insert, select

from atlas.alpha.canonical_security.table import (
    canonical_security_identifiers_table,
    canonical_securities_table,
    create_canonical_security_tables,
)
from atlas.alpha.security_identity_evidence.master_population import PROVIDER, plan_identity
from atlas.alpha.security_identity_evidence.openfigi_adapter import map_ticker
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

#: OpenFIGI allows 25 requests a minute without a key. One security per
#: request, paced, keeps this well inside that without needing one.
_DEFAULT_PAUSE_SECONDS = 3.0

_TYPES = (("figi", "FIGI"), ("composite_figi", "COMPOSITE_FIGI"), ("share_class_figi", "SHARE_CLASS_FIGI"))


def _existing(connection, security_id: str) -> dict[str, str]:
    rows = connection.execute(
        select(canonical_security_identifiers_table)
        .where(canonical_security_identifiers_table.c.canonical_security_id == security_id)
    ).mappings().all()
    return {row["identifier_type"]: row["value"] for row in rows}


def main(argv: list[str] | None = None) -> int:
    ensure_development_environment()
    parser = argparse.ArgumentParser(
        prog="python -m atlas.dev.populate_security_identifiers",
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None)
    parser.add_argument("--apply", action="store_true", help="Write. Without this, nothing is written.")
    parser.add_argument("--ticker", action="append", default=[], help="Limit to these tickers. Repeatable.")
    parser.add_argument("--pause", type=float, default=_DEFAULT_PAUSE_SECONDS)
    arguments = parser.parse_args(argv)

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    create_canonical_security_tables(engine)

    with engine.connect() as connection:
        securities = connection.execute(
            select(canonical_securities_table.c.id,
                   canonical_securities_table.c.native_ticker,
                   canonical_securities_table.c.primary_exchange_mic)
            .order_by(canonical_securities_table.c.native_ticker)
        ).mappings().all()
    wanted = {t.strip().upper() for t in arguments.ticker}
    if wanted:
        securities = [s for s in securities if s["native_ticker"].upper() in wanted]

    print(f"database        : {path}")
    print(f"securities       : {len(securities)}")
    print(f"mode             : {'APPLY' if arguments.apply else 'dry run -- nothing is written'}")
    print(f"provider         : {PROVIDER} (no API key required)\n")

    calls = written = skipped = conflicts = unresolved = 0
    for security in securities:
        ticker, mic = security["native_ticker"], security["primary_exchange_mic"]
        plan = plan_identity(
            ticker=ticker, mic=mic,
            lookup=lambda t, code: map_ticker(t, exchange_code=code),
        )
        if plan.exchange_code is not None:
            calls += 1
            time.sleep(max(0.0, arguments.pause))

        if plan.share_class_figi is None:
            unresolved += 1
            print(f"  {ticker:8} {str(mic):6} -- {plan.reason}")
            continue

        observed = datetime.now(timezone.utc)
        with engine.begin() as connection:
            already = _existing(connection, security["id"])
            for attribute, identifier_type in _TYPES:
                value = getattr(plan, attribute)
                if value is None:
                    continue
                stored = already.get(identifier_type)
                if stored == value:
                    skipped += 1
                    continue
                if stored is not None:
                    conflicts += 1
                    print(f"  {ticker:8} CONFLICT {identifier_type}: stored {stored!r} "
                          f"but provider says {value!r} -- not overwritten", file=sys.stderr)
                    continue
                if arguments.apply:
                    connection.execute(insert(canonical_security_identifiers_table).values(
                        id=f"{security['id']}/{identifier_type}",
                        canonical_security_id=security["id"],
                        identifier_type=identifier_type,
                        value=value,
                        recorded_at=observed.isoformat(),
                        provider=PROVIDER,
                        query_type="TICKER+EXCH",
                        query_value=f"{ticker}@{plan.exchange_code}",
                        observed_at=observed.isoformat(),
                    ))
                written += 1
        print(f"  {ticker:8} {str(mic):6} share_class={plan.share_class_figi}  {plan.provider_name}")

    print(f"\nOpenFIGI calls   : {calls}")
    print(f"identifiers {'written' if arguments.apply else 'that would be written'}: {written}")
    print(f"already recorded : {skipped}")
    print(f"unresolved       : {unresolved}")
    print(f"conflicts        : {conflicts}")
    print("Alpha Vantage    : 0\nSEC              : 0")
    if not arguments.apply:
        print("\n[dry run] nothing written.")
    return 2 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
