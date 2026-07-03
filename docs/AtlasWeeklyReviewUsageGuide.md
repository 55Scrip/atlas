# Atlas Weekly Review Usage Guide

Atlas Weekly Review is a local, deterministic investment research workflow.
It reads files you maintain on your own machine and produces a structured
10-section review. No live data. No broker connection. No AI. No recommendations.

---

## What This Does

Atlas Weekly Review reads your local portfolio and watchlist files, applies your
investor profile and decision journal notes, and produces a structured summary
covering portfolio context, watchlist evidence gaps, open decisions, missing
inputs, and reasons to wait.

It helps you organise what you know, what you are missing, and what should remain
deferred — without telling you what to do.

---

## What This Does Not Do

Atlas Weekly Review does not:

- fetch live market data or prices
- fetch live news or earnings releases
- connect to any broker (Avanza, Nordnet, or others)
- import portfolios automatically from external sources
- generate investment recommendations
- compare companies as investment opportunities
- advise you to act on any position
- use AI or LLMs
- access external APIs

Everything Atlas produces comes from files you create and maintain locally.

---

## Required Files

Two files are required:

| File | Purpose |
|------|---------|
| `portfolio.json` | Your current portfolio holdings |
| `watchlist.json` | Companies or ideas you are following |

Without both of these, the review cannot run.

---

## Optional Files

These files add context. Atlas continues without them — but their absence is
noted in Section 8 (Missing Evidence) and Section 10 (Non-Actions / Reasons to Wait).

| File / Directory | Purpose |
|------------------|---------|
| `investor_profile.json` | Risk tolerance, time horizon, principles, constraints |
| `decision_journal.json` | Notes from prior research decisions |
| `company_facts/` | Directory of per-ticker JSON files with company facts |
| `financials/` | Directory of per-ticker CSV files with historical financials |
| `scope_notes.md` | Free-text notes about the scope of this specific review |

---

## Recommended Folder Structure

Organise your input files in one directory per portfolio or review context.
The structure below matches the working examples included in this repository:

```
my_review/
  portfolio.json
  watchlist.json
  investor_profile.json
  decision_journal.json
  scope_notes.md
  company_facts/
    ASML.json
    MSFT.json
  financials/
    ASML.csv
    MSFT.csv
```

You do not need to use this exact layout. Any directory structure works as long
as you provide the correct paths when running the command.

Working examples are available at:
- `examples/weekly_review/` — minimal example bundle
- `examples/weekly_review_realistic/` — realistic 11-holding example bundle

---

## Portfolio File

`portfolio.json` describes your current holdings.

**Minimal valid example (positions format):**

```json
{
  "positions": [
    {
      "ticker": "EXAMPLE",
      "name": "Example Company",
      "sector": "Technology",
      "market_value": 25000,
      "currency": "EUR"
    },
    {
      "ticker": "CASHEUR",
      "name": "Cash EUR",
      "sector": "Cash",
      "market_value": 5000,
      "currency": "EUR"
    }
  ]
}
```

**Extended format (accounts-based):**

```json
{
  "accounts": [
    {
      "name": "Core Equity Portfolio",
      "currency": "EUR",
      "holdings": [
        {
          "ticker": "EXAMPLE",
          "name": "Example Company",
          "sector": "Technology",
          "market_value": 25000,
          "currency": "EUR",
          "role": "Core holding",
          "notes": "Long-term quality holding."
        }
      ]
    }
  ]
}
```

**Key fields:**

| Field | Required | Notes |
|-------|----------|-------|
| `ticker` | Yes | Short identifier used to match company facts and financials |
| `name` | Yes | Display name |
| `sector` | Recommended | Missing sector becomes `Unclassified` |
| `market_value` | One of these | Used to derive portfolio weights |
| `weight` | One of these | Provide directly if market values are not available |
| `currency` | Optional | Informational |
| `role` | Optional | E.g., "Core holding", "Satellite position" |
| `notes` | Optional | Free-text holding notes |

Notes:
- `market_value` and portfolio weight are derived automatically when `market_value` is provided across all holdings.
- If you provide `weight` directly, it must be a decimal fraction (e.g., `0.24` for 24%).
- Missing both `market_value` and `weight` is invalid.
- Cash holdings use sector `"Cash"` and are excluded from investable-ticker checks.

---

## Watchlist File

`watchlist.json` describes companies or ideas you are following.

