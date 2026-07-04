# Atlas v1 Operating Mode

**Created:** 2026-07-03 (Sprint 208)  
**Status:** DEFINED — v1 operating mode established. Sprint 209 COMPLETE: Weekly Investment Review workflow specified in full. See `docs/AtlasWeeklyInvestmentReviewSpec.md`. Sprint 210 target: implement local input schemas.

---

## v1 Product Boundary

Atlas v1 is a CLI-first, deterministic investment reasoning workflow for long-term investors. It helps the user review companies, watchlist candidates, portfolio fit, suitability, risks, evidence gaps, and decision history. It does not provide buy/sell recommendations, price targets, market-timing signals, live news, live market data, or automated trading guidance.

**Atlas v1 should support better judgment. It should not replace judgment.**

---

## Who Atlas v1 Is For

A self-directed long-term investor who:
- manages a personal or small-fund portfolio
- wants a repeatable weekly reasoning process
- does not want automated trading or algorithmic signals
- wants to track open decisions, evidence gaps, and assumptions over time
- works primarily from a terminal or file-based workflow
- does not require live data for the weekly review process

---

## The Job Atlas v1 Performs

Atlas v1 helps the user answer the same questions each week, in a consistent and deterministic way:

- What deserves my attention this week?
- Which companies or watchlist items need review?
- Which open decisions need follow-up?
- Which portfolio risks are visible?
- Which assumptions should be rechecked?
- Which cases should remain on watch rather than trigger action?
- What evidence is missing?
- What should I avoid overreacting to?

---

## Flagship v1 Workflow: Weekly Investment Review

The Atlas Weekly Investment Review is the core v1 operating mode. It is the primary repeatable workflow that ties all other Atlas capabilities together.

### Purpose

Help the user conduct a structured weekly review of their investment process — companies, watchlist, portfolio, suitability, risks, open decisions, and missing evidence — without giving recommendations.

### Sections

1. **Review Scope** — what is being reviewed and why
2. **Portfolio Context** — current holdings, weights, risk profile
3. **Watchlist Changes** — items added, removed, or changed status
4. **Company Reviews Needing Attention** — cases due for re-evaluation
5. **Suitability / Fit Notes** — profile compatibility changes or drift
6. **Risk and Principle Guardrails** — active risk drift, principle violations
7. **Open Decisions** — pending decisions with last-update dates
8. **Missing Evidence** — gaps identified; what would change the view
9. **Follow-Up Questions** — questions to answer before next review
10. **Non-Actions / Reasons to Wait** — explicitly noting where no action is warranted

### What the Weekly Review Must Not Include

- Buy/sell/strong-buy language
- Price targets or target prices
- Urgent action language
- Market-timing signals
- Live news summaries
- LLM-generated opinions

### CLI Entrypoint

`atlas daily summary` — currently the closest existing command (Blueprint-aligned Daily Brief). The Weekly Review is a higher-level orchestration of this and related commands. Full Weekly Review workflow is a Sprint 209+ implementation target.

### Missing Implementation Gap

No single `atlas weekly-review` command exists. The weekly review must currently be assembled by the user from individual CLI commands. Sprint 209 should specify the workflow inputs, steps, and output format in detail; Sprint 210+ should implement it.

---

## v1 Workflow Inventory

### Workflow 1 — Company Analysis

| Attribute | Value |
|---|---|
| Purpose | Deterministic scoring and review of a single company across quality, growth, financial strength, valuation, and risk dimensions |
| Existing package | `atlas/analysis/` (AtlasInvestmentEngine), `atlas/capabilities/company_analysis/` |
| CLI | `atlas report <TICKER>`, `atlas analyze <TICKER>`, `atlas company-analysis export` |
| Required input | Ticker + optional manual company facts or CSV financials |
| Output | InvestmentReport with scored categories; intelligence synthesis via `atlas analyze` |
| v1 usable now | Yes — `atlas report` and `atlas analyze` are functional |
| Productization gap | Output readability could be improved; no Company Review template connecting all sections |
| Belongs in v1 | **Yes** |

### Workflow 2 — Portfolio Fit Review

| Attribute | Value |
|---|---|
| Purpose | Evaluate how a company or watchlist item fits the current portfolio in terms of concentration, sector, country, and market cap exposure |
| Existing package | `atlas/capabilities/portfolio_intelligence/` (PortfolioFitEngine, PortfolioFitResult) |
| CLI | `atlas portfolio summary` |
| Required input | Portfolio JSON snapshot |
| Output | PortfolioFitResult with concentration signals and overlap |
| v1 usable now | Partially — engine is functional; CLI output is a summary, not a per-company fit report |
| Productization gap | No integrated company-to-portfolio fit report |
| Belongs in v1 | **Yes** |

