# Atlas Weekly Investment Review — Workflow Specification

**Created:** 2026-07-03 (Sprint 209)  
**Status:** SPECIFIED (Sprint 209) + INPUT SCHEMAS IMPLEMENTED (Sprint 210) + CLI SKELETON IMPLEMENTED (Sprint 211) + DETERMINISTIC RENDERER IMPLEMENTED (Sprint 212) + REAL PORTFOLIO TRIAL RUN (Sprint 213) + JOURNAL AGING ALERTS (Sprint 214) + V1 USAGE GUIDE (Sprint 215) + RELEASE HARDENED (Sprint 216) + INTERNAL V1 RC FROZEN (Sprint 217) + PROFILE PRINCIPLES AND CONSTRAINTS RENDERED (Sprint 218) + PER-TICKER EVIDENCE PRESENCE CHECKS (Sprint 219). Sprint 220 recommendation: Run second real portfolio trial.

---

## Product Boundary

Atlas Weekly Investment Review is a CLI-first, deterministic weekly workflow that combines local portfolio input, watchlist items, company reviews, suitability checks, risk/principle guardrails, open decisions, and missing evidence into a structured review. It helps the user decide what deserves further attention, what should remain on watch, and what evidence is missing. It does not provide buy/sell recommendations, price targets, market-timing signals, live news, live market data, or automated trading guidance.

---

## What Problem This Solves

Without a repeatable review workflow, an investor has no structured way to:
- Surface which companies or watchlist items need attention this week
- Track open decisions and their follow-up triggers
- Identify evidence gaps before they become decision-time surprises
- Explicitly record "no action warranted" as a valid outcome
- Separate reasoning from noise and market-timing temptation

The Atlas Weekly Investment Review answers the same questions every week in a consistent, deterministic order.

---

## Workflow Steps

```
1.  Load and validate local inputs
2.  Establish review scope
3.  Summarize portfolio context
4.  Review watchlist items
5.  Identify companies needing attention
6.  Run or reference company review outputs
7.  Evaluate portfolio fit and suitability notes
8.  Review risk and principle guardrails
9.  Review open decisions and follow-up triggers
10. Compile missing evidence
11. Generate non-actions / reasons to wait
12. Render Weekly Investment Review output
```

### Step 1 — Load and validate local inputs

- **Purpose:** Load portfolio, watchlist, and investor profile from local files. Validate required files are present. Warn on missing optional files.
- **Inputs:** All CLI arguments (file paths)
- **Existing capability:** `atlas.adapters.portfolio.Portfolio.from_json_file`, `atlas.profile.InvestorProfileEngine.load_profile`, `atlas.watchlist_review.watchlist_review_input_from_json_file`
- **Expected output:** Loaded data structs or validation errors
- **Failure behavior:** Missing required file → exit with clear error. Missing optional file → continue with warning.
- **Required:** Yes
- **Guardrails:** No live data fetched. No network calls.

### Step 2 — Establish review scope

- **Purpose:** Determine what is being reviewed and why. Record the review date and the scope (which tickers, which watchlist, optional user-supplied scope notes).
- **Inputs:** `--as-of`, `--scope-notes`, portfolio tickers, watchlist items
- **Existing capability:** None (new logic required)
- **Expected output:** Review scope record (date, item count, tickers in scope, user notes)
- **Failure behavior:** Defaults to current date if `--as-of` not supplied.
- **Required:** Yes
- **Guardrails:** Scope is descriptive only. No ranking or prioritization at this step.

### Step 3 — Summarize portfolio context

- **Purpose:** Produce a concise summary of the current portfolio: holdings, sector/country exposure, concentration, cash position, quality/risk profile.
- **Inputs:** Portfolio file
- **Existing capability:** `atlas.adapters.portfolio.Portfolio`, `atlas.adapters.portfolio.legacy_portfolio_to_domain_portfolio`, `atlas.capabilities.portfolio_intelligence.PortfolioFitEngine`
- **Expected output:** Portfolio summary — holdings list, top sectors, concentration signals, quality/risk summary
- **Failure behavior:** Missing market values → exclude from exposure calculations, emit warning. Unknown sector → classify as "Unclassified".
- **Required:** Yes (portfolio file required)
- **Guardrails:** No live price dependency. Uses user-supplied weights or market values only.

### Step 4 — Review watchlist items

- **Purpose:** Surface current state of each watchlist item: status, open questions, evidence needed, notes.
- **Inputs:** Watchlist file, investor profile (optional), company analysis provider (mock default)
- **Existing capability:** `atlas.watchlist_review.WatchlistReviewEngine`, `atlas.watchlist_review.watchlist_review_input_from_json_file`, `atlas.capabilities.watchlist_intelligence.WatchlistIntelligenceEngine`
- **Expected output:** Per-item status, open questions, evidence needed, priority signals
- **Failure behavior:** Missing watchlist file → fail (required). Empty watchlist → produce "No watchlist items" note.
- **Required:** Yes (watchlist file required)
- **Guardrails:** No buy/sell/urgent language per item. "Needs More Evidence" and "Continue Research" are acceptable status labels.

### Step 5 — Identify companies needing attention

- **Purpose:** From the portfolio + watchlist, identify which companies are due for review based on: stale analysis, open questions, evidence gaps, decisions pending, or risk drift.
- **Inputs:** Portfolio, watchlist, decision journal (optional)
- **Existing capability:** Partial — `atlas.capabilities.watchlist_intelligence.WatchlistIntelligenceReport.companies_needing_attention`
- **Expected output:** List of tickers or names flagged for attention, with reason for flagging
- **Failure behavior:** No companies flagged → produce explicit "No companies flagged for attention this week" note (valid outcome).
- **Required:** Yes
- **Guardrails:** Attention flags are evidence-driven, not price-driven. Explicit "none" is always a valid outcome.

### Step 6 — Run or reference company review outputs

- **Purpose:** For each company flagged in Step 5, include a summary of the latest company analysis or note that no recent analysis exists.
- **Inputs:** Tickers from Step 5, optional `--company-facts` directory, optional `--financials` directory
- **Existing capability:** `atlas report <TICKER>` → `atlas.analysis.AtlasInvestmentEngine`, `atlas.capabilities.company_analysis.CompanyAnalysisCapability`
- **Expected output:** Per-company summary (key scored factors, evidence summary, confidence, missing information) or "No company analysis available — evidence gap noted."
- **Failure behavior:** Missing company data → produce evidence-gap warning and continue. Do not fail the full review.
- **Required:** Optional — runs only for tickers flagged in Step 5
- **Guardrails:** No recommendation language. No price targets. Output framed as "analysis of available evidence" only.

### Step 7 — Evaluate portfolio fit and suitability notes

- **Purpose:** For flagged companies, surface portfolio fit and profile compatibility signals.
- **Inputs:** Portfolio, investor profile, company analysis from Step 6
- **Existing capability:** `atlas.suitability.SuitabilityEngine`, `atlas.capabilities.portfolio_intelligence.PortfolioFitEngine`
- **Expected output:** Per-company suitability and fit notes (fit factors, mismatches, concentration signals)
- **Failure behavior:** Missing investor profile → use default profile with warning. Missing company analysis → skip suitability and note gap.
- **Required:** Optional — runs for flagged companies only
- **Guardrails:** Anti-advice disclaimer required. "Not Suitable Under Current Constraints" is acceptable; "Don't Buy" is not.

### Step 8 — Review risk and principle guardrails

- **Purpose:** Surface active risk drift signals and any principle concerns across the portfolio and watchlist.
- **Inputs:** Portfolio, investor profile, company analysis (optional)
- **Existing capability:** `atlas.risk.RiskEngine`, `atlas.principles.PrinciplesEngine`, `atlas risk-drift analyze`, `atlas principles check`
- **Expected output:** Risk drift signals (if any), principle concerns (if any), or explicit "No active drift signals" note.
- **Failure behavior:** No risk input → produce "Risk drift analysis not available — no prior risk state provided."
- **Required:** Optional
- **Guardrails:** Risk signals are descriptive ("Risk to Monitor"), not directives ("Exit position"). No urgent action language.

