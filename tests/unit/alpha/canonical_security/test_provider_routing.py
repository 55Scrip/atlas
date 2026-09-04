"""Provider symbol routing -- the BRK.B -> BRK-B pattern.

Atlas knows Berkshire Class B as `BRK.B`. Alpha Vantage answers only to
`BRK-B`, verified live on 2026-09-04 with one OVERVIEW request. The
danger in encoding that is not the fact itself but the shape of the
fix: a dot-to-hyphen rule would be indistinguishable from the suffix
stripping that would merge `SU` (Suncor) with `SU.PA` (Schneider
Electric), and would silently claim `BRK.A` and `BRK.B` are the same
instrument. These tests pin that the implementation is a lookup of
stored facts and can never become a rule.
"""
from __future__ import annotations

import ast
import inspect

import pytest

from atlas.alpha.canonical_security import provider_routing
from atlas.alpha.canonical_security.provider_routing import (
    ProviderSymbolRoute,
    build_routing_table,
    resolve_provider_symbol,
)

def _executable_source(module) -> str:
    """The module's code with every docstring removed.

    Scanning raw source would flag this module's own prose -- it
    discusses `CanonicalSecurity`, the portfolio, and why no `.replace`
    rule may exist -- and a guard that trips on its own explanation
    teaches nothing.
    """
    tree = ast.parse(inspect.getsource(module))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            body.pop(0)
    return ast.unparse(tree)


_BERKSHIRE = ProviderSymbolRoute(
    canonical_ticker="BRK.B", provider_name="ALPHA_VANTAGE", provider_symbol="BRK-B"
)


@pytest.fixture
def table():
    return build_routing_table((_BERKSHIRE,))


class TestTheProvenRoute:
    def test_alpha_vantage_receives_the_hyphen_form(self, table):
        assert resolve_provider_symbol("BRK.B", "ALPHA_VANTAGE", routing_table=table) == "BRK-B"

    def test_sec_keeps_its_own_notation_independently(self, table):
        """SEC resolves Berkshire through a CIK and needs neither
        spelling. Routing is keyed per provider, so Alpha Vantage's
        route cannot reach it."""
        assert resolve_provider_symbol("BRK.B", "SEC_EDGAR", routing_table=table) == "BRK.B"

    def test_sec_may_hold_its_own_route_for_the_same_ticker(self):
        """Two providers, same security, different notations, neither
        affecting the other."""
        both = build_routing_table((
            _BERKSHIRE,
            ProviderSymbolRoute("BRK.B", "SEC_EDGAR", "BRK-B-SEC"),
        ))
        assert resolve_provider_symbol("BRK.B", "ALPHA_VANTAGE", routing_table=both) == "BRK-B"
        assert resolve_provider_symbol("BRK.B", "SEC_EDGAR", routing_table=both) == "BRK-B-SEC"

    def test_a_provider_declaring_no_name_is_never_routed(self, table):
        assert resolve_provider_symbol("BRK.B", None, routing_table=table) == "BRK.B"


