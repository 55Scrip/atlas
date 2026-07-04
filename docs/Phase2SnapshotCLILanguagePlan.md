# Phase 2 Snapshot CLI Language Plan

**Status: Implemented (Sprint 259). Phase 1 live (Sprint 257). Phase 2 live (Sprint 259).**
**Sprint:** 258 (planning), 259 (implementation).

---

## Purpose

Document the safety boundary, implementation pattern, and required tests for
extending `--language {en,sv}` to the four local write-producing Snapshot CLI
commands. This document is a prerequisite for any Phase 2 implementation sprint.
No production code is changed by this document.

---

## Non-Goals

- Do not add `--language` to any command in this sprint.
- Do not change CLI behavior.
- Do not change default English output.
- Do not change Swedish output for Phase 1 commands.
- Do not change renderer code.
- Do not change export code.
- Do not change confirm/reject code.
- Do not translate written files.
- Do not add gettext, string catalogs, or `.po`/`.mo` files.
- Do not add runtime locale detection, environment-variable language selection,
  config-file language selection, or automatic language inference.
- Do not add AI/LLM translation.
- Do not change schemas, enum values, or warning codes.
- Do not add any locale beyond `en` and `sv`.

---

## Current State

```
Phase 1 (complete — Sprint 257):
  atlas weekly-review          --language {en,sv}   ✓ implemented
  atlas snapshot validate      --language {en,sv}   ✓ implemented
  atlas snapshot review        --language {en,sv}   ✓ implemented

Phase 2 (implemented — Sprint 259):
  atlas snapshot confirm               --language {en,sv}   ✓ implemented
  atlas snapshot reject                --language {en,sv}   ✓ implemented
  atlas snapshot export-research-notes --language {en,sv}   ✓ implemented
  atlas snapshot export-company-facts  --language {en,sv}   ✓ implemented

Default:                  en (English)
Runtime detection:        not implemented
String catalogs:          not used
gettext:                  not used
```

Phase 1 is stable. All Phase 1 commands accept `--language en` (default) or
`--language sv`. Unsupported values fail before rendering with non-zero exit.
Default English output is identical to pre-Sprint-257. 3896 tests pass.

---

## Target Commands

Phase 2 adds `--language {en,sv}` to these four local write-producing commands:

```
atlas snapshot confirm               --language {en,sv}
atlas snapshot reject                --language {en,sv}
atlas snapshot export-research-notes --language {en,sv}
atlas snapshot export-company-facts  --language {en,sv}
```

These commands write local files. The `--language` option must affect only
the CLI display text printed to the terminal. It must never affect the content
of any written file.

---

## Display-Only Localization Boundary

The `--language` option for Phase 2 commands must affect **only CLI display text**.

It must not affect:

- Written artifact content (JSON or Markdown files)
- File paths or output directory names
- Schema keys
- Enum values
- JSON output structure
- Markdown export structure
- Stored data of any kind

### Examples by command

**`snapshot confirm`:**
- CLI success/block/error text printed to terminal may be Swedish.
- The confirmed draft JSON file content must remain canonical and identical to
  the output that `--language en` (or omitted) would produce.

**`snapshot reject`:**
- CLI success/block/error text printed to terminal may be Swedish.
- The rejected draft JSON file content must remain canonical and identical to
  the output that `--language en` (or omitted) would produce.

**`snapshot export-research-notes`:**
- CLI success/block/error text printed to terminal may be Swedish.
- The written `notes.md` content must remain in its existing export format;
  user-provided research note text must remain unchanged.
  `--language sv` must produce a byte-for-byte identical `notes.md` compared
  to `--language en` or the default.

**`snapshot export-company-facts`:**
- CLI success/block/error text printed to terminal may be Swedish.
- The written company facts JSON content must remain canonical JSON.
  `--language sv` must produce a byte-for-byte identical `.json` file compared
  to `--language en` or the default.

---

## Written Artifact Preservation

The following must not change based on `--language`:

**JSON and Markdown files written to disk:**
- Confirmed draft JSON files
- Rejected draft JSON files
- Research notes Markdown exports (`notes.md`)
- Company facts JSON exports (`<TICKER>.json`)

**Fields and values within written files:**
- Output file paths
- `target_local_file` values
- `raw_source_reference` values
- `extracted_fields` keys and values
- Schema keys (all JSON field names)
- Enum values (`confirmation_status`, `snapshot_type`, `confidence`)
- Ticker symbols
- User-provided notes, source descriptions, and free-text fields
- `created_at` values (determined by the command, not by display language)
- `draft_id` values

The same input and output path must produce identical written files regardless
of whether `--language en` or `--language sv` is passed. If timestamps cause
minor non-determinism in specific fields, byte-for-byte identity is required for
all fields except those explicitly documented timestamp fields.

---

## Command-by-Command Plan

### `atlas snapshot confirm`

**Future invocation:**
```bash
atlas snapshot confirm draft.json --output-draft confirmed.json --language sv
```

**Expected behavior:**
- CLI display text (success message, block message, error text) in Swedish.
- Output draft file content identical to `--language en` / default.
- `confirmation_status` remains `confirmed`.
- All canonical values remain English.
- User-provided fields (`notes`, `source_description`, `extracted_fields`, etc.)
  unchanged.

**Implementation pattern (to be applied in Phase 2 sprint):**

1. Add `language: str = typer.Option("en", "--language", help="Output language: en (English, default) or sv (Swedish).")` to `snapshot_confirm_command` signature.
2. Call `ensure_supported_locale(language)` immediately; catch `ValueError`, print error, exit 1.
3. Determine which renderer functions produce CLI display text and pass `locale=language` to them.
4. Do not pass `language` / `locale` to any file-writing path.

### `atlas snapshot reject`

**Future invocation:**
```bash
atlas snapshot reject draft.json --output-draft rejected.json --language sv
```

**Expected behavior:**
- CLI display text in Swedish.
- Output draft file content identical to `--language en` / default.
- `confirmation_status` remains `rejected`.
- All canonical values remain English.
- User-provided fields unchanged.

**Implementation pattern:** Same as `snapshot confirm` above.

### `atlas snapshot export-research-notes`

**Future invocation:**
```bash
atlas snapshot export-research-notes confirmed_research_notes.json \
  --output-dir out --language sv
```

**Expected behavior:**
- CLI success/block/error text in Swedish.
- Written `notes.md` content unaffected by CLI display language.
- User-provided research note text unchanged.
- Output file path unchanged.
- Ticker path unchanged.

**File invariance requirement:** `notes.md` produced with `--language sv` must be
byte-for-byte identical to `notes.md` produced with `--language en` or default,
given the same confirmed draft and output directory.

### `atlas snapshot export-company-facts`

**Future invocation:**
```bash
atlas snapshot export-company-facts confirmed_company_facts.json \
  --output-dir out --language sv
```

**Expected behavior:**
- CLI success/block/error text in Swedish.
- Company facts JSON written content unaffected by CLI display language.
- Schema keys remain canonical English.
- User-provided company facts values unchanged.

**File invariance requirement:** `<TICKER>.json` produced with `--language sv`
must be byte-for-byte identical to `<TICKER>.json` produced with `--language en`
or default, given the same confirmed draft and output directory.

---

## Unsupported Language Handling

Phase 2 must apply the same policy as Phase 1: unsupported values fail **before
any command side effects**.

No output files must be created or changed if language validation fails.

**Unsupported values (representative):**
```
fr    de    ja    no    da    fi    es
xx    ""    EN    SV    en-US    sv-SE
```

**Expected behavior for all of the above:**
- Non-zero exit code.
- Error message names the unsupported value.
- Error message lists supported locales (`en`, `sv`).
- No partial rendered output printed.
- No file writes initiated.
- No output directories created.

This is enforced by calling `ensure_supported_locale(language)` at the start of
the command body, before any file I/O, using the same pattern as Phase 1.

---

## Backward Compatibility

