# Atlas Snapshot / Screenshot Input Workflow

**Sprint:** 221
**Date:** 2026-07-04
**Status:** Specified — not yet implemented

---

## Overview

Snapshot Input is a future low-friction layer for supplying information to Atlas.
It is not implemented in Sprint 221. This document defines what it should become.

The guiding product principle:

> Snapshot Input should be a low-friction way for the user to provide information
> to Atlas, not a source of truth by itself.

Screenshots, pasted text, exported snippets, and manually supplied snapshots
should create **drafts**. Drafts should require **user confirmation** before they
are committed to any Atlas local input file. Atlas should never silently treat
visual extraction or text parsing as authoritative.

---

## Workflow Pattern

```
Screenshot / pasted text / exported snippet
  → classification
  → structured draft
  → uncertainty notes
  → user confirmation
  → Atlas local input
  → Weekly Review / Order Review / Decision Journal
```

This pattern applies to all seven supported snapshot types.

---

## Supported Snapshot Types

| # | Type | Target Atlas Structure |
|---|------|------------------------|
| 1 | Portfolio Snapshot | `portfolio.json` |
| 2 | Watchlist Snapshot | `watchlist.json` |
| 3 | Open Orders Snapshot | `decision_journal.json` or future `order_review.json` |
| 4 | News Snapshot | `scope_notes.md` or `research_notes/<ticker>/` |
| 5 | External Analysis Snapshot | `research_notes/<ticker>/<source>.md` or `company_facts/<ticker>.json` |
| 6 | Research Notes Snapshot | `research_notes/<ticker>/notes.md` or `decision_journal.json` |
| 7 | Company Facts Snapshot | `company_facts/<ticker>.json` |

---

## Type 1 — Portfolio Snapshot

**User-provided input examples:**
- Broker portfolio screenshot
- Exported portfolio table (PDF, CSV, copy-paste)
- Manually pasted holdings list

**Classification criteria:**
- Contains one or more recognisable holdings (names, tickers, ISINs, or values)
- May contain account or currency context

**Extracted draft fields:**

| Field | Confidence notes |
|-------|-----------------|
| account name | Visible or absent |
| holding name | Usually visible |
| ticker | Visible or must be user-confirmed |
| ISIN | Visible or absent |
| currency | Visible or must not be guessed |
| quantity | Visible or absent |
| market value | Visible or absent |
| weight | Visible, computed, or absent |
| sector | Visible or mapped to Unclassified |
| notes | User-supplied |
| confidence per field | Low / Medium / High |

**Uncertainty fields:**
- Missing ticker must be flagged — do not guess
- Missing market value and weight must be flagged
- Missing sector maps to `Unclassified` until user confirms
- Currency must not be guessed unless explicitly visible
- All values must be marked as: `visible`, `inferred`, or `user-confirmed`

**Confirmation requirements:**
- Full review before committing to `portfolio.json`
- Low-confidence fields must be highlighted
- Missing required fields must be shown

**Target Atlas structure:** `portfolio.json`

**Limitations:**
- Cannot verify values against live market prices
- Broker UI layouts vary and change over time
- Screenshots may be cropped or partial
- Decimal and currency separators are locale-dependent

---

## Type 2 — Watchlist Snapshot

**User-provided input examples:**
- Broker watchlist screenshot
- Copied watchlist table
- User list of companies being followed
- Exported watchlist

**Extracted draft fields:**
- `ticker`
- `name`
- `status` (default safe value: `Watchlist`)
- `reason`
- `evidence_needed`
- `open_questions`
- `manual_observations`
- `notes`

**Default safe status:** `Watchlist`

Do not infer strong conviction solely from a ticker's presence on a watchlist.
Thesis strength requires explicit user input.

**Confirmation requirements:** Full review before committing to `watchlist.json`

**Target Atlas structure:** `watchlist.json`

**Limitations:**
- Status must be confirmed by user, not assumed
- Evidence and questions require user elaboration

---

## Type 3 — Open Orders Snapshot

Open Orders snapshots should be handled carefully. Atlas does not execute,
change, or recommend orders.

**User-provided input examples:**
- Broker open orders screenshot
- Copied order table
- User-written list of pending orders

