"""Importing a portfolio must not depend on SEC being reachable.

Sprint 69 drove the real UI and found that `POST /alpha-portfolio/import/preview`
returned a bare 500 whenever `www.sec.gov` was unreachable: the SEC
company-ticker index was fetched eagerly as a FastAPI dependency of the
endpoint, `_fetch_json` let `httpx.ConnectError` escape, and the screen offered
"try again" as the only remedy -- which could not succeed. The index is
process-local with no disk cache, so every backend restart re-exposed it.

Two things are asserted here, and they are different:

* the index itself answers "no entries" instead of raising, so a row that
  genuinely needs name->ticker discovery degrades rather than crashing;
* a row that already carries a ticker never asks for the index at all, which
  is the common case a broker export produces and the reason the dependency
  was wrong to be eager.

Neither may buy resilience with a weaker identity: nothing below is allowed to
invent a `canonicalSecurityId` or fall back to a ticker for one.
"""
from __future__ import annotations

import httpx
import pytest

from atlas.alpha.portfolio_import.models import ColumnRole, RowResolutionStatus
from atlas.alpha.portfolio_import.resolution_service import resolve_row
from atlas.alpha.portfolio_import.row_parser import parse_input
from atlas.alpha.portfolio_import.service import PortfolioImportPreviewService
from atlas.alpha.security_discovery.sec_source import SecTitleIndexSource

_SWEDISH_EXPORT = (
    "Namn;Ticker;ISIN;Marknad;Antal;Kurs;Valuta\n"
    "Volvo AB ser. B;VOLV-B;SE0000115446;Nasdaq Stockholm;100;280,50;SEK\n"
    "Microsoft Corp;MSFT;US5949181045;NASDAQ;10;420,00;SEK\n"
)

_SEC_PAYLOAD = {
    "0": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
    "1": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
}


class CountingFetcher:
    """Counts, because "the import did not reach SEC" is a claim that has to
    be measurable rather than asserted in prose."""

    def __init__(self, payload=None, raises: Exception | None = None) -> None:
        self.payload = payload if payload is not None else dict(_SEC_PAYLOAD)
        self.raises = raises
        self.calls: list[str] = []

    def __call__(self, url, headers=None):
        self.calls.append(url)
        if self.raises is not None:
            raise self.raises
        return self.payload


class TestTheIndexDegradesInsteadOfRaising:
    def test_a_reachable_sec_returns_its_entries(self):
        fetcher = CountingFetcher()

        entries = SecTitleIndexSource(fetcher).entries()

        assert {e.ticker for e in entries} == {"MSFT", "AAPL"}
        assert len(fetcher.calls) == 1

    @pytest.mark.parametrize(
        "failure",
        [
            httpx.ConnectError("sec unreachable"),
            httpx.ReadTimeout("sec timed out"),
            httpx.HTTPStatusError(
                "403", request=httpx.Request("GET", "https://sec.gov"),
                response=httpx.Response(403),
            ),
            ValueError("not json at all"),
        ],
        ids=["unreachable", "timeout", "http-error-status", "malformed-body"],
    )
    def test_every_failure_shape_yields_no_entries(self, failure):
        """A transport failure, a timeout, a rate-limit status and a body that
        is not JSON all mean the same thing to a caller."""
        assert SecTitleIndexSource(CountingFetcher(raises=failure)).entries() == ()

    def test_a_malformed_but_parseable_payload_yields_no_entries(self):
        assert SecTitleIndexSource(CountingFetcher(payload=["not", "a", "dict"])).entries() == ()

    def test_a_failure_is_not_cached_so_recovery_needs_no_restart(self):
        """Caching the failure would make one unlucky request poison every
        later one for the lifetime of the process."""
        source = SecTitleIndexSource(CountingFetcher(raises=httpx.ConnectError("down")))
        assert source.entries() == ()

        source._fetch_json = CountingFetcher()  # SEC comes back
        assert {e.ticker for e in source.entries()} == {"MSFT", "AAPL"}

    def test_a_success_is_still_cached(self):
        fetcher = CountingFetcher()
        source = SecTitleIndexSource(fetcher)

        source.entries()
        source.entries()

        assert len(fetcher.calls) == 1


