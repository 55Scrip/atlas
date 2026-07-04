# Input-First Workspace Onboarding

**Created:** 2026-07-04 (Sprint 267)  
**Status:** DEFINED — specification only. No implementation in this sprint.  
**Depends on:** [docs/NoAccountFirstValueOnboarding.md](NoAccountFirstValueOnboarding.md)

---

## Purpose

This document defines Atlas's input-first workspace onboarding model. It
specifies what the first screen should invite users to do, what input types
Atlas should accept, how input should be classified into a temporary workspace,
what cards that workspace should contain, and how the no-account flow
transitions to a saved account workspace.

This is a product specification. No UI, web app, backend service, database
schema, authentication, or input classifier is implemented here.

---

## Product Principle

**Atlas should start with the user's input, not with an empty dashboard or
a signup wall.**

The first product moment should be:

> Paste something investment-related and receive a structured Atlas workspace.

Atlas onboarding should not be dashboard-first. It should not be signup-first.
It should be input-first:

- paste portfolio
- paste watchlist
- paste research notes
- paste an order idea
- paste broker text
- paste a decision journal note
- ask an investment-process question

Input arrives first. Structure follows. Account creation follows value.

---

## Non-Goals

This sprint does not:

- implement UI, web app, or desktop app
- implement upload handling, file parsing, or image import
- implement OCR or screenshot parsing
- implement input classification logic
- implement the temporary workspace data model
- implement workspace cards or rendering
- implement persistence or saved workspaces
- implement account creation, authentication, or login
- implement backend services, APIs, or database schema
- implement broker import or live data integration
- add AI or LLM calls
- change CLI behaviour
- change runtime behaviour
- add new CLI commands

---

## First Screen

The first screen in any Atlas web or desktop implementation should present a
single input-first surface. No empty dashboard. No account wall. No tour.

**Suggested prompt:**

> Paste a portfolio, watchlist, research note, order idea, broker text, or
> investment question. Atlas will structure it into a temporary workspace.

**First screen properties:**

- Accepts free-form text as primary entry point
- Provides example inputs to reduce cold-start friction
- Does not require login, email, or account to begin
- Does not present a portfolio dashboard before any input exists
- Does not present a signup prompt as the first action

**Supporting actions on the first screen:**

- Load an example (pre-filled with a sample portfolio or watchlist)
- Learn more about what Atlas does (non-blocking)
- Sign in (available but not the primary call to action)

---

## Supported First Inputs

The following input types are intended to be accepted on the first screen.
Actual image upload, OCR, screenshot parsing, and broker import are future
implementation areas and are not part of this sprint.

| Input type | Description |
|------------|-------------|
| Portfolio snapshot | Holdings list with tickers, names, weights, or market values |
| Watchlist | Companies or ideas with status, reasons, and evidence gaps |
| Open order idea | A possible position change under consideration |
| Broker portfolio text | Raw copied text from a broker platform (treated as portfolio input) |
| Research notes | Markdown or free-text notes on one or more companies |
| Company facts | Qualitative company information (products, moat, risks) |
| Investment-process question | A question about a position, decision, or evidence gap |
| Decision journal note | A note about a prior research decision or follow-up trigger |
| News or external analysis snippet | A copied excerpt the user wants to reason about |
| Pasted table | A copied spreadsheet or CSV-like text block |
| CSV-like text | Comma- or tab-separated holdings data |
| Screenshot-derived text | Text manually transcribed or pasted from a screenshot |
| Mixed input | Multiple types in a single paste |

Atlas should be resilient to messy, mixed, or ambiguous input. When
classification confidence is low, Atlas should surface uncertainties and
missing fields rather than failing silently.

---

## Input Classification

When input is received, Atlas should classify it into one or more of the
following categories. This classification drives which workspace cards are
generated.

**Classification categories:**

| Category | Description |
|----------|-------------|
| `portfolio_input` | Holdings, weights, tickers, accounts |
| `watchlist_input` | Research candidates with status and evidence gaps |
| `order_review_input` | A possible position change under consideration |
| `research_note_input` | Notes on one or more companies |
| `company_facts_input` | Qualitative company data |
| `journal_note_input` | Decision journal entry |
| `news_or_external_analysis_input` | External excerpt being reviewed |
| `question_input` | Investment-process question |
| `mixed_input` | Two or more types detected in a single paste |
| `unknown_input` | Classification confidence too low to determine type |

**For each classification, the classifier should produce:**

