# Investment Review Pipeline V1

**Created:** 2026-07-08 (Sprint 280)
**Status:** DEFINED — architecture specification. No runtime implementation.
**Depends on:** [docs/ValueScenarioReview.md](ValueScenarioReview.md), [docs/ValueScenarioDataModel.md](ValueScenarioDataModel.md), [docs/AtlasProductPositioningV1.md](AtlasProductPositioningV1.md)

---

## Purpose

This document defines the canonical internal Investment Review Pipeline for Atlas.

The pipeline defines how Atlas processes investment information from raw user input to structured investment judgment. It is internal architecture. It is not a UI, not a CLI, and not exposed to users directly.

The pipeline answers one question:

> **How does Atlas think?**

It does not answer:

> ~~What should the user buy?~~

---

## Core Principle

**Atlas never begins with conclusions. Atlas always begins with evidence.**

Every later stage depends on the quality of the previous stage. No stage may skip earlier reasoning. The pipeline is sequential. Skipping a stage means skipping reasoning.

---

## Pipeline Diagram

```
Input
 ↓
Classification
 ↓
Entity Extraction
 ↓
Evidence Assembly
 ↓
Evidence Quality Review
 ↓
Assumption Review
 ↓
Risk Review
 ↓
Value Scenario Review
 ↓
Weekly Review
 ↓
Snapshot Draft
 ↓
Decision Journal
 ↓
Workspace / Save
```

---

## Stage Definitions

### Stage 1 — Input

**Purpose:** Receive user material and produce structured input objects.

**Accepts:**
- Portfolio (holdings, quantities, cost basis)
- Watchlist (companies under consideration)
- Research notes (user-written observations, excerpts, questions)
- Decision journal entries
- Company facts (structured company data)
- User questions
- Pasted text (earnings calls, reports, notes)
- Mixed or unclassified input

**Output:** Structured input objects ready for classification.

**Constraints:**
- No transformation of user content.
- No interpretation at this stage.
- User-provided text is preserved verbatim.

---

### Stage 2 — Classification

**Purpose:** Determine what the input contains.

**Classifies:**
- Holdings (position in a company)
- Companies (entity reference without position)
- Questions (explicit or implicit)
- Research (evidence material)
- Notes (qualitative observations)
- Portfolio (collection of holdings)
- Unknown (cannot classify)

**Output:** Classification label with confidence level.

**Constraints:**
- Classification is not a recommendation.
- Unknown is a valid and expected output.
- Confidence must be reported, not hidden.

---

### Stage 3 — Entity Extraction

**Purpose:** Extract canonical structured entities from classified input.

**Extracts:**
- Ticker symbol
- Company name
- Quantities (shares, percentages, weights)
- Dates and time references
- Currencies and amounts
- Source references

**Output:** Canonical structured entities with source attribution.

**Constraints:**
- Canonical values remain in English.
- Ambiguous entities are flagged, not silently resolved.
- No inference beyond what is present in the input.

---

### Stage 4 — Evidence Assembly

**Purpose:** Collect all available evidence relevant to the extracted entities.

**Sources:**
- Company Facts (structured company data)
- Research Notes (user-written per-ticker notes)
- Decision Journal (prior decisions and their rationale)
- Portfolio (current position, cost basis, history)
- Historical user observations from prior reviews

**Output:** Assembled evidence set, with source and date for each item.

**Constraints:**
- Atlas does not generate evidence.
- Atlas only assembles existing evidence that the user has provided.
- Missing evidence is surfaced explicitly — it is not filled in.
- Evidence gaps are a first-class output of this stage.

---

### Stage 5 — Evidence Quality Review

**Purpose:** Assess the quality of the assembled evidence set.

**Quality levels:**
- `strong` — multiple consistent, recent, primary sources
- `adequate` — sufficient for a preliminary view; gaps exist
- `incomplete` — significant gaps; judgment limited
- `weak` — little supporting evidence; high uncertainty
- `conflicting` — evidence contradicts itself; requires resolution
- `outdated` — evidence exists but is no longer current