### Workflow 3 — Suitability Check

| Attribute | Value |
|---|---|
| Purpose | Evaluate whether a company or portfolio fits the investor's stated risk profile, time horizon, and investment purpose |
| Existing package | `atlas/suitability/` (SuitabilityEngine, SuitabilityAssessment) |
| CLI | `atlas suitability analyze <SUBJECT>` |
| Required input | Subject (ticker or portfolio JSON) + optional investor profile JSON |
| Output | SuitabilityAssessment with fit factors, mismatches, confidence, assumptions, missing information |
| v1 usable now | **Yes** — output is structured, explicit, and correctly framed as profile-compatibility (not advice) |
| Productization gap | Investor profile requires manual JSON; no profile wizard |
| Belongs in v1 | **Yes** |

### Workflow 4 — Watchlist Review

| Attribute | Value |
|---|---|
| Purpose | Systematic review of watchlist items — what changed, what deserves action, what should remain on watch |
| Existing package | `atlas/watchlist_review/` (WatchlistReviewEngine), `atlas/capabilities/watchlist_intelligence/` |
| CLI | `atlas watchlist review`, `atlas watchlist intelligence` |
| Required input | Watchlist entries (JSON or manual) + optional investor profile |
| Output | WatchlistReviewReport with items, observations, and ratings |
| v1 usable now | **Yes** — `atlas watchlist review` is functional with demo and file input |
| Productization gap | Watchlist input format needs documentation; CIO-style review output may need narrative improvement |
| Belongs in v1 | **Yes** |

### Workflow 5 — Decision Journal

| Attribute | Value |
|---|---|
| Purpose | Record, track, and review investment decisions over time — including thesis, evidence, outcome, and lessons |
| Existing package | `atlas/decision_journal/` (DecisionJournalEngine, DecisionJournalEntry, DecisionJournalReview) |
| CLI | `atlas journal create`, `atlas journal list`, `atlas journal review` |
| Required input | Decision details (thesis, type, conviction, horizon) as JSON or demo |
| Output | Decision entries, review with lessons and follow-up triggers |
| v1 usable now | **Yes** — `atlas journal review` produces a structured review |
| Productization gap | No guided entry flow; demo entry only; no link from company analysis to journal |
| Belongs in v1 | **Yes** |

### Workflow 6 — Daily / Weekly Brief

| Attribute | Value |
|---|---|
| Purpose | Deterministic overview combining portfolio context, watchlist, economic signals, market regime, and daily focus items |
| Existing package | `atlas/home/` (HomeEngine), `atlas/dashboard/` |
| CLI | `atlas daily summary`, `atlas home`, `atlas dashboard show` |
| Required input | Portfolio JSON (optional), watchlist (optional), investor profile (optional) |
| Output | Daily Brief text output with sections |
| v1 usable now | **Yes** — `atlas daily summary` is the current flagship demo command |
| Productization gap | "Daily" framing is accurate; "Weekly Review" orchestration layer does not yet exist |
| Belongs in v1 | **Yes** (evolves into Weekly Review in Sprint 209+) |

### Workflow 7 — Evidence and Missing Evidence Review

| Attribute | Value |
|---|---|
| Purpose | Identify what evidence exists, what is missing, and what gaps would need to close before confidence increases |
| Existing package | `atlas/evidence/` (EvidenceEngine, EvidenceAssessment) |
| CLI | No dedicated `atlas evidence` top-level command (retired Sprint 86 as CLI body; engine remains active) |
| Required input | CompanyAnalysis or manual evidence inputs |
| Output | EvidenceAssessment with supporting/opposing evidence, confidence level, missing evidence list |
| v1 usable now | Engine is active; CLI entrypoint is retired — evidence output surfaces through `atlas analyze` and `atlas report` |
| Productization gap | No standalone "missing evidence" report; evidence embedded in larger outputs |
| Belongs in v1 | **Yes — as a section within Company Review and Weekly Review outputs, not a standalone command** |

### Workflow 8 — Risk and Principle Guardrail Review

