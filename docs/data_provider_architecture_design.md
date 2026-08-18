# Data Provider Architecture & International Coverage — Design Report

**Sprint scope:** Determine the long-term provider architecture that lets
Atlas reliably build investment cases for publicly listed companies across
major global markets. This is a design/documentation sprint — no product
code, UI, or analysis logic changes. It builds directly on the
[Company Coverage & Enrichment Reliability report](company_coverage_enrichment_reliability_report.md),
whose three root causes (SEC US-only scope, 20-F/IFRS foreign filers, Alpha
Vantage's 25/day free-tier cap) are treated here as established input, not
re-derived.

Target markets: US, Canada, Sweden, Norway, Denmark, Finland, Germany,
France, Netherlands, Switzerland, UK, Japan, Taiwan, South Korea, Australia.

---

## Deliverable 1 — Current Architecture Map

Atlas's provider layer is a small Protocol family in
[`atlas/analysis_engine/business_data/providers.py`](../atlas/analysis_engine/business_data/providers.py):

| Protocol | Method | Purpose | Required or optional |
|---|---|---|---|
| `BusinessDataProvider` | `fetch(*, company_identifier, evaluated_at) -> tuple[RawBusinessDocument, ...]` | Any raw document a provider can produce (filing extract, quote, profile) | Required — every provider implements this |
| `HistoricalMarketDataProvider` | `fetch_historical_snapshots(*, company_identifier, filing_dates, evaluated_at)` | Price history aligned to filing dates, for temporal valuation | Optional, `isinstance`-probed |
| `CompanyProfileProvider` | `fetch_company_profile(*, company_identifier, evaluated_at)` | Static identity/descriptive facts (name, sector, currency, fiscal year end) | Optional, `isinstance`-probed |

The orchestration entrypoint, `refresh_company_data`
([`atlas/alpha/business_data_refresh/service.py`](../atlas/alpha/business_data_refresh/service.py)),
calls every configured provider independently — one provider's failure is
recorded in `RefreshSummary.provider_errors` and never blocks another
provider's success — then probes each for the two optional capabilities via
`isinstance`. This is already a **provider-agnostic, pluggable
architecture**: adding a new provider means implementing the Protocol and
adding it to the tuple passed to `refresh_company_data`, not changing any
orchestration, normalization, or analysis code. This substantially de-risks
this sprint's recommendations — the extension point already exists.

Two providers are live today, in `atlas/business_data_providers/`:

### `SecEdgarFundamentalsProvider`

| Attribute | Detail |
|---|---|
| Responsibility | US financial statements (income statement, balance sheet, cash flow, EPS, shares, debt) |
| Input | Ticker string, resolved internally via SEC's own `company_tickers.json` ticker→CIK map |
| Output | `RawBusinessDocument` per filing, tagged with `us-gaap:*` XBRL facts |
| Coverage | US SEC-registered filers on **Form 10-K only** |
| Known limitation (own docstring) | *"SEC EDGAR only covers US SEC-registered filers... roughly half of the real internal dev portfolio... resolve to `CompanyNotFound`... every time — there is no fallback guess."* Confirmed live in Sprint F: foreign private issuers (ASML, TSM) resolve a real CIK but file **20-F**, not 10-K, so zero usable facts are extracted despite CIK resolution succeeding. |
| Rate limits | SEC's fair-access policy — requires a contact-email-shaped `User-Agent`, 403 without one; no published hard request cap for reasonable single-company use |
| Cost | Free, no API key |
| Failure modes | `CompanyNotFound` (no CIK match — non-US names, e.g. Volvo B); silently-empty fact set (CIK resolves, wrong form type — ASML/TSM) |

### `AlphaVantageMarketDataProvider`

| Attribute | Detail |
|---|---|
| Responsibility | Market quote (`fetch`/GLOBAL_QUOTE), historical prices (`fetch_historical_snapshots`/MONTHLY_ADJUSTED), company profile (`fetch_company_profile`/OVERVIEW) |
| Input | Ticker/symbol string, Alpha Vantage's own symbol matching |
| Output | `RawBusinessDocument` per call type |
| Coverage | Global tickers *nominally* (GLOBAL_QUOTE resolves many non-US symbols), but see cost/quota below |
| Known limitation | Built-in inter-request pacing (`_DEFAULT_INTER_REQUEST_DELAY_SECONDS = 1.1`, added in ATLAS-032) prevents hammering **within one process** but does **not** address the account-level daily quota |
| Rate limits | **Confirmed live this session: the deployed key is on the free tier's 25-requests/day cap** — exhausted mid-session during routine testing, blocking even fully-covered US tickers (e.g. MSFT) for the rest of that day |
| Cost | Free tier (25 req/day) deployed today; paid tiers exist but were not evaluated as "the fix" since coverage, not just quota, is the deeper problem (see Deliverable 2) |
| Failure modes | Rate-limit error string returned as a normal API 200 response (not an HTTP error code) — must be parsed from response content, a fragile contract |

### What's structurally missing today

- **No canonical company identity model.** `normalize()` in
  [`atlas/analysis_engine/business_data/normalization.py`](../atlas/analysis_engine/business_data/normalization.py)
  does only document-structural cleanup (whitespace, hash/language-code
  case, `SourceKind` conversion) — it does **not** reconcile ticker/company
  identity across providers or exchanges. Each provider resolves the raw
  `company_identifier: str` independently (SEC via its CIK map, Alpha
  Vantage via its own symbol match). Two providers could each believe they
  resolved "the same company" and be wrong, with nothing to catch it. This
  is a real gap, addressed in Deliverable 5 (Phase 7).
- **No non-US, non-Alpha-Vantage market data source.** Every non-US company
  today depends entirely on Alpha Vantage's global reach, which is both
  quota-constrained and has unconfirmed depth for local-exchange-only names
  (Sprint F never got a clean historical-snapshot test for a Sweden-only
  name before the quota was exhausted).
- **No IFRS/20-F-aware financial statement provider.** SEC EDGAR is
  US-GAAP/10-K only; nothing in the current stack reads 20-F, 6-K, or
  IFRS-tagged filings.

---

## Deliverable 2 — Coverage Comparison (Current vs. Target Markets)

Live-evidence status per market, carried forward from Sprint F where tested,
otherwise assessed from the current architecture's own design (SEC = US
only; Alpha Vantage = quote/profile only, depth unconfirmed for most
non-US names):

