"""Alpha Vantage market-data provider (ATLAS-031, Phase 3/9).

The market-data half of the "one provider for fundamentals, one for
market data" split this sprint's Phase 3 explicitly sanctions. Chosen
over Yahoo Finance's unofficial `chart` endpoint (which does still
work without auth, per the live Phase 1 audit) specifically because it
is official and documented, at the cost of requiring the operator's
own free API key and accepting the free tier's 25-calls/day cap --
fine for the explicit, single-company refresh this sprint builds
(Phase 40), not for polling the whole portfolio on a schedule (which
this sprint deliberately does not build either).

Combines two calls -- `GLOBAL_QUOTE` (current price) and `OVERVIEW`
(shares outstanding) -- into exactly **one**
`SourceKind.MARKET_DATA_SNAPSHOT` `RawBusinessDocument` per fetch, so
`atlas.analysis_engine.valuation.facts.extract_valuation_facts`'s own
`document_type is MARKET_DATA_SNAPSHOT` gate (confirmed live in the
Phase 1 audit) picks both facts up together. Per Phase 9: Atlas
derives `market_cap = share_price × shares_outstanding` itself from
these two canonical facts -- this provider never reports (or is asked
to report) a provider-computed market cap number directly.

ATLAS-031B: live testing with a real key found the free tier rejects a
second call made less than ~1 second after the first -- `GLOBAL_QUOTE`
and `OVERVIEW` are spaced by an injectable delay (`_sleeper`, default
`time.sleep`) so production calls are genuinely paced while tests never
actually wait. No retry, no backoff, no queue -- if Alpha Vantage still
rate-limits after the delay, that surfaces through the existing typed
`RateLimited` error exactly as before.

**ATLAS-032: `fetch_historical_snapshots` is a second, optional
capability on this same provider** (see `business_data.providers
.HistoricalMarketDataProvider` for the Protocol and why it is not
folded into `fetch` itself), used to give Valuation genuine historical
market observations to compare a current FCF Yield against. Live
testing this sprint confirmed `TIME_SERIES_MONTHLY_ADJUSTED` is real,
free-tier-available (321 monthly points back to 1999, no premium gate
-- unlike `TIME_SERIES_DAILY?outputsize=full`, which is premium-gated),
and critically **split-adjusted**, confirmed live for NVDA: a 2020 raw
close of $236.43 vs. an adjusted close of $5.8775 for the same date,
reflecting NVDA's two real 10-for-1 splits (2021, 2024). Sampling one
of the *raw* monthly closes against a *current* (post-split) shares-
outstanding count would silently fabricate a wildly wrong historical
market cap; the adjusted series is designed precisely so it can be
compared on a constant, current-share-basis without that distortion,
so it is the only series this method reads.

**A disclosed, honest approximation, not a silently wrong one:**
`shares_outstanding` used for every historical observation is today's
`OVERVIEW` figure, not a genuine historical share count (Alpha
Vantage's free tier reports none). This corrects for the one real
distortion the adjusted-close series exists to prevent (stock splits)
but not for the smaller day-to-day drift of buybacks/issuance between
a historical date and today -- a real, named, and comparatively minor
limitation, not a hidden one.

**No look-ahead, deterministic sampling:** for each caller-supplied
`filing_date`, the sampled observation is the first available monthly
close *on or after* that date -- the earliest point the market could
have reacted to a filing published on or before it, never an earlier
point (which would use a price predating the filing) and never an
arbitrary/nearest one.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import date, datetime
from typing import Any, Callable

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.business_data_providers.errors import (
    CompanyNotFound,
    MalformedProviderResponse,
    MissingRequiredField,
    RateLimited,
    UnsupportedUnit,
)
from atlas.business_data_providers.http import JsonFetcher, fetch_json

__all__ = ["AlphaVantageMarketDataProvider"]

_BASE_URL = "https://www.alphavantage.co/query"
_SUPPORTED_CURRENCY = "USD"

#: Alpha Vantage's free tier rejects a second call made less than
#: ~1 second after the first -- confirmed by live testing with a real
#: key. A small safety margin above the observed limit, not a tuned or
#: documented constant from Alpha Vantage itself.
_DEFAULT_INTER_REQUEST_DELAY_SECONDS = 1.1

Sleeper = Callable[[float], None]


def _api_key(explicit: str | None) -> str | None:
    return explicit if explicit is not None else os.environ.get("ALPHA_VANTAGE_API_KEY")


def _check_for_provider_error(payload: Any, *, context: str) -> None:
    """Alpha Vantage returns HTTP 200 for its own error states -- a
    rate-limited/quota-exhausted call and an unrecognized symbol are
    both still a 200 with a differently-shaped JSON body, never a 4xx.
    This is the one place that shape is translated into this package's
    typed errors instead of being read as if it were real data."""
    if not isinstance(payload, dict):
        raise MalformedProviderResponse(f"{context}: response was not a JSON object")
    if "Error Message" in payload:
        raise CompanyNotFound(f"{context}: {payload['Error Message']}")
    if "Note" in payload or "Information" in payload:
        raise RateLimited(f"{context}: {payload.get('Note') or payload.get('Information')}")


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _confirmed_currency_metadata(
    currency: Any, *, share_price: float, shares_outstanding: float | None
) -> dict[str, Any]:
    """The one currency-safety rule (ATLAS-031A, Issue 1), factored out
    so `fetch` and `fetch_historical_snapshots` apply the identical
    check rather than risking two copies drifting apart. `currency`
    must be positively confirmed as `_SUPPORTED_CURRENCY` -- an
    unconfirmed value returns an empty dict (the price is omitted
    entirely, never guessed under a default currency); an explicit
    non-USD value still raises `UnsupportedUnit`."""
    currency_confirmed = isinstance(currency, str) and currency.strip() != ""
    if not currency_confirmed:
        return {}
    if currency != _SUPPORTED_CURRENCY:
        raise UnsupportedUnit(
            f"Alpha Vantage reports currency {currency!r}; this provider's v1 only supports {_SUPPORTED_CURRENCY}"
        )
    metadata: dict[str, Any] = {"share_price": share_price, "currency": currency}
    if shares_outstanding is not None:
        metadata["shares_outstanding"] = shares_outstanding
    return metadata


def _first_on_or_after(sorted_dates: list[date], target: date) -> date | None:
    """The deterministic, no-look-ahead sampling rule (ATLAS-032): the
    first available date >= `target`, or `None` if `target` is later
    than every available date -- never the nearest date, and never one
    before `target` (which would use a price predating the filing it
    is meant to represent)."""
    for candidate in sorted_dates:
        if candidate >= target:
            return candidate
    return None


class AlphaVantageMarketDataProvider:
    """One `RawBusinessDocument` per fetch, tagged
    `SourceKind.MARKET_DATA_SNAPSHOT`, carrying whichever of
    `share_price`/`shares_outstanding` were actually available --
    Phase 9 does not require failing the whole fetch just because one
    side (typically shares outstanding, from the separate `OVERVIEW`
    call) is momentarily unavailable; the downstream Valuation
    evaluator already reports an honest `INSUFFICIENT_INPUT` for a
    period missing a fact it needs, which is the correct place for
    that gap to surface, not an exception here.

    Missing `ALPHA_VANTAGE_API_KEY` raises `MissingRequiredField`
    immediately on `fetch` -- Phase 31's "fail clearly when missing,"
    never a silent empty result.
    """

    def __init__(
        self,
        fetch_json_fn: JsonFetcher | None = None,
        *,
        api_key: str | None = None,
        sleeper: Sleeper | None = None,
        inter_request_delay_seconds: float = _DEFAULT_INTER_REQUEST_DELAY_SECONDS,
    ) -> None:
        self._fetch_json = fetch_json_fn or fetch_json
        self._explicit_api_key = api_key
        # `sleeper` defaults to `None`, resolved to `time.sleep` fresh at
        # call time (never bound as a mutable default) so a test-suite
        # -wide `monkeypatch.setattr(time, "sleep", ...)` silences every
        # existing call site without editing each one individually --
        # only tests asserting the delay's own call order/count inject
        # an explicit fake here.
        self._sleeper = sleeper
        self._inter_request_delay_seconds = inter_request_delay_seconds

    def _resolved_api_key(self) -> str:
        key = _api_key(self._explicit_api_key)
        if not key:
            raise MissingRequiredField(
                "ALPHA_VANTAGE_API_KEY is not set. Register a free key at "
                "https://www.alphavantage.co/support/#api-key and set it in the environment, "
                "or pass api_key= explicitly."
            )
        return key

    def _global_quote(self, ticker: str, api_key: str) -> dict[str, Any]:
        url = f"{_BASE_URL}?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}"
        payload = self._fetch_json(url, None)
        _check_for_provider_error(payload, context=f"Alpha Vantage GLOBAL_QUOTE({ticker})")
        quote = payload.get("Global Quote") if isinstance(payload, dict) else None
        if not quote:
            raise CompanyNotFound(f"Alpha Vantage GLOBAL_QUOTE has no data for {ticker!r}")
        return quote

    def _overview(self, ticker: str, api_key: str) -> dict[str, Any]:
        url = f"{_BASE_URL}?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
        payload = self._fetch_json(url, None)
        _check_for_provider_error(payload, context=f"Alpha Vantage OVERVIEW({ticker})")
        return payload if isinstance(payload, dict) else {}

    def _monthly_adjusted(self, ticker: str, api_key: str) -> dict[str, Any]:
        url = f"{_BASE_URL}?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}&apikey={api_key}"
        payload = self._fetch_json(url, None)
        _check_for_provider_error(payload, context=f"Alpha Vantage TIME_SERIES_MONTHLY_ADJUSTED({ticker})")
        series = payload.get("Monthly Adjusted Time Series") if isinstance(payload, dict) else None
        if not isinstance(series, dict):
            raise MalformedProviderResponse(
                f"Alpha Vantage TIME_SERIES_MONTHLY_ADJUSTED({ticker}) missing its time series"
            )
        return series

    def _sleep(self) -> None:
        # ATLAS-031B: the free tier rejects a second call made too soon
        # after the first -- resolved fresh here (not a bound default)
        # so tests can patch `time.sleep` globally instead of injecting
        # a fake into every construction.
        sleeper = self._sleeper if self._sleeper is not None else time.sleep
        sleeper(self._inter_request_delay_seconds)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        api_key = self._resolved_api_key()
        ticker = company_identifier.upper()

        quote = self._global_quote(ticker, api_key)
        share_price = _numeric(quote.get("05. price"))
        trading_day = quote.get("07. latest trading day")
        if share_price is None or not trading_day:
            raise MalformedProviderResponse(f"Alpha Vantage GLOBAL_QUOTE({ticker}) missing price/trading day")
        try:
            snapshot_date = date.fromisoformat(trading_day)
        except ValueError:
            raise MalformedProviderResponse(
                f"Alpha Vantage GLOBAL_QUOTE({ticker}) latest trading day {trading_day!r} is not ISO-8601"
            ) from None

        self._sleep()  # pace GLOBAL_QUOTE -> OVERVIEW

        overview = self._overview(ticker, api_key)
        shares_outstanding = _numeric(overview.get("SharesOutstanding"))
        currency = overview.get("Currency")
        # ATLAS-031A, Issue 1: currency must be positively confirmed --
        # never assumed. An unconfirmed currency (OVERVIEW empty or
        # missing the field) omits share_price/shares_outstanding/
        # currency entirely rather than reporting a price under a
        # guessed denomination. This produces explicit missing data --
        # the document is still constructed and ingested, but
        # extract_valuation_facts finds no share_price to extract, so
        # FCF Yield honestly reports INSUFFICIENT_INPUT rather than
        # computing a meaningless yield.
        metadata = _confirmed_currency_metadata(
            currency, share_price=share_price, shares_outstanding=shares_outstanding
        )

        content_hash = hashlib.sha256(
            json.dumps({"date": trading_day, **metadata}, sort_keys=True).encode("utf-8")
        ).hexdigest()

        document = RawBusinessDocument(
            identifier=f"{ticker}:snapshot:{trading_day}",
            company=ticker,
            source_kind=SourceKind.MARKET_DATA_SNAPSHOT.value,
            published_at=evaluated_at,
            provider_id="alpha_vantage",
            raw_reference=f"{_BASE_URL}?function=GLOBAL_QUOTE&symbol={ticker}",
            content_hash=content_hash,
            period_start=snapshot_date,
            period_end=snapshot_date,
            language="en",
            metadata=metadata,
        )
        return (document,)

    def fetch_historical_snapshots(
        self, *, company_identifier: str, filing_dates: tuple[date, ...], evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        """(ATLAS-032) See this module's own docstring for why the
        split-adjusted monthly series is the only correct source here,
        and why `shares_outstanding` is today's figure, disclosed as an
        approximation, not a genuine historical count.

        One document per *distinct sampled date* -- several
        `filing_dates` landing on the same "first available close on
        or after" observation collapse into a single document, never
        duplicated. `filing_dates` with no eligible future observation
        at all (later than every available monthly close) are silently
        skipped, not fabricated forward.
        """
        if not filing_dates:
            return ()

        api_key = self._resolved_api_key()
        ticker = company_identifier.upper()

        overview = self._overview(ticker, api_key)
        shares_outstanding = _numeric(overview.get("SharesOutstanding"))
        currency = overview.get("Currency")

        self._sleep()  # pace OVERVIEW -> TIME_SERIES_MONTHLY_ADJUSTED

        series = self._monthly_adjusted(ticker, api_key)
        available_dates = sorted(d for d in (self._parse_series_date(key) for key in series) if d is not None)

        sampled_dates: set[date] = set()
        for filing_date in filing_dates:
            sampled = _first_on_or_after(available_dates, filing_date)
            if sampled is not None:
                sampled_dates.add(sampled)

        documents: list[RawBusinessDocument] = []
        for sampled_date in sorted(sampled_dates):
            bar = series[sampled_date.isoformat()]
            adjusted_close = _numeric(bar.get("5. adjusted close"))
            if adjusted_close is None:
                continue
            metadata = _confirmed_currency_metadata(
                currency, share_price=adjusted_close, shares_outstanding=shares_outstanding
            )
            content_hash = hashlib.sha256(
                json.dumps({"date": sampled_date.isoformat(), **metadata}, sort_keys=True).encode("utf-8")
            ).hexdigest()
            documents.append(
                RawBusinessDocument(
                    identifier=f"{ticker}:historical_snapshot:{sampled_date.isoformat()}",
                    company=ticker,
                    source_kind=SourceKind.MARKET_DATA_SNAPSHOT.value,
                    # The historical close was genuinely public on the
                    # trading day itself -- unlike `evaluated_at` (used
                    # for the *current* snapshot, when Atlas actually
                    # fetched it), this reflects the real-world
                    # publication date of a historical value.
                    published_at=datetime.combine(sampled_date, datetime.min.time(), tzinfo=evaluated_at.tzinfo),
                    provider_id="alpha_vantage",
                    raw_reference=f"{_BASE_URL}?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}",
                    content_hash=content_hash,
                    period_start=sampled_date,
                    period_end=sampled_date,
                    language="en",
                    metadata=metadata,
                )
            )
        return tuple(documents)

    @staticmethod
    def _parse_series_date(key: str) -> date | None:
        try:
            return date.fromisoformat(key)
        except ValueError:
            return None
