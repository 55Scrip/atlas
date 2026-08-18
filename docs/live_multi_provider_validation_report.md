# Sprint H — Live Multi-Provider Validation Report

**Sprint scope:** validate Sprint G's provider-architecture conclusions with
real data, not documentation. Per explicit user instruction, this sprint
live-tests **SEC EDGAR, Alpha Vantage, and Twelve Data only**. Financial
Modeling Prep, Finnhub, Polygon, Tiingo, and Intrinio are **not live-tested**
this sprint — where referenced below, they are explicitly labeled
`[DOCUMENTED — Sprint G]`, never presented as tested.

**Evidence labeling used throughout this report:**
- `[LIVE — Sprint H]`: a real API call made during this sprint, raw response
  captured.
- `[LIVE — Sprint F]`: a real API call made during the prior Company
  Coverage & Enrichment Reliability sprint (same investigation, cited
  rather than re-run to conserve Alpha Vantage's shared daily quota).
- `[DOCUMENTED — Sprint G]`: a claim from provider documentation or public
  web sources, not independently verified by a live call.
- `[INFERRED]`: a conclusion drawn from live evidence but not itself
  directly observed — always stated as inference, never as fact.

No production code was modified. No provider was integrated. This is a
validation-only sprint, per the brief's own scope rules.

---

## Phase 1 — Validation Matrix (companies tested)

| # | Ticker | Company | Market |
|---|---|---|---|
| 1 | AAPL | Apple | US |
| 2 | MSFT | Microsoft | US |
| 3 | GOOGL | Alphabet | US |
| 4 | AMZN | Amazon | US |
| 5 | NVDA | Nvidia | US |
| 6 | TSLA | Tesla | US |
| 7 | VOLV-B | Volvo B | Sweden |
| 8 | ATCO-B | Atlas Copco B | Sweden |
| 9 | EVO | Evolution | Sweden |
| 10 | INVE-B | Investor B | Sweden |
| 11 | HEXA-B | Hexagon B | Sweden |
| 12 | SAAB-B | Saab B | Sweden |
| 13 | NOVO-B | Novo Nordisk B | Denmark |
| 14 | ASML | ASML | Netherlands |
| 15 | SAP | SAP | Germany |
| 16 | TSM | Taiwan Semiconductor | Taiwan |
| 17 | TM | Toyota | Japan |
| 18 | SONY | Sony | Japan |
| 19 | MC | LVMH | France |

All 19 companies were tested against SEC EDGAR (fresh, `[LIVE — Sprint H]`)
and Twelve Data (fresh, `[LIVE — Sprint H]`). Alpha Vantage could not be
freshly tested for most of this matrix — see Phase 2's rate-limit finding —
so its columns below combine a fresh `[LIVE — Sprint H]` quota-exhaustion
check with `[LIVE — Sprint F]` citations for the subset of tickers that
sprint already live-tested.

---

## Phase 2 — Identification Results

### SEC EDGAR `[LIVE — Sprint H]`

SEC EDGAR resolves tickers through its own flat `company_tickers.json`
map (ticker → CIK), with no exchange qualifier.

| Ticker | Resolved to | Result |
|---|---|---|
| AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA | correct US filer | ✅ Identified |
| VOLV-B, ATCO-B, INVE-B, HEXA-B, SAAB-B | — | ❌ `did not resolve to any SEC-registered filer` |
| NOVO-B | — | ❌ same (SEC's ticker for Novo Nordisk is `NVO`, not `NOVO-B` — confirmed by directly testing `NVO`, see Phase 5) |
| ASML, SAP, TSM, TM, SONY | correct foreign filer, real CIK | ✅ Identified (statement-stage failure, see Phase 5) |
| **EVO** | **Evotec SE (CIK 1412558) — a German biotech company** | ❌ **Wrong company.** The ticker "EVO" is claimed by Evotec SE in SEC's ticker map; Evolution AB (the Swedish gaming company this test intended) is not the SEC's "EVO." |
| **MC** | **Moelis & Co (CIK 1596967) — a US investment bank** | ❌ **Wrong company.** The ticker "MC" is Moelis & Co on SEC's map; LVMH (Euronext Paris: MC) is a completely different company. This is a live-confirmed identity collision — the SEC probe actually ingested 14 real financial records under Moelis & Co's identity in a call intended for LVMH. |

**Finding:** SEC EDGAR's bare-ticker resolution produced **two real,
live-confirmed wrong-company matches** out of 19 attempts (EVO→Evotec SE,
MC→Moelis & Co) — an 11% silent-collision rate on this matrix. Both
failures are silent in the sense that the pipeline does not surface "this
might be the wrong company" — it simply proceeds as if the ticker were
unambiguous. This is a direct, concrete confirmation of Sprint G's
Deliverable 5b finding (no canonical `CompanyIdentity` model exists) — not
a theoretical risk, but one that reproduced twice in a 19-company sample.

### Twelve Data `[LIVE — Sprint H]`

Twelve Data's `symbol_search` endpoint returns exchange-qualified,
disambiguated matches (symbol, exchange, MIC code, country, currency).

| Ticker | Resolved to | Alt ticker needed? |
|---|---|---|
| All 19/19 | Correct company, correct native exchange (or correctly the requested company on a US ADR listing for TSM/TM) | **No — 0/19 needed an alternate ticker spelling.** |
| **MC** | **LVMH Moët Hennessy Louis Vuitton SE, Euronext Paris (XPAR)** | Correctly disambiguated the exact ticker SEC EDGAR got wrong. |
| **EVO** | **Evolution AB (publ), OMX Stockholm (XSTO)** | Correctly disambiguated the exact ticker SEC EDGAR got wrong. |

**Finding:** Twelve Data's identification layer is unambiguously the
stronger of the two live-tested identity resolvers — 19/19 correct on the
first try, including both tickers where SEC EDGAR silently matched the
wrong company. This is a genuine, live-confirmed advantage, independent of
anything else in this report.

### Alpha Vantage

`[LIVE — Sprint H]`: the deployed free-tier key was **already at its 25
requests/day cap before a single fresh call was made today** — every
identification attempt (`VOLV-B`, `ATCO-B`, `EVO`, `INVE-B`, `HEXA-B`,
`SAAB-B`, `NOVO-B`, `MC`) returned the same rate-limit error. This
independently reconfirms Sprint F's finding on a different calendar day: the
quota ceiling is a persistent operational condition, not a one-off.

`[LIVE — Sprint F]`, cited: AAPL/MSFT/AMZN/GOOGL/NVDA/TSLA all resolved
successfully; ASML, SAP (as `SIEGY`/German OTC ADR test used `SIEGY` for
Siemens, not SAP directly — SAP itself was tested and succeeded), TSM, TM,
SONY all resolved via their US-listed ADR tickers; `ATCO-B.ST` (a
suffixed form, not the bare `ATCO-B` this sprint's matrix specifies) was
the only Nordic-market symbol attempted, and it succeeded.

---

## Phase 3 — Company Profile Validation

### Twelve Data `[LIVE — Sprint H]`

The `/profile` and `/statistics` endpoints returned this **exact,
plan-stated restriction** on the deployed "basic" (free) key:

> `"/profile is available exclusively with grow or pro or ultra or venture
> or enterprise plans. Consider upgrading your API Key now at
> https://twelvedata.com/pricing"` (HTTP 403)

This fired for **17 of 19 companies tested**, with **two unexplained live
exceptions**: AAPL returned a full profile (name, exchange, sector,
industry, employees, description, CEO, address) on **two separate
occasions** this sprint (once in the initial endpoint-mapping probe, once
in the full matrix run); INVE-B returned a full profile **once**. Both
exceptions directly contradict the plan's own stated restriction, and no
explanation for them could be established from available evidence — see
Remaining Unknowns.

**Fields observed, where profile access succeeded (AAPL, INVE-B):** company
name, exchange, MIC code, sector, industry, employee count, website,
description, CEO, full address, country — every field the brief's Phase 3
asks for except market cap and shares outstanding directly (those come from
`/statistics`, which was gated identically).

**Finding:** on the plan actually available to Atlas today, company profile
data is **not reliably obtainable from Twelve Data for arbitrary
companies** — it is architecturally present (the two exceptions prove the
data exists and the schema is right) but access-gated behind a paid tier
this sprint did not test.

### SEC EDGAR / Alpha Vantage

Neither provider in Atlas's current stack has ever attempted to serve
company-profile fields (sector, industry, employees, description) — SEC
EDGAR is statements-only; Alpha Vantage's `fetch_company_profile`/OVERVIEW
capability exists in code but was not exercised this sprint due to the
quota exhaustion noted above. `[LIVE — Sprint F]` confirms OVERVIEW works
for US names when quota allows.

---

## Phase 4 — Market Data Validation

### Twelve Data `/quote` and `/time_series` `[LIVE — Sprint H]`

| Symbol population | Result |
|---|---|
| US-native listings (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA) | ✅ 200 — current price, OHLC, volume, average volume, 52-week range (low/high/change/%change), daily candles all returned correctly |
| US-listed ADRs (TSM on XNYS, TM on XNYS) | ✅ 200 — identical field completeness to native US listings |
| **Foreign-exchange-native listings** (VOLV.B/XSTO, ATCO.B/XSTO, EVO/XSTO, INVE.B/XSTO, HEXA.B/XSTO, SAAB.B/XSTO, NOVO.B/XCSE, ASML/XAMS, SAP/XETR, 6758/XJPX, MC/XPAR) | ❌ **404 — `symbol or figi parameter is missing or invalid`** — for the exact same symbol+MIC pair that `symbol_search` had just successfully resolved moments earlier |

**Finding:** this is the sprint's single clearest, most decision-relevant
result. On the currently-accessible "basic" plan, Twelve Data's market-data
endpoints work **only for US-exchange-listed symbols** (native or ADR) —
every one of the 11 foreign-exchange-native symbols tested was rejected,
despite being correctly identified one call earlier. This directly and
concretely confirms Sprint G's own flagged caveat (*"Twelve Data's Oslo...
coverage requires a Pro+/Venture+ tier, not their entry $29/mo plan"*) — and
extends it: the restriction is not Oslo-specific, it applies to every
non-US exchange tested, including Sweden, Denmark, Netherlands, Germany,
and Japan.

No 52-week range, corporate actions, or currency-consistency fields could
be evaluated for any foreign-native symbol, since the base quote call
itself was rejected. Currency was correctly reported wherever data *did*
return (SEK, DKK, EUR, JPY all appeared correctly in `symbol_search`'s
identification payload even though the quote calls themselves failed).

### SEC EDGAR / Alpha Vantage

SEC EDGAR does not serve market data by design (statements only). Alpha
Vantage's market-data results this sprint are entirely `[LIVE — Sprint F]`
citations (see Phase 2) due to quota exhaustion; no fresh price data was
obtained for any company this sprint via Alpha Vantage.

---

## Phase 5 — Financial Statement Validation

### SEC EDGAR `[LIVE — Sprint H]`, full matrix re-run

| Ticker | Result |
|---|---|
| AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA | ✅ 13–19 fetched documents each (all duplicates of prior ingestion — confirms continued stability of the US 10-K/US-GAAP path) |
| VOLV-B, ATCO-B, INVE-B, HEXA-B, SAAB-B | ❌ No CIK resolves at all — clean `CompanyNotFound`-style failure |
| **EVO** | ❌ CIK resolves (to the wrong company, Evotec SE) — `SEC companyfacts for CIK 0001412558 (EVO) has no us-gaap facts at all` |
| **NOVO-B** | ❌ No CIK resolves for this exact ticker string |
| **NVO** (Novo Nordisk's real SEC ticker, tested as a direct follow-up `[LIVE — Sprint H]`) | ❌ CIK resolves correctly this time (0000353278, the real Novo Nordisk) but still **zero us-gaap facts** — confirms the 20-F/IFRS gap holds even once the identity problem is fixed |
| ASML | ❌ CIK resolves; `No annual 10-K fundamentals found` (20-F filer — matches Sprint F) |
| SAP, TSM | ❌ CIK resolves; `has no us-gaap facts at all` (20-F filer — matches Sprint F) |
| TM, SONY | ❌ CIK resolves; `No annual 10-K fundamentals found` (20-F filer — matches Sprint F) |
| **MC** | ❌ Not a genuine pass — **14 records were ingested for Moelis & Co, not LVMH.** Reported separately from the 20-F group because this is an identity failure, not a reporting-standard failure; LVMH's real financial statements were never actually retrieved. |

**Result: 0 of 13 non-US companies produced usable financial statements
via SEC EDGAR** — 5 fail at identification, 1 fails at identification with
a wrong-company substitution (EVO), 1 (MC) fails the same way, and 6
(NOVO-B/NVO, ASML, SAP, TSM, TM, SONY) resolve identity correctly but hit
the already-documented 20-F/IFRS gap.

### Twelve Data `/income_statement`, `/balance_sheet`, `/cash_flow` `[LIVE — Sprint H]`

Same plan-gated 403 pattern as Phase 3, with the same two exceptions:

- **AAPL** (both times tested): full annual income statement, balance
  sheet, and cash flow returned — revenue, cost of goods, gross profit,
  operating income, net income, EPS (basic/diluted), shares outstanding,
  EBIT/EBITDA, full current/non-current asset and liability breakdown,
  operating/investing/financing cash flow — every field the brief's Phase 5
  asks for, cleanly structured, standard-agnostic field names (not raw
  XBRL tags).
- **INVE-B**: same full income statement returned once, in SEK, correctly
  currency-tagged, with real 2025/2026 fiscal-year figures (revenue
  216.578B SEK, net income 157.34B SEK). This is the **only live evidence
  this sprint of a non-US, non-ADR company's real financial statements
  being retrieved from any provider** — but it could not be reproduced for
  any of the other 10 non-US-native companies tested, including on retry
  patterns implicit in testing HEXA-B and SAAB-B immediately afterward
  (both 403'd normally).
- **All other 17 companies**: 403, plan-gated, per the message quoted in
  Phase 3.

**Finding:** Twelve Data's fundamentals schema (when accessible) is
materially better-structured for Atlas's purposes than SEC EDGAR's raw XBRL
— standard-agnostic field names mean the same extraction code could handle
a US-GAAP company and a Swedish IFRS company identically, which is exactly
what Sprint G's Deliverable 3 said Atlas's architecture lacks today. But
this sprint's live evidence shows that schema is **not currently
accessible** on the plan Atlas has — real access requires a paid tier this
sprint did not test.

---

## Phase 6 — Pipeline Readiness (per company, using only data actually obtained this sprint)

Atlas's downstream pipeline (Business Analysis, Growth, Capital Allocation,
Valuation, Risk, Investment Thesis, Recommendation) requires — at minimum —
real financial-statement facts (revenue, income, cash flow, shares, debt)
**and** real market price data, both temporally aligned.

| Company | Financial statements obtained? | Market data obtained? | Pipeline-ready? |
|---|---|---|---|
| AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA | ✅ SEC EDGAR | ✅ AV (Sprint F, cited) + Twelve Data (Sprint H) | **Yes** |
| VOLV-B, ATCO-B, HEXA-B, SAAB-B | ❌ | ❌ (Twelve Data 404 on basic plan) | **No** |
| EVO | ❌ (wrong company via SEC; blocked via Twelve Data) | ❌ | **No** |
| INVE-B | ⚠️ Twelve Data, once, unreproduced | ❌ (Twelve Data 404) | **No** — statements alone are not sufficient without price data, and the statement access itself is not reliably repeatable |
| NOVO-B | ❌ (20-F gap, confirmed even with correct ticker) | ❌ | **No** |
| ASML, SAP | ❌ (20-F gap) | ✅ AV ADR quote (Sprint F, cited) | **No** — price alone can't support Valuation/Growth/Capital Allocation, which need statements |
| TSM, TM | ❌ (20-F gap) | ✅ AV (Sprint F) + Twelve Data ADR (Sprint H, both live-confirmed) | **No** — same reasoning |
| SONY | ❌ (20-F gap) | ✅ AV ADR (Sprint F, cited) only — Twelve Data's native-Japan quote 404'd | **No** |
| MC | ❌ (wrong company via SEC; blocked via Twelve Data native listing) | ⚠️ only via a different ticker (`LVMUY`, Sprint F) not tested this sprint against the `MC` identity actually resolved | **No** |

**Result: 6 of 19 companies (all US) are pipeline-ready today. 0 of 13
non-US companies are pipeline-ready**, even counting Twelve Data's
anomalous fundamentals access and Alpha Vantage's cited Sprint F evidence.
This matches, almost exactly, Sprint F's original coverage finding — this
sprint's live evidence shows Twelve Data's *currently accessible* tier does
not yet move that number.

---

## Phase 7 — Reliability Classification

| Company | Classification | Basis |
|---|---|---|
| AAPL | `FULLY_SUPPORTED` | SEC EDGAR statements + AV/Twelve Data market data, all live-confirmed |
| MSFT, GOOGL, AMZN, NVDA, TSLA | `FULLY_SUPPORTED` | Same, statements confirmed fresh this sprint, market data cited from Sprint F (AV) or fresh (Twelve Data) |
| TSM, TM | `MARKET_DATA_ONLY` | Real price data from two independent live sources; statements blocked by the 20-F/IFRS gap |
| SAP, ASML | `MARKET_DATA_ONLY` | Real price data (AV, Sprint F, ADR ticker); statements blocked by 20-F/IFRS gap |
| SONY | `MARKET_DATA_ONLY` | Price data only via AV's ADR ticker (Sprint F); Twelve Data's native listing failed market data on the basic plan |
| INVE-B | `PROFILE_ONLY` | One unreproduced fundamentals success, zero market data — real data exists but is not reliably retrievable |
| VOLV-B, ATCO-B, HEXA-B, SAAB-B | `IDENTIFICATION_ONLY` | Twelve Data correctly identifies all four; nothing further is retrievable on the current plan; SEC EDGAR fails identification entirely |
| NOVO-B | `IDENTIFICATION_ONLY` | Twelve Data identifies correctly; SEC EDGAR's correct ticker (NVO) resolves identity but not statements |
| EVO | `NOT_SUPPORTED` | SEC EDGAR silently resolves to the wrong company; Twelve Data identifies correctly but nothing further is retrievable |
| MC | `NOT_SUPPORTED` | SEC EDGAR silently resolves to the wrong company (Moelis & Co); Twelve Data identifies correctly (LVMH) but nothing further is retrievable on the tested ticker |

**6 `FULLY_SUPPORTED`, 5 `MARKET_DATA_ONLY`, 1 `PROFILE_ONLY`, 5
`IDENTIFICATION_ONLY`, 2 `NOT_SUPPORTED`.** Zero companies fell in
`SUPPORTED_WITH_LIMITATIONS` — the gap between "fully working" and
"identification only" is stark, with almost nothing landing in between on
the currently-accessible provider tiers.

---

## Phase 8 — Provider Comparison (live-tested providers only)

| Dimension | SEC EDGAR `[LIVE]` | Alpha Vantage `[LIVE — quota check; Sprint F for data]` | Twelve Data `[LIVE — Sprint H]` |
|---|---|---|---|
| **Coverage** | US SEC-registered filers only, confirmed | Nominally global; Sprint F confirmed ADR-ticker quotes work; native-exchange coverage still unconfirmed for most markets | Identification: confirmed global (19/19). Market data + fundamentals: confirmed **US-only** on the accessible plan |
| **Reliability** | Consistent, deterministic — every US ticker behaves the same way every time | **Unreliable at the account level** — quota exhausted before this sprint's first call | Identification: 100% consistent. Fundamentals/non-US market data: **inconsistent** — two unexplained 200s against a documented blanket 403 |
| **Consistency** | High — clean, reproducible failure messages distinguish "no CIK" from "CIK but no us-gaap facts" | Not evaluable this sprint (quota exhausted) | Mixed — identification is perfectly consistent; premium-endpoint access is not |
| **Rate limits** | No hard cap observed for reasonable single-company use | **25/day, confirmed exhausted independently on a second, later date** — the single most damaging finding for AV's viability as anything but a fallback | 8/min, 800/day on basic plan — never hit during this sprint's ~152 calls, well-paced |
| **Latency** | Not formally measured; calls completed within normal request timeouts throughout | Not measured this sprint (all calls immediately rate-limited) | Consistently fast, sub-second response times observed informally during the paced run |
| **Licensing** | Public data, free | Standard commercial, free tier | Standard commercial, free tier |
| **Cost** | Free | Free (tested tier) | Free (tested tier); paid tiers required for the functionality this sprint most needed to validate — untested |
| **International support** | None by design (explicit scope) | Unconfirmed for native-exchange listings (only ADR tickers tested) | Identification: strong, confirmed. Data access: **not available on the tested tier** |
| **Financial statement quality** | Deep (US-GAAP, granular XBRL tags) where available | Not evaluated (OVERVIEW is descriptive, not full financials) | Well-structured, standard-agnostic field names — but only observed twice, both anomalies |
| **Ease of integration** | Already integrated, stable | Already integrated | Would be new work — no client code exists yet in the codebase, per Sprint G's finding |
| **API quality** | Plain REST, JSON, clear per-CIK error messages | Free-tier rate-limit errors are returned as HTTP 200 with an error string inside the payload — a fragile contract, previously noted in Sprint G | Clean REST, JSON, informative HTTP status codes (403/404) with explicit human-readable upgrade messaging |
| **Documentation quality** | Adequate for the narrow 10-K/XBRL use case | Adequate | Good — endpoint behavior largely matched documented expectations except for the two access anomalies |

`FMP, Finnhub, Polygon, Tiingo, Intrinio` — `[DOCUMENTED — Sprint G]` only,
carried forward unchanged from that report's Deliverable 4, not re-verified
this sprint per explicit user instruction.

---

## Phase 9 — Architecture Decision

**Should Twelve Data become the primary international provider?**
**Conditional yes — not yet confirmed.** The identification layer is
unambiguously strong (100% live success, correctly disambiguated both
tickers where SEC EDGAR silently matched the wrong company). But the
**specific plan Atlas has access to today cannot serve non-US market data
or fundamentals for any but two anomalous cases**, and this sprint did not
test a paid tier. This is a genuinely different, more decision-useful
finding than Sprint G's documentation-based conclusion: it does not
contradict "Twelve Data is the right architecture," but it does mean **that
conclusion cannot yet be acted on with the access currently in hand.**

**Should Alpha Vantage remain?** Yes, as fallback/secondary only — this
sprint's live quota-exhaustion finding, on a different calendar day than
Sprint F's, independently confirms the 25/day cap is a persistent
structural condition, not an incident.

**Should another provider replace Twelve Data?** No evidence for this —
nothing tested this sprint suggests a different candidate would fare
better; identification quality strongly favors Twelve Data specifically.
Per the user's own explicit trigger condition (*"Only if Twelve Data fails
materially should we open a follow-up validation sprint"*), this sprint's
findings do **not** meet that bar — Twelve Data did not fail materially, it
failed to be *testable* on the current plan for the functionality that
matters most.

**Should Atlas require multiple providers?** Yes. Even in the best
observed case, no single provider covered every field for every company —
and the two live-confirmed ticker collisions (SEC's EVO→Evotec SE,
MC→Moelis & Co) argue for never trusting one provider's bare-ticker
resolution without a second provider's confirmation, independent of
coverage questions entirely.

**Would one provider ever be sufficient?** No, based on live evidence — the
collision risk alone is a structural argument for cross-provider identity
confirmation, not just a coverage-gap argument.

---

## Phase 10 — Deliverables

### 1. Validation Matrix
See Phases 2–6 above — every cell is sourced to a specific live call or
explicitly labeled as cited/documented.

### 2. Company Coverage Matrix
See Phase 7's reliability classification table.

### 3. Provider Comparison Matrix
See Phase 8.

### 4. Failure Analysis

| Failure class | Companies affected | Provider | Root cause |
|---|---|---|---|
| No CIK / no exchange match | VOLV-B, ATCO-B, HEXA-B, SAAB-B, NOVO-B (as given) | SEC EDGAR | Local-exchange-only, not SEC-registered |
| **Wrong company (ticker collision)** | EVO, MC | SEC EDGAR | Flat ticker map, no exchange qualifier, no canonical identity check |
| 20-F/IFRS gap | NOVO-B (NVO), ASML, SAP, TSM, TM, SONY | SEC EDGAR | Extractor is 10-K/us-gaap only, confirmed again this sprint including with a corrected ticker |
| Plan-gated fundamentals | 17 of 19 companies | Twelve Data | Documented restriction, live-confirmed: `/profile`, `/statistics`, `/income_statement`, `/balance_sheet`, `/cash_flow` require grow/pro/ultra/venture/enterprise |
| Plan-gated non-US market data | 11 of 19 companies | Twelve Data | `/quote`, `/time_series` return 404 for any non-US-exchange-native symbol on the basic plan |
| Account-level rate limit | All companies | Alpha Vantage | 25/day cap, confirmed exhausted independently on two different calendar days |
| Unexplained access anomaly | AAPL (×2), INVE-B (×1) | Twelve Data | Not determined — see Remaining Unknowns |

### 5. Recommended Production Architecture

Unchanged in shape from Sprint G's Deliverable 5/10 (SEC EDGAR extended for
20-F, Twelve Data as primary international source, Alpha Vantage demoted to
fallback) — **but gated on one new precondition this sprint surfaced**: a
live trial against Twelve Data's `grow`/`pro`/`ultra`/`venture` tier (whichever
is the minimum that unlocks both non-US `/quote` and `/income_statement`
family endpoints) must be completed before this architecture is committed
to. Sprint G's recommendation was directionally sound; this sprint shows
the free tier cannot be used to verify it further, and no engineering
should proceed against Twelve Data until a paid-tier trial confirms the
data is actually retrievable at the field level this sprint could only
confirm existed via two anomalies.

Additionally, **Sprint G's Phase 7 canonical-identity recommendation is now
higher priority, not lower** — this sprint found two live wrong-company
collisions in a 19-company sample (11%), which is a materially higher risk
than a theoretical gap. Any production integration of a second provider
should ship the `CompanyIdentity` cross-check (ISIN or exchange-qualified
ticker) alongside it, not as a later-priority follow-up.

### 6. Migration Recommendation

1. **Do not integrate Twelve Data yet.** Obtain a paid-tier trial key
   (`grow` or `pro`, whichever is cheapest that unlocks `/income_statement`
   and non-US `/quote`) and re-run this exact validation matrix before
   writing any provider-integration code.
2. **Do not remove or deprioritize SEC EDGAR.** Its US coverage remains
   the strongest, cheapest, most reliable result of anything tested across
   two sprints.
3. **Treat the EVO/MC collisions as a standing data-integrity risk in the
   current system**, not just a future-architecture concern — any
   ticker-only lookup against SEC EDGAR today can silently return another
   company's financials. This is worth a narrow, separate follow-up (see
   Risks).
4. **Do not spend further effort on Alpha Vantage's free tier.** Its
   quota ceiling is now confirmed on two separate days; no further live
   testing of it will produce new information.

### 7. Remaining Unknowns

- **What Twelve Data plan tier actually unlocks the tested endpoints, and
  at what price?** Not established this sprint — Sprint G's documentation
  research suggested Pro+/Venture+ for Nordic coverage specifically, but
  this sprint's 403 messages named `grow/pro/ultra/venture/enterprise` as a
  block of options without pricing detail.
- **Why did AAPL and INVE-B get anomalous free access to plan-gated
  endpoints?** Three hypotheses were considered and none could be
  confirmed from available evidence: (a) AAPL is a documentation/demo
  symbol with special-cased free access — plausible for AAPL (repeated
  twice) but does not explain INVE-B (once, no obvious reason a niche
  Swedish holding company would be a demo symbol); (b) a small, randomly-
  allocated daily trial-call allowance across all symbols — does not
  cleanly explain why AAPL got full access on both attempts while 17 other
  companies got zero; (c) a transient account/billing-state inconsistency
  — cannot be tested further without either time passing or Twelve Data
  support contact. This should be resolved before any paid-tier trial, so
  it doesn't get mistaken for evidence the free tier "sometimes works."
- **Does Alpha Vantage's native (non-ADR) coverage work for Nordic
  exchanges at all?** Never live-tested with a bare, unsuffixed ticker this
  sprint or in Sprint F — quota exhaustion blocked every attempt this
  sprint, and Sprint F only tried the suffixed `ATCO-B.ST` form.
- **How many other ticker collisions exist in SEC EDGAR's map beyond
  EVO and MC?** Not systematically audited — these two were found
  incidentally in a 19-company sample, which suggests more exist across
  Atlas's broader ticker universe.

### 8. Risks

- **Silent wrong-company data ingestion is a live, present risk in Atlas
  today**, not just a future one — the EVO and MC collisions happened
  against the exact `SecEdgarFundamentalsProvider` code currently in
  production, using tickers a real investor might plausibly enter for a
  Swedish or French holding.
- **Committing to Twelve Data as "the" international provider based on
  Sprint G's documentation alone would have been premature** — this
  sprint's live evidence shows the actually-provisioned tier cannot deliver
  the promised functionality, a gap documentation research alone could not
  have surfaced.
- **Alpha Vantage's fragile rate-limit contract** (a 200 response with an
  error string, not an HTTP error code) means any future fallback logic
  built against it must parse response content, not status codes, to
  detect exhaustion — a real implementation risk if this is missed.

