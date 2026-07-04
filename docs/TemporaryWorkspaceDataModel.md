# Temporary Workspace Data Model

**Created:** 2026-07-04 (Sprint 268)
**Status:** DEFINED — specification only. No implementation in this sprint.
**Depends on:** [docs/InputFirstWorkspaceOnboarding.md](InputFirstWorkspaceOnboarding.md)
**Depends on:** [docs/NoAccountFirstValueOnboarding.md](NoAccountFirstValueOnboarding.md)

---

## Purpose

This document defines the temporary workspace data model for Atlas input-first
onboarding. It specifies the fields, sub-models, and relationships that will
form the bridge between the future classification layer and the future
rendering layer.

A temporary workspace is the in-memory, no-account structure created from a
user's first input. It carries raw input context, classification results,
detected entities, uncertainties, workspace cards, and save/account handoff
state — without committing any of it to persistent storage unless the user
explicitly chooses to save.

This began as a product architecture specification. Sprint 270 adds minimal
schema-only Python dataclasses in `atlas/temporary_workspace/schema.py` that
represent this model without implementing JSON Schema, classifier, renderer,
database schema, UI, auth, backend services, or persistence.

---

## Model Principle

**A temporary workspace is an unsaved, no-account structure created from a
user's first input.**

It should be inspectable, explainable, and safe to discard.

It must not imply persistence unless the user explicitly chooses to save.

---

## Non-Goals

Sprint 268 did not:

- implement Python dataclasses or typed models
- implement JSON Schema or formal schema validation
- implement a classifier or entity extractor
- implement workspace rendering or card display
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

## Model Overview

A temporary workspace is created the moment a user submits input to Atlas. It
passes through three logical stages:

1. **Source input** — raw text or structured reference from the user
2. **Classification** — primary type, detected entities, confidence, uncertainties
3. **Card assembly** — workspace cards built from classification output

Throughout all three stages, the workspace remains temporary. It carries a
`status: "temporary"` flag and no persistence handle until the user chooses
to save.

The workspace connects upstream to the user's first input and downstream to
Snapshot Drafts and the Weekly Review Preview.

---

## Temporary Workspace

The top-level workspace object brings together all sub-models.

**Top-level fields:**

| Field | Type | Description |
|---|---|---|
| `workspace_id` | string | Unique temporary identifier, e.g. `tmp_ws_<random>` |
| `status` | string | Always `"temporary"` unless user saves |
| `created_at` | string (ISO 8601) | When the workspace was created |
| `source_input` | object | See Source Input |
| `classification` | object | See Classification Result |
| `detected_entities` | array | See Detected Entities |
| `uncertainties` | array | See Uncertainties |
| `missing_fields` | array | See Missing Fields |
| `cards` | array | See Workspace Cards |
| `save_handoff` | object | See Save / Account Handoff State |
| `safety_boundary` | object | See Safety Boundary |

**Example skeleton:**

```json
{
  "workspace_id": "tmp_ws_a3f9b2",
  "status": "temporary",
  "created_at": "2026-01-01T12:00:00Z",
  "source_input": {},
  "classification": {},
  "detected_entities": [],
  "uncertainties": [],
  "missing_fields": [],
  "cards": [],
  "save_handoff": {},
  "safety_boundary": {}
}
```

The `workspace_id` prefix `tmp_ws_` communicates that the workspace is not
yet saved. A future saved workspace would receive a stable identifier.

---

## Source Input

The source input sub-model represents what the user submitted, without
attempting to interpret it.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `input_id` | string | Unique identifier for this input, e.g. `input_<random>` |
| `input_type` | string | Classification category (see Classification Result) |
| `raw_text_preview` | string | First 500 characters of raw input, for explainability |
| `source_description` | string | Human-readable description of what was pasted |
| `submitted_at` | string (ISO 8601) | When the input was submitted |
| `user_language_hint` | string or null | If user explicitly selected `"en"` or `"sv"`; null otherwise |
| `contains_sensitive_data` | boolean | True if a future system infers PII or sensitive content |

