# Snapshot Draft Confirmation Workflow

**Sprint:** 227
**Date:** 2026-07-04
**Status:** Specified — not yet implemented
**Relates to:** `docs/AtlasSnapshotInputWorkflow.md`

---

## Overview

A Snapshot Draft is a structured interpretation of user-supplied information.
It is not authoritative until confirmed. This document defines the confirmation
workflow: how a draft moves from its initial state to a state that export commands
will accept.

The confirmation boundary exists to keep the user in control of every write to
Atlas local input files. No export command may write an Atlas input file from an
unconfirmed draft.

---

## Confirmation Principles

The following principles apply to all current and future Snapshot Draft
confirmation behavior:

1. **A Snapshot Draft is not authoritative until confirmed.**
   A draft is a candidate interpretation, not a fact.

2. **Confirmation is a user-review boundary.**
   The user explicitly accepts a draft before any Atlas input file is written.

3. **Confirmation must be explicit.**
   Confirmation does not happen automatically. No inference, no default-accept,
   no silent promotion.

4. **Confirmation must be local.**
   Confirmation state is stored in local JSON files. No cloud sync, no external
   service.

5. **Confirmation must not depend on live data.**
   A draft may be confirmed without fetching any external information.

6. **Confirmation must not call AI or LLMs.**
   No AI model is consulted during confirmation.

7. **Confirmation must not call providers.**
   No provider imports are permitted in the confirmation path.

8. **Confirmation does not write Atlas input files by itself.**
   Confirmation changes the draft's status. A subsequent export command writes
   the Atlas input file. These are separate steps.

9. **Export commands only accept confirmed drafts.**
   Any future `atlas snapshot export-*` command must check
   `confirmation_status == confirmed` before writing any Atlas local input file.

10. **Uncertainties remain visible through confirmation.**
    The `uncertainties` field is preserved. Confirmation does not erase
    uncertainty — it records that the user saw and accepted it.

11. **Missing required fields must be resolved or explicitly acknowledged.**
    If `missing_required_fields` is non-empty, the confirmation step should make
    this visible. Confirmation may proceed if the user explicitly acknowledges
    the gap, but the field is preserved in the confirmed draft.

---

## Confirmation State Definitions

The `SnapshotConfirmationStatus` enum defines five states. Their meanings are:

### `draft`
- **Meaning:** Initial structured interpretation. Not yet reviewed by the user.
- **Exportable:** No.
- **Transition:** → `needs_user_review` (when the draft is ready for review) or
  directly → `confirmed` (when the user sets status manually in simple workflows).
- **Notes:** Most newly created drafts start here.

### `needs_user_review`
- **Meaning:** Structured enough to review, but not yet confirmed. The draft has
  been surfaced to the user and is awaiting an explicit decision.
- **Exportable:** No.
- **Transition:** → `confirmed` (user accepts) or → `rejected` (user declines).
- **Notes:** This state is appropriate when a future validation or presentation
  step flags the draft for user attention before export.

### `confirmed`
- **Meaning:** The user has reviewed and explicitly accepted this draft. The draft
  may be exported by supported export commands.
- **Exportable:** Yes — the only exportable state.
- **Transition:** → `superseded` (if a newer draft replaces it).
- **Notes:** Confirmation does not mean the draft is perfect. Uncertainties and
  missing fields may remain. The user accepted the draft in its current form.

### `rejected`
- **Meaning:** The user decided this draft should not be used. The interpretation
  was incorrect, out of date, or otherwise not suitable.
- **Exportable:** No.
- **Transition:** Terminal (a rejected draft is not re-confirmed; a new draft
  should be created instead).
- **Notes:** Rejected drafts should be retained for traceability.

### `superseded`
- **Meaning:** A newer draft has replaced this one. The superseded draft is
  preserved for traceability but should not be exported.
- **Exportable:** No.
- **Transition:** Terminal.
- **Notes:** When a user corrects a draft, the original is marked superseded and
  a new draft is created with the corrected fields.

---

## Exportability Rule

**Only `confirmed` drafts are exportable.**

Every current and future `atlas snapshot export-*` command must enforce:

```python
if draft.confirmation_status != SnapshotConfirmationStatus.CONFIRMED:
    # fail with clear message
    "Draft is not confirmed. Conversion requires confirmation_status=confirmed."
```