### Step 9 — Review open decisions and follow-up triggers

- **Purpose:** List all open decisions from the decision journal, with last-review date, status, and follow-up trigger.
- **Inputs:** Decision journal file (`.atlas/decision_journal.json` or `--journal` argument)
- **Existing capability:** `atlas.decision_journal.DecisionJournalEngine.load_entries`, `atlas.decision_journal.render_decision_journal_entries`
- **Expected output:** List of open decisions with status, date, thesis summary, and follow-up trigger. Or "No journal input provided."
- **Failure behavior:** Missing journal → continue with "No journal input provided." This is a valid state.
- **Required:** Optional
- **Guardrails:** No buy/sell language in decision status. Permitted statuses defined in Decision Memo spec. "Decision Deferred" and "Needs More Evidence" are valid open statuses.

### Step 10 — Compile missing evidence

- **Purpose:** Collect all evidence gaps surfaced across all prior steps into one consolidated list.
- **Inputs:** Watchlist review, company analysis, suitability notes, decision journal
- **Existing capability:** `atlas.evidence.EvidenceEngine` (internal, surfaces through `atlas analyze`), `atlas.capabilities.watchlist_intelligence.WatchlistIntelligenceReport.evidence_gaps`
- **Expected output:** Deduplicated list of evidence gaps with source (watchlist item, company, decision)
- **Failure behavior:** No gaps identified → produce explicit "No evidence gaps identified this week."
- **Required:** Yes
- **Guardrails:** Evidence gaps are stated as facts ("Margin durability for XYL not yet reviewed"), not as action items ("You must research XYL margins").

### Step 11 — Generate non-actions / reasons to wait

- **Purpose:** Explicitly record cases where no action is warranted. This section is required and must always be present.
- **Inputs:** All prior step outputs
- **Existing capability:** None — new logic required. Currently no Atlas output guarantees a "no action warranted" section.
- **Expected output:** Explicit list of cases, portfolio positions, or watchlist items where the conclusion is "no action warranted" and the reason.
- **Failure behavior:** This step cannot fail. If no other content is available, produce "No action warranted this week. Maintain current positions and watchlist. Continue research as evidence becomes available."
- **Required:** Yes — must always be present
- **Guardrails:** "No Action Warranted" is a first-class outcome. This section must never be empty or omitted.

### Step 12 — Render Weekly Investment Review output

- **Purpose:** Assemble all step outputs into the 10-section Weekly Investment Review output format.
- **Inputs:** All prior step outputs
- **Existing capability:** None — new renderer required
- **Expected output:** Rendered Weekly Investment Review (markdown or rich text)
- **Failure behavior:** Any step with no output produces an explicit "Not available" note in its section.
- **Required:** Yes
- **Guardrails:** Rendering applies language guardrail scan. All 10 sections present. Section 10 (Non-Actions) must never be empty.

---

## Planned CLI Entrypoint

### Full command

```bash
atlas weekly-review \
  --portfolio examples/portfolio.json \
  --watchlist examples/watchlist.json \
  --profile examples/investor_profile.json \
  --journal .atlas/decision_journal.json \
  --company-facts examples/company_facts \
  --financials examples/financials \
  --as-of 2026-01-01 \
  --scope-notes "Q1 2026 review — focus on semiconductor positions"
```

### Minimal command

```bash
atlas weekly-review \
  --portfolio examples/portfolio.json \
  --watchlist examples/watchlist.json \
  --profile examples/investor_profile.json
```

### Argument specification

| Argument | Required | Type | Default | Purpose |
|---|---|---|---|---|
| `--portfolio` | **Required** | File path | None | Portfolio JSON file |
| `--watchlist` | **Required** | File path | None | Watchlist JSON file |
| `--profile` | **Required** | File path | None | Investor profile JSON file |
| `--journal` | Optional | File path | `.atlas/decision_journal.json` | Decision journal file |
| `--company-facts` | Optional | Directory path | None | Directory of per-ticker company facts JSON |
| `--financials` | Optional | Directory path | None | Directory of per-ticker financial history CSV |
| `--as-of` | Optional | Date (ISO 8601) | Current date | Review date |
| `--scope-notes` | Optional | String | None | User-supplied review scope annotation |

### Exit codes

- `0` — review completed successfully
- `1` — required file missing or unreadable
- `2` — required file has invalid format

### Command placement

- `atlas weekly-review` at root level (not under a subgroup)
- Parallel to `atlas daily summary` and `atlas home` as a top-level workflow command
- Not a replacement for `atlas daily summary` — the daily brief is a lighter, faster overview; the weekly review is the deeper weekly workflow

### Relationship to existing commands

| Existing command | Role in Weekly Review |
|---|---|
| `atlas daily summary` | Lighter daily brief; weekly-review is the deeper weekly version |
| `atlas home` | Home engine currently orchestrates portfolio + watchlist + profile; weekly-review will use the same engines but add journal + evidence + non-actions |
| `atlas report <TICKER>` | Company analysis step (Step 6); weekly-review calls this logic per flagged ticker |
| `atlas suitability analyze` | Suitability step (Step 7); weekly-review calls this logic per flagged ticker |
| `atlas watchlist review` | Watchlist step (Step 4); weekly-review uses `WatchlistReviewEngine` |
| `atlas journal review` | Decision journal step (Step 9); weekly-review calls `DecisionJournalEngine.load_entries` |
| `atlas risk-drift analyze` | Risk guardrail step (Step 8); weekly-review calls `RiskEngine` |

---

## Input Specifications

### Portfolio Input

**File:** `portfolio.json` (user-supplied, any path, passed via `--portfolio`)

**Existing support:** `atlas.adapters.portfolio.Portfolio.from_json_file` — **parser exists**. Required fields: `ticker`, `company`, `sector`, `country`, `market_cap`, `weight`, `quality_score`, `risk_score` per position.

**Current format (existing):**

```json
{
  "_comment": "Atlas portfolio. Not real holdings. No investment advice.",
  "positions": [
    {
      "ticker": "ASML",
      "company": "ASML Holding",
      "sector": "Semiconductors",
      "country": "Netherlands",
      "market_cap": 285000,
      "weight": 0.18,
      "quality_score": 85,
      "risk_score": 40
    }
  ]
}
```

**v1 extended format (new fields, backward-compatible):**

```json
{
  "as_of": "2026-01-01",
  "_comment": "Atlas portfolio. Not real holdings. No investment advice.",
  "accounts": [
    {
      "name": "Private",
      "holdings": [
        {
          "name": "ASML Holding",
          "ticker": "ASML",
          "isin": "NL0010273215",
          "currency": "EUR",
          "quantity": 10,
          "market_value": 95000,
          "cost_basis": 82000,
          "sector": "Semiconductors",
          "country": "Netherlands",
          "quality_score": 85,
          "risk_score": 40,
          "role": "Core holding",
          "notes": "Quality compounder"
        }
      ]
    }
  ]
}
```

**Note:** The extended format is the v1 target. Sprint 210 should decide whether to add `accounts`-based parsing or keep the flat `positions` format with new optional fields. The existing parser can load v1 portfolios today if they use the `positions` list. The extended format requires a new parser.

| Field | Required | Notes |
|---|---|---|
| `positions` OR `accounts[].holdings` | Required | At least one holding required |
| `ticker` | Required | Uppercase ticker symbol |
| `company` or `name` | Required | Human-readable company name |
| `sector` | Required | Sector classification; use "Unclassified" if unknown |
| `country` | Optional | Country of listing or incorporation |
| `weight` | Required if no `market_value` | Fractional weight (0.0–1.0 or 0–100) |
| `market_value` | Optional | Absolute position value in `currency`; used instead of weight if provided |
| `cost_basis` | Optional | Original cost; not used in weekly review calculations |
| `quality_score` | Optional | 0–100 atlas quality score; defaults to 50 if absent |
| `risk_score` | Optional | 0–100 atlas risk score; defaults to 50 if absent |
| `currency` | Optional | ISO 4217 currency code; defaults to "USD" |
| `role` | Optional | Free text describing portfolio role |
| `notes` | Optional | Free text user annotation |
| `as_of` | Optional | ISO 8601 date of last update |
| `isin` | Optional | ISIN for reference; not used in calculations |