- **confidence** — high / medium / low
- **detected tickers** — list of ticker symbols found in the input
- **detected dates** — list of dates found (ISO or free-form)
- **detected quantities or weights** — numeric values associated with positions
- **uncertainties** — fields that are ambiguous or unresolvable without more input
- **missing fields** — fields required for the associated workspace card type
  that were not found
- **suggested workspace cards** — the cards that should be generated given this
  classification

**Unknown or low-confidence input** should surface an Input Summary card with
the raw input, a confidence note, and a prompt asking the user to clarify or
provide more detail. It should not fail silently or produce an empty workspace.

The classifier is not implemented in this sprint. This section defines its
contract for future implementation.

---

## Temporary Workspace Model

A temporary workspace is a no-account, unsaved working area generated from
the user's first input. It exists to help the user inspect, structure, and
reason about the input before deciding whether to save or create an account.

**Temporary workspace properties:**

- no account required to create
- no broker connection required
- no persistence promised — workspace may be lost if the browser tab is closed
  (unless future implementation adds session-level local storage)
- user can inspect structured output across all generated cards
- user can copy or export result if future product supports it
- user can refine or add to the input and regenerate cards
- user can choose to save by creating an account
- account prompt appears only after cards are rendered and value is visible

**What a temporary workspace is not:**

- it is not a saved project
- it is not connected to a portfolio history
- it is not personalised beyond the input the user provided
- it is not a recommendation or a financial advice document

**Temporary data handling:**

- input data should be processed locally or discarded at session end unless
  the user explicitly saves
- no sensitive investment data should be silently retained beyond the session
- users should be informed that their workspace is temporary before they close
  or navigate away

---

## Workspace Cards

The following cards may appear in a temporary workspace, depending on input
classification. Cards appear only when the relevant input was detected with
sufficient confidence. Cards are information surfaces, not action instructions.

| Card | Appears when | Safe description |
|------|-------------|------------------|
| **1. Input Summary** | Always | The classified input type, detected tickers, detected dates, confidence level, and any identified uncertainties or missing fields |
| **2. Detected Holdings / Tickers** | Portfolio or watchlist input detected | A structured list of tickers and names identified from the input, with detected weights or values where available |
| **3. Portfolio Context** | Portfolio input | Holdings sorted by weight, sector exposure notes, concentration observations, cash position |
| **4. Watchlist Review** | Watchlist input | Per-item status, evidence gaps, open questions, and observations from the input |
| **5. Open Decisions** | Order idea or journal note input | The open question or decision framing from the input, without recommendation |
| **6. Evidence Gaps** | Any input with tickers | What is not yet known or documented for the detected tickers; missing company facts or financials |
| **7. Risks to Monitor** | Portfolio or research input | User-supplied risk factors from the input; structural observations from detected sector or concentration |
| **8. Reasons to Wait** | Any input | Evidence gaps, missing inputs, or structural reasons not to act on the input immediately |
| **9. Follow-Up Questions** | Research or watchlist input | Open questions from the input; questions that would resolve key evidence gaps |
| **10. Missing Inputs** | Any input | Fields that would improve the workspace — investor profile, decision journal, company facts, financials |
| **11. Snapshot Drafts** | Any structured input | One or more draft objects generated from the input, each pending user review and confirmation |
| **12. Weekly Review Preview** | Portfolio + watchlist detected | A provisional 10-section Weekly Review based on the detected portfolio and watchlist |
| **13. Save Workspace Prompt** | Always (shown after other cards) | A non-intrusive prompt to save the workspace by creating a free account |

Cards should never tell the user what to do with a position. They should
surface structure, gaps, and open questions — not decisions.

---

## Example Flows

The following flows describe intended future user sessions. These are product
direction, not current implementation.

### Flow 1 — Portfolio Paste

```
User pastes a portfolio list (tickers, names, approximate values or weights).

Atlas classifies as: portfolio_input (high confidence)
Detected tickers: ASML, XYL, NOVO, CASHEUR
Detected weights: approximate from market values

Atlas creates:
  1. Input Summary
  2. Detected Holdings / Tickers
  3. Portfolio Context (by weight, sector exposure, cash position)
  6. Evidence Gaps (company facts and financials not provided)
  7. Risks to Monitor (sector concentration if applicable)
  8. Reasons to Wait (evidence directories absent)
 10. Missing Inputs (investor profile, watchlist, decision journal not provided)
 12. Weekly Review Preview (partial — no watchlist; note displayed)
 13. Save Workspace Prompt

Account prompt: "Save this portfolio workspace to keep history and continue
later."
```

### Flow 2 — Watchlist and Research Notes

