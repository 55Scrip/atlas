# CLI Language Option Plan

**Status: Phase 1 implemented (Sprint 257). Phase 2 implemented (Sprint 259). Usage documented (Sprint 260). Regression matrix added (Sprint 261).**
**Sprint:** 256 (planning), 257 (Phase 1 implementation), 258 (Phase 2 planning), 259 (Phase 2 implementation), 260 (documentation), 261 (regression matrix).

---

## Purpose

Document the future shape of the `--language` CLI option for Atlas, including
option naming, allowed values, command coverage, locale propagation path, error
handling, backward compatibility requirements, canonical value preservation,
user-content passthrough, safety gates, and required tests before any
implementation sprint begins.

This document is a prerequisite for implementation. No production code is changed
by this document.

---

## Non-Goals

- Do not add `--language` in this sprint.
- Do not expose Swedish output through the CLI in this sprint.
- Do not add runtime locale detection, environment-variable language selection,
  config-file language selection, or automatic language inference.
- Do not add gettext, string catalogs, or `.po`/`.mo` files.
- Do not add AI/LLM translation.
- Do not change schemas, enum values, warning codes, or CLI command names.
- Do not add `fr`, `de`, `ja`, or any locale beyond `en` and `sv`.

---

## Current State

```
Supported internally:   en, sv
Default:                en
CLI exposure:           Phase 1 (weekly-review, snapshot validate, snapshot review)
--language:             implemented for Phase 1 read-only commands (Sprint 257)
--language Phase 2:     deferred (snapshot confirm/reject/export-*)
Runtime detection:      not implemented
String catalogs:        not used
gettext:                not used
```

Swedish internal activation is complete (B1–B14 DONE, Sprint 255). Both
`render_weekly_review` and all 14 Snapshot renderer functions accept
`locale="sv"` and produce correct Swedish output. Phase 1 CLI commands pass
`locale=language` to their respective renderers after `ensure_supported_locale`
validation. Default CLI output remains English — `--language` is an explicit
opt-in.

---

## Proposed Option

```
--language {en,sv}
```

**Rationale:**

- Explicit user choice — no automatic detection.
- Simple and understandable.
- Maps directly to supported renderer locales (`SUPPORTED_LOCALE_EN`,
  `SUPPORTED_LOCALE_SV` in `atlas/locale_support.py`).
- Avoids conflating user interface language with internal canonical values.
- The value set `{en,sv}` matches `locale_support._SUPPORTED_LOCALES` exactly,
  preventing CLI and renderer from drifting independently.

**Not proposed:**

- `--locale` — less familiar to end users; implies system locale semantics.
- `--lang` — ambiguous abbreviation.
- `ATLAS_LANGUAGE` environment variable — violates explicit-choice principle.
- Config-file `language:` key — same concern; also harder to audit in tests.

---

## Supported Values

```
en   — English (default)
sv   — Swedish
```

Any other value must fail before rendering. No fallback to English. No silent
coercion. No case normalization (so `EN`, `SV`, `En`, `Sv` all fail). No
region-code expansion (so `en-US`, `sv-SE` both fail). These constraints are
already enforced by `ensure_supported_locale` in `atlas/locale_support.py` and
do not need to be re-implemented in CLI argument parsing.

---

## Command Coverage

### Phase 1 — Read-Only Commands ✓ IMPLEMENTED (Sprint 257)

```
atlas weekly-review     --language {en,sv}
atlas snapshot validate --language {en,sv}
atlas snapshot review   --language {en,sv}
```

**Rationale:** Read-only commands produce terminal output only. No local files
are written or modified. This is the lowest-risk starting point.

### Phase 2 — Write-Producing Local Commands (implement after Phase 1 stable)

```
atlas snapshot confirm             --language {en,sv}
atlas snapshot reject              --language {en,sv}
atlas snapshot export-research-notes --language {en,sv}
atlas snapshot export-company-facts  --language {en,sv}
```

**Rationale:** These commands write or rename local files. The confirmation and
rejection messages are terminal output only (the written file content is
canonical JSON — unaffected by locale). The export commands write local files
whose names and content are determined by schema, not by display language.
Phase 2 is lower-risk than it first appears, but it is still separated so that
Phase 1 stability can be confirmed first.

### Commands with no language output

Commands that produce no user-facing display text do not need `--language`. If
any such command is added in the future it should be assessed individually.

---

## Default Behavior

If `--language` is omitted, output must remain identical to the current English
output. This is a hard backward-compatibility constraint.

```
atlas weekly-review ...                 → English (unchanged)
atlas weekly-review ... --language en   → English (identical to default)
atlas weekly-review ... --language sv   → Swedish
```

No automatic detection. No locale from:

- Environment variables (`LANG`, `LC_ALL`, `LC_MESSAGES`, `ATLAS_LANGUAGE`, etc.)
- Config files (`.atlas.toml`, `~/.atlasrc`, etc.)
- System locale (`locale.getlocale()`)
- Terminal locale detection

The absence of `--language` must always mean English.

---