| Market | Security ID / quote | Historical prices | Company profile | Financial statements | Status |
|---|---|---|---|---|---|
| **US** | ✅ Alpha Vantage | ✅ Alpha Vantage | ✅ Alpha Vantage | ✅ SEC EDGAR (10-K/US-GAAP) | **Full coverage** (Sprint F: 6/6 pass) |
| **Canada** | ⚠️ AV symbol match untested | ⚠️ untested | ⚠️ untested | ❌ no provider (not a SEC 10-K filer for TSX-only names) | **No coverage confirmed** |
| **Sweden** | ⚠️ AV resolves some ADR-style symbols; local-exchange-only (`.ST`) untested before quota exhaustion | ❌ untested | ❌ untested | ❌ SEC has no CIK (Sprint F: Volvo B, Atlas Copco fail at identification) | **Fails — local-exchange-only names have zero path to a financial statement** |
| **Norway** | ⚠️ untested | ❌ untested | ❌ untested | ❌ same as Sweden | **No coverage confirmed** |
| **Denmark** | ⚠️ untested | ❌ untested | ❌ untested | ❌ same pattern | **No coverage confirmed** |
| **Finland** | ⚠️ untested | ❌ untested | ❌ untested | ❌ same pattern | **No coverage confirmed** |
| **Germany** | ✅ ADR names resolve (SIEGY tested) | ⚠️ untested | ⚠️ untested | ❌ SEC has no CIK for OTC-ADR-only names; local Xetra listing has none either | **Partial — quote only, no statements** |
| **France** | ⚠️ ADR untested (LVMUY attempted) | ❌ untested | ❌ untested | ❌ same pattern | **No coverage confirmed** |
| **Netherlands** | ✅ ASML resolves (Nasdaq-listed) | ⚠️ untested | ⚠️ untested | ⚠️ **SEC CIK resolves but files 20-F, zero us-gaap facts** (Sprint F root cause 3.2) | **Partial — identification only, statements fail** |
| **Switzerland** | ⚠️ untested | ❌ untested | ❌ untested | ❌ no provider | **No coverage confirmed** |
| **UK** | ⚠️ untested | ❌ untested | ❌ untested | ❌ no provider (Companies House has no clean structured API — see Deliverable 3) | **No coverage confirmed** |
| **Japan** | ✅ ADR names resolve (TM, SONY tested) | ⚠️ untested | ⚠️ untested | ❌ ADR filers are 20-F, same IFRS/GAAP-gap pattern as Netherlands | **Partial — identification only** |
| **Taiwan** | ✅ TSM (ADR) resolves | ⚠️ untested | ⚠️ untested | ⚠️ **SEC CIK resolves but files 20-F, zero facts** (Sprint F root cause 3.2, TSM was the second confirmed case) | **Partial — identification only, statements fail** |
| **South Korea** | ⚠️ untested | ❌ untested | ❌ untested | ❌ no provider | **No coverage confirmed** |
| **Australia** | ⚠️ untested | ❌ untested | ❌ untested | ❌ no provider | **No coverage confirmed** |

