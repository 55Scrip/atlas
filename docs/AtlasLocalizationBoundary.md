# Atlas Localization Boundary

**Sprint:** 236 (specification) / 244 (Weekly Review locale boundary) / 245 (Snapshot CLI locale boundary) / 246 (Shared locale helper) / 247 (Swedish guardrail spec) / 248 (Swedish readiness checklist) / 249 (Swedish string constants) / 250 (Swedish renderer dispatch boundary) / 251 (sv locale activation) / 252 (Swedish output test matrix)
**Date:** 2026-07-04
**Status:** Shared locale boundary in `atlas/locale_support.py` — only "en" supported — no translations implemented

---

## Core Principle

> Atlas thinks internally in canonical English and may eventually speak externally
> in the user's selected language.

Internal logic, schema values, enum values, and test fixtures remain stable
canonical English regardless of any future output language setting. User-facing
display strings — report headings, explanatory text, safety boundary messages —
are the only layer that may eventually be localized.

This separation protects:

- deterministic internal behavior across all language settings
- stable test assertions that do not depend on display language
- safe-language guardrails that remain enforceable per locale
- file and directory conventions that work across operating systems
- schema interoperability with external tools or future data exports

---

## Canonical Internal English

The following must remain English permanently. They are internal identifiers,
not display text. They must never be translated at runtime.

### Schema keys and JSON field names

```
snapshot_type
confirmation_status
confidence
extracted_fields
uncertainties
missing_required_fields
target_local_file
draft_id
source_description
raw_source_reference
related_tickers
created_at
notes
```

### Enum values

```
snapshot_type:
  research_notes_snapshot
  company_facts_snapshot
  portfolio_snapshot
  watchlist_snapshot
  open_orders_snapshot
  news_snapshot
  external_analysis_snapshot
  unknown_snapshot

confirmation_status:
  draft
  needs_user_review
  confirmed
  rejected
  superseded

confidence:
  high
  medium
  low
  unknown
```

### CLI option names

```
--portfolio
--watchlist
--profile
--journal
--company-facts
--financials
--research-notes
--as-of
--scope-notes
--output-draft
--output-dir
--overwrite
```

### Internal status and warning codes

```
confirmation_status values
warning_code identifiers
error identifiers
```

### File and directory conventions

```
research_notes/<TICKER>/notes.md
company_facts/<TICKER>.json
portfolio.json
watchlist.json
investor_profile.json
decision_journal.json
```

### Test fixture keys

All keys in test fixture JSON files remain English. Test assertions against
internal values (e.g. `confirmation_status == "confirmed"`) remain English.

### Guardrail category names

Internal guardrail categories are English identifiers, not display strings:

```
recommendation_language
price_target_language
urgency_language
certainty_language
execution_language
```

---

## User-Facing Localizable Strings

The following strings are display text generated at the rendering layer.
They may eventually be localized per user-selected language.

### Weekly Review output

```
Section titles (e.g. "Portfolio Context", "Missing Evidence")
Section body explanatory text
Input status messages
Warning explanations
Evidence gap labels
Risk to monitor labels
Reason to wait labels
Non-action labels
```

### Snapshot CLI output

```
"Snapshot Draft Validation"
"Status: valid"
"Status: confirmed"
"Status: blocked"
"Exportable: yes"
"Exportable: no"
"Safety Boundary:" message text
"Blocking Issues:" message text
"Research Notes Export"
"Company Facts Export"
```

### Demo and usage guide prose

```
Stage headings in run_internal_v1_demo.sh (may be localized)
Usage guide explanatory paragraphs (may have localized variants)
```

These strings exist only in renderer modules and display scripts. They carry
no internal semantics. Changing them does not change program behavior.

---

## Boundary Rules

These rules govern how localization must be introduced when the time comes.

1. **Canonical data remains English.** Schema keys, enum values, and internal
   status codes are never translated at runtime or in storage.

2. **Localized display text is generated at the final rendering layer only.**
   Business logic receives and returns canonical values. Renderers convert them
   to display strings. Only renderers are localized.

3. **Tests for logic assert canonical values.** A test that checks
   `result.confirmation_status == "confirmed"` will never need to change for
   localization. A test that checks rendered output text should only assert
   locale-specific strings when explicitly testing the localization layer.

4. **User-provided content is not translated automatically.** Research notes,
   scope notes, snapshot draft content, and journal entries remain in the
   language the user wrote them. Atlas does not rewrite or translate
   user-provided text.

5. **File paths and schema keys are not translated.** The directory
   `research_notes/ASML/notes.md` and the field `confirmation_status` are the
   same in every language setting.