class TestDiscoveryIsOnlyAskedForWhenNeeded:
    """`resolve_row` reaches `discover` only through its `elif company_name`
    branch, after the local registry and the learned-alias step. These tests
    pin that, because it is what makes the eager dependency unnecessary."""

    def _rows(self, text):
        return parse_input(text).rows

    def test_a_row_with_a_ticker_never_calls_discovery(self):
        calls = []

        def discover(query):
            calls.append(query)
            raise AssertionError("a row that already has a ticker must not need SEC")

        for row in self._rows(_SWEDISH_EXPORT):
            resolve_row(row, discover=discover)

        assert calls == []

    def test_a_row_without_a_ticker_does_call_discovery(self):
        calls = []
        rows = self._rows("Namn;Antal;Kurs\nEtt Helt Okant Bolag AB;10;5,00\n")

        resolve_row(rows[0], discover=lambda q: calls.append(q) or ())

        assert calls, "a name-only row is exactly the case discovery exists for"

    def test_the_whole_preview_of_a_ticker_bearing_export_never_calls_discovery(self):
        calls = []

        def discover(query):
            calls.append(query)
            return ()

        preview = PortfolioImportPreviewService().preview(_SWEDISH_EXPORT, discover=discover)

        assert calls == []
        assert [r.ticker for r in preview.rows] == ["VOLV-B", "MSFT"]
        assert all(r.status is RowResolutionStatus.RESOLVED for r in preview.rows)


class TestPreviewSurvivesAnUnavailableSec:
    def _preview(self, text, *, discover):
        return PortfolioImportPreviewService().preview(text, discover=discover)

    def _dead_discovery(self):
        source = SecTitleIndexSource(CountingFetcher(raises=httpx.ConnectError("sec down")))

        def discover(query):
            from atlas.alpha.security_discovery.service import (
                build_ticker_index,
                build_title_index,
                discover_security_candidates,
            )

            entries = source.entries()
            return discover_security_candidates(
                query, title_index=build_title_index(entries),
                ticker_index=build_ticker_index(entries),
            )

        return discover

    def test_ticker_and_isin_rows_import_fine_with_sec_down(self):
        preview = self._preview(_SWEDISH_EXPORT, discover=self._dead_discovery())

        assert [r.ticker for r in preview.rows] == ["VOLV-B", "MSFT"]
        assert [r.isin for r in preview.rows] == ["SE0000115446", "US5949181045"]
        assert preview.holdings_found == 2

    def test_a_ticker_without_an_isin_still_imports_with_sec_down(self):
        preview = self._preview(
            "Namn;Ticker;Antal;Kurs\nMicrosoft Corp;MSFT;10;420,00\n",
            discover=self._dead_discovery(),
        )

        assert preview.rows[0].ticker == "MSFT"
        assert preview.rows[0].isin is None
        assert preview.rows[0].canonical_security_id is None

    def test_a_row_without_a_ticker_degrades_rather_than_crashing(self):
        preview = self._preview(
            "Namn;Antal;Kurs\nEtt Helt Okant Bolag AB;10;5,00\n",
            discover=self._dead_discovery(),
        )

        assert preview.rows[0].ticker is None
        assert preview.rows[0].status is not RowResolutionStatus.RESOLVED
        assert preview.rows[0].canonical_security_id is None

    def test_a_mixed_export_resolves_what_it_can_and_withholds_the_rest(self):
        preview = self._preview(
            "Namn;Ticker;ISIN;Antal;Kurs\n"
            "Volvo AB ser. B;VOLV-B;SE0000115446;100;280,50\n"
            "Microsoft Corp;MSFT;;10;420,00\n"
            "Ett Helt Okant Bolag AB;;;5;10,00\n",
            discover=self._dead_discovery(),
        )

        by_ticker = {r.ticker: r for r in preview.rows}
        assert by_ticker["VOLV-B"].isin == "SE0000115446"
        assert by_ticker["MSFT"].isin is None
        assert None in by_ticker, "the unnamed row is present, not dropped"
        assert all(r.canonical_security_id is None for r in preview.rows)

    def test_the_pasted_data_is_preserved_on_every_row(self):
        """Requirement 8: whatever the user pasted comes back, so the review
        screen can show it rather than losing their input."""
        preview = self._preview(_SWEDISH_EXPORT, discover=self._dead_discovery())

        raws = [r.raw for r in preview.rows]
        assert "Volvo AB ser. B;VOLV-B;SE0000115446;Nasdaq Stockholm;100;280,50;SEK" in raws
        assert "Microsoft Corp;MSFT;US5949181045;NASDAQ;10;420,00;SEK" in raws


