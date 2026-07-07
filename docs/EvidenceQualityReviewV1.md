# Evidence Quality Review V1

**Created:** 2026-07-08 (Sprint 282)
**Status:** DEFINED — architecture specification. No runtime implementation.
**Depends on:** [docs/EvidenceAssemblyV1.md](EvidenceAssemblyV1.md), [docs/InvestmentReviewPipelineV1.md](InvestmentReviewPipelineV1.md)
**Pipeline stage:** Stage 5 — Evidence Quality Review

---

## Purpose

This document defines how Atlas evaluates the quality of assembled evidence in a deterministic, recommendation-free manner.

It answers:

> **How trustworthy, complete, and current is the evidence available?**

It does not answer:

> ~~Is this investment good?~~

Evidence quality is not investment quality. A company may have strong evidence supporting a weak thesis. A company may have weak evidence about what could be an exceptional opportunity. Evidence quality tells Atlas how much confidence later stages may place in the assembled evidence — nothing more.

---

## Position in the Pipeline

```
Evidence Assembly  (Stage 4)
 ↓
Evidence Quality Review  (Stage 5)  ←  defined in this document
 ↓
Assumption Review  (Stage 6)
 ↓
Risk Review  (Stage 7)
 ↓
Value Scenario Review  (Stage 8)
 ↓
Weekly Review  (Stage 9)
```

Evidence Quality Review is the first stage that produces a judgment. Every judgment it produces is about the evidence — not about the investment.

---

## Evidence Quality Dimensions

The following dimensions are assessed for each evidence item and for the evidence set as a whole. No scores are assigned. No weights are calculated. Each dimension is assessed descriptively.

### 1. Freshness

**Definition:** How recently was this evidence produced, updated, or confirmed?

**Why it matters:** Investment-relevant facts change. An earnings report from three years ago may describe a fundamentally different business. A research note from last week may not yet reflect a major product announcement. Stale evidence misleads rather than informs.

**Freshness levels:**
- `current` — produced within the last four weeks, or confirmed as still accurate
- `recent` — produced one to three months ago; likely still relevant but should be verified
- `stale` — produced more than three months ago without reconfirmation; treat with caution
- `unknown` — no date available; freshness cannot be assessed

**Implication:** Stale or unknown freshness reduces overall evidence quality even when the evidence is otherwise strong.

---

### 2. Source Quality

**Definition:** How reliable and authoritative is the source of each evidence item?

