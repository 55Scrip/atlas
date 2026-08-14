# Atlas Alpha — Company Intelligence Root Cause Audit

**Scope:** read-only investigation. No code was changed, no commits made.
**Subject:** MSFT, case id `2b419ce4-060c-40e6-a568-9a4db64d13a9`, live on the running backend (`database/atlas.db`) at time of audit (2026-08-12).
**Method:** live API calls against the running backend, direct read-only SQLite inspection of `database/atlas.db`, a live test of the SEC EDGAR extraction functions against the real `data.sec.gov` API, and source-code tracing with file:line citations throughout. Four parallel research passes covered providers, ingestion/storage, the analysis engine, and case composition/frontend; every cross-agent claim below was independently re-verified against at least one other source (live API, raw DB, or a second agent) before being included.

**One correction made during synthesis, stated up front:** an early single-datapoint read produced the working assumption "`totalDebt` is null for every year." That was wrong. A full re-pull of MSFT's 19-year `financialHistory`, cross-checked against the raw SQLite rows and a live SEC EDGAR API call, shows **`total_debt` is populated for 18 of 19 years** — only fiscal year 2008 is genuinely absent. This is called out explicitly wherever it matters below.

---

## 1. Providers configured today

| Provider | Real / stub | Wired into live pipeline? | Config | Endpoints called | Fields extracted |
|---|---|---|---|---|---|
| **SEC EDGAR** (`SecEdgarFundamentalsProvider`, `atlas/business_data_providers/sec_edgar.py:292`) | Real | **Yes** | No API key; `User-Agent` header from `ATLAS_SEC_EDGAR_USER_AGENT` env var (`sec_edgar.py:186-187`) — **not set in `.env`**, so it runs on the hardcoded placeholder default | `sec.gov/files/company_tickers.json`, `data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`, `sec.gov/cgi-bin/browse-edgar` (raw-reference only) | Revenue, operating income, net income, EPS, capex, buybacks, issuance, dividends, debt issuance/repayment, cash, **total debt**, shares outstanding — both duration (income-statement) and instant (balance-sheet) XBRL concepts |
| **Alpha Vantage** (`AlphaVantageMarketDataProvider`, `atlas/business_data_providers/alpha_vantage.py:240`) | Real | **Yes** | `ALPHA_VANTAGE_API_KEY` env var (`alpha_vantage.py:178-179`) — **present in `.env`** | `GLOBAL_QUOTE`, `OVERVIEW`, `TIME_SERIES_MONTHLY_ADJUSTED` | Share price, shares outstanding, currency, company identity fields (name/exchange/sector/industry/country/description/fiscal-year-end). Explicitly excludes Alpha Vantage's own precomputed ratios (P/E, EBITDA, margins) and never supplies debt or market cap (market cap is derived downstream as price × shares) |
| **Finnhub** | Does not exist | — | — | — | — |
| **Polygon** | Does not exist | — | — | — | — |
| **FMP** (Financial Modeling Prep) | Does not exist | — | — | — | — |
| **Yahoo Finance** (`atlas/providers/yahoo.py:64`) | Real implementation | **No — dead code.** Confirmed by the codebase's own docstring (`atlas/analysis_engine/business_data/providers.py:8-17`): "part of the legacy CLI tree (confirmed unreachable from the live FastAPI app)... not reused here." Its only construction site is `atlas/cli/main.py:2099`, inside an entirely separate legacy CLI dashboard tree | — | — | — |

**Grep confirmation:** no hits for `Finnhub`/`Polygon`/`FMP` anywhere in the codebase except doc-comments listing them as *hypothetical future* providers a `Protocol` interface could support later (`atlas/analysis_engine/business_data/providers.py:4-6`).

**`.env` contents:** exactly one key, `ALPHA_VANTAGE_API_KEY` (confirmed non-empty). No SEC user-agent override, no other provider keys. **Caveat:** no `dotenv`/`pydantic-settings` loading exists anywhere in the app (`atlas/config.py` only reads `ATLAS_HOME` via plain `os.environ.get`) — the `.env` file is only effective if something outside the Python code (shell profile, process manager) exports it into the real process environment. Not independently verified how the running process actually sources it.

