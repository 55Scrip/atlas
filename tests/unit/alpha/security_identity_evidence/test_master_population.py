"""Planning a security's strong identifiers, and everything it refuses.

The refusals matter more than the successes here. A wrong FIGI is a wrong
company, and the fastest route to one is asking a provider about a bare
ticker: `SU` is Schneider Electric in Paris and Suncor Energy in Canada.
"""
from __future__ import annotations

import pytest

from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiMappingResult,
    OpenFigiMatch,
    OpenFigiProviderUnavailable,
)
from atlas.alpha.security_identity_evidence.master_population import (
    exchange_code_for_mic,
    plan_identity,
)

SCHNEIDER_SHARE_CLASS = "BBG001S67MN2"
SUNCOR_SHARE_CLASS = "BBG001S5YSF0"
MSFT_SHARE_CLASS = "BBG001S5TD05"


def _match(figi, share_class, *, ticker="MSFT", exch="US", name="MICROSOFT CORP", composite=None):
    return OpenFigiMatch(
        figi=figi, ticker=ticker, name=name, exch_code=exch,
        security_type="Common Stock", market_sector="Equity",
        composite_figi=composite, share_class_figi=share_class,
    )


def _lookup(matches):
    def lookup(ticker, exchange_code):
        return OpenFigiMappingResult(matches=matches)

    return lookup


# --- Venue is required -------------------------------------------------


def test_a_security_without_a_venue_is_never_queried() -> None:
    """The whole point. A bare ticker is the question that cannot tell
    Schneider from Suncor, so it is not asked."""
    asked = []

    def lookup(ticker, exchange_code):
        asked.append(ticker)
        raise AssertionError("must not reach the provider")

    plan = plan_identity(ticker="SU", mic=None, lookup=lookup)
    assert plan.eligible is False
    assert plan.share_class_figi is None
    assert "bare ticker" in plan.reason
    assert asked == []


def test_an_unmapped_venue_is_not_guessed() -> None:
    """Stockholm has a MIC, but no verified OpenFIGI code in the table, so
    the security is skipped rather than queried against a guessed venue."""
    plan = plan_identity(ticker="VOLV-B", mic="XSTO", lookup=_lookup(()))
    assert plan.eligible is False
    assert plan.exchange_code is None
    assert "XSTO" in plan.reason


@pytest.mark.parametrize("mic,expected", [("XNAS", "US"), ("XNYS", "US"), ("xnas", "US")])
def test_verified_mics_map_to_their_exchange_code(mic, expected) -> None:
    assert exchange_code_for_mic(mic) == expected


@pytest.mark.parametrize("mic", ["XSTO", "XPAR", "XTAI", "", "ZZZZ", None])
def test_unverified_mics_map_to_nothing(mic) -> None:
    assert exchange_code_for_mic(mic) is None


# --- Interpreting the answer -------------------------------------------


def test_a_single_clean_match_resolves_all_three_figis() -> None:
    plan = plan_identity(
        ticker="MSFT", mic="XNAS",
        lookup=_lookup((_match("BBG000BPH459", MSFT_SHARE_CLASS, composite="BBG000BPH459"),)),
    )
    assert plan.reason == "resolved"
    assert plan.figi == "BBG000BPH459"
    assert plan.composite_figi == "BBG000BPH459"
    assert plan.share_class_figi == MSFT_SHARE_CLASS
    assert plan.provider_name == "MICROSOFT CORP"


def test_an_unrecognised_security_writes_nothing() -> None:
    plan = plan_identity(ticker="ZZZZ", mic="XNAS", lookup=_lookup(()))
    assert plan.eligible is True
    assert plan.share_class_figi is None
    assert "recognised no security" in plan.reason


def test_listings_that_disagree_about_the_share_class_write_nothing() -> None:
    matches = (
        _match("BBG000BBWCH2", SCHNEIDER_SHARE_CLASS, ticker="SU", name="SCHNEIDER ELECTRIC SE"),
        _match("BBG000BC1LY5", SUNCOR_SHARE_CLASS, ticker="SU", name="SUNCOR ENERGY INC"),
    )
    plan = plan_identity(ticker="SU", mic="XNYS", lookup=_lookup(matches))
    assert plan.share_class_figi is None
    assert "did not agree" in plan.reason


def test_a_provider_failure_destroys_nothing() -> None:
    def lookup(ticker, exchange_code):
        raise OpenFigiProviderUnavailable("connection reset")

    plan = plan_identity(ticker="MSFT", mic="XNAS", lookup=lookup)
    assert plan.share_class_figi is None
    assert "provider unavailable" in plan.reason


def test_an_ambiguous_venue_still_yields_the_share_class() -> None:
    """Two venue FIGIs means Atlas cannot say which listing this is, but the
    share class is still unanimous -- so the strong identity is recorded and
    the weaker one is not."""
    matches = (
        _match("BBG000BCH2F1", MSFT_SHARE_CLASS, composite="BBG000BCH216"),
        _match("BBG000BLPJ65", MSFT_SHARE_CLASS, composite="BBG000BLPJ65"),
    )
    plan = plan_identity(ticker="MSFT", mic="XNAS", lookup=_lookup(matches))
    assert plan.share_class_figi == MSFT_SHARE_CLASS
    assert plan.figi is None
    assert plan.composite_figi is None


# --- The collision -----------------------------------------------------


def test_schneider_and_suncor_never_produce_the_same_identity() -> None:
    schneider = plan_identity(
        ticker="SU", mic="XNYS",
        lookup=_lookup((_match("BBG000BBWCH2", SCHNEIDER_SHARE_CLASS, ticker="SU", exch="FP",
                               name="SCHNEIDER ELECTRIC SE"),)),
    )
    suncor = plan_identity(
        ticker="SU", mic="XNYS",
        lookup=_lookup((_match("BBG000BC1LY5", SUNCOR_SHARE_CLASS, ticker="SU", exch="CN",
                               name="SUNCOR ENERGY INC"),)),
    )
    assert schneider.share_class_figi != suncor.share_class_figi
    assert schneider.provider_name == "SCHNEIDER ELECTRIC SE"
    assert suncor.provider_name == "SUNCOR ENERGY INC"


def test_planning_decides_nothing_about_a_company() -> None:
    """A FIGI is a name, not a fact about earnings. Checked against code
    rather than prose -- the module may discuss Cases, it may not touch
    one."""
    import ast
    import inspect

    from atlas.alpha.security_identity_evidence import master_population as module

    tree = ast.parse(inspect.getsource(module))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    names |= {alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names}
    names |= {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    literals = {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in docstrings}
    haystack = " ".join(names) + " " + " ".join(literals)
    for forbidden in ("valuation", "recommendation", "conviction", "free_cash_flow",
                      "investment_case", "snapshot"):
        assert forbidden not in haystack, f"{forbidden} referenced in code"


def test_the_exchange_table_is_a_closed_list_not_a_rule() -> None:
    """A derivation would eventually invent a venue. Only pairs actually
    verified against the provider belong here."""
    import inspect

    from atlas.alpha.security_identity_evidence import master_population as module

    source = inspect.getsource(module)
    for forbidden in (".replace(", ".split(", "startswith(", "endswith("):
        assert forbidden not in source
