# Evidence Assembly V1

**Created:** 2026-07-08 (Sprint 281)
**Status:** DEFINED — architecture specification. No runtime implementation.
**Depends on:** [docs/InvestmentReviewPipelineV1.md](InvestmentReviewPipelineV1.md)
**Pipeline stage:** Stage 4 — Evidence Assembly

---

## Purpose

This document defines how Atlas constructs one canonical evidence set from all available user information.

It answers:

> **What counts as evidence inside Atlas?**

It does not answer:

> ~~What investment is best?~~

---

## Evidence Philosophy

Atlas begins with evidence. Not conclusions. Not recommendations. Not predictions.

```
Evidence exists before judgment.
Judgment exists before action.
Action is outside Atlas.
```

Evidence is the raw material of investment reasoning. Without it, all downstream stages — Evidence Quality Review, Assumption Review, Risk Review, Value Scenario Review, Weekly Review — produce outputs of unknown reliability.

The quality of the final review is bounded by the quality of the evidence assembled at this stage. No later stage can compensate for evidence that was never collected, was misclassified, or was silently altered.

---

## Evidence vs Other Information

Evidence is not the same as other types of information that appear in investment reasoning. These categories are distinct and must not be conflated.

| Type | Definition | Example |
|---|---|---|
| **Evidence** | A verifiable observation with a traceable source | "Microsoft revenue grew 14% in Q2 2026 (earnings release, 2026-07-24)" |
| **Observation** | A direct user note without a primary source citation | "Revenue growth appeared to accelerate in the call" |
| **Assumption** | A belief held without direct evidence | "AI demand continues" |
| **Question** | An open item requiring investigation | "Need to verify Azure growth next quarter" |
| **Hypothesis** | A testable proposition not yet confirmed | "Margin expansion may continue if headcount growth slows" |
| **Risk** | A condition that could invalidate a thesis | "If rates rise, valuation multiple may compress" |
| **Opinion** | A judgment not grounded in traceable evidence | "Microsoft is probably undervalued" |
| **Decision** | An action or commitment made by the user | "Added 5% to position on 2026-07-01" |

**Examples:**

```
Microsoft revenue grew 14% in Q2 2026.
→ Evidence  (source: earnings release)

Microsoft is probably undervalued.
→ Opinion  (no traceable source)

AI demand continues at this rate.
→ Assumption  (not directly evidenced)

Need to verify Azure growth next quarter.
→ Question

Margin expansion may continue if headcount growth slows.
→ Hypothesis

If rates rise 100bps, the multiple may compress.
→ Risk

Added 5% to position.
→ Decision
```

Atlas assembles evidence. It preserves observations, assumptions, questions, hypotheses, risks, and opinions — but it never promotes them to evidence status without a traceable source.

---

## Canonical Evidence Categories

### 1. Company Facts

**Purpose:** Structured foundational data about a company — business model, sector, exchange, identifiers, and user-verified company-level notes.

**Strengths:** Stable, structured, user-controlled, no external dependency.

**Weaknesses:** Does not contain financial performance data. Must be kept current by the user.

**Expected freshness:** Durable (weeks to months). Business model changes slowly.

**Relationship to other evidence:** Provides entity anchors used by all other evidence categories. Research Notes, Decision Journal, and Portfolio Holdings reference Company Facts by ticker or Atlas ID.

---

### 2. Research Notes

**Purpose:** User-written per-ticker notes containing observations, excerpts from reports or calls, open questions, evidence gaps, risks to monitor, and reasons to wait.

**Strengths:** User-controlled, verbatim, directly reflects what the user has read and thought. High signal for qualitative reasoning.

**Weaknesses:** Unstructured. Freshness depends on when the user last updated the notes. May contain opinions mixed with evidence.

**Expected freshness:** Medium (days to weeks). Should be updated around earnings and news events.

**Relationship to other evidence:** Primary qualitative evidence source. Links to Company Facts by ticker. Referenced by Value Scenario assumptions and change triggers.

---

### 3. Decision Journal

**Purpose:** A structured record of past investment decisions, the reasoning held at the time, assumptions made, and how the view evolved.

**Strengths:** Provides longitudinal context. Makes assumption drift visible. Allows comparison of past reasoning to current evidence.