**Design notes:**

- `raw_text_preview` is intentionally limited to a preview. Full raw input
  retention must be carefully designed in a future phase. Storing complete
  financial text from users may have privacy and compliance implications.
- `contains_sensitive_data` is reserved for future use. It must default to
  `false` until an explicit inference layer is implemented.
- `user_language_hint` reflects an explicit user selection only. Atlas does
  not detect language automatically and does not add `--language` to any
  command not already supporting it.

---

## Classification Result

The classification result sub-model records what type of input was submitted
and how confident the classifier is.

**Input categories** (from Sprint 267):

| Category | Description |
|---|---|
| `portfolio_input` | A list of holdings, weights, or values |
| `watchlist_input` | A list of tickers or companies under observation |
| `order_review_input` | An open or pending order idea |
| `research_note_input` | Qualitative notes about a company or sector |
| `company_facts_input` | Structured company profile facts |
| `journal_note_input` | An investor decision journal entry |
| `news_or_external_analysis_input` | A pasted article, excerpt, or analyst note |
| `question_input` | An investment-process question |
| `mixed_input` | Multiple types detected in the same input |
| `unknown_input` | Could not be classified with acceptable confidence |

**Fields:**

| Field | Type | Description |
|---|---|---|
| `primary_type` | string | One of the categories above |
| `secondary_types` | array of strings | Additional types if `mixed_input` |
| `confidence` | number | 0.0–1.0; classifier confidence in primary type |
| `rationale` | string | Human-readable reason for the classification |
| `uncertainties` | array | Uncertainty IDs linked to classification ambiguity |
| `suggested_cards` | array of strings | Card types the classifier recommends rendering |

**Design notes:**

- The classifier is not implemented in this sprint.
- `confidence` of 1.0 means unambiguous; 0.0 means entirely unclassifiable.
- If `confidence` is below a future-defined threshold, `unknown_input` should
  be used as `primary_type` and a user-facing uncertainty should be created.
- `suggested_cards` is advisory. The rendering layer remains free to override
  ordering or suppress cards not applicable to the detected content.

---

## Detected Entities

Detected entities are structured values extracted from the source input. Each
entity has a type, a raw value, and optional normalization and provenance.

**Entity types:**

| Entity type | Description |
|---|---|
| `ticker` | A stock or fund ticker symbol |
| `company_name` | A company name as written by the user |
| `holding` | A position in the user's portfolio |
| `quantity` | A share count or lot size |
| `portfolio_weight` | A percentage or fraction of portfolio |
| `currency` | A currency code or symbol |
| `date` | A date or date range referenced in the input |
| `watchlist_item` | A ticker or company on the user's watchlist |
| `open_decision` | A pending investment decision referenced by the user |
| `research_note` | A qualitative observation about a specific company |
| `company_fact` | A structured fact about a company |
| `source_reference` | A reference to an external source (article, filing, etc.) |

**Per-entity fields:**

| Field | Type | Description |
|---|---|---|
| `entity_id` | string | Unique identifier, e.g. `ent_<random>` |
| `entity_type` | string | One of the entity types above |
| `value` | string | Raw value as extracted from input |
| `normalized_value` | string or null | Canonical form if normalization is possible |
| `source_span` | string or null | Excerpt from input text where entity was found |
| `confidence` | number | 0.0–1.0; extraction confidence |
| `uncertainty_reason` | string or null | Why confidence is below 1.0, if applicable |

**Design notes:**

- Entity extraction is not implemented in this sprint.
- `normalized_value` for a ticker might map `"ASML"` to `"ASML.AS"` in a
  future phase. For this sprint, leave it null.
- `source_span` enables future explainability UI: "This holding was detected
  from this portion of your input."
- Entity extraction must not fabricate entities not present in the source
  input.

---

## Uncertainties

