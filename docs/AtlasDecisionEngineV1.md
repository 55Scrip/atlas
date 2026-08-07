# Atlas Decision Engine V1

**Created:** 2026-07-08 (Sprint 285)
**Status:** DEFINED — architecture specification. No runtime implementation.
**Connects:** [docs/InvestmentReviewPipelineV1.md](InvestmentReviewPipelineV1.md), [docs/EvidenceAssemblyV1.md](EvidenceAssemblyV1.md), [docs/EvidenceQualityReviewV1.md](EvidenceQualityReviewV1.md), [docs/AssumptionReviewV1.md](AssumptionReviewV1.md), [docs/RiskReviewV1.md](RiskReviewV1.md), [docs/ValueScenarioReview.md](ValueScenarioReview.md), [docs/AtlasDecisionJournal.md](AtlasDecisionJournal.md)

> **Superseded (partial), Atlas Phase 3.** This document's "Recommendations
> never generated" stance (below) is formally superseded by
> [docs/ATLAS_DECISION_ENGINE_DOCTRINE.md](ATLAS_DECISION_ENGINE_DOCTRINE.md)
> §8 and [docs/atlas_decision_engine/DE-001-Recommendation-Framework.md](atlas_decision_engine/DE-001-Recommendation-Framework.md),
> which define an explainable Atlas Recommendation framework. The rest of
> this document (the evidence-quality pipeline and its stages) is not
> superseded and remains informative background. Preserved here as
> historical record, not deleted.

---

## Purpose

This document defines the canonical Atlas Decision Engine.

It answers one question:

> **How does Atlas produce structured judgment from raw user input?**

The Decision Engine is the orchestration layer. It connects the pipeline stages defined in Sprints 280–284 into a complete, deterministic flow. It does not redefine those stages. It specifies how they interact: what flows between them, which stages are mandatory, which are optional, and how the output of each stage becomes the input of the next.

---

## The Complete Flow

```
User Input
 ↓
Classification
 ↓
Entity Extraction
 ↓
Evidence Assembly  (Stage 4)
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
Structured Judgment
 ↓
User
```

The flow is linear and deterministic. Each stage receives the structured output of the previous stage. No stage is skipped silently. If a stage cannot proceed, it produces an empty or incomplete output and records the reason. The next stage receives that output and behaves accordingly.

---

## Stages

### Classification

**Type:** Mandatory
**Input:** Raw user input (text, file, structured data)
**Output:** Input type label, confidence, subject entity candidates
**Depends on:** Nothing
**Referenced in:** [docs/AtlasSnapshotInputWorkflow.md](AtlasSnapshotInputWorkflow.md)

Classification identifies what type of input Atlas has received and what entity or entities the input concerns. Every other stage downstream depends on this classification being correct. If classification confidence is low, it is recorded and propagated — it is never silently resolved.

Classification determines which downstream stages are applicable and which are optional for this input.

---

### Entity Extraction

**Type:** Mandatory
**Input:** Classified input, subject entity candidates
**Output:** Resolved entity set (tickers, company names, portfolio references, watchlist entries)
**Depends on:** Classification
**Referenced in:** [docs/AtlasSnapshotInputWorkflow.md](AtlasSnapshotInputWorkflow.md)

Entity Extraction resolves the subject entities from the classified input. For a portfolio input, it resolves each holding. For a watchlist input, it resolves each watchlist entry. For a research note, it resolves the associated ticker. Ambiguous entities are flagged, not resolved silently.

---

### Evidence Assembly (Stage 4)

**Type:** Mandatory
**Input:** Resolved entity set, all available local evidence sources
**Output:** Canonical evidence set (normalised, deduplicated, source-linked)
**Depends on:** Entity Extraction
**Defined in:** [docs/EvidenceAssemblyV1.md](EvidenceAssemblyV1.md)

Evidence Assembly collects all available evidence for the resolved entities from local sources: company facts, research notes, decision journal, portfolio holdings, watchlist, weekly review observations, snapshot drafts, user observations, and historical revisions. It normalises, deduplicates, and links sources. The canonical evidence set is the sole evidence input to every downstream stage.