This rule is already implemented in `atlas snapshot export-research-notes`
(Sprint 225). Every future export command must follow the same pattern.

Future export commands and the input types they would write:

| Future command | Target Atlas input |
|---------------|--------------------|
| `export-research-notes` | `research_notes/<TICKER>/notes.md` ✓ Implemented |
| `export-watchlist` | `watchlist.json` |
| `export-company-facts` | `company_facts/<TICKER>.json` |
| `export-portfolio` | `portfolio.json` |
| `export-journal` | `decision_journal.json` |
| `export-scope-notes` | `scope_notes.md` |

None of the future commands are implemented in Sprint 227.

---

## Review Checklist

Before a user confirms a draft, the following should be visible:

### Universal (all draft types)

| Field | Description |
|-------|-------------|
| `draft_id` | Unique identifier for traceability |
| `snapshot_type` | The interpreted type of the snapshot |
| `confidence` | Descriptive confidence level (low / medium / high / unknown) |
| `confirmation_status` | Current status — must be `draft` or `needs_user_review` |
| `source_description` | Human-readable description of where the draft came from |
| `related_tickers` | Tickers associated with this draft |
| `target_local_file` | The Atlas input file this draft would update |
| `uncertainties` | All known uncertainties in the extracted fields |
| `missing_required_fields` | Fields that could not be extracted confidently |
| `raw_source_reference` | Path or description of the original source material |
| Safety boundary statement | What files will and will not be written on export |

### Research notes drafts (`research_notes_snapshot`)

In addition to the universal checklist:

| Field | Description |
|-------|-------------|
| `extracted_fields["ticker"]` | Ticker that will become the notes directory name |
| `extracted_fields["title"]` | Title of the research notes file |
| `extracted_fields["thesis_notes"]` | Thesis bullets that will be written |
| `extracted_fields["evidence_gaps"]` | Evidence gap bullets |
| `extracted_fields["open_questions"]` | Open question bullets |
| `extracted_fields["risks_to_monitor"]` | Risk bullets |
| `extracted_fields["reasons_to_wait"]` | Reason to wait bullets |
| Target path | `<output-dir>/<TICKER>/notes.md` |

---

## Blocking Rules

A future `atlas snapshot review` or `atlas snapshot confirm` command should block
confirmation when any of the following apply:

| Rule | Condition | Message |
|------|-----------|---------|
| Unsupported type | `snapshot_type == unknown_snapshot` | "Unknown snapshot type cannot be confirmed." |
| Missing draft ID | `draft_id` is empty | "draft_id must be non-empty." |
| Missing source description | `source_description` is empty | "source_description must be non-empty." |
| Missing target file | `target_local_file` is empty | "target_local_file must be non-empty." |
| Already terminal | `confirmation_status in (confirmed, rejected, superseded)` | "Draft is already in terminal state: {status}." |
| Missing ticker (ticker-required types) | No ticker in `extracted_fields` or `related_tickers` | "Ticker is required for {snapshot_type} drafts." |
| Unsafe ticker | Ticker contains `/`, `\`, or `..` | "Unsafe ticker value: {ticker}." |
| Empty extracted fields (when fields required) | `extracted_fields == {}` for non-trivial types | "extracted_fields is empty. Review the source interpretation before confirming." |

Unresolved `missing_required_fields` should be surfaced as a warning, not a hard
block — the user may choose to confirm a draft knowing that some fields were not
extracted. The field list must remain visible in the confirmed draft.

These rules are not yet implemented. They define the expected behavior of future
`atlas snapshot confirm` and `atlas snapshot review` commands.

---

## Field Correction Model

When a user identifies an error in a draft's extracted fields before confirmation,
the correction model should follow this pattern:

1. **Create a revised draft** — do not silently mutate the original. A new draft
   is created with corrected fields and a new `draft_id` (or a versioned suffix).
2. **Mark the prior draft as superseded** — set `confirmation_status = superseded`
   on the original. This preserves the audit trail.
3. **Preserve source attribution** — `source_description` and
   `raw_source_reference` from the original draft should be carried into the
   revised draft.
4. **Preserve uncertainties** — corrections to extracted fields do not remove
   uncertainty notes. If the uncertainty is resolved, it may be removed explicitly
   by the user.
5. **Update confirmation_status** — the revised draft starts at `draft` or
   `needs_user_review`.

This model ensures that the original source interpretation is never silently
overwritten. The correction is traceable.

*Implementation is future work. Sprint 227 only specifies this model.*

---

## Future CLI Shape

The following commands are planned but not yet implemented:

### `atlas snapshot review <draft_path>`

Read-only. Displays the full confirmation checklist for a draft. Does not write
any files. Shows blocking issues, uncertainties, and missing fields. The user can
use this to decide whether to confirm or reject.

```bash
atlas snapshot review examples/snapshot_drafts/research_notes_snapshot_asml.json
```

### `atlas snapshot confirm <draft_path> --output-draft <confirmed_draft_path>`

Writes a new draft JSON file with `confirmation_status` set to `confirmed`.
Does **not** write any Atlas local input file (portfolio, watchlist, notes, etc.).
The confirmed draft is then passed to an export command to produce the Atlas input.

```bash
atlas snapshot confirm \
  examples/snapshot_drafts/research_notes_snapshot_asml.json \
  --output-draft examples/snapshot_drafts/research_notes_snapshot_asml_confirmed.json