**Weaknesses:** Retrospective. Does not directly inform current evidence quality — only historical reasoning quality.

**Expected freshness:** Historical (each entry is a point-in-time snapshot). Never updated retroactively.

**Relationship to other evidence:** Provides revision history context for Value Scenario Review and Assumption Review. Linked to Company Facts and Research Notes by ticker and date.

---

### 4. Portfolio Holdings

**Purpose:** The user's current positions — tickers, quantities, cost basis, acquisition dates, and portfolio weights.

**Strengths:** Directly reflects the user's actual exposure. Provides concentration data for Risk Review.

**Weaknesses:** Quantity and cost basis are user-provided and may be out of date. Does not contain performance data unless the user provides it.

**Expected freshness:** Medium (days to weeks). Should reflect the actual current portfolio.

**Relationship to other evidence:** Drives concentration risk assessment in Risk Review. Anchors Value Scenario Review subjects. Referenced by Weekly Review for position sizing context.

---

### 5. Watchlist

**Purpose:** Companies the user is monitoring but does not currently hold.

**Strengths:** Provides early-stage evidence context for companies under consideration.

**Weaknesses:** Evidence quality is typically lower than for holdings — research may be preliminary.

**Expected freshness:** Variable. A watchlist company may be researched intensively or only briefly noted.

**Relationship to other evidence:** Functions identically to a holding for Evidence Assembly purposes. Linked to Company Facts and Research Notes. May generate Snapshot Drafts.

---

### 6. Weekly Review Observations

**Purpose:** Observations surfaced during prior Weekly Reviews — evidence gaps identified, questions raised, holdings flagged for review, reasons to wait recorded.

**Strengths:** Structured, dated, and systematically produced. Provides a consistent cadence of evidence generation.

**Weaknesses:** Retrospective at time of next review. Does not contain new primary evidence — only synthesised observations from prior cycles.

**Expected freshness:** Recent (one week old by definition at next review). May become stale quickly if conditions change.

**Relationship to other evidence:** Feeds forward into Evidence Assembly for the next review cycle. Open questions from prior Weekly Reviews become evidence gaps for current assembly.

---

### 7. Snapshot Drafts

**Purpose:** Structured draft objects produced from classified user input — pasted text, uploaded documents, or typed observations — that have been validated but not yet confirmed.

**Strengths:** Structured, typed, and validated against the schema. Higher quality than raw text input.

**Weaknesses:** Not confirmed. Snapshot Drafts are provisional until the user explicitly confirms them.

**Expected freshness:** Current (recent user input). Drafts are session-scoped by default.

**Relationship to other evidence:** May become Research Notes, Company Facts, or Decision Journal entries after confirmation. Before confirmation, they are provisional evidence only.

---

### 8. User Observations

**Purpose:** Unstructured or semi-structured text entered directly by the user — typed notes, pasted excerpts, inline comments — that has not yet been classified as a specific evidence type.

**Strengths:** Direct and immediate. Captures user reasoning as it is formed.

**Weaknesses:** Unclassified. Requires Evidence Assembly to determine category. May contain a mix of evidence, opinion, and assumption.

**Expected freshness:** Current (entered in the current session or recently).

**Relationship to other evidence:** Feeds into Classification (Stage 2) and then into Evidence Assembly. May resolve into Research Notes, Snapshot Drafts, or Decision Journal entries.

---

### 9. Historical Revisions

**Purpose:** Prior versions of user-provided evidence — earlier drafts of research notes, superseded assumptions, revised position sizes, prior view statements.

**Strengths:** Allows comparison of how evidence and reasoning have evolved. Supports learning and self-correction.

**Weaknesses:** No longer current. Must be treated as historical context, not current evidence.

**Expected freshness:** Historical (explicitly dated). Never used as current evidence without explicit user reference.

**Relationship to other evidence:** Referenced by Decision Journal and Assumption Review. Preserved in revision history. Never overwritten.

---

### 10. External Documents (Future)

**Purpose:** Documents not authored by the user — SEC filings, earnings transcripts, annual reports, broker research, news articles.

**Strengths:** Primary sources. High quality when recent and unambiguous.

**Weaknesses:** Not yet available in Atlas V1. Require ingestion, parsing, and classification before they become evidence. Quality varies by source type.

