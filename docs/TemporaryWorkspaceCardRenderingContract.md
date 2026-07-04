# Temporary Workspace Card Rendering Contract

**Created:** 2026-07-04 (Sprint 269)
**Status:** DEFINED — specification only. No implementation in this sprint.
**Depends on:** [docs/TemporaryWorkspaceDataModel.md](TemporaryWorkspaceDataModel.md)
**Depends on:** [docs/InputFirstWorkspaceOnboarding.md](InputFirstWorkspaceOnboarding.md)

---

## Purpose

This document defines the rendering contract for temporary workspace cards.
It specifies how each card type maps to a rendered structure, what fields
are required or optional, how uncertainties and missing inputs appear, how
safety boundaries constrain card copy, and how user-provided content must
pass through unchanged.

This is a product architecture and UX specification. No renderer, dataclass,
schema, UI, CLI command, classifier, entity extractor, or persistence layer
is implemented here.

---

## Non-Goals

This sprint does not:

- implement a card renderer in Python or any other language
- implement dataclasses or typed models for the rendering layer
- implement JSON Schema or formal schema validation
- implement a classifier or entity extractor
- implement workspace generation or card assembly
- implement a temporary workspace CLI command
- implement persistence, saved workspaces, or workspace history
- implement account creation, authentication, login, or signup
- implement backend services, REST APIs, or database schema
- implement broker import, live data, or external API calls
- add AI or LLM calls
- add OCR or screenshot parsing
- change CLI behavior
- change runtime behavior
- change existing schemas, enum values, or warning codes

---

## Rendering Principles

All temporary workspace cards follow these principles:

1. **Cards surface structure, gaps, and questions.** They do not tell the
   user what to do.
2. **Cards do not create investment recommendations.** No card may instruct
   the user to buy, sell, enter, or exit a position.
3. **Cards preserve user-provided content.** Pasted text, holdings, notes,
   reasons, and descriptions pass through without rewriting.
4. **Cards preserve canonical internal values.** Schema values and identifiers
   remain English regardless of display language.
5. **Cards make uncertainty visible.** Uncertainty is shown, not hidden behind
   confident phrasing.
6. **Cards make missing inputs visible.** Missing fields are listed, not
   silently omitted.
7. **Cards show source references when available.** Sources are preserved
   exactly as provided; they are not fabricated.
8. **Cards can be discarded unless explicitly saved later.** No card implies
   persistence.
9. **Cards acknowledge the workspace is temporary.** Language should not
   suggest the workspace is a saved record.

---

## Shared Card Layout

Every card, regardless of type, renders into this common structure:

```json
{
  "title": "Evidence Gaps",
  "status_label": "Needs More Evidence",
  "summary": "One-sentence description of what this card contains.",
  "items": [],
  "uncertainties": [],
  "missing_fields": [],
  "source_references": [],
  "next_prompt": null
}
```

| Field | Required | Description |
|---|---|---|
| `title` | Yes | Display title for this card (may be localized in future) |
| `status_label` | Yes | Human-readable status (see Card Status Display) |
| `summary` | Yes | One-sentence description of the card's content |
| `items` | Yes (may be empty list) | Card-type-specific list of rendered items |
| `uncertainties` | Yes (may be empty list) | Uncertainty items for this card |
| `missing_fields` | Yes (may be empty list) | Missing field notices for this card |
| `source_references` | Yes (may be empty list) | Source references, if available |
| `next_prompt` | No | Optional user-confirmation question |

`items` structure varies by card type. All other fields follow the shared
shape defined here.

---

## Card Status Display

Each card carries a `status` value from the data model. The rendering layer
maps it to a human-readable label.

| Status (canonical) | Display label |
|---|---|
| `ready_for_review` | Ready for Review |
| `needs_more_evidence` | Needs More Evidence |
| `missing_required_input` | Missing Required Input |
| `user_confirmation_needed` | User Confirmation Needed |
| `not_applicable` | Not Applicable |
| `no_action_warranted` | No Action Warranted |
| `decision_deferred` | Decision Deferred |

**Rules:**

- The canonical status value (e.g. `needs_more_evidence`) is the internal
  model value. The display label is what the user sees.
