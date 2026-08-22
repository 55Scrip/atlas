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
second call made less than ~1 second after the first -- every outbound
call is spaced by an injectable delay (`_sleeper`, default
`time.sleep`) so production calls are genuinely paced while tests never
actually wait. No retry, no backoff, no queue -- if Alpha Vantage still
rate-limits after the delay, that surfaces through the existing typed
`RateLimited` error exactly as before.

**ATLAS-032 corrective: pacing is enforced at the provider-instance
level, not hand-placed between specific call pairs.** A real refresh
calls `fetch()` (2 requests) and then, moments later,
`fetch_historical_snapshots()` (2 more requests) on the *same*
provider instance -- confirmed live to violate the 1-request/second
limit, because each method only paced its own internal calls and
neither knew the other had just run. Every outbound call now funnels
through `_request_json`, which calls `_pace()` first: `_pace()` tracks
`self._last_request_at` (a monotonic timestamp) across every call this
instance has ever made, of either public method, and sleeps only the
*remaining* interval if less than `_inter_request_delay_seconds` has
elapsed since the last one -- never a flat delay, and never before the
very first request on a freshly constructed instance.

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

**ATLAS-033: the current OVERVIEW figures are fetched at most once per
ticker per instance.** `fetch()` and `fetch_historical_snapshots()`
both need the same two current-basis values -- `SharesOutstanding` and
`Currency` -- and were originally each written to independently call
`OVERVIEW` for them, wasting one full request whenever both methods
run in the same refresh. `_current_overview` now retains those
already-parsed values (never the raw payload, no expiration, no
general response cache) keyed by ticker; whichever method runs first
populates it, the other reuses it. Calling either method alone, or for
a different ticker, still makes its own real `OVERVIEW` request exactly
as before.

**Investment Case Engine v1 slice: `fetch_company_profile` reuses the
identical cached OVERVIEW call -- no third request.** `OVERVIEW`
already returns descriptive identity fields (`Name`, `Exchange`,
`Sector`, `Industry`, `Country`, `Description`) alongside
`SharesOutstanding`/`Currency`; this provider previously parsed only
the latter two and discarded the rest. `_current_overview` now also
retains those identity fields from the same response, and
`fetch_company_profile` (the optional `CompanyProfileProvider`
capability) reads them from that same cache -- whichever of `fetch`,
`fetch_historical_snapshots`, or `fetch_company_profile` runs first for
a ticker is the one real `OVERVIEW` request; the other two reuse it.

**Sprint O.1: `AssetType` is now extracted too.** OVERVIEW's response
already carries this field (documented values: typically `"Common
Stock"`, sometimes `"Preferred Stock"`/`"ETF"`/etc.) alongside the
fields above -- this provider previously discarded it, which is the one
reason a real Alpha Vantage candidate could never reach the Canonical
Security Identity Gate's `HIGH`-confidence tier alone (see Sprint O's
own readiness assessment). This still only *extracts* the raw display
string into `metadata["asset_type"]`, unchanged and untranslated;
turning it into Atlas' closed `SecurityType` vocabulary is
`canonical_security_gate.candidate_mapping`'s job, not this provider's
-- this file still has no `atlas.alpha.canonical_security*` import of
any kind.
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

#: Investment Case Engine v1 slice -- canonical `business_facts`/
#: `CompanyProfile` metadata key -> the OVERVIEW field it comes from.
#: Alpha Vantage reports the literal string `"None"` for a field it does
#: not have for a given ticker (confirmed shape of the real API, not
#: assumed) -- `_identity_fields` below treats that exactly like a
#: blank/missing value, never as real content, so a genuinely unknown
#: field is omitted rather than persisted as the four-character string
#: "None".
#:
#: Company Data Foundation v1: `Currency`/`FiscalYearEnd` added --
#: both already present in this same, already-fetched OVERVIEW
#: response (no new request). Deliberately NOT added here: OVERVIEW's
#: own provider-computed ratios (`PERatio`, `PEGRatio`, `EBITDA`,
#: `ProfitMargin`, `OperatingMarginTTM`, `ReturnOnEquityTTM`, etc.) --
#: SEC EDGAR now supplies the raw fundamentals (`net_income`,
#: `operating_income`, `eps`) Atlas can derive an equivalent ratio from
#: itself, deterministically and traceably, per this sprint's own
#: "prefer fundamental raw inputs over provider-computed ratios"
#: instruction; ingesting Alpha Vantage's own pre-computed versions
#: alongside would be a second, silently-competing source for the same
#: number rather than a genuinely new fact.
_IDENTITY_FIELD_MAP: dict[str, str] = {
    "Name": "name",
    "AssetType": "asset_type",
    "Exchange": "exchange",
    "Sector": "sector",
    "Industry": "industry",
    "Country": "country",
    "Description": "description",
    "Currency": "currency",
    "FiscalYearEnd": "fiscal_year_end",
}