| Attribute | Value |
|---|---|
| Purpose | Detect risk drift from original assumptions; validate outputs against Atlas communication principles |
| Existing packages | `atlas/risk/` (RiskEngine), `atlas/principles/` (PrinciplesEngine), `atlas/risk_drift/` |
| CLI | `atlas risk-drift analyze`, `atlas principles check` |
| Required input | Company analysis + risk profile; or text string for principles check |
| Output | RiskDriftReport with drift signals; PrinciplesAssessment with guardrail violations |
| v1 usable now | **Yes** — both commands are functional |
| Productization gap | Risk drift requires prior suitability assessment as input; no automated pipeline |
| Belongs in v1 | **Yes — as guardrail layer within Weekly Review** |

---

## Existing Capability Map: v1 Roles

| Package | Lines | v1 Role | CLI | Status |
|---|---|---|---|---|
| `atlas/analysis/` | 648 | Company scoring engine — core v1 analysis | `atlas report`, `atlas analyze` | Active, v1-ready |
| `atlas/capabilities/company_analysis/` | 571 | Blueprint company analysis capability | `atlas company-analysis export` | Active, v1-ready |
| `atlas/capabilities/portfolio_intelligence/` | 455 | Portfolio fit evaluation | `atlas portfolio summary` | Active, v1-ready |
| `atlas/suitability/` | 642 | Profile compatibility check | `atlas suitability analyze` | Active, v1-ready |
| `atlas/watchlist_review/` | 894 | Systematic watchlist review | `atlas watchlist review` | Active, v1-ready |
| `atlas/decision_journal/` | 605 | Decision tracking and review | `atlas journal create/list/review` | Active, v1-ready |
| `atlas/evidence/` | 563 | Evidence assessment | Embedded in analyze/report | Active, internal support |
| `atlas/risk/` | 469 | Risk assessment | `atlas risk-drift analyze` | Active, guardrail layer |
| `atlas/principles/` | 334 | Output guardrail validation | `atlas principles check` | Active, guardrail layer |
| `atlas/intelligence/` | 484 | Synthesis across analysis dimensions | `atlas intelligence analyze` | Active, supporting |
| `atlas/dashboard/` | 533 | Home dashboard briefing | `atlas dashboard show` | Active, v1-ready |
| `atlas/conversation/` | 565 | Conversational Q&A interface | `atlas ask` | Active, supporting |
| `atlas/comparison/` | 1032 | Multi-idea comparison | `atlas compare` | Active, supporting |
| `atlas/home/` | 630 | Primary daily brief | `atlas home`, `atlas daily summary` | Active, v1 flagship |

---

## v1 Input Model

| Input | Required | Format | Currently Supported | Manual Acceptable in v1 | Live Data Needed |
|---|---|---|---|---|---|
| Company identifier (ticker) | Required for company review | String | Yes | Yes | No |
| Manual company facts | Optional | Atlas CLI prompt / CompanyAnalysis struct | Partial | Yes | No |
| Portfolio snapshot | Optional | JSON file (`Portfolio.from_json_file`) | Yes | Yes (manual JSON) | No |
| Watchlist entries | Optional | JSON file or mapping | Yes | Yes (manual JSON) | No |
| Decision journal entries | Optional | JSON file (`.atlas/decision_journal.json`) | Yes | Yes (manual JSON) | No |
| Investor profile | Optional | JSON file (`atlas_profile.json`) | Yes | Yes (manual JSON) | No |
| CSV financial history | Optional | CSV (`atlas import-financials`) | Yes | Yes | No |
| User notes / annotations | Optional | Free text, not yet structured | No — future sprint | Yes | No |
| Manually supplied evidence | Optional | Not yet structured | No — future sprint | Yes | No |

**v1 principle:** All inputs are local, manual, and file-based. Live provider data is opt-in only and not required for v1.

---

## v1 Output Model

| Output | Purpose | Format | CLI | Language Guardrail | v1-Ready |
|---|---|---|---|---|---|
| Weekly Investment Review | Top-level weekly workflow output | Text / markdown sections | `atlas daily summary` (partial) | No buy/sell/urgent | Partially — no unified command yet |
| Company Review Summary | Per-company scored analysis | Text report | `atlas report <TICKER>` | No recommendations | Yes |
| Intelligence Synthesis | Cross-dimension synthesis | Text report | `atlas analyze <TICKER>` | No recommendations | Yes |
| Portfolio Fit Summary | Concentration and fit signals | Text report | `atlas portfolio summary` | No recommendations | Yes |
| Suitability Assessment | Profile compatibility | Text report | `atlas suitability analyze` | Anti-advice disclaimer ✓ | Yes |
| Watchlist Review | Per-item review with ratings | Text report | `atlas watchlist review` | No recommendations | Yes |
| Decision Memo | Structured decision record | JSON + text | `atlas journal review` | No buy/sell ✓ | Yes |
| Risk Drift Report | Drift signals from prior assumptions | Text report | `atlas risk-drift analyze` | No urgency language | Yes |
| Principles Check | Guardrail validation of text | Text report | `atlas principles check` | N/A — validates others | Yes |
| Daily Brief | Combined overview | Text | `atlas daily summary` | No recommendations | Yes |