- Display labels must not use urgency language ("Urgent", "Critical",
  "Must Act").
- Display labels must not use recommendation language ("Buy Signal",
  "Action Required", "Execute").
- If a future localization layer is introduced, display labels may be
  translated. The canonical status value must remain English.
- Cards with `not_applicable` status may be omitted from rendering or shown
  with a minimal collapsed state.

---

## Uncertainty Display

When a card has associated uncertainties, each is rendered as a notice
alongside the card's items.

**Uncertainty display structure:**

```json
{
  "severity": "low",
  "message": "No currency detected. Holdings may be in mixed currencies.",
  "confirmation_prompt": "Are all holdings denominated in the same currency?"
}
```

**Display rules:**

- Always show the uncertainty message. Do not hide it.
- Show severity as a visual indicator (low / medium / high / blocking) without
  urgency framing.
- Show `confirmation_prompt` as an optional question the user can answer.
- Do not assert confidence where uncertainty exists.
- Preferred safe uncertainty phrasing:
  - "Needs user confirmation"
  - "Unclear from provided input"
  - "Missing supporting detail"
  - "Assumption to recheck"

**Severity display guidance:**

| Severity | Guidance |
|---|---|
| `low` | Show inline with items; no special visual weight |
| `medium` | Show as a notice below items |
| `high` | Show prominently; consider a separate notice block |
| `blocking` | Show at top of card; items may be partially suppressed |

---

## Missing Field Display

When a card has associated missing fields, each is rendered as a notice
indicating what is absent and why it matters.

**Missing field display structure:**

```json
{
  "field_name": "investor_profile",
  "reason": "No profile detected. Weekly Review quality is limited without a profile.",
  "optional_or_required": "required_for_review_quality",
  "display_label": "Review Quality Limitation"
}
```

**Display label mapping:**

| `optional_or_required` (canonical) | Display label |
|---|---|
| `optional` | Optional Input Missing |
| `required_for_export` | Required for Export |
| `required_for_save` | Required for Save |
| `required_for_review_quality` | Review Quality Limitation |

**Display rules:**