**Missing market value:** Exclude position from absolute-value calculations; use weight for relative calculations. Emit warning.

**Unknown sector:** Classify as "Unclassified". Continue. No error.

**Multiple accounts:** Merge holdings for weekly review calculations. Preserve account names in output.

**Live market dependency:** None. All values are user-supplied.

**Validation:** Missing `positions` or empty positions → fail with error. Missing required per-position fields → fail with error listing missing fields.

---

### Watchlist Input

**File:** `watchlist.json` (user-supplied, any path, passed via `--watchlist`)

**Existing support (partial):**
- `atlas.capabilities.watchlist_intelligence.WatchlistInput.from_json_file` — parser exists but accepts only `{"name": ..., "tickers": [...]}` (ticker-only format). **Gap: does not accept richer per-item fields.**
- `atlas.watchlist_review.watchlist_review_input_from_json_file` — accepts the demo format (`name`, `items[]` with `id`, `ticker`, `company`, `status`, `open_questions`, `manual_observations`). This is the closer match.

**v1 watchlist format:**

```json
{
  "name": "My Watchlist",
  "as_of": "2026-01-01",
  "items": [
    {
      "ticker": "XYL",
      "name": "Xylem",
      "status": "researching",
      "reason": "Water infrastructure theme",
      "evidence_needed": [
        "Margin durability under commodity cost cycles",
        "Valuation context relative to peers",
        "Portfolio overlap with existing holdings"
      ],
      "open_questions": [
        "Is revenue mix shifting toward higher-margin software services?",
        "What is the capital allocation track record?"
      ],
      "manual_observations": [
        "Exposed to water infrastructure spending cycles.",
        "No position currently. Research in early stage."
      ],
      "notes": "Potential long-term water infrastructure candidate."
    }
  ]
}
```

**Allowed statuses** (from `atlas.capabilities.watchlist_intelligence.WatchlistStatus`):

| Status | Meaning |
|---|---|
| `observing` | Awareness only — no active research |
| `researching` | Active research underway |
| `needs_more_evidence` | Research started but gaps remain |
| `thesis_forming` | Evidence sufficient to form initial thesis |
| `ready_for_review` | Ready for suitability and fit review |
| `paused` | Research paused; review on trigger |
| `archived` | Removed from active consideration |

| Field | Required | Notes |
|---|---|---|
| `name` | Optional | Watchlist name; defaults to "Watchlist" |
| `as_of` | Optional | Date of last update |
| `items` | Required | Non-empty list of watchlist items |
| `items[].ticker` | Required | Uppercase ticker symbol |
| `items[].name` | Optional | Human-readable company name |
| `items[].status` | Optional | One of allowed statuses above; defaults to "observing" |
| `items[].reason` | Optional | Why this item is on the watchlist |
| `items[].evidence_needed` | Optional | List of evidence gaps to fill |
| `items[].open_questions` | Optional | List of unresolved research questions |
| `items[].manual_observations` | Optional | Free-text observations already made |
| `items[].notes` | Optional | Free-text user annotation |

**Missing evidence handling:** `evidence_needed` feeds directly into the Missing Evidence section (Section 8) of the weekly review.

**No action language:** Watchlist item review must not emit buy/sell/urgent language. Allowed: "Needs More Evidence", "Continue Research", "Reason to Wait", "Evidence Gap".

**Gap:** The existing `WatchlistInput.from_mapping` (in `watchlist_intelligence/models.py`) accepts only a flat `tickers` list. Sprint 210 must extend or create a new parser for the richer watchlist format. The `watchlist_review/engine.py` format (with `open_questions`, `manual_observations`) is the closest existing parser; the v1 format is an extension of this.

---

### Investor Profile Input

**File:** `investor_profile.json` (user-supplied, any path, passed via `--profile`)

**Existing support:** `atlas.profile.InvestorProfileEngine.load_profile` — **parser exists**. Required fields: `investment_goals` (list), `portfolio_purpose`, `risk_preference`, `risk_tolerance`, `risk_capacity`, `time_horizon`.

**Allowed enum values** (from `atlas.profile.engine`):

| Field | Allowed values |
|---|---|
| `investment_goals` | `"Wealth accumulation"`, `"Retirement"`, `"Income"`, `"Financial Independence"`, `"Capital Preservation"`, `"Learning"`, `"Experimental Portfolio"` |
| `portfolio_purpose` | `"Core Portfolio"`, `"Growth Portfolio"`, `"Income Portfolio"`, `"Exploration Portfolio"`, `"High Conviction Portfolio"` |
| `risk_preference` | `"Conservative"`, `"Balanced"`, `"Growth"`, `"Aggressive"` |
| `risk_tolerance` | `"Conservative"`, `"Balanced"`, `"Growth"`, `"Aggressive"` |
| `risk_capacity` | `"Low"`, `"Medium"`, `"High"` |
| `time_horizon` | `"<3 years"`, `"3-10 years"`, `"10+ years"` |

**v1 investor profile format:**

```json
{
  "name": "My Profile",
  "investment_goals": ["Wealth accumulation"],
  "portfolio_purpose": "Core Portfolio",
  "risk_preference": "Balanced",
  "risk_tolerance": "Balanced",
  "risk_capacity": "Medium",
  "time_horizon": "10+ years",
  "principles": [
    "Evidence before opinion",
    "Avoid forced selling",
    "Keep reserve capacity",
    "Prefer quality businesses",
    "No action is an acceptable outcome"
  ],
  "constraints": [
    "Avoid excessive concentration in any single sector",
    "Avoid decisions based only on recent price movement"
  ],
  "notes": "Long-term portfolio. Quality over speed."
}
```

**Note:** `principles` and `constraints` are new optional fields not yet parsed by `atlas.profile.InvestorProfileEngine`. Sprint 210 should add these to `InvestorProfile` or handle them in the weekly-review input loader. The existing parser ignores unknown fields gracefully (via `payload.get`).

| Field | Required | Notes |
|---|---|---|
| `investment_goals` | Required | Non-empty list of goal strings |
| `portfolio_purpose` | Required | Enum value |
| `risk_preference` | Required | Enum value |
| `risk_tolerance` | Required | Enum value |
| `risk_capacity` | Required | Enum value |
| `time_horizon` | Required | Enum value |
| `name` | Optional | Investor name; defaults to "Atlas Investor" |
| `principles` | Optional | Free-text principles list; used in risk and guardrail review |
| `constraints` | Optional | Free-text constraints list; used in suitability and fit checks |
| `notes` | Optional | Free-text annotation |

**Suitability usage:** Profile fields map directly to `atlas.suitability.SuitabilityInput` for per-company suitability checks.

**Principles usage:** `principles` list feeds into `atlas.principles.PrinciplesEngine.check` (Step 8) and into the Non-Actions section.

**Risk guardrail usage:** `risk_tolerance` and `risk_capacity` feed into `atlas.risk.RiskEngine`.

**Missing profile:** If `--profile` is not supplied, `InvestorProfileEngine.create_default_profile()` is used with a visible warning: "Using default investor profile. Suitability and fit results may not reflect your actual profile."

**Financial advice framing:** Profile describes the investor's stated preferences. Output must say "compatible with this profile" or "not compatible with this profile", never "you should" or "this is right for you".

---

### Decision Journal Input

**File:** `.atlas/decision_journal.json` (default) or `--journal` argument

**Existing support:** `atlas.decision_journal.DecisionJournalEngine.load_entries` — **parser exists**. File is a JSON array of decision entry objects. Path is `.atlas/decision_journal.json` relative to the project root.

**Format:** Existing format defined by `_entry_from_mapping` in `atlas/decision_journal/engine.py`. Required fields per entry: `entry_id`, `decision_title`, `asset_or_idea`, `decision_type`, `decision_date`, `investor_profile_context`, `portfolio_context_summary`, `atlas_rating`, `atlas_view`, `atlas_fit`, `atlas_confidence`, `investment_thesis`, `evidence_quality`, `evidence_summary`.