1. Omitting `--language` keeps existing English display output exactly as before.
   Existing scripts (`scripts/verify_release_candidate.sh`,
   `scripts/run_daily_brief_demo.sh`, `scripts/run_internal_v1_demo.sh`) must
   continue to work unchanged.
2. `--language en` must produce display output identical to omitted `--language`.
3. `--language sv` must alter display text only — no file writes affected.
4. All existing written files (confirmed drafts, rejected drafts, notes.md,
   company facts JSON) remain identical.
5. All existing tests must remain green after implementation.
6. CLI `--help` changes only when `--language` is intentionally added in the
   Phase 2 sprint.

---

## Canonical Values That Must Remain English

Phase 2 must preserve these in all written files and displayed canonical values:

**Snapshot schema values:**
```
research_notes_snapshot    company_facts_snapshot
portfolio_snapshot         watchlist_snapshot
open_orders_snapshot       news_snapshot
external_analysis_snapshot unknown_snapshot

confirmed    rejected    draft    needs_user_review    superseded

high    medium    low    unknown
```

**Schema keys:**
```
snapshot_type    confirmation_status    confidence
extracted_fields    target_local_file    draft_id
source_description    raw_source_reference    notes
related_tickers    created_at    uncertainties
missing_required_fields
```

**CLI option names and command names:**
```
snapshot    confirm    reject    export-research-notes    export-company-facts
--output-draft    --output-dir    --overwrite    --language
```

**Warning codes:**
```
missing_optional_profile    missing_optional_journal
missing_optional_financials  missing_optional_company_facts
missing_watchlist_status    unknown_watchlist_status
missing_sector              missing_market_value
```

**Ticker symbols:** Any ticker symbol passed by the user or written to disk.

**File paths:** Any path passed by the user or written to disk.

---

## User-Provided Content Handling

User-provided content must not be translated. This includes:

- `source_description` field value
- `notes` field value
- `raw_source_reference` field value
- Values within `extracted_fields`
- Research note text (all sections)
- Company facts values (all fields)
- Open questions text
- Risks text
- Evidence gaps text
- Reasons to wait text

Only Atlas-generated CLI display labels, status messages, and headings may be
Swedish. User-provided content passes through unchanged in every locale.

---

## Required Tests Before Implementation

The Phase 2 implementation sprint must add the following tests before
`--language` is considered complete for write-producing commands:

**CLI option presence:**
- `atlas snapshot confirm --help` includes `--language`
- `atlas snapshot reject --help` includes `--language`
- `atlas snapshot export-research-notes --help` includes `--language`
- `atlas snapshot export-company-facts --help` includes `--language`

**Default behavior (backward compatibility):**
- `atlas snapshot confirm ...` (no `--language`) display output unchanged
- `atlas snapshot confirm ... --language en` display output identical to default
- All existing scripts pass without modification

**Swedish CLI display output:**
- `atlas snapshot confirm ... --language sv` terminal output includes Swedish heading
- `atlas snapshot reject ... --language sv` terminal output includes Swedish heading
- `atlas snapshot export-research-notes ... --language sv` terminal output includes Swedish heading
- `atlas snapshot export-company-facts ... --language sv` terminal output includes Swedish heading

**Unsupported locale rejection (before file writes):**
- `atlas snapshot confirm ... --language fr` exits non-zero, no files written
- `atlas snapshot export-research-notes ... --language fr` exits non-zero, no directories created
- All unsupported values tested: `fr`, `de`, `EN`, `SV`, `en-US`, `sv-SE`

**Written file invariance:**
- `snapshot confirm ... --language sv` output draft identical to `--language en`
- `snapshot reject ... --language sv` output draft identical to `--language en`
- `snapshot export-research-notes ... --language sv` notes.md identical to `--language en`
- `snapshot export-company-facts ... --language sv` .json identical to `--language en`

**Canonical value preservation:**
- Confirmed draft with `--language sv` has `confirmation_status: confirmed`
- Rejected draft with `--language sv` has `confirmation_status: rejected`
- Exported notes.md with `--language sv` contains the original ticker path
- Exported company facts with `--language sv` contains canonical schema keys

