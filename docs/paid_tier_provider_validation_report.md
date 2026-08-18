# Sprint I — Paid-Tier Provider Validation & Identity Safety Report

**Evidence labeling used throughout:** `[LIVE — Sprint I]` = a real API call
made during this sprint. `[LIVE — Sprint H]` = a real call made in the prior
sprint, cited rather than re-run because the Twelve Data plan is confirmed
unchanged (re-running would reproduce identical results and burn quota for
zero new information — see Phase 2). `[DOCUMENTED]` = provider
documentation/public source, not independently verified by a live call.
`[DESIGN]` = new architecture/rules work this sprint, not itself a live
test result.

---

## Phase 1 — Baseline

- `git status`: `[LIVE — Sprint I]` clean except the same three
  pre-existing untracked local files present since before Sprint H
  (`.env`, `atlas/business_data_providers/alpha_vantage.py.save`,
  `docs/atlas_beta_sprint1_figma_implementation_review.md`). No drift.
- HEAD: `00efa69` (Sprint H's commit) — confirmed.
- API keys: `.env` remains untracked; never staged, printed, or included in
  any committed file this sprint. The Twelve Data key added in Sprint H is
  reused; no key value appears anywhere in this report or its commit.
- Backend baseline tests: `.venv/bin/python -m pytest tests/ -k "provider or
  business_data or sec_edgar or alpha_vantage"` → **405 passed, 2 failed**.
  Both failures (`test_no_provider_imports_added` in
  `test_atlas_product_positioning_v1_sprint272.py` and
  `test_temporary_workspace_data_model_sprint268.py`) assert that
  `atlas/business_data_providers/http.py` contains no `httpx` import — it
  does, and always has for the entire span of this session. **Confirmed
  pre-existing, unrelated to this sprint**: zero production code has been
  touched in Sprints H or I, so this is baseline state, not a regression.
- No push performed this sprint.

---

## Phase 2 — Paid-Tier Access Verification

`[LIVE — Sprint I]`, checked via Twelve Data's own `/api_usage` endpoint at
the start of this sprint and again mid-sprint after the user's response:

```
{"plan_category": "basic", "plan_limit": 8, "plan_daily_limit": 800}
```

**The key remains on the free "basic" plan — no upgrade has been applied.**
This was flagged to the user before proceeding; the user's guidance was to
continue, following the brief's own explicit instruction to *"treat the
restriction itself as a test result"* rather than pause indefinitely.

Consequently: **this sprint's Phase 2 answer is, itself, the primary
finding of this sprint.** Every endpoint this sprint needed to validate is
gated identically to Sprint H, reconfirmed fresh this sprint:

| Endpoint | Result `[LIVE — Sprint I / Sprint H]` |
|---|---|
| International exchange identification (`symbol_search`) | ✅ Enabled, unrestricted |
| Quote — US symbols | ✅ Enabled |
| Quote — international symbols | ❌ 404, `"symbol or figi parameter is missing or invalid"` — confirmed fresh this sprint for VOLV.B |
| Historical time series — international | ❌ Same 404 pattern (not re-tested fresh this sprint beyond the identical quote-endpoint mechanism; Sprint H tested this directly for all 11 non-US-native symbols) |
| Company profile | ❌ 403, `"/profile is available exclusively with grow or pro or ultra or venture or enterprise plans"` — confirmed fresh this sprint for NOVO.B; **AAPL still anomalously returns 200** |
| Statistics | ❌ Same 403 pattern (Sprint H) |
| Income statement | ❌ Same 403 pattern (Sprint H) |
| Balance sheet | ❌ Same 403 pattern (Sprint H) |
| Cash flow | ❌ Same 403 pattern (Sprint H) |
| ISIN | ❌ Not present in any response schema tested; `[DOCUMENTED]` confirms ISIN requires a paid "Data add-on," separate even from the base subscription tier |
| FIGI | ❌ Not present in any response schema tested; `[DOCUMENTED]` confirms FIGI requires the **Ultra** (individual) or **Enterprise** (business) plan or above |
| CUSIP | ❌ Not present; `[DOCUMENTED]` same Data add-on gating as ISIN |
| A dedicated `/instruments` reference endpoint | ❌ `[LIVE — Sprint I]` returns plain-text `404 page not found` — this route does not exist on Twelve Data's API at all, distinct from the JSON-formatted plan-restriction 404s seen elsewhere |

**This sprint cannot answer its own Phase 2 objective ("does a paid tier
provide the coverage Atlas needs") because no paid tier was available to
test — this is the second consecutive sprint blocked on this exact
precondition.** Per the brief's own rule, this is reported as the test
result it is, not inferred around.

---

## Phase 3 — Validation Matrix

Same 19-company matrix as Sprint H, reused for direct comparability (see
that report's Phase 1 table). No new company was substituted or dropped.

---

## Phase 4 — Identity Resolution Validation

Reclassified from Sprint H's raw evidence using this sprint's stricter
six-category scheme (`EXACT_NATIVE_MATCH` / `EXACT_ADR_MATCH` /
`ALTERNATIVE_TICKER_REQUIRED` / `MULTIPLE_PLAUSIBLE_MATCHES` /
`WRONG_COMPANY_MATCH` / `UNRESOLVED`), plus fresh confirmation calls this
sprint for the two names that most needed it (EVO, MC).

**Critical refinement from Sprint H:** Sprint H's classification treated
Twelve Data's identification as a clean "correct match" wherever the
*first* result matched the expected company. This sprint's fresh
`symbol_search` calls `[LIVE — Sprint I]` show that framing understated the
risk — **`symbol_search` returns multiple candidates for ambiguous
tickers, and correct selection requires business logic Atlas does not yet
have**, not something the API guarantees on its own:

- `symbol_search(EVO)` `[LIVE — Sprint I]` returns Evolution AB (Sweden,
  correct) **first**, but also returns *Embark Early Education Limited*
  (ASX, Australia) and *Evovest Global Equity ETF* (TSX, Canada) as
  same-ticker matches.
- `symbol_search(MC)` `[LIVE — Sprint I]` returns **both** LVMH Moët
  Hennessy Louis Vuitton SE (Euronext Paris, correct) **and Moelis &
  Company (NYSE)** — the exact same wrong company SEC EDGAR silently
  resolves to — as top-ranked candidates in the same response.

| Ticker | Twelve Data classification | SEC EDGAR classification |
|---|---|---|
| AAPL–TSLA (US) | `EXACT_NATIVE_MATCH` | `EXACT_NATIVE_MATCH` |
| VOLV-B, ATCO-B, INVE-B, HEXA-B, SAAB-B | `EXACT_NATIVE_MATCH` (single unambiguous candidate returned) | `UNRESOLVED` (no CIK) |
| **EVO** | `MULTIPLE_PLAUSIBLE_MATCHES` (correct result ranked first, but two unrelated companies share the ticker) | `WRONG_COMPANY_MATCH` (Evotec SE) |
| NOVO-B | `EXACT_NATIVE_MATCH` | `UNRESOLVED` as given; `EXACT_ADR_MATCH` if queried as `NVO` (statement stage still fails — see Phase 9) |
| ASML, SAP | `EXACT_NATIVE_MATCH` | `EXACT_NATIVE_MATCH` (identity resolves; statement stage fails — 20-F gap) |
| TSM, TM | `EXACT_ADR_MATCH` (Twelve Data returned the NYSE ADR listing, not a native Taiwan/Japan listing, for the bare ticker) | `EXACT_NATIVE_MATCH` (real CIK; statement stage fails) |
| SONY | `EXACT_NATIVE_MATCH` (native Tokyo listing, ticker `6758`) | `EXACT_NATIVE_MATCH` (statement stage fails) |
| **MC** | `MULTIPLE_PLAUSIBLE_MATCHES` (LVMH ranked first, Moelis & Co present in the same response) | `WRONG_COMPANY_MATCH` (Moelis & Co) |

**Finding:** ticker equality alone is unsafe on **both** providers, not
just SEC EDGAR. Twelve Data's advantage over SEC EDGAR is that its top-
ranked result was correct in every case tested (19/19), and its response
*exposes* the ambiguity (multiple candidates, distinguishable by
country/exchange/security type) rather than hiding it behind a single flat
answer — but an integration that naively took "first result" without
checking country/name/security-type agreement would still be exposed to
exactly the same collision risk Sprint H found in SEC EDGAR, on the same
two tickers.

---

## Phase 5 — Explicit Collision Tests

Retested fresh `[LIVE — Sprint I]` for both Sprint H collisions:

| Ticker | SEC EDGAR (fresh, `[LIVE — Sprint I]`) | Twelve Data (fresh, `[LIVE — Sprint I]`) |
|---|---|---|
| EVO | Evotec SE, CIK 1412558 — **wrong company**, unchanged from Sprint H | Evolution AB ranked first (correct) + 2 unrelated companies in the same response |
| MC | Moelis & Co, CIK 1596967 — **wrong company**, unchanged from Sprint H | LVMH ranked first (correct) + **Moelis & Co present in the same response** |

**Directly answering the brief's Phase 5 question — does exchange-aware
identity materially reduce collision risk?** Yes, but conditionally, not
absolutely: Twelve Data's *ranking* was correct in both cases, and its
richer per-candidate metadata (exchange, country, security type) makes
disambiguation *possible* in a way SEC EDGAR's flat ticker map never
allows. But the raw presence of Moelis & Co in Twelve Data's own `MC`
results proves the collision risk is not eliminated by switching providers
— it is only made *detectable*, and only if Atlas's integration code
actually checks country/exchange/name agreement rather than taking the
first or ticker-matching result. This is exactly why Phase 13's identity
safety rules below are necessary regardless of which provider Atlas adds.

---

## Phase 6 — Market Data Validation

`[LIVE — Sprint H]`, reconfirmed fresh this sprint for a stability sample
(AAPL quote 200, VOLV.B quote 404):

| Population | Classification |
|---|---|
| US-native (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA) | `FULL` |
| US-listed ADRs (TSM, TM) | `FULL` (current quote + time series both returned) |
| All 11 foreign-exchange-native symbols (Swedish, Danish, Dutch, German, Japanese-native, French) | `PLAN_GATED` — 404, not `UNSUPPORTED_SYMBOL`, since the identical symbol+MIC pair was just successfully resolved one call earlier by `symbol_search` |

No `WRONG_SECURITY` or `ERROR` classifications occurred in market data —
every failure was a clean, consistent plan restriction, not a data-quality
or identity problem.

---

## Phase 7 — Company Profile Validation

`[LIVE — Sprint H]`, reconfirmed fresh this sprint (NOVO.B profile → 403):

| Company | Classification |
|---|---|
| AAPL (both Sprint H attempts + this sprint's fresh check) | `FULL` — all fields present, and each field agreed with Phase 4's identity (name "Apple Inc.", country "United States", exchange NASDAQ — no `IDENTITY_CONFLICT`) |
| INVE-B (one Sprint H occurrence) | `FULL`, real SEK-denominated data, name "Investor AB" agreed with identity |
| All 17 other companies | `PLAN_GATED` |

No `IDENTITY_CONFLICT` was observed in the profile data that *did* return —
where accessible, Twelve Data's profile metadata was internally consistent
with its own identification layer. This is a real point in its favor,
distinct from and not undermined by the ticker-ambiguity finding in Phase
4/5 (that risk lives in the *symbol_search* candidate list, not in
disagreement between a resolved symbol and its own profile).

---

## Phase 8 — Financial Statement Validation

`[LIVE — Sprint H]`:

| Company | Classification |
|---|---|
| AAPL | `FULL` — revenue, operating income, net income, EPS, shares outstanding, EBIT/EBITDA, full balance sheet and cash flow, all internally consistent with AAPL's identity |
| INVE-B | `FULL` (one occurrence) — SEK-denominated, real 2025/2026 fiscal-year figures, all fields agreed with Investor AB's identity — **no `IDENTITY_CONFLICT`** |
| All 17 other companies | `PLAN_GATED` |

No case of "technically successful but wrong company" financials was found
in Twelve Data's statement responses — unlike SEC EDGAR's `MC` result
(Phase 5), where 14 real records were ingested under Moelis & Co's
identity while nominally serving an LVMH request. This is a meaningful,
live-confirmed difference in failure *character* between the two
providers: SEC EDGAR's collision silently produces wrong data; Twelve
Data's plan-gating silently produces *no* data, which is a strictly safer
failure mode even though it is also less useful.

---

## Phase 9 — IFRS / Foreign Issuer Validation

Answering each of the brief's explicit questions, using only live evidence:

- **Does Twelve Data normalize IFRS statements?** `UNDETERMINED` — no
  IFRS-reporting company's statements were ever actually retrieved this
  sprint or last (plan-gated for all of ASML, SAP, TSM, NOVO-B, TM, SONY,
  MC). The one live example of Twelve Data's statement schema (INVE-B) is
  a Swedish company but was not confirmed to be IFRS-tagged as opposed to
  a normalized/generic schema — the response used standard-agnostic field
  names (`sales`, `operating_income`, `net_income`), which is suggestive
  but not proof of IFRS-specific handling.
- **Are 20-F filers usable via Twelve Data?** `UNDETERMINED` — same
  plan-gating blocks every 20-F-filer test case.
- **Are native European/Japanese/Taiwanese statements returned?**
  `UNDETERMINED` for the same reason.
- **Are line items normalized consistently enough for Atlas's analysis
  engine?** Partially answerable from the one live example: INVE-B's
  income statement used the same field names as AAPL's (`sales`,
  `operating_income`, `net_income`, `eps_basic`, `eps_diluted`,
  `basic_shares_outstanding`) — this is a real, positive signal for
  normalization compatibility (see Phase 11), but n=1 is not a sufficient
  sample to generalize to all 7 companies this phase asks about.
- **Are reporting currencies correct?** Yes, for the one live example —
  INVE-B's statements were correctly tagged `SEK` throughout.
- **Are period dates reliable?** Yes, for the one live example — INVE-B's
  `fiscal_date` (2025-12-31) and `year` (2026) fields were internally
  consistent and plausible for a Swedish fiscal year.
- **Which important fields remain unavailable?** All of them, for 6 of the
  7 companies this phase names (ASML, SAP, TSM, NOVO-B, TM, SONY, MC) —
  blocked at the plan level before any field-level question can be
  answered.

**This phase's honest conclusion: this sprint cannot answer its own
central IFRS question.** The single INVE-B data point is encouraging but
statistically meaningless against a 7-company ask, and it arose from the
same unreproduced access anomaly flagged in Sprint H, not from confirmed
plan access.

---

## Phase 10 — Nordic Coverage Validation

Directly addressing the Volvo B problem, per company:

| Company | Native symbol resolves? | Exchange correct? | Market prices? | Historical? | Profile? | Statements? | Currency? | Correct entity? |
|---|---|---|---|---|---|---|---|---|
| VOLV-B | ✅ `VOLV.B` | ✅ XSTO | ❌ 404 | ❌ 404 | ❌ 403 | ❌ 403 | ✅ SEK (in identity response) | ✅ Volvo AB |
| ATCO-B | ✅ `ATCO.B` | ✅ XSTO | ❌ | ❌ | ❌ | ❌ | ✅ SEK | ✅ Atlas Copco AB |
| EVO | ✅ (ranked first) | ✅ XSTO | ❌ | ❌ | ❌ | ❌ | ✅ SEK | ✅ Evolution AB (with the multi-match caveat in Phase 4/5) |
| INVE-B | ✅ `INVE.B` | ✅ XSTO | ❌ | ❌ | ✅ (one occurrence) | ✅ (one occurrence) | ✅ SEK | ✅ Investor AB |
| HEXA-B | ✅ `HEXA.B` | ✅ XSTO | ❌ | ❌ | ❌ | ❌ | ✅ SEK | ✅ Hexagon AB |
| SAAB-B | ✅ `SAAB.B` | ✅ XSTO | ❌ | ❌ | ❌ | ❌ | ✅ SEK | ✅ Saab AB |
| NOVO-B | ✅ `NOVO.B` | ✅ XCSE | ❌ | ❌ | ❌ (fresh-confirmed this sprint) | ❌ | ✅ DKK | ✅ Novo Nordisk A/S |

**Direct answer to the brief's requirement: "For Volvo B specifically,
Atlas must either produce usable real company data or clearly fail for a
documented provider limitation. No silent fallback to unrelated ADRs or
similarly-named companies."** Volvo B **clearly fails** on the currently
accessible Twelve Data tier, for the single, cleanly documented reason of
plan-level access restriction (HTTP 403/404 with explicit upgrade
messaging) — not ambiguity, not a wrong-company substitution, not a silent
fallback. This is the safe failure mode the brief asks for, even though
it's still a failure. Identity resolution itself is perfect (correct
company, correct exchange, correct currency, every time) — the gap is
entirely in market/statement data access, confirming Sprint H's finding
still holds unchanged.

---

## Phase 11 — Normalization Compatibility with Atlas

Based on the one full live example (AAPL, extended by the INVE-B partial
match), comparing Twelve Data's field names against Atlas's
`BusinessFactKind` / `CompanyProfile` / `MarketSnapshot` expectations:

| Atlas field | Twelve Data field | Classification |
|---|---|---|
| Revenue | `sales` (income_statement) | `DIRECT_MATCH` — semantically identical, just a naming difference |
| Free Cash Flow | Not directly returned; `operating_cash_flow` and `capital_expenditures` both present in `cash_flow.investing_activities`/`operating_activities` | `DERIVABLE` — FCF = operating cash flow − capex, same derivation Atlas's own `valuation/cash_flow.py` already performs for SEC EDGAR data |
| Debt | Not seen in the AAPL sample's top-level fields (would require the full balance sheet's liabilities section, not fully captured in this sprint's truncated raw responses) | `REQUIRES_NORMALIZATION_RULE` — needs a follow-up check of the full balance sheet schema before this can be marked `DIRECT_MATCH` |
| Cash | `cash_and_cash_equivalents` (balance_sheet.assets.current_assets) | `DIRECT_MATCH` |
| Capex | `capital_expenditures` (cash_flow.investing_activities) | `DIRECT_MATCH` — though the AAPL sample showed this field as `null` for the FY2025 period tested, meaning derivability is real but not guaranteed present every period |
| Shares outstanding | `basic_shares_outstanding` / `diluted_shares_outstanding` (income_statement) | `DIRECT_MATCH` |
| Market price | `close` (quote / time_series) | `DIRECT_MATCH` |
| Market cap | Dedicated `/market_cap` endpoint, returned as a time series (`[LIVE — Sprint H]`, tested for AAPL only, this endpoint was never re-checked for plan-gating on other symbols this sprint) | `DIRECT_MATCH`, unconfirmed for non-US symbols |
| Currency | `currency` field present in nearly every response type (quote, income_statement.meta, balance_sheet.meta, cash_flow.meta) | `DIRECT_MATCH` — and notably *more* consistently present than in Atlas's current SEC EDGAR/Alpha Vantage pipeline |
| Annual period | `fiscal_date` + `year` (income_statement etc.) | `DIRECT_MATCH` |
| Company profile metadata | `sector`, `industry`, `country`, `employees`, `website`, `description` all map directly to Atlas's existing `CompanyProfile` fields | `DIRECT_MATCH` |

**Overall: where Twelve Data's data is accessible, it is well-suited to
Atlas's existing canonical model** — most fields are `DIRECT_MATCH` or
cleanly `DERIVABLE` using logic Atlas already has for its SEC EDGAR
pipeline. The one flagged `REQUIRES_NORMALIZATION_RULE` item (debt) needs
a follow-up schema check, not a redesign. This is a genuinely positive
finding, independent of and not weakened by the access-gating problem
documented elsewhere in this report.

---

## Phase 12 — Reporting Currency and FX Safety

`[LIVE — Sprint H + Sprint I]` evidence, audited for currency-mixing risk:

| Company | Trading currency (identity) | Financial statement currency | Market cap currency | Quote currency | Discrepancy? |
|---|---|---|---|---|---|
| AAPL | USD | USD | USD | USD | None |
| INVE-B | SEK | SEK | Not observed (statement/market-cap endpoints not both exercised together for this symbol) | Not observed (quote 404'd) | None observed, but incomplete coverage |
| TSM (Twelve Data's ADR route) | USD (NYSE ADR) | Not observed (plan-gated) | Not observed | USD | **Latent risk**: Twelve Data resolved TSM as its NYSE ADR (`XNYS`, USD), not its native Taiwan listing (`TWSE`, TWD) — if fundamentals ever *were* accessible for the native listing while price data came from the ADR route, a naive merge would combine TWD financials with a USD quote without any FX conversion |
| TM (same pattern as TSM) | USD (NYSE ADR) | — | — | USD | Same latent risk |
| ASML/SAP/MC (native-listing route, all EUR) | EUR | Not observed (plan-gated) | Not observed | Not observed (404) | No live discrepancy observed, but **no live confirmation Atlas would catch one if it existed**, since neither side of the comparison was ever actually retrieved together |

**Does Atlas currently have sufficient metadata to prevent these
mixtures?** `[DESIGN]` — **No, not reliably.** Atlas's `CompanyProfile.currency`
field (added in ATLAS-032/033) captures a single currency value per
company, populated from whichever provider call happened to run — there is
no per-fact currency tag that would let Atlas detect "this MarketSnapshot's
currency disagrees with this FinancialPeriod's currency" if two different
provider calls (e.g., an ADR quote and a native-listing statement) were
ever merged into the same `BusinessRecord`. This sprint did not find a live
case of this actually happening (no company had both sides of data
successfully retrieved this sprint), but the **architectural gap that would
allow it to happen silently is real and independent of that**. Per the
brief's explicit instruction, no FX conversion or currency-consistency
enforcement is implemented this sprint — this is documented as a safety
requirement for Phase 13/20, not fixed now.

---

## Phase 13 — Identity Safety Rules

`[DESIGN]`, grounded directly in Phases 4/5's live collision evidence.

**Minimum canonical identity fields Atlas must require before accepting
provider data as canonical:**

| Field | Required? | Rationale |
|---|---|---|
| Ticker | Required, but never sufficient alone | Both live collisions (EVO, MC) were ticker matches |
| Exchange / MIC code | **Required** | The single field that would have caught both live collisions — Evotec SE and Evolution AB are on different exchanges; Moelis & Co and LVMH are on different exchanges |
| Country | **Required** | Redundant with exchange in most cases, but catches cases where the same exchange group spans multiple countries (e.g., Euronext) |
| Legal company name | **Required**, compared via normalized string match, not exact equality | Human-readable final check; catches cases where exchange/MIC alone is ambiguous (e.g., dual share classes) |
| Currency | Recommended, not blocking | Corroborating signal (a Swedish company should report in SEK), not independently sufficient |
| Security type | Recommended | Distinguishes a Common Stock match from an ETF/Depositary Receipt match sharing the same ticker (seen live in the EVO ASX/TSX false candidates) |
| ISIN | Not currently obtainable on any live-tested provider tier — cannot be required today, should be adopted opportunistically once available (paid Twelve Data add-on, per Phase 2) | |
| FIGI | Same as ISIN — Ultra/Enterprise-tier only, not currently obtainable | |
| CIK | Required specifically for SEC EDGAR-sourced data, not a cross-provider field | |
| Provider-specific identifier | Recommended, for audit/provenance, not for identity confirmation itself | |

**Explicit acceptance rules, directly answering the brief's examples:**

1. **A provider response must not be accepted solely because ticker
   matches.** Confirmed necessary by two independent live collisions this
   sprint and last.
2. **A result must require agreement on at least ticker + exchange/MIC +
   country before being treated as identified**, with legal name compared
   as a secondary corroborating check, not the primary gate (company names
   vary in formatting — "LVMH Moët Hennessy Louis Vuitton SE" vs "LVMH" —
   in a way exchange/MIC does not).
3. **A cross-provider merge must independently verify identity on both
   sides before merging fields.** Never assume Provider A's `ticker=X` and
   Provider B's `ticker=X` refer to the same security without checking
   exchange/country agreement — this sprint's own probe script had to add
   exactly this logic (`pick_best_match` filtering by expected country) to
   get correct results; the raw API alone did not guarantee it.
4. **A native listing and an ADR must never be silently treated as the
   same security**, even though they represent economic exposure to the
   same underlying company — they have different currencies, different
   trading calendars, and (per Phase 12) different latent FX-mixing risk.
   Atlas's canonical model should record them as *related* (same
   underlying company) but *distinct* securities.
5. **Ambiguous identity (`MULTIPLE_PLAUSIBLE_MATCHES`, per Phase 4's
   classification) must be rejected outright, not resolved by picking the
   first or highest-ranked result automatically**, unless the full
   agreement check in rule 2 passes for exactly one candidate.

---

## Phase 14 — Provider Conflict Scenarios

`[DESIGN]`, using this sprint's live evidence as the concrete cases:

| Conflict | Correct Atlas behavior |
|---|---|
| SEC EVO → Evotec SE; Twelve Data EVO → Evolution AB | **Prefer the exchange-qualified identity** (Twelve Data's), but do not silently discard SEC's answer — record it as a rejected candidate for audit purposes. Never merge Evotec SE's financials with Evolution AB's identity under any circumstance. |
| SEC MC → Moelis & Co; Twelve Data MC → LVMH (ranked first) + Moelis & Co (also present) | Same as above — **reject SEC's flat-ticker answer entirely** when a richer, exchange-qualified source disagrees; additionally, since Twelve Data itself returns Moelis & Co as a candidate, Atlas must apply rule 2 (exchange/country agreement) even to a single provider's own candidate list, not just across providers. |
| Twelve Data resolves TSM/TM as their NYSE ADR rather than a native listing | **Treat as `EXACT_ADR_MATCH`, not `EXACT_NATIVE_MATCH`** (per Phase 4's taxonomy) and require the caller/composition layer to be explicit about which one it wanted — if Atlas ever needs the native Taiwan/Japan listing specifically (e.g., for local-market corporate actions), an ADR match must not silently substitute for it. |
| Financial statement currency differs from quote currency for the same nominal company (the latent risk in Phase 12, not yet observed live) | **Reject the merge and surface a data-integrity flag** rather than silently combining figures across currencies — this is a "do not implement FX, but do not silently combine" case per the brief's own Phase 12 instruction. |
| Any case where two providers disagree and neither is exchange-qualified | **Reject the ambiguous result entirely** rather than defaulting to whichever provider was called first or listed first in configuration — this sprint found no case where "first responder wins" would have been safe. |

**No case this sprint supports silently merging conflicting identities
under any circumstance** — every live conflict found was resolved correctly
only by an explicit, additional cross-check (exchange, country, security
type), never by a default or ordering rule.

---

## Phase 15 — Rate Limit & Operational Reliability

`[LIVE — Sprint H, reconfirmed unchanged this sprint since the plan itself
is unchanged]`:

| Provider | Requests/min | Requests/day | Throttle behavior | Latency |
|---|---|---|---|---|
| Twelve Data (basic) | 8 | 800 | Not tested at the throttle boundary — Sprint H's ~160 calls across two sprints were paced at 1/8s and never approached the limit; no burst/throttle/HTTP-429 behavior has been observed | Sub-second, informally observed |
| SEC EDGAR | No hard cap for reasonable single-company use `[DOCUMENTED — provider policy]` | N/A | N/A | Normal request timeouts throughout, no formal measurement |
| Alpha Vantage (free) | Not applicable — daily cap dominates | **25**, confirmed exhausted independently on three separate calendar days now (Sprint F, Sprint H, Sprint I) | Returns HTTP 200 with an error string in the body, not a 429 — a fragile contract flagged again this sprint | Not measurable — every attempt is rate-limited before any real latency occurs |

**Batch endpoints**: not tested this sprint — out of scope given the plan
restriction makes the underlying fundamentals/international-market-data
calls this would batch unavailable anyway.

**Practical capacity estimate** (`[DESIGN]`, extrapolated only from
confirmed rate limits, not from untested paid-tier throughput):

- On the confirmed **basic** plan: 800 requests/day ÷ ~7 calls per company
  (identification + quote + time series + profile + 3 statements) ≈ **~114
  companies/day theoretical**, but this is a hollow number since most of
  those calls would 403/404 for non-US names — **actual usable enrichment
  throughput for non-US companies today is effectively zero**, independent
  of the request budget.
- A 100-company universe refresh is **not currently achievable** for
  non-US names on any live-tested provider tier — this is the same
  conclusion Sprint H reached, reconfirmed rather than improved.

---

## Phase 16 — Reliability Matrix

| Company | Requested ticker | Resolved symbol | Exchange | Country | Identity | Market Data | Historical | Profile | Financial Statements | Currency Safety | SEC Status | Twelve Data Status | Alpha Vantage Status | Pipeline Readiness | Failure Reason | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AAPL | AAPL | AAPL | NASDAQ | US | EXACT_NATIVE_MATCH | FULL | FULL | FULL | FULL | Safe (single currency) | FULL | FULL (anomalous) | FULL (Sprint F) | **Yes** | — | Twelve Data's only full-access example, unreproduced for other symbols |
| MSFT/GOOGL/AMZN/NVDA/TSLA | (same) | (same) | NASDAQ | US | EXACT_NATIVE_MATCH | FULL | FULL | PLAN_GATED | PLAN_GATED | Safe | FULL | Market data only | FULL (Sprint F) | **Yes** (via SEC EDGAR) | — | Statements come from SEC, not Twelve Data |
| VOLV-B | VOLV-B | VOLV.B | OMX/XSTO | Sweden | EXACT_NATIVE_MATCH | PLAN_GATED | PLAN_GATED | PLAN_GATED | PLAN_GATED | N/A (no data to mix) | UNRESOLVED | Identity only | Untested (bare ticker, quota exhausted) | No | Plan-gated, non-US | Clean documented failure, no silent fallback |
| ATCO-B, HEXA-B, SAAB-B | (same pattern) | .B native | OMX/XSTO | Sweden | EXACT_NATIVE_MATCH | PLAN_GATED | PLAN_GATED | PLAN_GATED | PLAN_GATED | N/A | UNRESOLVED | Identity only | Untested | No | Plan-gated | Same as VOLV-B |
| EVO | EVO | EVO | OMX/XSTO | Sweden | MULTIPLE_PLAUSIBLE_MATCHES | PLAN_GATED | PLAN_GATED | PLAN_GATED | PLAN_GATED | N/A | **WRONG_COMPANY_MATCH** | Identity only (correct, with caveat) | Untested | No | Plan-gated + SEC collision | Do not use SEC for this ticker under any config |
| INVE-B | INVE-B | INVE.B | OMX/XSTO | Sweden | EXACT_NATIVE_MATCH | PLAN_GATED | PLAN_GATED | FULL (unreproduced) | FULL (unreproduced) | Safe in the one sample observed | UNRESOLVED | Statements only, once | Untested | No | Statement access unreliable, no price data at all | The strongest non-US data point, but not repeatable |
| NOVO-B | NOVO-B | NOVO.B | OMXC/XCSE | Denmark | EXACT_NATIVE_MATCH | PLAN_GATED | PLAN_GATED | PLAN_GATED | PLAN_GATED | N/A | UNRESOLVED as given; identity-only via NVO | Identity only | Untested | No | Plan-gated + 20-F gap even via correct ticker | Confirmed fresh this sprint |
| ASML | ASML | ASML | Euronext/XAMS | Netherlands | EXACT_NATIVE_MATCH | PLAN_GATED | PLAN_GATED | PLAN_GATED | PLAN_GATED | N/A | Identity only (20-F gap) | Identity only | Market data only (Sprint F, ADR) | No | Plan-gated + 20-F gap | Two independent statement-stage failures, same root outcome |
| SAP | SAP | SAP | XETR | Germany | EXACT_NATIVE_MATCH | PLAN_GATED | PLAN_GATED | PLAN_GATED | PLAN_GATED | N/A | Identity only (20-F gap) | Identity only | Market data only (Sprint F, ADR) | No | Plan-gated + 20-F gap | Same pattern |
| TSM | TSM | TSM | NYSE/XNYS | US (ADR) | **EXACT_ADR_MATCH** | FULL | FULL | PLAN_GATED | PLAN_GATED | **Latent risk if merged with native TWD data** | Identity only (20-F gap) | Market data full, statements gated | Market data (Sprint F) | No | 20-F gap + statements plan-gated | Two independent live market-data sources agree |
| TM | TM | TM | NYSE/XNYS | US (ADR) | EXACT_ADR_MATCH | FULL | FULL | PLAN_GATED | PLAN_GATED | Same latent risk | Identity only (20-F gap) | Market data full, statements gated | Market data (Sprint F) | No | Same as TSM | Same pattern |
| SONY | SONY | 6758 | JPX/XJPX | Japan | EXACT_NATIVE_MATCH | PLAN_GATED | PLAN_GATED | PLAN_GATED | PLAN_GATED | N/A | Identity only (20-F gap) | Identity only via native route; market data only via a different ADR ticker (Sprint F) | Market data (Sprint F, different ticker) | No | Plan-gated, 20-F gap | Twelve Data resolved the *native* listing here, unlike TSM/TM |
| MC | MC | MC | Euronext/XPAR | France | MULTIPLE_PLAUSIBLE_MATCHES | PLAN_GATED | PLAN_GATED | PLAN_GATED | PLAN_GATED | N/A | **WRONG_COMPANY_MATCH** (Moelis & Co) | Identity only (correct, with caveat) | Untested this sprint (LVMUY tested Sprint F, a different ticker) | No | Plan-gated + SEC collision | Same do-not-use-SEC finding as EVO |

**Zero companies are newly marked `SUPPORTED` by financial-statement
availability from Twelve Data this sprint** — per the brief's own explicit
rule ("do not mark a company SUPPORTED if financial statements are
missing"), INVE-B's single unreproduced success is not sufficient to
change its status from anything but a flagged anomaly.

---

## Phase 17 — Coverage Score

Computed from live evidence only, across the 19-company matrix:

| Metric | Current stack (SEC EDGAR + Alpha Vantage) | Proposed stack (+ Twelve Data, basic plan) | Change |
|---|---|---|---|
| Correct identity resolution rate | 6/19 (32%) — SEC only resolves US names correctly; 2 more resolve but to the *wrong* company | **19/19 (100%)** via Twelve Data's identification layer alone | **+68 points** — the one unambiguous, confirmed improvement this sprint reconfirms |
| Market-data coverage rate | 8/19 (42%) — US names + ADR-ticker names tested in Sprint F | 8/19 (42%) via Twelve Data alone (identical population — US-native + ADR) | **No change** — same companies covered, not a net new set |
| Historical-data coverage rate | Same 8/19 pattern (Sprint F, cited) | Same 8/19 (Sprint H, live) | No change |
| Profile coverage rate | 0/19 (not exercised this session on Alpha Vantage due to quota) | 2/19 (11%) — AAPL + one unreproduced INVE-B occurrence | Marginal, unreliable |
| Financial-statement coverage rate | 6/19 (32%) — US names only, via SEC EDGAR | 7/19 (37%) if the unreproduced INVE-B success is counted; 6/19 (32%) if it is excluded as unreliable, which the brief's own rules require | **Effectively no change** |
| Full-pipeline-ready rate | 6/19 (32%) | 6/19 (32%) | **No change** |

**By region:**

| Region | Current stack pipeline-ready | Proposed stack pipeline-ready |
|---|---|---|
| United States (6 companies) | 6/6 (100%) | 6/6 (100%) — unchanged |
| Nordics (7: Sweden ×6 + Denmark ×1) | 0/7 (0%) | 0/7 (0%) — unchanged |
| Continental Europe (3: ASML, SAP, MC) | 0/3 (0%) | 0/3 (0%) — unchanged |
| Asia (3: TSM, TM, SONY) | 0/3 (0%) | 0/3 (0%) — unchanged |

**The paid-tier hypothesis remains entirely untested — this table reports
the free-tier reality, unchanged from Sprint H, not a paid-tier
improvement.** The only metric that moved is identity resolution, which
was already Sprint H's headline finding.

---

## Phase 18 — Go / No-Go Decision

**CONDITIONAL GO.**

This is not a new verdict — it is Sprint H's verdict, unable to be moved
forward because its precondition (a live paid-tier trial) still has not
been met. Restating why this is `CONDITIONAL GO` rather than `NO-GO`,
per the brief's own required breakdown of failure category: **the
blocker is access/pricing, not coverage, data quality, identity safety, or
normalization incompatibility.**

- **Not a coverage failure**: identification coverage is 100%, confirmed
  twice now.
- **Not a data-quality failure**: the two live examples of unblocked data
  (AAPL, INVE-B) were clean, well-structured, and internally consistent —
  no wrong-company data, no malformed fields.
- **Not an identity-safety failure** in the sense of being uncorrectable —
  Phase 13's rules show the risk is manageable with agreement checks, and
  Twelve Data's richer metadata makes those checks *possible* in a way SEC
  EDGAR's flat ticker map does not.
- **Not a normalization-incompatibility failure**: Phase 11 found mostly
  `DIRECT_MATCH`/`DERIVABLE` fields.
- **It is a pricing/access failure**, plain and simple: the specific plan
  provisioned cannot serve the data this sprint needed to validate, for
  the second sprint running.

**Unresolved conditions, unchanged from Sprint H, now confirmed twice:**

1. A paid Twelve Data tier (`grow`/`pro`/`ultra`/`venture`, per the 403
   messages) must actually be provisioned and tested before this
   recommendation can move to `GO`.
2. Per the brief's own instruction, **this does not meet the bar to reopen
   the six-provider scan** — nothing found this sprint suggests Twelve
   Data fails materially; it suggests the access path to test it has not
   yet been completed.

---

## Phase 19 — Architecture Recommendation

Unchanged in shape from Sprint G/H, refined with this sprint's identity-
safety findings:

- **Identity**: a new, exchange-aware canonical `CompanyIdentity` model
  (Phase 13), required as a gate *before* any provider result — from any
  provider, including Twelve Data itself — becomes canonical. This is now
  a harder requirement than Sprint G/H suggested: this sprint proved the
  risk exists even within Twelve Data's own candidate list (Phase 4/5's
  MC finding), not only across providers.
- **US regulatory fundamentals**: SEC EDGAR, unchanged, with the ticker-
  collision risk (Phase 5) requiring the identity gate above before any
  SEC result is trusted, not just before cross-provider merges.
- **International market data**: Twelve Data, *pending the paid-tier
  trial* — architecturally the right shape per Phase 6/11's evidence, but
  not yet confirmed at the tier Atlas can actually afford/access.
- **International fundamentals**: Twelve Data, same conditional status,
  reinforced by Phase 9's inability to answer the IFRS question this
  sprint.
- **Fallback market data**: Alpha Vantage, confirmed quota-limited on a
  third separate calendar day — fallback-only, never primary.
- **Provider disagreement**: never silently merge (Phase 14) — every
  conflict scenario this sprint found requires an explicit agreement check,
  with no safe default ordering rule.

No UI work, no recommendation-engine changes, and no decision-engine
redesign occurred or is proposed — consistent with the brief's explicit
scope limits.

---

## Phase 20 — Migration Plan

Smallest implementation sequence, **not implemented this sprint** per
explicit instruction:

1. Add the canonical `CompanyIdentity` model (Phase 13's fields: ticker,
   exchange/MIC, country, currency, legal name, security type; ISIN/FIGI
   added opportunistically once a tier that exposes them is confirmed).
2. Harden ticker+exchange resolution in `SecEdgarFundamentalsProvider` and
   any future Twelve Data adapter to apply Phase 13's agreement rules
   before accepting a match — this directly closes the EVO/MC collision
   risk at its source, independent of any new provider.
3. Fix the SEC collision risk specifically: add an exchange/country cross-
   check (even a minimal one, since SEC EDGAR itself has no exchange
   metadata) using a second, cheap signal — e.g., reject a SEC match when
   a bare ticker is known-ambiguous per a small manually curated block-list
   seeded from this sprint's two confirmed cases, pending the fuller model
   in step 1.
4. Complete the paid-tier Twelve Data trial (the actual blocker this
   sprint could not clear) — this should happen **before**, not after, any
   further implementation work, since steps 5+ depend on knowing what a
   paid tier actually returns.
5. Implement the Twelve Data provider adapter, following the existing
   `BusinessDataProvider`/`HistoricalMarketDataProvider`/
   `CompanyProfileProvider` Protocol family unchanged.
6. Add normalized financial-statement mapping per Phase 11's field table,
   resolving the one `REQUIRES_NORMALIZATION_RULE` item (debt) first.
7. Add provider fallback orchestration (SEC → Twelve Data → Alpha Vantage,
   per responsibility, as designed in Sprint G).
8. Add conflict detection per Phase 14's rules — reject-and-flag, never
   silent-merge.
9. Add provider provenance fields to `BusinessRecord` (which provider,
   which identity fields agreed, confidence level) so every canonical fact
   is auditable back to the check that admitted it.
10. Add integration tests using this exact 19-company matrix, including
    the two collision cases as permanent regression tests.
11. Enable international enrichment behind a feature flag, defaulting off,
    until the paid-tier trial and steps above are complete.

---

## Final Deliverables Index

1. This document — `docs/paid_tier_provider_validation_report.md`.
2. Live company reliability matrix — Phase 16.
3. Identity-collision analysis — Phases 4, 5, 14.
4. IFRS/20-F coverage findings — Phase 9 (inconclusive, explicitly stated
   as such).
5. Nordic coverage findings — Phase 10.
6. Rate-limit/capacity analysis — Phase 15.
7. Normalization compatibility assessment — Phase 11.
8. Identity safety rules — Phase 13.
9. Coverage score — Phase 17.
10. Go/no-go recommendation — Phase 18: **CONDITIONAL GO**.
11. Recommended provider architecture — Phase 19.
12. Migration plan — Phase 20 (not implemented).
13. Remaining unknowns and risks — Phase 9's IFRS question is unresolved
    for the third time (Sprint G documentation, Sprint H free-tier, Sprint
    I still-free-tier); the AAPL/INVE-B access anomaly from Sprint H
    remains unexplained; whether a paid tier will actually resolve these
    gaps is itself still unverified — this sprint narrows *why* it's
    unverified (pricing/access, not architecture) without closing the gap.
14. Exact API plan tested: Twelve Data **`basic`** (free tier),
    `plan_limit: 8/min`, `plan_daily_limit: 800/day` — confirmed live at
    the start and mid-point of this sprint, unchanged from Sprint H.
15. Commit hash: recorded after this report is committed, below.