**Weekly review usage:** Load all entries, filter to open decisions (status not in closed set), surface in Section 7 (Open Decisions).

**Open decision status handling:** Entries with status `Continue Research`, `Needs More Evidence`, `Watchlist`, or `Decision Deferred` are considered open for the purposes of the weekly review. Entries with status `Suitable for Further Review` or `Not Suitable Under Current Constraints` are also surfaced if the `follow_up_triggers` field is non-empty and the follow-up date is past or absent.

**Missing journal:** Continue review with "No journal input provided. Open decisions not reviewed." This is a valid state — no error.

**Deferred decisions:** Decisions with status `Decision Deferred` must appear in the Non-Actions section (Section 10) as well as Section 7.

**New entry vs. reading:** Weekly review reads existing journal entries only. It does not create new entries. Journal creation remains in `atlas journal create`.

---

### Company Facts Input

**Directory:** `company_facts/` (optional, passed via `--company-facts`)

**Format:** One JSON file per ticker, e.g., `company_facts/ASML.json`.

**Purpose:** Supply manual company facts (business description, competitive position, revenue model, key risks) that feed into company analysis (`atlas report`, `atlas analyze`) without requiring a live provider.

**Existing support:** `atlas report` and `atlas analyze` accept company facts as structured input to `atlas.analysis.AtlasInvestmentEngine`. The exact intake path depends on how company facts are passed — this is not yet a standardized file-based input convention. **Gap: no standard `company_facts/<ticker>.json` convention or parser exists yet.**

**Minimal structure:**

```json
{
  "ticker": "ASML",
  "name": "ASML Holding",
  "business": "ASML designs and manufactures photolithography machines used in semiconductor fabrication.",
  "competitive_position": "Sole supplier of EUV lithography systems worldwide.",
  "revenue_model": "Equipment sales and long-term service contracts.",
  "key_risks": [
    "Export controls limiting sales to certain countries",
    "Customer concentration among leading-edge chip manufacturers",
    "Long technology development cycles"
  ],
  "notes": "No position currently. Researching for potential addition."
}
```

**Effect on weekly review:** If a company facts file exists for a ticker flagged in Step 5, its data is passed into the company analysis step (Step 6). If not, company analysis proceeds without manual facts and notes the absence as an evidence gap.

**Missing company data:** Do not fail the full weekly review. Produce: "Company facts not available for [TICKER] — evidence gap noted."

---

### Financial History Input

**Directory:** `financials/` (optional, passed via `--financials`)

**Format:** One CSV file per ticker, e.g., `financials/ASML.csv`. Importable via `atlas import-financials`.

**Purpose:** Supply historical financial data (revenue, earnings, margins, free cash flow) for company analysis scoring in the weekly review.

**Existing support:** `atlas.services.financial_import_service.FinancialImportService` and `atlas import-financials` CLI command. Data is persisted to the Atlas SQLite database. **Gap: `atlas weekly-review` would need to read from the database or accept a CSV directory directly — the current path is import-then-read-from-DB, not direct CSV-to-analysis.**

**Minimal CSV format (existing Atlas convention):**

```csv
ticker,fiscal_year,revenue,net_income,free_cash_flow,total_assets,total_equity
ASML,2023,27558,7830,3200,28700,14200
ASML,2022,21173,5621,2700,24100,12400
```

**Effect on weekly review:** If financial history exists for a flagged company (in the database or CSV directory), it feeds into the quality/growth/financial-strength scoring. If not, scoring proceeds on defaults and notes the absence as an evidence gap.

**Missing financial history:** Do not fail. Produce: "Financial history not available for [TICKER] — quality and growth scoring may be incomplete."

---

## Output Sections

### Section 1 — Review Scope

**Purpose:** Establish what is being reviewed and why.

**Required content:**
- Review date (`as_of`)
- Items in scope (portfolio holdings count, watchlist item count)
- Companies flagged for review this week
- User-supplied scope notes (if provided)

**Optional content:**
- Prior review date if trackable

**Forbidden:** No ranking language ("most important", "top priority"). No urgency.

**Example heading:** `## 1. Review Scope`

**Example safe phrasing:**
```
Review date: 2026-01-05
Portfolio: 5 positions reviewed
Watchlist: 3 items reviewed
Companies flagged for attention: ASML, XYL
Scope notes: Q1 2026 — focus on semiconductor and water infrastructure positions.
```

---

### Section 2 — Portfolio Context

**Purpose:** Summarize current portfolio composition without recommendation language.

**Required content:**
- Holdings list with weights/values
- Sector and country concentration
- Top holdings by weight
- Cash or reserve position (if any)
- Quality and risk summary (average scores if available)

**Optional content:**
- Account breakdown (if multiple accounts)
- Cost basis vs. current value (if supplied)
- Unclassified holdings with explanation

**Forbidden:** No buy/sell language. No "overweight / underweight" in recommendation sense. No price targets. No commentary on whether concentration is "too high".

**Acceptance criteria:** All holdings present. Weights sum to ~1.0 or warning produced. Unknown sectors labeled "Unclassified".

**Example heading:** `## 2. Portfolio Context`

**Example safe phrasing:**
```
Holdings: ASML (18%), MSFT (15%), XYL (12%), Cash (55%)
Top sector: Technology (33%)
Cash / reserve: 55%
Average quality score: 82 | Average risk score: 38
Note: Market values are user-supplied as of 2026-01-01.
```

---

### Section 3 — Watchlist Review

**Purpose:** Surface the current state of each watchlist item.

**Required content:**
- Per-item: ticker, name, status, reason for watchlist inclusion
- Per-item: open questions (if any)
- Per-item: evidence needed (if any)
- Per-item: last observations (if any)
- Items due for review or with changed status

**Optional content:**
- Items recently added or removed
- Items paused (with reason and trigger for resumption)

**Forbidden:** No buy/sell/urgent language per item. No price targets. "Suitable for Further Review" acceptable; "Should Buy" not acceptable.

**Acceptance criteria:** All watchlist items present. No item missing its status. Evidence gaps fed forward to Section 8.

**Example heading:** `## 3. Watchlist Review`

**Example safe phrasing:**
```
XYL — Xylem | Status: Researching
Reason: Water infrastructure theme
Open questions: Margin durability; capital allocation track record
Evidence needed: Valuation context; portfolio overlap assessment
Observations: No active position. Research in early stage.
```

---

### Section 4 — Company Reviews Needing Attention

**Purpose:** For each company flagged in Step 5, include a structured summary of the latest analysis.

**Required content:**
- Ticker and company name
- Analysis summary: key scored factors, overall confidence, evidence summary
- Missing information (what Atlas does not know)

**Optional content:**
- Score breakdown by dimension (quality, growth, financial strength, valuation, risk)
- Recent changes to evidence or assumptions

**Forbidden:** No recommendation language. No price targets. No "you should add/remove this position."

**Acceptance criteria:** Every flagged company has an entry. If no analysis available, entry reads "No company analysis available — evidence gap noted."

**Example heading:** `## 4. Company Reviews Needing Attention`

**Example safe phrasing:**
```
ASML — ASML Holding
Confidence: Medium | Quality: 85 | Risk: 40
Evidence summary: EUV monopoly well-documented; export control exposure unresolved.
Missing information: Impact of US export restrictions on 2024–2026 revenue.
```

---

### Section 5 — Portfolio Fit and Suitability Notes

**Purpose:** Surface profile compatibility and concentration signals for flagged companies.

**Required content:**
- Per-company: suitability compatibility (fit factors and mismatches)
- Per-company: portfolio concentration signal (if adding this would increase concentration)
- Assumptions made (e.g., "Atlas assumed long-term time horizon")

**Optional content:**
- Portfolio-level suitability drift (if profile changed)

**Forbidden:** No advice language. No "you should" framing. Anti-advice disclaimer required.