def _identity_fields(overview: dict[str, Any]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for source_key, metadata_key in _IDENTITY_FIELD_MAP.items():
        value = overview.get(source_key)
        if isinstance(value, str) and value.strip() and value.strip().lower() != "none":
            fields[metadata_key] = value.strip()
    return fields

#: Alpha Vantage's free tier rejects a second call made less than
#: ~1 second after the first -- confirmed by live testing with a real
#: key. A small safety margin above the observed limit, not a tuned or
#: documented constant from Alpha Vantage itself.
_DEFAULT_INTER_REQUEST_DELAY_SECONDS = 1.1

#: Quarter-end (month, day) per Alpha Vantage's own `"YYYYQN"` quarter
#: format -- lets `_quarter_end_date` derive a real calendar date from a
#: quarter string alone, with no extra API field.
_QUARTER_END_MONTH_DAY: dict[int, tuple[int, int]] = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}

Sleeper = Callable[[float], None]
Clock = Callable[[], float]


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


def _most_recent_completed_quarter(evaluated_at: datetime) -> str:
    """The most recently *ended* calendar quarter as of `evaluated_at`
    -- no invented reporting-lag heuristic (real lag varies by company
    and Atlas has no owned constant for it). If that quarter's own
    transcript is not yet published, Alpha Vantage's own response says
    so (an empty `transcript` array) and `fetch_earnings_call_transcripts`
    honestly returns `()`, exactly like `fetch_company_profile` does
    when OVERVIEW carries no identity fields."""
    quarter_of_month = (evaluated_at.month - 1) // 3 + 1
    if quarter_of_month == 1:
        return f"{evaluated_at.year - 1}Q4"
    return f"{evaluated_at.year}Q{quarter_of_month - 1}"