---

## Usable Output Criteria

A v1 output is **usable** if the user can read it and understand:

1. **What was reviewed** — company, portfolio, watchlist item, or decision
2. **What evidence was used** — scored factors, financial data, profile inputs
3. **What is uncertain** — confidence level and missing information explicitly stated
4. **What risks were identified** — drift signals, mismatches, principle concerns
5. **What assumptions were made** — stated explicitly (Atlas assumes X = Y)
6. **How the case fits or does not fit** — profile compatibility stated, not implied
7. **What decision remains open** — status, next trigger, follow-up date
8. **Why no action may be warranted** — explicitly permitted conclusion

A v1 output is **not usable** if it:

- Requires source-code knowledge to interpret
- Uses unexplained scores without context
- Gives buy/sell/price-target language
- Hides uncertainty or confidence level
- Fails to separate evidence from interpretation
- Cannot be reproduced deterministically
- Presents a conclusion without stating what evidence it rests on

---

## CLI Operating Sequence for v1

The recommended v1 weekly workflow using existing commands:

```
Step 1 — Company review (repeat per company under review)
  atlas report <TICKER>                     # scored investment report
  atlas analyze <TICKER>                    # intelligence synthesis

Step 2 — Portfolio fit
  atlas portfolio summary                   # portfolio domain overview

Step 3 — Suitability check
  atlas suitability analyze <TICKER>        # profile compatibility
  atlas suitability analyze portfolio.json  # portfolio-level suitability

Step 4 — Watchlist review
  atlas watchlist review                    # CIO-style watchlist review
  atlas watchlist intelligence              # Blueprint-aligned watchlist report

Step 5 — Decision journal
  atlas journal list                        # list open decisions
  atlas journal review                      # review latest entry

Step 6 — Daily brief / weekly overview
  atlas daily summary                       # combined daily brief

Step 7 — Risk and guardrail check (optional, per case)
  atlas risk-drift analyze                  # detect assumption drift
  atlas principles check "<text>"           # validate output language
```

This sequence is assembled manually in v1. The Sprint 209+ target is to specify a unified `atlas weekly-review` command that orchestrates these steps.

---

## v1 Workflow Specifications

### Atlas Company Review Specification

**Purpose:** Produce a structured, scored, deterministic review of a single company across all Atlas analysis dimensions.

**Inputs:** Ticker + optional portfolio JSON (for fit context) + optional investor profile JSON (for suitability)

**Required sections:**

1. Business Overview — ticker, company name, exchange, sector, industry
2. Evidence Summary — sources used; manual facts if any
3. Quality Factors — quality score, components, reasoning
4. Growth Factors — growth score, components, reasoning
5. Financial Strength — financial score, components, reasoning
6. Valuation Risk — valuation score, components, reasoning
7. Risk Profile — risk score, components, reasoning
8. Portfolio Fit — concentration and overlap signals (if portfolio provided)
9. Suitability Notes — compatibility with investor profile (if profile provided)
10. Missing Evidence — what Atlas does not know
11. Follow-Up Triggers — conditions that would change the view

**Forbidden sections:** Price targets, buy/sell recommendations, urgent language, predicted outcomes.

**Acceptance criteria:**
- All scores include reasoning, not just numbers
- Confidence level stated
- Missing information explicitly listed
- No recommendation language
- Output is reproducible with the same inputs

**Existing CLI support:** `atlas report <TICKER>` covers items 1–7. Items 8–11 are embedded in `atlas analyze` output. A unified Company Review template does not yet exist as a single command.

**Gap:** No single `atlas company-review` command combining all 11 sections.

---

### Atlas Watchlist Review Specification

**Purpose:** Review all active watchlist items systematically — changes, ratings, what deserves attention, what should remain on watch.

**Inputs:** Watchlist JSON + optional investor profile

**Required sections:**

1. Review Date and Scope
2. Items Reviewed (with rating per item: Active / Watch / Deferred / Removed)
3. Observations per Item (what changed, evidence notes)
4. Items Needing Attention This Week
5. Items to Remain on Watch
6. Items Removed or Deferred
7. Missing Evidence Across Watchlist

**Forbidden sections:** Buy/sell/urgent language per item.