**Reading this table honestly:** Atlas has full coverage for exactly one
market (US) and zero markets with complete non-US coverage. Even the
"partial" markets (Netherlands, Taiwan, Japan, Germany) only succeed at
company *identification*, not the financial-statement stage that an
investment case actually needs — which matches this sprint's own framing:
*"the architecture — not the analysis engine — is the main obstacle."*

**Data quality / financial statement / corporate action / price history
notes:**
- Every non-US financial-statement gap traces to one of two root causes:
  SEC has no filing at all for the company (Nordic local-exchange names),
  or SEC has a filing in the wrong reporting standard (20-F/IFRS ADRs).
- No provider in the current stack returns corporate actions (splits,
  dividends, spin-offs) at all — Alpha Vantage's MONTHLY_ADJUSTED implicitly
  adjusts for splits/dividends in its price series but does not expose the
  discrete events, and this was out of scope for Sprint F/G's live testing.
- Currency handling exists in the data model (`CompanyProfile.currency`,
  populated from Alpha Vantage OVERVIEW per ATLAS-032/033) but has only ever
  been exercised against US-denominated instruments in practice.

---

## Deliverable 3 — Reporting Standards Gap

The brief asks where the architecture assumes US-only reporting. Concretely:

| Standard | Who files it | Current Atlas support |
|---|---|---|
| **US GAAP / Form 10-K** | US domestic filers | ✅ Fully supported — `SecEdgarFundamentalsProvider` extracts `us-gaap:*` XBRL tags from `data.sec.gov/api/xbrl/companyfacts/` |
| **US GAAP / Form 10-Q** | US domestic filers, quarterly | ❌ Not fetched — provider template targets `type=10-K` only |
| **IFRS / Form 20-F** | Foreign private issuers registered with the SEC (ASML, TSM, Sony, Novo Nordisk, etc.) | ❌ Not read at all. This is the single largest confirmed gap: these companies pass identification (real CIK resolves) and then produce **zero** financial facts, which is more misleading than an outright `CompanyNotFound` because nothing signals *why* the case stays empty. |
| **Form 6-K** (foreign issuer interim/current reports) | Same population as 20-F filers | ❌ Not read |
| **Local-jurisdiction IFRS filings** (Nordic, German, French, Dutch, Swiss, UK, Australian domestic-only listings with no US registration) | Companies with no SEC presence at all | ❌ No provider exists for this population at any level — not a parsing gap, a total absence |
| **Japanese / Taiwanese / Korean domestic GAAP** (for the ~half of large-cap names in those markets not also SEC-registered) | Local-exchange-only names | ❌ No provider |

The architecture's US-only assumption is concentrated in exactly one place:
`SecEdgarFundamentalsProvider._extract_facts()`'s hardcoded `us-gaap:*`
namespace and its `type=10-K`-only filing-index URL. It is not diffused
across the codebase — normalization, ingestion, and every downstream
evaluator are standard-agnostic (they consume `BusinessFactKind` values,
not raw XBRL), which means **fixing this is additive** (a parallel
IFRS-aware extractor or a new provider), not a rewrite.

---

## Deliverable 4 — Provider Comparison

Evaluated against the brief's own criteria: coverage, reliability, API
quality, licensing, cost, rate limits, international support. Sources are
cited; the FMP pricing page returned an HTTP 403 to direct fetch and one
web-search claim ("$19/month unlimited real-time") could not be verified
against FMP's own site — it is flagged as unconfirmed rather than repeated
as fact.