**Qualitative business data (business model, competitive position, moat, management):** confirmed via source that **zero provider exists**, not merely "unwired." `atlas/analysis_engine/business.py:1-95`'s own module docstring states these categories are locked because attributing free-text content to a category "would require semantic/NLP parsing, which is forbidden everywhere this codebase already touches Business Evaluation." The `ExternalBusinessRecord` type these categories would need is never constructed anywhere in production code (only in test files). This would show identically for every company, not just MSFT.

---

## 2. The ingestion pipeline, stage by stage

```
Provider.fetch()
  → RawBusinessDocument (identifier, company, source_kind, published_at, metadata: dict)
  → normalize() — freezes metadata, no key filtering
  → validate_raw_document() — checks structural fields only, never inspects metadata contents
  → pipeline.ingest() — versions the record via content-hash comparison
  → BusinessRecord (generic model: no per-field columns, metadata stays a single dict)
  → SqlAlchemyBusinessRecordRepository.add() — INSERT into SQLite `business_records` table,
    metadata serialized whole as one `metadata_json` TEXT column (json.dumps)
  → [READ SIDE] InvestmentCaseCompositionService.build(case_id)
      resolves ticker → business_record_repository.get_by_company(ticker) (service.py:273)
      → extract_company_profile / extract_financial_history / extract_market_snapshot
        (plain dict .get() calls against metadata — e.g. total_debt=metadata.get("total_debt"))
      → assemble_analysis(engine_input, business_records=...) [atlas/analysis_engine/pipeline.py]
          → evaluate_business_analysis, evaluate_valuation, evaluate_risk,
            calculate_conviction, evaluate_recommendation_gate, synthesize_investment_case
      → CanonicalAnalysis
  → InvestmentCaseAnalysisView.from_domain() — Pydantic schema mapping, no further logic
  → GET /cases/{id}/analysis JSON response
```

**Storage confirmed as SQLite**, not JSON files or in-memory: `atlas/core/infrastructure/config/database.py:43-46`, file at `database/atlas.db` (811 KB, modified same day as this audit). Table `business_records` (`atlas/alpha/business_data_refresh/table.py:25-47`) has one `metadata_json` TEXT column holding the entire metadata dict — there is no per-field column for any metric, `total_debt` included.

**What exists for MSFT right now** (direct SQLite query, read-only): 38 `business_records` rows — 1 `company_profile`, 19 `financial_statement`, 18 `market_data_snapshot` — from exactly 2 providers, `alpha_vantage` (19 rows) and `sec_edgar` (19 rows). Nothing is discarded between ingestion and storage: every stage (normalize → validate → ingest → persist → reconstruct) is generically metric-agnostic and passes every metadata key through unchanged; confirmed by reading `repository.py`'s `_to_row`/`_to_record` (full JSON round-trip, no field-level logic).

**What's discarded, and where:** nothing structural is discarded for the fields that exist. What's genuinely absent is *never written in the first place*: `total_debt` for FY2008 specifically (the one year SEC's XBRL instant-tag coverage doesn't resolve a debt figure — confirmed by live-testing the real extraction function against the real SEC API, and by reading the raw stored JSON for that period, which simply has no `total_debt` key at all — never a fabricated null). Revenue is separately missing for 2011–2015 in the *rendered* Financials table (5 consecutive years) while operating income/net income/EPS are present for the same years — a distinct, unexplained provider-extraction gap not covered by this ingestion/storage trace (it originates in the provider's XBRL tag-to-concept mapping, likely a tag-name variant SEC EDGAR used for MSFT filings in that specific window that the current `_DURATION_CONCEPT_TAGS` mapping doesn't include a fallback for).

**The data-completeness gate** (`assess_data_completeness`, `atlas/analysis_engine/business_data/completeness.py:56-77`) only checks **which document kinds exist** (`is_minimally_complete = has_company_profile OR has_financial_statements`) — it has no concept of field-level completeness and never inspects `metadata` contents. This is a real, distinct architectural risk (see §5, Bottleneck class D-adjacent): if a new field is added to extraction in the future (as `total_debt` itself was, per the "Company Data Foundation v1" commit history), **every already-ingested ticker whose data predates that addition will never automatically pick it up** — `ensure_company_enriched` (the gate every automatic write path calls) short-circuits to a no-op the moment any prior financial-statement record exists, regardless of which fields it's missing. The only way to force a re-fetch is the explicit, manually-run CLI (`python -m atlas.alpha.business_data_refresh.cli TICKER`), never triggered automatically. **This did not end up affecting MSFT's `total_debt`** (confirmed populated for 18/19 years in the live DB right now) but is a real, generalizable risk worth fixing regardless.