Eight V1 source types: `company_facts`, `research_notes`, `journal`, `portfolio`, `weekly_review`, `snapshot_draft`, `user_observation`, `historical_revision`.

---

### Evidence Quality Review (Stage 5)

**Type:** Mandatory
**Input:** Canonical evidence set
**Output:** Evidence quality assessment (quality level per item, gaps identified, uncertainty flags)
**Depends on:** Evidence Assembly
**Defined in:** [docs/EvidenceQualityReviewV1.md](EvidenceQualityReviewV1.md)

Evidence Quality Review assesses each item in the canonical evidence set across eight quality dimensions: Freshness, Source Quality, Corroboration, Conflicting Evidence, Missing Evidence, Traceability, Documentation Completeness, User Verification Status.

It assigns one of six quality levels to each item: Strong, Adequate, Incomplete, Weak, Outdated, Conflicting. Missing evidence is surfaced as an explicit gap — not treated as evidence of absence. The quality assessment travels downstream as metadata attached to every evidence item.

---

### Assumption Review (Stage 6)

**Type:** Mandatory
**Input:** Canonical evidence set, evidence quality assessment
**Output:** Assumption register (explicit assumptions, implicit assumptions surfaced, evidence links, open questions, revision candidates)
**Depends on:** Evidence Quality Review
**Defined in:** [docs/AssumptionReviewV1.md](AssumptionReviewV1.md)

Assumption Review extracts explicit assumptions from user-authored content and surfaces implicit assumptions embedded in the investment thesis. It links each assumption to evidence, identifies unsupported and conflicting assumptions, surfaces open questions, and flags revision candidates.

It does not resolve assumptions. It does not decide which assumptions are correct. It makes all assumptions visible — including those the user has not stated — so that Risk Review can operate on them.

---

### Risk Review (Stage 7)

**Type:** Mandatory
**Input:** Assumption register, canonical evidence set, evidence quality assessment
**Output:** Risk register (risk objects with category, description, linked assumptions, evidence links, uncertainty, monitoring triggers, review status)
**Depends on:** Assumption Review
**Defined in:** [docs/RiskReviewV1.md](RiskReviewV1.md)

Risk Review converts the assumption register and evidence quality outputs into a structured risk register. For each assumption that is unsupported, conflicting, or partially supported, it identifies the corresponding risk. For each evidence gap, it identifies the risk that the absence of evidence represents.

No scoring. No probability. Every material risk is linked to at least one assumption and, where possible, to at least one evidence item. The risk register is the primary input to Value Scenario Review.

---

### Value Scenario Review (Stage 8)

**Type:** Optional (required for holdings and portfolio reviews; may be absent for journal-only or research-only inputs)
**Input:** Risk register, assumption register, canonical evidence set, evidence quality assessment
**Output:** Value scenario set (scenario ranges, evidence quality labels, confidence labels, concentration notes, open questions)
**Depends on:** Risk Review
**Defined in:** [docs/ValueScenarioReview.md](ValueScenarioReview.md)

Value Scenario Review produces scenario-based value and return ranges — not point estimates. It covers three time horizons (short-term, medium-term, long-term) and three scenario cases (bear, base, bull). Scenario widths reflect the uncertainty visible in the risk register and evidence quality assessment. Scenarios with incomplete or weak evidence are wider. Scenarios with strong evidence are narrower.

Value Scenario Review never generates a single-point target, an action signal, or a prediction. It is always framed as a range under stated assumptions.

---

### Weekly Review (Stage 9)

**Type:** Optional (required for weekly-review inputs; may be absent for journal-only or research-only inputs)
**Input:** Value scenario set, risk register, assumption register, canonical evidence set
**Output:** Structured weekly review (per-ticker sections, open questions, reasons to wait, evidence gaps, research notes summary)
**Depends on:** Value Scenario Review (when present), Risk Review (when Value Scenario is absent)
**Referenced in:** Atlas Weekly Review CLI (`atlas weekly-review`)

Weekly Review produces the structured review document used by the user to conduct their regular investment review. It assembles the outputs of upstream stages into a coherent per-entity narrative. It surfaces open questions, monitoring triggers, and reasons to wait without generating action recommendations.

---

### Snapshot Draft (Stage 10)