**Acceptance criteria:** Every flagged company has a suitability note or an explicit "Suitability check not available — investor profile missing or incomplete."

**Example heading:** `## 5. Portfolio Fit and Suitability Notes`

**Example safe phrasing:**
```
ASML — Suitability check
Compatible factors: Long time horizon aligns with capital-intensive business cycle.
Mismatches: Moderate risk tolerance may be stretched by export control exposure.
Concentration: Adding ASML at 15% would increase Technology sector to 48%.
Note: Atlas does not judge investment merit or provide personalized financial advice.
```

---

### Section 6 — Risk and Principle Guardrails

**Purpose:** Surface active risk drift signals and principle concerns.

**Required content:**
- Active risk drift signals (if any), with affected ticker and description
- Principle concerns (if any), with affected text and concern
- Explicit "No active drift signals" note if none found

**Optional content:**
- Investor principles from profile (as context)
- Suggested assumptions to recheck (not actions)

**Forbidden:** No "exit position" language. No urgency. Signals are observations, not directives.

**Acceptance criteria:** Section always present. "No active drift signals" is a valid and acceptable result.

**Example heading:** `## 6. Risk and Principle Guardrails`

**Example safe phrasing:**
```
Risk to Monitor: Semiconductor sector concentration (ASML + NVDA) has increased to 33%.
Assumption to Recheck: Original thesis for NVDA assumed stable hyperscaler demand — this assumption should be verified.
No principle concerns detected this week.
```

---

### Section 7 — Open Decisions

**Purpose:** List open decisions from the decision journal with status and follow-up triggers.

**Required content:**
- Per-decision: decision title, asset/idea, date, current status, follow-up trigger (if any)
- Deferred decisions must also appear in Section 10

**Optional content:**
- Evidence summary per decision (brief)
- Next review date

**Forbidden:** No buy/sell language in decision status.

**Acceptance criteria:** All open decisions listed. "No journal input provided" is an acceptable result if journal is absent.

**Example heading:** `## 7. Open Decisions`

**Example safe phrasing:**
```
XYL — Xylem | Status: Needs More Evidence
Date: 2025-11-15 | Trigger: Revisit when Q4 earnings available
Thesis: Potential water infrastructure exposure; evidence on margin durability incomplete.
```

---

### Section 8 — Missing Evidence

**Purpose:** Consolidated list of all evidence gaps surfaced this week.

**Required content:**
- Per-gap: what is missing, which company or watchlist item it affects, and which step surfaced it

**Optional content:**
- Suggested evidence sources (manual, no live data)

**Forbidden:** "You must find X" language. Evidence gaps are observations, not tasks.

**Acceptance criteria:** All gaps from Sections 3, 4, 5, 6, 7 consolidated here. "No evidence gaps identified this week" is a valid result.

**Example heading:** `## 8. Missing Evidence`

**Example safe phrasing:**
```
XYL: Margin durability under commodity cost cycles — not yet reviewed. (Source: Watchlist)
ASML: Impact of export control restrictions on 2024–2026 revenue — open research question. (Source: Company review)
NVDA: Long-term hyperscaler customer concentration — evidence incomplete. (Source: Watchlist)
```

---

### Section 9 — Follow-Up Questions

**Purpose:** Questions the user should consider answering before the next weekly review.

**Required content:**
- Questions derived from evidence gaps (Section 8), open decisions (Section 7), and risk signals (Section 6)

**Optional content:**
- Source of each question (which section surfaced it)

**Forbidden:** No "you must answer X" framing. Questions are offered, not required.

**Acceptance criteria:** At least one follow-up question if any evidence gaps or open decisions exist. "No follow-up questions this week" is valid if nothing outstanding.

**Example heading:** `## 9. Follow-Up Questions`

**Example safe phrasing:**
```
Has Xylem's margin profile changed in the most recent quarter?
Has ASML commented on the revenue impact of US export restrictions?
Has the hyperscaler spending environment changed in a way that affects the NVDA thesis?
```

---

### Section 10 — Non-Actions / Reasons to Wait

**Purpose:** Explicitly record cases where no action is warranted. This section is **always required and must never be empty**.

**Required content:**
- Cases, positions, or watchlist items where "no action warranted" is the conclusion
- Reason for each non-action (not just "no action")
- Deferred decisions from Section 7

**Optional content:**
- General "reasons to wait" for the portfolio as a whole

**Forbidden:** This section must never be omitted. "No action warranted" must never be framed as a negative outcome.

**Acceptance criteria:** Section always present. Even if everything is in active research, the section must include at least: "No action warranted this week. Continue current positions and research."

**Example heading:** `## 10. Non-Actions / Reasons to Wait`

**Example safe phrasing:**
```
ASML — No Action Warranted
Reason: Evidence on export control impact is incomplete. No basis for a position change until this is resolved.

XYL — Decision Deferred
Reason: Evidence on margin durability not yet reviewed. Revisit after Q4 earnings.

Portfolio — No Action Warranted
Reason: Current portfolio is within target parameters. No evidence of material thesis changes this week.

Reminder: No action is a valid and often appropriate outcome of a weekly review.
```

---

## Safe Output Language

### Allowed

| Term | When to use |
|---|---|
| Needs More Evidence | Watchlist item or decision missing key evidence |
| Continue Research | Ongoing research with no current conclusion |
| Watchlist | Item on active observation list |
| Suitable for Further Review | Profile-compatible; ready for deeper review |
| Not Suitable Under Current Constraints | Profile mismatch or principle conflict |
| Decision Deferred | Conditions not yet met for a decision |
| No Action Warranted | Current analysis supports maintaining the status quo |
| Reason to Wait | Specific identified reason to defer action |
| Evidence Gap | A specific piece of missing evidence |
| Risk to Monitor | A risk signal that warrants ongoing attention |
| Assumption to Recheck | An assumption that should be re-verified |
| Compatible factors | Suitability factors that align with the profile |
| Mismatches | Suitability factors that conflict with the profile |

### Forbidden

| Term | Why forbidden |
|---|---|
| Buy / Sell | Recommendation language |
| Strong Buy / Strong Sell | Recommendation language |
| Price Target / Target Price | Recommendation language |
| Urgent / Act Now | Urgency language |
| Must Buy / Must Sell | Directive language |
| Guaranteed / Will Outperform | Prediction language |
| Financial Advice / You should | Advice framing |
| Entry / Exit point | Trading signal language |
| Overweight / Underweight | Analyst rating language |
| Top Pick | Recommendation language |

### Output generation guardrail

Before rendering each section, the Weekly Investment Review renderer must pass the section text through `atlas.principles.PrinciplesEngine.check` or an equivalent language scan. Any forbidden term found must trigger a rendering error, not a silent pass-through.

---

## Failure and Missing Data Behavior

| Scenario | Behavior |
|---|---|
| Missing `--portfolio` file | **Fail** — exit code 1, clear error: "Required portfolio file not found: [path]" |
| Missing `--watchlist` file | **Fail** — exit code 1, clear error: "Required watchlist file not found: [path]" |
| Missing `--profile` file | **Warning** — use default profile, print: "Using default investor profile. Suitability results may not reflect your actual profile." |
| Invalid portfolio JSON | **Fail** — exit code 2, clear error: "Portfolio file is invalid: [error detail]" |
| Invalid watchlist JSON | **Fail** — exit code 2, clear error |
| Portfolio position missing required field | **Fail** — exit code 2, list missing fields |
| Missing optional `--journal` | **Continue** — Section 7 reads: "No journal input provided. Open decisions not reviewed." |
| Missing optional `--company-facts` | **Continue** — Step 6 skips company facts; evidence gap noted per ticker |
| Missing optional `--financials` | **Continue** — Step 6 skips financial history; evidence gap noted per ticker |
| Portfolio position missing market value | **Warning** — exclude from absolute calculations, use weight for relative calculations |
| Unknown sector in portfolio | **Continue** — classify as "Unclassified"; warn once |
| Watchlist item with unknown status | **Continue** — default to "observing" |
| No companies flagged for attention | **Continue** — Section 4 reads: "No companies flagged for attention this week." |
| No evidence gaps found | **Continue** — Section 8 reads: "No evidence gaps identified this week." |
| No open decisions | **Continue** — Section 7 reads: "No open decisions. Journal reviewed but no open entries found." |