**Extracted draft fields:**
- `ticker`
- `order_type` (if visible)
- `quantity` (if visible)
- `limit_level` (if visible — descriptive only)
- `account` (if visible)
- `order_date` (if visible)
- `expiration` (if visible)
- `user_note`

**Safe framing:** Open order snapshots are used for process review only:
- Is this order still linked to a current thesis?
- Is the evidence that motivated it still current?
- Does it fit stated constraints?
- Is there a reason to wait or revisit?

**Target Atlas structure:** `decision_journal.json` or future `order_review.json`

**Out of scope (permanently):**
- Executing orders
- Changing orders
- Recommending order levels or timing
- Ranking orders by urgency
- Live order monitoring

---

## Type 4 — News Snapshot

**User-provided input examples:**
- News headline screenshot
- Article excerpt (copied text)
- Broker news feed screenshot
- User-written news summary

**Extracted draft fields:**
- `headline`
- `source` (if visible)
- `date` (if visible or user-supplied)
- `related_tickers` (if visible or user-confirmed)
- `summary`
- `affected_assumptions`
- `uncertainty_notes`

**Safe output framing:**
- Separate stated fact from interpretation
- List assumptions affected
- List evidence missing
- Note whether no action still remains reasonable

**Target Atlas structure:**
- `scope_notes.md` for review context
- `research_notes/<ticker>/` for ticker-specific news
- `decision_journal.json` if user confirms relevance to an open decision

**Limitations:**
- No live news dependency
- Atlas does not fetch or monitor news
- User-provided excerpts only — no scraping, no ingestion

---

## Type 5 — External Analysis Snapshot

**User-provided input examples:**
- Simply Wall St export or screenshot
- Börsdata excerpt
- TIKR, Morningstar, Seeking Alpha excerpt
- Quartr transcript excerpt
- Annual report excerpt
- Analyst note excerpt (user-copied)

Atlas treats all external analysis as user-supplied research notes, not verified data.

**Draft classification distinctions:**
- Stated facts vs forecasts
- Assumptions vs opinions
- Missing evidence
- Contradictions with existing notes

**Target Atlas structure:**
- `research_notes/<ticker>/<source>.md` by default
- `company_facts/<ticker>.json` only if user manually confirms individual fields as facts

**Limitations:**
- Do not automatically scrape external services
- Do not assume permission to ingest copyrighted or paid content
- User-provided excerpts are notes, not full-source reproduction
- Source provenance must be preserved in the draft

---

## Type 6 — Research Notes Snapshot

**User-provided input examples:**
- User's own investment notes
- Meeting notes
- Copied bullet list
- Manually written thesis
- Investment checklist

**Extracted draft fields:**
- `ticker`
- `thesis`
- `evidence_for`
- `evidence_against`
- `risks`
- `assumptions`
- `missing_evidence`
- `follow_up_questions`

**Target Atlas structure:**
- `research_notes/<ticker>/notes.md`
- `decision_journal.json`
- `scope_notes.md`

---

## Type 7 — Company Facts Snapshot

**User-provided input examples:**
- Company description (copied)
- Business model summary
- Key metrics table
- User-written company profile

**Extracted draft fields:**
- `ticker`
- `company_name`
- `business_summary`
- `sector`
- `geography`
- `revenue_drivers`
- `key_risks`
- `notes`

**Target Atlas structure:** `company_facts/<ticker>.json`

**Limitations:**
- Do not treat uncertain text as verified fact
- All fields require user confirmation before writing to `company_facts/`
- Numerical data must be explicitly marked as visible, inferred, or user-confirmed

---

## Classification Contract

The classification step produces a structured output before any draft is built.
Future implementations may use deterministic text matching, heuristics, or
AI-assisted parsing. Regardless of implementation method, the classification
output contract is:

```json
{
  "snapshot_type": "portfolio_snapshot",
  "confidence": "medium",
  "related_tickers": ["ASML", "MSFT"],
  "requires_confirmation": true,
  "uncertainties": [
    "Currency not visible for one holding",
    "Sector not visible"
  ]
}
```

**Supported `snapshot_type` values:**

