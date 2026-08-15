"""Sprint 19 -- discover_security_candidates, exercised against
Sprint 19's own Primary Test Cases A-F. Fixture entries are copied
verbatim (ticker/cik/title) from SEC's real company_tickers.json, fetched
live during this sprint's investigation -- not invented data.
"""
from __future__ import annotations

import pytest

from atlas.alpha.security_discovery.models import SecTickerEntry
from atlas.alpha.security_discovery.service import (
    build_ticker_index,
    build_title_index,
    discover_security_candidates,
)

_REAL_SEC_FIXTURE = (
    SecTickerEntry(cik=1045810, ticker="NVDA", title="NVIDIA CORP"),
    SecTickerEntry(cik=1067983, ticker="BRK-A", title="BERKSHIRE HATHAWAY INC"),
    SecTickerEntry(cik=1067983, ticker="BRK-B", title="BERKSHIRE HATHAWAY INC"),
    SecTickerEntry(cik=1652044, ticker="GOOGL", title="Alphabet Inc."),
    SecTickerEntry(cik=1652044, ticker="GOOG", title="Alphabet Inc."),
    SecTickerEntry(cik=320193, ticker="AAPL", title="Apple Inc."),
    SecTickerEntry(cik=789019, ticker="MSFT", title="MICROSOFT CORP"),
    SecTickerEntry(cik=1326801, ticker="META", title="Meta Platforms, Inc."),
    SecTickerEntry(cik=1318605, ticker="TSLA", title="Tesla, Inc."),
    SecTickerEntry(cik=2488, ticker="AMD", title="ADVANCED MICRO DEVICES INC"),
    SecTickerEntry(cik=937966, ticker="ASML", title="ASML HOLDING NV"),
)


@pytest.fixture
def title_index():
    return build_title_index(_REAL_SEC_FIXTURE)


@pytest.fixture
def ticker_index():
    return build_ticker_index(_REAL_SEC_FIXTURE)


def _discover(query: str, title_index, ticker_index):
    return discover_security_candidates(query, title_index=title_index, ticker_index=ticker_index)


class TestCaseA_StraightforwardCompanyName:
    def test_nvidia_resolves_to_single_nvda_candidate(self, title_index, ticker_index):
        candidates = _discover("NVIDIA", title_index, ticker_index)
        assert len(candidates) == 1
        assert candidates[0].ticker == "NVDA"
        assert candidates[0].status == "candidate_only"
        assert candidates[0].discovery_method == "title_canonical"


class TestCaseB_AmbiguousShareClasses:
    def test_berkshire_hathaway_returns_both_share_classes_unranked(self, title_index, ticker_index):
        candidates = _discover("Berkshire Hathaway", title_index, ticker_index)
        tickers = {c.ticker for c in candidates}
        assert tickers == {"BRK-A", "BRK-B"}
        assert all(c.status == "candidate_only" for c in candidates)


class TestCaseC_AnotherMultiClassCompany:
    def test_alphabet_returns_both_share_classes_unranked(self, title_index, ticker_index):
        candidates = _discover("Alphabet", title_index, ticker_index)
        tickers = {c.ticker for c in candidates}
        assert tickers == {"GOOG", "GOOGL"}


class TestCaseD_AlreadyATicker:
    def test_nvda_ticker_input_short_circuits_to_ticker_exact(self, title_index, ticker_index):
        candidates = _discover("NVDA", title_index, ticker_index)
        assert len(candidates) == 1
        assert candidates[0].discovery_method == "ticker_exact"
        assert candidates[0].ticker == "NVDA"

    def test_ticker_lookup_is_case_insensitive(self, title_index, ticker_index):
        candidates = _discover("nvda", title_index, ticker_index)
        assert len(candidates) == 1
        assert candidates[0].discovery_method == "ticker_exact"


class TestCaseE_NoResult:
    def test_unknown_company_returns_no_fabricated_candidate(self, title_index, ticker_index):
        candidates = _discover("Completely Unknown Company XYZ", title_index, ticker_index)
        assert candidates == ()

    def test_empty_query_returns_no_candidates(self, title_index, ticker_index):
        assert _discover("", title_index, ticker_index) == ()
        assert _discover("   ", title_index, ticker_index) == ()


class TestCaseF_NoisyPartialWording:
    def test_nvidia_corp_resolves(self, title_index, ticker_index):
        candidates = _discover("Nvidia Corp", title_index, ticker_index)
        assert {c.ticker for c in candidates} == {"NVDA"}

    def test_nvidia_corporation_resolves(self, title_index, ticker_index):
        candidates = _discover("NVIDIA Corporation", title_index, ticker_index)
        assert {c.ticker for c in candidates} == {"NVDA"}

    def test_bare_meta_resolves_only_because_it_is_also_a_real_ticker(self, title_index, ticker_index):
        """'META' happens to be Meta Platforms' own ticker symbol, so
        this resolves via the ticker-exact path (Case D), not by
        fuzzy-bridging the company name to the fuller legal title --
        confirmed by `discovery_method`. See canonicalize.py's own
        TestDoesNotOverReach for proof that the *title* canonical form
        of 'Meta' alone genuinely differs from 'Meta Platforms, Inc.'"""
        candidates = _discover("Meta", title_index, ticker_index)
        assert len(candidates) == 1
        assert candidates[0].discovery_method == "ticker_exact"

    def test_meta_platforms_resolves(self, title_index, ticker_index):
        candidates = _discover("Meta Platforms", title_index, ticker_index)
        assert {c.ticker for c in candidates} == {"META"}


class TestFalseMergeProtection:
    def test_apple_never_returns_microsoft(self, title_index, ticker_index):
        candidates = _discover("Apple", title_index, ticker_index)
        assert {c.ticker for c in candidates} == {"AAPL"}

    def test_brk_a_and_brk_b_never_collapse_to_one_candidate(self, title_index, ticker_index):
        candidates = _discover("Berkshire Hathaway", title_index, ticker_index)
        assert len(candidates) == 2

    def test_goog_and_googl_never_collapse_to_one_candidate(self, title_index, ticker_index):
        candidates = _discover("Alphabet", title_index, ticker_index)
        assert len(candidates) == 2


class TestEveryCandidateIsUnconfirmed:
    def test_status_is_always_candidate_only(self, title_index, ticker_index):
        for query in ("NVIDIA", "Berkshire Hathaway", "NVDA", "Alphabet"):
            for candidate in _discover(query, title_index, ticker_index):
                assert candidate.status == "candidate_only"


class TestDeterminism:
    def test_repeated_calls_return_identical_results(self, title_index, ticker_index):
        first = _discover("Alphabet", title_index, ticker_index)
        second = _discover("Alphabet", title_index, ticker_index)
        assert first == second