6. **Safe-language guardrails must exist per locale before that locale is
   enabled.** An English guardrail list cannot protect Swedish output. Each
   locale requires its own guardrail list before being activated. See
   Locale-Specific Guardrails below.

7. **Default language remains English until localization is implemented.** All
   current output is English. This default persists until an explicit `--language`
   or config option is introduced with full guardrail coverage.

8. **Missing localization must fail safely to English.** If a string has no
   translation for the requested locale, the English string is used. No empty
   strings, no missing labels, no error messages left raw.

9. **Localization must not change program behavior.** Selecting a different
   output language must not affect which sections render, which evidence gaps
   are detected, which blocking rules are applied, or which files are written.
   It affects display text only.

10. **Localization is opt-in per command.** The `--language` option (when
    implemented) applies only to the command that receives it. Internal file
    formats and schema values are unaffected.

---

## Locale-Specific Safe-Language Guardrails

Each locale that Atlas supports for user-facing output must have its own
guardrail list before that locale is activated. Guardrails protect output
semantics, not just exact words.

### Guardrail categories (language-independent)

These categories apply in every locale. Each locale needs its own
prohibited phrase list within each category:

```
Recommendation language
  — phrases that direct the user to buy, sell, or take a specific position

Price-target language
  — phrases that state or imply a numerical target or forecast price

Urgency language
  — phrases that pressure the user to act immediately

Certainty language
  — phrases that imply guaranteed outcomes or zero risk

Execution/action language
  — phrases that instruct the user to execute a trade or order
```

### Current English guardrails (implemented)

The existing English guardrail list covers the categories above for English
output. Prohibited terms span recommendation, price-target, urgency, certainty,
and execution-language categories. These are enforced today across all CLI
output, generated JSON, docs, and test fixtures.

### Future Swedish guardrails (specification complete — Sprint 247)

`docs/SwedishSafeLanguageGuardrails.md` defines all safety requirements before
`sv` can be enabled. 7 prohibited categories (recommendation, transaction,
price-target, urgency, certainty, outperformance, personalized advice), safe
Swedish alternatives table, concept mapping, style rules, user-provided content
rules, and 10 testing requirements. Swedish renderer is not yet implemented.
`sv` is not enabled.

`docs/SwedishLocalizationReadinessChecklist.md` (Sprint 248) defines the 14
blocking criteria (B1–B14) that must all be satisfied before `sv` is added to
`atlas/locale_support.py`. 4 of 14 are currently DONE (B1 guardrail spec,
B2 readiness checklist, B3 string constants, B4 renderer dispatch boundary).
`sv` is not enabled.

Sprint 249 created `atlas/weekly_review/strings_sv.py` and
`atlas/snapshot_input/strings_sv.py` — isolated Swedish display string
constant modules.

Sprint 250 added `_strings_for_locale(locale)` dispatch helpers to both
renderers. Both `strings_sv` modules are now imported by their respective
renderers and mapped in the dispatch helper.

Sprint 251 updated `atlas/locale_support.py` to add `SUPPORTED_LOCALE_SV = "sv"`
and accept `"sv"` in `ensure_supported_locale`. The `sv` dispatch branch in both
renderers is now reachable. `render_weekly_review(result, locale="sv")` and all
14 Snapshot renderer functions return Swedish display strings when called directly
with `locale="sv"`. Default locale remains `"en"`. CLI output remains English —
there is no `--language` option and the CLI does not pass a locale parameter.
B5 is DONE.

Sprint 252 created `tests/test_swedish_output_matrix_sprint252.py` — a systematic
91-test matrix covering all Atlas-generated Swedish strings across direct renderer
calls. Renderer bug fixed: two hardcoded English phrases in Weekly Review section 10
(`REMINDER_NO_ACTION_VALID`, `REMINDER_ATLAS_SUPPORTS_JUDGMENT`) now use locale
constants via `S`. Swedish output is internally tested and passes forbidden-category
scan for all 7 prohibited categories. CLI output remains English. B6–B10 are DONE.

Sprint 253 created `tests/test_swedish_canonical_passthrough_sprint253.py` — a
systematic matrix verifying that Swedish-locale output does not translate canonical
internal values or user-provided content. All 8 SnapshotType values, all 5
SnapshotConfirmationStatus values, all 4 SnapshotConfidence values, warning codes,
ticker symbols, file paths, scope notes, watchlist reasons, research note text,
journal entries, snapshot notes, and snapshot extracted fields are verified unchanged.
English output is verified identical before and after calling the Swedish renderer.
B11 and B12 are DONE.

