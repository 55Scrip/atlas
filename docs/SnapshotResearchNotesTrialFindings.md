# Snapshot Research Notes Trial Findings

**Sprint:** 226
**Date:** 2026-07-04
**Trial type:** End-to-end validation — confirmed draft → export → Weekly Review
**Status:** Complete — loop validated

---

## Trial Setup

Three confirmed research-note draft examples were created for tickers that appear
in the example and realistic Weekly Review bundles:

| Draft file | Ticker | Confirmation status |
|-----------|--------|---------------------|
| `research_notes_snapshot_confirmed.json` | ASML | confirmed |
| `research_notes_snapshot_xyl_confirmed.json` | XYL | confirmed |
| `research_notes_snapshot_novo_confirmed.json` | NOVO | confirmed |

Each draft contained thesis notes, evidence gaps, open questions, risks to monitor,
and reasons to wait. No private data. Content is placeholder/illustrative.

---

## Commands Run

```bash
# Stage 1 — Validation (all three drafts)
atlas snapshot validate examples/snapshot_drafts/research_notes_snapshot_confirmed.json
atlas snapshot validate examples/snapshot_drafts/research_notes_snapshot_xyl_confirmed.json
atlas snapshot validate examples/snapshot_drafts/research_notes_snapshot_novo_confirmed.json

# Stage 2 — Export (all three drafts to temp dir)
atlas snapshot export-research-notes \
  examples/snapshot_drafts/research_notes_snapshot_confirmed.json \
  --output-dir /tmp/atlas_research_notes_export

atlas snapshot export-research-notes \
  examples/snapshot_drafts/research_notes_snapshot_xyl_confirmed.json \
  --output-dir /tmp/atlas_research_notes_export

atlas snapshot export-research-notes \
  examples/snapshot_drafts/research_notes_snapshot_novo_confirmed.json \
  --output-dir /tmp/atlas_research_notes_export

# Stage 3a — Weekly Review (example bundle)
atlas weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --profile examples/weekly_review/investor_profile.json \
  --journal examples/weekly_review/decision_journal.json \
  --company-facts examples/weekly_review/company_facts \
  --financials examples/weekly_review/financials \
  --research-notes /tmp/atlas_research_notes_export \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review/scope_notes.md

# Stage 3b — Weekly Review (realistic bundle)
atlas weekly-review \
  --portfolio examples/weekly_review_realistic/portfolio.json \
  --watchlist examples/weekly_review_realistic/watchlist.json \
  --profile examples/weekly_review_realistic/investor_profile.json \
  --journal examples/weekly_review_realistic/decision_journal.json \
  --company-facts examples/weekly_review_realistic/company_facts \
  --financials examples/weekly_review_realistic/financials \
  --research-notes /tmp/atlas_research_notes_export \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review_realistic/scope_notes.md
```

---

## Stage 1 — Draft Validation Results

All three drafts validated cleanly. Exit 0 for each.

Example output (ASML):
```
Snapshot Draft Validation

Status: valid
Snapshot Type: research_notes_snapshot
Confidence: high
Confirmation Status: confirmed
Target Local File: my_review/research_notes/ASML/notes.md
Related Tickers: ASML
Uncertainties: none
Missing Required Fields: none
Source Reference: my_notes/asml_notes_2026.md
Notes: Confirmed after user review on 2026-01-05. ...

Safety Boundary:
  - Draft validation does not write to Atlas local input files.
```

**Assessment:**
- Confirmation status is clearly displayed. No ambiguity about which drafts are
  confirmed and which are not.
- Uncertainties and missing fields are explicitly listed (none in these drafts).
- Safety boundary is visible before any export step.
- Wording is clear. No confusing language.
- The validation step gives sufficient confidence to proceed to export.

---

## Stage 2 — Research Notes Export Results

All three drafts exported cleanly. Exit 0 for each.

**Files written:**
```
/tmp/atlas_research_notes_export/ASML/notes.md
/tmp/atlas_research_notes_export/XYL/notes.md
/tmp/atlas_research_notes_export/NOVO/notes.md
```

**Example export output:**
```
Research Notes Export

Status: written
Ticker: ASML
Output File: /tmp/atlas_research_notes_export/ASML/notes.md

Safety Boundary:
  - Only local research notes were written.
  - No portfolio, watchlist, journal, or company facts files were changed.
```