### Warning format in output

Warnings appear as a `## Warnings` block at the top of the output, before Section 1, listing all non-blocking issues encountered during input loading:

```
## Warnings
- Using default investor profile (no --profile file supplied). Suitability results may not reflect your actual profile.
- Portfolio position CASH: market_value not supplied. Excluded from absolute calculations.
- No company facts found for XYL. Evidence gap noted.
```

### Deterministic behavior

All inputs are local and file-based. Same input files always produce the same output. No live data. No randomness. No LLM calls.

---

## Implementation Gap Analysis

### Input schema gaps

| Gap | Description | Priority |
|---|---|---|
| Rich watchlist format parser | `WatchlistInput.from_mapping` only accepts `tickers` list. Weekly review needs `items[]` with `status`, `evidence_needed`, `reason`, `open_questions`, `manual_observations`. | **High** |
| Portfolio `accounts`-based format | Current parser only handles flat `positions[]`. Extended format with `accounts[].holdings[]` not yet supported. | Medium |
| Investor profile `principles` and `constraints` | `InvestorProfile` does not have `principles` or `constraints` fields. Parser ignores them. | Medium |
| Company facts directory convention | No `company_facts/<ticker>.json` file convention or parser exists. | Medium |

### Parser gaps

| Gap | Description | Priority |
|---|---|---|
| Watchlist JSON parser for v1 format | Need new or extended parser that reads the full v1 watchlist format | **High** |
| Company facts JSON parser | Need parser that reads `company_facts/<ticker>.json` and maps to existing company analysis input | Medium |
| Weekly review input loader | Orchestrating parser that loads all inputs, validates required files, and warns on missing optional files | **High** |

### Workflow orchestration gaps

| Gap | Description | Priority |
|---|---|---|
| `atlas weekly-review` orchestrator | No top-level command or engine that calls the 12 workflow steps in sequence | **High** |
| "Companies needing attention" logic | No engine synthesizes portfolio + watchlist + journal to identify which tickers need attention this week | **High** |
| Evidence gap consolidation | No single aggregator collects gaps from watchlist, company analysis, suitability, and decision journal | Medium |
| Non-actions generator | No engine produces a "no action warranted" section — this is a new concept | **High** |
| Open decisions filter | No logic filters decision journal entries by open/closed status for weekly review | Medium |

### Renderer gaps

| Gap | Description | Priority |
|---|---|---|
| Weekly review renderer | No `render_weekly_investment_review()` function exists | **High** |
| Multi-section assembler | No renderer combines 10 sections into one structured document | **High** |
| Warnings block renderer | No standard format for warnings at the top of output | Low |

### CLI wiring gaps

| Gap | Description | Priority |
|---|---|---|
| `atlas weekly-review` command | No CLI command registered | **High** |
| Required/optional argument handling | No argument parser for the weekly-review command arguments | **High** |

### Sample data gaps

| Gap | Description | Priority |
|---|---|---|
| `examples/weekly_review/portfolio.json` | No sample portfolio in the v1 format | **High** |
| `examples/weekly_review/watchlist.json` | No sample watchlist in the v1 format | **High** |
| `examples/weekly_review/investor_profile.json` | No sample investor profile | **High** |
| `examples/weekly_review/decision_journal.json` | No sample decision journal | Medium |
| `examples/weekly_review/company_facts/` | No sample company facts directory | Medium |

### Documentation gaps

| Gap | Description | Priority |
|---|---|---|
| User-facing usage guide | No guide for how to create and maintain the input files | Medium |
| Input file format reference | This spec covers it; a shorter user-facing reference is needed | Medium |

### Test coverage gaps

| Gap | Description | Priority |
|---|---|---|
| Weekly review input parser tests | No tests for weekly review input loading | **High** |
| Watchlist v1 format parser tests | No tests for the richer watchlist format | **High** |
| Non-actions section tests | No tests for the non-actions generator | **High** |
| End-to-end weekly review tests | No integration test for the full workflow | Medium |
| Language guardrail tests | No tests verifying forbidden language is absent from output | Medium |

---

## Acceptance Criteria for Future Implementation

The `atlas weekly-review` command is accepted when:

1. Accepts `--portfolio`, `--watchlist`, and `--profile` as required CLI arguments
2. Does not require live provider data — runs entirely on local files
3. Produces all 10 required sections in the correct order
4. Section 10 (Non-Actions / Reasons to Wait) is always present and never empty
5. Missing evidence is surfaced explicitly in Section 8
6. Uses only safe output language (no buy/sell/price-target/urgent language)
7. Output is deterministic: same input files always produce the same output
8. Exits with code 1 on missing required files, with a clear error message
9. Exits with code 2 on invalid file format, with a clear error message
10. Continues with warnings (not errors) on missing optional files
11. Missing company data produces an evidence-gap note, not a failure
12. Covered by guardrail tests: at minimum, verify all 10 sections present and no forbidden language in output
13. Demo (`scripts/run_daily_brief_demo.sh`) remains provider-free
14. Release verification (`scripts/verify_release_candidate.sh`) passes
15. Test suite passes with no new failures

---

## Example Output Skeleton

```markdown
# Atlas Weekly Investment Review

Review date: 2026-01-05
Atlas v1 — deterministic, local-only, no recommendations.

---

## Warnings
- No company facts found for XYL. Evidence gap noted.

---

## 1. Review Scope

Review date: 2026-01-05
Portfolio: 3 positions reviewed (ASML, MSFT, Cash)
Watchlist: 2 items reviewed (XYL, NOVO)
Companies flagged for attention: ASML, XYL
Scope notes: Q1 2026 — focus on semiconductor and water infrastructure themes.

---

## 2. Portfolio Context

Holdings:
  ASML   — Semiconductors (Netherlands)  — 18%  — Quality: 85 | Risk: 40
  MSFT   — Technology (USA)              — 27%  — Quality: 88 | Risk: 35
  Cash   — Cash                          — 55%  — Reserve capacity maintained

Sector concentration: Technology 45% | Cash 55%
Average quality score: 87 | Average risk score: 37
Note: Market values are user-supplied as of 2026-01-01. No live pricing used.

---

## 3. Watchlist Review

XYL — Xylem | Status: Researching
Reason: Water infrastructure theme
Open questions:
  - Is revenue mix shifting toward higher-margin software services?
  - What is the capital allocation track record?
Evidence needed:
  - Margin durability under commodity cost cycles
  - Valuation context relative to sector peers
  - Portfolio overlap with existing holdings
Observations: No position currently. Research in early stage.

NOVO — Novo Nordisk | Status: Needs More Evidence
Reason: Healthcare quality compounder candidate
Evidence needed:
  - Long-term growth durability beyond GLP-1 franchise
  - Patent cliff exposure
Observations: Revenue concentration in GLP-1 products is high. Evidence on long-term durability incomplete.

---

## 4. Company Reviews Needing Attention

ASML — ASML Holding
Confidence: Medium
Quality: 85 | Growth: 72 | Financial Strength: 80 | Valuation Risk: 55 | Risk: 40
Evidence summary: EUV monopoly position well-documented. Long-term demand visibility is strong. Export
  control exposure is a material unresolved risk.
Missing information:
  - Impact of US export restrictions on 2024–2026 bookings
  - Customer concentration in leading-edge chip manufacturers

XYL — Xylem
No company analysis available — evidence gap noted.
Next step: Company facts and financial history not provided for XYL.

---

## 5. Portfolio Fit and Suitability Notes

ASML — Suitability and fit
Compatible factors:
  - Long time horizon (10+ years) aligns with capital-intensive semiconductor equipment cycle
  - Balanced risk tolerance is within the risk profile of this company
Mismatches:
  - Export control exposure adds geopolitical risk that is not fully reflected in current evidence
Concentration signal: Technology sector exposure would be 45% at current weight. Within tolerance.
Atlas does not judge investment merit or provide personalized financial advice.

XYL — Suitability check not available
Reason: Insufficient company analysis data to run suitability check.

---

## 6. Risk and Principle Guardrails

Risk to Monitor: Technology sector concentration (ASML + MSFT) at 45%. Within stated tolerance but approaching limit.
Assumption to Recheck: ASML thesis assumed export controls would not materially impact long-term demand — this should be re-evaluated.

No principle concerns detected this week.

---

## 7. Open Decisions

XYL — Xylem | Status: Needs More Evidence
Date opened: 2025-11-15
Thesis: Potential water infrastructure exposure; evidence on margin durability incomplete.
Follow-up trigger: Revisit after Q4 2025 earnings are available.

No other open decisions.

---

## 8. Missing Evidence

XYL: Margin durability under commodity cost cycles — not yet reviewed. (Source: Watchlist)
XYL: Valuation context relative to sector peers — not yet reviewed. (Source: Watchlist)
ASML: Impact of US export restrictions on 2024–2026 revenue — open research question. (Source: Company review)
NOVO: Long-term growth durability beyond GLP-1 franchise — evidence incomplete. (Source: Watchlist)
NOVO: Patent cliff exposure — not yet reviewed. (Source: Watchlist)

---

## 9. Follow-Up Questions

Has Xylem's margin profile held up in the most recent quarter?
Has ASML provided any guidance on the revenue impact of US export restrictions?
What is Novo Nordisk's stated plan for revenue diversification beyond GLP-1 products?

---

## 10. Non-Actions / Reasons to Wait

ASML — No Action Warranted
Reason: Export control evidence is incomplete. No basis for a position change until this is resolved.
Status: Continue Research.

XYL — Decision Deferred
Reason: Evidence on margin durability and valuation not yet reviewed. No basis for any position decision.
Trigger: Revisit after Q4 2025 earnings.

Portfolio — No Action Warranted
Reason: Current portfolio is within target parameters. Cash reserve at 55% — maintaining reserve capacity
  per stated principles. No material thesis changes identified this week.

Reminder: No action is a valid and often appropriate outcome of a weekly review.
Atlas supports better judgment. It does not replace it.
```