Sprint 254 created `tests/test_unsupported_locale_regression_sprint254.py` — a
systematic regression matrix verifying that every unsupported locale raises
`ValueError` from `ensure_supported_locale`, `render_weekly_review`, and all 14
public Snapshot locale-aware renderer functions. 13 unsupported locale values tested:
`fr`, `de`, `ja`, `no`, `da`, `fi`, `es`, `xx`, `""`, `EN`, `SV`, `en-US`, `sv-SE`.
Supported locales remain exactly `"en"` and `"sv"`. No production code changes. B13 is
DONE.

Sprint 255 created `tests/test_sv_activation_full_suite_gate_sprint255.py` — a compact
release gate verifying all 14 blocking criteria hold together: B1–B13 all DONE in
checklist, all 8 prior Swedish test files present, supported locales exactly `"en"` and
`"sv"`, direct Swedish renderers working, unsupported locales failing, English/CLI
preserved, no gettext/catalogs/detection/provider imports. Swedish internal activation
is complete. Swedish remains direct-renderer/internal only — CLI remains English, no
`--language` option. Any future CLI exposure requires a separate planning sprint. All
14 of 14 blocking criteria satisfied. B14 is DONE.

Sprint 256 created `docs/CLILanguageOptionPlan.md` — the design document for the
future `--language {en,sv}` CLI option. The plan documents option naming, command
coverage (Phase 1: read-only commands; Phase 2: write-producing local commands),
locale propagation path from CLI through `ensure_supported_locale` to renderer
`_strings_for_locale`, unsupported-locale error handling (fail before render, no
fallback, no coercion), backward compatibility requirements, canonical values that
must remain English, user-content passthrough requirements, safety guardrails, and
the full test matrix required before implementation. No production code was changed.
`--language` is not implemented. CLI output remains English.

### Future French guardrails (not yet defined)

Same requirement applies. No French guardrail list is defined in this sprint.

---

## User-Provided Content Handling

User-provided content is the text a user writes into snapshot drafts, research
notes, scope notes, decision journal entries, and investor profile fields.

Rules:

- **Do not translate user-provided notes automatically.** A Swedish research
  note remains Swedish. A French pasted excerpt remains French.

- **Preserve source language in all stored files.** `research_notes/ASML/notes.md`
  stores the user's original text unchanged.

- **Atlas-generated headings and explanations may be localized later.** When
  a Weekly Review is rendered in Swedish, the section headings and Atlas-generated
  explanatory text may appear in Swedish. The user's research note content within
  Section 8 or Section 9 remains in its original language.

- **Guardrail scans do not rewrite user-provided content.** The guardrail layer
  checks Atlas-generated output, not user-provided notes. If a future safety
  layer is added to scan user-provided content, it must be an explicit opt-in
  with its own boundary specification.

- **Clearly distinguish user-provided content from Atlas-generated output.**
  Section structure and provenance labels (e.g. "(research notes)") make this
  boundary visible in the Weekly Review output today.

---

## Snapshot Draft Localization Boundary

Snapshot Draft schema is canonical English. It does not change with locale.

| Element | Localized? |
|---------|-----------|
| `snapshot_type` field name | No |
| `snapshot_type` enum values | No |
| `confirmation_status` field name | No |
| `confirmation_status` enum values | No |
| `extracted_fields` key name | No |
| Keys within `extracted_fields` | No |
| `target_local_file` value | No |
| `source_description` value | User-provided — not translated |
| `notes` value | User-provided — not translated |
| CLI output of `snapshot validate` | Yes (future) |
| CLI output of `snapshot review` | Yes (future) |
| CLI output of `snapshot confirm` | Yes (future) |
| CLI output of `snapshot reject` | Yes (future) |
| CLI output of `snapshot export-*` | Yes (future) |

**Sprint 246 — Shared Locale Helper:**

`atlas/locale_support.py` provides `SUPPORTED_LOCALE_EN = "en"` and
`ensure_supported_locale(locale: str) -> None`. Both `atlas/weekly_review/render.py`
and `atlas/snapshot_input/render.py` now import and call this shared helper.
Local duplicate guards have been removed from both renderer modules.

**Sprint 245 — Locale Boundary Defined:**

All 14 public Snapshot CLI renderer functions now accept `*, locale: str = "en"`.
A shared `_ensure_locale(locale)` helper raises `ValueError` for unsupported locales.
Only `"en"` is currently supported. The CLI does not pass `locale=`; it always uses the default.

```python
# Supported:
render_snapshot_draft_review(draft)               # default en
render_snapshot_draft_review(draft, locale="en")  # explicit en

# Not yet supported:
render_snapshot_draft_review(draft, locale="sv")  # raises ValueError
```