**Generated Markdown assessment (ASML):**
```markdown
# ASML Research Notes

## Thesis Notes
- ASML occupies a structural monopoly position in EUV lithography.
- Aftermarket and service revenue provides resilience in soft capex environments.

## Evidence Gaps
- Margin durability through a downcycle has not been reviewed recently.
- China revenue exposure needs updated context.
- Long-term service revenue contribution not modelled.

## Open Questions
- What assumptions about EUV demand durability should be rechecked?
- Which financial history quarters are most relevant for margin review?
- How does backlog composition change in a slower-growth environment?

## Risks to Monitor
- Export controls affecting China shipments.
- Customer capex cyclicality during semiconductor inventory corrections.
- Competitive dynamics if alternative EUV or DUV approaches emerge.

## Reason to Wait
- Evidence gaps on margin durability and China exposure should be resolved before
  any position decision.
- Pending review of most recent quarterly earnings commentary.

## Source
- Source description: User-written ASML research notes covering thesis, ...
- Draft ID: draft-research-asml-20260105-confirmed-001
- Source reference: my_notes/asml_notes_2026.md
```

**Assessment:**
- Export output is clear and human-readable.
- File path is displayed in full (wraps on narrow terminals for long paths —
  acceptable; real paths would be shorter).
- Safety boundary is explicitly stated and visible.
- Generated Markdown uses the correct headings that the Weekly Review parser
  recognizes: `## Evidence Gaps`, `## Open Questions`, `## Risks to Monitor`,
  `## Reason to Wait`.
- Sections are compact and not verbose.
- Source attribution (description, draft ID, source reference) is present and
  traceable.

---

## Stage 3 — Weekly Review Consumption

### Input Status Line

```
Research notes: 3 ticker(s) with local notes.
```

Detection confirmed. The loader picks up all three ticker notes directories.

### Section 8 — Missing Evidence

**What works well:**
- Each research-note evidence gap is clearly labeled `Evidence Gap [TICKER]
  (research notes):`, making source provenance visible.
- ASML research notes surfaced 3 specific, actionable gaps that would otherwise
  be absent from Section 8 entirely (ASML is a portfolio holding with no watchlist
  entry in the example bundle).
- In the realistic bundle, XYL research note gaps (Evoqua integration, backlog
  conversion, margin profile) are complementary to and distinct from the watchlist
  gaps (commodity cost cycles, valuation, portfolio overlap). They cover different
  aspects of the same stock.

**What feels unclear:**
- Nothing confusing about the format itself.

**What feels repetitive:**
- In the example bundle, NOVO watchlist gaps and NOVO research note gaps are nearly
  verbatim identical (three of three), because the example draft was deliberately
  designed to match the watchlist. In real usage, research notes and watchlist
  entries would diverge over time. This is a data quality observation, not a
  renderer bug.
- When the same ticker appears in both watchlist and research notes with similar
  gap wording, Section 8 grows. With 3 tickers and research notes, Section 8 ran
  to 18 lines in the example bundle and ~38 lines in the realistic bundle (which
  has 12 tickers without company facts).

**Whether notes improve specificity:**
- Yes, clearly — particularly for ASML (portfolio holding with no watchlist entry)
  and for XYL in the realistic bundle (research notes add distinct integration and
  backlog gaps not present in the watchlist).

**Whether output remains safe and calm:**
- Yes. No forbidden language. All phrasing is factual and non-directive.

**Grouping improvement needed:**
- Not urgent. The `(research notes)` label is sufficient provenance. Deduplication
  logic would add complexity without clear immediate benefit.

---

### Section 9 — Follow-Up Questions

**What works well:**
- Research note open questions appear in a named block: `[TICKER] Research notes
  — open questions:` followed by bullet list. This is readable and scannable.
- Research note risks appear as: `[TICKER] Risk to Monitor (research notes): ...`
  — well-formatted and clearly attributed.
- For ASML, the research note questions are the *only* questions for that ticker
  in this section (no watchlist entry), making them purely additive.
- NOVO research note questions (pipeline diversification, US pricing policy) add
  specificity not present in the watchlist.
- XYL research note questions (Evoqua timing, municipal budget impact) are
  distinct from watchlist questions (revenue mix, capital allocation, replacement
  demand).

**What feels unclear:**
- Nothing confusing. Both watchlist questions and research-note questions use
  similar formatting, which creates visual consistency.

**What feels repetitive:**
- Minimal. The research note questions were written to be distinct from watchlist
  questions, and they are.

**Grouping improvement needed:**
- No immediate change needed.

---

### Section 10 — Non-Actions / Reasons to Wait

**What works well:**
- Research note reasons to wait are the strongest signal from this section.
  They are specific, well-formed, and directly actionable as reading assignments.
- Format: `Reason to Wait [TICKER] (research notes): ...` — clear ticker and
  provenance.
- Example lines:
  - `Reason to Wait [ASML] (research notes): Evidence gaps on margin durability
    and China exposure should be resolved before any position decision.`
  - `Reason to Wait [NOVO] (research notes): US pricing policy risk is a known
    unknown — not yet assessed.`
  - `Reason to Wait [XYL] (research notes): Integration evidence from Evoqua not
    yet reviewed.`