---

## 3. Why each Atlas View dimension is (or isn't) populated

| Dimension | Required inputs | Available for MSFT | Missing | Why it can't (fully) resolve |
|---|---|---|---|---|
| **Business Strength** | No backend concept exists at all — confirmed via grep, zero matches for `business_strength`/`BusinessStrength` outside comments. `business.py` produces 6 independent per-category findings; nothing rolls them into one score. | 2 of 6 categories real (Growth, Capital Allocation) | An aggregate/composite that was never built, plus the qualitative categories below | Frontend hardcodes `filled={null}` (`InvestmentCasePage.tsx:4828-4832`) — a literal constant, doesn't attempt to read anything |
| **Growth** | `evaluate_growth` reading REVENUE/FREE_CASH_FLOW `BusinessFact`s | **Full** — `status: moderate`, `recentTrend: strong_metric` (2023-2026), real supporting facts | Nothing computationally | Working correctly. `MODERATE` doesn't clear the "extreme conclusions only" threshold that promotes a finding into the Executive Summary/thesis narrative (see §4) |
| **Valuation** | `evaluate_valuation` / FCF-yield-relative, reading share price + shares outstanding + FCF over time | **Full** — `status: fairly_valued`, ~15 years of supporting facts | Only `SCENARIO_BASE/BEAR/BULL` (forward-assumption valuation) — permanently `INSUFFICIENT_INPUT`, hardcoded, never implemented | Working correctly for the current-yield method. Scenario valuation is the literal backend home of "Expected Return" and does not exist |
| **Risk Level** | `risk/pipeline.py`, 4 categories: business/financial/valuation/thesis risk | business/financial/valuation risk all `moderate`, `confidence: full` | thesis_risk always `insufficient_input` (needs the human evidence journal — see §4); financial_risk flags `missing_debt_history` generically (a stale/general reason string, not specific to the one real FY2008 gap) | Working correctly for 3 of 4 categories |
| **Capital Allocation** | `evaluate_capital_allocation` reading buybacks/issuance/debt/capex/dividends facts | **Full** — `status: moderate` | Nothing | Working correctly |
| **Expected Return** | Would require the scenario-valuation capability | **Nothing** — zero backend representation anywhere in `analysis_engine`/`decision_engine`; the only source-code mention is a docstring explicitly listing it among fields that structurally do **not** exist on `ValuationFinding` | Everything | Not built. Frontend hardcodes `filled={null}` (`InvestmentCasePage.tsx:4853-4857`) |
| **Portfolio Fit** | Would require portfolio-wide, cross-holding context (allocation, concentration, diversification, correlation, opportunity cost) | **Nothing** — hardcoded `PortfolioFitStatus(available=False, reason=NOT_YET_IMPLEMENTED)` at both call sites that could produce it (`atlas/alpha/case_intelligence/service.py:176-177`, `atlas/alpha/portfolio_intelligence/service.py:128-129`) | Everything, in the *active* pipeline | See detailed explanation below — this one has real nuance |

**Portfolio Fit, precisely:** a genuinely real, substantial scoring engine already exists in this repository — `atlas/capabilities/portfolio_intelligence/engine.py` (356 lines: diversification impact, sector/country/market-cap concentration, overlap with existing holdings, quality impact, risk impact, an aggregated fit score). It is **not reachable from the Investment Case pipeline**, and this is a *deliberate, documented* architectural boundary, not an oversight: the current decision_engine's own portfolio-intelligence stage (`atlas/decision_engine/stages/portfolio_intelligence.py:1-19`) states in its own docstring that it "never imports `atlas.alpha` or `atlas.capabilities.portfolio_intelligence`," because DE-003's seven substantive portfolio factors (Allocation, Concentration, Diversification, Correlation, Opportunity Cost, Existing Thesis, Previous Decisions) require portfolio-wide, cross-holding data that a single-holding `DecisionEngineInput` structurally cannot honestly supply — the module computes only a verbatim `HoldingContextFinding` (ticker, weight, trade log — never interpreted) and locks all seven factors to `INSUFFICIENT_INPUT`. This exactly matches the `openQuestions` observed live for MSFT (`portfolio_factor_not_assessable` for allocation/concentration/diversification/correlation/opportunity_cost/existing_thesis/previous_decisions). The real capability engine is confined entirely to a separate, legacy, "unreachable from the live FastAPI app" module tree (`atlas/suitability/`, `atlas/dashboard/`, `atlas/decision/decision_engine.py` — the same disowned tree Yahoo Finance belongs to), and reusing it as-is against the current architecture would require redesigning its inputs, which is out of scope for this read-only audit to prescribe in detail.