```
User pastes several tickers with notes on each, including evidence gaps
and open questions.

Atlas classifies as: mixed_input — watchlist_input + research_note_input
Detected tickers: ASML, XYL
Detected evidence gaps: from pasted text

Atlas creates:
  1. Input Summary
  2. Detected Holdings / Tickers
  4. Watchlist Review (status, evidence gaps, open questions per ticker)
  6. Evidence Gaps
  8. Reasons to Wait
  9. Follow-Up Questions
 11. Snapshot Drafts (one research_notes_snapshot draft per ticker, pending
     review)
 13. Save Workspace Prompt

Account prompt: "Save this research workspace to continue tracking evidence
gaps and questions."
```

### Flow 3 — Open Order Idea

```
User pastes a description of a position change they are considering,
with a ticker and reasoning.

Atlas classifies as: order_review_input (medium confidence)
Detected tickers: XYL
Uncertainties: position size not provided; no existing portfolio context

Atlas creates:
  1. Input Summary (with confidence note and uncertainties)
  2. Detected Holdings / Tickers
  5. Open Decisions (framing the decision without recommendation)
  6. Evidence Gaps (what is not yet documented for XYL)
  8. Reasons to Wait (open evidence gaps; no investor profile provided)
  9. Follow-Up Questions
 10. Missing Inputs (no portfolio or investor profile provided)
 11. Snapshot Drafts (one order_review draft pending user review)
 13. Save Workspace Prompt

Account prompt: "Create an account to save this open decision and track it
in your decision journal."
```

All three flows end with structured output before any account prompt.
No flow blocks the user on account creation before cards are visible.

---

## No-Account Flow

```
1. User arrives at Atlas (web or desktop).
2. Atlas shows input-first surface — no dashboard, no signup wall.
3. User provides input: portfolio text, watchlist, notes, or question.
4. Atlas classifies input (type, tickers, dates, quantities, confidence).
5. Atlas creates temporary workspace.
6. Atlas renders workspace cards based on classification.
7. User inspects cards, refines input, or adds more context.
8. Account prompt appears only when the user:
   - clicks Save
   - attempts to continue later
   - wants cross-device access
   - wants to collaborate or share
9. User may also close without saving — temporary workspace is not retained.
```

At no point in steps 1–7 is account creation required.

---

## Save / Account Handoff

Account creation should be introduced as persistence, not as a gate to
basic value.

**When to introduce account creation:**

| Trigger | Suggested copy |
|---------|---------------|
| User clicks Save | "Save this workspace. Create a free account to keep your history." |
| User wants to continue later | "Create an account to pick this up later on any device." |
| User wants cross-device access | "Sign in to access this workspace on another device." |
| User wants to share or collaborate | "Create an account to share this workspace." |
| Inactivity timeout approaching (future) | "Your session will end soon. Save your workspace to keep it." |

**What saving unlocks:**

- persistent workspace with named portfolio, watchlist, and notes
- decision journal history
- cross-device access
- future collaboration features

**What saving does not add:**

- live data
- broker connection
- AI analysis
- investment recommendations

**Account creation framing:** the account is a persistence layer, not an
intelligence layer. The structured review was already produced without it.

---

## Privacy and Trust Boundaries

- No-account mode should minimise data collection before account creation.
- Temporary-session behaviour must be explicit: users should understand
  their workspace is not saved until they create an account.
- Input data (portfolio, watchlist, notes) should be processed locally or
  in a transient server-side session — not stored permanently without consent.
- Users should be informed before sensitive financial data leaves their device
  if future web processing is introduced.
- Broker connection should not be required for first value.
- Account creation should be framed as persistence, not access to basic output.
- No email, phone number, or personal identity should be required before
  the first workspace is generated.
- Safe-language guardrails apply to all workspace card output regardless of
  account status. Atlas does not provide investment recommendations in any
  account state.

---

## Relationship to Existing Atlas Workflows

Input-first workspace onboarding connects directly to existing Atlas
components. Conversion from pasted input to structured Atlas objects is a
future implementation concern; this section describes the intended mapping.

**Snapshot Drafts:**
- Portfolio text, watchlist text, research notes, order ideas, and company
  facts pasted into the first screen may each become one or more Snapshot
  Draft objects pending user review and confirmation.
- The existing Snapshot Draft schema (`snapshot_type`, `confirmation_status`,
  `extracted_fields`, `uncertainties`) is the natural target for input
  classification output.
- No conversion is implemented in this sprint.

**Weekly Review:**
- When portfolio and watchlist inputs are both detected with sufficient
  confidence, a temporary Weekly Review Preview card may be generated.