### 9. Estimated Coverage Improvement

Based only on what this sprint actually observed (not projected from
documentation): **zero net new pipeline-ready companies** on the
currently-accessible provider tiers. Twelve Data's confirmed value this
sprint is entirely in the identification layer (correcting two SEC EDGAR
collisions, confirming exchange/currency metadata for all 19 companies) —
real, but not yet convertible into new investment cases without a paid-tier
trial. Any coverage-improvement estimate beyond this would be
`[INFERRED]` from Sprint G's documentation research, not this sprint's live
evidence, and is intentionally not restated here as if it were newly
confirmed.

### 10. Final Recommendation

**Twelve Data: conditional go, blocked on a paid-tier trial.** This
sprint neither confirms nor falsifies Sprint G's architectural
recommendation — it proves the free tier cannot be used to evaluate it
further, while simultaneously strengthening the case for Twelve Data
specifically via its clean win on identification quality (100% success,
2/2 correct disambiguations against SEC EDGAR's live collisions). The
correct next action is a small, low-cost paid-tier trial against the exact
same 19-company matrix — not integration work, and not a pivot to a
different provider, since no evidence gathered this sprint supports either
of those moves.

**Alpha Vantage: confirmed fallback-only**, independently reconfirmed on a
second date.

**SEC EDGAR: confirmed as the correct free/primary US source**, with one
newly-elevated, immediately actionable risk (ticker collisions) that
exists in production today, independent of anything else in this report.