| Provider | International coverage | Fundamentals depth | Reporting-standard breadth | Rate limits / cost | Licensing note | Verdict |
|---|---|---|---|---|---|---|
| **Twelve Data** | Strongest candidate found: 90+ exchanges, 1M+ symbols, 50+ countries. Confirmed via direct exchange-page fetch: Stockholm, Copenhagen, Helsinki, Frankfurt/Xetra, Paris, Amsterdam, Swiss/SIX, London, Tokyo, Taiwan, Korea, Australia, Toronto **and Oslo** (a dedicated `xosl` exchange page confirms real-time + historical + fundamentals coverage, correcting an earlier read of their general exchange list where Oslo did not appear) | 20+ years fundamentals history (Income Statement/Balance Sheet/Cash Flow/Operating Metrics) per their own documentation | Not confirmed IFRS-native vs. GAAP-normalized — needs direct verification before committing | Paid tiers from $29/mo; full international fundamentals + Oslo-tier coverage requires **Pro+ or Venture+** (higher tier, exact price not confirmed) | Standard commercial API license | **Primary candidate for market data + international fundamentals** |
| **Financial Modeling Prep (FMP)** | Claims NA/Europe/APAC/LatAm/Middle East/Africa. Coverage appears **tiered by depth**: Basic (free, 250 calls/day, EOD-only), Starter (real-time US), Premium (+UK/Canada), Ultimate (global + transcripts/13F/bulk) | Unclear whether Ultimate tier's "global coverage" extends to IFRS financial statements for Nordic/Asian names, or only pricing/EOD data — **not confirmed, pricing page blocked direct verification (403)** | Unconfirmed | Free tier exists (250 calls/day) but real global fundamentals likely requires Ultimate — exact price unconfirmed; the "$19/mo unlimited" claim seen in search results is **not verified and should not be cited** | Standard commercial | **Secondary candidate — needs a direct account/sales conversation before committing budget** |
| **Finnhub** | Claims 60+ global exchanges incl. LSE, TSX, ASX, Euronext, TSE, HKEX, SGX | Free tier: US real-time quotes, company news, basic fundamentals, SEC filings only. International stocks + detailed financials require Premium | IFRS-specific standardization **not confirmed** by available documentation | Free: 60 calls/minute (generous rate, narrow scope). Premium: $11.99–$99.99/mo | Standard commercial | **Viable low-cost fallback for market data; fundamentals depth for target markets unconfirmed** |
| **Tiingo** | Price/OHLCV coverage broad (82,468 global securities) | Fundamentals explicitly scoped to **"US, ADRs, Chinese Equities"** by Tiingo's own description — not Nordic/European native fundamentals. Fundamentals now gated as a sales-contact add-on | Effectively US-GAAP-only in practice | $30/mo individual, $50/mo commercial | Fundamentals require a separate sales conversation | **Not a fit for this sprint's international fundamentals requirement — price-history-only value** |
| **Intrinio** | Claims 100,000 globally-traded securities, but fundamentals product line reads as US-primary; international is offered as a **custom "data sourcing service"**, not a self-serve API tier | US Fundamentals priced separately ($9,600/yr) | Not demonstrated as IFRS-capable | $250/mo–$2,400/yr for various APIs; custom quote for international | Enterprise-style custom contracts | **Not a self-serve fit; possible future enterprise option, not now** |
| **Polygon.io** (rebranded "Massive" Oct 2025) | Marketing emphasizes forex/crypto/US-equities breadth; global **stock exchange** coverage is not clearly established in available material | Primarily US-focused | Not demonstrated | $79–199+/mo for production tiers | Standard commercial | **Not a fit for international requirement — strong for US-only if ever needed as an AV replacement** |
| **SEC EDGAR** (existing) | US SEC registrants only, by design | US-GAAP 10-K, deep and free | US GAAP / 10-K only (20-F unsupported today) | Free, fair-access policy | Public data, no license cost | **Keep — extend to also read 20-F/6-K filings (still free, same source, IFRS-tagged facts instead of us-gaap)** |
| **Companies House (UK)** | UK company registry | Raw iXBRL bulk-file accounts data; **no clean structured JSON API** for financial facts (confirmed via research) — the Document API exists but doesn't scale past low-rate individual lookups, and full structured extraction requires third-party parsing of bulk iXBRL/XBRL files | UK GAAP/IFRS as filed, unparsed | Free bulk downloads; Document API rate-limited | Public data | **Not a drop-in provider — would require building an iXBRL parser, a materially bigger lift than any API-based provider. Deprioritized versus a commercial UK-coverage provider (Twelve Data/FMP) for near-term coverage** |
| **Alpha Vantage** (existing) | Nominal global quote coverage, unconfirmed depth for local-exchange names | Company OVERVIEW only; no full financial-statement extraction attempted in current code | US-GAAP-flavored where present | **Free tier: 25 requests/day — the confirmed, currently-live bottleneck** | Standard commercial | **Retain only as a secondary/quote-check source once a broader provider is added; free-tier quota alone makes it unfit as Atlas's primary anything today** |