## Locale Propagation Path

### Weekly Review

```
User passes:  atlas weekly-review ... --language sv

CLI layer:    weekly_review_command(... language: str = "en")
              → validated with ensure_supported_locale(language) or
                equivalent argparse choices=list(locale_support._SUPPORTED_LOCALES)
              → load_weekly_review_inputs(paths)
              → render_weekly_review(result, locale=language)

Renderer:     render_weekly_review(result, locale="sv")
              → S = _strings_for_locale("sv")
              → returns Swedish display strings
```

### Snapshot

```
User passes:  atlas snapshot validate ... --language sv

CLI layer:    snapshot_validate_command(... language: str = "en")
              → validated with ensure_supported_locale(language)
              → load and parse draft
              → render_snapshot_draft_validation(draft, locale=language)

Renderer:     render_snapshot_draft_validation(draft, locale="sv")
              → S = _strings_for_locale("sv")
              → returns Swedish display strings
```

### Avoiding Supported-Language List Drift

The CLI should not maintain its own list of supported language values. Two
acceptable approaches:

1. **argparse `choices`:** Use
   `sorted(atlas.locale_support._SUPPORTED_LOCALES)` as the `choices` argument
   so the CLI enum stays in sync with the locale boundary automatically.
2. **Post-parse validation:** Accept any string in argparse and call
   `ensure_supported_locale(language)` before passing it to any renderer.
   The existing `ValueError` message names both the bad value and the supported
   values.

Either approach is acceptable. Approach 1 gives better argparse error messages
at parse time. Approach 2 keeps the error message consistent with direct
renderer calls. The implementation sprint must choose one and document the
choice.

---

## Unsupported Locale Handling

When an unsupported value is passed to `--language`, the command must fail
before rendering begins. No partial output should be emitted.

```
atlas weekly-review ... --language fr    → error, no output rendered
atlas weekly-review ... --language EN    → error (case-sensitive)
atlas weekly-review ... --language sv-SE → error (no region codes)
atlas weekly-review ... --language ""    → error
```

The error must:
- Name the unsupported value.
- List the supported values (`en`, `sv`).
- Exit with a non-zero return code.
- Not produce partial Weekly Review or Snapshot output.

The existing `ensure_supported_locale` error message satisfies points 1–2.
The implementation must ensure exit code and output suppression.

---

## Backward Compatibility Requirements

1. All existing Atlas commands without `--language` must produce output
   identical to their current English output. No exceptions.
2. All existing tests must remain green after implementation.
3. All existing scripts (`scripts/verify_release_candidate.sh`,
   `scripts/run_daily_brief_demo.sh`, `scripts/run_internal_v1_demo.sh`) must
   remain green without modification.
4. All existing fixtures remain valid.
5. CLI `--help` output changes only when `--language` is intentionally added in
   a future sprint.
6. The `render_weekly_review(result)` default call (no `locale=`) remains
   identical to `render_weekly_review(result, locale="en")`.

---

## Canonical Values That Must Remain English

Even when `--language sv` is eventually active, the following must remain
identical to their current English form in all output:

**Snapshot schema values:**

```
research_notes_snapshot    company_facts_snapshot
portfolio_snapshot         watchlist_snapshot
open_orders_snapshot       news_snapshot
external_analysis_snapshot unknown_snapshot

confirmed    rejected    draft    needs_user_review    superseded

high    medium    low    unknown
```

**Warning codes:**

```
missing_optional_profile    missing_optional_journal
missing_optional_financials  missing_optional_company_facts
missing_watchlist_status    unknown_watchlist_status
missing_sector              missing_market_value
```

**CLI commands and flags:**

```
weekly-review    snapshot    validate    review    confirm    reject
export-research-notes    export-company-facts
--portfolio    --watchlist    --as-of    --profile    --journal
--language
```

**Ticker symbols:**

```
Any ticker symbol (MSFT, ASML, XYL, NOVO, CASH, etc.)
```

**File paths and directory names:**

```
Any path passed by the user or written to disk.
```

The distinction: Atlas-generated *display labels* and *section headings* may be
localized. Canonical identifiers that appear in JSON files, schema keys, enum
values, warning codes, and CLI flag names must never be localized.

---

## User-Provided Content Handling

User-provided content must pass through unchanged regardless of `--language`.

This includes:

- Research notes loaded from disk
- Scope notes (`--scope-notes`)
- Decision journal entries
- Investor profile field values
- Portfolio notes
- Watchlist reasons and evidence-needed lists
- Snapshot `notes` field
- Snapshot `source_description`
- Snapshot `raw_source_reference`
- Snapshot `extracted_fields` values
- Company facts values

Only Atlas-generated display labels, section headings, status strings, and
disclaimers are localized. User-provided content is never translated — not
automatically, not by any renderer path.

---

## Safety Guardrails

Implementation of `--language` cannot proceed unless all of the following
remain green:

1. Swedish safe-language guardrails (`docs/SwedishSafeLanguageGuardrails.md`)
   remain in force — no prohibited category phrasing in any Swedish string.