**Example:**

```json
{
  "name": "Research Watchlist",
  "as_of": "2026-01-01",
  "items": [
    {
      "ticker": "EXAMPLE",
      "name": "Example Company",
      "status": "Needs More Evidence",
      "reason": "Strong business model under research. Margin durability unclear.",
      "evidence_needed": [
        "Margin durability through cost cycles",
        "Competitive positioning relative to peers"
      ],
      "open_questions": [
        "How does pricing power hold up in a downturn?",
        "What is the medium-term capital allocation plan?"
      ],
      "manual_observations": [
        "No position currently. Research in early stage."
      ],
      "notes": "Reason to wait: evidence on margin durability is needed before further consideration."
    }
  ]
}
```

**Key fields:**

| Field | Required | Notes |
|-------|----------|-------|
| `ticker` | Yes | |
| `name` | Yes | |
| `status` | Recommended | See allowed statuses below |
| `reason` | Optional | Why this is on the watchlist |
| `evidence_needed` | Optional | List of evidence gaps |
| `open_questions` | Optional | Questions to answer before changing status |
| `manual_observations` | Optional | Free-text observations |
| `notes` | Optional | Summary note for this review |

**Allowed statuses** (these are process statuses, not investment recommendations):

| Status | Meaning |
|--------|---------|
| `Watchlist` | Observation only; no active research |
| `Continue Research` | Active research in progress |
| `Needs More Evidence` | Research stalled; specific evidence required |
| `Suitable for Further Review` | Research substantially complete; further review warranted |
| `Not Suitable Under Current Constraints` | Does not fit current stated constraints |
| `Decision Deferred` | Decision paused pending new information |
| `No Action Warranted` | Review complete; no change to decision status warranted |

---

## Investor Profile File

`investor_profile.json` is optional. It describes your investment principles and constraints.

**Example:**

```json
{
  "risk_tolerance": "Balanced — quality focus",
  "time_horizon": "7-10 years",
  "principles": [
    "Evidence before opinion. No position without documented reasoning.",
    "Quality over quantity. Concentrated portfolio of well-understood businesses."
  ],
  "constraints": [
    "No leverage or margin trading.",
    "No companies with active financial misrepresentation history in the past 5 years."
  ]
}
```

When provided, Atlas renders your principles and constraints in three sections:

- **Section 5** (Portfolio Fit and Suitability Notes): risk tolerance, time horizon, and constraints
- **Section 6** (Risk and Principle Guardrails): principles listed as guardrail references
- **Section 10** (Non-Actions / Reasons to Wait): each principle as "Reason to Wait", each constraint as "No Action Warranted"

This makes your own stated investment discipline visible as part of the weekly process.

**Current limitation:** Atlas reads and displays profile fields but does not apply
them as rules or produce compliance assessments. Full profile-driven suitability
evaluation is deferred to a later sprint.

---

## Decision Journal File

`decision_journal.json` is optional. It records prior research decisions and follow-up triggers.

**Example:**

```json
[
  {
    "entry_id": "dj-2025-001",
    "decision_title": "EXAMPLE — thesis review",
    "asset_or_idea": "EXAMPLE",
    "decision_type": "Continue Research",
    "decision_date": "2025-10-01",
    "atlas_rating": "Continue Research",
    "atlas_view": "Business model is intact. Monitoring organic growth recovery.",
    "follow_up_triggers": [
      "Review after next earnings disclosure",
      "Revisit if revenue growth accelerates"
    ],
    "decision_notes": "No action warranted. Monitoring only."
  }
]
```

**Key fields:**

| Field | Notes |
|-------|-------|
| `decision_title` | Display title for the research note |
| `asset_or_idea` | Ticker or idea name |
| `decision_date` | ISO date (YYYY-MM-DD) — used for aging checks |
| `atlas_rating` | Process status (same allowed values as watchlist status) |
| `atlas_view` | Free-text summary of the current research view |
| `follow_up_triggers` | List of conditions that should trigger a revisit |
| `decision_notes` | Final note for this journal record |

**Date field priority** (first valid field found is used):
`decision_date` → `date` → `created_at` → `created` → `timestamp` → `review_date`

---

## Company Facts and Financials

These are optional directories of per-ticker files.

**Company facts** (`company_facts/TICKER.json`): free-form JSON with qualitative
company information. No required schema. Atlas detects presence/absence per ticker.