- The existing `atlas weekly-review` renderer is the target for this card.
- The first workspace is a superset of a single Weekly Review run: it may
  contain sections from the review alongside Snapshot Drafts and other cards.

**Decision Journal:**
- Open order ideas and journal notes pasted in the first session may become
  future decision journal entries only if the user saves the workspace.
- In temporary mode, they appear as Open Decisions cards only.

**Research Notes:**
- Pasted research text may become a temporary `research_notes_snapshot` draft,
  pending review and confirmation by the user before export to `notes.md`.
- The existing `atlas snapshot export-research-notes` workflow is the
  downstream target.

**Company Facts:**
- Pasted qualitative company data may become a temporary
  `company_facts_snapshot` draft, pending user review.
- The existing `atlas snapshot export-company-facts` workflow is the
  downstream target.

---

## Future Implementation Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Input-first workspace onboarding specified | **Complete — Sprint 267** |
| 1 | CLI/local text-to-workspace planning prototype | Future |
| 2 | Web no-account input surface | Future |
| 3 | Input classification layer (type, tickers, confidence) | Future |
| 4 | Temporary workspace preview with cards | Future |
| 5 | Save / account handoff | Future |
| 6 | Persistent saved workspaces behind account | Future |
| 7 | Collaboration and cross-device behind account | Future |

Phase 0 is complete. The CLI (Sprint 266, Phase 1 of
`NoAccountFirstValueOnboarding.md`) already demonstrates no-account first
value at the command line. Web phases follow.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Unclear temporary data retention | Explicit "not saved" indicator throughout temporary session |
| Users expecting saved history without account | Clear temporary-mode messaging before and after input |
| Pasted sensitive financial data in web context | Privacy notice before first input; local-or-transient processing by default |
| Poor classification of messy or ambiguous input | Low-confidence path: Input Summary with uncertainties, not silent failure |
| Onboarding feels like investment advice | Safe-language guardrails on all card output; disclaimer on every workspace |
| Abuse or spam if public web entry has no account wall | Rate limits implemented at web entry point when Phase 2 is built |
| User closes tab without saving | Warn before close if workspace has unsaved content |
| Order idea cards misread as recommendations | Cards frame decisions as open questions, not action instructions |

---

## Open Questions

1. **Session persistence in Phase 4:** Should temporary workspaces persist
   across browser refreshes (using local storage) before account creation,
   or only within a single tab session? (Preferred: local-storage-backed
   single-device persistence, with account required for cross-device.)

2. **Classification confidence threshold:** What confidence level is required
   to generate a full workspace card vs. an uncertainty-only Input Summary
   card? (Suggested: high → full card; medium → card with caveats; low →
   Input Summary only.)

3. **Mixed-input handling:** When a paste contains both portfolio and
   watchlist data, should Atlas generate one merged workspace or ask the
   user to confirm the split? (Preferred: generate merged workspace with
   Input Summary noting both detected types.)

4. **Example input quality:** What pre-filled example should ship with the
   web first screen to reduce cold-start friction for users with nothing
   ready to paste? (Suggested: a small fictional portfolio with two or three
   tickers, a watchlist with one evidence-gap item, and a brief research note.)

5. **Order review card language:** The Open Decisions card for an order idea
   must avoid recommendation framing. What exact copy governs its output?
   (Suggested: "Open Decision: [user's framing]. Evidence gaps: [...]. Reasons
   to wait: [...]." No buy/sell language, no urgency, no certainty.)

---

## Related Documents

- [docs/NoAccountFirstValueOnboarding.md](NoAccountFirstValueOnboarding.md) — no-account first-value principle
- [docs/AtlasV1OperatingMode.md](AtlasV1OperatingMode.md) — v1 product boundary
- [docs/AtlasWeeklyReviewUsageGuide.md](AtlasWeeklyReviewUsageGuide.md) — Weekly Review user guide
- [docs/AtlasSnapshotInputWorkflow.md](AtlasSnapshotInputWorkflow.md) — Snapshot Draft workflow
- [docs/SwedishSafeLanguageGuardrails.md](SwedishSafeLanguageGuardrails.md) — safe-language guardrails
- [docs/Architecture.md](Architecture.md) — system architecture overview

---

## Recommended Next Sprint

**Sprint 268 — Define Temporary Workspace Data Model**

After specifying input-first onboarding, Atlas should define the temporary
workspace data model: the data structure that captures input summary,
classification output, detected entities, workspace card list, uncertainties,
confidence levels, and save/account handoff state — without implementing
persistence.

This model is the bridge between the input classification layer (Sprint 267,
Input Classification section) and the rendering layer (workspace cards). It
must be defined before either can be implemented.