**Existing CLI support:** `atlas watchlist review` — functional and v1-ready.

**Gap:** Input format (watchlist JSON schema) needs documentation for users.

---

### Atlas Decision Memo Specification

**Purpose:** Record a single investment decision — thesis, evidence, risks, uncertainties, and status — in a structured and reviewable format.

**Inputs:** Decision details (ticker, thesis, type, conviction level, time horizon, evidence for, evidence against, risks)

**Required sections:**

1. Decision Under Review — ticker, type, date
2. Current Thesis — one-paragraph thesis statement
3. Evidence For — supporting facts and scored factors
4. Evidence Against — opposing facts and scored factors
5. Key Risks — identified risks with severity
6. Portfolio Fit — concentration and overlap signals
7. Suitability — profile compatibility rating
8. Uncertainties — what Atlas does not know
9. What Would Change the View — explicit conditions
10. Follow-Up Date or Trigger — when to revisit
11. Decision Status — see permitted statuses below

**Decision statuses (forbidden: buy/sell):**

- `Continue Research` — more evidence needed before forming a view
- `Watchlist` — case is interesting but not yet ready for further review
- `Needs More Evidence` — specific gaps identified; revisit when filled
- `Suitable for Further Review` — profile-compatible; next step is deeper analysis
- `Not Suitable Under Current Constraints` — profile mismatch or principle conflict
- `Decision Deferred` — external conditions prevent evaluation; revisit on trigger date

**Existing CLI support:** `atlas journal create` + `atlas journal review` — functional for recording and reviewing entries.

**Gap:** Structured 11-section output template not yet implemented; `atlas journal review` produces a summary rather than a full decision memo.

---

### Atlas Weekly Investment Review Specification

**Purpose:** The top-level v1 workflow. A single structured review that answers what deserves attention this week, integrating company reviews, watchlist, portfolio, suitability, risk, open decisions, and missing evidence.

**Inputs:** Portfolio JSON (optional), watchlist JSON (optional), investor profile JSON (optional), list of tickers to review (optional)

**Required sections:**

1. Review Scope — date, items in scope, investor profile summary
2. Portfolio Context — current weights, top exposures, concentration signals
3. Watchlist Changes — items added, rating changes, items due for review
4. Company Reviews Needing Attention — scored summaries for cases under review
5. Suitability / Fit Notes — profile compatibility drift or changes
6. Risk and Principle Guardrails — active drift signals, any principle concerns
7. Open Decisions — pending decisions with last-review date and status
8. Missing Evidence — gaps identified across all cases
9. Follow-Up Questions — questions to answer before next review
10. Non-Actions / Reasons to Wait — explicit statement of cases where no action is warranted

**Forbidden sections:** Buy/sell/urgent language, price targets, predicted outcomes.

**Acceptance criteria:**
- Reproducible with the same inputs
- Section 10 (Non-Actions) must always be present
- Confidence levels stated where available
- Missing evidence explicitly listed
- No recommendation language

**Current CLI entrypoint:** None — currently assembled manually from individual commands.

**Missing implementation gap:** No `atlas weekly-review` command. Sprint 209 should specify the workflow inputs, data structures, and output format in detail. Sprint 210+ should implement it.

---

## Out of Scope for v1

The following are explicitly excluded from Atlas v1:

| Category | Status |
|---|---|
| Live market data | Out of scope |
| Live news | Out of scope |
| Automatic web research | Out of scope |
| LLM-generated conclusions | Out of scope |
| UI / dashboard / web interface | Out of scope |
| Broker integrations (Avanza, Nordnet, etc.) | Out of scope |
| Automatic portfolio import from broker | Out of scope |
| Trading signals | Out of scope |
| Intraday logic | Out of scope |
| Atlas Edge concepts, naming, or architecture | Prohibited |
| Price targets | Prohibited |
| Buy / sell / strong-buy recommendations | Prohibited |
| Urgent action alerts | Prohibited |
| Automated position sizing | Out of scope |
| Background monitoring / automated alerts | Out of scope |
| Market-timing signals | Out of scope |
| Automatic decision execution | Out of scope |

---

## Guardrail Principles for v1 and Beyond

Atlas v1 must always preserve:

1. **Evidence before opinion** — conclusions require stated evidence
2. **Deterministic reasoning** — same inputs produce same outputs
3. **No buy/sell recommendations** — ever
4. **No price targets** — ever
5. **No urgent action language** — "act now", "don't miss", etc.
6. **No market-timing claims** — no assertions about short-term price direction
7. **No live provider dependency** — v1 works without network calls
8. **No Atlas Edge concepts** — Atlas and Atlas Edge are separate products
9. **Human judgment remains final** — Atlas informs, does not decide
10. **"No action warranted" is a valid outcome** — always explicitly available