---

## Sprint 211 Implementation Status — COMPLETE

Sprint 211 implemented the `atlas weekly-review` CLI skeleton.

**Command registered:** `atlas weekly-review` — root-level command on `app` in `atlas/cli/main.py`.

**Arguments:** `--portfolio` (required), `--watchlist` (required), `--profile` (optional), `--journal` (optional), `--company-facts` (optional), `--financials` (optional), `--as-of` (optional), `--scope-notes` (optional).

**Renderer created:** `atlas/weekly_review/render.py` — `render_weekly_review_skeleton(result)` returns a string with all 10 section headings and safe placeholder content. No engine calls. No provider dependency.

**Behavior:**
- Missing required portfolio or watchlist → exit code 1, clear error
- Missing optional inputs → warning in output, not failure
- Evidence gaps from watchlist `evidence_needed` fields surfaced in Section 8
- Deferred/Needs-More-Evidence watchlist items appear in Section 10
- Section 10 (Non-Actions) always present and non-empty
- No forbidden language in output, help text, or renderer
- Lazy import of `atlas.weekly_review` inside command — CLI module-level imports unchanged

**Tests:** `tests/test_weekly_review_cli_sprint211.py` — 28 tests, all passing. **1755 passed, 3 skipped | RC2 green | Demo passes.**

**Remaining gaps (for Sprint 212+):**
- Placeholder content in sections 4, 5, 6, 7, 9 — to be replaced with deterministic engine output
- Full investor profile object loading (with `principles`/`constraints`) not yet returned in `LoadResult`
- Companies-needing-attention logic not yet implemented
- Non-actions generator not yet connected to real decision data
- Financial CSV parsing not yet implemented

---

## Sprint 212 Implementation Status — COMPLETE

Sprint 212 replaced all placeholder renderer content with deterministic output derived from the loaded `WeeklyReviewLoadResult`.

**Renderer upgraded:** `atlas/weekly_review/render.py` — `render_weekly_review(result)` replaces skeleton placeholders. `render_weekly_review_skeleton` kept as backward-compatible alias.

**`WeeklyReviewLoadResult` extended:** Added `journal_entries: tuple[dict[str, Any], ...] = ()` field — raw journal dicts loaded alongside `journal_entry_count`. Zero-cost when journal absent.

**Section-by-section implementation:**

| Section | Sprint 211 | Sprint 212 |
|---|---|---|
| 1. Review Scope | as_of + counts | + optional input status + warnings count |
| 2. Portfolio Context | ticker list + sectors | + weights sorted desc + sector % breakdown + concentration note |
| 3. Watchlist Review | status + gap count | + per-item reason, evidence gaps, open questions, observations, notes |
| 4. Needs Attention | placeholder | + evidence-gap items + visible holdings + local-input-derived flags |
| 5. Suitability | placeholder | + profile availability + concentration note + cash position + deferred engine note |
| 6. Guardrails | placeholder | + elevated risk scores + missing cost basis + sector concentration + deferred engine note |
| 7. Open Decisions | count only | + per-entry title + status + follow-up triggers + atlas_view snippet |
| 8. Missing Evidence | watchlist gaps | + missing optional input flags |
| 9. Follow-Up Questions | placeholder | + watchlist open_questions + journal follow-up triggers + derived evidence questions |
| 10. Non-Actions | deferred items | + evidence gap count + missing optional reasons + universal reminders |

**Determinism:** stable sort by weight (desc) then ticker; stable warning order; no live timestamps.

**Forbidden language:** confirmed clean — 0 forbidden terms in output, help, or tests.

**Provider/network boundary:** no new imports added; `atlas.weekly_review.render` still free of provider/network imports.

**Tests:** `tests/test_weekly_review_renderer_sprint212.py` — 63 new tests. Sprint 211 tests unchanged. **1818 passed, 3 skipped | RC2 green | Demo passes.**

**Remaining gaps addressed in Sprint 213:**
- Full investor profile object loading (principles/constraints) → now parsed into LoadResult ✓
- Per-ticker company facts/financials presence check → now in LoadResult and rendered ✓

**Remaining gaps (for Sprint 215+):**
- Company analysis engine not yet wired into Section 4
- Suitability engine not yet wired into Section 5
- Risk/principles engine not yet wired into Section 6
- Financial CSV not yet parsed into financial model

---

## Sprint 214 Implementation Status — COMPLETE

Sprint 214 added deterministic journal entry aging alerts to Sections 7 and 10.

**Aging rule:** entries older than 90 calendar days (strictly greater than) from `as_of` are flagged if their status is not clearly closed (Closed, Archived, Completed, Resolved).

**Date field priority (first valid field wins):** `decision_date`, `date`, `created_at`, `created`, `timestamp`, `review_date`

**Status field priority:** `atlas_rating`, `decision_type`, `status`, `decision_status`, `state`

**Section 7 output (aged entries):**
```
[Aging Note] NESTE: Review date is older than 90 days (475 days). Thesis assumptions may need to be rechecked.
```

**Section 7 output (missing date on open entry):**
```
[Date Missing] No decision date recorded; aging cannot be assessed.
```

**Section 10 output (aged entries):**
```
Reason to Wait: NESTE decision journal notes are older than 90 days (475 days). Assumptions should be refreshed before changing decision status.
```

**Determinism:** aging requires `as_of` to be provided; if absent, no aging notes are rendered.

**Helper functions added to `render.py`:**
- `_parse_journal_entry_date(entry)` — date-field priority parser
- `_is_journal_entry_open(entry)` — closed-status filter
- `_journal_entry_age_days(entry, as_of)` — calendar day computation
- `_is_aged_journal_entry(entry, as_of, threshold_days=90)` — combined predicate
- `_render_journal_aging_note(entry, age_days)` — safe aging note string

**Tests:** 56 tests in `tests/test_weekly_review_journal_aging_sprint214.py`. 1928 total passing.