An uncertainty represents something the system is not sure about that may
affect the quality of the workspace.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `uncertainty_id` | string | Unique identifier, e.g. `unc_<random>` |
| `severity` | string | One of `low`, `medium`, `high`, `blocking` |
| `message` | string | Human-readable explanation of the uncertainty |
| `related_entity_ids` | array of strings | Entity IDs affected by this uncertainty |
| `related_card_ids` | array of strings | Card IDs that should surface this uncertainty |
| `suggested_user_confirmation` | string or null | Optional prompt to ask the user |

**Severity values:**

| Severity | Meaning |
|---|---|
| `low` | Minor ambiguity; workspace is still useful |
| `medium` | Notable ambiguity; some cards may be lower quality |
| `high` | Significant ambiguity; workspace should surface this prominently |
| `blocking` | Uncertainty prevents useful workspace construction |

**Design notes:**

- Uncertainties must not be hidden from the user. They should be retained and
  surfaced, not silently dropped.
- Do not use urgency language (e.g. "urgent", "critical", "must resolve").
- `suggested_user_confirmation` is a question the rendering layer may ask the
  user: e.g. `"Is ASML in EUR or USD?"`.

---

## Missing Fields

A missing field records structured input that would improve workspace quality
but was not provided.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `field_id` | string | Unique identifier, e.g. `miss_<random>` |
| `field_name` | string | Canonical English name of the missing field |
| `reason` | string | Why this field is expected |
| `related_card_ids` | array of strings | Cards that depend on this field |
| `optional_or_required` | string | One of four values below |

**`optional_or_required` values:**

| Value | Meaning |
|---|---|
| `optional` | Useful but not needed for any card |
| `required_for_export` | Required to produce a Snapshot Draft or similar export |
| `required_for_save` | Required before the workspace can be saved |
| `required_for_review_quality` | Required for full Weekly Review quality |

**Design notes:**

- Missing fields surface in the `missing_inputs` workspace card.
- They must not block workspace display unless `required_for_save` and the
  user has chosen to save.

---

## Workspace Cards

Each card in the workspace represents a structured view over a subset of the
classification and entity data.

**Card model fields:**

| Field | Type | Description |
|---|---|---|
| `card_id` | string | Unique identifier, e.g. `card_<random>` |
| `card_type` | string | One of the card types below |
| `title` | string | Display title (English; may be localized later) |
| `status` | string | One of the card status values below |
| `summary` | string | One-sentence summary of the card's content |
| `items` | array | Card-type-specific list of items |
| `related_entities` | array of strings | Entity IDs this card draws from |
| `related_uncertainties` | array of strings | Uncertainty IDs this card surfaces |
| `source_references` | array of strings | Input spans or source IDs this card references |

**Example card:**

```json
{
  "card_id": "card_ev_01",
  "card_type": "evidence_gaps",
  "title": "Evidence Gaps",
  "status": "needs_more_evidence",
  "summary": "2 holdings lack research notes. 1 holding lacks company facts.",
  "items": [
    {"ticker": "NOVO B", "missing": ["research_notes", "company_facts"]},
    {"ticker": "MSFT", "missing": ["research_notes"]}
  ],
  "related_entities": ["ent_a1", "ent_a2"],
  "related_uncertainties": [],
  "source_references": []
}
```

---

## Card Types

Card types align with Sprint 267's workspace card set.

| Card type | Description |
|---|---|
| `input_summary` | Summary of what was detected in the user's input |
| `detected_holdings` | Holdings extracted from a portfolio input |
| `detected_tickers` | Tickers detected without full holding context |
| `portfolio_context` | Portfolio-level context: concentration, currency, dates |
| `watchlist_review` | Watchlist items detected and their current review state |
| `open_decisions` | Open investment decisions detected in the input |
| `evidence_gaps` | Holdings or tickers lacking research notes or company facts |
| `risks_to_monitor` | Risks surfaced by profile principles or holding characteristics |
| `reasons_to_wait` | Reasons not to act: aging notes, open questions, missing evidence |
| `follow_up_questions` | Questions Atlas could not answer from available input |
| `missing_inputs` | Structured inputs that would improve workspace quality |
| `snapshot_drafts` | Snapshot Draft candidates for user review and confirmation |
| `weekly_review_preview` | Preview of a Weekly Review built from temporary inputs |
| `save_workspace_prompt` | Prompt to save the workspace and optionally create an account |