---

## Sprint 209 Status — COMPLETE

Sprint 209 specified the Atlas Weekly Investment Review workflow in full. See [`docs/AtlasWeeklyInvestmentReviewSpec.md`](AtlasWeeklyInvestmentReviewSpec.md) for:
- Product boundary, workflow steps, CLI entrypoint design
- Input specifications (portfolio, watchlist, investor profile, journal, company facts, financials)
- All 10 output sections with content requirements, acceptance criteria, and example phrasing
- Safe and forbidden language reference
- Missing data / failure behavior
- Implementation gap analysis (input schema, parser, orchestration, renderer, CLI, sample data, tests)
- Acceptance criteria for future implementation
- Example output skeleton

## Sprint 210 Recommendation

**Implement local input schemas for Weekly Investment Review.**

The Weekly Investment Review is the best flagship v1 workflow because it ties together company review, watchlist, suitability, risk/principles, open decisions, missing evidence, and non-actions without requiring live data or recommendation language. Sprint 209 should produce a detailed specification:

- Input data structures (types, formats, file paths)
- Workflow steps and sequence
- Output section definitions
- CLI entrypoint design (`atlas weekly-review` or pipeline of existing commands)
- Missing implementation gaps and implementation plan
- Acceptance criteria for each section

Sprint 210+ should implement the workflow based on the Sprint 209 specification.

## Sprint 212 Status — COMPLETE

Sprint 212 implemented the deterministic Weekly Investment Review renderer.

**Status:** `atlas weekly-review` now produces useful, input-derived output from local files only.

**What changed:**
- `atlas/weekly_review/render.py` rewritten — `render_weekly_review(result)` introduced; `render_weekly_review_skeleton` kept as backward-compatible alias
- `WeeklyReviewLoadResult` extended with `journal_entries: tuple[dict[str, Any], ...] = ()` — raw journal dicts alongside entry count
- All 10 sections produce deterministic content from loaded inputs
- No engine calls, no provider imports, no live data

**Sprint 213 recommendation:** Run real portfolio trial — run `atlas weekly-review` on a realistic local portfolio/watchlist/profile bundle and identify friction before wiring deeper engines.

---

## Sprint 213 Status — COMPLETE

Sprint 213 ran a realistic end-to-end trial of `atlas weekly-review` on a 11-holding, 5-watchlist-item portfolio and made targeted code improvements based on trial findings.

**Trial bundle:** `examples/weekly_review_realistic/` (anonymized placeholder data)

**What changed:**
- `WeeklyReviewLoadResult` extended with 6 new fields: `profile_principles`, `profile_constraints`, `profile_risk_tolerance`, `profile_time_horizon`, `tickers_missing_facts`, `tickers_missing_financials`
- `atlas/weekly_review/render.py` — Sections 5 and 6 now render profile fields; Section 8 and 10 use per-ticker missing facts/financials; `_preview_scope_notes()` helper strips markdown headers/syntax; combined top-2 concentration note added; single-position threshold 30%→25%
- 54 new tests in `tests/test_weekly_review_trial_sprint213.py`
- Trial findings documented in `docs/WeeklyReviewTrialFindings.md`
- No engine calls, no provider imports, no live data

**Sprint 214 recommendation:** Journal entry aging alerts — flag journal entries older than 90 days in Section 7 and Section 10. Small scope, high signal value.

---

## Sprint 214 Status — COMPLETE

Sprint 214 added deterministic journal entry aging alerts to `atlas weekly-review`.

**What changed:**
- `atlas/weekly_review/render.py` — 5 new aging helper functions; Section 7 renders `[Aging Note]` for open entries older than 90 days; Section 10 renders `Reason to Wait` for aged entries; open entries with no parseable date show `[Date Missing]` note
- Aging requires `as_of` for determinism; no current-date dependency introduced
- Date field priority: `decision_date`, `date`, `created_at`, `created`, `timestamp`, `review_date`
- Status filtering: closed statuses (`Closed`, `Archived`, `Completed`, `Resolved`) suppress alerts
- 56 new tests in `tests/test_weekly_review_journal_aging_sprint214.py`; 1928 total passing

**Sprint 215 recommendation:** v1 usage guide — write a practical one-page guide for using `atlas weekly-review` with a real local portfolio.

---

## Sprint 215 Status — COMPLETE