```
portfolio_snapshot
watchlist_snapshot
open_orders_snapshot
news_snapshot
external_analysis_snapshot
research_notes_snapshot
company_facts_snapshot
unknown_snapshot
```

**Rules:**
- All non-trivial classifications must set `requires_confirmation: true`
- `unknown_snapshot` is a valid and safe output — do not force a classification
- Confidence levels: `high`, `medium`, `low`
- Low-confidence classifications must display uncertainty prominently

---

## Draft Contract

A draft is a temporary structured interpretation of user-supplied information
that is not committed to any Atlas local input file until the user confirms or
edits it.

**Required draft fields:**

| Field | Description |
|-------|-------------|
| `draft_id` | Unique identifier for this draft session |
| `snapshot_type` | Classification result |
| `source_description` | How the user described the input |
| `extracted_fields` | Structured interpretation of the input |
| `uncertainties` | List of uncertain or ambiguous fields |
| `missing_required_fields` | Fields required by the target structure that are absent |
| `confirmation_status` | Current status (see below) |
| `target_local_file` | Intended write target (e.g. `portfolio.json`) |
| `created_at` | Deterministic timestamp if available, or user-supplied |

---

## Confirmation Workflow

**Confirmation states:**

```
draft               — initial extraction, not yet reviewed
needs_user_review   — uncertainties or missing fields require user input
confirmed           — user has reviewed and approved
rejected            — user has discarded the draft
superseded          — a newer draft replaced this one
```

**Rules:**
- Drafts cannot update `portfolio.json`, `watchlist.json`, `decision_journal.json`,
  or any other Atlas local input file until `confirmation_status` is `confirmed`
- Low-confidence fields must be clearly marked before confirmation
- Missing required fields must be shown before confirmation is available
- User corrections override extracted values — user input is authoritative
- Confirmed data must be written in the standard Atlas local input format for the
  target structure

---

## Accuracy and Safety Guardrails

The following limitations must be displayed or handled by any snapshot input implementation:

- Screenshots may be incomplete or cropped
- OCR may misread values, especially for numbers and currency symbols
- Currency and decimal separators are ambiguous across locales
- Broker UI layouts change over time without notice
- Screenshots may omit important context (total portfolio, cash, account type)
- Atlas must display uncertainty prominently — never suppress it
- Atlas must ask for confirmation before writing to any local file
- Atlas must preserve the original user-provided context (text or description) in the draft
- No financial decision should be based solely on unconfirmed snapshot extraction

---

## Privacy and Security Boundary

- Screenshots may contain sensitive financial information (account numbers, balances, holdings)
- Local-first storage is preferred for all draft and confirmed data
- No broker credentials should ever be requested by Atlas
- No BankID or authentication data should be handled by Atlas
- Users should be able to redact screenshots before supplying them
- Atlas should avoid storing raw screenshots unless the user explicitly configures this
- Draft files should be stored locally, not transmitted to external services

---

## Mapping to Weekly Review

Snapshot Input is an input creation layer, not a replacement for Weekly Review
schemas. Weekly Review continues to consume structured local files. Snapshot Input
makes it easier to create and maintain those files.

| Snapshot Type | Target Local File | Weekly Review Effect |
|---------------|-------------------|---------------------|
| Portfolio Snapshot | `portfolio.json` | Section 1, 2, 4, 5, 6 |
| Watchlist Snapshot | `watchlist.json` | Section 1, 3, 4, 8, 9 |
| Open Orders Snapshot | `decision_journal.json` | Section 7, 10 |
| News Snapshot | `scope_notes.md` or `research_notes/` | Section 1, 8, 9 |
| External Analysis Snapshot | `research_notes/<ticker>/<source>.md` | Section 8, 9 |
| Research Notes Snapshot | `research_notes/<ticker>/notes.md` | Section 8, 9 |
| Company Facts Snapshot | `company_facts/<ticker>.json` | Section 8 evidence check |

---

## Relationship to Chat-First Workspace UX

Atlas is moving toward a chat-first product experience where users start by
sharing information rather than navigating a structure. Snapshot Input is the
foundational layer for this experience.

**Intended future UX:**