**Financials** (`financials/TICKER.csv`): historical financial data. Minimal
expected columns: `ticker`, `fiscal_year`, `revenue`, `net_income`, `free_cash_flow`.

Atlas checks which tickers in your portfolio and watchlist have facts and financials
files available. Missing files appear in Section 8 (Missing Evidence) and Section 10
(Non-Actions / Reasons to Wait) as specific ticker lists — not just generic "no data" notices.

---

## Running the Weekly Review

**Full command with all optional inputs:**

```bash
atlas weekly-review \
  --portfolio my_review/portfolio.json \
  --watchlist my_review/watchlist.json \
  --profile my_review/investor_profile.json \
  --journal my_review/decision_journal.json \
  --company-facts my_review/company_facts \
  --financials my_review/financials \
  --as-of 2026-01-01 \
  --scope-notes my_review/scope_notes.md
```

**Minimal command (required files only):**

```bash
atlas weekly-review \
  --portfolio my_review/portfolio.json \
  --watchlist my_review/watchlist.json
```

**Using the included realistic example:**

```bash
atlas weekly-review \
  --portfolio examples/weekly_review_realistic/portfolio.json \
  --watchlist examples/weekly_review_realistic/watchlist.json \
  --profile examples/weekly_review_realistic/investor_profile.json \
  --journal examples/weekly_review_realistic/decision_journal.json \
  --company-facts examples/weekly_review_realistic/company_facts \
  --financials examples/weekly_review_realistic/financials \
  --as-of 2026-01-01
```

**`--as-of` note:** Provide a date in `YYYY-MM-DD` format. This is used for journal aging checks.
If omitted, aging notes are not rendered (no live-clock dependency is introduced).

---

## Understanding the Output

The review produces 10 sections. Each section is derived exclusively from your local files.

### 1. Review Scope

What it tells you: which files were loaded, how many holdings and watchlist items,
and whether optional inputs are available.

What it does not tell you: nothing is inferred or fetched externally.

### 2. Portfolio Context

What it tells you: your holdings sorted by weight, sector exposure, concentration
notes (single positions above 25%, top-2 combined above 40%), and cash position.

What it does not tell you: no performance data, no valuation, no live prices.

### 3. Watchlist Review

What it tells you: each watchlist item with its status, reason, evidence gaps,
open questions, observations, and notes.

What it does not tell you: no comparative analysis between watchlist items.

### 4. Company Reviews Needing Attention

What it tells you: watchlist items with open evidence gaps, portfolio holdings
above 20% weight, and holdings missing sector classification.

What it does not tell you: no assessment of company quality or merit.

### 5. Portfolio Fit and Suitability Notes

What it tells you: your stated risk tolerance, time horizon, and constraints
(from investor profile), plus structural concentration observations.

What it does not tell you: no compliance assessment, no personalised guidance.

### 6. Risk and Principle Guardrails

What it tells you: your stated principles (from investor profile), any
user-supplied risk scores above 60, and sector concentration above 35%.

What it does not tell you: no engine-level risk assessment, no automated
principles enforcement.

### 7. Open Decisions

What it tells you: a summary of each decision journal note with its status,
follow-up triggers, and abbreviated view. Entries older than 90 days (when
`--as-of` is provided) receive an **Aging Note** indicating assumptions may
need to be rechecked.

What it does not tell you: no recommendation, no urgency, no action instruction.

### 8. Missing Evidence

What it tells you: evidence gaps from each watchlist item, the specific tickers
missing company facts files, and the specific tickers missing financials files.

What it does not tell you: no assessment of which gaps are most important.

### 9. Follow-Up Questions

What it tells you: open questions from watchlist items and follow-up triggers
from journal notes.

What it does not tell you: no answers.

### 10. Non-Actions / Reasons to Wait

What it tells you: all the reasons why no decision change is warranted in this
review cycle — deferred items, evidence gaps, missing data, and stale journal notes.

What it does not tell you: what to do. No action is suggested.

---

## Section 10: Non-Actions / Reasons to Wait

Section 10 is the most important section to read.

Atlas treats no action as a valid — and often the most appropriate — outcome of
a weekly review. Section 10 makes the reasons visible:

- **Deferred watchlist items:** items with status `Decision Deferred` or
  `Needs More Evidence` are listed explicitly.
- **Evidence gaps:** the count of open evidence gaps across all watchlist items.
- **Missing optional data:** investor profile, decision journal, company facts,
  or financials not provided.
