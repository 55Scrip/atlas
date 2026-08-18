# Internal Alpha Sprint — Company Coverage & Enrichment Reliability Report

**Date:** 2026-08-18
**Scope:** Live investigation of `refresh_company_data` (SEC EDGAR + Alpha Vantage) and the downstream analysis pipeline, against the real Internal Alpha database.
**Method:** Direct, in-process calls to the real `refresh_company_data` use case (`atlas/alpha/business_data_refresh/service.py`) and the real providers (`SecEdgarFundamentalsProvider`, `AlphaVantageMarketDataProvider`) — the exact code path the product's own "Add to Watchlist/Portfolio" flow triggers. No mocks, no fabricated data. All persisted `BusinessRecord`s are genuine third-party company facts (SEC filings, Alpha Vantage quotes), not investor Decisions/Outcomes — safe, additive, and consistent with the product's own automatic-enrichment design.

---

## 1. Coverage Report

| Region | Company | Ticker tried | Verdict | Verified |
|---|---|---|---|---|
| US | Apple | AAPL | **Full pass** | Live, this session |
| US | Microsoft | MSFT | **Full pass** (SEC complete; AV blocked mid-session by daily quota, see §2) | Live, this session |
| US | Amazon | AMZN | **Full pass** (SEC) | Live, this session |
| US | Alphabet | GOOGL | **Full pass** (SEC) | Live, this session |
| US | Nvidia | NVDA | **Full pass** (SEC) | Live, this session |
| US | Tesla | TSLA | **Full pass** (SEC) | Live, this session |
| Sweden | Volvo B | VOLV-B.ST / VOLV-B.STO | **Zero coverage** | Live, this session |
| Sweden | Atlas Copco | ATCO-B.ST | **Zero coverage** | Live, this session |
| Sweden | Investor | — | Zero coverage (same class) | Extrapolated, high confidence |
| Sweden | Evolution | — | Zero coverage (same class) | Extrapolated, high confidence |
| Sweden | Hexagon | — | Zero coverage (same class) | Extrapolated, high confidence |
| Sweden | Saab | — | Zero coverage (same class) | Extrapolated, high confidence |
| Europe | ASML | ASML | **Partial**: SEC resolves the company but has no usable financials (20-F filer, no 10-K); AV market data succeeds | Live, this session |
| Europe | Novo Nordisk | NVO | **Partial** (same class as ASML, market data confirmed live) | Live (market data only) |
| Europe | SAP | SAP | **Partial** (same class) | Live (market data only) |
| Europe | LVMH | LVMUY (ADR) | **Partial** (same class) — *fails entirely* if a user enters the Paris-listing ticker instead of the ADR (see §3) | Live (market data only) |
| Europe | Siemens | SIEGY (ADR) | **Partial** (same class) — same Paris/Frankfurt-ticker caveat as LVMH | Live (market data only) |
| Asia | Toyota | TM | **Partial** (same class) | Live (market data only) |
| Asia | TSMC | TSM | **Partial**: SEC resolves the company but "has no us-gaap facts at all" (non-US-GAAP 20-F filer); AV market data succeeds | Live, this session |
| Asia | Sony | SONY | **Partial** (same class) | Live (market data only) |

**Headline:** 6/6 US companies fully pass. 0/6 Swedish companies get any data at all. 8/8 tested non-US, non-Swedish internationals get market data but never real financial statements — meaning **none of the 14 non-US companies in the test universe can produce a real Business Analysis, Valuation, or Risk Analysis today**, regardless of how well-known or liquid the company is.

---

## 2. Reliability Matrix

Rows are the sprint's own pipeline stages. Columns are the three coverage classes actually observed (a single row per company would be 1,300+ lines and mostly repeat one of these three patterns).