**Why it matters:** A primary source (the company's own filing, a management earnings call) provides direct evidence. A secondary source (a user note summarising an article) introduces interpretation risk. An anonymous or unattributed source has no traceability.

**Source quality gradient (descriptive, not scored):**
- Primary and traceable — company filings, official earnings releases, regulatory disclosures
- User-verified primary — user-confirmed excerpts from primary sources with reference
- Secondary with attribution — research notes referencing a named source
- Secondary without attribution — notes with no source reference
- Unverifiable — no source, no date, no reference

**Implication:** Evidence with weak source quality requires corroboration before it can support high-confidence assumptions.

---

### 3. Corroboration

**Definition:** Does more than one independent source support the same claim?

**Why it matters:** A single source supporting a claim may be an outlier. Two independent sources that agree increase confidence. Multiple independent sources that consistently point in the same direction constitute strong corroboration.

**Corroboration states:**
- `corroborated` — two or more independent sources support the claim
- `single_source` — only one source supports the claim
- `uncorroborated` — no source directly supports the claim; the claim rests on inference

**Implication:** Uncorroborated evidence carries higher uncertainty. Single-source evidence should be flagged for follow-up before it is treated as a firm basis for assumptions.

---

### 4. Conflicting Evidence

**Definition:** Does any evidence in the set contradict or materially qualify another item?

**Why it matters:** Conflicting evidence is a signal — not a problem to be resolved silently. It indicates that the available information does not tell a consistent story. Hiding conflicts produces false confidence.

**Conflict types:**
- `direct_conflict` — two evidence items make mutually exclusive claims about the same fact
- `material_qualification` — one item qualifies or limits the scope of another without fully contradicting it
- `temporal_conflict` — an older item contradicts a newer one (may simply be supersession)
- `source_bias_conflict` — two sources with different incentives disagree

**Implication:** Conflicting evidence must remain visible. It is surfaced in Evidence Quality Review and carried forward into Assumption Review and Risk Review. Atlas does not resolve conflicts.

---

### 5. Missing Evidence

**Definition:** Is evidence that should exist simply absent from the assembled set?

**Why it matters:** An absence of evidence is not the same as evidence of absence — but it is meaningful information. If no revenue data exists for a company the user is considering, that gap matters. If no management commentary on margins exists, the silence is relevant.

**Missing evidence categories:**
- `expected_and_absent` — the evidence item should normally exist and does not (e.g., no company facts for a ticker)
- `referenced_and_missing` — a research note references a source that has not been provided
- `gap_identified` — the user or a prior review flagged that evidence is needed
- `unknown_completeness` — it is not known what evidence exists or should exist

**Implication:** Missing evidence produces evidence gaps. Evidence gaps are a first-class output of Evidence Quality Review. They feed directly into follow-up questions in Weekly Review (Stage 9).

---

### 6. Traceability

**Definition:** Can the origin of each evidence item be identified, referenced, and independently verified?

**Why it matters:** Evidence without a traceable source cannot be evaluated, updated, or challenged. If the origin of a claim is unknown, any downstream judgment resting on that claim is unreliable.

**Traceability levels:**
- `fully_traceable` — source type, source reference, and evidence date all present
- `partially_traceable` — source type known, but reference or date is missing
- `untraceable` — no source information available

**Implication:** Untraceable evidence items should be flagged as opinions or observations rather than evidence (see Evidence Assembly V1). If they are included in the evidence set, their untraceable status must be visible at every downstream stage.

---

### 7. Documentation Completeness

**Definition:** Is the evidence item described with enough context to be re-evaluated later?

**Why it matters:** An evidence item that was understandable when written may be ambiguous when reviewed three months later. Completeness means the description includes enough context — what was measured, when, under what conditions — that a future reader can re-evaluate it without returning to the original source.

**Completeness states:**
- `complete` — description, source, date, and relevant context are present
- `adequate` — sufficient for current use; minor context gaps exist
- `incomplete` — key context is missing; description is ambiguous or abbreviated
- `minimal` — only a label or fragment; no supporting context

---

### 8. User Verification Status

**Definition:** Has the user confirmed that this evidence is accurate and current?

**Why it matters:** Atlas assembles evidence from user-provided sources. The user is the ultimate authority on whether a piece of evidence is still valid. An unverified evidence item may have been superseded by events the user has not yet recorded.

**Verification states:**
- `user_confirmed` — user has explicitly confirmed accuracy and currency
- `unverified` — no user confirmation; accuracy assumed but not validated
- `flagged_for_review` — user or prior review flagged this item for verification

---

## Canonical Evidence Quality Levels

The following quality levels apply to both individual evidence items and to the evidence set as a whole. They are descriptive. They are not scores.

### Strong

**Characteristics:** Multiple recent, primary, traceable, corroborated sources. No significant conflicts. No material gaps. User has verified or recently reviewed.

**Strengths:** Supports high-confidence assumptions. Allows narrower scenario ranges. Reduces the number of follow-up questions required.

**Limitations:** Strong evidence can still be wrong. Past data does not guarantee future conditions. Strong evidence quality does not mean investment attractiveness.

**Downstream implications:** Scenario ranges may be narrower. Confidence levels may be higher. Fewer reasons to wait. Evidence gaps are minor or absent.

---

### Adequate

**Characteristics:** Sufficient evidence to form a preliminary view. Some gaps exist. Sources are mostly traceable. Freshness is acceptable. Minor conflicts may be present but are not material.

**Strengths:** Enough to proceed with preliminary judgment. Identifies what further evidence is needed.

**Limitations:** Should not support final high-confidence decisions. Gaps are present.

**Downstream implications:** Scenario ranges are moderate. Confidence is medium. Some follow-up questions generated. Reasons to wait may be present.

---

### Incomplete

**Characteristics:** Significant gaps in the evidence set. Key evidence items are missing or untraceable. Freshness is uncertain. Limited corroboration.

**Strengths:** Identifies what is unknown. Makes uncertainty visible.

**Limitations:** Cannot support assumptions with confidence. Downstream stages produce wide scenario ranges and many open questions.

**Downstream implications:** Scenario ranges are wide. Confidence is low. Significant follow-up questions generated. Reasons to wait are likely.

---

### Weak

**Characteristics:** Very little supporting evidence. Sources are secondary or unverifiable. No corroboration. Freshness unknown or stale. Material gaps present.

**Strengths:** Signals that judgment is premature. Produces clear evidence gap outputs.

**Limitations:** Cannot support any meaningful assumption. All downstream stages carry high uncertainty.

**Downstream implications:** Scenario ranges are very wide or absent. Confidence is unknown. Weekly Review surfaces evidence gathering as the primary recommended action. No scenario assumptions should be treated as firm.

---

### Outdated

**Characteristics:** Evidence exists but is no longer current. Sources may have been strong when produced. Freshness is `stale` for most or all items.

**Strengths:** Historical context is preserved. Prior views are still accessible.

**Limitations:** May no longer reflect the current state of the company, market, or user's position.

**Downstream implications:** Revision of evidence is the primary recommended action. Prior scenario ranges carry an explicit outdated label. Follow-up questions focus on refreshing evidence.

---

### Conflicting

**Characteristics:** Evidence items within the set directly contradict each other on material facts. Conflict may be temporal, source-based, or direct.

**Strengths:** Makes disagreements visible. Prevents false consensus from forming. Supports better hypothesis formation.

**Limitations:** Cannot be used to support a definitive assumption without resolving the conflict. Downstream stages carry explicit conflict visibility.

**Downstream implications:** Conflicting evidence is surfaced in Assumption Review and Risk Review. Scenario ranges should reflect the conflict by remaining wider. Weekly Review surfaces conflict resolution as a follow-up item.

---

## Deterministic Review Flow

The following flow is deterministic. No AI is required. Given the same evidence set, it produces the same quality assessment.

```
Evidence Set  (from Stage 4)
 ↓
Freshness Review
 (assess freshness level of each item)
 ↓
Source Review
 (assess source quality and traceability of each item)
 ↓
Corroboration Review
 (identify which claims are supported by multiple sources)
 ↓
Conflict Review
 (identify contradictions within the evidence set)
 ↓
Missing Evidence Review
 (identify gaps relative to what should exist)
 ↓
Traceability Review
 (confirm source references and dates for each item)
 ↓
Documentation Review
 (confirm each item is described with sufficient context)
 ↓
User Verification Review
 (identify unverified items flagged for confirmation)
 ↓
Overall Evidence Quality
 (descriptive assessment: strong / adequate / incomplete / weak / outdated / conflicting)
```

Each step produces a descriptive output. No step produces a numeric score. No step generates recommendations. Each step feeds its output into the next.

**Overall Evidence Quality** is the synthesis: the quality level that best describes the evidence set as a whole. When the set contains items of mixed quality, the overall level is determined by the most significant weakness present, not by averaging.

---

## Examples

### Example 1 — Strong evidence

```
Three recent annual reports (current, primary, traceable)
+ earnings call transcript (current, primary, traceable)
+ user research notes referencing both (recent, secondary, attributed)
+ company facts confirmed by user last week

→ Strong evidence
```

Rationale: Multiple primary sources, all current, all traceable, corroborated across sources, user-verified.

---

### Example 2 — Weak evidence

```
Old blog article from three years ago (stale, secondary, unattributed)
+ user memory note ("I think revenue was growing") (no source, no date)
+ no company facts
+ no earnings history

→ Weak evidence
```

Rationale: No primary sources, no traceability, stale or unknown freshness, no corroboration.

---

### Example 3 — Conflicting evidence

```
Recent company earnings release states operating margin improved to 22%
+
Older user research note states "margins are declining, around 18%"
(Note was written 8 months ago before the latest earnings)

→ Conflicting evidence (temporal conflict — supersession likely but not confirmed)
```

Rationale: Two sources make different claims about the same dimension. The conflict may be temporal (the older note predates the improvement), but Atlas does not silently resolve it. The conflict is surfaced, the temporal relationship is noted, and the user is asked to confirm whether the older note should be superseded.

---

### Example 4 — Incomplete evidence

```
User has company facts (name, ticker, sector)
+ one research note with open questions but no conclusions
+ no earnings data
+ no financial history
+ watchlist item added six months ago with no updates

→ Incomplete evidence
```

Rationale: Sufficient structure exists, but key financial evidence is absent. Scenario ranges would be very wide. Follow-up questions dominate the weekly review output.

---

### Example 5 — Outdated evidence

```
Strong research notes and company facts — but all dated 18 months ago
+ Last earnings report in evidence set is from 18 months ago
+ User has not reviewed or confirmed any item since then
+ Three product launches and one earnings restatement have occurred since

→ Outdated evidence
```

Rationale: Evidence quality was strong when assembled. Freshness has degraded for every item. Events since the last review may have materially changed the picture.

---

## Downstream Behaviour

Evidence Quality Review produces outputs that influence — but do not determine — how later stages behave.

### Evidence Quality influences:

- **Uncertainty visibility** — lower quality evidence requires wider uncertainty disclosure at every downstream stage
- **Scenario width** — incomplete or weak evidence produces wider value scenario ranges; strong evidence allows narrower ranges
- **Follow-up questions** — evidence gaps and conflicts generate specific, traceable follow-up questions in Weekly Review
- **Reasons to wait** — low evidence quality is a primary reason to wait before acting
- **Revision prompts** — outdated evidence triggers a specific prompt to refresh or re-verify

### Evidence Quality must never:

- Trigger a buy recommendation
- Trigger a sell recommendation
- Generate execution advice
- Produce urgency framing ("you must act before evidence expires")
- Be presented as a proxy for investment quality
- Be used to produce a numeric rating of an investment

---

## Cross-Cutting Principles

### Evidence quality is independent of investment attractiveness
A company with weak evidence may be an extraordinary opportunity or a complete failure — the evidence quality alone does not tell you which. Evidence quality tells you how much you know, not whether the company is good.

### Incomplete evidence is acceptable
An incomplete evidence set is a valid and informative input. It produces accurate uncertainty. It is better to know that evidence is incomplete than to fill gaps with speculation.

### Conflicting evidence must remain visible
Atlas never silently resolves conflicts. A conflict in the evidence set is preserved and surfaced at every downstream stage until the user explicitly resolves it. Hiding a conflict would create false confidence.

### Uncertainty must never be hidden
If the evidence quality is low, the uncertainty it produces is high. That uncertainty is displayed — not smoothed away, not replaced with a middle estimate, not discarded.

### Stronger evidence narrows uncertainty, not guarantees outcomes
Even with strong evidence, the future is uncertain. Strong evidence allows Atlas to present narrower scenario ranges. It does not allow Atlas to present single-point predictions or guaranteed outcomes.

### Evidence quality may change over time
Evidence that was current becomes stale. Evidence that was incomplete becomes adequate when new items are added. Evidence quality is reassessed at every review cycle.

### Revisions preserve history
When evidence quality changes — because new items were added, old items became stale, or conflicts were resolved — the prior quality assessment is preserved in the revision history. The direction and reason for the change are recorded.

### Evidence quality applies to the set, not the conclusion
Evidence Quality Review assesses the evidence set. It does not assess whether the investment thesis is correct. A high-quality evidence set about a poor business is still high-quality evidence.

---

## Future Extension Points

When new evidence sources become available, they enter the Evidence Assembly stage and are subject to the same Evidence Quality Review without changing the review architecture.

| Future Source | Freshness impact | Source quality | Traceability |
|---|---|---|---|
| SEC filings | High (official quarterly cadence) | Primary | Fully traceable (EDGAR reference) |
| Earnings transcripts | High (quarterly) | Primary | Fully traceable (date, company, call) |
| Annual reports | Medium (annual) | Primary | Fully traceable |
| Broker imports | High (position data is near-real-time) | Primary | Traceable (broker source) |
| Market data | Very high (daily or intraday) | Primary | Traceable (date, source) |
| AI summarisation | Depends on underlying source | Secondary (AI-derived) | Must carry AI label and underlying source reference |
| OCR documents | Depends on document age | Varies | Must carry document reference and date |

**Principle:** No future source bypasses Evidence Quality Review. Every new source is assessed on the same eight dimensions. AI-derived summaries are labelled as AI-derived and their underlying source quality is tracked separately from the AI summary quality.

---

## What This Document Is Not

- This is not a scoring model.
- This is not a weighting algorithm.
- This is not a recommendation framework.
- This is not a valuation system.
- This is not a forecast.
- This is not a database schema.

It is a definition of how Atlas assesses the trustworthiness, completeness, and currency of evidence before any assumption, risk, or scenario analysis is performed.

---

## Sprint 283 Target

**Define Assumption Review V1**

After Atlas knows what evidence exists and how strong that evidence is, the next logical step is to define how explicit and implicit assumptions are identified, documented, challenged, revised, and linked back to evidence before any risk or scenario analysis is performed. This makes Stage 6 of the Investment Review Pipeline concrete while preserving Atlas's deterministic, evidence-first philosophy.
