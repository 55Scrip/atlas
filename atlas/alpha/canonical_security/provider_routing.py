"""Provider symbol routing: which string to send one provider when
asking about a security Atlas knows by another string.

Berkshire Hathaway Class B is the case this exists for. Atlas, the
portfolio, and the user all know it as `BRK.B`. Alpha Vantage answers
only to `BRK-B` -- verified live on 2026-09-04, one OVERVIEW request:
`BRK.B` returned a parseable body with no identity fields, `BRK-B`
returned name, exchange, country, currency and asset type. SEC EDGAR,
meanwhile, resolves the same company through a CIK and needs neither
spelling.

**This module contains no rule, and must never contain one.** It does
not transform `BRK.B` into `BRK-B`; it *looks up* a route that a human
approved and Atlas stored. A generic dot-to-hyphen rule would be the
same class of error as suffix stripping: `SU` and `SU.PA` are two
different companies, `BRK.A` and `BRK.B` are two different share
classes with different voting rights, and `VOLV-B`'s hyphen is a Nasdaq
Stockholm convention unrelated to Berkshire's. No spelling implies
another spelling. A test asserts this module's source contains no
`replace`, `strip`, `split`, or `-`-for-`.` substitution.

Routing is **not identity**. A route says only "this provider calls it
that"; it never renames a security, never creates one, never creates an
issuer, and never reaches the portfolio, the watchlist, or anything the
user sees. Absence of a route is the normal case and means "send the
canonical ticker unchanged" -- not an error, and never a reason to
guess.

Routes are read from `ProviderMapping` rows, the abstraction Sprint L
already built for exactly this: one provider's claim about a security's
identity, keyed by `(provider_name, provider_ticker)` and hanging off
the CanonicalSecurity rather than replacing any part of it.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ProviderSymbolRoute",
    "RoutingTable",
    "build_routing_table",
    "resolve_provider_symbol",
]


@dataclass(frozen=True)
class ProviderSymbolRoute:
    """One stored fact: `provider_name` calls `canonical_ticker` by
    `provider_symbol`. Both strings are recorded verbatim -- neither is
    derived from the other."""

    canonical_ticker: str
    provider_name: str
    provider_symbol: str

    def __post_init__(self) -> None:
        for field_name in ("canonical_ticker", "provider_name", "provider_symbol"):
            value = getattr(self, field_name)
            if not value or not value.strip():
                raise ValueError(f"ProviderSymbolRoute.{field_name} must be non-empty")


#: `(provider_name, canonical_ticker) -> provider_symbol`.
RoutingTable = dict[tuple[str, str], str]


def build_routing_table(
    routes: tuple[ProviderSymbolRoute, ...],
) -> RoutingTable:
    """Deterministic and order-independent for consistent input.

    A route whose symbol equals the canonical ticker is dropped: it
    carries no information, and keeping it would let the table grow one
    entry per security while saying nothing. Two *different* symbols
    claimed for the same `(provider, ticker)` pair is a contradiction in
    stored data, and raises rather than picking one -- silently choosing
    between them is how a wrong symbol would become permanent.
    """
    table: RoutingTable = {}
    for route in routes:
        if route.provider_symbol == route.canonical_ticker:
            continue
        key = (route.provider_name, route.canonical_ticker)
        existing = table.get(key)
        if existing is not None and existing != route.provider_symbol:
            raise ValueError(
                f"conflicting provider symbols for {key}: {existing!r} and {route.provider_symbol!r}"
            )
        table[key] = route.provider_symbol
    return table


def resolve_provider_symbol(
    canonical_ticker: str,
    provider_name: str | None,
    *,
    routing_table: RoutingTable,
) -> str:
    """The string to send this provider. Total, pure, and never
    fabricating: with no stored route -- or no provider name to key on
    -- the canonical ticker goes out unchanged, which is correct for
    every security whose spelling both sides already agree on.

    Routing is per `(provider, ticker)`, so SEC EDGAR keeps whatever
    notation it needs for the same security independently of Alpha
    Vantage, and neither can affect the other.
    """
    if not provider_name:
        return canonical_ticker
    return routing_table.get((provider_name, canonical_ticker), canonical_ticker)


def load_routes(connection) -> tuple[ProviderSymbolRoute, ...]:
    """Read every stored route: the bootstrap `provider_symbol_routes`
    table, plus any `ProviderMapping` whose provider ticker differs from
    its security's own native ticker.

    Reading both is what keeps `ProviderMapping` the long-term home. A
    mapping recorded by the ordinary resolution path is just as much a
    stored fact as a bootstrap row, and `build_routing_table` drops the
    no-op ones -- today every one of the 35 mappings matches its
    security's ticker exactly, so they contribute nothing and cost
    nothing.
    """
    from sqlalchemy import text

    routes: list[ProviderSymbolRoute] = [
        ProviderSymbolRoute(canonical_ticker=ticker, provider_name=provider, provider_symbol=symbol)
        for provider, ticker, symbol in connection.execute(text(
            "select provider_name, canonical_ticker, provider_symbol from provider_symbol_routes"
        ))
    ]
    routes.extend(
        ProviderSymbolRoute(canonical_ticker=ticker, provider_name=provider, provider_symbol=symbol)
        for provider, symbol, ticker in connection.execute(text(
            "select m.provider_name, m.provider_ticker, s.native_ticker "
            "from canonical_security_provider_mappings m "
            "join canonical_securities s on s.id = m.canonical_security_id"
        ))
    )
    return tuple(routes)