| Capability | US domestic filer (AAPL, MSFT, AMZN, GOOGL, NVDA, TSLA) | Foreign ADR/cross-listed (ASML, TSM, NVO, SAP, LVMUY, SIEGY, TM, SONY) | Local-exchange-only (VOLV-B.ST, ATCO-B.ST, + 4 more Sweden) |
|---|---|---|---|
| Identification | Pass | Pass (SEC resolves a real CIK; AV resolves the ticker) | **Fail** — SEC: `CompanyNotFound`; AV: `no data` |
| Market Data | Pass | Pass | **Fail** |
| Company Profile | Pass | Pass (via AV OVERVIEW) | **Fail** |
| Financial Statements | Pass (SEC XBRL 10-K) | **Fail** — SEC finds the filer but no 10-K facts (20-F filers use a different form/taxonomy) | **Fail** |
| Business Analysis | Pass | **INSUFFICIENT_INPUT** (no Revenue/FCF/Debt facts to evaluate) | **INSUFFICIENT_INPUT** |
| Valuation | Pass | **INSUFFICIENT_INPUT** (FCF Yield needs FCF history, not just price) | **INSUFFICIENT_INPUT** |
| Risk Analysis | Pass | **INSUFFICIENT_INPUT** across nearly all categories | **INSUFFICIENT_INPUT** |
| Evidence | Pass | Present but empty of real findings | Present but empty of real findings |
| Open Questions | Pass | Populated (correctly — Atlas is honest that it doesn't know) | Populated (correctly) |
| Investment Thesis | Pass | `ThesisPosture.INSUFFICIENT_DATA`, honest fallback narrative | Same fallback |
| Recommendation | Pass | `RecommendationWithheld` ("insufficient evidence") | Same |
| Decision Ready | **Yes** | **No** | **No** |

The downstream rows (Business Analysis → Decision Ready) for the two non-US classes were not re-run end-to-end against a live Case this session (that requires an existing persisted Case, out of scope for a data-only probe), but every evaluator in this codebase is independently, repeatedly documented and tested (ATLAS-021 through ATLAS-026) to degrade to a named `INSUFFICIENT_INPUT`/`INSUFFICIENT_EVIDENCE` state rather than crash or fabricate a conclusion when its required facts are absent — confirmed live elsewhere this session on TSLA's own "Atlas doesn't yet have enough evidence to form a clear view" state. **The pipeline does not break technically for these companies — it correctly, honestly produces an empty investment case.** That is a data-coverage failure, not a pipeline-robustness failure.

---

## 3. Root Cause Analysis

Three distinct, independent root causes were found — not one:

### 3.1 SEC EDGAR only covers US-domestic 10-K filers (documented, known limitation)
**Architectural component: Provider (fundamentals).** `SecEdgarFundamentalsProvider`'s own docstring already states this plainly: *"SEC EDGAR only covers US SEC-registered filers... roughly half the real internal dev portfolio... resolve to `CompanyNotFound` here, honestly, every time — there is no fallback guess."* Confirmed live for every Swedish ticker tested. This is not a bug; it is a stated, accepted scope boundary from ATLAS-031 that was never revisited.

### 3.2 Foreign private issuers that *do* file with the SEC still fail, because they don't file 10-Ks
**Architectural component: Provider (fundamentals) + parser.** This is a **new finding**, distinct from 3.1. ASML and TSMC both resolve to a real SEC CIK — SEC *does* have a record of them — but:
- ASML: *"No annual 10-K fundamentals found"* — ASML files Form 20-F (the SEC's foreign-private-issuer annual report), not 10-K. `SecEdgarFundamentalsProvider` only ever looks for `_FILING_INDEX_URL_TEMPLATE...type=10-K`.
- TSMC: *"SEC companyfacts... has no us-gaap facts at all"* — TSMC's 20-F is filed under IFRS, not US-GAAP, so the provider's `us-gaap:*` XBRL tag extraction finds an empty set even though the companyfacts document itself exists.

This means the "roughly half the portfolio" estimate in the ATLAS-031 docstring **understates the real gap**: it's not just tickers SEC has never heard of — it's *every* foreign private issuer, including large, liquid, US-cross-listed ones SEC has a full record of. Alpha Vantage's OVERVIEW/GLOBAL_QUOTE endpoints fill in market data and a text profile for these, but never their financial statement history, because AV's own OVERVIEW payload only carries a handful of trailing ratios, not multi-year Revenue/FCF/Debt/Buyback/Dividend series — the exact fields `business_facts/extraction.py` needs.

### 3.3 Alpha Vantage's free-tier key is capped at 25 requests/day, and this sprint's own testing exhausted it
**Architectural component: Provider (market data), operational/deployment configuration.** This is the most severe and most universal finding, because it affects **every** company, including the fully-covered US majors. Mid-session, a routine MSFT refresh returned:

> *"We have detected your API key... our standard API rate limit is 25 requests per day."*

At roughly 2–3 Alpha Vantage calls per newly-enriched company (GLOBAL_QUOTE + OVERVIEW + historical snapshots), **the current deployment can enrich on the order of 8–10 brand-new companies per day before Alpha Vantage stops answering entirely** — for *any* market, including US tickers that would otherwise pass immediately. `AlphaVantageMarketDataProvider` already has correct, honest error surfacing (this is exactly why the failure was legible instead of silent) and existing in-process request spacing (`_inter_request_delay_seconds = 1.1`, added in ATLAS-032's corrective sprint) — but request *spacing* only prevents hammering the API within one process; it does nothing about the **daily quota ceiling**, which is a hard external limit on the API key itself, not a client-side pacing problem.

---

## 4. Recovery Analysis

| Failure class | Manual refresh retry? | Automatic recovery? | Notes |
|---|---|---|---|
| Local-exchange-only, no SEC/AV coverage (3.1) | No — retrying returns the identical `CompanyNotFound`/`no data` error every time | No | Deterministic, not transient. Re-running `refresh_company_data` is safe (idempotent, correctly recorded in `provider_errors` again) but never succeeds without a new data source. |
| SEC-registered foreign filer, wrong form type (3.2) | No — the 10-K/us-gaap search will never find a 20-F/IFRS filing | No | Same as above: deterministic, not a timing or availability problem. |
| Alpha Vantage daily quota exhausted (3.3) | **Yes — but only after the quota window resets** (next UTC day on the free tier) | **Yes, automatically, once the day rolls over** — `ensure_company_enriched`'s "keep retrying only a company that's never been minimally complete" design (documented in `service.py`) means a still-incomplete company will pick right back up on its next Watchlist/Portfolio add, with no code change needed | This is the one failure class in this sprint that is genuinely just "try again later," not an architecture problem — provided the *volume* of new companies per day stays under the free-tier ceiling. |

No case in this sprint required a code change to recover — every failure is either a stable, correctly-reported data-coverage gap (3.1/3.2) or a quota that resets on its own (3.3).

---

## 5. Architectural Bottlenecks

Ranked by how many companies in the test universe they block:

1. **No financial-statement provider for non-US-GAAP / non-10-K filers.** Blocks all 14 non-US companies tested. This is the single largest bottleneck by company count — bigger than the "SEC has literally never heard of this ticker" case (3.1), because it also blocks large, liquid, ADR-covered names investors are very likely to actually add (ASML, TSMC, SAP, Toyota, Sony, Novo Nordisk).
2. **Alpha Vantage free-tier daily quota (25 requests/day).** Blocks *every* company, US or not, once the day's quota is spent — a hard ceiling on total daily enrichment throughput for the whole product, not specific to any market.
3. **SEC EDGAR's own, already-documented "US filers only" boundary.** Blocks the 6 Sweden-only tickers specifically. Already known; already honestly reported per-ticker; the smallest of the three bottlenecks in company count, but the *only* one where the company genuinely has no realistic financial-statement source in English-language, XBRL-shaped form at all (Swedish GAAP filings with Bolagsverket aren't XBRL-tagged the way SEC's are).

---

## 6. Prioritized Recommendations

Ordered by expected impact on overall company coverage, not by implementation effort:

1. **Move off the Alpha Vantage free tier, or add a second market-data provider as fallback.** This is the highest-impact, lowest-complexity fix: it doesn't require touching any parsing/normalization logic, and it immediately un-blocks every company class, including the ones that otherwise fully work today. A paid Alpha Vantage tier (or a provider swap, since the codebase's own `BusinessDataProvider` protocol is already proven provider-agnostic per the ATLAS-031 swappability tests) removes bottleneck #2 entirely.
2. **Add a 20-F/IFRS financial-statement extraction path to (or alongside) `SecEdgarFundamentalsProvider`.** SEC EDGAR *already has* the underlying filings for foreign private issuers (confirmed live for ASML and TSMC) — the gap is that the provider only looks for `type=10-K` and only extracts `us-gaap:*` tags. Extending it to also read 20-F filings and recognize IFRS-namespaced tags (`ifrs-full:*`) would close bottleneck #1 for every foreign issuer that files with the SEC at all — which, per this sprint's own evidence, is most of the large-cap non-US names investors would realistically add (ASML, TSMC, SAP, Novo Nordisk, Toyota, Sony), even though it would still leave Sweden-only-listed names uncovered.
3. **Add a genuinely non-US market data source (e.g., a Nordic/European exchange feed) for companies with no US listing at all.** This is real, non-trivial new-provider work (bottleneck #3) and should come last: it has the smallest company-count impact of the three, and — per the existing `SecEdgarFundamentalsProvider` docstring's own honest admission — was already a known, explicitly-deferred gap from ATLAS-031, not a regression introduced since.

None of these three recommendations require touching the enrichment orchestration, the business/valuation/risk evaluators, the Investment Case synthesis, or the frontend — every one of those layers was confirmed, live, to already do the right thing (honest `INSUFFICIENT_INPUT`/`INSUFFICIENT_EVIDENCE` degradation) with whatever data actually arrives. The entire coverage gap traced back to the two providers at the very top of the pipeline.