Avoid recommendation-oriented card names (e.g. "buy candidates", "action items").

---

## Card Status Values

Card status values describe the current state of a card's content.

| Status | Meaning |
|---|---|
| `ready_for_review` | Card has sufficient data and can be reviewed as-is |
| `needs_more_evidence` | Card is useful but missing some supporting data |
| `missing_required_input` | Card cannot be fully rendered without additional input |
| `user_confirmation_needed` | Card contains entities or values the user should confirm |
| `not_applicable` | Card type is not relevant to this workspace's classification |
| `no_action_warranted` | Content reviewed; no action needed by the user |
| `decision_deferred` | User has noted the card but deferred a response |

Do not use buy/sell/recommendation status values.

---

## Card Ordering

Default card ordering follows the user's likely information needs: context
first, gaps and concerns in the middle, handoff last.

| Position | Card type |
|---|---|
| 1 | `input_summary` |
| 2 | `detected_holdings` or `detected_tickers` |
| 3 | `portfolio_context` |
| 4 | `watchlist_review` |
| 5 | `open_decisions` |
| 6 | `evidence_gaps` |
| 7 | `risks_to_monitor` |
| 8 | `reasons_to_wait` |
| 9 | `follow_up_questions` |
| 10 | `missing_inputs` |
| 11 | `snapshot_drafts` |
| 12 | `weekly_review_preview` |
| 13 | `save_workspace_prompt` |

**Ordering rules:**

- `save_workspace_prompt` is always last. Account prompting must not block
  first value.
- `input_summary` is always first. The user should always see what was
  detected before seeing analysis.
- Cards with `not_applicable` status may be omitted entirely.
- Ordering may be adjusted based on classification: a `question_input`
  workspace may promote `follow_up_questions` above `evidence_gaps`.

---

## Save / Account Handoff State

The save/account handoff state records whether and how the workspace can be
saved.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `account_required` | boolean | Whether an account is needed |
| `save_available` | boolean | Whether the user can save the workspace |
| `save_requires_account` | boolean | Whether saving requires account creation |
| `prompt_timing` | string | When the save prompt should be shown |
| `prompt_reason` | string | Why the user might want to save |

**Example:**

```json
{
  "account_required": false,
  "save_available": true,
  "save_requires_account": true,
  "prompt_timing": "after_first_value",
  "prompt_reason": "save_workspace"
}
```

**`prompt_timing` values:**

| Value | Meaning |
|---|---|
| `after_first_value` | Show after workspace cards are rendered |
| `on_explicit_request` | Show only if user clicks Save |
| `never` | Do not prompt in this workspace context |

**`prompt_reason` values:**

| Value | Meaning |
|---|---|
| `save_workspace` | User wants to keep this workspace |
| `continue_later` | User wants to return to this workspace later |
| `keep_history` | User wants a history of their workspaces |
| `collaborate` | User wants to share this workspace with others |
| `cross_device_access` | User wants to access this workspace on another device |

**Design rule: account prompting must not block first value.**

`account_required` must be `false` for any temporary workspace. An account
prompt may appear in the `save_workspace_prompt` card after all other cards
have been rendered. It must never appear before `input_summary`.

---

## Safety Boundary

The safety boundary records the constraints that apply to all workspace cards.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `no_recommendations` | boolean | True: workspace does not contain investment recommendations |
| `no_order_execution` | boolean | True: workspace does not trigger order execution |
| `no_price_targets` | boolean | True: workspace does not contain price targets |
| `user_judgment_required` | boolean | True: all outputs require user review before acting |
| `local_or_temporary_context` | boolean | True: workspace is based on user-provided input only |

**Example:**

```json
{
  "no_recommendations": true,
  "no_order_execution": true,
  "no_price_targets": true,
  "user_judgment_required": true,
  "local_or_temporary_context": true
}
```