**Expected freshness:** Depends on document type. SEC filings: quarterly. Earnings transcripts: quarterly. News: daily or faster.

**Relationship to other evidence:** Will feed into Evidence Assembly at Stage 4 via dedicated ingestion. Will not bypass Evidence Quality Review. Subject to the same source traceability requirements as all other evidence.

---

## Evidence Assembly Flow

The following flow is deterministic. No AI is required. Given the same input, it produces the same evidence set.

```
Raw Input
 ↓
Evidence Extraction
 (identify what type of information each item is)
 ↓
Normalization
 (canonical tickers, dates, quantities, evidence types)
 ↓
Deduplication
 (identify overlapping items from multiple sources)
 ↓
Source Linking
 (attach source reference and date to every item)
 ↓
User Content Preservation
 (verbatim text preserved; no rewriting)
 ↓
Canonical Evidence Set
 ↓
Evidence Quality Review
 (Stage 5 of the Investment Review Pipeline)
```

### Evidence Extraction

Each input item is classified as one of: Evidence, Observation, Assumption, Question, Hypothesis, Risk, Opinion, or Decision. Only items classified as Evidence or Observation advance to the canonical evidence set. All other types are preserved separately for Assumption Review (Stage 6) and Risk Review (Stage 7).

### Normalization

Tickers are normalised to canonical form (e.g. `MSFT`, not `Microsoft`). Dates are converted to ISO 8601 (`YYYY-MM-DD`). Quantities use canonical units. Evidence type uses canonical English values.

### Deduplication

If the same fact appears in multiple sources (e.g., the same revenue figure appears in both a Research Note and a Snapshot Draft), both are preserved with their respective source references. The canonical evidence set records both sources. Deduplication means identifying overlap — not discarding one source.

### Source Linking

Every evidence item in the canonical set carries:
- `source_type` — which category provided it (see Source Traceability below)
- `source_reference` — a human-readable reference (e.g., "Q2 2026 earnings release")
- `evidence_date` — when the evidence was produced or last confirmed
- `added_by` — user-provided or Atlas-derived (never AI-inferred without label)

### User Content Preservation

User-written text — notes, descriptions, reasons, excerpts — is preserved verbatim. Atlas never rewrites, paraphrases, or summarises user evidence without explicit user action. If Atlas needs to display a shortened version, it references the full original.

---

## Source Traceability

Every evidence item must be traceable to a source. The following source types are supported in V1:

| Source Type | Description |
|---|---|
| `company_facts` | Company Facts record in Atlas |
| `research_notes` | User-written Research Notes file |
| `journal` | Decision Journal entry |
| `portfolio` | Portfolio holdings record |
| `weekly_review` | Prior Weekly Review observation |
| `snapshot_draft` | Confirmed or provisional Snapshot Draft |
| `user_observation` | Direct user input (typed or pasted) |
| `historical_revision` | Prior version of another evidence item |

**Future source types (not yet implemented):**

| Source Type | Description |
|---|---|
| `sec_filing` | SEC EDGAR filing |
| `earnings_transcript` | Earnings call transcript |
| `annual_report` | Company annual report |
| `broker_import` | Broker-synced data |
| `market_data` | Live or historical price/fundamental data |
| `ai_summary` | AI-generated summary (requires labelling as AI-derived) |

**Traceability principle:** An evidence item with no traceable source is not evidence. It is an opinion or an assumption. It must be classified and treated accordingly.

---

## Evidence Quality Inputs

The following factors affect evidence quality. They are inputs to Stage 5 (Evidence Quality Review). They are defined here — not scored here.

| Factor | Description |
|---|---|
| **Freshness** | How recently was this evidence produced or confirmed? |
| **Source quality** | Is the source primary (company filing) or secondary (user note about a note)? |
| **Corroboration** | Does more than one independent source support this claim? |
| **Conflicting evidence** | Does any other evidence contradict this item? |
| **Missing evidence** | Is evidence that should exist simply absent? |
| **Traceability** | Can the source be identified and referenced? |
| **User confidence** | Has the user expressed a confidence level for this item? |
| **Documentation quality** | Is the evidence clearly described with enough context to re-evaluate later? |

**No scoring occurs at this stage.** Evidence Quality Review (Stage 5) applies these factors to produce quality assessments.

---

## Canonical Evidence Principles