**User-provided content preservation:**
- `notes` field value unchanged in confirmed/rejected output draft
- Research note text unchanged in exported notes.md
- Company facts values unchanged in exported JSON

**Write collision behavior unchanged:**
- Overwrite guard still refuses existing output without `--overwrite`, regardless of `--language`

**Infrastructure:**
- No gettext imports introduced
- No locale detection introduced
- No translation catalogs added
- No environment-variable language selection

---

## Safety Gates

Phase 2 implementation cannot proceed unless all of the following remain green:

1. Phase 1 (`test_cli_language_phase1_sprint257.py`) remains fully green.
2. Swedish safe-language guardrails (`docs/SwedishSafeLanguageGuardrails.md`)
   remain in force — no prohibited category phrasing in any new Swedish string.
3. Forbidden-category scan (`test_swedish_output_matrix_sprint252.py` B6) passes.
4. Canonical value preservation matrix (`test_swedish_canonical_passthrough_sprint253.py`) passes.
5. Unsupported-locale regression matrix (`test_unsupported_locale_regression_sprint254.py`) passes.
6. sv activation full-suite gate (`test_sv_activation_full_suite_gate_sprint255.py`) passes.
7. CLI default-English regression passes: no Phase 2 command omitting `--language`
   produces Swedish output.
8. File-write invariance tests are included in the Phase 2 sprint.
9. No output files are created or modified when language validation fails.
10. Demos and RC verification remain green.

---

## Rollout Recommendation

```
Phase 0 — COMPLETE (Sprints 247–255)
  Swedish internal activation (B1–B14 all DONE)

Phase 1 — COMPLETE (Sprint 257)
  --language for read-only CLI commands:
    atlas weekly-review          --language {en,sv}
    atlas snapshot validate      --language {en,sv}
    atlas snapshot review        --language {en,sv}

Phase 2 — COMPLETE (Sprint 259)
  --language for write-producing local commands:
    atlas snapshot confirm               --language {en,sv}   ✓
    atlas snapshot reject                --language {en,sv}   ✓
    atlas snapshot export-research-notes --language {en,sv}   ✓
    atlas snapshot export-company-facts  --language {en,sv}   ✓
  Key constraint confirmed: --language affects display text only.
  Written files verified identical regardless of language setting.

Phase 3 — NOT YET PLANNED
  Consider Swedish user-facing documentation (N1)
  Consider Swedish investor profile field labels (N2)
```

---

## Open Questions

1. **Which Phase 2 commands to group together?** All four can be implemented in a
   single sprint (Sprint 259). They share the same pattern. Alternatively, confirm
   and reject could be implemented first, then export commands second. Recommendation:
   implement all four in a single sprint since the pattern is identical.

2. **Renderer functions for confirm/reject display text** — The implementation
   sprint must identify which renderer functions generate the CLI success/block/error
   text for confirm and reject, and ensure `locale=language` is passed to them.
   Review `atlas/snapshot_input/render.py` for confirm/reject display functions.

3. **Export commands have minimal CLI display text** — `export-research-notes` and
   `export-company-facts` may produce only a one-line success or error message.
   Verify what text they currently produce and whether Swedish variants exist in
   `atlas/snapshot_input/strings_sv.py`.

4. **File-write invariance testing strategy** — The test must write files with both
   `--language en` and `--language sv` and compare output. This requires a temporary
   output directory per test. The implementation sprint must define this test pattern.

---

## Recommended Implementation Sprint

**Sprint 259:** Implement `--language` for Phase 2 Snapshot write commands.

After Phase 2 is planned (this document), implementation can safely add
`--language` to all four local write-producing Snapshot commands with tests
proving display localization only and written artifact invariance.

**Pre-conditions for Sprint 259:**
- This planning document reviewed.
- Phase 1 (Sprint 257) remains stable.
- All safety gates from "Safety Gates" above are green.
- Implementation follows the display-only boundary documented above.
- File-write invariance tests are included.
- All required tests from "Required Tests Before Implementation" are added.