The safety boundary applies to all workspace cards. No card may assert a
recommendation, price target, certainty, or urgency. Cards surface structure,
evidence gaps, uncertainties, and questions — not conclusions or instructions.

---

## Relationship to Snapshot Drafts

A temporary workspace may contain Snapshot Draft candidates, surfaced in the
`snapshot_drafts` card. These are unconfirmed drafts derived from the
user's temporary input.

**Rules:**

- No Snapshot Draft should be silently persisted from a temporary workspace
  without explicit user action.
- The `snapshot_drafts` card presents candidates for the user to review,
  confirm, or discard — following the same confirm/reject workflow defined
  in earlier sprints.
- A Snapshot Draft candidate created from a temporary workspace carries a
  `source: "temporary_workspace"` marker to distinguish it from a draft
  created in a saved workspace.
- Until confirmed, a Snapshot Draft candidate is as temporary as the workspace
  it came from.

---

## Relationship to Weekly Review Preview

A temporary workspace may show a Weekly Review Preview in the
`weekly_review_preview` card. This preview is generated from the temporary
structured inputs extracted during classification.

**Rules:**

- The preview must not imply saved portfolio history. It is a preview of what
  a Weekly Review would look like if the user's input were saved and used as
  a starting point.
- The preview follows the same 10-section structure as a full Weekly Review,
  but sections that require persistent data (e.g. journal aging, saved
  company facts) will be minimal or absent.
- The preview uses the same deterministic renderer as the full Weekly Review.
  No new rendering logic is created in this sprint.
- The preview is labeled clearly as temporary so the user understands it does
  not reflect their full portfolio history.

---

## Canonical Values

Internal model values remain canonical English. This applies to:

- `card_type` values (e.g. `evidence_gaps`, `reasons_to_wait`)
- `status` values (e.g. `ready_for_review`, `needs_more_evidence`)
- `classification` category values (e.g. `portfolio_input`, `unknown_input`)
- `entity_type` values (e.g. `ticker`, `holding`, `open_decision`)
- `optional_or_required` values (e.g. `required_for_export`)
- `prompt_reason` values (e.g. `save_workspace`, `collaborate`)
- `prompt_timing` values (e.g. `after_first_value`)
- safety boundary field names

User-facing display labels (card titles, summary text, status labels) may be
localized separately in a future phase, following the existing Atlas locale
pattern (`strings.py` / `strings_sv.py`). Schema values, enum candidates,
and internal identifiers must remain English regardless of `--language`
selection.

---

## Example JSON

The following example represents a pasted portfolio/watchlist input that
produces five workspace cards: input summary, detected tickers, evidence gaps,
reasons to wait, weekly review preview, and save workspace prompt.