---

## 4. Why the Executive Summary stays weak

Two genuinely independent causes compound here — not one bug.

**Cause 1 — two separate "evidence" systems, and the gate reads only the empty one.**

There are two structurally unrelated concepts sharing the word "evidence" in this codebase:

1. **Auto-computed evidence**: `BusinessFact`/`ValuationFact` references (e.g. `"21ea5c5cd63a91e1eebaea01df3a9645:v1:free_cash_flow:2017-06-30"`) that populate `businessAnalysis.findings[].supportingEvidence` — substantial for MSFT (dozens of real facts).
2. **Human-recorded evidence**: `Observation`/`Evidence`/`Decision` domain entities — an investor's own journal entries, tied together via `observation_id`. Confirmed via direct SQLite query: **the entire database contains only 2 `evidence` rows, 15 `observations`, and 18 `decisions` system-wide** (across every case, not just MSFT) — and MSFT's case has zero of any of them.

`calculate_conviction` (`atlas/analysis_engine/conviction.py:111-147`) is an ordered decision table. Its second branch:
```python
if evidence_coverage in (EvidenceCoverageLevel.NOT_APPLICABLE, EvidenceCoverageLevel.NONE):
    return ConvictionAssessment(level=ConvictionLevel.INSUFFICIENT_EVIDENCE,
        reasons=(ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,))
```
`evidence_coverage` is `business_evaluation.evidence_quality.coverage`, computed in `atlas/decision_engine/stages/business_evaluation.py:89-139` **exclusively** from `engine_input.evidence`/`engine_input.observations` — system #2 above, never system #1. For a case with zero Observations, `coverage = NOT_APPLICABLE` unconditionally. This single primitive independently gates **four separate call sites** — Conviction, `select_direction` (`direction_selector.py:229-236`), `calculate_recommendation_conviction` (`recommendation_conviction.py:176-177`), and `thesis_risk` (`thesis_risk.py:73-75`) — each with its own copy of the identical check. **No amount of provider-data richness can move any of these four past "insufficient" without a human first recording at least one Observation on the case.**

**Cause 2 — even with evidence, MSFT's real findings currently land in the "no comment" middle zone.**

`investment_case_synthesis.py` only promotes *extreme* categorical conclusions into a narrative Strength or Risk: `STRONG`/`WEAK` for Growth/Capital Allocation (`_business_highlights`, lines 285-309), `UNDERVALUED`/`EXPENSIVE` for Valuation (lines 312-329), `LOW`/`HIGH` for Risk (lines 332-356). `MODERATE`/`FAIRLY_VALUED` — MSFT's actual, real, well-evidenced conclusions on every working dimension — produce **neither**. With `strengths=()` and `risks=()`, the function falls through to:
```python
if not strengths and not risks:
    return AtlasThesis(posture=ThesisPosture.INSUFFICIENT_DATA,
        narrative="Atlas does not yet have enough evaluated business, valuation, or risk "
                   "signal to describe a case for this company. Available real company data "
                   "has been gathered, but no dimension has reached a strong or weak "
                   "conclusion yet.")
```
This is the exact narrative text observed live. **This would happen even with a fully populated evidence journal** — it's a second, independent gap: this synthesis logic currently has no vocabulary for "here's what we found, and it's unremarkable" — every dimension must be exceptional to be mentioned.

**A third, smaller wrinkle:** the Executive Summary card on the *main* Investment Case page is not even this `atlasThesis.narrative` — it's a separately constructed, shorter frontend summary (`deriveAssessmentPoints`, `frontend/src/investmentCase/deriveExecutiveSummary.ts:132-161`), picking up to 3 fixed, pre-written sentences keyed off conviction level / the FCF-yield valuation finding / the single most severe risk finding / thesis staleness. The fuller backend narrative *does* exist and *is* rendered — but only in the "More Details" tab (`CaseNarrativeDetailSection`, `InvestmentCasePage.tsx:4878-4884`), one click away from the page most users will actually read.