---

## Deliverable 5 — Recommended Provider Roles (Phase 5)

Rather than one provider owning everything, split responsibility by data
type — matching the existing Protocol split (`BusinessDataProvider` /
`HistoricalMarketDataProvider` / `CompanyProfileProvider`), which already
anticipates multi-provider composition:

| Responsibility | Recommended owner | Fallback |
|---|---|---|
| Security identification (ticker/exchange resolution) | Twelve Data (broadest confirmed exchange list) | Alpha Vantage (existing, narrower) |
| Market prices (current quote) | Twelve Data | Alpha Vantage |
| Historical prices | Twelve Data | Alpha Vantage (existing MONTHLY_ADJUSTED) |
| Company profile (name, sector, currency, fiscal year end) | Twelve Data | Alpha Vantage (existing OVERVIEW) |
| Financial statements — US GAAP / 10-K | **SEC EDGAR (keep, unchanged)** | Twelve Data fundamentals |
| Financial statements — IFRS / 20-F / non-US | **New: extend SEC EDGAR provider to also parse 20-F filings' IFRS-tagged XBRL** (same free source, same CIK resolution, additive extractor) for SEC-registered foreign issuers; **Twelve Data fundamentals** for local-exchange-only names with no SEC presence at all | — |
| Corporate actions | Twelve Data (has a dedicated corporate-actions data category per their documentation) | — |
| Currency | Twelve Data / provider-native `CompanyProfile.currency` field (already modeled) | — |
| Exchange metadata | Twelve Data | — |

**Why SEC EDGAR stays for US and gets extended, not replaced:** it is free,
already deeply integrated (extraction, mapping to `BusinessFactKind`,
tested), and its only real gap is the 10-K-only/US-GAAP-only scope — a
targeted extension (read 20-F too), not a replacement.

**Why Alpha Vantage moves from primary to fallback:** the confirmed 25/day
quota makes it structurally unfit as *the* market-data provider for a
platform meant to enrich many companies; it remains useful as a
low-cost cross-check once request volume is naturally low (e.g. verifying
one company at a time in a UI-triggered enrichment flow), not for the bulk
refresh case.

---

## Deliverable 6 — Failure Classification Taxonomy (Phase 9)

Every ingestion attempt must resolve to exactly one of these classes —
extending the ad hoc failure modes already observed in Sprint F into a
deterministic set every provider's errors get mapped onto:

| Class | Meaning | Example observed this session |
|---|---|---|
| `UNKNOWN_SECURITY` | No provider could resolve the identifier to a real company at all | (would apply to a genuinely nonexistent ticker; not observed for any real company tested) |
| `UNSUPPORTED_EXCHANGE` | Identifier resolves, but no configured provider covers that exchange | Volvo B / Atlas Copco (`.ST`) against SEC EDGAR |
| `UNSUPPORTED_REPORTING_STANDARD` | Identifier and filer resolve, but the filing type/standard has no extractor | ASML, TSM — 20-F/IFRS against a 10-K/US-GAAP-only extractor (new class, did not exist as a named concept before Sprint F/G) |
| `PROVIDER_UNAVAILABLE` | Transient failure (network, 5xx, timeout) | Not observed this session, but must be distinguished from quota exhaustion below |
| `RATE_LIMITED` | Provider reachable but refusing due to quota/rate | Alpha Vantage 25/day cap, confirmed live |
| `FINANCIAL_STATEMENTS_UNAVAILABLE` | Company identified, but no statement data exists at the source for the requested period | e.g. a newly-listed company with no filed 10-K yet |
| `CORPORATE_ACTION_UNAVAILABLE` | Requested corporate-action data doesn't exist at the source | Not yet exercised — no provider returns this data category today |
| `NORMALIZATION_FAILURE` | Raw document fetched successfully but fails `normalize()`'s structural checks | Not observed this session |
| `PARSER_FAILURE` | Provider-specific extraction logic (XBRL tag mapping, JSON schema) throws | Not observed this session |
| `INTERNAL_PERSISTENCE_FAILURE` | `BusinessRecord` repository write fails | Not observed this session |