These principles apply to every step of Evidence Assembly.

### Evidence before conclusions
The evidence set is assembled before any judgment is produced. Evidence Assembly has no access to downstream outputs. It cannot be influenced by what the user expects the review to say.

### Preserve provenance
Every evidence item carries its source type, source reference, and date. Provenance is never discarded. Provenance cannot be retroactively altered.

### Preserve user wording
User-written text is never rewritten. If Atlas references a user note, it references it verbatim or with clear attribution. Atlas does not summarise user evidence without the user's knowledge.

### Evidence can conflict
Conflicting evidence is preserved. Both items appear in the canonical evidence set. The conflict is surfaced in Evidence Quality Review (Stage 5). Atlas does not silently resolve conflicts.

### Uncertainty is allowed
An evidence set with gaps, conflicts, or low-quality items is a valid and informative evidence set. It produces an accurate picture of what is and is not known. Uncertainty is a first-class output.

### Missing evidence is itself evidence
If evidence that should exist cannot be found, that absence is recorded as an evidence gap. Evidence gaps are a first-class output of Evidence Assembly. They are not hidden.

### Newer evidence does not automatically replace older evidence
A newer source does not automatically supersede an older one. Both are preserved. The relationship between them — supersession, corroboration, or conflict — is determined by the user or surfaced in Evidence Quality Review.

### Revisions preserve history
When a user updates Research Notes or a Decision Journal entry, the prior version is retained as a Historical Revision. The evidence set records that a change occurred and when.

### Evidence is deterministic
Given the same inputs, Evidence Assembly produces the same canonical evidence set. No randomness. No AI inference without explicit labelling.

### Evidence is independent of recommendations
The canonical evidence set is produced before any recommendation could be made. Evidence Assembly does not consider what recommendation might follow. The evidence is what it is.

---

## Relationship to the Investment Review Pipeline

```
Input  (Stage 1)
 ↓
Classification  (Stage 2)
 ↓
Entity Extraction  (Stage 3)
 ↓
Evidence Assembly  (Stage 4)  ←  defined in this document
 ↓
Evidence Quality Review  (Stage 5)
 ↓
Assumption Review  (Stage 6)
 ↓
Risk Review  (Stage 7)
 ↓
Value Scenario Review  (Stage 8)
 ↓
Weekly Review  (Stage 9)
 ↓
Snapshot Draft  (Stage 10)
 ↓
Decision Journal  (Stage 11)
 ↓
Workspace / Save  (Stage 12)
```

Evidence Assembly is the last stage that is purely about collection. Every stage after it is about reasoning over the evidence set it produces.

---

## Future Extension Points

The following capabilities extend Evidence Assembly by adding new source types. They do not change the assembly flow. They do not bypass Evidence Quality Review.

| Extension | How it plugs in | Notes |
|---|---|---|
| SEC filings | New source type: `sec_filing` | Ingested, parsed, classified before entry into assembly |
| Earnings transcripts | New source type: `earnings_transcript` | Primary source; high quality when current |
| Annual reports | New source type: `annual_report` | High quality; updated annually |
| Broker import | New source type: `broker_import` | Holdings and transaction data; replaces manual portfolio entry |
| OCR | Pre-processing step before Evidence Extraction | Converts images/PDFs to text before classification |
| AI summarisation | New source type: `ai_summary` | Must be labelled as AI-derived; subject to same traceability requirements |
| Market data | New source type: `market_data` | Price and fundamental data; freshness tracked strictly |

**Principle for all extensions:** New sources produce additional evidence items that enter at the Evidence Extraction step. They do not skip normalization, deduplication, source linking, or Evidence Quality Review. They do not change the canonical principles.

---

## What This Document Is Not

- This is not a database schema.
- This is not an API specification.
- This is not an AI architecture.
- This is not a recommendation framework.
- This is not a scoring model.
- This is not a calculation.

It is a definition of what Atlas considers evidence, how evidence is assembled, and what principles govern that assembly.

---

## Sprint 282 Target

**Define Evidence Quality Review V1**

After Atlas knows what evidence is and how it is assembled, the next logical step is to define how evidence quality is assessed before any assumptions, risks, or value scenarios are produced. This makes Stage 5 of the Investment Review Pipeline concrete while preserving Atlas's deterministic, evidence-first philosophy.