Sprint 215 created `docs/AtlasWeeklyReviewUsageGuide.md` — a practical guide covering required/optional files, folder structure, all file formats, command examples, all 10 output sections, Section 10 philosophy, journal aging behavior, common warnings, weekly update routine, and current limitations. README updated with pointer and Weekly Review capability row. 26 new tests; 1954 total passing.

**Sprint 216 recommendation:** Release hardening checkpoint across all Weekly Review sprints (209–215).

---

## Sprint 216 Status — COMPLETE

Sprint 216 hardened the Weekly Review v1 track. Fix: CLI docstring and import updated from stale `render_weekly_review_skeleton` alias to `render_weekly_review` (no behavioral change). All three command variants verified (minimal, full, realistic). NESTE aging alert confirmed (473 days). All 13 guide-referenced paths verified present. Provider boundary clean. Language guardrails clean. 7 closed deletion targets remain absent. 1954 tests passing. RC2 green. Hardening doc: `docs/WeeklyReviewReleaseHardening.md`.

**Sprint 217 recommendation:** Release candidate freeze for internal v1.

---

## Sprint 217 Status — COMPLETE

Sprint 217 froze the internal v1 release candidate. Created `docs/InternalV1ReleaseCandidate.md` with 24-item acceptance checklist (all met), included/excluded capabilities table, command surface, guardrail acceptance, verification results, known limitations, and productization track summary (Sprints 208–217). Added `__release_stage__ = "Internal v1 RC — Weekly Review (Sprint 217)"` to `atlas/__init__.py`. 16 new tests; 1970 total passing.

**Sprint 218 recommendation:** Load investor profile principles and constraints more deeply into Weekly Review — render them as explicit guardrail checks in Section 6 and as relevant constraints in Section 10, without invoking the full suitability engine.

---

## Sprint 218 Status — COMPLETE

Sprint 218 surfaced investor profile principles and constraints in Weekly Review Sections 5, 6, and 10. Changes: added `invalid_profile_principles` and `invalid_profile_constraints` warnings in `inputs.py` for malformed fields; added profile-derived reasons to wait in Section 10 of `render.py` (each principle as "Reason to Wait", each constraint as "No Action Warranted"). No engine wiring. No suitability scoring. 46 new tests; 2016 total passing.

**Sprint 219 recommendation:** Wire existing company facts and financial presence checks more deeply into Missing Evidence and Follow-Up Questions (per-ticker improvements without adding provider or engine dependencies).

---

## Sprint 219 Status — COMPLETE

Sprint 219 added per-ticker local evidence presence checks. New `WeeklyReviewTickerEvidence` dataclass tracks `company_facts_available`, `financials_available`, and `source` (portfolio/watchlist/portfolio_and_watchlist) for each investable ticker. Section 8 now emits per-ticker `Evidence Gap [TICKER]` lines instead of a bulk comma-separated list. Section 9 adds per-ticker follow-up questions when facts or financials are missing. Section 10 adds per-ticker reasons to wait. Missing directories remain non-blocking. 42 new tests; 2058 total passing.

**Sprint 220 recommendation:** Run second real portfolio trial — test the full Weekly Review output with the profile, per-ticker evidence checks, and all improvements from Sprints 213–219 against a realistic bundle before adding deeper engines.

---

## Sprint 220 Status — COMPLETE

Sprint 220 ran the second realistic Weekly Review trial. Trial confirmed output is specific and safe but identified four verbosity problems. Four trial-driven renderer improvements applied: (1) Section 8 combines "both missing" into one line per ticker; (2) Section 9 replaces 24 identical per-ticker questions with two grouped ticker lists; (3) Section 10 consolidates per-ticker missing evidence into two summary lines; (4) Section 10 uses block format for principles and constraints instead of N identical boilerplate lines. Section 10 reduced from ~40 lines to ~18 lines. 20 new tests; 2078 total passing.

---

## Sprint 221 Status — COMPLETE

Sprint 221 specified the Snapshot / Screenshot Input workflow. No runtime behavior was changed. A new document `docs/AtlasSnapshotInputWorkflow.md` defines: seven supported snapshot types (Portfolio, Watchlist, Open Orders, News, External Analysis, Research Notes, Company Facts); a classification contract with a structured JSON output; a draft contract with required fields and confirmation states; accuracy and safety guardrails; privacy and security boundary; mapping from each snapshot type to existing Atlas local input files; relationship to Weekly Review and future chat-first workspace UX; and an explicit out-of-scope section. No OCR, image parsing, AI, or provider dependencies introduced. 2078 tests still passing.