```

### `atlas snapshot reject <draft_path> --output-draft <rejected_draft_path>`

Writes a new draft JSON file with `confirmation_status` set to `rejected`.
Does not write any Atlas local input file.

```bash
atlas snapshot reject \
  examples/snapshot_drafts/research_notes_snapshot_asml.json \
  --output-draft examples/snapshot_drafts/research_notes_snapshot_asml_rejected.json
```

### `atlas snapshot supersede <draft_path> --replacement-draft <new_draft_path>`

Marks the original draft as superseded and links it to a replacement.

Rules for all future confirmation commands:
- Commands are local-only. No network calls.
- Commands do not call AI or providers.
- `confirm` does not write Atlas input files — that is the export command's job.
- Commands do not silently overwrite the original draft unless explicitly designed
  and documented to do so.
- The original draft JSON is never mutated in place.

---

## Export Command Dependency

Every `atlas snapshot export-*` command depends on confirmation status:

```
Draft state check:
  if confirmation_status != confirmed → fail with clear message
  if snapshot_type != <supported_type> → fail with clear message
  then: write Atlas local input file
```

This dependency is already implemented in `atlas snapshot export-research-notes`.

The dependency must be preserved in all future export commands. It must not be
possible to export from an unconfirmed draft by passing a flag or option.

---

## Audit and Traceability

The following fields are preserved through the confirmation lifecycle to support
traceability:

| Field | Preserved through confirmation | Notes |
|-------|-------------------------------|-------|
| `draft_id` | Yes | Identifier for the original interpretation |
| `source_description` | Yes | Human-readable source origin |
| `raw_source_reference` | Yes | Path or label of the original source |
| `created_at` | Yes | When the draft was initially created |
| `uncertainties` | Yes | Not erased on confirmation |
| `missing_required_fields` | Yes | Not erased on confirmation |
| `extracted_fields` | Yes | The interpreted content |
| `snapshot_type` | Yes | Type of the original source |
| `confidence` | Yes | Confidence in the original extraction |

Future optional fields that may be added:
- `confirmed_at` — ISO 8601 timestamp of confirmation (caller-supplied for
  determinism, not system clock by default).
- `confirmed_by` — User-supplied label (optional, never required).

These fields are not added to the schema in Sprint 227.

---

## Safety Boundary

Confirmation must never:

- Fetch data from any external source
- Call any Atlas provider
- Call any LLM or AI model
- Execute orders of any kind
- Write portfolio files (`portfolio.json`) directly
- Write watchlist files (`watchlist.json`) directly
- Write journal files (`decision_journal.json`) directly
- Write company facts files (`company_facts/*.json`) directly
- Write scope notes files directly
- Hide or remove uncertainties from the draft
- Remove source attribution or context
- Create investment recommendations
- Compare securities as investment opportunities
- Use forbidden language (buy/sell/price target/urgent/act now/guaranteed)

Confirmation changes only the draft's `confirmation_status`. Writing an Atlas
input file is always a separate, explicit export step.

---

## Relationship to Weekly Review

```
User writes notes / supplies portfolio data / observes information
         ↓
  Snapshot Draft created (snapshot_type, extracted_fields, uncertainties)
         ↓
  atlas snapshot review (read-only checklist)
         ↓
  atlas snapshot confirm (writes confirmed draft copy)
         ↓
  atlas snapshot export-* (writes Atlas local input file)
         ↓
  atlas weekly-review --research-notes / --portfolio / --watchlist / ...
         ↓
  Weekly Review Sections 1–10
```

Key rules:
- Weekly Review consumes structured local inputs (portfolio.json, watchlist.json,
  research_notes/<TICKER>/notes.md, etc.).
- Snapshot confirmation produces a confirmed intermediate draft.
- Export commands convert confirmed drafts into local Weekly Review inputs.
- Weekly Review must not consume unconfirmed Snapshot Drafts directly.
- The confirmation boundary keeps every write to Atlas local inputs traceable to
  an explicit user review step.

---

## Confirmation State Examples

### Example 1 — Draft not ready for export

```json
{
  "draft_id": "draft-research-asml-001",
  "snapshot_type": "research_notes_snapshot",
  "confirmation_status": "draft",
  "uncertainties": ["China revenue exposure is inferred, not confirmed."],
  "missing_required_fields": ["reasons_to_wait"]
}
```

**Result:** Not exportable. `atlas snapshot export-research-notes` would fail with:
`"Draft is not confirmed. Conversion requires confirmation_status=confirmed."`

---

### Example 2 — Needs user review

```json
{
  "draft_id": "draft-research-asml-001",
  "snapshot_type": "research_notes_snapshot",
  "confirmation_status": "needs_user_review",
  "uncertainties": ["China revenue exposure is inferred, not confirmed."]
}
```

**Result:** Not exportable. Awaiting explicit user decision.

---

### Example 3 — Confirmed and exportable

```json
{
  "draft_id": "draft-research-asml-001-confirmed",
  "snapshot_type": "research_notes_snapshot",
  "confirmation_status": "confirmed",
  "uncertainties": ["China revenue exposure is inferred, not confirmed."],
  "missing_required_fields": []
}
```

**Result:** Exportable. `atlas snapshot export-research-notes` proceeds.
Note: `uncertainties` is preserved even in the confirmed draft.

---

### Example 4 — Rejected

```json
{
  "draft_id": "draft-research-asml-001",
  "snapshot_type": "research_notes_snapshot",
  "confirmation_status": "rejected"
}
```

**Result:** Not exportable. Terminal state.

---

### Example 5 — Superseded

```json
{
  "draft_id": "draft-research-asml-001",
  "snapshot_type": "research_notes_snapshot",
  "confirmation_status": "superseded",
  "notes": "Superseded by draft-research-asml-002 after field corrections."
}
```

**Result:** Not exportable. The replacement draft (draft-research-asml-002)
should be confirmed and exported instead.

---

## Implementation Status

| Component | Status |
|-----------|--------|
| `SnapshotConfirmationStatus` enum (5 states) | Implemented (Sprint 223) |
| `SnapshotDraft` schema with `confirmation_status` field | Implemented (Sprint 223) |
| `atlas snapshot validate` (read-only validation) | Implemented (Sprint 224) |
| `atlas snapshot export-research-notes` (confirmed-only export) | Implemented (Sprint 225) |
| Confirmation workflow specification | **This document (Sprint 227)** |
| `atlas snapshot review` command | Not yet implemented |
| `atlas snapshot confirm` command | Not yet implemented |
| `atlas snapshot reject` command | Not yet implemented |
| `atlas snapshot supersede` command | Not yet implemented |
| `export-watchlist` command | Not yet implemented |
| `export-company-facts` command | Not yet implemented |
| `export-portfolio` command | Not yet implemented |

---

## Recommended Sprint 228 Target

**Add `atlas snapshot review` command.**

Before implementing confirmation writes, Atlas should expose a read-only review
command that renders the full confirmation checklist for a draft. This:

- Keeps the confirmation boundary explicit and visible.
- Lets users see blocking issues, uncertainties, and missing fields before
  deciding whether to confirm.
- Avoids file mutation entirely.
- Validates the review checklist UX before committing to a write command.

The `atlas snapshot review` command would be the natural predecessor to
`atlas snapshot confirm`. Once review is proven useful, the confirm command
(which writes a confirmed draft copy) follows as Sprint 229.

---

## Repository Identity

This is Atlas. This is not Atlas Edge. Atlas and Atlas Edge are separate products.
No Atlas Edge concepts, naming, or architecture are present in this document.