**Type:** Optional (triggered by snapshot input; may be absent for non-snapshot inputs)
**Input:** Classified input, entity extraction output, Evidence Assembly output
**Output:** Structured snapshot draft (type, subject, confidence, uncertainties, confirmation status, target local file)
**Depends on:** Entity Extraction, Evidence Assembly
**Defined in:** [docs/AtlasSnapshotInputWorkflow.md](AtlasSnapshotInputWorkflow.md)

Snapshot Draft converts a classified snapshot input (portfolio snapshot, order, research note, price observation, news item, company filing, user observation) into a structured draft pending user confirmation. No data is written to local storage until the user explicitly confirms the draft. Rejected drafts are discarded. Confirmed drafts become inputs to subsequent Evidence Assembly cycles.

---

### Decision Journal (Stage 11)

**Type:** Optional (triggered when the user records a decision; may be absent for read-only review inputs)
**Input:** User decision content, associated evidence set, assumption register, risk register
**Output:** Structured journal entry (decision, rationale, evidence state at time of decision, assumption state at time of decision, revision history)
**Depends on:** Risk Review (for evidence and assumption state)
**Referenced in:** [docs/AtlasDecisionJournal.md](AtlasDecisionJournal.md)

The Decision Journal captures what the user decided, why, and what the evidence and assumption state was at the time. Journal entries are immutable once written; revisions produce new entries. The journal is a first-class evidence source for future Evidence Assembly cycles — prior decisions and their rationale become evidence that informs subsequent reviews.

---

### Structured Judgment

**Type:** Output
**Input:** All upstream stage outputs
**Output:** A coherent, traceable record of what Atlas observed, what evidence it assembled, what assumptions it found, what risks it identified, what scenarios it described, and what the user reviewed

Structured Judgment is not a recommendation. It is the complete record of Atlas's deterministic analysis. It is traceable: every conclusion links to an assumption; every assumption links to evidence; every risk links to both. The user reads the structured judgment and decides what to do. Atlas does not decide for the user.

---

## Mandatory and Optional Stages

| Stage | Mandatory | Optional | Notes |
|---|---|---|---|
| Classification | ✓ | | Always runs |
| Entity Extraction | ✓ | | Always runs |
| Evidence Assembly | ✓ | | Always runs |
| Evidence Quality Review | ✓ | | Always runs |
| Assumption Review | ✓ | | Always runs |
| Risk Review | ✓ | | Always runs |
| Value Scenario Review | | ✓ | Runs for holding and portfolio reviews |
| Weekly Review | | ✓ | Runs for weekly review inputs |
| Snapshot Draft | | ✓ | Runs for snapshot inputs |
| Decision Journal | | ✓ | Runs when user records a decision |

The mandatory stages (Classification through Risk Review) run for every input. They form the irreducible core of the Decision Engine. No downstream stage is permitted to run without the outputs of all mandatory stages being available.

---

## Stage Dependencies

```
Classification
 └─ Entity Extraction
     └─ Evidence Assembly
         └─ Evidence Quality Review
             └─ Assumption Review
                 └─ Risk Review
                     ├─ Value Scenario Review
                     │   └─ Weekly Review
                     └─ Decision Journal
Entity Extraction
 └─ Snapshot Draft
```

Evidence Assembly, Evidence Quality Review, Assumption Review, and Risk Review form a strict linear chain. Each stage takes exactly the output of the stage before it as input. No stage in this chain may skip a predecessor.

Value Scenario Review and Decision Journal both take Risk Review output as input. They may run independently of each other. Weekly Review takes Value Scenario Review output as input (or Risk Review output if Value Scenario is absent).

Snapshot Draft takes Entity Extraction output as input. It runs independently of the main analytical chain.

---

## What Flows Between Stages

| From | To | What flows |
|---|---|---|
| Classification | Entity Extraction | Input type, confidence, entity candidates |
| Entity Extraction | Evidence Assembly | Resolved entity set |
| Entity Extraction | Snapshot Draft | Resolved entity set, classification label |
| Evidence Assembly | Evidence Quality Review | Canonical evidence set |
| Evidence Quality Review | Assumption Review | Evidence set with quality metadata |
| Assumption Review | Risk Review | Assumption register, evidence set, quality metadata |
| Risk Review | Value Scenario Review | Risk register, assumption register, evidence set |
| Risk Review | Decision Journal | Evidence state, assumption state at time of decision |
| Value Scenario Review | Weekly Review | Value scenario set, risk register, assumption register |