**Sprint 215 recommendation:** v1 usage guide — write a practical one-page guide for using `atlas weekly-review` with a real local portfolio. Bridges the gap between implementation and usability for a new user.

---

## Sprint 215 Implementation Status — COMPLETE

Sprint 215 created the v1 Weekly Review usage guide.

**Guide created:** `docs/AtlasWeeklyReviewUsageGuide.md`

**Contents:**
- What Atlas Weekly Review does and does not do
- Required files (portfolio.json, watchlist.json) and optional files
- Recommended folder structure with example paths
- Portfolio file format with minimal and extended examples
- Watchlist file format with allowed status values
- Investor profile and decision journal file formats
- Company facts and financials directory conventions
- Full command examples (minimal and all-optional)
- All 10 output sections explained in user terms
- Section 10 philosophy (no action is a valid outcome)
- Journal aging note behavior (>90 days, requires as_of)
- Common warnings table with non-urgent resolution notes
- Weekly update routine (7-step practical checklist)
- Current limitations (explicit, no promises)

**README updated:** pointer to usage guide added to capabilities table.

**Tests:** 26 tests in `tests/test_weekly_review_usage_guide_sprint215.py`. 1954 total passing.

**Sprint 216 recommendation:** Release hardening checkpoint — verify all Weekly Review sprints (209–215) are stable, all closed tracks remain clean, and `atlas weekly-review` end-to-end is solid before adding further engine wiring.

---

## Sprint 216 Implementation Status — COMPLETE

Sprint 216 performed a release hardening checkpoint for the Weekly Review v1 track.

**Fix applied:** CLI docstring in `atlas/cli/main.py` was stale ("skeleton"); updated to current description. Import updated from `render_weekly_review_skeleton` alias to `render_weekly_review` directly. No behavioral change.

**Commands verified:** minimal, full minimal-bundle, and realistic bundle — all exit 0, all 10 sections render, Section 10 non-empty.

**Journal aging verified:** NESTE (473 days) flagged; LVMH/MSFT/ADYEN not flagged; boundary conditions confirmed by 56 tests.

**Usage guide verified:** all 13 referenced paths exist, all flags match CLI, all 10 sections explained.

**Provider boundary:** clean across all `atlas/weekly_review/` modules.

**Language guardrails:** clean in all output, examples, and docs.

**Closed cleanup tracks:** all 7 deletion targets remain absent.

**Tests:** 1954 passed, 3 skipped. RC2 green.

**Hardening doc:** `docs/WeeklyReviewReleaseHardening.md`

**Sprint 217 recommendation:** Release candidate freeze for internal v1.

---

## Sprint 213 Implementation Status — COMPLETE

Sprint 213 ran a realistic end-to-end trial of `atlas weekly-review` on a 11-holding, 5-watchlist-item portfolio and made targeted improvements based on trial findings.

**Trial bundle:** `examples/weekly_review_realistic/` (anonymized placeholder data)

**Code improvements:**

| Change | Trigger |
|--------|---------|
| Load profile principles/constraints/risk_tolerance/time_horizon into `WeeklyReviewLoadResult` | Sections 5+6 were empty without profile fields |
| Per-ticker company facts presence check | Generic "facts not loaded" was not actionable |
| Per-ticker financials presence check | Same |
| `_preview_scope_notes()` helper strips markdown syntax | Raw markdown rendered in Section 1 |
| Combined top-2 concentration note (>40% threshold) | ASML+NOVO at 45% was invisible under old threshold |
| Single-position threshold lowered 30% → 25% | ASML at 24% should fire |

**Tests added:** `tests/test_weekly_review_trial_sprint213.py` — 54 tests covering all 10 sections, profile fields, per-ticker checks, forbidden language, determinism, and CLI integration.

**Findings documented:** `docs/WeeklyReviewTrialFindings.md`

**Sprint 214 recommendation:** Journal entry aging alerts — flag journal entries older than 90 days in Section 7 and Section 10.

## Sprint 210 Implementation Status — COMPLETE

Sprint 210 implemented all local input schemas for the Weekly Investment Review.

**Package created:** `atlas/weekly_review/` (top-level, matching `atlas/decision_journal/` and `atlas/watchlist_review/` conventions)

**Modules:**
- `atlas/weekly_review/__init__.py` — re-exports, `__all__`
- `atlas/weekly_review/inputs.py` — all dataclasses, parsers, loader, warnings

**Implemented:**

| Component | Status |
|---|---|
| `WeeklyReviewPortfolioInput` — v1 extended accounts[] format | ✓ |
| `WeeklyReviewPortfolioInput` — existing positions[] format | ✓ |
| Weight derivation from market_value across all holdings | ✓ |
| Multi-account support | ✓ |
| `WeeklyReviewWatchlistInput` — v1 rich item format | ✓ |
| `WeeklyReviewWatchlistStatus` enum with legacy alias mapping | ✓ |
| Missing status → Watchlist + warning | ✓ |
| Missing sector → Unclassified + warning | ✓ |
| `WeeklyReviewInputWarning` (code + message) | ✓ |
| `WeeklyReviewInputPaths` (required + optional paths) | ✓ |
| `WeeklyReviewLoadResult` (all loaded inputs + warnings) | ✓ |
| `load_weekly_review_inputs()` — top-level loader | ✓ |
| Profile: existing `InvestorProfileEngine.load_profile` reused | ✓ (path forwarded; profile_available flag) |
| Journal: entry count from existing `.atlas/decision_journal.json` | ✓ (lightweight JSON read, no full parse) |
| Company facts dir: existence check | ✓ |
| Financials dir: existence check | ✓ |
| No provider/network imports | ✓ |
| No buy/sell/price-target language in warnings or sample files | ✓ |

**Sample files created:** `examples/weekly_review/portfolio.json`, `watchlist.json`, `investor_profile.json`, `decision_journal.json`, `company_facts/ASML.json`, `financials/ASML.csv`, `scope_notes.md`

**Tests:** `tests/test_weekly_review_inputs_sprint210.py` — 35 tests, all passing. **1727 passed, 3 skipped | RC2 green | Demo passes.**

**Remaining gaps (for Sprint 211+):**
- No `atlas weekly-review` CLI command yet
- No multi-section Weekly Review renderer yet
- No "companies needing attention" orchestration logic yet
- No non-actions generator yet
- Full investor profile loading (with `principles`/`constraints` fields) deferred — profile_available flag is set but profile object not yet returned in LoadResult
- Financial CSV parsing deferred — directory existence check only

## Sprint 210 Recommendation (NOW COMPLETE)

**Implement local input schemas for Weekly Investment Review.**

Create the v1 sample input file set and the corresponding input loader, including:

1. `examples/weekly_review/portfolio.json` — sample portfolio in the existing `positions[]` format
2. `examples/weekly_review/watchlist.json` — sample watchlist in the v1 rich item format (with `status`, `evidence_needed`, `reason`, `open_questions`, `manual_observations`)
3. `examples/weekly_review/investor_profile.json` — sample investor profile with `principles` and `constraints` fields
4. `examples/weekly_review/decision_journal.json` — sample decision journal with one open decision
5. A new `WeeklyReviewInput` loader that validates required files, warns on missing optional files, and returns structured Python objects for each input type
6. A new rich watchlist parser (`WeeklyReviewWatchlistInput.from_json_file`) that reads the v1 watchlist format and maps to the existing `WatchlistReviewEngine` input types
7. Guardrail tests: verify all sample files load without error; verify parser rejects invalid formats

**Why this first:** The weekly review workflow depends entirely on the quality and consistency of its local inputs. Before wiring orchestration, rendering, or the CLI command, Atlas needs stable schemas, sample files, and parser validation. Getting the inputs right first prevents rework in later sprints.

**If sample files already exist in `examples/`** (only `daily_brief_demo/` exists as of Sprint 209): create a new `examples/weekly_review/` directory in Sprint 210.

---

## Repository Identity Confirmation

This is Atlas. This is NOT Atlas Edge. No Atlas Edge concepts, naming, or architecture have been applied in this specification. No Atlas Edge naming was encountered during Sprint 209 discovery.