```json
{
  "workspace_id": "tmp_ws_c7e4a1",
  "status": "temporary",
  "created_at": "2026-01-01T09:15:00Z",
  "source_input": {
    "input_id": "input_0b3d72",
    "input_type": "portfolio_input",
    "raw_text_preview": "ASML 12%, NOVO B 18%, MSFT 10%, LVMH 8%, cash 52%",
    "source_description": "Pasted portfolio text with 4 holdings and cash",
    "submitted_at": "2026-01-01T09:15:00Z",
    "user_language_hint": null,
    "contains_sensitive_data": false
  },
  "classification": {
    "primary_type": "portfolio_input",
    "secondary_types": [],
    "confidence": 0.91,
    "rationale": "Input contains tickers with percentage weights summing to 100%.",
    "uncertainties": ["unc_001"],
    "suggested_cards": [
      "input_summary",
      "detected_tickers",
      "evidence_gaps",
      "reasons_to_wait",
      "weekly_review_preview",
      "save_workspace_prompt"
    ]
  },
  "detected_entities": [
    {
      "entity_id": "ent_001",
      "entity_type": "holding",
      "value": "ASML 12%",
      "normalized_value": null,
      "source_span": "ASML 12%",
      "confidence": 0.97,
      "uncertainty_reason": null
    },
    {
      "entity_id": "ent_002",
      "entity_type": "holding",
      "value": "NOVO B 18%",
      "normalized_value": null,
      "source_span": "NOVO B 18%",
      "confidence": 0.95,
      "uncertainty_reason": null
    },
    {
      "entity_id": "ent_003",
      "entity_type": "holding",
      "value": "MSFT 10%",
      "normalized_value": null,
      "source_span": "MSFT 10%",
      "confidence": 0.97,
      "uncertainty_reason": null
    },
    {
      "entity_id": "ent_004",
      "entity_type": "holding",
      "value": "LVMH 8%",
      "normalized_value": null,
      "source_span": "LVMH 8%",
      "confidence": 0.94,
      "uncertainty_reason": null
    }
  ],
  "uncertainties": [
    {
      "uncertainty_id": "unc_001",
      "severity": "low",
      "message": "No currency detected. Holdings may be in mixed currencies.",
      "related_entity_ids": ["ent_001", "ent_002", "ent_003", "ent_004"],
      "related_card_ids": ["card_tickers_01"],
      "suggested_user_confirmation": "Are all holdings denominated in the same currency?"
    }
  ],
  "missing_fields": [
    {
      "field_id": "miss_001",
      "field_name": "investor_profile",
      "reason": "No profile detected in input. Weekly Review quality is lower without a profile.",
      "related_card_ids": ["card_review_01"],
      "optional_or_required": "required_for_review_quality"
    },
    {
      "field_id": "miss_002",
      "field_name": "research_notes",
      "reason": "No research notes provided for ASML, NOVO B, MSFT, or LVMH.",
      "related_card_ids": ["card_gaps_01"],
      "optional_or_required": "required_for_review_quality"
    }
  ],
  "cards": [
    {
      "card_id": "card_summary_01",
      "card_type": "input_summary",
      "title": "Input Summary",
      "status": "ready_for_review",
      "summary": "Detected 4 holdings from a pasted portfolio text.",
      "items": [],
      "related_entities": ["ent_001", "ent_002", "ent_003", "ent_004"],
      "related_uncertainties": ["unc_001"],
      "source_references": []
    },
    {
      "card_id": "card_tickers_01",
      "card_type": "detected_tickers",
      "title": "Detected Tickers",
      "status": "user_confirmation_needed",
      "summary": "4 tickers detected: ASML, NOVO B, MSFT, LVMH.",
      "items": ["ASML", "NOVO B", "MSFT", "LVMH"],
      "related_entities": ["ent_001", "ent_002", "ent_003", "ent_004"],
      "related_uncertainties": ["unc_001"],
      "source_references": []
    },
    {
      "card_id": "card_gaps_01",
      "card_type": "evidence_gaps",
      "title": "Evidence Gaps",
      "status": "needs_more_evidence",
      "summary": "4 holdings lack research notes. No company facts found.",
      "items": [
        {"ticker": "ASML", "missing": ["research_notes", "company_facts"]},
        {"ticker": "NOVO B", "missing": ["research_notes", "company_facts"]},
        {"ticker": "MSFT", "missing": ["research_notes", "company_facts"]},
        {"ticker": "LVMH", "missing": ["research_notes", "company_facts"]}
      ],
      "related_entities": ["ent_001", "ent_002", "ent_003", "ent_004"],
      "related_uncertainties": [],
      "source_references": []
    },
    {
      "card_id": "card_wait_01",
      "card_type": "reasons_to_wait",
      "title": "Reasons to Wait",
      "status": "needs_more_evidence",
      "summary": "Evidence gaps across all holdings are reasons to wait before acting.",
      "items": [
        "Evidence gaps: 4 holdings lack research notes",
        "No investor profile to check suitability"
      ],
      "related_entities": [],
      "related_uncertainties": ["unc_001"],
      "source_references": []
    },
    {
      "card_id": "card_review_01",
      "card_type": "weekly_review_preview",
      "title": "Weekly Review Preview",
      "status": "needs_more_evidence",
      "summary": "Preview based on temporary inputs. No saved portfolio history used.",
      "items": [],
      "related_entities": ["ent_001", "ent_002", "ent_003", "ent_004"],
      "related_uncertainties": ["unc_001"],
      "source_references": []
    },
    {
      "card_id": "card_save_01",
      "card_type": "save_workspace_prompt",
      "title": "Save Workspace",
      "status": "ready_for_review",
      "summary": "Save this workspace to keep your analysis and continue later.",
      "items": [],
      "related_entities": [],
      "related_uncertainties": [],
      "source_references": []
    }
  ],
  "save_handoff": {
    "account_required": false,
    "save_available": true,
    "save_requires_account": true,
    "prompt_timing": "after_first_value",
    "prompt_reason": "save_workspace"
  },
  "safety_boundary": {
    "no_recommendations": true,
    "no_order_execution": true,
    "no_price_targets": true,
    "user_judgment_required": true,
    "local_or_temporary_context": true
  }
}
```