- **Per-ticker missing facts:** specific tickers without company facts files.
- **Per-ticker missing financials:** specific tickers without financials files.
- **Aged journal notes:** journal notes older than 90 days, flagged as needing
  assumption refresh (see Journal Aging Notes below).
- **Profile-derived reasons:** each stated principle appears as a "Reason to
  Wait" and each stated constraint appears as a "No Action Warranted" note —
  making your own investment discipline visible as part of the weekly review.

The section always ends with a reminder: this review is informational only.
Atlas supports better judgment. It does not replace it.

---

## Journal Aging Notes

If `--as-of` is provided, Atlas checks whether any open decision journal notes
are older than 90 calendar days.

- An entry must be **strictly older than 90 days** to be flagged (exactly 90 days is not flagged).
- Only **open** entries are flagged. Entries with status `Closed`, `Archived`,
  `Completed`, or `Resolved` are skipped.
- Entries with no parseable date receive a `[Date Missing]` note in Section 7.
- Aged entries appear as:
  - **Section 7:** `[Aging Note] TICKER: Review date is older than 90 days (N days). Thesis assumptions may need to be rechecked.`
  - **Section 10:** `Reason to Wait: TICKER decision journal notes are older than 90 days (N days). Assumptions should be refreshed before changing decision status.`

Aging notes are reminders to refresh assumptions. They are not action instructions.

---

## Common Warnings

Warnings appear in the **Input Warnings** section at the top of the review.
They do not block the review from running.

| Warning code | Meaning | What to do before next run |
|--------------|---------|---------------------------|
| `missing_sector` | A holding has no sector specified | Add `"sector"` to the holding in `portfolio.json` |
| `missing_watchlist_status` | A watchlist item has no status | Add a `"status"` field to the item in `watchlist.json` |
| `unknown_watchlist_status` | A watchlist item has an unrecognised status | Replace with one of the allowed status values |
| `invalid_profile` | The investor profile file could not be parsed | Check `investor_profile.json` for JSON formatting errors |
| `invalid_profile_principles` | The `principles` field is not a list | Change `"principles"` to a JSON array of strings |
| `invalid_profile_constraints` | The `constraints` field is not a list | Change `"constraints"` to a JSON array of strings |
| `invalid_journal` | The journal file could not be parsed | Check `decision_journal.json` for JSON formatting errors |

Missing optional files (profile, journal, company facts, financials) are noted
in Section 8 and Section 10 rather than as warnings. They are informational,
not errors.

---

## Weekly Update Routine

Before each weekly review:

1. **Update `portfolio.json`** — adjust market values or weights to reflect the
   current approximate state of your portfolio. Exact values are not required;
   the goal is a reasonably current picture.

2. **Update `watchlist.json`** — add new evidence gaps and open questions since
   the last review. Update status if it has genuinely changed.

3. **Update `decision_journal.json`** — add a new note if you reviewed a
   company or made a research decision since the last run.

4. **Set `--as-of`** to today's date (or the relevant review date).

5. **Run `atlas weekly-review`** with your files.

6. **Read Section 8 and Section 10** before changing any watchlist status or
   decision journal status. Missing evidence and open reasons to wait should be
   resolved before a status changes.

7. **Update notes for next week** — add new evidence gaps and follow-up
   triggers to watchlist items while context is fresh.

There is no import step, no sync step, and no live data required. The entire
routine is manual and local.

---

## Current Limitations

Atlas Weekly Review v1 does not yet:

- fetch live market data or prices
- fetch live news or earnings releases
- connect to any broker (no Avanza, Nordnet, or similar)
- import portfolios from external sources automatically
- run the full company analysis engine inside the weekly review
- run the full suitability engine inside the weekly review
- analyse financial CSVs numerically (only checks file presence)
- support multiple currencies in weight calculations
- generate any investment recommendations
- provide a user interface
- support multiple languages in renderer output

These may be addressed in future sprints. No timeline is committed here.

---

## Next Steps

- Add company facts files (`company_facts/TICKER.json`) for your most important
  holdings to reduce missing-evidence notices.
- Add historical financials (`financials/TICKER.csv`) to enable future financial
  trend analysis.
- Keep your investor profile principles and constraints up to date — they appear
  directly in Sections 5 and 6.
- Review Section 10 weekly and update journal notes when assumptions change.