**Output:** Evidence quality assessment per entity and per claim, with reasons.

**Constraints:**
- No recommendations at this stage.
- Quality assessment is descriptive, not prescriptive.
- Conflicting evidence is surfaced, not resolved by Atlas.

---

### Stage 6 — Assumption Review

**Purpose:** Identify assumptions already present in the user's material and in Atlas's assembled evidence.

**Documents:**
- Explicit assumptions (stated by the user or source)
- Implicit assumptions (embedded in framing, comparisons, or projections)
- Unsupported assumptions (no evidence found for the claim)

**Output:** Assumption register with type (explicit / implicit / unsupported) and supporting evidence IDs.

**Constraints:**
- Do not invent assumptions.
- Do not resolve unsupported assumptions.
- Unsupported assumptions are reported as gaps, not filled.

---

### Stage 7 — Risk Review

**Purpose:** Surface risks relevant to the investment judgment.

**Risk categories:**
- Concentration (position size, sector, geography)
- Evidence gaps (missing information that would change the view)
- Dependency risks (thesis depends on unverified assumptions)
- Valuation sensitivity (range is wide or assumptions are uncertain)
- Macro sensitivity (exposure to rates, currency, cycle)
- Missing information (data that exists but has not been provided)

**Output:** Risk register with category, description, and relationship to assumptions and evidence.

**Constraints:**
- No scoring.
- No probability weighting.
- No ranking of risks by severity.
- Surfacing a risk is not a recommendation to act.

---

### Stage 8 — Value Scenario Review

**Purpose:** Apply the Value Scenario framework to express possible value ranges.

**Renders:**
- Scenario ranges (bear / base / bull / downside / upside / uncertainty band)
- Evidence quality per range
- Confidence per range
- Uncertainty notes
- Change triggers (what would cause the range to shift)
- Revision history

**Output:** `ValueScenarioReview` object (see `atlas/value_scenario/schema.py`).

**Constraints:**
- Never single-point targets.
- Ranges are driven by evidence and assumptions, not by calculation.
- Change triggers are explicit — not inferred.
- "No scenario warranted yet" is a valid output when evidence quality is too low.

---

### Stage 9 — Weekly Review

**Purpose:** Assemble a structured weekly investment review from the outputs of prior stages.

**Surfaces:**
- Evidence gaps requiring follow-up
- Reasons to wait (what would need to change before acting)
- Open questions to research
- Risks to monitor
- Holdings to review
- Explicit acknowledgement when no action is warranted

**Output:** Weekly Review report (see `atlas/weekly_review/`).

**Constraints:**
- No execution instructions.
- No urgency framing.
- "No action warranted" is a valid and complete output.

---

### Stage 10 — Snapshot Draft

**Purpose:** Generate structured draft objects that could become inputs to future decisions.

**Generates:**
- Snapshot Draft objects (see `atlas/snapshot_input/`)
- Classification, detected entities, uncertainties, missing fields

**Output:** `SnapshotDraft` object awaiting user confirmation.

**Constraints:**
- Never execute.
- Never mutate source material.
- Require explicit user confirmation before any downstream use.
- Draft status is always visible.

---

### Stage 11 — Decision Journal

**Purpose:** Capture the reasoning behind any decision or change in view.

**Captures:**
- What changed (position, view, assumption, confidence)
- Why (the reasoning at the time)
- Assumptions held at the time of the decision
- Revision history (how the view evolved)

**Output:** Journal entries linked to prior stages and entities.

**Constraints:**
- The journal is a record, not an instruction.
- Past entries are immutable.
- Revisions are additions, not replacements.
- The journal supports learning, not justification.

---

### Stage 12 — Workspace / Save

**Purpose:** Persist structured outputs after value has been created through the pipeline.

**Accepts:**
- Temporary Workspace (unsaved, session-scoped)
- Confirmed review outputs
- User-approved snapshots

**Output:** Persisted or in-session workspace objects.

**Constraints:**
- Persistence is optional. The pipeline runs without it.
- Account is optional.
- Nothing is saved without explicit user intent.
- Temporary Workspace requires no account.