- List missing fields without implying the user must act immediately.
- Do not use urgency language ("You must provide", "Required before
  continuing").
- Do not block card display because of missing optional inputs.
- Safe phrasing: "This input would improve the quality of this card."
- Do not fabricate default values for missing fields.

---

## Source Reference Display

When a card has associated source references, they are shown to trace where
card content came from.

**Source reference display structure:**

```json
{
  "source_id": "src_001",
  "source_description": "Pasted broker portfolio text",
  "source_span": "ASML 12%, NOVO B 18%"
}
```

**Display rules:**

- Show source references when available; omit the section if `source_references`
  is empty.
- Preserve user-provided source descriptions exactly. Do not rewrite them.
- Do not fabricate sources not present in the input.
- If source is unknown, label it "Source unknown" rather than asserting a
  fabricated origin.
- `source_span` is shown as a brief excerpt to help the user trace an entity
  back to their original text.

---

## User-Provided Content Handling

User-provided content must pass through the rendering layer unchanged.

**Content that must pass through:**

- Pasted portfolio or holdings text
- Pasted watchlist reasons
- Pasted research note text
- Pasted journal notes
- Pasted source descriptions
- Pasted company facts values
- File paths or filenames the user referenced
- Any free-text the user submitted as input

**Rules:**

- Do not paraphrase, summarize, or rewrite user-provided text in the rendering
  layer. Summarization belongs in the classification layer if it is ever
  implemented, and must be clearly labeled as a generated summary.
- Do not correct spelling, grammar, or formatting in user-provided fields.
- User-provided content that appears in `items` must be clearly attributable
  to user input (e.g. via `source_references`).
- Do not add editorial framing ("The user believes...", "This suggests...").

---

## Canonical Values

Internal model values remain canonical English in the rendering layer and
must not be translated, aliased, or overloaded.

**Values that must remain canonical English:**

| Value type | Examples |
|---|---|
| `card_type` | `evidence_gaps`, `snapshot_drafts`, `save_workspace_prompt` |
| `status` | `ready_for_review`, `needs_more_evidence` |
| Classification categories | `portfolio_input`, `unknown_input` |
| `entity_type` | `ticker`, `holding`, `open_decision` |
| `optional_or_required` | `optional`, `required_for_export` |
| `prompt_reason` | `save_workspace`, `continue_later` |
| `prompt_timing` | `after_first_value`, `on_explicit_request` |
| Safety boundary keys | `no_recommendations`, `user_judgment_required` |
| Snapshot types | `portfolio_snapshot`, `research_notes_snapshot` |
| Warning codes | existing Atlas warning codes |
| Confidence field | numeric 0.0–1.0; not a label |

**Display labels** (e.g. `status_label`, `title`, `display_label`) are
presentation values and may be localized in a future phase following the
existing Atlas locale pattern.

---

## Safety Copy Rules

All card copy must conform to Atlas's safety language boundary.

**Cards must avoid:**

- Direct recommendation language: "buy", "sell", "invest", "divest", "add
  to portfolio", "remove from portfolio"
- Transaction or execution instruction: "place the order", "execute",
  "enter the trade", "exit the position"
- Urgency language: "urgent", "immediately", "must act now", "critical
  action required", "do not delay"
- Certainty or promise language: "guaranteed", "certain to", "will
  outperform", "safe investment"
- Price-target framing: "target price", "price target", "fair value estimate"
- Outperformance prediction: "expected to outperform", "strong buy",
  "outperform the market"
- Personalized financial advice framing: "you should", "we recommend",
  "our advice is", "based on your situation"

**Safe alternatives for card copy:**

| Unsafe phrasing | Safe alternative |
|---|---|
| "You should buy X" | "Open decision detected for X" |
| "Strong buy signal" | "Reason to revisit this position" |
| "Act immediately" | "Reason to Wait" |
| "Guaranteed returns" | (not used) |
| "Price target: $X" | (not used) |
| "Recommended action" | "Question to Revisit" or "Follow-Up Question" |
| "Risk-free opportunity" | (not used) |
| "Execute the trade" | "Decision Deferred" |

**User judgment is always required.** Cards surface structure, gaps, and
questions. They do not replace user judgment.

---

## Card Rendering Contracts

### `input_summary`

**Purpose:** Summarize what the user provided and what Atlas detected from it.

**Required fields:** `title`, `status_label`, `summary`

**Optional fields:** `items` (detected input types), `uncertainties`,
`source_references`

**Display sections:**
1. Summary sentence: what was submitted and what type was detected
2. Item list: detected input types with confidence if available
3. Uncertainty notices (if any)

**Allowed statuses:** `ready_for_review`, `user_confirmation_needed`

**Uncertainty handling:** Show any classification uncertainty prominently.
If confidence is below threshold, show "Classification unclear — please
confirm input type."

**Missing field handling:** Not applicable for `input_summary`.

**Source reference handling:** Show the raw preview or source description
so the user can confirm Atlas detected the right thing.

**Safety notes:** Must not infer intent beyond what the input contains.
Must not assert the user intends to act on any detected entity.

---

### `detected_holdings`

**Purpose:** Show holdings detected from a portfolio input, with weights and
any confidence caveats.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `source_references`

**Display sections:**
1. Summary sentence: how many holdings detected
2. Item list: ticker / weight / confidence per holding
3. Uncertainty notices (e.g. mixed currencies, ambiguous tickers)
4. Source reference: excerpt from user input

**Item structure:**
```json
{"ticker": "ASML", "weight": "12%", "confidence": 0.97, "source_span": "ASML 12%"}
```

**Allowed statuses:** `ready_for_review`, `user_confirmation_needed`,
`needs_more_evidence`

**Uncertainty handling:** Show per-holding uncertainty if extraction
confidence is below threshold. Ask user to confirm ambiguous tickers.

**Missing field handling:** If currency is absent, show "Optional Input
Missing: currency." Do not assume a currency.

**Source reference handling:** Show the input span from which each holding
was extracted. Preserve ticker symbols exactly as written by the user.

**Safety notes:** Must not imply portfolio is optimized, diversified, or
suitable. Must not suggest adding or removing any holding.

---

### `detected_tickers`

**Purpose:** Show tickers detected without a full holding context (e.g. from
a watchlist or research note).

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `source_references`

**Display sections:**
1. Summary sentence: how many tickers detected
2. Item list: ticker / detection context / confidence
3. Uncertainty notices

**Item structure:**
```json
{"ticker": "NOVO B", "context": "watchlist_item", "confidence": 0.95}
```

**Allowed statuses:** `ready_for_review`, `user_confirmation_needed`

**Uncertainty handling:** Flag ambiguous ticker symbols (e.g. "B" could be
multiple companies). Ask user to confirm.

**Missing field handling:** Not applicable.

**Source reference handling:** Show source span for each ticker.

**Safety notes:** Must not assert that any detected ticker is a holding or a
recommendation. Must preserve ticker symbols exactly.

---

### `portfolio_context`

**Purpose:** Describe the structural context of the detected portfolio:
concentration, currency exposure, date context.

**Required fields:** `title`, `status_label`, `summary`

**Optional fields:** `items`, `uncertainties`, `missing_fields`

**Display sections:**
1. Summary sentence: top holdings, total detected weight
2. Context items: concentration (top N by weight), currency (if detected),
   date context (if detected)
3. Uncertainty notices
4. Missing field notices (e.g. no currency, no date)

**Allowed statuses:** `ready_for_review`, `needs_more_evidence`,
`user_confirmation_needed`

**Uncertainty handling:** Show currency and date uncertainties prominently.
These affect downstream card quality.

**Missing field handling:** If currency is absent, show "Optional Input
Missing: currency. Portfolio weights may be in mixed currencies."

**Source reference handling:** Not typically shown unless a specific source
was referenced.

**Safety notes:** Must not describe concentration as good or bad. Must not
suggest diversification changes. Must not imply suitability for any investor.

---

### `watchlist_review`

**Purpose:** Show watchlist items detected from the input, with any
user-provided reasons or open questions.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `missing_fields`, `source_references`

**Display sections:**
1. Summary sentence: how many watchlist items detected
2. Item list: ticker / reason (user-provided) / open questions (if any)
3. Uncertainty notices
4. Missing field notices

**Item structure:**
```json
{
  "ticker": "LVMH",
  "reason": "Monitoring for luxury sector rotation",
  "open_questions": ["Q2 earnings not yet reviewed"]
}
```

**Allowed statuses:** `ready_for_review`, `needs_more_evidence`,
`user_confirmation_needed`

**Uncertainty handling:** Flag tickers with no reason provided.

**Missing field handling:** If no reason is provided for a watchlist item,
show "Optional Input Missing: watchlist reason for [ticker]."

**Source reference handling:** Preserve user-provided watchlist reasons
exactly. Do not rewrite or editorialize.

**Safety notes:** Must not suggest acting on any watchlist item. Must
preserve user-provided reasons without rewriting.

---

### `open_decisions`

**Purpose:** Show unresolved investment decisions detected in the input.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `missing_fields`, `source_references`

**Display sections:**
1. Summary sentence: how many open decisions detected
2. Item list: ticker / decision description / stated reason (if present)
3. Uncertainty notices
4. Missing field notices (e.g. no rationale provided)

**Item structure:**
```json
{
  "ticker": "MSFT",
  "description": "Considering reducing weight from 10% to 7%",
  "rationale": "Valuation concerns noted in journal",
  "status_label": "Decision Deferred"
}
```

**Allowed statuses:** `ready_for_review`, `needs_more_evidence`,
`decision_deferred`, `user_confirmation_needed`

**Uncertainty handling:** Flag decisions with no stated rationale.

**Missing field handling:** If no rationale is present, show "Review Quality
Limitation: no rationale detected for this decision."

**Source reference handling:** Preserve source span from decision journal or
notes.

**Safety notes:** Must not instruct the user to execute any decision. Must
not imply a correct answer. Must not rewrite the decision description.

---

### `evidence_gaps`

**Purpose:** Surface holdings or tickers that lack research notes, company
facts, or other supporting evidence.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `missing_fields`, `source_references`

**Display sections:**
1. Summary sentence: how many holdings have evidence gaps
2. Item list: ticker / missing evidence types
3. Missing field notices

**Item structure:**
```json
{
  "ticker": "ASML",
  "missing": ["research_notes", "company_facts"],
  "display_labels": ["Research Notes Missing", "Company Facts Missing"]
}
```

**Allowed statuses:** `needs_more_evidence`, `ready_for_review`,
`missing_required_input`

**Uncertainty handling:** Not typically shown unless the gap itself is
uncertain.

**Missing field handling:** List each gap as a missing field notice. Show
`optional_or_required` display label so the user knows whether the gap
affects export, save, or review quality.

**Source reference handling:** Not applicable.

**Safety notes:** Must not imply evidence gaps make a position dangerous or
safe. Must not suggest the user must resolve gaps before acting.

---

### `risks_to_monitor`

**Purpose:** Surface risks identified from profile principles, holding
characteristics, or user-provided notes.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `source_references`

**Display sections:**
1. Summary sentence: how many risks detected
2. Item list: risk description / related ticker (if applicable) / source
3. Uncertainty notices (e.g. risk inference is uncertain)

**Item structure:**
```json
{
  "description": "Concentration in technology sector exceeds profile limit",
  "related_ticker": null,
  "source": "profile_principles"
}
```

**Allowed statuses:** `ready_for_review`, `needs_more_evidence`,
`user_confirmation_needed`

**Uncertainty handling:** If a risk is inferred rather than stated, show
"Assumption to recheck" and ask the user to confirm.

**Missing field handling:** If no investor profile is present, show "Review
Quality Limitation: no investor profile. Risk to monitor checks are limited."

**Source reference handling:** Show source (e.g. "profile_principles",
"user-provided notes") without fabricating risk sources.

**Safety notes:** Must not use urgency language. Must not imply a position
must be changed. Must not assert risk severity beyond what the data supports.

---

### `reasons_to_wait`

**Purpose:** Explain reasons not to rush a decision: aging notes, evidence
gaps, open questions, missing evidence.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `missing_fields`, `source_references`

**Display sections:**
1. Summary sentence: how many reasons to wait detected
2. Item list: reason description / related ticker or context (if applicable)

**Item structure:**
```json
{
  "reason": "Evidence gaps: 4 holdings lack research notes",
  "related_tickers": ["ASML", "NOVO B", "MSFT", "LVMH"]
}
```

**Allowed statuses:** `ready_for_review`, `needs_more_evidence`

**Uncertainty handling:** Not typically shown.

**Missing field handling:** Not applicable; missing inputs are the source of
reasons to wait, not an additional concern.

**Source reference handling:** Not typically shown.

**Safety notes:** Must not imply the user must wait indefinitely. Must not
use urgency language to describe waiting. Must not suggest any action
instead of waiting.

---

### `follow_up_questions`

**Purpose:** Pose clarifying questions Atlas could not answer from the
available input.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `source_references`

**Display sections:**
1. Summary sentence: how many follow-up questions
2. Item list: question / related ticker or context (if applicable)

**Item structure:**
```json
{
  "question": "What is the intended holding period for ASML?",
  "related_ticker": "ASML",
  "related_card_ids": ["card_gaps_01"]
}
```

**Allowed statuses:** `ready_for_review`, `user_confirmation_needed`

**Uncertainty handling:** Not typically shown; the card is itself an
expression of uncertainty.

**Missing field handling:** Not applicable.

**Source reference handling:** Not applicable.

**Safety notes:** Questions must be neutral and open-ended. Must not embed a
recommendation in the question ("Shouldn't you reduce your ASML weight?").
Must not assert that any particular answer is correct.

---

### `missing_inputs`

**Purpose:** List structured inputs that would improve workspace quality but
were not provided.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `source_references`

**Display sections:**
1. Summary sentence: how many missing inputs detected
2. Item list: field name / reason / optional_or_required display label

**Item structure:**
```json
{
  "field_name": "investor_profile",
  "reason": "No profile detected. Suitability checks are not available.",
  "display_label": "Review Quality Limitation"
}
```

**Allowed statuses:** `ready_for_review`, `missing_required_input`

**Uncertainty handling:** Not typically shown.

**Missing field handling:** This card is itself the missing field display.
No additional missing field notices needed.

**Source reference handling:** Not applicable.

**Safety notes:** Must not block workspace display for optional missing
inputs. Must not imply the user must provide all inputs before seeing value.

---

### `snapshot_drafts`

**Purpose:** Show Snapshot Draft candidates generated from the temporary
workspace, for user review and explicit confirmation.

**Required fields:** `title`, `status_label`, `summary`, `items`

**Optional fields:** `uncertainties`, `source_references`

**Display sections:**
1. Summary sentence: how many draft candidates are available
2. Item list: draft type / ticker / confirmation status / action prompt
3. Source reference: which part of the input generated this draft

**Item structure:**
```json
{
  "draft_type": "portfolio_snapshot",
  "ticker": null,
  "confirmation_status": "pending",
  "action_prompt": "Review this draft before confirming."
}
```

**Confirmation status values:**

| Value | Display label |
|---|---|
| `pending` | Awaiting Review |
| `confirmed` | Confirmed |
| `rejected` | Rejected |

**Allowed statuses:** `ready_for_review`, `user_confirmation_needed`,
`needs_more_evidence`

**Uncertainty handling:** Show any uncertainty in the draft generation (e.g.
ambiguous ticker mapping) before asking for confirmation.

**Missing field handling:** If a required field for a draft is missing, show
the missing field notice before displaying the draft action prompt.

**Source reference handling:** Show the input excerpt that generated the
draft candidate.

**Safety notes:** Must not auto-confirm any draft. The user must review and
explicitly confirm each draft. Must not imply confirmation is required to
see workspace value.

---

### `weekly_review_preview`

**Purpose:** Show a preview of a Weekly Review that would be generated from
the temporary structured inputs.

**Required fields:** `title`, `status_label`, `summary`

**Optional fields:** `items` (preview section list), `uncertainties`,
`missing_fields`

**Display sections:**
1. Summary sentence: what the preview covers and how complete it is
2. Preview section list: sections available with current inputs
3. Limitation notice: sections not available without additional inputs
4. Temporary workspace notice: "This preview does not reflect saved portfolio
   history."

**Allowed statuses:** `ready_for_review`, `needs_more_evidence`,
`missing_required_input`

**Uncertainty handling:** Show uncertainties that affect preview quality
(e.g. unconfirmed tickers, missing profile).

**Missing field handling:** Show which Weekly Review sections are not
available due to missing inputs. Use "Review Quality Limitation" label.

**Source reference handling:** Not typically shown.

**Safety notes:** Must label the preview as temporary. Must not imply saved
portfolio history. Must not imply the preview is a recommendation.

---

### `save_workspace_prompt`

**Purpose:** Invite the user to save the workspace and optionally create an
account, after first value has been delivered.

**Required fields:** `title`, `status_label`, `summary`

**Optional fields:** `items` (save options), `next_prompt`

**Display sections:**
1. Summary sentence: what saving enables
2. Save options: what the user can do (save locally, create account, discard)
3. Account framing: account enables persistence, history, collaboration —
   not access to first value

**Allowed statuses:** `ready_for_review`

**Uncertainty handling:** Not applicable.

**Missing field handling:** Not applicable.

**Source reference handling:** Not applicable.

**Safety notes:**
- Must appear after all value-delivering cards.
- Must not block access to any other card.
- Must not use urgency language ("Save now before it's gone").
- Account creation must be framed as enabling persistence, not as unlocking
  features the user has already seen.
- Must not use dark patterns: no countdown timers, no artificial scarcity,
  no blocked exit.
- Safe summary: "Save this workspace to continue later. No account required
  to review your results."

---

## Example Rendered Cards

### Example 1: Evidence Gaps Card

```json
{
  "title": "Evidence Gaps",
  "status_label": "Needs More Evidence",
  "summary": "4 holdings lack research notes. No company facts found.",
  "items": [
    {
      "ticker": "ASML",
      "missing": ["research_notes", "company_facts"],
      "display_labels": ["Research Notes Missing", "Company Facts Missing"]
    },
    {
      "ticker": "NOVO B",
      "missing": ["research_notes", "company_facts"],
      "display_labels": ["Research Notes Missing", "Company Facts Missing"]
    },
    {
      "ticker": "MSFT",
      "missing": ["research_notes"],
      "display_labels": ["Research Notes Missing"]
    },
    {
      "ticker": "LVMH",
      "missing": ["research_notes", "company_facts"],
      "display_labels": ["Research Notes Missing", "Company Facts Missing"]
    }
  ],
  "uncertainties": [],
  "missing_fields": [
    {
      "field_name": "research_notes",
      "reason": "Research notes support the quality of evidence checks.",
      "optional_or_required": "required_for_review_quality",
      "display_label": "Review Quality Limitation"
    }
  ],
  "source_references": [],
  "next_prompt": null
}
```

---

### Example 2: Snapshot Drafts Card

```json
{
  "title": "Snapshot Drafts",
  "status_label": "User Confirmation Needed",
  "summary": "1 snapshot draft candidate detected. Review before confirming.",
  "items": [
    {
      "draft_type": "portfolio_snapshot",
      "ticker": null,
      "confirmation_status": "pending",
      "action_prompt": "Review this draft before confirming."
    }
  ],
  "uncertainties": [
    {
      "severity": "low",
      "message": "Currency not confirmed. Draft may reflect mixed-currency weights.",
      "confirmation_prompt": "Are all holdings in the same currency?"
    }
  ],
  "missing_fields": [],
  "source_references": [
    {
      "source_id": "src_001",
      "source_description": "Pasted portfolio text",
      "source_span": "ASML 12%, NOVO B 18%, MSFT 10%, LVMH 8%, cash 52%"
    }
  ],
  "next_prompt": "Would you like to confirm this portfolio snapshot draft?"
}
```

---

### Example 3: Save Workspace Prompt Card

```json
{
  "title": "Save Workspace",
  "status_label": "Ready for Review",
  "summary": "Save this workspace to continue later. No account required to review your results.",
  "items": [
    {
      "option": "save_workspace",
      "label": "Save workspace",
      "description": "Keep your analysis and return to it later. Requires an account."
    },
    {
      "option": "continue_later",
      "label": "Save for later",
      "description": "Save a local copy without creating an account (future feature)."
    },
    {
      "option": "discard",
      "label": "Discard workspace",
      "description": "Close without saving. Your input will not be retained."
    }
  ],
  "uncertainties": [],
  "missing_fields": [],
  "source_references": [],
  "next_prompt": "Would you like to save this workspace?"
}
```

---

### Example 4: Portfolio Context Card

```json
{
  "title": "Portfolio Context",
  "status_label": "User Confirmation Needed",
  "summary": "4 holdings detected. Portfolio appears equity-heavy with 48% in 4 positions.",
  "items": [
    {"label": "Top holding", "value": "NOVO B at 18%"},
    {"label": "Total detected weight", "value": "48% (4 holdings)"},
    {"label": "Remaining", "value": "52% (labeled cash)"},
    {"label": "Currency", "value": "Not detected"}
  ],
  "uncertainties": [
    {
      "severity": "low",
      "message": "No currency detected. Holdings may be in mixed currencies.",
      "confirmation_prompt": "Are all holdings denominated in the same currency?"
    }
  ],
  "missing_fields": [
    {
      "field_name": "currency",
      "reason": "Currency affects portfolio weight comparability.",
      "optional_or_required": "optional",
      "display_label": "Optional Input Missing"
    }
  ],
  "source_references": [],
  "next_prompt": null
}
```

---

### Example 5: Open Decisions Card

```json
{
  "title": "Open Decisions",
  "status_label": "Decision Deferred",
  "summary": "1 open decision detected from provided notes.",
  "items": [
    {
      "ticker": "MSFT",
      "description": "Considering reducing weight from 10% to 7%",
      "rationale": "Valuation concerns noted in journal",
      "status_label": "Decision Deferred"
    }
  ],
  "uncertainties": [],
  "missing_fields": [
    {
      "field_name": "decision_rationale",
      "reason": "No formal rationale detected. Informal note used.",
      "optional_or_required": "required_for_review_quality",
      "display_label": "Review Quality Limitation"
    }
  ],
  "source_references": [
    {
      "source_id": "src_002",
      "source_description": "User-provided journal note",
      "source_span": "Considering reducing weight from 10% to 7%"
    }
  ],
  "next_prompt": null
}
```

---

## Validation Expectations

When a card rendering layer is implemented in a future phase, the following
properties should be validated:

| Expectation | Rule |
|---|---|
| Every card has `card_type`, `title`, `status`, `summary` | These fields must always be present |
| `card_type` is from known set | Must match Sprint 268 card type list |
| `status` is allowed for this card type | Each card type defines allowed statuses |
| User content marked or traceable | User-provided items link to `source_references` |
| Uncertainties retained | `uncertainties` array must not be silently emptied |
| Missing fields retained | `missing_fields` array must not be silently emptied |
| Source references preserved when available | `source_references` from data model passed through |
| `save_workspace_prompt` appears after first-value cards | Validated by card ordering |
| No card copy violates safety language rules | No recommendation, urgency, or execution phrasing |
| Canonical values remain English in schema | Display labels may differ; schema values must not |
| User-provided content unchanged | No paraphrase, correction, or rewrite in items |

---

## Future Implementation Phases

| Phase | Target | Status |
|---|---|---|
| Phase 0 | Define data model (Sprint 268) | Complete |
| Phase 1 | Define card rendering contract (this sprint) | Complete |
| Phase 2 | Prototype Python dataclasses for the model | Future (Sprint 270 candidate) |
| Phase 3 | Implement input classifier | Future |
| Phase 4 | Implement entity extraction | Future |
| Phase 5 | Implement card assembly from classification output | Future |
| Phase 6 | Implement card renderer using this contract | Future |
| Phase 7 | Implement temporary workspace CLI command | Future |
| Phase 8 | Implement save/account handoff | Future |

No implementation is performed in this sprint.

---

## Open Questions

1. **Partial rendering:** If the classifier has low confidence on a
   `mixed_input`, should the rendering layer show all possible card types
   at low quality, or show only the high-confidence cards? The current
   contract suggests showing high-confidence cards and surfacing a
   classification uncertainty in `input_summary`.

2. **Card collapse:** Should cards with `not_applicable` status be hidden
   entirely, shown collapsed, or shown with a minimal state? This affects
   UX but not the rendering contract schema.

3. **`next_prompt` interaction model:** The rendering contract defines
   `next_prompt` as an optional question. In a CLI implementation, this
   might be a terminal prompt. In a web app, it might be an inline input.
   The contract is intentionally implementation-agnostic.

4. **Localization boundary for items:** `items` content in user-provided
   fields must pass through unchanged. But Atlas-generated item text (e.g.
   "Research Notes Missing") may be localized in future. The boundary
   between user content and Atlas-generated content within `items` must
   be explicitly tracked by the implementation.

5. **Preview fidelity indicator:** The `weekly_review_preview` card shows a
   preview of a Weekly Review. Should it show a completeness percentage
   ("Preview quality: 40% — 3 of 8 sections available")? This would require
   a scoring model for preview completeness.

---

## Recommended Next Sprint

**Sprint 270: Prototype temporary workspace schema dataclasses**

After the temporary workspace data model (Sprint 268) and card rendering
contract (Sprint 269) are both specified, Atlas can safely introduce minimal
Python dataclasses for the model — without UI, persistence, accounts, or
classifier implementation.

The dataclass prototype should:

- Define `TemporaryWorkspace`, `SourceInput`, `ClassificationResult`,
  `DetectedEntity`, `Uncertainty`, `MissingField`, `WorkspaceCard`, and
  `SaveHandoff` as simple `@dataclass` or `TypedDict` structures
- Use only Python standard library (`dataclasses`, `typing`)
- Not import any provider, network, database, or UI library
- Not implement any classifier or rendering logic
- Pass `compileall` and existing tests without modification
- Add a minimal test for instantiating each dataclass with valid fields