Two classes above (`UNSUPPORTED_REPORTING_STANDARD`, and the
`RATE_LIMITED`/`PROVIDER_UNAVAILABLE` split) don't exist as distinct
concepts in the current `RefreshSummary.provider_errors` shape — today
every provider failure collapses to a bare `{provider_id, error}` string
pair. Recommendation: extend `ProviderError` with a `failure_class` field
using this taxonomy, so downstream reporting (and any future "why is this
company incomplete" UI) can distinguish "we don't support this market yet"
from "try again later" from "this company genuinely has no data" — three
very different investor-facing messages that a raw error string can't
convey. This is the one piece of this sprint's recommendations that touches
existing data shapes; everything else is additive.

---

## Deliverable 5b — Canonical Company Identity (Phase 7)

No canonical identity model exists today (confirmed via full read of
`normalization.py`). Evaluated identifier types:

| Identifier | Scope | Verdict |
|---|---|---|
| Ticker alone | Ambiguous across exchanges (e.g. "VOLV" resolves differently per market) | Not sufficient alone |
| Ticker + Exchange (MIC code) | Unambiguous, human-readable, matches how every provider evaluated above actually indexes symbols (Twelve Data's own exchange pages are keyed this way) | **Recommended as the primary working key** |
| ISIN | Globally unique, exchange-independent, the standard cross-border security identifier | **Recommended as the canonical stored identity** — it's what lets Atlas recognize "this is the same company" across providers that use different ticker conventions for the same security |
| CUSIP / SEDOL | US/UK-centric legacy identifiers, narrower than ISIN | Not needed given ISIN coverage |
| FIGI | Open, granular (share-class level), increasingly used by data vendors | Worth capturing when providers expose it, but not required as the primary key given cost/complexity of a dedicated FIGI-mapping integration |
| CIK | SEC-specific, only exists for SEC registrants | Keep as a provider-local field on the SEC EDGAR provider, not promoted to canonical |
| Internal Atlas ID | Atlas's own primary key, already exists implicitly wherever `Company`/`Case` records are stored | **Keep as the actual database primary key**; ISIN + Ticker/Exchange become identity *attributes* on that record, not replacements for it |

**Recommended model:** an internal `CompanyIdentity` value object with
`atlas_id` (existing internal PK), `isin` (canonical cross-provider key,
nullable until resolved), and a list of `(ticker, exchange_mic)` pairs (one
per market the company trades on — relevant for dual-listed names like
Volvo B, which may trade on both its home exchange and via an ADR). Provider
adapters resolve *into* this model rather than each provider inventing its
own resolution silently — this is the concrete fix for the "two providers
believe they matched the same company and are both wrong, undetected" risk
named in Deliverable 1.

---

## Deliverable 5c — Fallback Strategy (Phase 6)

Deterministic, per the brief's own template (*"Provider A fails → try
Provider B → normalize → retry → record failure reason → continue where
possible... Never silently fail."*):

```
For each data responsibility (identification, quote, history, profile, statements):
  1. Call the primary provider for that responsibility.
  2. On success → normalize → persist → done.
  3. On failure → classify into the Deliverable 6 taxonomy.
     - If RATE_LIMITED or PROVIDER_UNAVAILABLE → try the configured fallback
       provider for that same responsibility, if one exists.
     - If UNSUPPORTED_EXCHANGE / UNSUPPORTED_REPORTING_STANDARD /
       UNKNOWN_SECURITY → do NOT retry the same provider; these are not
       transient. Try the fallback provider only if it has a documented
       chance of covering that gap (e.g. Twelve Data as fallback for a
       Nordic name SEC can't reach at all — a real chance; retrying SEC
       EDGAR itself for the same company — no chance).
  4. Record every attempt (provider, failure_class, timestamp) — this is
     what `RefreshSummary.provider_errors` already does structurally; it
     just needs the richer failure_class from Deliverable 6.
  5. A failure in one responsibility (e.g. no corporate-action data) never
     blocks the others — this invariant already exists in
     refresh_company_data today and should be preserved exactly.
  6. The case-composition layer (already proven, per Sprint F, to degrade
     every evaluator to a named INSUFFICIENT_* state rather than crash)
     continues to be the thing that turns "some data missing" into an
     honest partial case — the fallback strategy's job is only to minimize
     how often that honest-partial state is reached, not to hide it.
```

This requires no new architectural concept — `refresh_company_data`
already tries every configured provider independently per responsibility;
what's new is (a) more providers configured per responsibility so a real
fallback exists, and (b) the failure_class-aware retry logic above replacing
today's "try everything, log whatever failed" flat behavior.

---

## Deliverable 8 — Coverage Targets (Phase 8)

| Universe | Target | Rationale |
|---|---|---|
| S&P 500 | 95%+ full coverage (ID + prices + statements) | Already close to this today via SEC EDGAR + Alpha Vantage for the US; achievable once Alpha Vantage's quota is no longer the primary blocker |
| OMX Stockholm Large Cap | 95%+ full coverage | **Currently ~0%** for local-exchange-only names (Sprint F: Volvo B, Atlas Copco both fail); requires Twelve Data (or equivalent) as the financial-statement source, since SEC EDGAR structurally cannot serve this population |
| Euro Stoxx 50 | 90%+ (mix of SEC-registered 20-F filers and local-only names) | Requires both the 20-F extension (for names like ASML) and the Twelve Data fallback (for names with no SEC presence) |
| Major ADRs (Nasdaq/NYSE-listed foreign issuers) | 95%+ for identification, 90%+ for statements once 20-F support ships | Identification already works today (ASML/TSM/SAP/Sony all resolve); statements are the gap this sprint's #1 recommendation closes |

These targets are only reachable in the order laid out in the roadmap below
— coverage-target claims without the underlying provider/extension work
would just restate the brief's goal, not evidence a path to it.

---

## Deliverable 5d / 7 — Final Recommended Architecture (Phase 10)

1. **Keep the existing Protocol-based provider architecture unchanged.**
   It already supports everything this design needs — no new abstraction.
2. **Add Twelve Data as a new `BusinessDataProvider` +
   `HistoricalMarketDataProvider` + `CompanyProfileProvider` implementation**,
   configured as primary for all non-US-GAAP-statement responsibilities and
   as the financial-statement source for companies with no SEC presence.
3. **Extend `SecEdgarFundamentalsProvider` to also parse Form 20-F filings**,
   mapping IFRS-tagged facts to the same `BusinessFactKind` enum used for
   `us-gaap:*` facts today — additive, same free data source, same CIK
   resolution path, no new provider needed for this specific gap.
4. **Demote Alpha Vantage to secondary/fallback** for quote and profile
   data only, given its confirmed quota ceiling.
5. **Introduce `CompanyIdentity`** (Deliverable 5b) as the reconciliation
   point between providers, populated opportunistically (ISIN captured
   wherever a provider exposes it; ticker+exchange always captured).
6. **Extend `ProviderError` with `failure_class`** (Deliverable 6), and
   implement the fallback sequencing in Deliverable 5c inside
   `refresh_company_data`.
7. **Do not build a Companies House / bulk-iXBRL parser this cycle** — the
   lift is disproportionate to the near-term coverage gain when a
   commercial provider (Twelve Data) already claims UK coverage through a
   normal API call.

**Expected coverage after implementation:** US stays at current (already
strong) coverage; Sweden/Norway/Denmark/Finland move from ~0% to whatever
Twelve Data's confirmed Nordic exchange coverage (Stockholm, Oslo,
Copenhagen, Helsinki — all confirmed present) actually delivers once
integrated and live-tested; Netherlands/Taiwan/Japan/Germany move from
identification-only to full coverage via the 20-F extension for
SEC-registered names, with local-exchange-only names in those markets
picked up by Twelve Data. UK, Switzerland, France, Canada, South Korea,
Australia move from no confirmed coverage to Twelve Data's claimed coverage,
pending live verification (see Migration Roadmap step 2).

**Operational risks:**
- Twelve Data's exact fundamentals depth/IFRS-normalization behavior is
  based on documentation and one exchange-page fetch, not a live API test
  with a real key — the highest-priority unknown to close before committing
  further.
- Twelve Data's Oslo (and likely other Nordic) coverage requires a
  **Pro+/Venture+** tier, not their entry $29/mo plan — actual cost for the
  full target market list needs a direct quote before budgeting.
- The 20-F/IFRS extraction adds real parsing complexity (IFRS taxonomy
  differs from US-GAAP XBRL tags) — should be scoped as its own
  implementation slice, not bundled into "just add Twelve Data."

**Cost implications:** Twelve Data's higher tiers (needed for the full
target-market list) were not fully priced in this research pass — this is
the most important open item before this design becomes a committed budget
line, and should be resolved via a direct sales/pricing conversation before
implementation starts.