---

## Weekly Review Localization Boundary

| Element | Localized? |
|---------|-----------|
| Section identifiers (internal) | No |
| Section titles (rendered) | Yes (future) |
| Section body explanatory text | Yes (future) |
| Input status messages | Yes (future) |
| Warning messages | Yes (future) |
| Evidence gap labels | Yes (future) |
| Reason to wait labels | Yes (future) |
| User's research notes content | No — preserve original |
| User's scope notes content | No — preserve original |
| Portfolio JSON schema keys | No |
| Watchlist JSON schema keys | No |
| Investor profile JSON schema keys | No |

The 10-section structure of the Weekly Review remains stable regardless of
output language. Section count, section order, and section content logic do
not change with locale.

**Sprint 244 — Locale Boundary Defined:**

`render_weekly_review(result, *, locale: str = "en") -> str` now accepts an
explicit `locale` keyword argument. Only `"en"` is currently supported.
Unsupported locales raise `ValueError` immediately. The CLI does not expose
`--language`; it always uses the default. No translations are implemented.
This is a boundary-only change — all output is identical to pre-Sprint 244.

```python
# Supported:
render_weekly_review(result)             # default en
render_weekly_review(result, locale="en")  # explicit en

# Not yet supported:
render_weekly_review(result, locale="sv")  # raises ValueError
```

---

## Documentation Boundary

| Document type | Language |
|--------------|---------|
| Developer docs (architecture, internals) | English by default |
| API and schema reference | English permanently |
| User-facing usage guides | May have localized variants (future) |
| Localized usage guides | Must not redefine schema or enum values |
| Test files | English permanently |

Localized usage guide variants, when created, are companion documents alongside
the English canonical guide — not replacements. The English canonical guide
remains the source of truth for schema and behavior.

---

## Future Implementation Phases

These phases describe how localization should eventually be introduced.
No phase is implemented in Sprint 236.

| Phase | Description |
|-------|-------------|
| 1 | Extract user-facing strings from Weekly Review and Snapshot CLI renderers into a strings inventory |
| 2 | Add locale-aware rendering helpers with English as the only loaded locale |
| 3 | Add `--language` option to selected commands (Weekly Review first) |
| 4 | Add locale-specific safe-language guardrail tests before enabling non-English locales |
| 5 | Add Swedish user-facing output with full guardrail coverage |
| 6 | Add French user-facing output with full guardrail coverage |

Phase 1 (strings inventory) is the recommended next step after this boundary
is defined. See Sprint 237 recommendation below.

---

## Out of Scope

The following are explicitly out of scope and must not be introduced while
localizing Atlas:

| Item | Note |
|------|------|
| Multilingual rendering implementation | Future — Phase 5+ |
| `--language` CLI option | Future — Phase 3 |
| Translation files or catalogs | Future — Phase 2+ |
| Runtime locale detection | Not planned — explicit opt-in only |
| Translating user-provided content | Not planned — preserve source language |
| Translating schemas or enums | Never |
| Changing Snapshot Draft schema | Not in scope of localization |
| Changing Weekly Review output behavior | Localization changes display only |
| AI translation | Not planned |
| External translation APIs | Not planned |
| UI language settings | Future — UI not yet implemented |

---

## Sprint 237 Recommendation

**Recommended target: Extract user-facing strings inventory**

After defining the localization boundary, the safest next step is to produce a
complete inventory of user-facing strings in the Weekly Review and Snapshot CLI
renderers. This inventory is the prerequisite for Phase 1 of the implementation
plan above.

The inventory should list every Atlas-generated display string, grouped by
command or renderer, without changing any behavior. It makes the scope of
localization work concrete and testable before any rendering layer changes
are made.

**Alternative if product breadth is prioritised:** Implement draft-to-watchlist
conversion.

**Alternative if demo polish is prioritised:** Run internal demo dry-run with
documentation only.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [docs/AtlasV1OperatingMode.md](AtlasV1OperatingMode.md) | v1 product boundary |
| [docs/AtlasWeeklyInvestmentReviewSpec.md](AtlasWeeklyInvestmentReviewSpec.md) | Weekly Review specification |
| [docs/AtlasSnapshotInputWorkflow.md](AtlasSnapshotInputWorkflow.md) | Snapshot Input workflow |
| [docs/InternalV1ReleaseCandidate.md](InternalV1ReleaseCandidate.md) | v1 release candidate status |
| [docs/DecisionLog.md](DecisionLog.md) | Sprint-by-sprint decisions |