**Sprint 222 recommendation:** Add research notes input — the safest bridge between Snapshot Input and Weekly Review, requiring no OCR, AI, or broker integration.

---

## Sprint 222 Status — COMPLETE

Sprint 222 added local research notes input to Weekly Review. New `--research-notes DIR` CLI argument. New `WeeklyReviewResearchNote` dataclass. Per-ticker `research_notes/<TICKER>/notes.md` files are loaded using bounded reads (8,000 char max) and a lightweight section parser. Evidence gaps appear in Section 8; open questions and risks appear in Section 9; reasons to wait appear in Section 10. Missing or malformed notes do not fail the review. Two example files added (`ASML/notes.md`, `XYL/notes.md`). No OCR, AI, image parsing, or provider dependency introduced. 45 new tests; 2159 total passing.

**Sprint 223 recommendation:** Define Snapshot Draft schema — the next step toward making Snapshot Input concrete without implementing OCR or image parsing.

---

## Sprint 223 Status — COMPLETE

Sprint 223 defined the formal Snapshot Draft schema. New package `atlas/snapshot_input/` with `schema.py`. `SnapshotType` (8 values), `SnapshotConfirmationStatus` (5 states), `SnapshotConfidence` (4 levels), `SnapshotDraft` dataclass with 9 required and 4 optional fields, `validate_snapshot_draft`, `to_dict`/`from_dict`/`to_json`/`from_json` serialization, and `load_snapshot_draft`/`save_snapshot_draft` file helpers. Three example draft files created. No OCR, AI, image parsing, or provider dependency introduced. No Weekly Review behavior changed. 72 new tests; 2231 total passing.

---

## Sprint 227 Status — COMPLETE

Sprint 227 defined the standard Snapshot Draft confirmation workflow.
New document `docs/SnapshotDraftConfirmationWorkflow.md` specifies:
11 confirmation principles, all five state definitions, the exportability rule
(only `confirmed` is exportable), a review checklist, blocking rules, a field
correction model, future CLI command shapes, export command dependency,
audit/traceability expectations, and safety boundary. No runtime behavior changed.
No new CLI commands implemented. 57 new tests. 2384 total passing.

**Sprint 228 recommendation:** Add `atlas snapshot review` command — a read-only
command that renders the full confirmation checklist for a draft.

---

## Sprint 226 Status — COMPLETE

Sprint 226 ran the third real portfolio trial with exported research notes. Three
confirmed `research_notes_snapshot` drafts (ASML, XYL, NOVO) were validated,
exported, and consumed by `atlas weekly-review --research-notes DIR`. Sections 8,
9, and 10 were evaluated. Loop confirmed functional, useful, and safe. ASML gained
purely additive coverage in Sections 8/9/10. Research note provenance labels work
correctly. File mutation safety confirmed. No forbidden language in any output.
No code changes required. Trial findings in `docs/SnapshotResearchNotesTrialFindings.md`.

**Sprint 227 recommendation:** Add snapshot draft confirmation planning.

---

## Sprint 225 Status — COMPLETE

Sprint 225 implemented the first safe Snapshot Draft conversion path.
`atlas snapshot export-research-notes <draft_path> --output-dir DIR` converts
a confirmed `research_notes_snapshot` draft to `research_notes/<TICKER>/notes.md`.
Type and confirmation status are enforced. Ticker is normalized and validated.
Existing files are protected by default; `--overwrite` enables replacement.
Output is bounded (500 chars/bullet, 20 bullets/section). Draft is never mutated.
End-to-end path confirmed: exported file is immediately readable by
`atlas weekly-review --research-notes DIR`. No provider imports. No network calls.
No OCR. No AI. 52 new tests; 2327 total passing.

**Sprint 226 recommendation:** Run third real portfolio trial with exported research notes.

---

## Sprint 224 Status — COMPLETE

Sprint 224 added `atlas snapshot validate <path>` — a read-only CLI command that validates a Snapshot Draft JSON file and renders a human-readable summary. Output includes: type, confidence, confirmation status, target local file, related tickers, uncertainties, missing required fields, and safety boundary. Exit 0 on valid draft, exit 1 on invalid JSON, invalid schema, or missing file. No file writing. No mutation. New `atlas/snapshot_input/render.py` created. CLI extended with `snapshot_app` Typer sub-group. No provider imports. No network calls. 44 new tests; 2275 total passing.

**Sprint 225 recommendation:** TBD.

**Sprint 221 recommendation:** Group or simplify Section 10 output — add visual grouping (reason-type headers) so the section is scannable rather than requiring sequential reading.