**What feels unclear:**
- Nothing confusing. These are among the clearest lines in the section.

**What feels repetitive:**
- Not repetitive. Section 10 already has diverse reason types (watchlist decisions,
  evidence totals, company facts, financial history, principles, constraints).
  Research note reasons to wait are specific enough to stand out.

**Grouping improvement needed:**
- No change needed. Section 10 density is acceptable.

---

## File Mutation Safety

**Verified:**
- Export directory contained only:
  ```
  /tmp/atlas_research_notes_export/ASML/notes.md
  /tmp/atlas_research_notes_export/XYL/notes.md
  /tmp/atlas_research_notes_export/NOVO/notes.md
  ```
- Draft files were not modified (file sizes unchanged before and after export).
- Portfolio, watchlist, and journal files were not modified (MD5 checksums
  confirmed unchanged).
- No files were written outside the export output directory.

**Safety boundary confirmed.** The export path is fully contained to the
designated output directory.

---

## Product Judgment

### Does the loop feel complete?
Yes. The path from confirmed draft to Weekly Review is end-to-end and functional:
1. `atlas snapshot validate` gives clear confirmation-status visibility before
   export — no guessing about draft state.
2. `atlas snapshot export-research-notes` produces well-structured Markdown
   readable by the Weekly Review parser and by humans.
3. `atlas weekly-review --research-notes DIR` picks up all ticker notes
   automatically, surfaces them in Sections 8, 9, and 10 with clear provenance.

### Does the loop feel useful?
Yes — particularly for portfolio holdings that have no watchlist entry. ASML in
the example bundle received zero evidence coverage in Sections 8/9 without
research notes; with notes, it gained 3 evidence gaps, 3 open questions, 3 risks
to monitor, and 2 reasons to wait. That is a meaningful improvement in review
completeness.

### Does the loop feel worth extending?
Yes. The confirmation-boundary enforcement (type check, status check, ticker
validation) has been validated through multiple test scenarios and is robust.
The output format is stable and parseable. Extending to other draft types
(watchlist updates, company facts) would follow the same pattern.

### What is the smallest next improvement?
Before adding more conversion types, defining the confirmation workflow more
explicitly would prevent each new conversion path from reinventing its own user-
review boundary. A `snapshot draft confirmation planning` sprint would establish
consistent rules for how a draft moves from `draft` → `needs_user_review` →
`confirmed`, so every future `export-*` command relies on the same upstream state.

---

## Small Improvements Made

None. The trial confirmed the system works as intended. No trial-driven code
changes were necessary.

Two additional confirmed draft examples were created for trial coverage:
- `examples/snapshot_drafts/research_notes_snapshot_xyl_confirmed.json`
- `examples/snapshot_drafts/research_notes_snapshot_novo_confirmed.json`

---

## Remaining Implementation Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| Evidence gap semantic deduplication | Low | When watchlist and research notes cover the same topic with similar wording, Section 8 can list near-identical lines. The `(research notes)` label keeps provenance clear. Deduplication adds complexity before the benefit is proven in real usage. |
| Export CLI output path wrapping | Cosmetic | Long scratchpad paths wrap across lines in terminal. Real paths (`my_review/research_notes`) are shorter and display cleanly. |
| Confirmation workflow undefined | Medium | Drafts move from `draft` → `confirmed` by manual JSON edit. A formal confirmation UI/workflow step is not implemented. Sprint 227 target. |
| Only research_notes_snapshot is exportable | Intentional | Portfolio, watchlist, company facts conversions not yet implemented. |
| No OCR / image parsing | Intentional deferral | Not in scope for Atlas v1 track. |

---

## Language Guardrail Check

All output reviewed across:
- CLI validation output
- CLI export output
- Generated Markdown (`notes.md` files)
- Weekly Review Sections 8, 9, 10

**Result:** No forbidden language found. No recommendation, price-target, urgency,
or directional language in any output. All phrasing uses safe language from the
allowed set.

---

## Provider / Network Boundary

No new imports introduced. No provider, requests, urllib, httpx, or aiohttp imports
in any touched module. All output is derived from local files only.

---

## Recommended Sprint 227 Target

**Add snapshot draft confirmation planning.**

Before adding more conversion types (watchlist, company facts), Atlas should define
the confirmation workflow and safety rules consistently:
- How does a draft move from `draft` → `needs_user_review` → `confirmed`?
- What information must be reviewed before confirmation is allowed?
- How is the confirmation event recorded (field update, timestamp, journal entry)?
- Should a separate `atlas snapshot confirm` command be added?

This ensures every future `export-*` command follows the same upstream user-review
boundary without each conversion type inventing its own rules.

Alternative if confirmation planning feels too abstract: **Implement
draft-to-company-facts conversion** — the next safest conversion target after
research notes, since company facts files are simple JSON with a clear local schema.
