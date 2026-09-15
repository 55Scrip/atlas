"""The case router's price refresh (lazy trigger and "Uppdatera") resolves
the security's listed siblings when it runs and refreshes them together;
a sibling lookup that fails refreshes the security alone, as before."""
from __future__ import annotations

from atlas.alpha.investment_case.api.router import _refresh_with_listed_siblings
from tests.unit.alpha.business_data_refresh.test_listed_sibling_refresh import _Harness


def _run(h, ticker, resolve):
    return _refresh_with_listed_siblings(ticker, resolve_siblings=resolve, provider=h.provider, repository=h.repository,
                                         quota=h.quota, coordinator=h.coordinator)


def test_the_resolved_siblings_are_refreshed_in_the_same_pass():
    h = _Harness()
    seen = []
    outcome = _run(h, "AAC", lambda ticker, on: seen.append(ticker) or ("AAA",))
    assert (seen, h.requests, outcome.synchronized) == (["AAC"], ["AAC", "AAA"], True)


def test_a_security_without_siblings_is_one_call():
    h = _Harness()
    _run(h, "SGL", lambda ticker, on: ())
    assert h.requests == ["SGL"]


def test_a_failed_sibling_lookup_refreshes_the_security_alone():
    h = _Harness()

    def broken(ticker, on):
        raise RuntimeError("count evidence unreadable")

    outcome = _run(h, "AAA", broken)
    assert (h.requests, outcome.succeeded, outcome.synchronized) == (["AAA"], True, None)