> The user shares a portfolio screenshot, open order, company analysis excerpt,
> news item, or question.
>
> Atlas classifies the input, creates a draft, asks for confirmation, and then
> updates or creates the relevant workspace.

**Future workspaces that Snapshot Input will feed:**

- Portfolio Structure
- Weekly Review
- Watchlist
- Open Decisions
- Order Review
- News / Evidence
- Company Analysis
- Risk and Principles
- Decision Journal

This does not require a UI, dashboard, or browser extension. The initial
implementation should work as a CLI workflow.

---

## Out of Scope

The following are explicitly out of scope for the Snapshot Input workflow, now
and in future sprints unless separately specified:

- OCR implementation
- Image processing or computer vision
- LLM-based parsing (may be added as an opt-in path, never as a requirement)
- Automatic screenshot ingestion (without user action)
- Broker login or session handling
- Avanza/Nordnet API sync
- Live portfolio synchronisation
- Order execution or modification
- Automated recommendations of any kind
- Price targets or valuation estimates
- Live news monitoring or ingestion
- Background alerts or push notifications
- UI or dashboard
- Multilingual renderer output

---

## Language Guardrails

All Snapshot Input output and drafts must avoid forbidden language:

**Forbidden:**
`Buy`, `Sell`, `Strong Buy`, `Strong Sell`, `Price Target`, `Target Price`,
`Urgent`, `Act Now`, `Must Buy`, `Must Sell`, `Guaranteed`, `Will Outperform`,
`Financial Advice`, `Entry`, `Exit`

**Allowed safe language:**
`Needs More Evidence`, `Continue Research`, `Watchlist`, `Suitable for Further Review`,
`Not Suitable Under Current Constraints`, `Decision Deferred`, `No Action Warranted`,
`Reason to Wait`, `Evidence Gap`, `Risk to Monitor`, `Assumption to Recheck`,
`Aging Note`, `Thesis Refresh`

Open Orders snapshots must use descriptive language only. Do not use action or
urgency framing when presenting order context.

---

## Provider / Network Boundary

This document is specification only.

No provider imports, network imports, runtime behavior changes, live data, or
broker API calls are introduced by Sprint 221. The provider/network boundary
established in internal v1 remains unchanged.

---

## Snapshot Draft Schema — DEFINED (Sprint 223)

Sprint 223 defined the formal Snapshot Draft schema as a typed Python dataclass
and local JSON file format. The schema lives in `atlas/snapshot_input/schema.py`.

**Key types:**
- `SnapshotType` — 8 supported snapshot types (string enum)
- `SnapshotConfirmationStatus` — 5 confirmation states
- `SnapshotConfidence` — 4 confidence levels (descriptive only)
- `SnapshotDraft` — full draft schema with required and optional fields
- `validate_snapshot_draft` — validation helper
- `load_snapshot_draft` / `save_snapshot_draft` — local file helpers

**Required draft fields:** `draft_id`, `snapshot_type`, `source_description`,
`extracted_fields`, `uncertainties`, `missing_required_fields`,
`confirmation_status`, `target_local_file`, `created_at`

**Optional fields:** `confidence`, `related_tickers`, `raw_source_reference`, `notes`

**Serialization:** `SnapshotDraft.to_dict()`, `from_dict()`, `to_json()`, `from_json()`
— deterministic, sort-keyed JSON output.

**Example drafts:** `examples/snapshot_drafts/` — portfolio, research notes, news.

---

## First Implementation Step — COMPLETE (Sprint 222)

The first implementation step was:

**Add research notes input** — completed in Sprint 222.

Research notes (`research_notes/<TICKER>/notes.md`) are now supported by the
Weekly Review CLI via `--research-notes DIR`. Evidence gaps appear in Section 8;
open questions and risks in Section 9; reasons to wait in Section 10.

This was implemented without OCR, image parsing, AI, broker integration, or live
data. It is the first concrete step from Snapshot Input specification toward a
working low-friction input layer.

---

## Repository Identity Confirmation

This is Atlas. This is not Atlas Edge. Atlas and Atlas Edge are separate products.
No Atlas Edge concepts, naming, or architecture are present in this document.