def _quarter_end_date(quarter: str) -> date | None:
    try:
        year = int(quarter[:4])
        q = int(quarter[5])
    except (ValueError, IndexError):
        return None
    month_day = _QUARTER_END_MONTH_DAY.get(q)
    if month_day is None:
        return None
    return date(year, *month_day)


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
        clock: Clock | None = None,
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
        # ATLAS-032 corrective: `clock` follows the identical "resolved
        # fresh at call time, never a bound default" discipline as
        # `sleeper` -- defaults to `time.monotonic`, overridable by
        # tests that need deterministic elapsed-time control.
        self._clock = clock
        # The monotonic time of this INSTANCE's most recent outbound
        # Alpha Vantage request, across every public method -- `None`
        # until the first request is made, so that request never sleeps.
        self._last_request_at: float | None = None
        # ATLAS-033 (extended by the Investment Case Engine v1 slice):
        # the already-parsed OVERVIEW values `fetch`,
        # `fetch_historical_snapshots`, and `fetch_company_profile` all
        # need, keyed by ticker so a (hypothetical) instance reused
        # across companies never returns one company's figures for
        # another -- never the raw payload, never given an expiry,
        # since one instance's lifetime is already scoped to one
        # refresh run.
        self._overview_cache: tuple[str, float | None, Any, dict[str, str]] | None = None

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
        payload = self._request_json(url)
        _check_for_provider_error(payload, context=f"Alpha Vantage GLOBAL_QUOTE({ticker})")
        quote = payload.get("Global Quote") if isinstance(payload, dict) else None
        if not quote:
            raise CompanyNotFound(f"Alpha Vantage GLOBAL_QUOTE has no data for {ticker!r}")
        return quote

    def _overview(self, ticker: str, api_key: str) -> dict[str, Any]:
        url = f"{_BASE_URL}?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
        payload = self._request_json(url)
        _check_for_provider_error(payload, context=f"Alpha Vantage OVERVIEW({ticker})")
        return payload if isinstance(payload, dict) else {}

    def _current_overview(self, ticker: str, api_key: str) -> tuple[float | None, Any, dict[str, str]]:
        """(ATLAS-033, extended) `(shares_outstanding, currency,
        identity_fields)` -- reused from this same instance's earlier
        `OVERVIEW` call for `ticker` if one exists, instead of issuing a
        second, redundant request for the identical current-basis
        figures. `identity_fields` is the same OVERVIEW response's
        descriptive fields (see `_identity_fields`), added by the
        Investment Case Engine v1 slice; callers that only need
        `shares_outstanding`/`currency` simply ignore the third value."""
        if self._overview_cache is not None and self._overview_cache[0] == ticker:
            return self._overview_cache[1], self._overview_cache[2], self._overview_cache[3]
        overview = self._overview(ticker, api_key)
        shares_outstanding = _numeric(overview.get("SharesOutstanding"))
        currency = overview.get("Currency")
        identity = _identity_fields(overview)
        self._overview_cache = (ticker, shares_outstanding, currency, identity)
        return shares_outstanding, currency, identity

    def _monthly_adjusted(self, ticker: str, api_key: str) -> dict[str, Any]:
        url = f"{_BASE_URL}?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}&apikey={api_key}"
        payload = self._request_json(url)
        _check_for_provider_error(payload, context=f"Alpha Vantage TIME_SERIES_MONTHLY_ADJUSTED({ticker})")
        series = payload.get("Monthly Adjusted Time Series") if isinstance(payload, dict) else None
        if not isinstance(series, dict):
            raise MalformedProviderResponse(
                f"Alpha Vantage TIME_SERIES_MONTHLY_ADJUSTED({ticker}) missing its time series"
            )
        return series

    def _earnings_call_transcript(self, ticker: str, quarter: str, api_key: str) -> list[dict[str, Any]]:
        url = f"{_BASE_URL}?function=EARNINGS_CALL_TRANSCRIPT&symbol={ticker}&quarter={quarter}&apikey={api_key}"
        payload = self._request_json(url)
        _check_for_provider_error(payload, context=f"Alpha Vantage EARNINGS_CALL_TRANSCRIPT({ticker}, {quarter})")
        transcript = payload.get("transcript") if isinstance(payload, dict) else None
        if not isinstance(transcript, list):
            return []
        return [entry for entry in transcript if isinstance(entry, dict)]

    def _now(self) -> float:
        return self._clock() if self._clock is not None else time.monotonic()

    def _pace(self) -> None:
        """(ATLAS-032 corrective) The one place inter-request spacing is
        decided -- called by `_request_json` before every actual
        outbound call, regardless of which public method triggered it.
        The first request on a freshly constructed instance
        (`_last_request_at is None`) never sleeps; every request after
        that sleeps only the *remaining* interval if less than
        `_inter_request_delay_seconds` has genuinely elapsed since the
        last request this instance made -- never a flat delay
        regardless of real elapsed time."""
        now = self._now()
        if self._last_request_at is not None:
            remaining = self._inter_request_delay_seconds - (now - self._last_request_at)
            if remaining > 0:
                sleeper = self._sleeper if self._sleeper is not None else time.sleep
                sleeper(remaining)
        self._last_request_at = self._now()

    def _request_json(self, url: str) -> Any:
        """The narrowest common boundary every outbound Alpha Vantage
        HTTP call passes through -- `_global_quote`/`_overview`/
        `_monthly_adjusted` all call this instead of `self._fetch_json`
        directly, so pacing is enforced across the whole instance
        (both `fetch` and `fetch_historical_snapshots`), not hand-placed
        between specific call pairs inside one method."""
        self._pace()
        return self._fetch_json(url, None)

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

        shares_outstanding, currency, _identity = self._current_overview(ticker, api_key)
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

        shares_outstanding, currency, _identity = self._current_overview(ticker, api_key)

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

    def fetch_company_profile(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        """(Investment Case Engine v1 slice) The optional
        `CompanyProfileProvider` capability. Reuses `_current_overview`'s
        cache exactly like `fetch_historical_snapshots` does -- if
        `fetch` already ran for this ticker on this instance, this makes
        no additional request at all. Returns `()`, never a fabricated
        document, when the OVERVIEW response carried none of the known
        identity fields (see `_identity_fields`)."""
        api_key = self._resolved_api_key()
        ticker = company_identifier.upper()

        _shares_outstanding, _currency, identity = self._current_overview(ticker, api_key)
        if not identity:
            return ()

        content_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
        document = RawBusinessDocument(
            identifier=f"{ticker}:profile",
            company=ticker,
            source_kind=SourceKind.COMPANY_PROFILE.value,
            published_at=evaluated_at,
            provider_id="alpha_vantage",
            raw_reference=f"{_BASE_URL}?function=OVERVIEW&symbol={ticker}",
            content_hash=content_hash,
            language="en",
            metadata=identity,
        )
        return (document,)

    def fetch_earnings_call_transcripts(
        self, *, company_identifier: str, evaluated_at: datetime
    ) -> tuple[RawBusinessDocument, ...]:
        """(Capability Expansion Sprint 2) The optional `EarningsCall
        TranscriptProvider` capability -- one real API call, requesting
        the most recently *ended* calendar quarter (see `_most_recent_
        completed_quarter`'s own docstring for why no reporting-lag
        heuristic is invented). Returns `()`, never a fabricated
        document, when that quarter's transcript is not yet published
        (an empty `transcript` array in Alpha Vantage's own response)
        or the symbol has none at all.

        **One `RawBusinessDocument` per individual speaker statement**,
        not one per transcript -- `RawBusinessDocument.metadata` only
        supports scalar values (see its own dataclass docstring), so a
        transcript's own list of statements cannot be packed into a
        single document's metadata without inventing a bespoke blob
        format this sprint's own "no provider-specific architecture"
        instruction rules out. This mirrors `SecEdgarFundamentalsProvider
        .fetch`'s own "one document per atomic fact" convention exactly,
        just at statement granularity instead of fiscal-period
        granularity. A real transcript can therefore produce dozens of
        documents from this one call -- `refresh_company_data`'s own
        `_ingest_documents` loop already handles an arbitrary document
        count per provider call with no special case (confirmed by its
        own use for `SecEdgarFundamentalsProvider`'s multi-period
        `fetch`)."""
        api_key = self._resolved_api_key()
        ticker = company_identifier.upper()
        quarter = _most_recent_completed_quarter(evaluated_at)

        entries = self._earnings_call_transcript(ticker, quarter, api_key)
        if not entries:
            return ()

        fiscal_date_ending = _quarter_end_date(quarter)
        documents: list[RawBusinessDocument] = []
        for index, entry in enumerate(entries):
            speaker = entry.get("speaker")
            content = entry.get("content")
            if not isinstance(speaker, str) or not isinstance(content, str) or not content.strip():
                continue
            title = entry.get("title")
            sentiment = _numeric(entry.get("sentiment"))
            metadata: dict[str, Any] = {
                "quarter": quarter,
                "statement_index": index,
                "speaker": speaker.strip(),
                "content": content.strip(),
            }
            if isinstance(title, str) and title.strip():
                metadata["title"] = title.strip()
            if sentiment is not None:
                metadata["sentiment"] = sentiment

            content_hash = hashlib.sha256(
                json.dumps({"quarter": quarter, "index": index, **metadata}, sort_keys=True).encode("utf-8")
            ).hexdigest()
            documents.append(
                RawBusinessDocument(
                    identifier=f"{ticker}:transcript:{quarter}:{index}",
                    company=ticker,
                    source_kind=SourceKind.TRANSCRIPT.value,
                    published_at=evaluated_at,
                    provider_id="alpha_vantage",
                    raw_reference=f"{_BASE_URL}?function=EARNINGS_CALL_TRANSCRIPT&symbol={ticker}&quarter={quarter}",
                    content_hash=content_hash,
                    period_start=fiscal_date_ending,
                    period_end=fiscal_date_ending,
                    language="en",
                    metadata=metadata,
                )
            )
        return tuple(documents)
