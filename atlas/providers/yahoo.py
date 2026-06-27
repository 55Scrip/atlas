from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from atlas.analysis.company_analysis import CompanyAnalysis, create_placeholder_company_analysis
from atlas.analysis.portfolio import CompanyPortfolioProfile


YAHOO_QUOTE_SUMMARY_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary"
YAHOO_MODULES = ",".join(
    (
        "price",
        "summaryProfile",
        "defaultKeyStatistics",
        "financialData",
        "summaryDetail",
    )
)


class YahooFinanceProviderError(LookupError):
    """Raised when Yahoo Finance data cannot be retrieved or mapped."""


@dataclass(frozen=True)
class YahooCompany:
    ticker: str
    name: str
    exchange: str | None
    sector: str | None
    industry: str | None
    market_cap: float | None


@dataclass(frozen=True)
class YahooFinancials:
    revenue: float | None
    gross_margin: float | None
    operating_margin: float | None
    net_margin: float | None
    free_cash_flow: float | None
    eps: float | None
    shares_outstanding: float | None


@dataclass(frozen=True)
class YahooMarketData:
    current_price: float | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None
    pe_ratio: float | None
    beta: float | None
    dividend_yield: float | None


JsonFetcher = Callable[[str], dict[str, Any]]


class YahooFinanceProvider:
    def __init__(self, fetcher: JsonFetcher | None = None, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self._fetcher = fetcher or (lambda url: _fetch_json(url, timeout=self.timeout))
        self._cache: dict[str, dict[str, Any]] = {}

    def get_company(self, ticker: str) -> YahooCompany:
        normalized_ticker = _normalize_ticker(ticker)
        payload = self._quote_summary(normalized_ticker)
        price = payload.get("price", {})
        profile = payload.get("summaryProfile", {})
        return YahooCompany(
            ticker=normalized_ticker,
            name=_string_value(price.get("longName"))
            or _string_value(price.get("shortName"))
            or normalized_ticker,
            exchange=_string_value(price.get("exchangeName"))
            or _string_value(price.get("exchange")),
            sector=_string_value(profile.get("sector")),
            industry=_string_value(profile.get("industry")),
            market_cap=_number_value(price.get("marketCap")),
        )

    def get_financials(self, ticker: str) -> YahooFinancials:
        normalized_ticker = _normalize_ticker(ticker)
        payload = self._quote_summary(normalized_ticker)
        financial_data = payload.get("financialData", {})
        default_key_statistics = payload.get("defaultKeyStatistics", {})
        return YahooFinancials(
            revenue=_number_value(financial_data.get("totalRevenue")),
            gross_margin=_number_value(financial_data.get("grossMargins")),
            operating_margin=_number_value(financial_data.get("operatingMargins")),
            net_margin=_number_value(financial_data.get("profitMargins")),
            free_cash_flow=_number_value(financial_data.get("freeCashflow")),
            eps=_number_value(default_key_statistics.get("trailingEps")),
            shares_outstanding=_number_value(default_key_statistics.get("sharesOutstanding")),
        )

    def get_market_data(self, ticker: str) -> YahooMarketData:
        normalized_ticker = _normalize_ticker(ticker)
        payload = self._quote_summary(normalized_ticker)
        summary_detail = payload.get("summaryDetail", {})
        financial_data = payload.get("financialData", {})
        default_key_statistics = payload.get("defaultKeyStatistics", {})
        return YahooMarketData(
            current_price=_number_value(financial_data.get("currentPrice"))
            or _number_value(payload.get("price", {}).get("regularMarketPrice")),
            fifty_two_week_high=_number_value(summary_detail.get("fiftyTwoWeekHigh")),
            fifty_two_week_low=_number_value(summary_detail.get("fiftyTwoWeekLow")),
            pe_ratio=_number_value(summary_detail.get("trailingPE")),
            beta=_number_value(default_key_statistics.get("beta")),
            dividend_yield=_number_value(summary_detail.get("dividendYield")),
        )

    def get_company_analysis(self, ticker: str) -> CompanyAnalysis:
        company = self.get_company(ticker)
        market_data = self.get_market_data(ticker)
        financials = self.get_financials(ticker)
        label = f"{company.name} ({company.ticker})"
        analysis = create_placeholder_company_analysis(label)
        return replace(
            analysis,
            valuation=analysis.valuation.__class__(
                score=_valuation_score(market_data),
                summary=_valuation_summary(label, market_data),
                strengths=analysis.valuation.strengths,
                weaknesses=analysis.valuation.weaknesses,
            ),
            quality=analysis.quality.__class__(
                score=_quality_score(financials),
                summary=_quality_summary(label, financials),
                strengths=analysis.quality.strengths,
                weaknesses=analysis.quality.weaknesses,
            ),
        )

    def get_portfolio_profile(self, ticker: str) -> CompanyPortfolioProfile:
        company = self.get_company(ticker)
        financials = self.get_financials(ticker)
        market_data = self.get_market_data(ticker)
        return CompanyPortfolioProfile(
            ticker=company.ticker,
            company=company.name,
            sector=company.sector or "Unknown",
            country="Unknown",
            market_cap=company.market_cap or 0.0,
            quality_score=_quality_score(financials),
            risk_score=_portfolio_risk_score(market_data),
        )

    def _quote_summary(self, ticker: str) -> dict[str, Any]:
        if ticker not in self._cache:
            url = (
                f"{YAHOO_QUOTE_SUMMARY_URL}/{quote(ticker)}"
                f"?modules={YAHOO_MODULES}&corsDomain=finance.yahoo.com"
            )
            try:
                payload = self._fetcher(url)
            except HTTPError as exc:
                raise _http_error(ticker, exc) from exc
            except URLError as exc:
                raise YahooFinanceProviderError(
                    f"Yahoo Finance network error for {ticker}: {exc.reason}"
                ) from exc
            except TimeoutError as exc:
                raise YahooFinanceProviderError(
                    f"Yahoo Finance request timed out for {ticker}."
                ) from exc
            except OSError as exc:
                raise YahooFinanceProviderError(
                    f"Yahoo Finance request failed for {ticker}: {exc}"
                ) from exc
            self._cache[ticker] = _extract_quote_summary_result(ticker, payload)
        return self._cache[ticker]


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "AtlasInvestmentOS/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_quote_summary_result(ticker: str, payload: dict[str, Any]) -> dict[str, Any]:
    quote_summary = payload.get("quoteSummary")
    if not isinstance(quote_summary, dict):
        raise YahooFinanceProviderError(
            f"Yahoo Finance returned an unexpected response for {ticker}."
        )
    error = quote_summary.get("error")
    if error:
        description = error.get("description") if isinstance(error, dict) else str(error)
        raise YahooFinanceProviderError(f"Yahoo Finance error for {ticker}: {description}")
    results = quote_summary.get("result")
    if not isinstance(results, list) or not results:
        raise YahooFinanceProviderError(
            f"No Yahoo Finance data found for {ticker}. Check the ticker symbol."
        )
    result = results[0]
    if not isinstance(result, dict):
        raise YahooFinanceProviderError(
            f"Yahoo Finance returned malformed data for {ticker}."
        )
    return result


def _http_error(ticker: str, exc: HTTPError) -> YahooFinanceProviderError:
    if exc.code == 404:
        return YahooFinanceProviderError(
            f"No Yahoo Finance data found for {ticker}. Check the ticker symbol."
        )
    if exc.code == 429:
        return YahooFinanceProviderError(
            f"Yahoo Finance rate limit reached for {ticker}. Try again later."
        )
    return YahooFinanceProviderError(
        f"Yahoo Finance HTTP error for {ticker}: {exc.code} {exc.reason}"
    )


def _normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not normalized:
        raise YahooFinanceProviderError("Ticker symbol cannot be empty.")
    return normalized


def _number_value(value: Any) -> float | None:
    if isinstance(value, dict):
        raw = value.get("raw")
    else:
        raw = value
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _string_value(value: Any) -> str | None:
    if isinstance(value, dict):
        raw = value.get("raw") or value.get("fmt")
    else:
        raw = value
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _valuation_score(market_data: YahooMarketData) -> int:
    score = 70
    if market_data.pe_ratio is not None:
        if market_data.pe_ratio <= 15:
            score += 12
        elif market_data.pe_ratio <= 25:
            score += 4
        elif market_data.pe_ratio >= 50:
            score -= 15
        elif market_data.pe_ratio >= 35:
            score -= 8
    if (
        market_data.current_price is not None
        and market_data.fifty_two_week_high is not None
        and market_data.fifty_two_week_high > 0
    ):
        distance_from_high = 1 - (market_data.current_price / market_data.fifty_two_week_high)
        if distance_from_high >= 0.30:
            score += 8
        elif distance_from_high <= 0.05:
            score -= 5
    return max(0, min(100, score))


def _quality_score(financials: YahooFinancials) -> int:
    score = 65
    if financials.gross_margin is not None:
        if financials.gross_margin >= 0.50:
            score += 10
        elif financials.gross_margin >= 0.30:
            score += 4
        else:
            score -= 5
    if financials.operating_margin is not None:
        if financials.operating_margin >= 0.25:
            score += 12
        elif financials.operating_margin >= 0.10:
            score += 5
        else:
            score -= 8
    if financials.net_margin is not None:
        if financials.net_margin >= 0.20:
            score += 10
        elif financials.net_margin >= 0.08:
            score += 4
        else:
            score -= 8
    if financials.free_cash_flow is not None:
        score += 8 if financials.free_cash_flow > 0 else -10
    return max(0, min(100, score))


def _portfolio_risk_score(market_data: YahooMarketData) -> int:
    score = 75
    if market_data.beta is not None:
        if market_data.beta >= 1.8:
            score -= 20
        elif market_data.beta >= 1.3:
            score -= 10
        elif market_data.beta <= 0.8:
            score += 5
    if (
        market_data.current_price is not None
        and market_data.fifty_two_week_low is not None
        and market_data.fifty_two_week_high is not None
        and market_data.fifty_two_week_high > market_data.fifty_two_week_low
    ):
        range_position = (
            (market_data.current_price - market_data.fifty_two_week_low)
            / (market_data.fifty_two_week_high - market_data.fifty_two_week_low)
        )
        if range_position >= 0.85:
            score -= 8
        elif range_position <= 0.35:
            score += 5
    return max(0, min(100, score))


def _valuation_summary(label: str, market_data: YahooMarketData) -> str:
    pe = "unknown" if market_data.pe_ratio is None else f"{market_data.pe_ratio:.1f}"
    price = (
        "unknown"
        if market_data.current_price is None
        else f"{market_data.current_price:.2f}"
    )
    return f"{label} valuation uses Yahoo price {price} and trailing P/E {pe}."


def _quality_summary(label: str, financials: YahooFinancials) -> str:
    operating_margin = (
        "unknown"
        if financials.operating_margin is None
        else f"{financials.operating_margin:.1%}"
    )
    return f"{label} quality uses Yahoo operating margin {operating_margin}."