Together: (1) the gate that decides Conviction/Recommendation/thesis-risk is structurally blind to everything except a human-maintained journal that's essentially empty system-wide; (2) the narrative generator that decides Business/Valuation/Risk highlights only speaks in extremes and has nothing to say about MSFT's real, solid-but-unremarkable findings; (3) even the fuller narrative that *does* get generated is one tab away from where users are actually looking.

---

## 5. Bottleneck classification

**A. Data exists from providers but never reaches Atlas** — no confirmed instance found for MSFT. Everything ingested (companyProfile, 19 years of financials, market snapshot) does reach the composition layer and the API response.

**B. Data reaches Atlas but analysis never uses it** — no clean instance found. (The closest candidate, Portfolio Fit ignoring `pipeline_outputs`, was investigated in depth and ruled out: the decision_engine's portfolio_intelligence stage genuinely never *computes* a fit score in the first place — by deliberate DE-003 doctrine — so there is nothing for that field to ignore.)

**C. Analysis exists but UI never displays it, or displays a lesser version** — **confirmed, twice**:
  - The real, richer `atlasThesis.narrative` (backend-computed, when it does have content) is generated but shown only in a secondary "More Details" tab; the primary Executive Summary card is a separate, shorter, frontend-only construction.
  - `CanonicalAnalysis.catalysts`/`scenario_analysis` domain fields exist (as explicit `UnavailableCapability` markers) but aren't even serialized into the API schema at all — a smaller instance of the same pattern.

**D. Capability simply does not exist yet** — the largest bucket, and the true root cause for most of the sparseness:
  - Business Model / Competitive Position / Management / Durability: no qualitative-data provider, no content-interpreting evaluator — `business.py:169-223`'s `_evaluate_category` hardcodes `INSUFFICIENT_INPUT` unconditionally, by explicit design, for anyone, forever, until a genuinely new capability (data source + NLP-style evaluator) is built.
  - Expected Return / scenario valuation: zero backend representation.
  - Portfolio Fit in the active pipeline: zero backend representation, despite a real, unused engine sitting in a deliberately quarantined legacy module tree.
  - "No comment on unremarkable findings" in the narrative synthesizer: a real gap in what the synthesizer *can say*, not a data gap.
  - The evidence-coverage gate requiring human journal activity for Conviction/Recommendation: arguably by design (this *is* Atlas's stated doctrine — analysis is not advice, and a "conviction" without any recorded investor judgment may be intentionally withheld) rather than a bug, but its effect is indistinguishable from a capability gap to a user looking at a sparse Investment Case.

---

## 6. Gap matrix

| Capability | Current status | Root cause | Difficulty to solve | Estimated impact |
|---|---|---|---|---|
| Conviction/Recommendation/thesis-risk require human evidence journal | Always `insufficient_evidence`/`insufficient_input` for any case with zero recorded Observations (true for essentially all cases today — 2 evidence rows system-wide) | Deliberate architectural gate (Bucket D, likely intentional doctrine) | N/A — a product decision, not a bug, but worth explicitly confirming as intended | Very high — this is the single biggest visible driver of "weak" cases across the whole product, not just MSFT |
| Narrative synthesizer has no vocabulary for "moderate/unremarkable" findings | `atlasThesis.posture=insufficient_data` whenever every dimension lands in the neutral middle, even with rich, confident, well-evidenced findings | `investment_case_synthesis.py` only promotes STRONG/WEAK/UNDERVALUED/EXPENSIVE/LOW/HIGH into highlights | Low — additive logic change to `_business_highlights`/`_valuation_highlights`/`_risk_highlights` and the fallback branch | High — directly fixes the exact symptom reported (MSFT has real "moderate" findings on 5 of 6 working dimensions and none of them get mentioned) |
| Primary Executive Summary is a separate, shorter frontend construction; the fuller backend narrative is one tab away | Backend narrative exists (when non-empty) but isn't the first thing shown | Frontend design choice (`ExecutiveSummaryCard` vs. `CaseNarrativeDetailSection`) | Low — surfacing/promoting existing content | Medium — makes existing backend work visible sooner, no new computation needed |
| `ensure_company_enriched` gate is document-kind-only, never field-level | A ticker ingested before a new field existed will never auto-pick it up | `assess_data_completeness` checks only which `SourceKind`s exist | Low-medium — add a schema/field-version stamp the gate can compare | Medium, systemic — protects every future field addition from silently going stale for already-ingested tickers |
| Revenue missing for MSFT FY2011–2015 while other line items are present | 5-year gap in a key metric | Likely an SEC XBRL tag-name variant not covered by `_DURATION_CONCEPT_TAGS`'s revenue mapping for that filing period (not independently confirmed — flagged as uncertain) | Low-medium, once confirmed — add fallback tag names | Medium — one company-specific but plausibly widespread gap (older filings across many companies may use the same older tag name) |
| Business Model / Competitive Position / Management / Durability | Permanently `insufficient_input`, by design, for every company | No qualitative provider, no content-interpreting evaluator exists anywhere in the codebase | High — genuinely new capability (data source + evaluator), explicitly out of scope for "smallest sequence" work | High long-term, but not the near-term lever |
| Expected Return / scenario valuation | Zero backend representation | Never built | High — new valuation methodology | Medium-high, but large scope |
| Portfolio Fit (active pipeline) | Hardcoded unavailable | Deliberate DE-003 doctrine boundary; a real engine exists but is architecturally quarantined and would need input-contract redesign to reintegrate | High — not a simple "call the existing function," despite the function existing | Medium-high, but genuinely complex, not a quick win |

---

## 7. Recommended implementation order (smallest sequence, largest quality lift — not new features, no redesign)

1. **Extend the narrative synthesizer to speak about moderate/neutral findings**, not only extremes. This is the single highest-leverage, lowest-difficulty change identified: MSFT already has confident, well-evidenced conclusions on Growth, Capital Allocation, Valuation, and 3 of 4 Risk categories — none of it currently reaches the thesis narrative purely because none of it is STRONG/WEAK/UNDERVALUED/EXPENSIVE/LOW/HIGH. Fixing this alone would change MSFT's `atlasThesis.posture` from `insufficient_data` to something substantive, without touching any provider, evaluator, or the evidence-coverage gate.
2. **Promote the backend's fuller `atlasThesis.narrative` to the primary Executive Summary surface** (or otherwise make it visibly first), rather than leaving it in the secondary "More Details" tab behind a separately-constructed, shorter frontend summary. Zero new backend computation required — this is a presentation change that surfaces work already being done.
3. **Confirm, explicitly, whether the evidence-coverage gate on Conviction/Recommendation is intended product doctrine or an oversight.** If intended (analysis should never imply a "conviction" without recorded investor judgment), that's worth stating plainly in-product rather than leaving users to interpret "insufficient evidence" as a data-quality complaint. If not intended, this is the highest-impact fix in the entire audit, but it's a product decision this report should not make unilaterally.
4. **Make the `ensure_company_enriched` completeness gate field-aware** (or at least version-aware), so future field additions to the extraction pipeline (the way `total_debt` itself was added) don't silently skip every already-ingested ticker forever. Low effort, protects all future ingestion work.
5. **Confirm and fix the MSFT FY2011–2015 revenue gap** — first by reproducing it directly against the SEC EDGAR raw JSON to identify the exact tag-name variant in use for that filing window, then adding the fallback mapping. Likely affects other companies with older filings, not just MSFT.

Explicitly **not recommended** as near-term work, despite being real gaps: a qualitative business-analysis capability (Business Model/Competitive Position/Management/Durability) and a scenario-based Expected Return valuation — both require genuinely new capabilities (a new data source plus a new kind of evaluator), not wiring or presentation fixes, and are correctly out of scope for "smallest sequence, largest impact."

---

## Uncertainties explicitly flagged

- How the running backend process actually sources `ALPHA_VANTAGE_API_KEY` from `.env` (no in-repo `.env`-loading code was found) was not independently confirmed.
- The exact SEC XBRL tag-name variant responsible for MSFT's FY2011–2015 revenue gap was not identified — flagged as a real, confirmed symptom with a plausible but unverified cause.
- Whether the Conviction/Recommendation evidence-coverage gate is intended product doctrine versus an unintentional gap was not something this read-only, code-only audit could resolve — it requires a product decision, not more code reading.
- A `.claude/worktrees/charming-satoshi-c1c8e3/` directory exists containing a parallel, more extensive `docs/` tree (weekly review, storage/architecture consolidation, a "V1 release candidate") that appears unrelated to the current working tree and was not investigated as part of this audit — noted only because it may explain the previously-observed unrelated `test_weekly_review_*` test failures in the main tree (stale references to a feature that may live in that other worktree).