---

## Cross-Cutting Principles

These principles apply to every stage of the pipeline.

### Evidence before conclusions
No stage produces a conclusion without evidence from a prior stage. The pipeline is not a shortcut to recommendations.

### Uncertainty always visible
Uncertainty is never hidden. Every stage that produces a judgment must also produce a confidence level and a description of what is unknown.

### Assumptions explicit
Assumptions are named and documented. Implicit assumptions are surfaced. Unsupported assumptions are flagged. Atlas does not silently adopt assumptions on the user's behalf.

### Revisions preserved
When a view changes, the prior view is preserved. The journal records what changed and why. History is not overwritten.

### User content preserved
User-provided text, notes, descriptions, and reasons are preserved verbatim throughout the pipeline. Atlas does not paraphrase or summarise user content without attribution.

### Canonical values remain English
All canonical field values (enum values, review types, case types, evidence quality levels, etc.) remain in English regardless of display locale. Localisation applies to display only.

### Deterministic first
The pipeline is deterministic by default. Given the same input, Atlas produces the same output. AI reasoning is a future optional extension, not a current dependency.

### No action warranted is a valid outcome
The pipeline may conclude that no action is warranted at this time. This is a complete and valid output. It is not a failure. It is not a placeholder. It is a judgment.

### AI optional in future
AI reasoning may be introduced at specific stages as an optional enhancement. It does not replace the pipeline. It does not skip stages. AI outputs are subject to the same evidence and assumption requirements as non-AI outputs.

---

## Future Extension Points

The following capabilities may be added to the pipeline at the stages noted, without changing the pipeline's structure or cross-cutting principles.

| Extension | Plugs into Stage | Notes |
|---|---|---|
| Market data (live prices, fundamentals) | Stage 4 — Evidence Assembly | Optional additional evidence source |
| Valuation models | Stage 8 — Value Scenario Review | Inputs to range construction; do not replace evidence review |
| AI reasoning | Stage 5, 6, 7, or 8 | Optional; subject to same quality and assumption requirements |
| OCR / document parsing | Stage 1 — Input | Converts images or PDFs to structured text before classification |
| Broker sync | Stage 1 — Input | Provides portfolio data automatically; replaces manual entry |
| Collaboration | Stage 12 — Workspace / Save | Shared workspaces; requires account system |
| News fetching | Stage 4 — Evidence Assembly | Current events as additional evidence; quality must be assessed |
| Earnings call transcripts | Stage 4 — Evidence Assembly | Primary source evidence; high quality when current |

**Principle for all extensions:** Extensions are inputs to existing stages. They do not add new stages. They do not skip reasoning. They do not replace the evidence-first pipeline.

---

## Relationship to Existing Atlas Capabilities

| Capability | Pipeline Stage(s) |
|---|---|
| Temporary Workspace | Stage 12 (Workspace / Save) |
| Snapshot Drafts | Stage 10 (Snapshot Draft) |
| Weekly Review | Stage 9 (Weekly Review) |
| Value Scenario Review | Stage 8 (Value Scenario Review) |
| Research Notes | Stage 4 (Evidence Assembly) |
| Company Facts | Stage 4 (Evidence Assembly) |
| Decision Journal | Stage 11 (Decision Journal) |
| Investor Profile | Stage 7 (Risk Review) — suitability context |

---

## What This Document Is Not

- This is not a UI specification.
- This is not a CLI specification.
- This is not an AI architecture.
- This is not a recommendation framework.
- This is not a valuation model.
- This is not a forecast.

It is a definition of how Atlas reasons — deterministically, evidence-first, with uncertainty always visible.

---

## Sprint 281 Target

**Define Evidence Assembly V1**

Evidence is the heart of Atlas. Before introducing valuation models, AI, or market data, Atlas should precisely define how evidence from Company Facts, Research Notes, Decision Journal, Weekly Review, and future sources is assembled into one canonical evidence set. This will make Stage 4 of the pipeline concrete and implementable.