---

## Deliverable 6b / 7b — Migration Roadmap & Prioritized Implementation Plan

Ordered by expected coverage impact per unit of architectural complexity,
per the brief's own success criterion:

| Priority | Action | Expected impact | Complexity |
|---|---|---|---|
| **1** | Get a live Twelve Data trial/API key and re-run Sprint F's exact test universe (Volvo B, Atlas Copco, ASML, TSM, SAP, LVMH, Siemens, Toyota, Sony) against it directly — verify the documentation-based claims in this report with real calls before committing budget | De-risks the entire recommendation | Low — a probe script, same pattern as Sprint F/G's existing scratchpad probes |
| **2** | Extend `SecEdgarFundamentalsProvider` to parse Form 20-F / IFRS-tagged facts | Immediately fixes ASML/TSM/Novo Nordisk/Sony-class companies (SEC-registered, wrong form type today) at **zero new vendor cost** | Medium — new extraction logic, same provider, same data source |
| **3** | Integrate Twelve Data as a new provider (all three Protocol roles) for markets with no SEC presence at all (Nordics, Switzerland, most of local-exchange UK/Australia/Korea) | Fixes the largest confirmed gap (Sweden: 0/6 → target 95%+) | Medium — new provider implementation, following the existing Protocol contract exactly |
| **4** | Add `failure_class` to `ProviderError` and implement the fallback sequencing from Deliverable 5c | Turns today's flat "it failed" signal into an actionable, investor-honest reason — improves trust even before coverage numbers move | Low-medium — additive field + orchestration logic in `refresh_company_data` |
| **5** | Introduce `CompanyIdentity` (ISIN + ticker/exchange pairs) as the cross-provider reconciliation point | Prevents silent misidentification as more providers are added; not urgent with 2 providers, becomes necessary at 3+ | Medium — new domain object, threading through provider adapters |
| **6** | Demote Alpha Vantage to fallback-only role in provider configuration | Removes the confirmed quota bottleneck from the critical path | Low — configuration/ordering change, no new code |
| **7** | Revisit Companies House / bulk-iXBRL parsing, and Intrinio/FMP as possible second-source fundamentals providers | Only worth it if Twelve Data's live-verified UK/broader coverage (step 1) turns out weaker than documented | Deferred — not scheduled unless step 1 reveals a gap |