class TestResilienceBuysNoWeakerIdentity:
    def test_an_unavailable_provider_withholds_identity_rather_than_guessing(self):
        """Requirements 4/5/6. With no identity resolver reachable, a row keeps
        its own ISIN and names no security -- it never borrows one from a
        ticker and never invents an id."""
        from atlas.alpha.canonical_security_gate.import_resolution import (
            ImportIdentityStatus,
        )

        def resolver(**kwargs):
            class _Unavailable:
                status = ImportIdentityStatus.PROVIDER_UNAVAILABLE
                reason = "identity provider unavailable"
                security = None
                strong_identifier_used = None
                exchange_mic = None

            return _Unavailable()

        preview = PortfolioImportPreviewService().preview(
            _SWEDISH_EXPORT, resolve_identity=resolver
        )

        for row in preview.rows:
            assert row.identity_status == "PROVIDER_UNAVAILABLE"
            assert row.canonical_security_id is None
            assert row.security_name is None
            assert row.isin is not None, "the file's own identifier is still kept"

    def test_no_resolver_at_all_leaves_identity_unasked_not_assumed(self):
        preview = PortfolioImportPreviewService().preview(_SWEDISH_EXPORT)

        for row in preview.rows:
            assert row.identity_status is None
            assert row.canonical_security_id is None


class _FakeRequest:
    """Just enough of `Request` for `get_security_discovery_fn`: the override
    map it consults. Supplying a real one would mean standing up an app,
    which would test FastAPI rather than this wiring."""

    def __init__(self, overrides: dict) -> None:
        self.app = type("_App", (), {"dependency_overrides": overrides})()


class TestDiscoveryCostIsBoundedPerRequest:
    """The index is memoised inside the callable `get_security_discovery_fn`
    returns. On the happy path `SecTitleIndexSource` already caches
    process-wide so this is invisible; it matters during an outage, because a
    failed fetch is deliberately not cached and `resolve_row` can consult
    `discover` more than once for one unnamed row."""

    def _discover_with(self, provider):
        import atlas.alpha.portfolio_import.api.dependencies as deps
        from atlas.alpha.security_discovery.api.dependencies import (
            get_security_discovery_indexes,
        )

        request = _FakeRequest({get_security_discovery_indexes: provider})
        return deps.get_security_discovery_fn(request)

    def test_many_name_only_rows_build_the_index_once(self):
        builds: list[int] = []

        def counting_indexes():
            builds.append(1)
            return ({}, {})

        preview = PortfolioImportPreviewService().preview(
            "Namn;Antal;Kurs\n"
            "Ett Helt Okant Bolag AB;10;5,00\n"
            "Ett Annat Okant Bolag AB;5;3,00\n"
            "Tredje Okanda AB;1;1,00\n",
            discover=self._discover_with(counting_indexes),
        )

        assert len(preview.rows) == 3
        assert len(builds) == 1, f"index built {len(builds)} times for one request"

    def test_a_ticker_bearing_request_never_builds_the_index(self):
        def exploding_indexes():
            raise AssertionError("a ticker-bearing export must not build the SEC index")

        preview = PortfolioImportPreviewService().preview(
            _SWEDISH_EXPORT, discover=self._discover_with(exploding_indexes)
        )

        assert [r.ticker for r in preview.rows] == ["VOLV-B", "MSFT"]

    def test_a_dependency_override_is_honoured_rather_than_silently_ignored(self):
        """Dropping the `Depends` must not drop the override seam: the
        endpoint's own tests swap the real SEC source through
        `dependency_overrides`, and an override that is visibly set but
        inert is worse than no override at all."""
        from atlas.alpha.security_discovery.service import (
            build_ticker_index,
            build_title_index,
        )
        from atlas.alpha.security_discovery.sec_source import SecTickerEntry

        entries = (SecTickerEntry(cik=789019, ticker="MSFT", title="MICROSOFT CORP"),)
        overridden = lambda: (build_title_index(entries), build_ticker_index(entries))

        preview = PortfolioImportPreviewService().preview(
            "Namn;Antal;Kurs\nMICROSOFT CORP;10;5,00\n",
            discover=self._discover_with(overridden),
        )

        assert preview.rows[0].ticker == "MSFT", "the overridden index was not used"