---

## Validation Expectations

When a temporary workspace is constructed in a future implementation, the
following properties should be validated:

| Expectation | Rule |
|---|---|
| Required top-level fields present | All fields in the skeleton must be present |
| Status is temporary | `status` must be `"temporary"` unless user has saved |
| `card_type` values from known set | Each card's `card_type` must be one of the defined types |
| No `account_required: true` before first value | `save_handoff.account_required` must be `false` |
| Save prompt appears after all other cards | `save_workspace_prompt` card must be last in `cards` array |
| `input_summary` appears first | First card must be `input_summary` |
| Canonical values remain English | No localized strings in schema fields, enum values, or identifiers |
| Raw user content is marked as user-provided | `source_input.raw_text_preview` must be clearly attributed to user |
| Uncertainties retained rather than hidden | `uncertainties` array must not be silently emptied |
| Safety boundary all true | All five safety boundary fields must be `true` for temporary workspaces |

---

## Future Implementation Phases

| Phase | Target | Status |
|---|---|---|
| Phase 0 | Define data model (this sprint) | Complete |
| Phase 1 | Define card rendering contract (Sprint 269) | Complete |
| Phase 2 | Prototype Python dataclasses for the model (Sprint 270) | Complete |
| Phase 3 | Implement input classifier | Future |
| Phase 4 | Implement entity extraction | Future |
| Phase 5 | Implement card assembly from classification output | Future |
| Phase 6 | Implement temporary workspace CLI command | Future |
| Phase 7 | Implement save/account handoff | Future |

Sprint 268 performed no implementation. Sprint 270 later added schema-only
dataclasses in `atlas/temporary_workspace/schema.py`; classifier, renderer,
persistence, accounts, and CLI behavior remain future work.

---

## Open Questions

1. **Raw input retention:** How long should `raw_text_preview` be? Should the
   full raw input be retained in memory for the duration of the session, or
   only the preview? What are the privacy implications of retaining full text
   in a local-only temporary workspace?

2. **Workspace lifecycle:** When does a temporary workspace expire? On session
   end? After a timer? If Atlas is a CLI tool, the workspace lives for the
   duration of the command. For a future web or desktop app, a session model
   is needed.

3. **Multiple inputs in one workspace:** Can a user paste a second input and
   have it merged into the same temporary workspace? Or does each input create
   a new workspace? The `mixed_input` category suggests merging is intended,
   but the merge contract needs to be defined.

4. **Entity normalization:** Who performs ticker normalization (e.g. `ASML` →
   `ASML.AS`)? Should this happen in the classifier or in a separate
   normalization layer?

5. **Weekly Review Preview fidelity:** A full Weekly Review requires a saved
   portfolio, journal, profile, and company facts. A temporary workspace
   preview will be partial. Should the preview display a confidence or
   completeness indicator?

---

## Recommended Next Sprint

**Sprint 271: Add temporary workspace schema examples**

After schema dataclasses exist, Atlas should add example temporary workspace
JSON fixtures that can support future renderer and classifier work.

This should remain documentation and fixture work only. It should not implement
classification, entity extraction, rendering, CLI commands, persistence,
accounts, providers, network calls, OCR, or AI.

This continues the pattern of specifying architecture before building it.