Steps 1–3 alone directly address this sprint's own success criteria: they
name which providers to add (Twelve Data), which to keep (SEC EDGAR,
extended), which to demote (Alpha Vantage), and the concrete mechanism
(20-F extraction + a new international provider) for reaching high
coverage without touching analysis quality — every evaluator downstream
already handles partial data honestly, per Sprint F's own finding, so nothing
in the analysis engine needs to change for any of this to work.

---

## Summary — Answering the Sprint's Own Success Criteria

- **Which providers Atlas should use:** SEC EDGAR (extended for 20-F),
  Twelve Data (new, primary for non-US market data + fundamentals),
  Alpha Vantage (retained, demoted to fallback).
- **Which providers should be replaced:** None outright — Alpha Vantage is
  demoted, not removed; it remains useful as a secondary quote source at low
  volume.
- **Which should be retained:** SEC EDGAR, unchanged in scope for US
  10-K/GAAP, extended for 20-F/IFRS.
- **How Atlas should support global listed companies:** Twelve Data as the
  primary non-US data source, layered under the existing Protocol
  architecture with no orchestration changes required.
- **How Atlas reaches high coverage without compromising analysis quality:**
  by adding providers at the data-acquisition layer only — every downstream
  evaluator already degrades honestly to a named insufficient-data state
  (proven in Sprint F), so more coverage flows straight through to more real
  cases without any analysis-engine change.
- **What implementation path gives the greatest coverage increase for the
  least architectural complexity:** the 20-F extension (priority 2) is the
  single cheapest, highest-confidence win (zero new vendor, fixes a
  confirmed multi-company gap); the Twelve Data integration (priority 3) is
  the largest win but carries real unverified assumptions that priority 1's
  live-key trial exists specifically to resolve before committing further
  budget or engineering time.