2. Forbidden-category scan (`test_swedish_output_matrix_sprint252.py` B6) passes.
3. Canonical value preservation matrix (`test_swedish_canonical_passthrough_sprint253.py`)
   passes.
4. User-content passthrough matrix (`test_swedish_canonical_passthrough_sprint253.py`)
   passes.
5. Unsupported-locale regression matrix (`test_unsupported_locale_regression_sprint254.py`)
   passes.
6. sv activation full-suite gate (`test_sv_activation_full_suite_gate_sprint255.py`) passes.
7. CLI default-English regression passes (no `--language` call produces Swedish).
8. Demos and RC verification remain green.

---

## Required Tests Before Implementation

The implementation sprint must add the following tests before `--language` is
considered complete:

**CLI option presence:**

- `atlas weekly-review --help` includes `--language`
- `atlas snapshot validate --help` includes `--language`
- `atlas snapshot review --help` includes `--language`

**Default behavior (backward compatibility):**

- `atlas weekly-review ...` (no `--language`) output is identical to before
- `atlas weekly-review ... --language en` output is identical to default
- All existing scripts pass without modification

**Swedish CLI output:**

- `atlas weekly-review ... --language sv` includes Swedish title
- `atlas weekly-review ... --language sv` includes Swedish section titles
- `atlas weekly-review ... --language sv` includes Swedish disclaimer
- `atlas snapshot validate ... --language sv` includes Swedish validation heading
- `atlas snapshot review ... --language sv` includes Swedish review heading

**Unsupported locale rejection:**

- `atlas weekly-review ... --language fr` exits non-zero, no partial output
- `atlas weekly-review ... --language EN` exits non-zero
- `atlas weekly-review ... --language sv-SE` exits non-zero

**Canonical value preservation (CLI path):**

- `atlas weekly-review ... --language sv` output contains warning codes unchanged
- `atlas weekly-review ... --language sv` output contains ticker symbols unchanged
- `atlas snapshot validate ... --language sv` output contains `snapshot_type` unchanged
- `atlas snapshot validate ... --language sv` output contains `confirmation_status` unchanged

**User-content passthrough (CLI path):**

- `atlas weekly-review ... --language sv` scope notes unchanged
- `atlas weekly-review ... --language sv` watchlist reasons unchanged
- `atlas snapshot validate ... --language sv` snapshot notes unchanged

**Infrastructure:**

- No gettext imports introduced
- No locale detection introduced
- No translation catalogs added
- No environment-variable language selection

---

## Rollout Plan

```
Phase 0 — COMPLETE (Sprints 247–255)
  Swedish internal activation (B1–B14 all DONE)

Phase 1 — COMPLETE (Sprint 257)
  Implemented --language for read-only CLI commands:
    atlas weekly-review     --language {en,sv}
    atlas snapshot validate --language {en,sv}
    atlas snapshot review   --language {en,sv}
  Validation via ensure_supported_locale; locale passed to renderers.
  Unsupported values fail before rendering with non-zero exit.
  68 CLI tests added. Default remains English.

Phase 2 — COMPLETE (Sprint 259)
  --language extended to write-producing local commands:
    atlas snapshot confirm               --language {en,sv}   ✓
    atlas snapshot reject                --language {en,sv}   ✓
    atlas snapshot export-research-notes --language {en,sv}   ✓
    atlas snapshot export-company-facts  --language {en,sv}   ✓
  Safety boundary: docs/Phase2SnapshotCLILanguagePlan.md.
  Written files verified byte-for-byte identical across language settings.
  Unsupported values fail before any file writes.

Phase 3 — NOT YET PLANNED
  Consider Swedish user-facing documentation (N1)
  Consider Swedish investor profile field labels (N2)
```

---

## Open Questions

1. **argparse `choices` vs post-parse validation** — Which approach for CLI
   validation? `choices=sorted(_SUPPORTED_LOCALES)` gives a better argparse
   error; `ensure_supported_locale()` gives a consistent error format with
   direct renderer calls. The implementation sprint must decide and document.

2. **`--language` position** — Should it be a global option (before the
   subcommand) or a per-command option (after the subcommand name)? Per-command
   is safer — it limits scope and avoids ambiguity for commands that do not
   support it.

3. **Phase 2 timing** — Sprint 258 planned Phase 2. Sprint 259 is the recommended
   implementation sprint. All four write-producing commands implement the same
   pattern so they can be added in a single sprint.

4. **Swedish `--help` text** — Should `--help` output itself be localized? Not
   in the initial implementation. CLI help text is English only; `--language`
   affects rendered output, not the CLI help interface.

---

## Recommended Implementation Sprint

**Sprint 257:** Implement `--language` for Phase 1 read-only commands only:
`atlas weekly-review`, `atlas snapshot validate`, `atlas snapshot review`.

Pre-conditions:
- This planning document reviewed and approved.
- All safety gates from the "Safety Guardrails" section above are green.
- Implementation follows the locale propagation path documented above.
- All required tests from "Required Tests Before Implementation" are added.