---

## Canonical Principles

### Deterministic first
Given the same inputs, the Decision Engine always produces the same outputs. No stage introduces randomness, sampling, or model variance. Determinism is the default. Any future non-deterministic capability (AI reasoning) is explicitly labelled and isolated.

### Evidence before conclusions
No stage produces a conclusion before Evidence Assembly has run. Evidence is the foundation. Assumptions, risks, and scenarios are all built on evidence — not on heuristics or defaults.

### Assumptions explicit
Every assumption — whether stated by the user or surfaced by Atlas — is visible in the assumption register before Risk Review runs. No assumption is left implicit. No conclusion rests on an assumption that has not been surfaced.

### Uncertainty visible
Uncertainty is never hidden or averaged away. Evidence quality levels, assumption states, risk uncertainty fields, and scenario range widths all carry uncertainty explicitly. A stage that cannot produce high-confidence output says so.

### Recommendations never generated
No stage in the Decision Engine generates an action recommendation. The engine does not tell the user to take any action. The output is always a structured description of what Atlas observed — not what the user should do.

### User content preserved
User-authored content — research notes, journal entries, observations, decisions — is preserved exactly as written. Atlas does not paraphrase, summarise, or re-interpret user content. It organises and links it.

### Revisions accumulate
Prior outputs are not deleted when new inputs arrive. Historical evidence states, assumption registers, risk registers, and scenario sets are preserved in revision history. The decision journal is immutable. New inputs produce new versions alongside prior ones.

### Structured judgment over prediction
The engine produces structured judgment: a traceable record of analysis. It does not produce predictions about what will happen, forecasts of future prices, or probability estimates of outcomes. Structured judgment is always the output. Prediction is never the output.

---

## Extension Points

The Decision Engine is designed so that future capabilities connect as inputs, not as architectural changes. Every future source feeds into Evidence Assembly or Classification. It does not change how the stages work.

| Future capability | Where it connects | How |
|---|---|---|
| AI reasoning | Assumption Review, Risk Review | Surfaces additional implicit assumptions and risks; labelled AI-derived; subject to same evidence-linkage requirements |
| Market data | Evidence Assembly | Becomes an evidence source; subject to Evidence Quality Review |
| SEC filings | Evidence Assembly | Becomes a primary evidence source; high traceability |
| Earnings transcripts | Evidence Assembly | Becomes a primary source for management assumption assessment |
| Broker sync | Evidence Assembly, Classification | Portfolio and order data enters as structured input |
| OCR | Classification, Evidence Assembly | Converts physical documents to structured evidence before assembly |
| Collaboration | Evidence Assembly | Multiple users contribute evidence; conflict detection applies |

**Principle:** No future capability bypasses Classification, Evidence Assembly, or Evidence Quality Review. Every input is classified, assembled, and quality-assessed before reaching Assumption Review or Risk Review. The core chain is invariant.

---

## What This Document Is Not

- This is not a runtime implementation.
- This is not a configuration schema.
- This is not a workflow engine specification.
- This is not an AI system prompt.
- This is not a rendering or output format specification.
- This is not a persistence or storage schema.

It is a definition of how Atlas thinks: the sequence of stages, what flows between them, and what principles govern every stage. The implementation of each stage is defined in the referenced documents. This document defines how they connect.

---

## Sprint 286 Target

**Architecture Review and Alpha Planning**

Atlas now has a complete architectural foundation: Evidence Assembly, Evidence Quality Review, Assumption Review, Risk Review, Value Scenario Review, Weekly Review, Snapshot Drafts, Decision Journal, and the Decision Engine connecting them.

Sprint 286 should evaluate whether this architecture is sufficient to begin focusing on the first real end-to-end user experience. It should ask: what does a user actually do, from first input to structured judgment, in the current Atlas? What works end-to-end today? What gaps remain between the defined architecture and a usable alpha experience? Sprint 286 is a planning and evaluation sprint, not an architecture sprint.