class TestNoGenericRuleExists:
    def test_brk_a_is_untouched_and_remains_distinct(self, table):
        """The share class Atlas has NOT proven. `BRK.A` and `BRK.B`
        are different instruments with different voting rights; a rule
        would have routed both."""
        assert resolve_provider_symbol("BRK.A", "ALPHA_VANTAGE", routing_table=table) == "BRK.A"
        assert resolve_provider_symbol("BRK.A", "ALPHA_VANTAGE", routing_table=table) != "BRK-A"

    def test_su_pa_and_su_are_both_untouched(self, table):
        """The verified case that proves naive normalization is unsafe:
        `SU` is Suncor on NYSE, `SU.PA` is Schneider Electric on
        Euronext Paris. Neither may be rewritten, and neither may
        become the other."""
        assert resolve_provider_symbol("SU.PA", "ALPHA_VANTAGE", routing_table=table) == "SU.PA"
        assert resolve_provider_symbol("SU", "ALPHA_VANTAGE", routing_table=table) == "SU"

    @pytest.mark.parametrize("ticker", ["BRK.A", "SU.PA", "BF.B", "RDS.A", "VOLV-B", "NVDA"])
    def test_no_other_dotted_or_hyphenated_ticker_is_rewritten(self, table, ticker):
        assert resolve_provider_symbol(ticker, "ALPHA_VANTAGE", routing_table=table) == ticker

    def test_the_module_contains_no_string_surgery(self):
        """Structural, not behavioural: a rule cannot be added here
        without this failing. `VOLV-B`'s hyphen is a Nasdaq Stockholm
        convention unrelated to Berkshire's, so no spelling implies
        another."""
        source = _executable_source(provider_routing)
        for forbidden in (".replace(", ".split(", ".rstrip(", ".lstrip(",
                          "re.sub", "re.match", "endswith", "startswith",
                          "translate", "maketrans"):
            assert forbidden not in source, forbidden
        # `.strip()` survives, and only there: it rejects a blank field
        # in `__post_init__`. It never produces a symbol -- every value
        # returned by this module is either a dict lookup or the
        # caller's own unmodified ticker.
        assert source.count(".strip()") == source.count("value.strip()")


class TestTableConstruction:
    def test_a_route_equal_to_the_canonical_ticker_is_dropped(self):
        """Today all 35 stored ProviderMappings match their security's
        ticker exactly. Keeping them would grow the table by one entry
        per security while saying nothing."""
        assert build_routing_table((ProviderSymbolRoute("NVDA", "ALPHA_VANTAGE", "NVDA"),)) == {}

    def test_conflicting_symbols_raise_rather_than_pick_one(self):
        with pytest.raises(ValueError, match="conflicting provider symbols"):
            build_routing_table((
                _BERKSHIRE,
                ProviderSymbolRoute("BRK.B", "ALPHA_VANTAGE", "BRKB"),
            ))

    def test_the_same_route_twice_is_not_a_conflict(self):
        assert build_routing_table((_BERKSHIRE, _BERKSHIRE)) == {("ALPHA_VANTAGE", "BRK.B"): "BRK-B"}

    def test_construction_is_order_independent(self):
        a = ProviderSymbolRoute("BRK.B", "ALPHA_VANTAGE", "BRK-B")
        b = ProviderSymbolRoute("X.Y", "SEC_EDGAR", "X-Y")
        assert build_routing_table((a, b)) == build_routing_table((b, a))

    def test_resolution_is_deterministic_across_repeated_calls(self, table):
        assert len({resolve_provider_symbol("BRK.B", "ALPHA_VANTAGE", routing_table=table)
                    for _ in range(50)}) == 1

    def test_an_empty_table_routes_nothing(self):
        assert resolve_provider_symbol("BRK.B", "ALPHA_VANTAGE", routing_table={}) == "BRK.B"

    @pytest.mark.parametrize("bad", ["", "   "])
    def test_a_blank_component_is_rejected(self, bad):
        with pytest.raises(ValueError):
            ProviderSymbolRoute(canonical_ticker=bad, provider_name="ALPHA_VANTAGE",
                                provider_symbol="BRK-B")


class TestArchitectureBoundaries:
    def test_routing_never_touches_identity_or_persistence(self):
        """Routing is not identity. The module may not reach for a
        security, an issuer, a repository, or the portfolio."""
        source = _executable_source(provider_routing)
        for forbidden in ("CanonicalSecurity", "CanonicalIssuer", "issuer_id",
                          "portfolio", "watchlist", "repository"):
            assert forbidden not in source, forbidden

    def test_the_enrichment_service_does_not_import_canonical_security(self):
        """`business_data_refresh` may not import this foundation --
        the resolver is injected as a plain callable through the gate
        package instead, which is the sanctioned seam."""
        from pathlib import Path

        target = "atlas.alpha.canonical_security"
        source = Path("atlas/alpha/business_data_refresh/service.py").read_text()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                # Dot-boundary safe: a plain `startswith` would flag the
                # sibling package `canonical_security_gate`, which the
                # service imports legitimately as the sanctioned seam.
                assert not (module == target or module.startswith(target + ".")), module
